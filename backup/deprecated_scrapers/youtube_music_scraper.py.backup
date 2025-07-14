# youtube_music_scraper.py (modified for database integration)

import json
import re
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

def parse_metric(metric_str):
    """
    Parses a metric string like "1.2M" or "123,456" into an integer.
    Handles "K", "M" suffixes and commas.
    """
    if not metric_str:
        return 0
    
    metric_str = metric_str.replace(',', '').strip()
    if 'K' in metric_str:
        return int(float(metric_str.replace('K', '')) * 1000)
    elif 'M' in metric_str:
        return int(float(metric_str.replace('M', '')) * 1000000)
    else:
        try:
            return int(metric_str)
        except ValueError:
            return 0 # Return 0 if parsing fails

def clean_artist_name(artist_text):
    """
    Minimal artist name cleaning to preserve YouTube Music's original credit information.
    Only handles basic whitespace normalization and obvious exact duplications.
    """
    if not artist_text:
        return ""
    
    normalized = re.sub(r'\s+', ' ', artist_text.replace('\n', ' ')).strip()
    
    words = normalized.split()
    if len(words) > 1 and len(words) % 2 == 0:
        mid = len(words) // 2
        first_half = ' '.join(words[:mid])
        second_half = ' '.join(words[mid:])
        
        if first_half.lower() == second_half.lower():
            return first_half
    
    return normalized

def extract_youtube_id_from_endpoint(element):
    """
    Extract YouTube ID from endpoint attribute JSON.
    """
    endpoint_attr = element.get('endpoint')
    if endpoint_attr:
        try:
            endpoint_data = json.loads(endpoint_attr)
            url = endpoint_data.get('urlEndpoint', {}).get('url', '')
            if 'watch?v=' in url:
                return url.split('watch?v=')[1].split('&')[0]
        except json.JSONDecodeError:
            pass
    return None

def scrape_category_data(page, category_name):
    """
    Scrapes data from the currently displayed chart.
    """
    scraped_data = []
    
    logger.info(f"📊 '{category_name}' 카테고리 데이터 스크래핑 시작...")

    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')

    song_items = soup.select("ytmc-entry-row")

    for i, item_tag in enumerate(song_items):
        rank = "Unknown Rank"
        title = "Unknown Title"
        artist = "Unknown Artist"
        thumbnail_url = ""
        daily_metrics = "Unknown Metrics"

        rank_tag = item_tag.select_one("#rank")
        if rank_tag:
            rank = rank_tag.get_text().strip()

        title_tag = item_tag.select_one("#entity-title")
        if title_tag:
            title = title_tag.get_text().strip()

        artist_tag = item_tag.select_one("#artist-names")
        if artist_tag:
            raw_artist = artist_tag.get_text().strip()
            artist = clean_artist_name(raw_artist)

        thumbnail_tag = item_tag.select_one("img#thumbnail")
        if thumbnail_tag and 'src' in thumbnail_tag.attrs:
            thumbnail_url = thumbnail_tag['src']

        metrics_tags = item_tag.select(".metric.content.center")
        if len(metrics_tags) > 1:
            daily_metrics = metrics_tags[1].get_text().strip()

        youtube_id = ""
        
        # Extract YouTube ID from endpoint attribute
        thumbnail_tag = item_tag.select_one("img#thumbnail")
        if thumbnail_tag:
            youtube_id = extract_youtube_id_from_endpoint(thumbnail_tag)
        
        # If not found in thumbnail, try title element
        if not youtube_id:
            title_tag = item_tag.select_one("#entity-title")
            if title_tag:
                youtube_id = extract_youtube_id_from_endpoint(title_tag)
        
        # If still not found, check all elements with endpoint attribute
        if not youtube_id:
            elements_with_endpoint = item_tag.select("[endpoint]")
            for element in elements_with_endpoint:
                youtube_id = extract_youtube_id_from_endpoint(element)
                if youtube_id:
                    break

        scraped_data.append({
            "rank": rank,
            "title": title,
            "artist": artist,
            "thumbnail": thumbnail_url,
            "daily_metrics": daily_metrics,
            "youtube_id": youtube_id
        })
    
    logger.info(f"✅ '{category_name}' 카테고리 스크래핑 완료: {len(scraped_data)}개 항목")
    return scraped_data

def get_song_titles_from_category(page, category_name):
    """
    특정 카테고리에서 곡 제목과 아티스트 정보만 추출합니다.
    """
    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    song_items = soup.select("ytmc-entry-row")
    
    titles = []
    for item_tag in song_items:
        title = "Unknown Title"
        artist = "Unknown Artist"
        
        title_tag = item_tag.select_one("#entity-title")
        if title_tag:
            title = title_tag.get_text().strip()
        
        artist_tag = item_tag.select_one("#artist-names")
        if artist_tag:
            raw_artist = artist_tag.get_text().strip()
            artist = clean_artist_name(raw_artist)
        
        titles.append({"title": title, "artist": artist})
    
    logger.info(f"✅ '{category_name}' 카테고리에서 {len(titles)}개 곡 제목 수집")
    return titles

