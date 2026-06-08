# PREMONITION — Admin Manual

## Tenant Management

### Onboard New Hospital

```bash
curl -X POST http://localhost:8000/api/v1/tenants/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "organization": {"name": "City Health", "slug": "city-health", "contact_email": "admin@city.com"},
    "tenant": {"hospital_name": "City General", "slug": "city-general", "organization_id": "x", "bed_capacity": 300, "icu_beds": 60},
    "admin_email": "admin@citygeneral.com",
    "admin_role": "admin"
  }'
```

### Manage Tenants
- `GET /api/v1/tenants` — list all hospitals
- `PATCH /api/v1/tenants/{id}/config` — update feature flags
- `GET /api/v1/tenants/{id}/usage` — view API usage
- `GET /api/v1/tenants/{id}/billing` — view plan limits

## User Management

Default users (change passwords in production):
| Email | Role | Password |
|-------|------|----------|
| admin@premonition.health | admin | AdminPass123! |
| clinician@premonition.health | clinician | Clinician123! |
| executive@premonition.health | executive | Executive123! |
| auditor@premonition.health | auditor | Auditor123! |

## Model Management

```bash
python scripts/train.py                    # Train models
python scripts/explain.py                # Generate SHAP reports
curl http://localhost:8000/api/v1/models   # View registry
```

## MLOps

- `POST /api/v1/mlops/promote` — promote model to production
- `GET /api/v1/mlops/drift` — check data drift
- `GET /api/v1/mlops/monitoring` — model health metrics

## Monitoring

```bash
docker compose --profile monitoring up    # Prometheus + Grafana
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```
