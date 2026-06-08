"""Copilot service integration tests."""

from __future__ import annotations

import pytest

from premonition.analytics.service import AnalyticsService
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


@pytest.fixture
def copilot(settings):
    analytics = AnalyticsService(settings)
    return CopilotService(settings, analytics)


class TestCopilotService:
    def test_chat(self, copilot):
        result = copilot.chat(ChatRequest(message="What is the sepsis bundle?"), actor="clinician")
        assert result.conversation_id
        assert len(result.message) > 10

    def test_explain_prediction(self, copilot):
        result = copilot.explain_prediction(ExplainPredictionRequest(risk_score=0.7, top_factors=["hr_mean"]))
        assert len(result.message) > 10

    def test_explain_alert(self, copilot):
        result = copilot.explain_alert(ExplainAlertRequest(alert_level="ORANGE", risk_score=0.45))
        assert len(result.message) > 5

    def test_patient_summary(self, copilot):
        result = copilot.patient_summary(PatientSummaryRequest(patient_id="test-patient-1"))
        assert len(result.message) > 5

    def test_handover(self, copilot):
        result = copilot.handover(HandoverRequest(patient_ids=["p1"]))
        assert len(result.message) > 10

    def test_executive_summary(self, copilot):
        result = copilot.executive_summary(ExecutiveSummaryRequest())
        assert len(result.message) > 10

    def test_recommendations(self, copilot):
        result = copilot.recommendations(CopilotRecommendationsRequest(risk_score=0.6))
        assert len(result.message) > 10

    def test_ingest_document(self, copilot):
        result = copilot.ingest_document(IngestDocumentRequest(
            title="Custom SOP", content="ICU rounding every 4 hours for sepsis patients.", doc_type="sop",
        ))
        assert result["chunks"] >= 1

    def test_search(self, copilot):
        result = copilot.search(SearchRequest(query="sepsis antibiotics", top_k=3))
        assert "citations" in result
        assert "retrieval_trace" in result

    def test_conversations(self, copilot):
        copilot.chat(ChatRequest(message="Hello"), actor="user1")
        convs = copilot.list_conversations("user1")
        assert len(convs) >= 1

    def test_get_conversation(self, copilot):
        r = copilot.chat(ChatRequest(message="Test message"), actor="user2")
        detail = copilot.get_conversation(r.conversation_id)
        assert detail is not None
        assert len(detail["messages"]) == 2

    def test_audit_records(self, copilot):
        copilot.explain_prediction(ExplainPredictionRequest(risk_score=0.5), actor="admin")
        records = copilot.audit.query(action="explain_prediction")
        assert len(records) >= 1
