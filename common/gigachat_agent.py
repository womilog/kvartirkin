"""DEPRECATED stub — task-tracker prototype.

This module used to contain a LangGraph agent that managed a SQLite
``tasks`` table. It has been superseded by :mod:`common.ai_assistant`,
the production-grade RAG consultant for apartment booking.

The file is kept only as a documentation marker. No code path imports
from it. Safe to delete once the migration is reviewed.

Migration map (old -> new):

* ``GigaChat`` LangChain wrapper          -> ``common.ai_assistant.client.GigaChatClient``
* ``create_agent`` + ``InMemorySaver``    -> ``common.ai_assistant.assistant.Assistant`` +
                                              ``common.ai_assistant.session`` (Django session)
* SQLite ``tasks`` table tools             -> RAG over the Apartment/Review ORM
                                              (``common.ai_assistant.knowledge_base``)
* No error handling                        -> ``common.ai_assistant.exceptions`` +
                                              fallback in ``Assistant.answer``
"""
