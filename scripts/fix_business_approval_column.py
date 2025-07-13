#!/usr/bin/env python3
"""
is_approved_for_business_use 컬럼의 NULL 문제 해결 스크립트
1. 기존 NULL 값들을 0으로 업데이트
2. 향후 INSERT 시 기본값 0 설정을 위한 가이드 제공
"""

import sqlite3
import os
import sys

# 프로젝트 루트 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.database_manager import DB_FILE, get_db_connection

def analyze_current_state():
    """
    현재 is_approved_for_business_use 컬럼의 상태를 분석
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 전체 통계
        cur.execute("SELECT COUNT(*) as total_songs FROM songs")
        total = cur.fetchone()['total_songs']
        
        # NULL 개수
        cur.execute("SELECT COUNT(*) as null_count FROM songs WHERE is_approved_for_business_use IS NULL")
        null_count = cur.fetchone()['null_count']
        
        # 승인됨 (1) 개수
        cur.execute("SELECT COUNT(*) as approved_count FROM songs WHERE is_approved_for_business_use = 1")
        approved_count = cur.fetchone()['approved_count']
        
        # 승인 안됨 (0) 개수
        cur.execute("SELECT COUNT(*) as not_approved_count FROM songs WHERE is_approved_for_business_use = 0")
        not_approved_count = cur.fetchone()['not_approved_count']
        
        print(f"📊 현재 상태 분석:")
        print(f"   전체 곡 수: {total}")
        print(f"   NULL (알 수 없음): {null_count} ({null_count/total*100:.1f}%)")
        print(f"   승인됨 (1): {approved_count} ({approved_count/total*100:.1f}%)")
        print(f"   승인 안됨 (0): {not_approved_count} ({not_approved_count/total*100:.1f}%)")
        
        return null_count, total

def demonstrate_null_problem():
    """
    NULL로 인한 쿼리 문제를 실제로 보여줌
    """
    print(f"\n🚨 NULL 문제 시연:")
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 문제가 있는 쿼리들
        queries = [
            ("승인되지 않은 곡 (= 0)", "SELECT COUNT(*) FROM songs WHERE is_approved_for_business_use = 0"),
            ("승인되지 않은 곡 (!= 1)", "SELECT COUNT(*) FROM songs WHERE is_approved_for_business_use != 1"),
            ("승인된 곡 (= 1)", "SELECT COUNT(*) FROM songs WHERE is_approved_for_business_use = 1"),
            ("NULL 포함 승인 안된 곡", "SELECT COUNT(*) FROM songs WHERE is_approved_for_business_use = 0 OR is_approved_for_business_use IS NULL")
        ]
        
        for description, query in queries:
            cur.execute(query)
            result = cur.fetchone()[0]
            print(f"   {description}: {result}개")

def fix_null_values():
    """
    기존 NULL 값들을 0으로 업데이트
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # NULL 값들을 0으로 업데이트
        cur.execute("""
        UPDATE songs 
        SET is_approved_for_business_use = 0 
        WHERE is_approved_for_business_use IS NULL
        """)
        
        updated_count = cur.rowcount
        conn.commit()
        
        print(f"✅ {updated_count}개의 NULL 값을 0으로 업데이트했습니다.")
        return updated_count

def create_new_table_with_default():
    """
    기본값이 설정된 새로운 테이블 구조를 생성하는 방법을 보여줌
    (SQLite는 기존 컬럼에 DEFAULT 추가가 제한적이므로)
    """
    new_table_sql = """
    -- 새로운 songs 테이블 구조 (기본값 포함)
    CREATE TABLE IF NOT EXISTS songs_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        thumbnail_url TEXT,
        youtube_id TEXT,
        tiktok_id TEXT,
        is_approved_for_business_use INTEGER DEFAULT 0 NOT NULL, -- 기본값 0 설정!
        youtube_ugc_count INTEGER,
        tiktok_ugc_count INTEGER,
        ugc_last_updated DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(title, artist)
    );
    """
    
    print(f"\n💡 향후 권장 테이블 구조:")
    print(new_table_sql)
    
    migration_guide = """
    📝 완전한 마이그레이션 방법 (선택사항):
    1. CREATE TABLE songs_new (...);
    2. INSERT INTO songs_new SELECT ..., COALESCE(is_approved_for_business_use, 0), ... FROM songs;
    3. DROP TABLE songs;
    4. ALTER TABLE songs_new RENAME TO songs;
    """
    print(migration_guide)

def verify_fix():
    """
    수정 후 상태 검증
    """
    print(f"\n🔍 수정 후 검증:")
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # NULL 개수 재확인
        cur.execute("SELECT COUNT(*) as null_count FROM songs WHERE is_approved_for_business_use IS NULL")
        null_count = cur.fetchone()['null_count']
        
        if null_count == 0:
            print("✅ 모든 NULL 값이 제거되었습니다!")
        else:
            print(f"⚠️ 아직 {null_count}개의 NULL 값이 남아있습니다.")
        
        # 수정 후 쿼리 테스트
        demonstrate_null_problem()

def update_database_manager_logic():
    """
    database_manager.py의 로직 개선 제안을 출력
    """
    print(f"\n🔧 database_manager.py 개선 제안:")
    
    improvement_code = '''
def add_song_and_get_id(title, artist, thumbnail_url=None, youtube_id=None, tiktok_id=None, is_approved=None):
    """
    개선된 버전: is_approved가 None일 때 명시적으로 False(0)로 설정
    """
    # None인 경우 명시적으로 False로 설정 (NULL 방지)
    is_approved_int = 1 if is_approved is True else 0
    
    sql_insert = """
    INSERT INTO songs (title, artist, thumbnail_url, youtube_id, tiktok_id, is_approved_for_business_use)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(title, artist) DO NOTHING;
    """
    
    # ... 나머지 코드
'''
    print(improvement_code)

def main():
    """
    메인 실행 함수
    """
    print("🔧 is_approved_for_business_use NULL 문제 해결을 시작합니다...")
    
    try:
        # 1. 현재 상태 분석
        print("\n1️⃣ 현재 상태 분석...")
        null_count, total = analyze_current_state()
        
        if null_count == 0:
            print("✅ NULL 값이 없습니다. 문제가 이미 해결되었습니다!")
            return
        
        # 2. NULL 문제 시연
        demonstrate_null_problem()
        
        # 3. 사용자 확인
        print(f"\n⚠️ {null_count}개의 NULL 값을 0으로 변경하겠습니다.")
        user_input = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
        
        if user_input != 'y':
            print("❌ 사용자가 취소했습니다.")
            return
        
        # 4. NULL 값 수정
        print("\n2️⃣ NULL 값 수정 중...")
        updated_count = fix_null_values()
        
        # 5. 수정 검증
        print("\n3️⃣ 수정 결과 검증...")
        verify_fix()
        
        # 6. 향후 개선 제안
        print("\n4️⃣ 향후 개선 제안...")
        create_new_table_with_default()
        update_database_manager_logic()
        
        print("\n🎉 is_approved_for_business_use NULL 문제가 해결되었습니다!")
        print("💡 이제 WHERE is_approved_for_business_use = 0 쿼리가 정확하게 작동합니다.")
        
    except Exception as e:
        print(f"❌ 문제 해결 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()