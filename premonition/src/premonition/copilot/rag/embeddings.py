"""Embedding service — hash-based for offline, sklearn TF-IDF optional."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

import numpy as np


class EmbeddingService:
    """Generate deterministic embeddings without external APIs."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> np.ndarray:
        tokens = re.findall(r"\w+", text.lower())
        vec = np.zeros(self.dimensions, dtype=np.float32)
        if not tokens:
            return vec
        for token in tokens:
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            idx = h % self.dimensions
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts])

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = float(np.dot(a, b))
        return max(0.0, min(1.0, dot))
