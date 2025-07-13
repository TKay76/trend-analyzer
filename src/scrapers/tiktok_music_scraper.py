# tiktok_music_scraper.py (modified for database integration)

import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import database_manager as db
from src.utils.logger_config import get_logger, log_scraper_start, log_scraper_end, log_database_operation, log_error_with_context

# 로거 설정
logger = get_logger(__name__)

def parse_track_data(track_string):
    """
    Parses a track string (e.g., "Title - Artist") into title and artist.
    """
    parts = track_string.split(' - ', 1)
    if len(parts) == 2:
        return {"title": parts[0].strip(), "artist": parts[1].strip()}
    else:
        # If no clear " - " separator, assume the whole string is the title
        return {"title": track_string.strip(), "artist": "Unknown"}

def extract_tiktok_sound_id(item_tag):
    """
    Extract TikTok Sound ID from music item HTML.
    """
    # Method 1: Extract from href attribute
    link_tag = item_tag.select_one("a[href*='/song/']")
    if link_tag:
        href = link_tag.get('href', '')
        if '/song/' in href:
            # Extract ID from URL pattern: /song/Title-SOUNDID
            parts = href.split('-')
            if parts:
                sound_id = parts[-1].split('?')[0]  # Remove query parameters
                if sound_id.isdigit() and len(sound_id) > 15:  # TikTok Sound IDs are long numbers
                    return sound_id
    
    # Method 2: Extract from chart element ID
    chart_element = item_tag.select_one("div[id*='-']")
    if chart_element:
        element_id = chart_element.get('id', '')
        if '-' in element_id:
            parts = element_id.split('-')
            if len(parts) >= 2:
                sound_id = parts[-1]
                if sound_id.isdigit() and len(sound_id) > 15:
                    return sound_id
    
    return None

def scrape_tab_data(page, tab_name):
    """
    Scrapes music data from a given tab, handling "View More" pagination.
    """
    scraped_data = []
    seen_tracks = set() # To avoid duplicate entries if "View More" loads existing items

    logger.info(f"📊 '{tab_name}' 탭 데이터 스크래핑 시작...")

    while True:
        # Scroll to the bottom of the page to load more content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000) # Give time for new content to load after scrolling

        # Wait for the music list items to be present
        try:
            page.wait_for_selector("div.ItemCard_soundItemContainer__GUmFb", timeout=10000)
        except Exception as e:
            logger.warning(f"⚠️ '{tab_name}' 탭에서 음악 항목을 찾을 수 없거나 타임아웃 발생: {e}")
            break

        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        music_items = soup.select("div.ItemCard_soundItemContainer__GUmFb")

        new_items_found = False
        current_scraped_count = len(scraped_data)

        for i, item_tag in enumerate(music_items):
            rank_tag = item_tag.select_one("span.RankingStatus_rankingIndex__ZMDrH")
            title_tag = item_tag.select_one("span.ItemCard_musicName__2znhM")
            artist_tag = item_tag.select_one("span.ItemCard_autherName__gdrue")

            rank = int(rank_tag.get_text().strip()) if rank_tag else (len(scraped_data) + 1)
            title = title_tag.get_text().strip() if title_tag else "Unknown Title"
            artist = artist_tag.get_text().strip() if artist_tag else "Unknown Artist"

            is_approved_for_business_use = False
            approved_tag = item_tag.select_one("div.FeatureText_container__hy_dH")
            if approved_tag and "Approved for business use" in approved_tag.get_text():
                is_approved_for_business_use = True

            # Extract TikTok Sound ID
            tiktok_id = extract_tiktok_sound_id(item_tag)
            
            unique_key = f"{title}-{artist}"
            if unique_key not in seen_tracks:
                scraped_data.append({
                    "rank": rank,
                    "title": title,
                    "artist": artist,
                    "is_approved_for_business_use": is_approved_for_business_use,
                    "tiktok_id": tiktok_id
                })
                seen_tracks.add(unique_key)
                new_items_found = True

        if len(scraped_data) == current_scraped_count and not page.query_selector("button.view-more-button"):
            logger.info(f"📄 '{tab_name}' 탭에서 새로운 항목이 없음. 리스트 끝으로 판단.")
            break

        view_more_button_selector = "text=\"View More\""
        view_more_button = page.query_selector(view_more_button_selector)

        if view_more_button and view_more_button.is_visible() and view_more_button.is_enabled():
            logger.debug(f"🔄 '{tab_name}' 탭에서 'View More' 버튼 클릭...")
            view_more_button.click()
            page.wait_for_timeout(2000)
        else:
            logger.debug(f"🔚 '{tab_name}' 탭에서 더 이상 'View More' 버튼 없음.")
            break

    logger.info(f"✅ '{tab_name}' 탭 스크래핑 완료: {len(scraped_data)}개 항목")
    return scraped_data

