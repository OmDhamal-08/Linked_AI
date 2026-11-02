from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.knowledge import IngestionJob, KnowledgeItem


class KnowledgeRepository:
    def hash_exists(self, session: Session, content_hash: str) -> bool:
        return session.scalar(select(KnowledgeItem.id).where(KnowledgeItem.content_hash == content_hash).limit(1)) is not None

    def add_many(self, session: Session, items: list[KnowledgeItem]) -> None:
        session.add_all(items)
        session.commit()

    def get(self, session: Session, item_id: str) -> KnowledgeItem | None:
        return session.get(KnowledgeItem, item_id)

    def delete(self, session: Session, item: KnowledgeItem) -> None:
        session.delete(item)
        session.commit()

    def list(
        self, session: Session, *, category: str | None, limit: int, offset: int
    ) -> tuple[list[KnowledgeItem], int]:
        base = select(KnowledgeItem)
        if category:
            base = base.where(KnowledgeItem.category == category)
        total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = session.scalars(base.order_by(KnowledgeItem.created_at.desc()).limit(limit).offset(offset)).all()
        return list(rows), int(total)

    def stats(self, session: Session) -> dict[str, Any]:
        total = session.scalar(select(func.count()).select_from(KnowledgeItem)) or 0
        by_category = session.execute(
            select(KnowledgeItem.category, func.count()).group_by(KnowledgeItem.category)
        ).all()
        return {"total": int(total), "by_category": {c: int(n) for c, n in by_category}}


class IngestionJobRepository:
    def create(self, session: Session, **fields) -> IngestionJob:
        job = IngestionJob(**fields)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    def update(self, session: Session, job: IngestionJob, changes: dict[str, Any]) -> IngestionJob:
        for key, value in changes.items():
            setattr(job, key, value)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    def list_recent(self, session: Session, limit: int = 20) -> list[IngestionJob]:
        return list(session.scalars(select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)).all())
