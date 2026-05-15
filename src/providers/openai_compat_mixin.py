"""Mixin for providers that use OpenAI-compatible APIs."""

import time
import httpx
from .base import BaseProvider, ModelInfo, TestResult, ProviderError


class OpenAICompatMixin(BaseProvider):
    """Mixin for providers that follow OpenAI's API schema."""

    BASE_URL: str = None

    def _auth_header(self, api_key: str) -> str:
        """Return the Authorization header value for this provider."""
        return f"Bearer {api_key}"

    async def list_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch available models from an OpenAI-compatible endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.BASE_URL}/v1/models"
                headers = {"Authorization": self._auth_header(api_key)}
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ProviderError("Invalid API key", status_code=401)
                raise ProviderError(f"API error: {e.response.status_code}", status_code=e.response.status_code)
            except httpx.TimeoutException:
                raise ProviderError("Request timeout")
            except httpx.RequestError as e:
                raise ProviderError(f"Request failed: {e}")

            data = response.json()
            models = []
            for item in data.get("data", []):
                try:
                    model_id = item.get("id")
                    if model_id:
                        models.append(
                            ModelInfo(
                                id=model_id,
                                name=model_id,
                                owned_by=item.get("owned_by"),
                            )
                        )
                except Exception:
                    continue

            return sorted(models, key=lambda m: m.id)

    async def test_key(self, api_key: str, model_id: str) -> TestResult:
        """Test the API key with a simple completion request."""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            try:
                url = f"{self.BASE_URL}/v1/chat/completions"
                headers = {"Authorization": self._auth_header(api_key)}
                response = await client.post(
                    url,
                    headers=headers,
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": "Say hello in one word."}],
                        "max_tokens": 10,
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
            except (httpx.TimeoutException, httpx.RequestError) as e:
                latency_ms = (time.time() - start_time) * 1000
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=f"Request failed: {e}",
                    model_id=model_id,
                    provider=self.name,
                )

            latency_ms = (time.time() - start_time) * 1000

            try:
                data = response.json()
                response_text = data["choices"][0]["message"]["content"]
                return TestResult(
                    success=True,
                    response_text=response_text,
                    latency_ms=latency_ms,
                    error_message=None,
                    model_id=model_id,
                    provider=self.name,
                )
            except (KeyError, IndexError, ValueError) as e:
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=f"Failed to parse response: {e}",
                    model_id=model_id,
                    provider=self.name,
                )
