#!/usr/bin/env python3
"""Get full prediction response details for proof."""
import httpx, json, jwt, datetime

BASE = "http://127.0.0.1:8000"
API = f"{BASE}/api/v1"
SECRET = "super-secret-key-for-premonition-early-warning-system-1234"

payload = {
    "sub": "dr@test.ai",
    "role": "admin",
    "type": "access",
    "tenant_id": "t1",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    "iat": datetime.datetime.utcnow(),
}
token = jwt.encode(payload, SECRET, algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}

PATIENTS = [
    {
        "patient_id": "PT-CRITICAL-001",
        "features": {
            "age": 72, "gender": "M", "weight_kg": 90.0, "height_cm": 175.0, "bmi": 29.4,
            "ethnicity": "Caucasian", "insurance": "Medicare", "diabetes": 1, "hypertension": 1,
            "chf": 0, "copd": 1, "chronic_kidney_disease": 0, "liver_disease": 0,
            "immunosuppression": 0, "cad": 1, "atrial_fibrillation": 0, "cancer_active": 0,
            "hospital_admit_source": "Emergency", "icu_admit_time_hour": 2, "day_of_week": 1,
            "hr_mean": 115.0, "hr_max": 130.0, "hr_min": 95.0, "hr_std": 15.0,
            "sbp_mean": 90.0, "sbp_max": 105.0, "sbp_min": 75.0, "sbp_std": 10.0,
            "dbp_mean": 58.0, "dbp_max": 70.0, "dbp_min": 45.0, "dbp_std": 8.0,
            "map_mean": 69.0, "temp_celsius_mean": 39.1, "temp_celsius_max": 39.8,
            "temp_celsius_min": 38.5, "temp_celsius_std": 0.4,
            "spo2_mean": 89.0, "spo2_min": 85.0, "spo2_max": 93.0, "spo2_std": 2.5,
            "respiratory_rate_mean": 26.0, "respiratory_rate_max": 32.0,
            "respiratory_rate_min": 22.0, "respiratory_rate_std": 3.0,
        },
    },
    {
        "patient_id": "PT-MODERATE-002",
        "features": {
            "age": 55, "gender": "F", "weight_kg": 70.0, "height_cm": 162.0, "bmi": 26.7,
            "ethnicity": "Hispanic", "insurance": "Private", "diabetes": 0, "hypertension": 1,
            "chf": 0, "copd": 0, "chronic_kidney_disease": 0, "liver_disease": 0,
            "immunosuppression": 0, "cad": 0, "atrial_fibrillation": 0, "cancer_active": 0,
            "hospital_admit_source": "Transfer", "icu_admit_time_hour": 14, "day_of_week": 3,
            "hr_mean": 95.0, "hr_max": 108.0, "hr_min": 80.0, "hr_std": 8.0,
            "sbp_mean": 118.0, "sbp_max": 135.0, "sbp_min": 100.0, "sbp_std": 9.0,
            "dbp_mean": 76.0, "dbp_max": 88.0, "dbp_min": 62.0, "dbp_std": 7.0,
            "map_mean": 90.0, "temp_celsius_mean": 38.2, "temp_celsius_max": 38.9,
            "temp_celsius_min": 37.6, "temp_celsius_std": 0.3,
            "spo2_mean": 94.0, "spo2_min": 91.0, "spo2_max": 97.0, "spo2_std": 1.5,
            "respiratory_rate_mean": 20.0, "respiratory_rate_max": 25.0,
            "respiratory_rate_min": 16.0, "respiratory_rate_std": 2.2,
        },
    },
    {
        "patient_id": "PT-STABLE-003",
        "features": {
            "age": 42, "gender": "M", "weight_kg": 78.0, "height_cm": 180.0, "bmi": 24.1,
            "ethnicity": "Asian", "insurance": "Self-pay", "diabetes": 0, "hypertension": 0,
            "chf": 0, "copd": 0, "chronic_kidney_disease": 0, "liver_disease": 0,
            "immunosuppression": 0, "cad": 0, "atrial_fibrillation": 0, "cancer_active": 0,
            "hospital_admit_source": "Elective", "icu_admit_time_hour": 8, "day_of_week": 2,
            "hr_mean": 72.0, "hr_max": 85.0, "hr_min": 60.0, "hr_std": 6.0,
            "sbp_mean": 130.0, "sbp_max": 145.0, "sbp_min": 115.0, "sbp_std": 7.0,
            "dbp_mean": 82.0, "dbp_max": 92.0, "dbp_min": 70.0, "dbp_std": 5.0,
            "map_mean": 98.0, "temp_celsius_mean": 36.8, "temp_celsius_max": 37.2,
            "temp_celsius_min": 36.4, "temp_celsius_std": 0.2,
            "spo2_mean": 98.0, "spo2_min": 96.0, "spo2_max": 99.0, "spo2_std": 0.8,
            "respiratory_rate_mean": 15.0, "respiratory_rate_max": 18.0,
            "respiratory_rate_min": 12.0, "respiratory_rate_std": 1.5,
        },
    },
]

