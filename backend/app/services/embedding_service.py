"""Embedding service: batching for documents, cached single-query embeddings."""

import logging
from collections import OrderedDict

from app.core.errors import EmbeddingError
from app.core.logging import get_logger, log_event
from app.embeddings.base import EmbeddingProvider

logger = get_logger(__name__)
BATCH_SIZE = 64


class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider, cache_size: int = 512) -> None:
        self._provider = provider
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_size = cache_size

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def model(self) -> str:
        return self._provider.model

    @property
    def dim(self) -> int:
        return self._provider.dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start : start + BATCH_SIZE]
            try:
                vectors.extend(self._provider.embed(batch))
            except Exception as exc:  # noqa: BLE001
                log_event(logger, logging.ERROR, "embedding_failed", provider=self.provider_name, error=type(exc).__name__)
                raise EmbeddingError() from exc
        return vectors

    def embed_query(self, text: str) -> list[float]:
        key = text.strip().lower()
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        try:
            vector = self._provider.embed([text])[0]
        except Exception as exc:  # noqa: BLE001
            log_event(logger, logging.ERROR, "embedding_failed", provider=self.provider_name, error=type(exc).__name__)
            raise EmbeddingError() from exc
        self._cache[key] = vector
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return vector
