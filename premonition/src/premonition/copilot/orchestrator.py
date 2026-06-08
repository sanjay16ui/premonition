"""Clinical AI orchestrator."""

from __future__ import annotations

import os
from pathlib import Path

from premonition.copilot.audit.ai_audit import AIAuditLogger
from premonition.copilot.generators.context_builder import ClinicalContextBuilder
from premonition.copilot.generators.explanations import (
    AlertExplanationGenerator,
    ClinicalExplanationGenerator,
    ExecutiveReportGenerator,
    RecommendationExplanationGenerator,
)
from premonition.copilot.generators.handover import ShiftHandoverGenerator
from premonition.copilot.generators.patient_summary import PatientSummaryGenerator
from premonition.copilot.llm.service import LLMService
from premonition.copilot.memory.conversation import AIConversationMemory
from premonition.copilot.prompts.manager import PromptManager
from premonition.copilot.rag.chroma_store import ChromaVectorStore
from premonition.copilot.rag.embeddings import EmbeddingService
from premonition.copilot.rag.faiss_store import FaissVectorStore
from premonition.copilot.rag.ingestion import DocumentIngestionPipeline
from premonition.copilot.rag.knowledge import KnowledgeBaseManager
from premonition.copilot.rag.retrieval import RAGRetrievalEngine
from premonition.copilot.rag.vector_store import InMemoryVectorStore, VectorStore
from premonition.copilot.schemas import CopilotResponse


class ClinicalAIOrchestrator:
    """Orchestrate all copilot subsystems."""

    def __init__(self, logs_dir: Path, data_dir: Path | None = None) -> None:
        self.logs_dir = logs_dir
        self.data_dir = data_dir or logs_dir

        self.llm = LLMService()
        self.prompts = PromptManager()
        self.embedder = EmbeddingService()
        self.vector_store = self._create_vector_store()
        self.knowledge = KnowledgeBaseManager(self.data_dir)
        self.ingestion = DocumentIngestionPipeline(self.knowledge, self.vector_store, self.embedder)
        self.rag = RAGRetrievalEngine(self.vector_store, self.embedder)
        self.memory = AIConversationMemory(self.data_dir)
        self.audit = AIAuditLogger(self.logs_dir)
        self.context_builder = ClinicalContextBuilder()

        self.patient_summary_gen = PatientSummaryGenerator(self.llm, self.prompts, self.rag, self.context_builder)
        self.handover_gen = ShiftHandoverGenerator(self.llm, self.prompts, self.rag)
        self.clinical_explainer = ClinicalExplanationGenerator(self.llm, self.prompts, self.rag, self.context_builder)
        self.alert_explainer = AlertExplanationGenerator(self.llm, self.prompts, self.rag, self.context_builder)
        self.rec_explainer = RecommendationExplanationGenerator(self.llm, self.prompts, self.rag)
        self.executive_gen = ExecutiveReportGenerator(self.llm, self.prompts, self.rag, self.context_builder)

        self._seed_default_knowledge()

    def _create_vector_store(self) -> VectorStore:
        backend = os.getenv("PREMONITION_VECTOR_BACKEND", "inmemory").lower()
        if backend == "faiss":
            return FaissVectorStore()
        if backend == "chroma":
            return ChromaVectorStore(self.data_dir / "copilot" / "chroma")
        return InMemoryVectorStore()

    def _seed_default_knowledge(self) -> None:
        if self.knowledge.count() > 0:
            return
        defaults = [
            ("Sepsis-3 Criteria", "Sepsis is life-threatening organ dysfunction caused by dysregulated host response to infection. qSOFA criteria include altered mental status, systolic BP <=100, respiratory rate >=22."),
            ("SSC Hour-1 Bundle", "Within 1 hour: measure lactate, obtain blood cultures, administer broad-spectrum antibiotics, begin fluid resuscitation for hypotension."),
            ("PREMONITION Model", "PREMONITION uses logistic regression, random forest, and XGBoost ensemble for ICU sepsis early warning with SHAP explainability."),
        ]
        for title, content in defaults:
            self.ingestion.ingest_text(title, content, "protocol")

    def chat(self, message: str, conversation_id: str | None, actor: str, extra_context: str = "") -> CopilotResponse:
        conv = self.memory.get(conversation_id) if conversation_id else None
        if not conv:
            conv = self.memory.create(user_id=actor)
        conv_context = self.memory.get_context_string(conv.id)
        rag_context, citations, trace = self.rag.retrieve(message, top_k=5, conversation_context=conv_context)
        full_context = f"{extra_context}\n{rag_context}" if extra_context else rag_context
        system, prompt, version = self.prompts.render("chat", context=full_context, message=message)
        response = self.llm.complete(prompt, system=system)
        self.memory.add_message(conv.id, "user", message)
        self.memory.add_message(conv.id, "assistant", response.content)
        self.audit.log(actor, "chat", version, response.model, message, response.content, [c.model_dump() for c in citations], trace, conv.id)
        return CopilotResponse(
            conversation_id=conv.id, message=response.content,
            citations=citations, prompt_version=version, model=response.model, retrieval_trace=trace,
        )
