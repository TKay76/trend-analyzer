#!/usr/bin/env python3
"""
해시태그 데이터 저장을 위한 데이터베이스 테이블 추가 스크립트
"""

import sqlite3
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.database_manager import DB_FILE, get_db_connection
from src.utils.logger_config import get_logger, log_database_operation, log_error_with_context

logger = get_logger(__name__)

def create_hashtag_tables():
    """
    해시태그 관련 테이블들을 생성합니다.
    """
    
    tables = [
        # 해시태그 기본 정보 테이블
        """
        CREATE TABLE IF NOT EXISTS hashtags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,                    -- 해시태그 이름 (# 없이)
            first_discovered DATE DEFAULT (date('now')), -- 처음 발견된 날짜
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_videos INTEGER DEFAULT 0,              -- 총 비디오 개수
            is_trending INTEGER DEFAULT 0,               -- 트렌딩 여부 (0: false, 1: true)
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # 해시태그 일별 통계 테이블
        """
        CREATE TABLE IF NOT EXISTS hashtag_daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hashtag_id INTEGER NOT NULL,
            video_count INTEGER NOT NULL,                -- 해당 날짜의 비디오 개수
            growth_rate REAL,                           -- 전날 대비 증가율
            rank_position INTEGER,                      -- 인기도 순위 (있는 경우)
            date DATE DEFAULT (date('now')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hashtag_id) REFERENCES hashtags (id),
            UNIQUE(hashtag_id, date)
        )
        """,
        
        # 곡과 해시태그 연관관계 테이블
        """
        CREATE TABLE IF NOT EXISTS song_hashtags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            hashtag_id INTEGER NOT NULL,
            frequency INTEGER DEFAULT 1,                -- 해당 곡에서 이 해시태그 등장 빈도
            first_seen DATE DEFAULT (date('now')),      -- 이 연관관계가 처음 발견된 날
            last_seen DATE DEFAULT (date('now')),       -- 마지막으로 확인된 날
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs (id),
            FOREIGN KEY (hashtag_id) REFERENCES hashtags (id),
            UNIQUE(song_id, hashtag_id)
        )
        """
    ]
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for i, table_sql in enumerate(tables, 1):
            try:
                cur.execute(table_sql)
                logger.info(f"✅ 테이블 {i}/3 생성 완료")
            except sqlite3.Error as e:
                log_error_with_context(logger, e, f"테이블 {i} 생성")
                raise
        
        conn.commit()
    
    log_database_operation(logger, "생성", "해시태그 테이블", 3)

def create_hashtag_indexes():
    """
    해시태그 테이블들에 대한 인덱스를 생성합니다.
    """
    
    indexes = [
        # hashtags 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_hashtags_name ON hashtags (name)",
        "CREATE INDEX IF NOT EXISTS idx_hashtags_trending ON hashtags (is_trending)",
        "CREATE INDEX IF NOT EXISTS idx_hashtags_total_videos ON hashtags (total_videos)",
        
        # hashtag_daily_stats 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_hashtag_daily_stats_hashtag_id ON hashtag_daily_stats (hashtag_id)",
        "CREATE INDEX IF NOT EXISTS idx_hashtag_daily_stats_date ON hashtag_daily_stats (date)",
        "CREATE INDEX IF NOT EXISTS idx_hashtag_daily_stats_video_count ON hashtag_daily_stats (video_count)",
        "CREATE INDEX IF NOT EXISTS idx_hashtag_daily_stats_hashtag_date ON hashtag_daily_stats (hashtag_id, date)",
        
        # song_hashtags 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_song_id ON song_hashtags (song_id)",
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_hashtag_id ON song_hashtags (hashtag_id)",
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_frequency ON song_hashtags (frequency)",
    ]
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        created_count = 0
        for index_sql in indexes:
            try:
                cur.execute(index_sql)
                created_count += 1
            except sqlite3.Error as e:
                logger.warning(f"⚠️ 인덱스 생성 실패: {e}")
        
        conn.commit()
    
    logger.info(f"📊 생성된 인덱스: {created_count}/{len(indexes)}개")

def add_hashtag_functions_to_database_manager():
    """
    database_manager.py에 추가할 해시태그 관련 함수들의 예시를 출력합니다.
    """
    
    function_examples = '''
# database_manager.py에 추가할 함수들:

def add_hashtag_and_get_id(name):
    """해시태그를 추가하고 ID를 반환합니다."""
    sql = """
    INSERT INTO hashtags (name) 
    VALUES (?) 
    ON CONFLICT(name) DO UPDATE SET last_updated = CURRENT_TIMESTAMP
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (name,))
        
        # ID 조회
        cur.execute("SELECT id FROM hashtags WHERE name = ?", (name,))
        result = cur.fetchone()
        conn.commit()
        return result['id'] if result else None

