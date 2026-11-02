"""Hybrid retriever: semantic similarity + metadata filtering + keyword matching, then top-K.

Pipeline:
1. Vector search with metadata filters (over-fetch K * multiplier candidates).
2. If too few candidates, relax the filters and merge (never return nothing when data exists).
3. Re-score each candidate with weighted vector, keyword, and metadata signals.
4. Rerank (pluggable) and keep the top K.
"""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.knowledge import KnowledgeItem
from app.rag.query_builder import AnalyzedQuery
from app.rag.reranker import NoopReranker, Reranker
from app.rag.vector_store import Candidate, VectorStore
from app.services.embedding_service import EmbeddingService


@dataclass
class RetrievalResult:
    items: list[dict[str, Any]] = field(default_factory=list)
    filters_used: dict[str, Any] = field(default_factory=dict)
    relaxed: bool = False
    candidates_considered: int = 0

    @property
    def count(self) -> int:
        return len(self.items)


def _item_view(item: KnowledgeItem, score: float, vector_score: float) -> dict[str, Any]:
    # Only derived metadata is returned. Source text is never stored, so it cannot leak.
    return {
        "id": item.id,
        "category": item.category,
        "topic": item.topic,
        "keywords": list(item.keywords or []),
        "hook_type": item.hook_type,
        "hook_pattern": item.hook_pattern,
        "tone": item.tone,
        "emotion": item.emotion,
        "structure": list(item.structure or []),
        "cta_type": item.cta_type,
        "hashtag_concepts": list(item.hashtag_concepts or []),
        "audience": item.audience,
        "score": round(score, 4),
        "vector_score": round(vector_score, 4),
    }


def keyword_overlap(query_keywords: list[str], item_keywords: list[str], topic: str) -> float:
    if not query_keywords:
        return 0.0
    item_terms = {k.lower() for k in item_keywords} | {w for w in topic.lower().split()}
    hits = 0
    for q in query_keywords:
        q = q.lower()
        if q in item_terms or any(q in term or term in q for term in item_terms if len(term) > 3):
            hits += 1
    return hits / len(query_keywords)


class Retriever:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        settings: Settings,
        reranker: Reranker | None = None,
    ) -> None:
        self._store = vector_store
        self._embeddings = embedding_service
        self._settings = settings
        self._reranker = reranker or NoopReranker()

    def retrieve(self, session: Session, query: AnalyzedQuery, *, top_k: int | None = None) -> RetrievalResult:
        k = top_k or self._settings.rag_top_k
        fetch_k = max(k, k * self._settings.rag_candidate_multiplier)
        query_vector = self._embeddings.embed_query(query.semantic_query)

        strict_filters = query.metadata_filters
        candidates: dict[str, Candidate] = {}
        for c in self._store.search_similar(session, query_vector, k=fetch_k, filters=strict_filters):
            candidates[c.item.id] = c

        relaxed = False
        if len(candidates) < k and any(strict_filters.values()):
            relaxed = True
            for c in self._store.search_similar(session, query_vector, k=fetch_k, filters=None):
                candidates.setdefault(c.item.id, c)

        w_v = self._settings.rag_weight_vector
        w_k = self._settings.rag_weight_keyword
        w_m = self._settings.rag_weight_metadata
        scored: list[dict[str, Any]] = []
        for c in candidates.values():
            item = c.item
            kw = keyword_overlap(query.keywords, list(item.keywords or []), item.topic)
            meta = 0.0
            meta += 1.0 if query.knowledge_category and item.category == query.knowledge_category else 0.0
            meta += 1.0 if item.tone == query.tone else 0.0
            meta /= 2.0
            vector_component = max(0.0, c.vector_score)
            final = w_v * vector_component + w_k * kw + w_m * meta
            scored.append(_item_view(item, final, c.vector_score))

        ranked = self._reranker.rerank(query.semantic_query, scored)[:k]
        return RetrievalResult(
            items=ranked,
            filters_used={kk: vv for kk, vv in strict_filters.items() if vv},
            relaxed=relaxed,
            candidates_considered=len(candidates),
        )
