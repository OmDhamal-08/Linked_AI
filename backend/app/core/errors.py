"""Application error types. Every error returned to clients is friendly and
carries a machine-readable code; technical details stay in server logs."""

from typing import Any


class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"
    message: str = "Something went wrong. Please try again."

    def __init__(self, message: str | None = None, *, details: Any = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details


class InvalidRequestError(AppError):
    status_code = 400
    code = "invalid_request"
    message = "The request could not be processed. Please check your input."


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Please log in to continue."


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have permission to do that."


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "We could not find what you were looking for."


class SubscriptionRequiredError(AppError):
    status_code = 403
    code = "subscription_required"
    message = "This feature is available on the Premium plan."


class UsageLimitError(AppError):
    status_code = 429
    code = "usage_limit_reached"
    message = "You have reached today's limit for this feature. It resets at midnight UTC."


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
    message = "Too many requests. Please wait a moment and try again."


class AIUnavailableError(AppError):
    status_code = 503
    code = "ai_provider_unavailable"
    message = "The AI service is busy right now. Please try again in a moment."


class EmbeddingError(AppError):
    status_code = 503
    code = "embedding_failure"
    message = "We could not analyse your content right now. Please try again."


class VectorStoreError(AppError):
    status_code = 503
    code = "vector_database_failure"
    message = "Our content library is temporarily unavailable. Please try again."


class TimeoutAppError(AppError):
    status_code = 504
    code = "timeout"
    message = "The request took too long. Please try again."


class GenerationFailedError(AppError):
    status_code = 502
    code = "generation_failed"
    message = "We could not produce a clean draft this time. Please try again or adjust your input."


class IngestionError(AppError):
    status_code = 400
    code = "ingestion_failed"
    message = "The dataset could not be ingested. Check the file format and try again."
