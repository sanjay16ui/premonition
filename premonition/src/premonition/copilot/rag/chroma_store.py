"""Chroma vector store backend (file-backed abstraction)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from premonition.copilot.rag.vector_store import SearchResult, VectorDocument, VectorStore
from premonition.utils.paths import ensure_dir


class ChromaVectorStore(VectorStore):
    """Chroma-compatible file-backed store with numpy search."""

    def __init__(self, persist_dir: Path) -> None:
        self.persist_dir = ensure_dir(persist_dir)
        self._docs: list[VectorDocument] = []
        self._load()

    def _load(self) -> None:
        meta_file = self.persist_dir / "chroma_docs.json"
        if meta_file.exists():
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            for item in data:
                self._docs.append(VectorDocument(
                    id=item["id"],
                    text=item["text"],
                    embedding=np.array(item["embedding"], dtype=np.float32),
                    metadata=item.get("metadata", {}),
                    chunk_index=item.get("chunk_index", 0),
                ))

    def _save(self) -> None:
        meta_file = self.persist_dir / "chroma_docs.json"
        data = [
            {
                "id": d.id,
                "text": d.text,
                "embedding": d.embedding.tolist(),
                "metadata": d.metadata,
                "chunk_index": d.chunk_index,
            }
            for d in self._docs
        ]
        meta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, documents: list[VectorDocument]) -> int:
        self._docs.extend(documents)
        self._save()
        return len(documents)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if not self._docs:
            return []
        scores = [(d, float(np.dot(query_embedding, d.embedding))) for d in self._docs]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [SearchResult(document=d, score=s) for d, s in scores[:top_k]]

    def count(self) -> int:
        return len(self._docs)

    def delete(self, doc_id: str) -> bool:
        before = len(self._docs)
        self._docs = [d for d in self._docs if d.id != doc_id]
        if len(self._docs) < before:
            self._save()
            return True
        return False

    def backend_name(self) -> str:
        return "chroma"
