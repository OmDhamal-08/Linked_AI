"""Builds AI providers from configuration. Missing credentials fall back to the mock provider with a warning."""

from app.ai.anthropic_provider import AnthropicProvider
from app.ai.base import AIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.core.config import Settings
from app.core.logging import get_logger, log_event
import logging

logger = get_logger(__name__)


def build_provider(name: str, *, api_key: str, model: str, base_url: str, timeout: float) -> AIProvider:
    name = (name or "mock").lower()
    if name == "mock":
        return MockAIProvider(model=model or "mock-linkdine-v1")
    if name in ("openai", "anthropic") and not api_key:
        log_event(logger, logging.WARNING, "ai_provider_missing_key", provider=name, fallback="mock")
        return MockAIProvider()
    if name == "openai":
        return OpenAIProvider(api_key, model or "gpt-4o-mini", base_url=base_url, timeout=timeout)
    if name == "anthropic":
        return AnthropicProvider(api_key, model or "claude-haiku-5-5", base_url=base_url, timeout=timeout)
    raise ValueError(f"Unsupported AI provider: {name}")


def build_primary_provider(settings: Settings) -> AIProvider:
    return build_provider(
        settings.ai_provider,
        api_key=settings.ai_api_key,
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        timeout=settings.ai_timeout_seconds,
    )


def build_fallback_provider(settings: Settings) -> AIProvider | None:
    if not settings.ai_fallback_provider:
        return None
    return build_provider(
        settings.ai_fallback_provider,
        api_key=settings.ai_fallback_api_key,
        model=settings.ai_fallback_model,
        base_url="",
        timeout=settings.ai_timeout_seconds,
    )
