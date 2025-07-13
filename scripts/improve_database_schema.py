#!/usr/bin/env python3
"""
데이터베이스 스키마 개선 및 기존 데이터 마이그레이션 스크립트
metrics JSON 컬럼을 구조화된 숫자 컬럼들로 분리합니다.
"""

import sqlite3
import json
import re
import os
import sys

# 프로젝트 루트 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.database_manager import DB_FILE, get_db_connection

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
        print(f"Warning: Could not parse metric value: {metric_str}")
        return None

def add_new_columns():
    """
    daily_trends 테이블에 새로운 숫자 컬럼들을 추가
    """
    alter_commands = [
        "ALTER TABLE daily_trends ADD COLUMN daily_view_count INTEGER",
        "ALTER TABLE daily_trends ADD COLUMN weekly_view_count INTEGER", 
        "ALTER TABLE daily_trends ADD COLUMN engagement_rate REAL",
        "ALTER TABLE daily_trends ADD COLUMN raw_metrics_backup TEXT"  # 기존 데이터 백업용
    ]
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        for command in alter_commands:
            try:
                cur.execute(command)
                print(f"✅ 실행 완료: {command}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️ 컬럼이 이미 존재함: {command}")
                else:
                    print(f"❌ 오류: {command} - {e}")
                    raise
        
        conn.commit()

def migrate_existing_data():
    """
    기존 metrics JSON 데이터를 새로운 컬럼들로 마이그레이션
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 기존 데이터 백업
        cur.execute("UPDATE daily_trends SET raw_metrics_backup = metrics WHERE raw_metrics_backup IS NULL")
        
        # 기존 데이터 조회
        cur.execute("SELECT id, metrics FROM daily_trends WHERE metrics IS NOT NULL")
        rows = cur.fetchall()
        
        print(f"📊 {len(rows)}개의 레코드를 마이그레이션합니다...")
        
        migrated_count = 0
        for row in rows:
            row_id = row['id']
            metrics_json = row['metrics']
            
            try:
                if metrics_json:
                    metrics_data = json.loads(metrics_json)
                    
                    # daily_metrics 파싱
                    daily_metrics = metrics_data.get('daily_metrics')
                    daily_view_count = parse_metric_value(daily_metrics) if daily_metrics else None
                    
                    # 다른 메트릭들도 필요시 추가 가능
                    # weekly_metrics = metrics_data.get('weekly_metrics')
                    # engagement = metrics_data.get('engagement_rate')
                    
                    # 새로운 컬럼에 값 업데이트
                    update_sql = """
                    UPDATE daily_trends 
                    SET daily_view_count = ?
                    WHERE id = ?
                    """
                    cur.execute(update_sql, (daily_view_count, row_id))
                    migrated_count += 1
                    
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ 레코드 ID {row_id} 파싱 실패: {e}")
                continue
        
        conn.commit()
        print(f"✅ {migrated_count}개 레코드 마이그레이션 완료")

def verify_migration():
    """
    마이그레이션 결과 검증
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # 통계 정보 출력
        cur.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(daily_view_count) as migrated_records,
            MIN(daily_view_count) as min_views,
            MAX(daily_view_count) as max_views,
            AVG(daily_view_count) as avg_views
        FROM daily_trends
        """)
        
        stats = cur.fetchone()
        print(f"\n📈 마이그레이션 통계:")
        print(f"   전체 레코드: {stats['total_records']}")
        print(f"   마이그레이션된 레코드: {stats['migrated_records']}")
        print(f"   최소 조회수: {stats['min_views']:,}" if stats['min_views'] else "   최소 조회수: None")
        print(f"   최대 조회수: {stats['max_views']:,}" if stats['max_views'] else "   최대 조회수: None")
        print(f"   평균 조회수: {stats['avg_views']:,.0f}" if stats['avg_views'] else "   평균 조회수: None")

def show_example_queries():
    """
    개선된 스키마로 가능한 쿼리 예시를 보여줌
    """
    print(f"\n🔍 이제 가능한 고급 쿼리들:")
    
    example_queries = [
        "-- 일일 조회수 100만 이상인 곡들",
        "SELECT s.title, s.artist, dt.daily_view_count FROM songs s JOIN daily_trends dt ON s.id = dt.song_id WHERE dt.daily_view_count >= 1000000;",
        "",
        "-- 조회수 기준으로 정렬",
        "SELECT s.title, s.artist, dt.daily_view_count FROM songs s JOIN daily_trends dt ON s.id = dt.song_id ORDER BY dt.daily_view_count DESC LIMIT 10;",
        "",
        "-- 플랫폼별 평균 조회수",
        "SELECT source, AVG(daily_view_count) as avg_views FROM daily_trends WHERE daily_view_count IS NOT NULL GROUP BY source;",
        "",
        "-- 조회수 범위별 곡 개수",
        "SELECT CASE WHEN daily_view_count >= 10000000 THEN '10M+' WHEN daily_view_count >= 1000000 THEN '1M-10M' WHEN daily_view_count >= 100000 THEN '100K-1M' ELSE 'Under 100K' END as view_range, COUNT(*) FROM daily_trends WHERE daily_view_count IS NOT NULL GROUP BY view_range;"
    ]
    
    for query in example_queries:
        print(query)

def main():
    """
    메인 실행 함수
    """
    print("🔧 데이터베이스 스키마 개선을 시작합니다...")
    
    try:
        # 1. 새로운 컬럼 추가
        print("\n1️⃣ 새로운 컬럼 추가 중...")
        add_new_columns()
        
        # 2. 기존 데이터 마이그레이션
        print("\n2️⃣ 기존 데이터 마이그레이션 중...")
        migrate_existing_data()
        
        # 3. 결과 검증
        print("\n3️⃣ 마이그레이션 결과 검증 중...")
        verify_migration()
        
        # 4. 예시 쿼리 출력
        show_example_queries()
        
        print("\n🎉 스키마 개선이 완료되었습니다!")
        print("💡 이제 metrics 컬럼 대신 daily_view_count 등의 숫자 컬럼을 사용하여 효율적인 쿼리가 가능합니다.")
        
    except Exception as e:
        print(f"❌ 스키마 개선 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()