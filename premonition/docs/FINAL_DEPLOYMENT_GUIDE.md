# PREMONITION — Final Deployment Guide

## Deployment Options

| Method | Use Case |
|--------|----------|
| Local dev | Development and demos |
| Docker Compose | Staging / single-node production |
| Kubernetes (Helm) | Production on-prem or cloud |
| Terraform (AWS/Azure/GCP) | Full cloud infrastructure |

## Quick Start — Local

```bash
pip install -r requirements-dev.txt
python scripts/train.py
python scripts/run_api.py          # :8000
cd frontend && npm install && npm run dev  # :5173
```

## Docker

```bash
docker compose up --build
docker compose --profile monitoring up  # + Prometheus/Grafana
```

## Kubernetes

```bash
kubectl apply -f infra/k8s/
helm upgrade --install premonition infra/helm/premonition -n premonition
```

## Cloud (Terraform)

```bash
cd infra/terraform
terraform init
terraform apply -var="cloud_provider=aws"   # or azure, gcp
```

See `infra/aws/DEPLOYMENT_GUIDE.md`, `infra/azure/DEPLOYMENT_GUIDE.md`, `infra/gcp/DEPLOYMENT_GUIDE.md`.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PREMONITION_JWT_SECRET` | Production | JWT signing key |
| `PREMONITION_API_KEY` | Optional | Legacy API key |
| `PREMONITION_REALTIME_ENABLED` | Optional | Enable live monitoring |
| `PREMONITION_LLM_PROVIDER` | Optional | mock (default), openai, azure |
| `PREMONITION_VECTOR_BACKEND` | Optional | inmemory, faiss, chroma |

## Multi-Tenant Setup

1. `POST /api/v1/tenants/onboard` — create org + hospital
2. Pass `X-Tenant-ID` header on all requests
3. Include `tenant_id` in JWT claims for mobile/web auth
