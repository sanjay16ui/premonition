"""FAISS vector store backend."""

from __future__ import annotations

import numpy as np

from premonition.copilot.rag.vector_store import SearchResult, VectorDocument, VectorStore


class FaissVectorStore(VectorStore):
    """FAISS-backed vector store with numpy fallback."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions
        self._docs: list[VectorDocument] = []
        self._index = None
        self._use_faiss = False
        try:
            import faiss
            self._index = faiss.IndexFlatIP(dimensions)
            self._use_faiss = True
        except ImportError:
            pass

    def add(self, documents: list[VectorDocument]) -> int:
        self._docs.extend(documents)
        if self._use_faiss and self._index is not None:
            import faiss
            vectors = np.stack([d.embedding for d in documents]).astype(np.float32)
            self._index.add(vectors)
        return len(documents)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if not self._docs:
            return []
        if self._use_faiss and self._index is not None and self._index.ntotal > 0:
            import faiss
            q = query_embedding.reshape(1, -1).astype(np.float32)
            scores, indices = self._index.search(q, min(top_k, len(self._docs)))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0:
                    results.append(SearchResult(document=self._docs[idx], score=float(score)))
            return results
        scores = [(d, float(np.dot(query_embedding, d.embedding))) for d in self._docs]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [SearchResult(document=d, score=s) for d, s in scores[:top_k]]

    def count(self) -> int:
        return len(self._docs)

    def delete(self, doc_id: str) -> bool:
        self._docs = [d for d in self._docs if d.id != doc_id]
        return True

    def backend_name(self) -> str:
        return "faiss" if self._use_faiss else "faiss-fallback"
