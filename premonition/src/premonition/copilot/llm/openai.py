"""OpenAI provider adapter (interface only — no live calls)."""

from __future__ import annotations

import os

from premonition.copilot.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider — requires OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._api_key = os.getenv("OPENAI_API_KEY")

    @property
    def name(self) -> str:
        return f"openai/{self.model}"

    def is_available(self) -> bool:
        return bool(self._api_key)

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("OPENAI_API_KEY not configured")
        raise NotImplementedError("External OpenAI calls disabled — use mock or configure in production")
