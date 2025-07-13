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

def scrape_youtube_shorts_data(url):
    """
    Scrapes the total video count for a given YouTube Shorts URL.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False for visual debugging
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded")

            # Wait longer for YouTube's dynamic content to load
            page.wait_for_timeout(5000)
            
            # Get the page content after dynamic loading
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Get all text content from the page
            all_text = soup.get_text()
            
            # Look for video count patterns in all text
            patterns = [
                r'(\d+[.,]?\d*[KM]?)\s*videos?',
                r'(\d+[.,]?\d*[KM]?)\s*shorts?',
                r'(\d+[.,]?\d*[KM]?)\s*개의?\s*동영상',
                r'(\d+[.,]?\d*[KM]?)\s*개의?\s*쇼츠',
                r'(\d+[.,]?\d*[KM]?)\s*short',
                r'(\d+[.,]?\d*[KM]?)\s*video'
            ]
            
            # Search for video count patterns
            for pattern in patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    # Return the first meaningful match
                    for match in matches:
                        try:
                            count = parse_video_count(match)
                            if count > 0:
                                return count
                        except:
                            continue
            
            return 0
        except Exception as e:
            print(f"An error occurred: {e}")
            return 0
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_shorts_scraper.py <YouTube_Shorts_URL>")
        sys.exit(1)

    youtube_url = sys.argv[1]
    video_count = scrape_youtube_shorts_data(youtube_url)
    print(video_count)