#!/usr/bin/env python3
"""
YouTube UGC 데이터 배치 수집
"""

import sqlite3
import time
from src.scrapers.youtube_ugc_counter import scrape_youtube_shorts_data
from src.database import database_manager as db

def collect_all_youtube_ugc():
    """모든 YouTube 곡의 UGC 데이터 수집"""
    
    # 미수집 YouTube 곡들 조회
    conn = sqlite3.connect('data/trend_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, artist, youtube_id 
        FROM songs 
        WHERE youtube_id IS NOT NULL 
          AND (youtube_ugc_count IS NULL OR youtube_ugc_count = 0)
    ''')
    
    remaining_songs = cursor.fetchall()
    conn.close()
    
    print(f"📺 YouTube UGC 수집 시작")
    print(f"대상 곡: {len(remaining_songs)}개")
    print("=" * 60)
    
    success_count = 0
    
    for i, (song_id, title, artist, youtube_id) in enumerate(remaining_songs, 1):
        print(f"[{i}/{len(remaining_songs)}] {title} - {artist}")
        print(f"    YouTube ID: {youtube_id}")
        
        url = f"https://youtube.com/source/{youtube_id}/shorts"
        
        try:
            count = scrape_youtube_shorts_data(url)
            
            if count > 0:
                success = db.update_ugc_counts(song_id, youtube_count=count)
                if success:
                    print(f"    ✅ 성공: {count:,}개 → DB 저장됨")
                    success_count += 1
                else:
                    print(f"    ❌ DB 저장 실패")
            else:
                print(f"    ⚠️ UGC 데이터 없음")
            
            # API 부하 방지
            if i < len(remaining_songs):
                print(f"    ⏳ 3초 대기...")
                time.sleep(3)
                
        except Exception as e:
            print(f"    💥 오류: {e}")
        
        print("-" * 40)
    
    print(f"\n🎉 YouTube UGC 수집 완료!")
    print(f"✅ 성공: {success_count}/{len(remaining_songs)}")

if __name__ == "__main__":
    collect_all_youtube_ugc()