"""OpenAI API provider integration."""

import time
from typing import Optional
import httpx
from pydantic import BaseModel, Field
from .base import BaseProvider, ModelInfo, TestResult, ProviderError


class OpenAIModel(BaseModel):
    """OpenAI model response from /v1/models."""

    id: str
    object: str
    created: int
    owned_by: str


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI API."""

    name = "OpenAI"
    key_prefixes = ["sk-"]

    async def list_models(self, api_key: str) -> list[ModelInfo]:
        """Fetch available models from OpenAI API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
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
            for item in data.get("data", []):
                try:
                    model = OpenAIModel(**item)
                    models.append(
                        ModelInfo(
                            id=model.id,
                            name=model.id,
                            owned_by=model.owned_by,
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
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
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
