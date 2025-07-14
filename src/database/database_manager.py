import sqlite3
import json
import os
from contextlib import contextmanager
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.logger_config import get_logger, log_database_operation, log_error_with_context

# 로거 설정
logger = get_logger(__name__)

# 프로젝트 루트에서 data 폴더 내의 데이터베이스 파일 경로
DB_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'music_trends.db')

def parse_metric_value(metric_str):
    """
    "1.2M", "500K", "123,456" 등의 문자열을 숫자로 변환
    """
    if not metric_str or metric_str == "Unknown Metrics":
        return None
    
    # 쉼표 제거 및 정리
    metric_str = metric_str.replace(',', '').strip()
    
    try:
        if 'K' in metric_str.upper():
            return int(float(metric_str.upper().replace('K', '')) * 1000)
        elif 'M' in metric_str.upper():
            return int(float(metric_str.upper().replace('M', '')) * 1000000)
        elif 'B' in metric_str.upper():
            return int(float(metric_str.upper().replace('B', '')) * 1000000000)
        else:
            # 숫자만 있는 경우
            return int(float(metric_str))
    except (ValueError, TypeError):
        return None

@contextmanager
def get_db_connection():
    """SQLite DB 커넥션을 생성하고 관리하는 컨텍스트 매니저"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # 결과를 딕셔너리처럼 접근 가능하게 함
        yield conn
    except sqlite3.Error as e:
        log_error_with_context(logger, e, "데이터베이스 연결")
        raise
    finally:
        if conn:
            conn.close()

def create_tables():
    """songs와 daily_trends 테이블을 생성합니다."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            thumbnail_url TEXT,
            youtube_id TEXT,
            tiktok_id TEXT,
            is_approved_for_business_use INTEGER, -- 0 for False, 1 for True
            youtube_ugc_count INTEGER, -- YouTube UGC video count
            tiktok_ugc_count INTEGER, -- TikTok UGC video count
            ugc_last_updated DATETIME, -- Last time UGC counts were updated
            is_trending INTEGER DEFAULT 0, -- 인기급상승 태그 (Biggest movers)
            is_new_hit INTEGER DEFAULT 0, -- 가장인기 있는 신곡 태그 (Highest debut)
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title, artist)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            rank INTEGER NOT NULL,
            metrics TEXT, -- JSON stored as TEXT
            daily_view_count INTEGER, -- 일일 조회수 (숫자)
            weekly_view_count INTEGER, -- 주간 조회수 (숫자)  
            engagement_rate REAL, -- 참여율 (소수점)
            date DATE DEFAULT (date('now')),
            FOREIGN KEY (song_id) REFERENCES songs (id),
            UNIQUE(song_id, source, category, date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS song_hashtags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            hashtag TEXT NOT NULL,
            count INTEGER NOT NULL,
            rank INTEGER NOT NULL, -- 해당 곡에서의 해시태그 순위 (1-10)
            collected_date DATE DEFAULT (date('now')),
            FOREIGN KEY (song_id) REFERENCES songs (id),
            UNIQUE(song_id, hashtag, collected_date)
        )
        """
    )
    with get_db_connection() as conn:
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        
    # 테이블 생성 후 인덱스도 함께 생성
    create_indexes()

def create_indexes():
    """성능 최적화를 위한 필수 인덱스들을 생성합니다."""
    indexes = [
        # daily_trends 테이블 인덱스들 (핵심 성능 개선)
        "CREATE INDEX IF NOT EXISTS idx_daily_trends_song_id ON daily_trends (song_id)",
        "CREATE INDEX IF NOT EXISTS idx_daily_trends_date ON daily_trends (date)",
        "CREATE INDEX IF NOT EXISTS idx_daily_trends_source ON daily_trends (source)",
        "CREATE INDEX IF NOT EXISTS idx_daily_trends_source_category ON daily_trends (source, category)",
        "CREATE INDEX IF NOT EXISTS idx_daily_trends_song_date ON daily_trends (song_id, date)",
        "CREATE INDEX IF NOT EXISTS idx_daily_trends_daily_view_count ON daily_trends (daily_view_count)",
        
        # songs 테이블 인덱스들
        "CREATE INDEX IF NOT EXISTS idx_songs_youtube_id ON songs (youtube_id)",
        "CREATE INDEX IF NOT EXISTS idx_songs_tiktok_id ON songs (tiktok_id)",
        "CREATE INDEX IF NOT EXISTS idx_songs_approval_status ON songs (is_approved_for_business_use)",
        "CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs (artist)",
        
        # song_hashtags 테이블 인덱스들
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_song_id ON song_hashtags (song_id)",
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_hashtag ON song_hashtags (hashtag)",
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_count ON song_hashtags (count)",
        "CREATE INDEX IF NOT EXISTS idx_song_hashtags_date ON song_hashtags (collected_date)"
    ]
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        for index_sql in indexes:
            try:
                cur.execute(index_sql)
            except sqlite3.Error as e:
                logger.warning(f"⚠️ 인덱스 생성 실패: {e}")
        conn.commit()

def add_song_and_get_id(title, artist, thumbnail_url=None, youtube_id=None, tiktok_id=None, is_approved=None):
    """
    songs 테이블에 노래를 추가(이미 있으면 무시)하고, 해당 노래의 id를 반환합니다.
    
    Args:
        is_approved: None일 경우 False(0)로 처리하여 NULL 방지
    """
    # NULL 방지: None인 경우 명시적으로 False(0)로 설정
    # True -> 1, False/None -> 0 (NULL 값 생성 방지)
    is_approved_int = 1 if is_approved is True else 0

    sql_insert = """
    INSERT INTO songs (title, artist, thumbnail_url, youtube_id, tiktok_id, is_approved_for_business_use)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(title, artist) DO NOTHING;
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql_insert, (title, artist, thumbnail_url, youtube_id, tiktok_id, is_approved_int))
        conn.commit()
        
        # song_id를 다시 조회하여 반환
        cur.execute("SELECT id FROM songs WHERE title = ? AND artist = ?", (title, artist))
        result = cur.fetchone()
        if result:
            return result['id']
        return None # 삽입 실패 또는 다른 문제

