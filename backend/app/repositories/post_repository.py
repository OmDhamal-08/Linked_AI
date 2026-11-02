from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post import Post, PostAnalysis


class PostRepository:
    def create(self, session: Session, post: Post, analysis: PostAnalysis | None = None) -> Post:
        session.add(post)
        session.flush()
        if analysis is not None:
            analysis.post_id = post.id
            session.add(analysis)
        session.commit()
        session.refresh(post)
        return post

    def get_for_user(self, session: Session, user_id: str, post_id: str) -> Post | None:
        return session.scalar(select(Post).where(Post.id == post_id, Post.user_id == user_id))

    def list_for_user(
        self,
        session: Session,
        user_id: str,
        *,
        limit: int,
        offset: int,
        post_type: str | None = None,
        category: str | None = None,
    ) -> tuple[list[Post], int]:
        base = select(Post).where(Post.user_id == user_id)
        if post_type:
            base = base.where(Post.type == post_type)
        if category:
            base = base.where(Post.category == category)
        total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = session.scalars(base.order_by(Post.created_at.desc()).limit(limit).offset(offset)).all()
        return list(rows), int(total)

    def update(self, session: Session, post: Post, changes: dict[str, Any]) -> Post:
        for key, value in changes.items():
            setattr(post, key, value)
        session.add(post)
        session.commit()
        session.refresh(post)
        return post

    def delete(self, session: Session, post: Post) -> None:
        session.delete(post)
        session.commit()

    def recent_scores(self, session: Session, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = session.scalars(
            select(Post).where(Post.user_id == user_id, Post.score.is_not(None)).order_by(Post.created_at.desc()).limit(limit)
        ).all()
        return [p.score for p in rows if p.score]
