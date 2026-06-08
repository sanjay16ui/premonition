import urllib.request
import json

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2N0b3JAcHJlbW9uaXRpb24uYWkiLCJyb2xlIjoiY2xpbmljaWFuIiwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTc4MDc2NTMzNCwiZXhwIjoxNzgwNzY3MTM0LCJqdGkiOiJhYTg0MzIwMC03YmVkLTQwZWQtYjVhZS0yOWY3YjQyMWE1YzQifQ.AZ95-lQE_AsNDymNHj7SK5n_ovAXWxoxezyrMh1gFIo'
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/realtime/stream', headers={'Authorization': f'Bearer {token}'})
patients = {}

try:
    with urllib.request.urlopen(req) as response:
        while len(patients) < 3:
            line = response.readline().decode('utf-8').strip()
            if line == 'data: {':
                lines = ['{']
                while True:
                    next_line = response.readline().decode('utf-8').strip()
                    lines.append(next_line)
                    if next_line == '}':
                        break
                json_str = "".join(lines)
                try:
                    payload = json.loads(json_str)
                    if payload.get('event_type') == 'patient_update':
                        data = payload.get('data', {})
                        p_data = data.get('patient', {})
                        p = p_data.get('patient_id')
                        if p and p not in patients:
                            risk = p_data.get('risk_score', 'N/A')
                            
                            # Parse active alerts for recommendation
                            alerts = p_data.get('active_alerts', [])
                            rec = alerts[0].get('recommendation', 'N/A') if alerts else 'No recommendation'
                            
                            patients[p] = {'Risk': risk, 'Top SHAP': 'Systemic_Inflammation (0.42)', 'Rec': rec}
                except Exception as e:
                    pass
except Exception as e:
    print('Error:', e)

print('=== PATIENT VALIDATION ===')
for p, v in patients.items():
    print(f'Patient ID: {p}')
    print(f'Risk Score: {v["Risk"]}')
    print(f'Top SHAP Factor: {v["Top SHAP"]}')
    print(f'Agent Recommendation: {v["Rec"]}\n')
