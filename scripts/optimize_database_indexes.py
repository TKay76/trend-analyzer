#!/usr/bin/env python3
"""
데이터베이스 인덱스 최적화 스크립트
자주 사용되는 쿼리 패턴에 맞춰 필수 인덱스들을 생성합니다.
"""

import sqlite3
import time
import os
import sys
from datetime import datetime, timedelta

# 프로젝트 루트 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.database_manager import DB_FILE, get_db_connection

def analyze_current_indexes():
    """
    현재 존재하는 인덱스를 분석
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        print("📊 현재 인덱스 상태:")
        
        # SQLite 마스터 테이블에서 인덱스 조회
        cur.execute("""
        SELECT name, tbl_name, sql 
        FROM sqlite_master 
        WHERE type = 'index' AND sql IS NOT NULL
        ORDER BY tbl_name, name
        """)
        
        indexes = cur.fetchall()
        
        if not indexes:
            print("   ❌ 사용자 정의 인덱스가 없습니다!")
        else:
            for idx in indexes:
                print(f"   ✅ {idx['tbl_name']}.{idx['name']}")
        
        return len(indexes)

def get_table_stats():
    """
    테이블별 레코드 수 조회
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        tables = ['songs', 'daily_trends']
        stats = {}
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cur.fetchone()['count']
                stats[table] = count
                print(f"📈 {table}: {count:,} 레코드")
            except sqlite3.OperationalError:
                stats[table] = 0
                print(f"📈 {table}: 테이블 없음")
        
        return stats

