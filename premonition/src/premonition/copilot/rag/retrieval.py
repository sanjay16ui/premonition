"""RAG retrieval engine."""

from __future__ import annotations

from premonition.copilot.rag.embeddings import EmbeddingService
from premonition.copilot.rag.ranking import RetrievalRankingEngine
from premonition.copilot.rag.vector_store import SearchResult, VectorStore
from premonition.copilot.schemas import Citation


class RAGRetrievalEngine:
    """Retrieve, rank, and assemble context with citations."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingService | None = None,
        ranker: RetrievalRankingEngine | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedder = embedder or EmbeddingService()
        self.ranker = ranker or RetrievalRankingEngine()

    def retrieve(self, query: str, top_k: int = 5, conversation_context: str | None = None) -> tuple[str, list[Citation], list[str]]:
        enriched_query = f"{conversation_context}\n{query}" if conversation_context else query
        query_emb = self.embedder.embed(enriched_query)
        raw_results = self.vector_store.search(query_emb, top_k=top_k * 2)
        ranked = self.ranker.rank(query, raw_results, top_k=top_k)

        context_parts = []
        citations: list[Citation] = []
        trace: list[str] = []

        for i, result in enumerate(ranked):
            doc = result.document
            title = doc.metadata.get("title", doc.id)
            context_parts.append(f"[{i + 1}] {doc.text}")
            citations.append(Citation(
                source_id=doc.metadata.get("doc_id", doc.id),
                title=title,
                excerpt=doc.text[:200],
                score=round(result.score, 4),
                chunk_index=doc.chunk_index,
            ))
            trace.append(f"retrieved:{doc.id}:score={result.score:.3f}")

        context = "\n\n".join(context_parts)
        return context, citations, trace

    def search_only(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_emb = self.embedder.embed(query)
        raw = self.vector_store.search(query_emb, top_k=top_k * 2)
        return self.ranker.rank(query, raw, top_k=top_k)
