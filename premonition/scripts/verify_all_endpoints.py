import urllib.request, urllib.error, json

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

checks = [
    ('GET',  '/health',                     {}),
    ('GET',  '/realtime/patients',          {}),
    ('GET',  '/realtime/alerts',            {}),
    ('GET',  '/realtime/status',            {}),
    ('GET',  '/analytics/kpis',             {}),
    ('GET',  '/analytics/population',       {}),
    ('GET',  '/analytics/compare-models',   {}),
    ('GET',  '/analytics/executive',        {}),
    ('GET',  '/copilot/conversations',      {}),
    ('POST', '/copilot/chat',               {'message': 'hello', 'patient_id': 'test'}),
    ('POST', '/copilot/patient-summary',    {'patient_id': 'patient-001'}),
    ('POST', '/copilot/executive-summary',  {}),
    ('POST', '/copilot/handover',           {'patient_ids': ['patient-001']}),
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
            detail = str(list(d.keys())[:4])
        tests.append(('PASS', method, ep, detail))
    except Exception as e:
        tests.append(('FAIL', method, ep, str(e)[:100]))

print()
for status, method, ep, detail in tests:
    icon = 'OK' if status == 'PASS' else 'XX'
    print(f'[{icon}] {status} {method:<4} {ep:<45} {detail}')

passed = sum(1 for s,_,_,_ in tests if s == 'PASS')
print(f'\n{passed}/{len(tests)} PASSED')
