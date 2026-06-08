"""Patient summary generator."""

from __future__ import annotations

from premonition.copilot.generators.context_builder import ClinicalContextBuilder
from premonition.copilot.llm.service import LLMService
from premonition.copilot.prompts.manager import PromptManager
from premonition.copilot.rag.retrieval import RAGRetrievalEngine
from premonition.copilot.schemas import CopilotResponse, PatientSummaryRequest


class PatientSummaryGenerator:
    def __init__(self, llm: LLMService, prompts: PromptManager, rag: RAGRetrievalEngine, context_builder: ClinicalContextBuilder) -> None:
        self.llm = llm
        self.prompts = prompts
        self.rag = rag
        self.ctx = context_builder

    def generate(self, request: PatientSummaryRequest, platform_context: str, actor: str = "system") -> CopilotResponse:
        rag_context, citations, trace = self.rag.retrieve(f"patient {request.patient_id} sepsis status", top_k=3)
        full_context = f"{platform_context}\n\n{rag_context}"
        system, prompt, version = self.prompts.render(
            "patient_summary", patient_id=request.patient_id, context=full_context,
        )
        response = self.llm.complete(prompt, system=system)
        return CopilotResponse(
            conversation_id="",
            message=response.content,
            citations=citations,
            prompt_version=version,
            model=response.model,
            retrieval_trace=trace,
        )
