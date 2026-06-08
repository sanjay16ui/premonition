# GCP Deployment Guide — PREMONITION

## Prerequisites
- gcloud CLI, Terraform >= 1.5, kubectl, Helm 3
- GCP project with GKE, Cloud SQL, Cloud Storage APIs enabled

## Quick Deploy

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
cd infra/terraform
terraform init
terraform apply -var="cloud_provider=gcp" -auto-approve
```

## Architecture
- **GKE** — regional cluster with node autoscaling (2–20)
- **Cloud SQL PostgreSQL 15** — HA with PITR backups
- **Cloud Storage** — versioned bucket for artifacts
- **Secret Manager** — credentials
- **Cloud CDN + Security Policy** — CDN and WAF

## Post-Deploy

```bash
gcloud container clusters get-credentials premonition-production-gke --zone us-central1-a
kubectl apply -f ../k8s/
helm upgrade --install premonition ../helm/premonition -n premonition
```

## Cost Estimate (Monthly)
| Resource | Estimate |
|----------|----------|
| GKE control plane | $73 |
| 3× e2-standard-4 | $290 |
| Cloud SQL db-custom-4-16384 | $400 |
| Cloud Storage | $30 |
| Secret Manager | $3 |
| **Total** | **~$800/mo** |

## Production Checklist
- [ ] Enable Workload Identity
- [ ] Configure Cloud Armor WAF rules
- [ ] Set up Cloud CDN for frontend
- [ ] Enable Cloud SQL automated backups
- [ ] Configure Cloud Monitoring dashboards
