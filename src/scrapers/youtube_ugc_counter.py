import sys
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def parse_video_count(count_str):
    """
    Parses a string like '1.4M videos', '12만개' or '1,400,000 videos' into an integer.
    """
    if not count_str:
        return 0
        
    count_str = count_str.lower().replace('videos', '').replace('video', '').replace('shorts', '').replace('short', '').replace('개', '').strip()
    count_str = count_str.replace(',', '')

    try:
        # Korean number units
        if '만' in count_str:
            return int(float(count_str.replace('만', '')) * 10000)
        elif '억' in count_str:
            return int(float(count_str.replace('억', '')) * 100000000)
        elif '천' in count_str:
            return int(float(count_str.replace('천', '')) * 1000)
        elif '백' in count_str:
            return int(float(count_str.replace('백', '')) * 100)
        elif '십' in count_str:
            return int(float(count_str.replace('십', '')) * 10)
        # English units
        elif 'k' in count_str:
            return int(float(count_str.replace('k', '')) * 1000)
        elif 'm' in count_str:
            return int(float(count_str.replace('m', '')) * 1000000)
        elif 'b' in count_str:
            return int(float(count_str.replace('b', '')) * 1000000000)
        else:
            return int(float(count_str))
    except (ValueError, TypeError):
        return 0

def scrape_youtube_shorts_data(url):
    """
    Scrapes the total video count for a given YouTube Shorts URL.
    Returns the count as integer, or 0 if no count found.
    """
    print(f"📺 YouTube UGC 수집: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False for visual debugging
        page = browser.new_page()
        
        try:
            # Navigate to page
            page.goto(url, wait_until="domcontentloaded")
            print("  ⏳ 페이지 로딩 중...")

            # Wait for content to load
            page.wait_for_timeout(8000)  # 더 긴 대기 시간
            
            # Scroll to load more content
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            
            # Get page content
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Get all text content from the page
            all_text = soup.get_text()
            
            # Debug: Print some page text to see what we're getting
            print(f"  🔍 페이지 텍스트 샘플: {all_text[:200].strip()}...")
            
            # Look for video count patterns (Korean and English)
            patterns = [
                r'(\d+[.,]?\d*[만억천백십]?)\s*개',  # 12만개
                r'(\d+[.,]?\d*[KMB]?)\s*(?:videos?|shorts?)',
                r'(\d+[.,]?\d*[KMB]?)\s*(?:video|short)',
                r'(\d+[.,]?\d*[만억천백십]?)\s*(?:개의?\s*)?(?:동영상|쇼츠)',
                r'(\d+[.,]?\d*[KMB]?)\s*결과',
            ]
            
            found_counts = []
            
            # Search for video count patterns
            for pattern in patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        try:
                            count = parse_video_count(match)
                            if count > 0:
                                found_counts.append(count)
                                print(f"  📊 발견된 카운트: {match} → {count:,}")
                        except Exception as e:
                            print(f"  ⚠️ 파싱 실패: {match} ({e})")
                            continue
            
            # Return the highest count found (most likely to be the total)
            if found_counts:
                result = max(found_counts)
                print(f"  ✅ 최종 결과: {result:,}개")
                return result
            else:
                print(f"  ❌ 비디오 카운트를 찾을 수 없음")
                return 0
                
        except Exception as e:
            print(f"  💥 오류: {e}")
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