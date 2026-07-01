"""Knowledge-base layer.

This module turns Django ORM rows (Apartments, Reviews, static FAQ entries)
into plain-text "documents" suitable for retrieval. Each document is
self-contained: the LLM only ever sees these snippets, never raw model
instances.

Why not a vector DB?
--------------------
For a few dozen apartments a pure-Python TF-IDF index is faster end-to-end
(no network hop, no embedding cost, no extra service) and zero-dep beyond
what's already in Django. The ``Document`` abstraction and the
``KnowledgeBase`` interface are deliberately narrow so a future swap to
pgvector/Chroma/FAISS only touches ``retriever.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A retrievable chunk of knowledge.

    ``doc_id`` is opaque but stable; ``source`` is one of
    ``"apartment" | "review" | "faq"`` for downstream filtering/UX.
    """

    doc_id: str
    source: str
    title: str
    text: str


# ---------------------------------------------------------------------------
# Static, hand-written FAQ. Living in code (vs. a DB table) on purpose:
# - it ships with the deployment, no separate migration step;
# - changes are reviewed via PRs;
# - the content is tiny.
# Move to a model later if non-developers need to edit it.
# ---------------------------------------------------------------------------
FAQ: list[tuple[str, str]] = [
    (
        "Как забронировать квартиру?",
        "Чтобы забронировать апартаменты, откройте страницу нужной квартиры в "
        "разделе «Квартиры», выберите даты заезда и выезда, число гостей и "
        "нажмите «Забронировать». Для отправки заявки нужно войти в аккаунт. "
        "После отправки заявка получает статус «Ожидает подтверждения» — "
        "администратор свяжется с вами для подтверждения.",
    ),
    (
        "Как происходит оплата?",
        "Оплата согласуется индивидуально с администратором после "
        "подтверждения заявки. На сайте сейчас не проводится онлайн-оплата.",
    ),
    (
        "Можно ли с питомцем?",
        "В некоторых квартирах разрешено проживание с питомцем — это указано "
        "в карточке квартиры. При бронировании отметьте опцию «с питомцем», "
        "к стоимости добавляется 500 ₽ за сутки.",
    ),
    (
        "Как отменить или изменить бронирование?",
        "Откройте раздел «Профиль» — там перечислены ваши бронирования и "
        "их статусы. Для отмены или изменения дат свяжитесь с "
        "администратором: контакты есть в подвале сайта.",
    ),
    (
        "Где находятся апартаменты?",
        "Все квартиры расположены в Геленджике. Точный адрес и расстояние "
        "до моря указаны на странице каждой квартиры.",
    ),
    (
        "Что такое статус заявки?",
        "Заявка проходит этапы: «Ожидает подтверждения» (отправлена, "
        "даты уже зарезервированы), «Подтверждено» (одобрена администратором), "
        "«Отклонено» или «Отменено» (даты освобождаются).",
    ),
]


def _apartment_to_text(apt) -> str:
    """Render an ``Apartment`` instance as a compact descriptive paragraph.

    Kept deliberately verbose-but-structured so TF-IDF picks up amenity
    keywords ("wi-fi", "кондиционер", "бассейн"…) and so the LLM has all
    facts it might be asked about in one place.
    """
    amenities = []
    if apt.has_wifi:
        amenities.append("Wi-Fi")
    if apt.has_smart_tv:
        amenities.append("Smart TV")
    if apt.has_washing_machine:
        amenities.append("стиральная машина")
    if apt.has_ac:
        amenities.append("кондиционер")
    if apt.pets_allowed:
        amenities.append("можно с питомцем")
    if apt.free_private_park:
        amenities.append("бесплатная частная парковка")
    if apt.near_pool:
        amenities.append("открытый бассейн рядом")
    if apt.avaible_smoke:
        amenities.append("разрешено курить")
    amenities_str = ", ".join(amenities) if amenities else "без особых удобств"

    distance = apt.distance_to_sea or "не указано"
    booking_state = (
        "бронирование открыто" if apt.bookings_enabled else "бронирование временно закрыто"
    )

    return (
        f"Квартира: {apt.name}.\n"
        f"Адрес: {apt.address}.\n"
        f"Комнат: {apt.rooms}; площадь: {apt.area} м²; "
        f"максимум гостей: {apt.max_guests}.\n"
        f"Цена за сутки: {int(apt.price_per_day)} ₽.\n"
        f"Расстояние до моря: {distance}.\n"
        f"Удобства: {amenities_str}.\n"
        f"Статус: {booking_state}.\n"
        f"Описание: {apt.description}"
    )


def _review_to_text(review) -> str:
    return (
        f"Отзыв о квартире «{review.apartment.name}», оценка "
        f"{review.rating}/5: {review.text}"
    )


def load_documents() -> list[Document]:
    """Materialize the full corpus from the ORM + the static FAQ.

    Returns a fresh list each call; the caller decides about caching
    (``retriever.IndexCache``).
    """
    # Local imports so importing this module never triggers Django app
    # loading during ``manage.py`` startup.
    from apartments.models import Apartment, Review

    docs: list[Document] = []

    try:
        apartments = list(Apartment.objects.filter(is_active=True))
    except Exception:  # noqa: BLE001
        logger.exception("AI assistant: failed to load apartments for RAG")
        apartments = []

    for apt in apartments:
        docs.append(
            Document(
                doc_id=f"apartment:{apt.pk}",
                source="apartment",
                title=apt.name,
                text=_apartment_to_text(apt),
            )
        )

    try:
        # Cap reviews so the corpus stays bounded.
        reviews = list(
            Review.objects.select_related("apartment").order_by("-created_at")[:50]
        )
    except Exception:  # noqa: BLE001
        logger.exception("AI assistant: failed to load reviews for RAG")
        reviews = []

    for rv in reviews:
        docs.append(
            Document(
                doc_id=f"review:{rv.pk}",
                source="review",
                title=f"Отзыв — {rv.apartment.name}",
                text=_review_to_text(rv),
            )
        )

    for i, (q, a) in enumerate(FAQ):
        docs.append(
            Document(
                doc_id=f"faq:{i}",
                source="faq",
                title=q,
                text=f"Вопрос: {q}\nОтвет: {a}",
            )
        )

    return docs


def iter_documents() -> Iterable[Document]:
    """Generator wrapper; kept for API symmetry."""
    yield from load_documents()
