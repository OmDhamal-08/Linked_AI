"""OpenAI embeddings adapter (REST via httpx)."""

import httpx

from app.embeddings.base import EmbeddingProvider

DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, dim: int, *, base_url: str = "", timeout: float = 30.0) -> None:
        self._api_key = api_key
        self.model = model
        self.dim = dim
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        payload: dict = {"model": self.model, "input": texts}
        # text-embedding-3 models accept a reduced dimension that must match the DB column.
        if self.model.startswith("text-embedding-3"):
            payload["dimensions"] = self.dim
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            response = httpx.post(f"{self._base_url}/embeddings", json=payload, headers=headers, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"embedding request failed: {type(exc).__name__}") from exc
        if response.status_code >= 400:
            raise RuntimeError(f"embedding http {response.status_code}")
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        vectors = [item["embedding"] for item in data]
        if vectors and len(vectors[0]) != self.dim:
            raise RuntimeError("embedding dimension mismatch; check EMBEDDING_DIM")
        return vectors