client = httpx.Client(timeout=30)

print("\n" + "="*65)
print("  PATIENT PREDICTION VALIDATION - FULL RESPONSE DETAILS")
print("="*65)

for p in PATIENTS:
    r = client.post(f"{API}/predict", json=p, headers=headers)
    d = r.json()

    # Extract top SHAP factor
    shap = d.get("shap", {})
    top_factors = d.get("top_factors", [])
    if isinstance(shap, dict) and shap:
        top_shap_key = max(shap, key=lambda k: abs(float(shap[k])))
        top_shap_val = shap[top_shap_key]
    elif top_factors:
        top_shap_key = top_factors[0] if isinstance(top_factors[0], str) else str(top_factors[0])
        top_shap_val = "N/A"
    else:
        top_shap_key = "N/A"
        top_shap_val = "N/A"

    risk_pct = float(d.get("risk_score", 0)) * 100
    cat = d.get("risk_category", "?")
    label = d.get("prediction_label", "?")
    conf = d.get("confidence", "?")
    explanation = d.get("explanation_summary", "No explanation")

    print(f"\n  Patient ID      : {p['patient_id']}")
    print(f"  Risk Score      : {d.get('risk_score')} ({risk_pct:.1f}%)")
    print(f"  Risk Category   : {cat.upper()}")
    print(f"  Prediction      : {label}")
    print(f"  Confidence      : {conf}")
    print(f"  Top SHAP Factor : {top_shap_key} = {top_shap_val}")
    print(f"  Agent Recommend : {explanation[:100]}")

    # Show all SHAP values sorted by magnitude
    if isinstance(shap, dict) and shap:
        sorted_shap = sorted(shap.items(), key=lambda x: abs(float(x[1])), reverse=True)
        print(f"  Top 5 SHAP Factors:")
        for fname, fval in sorted_shap[:5]:
            print(f"    -> {fname}: {float(fval):+.4f}")
    print()

# Also get the realtime monitoring agent logs
print("\n" + "="*65)
print("  AGENT PIPELINE EXECUTION TRACE")
print("="*65)

r = client.get(f"{API}/realtime/status", headers=headers)
status = r.json()
print(f"\n  MonitoringAgent  : running={status.get('running')} patients_monitored={status.get('patients_monitored')}")

r = client.get(f"{API}/realtime/priority", headers=headers)
priority = r.json()
critical = priority.get("critical", [])
if critical:
    p0 = critical[0]
    print(f"  PredictionAgent  : patient={p0.get('patient_id')} risk={p0.get('risk_score')} alert={p0.get('alert_level')}")

r = client.get(f"{API}/realtime/alerts", headers=headers)
alerts_data = r.json()
total = alerts_data.get("total_alerts", {})
count = total.get("count", 0) if isinstance(total, dict) else alerts_data.get("count", 0)
items = alerts_data.get("total_alerts", {}).get("items", []) if isinstance(total, dict) else alerts_data.get("items", [])
print(f"  ClinicalAgent    : total_alerts={count}")
if items:
    a0 = items[0]
    print(f"    Latest alert: patient={a0.get('patient_id')} level={a0.get('alert_level')} risk={a0.get('risk')}")

r = client.get(f"{API}/realtime/notifications", headers=headers)
notifs = r.json()
notif_count = notifs.get("count", 0)
print(f"  EscalationAgent  : notifications_dispatched={notif_count}")

r = client.get(f"{API}/realtime/executive", headers=headers)
exec_data = r.json()
print(f"  MemoryAgent      : high_risk_count={exec_data.get('high_risk_count')} critical_alerts={exec_data.get('critical_alert_count')}")

print()
print("="*65)
print("  LOGIN SECURITY VERIFICATION")
print("="*65)
protected = ["/api/v1/analytics/executive", "/api/v1/realtime/patients", "/api/v1/realtime/status"]
for ep in protected:
    r_no = client.get(f"{BASE}{ep}")
    ok = r_no.status_code == 401
    icon = "PASS" if ok else "FAIL"
    print(f"  [{icon}] {ep} (no token) -> HTTP {r_no.status_code} {'-> REDIRECTS TO LOGIN' if ok else ''}")

client.close()
print()
