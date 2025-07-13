import sys
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def parse_video_count(count_str):
    """
    Parses a string like '1.4M videos' or '1,400,000 videos' into an integer.
    """
    count_str = count_str.lower().replace('videos', '').strip()
    count_str = count_str.replace(',', '')

    if 'k' in count_str:
        return int(float(count_str.replace('k', '')) * 1000)
    elif 'm' in count_str:
        return int(float(count_str.replace('m', '')) * 1000000)
    else:
        return int(count_str)

def scrape_tiktok_sound_data(url):
    """
    Scrapes the total video count for a given TikTok sound URL.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False for visual debugging
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded")

            # Explicit wait for the element containing the video count
            # This selector might need adjustment if TikTok's HTML changes
            # Explicit wait for an element containing the text "videos"
            # This is more robust than specific data-e2e attributes which can change.
            page.wait_for_selector('text=videos', timeout=30000)
            
            # Get the page content after dynamic loading
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find elements that contain the text "videos"
            # TikTok often uses various tags (h2, span, div) for this information.
            # We'll search for elements that contain the word "videos" and then extract the number.
            video_count_element = None
            for tag in ['h1', 'h2', 'h3', 'span', 'div', 'p', 'strong']:
                found_elements = soup.find_all(tag, string=re.compile(r'\d[.,]?\d*[KM]?\s*videos', re.IGNORECASE))
                if found_elements:
                    # Prioritize elements that are more likely to contain the main count
                    # This might need further refinement based on actual page structure
                    video_count_element = found_elements[0]
                    break
            
            if video_count_element:
                count_text = video_count_element.get_text()
                # Use regex to find numbers with K/M or commas
                match = re.search(r'([\d.,]+[KM]?)', count_text)
                if match:
                    return parse_video_count(match.group(1))
                else:
                    print(f"Could not find video count in: {count_text}")
                    return 0
            else:
                print("Could not find the video count element on the page.")
                return 0
        except Exception as e:
            print(f"An error occurred: {e}")
            return 0
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper_poc.py <TikTok_Sound_URL>")
        sys.exit(1)

    tiktok_url = sys.argv[1]
    video_count = scrape_tiktok_sound_data(tiktok_url)
    print(video_count)
