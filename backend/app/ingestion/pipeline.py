"""Ingestion pipeline:

Raw rows -> validation -> cleaning -> PII check -> dedupe -> content analysis
-> metadata generation -> embedding -> vector storage.

Only derived metadata and the embedding are stored. The source text is discarded
after embedding, so third-party wording is never kept in the knowledge base.
"""

import logging
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger, log_event
from app.core.taxonomy import get_taxonomy
from app.ingestion.cleaner import content_hash
from app.ingestion.pii import detect_and_redact
from app.ingestion.validator import validate_record
from app.models.knowledge import KnowledgeItem
from app.nlp.analysis import (
    detect_category,
    detect_cta,
    detect_emotion,
    detect_hook_type,
    detect_structure,
    detect_tone,
    extract_keywords,
    first_line,
    hashtag_concepts,
)
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.embedding_service import EmbeddingService

logger = get_logger(__name__)
FALLBACK_CATEGORY = "Career"


class IngestionPipeline:
    def __init__(
        self,
        *,
        embeddings: EmbeddingService,
        repo: KnowledgeRepository,
        settings: Settings,
    ) -> None:
        self._embeddings = embeddings
        self._repo = repo
        self._settings = settings

    def run(self, session: Session, rows: list[dict[str, Any]], *, source_type: str, source_reference: str) -> dict[str, Any]:
        counts: Counter[str] = Counter()
        errors: list[dict[str, Any]] = []
        pending: list[tuple[dict[str, Any], str, str]] = []
        seen: set[str] = set()
        action = self._settings.ingestion_pii_action

        for index, row in enumerate(rows, start=1):
            record, reason = validate_record(row)
            if reason:
                counts["rejected"] += 1
                errors.append({"row": index, "reason": reason})
                continue

            text, pii_found = detect_and_redact(record["text"])
            if pii_found and action == "reject":
                counts["rejected"] += 1
                errors.append({"row": index, "reason": "pii_detected", "types": pii_found})
                continue
            if pii_found:
                counts["pii_redacted"] += 1

            digest = content_hash(text)
            if digest in seen or self._repo.hash_exists(session, digest):
                counts["duplicates"] += 1
                continue
            seen.add(digest)

            metadata = self._derive(text, record)
            pending.append((metadata, digest, text))

        if pending:
            vectors = self._embeddings.embed_documents([text for _, _, text in pending])
        else:
            vectors = []

        items = []
        for (metadata, digest, _text), vector in zip(pending, vectors):
            items.append(
                KnowledgeItem(
                    **metadata,
                    content_hash=digest,
                    embedding=vector,
                    embedding_model=self._embeddings.model,
                    source_type=source_type,
                    source_reference=source_reference[:255],
                )
            )
        if items:
            self._repo.add_many(session, items)

        log_event(logger, logging.INFO, "ingestion_completed", processed=len(items), rejected=counts["rejected"], duplicates=counts["duplicates"])
        return {
            "records_processed": len(items),
            "records_rejected": counts["rejected"],
            "duplicates": counts["duplicates"],
            "embeddings_generated": len(vectors),
            "pii_redacted": counts["pii_redacted"],
            "errors": errors[:50],
        }

    def _derive(self, text: str, record: dict[str, Any]) -> dict[str, Any]:
        taxonomy = get_taxonomy()
        detected_category, _ = detect_category(text)
        category = record.get("category") or detected_category or FALLBACK_CATEGORY

        extracted_keywords = extract_keywords(text, limit=8)
        keywords = list(dict.fromkeys([k.lower() for k in record.get("keywords") or []] + extracted_keywords))[:10]
        topic = record.get("topic") or (keywords[0].title() if keywords else category)
        tone = record.get("tone") or detect_tone(text)
        hook_type = record.get("hook_type") or detect_hook_type(first_line(text))
        structure = record.get("structure") or detect_structure(text)
        cta_type = record.get("cta_type") or detect_cta(text)
        tags = record.get("hashtags") or hashtag_concepts(text, keywords)
        audience = record.get("audience") or "general audience"
        emotion = detect_emotion(text)

        hook_pattern = f"{hook_type}_{structure[1]}" if len(structure) > 1 else hook_type
        return {
            "category": category,
            "topic": topic[:200],
            "keywords": keywords,
            "hook_type": hook_type,
            "hook_pattern": hook_pattern[:200],
            "tone": tone,
            "emotion": emotion,
            "structure": structure,
            "cta_type": cta_type if cta_type in taxonomy["cta_types"] else "none",
            "hashtag_concepts": tags[:5],
            "audience": audience[:120],
        }
