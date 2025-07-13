import sys
import re
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from src.utils.logger_config import get_logger, log_error_with_context

# 로거 설정
logger = get_logger(__name__)

def parse_count(count_str):
    """
    Parses a string like '1.4M videos', '1.2K posts', or '1,400,000 videos' into an integer.
    """
    if not count_str:
        return 0
    
    count_str = count_str.lower().replace('videos', '').replace('posts', '').strip()
    count_str = count_str.replace(',', '')

    try:
        if 'k' in count_str:
            return int(float(count_str.replace('k', '')) * 1000)
        elif 'm' in count_str:
            return int(float(count_str.replace('m', '')) * 1000000)
        elif 'b' in count_str:
            return int(float(count_str.replace('b', '')) * 1000000000)
        else:
            return int(float(count_str))
    except (ValueError, TypeError):
        logger.warning(f"⚠️ 숫자 파싱 실패: {count_str}")
        return 0

def extract_hashtags_from_page(soup):
    """
    TikTok 페이지에서 해시태그들을 추출합니다.
    """
    hashtags = []
    
    # 다양한 해시태그 선택자 시도
    hashtag_selectors = [
        'a[href*="/tag/"]',  # 해시태그 링크
        '[data-e2e="video-desc"] a',  # 동영상 설명의 링크
        '.video-meta-caption a',  # 캡션 내 링크
        'a[href^="/tag/"]',  # /tag/로 시작하는 링크
    ]
    
    for selector in hashtag_selectors:
        elements = soup.select(selector)
        for element in elements:
            href = element.get('href', '')
            text = element.get_text().strip()
            
            if '/tag/' in href and text.startswith('#'):
                hashtag = text.replace('#', '').strip()
                if hashtag and hashtag not in hashtags:
                    hashtags.append(hashtag)
                    logger.debug(f"📌 해시태그 발견: #{hashtag}")
    
    return hashtags

def scrape_tiktok_sound_with_hashtags(url):
    """
    TikTok 사운드 페이지에서 비디오 개수와 관련 해시태그를 수집합니다.
    """
    logger.info(f"🎵 TikTok 사운드 페이지 분석 시작: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        result = {
            'video_count': 0,
            'hashtags': [],
            'success': False
        }
        
        try:
            logger.info("🌐 페이지 로딩 중...")
            page.goto(url, wait_until="domcontentloaded")
            
            # 페이지 완전 로딩 대기
            time.sleep(3)
            
            # 비디오 카운트가 포함된 요소 대기
            try:
                page.wait_for_selector('text=videos', timeout=30000)
                logger.info("📊 비디오 카운트 요소 로딩 완료")
            except Exception:
                logger.warning("⚠️ 비디오 카운트 요소를 찾을 수 없음 (타임아웃)")
            
            # 페이지 스크롤로 더 많은 콘텐츠 로드
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            
            # HTML 콘텐츠 가져오기
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. 비디오 개수 추출
            video_count = extract_video_count(soup)
            result['video_count'] = video_count
            
            # 2. 해시태그 추출
            hashtags = extract_hashtags_from_page(soup)
            result['hashtags'] = hashtags
            
            # 3. 추가 해시태그 수집 (비디오 목록에서)
            additional_hashtags = extract_hashtags_from_videos(soup)
            for hashtag in additional_hashtags:
                if hashtag not in result['hashtags']:
                    result['hashtags'].append(hashtag)
            
            result['success'] = True
            
            logger.info(f"✅ 수집 완료 - 비디오: {video_count:,}개, 해시태그: {len(result['hashtags'])}개")
            if result['hashtags']:
                logger.info(f"📌 발견된 해시태그: {', '.join(['#' + tag for tag in result['hashtags'][:10]])}")
            
        except Exception as e:
            log_error_with_context(logger, e, "TikTok 사운드 페이지 스크래핑")
            
        finally:
            browser.close()
        
        return result

def extract_video_count(soup):
    """
    페이지에서 비디오 개수를 추출합니다.
    """
    video_count = 0
    
    # 비디오 카운트를 찾는 다양한 방법 시도
    count_patterns = [
        r'(\d+(?:[.,]\d+)*[KMB]?)\s*videos',
        r'(\d+(?:[.,]\d+)*[KMB]?)\s*posts',
        r'(\d+(?:[.,]\d+)*[KMB]?)\s*개',
    ]
    
    for tag in ['h1', 'h2', 'h3', 'span', 'div', 'p', 'strong']:
        elements = soup.find_all(tag)
        for element in elements:
            text = element.get_text()
            for pattern in count_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    count_str = match.group(1)
                    video_count = parse_count(count_str)
                    if video_count > 0:
                        logger.debug(f"📊 비디오 카운트 발견: {count_str} → {video_count:,}")
                        return video_count
    
    logger.warning("⚠️ 비디오 개수를 찾을 수 없습니다.")
    return video_count

