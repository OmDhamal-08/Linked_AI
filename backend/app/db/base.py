from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def timestamp_column(**kwargs):
    return mapped_column(DateTime(timezone=True), default=utcnow, **kwargs)
