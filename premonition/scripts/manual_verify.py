#!/usr/bin/env python3
"""PREMONITION Manual Verification — All 10 steps."""
import io, sys, httpx, json, datetime, jwt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
API  = f"{BASE}/api/v1"
FE   = "http://localhost:5173"
SECRET = "super-secret-key-for-premonition-early-warning-system-1234"

tok = jwt.encode(
    {"sub": "dr@test.ai", "role": "admin", "type": "access", "tenant_id": "t1",
     "exp": datetime.datetime(2027, 1, 1), "iat": datetime.datetime(2026, 6, 7)},
    SECRET, algorithm="HS256"
)
HDR = {"Authorization": f"Bearer {tok}"}
c = httpx.Client(timeout=30)

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

def chk(label, r, expected=200):
    ok = r.status_code == expected
    print(f"  {PASS if ok else FAIL} {label} -> HTTP {r.status_code}")
    return ok

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

results = {}

# ─── STEP 1: BACKEND ─────────────────────────────────────────────
sep("STEP 1 — BACKEND STATUS")
results["backend_health"] = chk("GET /health (public)", c.get(f"{BASE}/health"))
r2 = c.get(f"{API}/health")
results["api_health"] = chk("GET /api/v1/health", r2)
r3 = c.get(f"{BASE}/docs")
results["swagger_docs"] = chk("GET /docs (Swagger UI)", r3)
if r2.status_code == 200:
    print(f"  {INFO} Backend response: {json.dumps(r2.json())}")
# Show model info
rv = c.get(f"{API}/models/version", headers=HDR)
if rv.status_code == 200:
    dv = rv.json()
    print(f"  {INFO} Model: {dv.get('model_name')} | Features: {dv.get('n_features')} | Tier: {dv.get('tier')}")

# ─── STEP 2: FRONTEND ────────────────────────────────────────────
sep("STEP 2 — FRONTEND STATUS")
try:
    rf = httpx.get(FE, timeout=10, follow_redirects=True)
    results["frontend"] = rf.status_code == 200
    print(f"  {PASS if results['frontend'] else FAIL} Frontend accessible -> HTTP {rf.status_code}")
    ct = rf.headers.get("content-type", "?")
    print(f"  {INFO} Content-Type: {ct}")
    has_html = b"<html" in rf.content or b"<!DOCTYPE" in rf.content or b"<div" in rf.content
    print(f"  {INFO} HTML content detected: {has_html}")
    print(f"  {INFO} Response size: {len(rf.content)} bytes")
except Exception as e:
    results["frontend"] = False
    print(f"  {FAIL} Frontend error: {e}")

# ─── STEP 3: OLLAMA ──────────────────────────────────────────────
sep("STEP 3 — OLLAMA CONNECTION")
try:
    ro = httpx.get("http://localhost:11434", timeout=5)
    results["ollama"] = True
    print(f"  {PASS} Ollama server reachable -> HTTP {ro.status_code}")
    # Check available models
    rm = httpx.get("http://localhost:11434/api/tags", timeout=5)
    if rm.status_code == 200:
        models = rm.json().get("models", [])
        names = [m.get("name", "?") for m in models]
        print(f"  {INFO} Available models: {names}")
    else:
        print(f"  {INFO} /api/tags -> HTTP {rm.status_code}")
except Exception as e:
    results["ollama"] = False
    print(f"  {FAIL} Ollama not reachable: {e}")
    print(f"  {INFO} To start: ollama serve  (in a separate terminal)")
r_sys = c.get(f"{API}/system/status", headers=HDR)
if r_sys.status_code == 200:
    ds = r_sys.json()
    print(f"  {INFO} System status: {json.dumps(ds, default=str)[:300]}")

# ─── STEP 4: LOGIN PAGE ──────────────────────────────────────────
sep("STEP 4 — LOGIN PAGE & OTP EMAIL")
r_otp = c.post(f"{API}/auth/request-otp", json={"email": "sanjaykumarsk0416@gmail.com"})
results["otp_request"] = chk("POST /auth/request-otp (OTP email)", r_otp)
if r_otp.status_code == 200:
    d = r_otp.json()
    print(f"  {INFO} Message : {d.get('message')}")
    print(f"  {INFO} Expires : {d.get('expires_in_seconds')}s")
    print(f"  {INFO} Masked  : {d.get('masked_email')}")
    print(f"  {INFO} OTP email sent to: sanjaykumarsk0416@gmail.com")

# ─── STEP 5: OVERVIEW PAGE ───────────────────────────────────────
sep("STEP 5 — OVERVIEW PAGE")
r_exec = c.get(f"{API}/realtime/executive", headers=HDR)
results["overview_executive"] = chk("GET /realtime/executive", r_exec)
r_pats = c.get(f"{API}/realtime/patients", headers=HDR)
results["overview_patients"] = chk("GET /realtime/patients", r_pats)
if r_exec.status_code == 200:
    de = r_exec.json()
    print(f"  {INFO} ICU patients     : {de.get('current_icu_patients')}")
    print(f"  {INFO} High risk count  : {de.get('high_risk_count')}")
    print(f"  {INFO} Critical alerts  : {de.get('critical_alert_count')}")
    print(f"  {INFO} Avg risk score   : {de.get('average_risk_score')}")
