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

def update_youtube_ugc_counts(batch_size=3, max_songs=None):
    """YouTube UGC 카운트를 배치 처리로 업데이트합니다."""
    print(f"\nYouTube UGC 카운트 배치 업데이트 시작... (배치 크기: {batch_size})")
    
    # 이미 UGC 데이터가 수집된 곡들 확인
    import sqlite3
    conn = sqlite3.connect('data/trend_analysis.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT id FROM songs WHERE youtube_ugc_count IS NOT NULL AND youtube_ugc_count > 0')
    completed_songs = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    # 전체 YouTube 곡 조회
    songs = db.get_songs_with_platform_ids('youtube')
    
    # 미완료 곡들만 필터링
    remaining_songs = [song for song in songs if song['id'] not in completed_songs]
    
    # max_songs 제한 적용
    if max_songs:
        remaining_songs = remaining_songs[:max_songs]
    
    print(f"전체 YouTube 곡: {len(songs)}개")
    print(f"완료된 곡: {len(completed_songs)}개")
    print(f"남은 곡: {len(remaining_songs)}개")
    print("-" * 60)
    
    if not remaining_songs:
        print("✅ 모든 YouTube 곡의 UGC 수집이 완료되었습니다!")
        return len(songs)
    
    total_success = 0
    
    # 배치 처리
    for batch_start in range(0, len(remaining_songs), batch_size):
        batch_end = min(batch_start + batch_size, len(remaining_songs))
        batch_songs = remaining_songs[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (len(remaining_songs) + batch_size - 1) // batch_size
        
        print(f"🔄 배치 {batch_num}/{total_batches} 처리 중 ({len(batch_songs)}개 곡)")
        print("=" * 60)
        
        batch_success = 0
        
        for i, song in enumerate(batch_songs, 1):
            song_id = song['id']
            title = song['title']
            artist = song['artist']
            youtube_id = song['youtube_id']
            
            if not youtube_id:
                continue
                
            print(f"[{i}/{len(batch_songs)}] {title} - {artist}")
            print(f"    YouTube ID: {youtube_id}")
            
            # YouTube URL 구성
            youtube_url = f"https://youtube.com/source/{youtube_id}/shorts"
            
            try:
                # UGC 카운트 수집
                ugc_count = scrape_youtube_shorts_data(youtube_url)
                
                if ugc_count > 0:
                    # 데이터베이스 업데이트
                    if db.update_ugc_counts(song_id, youtube_count=ugc_count):
                        print(f"    ✅ 성공: {ugc_count:,}개")
                        batch_success += 1
                        total_success += 1
                    else:
                        print(f"    ❌ DB 업데이트 실패")
                else:
                    print(f"    ⚠️ UGC 데이터 없음")
                
                # API 부하 방지를 위한 딜레이
                if i < len(batch_songs):
                    time.sleep(3)
                
            except Exception as e:
                print(f"    💥 오류: {e}")
            
            print("-" * 40)
        
        # 배치 완료 요약
        print(f"📊 배치 {batch_num} 완료: {batch_success}/{len(batch_songs)} 성공")
        print(f"🎯 전체 진행률: {total_success + len(completed_songs)}/{len(songs)} ({(total_success + len(completed_songs))/len(songs)*100:.1f}%)")
        
        if batch_start + batch_size < len(remaining_songs):
            print(f"⏳ 다음 배치까지 5초 대기...")
            time.sleep(5)
        
        print("=" * 60)
    
    print(f"\n🎉 YouTube UGC 업데이트 완료!")
    print(f"✅ 이번 세션: {total_success}개 곡 성공")
    print(f"📊 전체 완료: {total_success + len(completed_songs)}/{len(songs)}개 곡")
    return total_success

def update_tiktok_ugc_counts(batch_size=5):
    """TikTok UGC 카운트를 배치 처리로 업데이트합니다."""
    print(f"\nTikTok UGC 카운트 배치 업데이트 시작... (배치 크기: {batch_size})")
    
    # 이미 해시태그가 수집된 곡들 확인
    import sqlite3
    conn = sqlite3.connect('data/trend_analysis.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT song_id FROM song_hashtags')
    completed_songs = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    # 전체 TikTok 곡 조회
    songs = db.get_songs_with_platform_ids('tiktok')
    
    # 미완료 곡들만 필터링
    remaining_songs = [song for song in songs if song['id'] not in completed_songs]
    
    print(f"전체 TikTok 곡: {len(songs)}개")
    print(f"완료된 곡: {len(completed_songs)}개")
    print(f"남은 곡: {len(remaining_songs)}개")
    print("-" * 60)
    
    if not remaining_songs:
        print("✅ 모든 TikTok 곡의 해시태그 수집이 완료되었습니다!")
        return len(songs)
    
    total_success = 0
    
    # 배치 처리
    for batch_start in range(0, len(remaining_songs), batch_size):
        batch_end = min(batch_start + batch_size, len(remaining_songs))
        batch_songs = remaining_songs[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (len(remaining_songs) + batch_size - 1) // batch_size
        
        print(f"🔄 배치 {batch_num}/{total_batches} 처리 중 ({len(batch_songs)}개 곡)")
        print("=" * 60)
        
        batch_success = 0
        
        for i, song in enumerate(batch_songs, 1):
            song_id = song['id']
            title = song['title']
            artist = song['artist']
            tiktok_id = song['tiktok_id']
            
            if not tiktok_id:
                continue
                
            print(f"[{i}/{len(batch_songs)}] {title} - {artist}")
            print(f"    TikTok ID: {tiktok_id}")
            
            # TikTok URL 구성
            tiktok_url = f"https://www.tiktok.com/music/x-{tiktok_id}"
            
            try:
                # UGC 카운트 및 해시태그 수집
                result = scrape_tiktok_sound_data(tiktok_url)
                
                if result['success'] and result['video_count'] > 0:
                    # 비디오 카운트 업데이트
                    if db.update_ugc_counts(song_id, tiktok_count=result['video_count']):
                        print(f"    ✅ 비디오: {result['video_count']:,}개")
                        
                        # 해시태그 저장
                        if result['top_hashtags']:
                            db.save_song_hashtags(song_id, result['top_hashtags'])
                            print(f"    🏷️ 해시태그: {len(result['top_hashtags'])}개")
                            top_tags = ', '.join([f'#{tag}({count})' for tag, count in result['top_hashtags'][:3]])
                            print(f"    📌 상위: {top_tags}...")
                        
                        batch_success += 1
                        total_success += 1
                    else:
                        print(f"    ❌ 데이터베이스 업데이트 실패")
                else:
                    error_msg = result.get('error_message', 'No videos found')
                    print(f"    ⚠️ {error_msg}")
                
                # API 부하 방지를 위한 딜레이
                if i < len(batch_songs):
                    time.sleep(3)
                
            except Exception as e:
                print(f"    ❌ 오류: {e}")
            
            print("-" * 40)
        
        # 배치 완료 요약
        print(f"📊 배치 {batch_num} 완료: {batch_success}/{len(batch_songs)} 성공")
        print(f"🎯 전체 진행률: {total_success + len(completed_songs)}/{len(songs)} ({(total_success + len(completed_songs))/len(songs)*100:.1f}%)")
        
        if batch_start + batch_size < len(remaining_songs):
            print(f"⏳ 다음 배치까지 5초 대기...")
            time.sleep(5)
        
        print("=" * 60)
    
    print(f"\n🎉 TikTok UGC 업데이트 완료!")
    print(f"✅ 이번 세션: {total_success}개 곡 성공")
    print(f"📊 전체 완료: {total_success + len(completed_songs)}/{len(songs)}개 곡")
    return total_success

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