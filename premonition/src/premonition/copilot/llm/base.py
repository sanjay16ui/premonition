"""LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract LLM provider — OpenAI, Azure, or local."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> LLMResponse: ...

    @abstractmethod
    def is_available(self) -> bool: ...
