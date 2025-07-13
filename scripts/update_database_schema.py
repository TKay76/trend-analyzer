#!/usr/bin/env python3
"""
데이터베이스 스키마 업데이트 스크립트
기존 daily_trends 테이블에 UNIQUE 제약조건을 추가합니다.
"""

import sqlite3
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def backup_database():
    """기존 데이터베이스를 백업합니다."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'trend_analysis.db')
    
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(os.path.dirname(__file__), '..', 'data', f'trend_analysis_backup_schema_update_{timestamp}.db')
        
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    else:
        print("⚠️ No existing database found, no backup needed")
        return None

def update_schema():
    """스키마를 업데이트합니다."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'trend_analysis.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Checking current schema...")
        
        # 현재 daily_trends 테이블 구조 확인
        cursor.execute('PRAGMA table_info(daily_trends)')
        columns = cursor.fetchall()
        print(f"Current daily_trends columns: {[col[1] for col in columns]}")
        
        # 제약조건 확인
        cursor.execute('PRAGMA index_list(daily_trends)')
        indexes = cursor.fetchall()
        print(f"Current indexes: {indexes}")
        
        # UNIQUE 제약조건이 이미 있는지 확인
        has_unique_constraint = False
        for index in indexes:
            cursor.execute(f'PRAGMA index_info({index[1]})')
            index_info = cursor.fetchall()
            if len(index_info) == 4:  # song_id, source, category, date
                has_unique_constraint = True
                break
        
        if has_unique_constraint:
            print("✅ UNIQUE constraint already exists. No update needed.")
            return True
        
        print("🔄 Creating new table with UNIQUE constraint...")
        
        # 새 테이블 생성 (UNIQUE 제약조건 포함)
        cursor.execute("""
        CREATE TABLE daily_trends_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            rank INTEGER NOT NULL,
            metrics TEXT,
            date DATE DEFAULT (date('now')),
            FOREIGN KEY (song_id) REFERENCES songs (id),
            UNIQUE(song_id, source, category, date)
        )
        """)
        
        # 기존 데이터 복사 (중복 제거)
        cursor.execute("""
        INSERT OR IGNORE INTO daily_trends_new (id, song_id, source, category, rank, metrics, date)
        SELECT id, song_id, source, category, rank, metrics, date FROM daily_trends
        """)
        
        # 기존 테이블 삭제하고 새 테이블 이름 변경
        cursor.execute("DROP TABLE daily_trends")
        cursor.execute("ALTER TABLE daily_trends_new RENAME TO daily_trends")
        
        conn.commit()
        print("✅ Schema update completed successfully!")
        
        # 업데이트 후 데이터 확인
        cursor.execute('SELECT COUNT(*) FROM daily_trends')
        count = cursor.fetchone()[0]
        print(f"📊 Total trends after update: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema update failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """메인 실행 함수"""
    print("🔧 데이터베이스 스키마 업데이트 시작...")
    
    # 1. 백업
    backup_path = backup_database()
    
    # 2. 스키마 업데이트
    try:
        if update_schema():
            print("\n🎉 Schema update completed successfully!")
            print("✅ UNIQUE constraint added to daily_trends table")
            print("✅ Duplicate entries removed")
            print("✅ Same-day re-runs will now update existing data instead of creating duplicates")
        else:
            print("\n❌ Schema update failed!")
            if backup_path:
                print(f"🔄 You can restore from backup: {backup_path}")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        if backup_path:
            print(f"🔄 You can restore from backup: {backup_path}")

if __name__ == "__main__":
    main()