def scrape_tiktok_creative_center():
    all_music_data = {
        "popular": [],
        "breakout": []
    }
    target_url = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en"
    start_time = time.time()
    
    log_scraper_start(logger, "TikTok Creative Center 스크래퍼", target_url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            logger.info(f"🌐 페이지 로딩 중: {target_url}")
            page.goto(target_url, wait_until="networkidle")
            page.wait_for_timeout(10000)
            logger.info("✅ 페이지 로딩 완료. 데이터 스크래핑 시작.")

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            breakout_tab_selector = "span.ContentTab_itemLabelText__hiCCd:has-text(\"Breakout\")"
            try:
                logger.info("🔄 'Breakout' 탭 클릭 중...")
                page.wait_for_selector(breakout_tab_selector, timeout=10000)
                page.locator(breakout_tab_selector).click(timeout=10000)
                page.wait_for_selector("div.ItemCard_soundItemContainer__GUmFb", timeout=30000)
                all_music_data["breakout"] = scrape_tab_data(page, "Breakout")
            except Exception as e:
                log_error_with_context(logger, e, "Breakout 탭 처리")

            popular_tab_selector = "span.ContentTab_itemLabelText__hiCCd:has-text(\"Popular\")"
            try:
                logger.info("🔄 'Popular' 탭 클릭 중...")
                page.wait_for_selector(popular_tab_selector, timeout=10000)
                page.locator(popular_tab_selector).click(timeout=10000)
                page.wait_for_selector("div.ItemCard_soundItemContainer__GUmFb", timeout=30000)
                all_music_data["popular"] = scrape_tab_data(page, "Popular")
            except Exception as e:
                log_error_with_context(logger, e, "Popular 탭 처리")

        except Exception as e:
            log_error_with_context(logger, e, "페이지 네비게이션 또는 초기 설정")
        finally:
            browser.close()

    # 스크래핑 결과 로깅
    total_items = sum(len(songs) for songs in all_music_data.values())
    duration = time.time() - start_time
    log_scraper_end(logger, "TikTok Creative Center 스크래퍼", total_items > 0, duration, total_items)
    
    return all_music_data

if __name__ == "__main__":
    # 1. Initialize Database
    logger.info("💾 데이터베이스 초기화 중...")
    db.create_tables()
    logger.info("✅ 데이터베이스 준비 완료.")

    # 2. Scrape Data
    all_music_data = scrape_tiktok_creative_center()

    # 3. Save Data to Database
    if not all_music_data or (not all_music_data['popular'] and not all_music_data['breakout']):
        logger.error("❌ 스크래핑된 데이터가 없습니다. 종료합니다.")
    else:
        logger.info("💾 스크래핑된 데이터를 데이터베이스에 저장 중...")
        total_saved = 0
        
        for category, songs in all_music_data.items():
            if not songs:
                logger.warning(f"⚠️ {category} 카테고리에서 곡을 찾지 못했습니다.")
                continue
            
            logger.info(f"🎵 {category} 카테고리에서 {len(songs)}곡 처리 중...")
            category_saved = 0
            
            for song in songs:
                try:
                    # Add song to 'songs' table and get its ID
                    song_id = db.add_song_and_get_id(
                        title=song['title'],
                        artist=song['artist'],
                        tiktok_id=song.get('tiktok_id'),
                        is_approved=song.get('is_approved_for_business_use')
                    )
                    
                    if song_id:
                        # Add trend data to 'daily_trends' table
                        db.add_trend(
                            song_id=song_id,
                            source='tiktok',
                            category=category,
                            rank=song['rank']
                            # TikTok에서는 현재 조회수 메트릭이 없음
                            # 필요시 향후 추가 가능
                        )
                        category_saved += 1
                        total_saved += 1
                        
                except Exception as e:
                    log_error_with_context(logger, e, f"곡 처리 '{song.get('title')}'")
            
            log_database_operation(logger, "저장", f"{category} 트렌드", category_saved)
        
        logger.info(f"✅ 데이터 저장 완료: 총 {total_saved}곡 저장됨")
