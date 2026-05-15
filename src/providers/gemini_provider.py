"""Google Gemini API provider integration."""

import time
import httpx
from .base import BaseProvider, ModelInfo, TestResult, ProviderError


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini API."""

    name = "Google Gemini"
    key_prefixes = ["AIza"]

    async def list_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch available models from Google Gemini API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": api_key},
                    timeout=10.0,
                )
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
            for item in data.get("models", []):
                try:
                    model_id = item.get("name", "").replace("models/", "")
                    display_name = item.get("displayName", model_id)
                    if model_id:
                        models.append(
                            ModelInfo(
                                id=model_id,
                                name=display_name,
                            )
                        )
                except Exception:
                    continue

            return sorted(models, key=lambda m: m.id)

    async def test_key(self, api_key: str, model_id: str) -> TestResult:
        """Test the API key with a simple generation request."""
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent",
                    params={"key": api_key},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": "Say hello in one word."}
                                ]
                            }
                        ]
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
                response_text = data["candidates"][0]["content"]["parts"][0]["text"]
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
