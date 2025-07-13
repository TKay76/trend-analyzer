import sys
import json
from playwright.sync_api import sync_playwright

def explore_tiktok_creative_center(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Set to False for visual observation
        page = browser.new_page()

        # Listen for network requests to identify potential APIs
        page.on("request", lambda request: print(f"Request: {request.method} {request.url}"))
        page.on("response", lambda response: print(f"Response: {response.status} {response.url}"))

        try:
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded")
            print("Page loaded. Please observe the browser for login requirements or data loading.")
            print("You can manually interact with the browser to switch tabs if needed.")
            print("Press Enter in this terminal to close the browser and exit.")
            
            # Keep the browser open until user input
            input()

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    target_url = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en"
    explore_tiktok_creative_center(target_url)