def extract_hashtags_from_videos(soup):
    """
    페이지의 비디오 목록에서 해시태그를 추출합니다.
    """
    hashtags = []
    
    # 비디오 설명이나 캡션에서 해시태그 추출
    video_selectors = [
        '[data-e2e="video-desc"]',
        '.video-desc',
        '.video-caption',
        '.tiktok-caption',
        '[class*="caption"]',
        '[class*="desc"]'
    ]
    
    for selector in video_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text()
            # 텍스트에서 #으로 시작하는 해시태그 찾기
            hashtag_matches = re.findall(r'#(\w+)', text)
            for hashtag in hashtag_matches:
                if hashtag and hashtag.lower() not in [h.lower() for h in hashtags]:
                    hashtags.append(hashtag)
                    logger.debug(f"📌 비디오에서 해시태그 발견: #{hashtag}")
    
    return hashtags

def scrape_tiktok_hashtag_page(hashtag):
    """
    특정 해시태그 페이지를 스크래핑하여 해당 해시태그의 비디오 개수를 가져옵니다.
    """
    hashtag_url = f"https://www.tiktok.com/tag/{hashtag.replace('#', '')}"
    logger.info(f"🏷️ 해시태그 페이지 분석: #{hashtag}")
    
    result = scrape_tiktok_sound_with_hashtags(hashtag_url)
    
    return {
        'hashtag': hashtag,
        'video_count': result['video_count'],
        'related_hashtags': result['hashtags'],
        'success': result['success']
    }

def analyze_trending_hashtags_from_sound(sound_url):
    """
    사운드 페이지에서 트렌딩 해시태그들을 분석합니다.
    """
    logger.info("🔥 트렌딩 해시태그 분석 시작")
    
    # 1. 사운드 페이지에서 해시태그 수집
    sound_data = scrape_tiktok_sound_with_hashtags(sound_url)
    
    if not sound_data['success'] or not sound_data['hashtags']:
        logger.warning("⚠️ 사운드 페이지에서 해시태그를 찾을 수 없습니다.")
        return sound_data
    
    # 2. 각 해시태그의 인기도 분석
    hashtag_analytics = []
    
    for hashtag in sound_data['hashtags'][:5]:  # 상위 5개 해시태그만 분석
        logger.info(f"📊 해시태그 분석 중: #{hashtag}")
        hashtag_data = scrape_tiktok_hashtag_page(hashtag)
        hashtag_analytics.append(hashtag_data)
        
        # API 제한 방지를 위한 대기
        time.sleep(2)
    
    # 3. 결과 정리
    result = {
        'sound_url': sound_url,
        'sound_video_count': sound_data['video_count'],
        'discovered_hashtags': sound_data['hashtags'],
        'hashtag_analytics': hashtag_analytics,
        'success': sound_data['success']
    }
    
    logger.info(f"✅ 트렌딩 해시태그 분석 완료: {len(hashtag_analytics)}개 해시태그 분석됨")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python tiktok_hashtag_counter.py <TikTok_Sound_URL>")
        print("  python tiktok_hashtag_counter.py --hashtag <hashtag_name>")
        print("  python tiktok_hashtag_counter.py --analyze <TikTok_Sound_URL>")
        sys.exit(1)
    
    if sys.argv[1] == "--hashtag" and len(sys.argv) >= 3:
        # 특정 해시태그 분석
        hashtag = sys.argv[2]
        result = scrape_tiktok_hashtag_page(hashtag)
        print(f"해시태그: #{result['hashtag']}")
        print(f"비디오 개수: {result['video_count']:,}")
        print(f"관련 해시태그: {', '.join(['#' + tag for tag in result['related_hashtags']])}")
        
    elif sys.argv[1] == "--analyze" and len(sys.argv) >= 3:
        # 사운드에서 트렌딩 해시태그 분석
        sound_url = sys.argv[2]
        result = analyze_trending_hashtags_from_sound(sound_url)
        
        print(f"\n🎵 사운드 URL: {result['sound_url']}")
        print(f"📊 사운드 비디오 개수: {result['sound_video_count']:,}")
        print(f"🏷️ 발견된 해시태그 ({len(result['discovered_hashtags'])}개):")
        for hashtag in result['discovered_hashtags']:
            print(f"  #{hashtag}")
        
        print(f"\n📈 해시태그 인기도 분석:")
        for analytics in result['hashtag_analytics']:
            print(f"  #{analytics['hashtag']}: {analytics['video_count']:,} 비디오")
            
    else:
        # 기본 사운드 URL 분석
        tiktok_url = sys.argv[1]
        result = scrape_tiktok_sound_with_hashtags(tiktok_url)
        
        print(f"비디오 개수: {result['video_count']:,}")
        print(f"해시태그 개수: {len(result['hashtags'])}")
        if result['hashtags']:
            print(f"해시태그: {', '.join(['#' + tag for tag in result['hashtags']])}")