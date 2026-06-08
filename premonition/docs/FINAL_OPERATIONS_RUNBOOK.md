# PREMONITION — Operations Runbook

## Daily Operations

1. Check system health: `GET /api/v1/health`
2. Review alert volume: `GET /api/v1/realtime/alerts`
3. Check model metrics: `GET /api/v1/metrics`
4. Review tenant usage: `GET /api/v1/tenants/{id}/usage`

## Backup

```bash
python scripts/backup.py
# K8s: infra/k8s/backup-cronjob.yaml runs daily at 02:00 UTC
```

## Scaling

- **HPA**: auto-scales API pods 2–20 based on CPU (70%)
- **Manual**: `kubectl scale deployment premonition-api --replicas=5`
- **Tenant growth**: onboard via `/tenants/onboard`, no code changes needed

## Monitoring Alerts

| Alert | Action |
|-------|--------|
| High error rate | Check logs, restart pods |
| Model not loaded | Run training, check registry |
| Drift detected | Review MLOps dashboard, retrain |
| Tenant overage | Review billing, contact hospital admin |

## Deployment Updates

```bash
# Rolling update
kubectl set image deployment/premonition-api api=premonition/api:v2.0
# Helm
helm upgrade premonition infra/helm/premonition --set image.tag=v2.0
```

## Log Locations

| Log | Path |
|-----|------|
| Predictions | `logs/predictions/` |
| Auth | `logs/auth/` |
| Copilot audit | `logs/copilot/audit/` |
| Tenant data | `logs/tenants/{tenant_id}/` |
