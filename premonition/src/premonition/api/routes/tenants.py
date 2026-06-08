"""Tenant management API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from premonition.auth.dependencies import AuthCtxDep, require_perm
from premonition.api.services.tenants import TenantApiService
from premonition.api.dependencies import TenantSvcDep
from premonition.tenant.schemas import (
    BillingPlanResponse,
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationResponse,
    TenantConfigUpdate,
    TenantCreate,
    TenantListResponse,
    TenantMemberCreate,
    TenantMemberResponse,
    TenantOnboardRequest,
    TenantResponse,
    TenantUsageResponse,
)

router = APIRouter(prefix="/tenants", tags=["Multi-Tenant"])


@router.get("", response_model=TenantListResponse, dependencies=[Depends(require_perm("tenants:read"))])
async def list_tenants(svc: TenantSvcDep, organization_id: str | None = None) -> TenantListResponse:
    return svc.list_tenants(organization_id)


@router.get("/{tenant_id}", response_model=TenantResponse, dependencies=[Depends(require_perm("tenants:read"))])
async def get_tenant(tenant_id: str, svc: TenantSvcDep) -> TenantResponse:
    return svc.get_tenant(tenant_id)


@router.post("/onboard", response_model=dict, dependencies=[Depends(require_perm("tenants:manage"))])
async def onboard_tenant(body: TenantOnboardRequest, svc: TenantSvcDep) -> dict:
    return svc.onboard(body)


@router.post("", response_model=TenantResponse, dependencies=[Depends(require_perm("tenants:manage"))])
async def create_tenant(body: TenantCreate, svc: TenantSvcDep) -> TenantResponse:
    return svc.create_tenant(body)


@router.patch("/{tenant_id}/config", response_model=TenantResponse,
              dependencies=[Depends(require_perm("tenants:manage"))])
async def update_config(tenant_id: str, body: TenantConfigUpdate, svc: TenantSvcDep) -> TenantResponse:
    return svc.update_config(tenant_id, body)


@router.delete("/{tenant_id}", dependencies=[Depends(require_perm("tenants:manage"))])
async def deactivate_tenant(tenant_id: str, svc: TenantSvcDep) -> dict:
    return svc.deactivate(tenant_id)


@router.get("/{tenant_id}/usage", response_model=TenantUsageResponse,
            dependencies=[Depends(require_perm("usage:read"))])
async def get_usage(tenant_id: str, svc: TenantSvcDep) -> TenantUsageResponse:
    return svc.get_usage(tenant_id)


@router.get("/{tenant_id}/billing", response_model=BillingPlanResponse,
            dependencies=[Depends(require_perm("billing:read"))])
async def get_billing(tenant_id: str, svc: TenantSvcDep) -> BillingPlanResponse:
    return svc.get_billing(tenant_id)


@router.get("/{tenant_id}/billing/estimate", dependencies=[Depends(require_perm("billing:read"))])
async def estimate_cost(tenant_id: str, svc: TenantSvcDep) -> dict:
    return svc.estimate_cost(tenant_id)


@router.post("/{tenant_id}/members", response_model=TenantMemberResponse,
             dependencies=[Depends(require_perm("users:manage"))])
async def add_member(tenant_id: str, body: TenantMemberCreate, svc: TenantSvcDep) -> TenantMemberResponse:
    return svc.add_member(tenant_id, body)


# Organizations
org_router = APIRouter(prefix="/organizations", tags=["Organizations"])


@org_router.get("", response_model=OrganizationListResponse,
                dependencies=[Depends(require_perm("orgs:read"))])
async def list_organizations(svc: TenantSvcDep) -> OrganizationListResponse:
    return svc.list_organizations()


@org_router.post("", response_model=OrganizationResponse,
                 dependencies=[Depends(require_perm("orgs:manage"))])
async def create_organization(body: OrganizationCreate, svc: TenantSvcDep) -> OrganizationResponse:
    return svc.create_organization(body)


@org_router.get("/{org_id}", response_model=OrganizationResponse,
                dependencies=[Depends(require_perm("orgs:read"))])
async def get_organization(org_id: str, svc: TenantSvcDep) -> OrganizationResponse:
    return svc.get_organization(org_id)
