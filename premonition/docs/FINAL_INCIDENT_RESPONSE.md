# PREMONITION — Incident Response

## Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| SEV-1 | Patient safety impact, system down | 15 minutes |
| SEV-2 | Degraded predictions, partial outage | 1 hour |
| SEV-3 | Non-critical feature failure | 4 hours |
| SEV-4 | Cosmetic/minor issue | Next business day |

## SEV-1: System Down

1. Check health endpoint and pod status
2. Review recent deployments — rollback if needed
3. Verify model is loaded (`GET /api/v1/system/status`)
4. Enable fallback manual clinical protocols
5. Notify hospital admins via alert system

```bash
kubectl get pods -n premonition
kubectl logs -l app=premonition-api --tail=100
helm rollback premonition
```

## SEV-1: Incorrect Predictions

1. Disable affected model: `POST /api/v1/mlops/demote`
2. Promote previous model version
3. Review audit logs for affected patients
4. Run drift analysis
5. Document in incident report

## SEV-2: Tenant Data Leak Suspected

1. Immediately isolate affected tenant
2. Review `TenantIsolationError` logs
3. Audit all cross-tenant access attempts
4. Rotate JWT secrets and API keys
5. Notify compliance officer

## SEV-2: Copilot Incorrect Response

1. Review AI audit log (`logs/copilot/audit/`)
2. Check retrieval trace and citations
3. Update knowledge base if protocol outdated
4. Escalate to clinical review board

## Post-Incident

1. Write incident report within 24 hours
2. Update runbook with lessons learned
3. Add regression test for root cause
4. Schedule retrospective
