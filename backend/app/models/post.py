from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, timestamp_column
from app.models.user import new_id


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # generate | enhance
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    input_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    keywords_used: Mapped[list[str]] = mapped_column(JSON, default=list)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    score: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = timestamp_column()
    updated_at: Mapped[datetime] = timestamp_column()

    analysis: Mapped["PostAnalysis | None"] = relationship(
        back_populates="post", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class PostAnalysis(Base):
    __tablename__ = "post_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(40), nullable=True)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    hook_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    structure: Mapped[list[str]] = mapped_column(JSON, default=list)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)
    hook_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = timestamp_column()

    post: Mapped[Post] = relationship(back_populates="analysis")
