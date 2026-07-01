"""Rule-based fallback when the LLM is unavailable.

Whenever GigaChat is unreachable (network down, tokens depleted, rate
limit hit repeatedly) we still want the chat widget to be useful. This
module turns the RAG hits into a short, deterministic answer.

It is intentionally simple: list the most relevant snippets and tell the
user the smart assistant is taking a break.
"""

from __future__ import annotations

from .knowledge_base import Document


_DEGRADED_PREFIX = (
    "Сейчас я отвечаю в упрощённом режиме (нейросеть временно недоступна), "
    "но вот что у меня нашлось по вашему вопросу:"
)

_NO_HITS = (
    "К сожалению, по вашему запросу я ничего не нашёл в базе. "
    "Попробуйте посмотреть раздел «Квартиры» или свяжитесь с администратором "
    "— контакты есть в подвале сайта."
)


def _format_hit(doc: Document) -> str:
    # Trim the doc text — fallback is meant to be a teaser, not a wall of text.
    body = doc.text.strip()
    if len(body) > 320:
        body = body[:317].rsplit(" ", 1)[0] + "…"
    return f"• {doc.title}\n  {body}"


def build_fallback_answer(hits: list[tuple[Document, float]]) -> str:
    if not hits:
        return _NO_HITS
    blocks = [_format_hit(d) for d, _ in hits[:3]]
    return _DEGRADED_PREFIX + "\n\n" + "\n\n".join(blocks)
