"""Admin knowledge-base operations: ingestion jobs, browsing and deleting records."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import IngestionError, NotFoundError
from app.core.logging import get_logger
from app.ingestion.loader import parse_upload
from app.ingestion.pipeline import IngestionPipeline
from app.models.knowledge import IngestionJob, KnowledgeItem
from app.repositories.knowledge_repository import IngestionJobRepository, KnowledgeRepository

logger = get_logger(__name__)


def _job_view(job: IngestionJob) -> dict[str, Any]:
    return {
        "job_id": job.id,
        "filename": job.filename,
        "source_type": job.source_type,
        "status": job.status,
        "records_uploaded": job.records_uploaded,
        "records_processed": job.records_processed,
        "records_rejected": job.records_rejected,
        "duplicates": job.duplicates,
        "embeddings_generated": job.embeddings_generated,
        "pii_redacted": job.pii_redacted,
        "errors": job.errors or [],
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


def item_view(item: KnowledgeItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "category": item.category,
        "topic": item.topic,
        "keywords": item.keywords,
        "hook_type": item.hook_type,
        "hook_pattern": item.hook_pattern,
        "tone": item.tone,
        "emotion": item.emotion,
        "structure": item.structure,
        "cta_type": item.cta_type,
        "hashtag_concepts": item.hashtag_concepts,
        "audience": item.audience,
        "source_type": item.source_type,
        "source_reference": item.source_reference,
        "embedding_model": item.embedding_model,
        "is_active": item.is_active,
    }


class KnowledgeService:
    def __init__(self, *, pipeline: IngestionPipeline, knowledge: KnowledgeRepository, jobs: IngestionJobRepository, max_rows: int) -> None:
        self._pipeline = pipeline
        self._knowledge = knowledge
        self._jobs = jobs
        self._max_rows = max_rows

    def ingest_upload(self, session: Session, *, filename: str, content: bytes, created_by: str | None) -> dict[str, Any]:
        job = self._jobs.create(
            session,
            filename=(filename or "upload")[:255],
            source_type="upload",
            status="processing",
            created_by=created_by,
        )
        try:
            source_type, rows = parse_upload(filename, content, self._max_rows)
            report = self._pipeline.run(session, rows, source_type=source_type, source_reference=filename)
        except IngestionError as exc:
            self._jobs.update(session, job, {"status": "failed", "error_message": exc.message, "completed_at": datetime.now(timezone.utc)})
            raise
        except Exception:  # noqa: BLE001 - log the detail, return a friendly error
            logger.exception("ingestion_unexpected_error", extra={"fields": {"job_id": job.id}})
            self._jobs.update(session, job, {"status": "failed", "error_message": "Unexpected error during ingestion.", "completed_at": datetime.now(timezone.utc)})
            raise IngestionError("The dataset could not be processed. Check the file and try again.")

        job = self._jobs.update(
            session,
            job,
            {
                "status": "completed",
                "source_type": source_type,
                "records_uploaded": len(rows),
                "records_processed": report["records_processed"],
                "records_rejected": report["records_rejected"],
                "duplicates": report["duplicates"],
                "embeddings_generated": report["embeddings_generated"],
                "pii_redacted": report["pii_redacted"],
                "errors": report["errors"],
                "completed_at": datetime.now(timezone.utc),
            },
        )
        return _job_view(job)

    def list_items(self, session: Session, *, category: str | None, limit: int, offset: int) -> dict[str, Any]:
        items, total = self._knowledge.list(session, category=category, limit=limit, offset=offset)
        return {"items": [item_view(i) for i in items], "total": total, "limit": limit, "offset": offset}

    def delete_item(self, session: Session, item_id: str) -> None:
        item = self._knowledge.get(session, item_id)
        if not item:
            raise NotFoundError()
        self._knowledge.delete(session, item)

    def stats(self, session: Session) -> dict[str, Any]:
        return self._knowledge.stats(session)

    def list_jobs(self, session: Session) -> list[dict[str, Any]]:
        return [_job_view(j) for j in self._jobs.list_recent(session)]