def update_hashtag_stats(hashtag_id, video_count, growth_rate=None, rank_position=None):
    """해시태그 일별 통계를 업데이트합니다."""
    sql = """
    INSERT OR REPLACE INTO hashtag_daily_stats 
    (hashtag_id, video_count, growth_rate, rank_position, date)
    VALUES (?, ?, ?, ?, date('now'))
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (hashtag_id, video_count, growth_rate, rank_position))
        
        # hashtags 테이블의 total_videos도 업데이트
        cur.execute("UPDATE hashtags SET total_videos = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?", 
                   (video_count, hashtag_id))
        conn.commit()

def link_song_hashtag(song_id, hashtag_id, frequency=1):
    """곡과 해시태그를 연결합니다."""
    sql = """
    INSERT INTO song_hashtags (song_id, hashtag_id, frequency, last_seen)
    VALUES (?, ?, ?, date('now'))
    ON CONFLICT(song_id, hashtag_id) DO UPDATE SET 
        frequency = frequency + ?,
        last_seen = date('now')
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (song_id, hashtag_id, frequency, frequency))
        conn.commit()

def get_trending_hashtags(limit=20):
    """트렌딩 해시태그를 조회합니다."""
    sql = """
    SELECT h.name, h.total_videos, hds.growth_rate, hds.video_count
    FROM hashtags h
    LEFT JOIN hashtag_daily_stats hds ON h.id = hds.hashtag_id AND hds.date = date('now')
    WHERE h.is_trending = 1 OR hds.growth_rate > 0.1
    ORDER BY h.total_videos DESC, hds.growth_rate DESC
    LIMIT ?
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (limit,))
        return cur.fetchall()

def get_song_hashtags(song_id):
    """특정 곡의 해시태그들을 조회합니다."""
    sql = """
    SELECT h.name, sh.frequency, sh.last_seen
    FROM song_hashtags sh
    JOIN hashtags h ON sh.hashtag_id = h.id
    WHERE sh.song_id = ?
    ORDER BY sh.frequency DESC
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (song_id,))
        return cur.fetchall()
'''
    
    print("\n💡 database_manager.py 확장 가이드:")
    print("=" * 60)
    print(function_examples)

def analyze_current_database():
    """
    현재 데이터베이스 상태를 분석합니다.
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 기존 테이블 확인
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        logger.info(f"📊 현재 데이터베이스 테이블: {', '.join(tables)}")
        
        # songs 테이블 레코드 수 확인
        if 'songs' in tables:
            cur.execute("SELECT COUNT(*) FROM songs")
            song_count = cur.fetchone()[0]
            logger.info(f"🎵 저장된 곡 수: {song_count:,}개")
        
        # daily_trends 테이블 레코드 수 확인
        if 'daily_trends' in tables:
            cur.execute("SELECT COUNT(*) FROM daily_trends")
            trend_count = cur.fetchone()[0]
            logger.info(f"📈 트렌드 레코드 수: {trend_count:,}개")

def main():
    """
    메인 실행 함수
    """
    logger.info("🏷️ 해시태그 테이블 추가 스크립트 시작")
    
    try:
        # 1. 현재 상태 분석
        logger.info("1️⃣ 현재 데이터베이스 상태 분석...")
        analyze_current_database()
        
        # 2. 해시태그 테이블 생성
        logger.info("\n2️⃣ 해시태그 테이블 생성...")
        create_hashtag_tables()
        
        # 3. 인덱스 생성
        logger.info("\n3️⃣ 해시태그 인덱스 생성...")
        create_hashtag_indexes()
        
        # 4. 확장 가이드 출력
        logger.info("\n4️⃣ 데이터베이스 매니저 확장 가이드...")
        add_hashtag_functions_to_database_manager()
        
        logger.info("\n🎉 해시태그 테이블 추가 완료!")
        logger.info("💡 이제 tiktok_hashtag_counter.py를 사용하여 해시태그 데이터를 수집할 수 있습니다.")
        
    except Exception as e:
        log_error_with_context(logger, e, "해시태그 테이블 추가")
        raise

if __name__ == "__main__":
    main()