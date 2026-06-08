"""Shift handover generator — enterprise quality with timestamp."""

from __future__ import annotations

from datetime import datetime, timezone

from premonition.copilot.llm.service import LLMService
from premonition.copilot.prompts.manager import PromptManager
from premonition.copilot.rag.retrieval import RAGRetrievalEngine
from premonition.copilot.schemas import CopilotResponse, HandoverRequest


class ShiftHandoverGenerator:
    def __init__(self, llm: LLMService, prompts: PromptManager, rag: RAGRetrievalEngine) -> None:
        self.llm = llm
        self.prompts = prompts
        self.rag = rag

    def generate(self, request: HandoverRequest, patients_context: str) -> CopilotResponse:
        rag_context, citations, trace = self.rag.retrieve("ICU handover sepsis high risk patients shift priorities", top_k=3)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        full = f"{patients_context}\n{request.shift_notes or ''}\n\nEvidence Base:\n{rag_context}"
        system, prompt, version = self.prompts.render("handover", context=full, timestamp=timestamp)
        response = self.llm.complete(prompt, system=system)
        return CopilotResponse(
            conversation_id="", message=response.content,
            citations=citations, prompt_version=version, model=response.model, retrieval_trace=trace,
        )
