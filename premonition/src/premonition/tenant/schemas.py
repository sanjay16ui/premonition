"""Pydantic schemas for tenant management APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from premonition.auth.roles import Role


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    contact_email: str
    region: str = "us-east-1"
    plan: str = "standard"


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    contact_email: str
    region: str
    plan: str
    status: str
    created_at: str


class TenantCreate(BaseModel):
    hospital_name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    organization_id: str
    timezone: str = "UTC"
    bed_capacity: int = Field(default=100, ge=1)
    icu_beds: int = Field(default=20, ge=1)


class TenantOnboardRequest(BaseModel):
    organization: OrganizationCreate
    tenant: TenantCreate
    admin_email: str
    admin_role: Role = Role.ADMIN


class TenantResponse(BaseModel):
    id: str
    hospital_name: str
    slug: str
    organization_id: str
    timezone: str
    bed_capacity: int
    icu_beds: int
    status: str
    created_at: str
    config: dict[str, Any] = Field(default_factory=dict)


class TenantConfigUpdate(BaseModel):
    config: dict[str, Any]


class TenantUsageResponse(BaseModel):
    tenant_id: str
    period: str
    predictions: int = 0
    copilot_requests: int = 0
    analytics_queries: int = 0
    realtime_events: int = 0
    storage_bytes: int = 0
    api_calls: int = 0


class BillingPlanResponse(BaseModel):
    tenant_id: str
    plan: str
    monthly_limit_predictions: int
    monthly_limit_copilot: int
    monthly_limit_api_calls: int
    overage_allowed: bool = False


class TenantMemberCreate(BaseModel):
    email: str
    role: Role
    tenant_id: str


class TenantMemberResponse(BaseModel):
    email: str
    role: Role
    tenant_id: str
    active: bool = True


class TenantListResponse(BaseModel):
    count: int
    items: list[TenantResponse]


class OrganizationListResponse(BaseModel):
    count: int
    items: list[OrganizationResponse]
