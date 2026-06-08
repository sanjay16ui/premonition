"""Clinical, alert, and recommendation explanation generators."""

from __future__ import annotations

from premonition.copilot.generators.context_builder import ClinicalContextBuilder
from premonition.copilot.llm.service import LLMService
from premonition.copilot.prompts.manager import PromptManager
from premonition.copilot.rag.retrieval import RAGRetrievalEngine
from premonition.copilot.schemas import (
    CopilotResponse,
    CopilotRecommendationsRequest,
    ExplainAlertRequest,
    ExplainPredictionRequest,
)


class ClinicalExplanationGenerator:
    def __init__(self, llm: LLMService, prompts: PromptManager, rag: RAGRetrievalEngine, ctx: ClinicalContextBuilder) -> None:
        self.llm = llm
        self.prompts = prompts
        self.rag = rag
        self.ctx = ctx

    def explain_prediction(self, request: ExplainPredictionRequest) -> CopilotResponse:
        factors_list = "\n".join(f"- {f}" for f in request.top_factors) if request.top_factors else "- No SHAP factors available"
        risk_pct = f"{(request.risk_score or 0) * 100:.1f}%" if (request.risk_score or 0) <= 1.0 else f"{request.risk_score:.1f}%"
        confidence_pct = getattr(request, 'confidence', round((request.risk_score or 0.5) * 100 + 10, 1))
        platform_ctx = self.ctx.build_prediction_context(
            request.risk_score or 0, request.prediction_label, request.top_factors, request.model_name,
        )
        rag_ctx, citations, trace = self.rag.retrieve("sepsis prediction SHAP explanation clinical intervention", top_k=3)
        full_context = f"{platform_ctx}\n\nEvidence Base:\n{rag_ctx}"
        system, prompt, version = self.prompts.render(
            "explain_prediction",
            patient_id=getattr(request, 'patient_id', 'UNKNOWN'),
            risk_score=risk_pct,
            prediction_label=request.prediction_label or "Sepsis Risk Elevated",
            confidence=confidence_pct,
            factors=factors_list,
            vital_trends="Trend data from real-time monitoring stream — refer to platform_ctx below",
            context=full_context,
        )
        response = self.llm.complete(prompt, system=system)
        return CopilotResponse(
            conversation_id="", message=response.content,
            citations=citations, prompt_version=version, model=response.model, retrieval_trace=trace,
        )


class AlertExplanationGenerator:
    def __init__(self, llm: LLMService, prompts: PromptManager, rag: RAGRetrievalEngine, ctx: ClinicalContextBuilder) -> None:
        self.llm = llm
        self.prompts = prompts
        self.rag = rag
        self.ctx = ctx

    def explain(self, request: ExplainAlertRequest) -> CopilotResponse:
        details = self.ctx.build_alert_context(request.alert_level, request.risk_score, request.top_factors, request.message)
        rag_ctx, citations, trace = self.rag.retrieve(f"alert {request.alert_level} sepsis escalation", top_k=3)
        system, prompt, version = self.prompts.render(
            "explain_alert", alert_level=request.alert_level,
            risk_score=request.risk_score, details=details + "\n" + rag_ctx,
        )
        response = self.llm.complete(prompt, system=system)
        return CopilotResponse(
            conversation_id="", message=response.content,
            citations=citations, prompt_version=version, model=response.model, retrieval_trace=trace,
        )


class RecommendationExplanationGenerator:
    def __init__(self, llm: LLMService, prompts: PromptManager, rag: RAGRetrievalEngine) -> None:
        self.llm = llm
        self.prompts = prompts
        self.rag = rag

    def explain(self, request: CopilotRecommendationsRequest, recommendations_text: str) -> CopilotResponse:
        factors = ", ".join(request.top_factors) if request.top_factors else "none"
        rag_ctx, citations, trace = self.rag.retrieve("sepsis clinical recommendations protocol", top_k=3)
        system, prompt, version = self.prompts.render(
            "recommendations",
            risk_score=request.risk_score or 0.3,
            factors=factors,
            recommendations=recommendations_text + "\n" + rag_ctx,
        )
        response = self.llm.complete(prompt, system=system)
        return CopilotResponse(
            conversation_id="", message=response.content,
            citations=citations, prompt_version=version, model=response.model, retrieval_trace=trace,
        )


class ExecutiveReportGenerator:
    def __init__(self, llm: LLMService, prompts: PromptManager, rag: RAGRetrievalEngine, ctx: ClinicalContextBuilder) -> None:
        self.llm = llm
        self.prompts = prompts
        self.rag = rag
        self.ctx = ctx

    def generate(self, executive_data: dict, kpis: dict | None = None) -> CopilotResponse:
        platform_ctx = self.ctx.build_executive_context(executive_data, kpis)
        rag_ctx, citations, trace = self.rag.retrieve("hospital executive KPI sepsis ICU status", top_k=3)
        system, prompt, version = self.prompts.render("executive_summary", context=platform_ctx + "\n" + rag_ctx)
        response = self.llm.complete(prompt, system=system)
        return CopilotResponse(
            conversation_id="", message=response.content,
            citations=citations, prompt_version=version, model=response.model, retrieval_trace=trace,
        )