def scrape_youtube_music_charts_csv():
    # 메인 곡 데이터와 태그 정보를 분리해서 수집
    main_songs = []
    trending_songs = []
    new_hit_songs = []
    target_url = "https://charts.youtube.com/charts/TopShortsSongs/kr/daily"
    start_time = time.time()
    
    log_scraper_start(logger, "YouTube Music Charts 스크래퍼", target_url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            logger.info(f"🌐 페이지 로딩 중: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            logger.info("✅ 페이지 로딩 완료. 데이터 스크래핑 시작.")

            logger.info("📜 모든 콘텐츠 로딩을 위해 스크롤 중...")
            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            logger.info("✅ 스크롤 완료. 모든 콘텐츠 로딩됨.")
            page.wait_for_timeout(3000)

            # 1. 메인 50곡 수집 (Most popular)
            main_songs = scrape_category_data(page, "Most popular (Trending)")

            # 2. Biggest movers 탭에서 인기급상승 곡 제목들 수집
            logger.info("🔄 'Biggest movers' 선택 중...")
            dropdown_button = page.locator("ytmc-dropdown-v2#sorting-options-selector paper-button")
            dropdown_button.wait_for(state="visible", timeout=30000)
            dropdown_button.click()
            page.locator("ytmc-dropdown-v2#sorting-options-selector iron-dropdown#dropdown").wait_for(state="attached", timeout=60000)
            page.wait_for_timeout(7000)
            biggest_movers_option = page.locator("paper-item[aria-label=\"Biggest movers\"]")
            biggest_movers_option.wait_for(state="visible", timeout=60000)
            biggest_movers_option.click(timeout=30000)
            page.wait_for_load_state('networkidle', timeout=60000)
            page.wait_for_timeout(3000)

            trending_songs = get_song_titles_from_category(page, "Biggest movers (Top rising)")

            # 3. Highest debut 탭에서 신곡 제목들 수집
            logger.info("🔄 'Highest debut' 선택 중...")
            dropdown_button.wait_for(state="visible", timeout=30000)
            dropdown_button.click()
            highest_debut_option = page.locator("paper-item[aria-label=\"Highest debut\"]")
            highest_debut_option.wait_for(state="visible", timeout=60000)
            highest_debut_option.click(timeout=30000)
            page.wait_for_load_state('networkidle', timeout=60000)
            page.wait_for_timeout(3000)

            new_hit_songs = get_song_titles_from_category(page, "Highest debut (Most popular new releases)")

        except Exception as e:
            log_error_with_context(logger, e, "네비게이션 또는 스크래핑")
        finally:
            browser.close()

    # 스크래핑 결과 로깅
    total_items = len(main_songs)
    duration = time.time() - start_time
    log_scraper_end(logger, "YouTube Music Charts 스크래퍼", total_items > 0, duration, total_items)

    return {
        "main_songs": main_songs,
        "trending_songs": trending_songs,
        "new_hit_songs": new_hit_songs
    }

if __name__ == "__main__":
    # 1. Initialize Database
    logger.info("💾 데이터베이스 초기화 중...")
    db.create_tables()
    logger.info("✅ 데이터베이스 준비 완료.")

    # 2. Scrape Data
    scraped_data = scrape_youtube_music_charts()

    # 3. Save Data to Database
    if not scraped_data or not scraped_data['main_songs']:
        logger.error("❌ 스크래핑된 데이터가 없습니다. 종료합니다.")
    else:
        logger.info("💾 스크래핑된 데이터를 데이터베이스에 저장 중...")
        
        # 메인 50곡 저장
        main_songs = scraped_data['main_songs']
        trending_songs = scraped_data['trending_songs']
        new_hit_songs = scraped_data['new_hit_songs']
        
        logger.info(f"🎵 메인 차트에서 {len(main_songs)}곡 처리 중...")
        
        # 태그 매칭을 위한 딕셔너리 생성
        trending_set = {(song['title'], song['artist']) for song in trending_songs}
        new_hit_set = {(song['title'], song['artist']) for song in new_hit_songs}
        
        total_saved = 0
        trending_matched = 0
        new_hit_matched = 0
        
        for song in main_songs:
            try:
                # 곡 저장
                song_id = db.add_song_and_get_id(
                    title=song['title'],
                    artist=song['artist'],
                    thumbnail_url=song.get('thumbnail'),
                    youtube_id=song.get('youtube_id')
                )
                
                if song_id:
                    # 트렌드 데이터 저장
                    daily_view_count = db.parse_metric_value(song.get('daily_metrics'))
                    db.add_trend(
                        song_id=song_id,
                        source='youtube',
                        category='trending',
                        rank=song['rank'],
                        daily_view_count=daily_view_count,
                        metrics={"daily_metrics": song.get('daily_metrics')}
                    )
                    
                    # 태그 매칭 및 업데이트
                    song_key = (song['title'], song['artist'])
                    is_trending = song_key in trending_set
                    is_new_hit = song_key in new_hit_set
                    
                    if is_trending or is_new_hit:
                        db.update_song_tags(
                            title=song['title'],
                            artist=song['artist'],
                            is_trending=is_trending,
                            is_new_hit=is_new_hit
                        )
                        if is_trending:
                            trending_matched += 1
                        if is_new_hit:
                            new_hit_matched += 1
                    
                    total_saved += 1
                    
            except Exception as e:
                log_error_with_context(logger, e, f"곡 처리 '{song.get('title')}'")
        
        logger.info(f"✅ 데이터 저장 완료:")
        logger.info(f"  📊 메인 차트: {total_saved}곡 저장")
        logger.info(f"  🔥 인기급상승 태그: {trending_matched}곡 매칭")
        logger.info(f"  ⭐ 신곡 태그: {new_hit_matched}곡 매칭")