"""HTTP endpoints for the AI assistant.

A single JSON POST endpoint at ``/ai/chat/`` accepts a user message and
returns the assistant's reply. The page that hosts the chat widget already
uses Django templates, so CSRF is enabled and the frontend reads the token
from the cookie (see ``static/js/main.js`` updates).

Response schema::

    {
        "reply":    "<assistant text>",
        "degraded": true | false,
        "reason":   null | "quota" | "rate_limited" | "unavailable" | ...,
        "sources":  ["<doc title>", ...]
    }

The view is intentionally tiny: it does request validation, per-IP rate
limiting, and delegates everything else to :mod:`assistant`.
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from threading import Lock

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from .assistant import get_assistant
from .config import get_settings
from .session import append_turn, load_history, reset_history

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight in-memory rate limiter (per-IP, sliding window).
# Good enough for a low-traffic site. For production behind multiple workers,
# replace with django-ratelimit (Redis backend).
# ---------------------------------------------------------------------------
_RL_LOCK = Lock()
_RL_BUCKETS: dict[str, deque[float]] = {}
_RL_WINDOW_SECONDS = 60.0


def _client_ip(request: HttpRequest) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _allow_request(ip: str, limit_per_minute: int) -> bool:
    now = time.monotonic()
    cutoff = now - _RL_WINDOW_SECONDS
    with _RL_LOCK:
        bucket = _RL_BUCKETS.setdefault(ip, deque())
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit_per_minute:
            return False
        bucket.append(now)
        return True


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
_MAX_MESSAGE_CHARS = 1000


@require_POST
def chat(request: HttpRequest) -> HttpResponse:
    settings = get_settings()

    # Parse body. We accept JSON (preferred) and form-encoded as a fallback.
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return JsonResponse(
                {"error": "Invalid JSON body."},
                status=400,
            )
        message = (payload.get("message") or "").strip()
        action = (payload.get("action") or "").strip()
    else:
        message = (request.POST.get("message") or "").strip()
        action = (request.POST.get("action") or "").strip()

    # Allow the client to wipe the conversation without sending a new turn.
    if action == "reset":
        reset_history(request.session)
        return JsonResponse({"reset": True})

    if not message:
        return JsonResponse(
            {"error": "Поле 'message' обязательно."},
            status=400,
        )
    if len(message) > _MAX_MESSAGE_CHARS:
        return JsonResponse(
            {"error": f"Сообщение слишком длинное (максимум {_MAX_MESSAGE_CHARS} символов)."},
            status=413,
        )

    if not _allow_request(_client_ip(request), settings.rate_limit_per_minute):
        return JsonResponse(
            {
                "error": (
                    "Слишком много запросов. Подождите немного и попробуйте "
                    "снова."
                ),
            },
            status=429,
        )

    history = load_history(request.session)

    assistant = get_assistant()
    reply = assistant.answer(message, history=history)

    # Persist the turn even when degraded — keeps the conversation coherent
    # once the LLM recovers.
    append_turn(request.session, message, reply.text)

    return JsonResponse(
        {
            "reply": reply.text,
            "degraded": reply.degraded,
            "reason": reply.reason,
            "sources": reply.sources,
        }
    )
