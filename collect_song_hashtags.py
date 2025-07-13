#!/usr/bin/env python3
"""
TikTok 음원별 해시태그 수집 스크립트
데이터베이스에 저장된 TikTok 음원들의 해시태그를 수집하여 데이터베이스에 저장합니다.
"""

import sys
import os
import time

sys.path.append('.')
from src.database.database_manager import get_songs_with_platform_ids, save_song_hashtags, update_ugc_counts
from src.scrapers.tiktok_ugc_counter import scrape_tiktok_sound_data
from src.utils.logger_config import get_logger, log_error_with_context

logger = get_logger(__name__)

def collect_hashtags_for_all_songs(limit=None):
    """
    데이터베이스의 모든 TikTok 음원에 대해 해시태그를 수집합니다.
    
    Args:
        limit: 처리할 곡 수 제한 (None이면 모든 곡 처리)
    """
    logger.info("🎵 TikTok 음원 해시태그 수집 시작")
    
    # TikTok ID가 있는 곡들 조회
    songs = get_songs_with_platform_ids(platform='tiktok')
    
    if limit:
        songs = songs[:limit]
    
    logger.info(f"📊 처리할 곡: {len(songs)}개")
    
    success_count = 0
    failed_count = 0
    
    for i, song in enumerate(songs, 1):
        song_id = song['id']
        title = song['title']
        artist = song['artist']
        tiktok_id = song['tiktok_id']
        
        logger.info(f"[{i}/{len(songs)}] 처리 중: {title} - {artist}")
        
        try:
            # TikTok 음악 페이지 URL 생성
            url = f"https://www.tiktok.com/music/x-{tiktok_id}"
            
            # 해시태그 및 비디오 개수 수집
            result = scrape_tiktok_sound_data(url)
            
            if result['success']:
                # 비디오 개수 업데이트
                if result['video_count'] > 0:
                    update_ugc_counts(song_id, tiktok_count=result['video_count'])
                
                # 해시태그 저장 (상위 10개)
                if result['top_hashtags']:
                    save_song_hashtags(song_id, result['top_hashtags'])
                    
                    logger.info(f"✅ 성공: 비디오 {result['video_count']:,}개, 해시태그 {len(result['top_hashtags'])}개")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ 해시태그 없음: {title} - {artist}")
                    success_count += 1  # 비디오 개수라도 수집했으면 성공으로 간주
            else:
                logger.error(f"❌ 실패: {result.get('error_message', '알 수 없는 오류')}")
                failed_count += 1
                
        except Exception as e:
            log_error_with_context(logger, e, f"곡 처리 실패: {title} - {artist}")
            failed_count += 1
            
        # 요청 간격 조절 (서버 부하 방지)
        if i < len(songs):
            time.sleep(2)
    
    # 결과 요약
    logger.info("🏁 해시태그 수집 완료")
    logger.info(f"✅ 성공: {success_count}개")
    logger.info(f"❌ 실패: {failed_count}개")
    logger.info(f"📊 성공률: {success_count/(success_count+failed_count)*100:.1f}%")

def collect_hashtags_for_song(song_id):
    """특정 곡의 해시태그를 수집합니다."""
    from src.database.database_manager import get_db_connection
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, artist, tiktok_id 
            FROM songs 
            WHERE id = ? AND tiktok_id IS NOT NULL AND tiktok_id != ''
        """, (song_id,))
        song = cur.fetchone()
    
    if not song:
        logger.error(f"❌ 곡을 찾을 수 없거나 TikTok ID가 없습니다: {song_id}")
        return False
    
    title = song['title']
    artist = song['artist'] 
    tiktok_id = song['tiktok_id']
    
    logger.info(f"🎵 해시태그 수집: {title} - {artist}")
    
    try:
        url = f"https://www.tiktok.com/music/x-{tiktok_id}"
        result = scrape_tiktok_sound_data(url)
        
        if result['success']:
            # 비디오 개수 업데이트
            if result['video_count'] > 0:
                update_ugc_counts(song_id, tiktok_count=result['video_count'])
            
            # 해시태그 저장
            if result['top_hashtags']:
                save_song_hashtags(song_id, result['top_hashtags'])
                
                logger.info(f"✅ 수집 완료: 비디오 {result['video_count']:,}개, 해시태그 {len(result['top_hashtags'])}개")
                
                # 결과 출력
                print(f"\n🎵 {title} - {artist}")
                print(f"📹 비디오 개수: {result['video_count']:,}")
                print(f"🏷️ 상위 해시태그:")
                for rank, (hashtag, count) in enumerate(result['top_hashtags'], 1):
                    print(f"  {rank:2d}. #{hashtag}: {count:,}회")
                
                return True
            else:
                logger.warning("⚠️ 해시태그를 찾을 수 없습니다")
                return False
        else:
            logger.error(f"❌ 수집 실패: {result.get('error_message', '알 수 없는 오류')}")
            return False
            
    except Exception as e:
        log_error_with_context(logger, e, f"해시태그 수집 실패")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--song-id" and len(sys.argv) > 2:
            # 특정 곡 처리
            try:
                song_id = int(sys.argv[2])
                collect_hashtags_for_song(song_id)
            except ValueError:
                print("❌ 올바른 곡 ID를 입력해주세요.")
                sys.exit(1)
        else:
            # 개수 제한
            try:
                limit = int(sys.argv[1])
                print(f"🎯 제한: {limit}개 곡만 처리")
                collect_hashtags_for_all_songs(limit=limit)
            except ValueError:
                print("❌ 올바른 숫자를 입력해주세요.")
                sys.exit(1)
    else:
        # 모든 곡 처리
        print("🎯 모든 곡을 처리합니다.")
        collect_hashtags_for_all_songs()