"""Azure OpenAI provider adapter (interface only)."""

from __future__ import annotations

import os

from premonition.copilot.llm.base import LLMProvider, LLMResponse


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider — requires AZURE_OPENAI_ENDPOINT and key."""

    def __init__(self, deployment: str = "gpt-4o") -> None:
        self.deployment = deployment
        self._endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self._api_key = os.getenv("AZURE_OPENAI_API_KEY")

    @property
    def name(self) -> str:
        return f"azure/{self.deployment}"

    def is_available(self) -> bool:
        return bool(self._endpoint and self._api_key)

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("Azure OpenAI not configured")
        raise NotImplementedError("External Azure OpenAI calls disabled — use mock provider")
