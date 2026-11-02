"""RAG orchestration: analyzed query -> retrieval -> content intelligence."""

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.rag.intelligence import build_content_intelligence
from app.rag.query_builder import AnalyzedQuery
from app.rag.retriever import RetrievalResult, Retriever

logger = get_logger(__name__)


@dataclass
class RagOutcome:
    retrieval: RetrievalResult
    intelligence: dict[str, Any] = field(default_factory=dict)


class RagService:
    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    def retrieve(self, session: Session, query: AnalyzedQuery) -> RagOutcome:
        retrieval = self._retriever.retrieve(session, query)
        intelligence = build_content_intelligence(retrieval.items, query)
        log_event(
            logger,
            logging.INFO,
            "rag_retrieval",
            retrieval_count=retrieval.count,
            candidates=retrieval.candidates_considered,
            relaxed=retrieval.relaxed,
            category=query.knowledge_category or "none",
        )
        return RagOutcome(retrieval=retrieval, intelligence=intelligence)
