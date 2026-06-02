"""OpenAI API provider integration."""

import time
from typing import Optional
import httpx
from pydantic import BaseModel, Field
from .base import BaseProvider, ModelInfo, TestResult, ProviderError, _handle_http_error, _handle_request_error


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
            except httpx.RequestError as e:
                raise _handle_request_error(e)
            _handle_http_error(response)

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
