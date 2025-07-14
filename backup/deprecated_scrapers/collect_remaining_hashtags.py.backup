#!/usr/bin/env python3
"""
남은 곡들의 해시태그 수집 스크립트
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.scrapers.tiktok_ugc_counter import scrape_tiktok_sound_data
from src.database import database_manager as db

def collect_remaining_hashtags(limit=5):
    """남은 곡들의 해시태그를 수집합니다."""
    
    # 이미 완료된 곡들 확인
    import sqlite3
    conn = sqlite3.connect('data/trend_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT song_id FROM song_hashtags')
    completed_songs = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT id, title, artist, tiktok_id FROM songs WHERE tiktok_id IS NOT NULL')
    all_songs = cursor.fetchall()
    conn.close()
    
    # 미완료 곡들 필터링
    remaining_songs = [song for song in all_songs if song[0] not in completed_songs]
    
    print(f"전체 TikTok 곡: {len(all_songs)}개")
    print(f"완료된 곡: {len(completed_songs)}개") 
    print(f"남은 곡: {len(remaining_songs)}개")
    print(f"이번에 처리할 곡: {min(limit, len(remaining_songs))}개")
    print("-" * 50)
    
    success_count = 0
    
    for i, song in enumerate(remaining_songs[:limit], 1):
        song_id, title, artist, tiktok_id = song
        
        print(f"[{i}/{min(limit, len(remaining_songs))}] 처리 중: {title} - {artist}")
        print(f"TikTok ID: {tiktok_id}")
        
        try:
            # TikTok URL 구성
            tiktok_url = f"https://www.tiktok.com/music/x-{tiktok_id}"
            
            # 해시태그 및 비디오 개수 수집
            result = scrape_tiktok_sound_data(tiktok_url)
            
            if result['success'] and result['video_count'] > 0:
                # 비디오 카운트 업데이트
                if db.update_ugc_counts(song_id, tiktok_count=result['video_count']):
                    print(f"✅ 비디오 업데이트: {result['video_count']:,}개")
                    
                    # 해시태그 저장
                    if result['top_hashtags']:
                        db.save_song_hashtags(song_id, result['top_hashtags'])
                        print(f"🏷️ 해시태그 저장: {len(result['top_hashtags'])}개")
                        print(f"📌 상위 해시태그: {', '.join([f'#{tag}({count})' for tag, count in result['top_hashtags'][:5]])}")
                    
                    success_count += 1
                else:
                    print(f"❌ 데이터베이스 업데이트 실패")
            else:
                error_msg = result.get('error_message', 'No videos found')
                print(f"⚠️ {error_msg}")
            
            print("-" * 50)
            
            # API 부하 방지를 위한 딜레이
            if i < min(limit, len(remaining_songs)):
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            print("-" * 50)
    
    print(f"\n🎉 수집 완료: {success_count}/{min(limit, len(remaining_songs))} 성공")
    print(f"남은 곡: {len(remaining_songs) - limit}개")

if __name__ == "__main__":
    limit = 5  # 한 번에 5개씩 처리
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("올바른 숫자를 입력해주세요.")
            sys.exit(1)
    
    collect_remaining_hashtags(limit)