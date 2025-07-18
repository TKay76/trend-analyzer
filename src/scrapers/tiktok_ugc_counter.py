import sys
import re
import os
import time
from collections import Counter
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.logger_config import get_logger, log_error_with_context
from src.database import database_manager as db

logger = get_logger(__name__)

def parse_video_count(count_str):
    """
    Parses a string like '1.4M videos' or '1,400,000 videos' into an integer.
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
        logger.warning(f"⚠️ 비디오 카운트 파싱 실패: {count_str}")
        return 0

def extract_hashtags_from_soup(soup):
    """
    BeautifulSoup 객체에서 해시태그를 추출하고 빈도수를 계산합니다.
    """
    hashtag_counter = Counter()
    
    # 방법 1: 해시태그 링크 찾기 (/tag/ 경로)
    hashtag_links = soup.find_all('a', href=re.compile(r'/tag/'))
    for link in hashtag_links:
        href = link.get('href', '')
        text = link.get_text().strip()
        
        # URL에서 해시태그 추출
        tag_match = re.search(r'/tag/([^/?#&]+)', href)
        if tag_match:
            hashtag = tag_match.group(1)
            if hashtag.lower() == 'fyp': continue # FYP 제외
            hashtag_counter[hashtag] += 1
            logger.debug(f"📌 링크에서 해시태그: #{hashtag}")
        
        # 링크 텍스트에서 해시태그 추출
        if text.startswith('#'):
            hashtag = text[1:].strip()
            if hashtag and len(hashtag) > 0:
                if hashtag.lower() == 'fyp': continue # FYP 제외
                hashtag_counter[hashtag] += 1
                logger.debug(f"📌 링크 텍스트에서 해시태그: #{hashtag}")
    
    # 방법 2: 전체 텍스트에서 #으로 시작하는 해시태그 찾기
    all_text = soup.get_text()
    text_hashtags = re.findall(r'#(\w+)', all_text)
    for hashtag in text_hashtags:
        if len(hashtag) > 1:  # 한 글자는 제외
            if hashtag.lower() == 'fyp': continue # FYP 제외
            hashtag_counter[hashtag] += 1
            logger.debug(f"📌 텍스트에서 해시태그: #{hashtag}")
    
    # 방법 3: 비디오 설명/캡션 영역에서 찾기
    video_desc_selectors = [
        '[data-e2e*="video-desc"]',
        '[data-e2e*="video-caption"]',
        '[class*="video-desc"]',
        '[class*="caption"]',
        '[class*="desc"]',
        '.tiktok-caption',
        '.video-meta-caption'
    ]
    
    for selector in video_desc_selectors:
        elements = soup.select(selector)
        for element in elements:
            # 요소 내 링크에서 해시태그 찾기
            links = element.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/tag/' in href:
                    tag_match = re.search(r'/tag/([^/?#&]+)', href)
                    if tag_match:
                        hashtag = tag_match.group(1)
                        if hashtag.lower() == 'fyp': continue # FYP 제외
                        hashtag_counter[hashtag] += 1
                        logger.debug(f"📌 비디오 설명에서 해시태그: #{hashtag}")
            
            # 요소 텍스트에서 해시태그 찾기
            text = element.get_text()
            desc_hashtags = re.findall(r'#(\w+)', text)
            for hashtag in desc_hashtags:
                if len(hashtag) > 1:
                    if hashtag.lower() == 'fyp': continue # FYP 제외
                    hashtag_counter[hashtag] += 1
                    logger.debug(f"📌 설명 텍스트에서 해시태그: #{hashtag}")
    
    return hashtag_counter

def scrape_tiktok_sound_data(url):
    """
    TikTok 사운드 페이지에서 비디오 개수와 상위 해시태그를 수집합니다.
    
    Returns:
        dict: {
            'video_count': int,
            'top_hashtags': [(hashtag, count), ...],  # 상위 10개
            'success': bool,
            'error_message': str or None
        }
    """
    logger.info(f"🎵 TikTok 사운드 데이터 수집 시작: {url}")
    
    result = {
        'video_count': 0,
        'top_hashtags': [],
        'success': False,
        'error_message': None
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to False for visual debugging
        page = browser.new_page()
        
        try:
            logger.info("🌐 페이지 로딩 중...")
            page.goto(url, wait_until="domcontentloaded")

            # 페이지 완전 로딩을 위한 대기
            time.sleep(3)

            # 비디오 카운트 요소 대기
            try:
                page.wait_for_selector('text=videos', timeout=30000)
                logger.info("✅ 비디오 카운트 요소 발견")
            except Exception:
                logger.warning("⚠️ 비디오 카운트 요소 타임아웃")

            # 더 많은 콘텐츠 로딩을 위한 스크롤
            logger.debug("📜 페이지 스크롤하여 추가 콘텐츠 로딩...")
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

            # HTML 콘텐츠 가져오기
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            # 1. 비디오 개수 추출
            video_count = extract_video_count_from_soup(soup)
            result['video_count'] = video_count

            # 2. 해시태그 추출 및 카운트
            hashtag_counter = extract_hashtags_from_soup(soup)
            
            # 상위 10개 해시태그만 저장
            top_hashtags = hashtag_counter.most_common(10)
            result['top_hashtags'] = top_hashtags
            result['success'] = True

            logger.info(f"✅ 수집 완료 - 비디오: {video_count:,}개, 해시태그: {len(top_hashtags)}개")
            if top_hashtags:
                logger.info(f"📌 상위 해시태그: {', '.join([f'#{tag}({count})' for tag, count in top_hashtags[:5]])}")

        except Exception as e:
            result['error_message'] = str(e)
            log_error_with_context(logger, e, "TikTok 사운드 페이지 스크래핑")
            
        finally:
            browser.close()

    return result

def extract_video_count_from_soup(soup):
    """
    BeautifulSoup 객체에서 비디오 개수를 추출합니다.
    """
    # Find elements that contain the text "videos"
    video_count_element = None
    
    for tag in ['h1', 'h2', 'h3', 'span', 'div', 'p', 'strong']:
        found_elements = soup.find_all(tag, string=re.compile(r'\d[.,]?\d*[KM]?\s*videos', re.IGNORECASE))
        if found_elements:
            video_count_element = found_elements[0]
            break
    
    if video_count_element:
        count_text = video_count_element.get_text()
        # Use regex to find numbers with K/M or commas
        match = re.search(r'([\d.,]+[KM]?)', count_text)
        if match:
            count_value = parse_video_count(match.group(1))
            logger.debug(f"📊 비디오 카운트 발견: {count_text} → {count_value:,}")
            return count_value
        else:
            logger.warning(f"⚠️ 비디오 카운트 파싱 실패: {count_text}")
            return 0
    else:
        logger.warning("⚠️ 비디오 카운트 요소를 찾을 수 없음")
        return 0

def save_to_database(tiktok_url, result_data):
    """수집된 데이터를 데이터베이스에 저장"""
    if not result_data['success']:
        return False
    
    # TikTok URL에서 TikTok ID 추출
    if '/music/x-' in tiktok_url:
        tiktok_id = tiktok_url.split('/music/x-')[1].split('?')[0]
    else:
        logger.warning("❌ TikTok ID를 추출할 수 없습니다")
        return False
    
    try:
        # 해당 TikTok ID를 가진 곡 찾기
        songs = db.get_songs_with_platform_ids('tiktok')
        target_song = None
        
        for song in songs:
            if len(song) >= 4 and song[3] == tiktok_id:  # tiktok_id 컬럼
                target_song = song
                break
        
        if not target_song:
            logger.warning(f"❌ TikTok ID {tiktok_id}에 해당하는 곡을 찾을 수 없습니다")
            return False
        
        song_id = target_song[0]
        title = target_song[1]
        artist = target_song[2]
        
        # UGC 카운트 저장
        ugc_count = result_data['video_count']
        if ugc_count > 0:
            db.update_ugc_counts(song_id, tiktok_count=ugc_count)
            logger.info(f"✅ UGC 카운트 저장: {title} - {artist} → {ugc_count:,}개")
        
        # 해시태그 저장
        hashtags = result_data['top_hashtags']
        if hashtags:
            db.save_song_hashtags(song_id, hashtags)
            logger.info(f"✅ 해시태그 저장: {title} - {artist} → {len(hashtags)}개")
        
        return True
        
    except Exception as e:
        log_error_with_context(logger, e, "데이터베이스 저장")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python tiktok_ugc_counter.py <TikTok_Sound_URL> [--save-db]")
        print("\n💡 TikTok 사운드 URL 예시:")
        print("  https://www.tiktok.com/music/x-7373776748699421486")
        print("\n💾 데이터베이스 저장:")
        print("  python tiktok_ugc_counter.py <URL> --save-db")
        sys.exit(1)

    tiktok_url = sys.argv[1]
    save_to_db = '--save-db' in sys.argv
    
    result = scrape_tiktok_sound_data(tiktok_url)
    
    if result['success']:
        print(f"비디오 개수: {result['video_count']:,}")
        print(f"상위 해시태그:")
        for i, (hashtag, count) in enumerate(result['top_hashtags'], 1):
            print(f"  {i:2d}. #{hashtag}: {count:,}회")
        
        # 데이터베이스 저장
        if save_to_db:
            if save_to_database(tiktok_url, result):
                print("\n💾 데이터베이스 저장 완료!")
            else:
                print("\n❌ 데이터베이스 저장 실패!")
    else:
        print(f"오류: {result['error_message']}")
