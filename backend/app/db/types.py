"""Portable embedding column type.

On PostgreSQL the column is a pgvector `vector(N)` (fast cosine search).
On other dialects (SQLite used for local dev and tests) it is a JSON list,
and similarity is computed in Python by the PythonVectorStore.
"""

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class EmbeddingType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int | None = None) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        return [float(x) for x in value]

    def process_result_value(self, value: Any, dialect):
        if value is None:
            return None
        return [float(x) for x in value]
