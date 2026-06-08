import httpx
import asyncio
import json

async def verify():
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 3. Verify Backend Endpoints
        print("--- VERIFY BACKEND ---")
        for endpoint in [
            "/api/v1/health",
            "/api/v1/realtime/status",
            "/api/v1/analytics/executive"
        ]:
            try:
                r = await client.get(endpoint)
                print(f"GET {endpoint} -> {r.status_code}")
            except Exception as e:
                print(f"GET {endpoint} -> ERROR: {e}")

        # 4. Verify Ollama Copilot
        print("\n--- VERIFY OLLAMA COPILOT ---")
        try:
            r = await client.post("/api/v1/copilot/chat", json={
                "message": "What is sepsis?",
                "context": {"patient_id": "P-101"}
            })
            print(f"POST /api/v1/copilot/chat -> {r.status_code}")
            if r.status_code == 200:
                print(f"Response: {r.json().get('reply', '')[:100]}...")
                print(f"Model: {r.json().get('model')}")
        except Exception as e:
            print(f"Ollama Error: {e}")

        # 5. Verify OTP
        print("\n--- VERIFY OTP ---")
        try:
            # Request
            r1 = await client.post("/api/v1/auth/request-otp", json={"email": "admin@premonition.health"})
            print(f"OTP Request -> {r1.status_code}")
            
            # Resend
            r2 = await client.post("/api/v1/auth/resend-otp", json={"email": "admin@premonition.health"})
            print(f"OTP Resend -> {r2.status_code}")

            # Verify (with dummy code to verify it returns 401 instead of 503)
            r3 = await client.post("/api/v1/auth/verify-otp", json={
                "email": "admin@premonition.health",
                "code": "0000"
            })
            print(f"OTP Verify (wrong code) -> {r3.status_code} (Expect 401, not 503)")
        except Exception as e:
            print(f"OTP Error: {e}")

        # 6. Verify Realtime
        print("\n--- VERIFY REALTIME ---")
        try:
            async with client.stream("GET", "/api/v1/realtime/stream") as response:
                print(f"SSE Connect -> {response.status_code}")
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        print(f"SSE Message: {chunk.strip()}")
                        break
        except Exception as e:
            print(f"SSE Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
