from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    print("Launching browser...")
    browser = p.chromium.launch(headless=False) # Keep headless=False to see if it launches
    page = browser.new_page()
    print("Browser launched. Navigating to example.com...")
    page.goto("https://example.com")
    print("Page loaded. Waiting 5 seconds...")
    time.sleep(5)
    browser.close()
    print("Browser closed.")
