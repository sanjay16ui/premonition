"""Tenant API service — bridges routes to TenantService."""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from premonition.tenant.isolation import assert_tenant_access
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
from premonition.tenant.service import TenantService


class TenantApiService:
    def __init__(self, tenant_service: TenantService, request: Request) -> None:
        self.svc = tenant_service
        self.request = request

    def _active_tenant_id(self) -> str:
        return getattr(self.request.state, "tenant_id", "premonition-default")

    def _to_tenant_response(self, tenant) -> TenantResponse:
        return TenantResponse(
            id=tenant.id, hospital_name=tenant.hospital_name, slug=tenant.slug,
            organization_id=tenant.organization_id, timezone=tenant.timezone,
            bed_capacity=tenant.bed_capacity, icu_beds=tenant.icu_beds,
            status=tenant.status, created_at=tenant.created_at, config=tenant.config,
        )

    def list_tenants(self, organization_id: str | None = None) -> TenantListResponse:
        tenants = self.svc.list_tenants(organization_id)
        return TenantListResponse(
            count=len(tenants),
            items=[self._to_tenant_response(t) for t in tenants],
        )

    def get_tenant(self, tenant_id: str) -> TenantResponse:
        tenant = self.svc.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
        return self._to_tenant_response(tenant)

    def onboard(self, body: TenantOnboardRequest) -> dict:
        try:
            return self._onboard_impl(body)
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    def _onboard_impl(self, body: TenantOnboardRequest) -> dict:
        result = self.svc.onboard_hospital(
            org_name=body.organization.name,
            org_slug=body.organization.slug,
            org_email=body.organization.contact_email,
            hospital_name=body.tenant.hospital_name,
            tenant_slug=body.tenant.slug,
            admin_email=body.admin_email,
            admin_role=body.admin_role.value,
            region=body.organization.region,
            plan=body.organization.plan,
            bed_capacity=body.tenant.bed_capacity,
            icu_beds=body.tenant.icu_beds,
        )
        return self._format_onboard_result(result, body.admin_email)

    def _format_onboard_result(self, result: dict, admin_email: str) -> dict:
        return {
            "organization": OrganizationResponse(
                id=result["organization"].id, name=result["organization"].name,
                slug=result["organization"].slug,
                contact_email=result["organization"].contact_email,
                region=result["organization"].region, plan=result["organization"].plan,
                status=result["organization"].status,
                created_at=result["organization"].created_at,
            ),
            "tenant": self._to_tenant_response(result["tenant"]),
            "admin_email": admin_email,
            "provisioned_paths": result["provisioned_paths"],
        }

    def create_tenant(self, body: TenantCreate) -> TenantResponse:
        tenant = self.svc.store.create_tenant(
            hospital_name=body.hospital_name, slug=body.slug,
            organization_id=body.organization_id, timezone=body.timezone,
            bed_capacity=body.bed_capacity, icu_beds=body.icu_beds,
        )
        self.svc.onboarding._provision_tenant_directories(tenant)
        return self._to_tenant_response(tenant)

    def update_config(self, tenant_id: str, body: TenantConfigUpdate) -> TenantResponse:
        config = self.svc.config.update_config(tenant_id, body.config)
        tenant = self.svc.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
        return self._to_tenant_response(tenant)

    def deactivate(self, tenant_id: str) -> dict:
        tenant = self.svc.store.deactivate_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
        return {"status": "deactivated", "tenant_id": tenant_id}

    def get_usage(self, tenant_id: str) -> TenantUsageResponse:
        usage = self.svc.usage.get_current_usage(tenant_id)
        return TenantUsageResponse(
            tenant_id=usage.tenant_id, period=usage.period,
            predictions=usage.predictions, copilot_requests=usage.copilot_requests,
            analytics_queries=usage.analytics_queries, realtime_events=usage.realtime_events,
            storage_bytes=usage.storage_bytes, api_calls=usage.api_calls,
        )

    def get_billing(self, tenant_id: str) -> BillingPlanResponse:
        plan = self.svc.billing.get_plan(tenant_id)
        return BillingPlanResponse(
            tenant_id=plan.tenant_id, plan=plan.plan,
            monthly_limit_predictions=plan.monthly_limit_predictions,
            monthly_limit_copilot=plan.monthly_limit_copilot,
            monthly_limit_api_calls=plan.monthly_limit_api_calls,
            overage_allowed=plan.overage_allowed,
        )

    def estimate_cost(self, tenant_id: str) -> dict:
        return self.svc.billing.estimate_cost(tenant_id)

    def add_member(self, tenant_id: str, body: TenantMemberCreate) -> TenantMemberResponse:
        member = self.svc.store.add_member(body.email, body.role.value, tenant_id)
        return TenantMemberResponse(
            email=member.email, role=body.role, tenant_id=member.tenant_id, active=member.active,
        )

    def list_organizations(self) -> OrganizationListResponse:
        orgs = self.svc.list_organizations()
        return OrganizationListResponse(
            count=len(orgs),
            items=[
                OrganizationResponse(
                    id=o.id, name=o.name, slug=o.slug,
                    contact_email=o.contact_email, region=o.region,
                    plan=o.plan, status=o.status, created_at=o.created_at,
                )
                for o in orgs
            ],
        )

    def create_organization(self, body: OrganizationCreate) -> OrganizationResponse:
        org = self.svc.store.create_organization(
            name=body.name, slug=body.slug,
            contact_email=body.contact_email, region=body.region, plan=body.plan,
        )
        return OrganizationResponse(
            id=org.id, name=org.name, slug=org.slug,
            contact_email=org.contact_email, region=org.region,
            plan=org.plan, status=org.status, created_at=org.created_at,
        )

    def get_organization(self, org_id: str) -> OrganizationResponse:
        org = self.svc.get_organization(org_id)
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
        return OrganizationResponse(
            id=org.id, name=org.name, slug=org.slug,
            contact_email=org.contact_email, region=org.region,
            plan=org.plan, status=org.status, created_at=org.created_at,
        )
