import asyncio
import re
from playwright.async_api import async_playwright

async def run_otp_test():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("--- OTP LOGIN TEST ---")
        
        responses = {}
        async def handle_response(response):
            if "api/v1/auth" in response.url:
                responses[response.url] = response.status
        page.on("response", handle_response)
        
        print("Navigating to http://localhost:5173/login...")
        await page.goto("http://localhost:5173/login")
        
        # Enter email
        print("Entering email sanjaykumar16292006@gmail.com...")
        await page.fill("input[type='email']", "sanjaykumar16292006@gmail.com")
        
        # Click Send Verification Code
        print("Clicking 'Send Verification Code'...")
        await page.click("button:has-text('Send Verification Code')")
        
        # Wait for the network request
        await page.wait_for_timeout(4000)
        
        print("Network Responses:")
        for url, status in responses.items():
            print(f"{url} -> {status}")
            
        # Extract OTP from backend log
        log_path = "C:/Users/S. SANJAYKUMAR/.gemini/antigravity/brain/f2eeedb0-c870-41d2-8ed3-555ca18927c0/.system_generated/tasks/task-5673.log"
        print(f"Reading backend logs from {log_path} to find OTP...")
        
        import time
        otp = None
        for _ in range(15): # wait up to 15 seconds
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
                matches = re.findall(r"Code\s+:\s+(\d{4})", content)
                if matches:
                    # check if the OTP changed from the initial old one
                    current_otp = matches[-1]
                    if current_otp != "0442" and current_otp != "4992":
                        otp = current_otp
                        break
            await page.wait_for_timeout(1000)
        
        if not otp:
            print("Failed to extract OTP from backend logs!")
            await browser.close()
            return
            
        print(f"Extracted OTP: {otp}. Entering into UI...")
        
        # UI has 4 separate input boxes for the OTP
        inputs = await page.query_selector_all("input[type='text']")
        for i, char in enumerate(otp):
            if i < len(inputs):
                await inputs[i].type(char)
                await page.wait_for_timeout(200)
                
        # Click Verify button
        print("Clicking Verify button...")
        await page.click("#otp-verify-btn")
        
        # Wait for Verification request
        await page.wait_for_timeout(3000)
        
        print("Network Responses after Verification:")
        for url, status in responses.items():
            print(f"{url} -> {status}")
            
        # Check if we navigated successfully
        current_url = page.url
        print(f"Current URL after verification: {current_url}")
        
        if "login" not in current_url:
            print("Successfully navigated to Dashboard with OTP!")
            await page.screenshot(path="c:/Users/S. SANJAYKUMAR/.gemini/antigravity/brain/f2eeedb0-c870-41d2-8ed3-555ca18927c0/otp_dashboard.png")
            print("Screenshot saved to artifacts.")
        else:
            print("FAILED to navigate. Still on login page.")
            error_el = await page.query_selector(".text-red-500")
            if error_el:
                error_text = await error_el.inner_text()
                print(f"UI Error message: {error_text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_otp_test())
