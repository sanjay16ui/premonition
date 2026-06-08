"""Vector store abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class VectorDocument:
    id: str
    text: str
    embedding: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


@dataclass
class SearchResult:
    document: VectorDocument
    score: float


class VectorStore(ABC):
    """Abstract vector store — FAISS or Chroma backends."""

    @abstractmethod
    def add(self, documents: list[VectorDocument]) -> int: ...

    @abstractmethod
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def delete(self, doc_id: str) -> bool: ...

    @abstractmethod
    def backend_name(self) -> str: ...


class InMemoryVectorStore(VectorStore):
    """Default in-memory vector store using numpy cosine similarity."""

    def __init__(self) -> None:
        self._docs: list[VectorDocument] = []

    def add(self, documents: list[VectorDocument]) -> int:
        self._docs.extend(documents)
        return len(documents)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if not self._docs:
            return []
        scores = []
        for doc in self._docs:
            score = float(np.dot(query_embedding, doc.embedding))
            scores.append((doc, max(0.0, score)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [SearchResult(document=d, score=s) for d, s in scores[:top_k]]

    def count(self) -> int:
        return len(self._docs)

    def delete(self, doc_id: str) -> bool:
        before = len(self._docs)
        self._docs = [d for d in self._docs if d.id != doc_id]
        return len(self._docs) < before

    def backend_name(self) -> str:
        return "inmemory"
