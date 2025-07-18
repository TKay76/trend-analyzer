import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

import sqlite3
import pandas as pd
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

# --- 설정 ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'music_trends.db')
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
TODAY_DT = datetime.now()
YESTERDAY_DT = TODAY_DT - timedelta(days=1)
TODAY_STR = TODAY_DT.strftime('%Y-%m-%d')
YESTERDAY_STR = YESTERDAY_DT.strftime('%Y-%m-%d')

def get_db_connection():
    """데이터베이스 커넥션을 반환합니다."""
    print(f"Attempting to connect to database at: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        print("Database connection successful.")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection failed: {e}")
        raise # Re-raise the exception after printing

def get_trends_data(conn, date_str):
    """특정 날짜의 트렌드 데이터를 songs 테이블과 조인하여 가져옵니다."""
    query = """
    SELECT
        dt.song_id,
        dt.source,
        dt.category,
        dt.rank,
        s.title,
        s.artist,
        s.thumbnail_url,
        s.is_approved_for_business_use,
        s.youtube_ugc_count,
        s.tiktok_ugc_count
    FROM daily_trends dt
    JOIN songs s ON dt.song_id = s.id
    WHERE dt.date = ?
    """
    df = pd.read_sql_query(query, conn, params=(date_str,))
    return df

def get_hashtags_data(conn, date_str):
    """특정 날짜의 모든 해시태그 데이터를 가져옵니다."""
    query = """
    SELECT
        song_id,
        hashtag,
        count
    FROM song_hashtags
    WHERE collected_date = ?
    ORDER BY song_id, rank
    """
    df = pd.read_sql_query(query, conn, params=(date_str,))
    # song_id로 그룹화하여 리스트로 만듭니다.
    return df.groupby('song_id').apply(lambda x: x[['hashtag', 'count']].to_dict('records')).to_dict()

def format_rank_change(change):
    """순위 변동을 포맷팅합니다."""
    if pd.isna(change):
        return '<span class="rank-new">NEW</span>'
    change = int(change)
    if change > 0:
        return f'<span class="rank-down">▼ {change}</span>'
    elif change < 0:
        return f'<span class="rank-up">▲ {-change}</span>'
    else:
        return '<span>-</span>'

def format_count(count):
    """숫자를 K, M 등으로 포맷팅합니다."""
    if pd.isna(count) or count == 0:
        return "0"
    count = int(count)
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    else:
        return str(count)

def format_count_change(change):
    """UGC 수 변동을 포맷팅합니다."""
    if pd.isna(change) or change == 0:
        return ""
    change = int(change)
    sign = "+" if change > 0 else ""
    formatted_change = format_count(abs(change))
    color_class = "rank-up" if change > 0 else "rank-down"
    return f'<span class="count-change {color_class}">({sign}{formatted_change})</span>'


def generate_report():
    """일일 트렌드 리포트 HTML을 생성합니다."""
    print(f"리포트 생성 시작: {TODAY_STR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = get_db_connection()

    # --- 디버깅: 테이블 목록 확인 ---
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"데이터베이스에 존재하는 테이블: {[table[0] for table in tables]}")
    # ---------------------------------

    # 1. 데이터 조회
    print("데이터베이스에서 오늘과 어제 데이터를 조회합니다.")
    df_today = get_trends_data(conn, TODAY_STR)
    df_yesterday = get_trends_data(conn, YESTERDAY_STR)
    hashtags_today = get_hashtags_data(conn, TODAY_STR)

    if df_today.empty:
        print("경고: 오늘자 트렌드 데이터가 없습니다. 리포트 생성을 중단합니다.")
        conn.close()
        return

    # 2. 데이터 처리 및 비교
    print("데이터를 비교하고 순위 변동을 계산합니다.")
    # 어제 데이터에서 순위와 UGC 수를 가져오기 위해 'rank_yesterday', 'ugc_yesterday' 컬럼 추가
    df_yesterday_slim = df_yesterday[['song_id', 'source', 'category', 'rank', 'tiktok_ugc_count', 'youtube_ugc_count']].rename(columns={
        'rank': 'rank_yesterday',
        'tiktok_ugc_count': 'tiktok_ugc_yesterday',
        'youtube_ugc_count': 'youtube_ugc_yesterday'
    })

    # 오늘 데이터와 어제 데이터를 병합
    df_merged = pd.merge(df_today, df_yesterday_slim, on=['song_id', 'source', 'category'], how='left')

    # 순위 및 UGC 수 변동 계산
    df_merged['rank_change'] = df_merged['rank'] - df_merged['rank_yesterday']
    df_merged['tiktok_ugc_change'] = df_merged['tiktok_ugc_count'] - df_merged['tiktok_ugc_yesterday']
    df_merged['youtube_ugc_change'] = df_merged['youtube_ugc_count'] - df_merged['youtube_ugc_yesterday']

    # 3. 최종 데이터 가공
    print("최종 리포트 데이터를 가공합니다.")
    report_data = {}
    categories = {
        'tiktok': ['popular', 'breakout'],
        "youtube": ['trending']
    }

    for source, cats in categories.items():
        for category in cats:
            key = f"{source}_{category}"
            
            # 해당 소스/카테고리 데이터 필터링 및 정렬
            df_cat = df_merged[(df_merged['source'] == source) & (df_merged['category'] == category)].sort_values('rank').copy()
            
            # UGC 수 및 변동 컬럼 선택
            ugc_col = f'{source}_ugc_count'
            ugc_change_col = f'{source}_ugc_change'
            
            # 포맷팅 적용
            df_cat['rank_change_html'] = df_cat['rank_change'].apply(format_rank_change)
            df_cat['ugc_count_formatted'] = df_cat[ugc_col].apply(format_count)
            df_cat['ugc_change_html'] = df_cat[ugc_change_col].apply(format_count_change)
            
            # 해시태그 데이터 추가
            if source == 'tiktok':
                df_cat['hashtags'] = df_cat['song_id'].map(hashtags_today).fillna('').apply(list)

            report_data[key] = df_cat.to_dict('records')

    conn.close()

    # 4. HTML 렌더링
    print("HTML 템플릿을 렌더링합니다.")
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template('report_template.html')

    template_data = {
        "report_date": TODAY_DT.strftime('%Y년 %m월 %d일'),
        "tiktok_popular": report_data.get('tiktok_popular', []),
        "tiktok_breakout": report_data.get('tiktok_breakout', []),
        "youtube_shorts": report_data.get('youtube_trending', [])
    }

    output_html = template.render(template_data)
    output_filename = os.path.join(OUTPUT_DIR, f"report_{TODAY_STR}.html")
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(output_html)

    print(f"리포트 생성 완료: {output_filename}")


if __name__ == "__main__":
    generate_report()