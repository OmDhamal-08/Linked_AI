"""Vector storage abstraction.

VectorStore is the only interface the rest of the app uses. Two implementations:
- PgVectorStore: PostgreSQL + pgvector, cosine distance computed in SQL (production).
- PythonVectorStore: JSON embeddings on any database, cosine computed in Python (dev/tests).
Swap providers later (e.g. Pinecone) by writing another subclass.
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, select, text, update
from sqlalchemy.orm import Session

from app.core.errors import VectorStoreError
from app.core.logging import get_logger, log_event
from app.models.knowledge import KnowledgeItem

logger = get_logger(__name__)
FILTER_COLUMNS = {"category", "tone", "audience", "hook_type"}


@dataclass
class Candidate:
    item: KnowledgeItem
    vector_score: float  # cosine similarity in [-1, 1]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _active_filtered(session: Session, filters: dict[str, Any] | None):
    conditions = [KnowledgeItem.is_active.is_(True)]
    for column, value in (filters or {}).items():
        if value and column in FILTER_COLUMNS:
            conditions.append(getattr(KnowledgeItem, column) == value)
    return select(KnowledgeItem).where(and_(*conditions))


class VectorStore(ABC):
    name: str = "base"

    @abstractmethod
    def add_embedding(self, session: Session, item: KnowledgeItem, vector: list[float]) -> None: ...

    @abstractmethod
    def update_embedding(self, session: Session, item_id: str, vector: list[float]) -> None: ...

    @abstractmethod
    def delete_embedding(self, session: Session, item_id: str) -> None: ...

    @abstractmethod
    def search_similar(
        self, session: Session, query_vector: list[float], *, k: int, filters: dict[str, Any] | None = None
    ) -> list[Candidate]: ...


class PythonVectorStore(VectorStore):
    name = "python"

    def add_embedding(self, session: Session, item: KnowledgeItem, vector: list[float]) -> None:
        item.embedding = vector
        session.add(item)

    def update_embedding(self, session: Session, item_id: str, vector: list[float]) -> None:
        session.execute(update(KnowledgeItem).where(KnowledgeItem.id == item_id).values(embedding=vector))

    def delete_embedding(self, session: Session, item_id: str) -> None:
        session.execute(update(KnowledgeItem).where(KnowledgeItem.id == item_id).values(embedding=None, is_active=False))

    def search_similar(
        self, session: Session, query_vector: list[float], *, k: int, filters: dict[str, Any] | None = None
    ) -> list[Candidate]:
        try:
            items = session.scalars(_active_filtered(session, filters)).all()
            scored = [
                Candidate(item=i, vector_score=_cosine(query_vector, i.embedding))
                for i in items
                if i.embedding
            ]
        except Exception as exc:  # noqa: BLE001
            log_event(logger, 40, "vector_search_failed", store=self.name, error=type(exc).__name__)
            raise VectorStoreError() from exc
        scored.sort(key=lambda c: c.vector_score, reverse=True)
        return scored[:k]


class PgVectorStore(VectorStore):
    """Uses pgvector's cosine distance operator (<=>) inside PostgreSQL."""

    name = "pgvector"

    @staticmethod
    def _literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{float(x):.8f}" for x in vector) + "]"

    def add_embedding(self, session: Session, item: KnowledgeItem, vector: list[float]) -> None:
        item.embedding = vector
        session.add(item)

    def update_embedding(self, session: Session, item_id: str, vector: list[float]) -> None:
        session.execute(update(KnowledgeItem).where(KnowledgeItem.id == item_id).values(embedding=vector))

    def delete_embedding(self, session: Session, item_id: str) -> None:
        session.execute(update(KnowledgeItem).where(KnowledgeItem.id == item_id).values(embedding=None, is_active=False))

    def search_similar(
        self, session: Session, query_vector: list[float], *, k: int, filters: dict[str, Any] | None = None
    ) -> list[Candidate]:
        clauses = ["is_active = TRUE", "embedding IS NOT NULL"]
        params: dict[str, Any] = {"qvec": self._literal(query_vector), "k": k}
        for column, value in (filters or {}).items():
            if value and column in FILTER_COLUMNS:
                clauses.append(f"{column} = :f_{column}")
                params[f"f_{column}"] = value
        where = " AND ".join(clauses)
        sql = text(
            f"""
            SELECT id, 1 - (embedding <=> CAST(:qvec AS vector)) AS score
            FROM knowledge_items
            WHERE {where}
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :k
            """
        )
        try:
            rows = session.execute(sql, params).all()
            if not rows:
                return []
            ids = [r.id for r in rows]
            items = {i.id: i for i in session.scalars(select(KnowledgeItem).where(KnowledgeItem.id.in_(ids)))}
        except Exception as exc:  # noqa: BLE001
            log_event(logger, 40, "vector_search_failed", store=self.name, error=type(exc).__name__)
            raise VectorStoreError() from exc
        return [Candidate(item=items[r.id], vector_score=float(r.score)) for r in rows if r.id in items]


def build_vector_store(mode: str, dialect_name: str) -> VectorStore:
    if mode == "pgvector" or (mode == "auto" and dialect_name == "postgresql"):
        return PgVectorStore()
    return PythonVectorStore()
