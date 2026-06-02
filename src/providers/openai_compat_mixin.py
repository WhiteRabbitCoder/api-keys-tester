"""Mixin for providers that use OpenAI-compatible APIs."""

import time
import httpx
from .base import BaseProvider, ModelInfo, TestResult, ProviderError, _handle_http_error, _handle_request_error


class OpenAICompatMixin(BaseProvider):
    """Mixin for providers that follow OpenAI's API schema."""

    BASE_URL: str = None

    def _auth_header(self, api_key: str) -> str:
        """Return the Authorization header value for this provider."""
        return f"Bearer {api_key}"

    async def list_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch available models from an OpenAI-compatible endpoint."""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/v1/models"
            headers = {"Authorization": self._auth_header(api_key)}
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
            except httpx.RequestError as e:
                raise _handle_request_error(e)
            _handle_http_error(response)

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
            url = f"{self.BASE_URL}/v1/chat/completions"
            headers = {"Authorization": self._auth_header(api_key)}
            try:
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
            except httpx.RequestError as e:
                latency_ms = (time.time() - start_time) * 1000
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=str(_handle_request_error(e)),
                    model_id=model_id,
                    provider=self.name,
                )

            latency_ms = (time.time() - start_time) * 1000

            try:
                _handle_http_error(response)
            except ProviderError as e:
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=str(e),
                    model_id=model_id,
                    provider=self.name,
                )

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
