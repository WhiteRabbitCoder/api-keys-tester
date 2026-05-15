"""Provider integrations for API key testing."""

from .base import BaseProvider, ModelInfo, TestResult, ProviderError
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .deepseek_provider import DeepSeekProvider
from .openrouter_provider import OpenRouterProvider
from .nvidia_nim_provider import NvidiaNIMProvider

PROVIDERS: dict[str, BaseProvider] = {
    "openai": OpenAIProvider(),
    "gemini": GeminiProvider(),
    "deepseek": DeepSeekProvider(),
    "openrouter": OpenRouterProvider(),
    "nvidia_nim": NvidiaNIMProvider(),
}


def get_provider(name: str) -> BaseProvider:
    """Get a provider by name."""
    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Unknown provider: {name}")
    return provider


def all_providers() -> list[str]:
    """Get list of all available provider names."""
    return sorted(PROVIDERS.keys())


__all__ = [
    "BaseProvider",
    "ModelInfo",
    "TestResult",
    "ProviderError",
    "PROVIDERS",
    "get_provider",
    "all_providers",
]