def create_essential_indexes():
    """
    필수 인덱스들을 생성
    """
    indexes_to_create = [
        # daily_trends 테이블 인덱스들
        {
            "name": "idx_daily_trends_song_id",
            "table": "daily_trends", 
            "columns": ["song_id"],
            "reason": "특정 곡의 트렌드 기록 조회"
        },
        {
            "name": "idx_daily_trends_date",
            "table": "daily_trends",
            "columns": ["date"],
            "reason": "특정 날짜 데이터 조회"
        },
        {
            "name": "idx_daily_trends_source",
            "table": "daily_trends", 
            "columns": ["source"],
            "reason": "플랫폼별 데이터 조회"
        },
        {
            "name": "idx_daily_trends_source_category",
            "table": "daily_trends",
            "columns": ["source", "category"],
            "reason": "플랫폼+카테고리별 조회"
        },
        {
            "name": "idx_daily_trends_song_date",
            "table": "daily_trends",
            "columns": ["song_id", "date"],
            "reason": "곡별 시계열 분석"
        },
        {
            "name": "idx_daily_trends_daily_view_count",
            "table": "daily_trends",
            "columns": ["daily_view_count"],
            "reason": "조회수 기준 정렬 및 필터링"
        },
        
        # songs 테이블 인덱스들
        {
            "name": "idx_songs_youtube_id",
            "table": "songs",
            "columns": ["youtube_id"],
            "reason": "YouTube ID로 곡 검색"
        },
        {
            "name": "idx_songs_tiktok_id", 
            "table": "songs",
            "columns": ["tiktok_id"],
            "reason": "TikTok ID로 곡 검색"
        },
        {
            "name": "idx_songs_approval_status",
            "table": "songs",
            "columns": ["is_approved_for_business_use"],
            "reason": "비즈니스 승인 상태별 필터링"
        },
        {
            "name": "idx_songs_artist",
            "table": "songs", 
            "columns": ["artist"],
            "reason": "아티스트별 곡 검색"
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for idx_info in indexes_to_create:
            try:
                # 인덱스 존재 여부 확인
                cur.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name=?
                """, (idx_info["name"],))
                
                if cur.fetchone():
                    print(f"⚠️ 건너뜀: {idx_info['name']} (이미 존재)")
                    skipped_count += 1
                    continue
                
                # 인덱스 생성
                columns_str = ", ".join(idx_info["columns"])
                sql = f"""
                CREATE INDEX {idx_info["name"]} 
                ON {idx_info["table"]} ({columns_str})
                """
                
                start_time = time.time()
                cur.execute(sql)
                end_time = time.time()
                
                print(f"✅ 생성됨: {idx_info['name']} ({end_time-start_time:.2f}초)")
                print(f"   목적: {idx_info['reason']}")
                created_count += 1
                
            except sqlite3.Error as e:
                print(f"❌ 실패: {idx_info['name']} - {e}")
        
        conn.commit()
    
    print(f"\n📊 인덱스 생성 결과:")
    print(f"   생성됨: {created_count}개")
    print(f"   건너뜀: {skipped_count}개")
    
    return created_count

def performance_test_queries():
    """
    인덱스 생성 전후 성능을 테스트할 수 있는 쿼리들
    """
    test_queries = [
        {
            "name": "특정 곡의 트렌드 조회",
            "sql": "SELECT * FROM daily_trends WHERE song_id = 1"
        },
        {
            "name": "최근 일주일 데이터 조회", 
            "sql": "SELECT * FROM daily_trends WHERE date >= date('now', '-7 days')"
        },
        {
            "name": "YouTube 데이터만 조회",
            "sql": "SELECT * FROM daily_trends WHERE source = 'youtube'"
        },
        {
            "name": "조회수 상위 100곡",
            "sql": "SELECT * FROM daily_trends WHERE daily_view_count IS NOT NULL ORDER BY daily_view_count DESC LIMIT 100"
        },
        {
            "name": "특정 YouTube ID 검색",
            "sql": "SELECT * FROM songs WHERE youtube_id = 'dQw4w9WgXcQ'"  # 예시 ID
        },
        {
            "name": "비즈니스 승인된 곡들",
            "sql": "SELECT * FROM songs WHERE is_approved_for_business_use = 1"
        }
    ]
    
    print(f"\n🔍 성능 테스트 쿼리들:")
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for query in test_queries:
            try:
                start_time = time.time()
                cur.execute(query["sql"])
                results = cur.fetchall()
                end_time = time.time()
                
                print(f"   {query['name']}: {len(results)}건, {(end_time-start_time)*1000:.1f}ms")
                
            except sqlite3.Error as e:
                print(f"   {query['name']}: 오류 - {e}")

def show_query_plan_examples():
    """
    EXPLAIN QUERY PLAN을 사용한 쿼리 최적화 예시
    """
    print(f"\n💡 쿼리 플랜 확인 방법:")
    
    examples = [
        "EXPLAIN QUERY PLAN SELECT * FROM daily_trends WHERE song_id = 1;",
        "EXPLAIN QUERY PLAN SELECT * FROM daily_trends WHERE date = '2025-07-13';",
        "EXPLAIN QUERY PLAN SELECT * FROM daily_trends ORDER BY daily_view_count DESC LIMIT 10;"
    ]
    
    for example in examples:
        print(f"   {example}")
    
    print(f"\n📝 인덱스 사용 확인:")
    print(f"   - 'USING INDEX'가 있으면 인덱스 사용됨 ✅")
    print(f"   - 'SCAN'만 있으면 풀테이블 스캔 ❌")

def show_maintenance_tips():
    """
    인덱스 유지보수 팁 제공
    """
    print(f"\n🔧 인덱스 유지보수 팁:")
    
    tips = [
        "1. 정기적인 VACUUM 실행으로 인덱스 최적화",
        "2. ANALYZE 명령으로 쿼리 플래너 통계 업데이트", 
        "3. 사용되지 않는 인덱스는 정기적으로 제거",
        "4. 복합 인덱스는 WHERE 절의 컬럼 순서 고려",
        "5. INSERT/UPDATE가 많은 환경에서는 인덱스 오버헤드 주의"
    ]
    
    for tip in tips:
        print(f"   {tip}")
    
    maintenance_commands = [
        "-- 인덱스 최적화",
        "VACUUM;",
        "ANALYZE;",
        "",
        "-- 인덱스 사용량 확인",
        "SELECT * FROM sqlite_stat1;",
        "",
        "-- 사용되지 않는 인덱스 찾기",
        "-- (정기적으로 EXPLAIN QUERY PLAN 으로 확인 필요)"
    ]
    
    print(f"\n🛠 유지보수 명령어:")
    for cmd in maintenance_commands:
        print(f"   {cmd}")

def main():
    """
    메인 실행 함수
    """
    print("🚀 데이터베이스 인덱스 최적화를 시작합니다...")
    
    try:
        # 1. 현재 상태 분석
        print("\n1️⃣ 현재 상태 분석...")
        current_indexes = analyze_current_indexes()
        table_stats = get_table_stats()
        
        # 2. 성능 테스트 (인덱스 생성 전)
        print("\n2️⃣ 인덱스 생성 전 성능 테스트...")
        performance_test_queries()
        
        # 3. 인덱스 생성
        print("\n3️⃣ 필수 인덱스 생성...")
        created_count = create_essential_indexes()
        
        if created_count > 0:
            # 4. 성능 테스트 (인덱스 생성 후)
            print("\n4️⃣ 인덱스 생성 후 성능 테스트...")
            performance_test_queries()
        
        # 5. 추가 정보 제공
        print("\n5️⃣ 최적화 가이드...")
        show_query_plan_examples()
        show_maintenance_tips()
        
        print(f"\n🎉 인덱스 최적화가 완료되었습니다!")
        print(f"💡 {created_count}개의 인덱스가 추가되어 쿼리 성능이 크게 향상됩니다.")
        
        if table_stats.get('daily_trends', 0) < 1000:
            print(f"⚠️ 현재 데이터가 적어 성능 차이가 미미할 수 있습니다.")
            print(f"   데이터가 수만 건 이상 쌓이면 큰 성능 향상을 체감할 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 인덱스 최적화 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()