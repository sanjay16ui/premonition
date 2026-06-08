# PREMONITION — Portfolio Guide

## Project Summary

**PREMONITION** is a full-stack enterprise healthcare AI platform for ICU sepsis early warning, built across 16 development sections as a production-ready portfolio project.

## Key Highlights

- **ML**: XGBoost ensemble with SHAP explainability, MLOps drift detection
- **Realtime**: Live ICU monitoring with 5-level alert escalation, SSE/WebSocket
- **Analytics**: 20-module enterprise analytics engine
- **AI Copilot**: RAG-powered clinical assistant with citation attribution
- **SaaS**: Multi-tenant architecture supporting 1000+ hospitals
- **Cloud**: Terraform IaC for AWS, Azure, GCP
- **Mobile**: React Native app for Android/iOS
- **Security**: JWT/RBAC, tenant isolation, AI audit logging

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.13, FastAPI, Pydantic, XGBoost, SHAP |
| Frontend | React 19, Vite, Tailwind, Recharts, Three.js |
| Mobile | React Native, Expo, TanStack Query |
| Infra | Docker, Kubernetes, Helm, Terraform |
| Monitoring | Prometheus, Grafana |

## Demo URLs (Local)

| Feature | URL |
|---------|-----|
| Web App | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| Analytics Dashboard | http://localhost:5173/analytics |
| AI Copilot | http://localhost:5173/copilot |
| 3D Digital Twin | http://localhost:5173/digital-twin |
| Tenant Management | http://localhost:5173/tenants |

## Resume Bullet Points

- Built enterprise Clinical AI Copilot with RAG retrieval, multi-LLM provider abstraction, and full audit compliance
- Designed multi-tenant SaaS platform with row-level security for 1000+ hospital scalability
- Implemented real-time ICU monitoring with SSE/WebSocket streaming and 5-level alert escalation
- Created Terraform multi-cloud deployment (AWS/Azure/GCP) with WAF, CDN, and auto-scaling
- Achieved 500+ backend and 100+ frontend tests with zero regressions
