"""OpenRouter API provider integration (OpenAI-compatible)."""

from .openai_compat_mixin import OpenAICompatMixin


class OpenRouterProvider(OpenAICompatMixin):
    """Provider for OpenRouter API (OpenAI-compatible)."""

    name = "OpenRouter"
    key_prefixes = ["sk-or-"]
    BASE_URL = "https://openrouter.io/api"
