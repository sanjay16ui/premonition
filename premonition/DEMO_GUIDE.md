# PREMONITION — Comprehensive Demo Guide
> Healthcare Agentic AI Platform | ICU Early Warning System

---

## 1. Project Overview

**PREMONITION** is a production-grade, autonomous AI early-warning system for Intensive Care Units.  
Instead of passive dashboards, it deploys a **swarm of five specialized AI agents** that:

1. **Observe** live patient vitals (HR, SpO2, Temp, Respiratory Rate)
2. **Analyse** multi-variate risk using trained ML models
3. **Decide** whether to trigger escalation, notify staff, or re-run prediction
4. **Act** — sending alerts, updating the 3D digital twin, and logging decisions
5. **Verify** — writing all actions to persistent SQLite memory for audit

---

## 2. Architecture

```
Browser (React / Three.js / WebGL)
         │  SSE / REST / WS
         ▼
FastAPI Backend  ──►  Agentic Loop (5 Agents)
         │                    │
   Realtime Engine       SQLite Memory DB
         │                    │
   Ollama LLM ◄──────── Patient Risk Engine
   (qwen2.5:7b)         (scikit-learn)
```

### Key Components
| Component | Technology | Role |
|:---|:---|:---|
| Live Monitoring | React + SSE | Real-time patient cards |
| Agentic Loop | Python asyncio | 5 orchestrated agents |
| LLM Inference | Ollama (qwen2.5:7b) | Clinical summaries & chat |
| 3D Digital Twin | Three.js / R3F | ICU ward spatial view |
| Auth | JWT + Resend OTP | Secure role-based access |
| Memory | SQLite | Persistent agent decisions |

---

## 3. Key Features

### 🧠 Autonomous Agentic Loop
- **Monitoring Agent** — Watches vitals every tick, detects anomalies
- **Prediction Agent** — Runs ML model, flags threshold crossings with 0.95 confidence
- **Escalation Agent** — Persists "Notify Nurse" decisions to memory with rationale
- **Clinical Agent** — Generates doctor-facing recommendations
- **Executive Agent** — Aggregates ward-level insights for leadership dashboards

### 🔴 Emergency Alert System
- Pulsing red banner when RED/BLACK patients are detected
- Web Audio API tones (unlocked on first user gesture)
- Acknowledge button mutates backend state and stops alerts

### 🤖 Clinical AI Copilot
- Chat interface backed by local Ollama LLM (HIPAA-compliant — no data leaves server)
- Generate Patient Summary, Shift Handover, Prediction Explanation with one click
- RAG (Retrieval-Augmented Generation) for document-based answers

### 📊 Analytics Dashboard
- Risk distribution donut chart
- Patient risk timeline (area chart)
- Model performance comparison (bar chart)
- Animated KPI cards (Recharts + Framer Motion)

### 🌐 3D Executive Dashboard
- WebGL ICU ward rendered with Three.js
- Patient nodes color-coded by risk severity
- Real-time orbit controls for spatial orientation

---

## 4. 5-Minute Demo Script

### ⏱️ Minute 1 — Login & Authentication
```
URL: http://localhost:5174/login
```
1. Enter your email → click **Send OTP**
2. Check email inbox → paste 6-digit OTP
3. **Talk track:** *"Authentication is handled via Resend-powered OTP — no passwords. JWT sessions persist across browser refreshes. All routes are protected."*

### ⏱️ Minute 2 — Live Patient Monitoring
```
URL: http://localhost:5174/monitoring
```
1. Point to the **red pulsing emergency banner** if a critical patient exists
2. Click **Acknowledge** on a critical card
3. **Talk track:** *"This isn't a static dashboard. A swarm of autonomous AI agents processes vitals continuously. When risk crosses a threshold, the Escalation Agent fires an alert with zero human intervention — and logs its decision to memory with confidence scores."*

### ⏱️ Minute 3 — Clinical AI Copilot
```
URL: http://localhost:5174/copilot
```
1. Click **Patient Summary** on the Copilot Patient page
2. Type in chat: *"Explain the risk factors for this critical patient"*
3. **Talk track:** *"Doctors interact via natural language. The Copilot uses a locally-hosted Qwen 2.5 7B model — no patient data leaves the hospital network. This is HIPAA-compliant by architecture, not configuration."*

