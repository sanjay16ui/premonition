"""Copilot generator and orchestrator tests."""

from __future__ import annotations

import pytest

from premonition.copilot.generators.context_builder import ClinicalContextBuilder
from premonition.copilot.generators.explanations import AlertExplanationGenerator, ClinicalExplanationGenerator
from premonition.copilot.generators.handover import ShiftHandoverGenerator
from premonition.copilot.generators.patient_summary import PatientSummaryGenerator
from premonition.copilot.llm.service import LLMService
from premonition.copilot.orchestrator import ClinicalAIOrchestrator
from premonition.copilot.schemas import (
    ExplainAlertRequest,
    ExplainPredictionRequest,
    HandoverRequest,
    PatientSummaryRequest,
)
from premonition.copilot.prompts.manager import PromptManager
from premonition.copilot.rag.retrieval import RAGRetrievalEngine
from premonition.copilot.rag.vector_store import InMemoryVectorStore
from premonition.copilot.rag.embeddings import EmbeddingService
from premonition.copilot.agents.workflow import MultiStepAgentWorkflowEngine, WorkflowStep


@pytest.fixture
def orchestrator(tmp_path):
    return ClinicalAIOrchestrator(tmp_path / "logs", tmp_path / "data")


class TestContextBuilder:
    def test_patient_context_from_logs(self):
        ctx = ClinicalContextBuilder()
        text = ctx.build_patient_context("p1", [{"patient_id": "p1", "risk_score": 0.6, "prediction": 1, "top_factors": ["hr_mean"]}])
        assert "p1" in text
        assert "0.6" in text

    def test_alert_context(self):
        ctx = ClinicalContextBuilder()
        text = ctx.build_alert_context("RED", 0.7, ["spo2_mean"], "Critical deterioration")
        assert "RED" in text
        assert "spo2" in text

    def test_prediction_context(self):
        ctx = ClinicalContextBuilder()
        text = ctx.build_prediction_context(0.55, "sepsis_alert", ["hr_mean", "temp_celsius_mean"], "logistic_regression")
        assert "0.55" in text
        assert "hr_mean" in text


class TestGenerators:
    def test_explain_prediction(self, orchestrator):
        result = orchestrator.clinical_explainer.explain_prediction(
            ExplainPredictionRequest(risk_score=0.65, prediction_label="sepsis_alert", top_factors=["hr_mean", "spo2_mean"]),
        )
        assert len(result.message) > 20
        assert result.prompt_version

    def test_explain_alert(self, orchestrator):
        result = orchestrator.alert_explainer.explain(
            ExplainAlertRequest(alert_level="RED", risk_score=0.8, top_factors=["hypoxemia"]),
        )
        assert "alert" in result.message.lower() or "risk" in result.message.lower()

    def test_patient_summary(self, orchestrator):
        result = orchestrator.patient_summary_gen.generate(
            PatientSummaryRequest(patient_id="p100"),
            "Patient p100 risk 0.5",
        )
        assert len(result.message) > 10

    def test_handover(self, orchestrator):
        result = orchestrator.handover_gen.generate(
            HandoverRequest(patient_ids=["p1", "p2"]),
            "Patient p1: risk 0.7\nPatient p2: risk 0.3",
        )
        assert len(result.message) > 20


class TestOrchestrator:
    def test_seeds_default_knowledge(self, orchestrator):
        assert orchestrator.knowledge.count() >= 3
        assert orchestrator.vector_store.count() >= 3

    def test_chat_creates_conversation(self, orchestrator):
        result = orchestrator.chat("What is sepsis?", None, "test-user")
        assert result.conversation_id
        assert len(result.message) > 10
        assert result.model in ["mock-local", "llama-3.1-8b-instant", "qwen2.5:7b"]

    def test_chat_uses_rag_citations(self, orchestrator):
        result = orchestrator.chat("Explain Sepsis-3 criteria", None, "user")
        assert len(result.citations) >= 0

    def test_audit_logged_on_chat(self, orchestrator):
        orchestrator.chat("test query", None, "auditor")
        records = orchestrator.audit.query(action="chat")
        assert len(records) >= 1


class TestWorkflow:
    def test_multi_step_workflow(self):
        engine = MultiStepAgentWorkflowEngine()
        result = engine.run([
            WorkflowStep("step1", lambda ctx: {"value": 1}),
            WorkflowStep("step2", lambda ctx: {"doubled": ctx["value"] * 2}),
        ])
        assert result.success
        assert len(result.steps_completed) == 2
        assert result.outputs["step2"]["doubled"] == 2

    def test_workflow_failure_handling(self):
        engine = MultiStepAgentWorkflowEngine()
        result = engine.run([
            WorkflowStep("ok", lambda ctx: {"a": 1}),
            WorkflowStep("fail", lambda ctx: 1 / 0),
        ])
        assert not result.success
        assert result.error
