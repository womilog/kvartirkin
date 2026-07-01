"""Domain-specific exceptions for the AI assistant.

Keeping these in one tiny module makes error handling explicit at every
layer (HTTP view, assistant facade, client) and lets callers distinguish
``ProviderUnavailable`` (retryable infra issue) from ``TokenQuotaExceeded``
(billing problem the user can't retry away).
"""


class AssistantError(Exception):
    """Base class for all AI-assistant errors."""


class ProviderUnavailable(AssistantError):
    """Network/5xx/timeout problems talking to GigaChat."""


class RateLimited(AssistantError):
    """HTTP 429 from the provider."""


class TokenQuotaExceeded(AssistantError):
    """The account's token balance is depleted (HTTP 402, or specific 401/403
    messages reported by GigaChat). The caller should fall back to a
    non-generative answer."""


class AuthError(AssistantError):
    """Invalid / expired credentials (HTTP 401 not related to quota)."""


class BadRequest(AssistantError):
    """HTTP 4xx that we shouldn't retry."""
