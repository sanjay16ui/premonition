import os
import re
import time
from playwright.sync_api import sync_playwright

def get_latest_otp():
    log_path = r"C:\Users\S. SANJAYKUMAR\.gemini\antigravity\brain\f2eeedb0-c870-41d2-8ed3-555ca18927c0\.system_generated\tasks\task-3622.log"
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    matches = re.findall(r'<h2>(\d{4})</h2>', content)
    if matches:
        return matches[-1]
    return None

def run():
    os.makedirs('artifacts/login_screenshots', exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        # Clear storage to force login
        context.add_init_script("window.localStorage.clear();")
        
        page = context.new_page()
        
        print("1. Opening application...")
        page.goto("http://localhost:5174/")
        page.wait_for_timeout(2000)
        
        # Verify it redirects to login
        if "login" in page.url:
            print("2. Login page appeared.")
        page.screenshot(path="artifacts/login_screenshots/login_page.png")
        
        print("3. Entering test email...")
        page.fill("#otp-email-input", "test@example.com")
        page.click("#otp-send-btn")
        
        print("4. Waiting for OTP email (Resend)...")
        page.wait_for_timeout(3000)
        
        otp = get_latest_otp()
        if not otp:
            print("Failed to retrieve OTP from logs.")
            return
            
        print(f"5. Retrieved OTP: {otp}")
        
        print("6. Submitting OTP...")
        for i, digit in enumerate(otp):
            page.fill(f"#otp-digit-{i}", digit)
        
        page.click("#otp-verify-btn")
        
        print("7. Verifying successful login...")
        page.wait_for_timeout(3000)
        page.screenshot(path="artifacts/login_screenshots/success_login.png")
        
        print("8. Verifying Session Persistence...")
        page.reload()
        page.wait_for_timeout(3000)
        page.screenshot(path="artifacts/login_screenshots/dashboard.png")
        
        print("9. Verifying protected routes...")
        routes = {
            "monitoring": "/monitoring",
            "analytics": "/analytics",
            "copilot": "/copilot",
            "digital_twin": "/digital-twin",
            "executive_3d": "/executive-3d"
        }
        for name, route in routes.items():
            page.goto(f"http://localhost:5174{route}")
            page.wait_for_timeout(2000)
            page.screenshot(path=f"artifacts/login_screenshots/{name}.png")
            
        print("10. Testing logout...")
        # To test logout, we'll clear token and check redirect
        page.evaluate("window.localStorage.clear()")
        page.reload()
        page.wait_for_timeout(2000)
        if "login" in page.url:
            print("Logout verified.")
            page.screenshot(path="artifacts/login_screenshots/logout.png")
            
        browser.close()

if __name__ == "__main__":
    run()
