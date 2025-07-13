#!/usr/bin/env python3
"""
트렌드 분석 데이터베이스 리포트 생성기
데이터베이스의 모든 정보를 보기 좋게 가공하여 출력합니다.
"""

import sqlite3
import sys
import os
from datetime import datetime
from collections import Counter

def get_db_connection():
    """데이터베이스 연결"""
    db_path = 'data/trend_analysis.db'
    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일을 찾을 수 없습니다: data/trend_analysis.db")
        return None
    return sqlite3.connect(db_path)

def print_section_header(title):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_subsection(title):
    """서브섹션 헤더 출력"""
    print(f"\n📊 {title}")
    print("-" * 60)

def show_database_overview():
    """데이터베이스 전체 개요"""
    print_section_header("📈 MUSIC TREND ANALYZER - 데이터베이스 리포트")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 기본 통계
    cursor.execute("SELECT COUNT(*) FROM songs")
    total_songs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM songs WHERE youtube_id IS NOT NULL")
    youtube_songs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM songs WHERE tiktok_id IS NOT NULL")
    tiktok_songs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM daily_trends")
    trend_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM song_hashtags")
    hashtag_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT song_id) FROM song_hashtags")
    songs_with_hashtags = cursor.fetchone()[0]
    
    # 최신 업데이트 시간
    cursor.execute("SELECT MAX(date) FROM daily_trends")
    latest_trend_date = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(collected_date) FROM song_hashtags")
    latest_hashtag_date = cursor.fetchone()[0]
    
    print(f"📅 리포트 생성시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎵 총 수집 곡 수: {total_songs:,}개")
    print(f"📺 YouTube 곡: {youtube_songs:,}개")
    print(f"🎬 TikTok 곡: {tiktok_songs:,}개")
    print(f"📈 트렌드 레코드: {trend_records:,}개")
    print(f"🏷️ 해시태그 레코드: {hashtag_records:,}개")
    print(f"🎯 해시태그 보유 곡: {songs_with_hashtags:,}개")
    print(f"📆 최신 트렌드 데이터: {latest_trend_date}")
    print(f"🔖 최신 해시태그 데이터: {latest_hashtag_date}")
    
    conn.close()

def show_platform_statistics():
    """플랫폼별 통계"""
    print_section_header("🎯 플랫폼별 상세 통계")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # YouTube 통계
    print_subsection("YouTube 통계")
    cursor.execute("""
        SELECT 
            COUNT(*) as song_count,
            AVG(youtube_ugc_count) as avg_ugc,
            MAX(youtube_ugc_count) as max_ugc,
            MIN(youtube_ugc_count) as min_ugc
        FROM songs 
        WHERE youtube_id IS NOT NULL AND youtube_ugc_count IS NOT NULL
    """)
    
    yt_stats = cursor.fetchone()
    if yt_stats[0] > 0:
        print(f"  • UGC 데이터가 있는 곡: {yt_stats[0]}개")
        print(f"  • 평균 UGC 수: {yt_stats[1]:.0f}개" if yt_stats[1] else "  • 평균 UGC 수: N/A")
        print(f"  • 최대 UGC 수: {yt_stats[2]:,}개" if yt_stats[2] else "  • 최대 UGC 수: N/A")
        print(f"  • 최소 UGC 수: {yt_stats[3]:,}개" if yt_stats[3] else "  • 최소 UGC 수: N/A")
    
    # TikTok 통계
    print_subsection("TikTok 통계")
    cursor.execute("""
        SELECT 
            COUNT(*) as song_count,
            AVG(tiktok_ugc_count) as avg_ugc,
            MAX(tiktok_ugc_count) as max_ugc,
            MIN(tiktok_ugc_count) as min_ugc
        FROM songs 
        WHERE tiktok_id IS NOT NULL AND tiktok_ugc_count IS NOT NULL
    """)
    
    tt_stats = cursor.fetchone()
    if tt_stats[0] > 0:
        print(f"  • UGC 데이터가 있는 곡: {tt_stats[0]}개")
        print(f"  • 평균 UGC 수: {tt_stats[1]:.0f}개" if tt_stats[1] else "  • 평균 UGC 수: N/A")
        print(f"  • 최대 UGC 수: {tt_stats[2]:,}개" if tt_stats[2] else "  • 최대 UGC 수: N/A")
        print(f"  • 최소 UGC 수: {tt_stats[3]:,}개" if tt_stats[3] else "  • 최소 UGC 수: N/A")
    
    conn.close()

