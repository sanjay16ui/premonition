# PREMONITION — Portfolio & GitHub Guide
> Autonomous Agentic AI Healthcare Platform

---

## GitHub Description (160 chars)

```
PREMONITION: Autonomous Agentic AI early-warning system for hospital ICUs. Multi-agent swarm, real-time SSE, 3D digital twin, local LLM Copilot. FastAPI + React 19 + Ollama.
```

---

## GitHub Topics / Tags

```
agentic-ai  healthcare-ai  fastapi  react  typescript  ollama  llm  icu-monitoring
digital-twin  three-js  sse  multi-agent  medical-ai  python  websocket  realtime
```

---

## Project Highlights

### 🧠 Agentic AI Multi-Agent System
Five specialized agents work autonomously in a continuous loop:
- **Monitoring Agent** — Detects vitals anomalies each tick
- **Prediction Agent** — ML model inference with 0.95 confidence scoring
- **Escalation Agent** — Auto-notifies staff for unresolved alerts (0.99 confidence)
- **Clinical Agent** — Drafts actionable doctor recommendations
- **Executive Agent** — Aggregates ward-level risk intelligence

All decisions are persisted to a SQLite `decision_memory` table with timestamps and rationale — providing a full audit trail.

### 📡 Real-Time Data Pipeline
- **Server-Sent Events (SSE)** for unidirectional telemetry streaming
- Sub-second latency from vitals change → UI update
- Automatic reconnection on network interruption
- WebSocket fallback for bidirectional scenarios

### 🏥 3D ICU Digital Twin
- React Three Fiber (Three.js) WebGL scene
- Real-time patient nodes colored by risk severity
- Interactive orbit controls — zoom, rotate, click to drill down
- Glassmorphic control panels overlay

### 🤖 HIPAA-Compliant Clinical Copilot
- Local LLM (Ollama `qwen2.5:7b`) — no data leaves the server
- Streaming responses with typing indicator
- Patient Summary, Shift Handover, Risk Explanation in one click
- RAG (Retrieval-Augmented Generation) for evidence-based answers

### 🔐 Enterprise Authentication
- OTP via Resend API (no passwords)
- JWT session with refresh token rotation
- All routes protected with global 401 interceptor
- Role-based access control (RBAC)

---

## Tech Stack

### Backend
| Technology | Purpose |
|:---|:---|
| Python 3.13 | Core language |
| FastAPI | Async REST API + SSE |
| Pydantic v2 | Schema validation |
| SQLite (aiosqlite) | Agent memory persistence |
| asyncio | Concurrent agentic loop |
| scikit-learn | Risk prediction model |
| Resend API | OTP email delivery |
| JWT | Session management |

### Frontend
| Technology | Purpose |
|:---|:---|
| React 19 | UI framework |
| TypeScript | Type safety |
| Vite | Build tooling |
| React Three Fiber | 3D WebGL scenes |
| Zustand | Global state |
| TanStack Query | Server state / caching |
| Recharts | Data visualizations |
| Framer Motion | Animations |
| Lucide React | Icon library |

### AI / ML
| Technology | Purpose |
|:---|:---|
| Ollama (qwen2.5:7b) | Local LLM inference |
| scikit-learn | Multi-variate risk model |
| Agentic Architecture | Observe-Analyze-Decide-Act loop |
| RAG Pattern | Document-grounded answers |

### Infrastructure
| Technology | Purpose |
|:---|:---|
| Docker / Docker Compose | Container orchestration |
| Kubernetes YAML | Production deployment manifests |
| AWS / Azure / GCP configs | Multi-cloud ready |
| GitHub Actions | CI/CD pipeline |

---

## Impact Metrics

| Metric | Value |
|:---|:---|
| Backend test suite | **536 tests** |
| Frontend TypeScript | **Zero type errors** |
| Build time | **4.82 seconds** (Vite) |
| Agentic loop latency | **< 1 second** observe-to-alert |
| LLM inference (CPU) | **2.5 tok/s** (qwen2.5:7b CPU-only) |
| Patient data egress | **Zero** (all inference local) |
| Pages | **8** fully functional routes |

---

## Recruiter-Friendly Summary

I designed and built **PREMONITION** — an enterprise-grade Agentic AI healthcare platform — from scratch.

Unlike a simple "AI chatbot" or dashboard project, this system:

- **Acts autonomously**: Five AI agents coordinate to monitor, predict, and escalate clinical events without any human-in-the-loop requirement.
- **Handles real data flows**: A continuous async pipeline processes simulated ICU telemetry streams at high frequency, demonstrated via SSE.
- **Is production-ready**: Docker containerized, Kubernetes-deployable, 536 pytest tests, TypeScript-strict, CI/CD-ready.
- **Solves a real problem**: ICU patient deterioration detection is a $2B+ market. PREMONITION demonstrates the architecture that next-generation clinical AI will use.

**Skills demonstrated**: Full-Stack Engineering (FastAPI / React 19 / TypeScript), Agentic AI Architecture, Real-Time Systems (SSE), 3D Visualization (Three.js), Local LLM Integration (Ollama), Enterprise Authentication (JWT + OTP), Production DevOps (Docker / K8s).

---

## Folder Structure

```
premonition/
├── src/premonition/         # Python backend
│   ├── api/                 # FastAPI routers
│   ├── copilot/             # LLM + RAG + Agents
│   │   ├── llm/             # Ollama / OpenAI / Azure providers
│   │   ├── agents/          # 5 specialized agents
│   │   └── orchestrator.py  # Agent loop coordinator
│   ├── realtime/            # SSE engine
│   ├── intelligence/        # ML risk model
│   ├── auth/                # JWT + OTP
│   └── models/              # Pydantic schemas
├── frontend/src/
│   ├── pages/               # 8 route pages
│   ├── components/          # Reusable UI components
│   ├── api/                 # Axios + React Query hooks
│   ├── store/               # Zustand stores
│   ├── three/               # Three.js / R3F scenes
│   └── hooks/               # Custom React hooks
├── tests/                   # 536 pytest tests
├── infra/                   # K8s, Helm, AWS, Azure, GCP
├── DEMO_GUIDE.md            # Step-by-step demo script
└── docker-compose.yml       # One-command startup
```

---

## Quick Start

```bash
# 1. Start Ollama
ollama serve
ollama pull qwen2.5:7b

# 2. Start backend
python scripts/run_api.py

# 3. Start frontend
cd frontend && npm run dev

# 4. Open
http://localhost:5174
```

---

## Related Projects / Inspiration
- Palantir Foundry — Enterprise intelligence platform
- Datadog — Real-time observability
- Epic Systems — Clinical decision support
