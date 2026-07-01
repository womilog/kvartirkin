"""Conversation memory backed by the Django session.

Design notes
------------
The original prototype used LangGraph's ``InMemorySaver`` keyed by a
``thread_id``. That's fine for a notebook but breaks the moment you run
more than one gunicorn/uwsgi worker: each worker has its own memory, so
follow-up questions land on a process that has never seen the user.

Django's session framework is the natural fit:

* it already survives across requests and workers (DB / cache backed);
* it's automatically scoped to the current user (or anonymous cookie);
* no extra infra.

We cap the stored history aggressively to keep cookies/DB small.
"""

from __future__ import annotations

from typing import Iterable

_SESSION_KEY = "ai_assistant_history"
_MAX_STORED = 20  # turns kept on disk; the assistant trims further at send time


def load_history(session) -> list[dict[str, str]]:
    raw = session.get(_SESSION_KEY) or []
    if not isinstance(raw, list):
        return []
    # Defensive copy + shape validation.
    out: list[dict[str, str]] = []
    for item in raw:
        if (
            isinstance(item, dict)
            and item.get("role") in ("user", "assistant")
            and isinstance(item.get("content"), str)
        ):
            out.append({"role": item["role"], "content": item["content"]})
    return out


def append_turn(
    session,
    user_message: str,
    assistant_message: str,
) -> None:
    history = load_history(session)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": assistant_message})
    if len(history) > _MAX_STORED:
        history = history[-_MAX_STORED:]
    session[_SESSION_KEY] = history
    session.modified = True


def reset_history(session) -> None:
    if _SESSION_KEY in session:
        del session[_SESSION_KEY]
        session.modified = True
