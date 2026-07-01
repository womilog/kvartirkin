"""Django AppConfig for the AI assistant.

We deliberately keep ``ready()`` empty for now: the assistant is
lazy-initialized on first use to avoid slowing down ``manage.py`` commands
(migrations, collectstatic) and to keep import-time side effects out of the
critical path.
"""

from django.apps import AppConfig


class AIAssistantConfig(AppConfig):
    name = "common.ai_assistant"
    label = "ai_assistant"
    verbose_name = "AI Assistant (RAG over apartments)"

    def ready(self) -> None:  # pragma: no cover - nothing to wire yet
        # If/when we add signals (e.g. invalidate the RAG index on Apartment
        # save), this is where we'd connect them.
        return None