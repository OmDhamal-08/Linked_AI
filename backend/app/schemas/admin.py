from typing import Any

from pydantic import BaseModel, Field


class KnowledgeItemOut(BaseModel):
    id: str
    category: str
    topic: str
    keywords: list[str]
    hook_type: str
    hook_pattern: str
    tone: str
    emotion: str
    structure: list[str]
    cta_type: str
    hashtag_concepts: list[str]
    audience: str
    source_type: str
    source_reference: str
    embedding_model: str | None
    is_active: bool


class IngestionReport(BaseModel):
    job_id: str
    status: str
    records_uploaded: int = 0
    records_processed: int = 0
    records_rejected: int = 0
    duplicates: int = 0
    embeddings_generated: int = 0
    pii_redacted: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)
