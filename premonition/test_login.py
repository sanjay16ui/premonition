import asyncio
from playwright.async_api import async_playwright

async def run_test():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("--- DEMO LOGIN TEST ---")
        
        # Listen for all network responses to capture exact status codes
        responses = {}
        async def handle_response(response):
            if "api/v1/auth" in response.url:
                responses[response.url] = {
                    "status": response.status,
                    "url": response.url
                }
        page.on("response", handle_response)
        
        print("Navigating to http://localhost:5173/login...")
        await page.goto("http://localhost:5173/login")
        
        # Click Direct Demo Login
        print("Clicking 'Direct Demo Login'...")
        await page.click("button:has-text('Direct Demo Login')")
        
        # Wait for the network request and navigation
        await page.wait_for_timeout(3000)
        
        print("Network Requests Captured:")
        for url, data in responses.items():
            print(f"URL: {url}")
            print(f"Status: {data['status']}")
            
        # Check if we navigated successfully
        current_url = page.url
        print(f"Current URL after login: {current_url}")
        
        if "login" not in current_url:
            print("Successfully navigated to Dashboard!")
            await page.screenshot(path="c:/Users/S. SANJAYKUMAR/.gemini/antigravity/brain/f2eeedb0-c870-41d2-8ed3-555ca18927c0/demo_dashboard.png")
            print("Screenshot saved to artifacts.")
        else:
            print("FAILED to navigate. Still on login page.")
            # Print error if visible
            error_el = await page.query_selector(".text-red-500")
            if error_el:
                error_text = await error_el.inner_text()
                print(f"UI Error message: {error_text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
