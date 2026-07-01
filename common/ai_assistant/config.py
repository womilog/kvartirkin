"""Configuration for the AI assistant.

All knobs live here so the rest of the code never reads ``os.environ`` or
``django.conf.settings`` directly. This keeps tests easy (just patch this
module) and makes the deployment contract obvious.

Environment variables (with sensible defaults so dev just works):

* ``GIGACHAT_CREDENTIALS``  - base64 client_id:secret pair from Sber.
* ``GIGACHAT_SCOPE``        - e.g. ``GIGACHAT_API_PERS`` or ``GIGACHAT_API_CORP``.
* ``GIGACHAT_MODEL``        - model name, defaults to ``GigaChat-2``.
* ``GIGACHAT_BASE_URL``     - REST base URL.
* ``GIGACHAT_AUTH_URL``     - OAuth token URL.
* ``GIGACHAT_VERIFY_SSL``   - ``1``/``0`` (Sber uses a Russian root CA that
                              isn't in the default trust store).
* ``AI_ASSISTANT_ENABLED``  - master kill-switch (``1``/``0``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from django.conf import settings


def _env(name: str, default: str = "") -> str:
    """Look up a value first in Django settings, then in os.environ.

    Letting Django settings win means production deployments can drop the
    credentials into ``settings.py`` (or a settings module loaded from a
    secrets manager) without exporting env vars.
    """
    val = getattr(settings, name, None)
    if val is not None and val != "":
        return str(val)
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class AssistantSettings:
    enabled: bool
    credentials: str
    scope: str
    model: str
    base_url: str
    auth_url: str
    verify_ssl: bool
    request_timeout: float
    max_history_messages: int
    max_retrieved_apartments: int
    rate_limit_per_minute: int

    @classmethod
    def load(cls) -> "AssistantSettings":
        return cls(
            enabled=_env_bool("AI_ASSISTANT_ENABLED", True),
            # NOTE: the literal default below is the same dev key that was
            # checked into the original prototype. Treat it as throwaway -
            # rotate it in production via ``GIGACHAT_CREDENTIALS``.
            credentials=_env(
                "GIGACHAT_CREDENTIALS",
                "M2UyMDc2ZGUtYjBmNC00ZDEzLWFhYmItNThjMDBkMzg1Nzc4OjBlMjM4ZjIzLTFkYzctNDgwYS1hYjliLTA5YmY0ZTg3OTE0NQ==",
            ),
            scope=_env("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
            model=_env("GIGACHAT_MODEL", "GigaChat-2"),
            base_url=_env(
                "GIGACHAT_BASE_URL",
                "https://gigachat.devices.sberbank.ru/api/v1",
            ),
            auth_url=_env(
                "GIGACHAT_AUTH_URL",
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            ),
            verify_ssl=_env_bool("GIGACHAT_VERIFY_SSL", "G:/sertifacts_for_gigachat/russian_trusted_root_ca.cer"),  # False
            request_timeout=float(_env("GIGACHAT_TIMEOUT", "30")),
            max_history_messages=int(_env("AI_ASSISTANT_MAX_HISTORY", "8")),
            max_retrieved_apartments=int(_env("AI_ASSISTANT_MAX_RAG_HITS", "4")),
            rate_limit_per_minute=int(_env("AI_ASSISTANT_RATE_LIMIT", "20")),
        )


def get_settings() -> AssistantSettings:
    """Return cached settings. Cheap to call."""
    global _CACHED
    if _CACHED is None:
        _CACHED = AssistantSettings.load()
    return _CACHED


_CACHED: AssistantSettings | None = None
