import os
import re
import time
from playwright.sync_api import sync_playwright

def get_latest_otp():
    log_path = r"C:\Users\S. SANJAYKUMAR\.gemini\antigravity\brain\f2eeedb0-c870-41d2-8ed3-555ca18927c0\.system_generated\tasks\task-3622.log"
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        matches = re.findall(r'<h2>(\d{4})</h2>', content)
        if matches:
            return matches[-1]
    except Exception as e:
        print(f"Error reading OTP from logs: {e}")
    return None

def run():
    os.makedirs('artifacts/emergency', exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        # Clear storage
        context.add_init_script("window.localStorage.clear();")
        
        page = context.new_page()
        
        # Listen to console and network to catch failures
        page.on("console", lambda msg: print(f"Browser Console: {msg.type} - {msg.text}"))
        page.on("requestfailed", lambda req: print(f"Request Failed: {req.url} - {req.failure}"))
        page.on("response", lambda res: print(f"Response: {res.url} - {res.status}") if not res.ok else None)

        print("--- LOGIN FLOW ---")
        page.goto("http://localhost:5174/")
        page.wait_for_timeout(2000)
        page.fill("#otp-email-input", "test3@example.com")
        page.click("#otp-send-btn")
        page.wait_for_timeout(3000)
        
        otp = get_latest_otp()
        if not otp:
            print("FAILED to get OTP.")
            return
            
        print(f"OTP: {otp}")
        for i, digit in enumerate(otp):
            page.fill(f"#otp-digit-{i}", digit)
        page.click("#otp-verify-btn")
        page.wait_for_timeout(3000)
        page.screenshot(path="artifacts/emergency/1_login.png")
        
        print("--- MONITORING: Acknowledge Button ---")
        page.goto("http://localhost:5174/monitoring")
        page.wait_for_timeout(4000)
        
        # Click Critical filter to make it easier to find Critical patients
        try:
            page.get_by_text("Critical").first.click()
            page.wait_for_timeout(1000)
            
            # Click the first Acknowledge button
            ack_btn = page.get_by_role("button", name="Acknowledge", exact=True).first
            if ack_btn.is_visible():
                print("Found Acknowledge button. Clicking...")
                # We want to capture the response
                with page.expect_response(lambda r: "acknowledge" in r.url) as response_info:
                    ack_btn.click()
                resp = response_info.value
                print(f"Acknowledge API Status: {resp.status}")
                print(f"Acknowledge API Payload: {resp.text()}")
            else:
                print("No Acknowledge button visible!")
        except Exception as e:
            print(f"Acknowledge test failed: {e}")
            
        page.screenshot(path="artifacts/emergency/2_monitoring.png")

        print("--- COPILOT: Generate Summary ---")
        page.goto("http://localhost:5174/copilot")
        page.wait_for_timeout(2000)
        # Assuming there is a link to a patient page
        try:
            links = page.locator("a[href^='/copilot/patient-']").all()
            if links:
                links[0].click()
                page.wait_for_timeout(2000)
            else:
                # Just go directly to a patient page
                page.goto("http://localhost:5174/copilot/patient-001")
                page.wait_for_timeout(2000)
                
            page.screenshot(path="artifacts/emergency/3_copilot_before.png")
            
            gen_btn = page.get_by_role("button", name="Generate Summary", exact=True).first
            if gen_btn.is_visible():
                print("Found Generate Summary button. Clicking...")
                with page.expect_response(lambda r: "summary" in r.url or "generate" in r.url, timeout=30000) as response_info:
                    gen_btn.click()
                resp = response_info.value
                print(f"Generate Summary Status: {resp.status}")
            else:
                print("No Generate Summary button visible!")
        except Exception as e:
            print(f"Generate Summary test failed: {e}")
            
        page.screenshot(path="artifacts/emergency/4_copilot_after.png")
        
        print("--- OLLAMA CHAT ---")
        page.goto("http://localhost:5174/copilot")
        page.wait_for_timeout(2000)
        try:
            # find chat input
            input_box = page.locator("textarea").first
            if input_box.is_visible():
                input_box.fill("hello")
                input_box.press("Enter")
                print("Sent 'hello' to Ollama. Waiting for response...")
                start = time.time()
                # wait until we see an answer
                page.wait_for_timeout(10000)
                print(f"Waited 10s. Let's see if response arrived.")
            else:
                print("No chat input found.")
        except Exception as e:
            print(f"Ollama chat test failed: {e}")
            
        page.screenshot(path="artifacts/emergency/5_ollama.png")
        
        print("--- ANALYTICS ---")
        page.goto("http://localhost:5174/analytics")
        page.wait_for_timeout(5000)
        page.screenshot(path="artifacts/emergency/6_analytics.png")

        print("--- TEST COMPLETE ---")
        browser.close()

if __name__ == "__main__":
    run()