def update_song_tags(title, artist, is_trending=None, is_new_hit=None):
    """
    곡의 태그 정보를 업데이트합니다.
    """
    updates = []
    params = []
    
    if is_trending is not None:
        updates.append("is_trending = ?")
        params.append(1 if is_trending else 0)
    
    if is_new_hit is not None:
        updates.append("is_new_hit = ?")
        params.append(1 if is_new_hit else 0)
    
    if not updates:
        return False
    
    sql = f"UPDATE songs SET {', '.join(updates)} WHERE title = ? AND artist = ?"
    params.extend([title, artist])
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount > 0

def add_trend(song_id, source, category, rank, metrics=None, daily_view_count=None, weekly_view_count=None, engagement_rate=None):
    """
    daily_trends 테이블에 트렌드 데이터를 추가합니다.
    같은 날짜에 같은 곡의 트렌드 데이터가 이미 있으면 업데이트합니다.
    
    Args:
        song_id: 곡 ID
        source: 데이터 소스 (tiktok, youtube)
        category: 카테고리 (popular, breakout, trending 등)
        rank: 순위
        metrics: 레거시 지원을 위한 JSON 메트릭 (deprecated)
        daily_view_count: 일일 조회수 (정수)
        weekly_view_count: 주간 조회수 (정수)
        engagement_rate: 참여율 (소수)
    """
    # metrics 딕셔너리를 JSON 문자열로 변환 (하위 호환성)
    metrics_json = json.dumps(metrics) if metrics else None

    sql = """
    INSERT OR REPLACE INTO daily_trends 
    (song_id, source, category, rank, metrics, daily_view_count, weekly_view_count, engagement_rate, date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'));
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (song_id, source, category, rank, metrics_json, daily_view_count, weekly_view_count, engagement_rate))
        conn.commit()

def update_ugc_counts(song_id, youtube_count=None, tiktok_count=None):
    """UGC 동영상 개수를 업데이트합니다."""
    updates = []
    params = []
    
    if youtube_count is not None:
        updates.append("youtube_ugc_count = ?")
        params.append(youtube_count)
    
    if tiktok_count is not None:
        updates.append("tiktok_ugc_count = ?")
        params.append(tiktok_count)
    
    if updates:
        updates.append("ugc_last_updated = CURRENT_TIMESTAMP")
        params.append(song_id)
        
        sql = f"UPDATE songs SET {', '.join(updates)} WHERE id = ?"
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount > 0
    return False

def save_song_hashtags(song_id, top_hashtags):
    """
    곡의 상위 해시태그들을 데이터베이스에 저장합니다.
    
    Args:
        song_id: 곡 ID
        top_hashtags: [(hashtag, count), ...] 형태의 리스트 (순위순으로 정렬됨)
    """
    if not top_hashtags:
        return
        
    # 기존 해시태그 데이터 삭제 (오늘 날짜)
    delete_sql = """
    DELETE FROM song_hashtags 
    WHERE song_id = ? AND collected_date = date('now')
    """
    
    # 새 해시태그 데이터 삽입
    insert_sql = """
    INSERT INTO song_hashtags (song_id, hashtag, count, rank, collected_date)
    VALUES (?, ?, ?, ?, date('now'))
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 기존 데이터 삭제
        cur.execute(delete_sql, (song_id,))
        
        # 새 데이터 삽입
        for rank, (hashtag, count) in enumerate(top_hashtags, 1):
            cur.execute(insert_sql, (song_id, hashtag, count, rank))
        
        conn.commit()
        
        log_database_operation(logger, "저장", f"곡 {song_id}의 해시태그", len(top_hashtags))

