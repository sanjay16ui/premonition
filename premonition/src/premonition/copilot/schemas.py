"""Copilot request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    patient_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    score: float
    chunk_index: int = 0


class CopilotResponse(BaseModel):
    conversation_id: str
    message: str
    citations: list[Citation] = Field(default_factory=list)
    prompt_version: str = ""
    model: str = ""
    retrieval_trace: list[str] = Field(default_factory=list)


class ExplainPredictionRequest(BaseModel):
    patient_id: str | None = None
    risk_score: float | None = None
    top_factors: list[str] = Field(default_factory=list)
    prediction_label: str | None = None
    model_name: str | None = None


class ExplainAlertRequest(BaseModel):
    alert_level: str
    risk_score: float
    patient_id: str | None = None
    message: str | None = None
    top_factors: list[str] = Field(default_factory=list)


class PatientSummaryRequest(BaseModel):
    patient_id: str
    include_trajectory: bool = True
    include_recommendations: bool = True


class HandoverRequest(BaseModel):
    patient_ids: list[str] = Field(default_factory=list)
    shift_notes: str | None = None


class ExecutiveSummaryRequest(BaseModel):
    include_kpis: bool = True
    include_capacity: bool = True


class CopilotRecommendationsRequest(BaseModel):
    patient_id: str | None = None
    risk_score: float | None = None
    top_factors: list[str] = Field(default_factory=list)


class IngestDocumentRequest(BaseModel):
    title: str
    content: str
    doc_type: str = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    conversation_id: str | None = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[ChatMessage]
    created_at: str
    updated_at: str
