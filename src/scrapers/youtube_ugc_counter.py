import sys
import re
import os
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.logger_config import get_logger, log_error_with_context
from src.database import database_manager as db

# 로거 설정
logger = get_logger(__name__)

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

def extract_video_count_with_selectors(page):
    """
    특정 선택자를 사용해 비디오 카운트를 추출합니다.
    """
    selectors = [
        # YouTube 공통 선택자들
        '[data-testid*="count"]',
        '.ytd-shelf-header-renderer .title',
        '#contents-count',
        '.metadata-stats-count',
        # 헤더나 제목 영역에서 찾기
        'h1:has-text("videos")',
        'h1:has-text("개")',
        'h2:has-text("videos")',
        'h2:has-text("개")',
        # 일반적인 카운트 표시 영역
        '.count',
        '.video-count',
        '.results-count'
    ]
    
    for selector in selectors:
        try:
            elements = page.locator(selector).all()
            for element in elements:
                text = element.text_content()
                if text:
                    count = extract_count_from_text(text.strip())
                    if count > 0:
                        logger.debug(f"📊 선택자 {selector}에서 카운트 발견: {text} → {count:,}")
                        return count
        except Exception as e:
            logger.debug(f"선택자 {selector} 실패: {e}")
            continue
    
    return 0

def extract_count_from_text(text):
    """
    텍스트에서 숫자와 단위를 추출하여 카운트를 반환합니다.
    """
    patterns = [
        r'(\d+[.,]?\d*[만억천백십]?)\s*개',  # 12만개
        r'(\d+[.,]?\d*[KMB]?)\s*(?:videos?|shorts?)',
        r'(\d+[.,]?\d*[KMB]?)\s*(?:video|short)',
        r'(\d+[.,]?\d*[만억천백십]?)\s*(?:개의?\s*)?(?:동영상|쇼츠)',
        r'(\d+[.,]?\d*[KMB]?)\s*결과',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                count = parse_video_count(match)
                if count > 0:
                    return count
    return 0

def extract_video_count_from_text(all_text):
    """
    전체 텍스트에서 비디오 카운트를 추출합니다.
    """
    patterns = [
        r'(\d+[.,]?\d*[만억천백십]?)\s*개',  # 12만개
        r'(\d+[.,]?\d*[KMB]?)\s*(?:videos?|shorts?)',
        r'(\d+[.,]?\d*[KMB]?)\s*(?:video|short)',
        r'(\d+[.,]?\d*[만억천백십]?)\s*(?:개의?\s*)?(?:동영상|쇼츠)',
        r'(\d+[.,]?\d*[KMB]?)\s*결과',
    ]
    
    found_counts = []
    
    for pattern in patterns:
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    count = parse_video_count(match)
                    if count > 0:
                        found_counts.append(count)
                        logger.debug(f"📊 발견된 카운트: {match} → {count:,}")
                except Exception as e:
                    logger.debug(f"⚠️ 파싱 실패: {match} ({e})")
                    continue
    
    # 가장 큰 값 반환 (전체 개수일 가능성이 높음)
    return max(found_counts) if found_counts else 0


def scrape_youtube_shorts_data(url):
    """
    Scrapes the total video count for a given YouTube Shorts URL.
    Supports both watch URLs and source/shorts URLs.
    Returns the count as integer, or 0 if no count found.
    """
    # YouTube ID에서 Shorts URL로 변환
    if '/watch?v=' in url:
        video_id = url.split('watch?v=')[1].split('&')[0]
        url = f"https://www.youtube.com/source/{video_id}/shorts"
    
    logger.info(f"📺 YouTube UGC 수집: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = browser.new_page()
        
        # 타임아웃 설정
        page.set_default_timeout(30000)  # 30초
        
        try:
            logger.info("🌐 페이지 로딩 중...")
            page.goto(url, wait_until="networkidle", timeout=20000)
            
            # 비디오 카운트 요소가 나타날 때까지 대기 (최대 15초)
            try:
                page.wait_for_selector(
                    'text=/\\d+[.,]?\\d*[KMB만억천백십]?\\s*(?:videos?|shorts?|개|결과)/', 
                    timeout=15000
                )
                logger.debug("✅ 비디오 카운트 요소 발견")
            except Exception:
                logger.warning("⚠️ 비디오 카운트 요소 대기 타임아웃, 계속 진행")
            
            # 짧은 스크롤로 추가 콘텐츠 로딩
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(2)
            
            # 특정 영역에서 비디오 카운트 찾기
            video_count = extract_video_count_with_selectors(page)
            
            if video_count > 0:
                logger.info(f"✅ 최종 결과: {video_count:,}개")
                return video_count
            
            # 선택자로 찾지 못한 경우 전체 텍스트에서 검색
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            all_text = soup.get_text()
            
            logger.debug(f"🔍 페이지 텍스트 샘플: {all_text[:200].strip()}...")
            
            # 텍스트에서 비디오 카운트 패턴 검색
            video_count = extract_video_count_from_text(all_text)
            
            if video_count > 0:
                logger.info(f"✅ 최종 결과: {video_count:,}개")
                return video_count
            else:
                logger.warning("❌ 비디오 카운트를 찾을 수 없음")
                return 0
                
        except Exception as e:
            log_error_with_context(logger, e, "YouTube Shorts 페이지 스크래핑")
            return 0
        finally:
            browser.close()

def save_to_database(youtube_url, video_count):
    """수집된 YouTube UGC 카운트를 데이터베이스에 저장"""
    if video_count <= 0:
        return False
    
    # YouTube URL에서 YouTube ID 추출
    if '/source/' in youtube_url and '/shorts' in youtube_url:
        youtube_id = youtube_url.split('/source/')[1].split('/shorts')[0]
    elif '/watch?v=' in youtube_url:
        youtube_id = youtube_url.split('watch?v=')[1].split('&')[0]
    else:
        logger.warning("❌ YouTube ID를 추출할 수 없습니다")
        return False
    
    try:
        # 해당 YouTube ID를 가진 곡 찾기
        songs = db.get_songs_with_platform_ids('youtube')
        target_song = None
        
        for song in songs:
            if len(song) >= 4 and song[3] == youtube_id:  # youtube_id 컬럼
                target_song = song
                break
        
        if not target_song:
            logger.warning(f"❌ YouTube ID {youtube_id}에 해당하는 곡을 찾을 수 없습니다")
            return False
        
        song_id = target_song[0]
        title = target_song[1]
        artist = target_song[2]
        
        # UGC 카운트 저장
        db.update_ugc_counts(song_id, youtube_count=video_count)
        logger.info(f"✅ UGC 카운트 저장: {title} - {artist} → {video_count:,}개")
        
        return True
        
    except Exception as e:
        log_error_with_context(logger, e, "데이터베이스 저장")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python youtube_ugc_counter.py <YouTube_Shorts_URL> [--save-db]")
        print("\n💡 YouTube Shorts URL 예시:")
        print("  https://www.youtube.com/source/983bBbJx0Mk/shorts")
        print("\n💾 데이터베이스 저장:")
        print("  python youtube_ugc_counter.py <URL> --save-db")
        sys.exit(1)

    youtube_url = sys.argv[1]
    save_to_db = '--save-db' in sys.argv
    
    video_count = scrape_youtube_shorts_data(youtube_url)
    print(video_count)
    
    # 데이터베이스 저장
    if save_to_db and video_count > 0:
        if save_to_database(youtube_url, video_count):
            print("💾 데이터베이스 저장 완료!")
        else:
            print("❌ 데이터베이스 저장 실패!")