r_met = c.get(f"{API}/metrics", headers=HDR)
if r_met.status_code == 200:
    dm = r_met.json()
    print(f"  {INFO} Predictions total: {dm.get('predictions_total')}")
    print(f"  {INFO} Uptime (seconds) : {dm.get('uptime_seconds')}")

# ─── STEP 6: LIVE MONITORING ─────────────────────────────────────
sep("STEP 6 — LIVE MONITORING PAGE")
r_stat = c.get(f"{API}/realtime/status", headers=HDR)
results["monitoring_status"] = chk("GET /realtime/status", r_stat)
if r_stat.status_code == 200:
    ds2 = r_stat.json()
    print(f"  {INFO} Running : {ds2.get('running')}")
    print(f"  {INFO} Patients: {ds2.get('patients_monitored')}")

r_prio = c.get(f"{API}/realtime/priority", headers=HDR)
results["monitoring_priority"] = chk("GET /realtime/priority", r_prio)
if r_prio.status_code == 200:
    dp = r_prio.json()
    crit = dp.get("critical", [])
    if crit:
        p0 = crit[0]
        print(f"  {INFO} Top critical: {p0.get('patient_id')} risk={p0.get('risk_score')} alert={p0.get('alert_level')}")
    print(f"  {INFO} Total critical patients: {len(crit)}")

r_alrt = c.get(f"{API}/realtime/alerts", headers=HDR)
results["monitoring_alerts"] = chk("GET /realtime/alerts", r_alrt)
r_notif = c.get(f"{API}/realtime/notifications", headers=HDR)
results["monitoring_notifications"] = chk("GET /realtime/notifications", r_notif)
if r_notif.status_code == 200:
    dn = r_notif.json()
    print(f"  {INFO} Active notifications: {dn.get('count')}")

# ─── STEP 7: COPILOT ─────────────────────────────────────────────
sep("STEP 7 — COPILOT (What is sepsis?)")
r_cop = c.post(f"{API}/copilot/chat",
               json={"message": "What is sepsis?"},
               headers=HDR, timeout=60)
results["copilot"] = r_cop.status_code == 200
if r_cop.status_code == 200:
    dc = r_cop.json()
    resp_text = dc.get("response", dc.get("message", dc.get("answer", dc.get("content", str(dc)))))
    print(f"  {PASS} Copilot answered -> HTTP 200")
    print(f"  {INFO} Question : What is sepsis?")
    print(f"  {INFO} Answer   : {str(resp_text)[:400]}")
    print(f"  {INFO} Response keys: {list(dc.keys())}")
else:
    print(f"  {FAIL} Copilot -> HTTP {r_cop.status_code}")
    print(f"  {INFO} Error: {r_cop.text[:300]}")

# ─── STEP 8: ANALYTICS ───────────────────────────────────────────
sep("STEP 8 — ANALYTICS PAGE")
r_ae = c.get(f"{API}/analytics/executive", headers=HDR)
results["analytics_executive"] = chk("GET /analytics/executive", r_ae)
if r_ae.status_code == 200:
    da = r_ae.json()
    kpis = da.get("kpis", {})
    print(f"  {INFO} ICU patients     : {kpis.get('icu_patients')}")
    print(f"  {INFO} Predictions today: {kpis.get('predictions_today')}")
    print(f"  {INFO} Model PR-AUC     : {kpis.get('model_pr_auc')}")
    print(f"  {INFO} System uptime    : {kpis.get('system_uptime_hours')}h")

r_ap = c.get(f"{API}/analytics/population", headers=HDR)
results["analytics_population"] = chk("GET /analytics/population", r_ap)
if r_ap.status_code == 200:
    dp2 = r_ap.json()
    print(f"  {INFO} Total patients   : {dp2.get('total_patients')}")
    print(f"  {INFO} Sepsis incidence : {dp2.get('sepsis_incidence')}")

# ─── SECURITY CHECK ──────────────────────────────────────────────
sep("STEP 9 — LOGIN SECURITY (No-Token = 401)")
for ep in ["/api/v1/analytics/executive", "/api/v1/realtime/patients", "/api/v1/copilot/chat"]:
    r_no = c.get(f"{BASE}{ep}")
    ok = r_no.status_code == 401
    print(f"  {PASS if ok else FAIL} {ep} without token -> HTTP {r_no.status_code}")

c.close()

# ─── FINAL SUMMARY ───────────────────────────────────────────────
sep("FINAL VERIFICATION SUMMARY")
passed = sum(1 for v in results.values() if v)
total  = len(results)
print()
for k, v in results.items():
    print(f"  {PASS if v else FAIL} {k}")
print()
print(f"  TOTAL: {passed}/{total} checks passed")
print()
print("  URLs:")
print(f"    Frontend URL  : {FE}")
print(f"    Backend URL   : {BASE}")
print(f"    Login URL     : {FE}/login")
print(f"    API Docs URL  : {BASE}/docs")
print(f"    Backend Health: {BASE}/health")
print()
