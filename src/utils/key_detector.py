"""Heuristic detection of AI provider from API key prefix."""


def detect_provider(api_key: str) -> str | None:
    """Infer the provider name from an API key's prefix.

    Returns the provider name string or None if the key doesn't match a known pattern.

    Detection rules (in order):
    - sk-or-* → openrouter
    - AIza* → gemini
    - nvapi-* → nvidia_nim
    - sk-* → openai (note: DeepSeek keys also start with sk-, so this is ambiguous)
    - sk-* (with nv- or other patterns) handled case-by-case
    """
    key = api_key.strip()

    if key.startswith("sk-or-"):
        return "openrouter"

    if key.startswith("AIza"):
        return "gemini"

    if key.startswith("nvapi-"):
        return "nvidia_nim"

    # sk-* is ambiguous: could be OpenAI or DeepSeek
    # Default to openai; user can override in the UI
    if key.startswith("sk-"):
        return "openai"

    return None