def get_song_hashtags(song_id, limit=10):
    """곡의 해시태그를 조회합니다."""
    sql = """
    SELECT hashtag, count, rank 
    FROM song_hashtags 
    WHERE song_id = ? 
    ORDER BY rank ASC 
    LIMIT ?
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (song_id, limit))
        return cur.fetchall()

def get_hashtag_songs(hashtag, limit=20):
    """특정 해시태그가 사용된 곡들을 조회합니다."""
    sql = """
    SELECT s.title, s.artist, sh.count, sh.rank
    FROM song_hashtags sh
    JOIN songs s ON sh.song_id = s.id
    WHERE sh.hashtag = ?
    ORDER BY sh.count DESC
    LIMIT ?
    """
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (hashtag, limit))
        return cur.fetchall()

def get_songs_with_platform_ids(platform='both'):
    """플랫폼 ID가 있는 곡들을 조회합니다."""
    if platform == 'youtube':
        sql = "SELECT id, title, artist, youtube_id FROM songs WHERE youtube_id IS NOT NULL AND youtube_id != ''"
    elif platform == 'tiktok':
        sql = "SELECT id, title, artist, tiktok_id FROM songs WHERE tiktok_id IS NOT NULL AND tiktok_id != ''"
    else:  # both
        sql = """SELECT id, title, artist, youtube_id, tiktok_id 
                 FROM songs 
                 WHERE (youtube_id IS NOT NULL AND youtube_id != '') 
                    OR (tiktok_id IS NOT NULL AND tiktok_id != '')"""
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

if __name__ == '__main__':
    # 모듈이 직접 실행될 때 테이블 생성 로직을 수행
    logger.info("💾 데이터베이스 초기화 및 테이블 생성 중...")
    create_tables()
    logger.info(f"✅ 테이블 준비 완료: '{DB_FILE}'")