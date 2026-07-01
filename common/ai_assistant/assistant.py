"""High-level facade tying together RAG, prompts and the LLM client.

The rest of the app only ever talks to ``get_assistant()``.

Flow per user message:

1. Retrieve top-K knowledge-base snippets for the question.
2. Build a chat-completion payload:
      - system prompt with persona + rules
      - context block with the RAG snippets
      - recent conversation history (truncated)
      - the new user message
3. Call GigaChat.
4. If anything goes wrong with the LLM (quota, network, rate-limit), build
   a deterministic fallback answer from the same RAG hits.

The class is stateless across requests — conversation history is supplied
by the caller (currently the Django session, see ``views.py``).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Iterable

from .client import GigaChatClient
from .config import AssistantSettings, get_settings
from .exceptions import (
    AssistantError,
    AuthError,
    BadRequest,
    ProviderUnavailable,
    RateLimited,
    TokenQuotaExceeded,
)

from .fallback import build_fallback_answer
from .knowledge_base import Document
from .prompts import SYSTEM_PROMPT, build_context_block
from .retriever import Retriever, get_retriever

logger = logging.getLogger(__name__)


@dataclass
class AssistantReply:
    """Structured reply so the view layer can render UX hints."""

    text: str
    degraded: bool          # True when we couldn't reach the LLM
    reason: str | None      # short machine-readable cause when degraded
    sources: list[str]      # titles of the RAG documents that fed the answer


class Assistant:
    def __init__(
        self,
        settings: AssistantSettings | None = None,
        retriever: Retriever | None = None,
        client: GigaChatClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._retriever = retriever or get_retriever()
        self._client = client or GigaChatClient(self._settings)

    # -- public -------------------------------------------------------------
    def answer(
        self,
        user_message: str,
        history: Iterable[dict[str, str]] | None = None,
    ) -> AssistantReply:
        user_message = (user_message or "").strip()
        if not user_message:
            return AssistantReply(
                text="Пожалуйста, напишите вопрос — я постараюсь помочь.",
                degraded=False,
                reason=None,
                sources=[],
            )

        if not self._settings.enabled:
            logger.info("AI assistant disabled via settings")
            return AssistantReply(
                text=(
                    "Нейро-консультант временно отключён администратором. "
                    "Свяжитесь с нами через контакты в подвале сайта."
                ),
                degraded=True,
                reason="disabled",
                sources=[],
            )

        hits = self._retriever.search(
            user_message,
            k=self._settings.max_retrieved_apartments,
        )
        sources = [doc.title for doc, _ in hits]

        messages = self._build_messages(user_message, history, hits)

        try:
            reply_text = self._client.chat(messages)
            return AssistantReply(
                text=reply_text,
                degraded=False,
                reason=None,
                sources=sources,
            )
        except TokenQuotaExceeded as exc:
            logger.error("AI assistant: token quota exhausted: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="quota",
                sources=sources,
            )
        except RateLimited as exc:
            logger.warning("AI assistant: rate limited by provider: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="rate_limited",
                sources=sources,
            )
        except AuthError as exc:
            logger.error("AI assistant: auth failure: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="auth",
                sources=sources,
            )
        except ProviderUnavailable as exc:
            logger.warning("AI assistant: provider unavailable: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="unavailable",
                sources=sources,
            )
        except BadRequest as exc:
            logger.error("AI assistant: bad request to provider: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="bad_request",
                sources=sources,
            )
        except AssistantError as exc:  # safety net
            logger.exception("AI assistant: unexpected error: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="error",
                sources=sources,
            )
        except Exception as exc:  # noqa: BLE001
            # Never crash the chat widget because of an unforeseen bug.
            logger.exception("AI assistant: unhandled exception: %s", exc)
            return AssistantReply(
                text=build_fallback_answer(hits),
                degraded=True,
                reason="error",
                sources=sources,
            )

    # -- internals ----------------------------------------------------------
    def _build_messages(
        self,
        user_message: str,
        history: Iterable[dict[str, str]] | None,
        hits: list[tuple[Document, float]],
    ) -> list[dict[str, str]]:
        snippets = [doc.text for doc, _ in hits]
        context_block = build_context_block(snippets)

        # GigaChat requires exactly one system message and it must come
        # first, so the persona prompt and the retrieved context are
        # concatenated into a single system turn.
        system_content = SYSTEM_PROMPT + "\n\n" + context_block

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content},
        ]

        if history:
            # Keep only the last N turns and only ``user``/``assistant`` roles
            # so a malformed session can't smuggle in extra system prompts.
            recent = [
                m for m in history
                if isinstance(m, dict)
                and m.get("role") in ("user", "assistant")
                and isinstance(m.get("content"), str)
            ][-self._settings.max_history_messages:]
            messages.extend(recent)

        messages.append({"role": "user", "content": user_message})
        return messages


_ASSISTANT: Assistant | None = None
_ASSISTANT_LOCK = threading.Lock()


def get_assistant() -> Assistant:
    """Lazy process-wide singleton."""
    global _ASSISTANT
    if _ASSISTANT is None:
        with _ASSISTANT_LOCK:
            if _ASSISTANT is None:
                _ASSISTANT = Assistant()
    return _ASSISTANT


def reset_assistant() -> None:
    """Test/admin hook: drop the cached instance so settings are re-read."""
    global _ASSISTANT
    with _ASSISTANT_LOCK:
        _ASSISTANT = None
