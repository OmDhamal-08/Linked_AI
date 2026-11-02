"""Local, dependency-free embedding provider (feature hashing over unigrams and bigrams).

It is deterministic and needs no API key, so development and tests always work.
Quality is lexical rather than semantic: swap in the OpenAI provider for
production-grade semantic search.
"""

import hashlib
import math
import re

from app.embeddings.base import EmbeddingProvider

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.]*")


def _features(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    grams = list(tokens)
    grams.extend(f"{a} {b}" for a, b in zip(tokens, tokens[1:]))
    return grams


class HashingEmbeddingProvider(EmbeddingProvider):
    name = "hashing"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim
        self.model = f"hashing-{dim}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for feature in _features(text):
            digest = hashlib.md5(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]
