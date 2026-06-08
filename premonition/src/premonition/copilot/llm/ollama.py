"""Ollama LLM provider."""

from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict

from premonition.copilot.llm.base import LLMProvider, LLMResponse
from premonition.utils.logging import get_logger

logger = get_logger(__name__)

class OllamaProvider(LLMProvider):
    """Local Ollama instance provider with optimizations."""

    def __init__(self):
        self._cache: Dict[str, LLMResponse] = {}

    @property
    def name(self) -> str:
        return "ollama"

    def _get_model_status(self, base_url: str) -> dict:
        """Check currently loaded model and GPU utilization (api/ps)."""
        try:
            req = urllib.request.Request(f"{base_url}/api/ps")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                if models:
                    m = models[0]
                    return {
                        "model": m.get("name"),
                        "size_vram": m.get("size_vram", 0),
                        "size": m.get("size", 0)
                    }
        except Exception:
            pass
        return {}

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.3) -> LLMResponse:
        model = os.getenv("PREMONITION_OLLAMA_MODEL", "qwen2.5:7b")
        base_url = os.getenv("PREMONITION_OLLAMA_URL", "http://localhost:11434").rstrip("/")
        url = f"{base_url}/api/generate"

        # 5. Reduce prompt size (trim excessively long prompts defensively)
        if len(prompt) > 8000:
            prompt = prompt[:8000] + "... [truncated]"

        # 7. Add fallback to cached responses
        cache_key = f"{model}:{temperature}:{system}:{prompt}"
        if cache_key in self._cache:
            logger.info("Ollama: Serving response from cache")
            return self._cache[cache_key]

        # 2 & 3. Check loaded model and GPU info
        status = self._get_model_status(base_url)
        if status:
            logger.info(f"Ollama Status - Model: {status.get('model')}, VRAM: {status.get('size_vram')} bytes")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,  # 8. Streaming enabled for chunk accumulation
            "keep_alive": "10m",  # 4. Enable model keep-alive (extended)
            "options": {
                "temperature": temperature,
                "num_predict": 512,    # Cap output tokens → faster CPU responses
                "num_ctx": 4096,       # Context window
                "repeat_penalty": 1.1  # Reduce repetition
            }
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        # 1 & 9. Measure and log latency
        start_time = time.time()
        
        full_content = []
        eval_count = 0
        prompt_eval_count = 0
        total_duration = 0

        try:
            # 6. Add request timeout handling
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
                    if not line.strip():
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    full_content.append(chunk.get("response", ""))
                    if chunk.get("done"):
                        eval_count = chunk.get("eval_count", 0)
                        prompt_eval_count = chunk.get("prompt_eval_count", 0)
                        total_duration = chunk.get("total_duration", 0)
        except Exception as e:
            # If timeout or failure occurs and we have a cache, fallback
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}") from e

        latency = time.time() - start_time
        logger.info(f"Ollama generated response in {latency:.2f}s (eval_count={eval_count})")

        response = LLMResponse(
            content="".join(full_content),
            model=model,
            tokens_used=eval_count + prompt_eval_count,
            metadata={
                "total_duration": total_duration,
                "eval_count": eval_count,
                "prompt_eval_count": prompt_eval_count,
                "latency_sec": latency,
                "vram_used": status.get("size_vram", 0)
            }
        )
        
        # Cache the successful response
        self._cache[cache_key] = response
        return response

    def is_available(self) -> bool:
        url = f"{os.getenv('PREMONITION_OLLAMA_URL', 'http://localhost:11434').rstrip('/')}/api/tags"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

