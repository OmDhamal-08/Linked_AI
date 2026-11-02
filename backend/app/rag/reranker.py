"""Reranker interface. The MVP uses a no-op; a cross-encoder or LLM reranker can be
added later without changing the retriever."""

from abc import ABC, abstractmethod
from typing import Any


class Reranker(ABC):
    name: str = "base"

    @abstractmethod
    def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return candidates in the new order. Each candidate carries a 'score' key."""


class NoopReranker(Reranker):
    name = "none"

    def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(candidates, key=lambda c: c["score"], reverse=True)
