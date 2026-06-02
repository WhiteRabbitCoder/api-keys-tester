"""Google Gemini API provider integration."""

import time
import httpx
from .base import BaseProvider, ModelInfo, TestResult, ProviderError, _handle_http_error, _handle_request_error


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
            except httpx.RequestError as e:
                raise _handle_request_error(e)
            _handle_http_error(response)

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

            data = response.json()

            # Check for prompt-level safety block
            prompt_feedback = data.get("promptFeedback", {})
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message=f"Prompt blocked by Gemini safety filter: {block_reason}",
                    model_id=model_id,
                    provider=self.name,
                )

            candidates = data.get("candidates", [])
            if not candidates:
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message="No response candidates returned — possible safety filter block",
                    model_id=model_id,
                    provider=self.name,
                )

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "")
            if finish_reason == "SAFETY":
                return TestResult(
                    success=False,
                    response_text=None,
                    latency_ms=latency_ms,
                    error_message="Response blocked by Gemini safety filter",
                    model_id=model_id,
                    provider=self.name,
                )

            try:
                response_text = candidate["content"]["parts"][0]["text"]
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
                    error_message=f"Empty response — the model returned no content ({e})",
                    model_id=model_id,
                    provider=self.name,
                )
