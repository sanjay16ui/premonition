import asyncio
import jwt
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright

SECRET = "super-secret-key-for-premonition-early-warning-system-1234"

def generate_token():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "doctor@hospital.com",
        "role": "admin",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=60),
        "jti": "mock-jti"
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture console and network
        logs = []
        page.on("console", lambda msg: logs.append(f"Console {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: logs.append(f"JS Error: {err.message}"))
        
        print("Setting up auth...")
        await page.goto("http://localhost:5174/login")
        token = generate_token()
        await page.evaluate(f"localStorage.setItem('premonition_access_token', '{token}')")
        
        print("1. Testing Generate Summary (Copilot Patient Page)")
        await page.goto("http://localhost:5174/copilot/patient-001", wait_until="load")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="artifacts/screenshots/pre_summary.png")
        # Try to click Generate Summary
        generate_btn = page.get_by_role("button", name="Generate Summary")
        if await generate_btn.count() > 0:
            await generate_btn.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path="artifacts/screenshots/post_summary.png")
            print("- Clicked Generate Summary")
        else:
            print("- Generate Summary button not found!")

        print("2. Testing Acknowledge & Critical Patients (Monitoring Page)")
        await page.goto("http://localhost:5174/monitoring", wait_until="load")
        await page.wait_for_timeout(3000)
        
        # Check critical patients
        critical_btn = page.get_by_role("button", name="High Risk / Critical")
        if await critical_btn.count() > 0:
            await critical_btn.click()
            await page.wait_for_timeout(1000)
            await page.screenshot(path="artifacts/screenshots/critical_patients.png")
            print("- Clicked Critical filter")
        
        ack_btn = page.get_by_role("button", name="Acknowledge").first
        if await ack_btn.count() > 0:
            await ack_btn.click()
            print("- Clicked Acknowledge")
        else:
            print("- Acknowledge button not found!")
            
        print("3. Testing Analytics Page")
        await page.goto("http://localhost:5174/analytics", wait_until="load")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="artifacts/screenshots/analytics_test.png")
        
        print("\n--- CAPTURED LOGS ---")
        for log in logs:
            print(log)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
