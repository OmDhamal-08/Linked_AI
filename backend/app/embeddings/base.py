from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    name: str = "base"
    model: str = "unknown"
    dim: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order. Raise on failure."""
