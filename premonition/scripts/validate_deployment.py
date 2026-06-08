import requests
import time
import json

def verify():
    base_url = "http://127.0.0.1:8000/api/v1"
    print(f"Backend API URL: {base_url}")
    
    # 1. Health
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health: {'PASS' if r.status_code == 200 else 'FAIL'} - {r.json()}")
    except Exception as e:
        print(f"Health: FAIL - {e}")
        
    # 2. Login & OTP
    try:
        r = requests.post(f"{base_url}/auth/request-otp", json={"email": "doctor@premonition.health"}, timeout=15)
        print(f"OTP Send: {'PASS' if r.status_code == 200 else 'FAIL'} - {r.json().get('message') if r.status_code == 200 else r.text}")
        
        # Test OTP verify (use universal dev OTP or valid code)
        r = requests.post(f"{base_url}/auth/verify-otp", json={"email": "doctor@premonition.health", "code": "1234"}, timeout=15)
        if r.status_code == 200:
            token = r.json().get("access_token")
            print("Login: PASS")
        else:
            print(f"Login: FAIL - {r.json()}")
            token = None
    except Exception as e:
        print(f"Login/OTP: FAIL - {e}")
        token = None

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 3. Analytics
    try:
        r = requests.get(f"{base_url}/analytics/kpis", headers=headers, timeout=5)
        print(f"Analytics: {'PASS' if r.status_code == 200 else 'FAIL'}")
    except Exception as e:
        print(f"Analytics: FAIL - {e}")

    # 4. Copilot test
    try:
        start_t = time.time()
        r = requests.post(f"{base_url}/copilot/chat", headers=headers, json={"message": "Summarize patient-001", "context": {"patient_id": "P-001", "vitals": "HR: 90"}}, timeout=15)
        end_t = time.time()
        latency = end_t - start_t
        resp = r.json()
        text = resp.get("response", "")
        
        has_placeholder = "[Insert " in text or "[Insert" in text
        print(f"Copilot Summary: {'PASS' if r.status_code == 200 and not has_placeholder and latency < 15 else 'FAIL'}")
        print(f"  -> Latency: {latency:.2f}s")
        print(f"  -> Placeholders: {has_placeholder}")
        print(f"  -> Model used: {resp.get('metadata', {}).get('model', 'unknown')}")
        
    except Exception as e:
        print(f"Copilot: FAIL - {e}")

    # 5. Check Frontend URLs
    fe_url = "http://localhost:5173"
    print("\nFrontend URL Verification:")
    paths = {
        "Login": "/login",
        "Monitoring": "/monitoring",
        "Analytics": "/analytics",
        "Copilot": "/copilot",
        "Digital Twin": "/digital-twin",
        "Executive Dashboard": "/executive",
    }
    for name, path in paths.items():
        try:
            r = requests.get(f"{fe_url}{path}", timeout=5)
            print(f"{name}: PASS - {fe_url}{path}")
        except Exception:
            print(f"{name}: FAIL - {fe_url}{path}")
            
    print(f"Backend: http://127.0.0.1:8000/api/v1")
    print(f"Swagger: http://127.0.0.1:8000/docs")
    print(f"Health: http://127.0.0.1:8000/api/v1/health")

if __name__ == "__main__":
    verify()
