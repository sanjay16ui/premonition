"""API copilot service wrapper."""

from __future__ import annotations

from fastapi import Request

from premonition.auth.rbac import AuthContext
from premonition.copilot.schemas import (
    ChatRequest,
    CopilotRecommendationsRequest,
    ExecutiveSummaryRequest,
    ExplainAlertRequest,
    ExplainPredictionRequest,
    HandoverRequest,
    IngestDocumentRequest,
    PatientSummaryRequest,
    SearchRequest,
)
from premonition.copilot.service import CopilotService


class CopilotApiService:
    def __init__(self, copilot: CopilotService, request: Request | None = None) -> None:
        self.copilot = copilot
        self._request = request

    def _actor(self, auth: AuthContext | None = None) -> str:
        if auth:
            return auth.subject
        return "anonymous"

    def _executive_data(self) -> dict | None:
        if not self._request:
            return None
        rt = getattr(self._request.app.state, "realtime_service", None)
        if rt:
            try:
                summary = rt.get_executive_summary()
                return summary.model_dump() if hasattr(summary, "model_dump") else dict(summary)
            except Exception:
                pass
        return None

    async def chat(self, body: ChatRequest, auth: AuthContext) -> dict:
        return self.copilot.chat(body, self._actor(auth)).model_dump()

    async def explain_prediction(self, body: ExplainPredictionRequest, auth: AuthContext) -> dict:
        return self.copilot.explain_prediction(body, self._actor(auth)).model_dump()

    async def explain_alert(self, body: ExplainAlertRequest, auth: AuthContext) -> dict:
        return self.copilot.explain_alert(body, self._actor(auth)).model_dump()

    async def patient_summary(self, body: PatientSummaryRequest, auth: AuthContext) -> dict:
        return self.copilot.patient_summary(body, self._actor(auth)).model_dump()

    async def handover(self, body: HandoverRequest, auth: AuthContext) -> dict:
        return self.copilot.handover(body, self._actor(auth)).model_dump()

    async def executive_summary(self, body: ExecutiveSummaryRequest, auth: AuthContext) -> dict:
        return self.copilot.executive_summary(
            body, self._actor(auth), self._executive_data(),
        ).model_dump()

    async def recommendations(self, body: CopilotRecommendationsRequest, auth: AuthContext) -> dict:
        return self.copilot.recommendations(body, self._actor(auth)).model_dump()

    async def ingest_document(self, body: IngestDocumentRequest, auth: AuthContext) -> dict:
        return self.copilot.ingest_document(body, self._actor(auth))

    async def search(self, body: SearchRequest) -> dict:
        return self.copilot.search(body)

    async def list_conversations(self, auth: AuthContext) -> list[dict]:
        return self.copilot.list_conversations(self._actor(auth))

    async def get_conversation(self, conv_id: str) -> dict | None:
        return self.copilot.get_conversation(conv_id)
