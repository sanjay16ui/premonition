"""RAG engine, embeddings, retrieval tests."""

from __future__ import annotations

import numpy as np
import pytest

from premonition.copilot.rag.chunking import DocumentChunker
from premonition.copilot.rag.embeddings import EmbeddingService
from premonition.copilot.rag.faiss_store import FaissVectorStore
from premonition.copilot.rag.ingestion import DocumentIngestionPipeline
from premonition.copilot.rag.knowledge import KnowledgeBaseManager
from premonition.copilot.rag.ranking import RetrievalRankingEngine
from premonition.copilot.rag.retrieval import RAGRetrievalEngine
from premonition.copilot.rag.vector_store import InMemoryVectorStore, VectorDocument


@pytest.fixture
def embedder():
    return EmbeddingService(dimensions=64)


@pytest.fixture
def vector_store():
    return InMemoryVectorStore()


@pytest.fixture
def rag_engine(vector_store, embedder):
    return RAGRetrievalEngine(vector_store, embedder)


class TestChunking:
    def test_chunk_short_text(self):
        c = DocumentChunker(chunk_size=100, overlap=10)
        chunks = c.chunk("Short text only.")
        assert len(chunks) == 1

    def test_chunk_long_text(self):
        c = DocumentChunker(chunk_size=50, overlap=10)
        text = "word " * 100
        chunks = c.chunk(text)
        assert len(chunks) > 1

    def test_empty_text(self):
        assert DocumentChunker().chunk("") == []


class TestEmbeddings:
    def test_embed_returns_vector(self, embedder):
        v = embedder.embed("sepsis prediction ICU")
        assert v.shape == (64,)
        assert np.linalg.norm(v) > 0

    def test_similar_texts_high_similarity(self, embedder):
        a = embedder.embed("sepsis ICU patient risk")
        b = embedder.embed("sepsis ICU patient alert")
        assert embedder.similarity(a, b) > 0.3

    def test_different_texts_lower_similarity(self, embedder):
        a = embedder.embed("sepsis ICU")
        b = embedder.embed("billing invoice payment")
        assert embedder.similarity(a, b) < embedder.similarity(a, a)

    def test_embed_batch(self, embedder):
        batch = embedder.embed_batch(["a", "b", "c"])
        assert batch.shape == (3, 64)


class TestVectorStore:
    def test_add_and_search(self, vector_store, embedder):
        doc = VectorDocument(id="d1", text="sepsis protocol", embedding=embedder.embed("sepsis protocol"))
        vector_store.add([doc])
        results = vector_store.search(embedder.embed("sepsis"), top_k=1)
        assert len(results) == 1
        assert results[0].document.id == "d1"

    def test_count(self, vector_store, embedder):
        vector_store.add([VectorDocument(id="d1", text="t", embedding=embedder.embed("t"))])
        assert vector_store.count() == 1

    def test_delete(self, vector_store, embedder):
        vector_store.add([VectorDocument(id="d1", text="t", embedding=embedder.embed("t"))])
        assert vector_store.delete("d1")


class TestFaissStore:
    def test_faiss_add_search(self, embedder):
        store = FaissVectorStore(dimensions=64)
        store.add([VectorDocument(id="f1", text="sepsis alert ICU", embedding=embedder.embed("sepsis alert ICU"))])
        results = store.search(embedder.embed("sepsis ICU"), top_k=1)
        assert len(results) >= 1

    def test_backend_name(self):
        store = FaissVectorStore(dimensions=64)
        assert "faiss" in store.backend_name()


class TestRanking:
    def test_keyword_boost(self, embedder, vector_store):
        ranker = RetrievalRankingEngine()
        from premonition.copilot.rag.vector_store import SearchResult
        r1 = SearchResult(VectorDocument(id="1", text="sepsis protocol bundle", embedding=embedder.embed("x")), 0.5)
        r2 = SearchResult(VectorDocument(id="2", text="billing codes", embedding=embedder.embed("y")), 0.6)
        ranked = ranker.rank("sepsis protocol", [r2, r1], top_k=2)
        assert ranked[0].document.text == "sepsis protocol bundle"


class TestRetrieval:
    def test_retrieve_with_citations(self, rag_engine, vector_store, embedder):
        vector_store.add([
            VectorDocument(id="d1", text="Sepsis-3 criteria for ICU patients", embedding=embedder.embed("Sepsis-3 criteria"), metadata={"title": "Sepsis-3"}),
            VectorDocument(id="d2", text="Antibiotic administration protocol", embedding=embedder.embed("Antibiotic protocol"), metadata={"title": "SSC"}),
        ])
        context, citations, trace = rag_engine.retrieve("sepsis criteria ICU", top_k=2)
        assert len(citations) >= 1
        assert len(trace) >= 1
        assert "Sepsis" in context or "sepsis" in context.lower()

    def test_conversation_aware_retrieval(self, rag_engine, vector_store, embedder):
        vector_store.add([VectorDocument(id="d1", text="Patient risk elevated", embedding=embedder.embed("patient risk"), metadata={"title": "Risk"})])
        _, citations, _ = rag_engine.retrieve("what about alerts?", conversation_context="patient: p123 risk high")
        assert isinstance(citations, list)


class TestKnowledgeAndIngestion:
    def test_ingest_text(self, tmp_path, embedder):
        kb = KnowledgeBaseManager(tmp_path)
        store = InMemoryVectorStore()
        pipeline = DocumentIngestionPipeline(kb, store, embedder)
        result = pipeline.ingest_text("Test Protocol", "Sepsis management requires early antibiotics and lactate measurement.", "protocol")
        assert result["chunks"] >= 1
        assert kb.count() == 1
        assert store.count() >= 1

    def test_knowledge_list(self, tmp_path):
        kb = KnowledgeBaseManager(tmp_path)
        kb.add("Doc1", "content", "text", chunk_count=2)
        docs = kb.list_documents()
        assert len(docs) == 1
        assert docs[0]["title"] == "Doc1"
