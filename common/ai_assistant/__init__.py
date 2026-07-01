"""AI Assistant package for the Kvartirkin apartment booking project.

Provides a Retrieval-Augmented Generation (RAG) consultant powered by
GigaChat. Exposes a Django app, an HTTP endpoint and a high-level
``Assistant`` facade.

The public API is intentionally small:

    from common.ai_assistant.assistant import get_assistant
    assistant = get_assistant()
    reply = assistant.answer(user_message, session_history=[])

See ``common/ai_assistant/README`` notes in ``views.py`` and ``assistant.py``
for implementation details.
"""

default_app_config = "common.ai_assistant.apps.AIAssistantConfig"
