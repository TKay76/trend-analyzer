#!/usr/bin/env python3
"""
HTML 형태의 데이터베이스 리포트 생성기
"""

import sqlite3
import os
from datetime import datetime

def generate_html_report():
    """HTML 리포트 생성"""
    
    # 데이터베이스 연결
    conn = sqlite3.connect('data/trend_analysis.db')
    cursor = conn.cursor()
    
    # 기본 통계 수집
    cursor.execute("SELECT COUNT(*) FROM songs")
    total_songs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM songs WHERE youtube_id IS NOT NULL")
    youtube_songs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM songs WHERE tiktok_id IS NOT NULL")
    tiktok_songs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM song_hashtags")
    hashtag_records = cursor.fetchone()[0]
    
    # 인기 해시태그
    cursor.execute("""
        SELECT hashtag, SUM(count) as total_count, COUNT(DISTINCT song_id) as song_count
        FROM song_hashtags 
        GROUP BY hashtag 
        ORDER BY total_count DESC 
        LIMIT 20
    """)
    top_hashtags = cursor.fetchall()
    
    # TikTok 인기곡
    cursor.execute("""
        SELECT title, artist, tiktok_ugc_count
        FROM songs 
        WHERE tiktok_ugc_count IS NOT NULL 
        ORDER BY tiktok_ugc_count DESC 
        LIMIT 10
    """)
    tiktok_top = cursor.fetchall()
    
    # HTML 생성
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Music Trend Analyzer - 데이터베이스 리포트</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                border-bottom: 3px solid #3498db;
                padding-bottom: 15px;
            }}
            h2 {{
                color: #34495e;
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin-top: 30px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .stat-card {{
                background-color: #ecf0f1;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .stat-number {{
                font-size: 24px;
                font-weight: bold;
                color: #2980b9;
            }}
            .stat-label {{
                color: #7f8c8d;
                margin-top: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #3498db;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .hashtag {{
                background-color: #e8f4fd;
                color: #2980b9;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: bold;
            }}
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Music Trend Analyzer</h1>
            <h2>📊 데이터베이스 리포트</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total_songs:,}</div>
                    <div class="stat-label">총 수집 곡 수</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{youtube_songs:,}</div>
                    <div class="stat-label">YouTube 곡</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{tiktok_songs:,}</div>
                    <div class="stat-label">TikTok 곡</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{hashtag_records:,}</div>
                    <div class="stat-label">해시태그 레코드</div>
                </div>
            </div>
            
            <h2>🏆 TikTok 인기곡 TOP 10</h2>
            <table>
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>곡명</th>
                        <th>아티스트</th>
                        <th>TikTok 동영상 수</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, (title, artist, count) in enumerate(tiktok_top, 1):
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{title}</td>
                        <td>{artist}</td>
                        <td>{count:,}</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
            
            <h2>🏷️ 인기 해시태그 TOP 20</h2>
            <table>
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>해시태그</th>
                        <th>총 사용 횟수</th>
                        <th>사용 곡 수</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, (hashtag, total_count, song_count) in enumerate(top_hashtags, 1):
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td><span class="hashtag">#{hashtag}</span></td>
                        <td>{total_count:,}</td>
                        <td>{song_count}</td>
                    </tr>
        """
    
    html_content += f"""
                </tbody>
            </table>
            
            <div class="timestamp">
                리포트 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    
    # HTML 파일 저장
    with open('database_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML 리포트가 생성되었습니다: database_report.html")
    print("브라우저에서 파일을 열어서 확인하세요!")
    
    conn.close()

if __name__ == "__main__":
    generate_html_report()