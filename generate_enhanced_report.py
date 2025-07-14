#!/usr/bin/env python3
"""
향상된 음악 트렌드 데이터 HTML 리포트 생성기 (UGC 카운트 및 해시태그 포함)
"""

import sqlite3
import json
import os
from datetime import datetime
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__)))

def get_all_data():
    """데이터베이스에서 모든 정보를 추출"""
    db_path = 'data/music_trends.db'
    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일이 없습니다.")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # TikTok Popular 데이터 (UGC 카운트와 해시태그 포함)
    cursor.execute("""
        SELECT s.id, s.title, s.artist, s.is_approved_for_business_use, dt.rank, 
               s.tiktok_id, s.tiktok_ugc_count
        FROM songs s 
        JOIN daily_trends dt ON s.id = dt.song_id 
        WHERE dt.source = 'tiktok' AND dt.category = 'popular'
        ORDER BY dt.rank
    """)
    tiktok_popular_raw = cursor.fetchall()
    
    # TikTok Breakout 데이터 (UGC 카운트와 해시태그 포함)
    cursor.execute("""
        SELECT s.id, s.title, s.artist, s.is_approved_for_business_use, dt.rank, 
               s.tiktok_id, s.tiktok_ugc_count
        FROM songs s 
        JOIN daily_trends dt ON s.id = dt.song_id 
        WHERE dt.source = 'tiktok' AND dt.category = 'breakout'
        ORDER BY dt.rank
    """)
    tiktok_breakout_raw = cursor.fetchall()
    
    # YouTube 데이터 (UGC 카운트 포함)
    cursor.execute("""
        SELECT s.id, s.title, s.artist, s.is_trending, s.is_new_hit, dt.rank, 
               s.youtube_id, s.youtube_ugc_count
        FROM songs s 
        JOIN daily_trends dt ON s.id = dt.song_id 
        WHERE dt.source = 'youtube'
        ORDER BY dt.rank
    """)
    youtube_data_raw = cursor.fetchall()
    
    # 각 곡의 해시태그 정보 추가
    def add_hashtags(songs_data, limit=3):
        enriched_data = []
        for song in songs_data:
            song_id = song[0]
            
            # 상위 3개 해시태그 조회
            cursor.execute("""
                SELECT hashtag, count 
                FROM song_hashtags 
                WHERE song_id = ? 
                ORDER BY rank 
                LIMIT ?
            """, (song_id, limit))
            hashtags = cursor.fetchall()
            
            # 원본 데이터에 해시태그 추가
            enriched_data.append(song + (hashtags,))
        
        return enriched_data
    
    # 해시태그 정보 추가
    tiktok_popular = add_hashtags(tiktok_popular_raw)
    tiktok_breakout = add_hashtags(tiktok_breakout_raw)
    youtube_data = [(song[0], song[1], song[2], song[3], song[4], song[5], song[6], song[7], []) for song in youtube_data_raw]  # YouTube는 해시태그 없음
    
    conn.close()
    
    return {
        'tiktok_popular': tiktok_popular,
        'tiktok_breakout': tiktok_breakout,
        'youtube': youtube_data,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_html_report(data):
    """HTML 리포트 생성"""
    
    html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>음악 트렌드 분석 리포트 (Enhanced)</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .platform-section {{
            margin-bottom: 50px;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }}
        
        .platform-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
            display: inline-block;
        }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-single {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #444;
            text-align: center;
            font-weight: 600;
        }}
        
        .song-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }}
        
        .song-table th {{
            background: #f1f3f4;
            padding: 12px 6px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #ddd;
            font-size: 0.9em;
        }}
        
        .song-table td {{
            padding: 10px 6px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        
        .song-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .rank {{
            font-weight: bold;
            color: #007bff;
            font-size: 1.1em;
            text-align: center;
            width: 40px;
        }}
        
        .song-info {{
            max-width: 180px;
        }}
        
        .song-title {{
            font-weight: 600;
            color: #333;
            margin-bottom: 3px;
            font-size: 0.9em;
        }}
        
        .artist {{
            color: #666;
            font-size: 0.8em;
        }}
        
        .ugc-count {{
            font-weight: bold;
            color: #28a745;
            text-align: center;
            font-size: 0.9em;
            width: 80px;
        }}
        
        .tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 500;
            margin: 1px;
        }}
        
        .tag-business {{
            background: #e7f5e7;
            color: #2d7d2d;
        }}
        
        .tag-trending {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .tag-new {{
            background: #d4edda;
            color: #155724;
        }}
        
        .hashtags {{
            font-size: 0.75em;
            color: #666;
            max-width: 140px;
        }}
        
        .hashtag {{
            display: inline-block;
            background: #e9ecef;
            padding: 2px 5px;
            border-radius: 6px;
            margin: 1px;
            font-size: 0.8em;
            color: #495057;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .chart-grid {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .song-table {{
                font-size: 0.75em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 음악 트렌드 분석 리포트 (Enhanced)</h1>
            <p>UGC 카운트 및 해시태그 정보 포함 | 생성일시: {data['generated_at']}</p>
        </div>
        
        <div class="content">
            <!-- TikTok 섹션 -->
            <div class="platform-section">
                <h2 class="platform-title">🎭 TikTok 음원 차트</h2>
                
                <div class="chart-grid">
                    <!-- TikTok Popular -->
                    <div class="chart-container">
                        <h3 class="chart-title">📈 Popular 차트</h3>
                        <table class="song-table">
                            <thead>
                                <tr>
                                    <th>순위</th>
                                    <th>곡 정보</th>
                                    <th>동영상 수</th>
                                    <th>태그</th>
                                    <th>해시태그 Top3</th>
                                </tr>
                            </thead>
                            <tbody>
"""
    
    # TikTok Popular 데이터 추가
    for song in data['tiktok_popular'][:10]:  # 상위 10곡만
        if len(song) >= 8:
            song_id, title, artist, is_approved, rank, tiktok_id, ugc_count, hashtags = song
            business_tag = '<span class="tag tag-business">비즈니스 승인</span>' if is_approved else ''
            ugc_display = f"{ugc_count:,}" if ugc_count else "-"
            
            # 해시태그 상위 3개 표시
            hashtag_display = ""
            if hashtags:
                hashtag_display = " ".join([f'<span class="hashtag">#{tag} ({count})</span>' for tag, count in hashtags[:3]])
            
            html_template += f"""
                                <tr>
                                    <td class="rank">{rank}</td>
                                    <td class="song-info">
                                        <div class="song-title">{title}</div>
                                        <div class="artist">{artist}</div>
                                    </td>
                                    <td class="ugc-count">{ugc_display}</td>
                                    <td>{business_tag}</td>
                                    <td class="hashtags">{hashtag_display}</td>
                                </tr>
"""
    
    html_template += """
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- TikTok Breakout -->
                    <div class="chart-container">
                        <h3 class="chart-title">🔥 Breakout 차트</h3>
                        <table class="song-table">
                            <thead>
                                <tr>
                                    <th>순위</th>
                                    <th>곡 정보</th>
                                    <th>동영상 수</th>
                                    <th>태그</th>
                                    <th>해시태그 Top3</th>
                                </tr>
                            </thead>
                            <tbody>
"""
    
    # TikTok Breakout 데이터 추가
    for song in data['tiktok_breakout'][:10]:  # 상위 10곡만
        if len(song) >= 8:
            song_id, title, artist, is_approved, rank, tiktok_id, ugc_count, hashtags = song
            business_tag = '<span class="tag tag-business">비즈니스 승인</span>' if is_approved else ''
            ugc_display = f"{ugc_count:,}" if ugc_count else "-"
            
            # 해시태그 상위 3개 표시
            hashtag_display = ""
            if hashtags:
                hashtag_display = " ".join([f'<span class="hashtag">#{tag} ({count})</span>' for tag, count in hashtags[:3]])
            
            html_template += f"""
                                <tr>
                                    <td class="rank">{rank}</td>
                                    <td class="song-info">
                                        <div class="song-title">{title}</div>
                                        <div class="artist">{artist}</div>
                                    </td>
                                    <td class="ugc-count">{ugc_display}</td>
                                    <td>{business_tag}</td>
                                    <td class="hashtags">{hashtag_display}</td>
                                </tr>
"""
    
    html_template += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- YouTube 섹션 -->
            <div class="platform-section">
                <h2 class="platform-title">📺 YouTube Shorts 차트</h2>
                
                <div class="chart-single">
                    <div class="chart-container">
                        <h3 class="chart-title">🎬 YouTube Shorts 인기 차트</h3>
                        <table class="song-table">
                            <thead>
                                <tr>
                                    <th>순위</th>
                                    <th>곡 정보</th>
                                    <th>동영상 수</th>
                                    <th>태그</th>
                                </tr>
                            </thead>
                            <tbody>
"""
    
    # YouTube 데이터 추가
    for song in data['youtube'][:20]:  # 상위 20곡
        if len(song) >= 8:
            song_id, title, artist, is_trending, is_new_hit, rank, youtube_id, ugc_count, _ = song
            
            tags = []
            if is_trending:
                tags.append('<span class="tag tag-trending">급상승</span>')
            if is_new_hit:
                tags.append('<span class="tag tag-new">신곡</span>')
            tags_html = ' '.join(tags)
            
            ugc_display = f"{ugc_count:,}" if ugc_count else "-"
            
            html_template += f"""
                                <tr>
                                    <td class="rank">{rank}</td>
                                    <td class="song-info">
                                        <div class="song-title">{title}</div>
                                        <div class="artist">{artist}</div>
                                    </td>
                                    <td class="ugc-count">{ugc_display}</td>
                                    <td>{tags_html}</td>
                                </tr>
"""
    
    html_template += f"""
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>📊 총 수집 데이터: TikTok Popular {len(data['tiktok_popular'])}곡, TikTok Breakout {len(data['tiktok_breakout'])}곡, YouTube {len(data['youtube'])}곡</p>
            <p>🎯 UGC 카운트 및 해시태그 정보 포함</p>
            <p>🤖 Enhanced Trend Analyzer v2.0 - Generated at {data['generated_at']}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_template

def main():
    print("📊 향상된 음악 트렌드 HTML 리포트 생성 중...")
    
    # 데이터 수집
    data = get_all_data()
    if not data:
        return
    
    # HTML 생성
    html_content = generate_html_report(data)
    
    # 파일 저장
    report_filename = f"enhanced_music_trend_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ 향상된 HTML 리포트 생성 완료: {report_filename}")
    print(f"🌐 브라우저에서 파일을 열어보세요: file://{os.path.abspath(report_filename)}")

if __name__ == "__main__":
    main()