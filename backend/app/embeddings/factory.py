import logging

from app.core.config import Settings
from app.core.logging import get_logger, log_event
from app.embeddings.base import EmbeddingProvider
from app.embeddings.hashing_provider import HashingEmbeddingProvider
from app.embeddings.openai_provider import OpenAIEmbeddingProvider

logger = get_logger(__name__)


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    name = settings.embedding_provider
    if name == "openai":
        if not settings.embedding_api_key:
            log_event(logger, logging.WARNING, "embedding_missing_key", fallback="hashing")
            return HashingEmbeddingProvider(settings.embedding_dim)
        return OpenAIEmbeddingProvider(
            settings.embedding_api_key,
            settings.embedding_model,
            settings.embedding_dim,
            base_url=settings.embedding_base_url,
            timeout=settings.ai_timeout_seconds,
        )
    return HashingEmbeddingProvider(settings.embedding_dim)
