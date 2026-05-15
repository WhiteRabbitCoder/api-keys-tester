"""Base provider class and shared models for API key testing."""

from abc import ABC, abstractmethod
from typing import Optional
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
