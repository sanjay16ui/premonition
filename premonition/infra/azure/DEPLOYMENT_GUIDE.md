# Azure Deployment Guide — PREMONITION

## Prerequisites
- Azure CLI, Terraform >= 1.5, kubectl, Helm 3
- Subscription with AKS, PostgreSQL Flexible Server, Key Vault permissions

## Quick Deploy

```bash
az login
cd infra/terraform
terraform init
terraform apply -var="cloud_provider=azure" -auto-approve
```

## Architecture
- **AKS** — 3-node cluster with autoscaling
- **PostgreSQL Flexible Server** — managed database
- **Azure Blob Storage** — artifacts and documents
- **Key Vault** — secrets management
- **WAF Policy** — OWASP 3.2 rules

## Post-Deploy

```bash
az aks get-credentials --resource-group premonition-production-rg --name premonition-production-aks
kubectl apply -f ../k8s/
helm upgrade --install premonition ../helm/premonition -n premonition
```

## Cost Estimate (Monthly)
| Resource | Estimate |
|----------|----------|
| AKS control plane | $73 |
| 3× Standard_D4s_v3 | $420 |
| PostgreSQL GP_Standard_D4s_v3 | $380 |
| Storage GRS | $40 |
| Key Vault | $5 |
| **Total** | **~$920/mo** |

## Production Checklist
- [ ] Enable Azure AD integration for RBAC
- [ ] Configure Application Gateway ingress
- [ ] Set Key Vault access policies
- [ ] Enable geo-redundant backups
- [ ] Configure Azure Monitor alerts
