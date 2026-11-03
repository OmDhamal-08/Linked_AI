"""Initial schema: users, posts, post_analysis, usage_logs, subscriptions, knowledge_items, ingestion_jobs.

On PostgreSQL the pgvector extension is enabled and knowledge_items.embedding is vector(EMBEDDING_DIM).
On other dialects the embedding is stored as JSON.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-02
"""

import os
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _embedding_type(dialect: str):
    if dialect == "postgresql":
        return Vector(int(os.getenv("EMBEDDING_DIM", "384")))
    return sa.JSON()


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(120), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("password_hash", sa.String(300), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "posts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("category", sa.String(60), nullable=True),
        sa.Column("topic", sa.String(200), nullable=True),
        sa.Column("tone", sa.String(40), nullable=True),
        sa.Column("input_payload", sa.JSON(), nullable=True),
        sa.Column("keywords_used", sa.JSON(), nullable=True),
        sa.Column("hashtags", sa.JSON(), nullable=True),
        sa.Column("score", sa.JSON(), nullable=True),
        sa.Column("suggestions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_posts_user_id", "posts", ["user_id"])

    op.create_table(
        "post_analysis",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("post_id", sa.String(36), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(60), nullable=True),
        sa.Column("topic", sa.String(200), nullable=True),
        sa.Column("tone", sa.String(40), nullable=True),
        sa.Column("emotion", sa.String(40), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("hook_type", sa.String(40), nullable=True),
        sa.Column("structure", sa.JSON(), nullable=True),
        sa.Column("readability_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("hook_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("keyword_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_post_analysis_post_id", "post_analysis", ["post_id"])

    op.create_table(
        "usage_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature", sa.String(40), nullable=False),
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="success"),
        sa.Column("provider", sa.String(40), nullable=True),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("error_code", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"])
    op.create_index("ix_usage_logs_feature", "usage_logs", ["feature"])
    op.create_index("ix_usage_logs_request_date", "usage_logs", ["request_date"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("provider", sa.String(40), nullable=False, server_default="mock"),
        sa.Column("external_subscription_id", sa.String(120), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("hook_type", sa.String(40), nullable=False),
        sa.Column("hook_pattern", sa.String(200), nullable=False),
        sa.Column("tone", sa.String(40), nullable=False),
        sa.Column("emotion", sa.String(40), nullable=False),
        sa.Column("structure", sa.JSON(), nullable=True),
        sa.Column("cta_type", sa.String(40), nullable=False),
        sa.Column("hashtag_concepts", sa.JSON(), nullable=True),
        sa.Column("audience", sa.String(120), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("source_reference", sa.String(255), nullable=False, server_default=""),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", _embedding_type(dialect), nullable=True),
        sa.Column("embedding_model", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("content_hash", name="uq_knowledge_items_content_hash"),
    )
    for column in ("category", "hook_type", "tone", "audience", "is_active"):
        op.create_index(f"ix_knowledge_items_{column}", "knowledge_items", [column])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False, server_default=""),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="upload"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("records_uploaded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embeddings_generated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pii_redacted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    for table in (
        "ingestion_jobs",
        "knowledge_items",
        "subscriptions",
        "usage_logs",
        "post_analysis",
        "posts",
        "users",
    ):
        op.drop_table(table)
