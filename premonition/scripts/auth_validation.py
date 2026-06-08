#!/usr/bin/env python3
"""PREMONITION Authenticated Validation -- Full end-to-end proof with JWT auth."""

from __future__ import annotations
import json
import datetime
import sys

import httpx
import jwt

BASE = "http://127.0.0.1:8000"
API = f"{BASE}/api/v1"
JWT_SECRET = "super-secret-key-for-premonition-early-warning-system-1234"

SAMPLE_FEATURES = {
    "age": 65,
    "gender": "M",
    "weight_kg": 85.0,
    "height_cm": 175.0,
    "bmi": 27.8,
    "ethnicity": "Caucasian",
    "insurance": "Medicare",
    "diabetes": 1,
    "hypertension": 1,
    "chf": 0,
    "copd": 0,
    "chronic_kidney_disease": 0,
    "liver_disease": 0,
    "immunosuppression": 0,
    "cad": 1,
    "atrial_fibrillation": 0,
    "cancer_active": 0,
    "hospital_admit_source": "Emergency",
    "icu_admit_time_hour": 14,
    "day_of_week": 3,
    "hr_mean": 88.0, "hr_max": 110.0, "hr_min": 65.0, "hr_std": 12.0,
    "sbp_mean": 125.0, "sbp_max": 145.0, "sbp_min": 100.0, "sbp_std": 10.0,
    "dbp_mean": 78.0, "dbp_max": 92.0, "dbp_min": 60.0, "dbp_std": 8.0,
    "map_mean": 93.0,
    "temp_celsius_mean": 37.2, "temp_celsius_max": 38.1, "temp_celsius_min": 36.5, "temp_celsius_std": 0.4,
    "spo2_mean": 96.0, "spo2_min": 92.0, "spo2_max": 99.0, "spo2_std": 1.5,
    "respiratory_rate_mean": 18.0, "respiratory_rate_max": 24.0, "respiratory_rate_min": 14.0, "respiratory_rate_std": 2.5,
}

# Three different patient profiles
PATIENT_PROFILES = [
    {
        "patient_id": "PT-CRITICAL-001",
        "features": {**SAMPLE_FEATURES, "age": 72, "hr_mean": 115.0, "temp_celsius_mean": 39.1,
                     "spo2_mean": 89.0, "respiratory_rate_mean": 26.0, "sbp_mean": 90.0}
    },
    {
        "patient_id": "PT-MODERATE-002",
        "features": {**SAMPLE_FEATURES, "age": 55, "hr_mean": 95.0, "temp_celsius_mean": 38.2,
                     "spo2_mean": 94.0, "respiratory_rate_mean": 20.0, "sbp_mean": 118.0}
    },
    {
        "patient_id": "PT-STABLE-003",
        "features": {**SAMPLE_FEATURES, "age": 42, "hr_mean": 72.0, "temp_celsius_mean": 36.8,
                     "spo2_mean": 98.0, "respiratory_rate_mean": 15.0, "sbp_mean": 130.0,
                     "diabetes": 0, "hypertension": 0, "cad": 0}
    },
]


