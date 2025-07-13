import sqlite3
import pandas as pd
import os

def view_database():
    """데이터베이스 내용을 보기 좋게 출력"""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'trend_analysis.db')
    conn = sqlite3.connect(db_path)
    
    print("=== 데이터베이스 개요 ===")
    
    # 테이블 목록
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"테이블: {[table[0] for table in tables]}")
    
    # 전체 통계
    cursor.execute('SELECT COUNT(*) FROM songs')
    total_songs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM songs WHERE youtube_id IS NOT NULL AND youtube_id != ""')
    youtube_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM songs WHERE tiktok_id IS NOT NULL AND tiktok_id != ""')
    tiktok_count = cursor.fetchone()[0]
    
    print(f"\n총 곡 수: {total_songs}")
    print(f"YouTube ID 보유: {youtube_count}개")
    print(f"TikTok ID 보유: {tiktok_count}개")
    
    # 소스별 트렌드 데이터
    cursor.execute('SELECT source, COUNT(*) FROM daily_trends GROUP BY source')
    sources = cursor.fetchall()
    print(f"\n소스별 트렌드:")
    for source, count in sources:
        print(f"  {source}: {count}개")
    
    print("\n" + "="*80)
    
    while True:
        print("\n메뉴를 선택하세요:")
        print("1. 모든 곡 보기 (songs 테이블)")
        print("2. YouTube 곡만 보기")
        print("3. TikTok 곡만 보기") 
        print("4. 트렌드 데이터 보기 (daily_trends 테이블)")
        print("5. 특정 곡 검색")
        print("6. 종료")
        
        choice = input("\n선택 (1-6): ").strip()
        
        if choice == '1':
            show_all_songs(conn)
        elif choice == '2':
            show_youtube_songs(conn)
        elif choice == '3':
            show_tiktok_songs(conn)
        elif choice == '4':
            show_trends(conn)
        elif choice == '5':
            search_songs(conn)
        elif choice == '6':
            break
        else:
            print("잘못된 선택입니다.")
    
    conn.close()

def show_all_songs(conn):
    """모든 곡 보기"""
    query = """
    SELECT id, title, artist, youtube_id, tiktok_id, is_approved_for_business_use, created_at
    FROM songs 
    ORDER BY id
    """
    df = pd.read_sql_query(query, conn)
    print("\n=== 모든 곡 목록 ===")
    print(df.to_string(index=False, max_colwidth=30))

def show_youtube_songs(conn):
    """YouTube 곡만 보기"""
    query = """
    SELECT id, title, artist, youtube_id, created_at,
           'https://youtube.com/source/' || youtube_id || '/shorts' as youtube_url
    FROM songs 
    WHERE youtube_id IS NOT NULL AND youtube_id != ""
    ORDER BY id
    """
    df = pd.read_sql_query(query, conn)
    print("\n=== YouTube 곡 목록 ===")
    print(df.to_string(index=False, max_colwidth=50))

def show_tiktok_songs(conn):
    """TikTok 곡만 보기"""
    query = """
    SELECT id, title, artist, tiktok_id, is_approved_for_business_use, created_at,
           'https://www.tiktok.com/music/x-' || tiktok_id as tiktok_url
    FROM songs 
    WHERE tiktok_id IS NOT NULL AND tiktok_id != ""
    ORDER BY id
    """
    df = pd.read_sql_query(query, conn)
    print("\n=== TikTok 곡 목록 ===")
    print(df.to_string(index=False, max_colwidth=50))

def show_trends(conn):
    """트렌드 데이터 보기"""
    query = """
    SELECT dt.id, s.title, s.artist, dt.source, dt.category, dt.rank, dt.date
    FROM daily_trends dt
    JOIN songs s ON dt.song_id = s.id
    ORDER BY dt.source, dt.rank
    """
    df = pd.read_sql_query(query, conn)
    print("\n=== 트렌드 데이터 ===")
    print(df.to_string(index=False, max_colwidth=30))

def search_songs(conn):
    """곡 검색"""
    keyword = input("검색할 곡명 또는 아티스트명을 입력하세요: ").strip()
    
    query = """
    SELECT id, title, artist, youtube_id, tiktok_id, is_approved_for_business_use
    FROM songs 
    WHERE title LIKE ? OR artist LIKE ?
    ORDER BY id
    """
    df = pd.read_sql_query(query, conn, params=[f'%{keyword}%', f'%{keyword}%'])
    
    if len(df) > 0:
        print(f"\n=== '{keyword}' 검색 결과 ===")
        print(df.to_string(index=False, max_colwidth=30))
        
        # URL 생성
        for _, row in df.iterrows():
            print(f"\n{row['title']} - {row['artist']}:")
            if pd.notna(row['youtube_id']) and row['youtube_id']:
                print(f"  YouTube: https://youtube.com/source/{row['youtube_id']}/shorts")
            if pd.notna(row['tiktok_id']) and row['tiktok_id']:
                print(f"  TikTok: https://www.tiktok.com/music/x-{row['tiktok_id']}")
    else:
        print("검색 결과가 없습니다.")

if __name__ == "__main__":
    view_database()