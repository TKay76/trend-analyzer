import sys
import json
from playwright.sync_api import sync_playwright

def explore_youtube_music_charts(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Keep headless=False for observation
        page = browser.new_page()

        # Listen for network requests to identify potential APIs
        page.on("request", lambda request: print(f"Request: {request.method} {request.url}"))
        def handle_response(response):
            print(f"Response: {response.status} {response.url}")
            if "youtubei/v1/browse" in response.url and response.status == 200:
                try:
                    json_response = response.json()
                    print("\n--- API Response for youtubei/v1/browse ---")
                    print(json.dumps(json_response, indent=2))
                    print("-------------------------------------------\n")
                except Exception as e:
                    print(f"Could not parse JSON response: {e}")
        page.on("response", handle_response)

        try:
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="networkidle") # Wait until network is idle
            print("Page loaded. Please observe the browser for data loading and structure.")
            print("You can manually interact with the browser (e.g., scroll, click) to trigger more requests.")
            print("Press Enter in this terminal to close the browser and exit.")
            
            # Keep the browser open until user input
            input()

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    target_url = "https://charts.youtube.com/charts/TopShortsSongs/kr/daily"
    explore_youtube_music_charts(target_url)
