# Contributing to API Keys Tester

Thanks for your interest in contributing! This document explains how to get started.

## 🚀 Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/api-keys-tester.git
cd api-keys-tester
```

### 2. Set Up Development Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## 💡 What to Contribute

### Easy (Great for First-Time Contributors)

- [ ] Add a new provider (follow the existing pattern in `src/providers/`)
- [ ] Improve documentation or fix typos
- [ ] Add helpful comments to existing code
- [ ] Report bugs via GitHub Issues

### Medium

- [ ] Add tests for providers
- [ ] Implement result persistence (save to CSV/JSON)
- [ ] Add configuration file support
- [ ] Improve error messages

### Advanced

- [ ] Add streaming response display
- [ ] Implement multi-key side-by-side comparison
- [ ] Add keyboard shortcuts customization
- [ ] Build a web API wrapper

## 🏗️ Adding a New Provider

### Step 1: Create the Provider File

Create `src/providers/yourservice_provider.py`:

```python
"""Your Service API provider integration."""

import time
import httpx
from .base import BaseProvider, ModelInfo, TestResult, ProviderError


class YourServiceProvider(BaseProvider):
    """Provider for Your Service API."""

    name = "Your Service"
    key_prefixes = ["prefix-"]  # What does your API key start with?

    async def list_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch available models from Your Service API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.yourservice.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ProviderError("Invalid API key", status_code=401)
                raise ProviderError(f"API error: {e.response.status_code}")
            except httpx.TimeoutException:
                raise ProviderError("Request timeout")
            except httpx.RequestError as e:
                raise ProviderError(f"Request failed: {e}")

            data = response.json()
            models = []
            # Parse your API's response format
            for item in data.get("models", []):
                models.append(
                    ModelInfo(
                        id=item["id"],
                        name=item.get("name", item["id"]),
                        owned_by=item.get("owner"),
                    )
                )
            return sorted(models, key=lambda m: m.id)

    async def test_key(self, api_key: str, model_id: str) -> TestResult:
        """Test the API key with a simple API call."""
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.yourservice.com/v1/chat",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model_id,
                        "prompt": "Say hello in one word.",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                latency_ms = (time.time() - start_time) * 1000
                if e.response.status_code == 401:
                    return TestResult(
                        success=False,
                        response_text=None,
                        latency_ms=latency_ms,
                        error_message="Invalid API key",
                        model_id=model_id,
                        provider=self.name,
                    )
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=f"API error: {e.response.status_code}",
                    model_id=model_id,
                    provider=self.name,
                )
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=str(e),
                    model_id=model_id,
                    provider=self.name,
                )

            latency_ms = (time.time() - start_time) * 1000
            try:
                data = response.json()
                response_text = data["output"]  # Adjust based on API response
                return TestResult(
                    success=True,
                    response_text=response_text,
                    latency_ms=latency_ms,
                    error_message=None,
                    model_id=model_id,
                    provider=self.name,
                )
            except Exception as e:
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=f"Failed to parse response: {e}",
                    model_id=model_id,
                    provider=self.name,
                )
```

### Step 2: Register the Provider

Edit `src/providers/__init__.py`:

```python
from .yourservice_provider import YourServiceProvider

PROVIDERS: dict[str, BaseProvider] = {
    # ... existing providers ...
    "yourservice": YourServiceProvider(),
}
```

### Step 3: Add Key Detection (Optional)

Edit `src/utils/key_detector.py`:

```python
def detect_provider(api_key: str) -> str | None:
    key = api_key.strip()

    # ... existing checks ...

    if key.startswith("prefix-"):
        return "yourservice"

    return None
```

### Step 4: Test

```bash
python test_providers.py
```

Should show your new provider in the list! ✓

## 🧪 Testing

### Run the Test Script

```bash
python test_providers.py
```

### Test Your Changes Manually

```bash
python main.py
```

## 📝 Code Style

- Use **type hints** (Python 3.12+ syntax)
- Keep functions **small and focused**
- **No comments needed** unless the WHY is non-obvious
- Use **snake_case** for functions/variables, **PascalCase** for classes
- Max line length: **100 characters** (soft limit, readability first)

## 🔄 Git Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Commit with clear messages: `git commit -m "feature: Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request on GitHub

### Commit Message Format

```
<type>: <subject>

<body (optional)>
```

Types: `feature`, `fix`, `docs`, `refactor`, `test`

Example:
```
feature: Add Anthropic Claude provider

Implements list_models and test_key for Claude API.
Uses OpenAI-compatible endpoints.
```

## 🚫 What NOT to Do

- ❌ Don't add external dependencies without discussing first
- ❌ Don't commit `.venv/` or `__pycache__/` (covered by .gitignore)
- ❌ Don't modify `tui.tcss` styling without discussion (keep it minimal)
- ❌ Don't remove type hints
- ❌ Don't add secrets or API keys to code

## ✅ Pull Request Checklist

Before submitting:

- [ ] Code follows project style (type hints, naming)
- [ ] All providers still work: `python test_providers.py` ✓
- [ ] App still runs: `python main.py` (no errors)
- [ ] Commit messages are clear
- [ ] No new dependencies added (unless discussed)
- [ ] README updated if adding features

## 📚 Resources

- [BaseProvider docs](../src/providers/base.py) — Interface you must implement
- [OpenAI Provider](../src/providers/openai_provider.py) — Full reference implementation
- [OpenAI-Compatible Mixin](../src/providers/openai_compat_mixin.py) — Reusable code
- [Textual Docs](https://textual.textualize.io/) — UI framework

## 🎯 Current Priorities

1. **Most Wanted**: Add Anthropic Claude, Cohere, Mistral providers
2. **Helpful**: Result persistence (SQLite/CSV export)
3. **Nice-to-Have**: Custom prompt templates, streaming output

## 💬 Questions?

Open an issue or discussion on GitHub!

---

Thank you for contributing! 🙏
