"""Anthropic Messages API adapter (REST via httpx; no SDK required)."""

import time

import httpx

from app.ai.base import AIProvider, AIRequest, AIResult, ProviderError, estimate_tokens

DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
API_VERSION = "2023-06-01"


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, *, base_url: str = "", timeout: float = 30.0) -> None:
        self._api_key = api_key
        self.model = model
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    def complete(self, request: AIRequest) -> AIResult:
        payload = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": request.user_prompt}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        started = time.perf_counter()
        try:
            response = httpx.post(f"{self._base_url}/messages", json=payload, headers=headers, timeout=self._timeout)
        except httpx.TimeoutException as exc:
            raise ProviderError("anthropic timeout") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"anthropic network error: {type(exc).__name__}") from exc

        if response.status_code >= 400:
            retryable = response.status_code in (408, 409, 429) or response.status_code >= 500
            raise ProviderError(f"anthropic http {response.status_code}", retryable=retryable)

        data = response.json()
        try:
            text = "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise ProviderError("anthropic returned an unexpected payload", retryable=False) from exc

        usage = data.get("usage") or {}
        return AIResult(
            text=text.strip(),
            provider=self.name,
            model=self.model,
            input_tokens=int(usage.get("input_tokens") or estimate_tokens(request.user_prompt)),
            output_tokens=int(usage.get("output_tokens") or estimate_tokens(text)),
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
