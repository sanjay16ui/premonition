"""API error response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Single validation or business error."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all API errors."""

    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    request_id: str | None = Field(None, description="Trace ID for support")
    details: list[ErrorDetail] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
