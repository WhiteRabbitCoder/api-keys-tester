"""DeepSeek API provider integration (OpenAI-compatible)."""

from .openai_compat_mixin import OpenAICompatMixin


class DeepSeekProvider(OpenAICompatMixin):
    """Provider for DeepSeek API (OpenAI-compatible)."""

    name = "DeepSeek"
    key_prefixes = ["sk-"]
    BASE_URL = "https://api.deepseek.com"
