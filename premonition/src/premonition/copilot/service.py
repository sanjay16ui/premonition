"""Copilot service — integrates with analytics, realtime, and audit."""

from __future__ import annotations

from typing import Any

from premonition.analytics.schemas import RecommendationRequest
from premonition.analytics.service import AnalyticsService
from premonition.copilot.audit.ai_audit import AIAuditLogger
from premonition.copilot.memory.conversation import AIConversationMemory
from premonition.copilot.orchestrator import ClinicalAIOrchestrator
from premonition.copilot.schemas import (
    ChatRequest,
    CopilotRecommendationsRequest,
    CopilotResponse,
    ExecutiveSummaryRequest,
    ExplainAlertRequest,
    ExplainPredictionRequest,
    HandoverRequest,
    IngestDocumentRequest,
    PatientSummaryRequest,
    SearchRequest,
)
from premonition.config.settings import Settings
from premonition.models.prediction_logger import PredictionLogger


class CopilotService:
    """Enterprise Clinical AI Copilot facade."""

    def __init__(self, settings: Settings, analytics: AnalyticsService | None = None) -> None:
        self.settings = settings
        self.analytics = analytics
        self.orchestrator = ClinicalAIOrchestrator(settings.logs_dir, settings.logs_dir)
        self.prediction_logger = PredictionLogger(settings.logs_dir)

    @property
    def memory(self) -> AIConversationMemory:
        return self.orchestrator.memory

    @property
    def audit(self) -> AIAuditLogger:
        return self.orchestrator.audit

    def _logs(self) -> list[dict]:
        return self.prediction_logger.read_log()

    def chat(self, request: ChatRequest, actor: str = "anonymous") -> CopilotResponse:
        extra = ""
        if request.patient_id:
            extra = self.orchestrator.context_builder.build_patient_context(
                request.patient_id, self._logs(),
            )
        return self.orchestrator.chat(request.message, request.conversation_id, actor, extra)

    def explain_prediction(self, request: ExplainPredictionRequest, actor: str = "system") -> CopilotResponse:
        result = self.orchestrator.clinical_explainer.explain_prediction(request)
        self.orchestrator.audit.log(
            actor, "explain_prediction", result.prompt_version, result.model,
            str(request.model_dump()), result.message,
            [c.model_dump() for c in result.citations], result.retrieval_trace,
        )
        return result

    def explain_alert(self, request: ExplainAlertRequest, actor: str = "system") -> CopilotResponse:
        result = self.orchestrator.alert_explainer.explain(request)
        self.orchestrator.audit.log(
            actor, "explain_alert", result.prompt_version, result.model,
            str(request.model_dump()), result.message,
            [c.model_dump() for c in result.citations], result.retrieval_trace,
        )
        return result

    def patient_summary(self, request: PatientSummaryRequest, actor: str = "system") -> CopilotResponse:
        ctx = self.orchestrator.context_builder.build_patient_context(request.patient_id, self._logs())
        if request.include_trajectory and self.analytics:
            traj = self.analytics.patient_trajectory(request.patient_id)
            ctx += f"\nTrajectory: {traj.get('trend', 'unknown')}"
        result = self.orchestrator.patient_summary_gen.generate(request, ctx, actor)
        self.orchestrator.audit.log(actor, "patient_summary", result.prompt_version, result.model, request.patient_id, result.message)
        return result

    def handover(self, request: HandoverRequest, actor: str = "system") -> CopilotResponse:
        parts = []
        for pid in request.patient_ids:
            parts.append(self.orchestrator.context_builder.build_patient_context(pid, self._logs()))
        if not parts:
            logs = self._logs()
            high_risk = [l for l in logs if float(l.get("risk_score", 0)) >= 0.35]
            for l in high_risk[:5]:
                parts.append(self.orchestrator.context_builder.build_patient_context(str(l.get("patient_id")), logs))
        result = self.orchestrator.handover_gen.generate(request, "\n---\n".join(parts))
        self.orchestrator.audit.log(actor, "handover", result.prompt_version, result.model, str(request.patient_ids), result.message)
        return result

    def executive_summary(self, request: ExecutiveSummaryRequest, actor: str = "system", executive_data: dict | None = None, kpis: dict | None = None) -> CopilotResponse:
        exec_data = executive_data or {}
        kpi_data = kpis or {}
        if self.analytics:
            if not exec_data:
                exec_data = self.analytics.get_executive()
            if request.include_kpis and not kpi_data:
                kpi_data = self.analytics.get_kpis()
        result = self.orchestrator.executive_gen.generate(exec_data, kpi_data)
        self.orchestrator.audit.log(actor, "executive_summary", result.prompt_version, result.model, "executive", result.message)
        return result

    def recommendations(self, request: CopilotRecommendationsRequest, actor: str = "system") -> CopilotResponse:
        recs_text = ""
        if self.analytics:
            from premonition.analytics.schemas import RecommendationRequest as AnalyticsRec
            recs = self.analytics.get_recommendations(AnalyticsRec(
                patient_id=request.patient_id,
                risk_score=request.risk_score,
                top_factors=request.top_factors,
            ))
            recs_text = "\n".join(f"{r['rank']}. [{r['priority']}] {r['action']}" for r in recs)
        result = self.orchestrator.rec_explainer.explain(request, recs_text)
        self.orchestrator.audit.log(actor, "recommendations", result.prompt_version, result.model, str(request.model_dump()), result.message)
        return result

    def ingest_document(self, request: IngestDocumentRequest, actor: str = "system") -> dict[str, Any]:
        result = self.orchestrator.ingestion.ingest_text(
            request.title, request.content, request.doc_type, request.metadata,
        )
        self.orchestrator.audit.log(actor, "ingest_document", "ingestion@1.0", "rag", request.title, f"Ingested {result['chunks']} chunks")
        return result

    def search(self, request: SearchRequest) -> dict[str, Any]:
        conv_ctx = None
        if request.conversation_id:
            conv_ctx = self.orchestrator.memory.get_context_string(request.conversation_id)
        context, citations, trace = self.orchestrator.rag.retrieve(
            request.query, top_k=request.top_k, conversation_context=conv_ctx,
        )
        return {
            "query": request.query,
            "context": context,
            "citations": [c.model_dump() for c in citations],
            "retrieval_trace": trace,
        }

    def list_conversations(self, user_id: str | None = None) -> list[dict]:
        return self.orchestrator.memory.list_conversations(user_id)

    def get_conversation(self, conv_id: str) -> dict | None:
        conv = self.orchestrator.memory.get(conv_id)
        if not conv:
            return None
        return {
            "id": conv.id, "title": conv.title,
            "messages": [m.model_dump() for m in conv.messages],
            "created_at": conv.created_at, "updated_at": conv.updated_at,
        }
