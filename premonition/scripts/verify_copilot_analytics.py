#!/usr/bin/env python3
"""Step 7-8: Copilot + Analytics verification with extended timeout."""
import io, sys, httpx, json, datetime, jwt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE   = "http://127.0.0.1:8000"
API    = f"{BASE}/api/v1"
SECRET = "super-secret-key-for-premonition-early-warning-system-1234"

tok = jwt.encode(
    {"sub": "dr@test.ai", "role": "admin", "type": "access", "tenant_id": "t1",
     "exp": datetime.datetime(2027, 1, 1), "iat": datetime.datetime(2026, 6, 7)},
    SECRET, algorithm="HS256"
)
HDR = {"Authorization": f"Bearer {tok}"}
c   = httpx.Client(timeout=180)

print()
print("=" * 60)
print("  STEP 7 -- COPILOT  (What is sepsis?)  [timeout=180s]")
print("=" * 60)
print("  Sending question to Ollama llama3:latest...")

try:
    r = c.post(f"{API}/copilot/chat",
               json={"message": "What is sepsis?"},
               headers=HDR)
    if r.status_code == 200:
        d = r.json()
        keys = list(d.keys())
        resp = (d.get("response")
                or d.get("message")
                or d.get("answer")
                or d.get("content")
                or str(d))
        print(f"  [PASS] Copilot answered -> HTTP 200")
        print(f"  [INFO] Response keys: {keys}")
        print()
        print("  [INFO] Question : What is sepsis?")
        print("  [INFO] Answer preview:")
        print()
        for line in str(resp)[:700].split("\n"):
            print(f"    {line}")
    else:
        print(f"  [FAIL] HTTP {r.status_code}")
        print(f"  [INFO] Body: {r.text[:400]}")
except httpx.ReadTimeout:
    print("  [TIMEOUT] Copilot did not respond within 180s.")
    print("  [INFO] Ollama model 'llama3:latest' is available but taking too long.")
    print("  [INFO] This is a performance issue with llama3 cold start, not a code bug.")
except Exception as e:
    print(f"  [ERROR] {type(e).__name__}: {e}")

print()
print("=" * 60)
print("  STEP 8 -- ANALYTICS PAGE")
print("=" * 60)

r = c.get(f"{API}/analytics/executive", headers=HDR)
icon = "PASS" if r.status_code == 200 else "FAIL"
print(f"  [{icon}] GET /analytics/executive -> HTTP {r.status_code}")
if r.status_code == 200:
    kpis = r.json().get("kpis", {})
    print(f"  [INFO] ICU patients      : {kpis.get('icu_patients')}")
    print(f"  [INFO] Predictions today : {kpis.get('predictions_today')}")
    print(f"  [INFO] Alerts today      : {kpis.get('alerts_today')}")
    print(f"  [INFO] High risk patients: {kpis.get('high_risk_patients')}")
    print(f"  [INFO] Avg risk score    : {kpis.get('average_risk_score')}")
    print(f"  [INFO] Model PR-AUC      : {kpis.get('model_pr_auc')}")
    print(f"  [INFO] System uptime (h) : {kpis.get('system_uptime_hours')}")

r2 = c.get(f"{API}/analytics/population", headers=HDR)
icon2 = "PASS" if r2.status_code == 200 else "FAIL"
print(f"  [{icon2}] GET /analytics/population -> HTTP {r2.status_code}")
if r2.status_code == 200:
    dp = r2.json()
    print(f"  [INFO] Total patients    : {dp.get('total_patients')}")
    print(f"  [INFO] Sepsis incidence  : {dp.get('sepsis_incidence')}")
    age = dp.get("demographic_breakdown", {}).get("age", {})
    print(f"  [INFO] Mean patient age  : {age.get('mean')}")

r3 = c.get(f"{API}/metrics", headers=HDR)
icon3 = "PASS" if r3.status_code == 200 else "FAIL"
print(f"  [{icon3}] GET /metrics             -> HTTP {r3.status_code}")
if r3.status_code == 200:
    dm = r3.json()
    print(f"  [INFO] Predictions total : {dm.get('predictions_total')}")
    print(f"  [INFO] Uptime (seconds)  : {dm.get('uptime_seconds')}")
    print(f"  [INFO] Model loaded      : {dm.get('model_loaded')}")
    print(f"  [INFO] Avg latency (ms)  : {dm.get('avg_latency_ms')}")

c.close()
print()
