"""Groq LLM provider."""

from __future__ import annotations

import os
import time
import logging
from typing import Any

from groq import Groq
from premonition.copilot.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Cloud Groq API provider."""

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment.")
        self.client = Groq(api_key=api_key) if api_key else None
        self._model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self._available_cache: bool | None = None
        self._available_until: float = 0.0

    @property
    def name(self) -> str:
        return "groq"

    def is_available(self) -> bool:
        if not self.client:
            return False
        # Cache availability for 30s to avoid a models.list() round-trip on every request
        if self._available_cache is not None and time.time() < self._available_until:
            return self._available_cache
        try:
            self.client.models.list()
            self._available_cache = True
        except Exception as e:
            logger.warning(f"Groq API not available: {e}")
            self._available_cache = False
        self._available_until = time.time() + 30.0
        return self._available_cache

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> LLMResponse:
        if not self.client:
            raise RuntimeError("Groq client not initialized (missing API key).")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        logger.info(f"Groq: Generating completion using {self._model}...")
        start_time = time.time()
        
        try:
            completion = self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=200,   # Cap at 200 tokens — keeps responses <2s and ≤150 words
            )
            
            content = completion.choices[0].message.content
            latency = time.time() - start_time
            
            usage = completion.usage
            tokens = usage.completion_tokens if usage else 0
            
            logger.info(f"Groq generated response in {latency:.2f}s (tokens={tokens})")
            
            return LLMResponse(
                content=content,
                model=self._model,
                tokens_used=tokens,
                metadata={
                    "latency_sec": latency,
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": tokens,
                    "total_tokens": usage.total_tokens if usage else 0
                }
            )
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise RuntimeError(f"Groq generation failed: {e}") from e
