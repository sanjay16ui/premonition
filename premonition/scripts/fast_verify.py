import urllib.request, json

base = 'http://localhost:8000/api/v1'
hdr = {'X-API-Key': 'premonition-dev-key-2026', 'Content-Type': 'application/json'}

def get(path):
    req = urllib.request.Request(base + path, headers=hdr)
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.status, json.loads(r.read().decode())

def post(path, data={}):
    body = json.dumps(data).encode()
    req = urllib.request.Request(base + path, data=body, headers=hdr, method='POST')
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.status, json.loads(r.read().decode())

tests = []

# Non-LLM checks only
checks = [
    ('GET',  '/health',                    {}),
    ('GET',  '/realtime/patients',         {}),
    ('GET',  '/realtime/alerts',           {}),
    ('GET',  '/realtime/status',           {}),
    ('GET',  '/analytics/kpis',            {}),
    ('GET',  '/analytics/population',      {}),
    ('GET',  '/analytics/compare-models',  {}),
    ('GET',  '/analytics/executive',       {}),
    ('GET',  '/copilot/conversations',     {}),
    ('GET',  '/system/status',             {}),
    ('GET',  '/mlops/status',              {}),
]

for method, ep, data in checks:
    try:
        if method == 'GET':
            s, d = get(ep)
        else:
            s, d = post(ep, data)
        detail = ''
        if isinstance(d, list):
            detail = str(len(d)) + ' items'
        elif isinstance(d, dict):
            keys = list(d.keys())[:4]
            detail = str(keys)
        tests.append(('PASS', method, ep, detail))
    except Exception as e:
        tests.append(('FAIL', method, ep, str(e)[:100]))

print()
for status, method, ep, detail in tests:
    icon = 'OK' if status == 'PASS' else 'XX'
    print(f'[{icon}] {status} {method:<4} {ep:<45} {detail}')

passed = sum(1 for s,_,_,_ in tests if s == 'PASS')
print(f'\n{passed}/{len(tests)} PASSED')

# Check for critical patients
try:
    _, patients = get('/realtime/patients')
    if isinstance(patients, list):
        critical = [p for p in patients if p.get('alert_level') in ['RED','BLACK']]
        print(f'\nCritical patients: {len(critical)}')
        for p in critical[:3]:
            print(f"  Patient {p.get('patient_id')} - {p.get('alert_level')} - risk={p.get('risk_score',0):.2f}")
except Exception as e:
    print(f'Critical patients check failed: {e}')
