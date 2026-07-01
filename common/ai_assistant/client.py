"""Thin HTTP client for the GigaChat REST API.

Why not ``langchain-gigachat``? It works, but pulls in LangChain core + a
stack of pydantic-v2-shape adapters we don't otherwise need. Hitting the
REST endpoint directly is ~80 lines of code, gives us first-class control
over timeouts, retries and error classification, and is trivially mockable
in tests.

The client is intentionally stateless except for the cached OAuth token.
It is safe to call from multiple threads (Django request workers).
"""

from __future__ import annotations

import logging
import random
import threading
import time
import uuid
from typing import Any

import requests
import urllib3

from .config import AssistantSettings
from .exceptions import (
    AuthError,
    BadRequest,
    ProviderUnavailable,
    RateLimited,
    TokenQuotaExceeded,
)

logger = logging.getLogger(__name__)

# Stop urllib3 from spamming the logs when ``verify_ssl=False``. This is the
# documented Sber/GigaChat dev path; production should install the Russian
# Trusted Root CA instead.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Token lifetime per GigaChat docs is 30 minutes. We refresh a bit earlier
# to avoid edge-of-expiry 401s.
_TOKEN_TTL_SECONDS = 25 * 60

# Substrings GigaChat puts in the response body when the account is out of
# tokens / has no active plan. We check both English and Russian variants.
_QUOTA_HINTS = (
    "insufficient",
    "quota",
    "balance",
    "токен",       # "токены закончились"
    "баланс",
    "исчерпан",
    "лимит",
)


class GigaChatClient:
    def __init__(self, settings: AssistantSettings) -> None:
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = threading.Lock()
        self._session = requests.Session()

    # -- OAuth --------------------------------------------------------------
    def _fetch_access_token(self) -> str:
        """Exchange the client credentials for a short-lived access token."""
        headers = {
            "Authorization": f"Basic {self._settings.credentials}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {"scope": self._settings.scope}
        try:
            resp = self._session.post(
                self._settings.auth_url,
                headers=headers,
                data=data,
                verify=self._settings.verify_ssl,
                timeout=self._settings.request_timeout,
            )
        except requests.RequestException as exc:
            raise ProviderUnavailable(f"OAuth network error: {exc}") from exc

        self._raise_for_status(resp, context="oauth")
        try:
            payload = resp.json()
            return payload["access_token"]
        except (ValueError, KeyError) as exc:
            raise ProviderUnavailable(
                f"OAuth response missing access_token: {resp.text[:200]!r}"
            ) from exc

    def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        with self._lock:
            if self._token and time.monotonic() < self._token_expires_at:
                return self._token
            self._token = self._fetch_access_token()
            self._token_expires_at = time.monotonic() + _TOKEN_TTL_SECONDS
            return self._token

    def _invalidate_token(self) -> None:
        with self._lock:
            self._token = None
            self._token_expires_at = 0.0

    # -- error classification ----------------------------------------------
    @staticmethod
    def _looks_like_quota_error(body_text: str) -> bool:
        low = body_text.lower()
        return any(h in low for h in _QUOTA_HINTS)

    def _raise_for_status(self, resp: requests.Response, *, context: str) -> None:
        if resp.ok:
            return

        status = resp.status_code
        body = resp.text or ""
        snippet = body[:300]

        # 402 is the standard "payment required" — GigaChat uses it for
        # depleted balances in some plans.
        if status == 402 or (status in (401, 403) and self._looks_like_quota_error(body)):
            raise TokenQuotaExceeded(
                f"GigaChat reports the token balance is exhausted ({context}, {status}): {snippet}"
            )
        if status == 401:
            raise AuthError(f"GigaChat 401 ({context}): {snippet}")
        if status == 429:
            raise RateLimited(f"GigaChat 429 ({context}): {snippet}")
        if 500 <= status < 600:
            raise ProviderUnavailable(
                f"GigaChat {status} ({context}): {snippet}"
            )
        if 400 <= status < 500:
            raise BadRequest(f"GigaChat {status} ({context}): {snippet}")
        raise ProviderUnavailable(
            f"GigaChat unexpected status {status} ({context}): {snippet}"
        )

    # -- chat ---------------------------------------------------------------
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = 512,
    ) -> str:
        """Send a chat completion request and return the assistant text.

        Retries on 429/5xx with exponential backoff + jitter. Never retries
        on token-quota or auth errors — those are propagated immediately so
        the caller can fall back.
        """
        url = f"{self._settings.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        max_attempts = 3
        base_delay = 0.8  # seconds
        last_exc: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            token = self._ensure_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Client-ID": str(uuid.uuid4()),
            }
            try:
                resp = self._session.post(
                    url,
                    headers=headers,
                    json=payload,
                    verify=self._settings.verify_ssl,
                    timeout=self._settings.request_timeout,
                )
            except requests.RequestException as exc:
                last_exc = ProviderUnavailable(f"Network error: {exc}")
                logger.warning("GigaChat network error (attempt %s/%s): %s",
                               attempt, max_attempts, exc)
            else:
                # Special-case 401: maybe our cached token expired between
                # checks. Drop it and let the next attempt re-auth.
                if resp.status_code == 401 and not self._looks_like_quota_error(resp.text or ""):
                    self._invalidate_token()
                    last_exc = AuthError("Token rejected, refreshing")
                else:
                    try:
                        self._raise_for_status(resp, context="chat")
                        return self._extract_text(resp.json())
                    except (RateLimited, ProviderUnavailable) as exc:
                        last_exc = exc
                        logger.warning(
                            "GigaChat retryable error (attempt %s/%s): %s",
                            attempt, max_attempts, exc,
                        )
                    # TokenQuotaExceeded / AuthError / BadRequest: do NOT retry.

            # Back off before the next attempt.
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                delay += random.uniform(0, 0.3)
                time.sleep(delay)

        assert last_exc is not None
        raise last_exc

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        try:
            return payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise ProviderUnavailable(
                f"Malformed GigaChat response: {str(payload)[:200]!r}"
            ) from exc
