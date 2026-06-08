import sys
sys.path.insert(0, 'src')
from fastapi.testclient import TestClient
from premonition.api.main import app
import time

client = TestClient(app)
emails = ['test1@gmail.com', 'test2@gmail.com', 'test3@outlook.com']
results = []

for email in emails:
    start = time.perf_counter()
    response = client.post('/api/v1/auth/request-otp', json={'email': email})
    end = time.perf_counter()
    results.append((email, response.status_code, end - start, response.text[:200]))

print('--- OTP SPEED TEST RESULTS ---')
for email, status, dur, body in results:
    print(f"Email: {email} | Status: {status} | Time: {dur:.4f}s")
    print(f"  Body: {body}")
