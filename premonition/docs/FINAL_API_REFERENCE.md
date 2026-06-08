# PREMONITION — API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | JWT login |
| POST | `/auth/refresh` | Refresh token |
| GET | `/auth/me` | Current user |
| POST | `/auth/api-keys` | Create API key |

## Core ML
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict` | Sepsis risk prediction |
| POST | `/explain` | SHAP explanation |
| GET | `/models` | Model registry |
| GET | `/audit/logs` | Audit trail |
| GET | `/metrics` | Operational metrics |

## Realtime
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/realtime/patients` | Live patient states |
| GET | `/realtime/alerts` | Alert history |
| GET | `/realtime/stream` | SSE event stream |
| WS | `/realtime/ws` | WebSocket stream |
| GET | `/realtime/executive` | Executive summary |

## Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/executive` | Executive intelligence |
| GET | `/analytics/kpis` | Hospital KPIs |
| GET | `/analytics/capacity` | Capacity planning |
| POST | `/analytics/recommendations` | Clinical recommendations |

## Copilot
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/copilot/chat` | AI chat |
| POST | `/copilot/explain-prediction` | Explain prediction |
| POST | `/copilot/patient-summary` | Patient summary |
| POST | `/copilot/handover` | Shift handover |
| POST | `/copilot/executive-summary` | Executive summary |
| POST | `/copilot/ingest-document` | RAG document ingest |
| POST | `/copilot/search` | Knowledge search |

## Multi-Tenant
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tenants` | List hospitals |
| POST | `/tenants/onboard` | Onboard hospital |
| GET | `/tenants/{id}/usage` | Usage metrics |
| GET | `/tenants/{id}/billing` | Billing plan |
| GET | `/organizations` | List organizations |

## Headers
- `Authorization: Bearer <jwt>` — JWT auth
- `X-API-Key: <key>` — API key auth
- `X-Tenant-ID: <tenant_id>` — Tenant context

Full interactive docs: `http://localhost:8000/docs`