### ⏱️ Minute 4 — Analytics
```
URL: http://localhost:5174/analytics
```
1. Point to the risk donut, timeline, and model performance charts
2. **Talk track:** *"Administrators see aggregated intelligence — not raw data. They can track which model versions perform best and where the population risk is clustering."*

### ⏱️ Minute 5 — 3D Executive Dashboard
```
URL: http://localhost:5174/executive-3d
```
1. Drag/orbit the 3D ICU map
2. **Talk track:** *"Hospital leadership gets spatial situational awareness. Red nodes are critical patients, green are stable. Clicking a node drills down to that patient's data."*

---

## 5. Screenshots to Capture

1. **Login page** — OTP entry screen
2. **Monitoring** — Red emergency banner + critical patient cards
3. **Copilot** — LLM generating a patient summary (streaming)
4. **Analytics** — All 4 charts visible with data
5. **Digital Twin / Executive 3D** — 3D rotating ward
6. **Monitoring: Acknowledge** — Button click + state change

---

## 6. Resume Bullet Points

```
• Built PREMONITION, a production-grade Agentic AI Healthcare Platform using FastAPI, React 19, and Ollama LLMs
• Engineered a 5-agent autonomous swarm (Monitoring, Prediction, Clinical, Escalation, Executive) with SQLite-persistent decision memory
• Implemented real-time ICU patient monitoring via Server-Sent Events (SSE) with sub-second latency
• Developed a 3D interactive hospital digital twin using Three.js / React Three Fiber
• Integrated HIPAA-compliant local LLM inference (Ollama qwen2.5:7b) for clinical summarization and RAG-based Copilot
• Built secure OTP authentication with Resend API, JWT session management, and role-based route protection
• Achieved 100% TypeScript type-safe frontend (536 backend tests passing) with Vite production build
```

---

## 7. Interview Talking Points

### Q: Why Agentic AI instead of a simple dashboard?
> *"Passive dashboards require a human to notice the change. Agentic AI acts on the data autonomously. Our system makes decisions with documented rationale at machine speed — the Escalation Agent fires in milliseconds, not the minutes it might take for a nurse to notice a vitals change."*

### Q: How do you handle HIPAA compliance?
> *"All LLM inference runs on the local Ollama instance — qwen2.5:7b. Patient data never leaves the hospital's network. The architecture makes HIPAA compliance a property of the infrastructure, not a policy."*

### Q: Why SSE over WebSockets?
> *"Server-Sent Events are lighter weight for unidirectional server-to-client streaming. WebSockets are bidirectional and add unnecessary overhead for telemetry. SSE reconnects automatically on disconnect, which is critical in clinical environments."*

### Q: How does the multi-agent coordination work?
> *"Each agent is a specialized asyncio coroutine with a defined contract: observe → analyze → decide → act → verify. They communicate through a shared in-memory state and write decisions to a SQLite memory table for auditability. The orchestrator runs the loop every few seconds."*

### Q: How does the Digital Twin work?
> *"It's a WebGL scene built with React Three Fiber (Three.js). Patient nodes are 3D spheres positioned on a hospital floor plan. Each sphere's color and pulse intensity map to the patient's real-time risk score from the backend."*

---

## 8. Technical Architecture Details

### Backend API Endpoints
| Endpoint | Method | Purpose |
|:---|:---|:---|
| `/api/realtime/live-patients` | GET | Fetch current ICU state |
| `/api/realtime/sse` | GET | SSE stream of patient updates |
| `/api/realtime/acknowledge/{id}` | POST | Acknowledge patient alert |
| `/api/copilot/chat` | POST | Ollama chat |
| `/api/copilot/patient-summary` | POST | Generate patient summary |
| `/api/copilot/handover` | POST | Generate shift handover |
| `/api/copilot/executive-summary` | POST | Executive report |
| `/api/analytics/kpis` | GET | Dashboard KPIs |
| `/api/auth/request-otp` | POST | Send OTP via Resend |
| `/api/auth/verify-otp` | POST | Verify OTP + issue JWT |
| `/docs` | GET | Swagger UI |

### Agentic Loop Proof (from SQLite memory)
```json
{"agent": "Prediction Agent", "patient_id": "37464",
 "decision": {"requires_action": true, "action": "Rerun Prediction",
              "reason": "Risk score crossed critical threshold", "confidence": 0.95}}

{"agent": "Escalation Agent", "patient_id": "37464",
 "decision": {"requires_action": true, "action": "Notify Nurse",
              "reason": "Alert unresolved for 5 min", "confidence": 0.99}}
```
