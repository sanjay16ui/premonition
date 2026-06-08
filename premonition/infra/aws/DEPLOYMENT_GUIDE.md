# AWS Deployment Guide — PREMONITION

## Prerequisites
- AWS CLI v2, Terraform >= 1.5, kubectl, Helm 3
- IAM permissions: EKS, RDS, S3, Secrets Manager, CloudFront, WAF

## Quick Deploy

```bash
cd infra/terraform
terraform init
terraform plan -var="cloud_provider=aws" -var="environment=production"
terraform apply -var="cloud_provider=aws" -auto-approve
```

## Architecture
- **EKS** — API pods with HPA (2–20 replicas)
- **RDS PostgreSQL 15** — tenant metadata, audit, usage
- **S3** — model artifacts, documents, backups
- **Secrets Manager** — DB credentials, JWT secrets
- **CloudFront** — CDN for frontend static assets
- **WAF** — rate limiting (2000 req/min/IP)

## Post-Deploy

```bash
aws eks update-kubeconfig --name premonition-production-eks --region us-east-1
kubectl apply -f ../k8s/
helm upgrade --install premonition ../helm/premonition -n premonition
```

## Cost Estimate (Monthly)
| Resource | Estimate |
|----------|----------|
| EKS cluster | $73 |
| 3× t3.large nodes | $180 |
| RDS db.r6g.large | $350 |
| S3 + CloudFront | $50 |
| Secrets Manager | $5 |
| **Total** | **~$660/mo** |

## Production Checklist
- [ ] Enable multi-region (`enable_multi_region=true`)
- [ ] Configure Route53 DNS
- [ ] Set `PREMONITION_JWT_SECRET` in Secrets Manager
- [ ] Enable RDS automated backups (7-day retention)
- [ ] Configure Prometheus/Grafana monitoring profile
- [ ] Run disaster recovery drill
