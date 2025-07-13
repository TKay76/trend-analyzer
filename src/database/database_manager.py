import sqlite3
import json
import os
from contextlib import contextmanager

# 프로젝트 루트에서 data 폴더 내의 데이터베이스 파일 경로
DB_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'trend_analysis.db')

@contextmanager
def get_db_connection():
    """SQLite DB 커넥션을 생성하고 관리하는 컨텍스트 매니저"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # 결과를 딕셔너리처럼 접근 가능하게 함
        yield conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
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
            date DATE DEFAULT (date('now')),
            FOREIGN KEY (song_id) REFERENCES songs (id),
            UNIQUE(song_id, source, category, date)
        )
        """
    )
    with get_db_connection() as conn:
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()

def add_song_and_get_id(title, artist, thumbnail_url=None, youtube_id=None, tiktok_id=None, is_approved=None):
    """
    songs 테이블에 노래를 추가(이미 있으면 무시)하고, 해당 노래의 id를 반환합니다.
    """
    # SQLite는 BOOLEAN 타입이 없으므로 INTEGER로 변환 (True -> 1, False -> 0)
    is_approved_int = 1 if is_approved else 0 if is_approved is not None else None

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

def add_trend(song_id, source, category, rank, metrics=None):
    """
    daily_trends 테이블에 트렌드 데이터를 추가합니다.
    같은 날짜에 같은 곡의 트렌드 데이터가 이미 있으면 업데이트합니다.
    """
    # metrics 딕셔너리를 JSON 문자열로 변환
    metrics_json = json.dumps(metrics) if metrics else None

    sql = """
    INSERT OR REPLACE INTO daily_trends (song_id, source, category, rank, metrics, date)
    VALUES (?, ?, ?, ?, ?, date('now'));
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (song_id, source, category, rank, metrics_json))
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
    print("Initializing database and creating tables if they don't exist...")
    create_tables()
    print(f"Tables are ready in '{DB_FILE}'.")