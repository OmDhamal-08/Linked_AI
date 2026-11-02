"""Provider-agnostic LLM interface. The rest of the app depends only on this."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIRequest:
    system_prompt: str
    user_prompt: str
    task: str  # generate | enhance | analyze | extract | validate
    variables: dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 900
    temperature: float = 0.7


@dataclass
class AIResult:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ProviderError(Exception):
    """Raised by providers for any recoverable failure (network, 5xx, 429, timeout)."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class AIProvider(ABC):
    name: str = "base"
    model: str = "unknown"

    @abstractmethod
    def complete(self, request: AIRequest) -> AIResult:
        """Run a completion. Must raise ProviderError on failure."""


def estimate_tokens(text: str) -> int:
    """Rough token estimate (about 4 characters per token) for providers that omit usage."""
    return max(1, len(text) // 4)
