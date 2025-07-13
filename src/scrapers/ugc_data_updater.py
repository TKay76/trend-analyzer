#!/usr/bin/env python3
"""
UGC 데이터 업데이터
데이터베이스에 저장된 곡들의 YouTube와 TikTok UGC 동영상 개수를 수집하여 업데이트합니다.
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.scrapers.tiktok_ugc_counter import scrape_tiktok_sound_data
from src.scrapers.youtube_ugc_counter import scrape_youtube_shorts_data
from src.database import database_manager as db

def update_youtube_ugc_counts():
    """YouTube UGC 카운트를 업데이트합니다."""
    print("YouTube UGC 카운트 업데이트 시작...")
    
    songs = db.get_songs_with_platform_ids('youtube')
    success_count = 0
    
    for song in songs:
        song_id = song['id']
        title = song['title']
        artist = song['artist']
        youtube_id = song['youtube_id']
        
        if not youtube_id:
            continue
            
        print(f"Processing: {title} - {artist} (YouTube ID: {youtube_id})")
        
        # YouTube URL 구성
        youtube_url = f"https://youtube.com/source/{youtube_id}/shorts"
        
        try:
            # UGC 카운트 수집
            ugc_count = scrape_youtube_shorts_data(youtube_url)
            
            if ugc_count > 0:
                # 데이터베이스 업데이트
                if db.update_ugc_counts(song_id, youtube_count=ugc_count):
                    print(f"✅ Updated: {ugc_count:,} YouTube videos")
                    success_count += 1
                else:
                    print(f"❌ Database update failed")
            else:
                print(f"⚠️ No videos found or extraction failed")
            
            # API 부하 방지를 위한 딜레이
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing {title}: {e}")
    
    print(f"YouTube UGC 업데이트 완료: {success_count}/{len(songs)} 성공")
    return success_count

def update_tiktok_ugc_counts():
    """TikTok UGC 카운트를 업데이트합니다."""
    print("\nTikTok UGC 카운트 업데이트 시작...")
    
    songs = db.get_songs_with_platform_ids('tiktok')
    success_count = 0
    
    for song in songs:
        song_id = song['id']
        title = song['title']
        artist = song['artist']
        tiktok_id = song['tiktok_id']
        
        if not tiktok_id:
            continue
            
        print(f"Processing: {title} - {artist} (TikTok ID: {tiktok_id})")
        
        # TikTok URL 구성
        tiktok_url = f"https://www.tiktok.com/music/x-{tiktok_id}"
        
        try:
            # UGC 카운트 수집
            ugc_count = scrape_tiktok_sound_data(tiktok_url)
            
            if ugc_count > 0:
                # 데이터베이스 업데이트
                if db.update_ugc_counts(song_id, tiktok_count=ugc_count):
                    print(f"✅ Updated: {ugc_count:,} TikTok videos")
                    success_count += 1
                else:
                    print(f"❌ Database update failed")
            else:
                print(f"⚠️ No videos found or extraction failed")
            
            # API 부하 방지를 위한 딜레이
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Error processing {title}: {e}")
    
    print(f"TikTok UGC 업데이트 완료: {success_count}/{len(songs)} 성공")
    return success_count

def update_all_ugc_counts():
    """모든 플랫폼의 UGC 카운트를 업데이트합니다."""
    print("=== UGC 데이터 업데이터 시작 ===")
    
    # 데이터베이스 초기화
    db.create_tables()
    
    # 업데이트 실행
    youtube_success = update_youtube_ugc_counts()
    tiktok_success = update_tiktok_ugc_counts()
    
    print(f"\n=== 업데이트 완료 ===")
    print(f"YouTube: {youtube_success}곡 업데이트")
    print(f"TikTok: {tiktok_success}곡 업데이트")
    print(f"총 {youtube_success + tiktok_success}곡의 UGC 데이터가 업데이트되었습니다.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
        if platform == 'youtube':
            db.create_tables()
            update_youtube_ugc_counts()
        elif platform == 'tiktok':
            db.create_tables()
            update_tiktok_ugc_counts()
        else:
            print("Usage: python ugc_data_updater.py [youtube|tiktok]")
            print("Or run without arguments to update both platforms")
            sys.exit(1)
    else:
        update_all_ugc_counts()