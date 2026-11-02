from datetime import datetime
"""Knowledge base models.

IMPORTANT: knowledge_items stores DERIVED content intelligence and an embedding,
never the full third-party source text. Only the content hash is kept for dedupe.
"""

from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base, timestamp_column
from app.db.types import EmbeddingType
from app.models.user import new_id


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    category: Mapped[str] = mapped_column(String(60), index=True)
    topic: Mapped[str] = mapped_column(String(200))
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    hook_type: Mapped[str] = mapped_column(String(40), index=True)
    hook_pattern: Mapped[str] = mapped_column(String(200))
    tone: Mapped[str] = mapped_column(String(40), index=True)
    emotion: Mapped[str] = mapped_column(String(40))
    structure: Mapped[list[str]] = mapped_column(JSON, default=list)
    cta_type: Mapped[str] = mapped_column(String(40))
    hashtag_concepts: Mapped[list[str]] = mapped_column(JSON, default=list)
    audience: Mapped[str] = mapped_column(String(120), index=True)
    source_type: Mapped[str] = mapped_column(String(40), default="manual")
    source_reference: Mapped[str] = mapped_column(String(255), default="")
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        EmbeddingType(dim=get_settings().embedding_dim), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = timestamp_column()
    updated_at: Mapped[datetime] = timestamp_column()


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String(255), default="")
    source_type: Mapped[str] = mapped_column(String(40), default="upload")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | completed | failed
    records_uploaded: Mapped[int] = mapped_column(Integer, default=0)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_generated: Mapped[int] = mapped_column(Integer, default=0)
    pii_redacted: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = timestamp_column()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
