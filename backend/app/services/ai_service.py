"""AI orchestrator: primary provider, optional fallback, uniform errors and logging."""

import logging
import time

from app.ai.base import AIProvider, AIRequest, AIResult, ProviderError
from app.core.errors import AIUnavailableError
from app.core.logging import get_logger, log_event

logger = get_logger(__name__)


class AIService:
    def __init__(self, primary: AIProvider, fallback: AIProvider | None = None) -> None:
        self.primary = primary
        self.fallback = fallback

    def complete(self, request: AIRequest) -> AIResult:
        started = time.perf_counter()
        try:
            result = self.primary.complete(request)
            self._log_success(result, request, started)
            return result
        except ProviderError as exc:
            log_event(
                logger,
                logging.WARNING,
                "ai_primary_failed",
                provider=self.primary.name,
                task=request.task,
                error=str(exc),
                fallback_available=self.fallback is not None,
            )
            if self.fallback is None:
                raise AIUnavailableError() from exc

        try:
            result = self.fallback.complete(request)
            self._log_success(result, request, started, fallback=True)
            return result
        except ProviderError as exc:
            log_event(logger, logging.ERROR, "ai_fallback_failed", provider=self.fallback.name, error=str(exc))
            raise AIUnavailableError() from exc

    @staticmethod
    def _log_success(result: AIResult, request: AIRequest, started: float, fallback: bool = False) -> None:
        log_event(
            logger,
            logging.INFO,
            "ai_completion",
            provider=result.provider,
            model=result.model,
            task=request.task,
            tokens_in=result.input_tokens,
            tokens_out=result.output_tokens,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            fallback=fallback,
        )