def mint_token() -> str:
    payload = {
        "sub": "dr.premonition@hospital.ai",
        "role": "admin",
        "type": "access",
        "tenant_id": "t1",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def section(title: str) -> None:
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")


def check(label: str, r: httpx.Response, show_keys: list[str] | None = None) -> bool:
    ok = r.status_code == 200
    icon = "[PASS]" if ok else "[FAIL]"
    print(f"  {icon} {label} -> HTTP {r.status_code}")
    if ok:
        try:
            data = r.json()
            if show_keys:
                for k in show_keys:
                    val = data.get(k, data)
                    if isinstance(val, (dict, list)):
                        print(f"         {k}: {json.dumps(val, default=str)[:120]}")
                    else:
                        print(f"         {k}: {val}")
            else:
                raw = json.dumps(data, default=str)[:250]
                print(f"         {raw}")
        except Exception:
            print(f"         (non-JSON, {len(r.content)} bytes)")
    else:
        print(f"         Error: {r.text[:200]}")
    return ok


def main() -> int:
    token = mint_token()
    print(f"\nJWT Token minted for: dr.premonition@hospital.ai (role=admin)")
    print(f"Token prefix: {token[:50]}...")
    headers = {"Authorization": f"Bearer {token}"}

    client = httpx.Client(timeout=30)
    results: dict[str, bool] = {}

    # ─── PHASE 1: HEALTH ──────────────────────────────────────────────────
    section("PHASE 1 — HEALTH CHECK (No Auth Required)")
    r = client.get(f"{BASE}/health")
    results["GET /health"] = check("GET /health (public)", r)

    # ─── PHASE 2: PATIENT VALIDATION (3 different patients) ───────────────
    section("PHASE 2 — PATIENT VALIDATION (3 Different Patients)")
    predictions = []
    for patient in PATIENT_PROFILES:
        r = client.post(f"{API}/predict", json=patient, headers=headers)
        ok = r.status_code == 200
        icon = "[PASS]" if ok else "[FAIL]"
        pid = patient["patient_id"]
        results[f"POST /predict {pid}"] = ok
        if ok:
            data = r.json()
            risk = data.get("risk_score", data.get("probability", "?"))
            shap = data.get("top_features", data.get("shap_values", {}))
            rec = data.get("recommendation", data.get("alert_level", "?"))
            if isinstance(shap, list) and shap:
                top_factor = shap[0] if isinstance(shap[0], str) else list(shap[0].keys())[0] if isinstance(shap[0], dict) else str(shap[0])
            elif isinstance(shap, dict):
                top_factor = max(shap, key=lambda k: abs(shap[k])) if shap else "N/A"
            else:
                top_factor = str(shap)[:40]
            predictions.append({"patient_id": pid, "risk": risk, "top_factor": top_factor, "recommendation": rec})
            print(f"  {icon} {pid}")
            print(f"         Risk Score    : {risk}")
            print(f"         Top SHAP Factor: {top_factor}")
            print(f"         Recommendation : {rec}")
            print(f"         Full response keys: {list(data.keys())}")
        else:
            print(f"  {icon} {pid} -> {r.text[:200]}")
        print()

    # ─── PHASE 3: AGENT EXECUTION TRACE ───────────────────────────────────
    section("PHASE 3 — REALTIME MONITORING (Agent Pipeline Proof)")
    r = client.get(f"{API}/realtime/status", headers=headers)
    results["GET /realtime/status"] = check("GET /realtime/status", r)

    r = client.get(f"{API}/realtime/patients", headers=headers)
    results["GET /realtime/patients"] = check("GET /realtime/patients", r,
                                               show_keys=["total_patients", "patients"])

    r = client.get(f"{API}/realtime/alerts", headers=headers)
    results["GET /realtime/alerts"] = check("GET /realtime/alerts", r,
                                             show_keys=["total_alerts", "alerts"])

    r = client.get(f"{API}/realtime/notifications", headers=headers)
    results["GET /realtime/notifications"] = check("GET /realtime/notifications", r)

    r = client.get(f"{API}/realtime/executive", headers=headers)
    results["GET /realtime/executive"] = check("GET /realtime/executive", r,
                                                show_keys=["critical_patients", "high_risk_patients"])

    r = client.get(f"{API}/realtime/priority", headers=headers)
    results["GET /realtime/priority"] = check("GET /realtime/priority", r)

    # ─── PHASE 4: ML PIPELINE ─────────────────────────────────────────────
    section("PHASE 4 — ML PIPELINE (SHAP Explanations)")
    r = client.post(f"{API}/explain", json=PATIENT_PROFILES[0], headers=headers)
    results["POST /explain"] = check("POST /explain (SHAP)", r,
                                      show_keys=["feature_importance", "shap_values", "top_features"])

    # ─── PHASE 5: ANALYTICS ───────────────────────────────────────────────
    section("PHASE 5 — ANALYTICS ENDPOINTS")
    r = client.get(f"{API}/analytics/executive", headers=headers)
    results["GET /analytics/executive"] = check("GET /analytics/executive", r)

    r = client.get(f"{API}/analytics/population", headers=headers)
    results["GET /analytics/population"] = check("GET /analytics/population", r)

    r = client.get(f"{API}/metrics", headers=headers)
    results["GET /metrics"] = check("GET /metrics", r)

    r = client.get(f"{API}/models/version", headers=headers)
    results["GET /models/version"] = check("GET /models/version", r)

    r = client.get(f"{API}/system/status", headers=headers)
    results["GET /system/status"] = check("GET /system/status", r,
                                           show_keys=["model", "realtime", "agents"])

    # ─── PHASE 6: LOGIN SECURITY (redirect proof) ────────────────────────
    section("PHASE 6 — LOGIN SECURITY (Protected Endpoints Return 401 Without Token)")
    for endpoint in ["/api/v1/analytics/executive", "/api/v1/realtime/patients", "/api/v1/system/status"]:
        r_no_auth = client.get(f"{BASE}{endpoint}")
        ok = r_no_auth.status_code == 401
        icon = "[PASS]" if ok else "[FAIL]"
        print(f"  {icon} {endpoint} without token -> HTTP {r_no_auth.status_code} (expected 401)")
        results[f"No-auth {endpoint}"] = ok

    client.close()

    # ─── SUMMARY ──────────────────────────────────────────────────────────
    section("FINAL SUMMARY")
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        icon = "[PASS]" if ok else "[FAIL]"
        print(f"  {icon} {name}")
    print(f"\n  TOTAL: {passed} passed, {failed} failed out of {len(results)}")
    print()

    if predictions:
        section("PATIENT VALIDATION SUMMARY")
        for p in predictions:
            print(f"  Patient ID     : {p['patient_id']}")
            print(f"  Risk Score     : {p['risk']}")
            print(f"  Top SHAP Factor: {p['top_factor']}")
            print(f"  Recommendation : {p['recommendation']}")
            print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
