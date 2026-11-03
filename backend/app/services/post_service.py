"""Post history: list, read, edit and delete the current user's saved posts."""

from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.post import Post
from app.models.user import User
from app.repositories.post_repository import PostRepository
from app.schemas.posts import PostUpdate


class PostService:
    def __init__(self, posts: PostRepository) -> None:
        self._posts = posts

    def list_posts(self, session: Session, user: User, *, limit: int, offset: int, post_type: str | None, category: str | None) -> dict[str, Any]:
        rows, total = self._posts.list_for_user(
            session, user.id, limit=limit, offset=offset, post_type=post_type, category=category
        )
        return {"items": [self.serialize(p) for p in rows], "total": total, "limit": limit, "offset": offset}

    def get_post(self, session: Session, user: User, post_id: str) -> dict[str, Any]:
        post = self._posts.get_for_user(session, user.id, post_id)
        if not post:
            raise NotFoundError()
        return self.serialize(post)

    def update_post(self, session: Session, user: User, post_id: str, req: PostUpdate) -> dict[str, Any]:
        post = self._posts.get_for_user(session, user.id, post_id)
        if not post:
            raise NotFoundError()
        changes: dict[str, Any] = {}
        if req.output_text is not None:
            changes["output_text"] = req.output_text.strip()
        if req.hashtags is not None:
            changes["hashtags"] = req.hashtags
        post = self._posts.update(session, post, changes)
        return self.serialize(post)

    def delete_post(self, session: Session, user: User, post_id: str) -> None:
        post = self._posts.get_for_user(session, user.id, post_id)
        if not post:
            raise NotFoundError()
        self._posts.delete(session, post)

    def serialize(self, post: Post) -> dict[str, Any]:
        analysis = post.analysis
        return {
            "id": post.id,
            "type": post.type,
            "input_text": post.input_text,
            "output_text": post.output_text,
            "category": post.category,
            "topic": post.topic,
            "tone": post.tone,
            "keywords_used": post.keywords_used or [],
            "hashtags": post.hashtags or [],
            "score": post.score,
            "suggestions": post.suggestions or [],
            "analysis": None if analysis is None else {
                "emotion": analysis.emotion,
                "hook_type": analysis.hook_type,
                "structure": analysis.structure,
                "readability_score": analysis.readability_score,
                "hook_score": analysis.hook_score,
                "keyword_score": analysis.keyword_score,
                "overall_score": analysis.overall_score,
            },
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
        }
