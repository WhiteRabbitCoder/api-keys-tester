"""NVIDIA NIM API provider integration (OpenAI-compatible)."""

from .openai_compat_mixin import OpenAICompatMixin


class NvidiaNIMProvider(OpenAICompatMixin):
    """Provider for NVIDIA NIM API (OpenAI-compatible)."""

    name = "NVIDIA NIM"
    key_prefixes = ["nvapi-"]
    BASE_URL = "https://integrate.api.nvidia.com/v1"
