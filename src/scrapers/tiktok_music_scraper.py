# tiktok_music_scraper.py (modified for database integration)

import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import database_manager as db

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

    print(f"Scraping data from '{tab_name}' tab...")

    while True:
        # Scroll to the bottom of the page to load more content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000) # Give time for new content to load after scrolling

        # Wait for the music list items to be present
        try:
            page.wait_for_selector("div.ItemCard_soundItemContainer__GUmFb", timeout=10000)
        except Exception:
            print(f"No music items found on '{tab_name}' tab or timeout exceeded.")
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
            print(f"No new items found after scrolling on '{tab_name}' tab. Assuming end of list.")
            break

        view_more_button_selector = "text=\"View More\""
        view_more_button = page.query_selector(view_more_button_selector)

        if view_more_button and view_more_button.is_visible() and view_more_button.is_enabled():
            print(f"Clicking 'View More' on '{tab_name}' tab...")
            view_more_button.click()
            page.wait_for_timeout(2000)
        else:
            print(f"No more 'View More' button or it's not clickable on '{tab_name}' tab.")
            break

    return scraped_data

def scrape_tiktok_creative_center():
    all_music_data = {
        "popular": [],
        "breakout": []
    }
    target_url = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print(f"Navigating to {target_url}...")
            page.goto(target_url, wait_until="networkidle")
            page.wait_for_timeout(10000)
            print("Page loaded. Attempting to scrape data.")

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            breakout_tab_selector = "span.ContentTab_itemLabelText__hiCCd:has-text(\"Breakout\")"
            try:
                print("Clicking 'Breakout' tab...")
                page.wait_for_selector(breakout_tab_selector, timeout=10000)
                page.locator(breakout_tab_selector).click(timeout=10000)
                page.wait_for_selector("div.ItemCard_soundItemContainer__GUmFb", timeout=30000)
                all_music_data["breakout"] = scrape_tab_data(page, "Breakout")
            except Exception as e:
                print(f"Could not click Breakout tab or scrape: {e}")

            popular_tab_selector = "span.ContentTab_itemLabelText__hiCCd:has-text(\"Popular\")"
            try:
                print("\nClicking 'Popular' tab...")
                page.wait_for_selector(popular_tab_selector, timeout=10000)
                page.locator(popular_tab_selector).click(timeout=10000)
                page.wait_for_selector("div.ItemCard_soundItemContainer__GUmFb", timeout=30000)
                all_music_data["popular"] = scrape_tab_data(page, "Popular")
            except Exception as e:
                print(f"Could not click Popular tab or scrape: {e}")

        except Exception as e:
            print(f"An error occurred during navigation or initial setup: {e}")
        finally:
            browser.close()

    return all_music_data

if __name__ == "__main__":
    # 1. Initialize Database
    print("Initializing database...")
    db.create_tables()
    print("Database ready.")

    # 2. Scrape Data
    all_music_data = scrape_tiktok_creative_center()

    # 3. Save Data to Database
    if not all_music_data or (not all_music_data['popular'] and not all_music_data['breakout']):
        print("No data was scraped. Exiting.")
    else:
        print("\nSaving scraped data to the database...")
        for category, songs in all_music_data.items():
            if not songs:
                print(f"No songs found for category: {category}")
                continue
            
            print(f"Processing {len(songs)} songs from category: {category}...")
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
                            # metrics can be added here if available
                        )
                except Exception as e:
                    print(f"Error processing song '{song.get('title')}': {e}")
        
        print("Data saving process complete.")
