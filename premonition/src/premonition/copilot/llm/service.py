"""LLM service layer — provider selection and completion."""

from __future__ import annotations

import os

from premonition.copilot.llm.azure import AzureOpenAIProvider
from premonition.copilot.llm.base import LLMProvider, LLMResponse
from premonition.copilot.llm.mock import MockLLMProvider
from premonition.copilot.llm.openai import OpenAIProvider
from premonition.copilot.llm.ollama import OllamaProvider
from premonition.copilot.llm.groq_provider import GroqProvider

import logging
logger = logging.getLogger(__name__)

class LLMService:
    """Select and invoke LLM provider based on environment, with fallback."""

    def __init__(self) -> None:
        self.primary = GroqProvider()
        self.fallback = OllamaProvider()

    @property
    def provider(self) -> LLMProvider:
        return self.primary if self.primary.is_available() else self.fallback

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> LLMResponse:
        if self.primary.is_available():
            try:
                return self.primary.complete(prompt, system=system, temperature=temperature)
            except Exception as e:
                logger.error(f"Primary provider (Groq) failed: {e}. Falling back to Ollama.")
                return self.fallback.complete(prompt, system=system, temperature=temperature)
        else:
            return self.fallback.complete(prompt, system=system, temperature=temperature)
