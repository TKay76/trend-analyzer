#!/usr/bin/env python3
"""
YouTube 미수집 곡들의 UGC 카운트를 일괄 수집하는 스크립트
"""

import sys
import os
import time
import subprocess
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__)))
from src.database import database_manager as db
from src.utils.logger_config import get_logger

logger = get_logger(__name__)

def get_missing_youtube_songs():
    """UGC 데이터가 없는 YouTube 곡들을 조회"""
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, artist, youtube_id 
                FROM songs 
                WHERE youtube_id IS NOT NULL AND youtube_ugc_count IS NULL
                ORDER BY id
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"❌ 미수집 곡 조회 실패: {e}")
        return []

def collect_single_youtube_song(song_id, title, artist, youtube_id):
    """개별 YouTube 곡의 UGC 수집"""
    shorts_url = f"https://www.youtube.com/source/{youtube_id}/shorts"
    
    try:
        logger.info(f"🎵 수집 시작: {title} - {artist}")
        
        # YouTube UGC 카운터 실행 (DB 저장 포함)
        venv_python = os.path.join(os.path.dirname(__file__), 'test_env', 'bin', 'python')
        result = subprocess.run([
            venv_python, 'src/scrapers/youtube_ugc_counter.py', shorts_url, '--save-db'
        ], capture_output=True, text=True, timeout=120)  # 2분 타임아웃
        
        if result.returncode == 0:
            # 성공한 경우 출력에서 UGC 카운트 추출
            try:
                ugc_count = int(result.stdout.strip().split('\n')[0])
                logger.info(f"✅ 수집 완료: {title} - {artist} → {ugc_count:,}개")
            except:
                logger.info(f"✅ 수집 완료: {title} - {artist}")
            return True
        else:
            logger.error(f"❌ 수집 실패: {title} - {artist}")
            logger.error(f"   오류: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ 타임아웃: {title} - {artist}")
        return False
    except Exception as e:
        logger.error(f"💥 예외 발생: {title} - {artist} → {e}")
        return False

def main():
    """메인 실행 함수"""
    start_time = time.time()
    
    logger.info("🚀 YouTube 미수집 곡 일괄 수집 시작")
    logger.info("=" * 60)
    
    # 미수집 곡 목록 조회
    missing_songs = get_missing_youtube_songs()
    
    if not missing_songs:
        logger.info("✅ 모든 YouTube 곡의 데이터가 이미 수집되었습니다!")
        return
    
    total_songs = len(missing_songs)
    logger.info(f"📊 수집 대상: {total_songs}개 곡")
    logger.info("=" * 60)
    
    success_count = 0
    error_count = 0
    
    for i, (song_id, title, artist, youtube_id) in enumerate(missing_songs, 1):
        logger.info(f"[{i}/{total_songs}] 처리 중...")
        
        if collect_single_youtube_song(song_id, title, artist, youtube_id):
            success_count += 1
        else:
            error_count += 1
        
        # 요청 간격 조절 (서버 부하 방지)
        if i < total_songs:  # 마지막 곡이 아니면 대기
            logger.info("⏳ 2초 대기 중...")
            time.sleep(2)
    
    # 최종 결과 요약
    duration = time.time() - start_time
    duration_min = duration / 60
    
    logger.info("=" * 60)
    logger.info("📊 YouTube 데이터 수집 완료!")
    logger.info(f"✅ 성공: {success_count}개 곡")
    logger.info(f"❌ 실패: {error_count}개 곡") 
    logger.info(f"⏱️ 소요 시간: {duration_min:.1f}분")
    logger.info(f"📈 성공률: {(success_count/total_songs)*100:.1f}%")
    
    if error_count > 0:
        logger.warning(f"⚠️ {error_count}개 곡에서 오류 발생. 로그를 확인해주세요.")
    
    # 수집 후 상태 확인
    remaining_songs = get_missing_youtube_songs()
    logger.info(f"🎯 남은 미수집 곡: {len(remaining_songs)}개")
    
    if len(remaining_songs) == 0:
        logger.info("🎉 모든 YouTube 곡의 UGC 수집 완료!")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)