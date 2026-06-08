import asyncio
import jwt
import os
import time
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
    token = generate_token()
    routes = [
        "/",
        "/monitoring",
        "/analytics",
        "/copilot",
        "/digital-twin",
        "/executive-3d"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console errors
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}") if msg.type in ['error', 'warning'] else None)
        
        # Listen for failed requests
        page.on("response", lambda res: print(f"Network Error: {res.status} {res.url}") if res.status >= 400 else None)
        page.on("requestfailed", lambda req: print(f"Request Failed: {req.url} - {req.failure}"))
        
        # Navigate to home first to set origin context
        print("Loading base URL to set localStorage...")
        await page.goto("http://localhost:5174/login")
        await page.evaluate(f"localStorage.setItem('premonition_access_token', '{token}')")
        
        for route in routes:
            url = f"http://localhost:5174{route}"
            print(f"Navigating to {url}")
            await page.goto(url, wait_until="load")
            
            # Wait a moment for dynamic content
            await page.wait_for_timeout(2000)
            
            # Take screenshot
            name = route.replace("/", "_") or "home"
            os.makedirs("artifacts/screenshots", exist_ok=True)
            path = f"artifacts/screenshots/screenshot_{name}.png"
            await page.screenshot(path=path)
            print(f"Saved screenshot: {path}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