def show_top_songs():
    """인기 곡 순위"""
    print_section_header("🏆 인기 곡 TOP 10")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # TikTok UGC 기준 TOP 10
    print_subsection("TikTok UGC 수 TOP 10")
    cursor.execute("""
        SELECT title, artist, tiktok_ugc_count, youtube_ugc_count
        FROM songs 
        WHERE tiktok_ugc_count IS NOT NULL 
        ORDER BY tiktok_ugc_count DESC 
        LIMIT 10
    """)
    
    tiktok_top = cursor.fetchall()
    for i, (title, artist, tt_count, yt_count) in enumerate(tiktok_top, 1):
        yt_text = f", YouTube: {yt_count:,}" if yt_count else ""
        print(f"  {i:2d}. {title} - {artist}")
        print(f"      TikTok: {tt_count:,}{yt_text}")
    
    # YouTube UGC 기준 TOP 10  
    print_subsection("YouTube UGC 수 TOP 10")
    cursor.execute("""
        SELECT title, artist, youtube_ugc_count, tiktok_ugc_count
        FROM songs 
        WHERE youtube_ugc_count IS NOT NULL 
        ORDER BY youtube_ugc_count DESC 
        LIMIT 10
    """)
    
    youtube_top = cursor.fetchall()
    for i, (title, artist, yt_count, tt_count) in enumerate(youtube_top, 1):
        tt_text = f", TikTok: {tt_count:,}" if tt_count else ""
        print(f"  {i:2d}. {title} - {artist}")
        print(f"      YouTube: {yt_count:,}{tt_text}")
    
    conn.close()

def show_hashtag_analysis():
    """해시태그 분석"""
    print_section_header("🏷️ 해시태그 트렌드 분석")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 전체 인기 해시태그 TOP 20
    print_subsection("전체 인기 해시태그 TOP 20")
    cursor.execute("""
        SELECT hashtag, SUM(count) as total_count, COUNT(DISTINCT song_id) as song_count
        FROM song_hashtags 
        GROUP BY hashtag 
        ORDER BY total_count DESC 
        LIMIT 20
    """)
    
    top_hashtags = cursor.fetchall()
    for i, (hashtag, total_count, song_count) in enumerate(top_hashtags, 1):
        print(f"  {i:2d}. #{hashtag}: {total_count:,}회 ({song_count}곡에서 사용)")
    
    # 카테고리별 해시태그 분석
    print_subsection("카테고리별 해시태그")
    
    # 한국어 해시태그
    cursor.execute("""
        SELECT hashtag, SUM(count) as total_count
        FROM song_hashtags 
        WHERE hashtag REGEXP '[가-힣]'
        GROUP BY hashtag 
        ORDER BY total_count DESC 
        LIMIT 10
    """)
    
    korean_tags = cursor.fetchall()
    if korean_tags:
        print("한국어 해시태그 TOP 10:")
        for i, (hashtag, count) in enumerate(korean_tags, 1):
            print(f"    {i:2d}. #{hashtag}: {count:,}회")
    
    # K-POP 관련 해시태그
    cursor.execute("""
        SELECT hashtag, SUM(count) as total_count
        FROM song_hashtags 
        WHERE hashtag LIKE '%kpop%' OR hashtag LIKE '%k%pop%' 
           OR hashtag LIKE '%korean%' OR hashtag LIKE '%korea%'
        GROUP BY hashtag 
        ORDER BY total_count DESC 
        LIMIT 5
    """)
    
    kpop_tags = cursor.fetchall()
    if kpop_tags:
        print("\nK-POP 관련 해시태그:")
        for i, (hashtag, count) in enumerate(kpop_tags, 1):
            print(f"    {i}. #{hashtag}: {count:,}회")
    
    conn.close()

def show_trend_analysis():
    """트렌드 분석"""
    print_section_header("📈 차트 트렌드 분석")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 플랫폼별 차트 데이터
    print_subsection("플랫폼/카테고리별 차트 현황")
    cursor.execute("""
        SELECT source, category, COUNT(*) as song_count
        FROM daily_trends 
        GROUP BY source, category 
        ORDER BY source, song_count DESC
    """)
    
    chart_stats = cursor.fetchall()
    current_source = ""
    for source, category, count in chart_stats:
        if source != current_source:
            print(f"\n{source.upper()}:")
            current_source = source
        print(f"  • {category}: {count}곡")
    
    # 최신 차트 순위 (상위 5곡)
    print_subsection("최신 차트 순위 (각 카테고리 TOP 5)")
    cursor.execute("""
        SELECT DISTINCT source, category FROM daily_trends 
        ORDER BY source, category
    """)
    
    categories = cursor.fetchall()
    for source, category in categories:
        print(f"\n{source.upper()} - {category}:")
        cursor.execute("""
            SELECT s.title, s.artist, dt.rank, dt.date
            FROM daily_trends dt
            JOIN songs s ON dt.song_id = s.id
            WHERE dt.source = ? AND dt.category = ?
            ORDER BY dt.date DESC, dt.rank ASC
            LIMIT 5
        """, (source, category))
        
        rankings = cursor.fetchall()
        for title, artist, rank, date in rankings:
            print(f"  {rank:2d}위. {title} - {artist} ({date})")
    
    conn.close()

