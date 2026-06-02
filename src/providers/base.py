"""Base provider class and shared models for API key testing."""

from abc import ABC, abstractmethod
from typing import Optional
import httpx
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Information about an available AI model."""

    id: str
    name: str
    context_window: Optional[int] = None
    owned_by: Optional[str] = None


class TestResult(BaseModel):
    """Result of a liveness test."""

    success: bool
    response_text: Optional[str] = None
    latency_ms: float
    error_message: Optional[str] = None
    model_id: str
    provider: str


class ProviderError(Exception):
    """Raised when a provider operation fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


_STATUS_MESSAGES: dict[int, str] = {
    400: "Bad request — check model ID and parameters",
    401: "Invalid or expired API key",
    402: "Payment required — no credits on this account",
    403: "Forbidden — account may be suspended or key lacks permissions",
    404: "Not found — model does not exist or the endpoint URL is wrong",
    408: "Server timeout — the provider took too long to respond",
    429: "Rate limited or quota exceeded — wait and retry, or check your plan limits",
    500: "Provider internal error — try again later",
    502: "Bad gateway — the provider's upstream server failed",
    503: "Service unavailable — the provider is down or overloaded",
    529: "Provider overloaded — try again later",
}


def _extract_api_error_message(response: httpx.Response) -> Optional[str]:
    """Try to extract a human-readable message from an API error response body.

    Handles both OpenAI-compatible and Gemini formats: {"error": {"message": "..."}}.
    Returns None if the body cannot be parsed or has no message.
    """
    try:
        body = response.json()
        error = body.get("error", {})
        if isinstance(error, dict):
            return error.get("message") or None
    except Exception:
        pass
    return None


def _handle_http_error(response: httpx.Response) -> None:
    """Raise ProviderError with a specific message if response is not 2xx.

    Call this instead of response.raise_for_status() so the response body
    can be read before the error is raised.
    """
    if response.is_success:
        return

    status = response.status_code
    api_msg = _extract_api_error_message(response)
    fallback = _STATUS_MESSAGES.get(status, f"Unexpected HTTP {status}")

    if api_msg:
        message = f"{api_msg} (HTTP {status})"
    else:
        message = f"{fallback} (HTTP {status})"

    raise ProviderError(message, status_code=status)


def _handle_request_error(exc: httpx.RequestError) -> ProviderError:
    """Convert an httpx RequestError into a ProviderError with a specific message.

    Returns the error (rather than raising) so callers can do:
        raise _handle_request_error(e)
    """
    cause_str = str(exc.__cause__) if exc.__cause__ else str(exc)

    if isinstance(exc, httpx.TimeoutException):
        return ProviderError("Request timed out — the provider did not respond in time")

    if isinstance(exc, httpx.ConnectError):
        cl = cause_str.lower()
        if "getaddrinfo" in cl or "name or service not known" in cl or "nodename nor servname" in cl:
            return ProviderError("DNS resolution failed — check your internet connection or the provider URL")
        if "connection refused" in cl:
            return ProviderError("Connection refused — the provider may be down")
        if "ssl" in cl or "certificate" in cl or "tls" in cl:
            return ProviderError("SSL/TLS error — certificate verification failed (check VPN or proxy settings)")
        if "reset" in cl:
            return ProviderError("Connection was reset by the provider — try again")
        return ProviderError(f"Connection failed: {cause_str}")

    return ProviderError(f"Network error: {exc}")


class BaseProvider(ABC):
    """Abstract base class for AI provider integrations."""

    name: str
    key_prefixes: list[str]

    @abstractmethod
    async def list_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch available models for the given API key.

        Raises:
            ProviderError: If authentication fails or API call errors.
        """

    @abstractmethod
    async def test_key(self, api_key: str, model_id: str) -> TestResult:
        """Test the API key with a simple prompt on the given model.

        Returns a TestResult with latency and response text.

        Raises:
            ProviderError: If the test fails (except API auth, which is caught and returned in TestResult).
        """