def show_cross_platform_analysis():
    """크로스 플랫폼 분석"""
    print_section_header("🔀 크로스 플랫폼 분석")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 양 플랫폼에 모두 있는 곡들
    print_subsection("양 플랫폼 모두 존재하는 곡")
    cursor.execute("""
        SELECT title, artist, youtube_ugc_count, tiktok_ugc_count,
               (CASE WHEN youtube_ugc_count > tiktok_ugc_count THEN 'YouTube'
                     WHEN tiktok_ugc_count > youtube_ugc_count THEN 'TikTok'  
                     ELSE 'Equal' END) as dominant_platform
        FROM songs 
        WHERE youtube_id IS NOT NULL AND tiktok_id IS NOT NULL
          AND youtube_ugc_count IS NOT NULL AND tiktok_ugc_count IS NOT NULL
        ORDER BY (youtube_ugc_count + tiktok_ugc_count) DESC
        LIMIT 10
    """)
    
    cross_platform = cursor.fetchall()
    if cross_platform:
        for i, (title, artist, yt_count, tt_count, dominant) in enumerate(cross_platform, 1):
            total = yt_count + tt_count
            print(f"  {i:2d}. {title} - {artist}")
            print(f"      YouTube: {yt_count:,}, TikTok: {tt_count:,}")
            print(f"      총합: {total:,}, 우세 플랫폼: {dominant}")
            print()
    else:
        print("  크로스 플랫폼 데이터가 없습니다.")
    
    conn.close()

def generate_summary_report():
    """요약 리포트"""
    print_section_header("📋 요약 리포트")
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # 핵심 인사이트
    print("🎯 핵심 인사이트:")
    
    # 가장 인기 있는 해시태그
    cursor.execute("""
        SELECT hashtag, SUM(count) as total_count 
        FROM song_hashtags 
        GROUP BY hashtag 
        ORDER BY total_count DESC 
        LIMIT 1
    """)
    top_hashtag = cursor.fetchone()
    if top_hashtag:
        print(f"  • 가장 인기 있는 해시태그: #{top_hashtag[0]} ({top_hashtag[1]:,}회)")
    
    # TikTok 최고 인기곡
    cursor.execute("""
        SELECT title, artist, tiktok_ugc_count 
        FROM songs 
        WHERE tiktok_ugc_count IS NOT NULL 
        ORDER BY tiktok_ugc_count DESC 
        LIMIT 1
    """)
    top_tiktok = cursor.fetchone()
    if top_tiktok:
        print(f"  • TikTok 최고 인기곡: {top_tiktok[0]} - {top_tiktok[1]} ({top_tiktok[2]:,}개 동영상)")
    
    # YouTube 최고 인기곡
    cursor.execute("""
        SELECT title, artist, youtube_ugc_count 
        FROM songs 
        WHERE youtube_ugc_count IS NOT NULL 
        ORDER BY youtube_ugc_count DESC 
        LIMIT 1
    """)
    top_youtube = cursor.fetchone()
    if top_youtube:
        print(f"  • YouTube 최고 인기곡: {top_youtube[0]} - {top_youtube[1]} ({top_youtube[2]:,}개 Shorts)")
    
    # 데이터 품질
    cursor.execute("SELECT COUNT(*) FROM songs")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM songs WHERE youtube_ugc_count IS NOT NULL OR tiktok_ugc_count IS NOT NULL")
    with_ugc = cursor.fetchone()[0]
    
    ugc_coverage = (with_ugc / total * 100) if total > 0 else 0
    print(f"  • UGC 데이터 커버리지: {ugc_coverage:.1f}% ({with_ugc}/{total})")
    
    conn.close()

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        section = sys.argv[1].lower()
        if section == "overview":
            show_database_overview()
        elif section == "platforms":
            show_platform_statistics()
        elif section == "songs":
            show_top_songs()
        elif section == "hashtags":
            show_hashtag_analysis()
        elif section == "trends":
            show_trend_analysis()
        elif section == "cross":
            show_cross_platform_analysis()
        elif section == "summary":
            generate_summary_report()
        else:
            print("사용법: python database_report.py [overview|platforms|songs|hashtags|trends|cross|summary]")
            print("또는 인자 없이 실행하면 전체 리포트를 생성합니다.")
    else:
        # 전체 리포트
        show_database_overview()
        show_platform_statistics()
        show_top_songs()
        show_hashtag_analysis()
        show_trend_analysis()
        show_cross_platform_analysis()
        generate_summary_report()

if __name__ == "__main__":
    main()