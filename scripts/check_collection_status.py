#!/usr/bin/env python3
"""
수집 상태 확인 및 리포트 생성 도구
데이터베이스의 현재 수집 상태를 확인하고 상세한 리포트를 제공합니다.
"""

import sys
import os
import json
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import database_manager as db
from src.utils.logger_config import get_logger

logger = get_logger(__name__)

class CollectionStatusChecker:
    def __init__(self):
        self.status_data = {
            'check_time': datetime.now().isoformat(),
            'total_songs': 0,
            'tiktok_stats': {},
            'youtube_stats': {},
            'hashtag_stats': {},
            'recent_collections': []
        }

    def get_overall_stats(self):
        """전체 통계 조회"""
        try:
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 전체 곡 수
                cursor.execute("SELECT COUNT(*) FROM songs")
                self.status_data['total_songs'] = cursor.fetchone()[0]
                
                return True
        except Exception as e:
            logger.error(f"❌ 전체 통계 조회 실패: {e}")
            return False

    def get_tiktok_stats(self):
        """TikTok 수집 통계"""
        try:
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # TikTok 곡 통계
                cursor.execute("SELECT COUNT(*) FROM songs WHERE tiktok_id IS NOT NULL")
                total_tiktok = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM songs WHERE tiktok_id IS NOT NULL AND tiktok_ugc_count IS NOT NULL")
                collected_tiktok = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM songs WHERE tiktok_id IS NOT NULL AND tiktok_ugc_count IS NULL")
                missing_tiktok = cursor.fetchone()[0]
                
                # TikTok UGC 통계
                cursor.execute("""
                    SELECT AVG(tiktok_ugc_count), MIN(tiktok_ugc_count), MAX(tiktok_ugc_count)
                    FROM songs 
                    WHERE tiktok_ugc_count IS NOT NULL AND tiktok_ugc_count > 0
                """)
                ugc_stats = cursor.fetchone()
                
                # 최근 수집된 TikTok 곡 (상위 5개)
                cursor.execute("""
                    SELECT title, artist, tiktok_ugc_count 
                    FROM songs 
                    WHERE tiktok_ugc_count IS NOT NULL 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
                recent_tiktok = cursor.fetchall()
                
                self.status_data['tiktok_stats'] = {
                    'total_songs': total_tiktok,
                    'collected': collected_tiktok,
                    'missing': missing_tiktok,
                    'collection_rate': (collected_tiktok / total_tiktok * 100) if total_tiktok > 0 else 0,
                    'ugc_avg': ugc_stats[0] if ugc_stats[0] else 0,
                    'ugc_min': ugc_stats[1] if ugc_stats[1] else 0,
                    'ugc_max': ugc_stats[2] if ugc_stats[2] else 0,
                    'recent_collections': recent_tiktok
                }
                
                return True
        except Exception as e:
            logger.error(f"❌ TikTok 통계 조회 실패: {e}")
            return False

    def get_youtube_stats(self):
        """YouTube 수집 통계"""
        try:
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # YouTube 곡 통계
                cursor.execute("SELECT COUNT(*) FROM songs WHERE youtube_id IS NOT NULL")
                total_youtube = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM songs WHERE youtube_id IS NOT NULL AND youtube_ugc_count IS NOT NULL")
                collected_youtube = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM songs WHERE youtube_id IS NOT NULL AND youtube_ugc_count IS NULL")
                missing_youtube = cursor.fetchone()[0]
                
                # YouTube UGC 통계
                cursor.execute("""
                    SELECT AVG(youtube_ugc_count), MIN(youtube_ugc_count), MAX(youtube_ugc_count)
                    FROM songs 
                    WHERE youtube_ugc_count IS NOT NULL AND youtube_ugc_count > 0
                """)
                ugc_stats = cursor.fetchone()
                
                # 최근 수집된 YouTube 곡 (상위 5개)
                cursor.execute("""
                    SELECT title, artist, youtube_ugc_count 
                    FROM songs 
                    WHERE youtube_ugc_count IS NOT NULL 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
                recent_youtube = cursor.fetchall()
                
                self.status_data['youtube_stats'] = {
                    'total_songs': total_youtube,
                    'collected': collected_youtube,
                    'missing': missing_youtube,
                    'collection_rate': (collected_youtube / total_youtube * 100) if total_youtube > 0 else 0,
                    'ugc_avg': ugc_stats[0] if ugc_stats[0] else 0,
                    'ugc_min': ugc_stats[1] if ugc_stats[1] else 0,
                    'ugc_max': ugc_stats[2] if ugc_stats[2] else 0,
                    'recent_collections': recent_youtube
                }
                
                return True
        except Exception as e:
            logger.error(f"❌ YouTube 통계 조회 실패: {e}")
            return False

    def get_hashtag_stats(self):
        """해시태그 수집 통계"""
        try:
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 해시태그 수집된 곡 수
                cursor.execute("SELECT COUNT(DISTINCT song_id) FROM song_hashtags")
                songs_with_hashtags = cursor.fetchone()[0]
                
                # 총 해시태그 수
                cursor.execute("SELECT COUNT(*) FROM song_hashtags")
                total_hashtags = cursor.fetchone()[0]
                
                # 가장 인기 있는 해시태그 (상위 10개)
                cursor.execute("""
                    SELECT hashtag, SUM(count) as total_count
                    FROM song_hashtags 
                    GROUP BY hashtag 
                    ORDER BY total_count DESC 
                    LIMIT 10
                """)
                popular_hashtags = cursor.fetchall()
                
                self.status_data['hashtag_stats'] = {
                    'songs_with_hashtags': songs_with_hashtags,
                    'total_hashtags': total_hashtags,
                    'avg_hashtags_per_song': total_hashtags / songs_with_hashtags if songs_with_hashtags > 0 else 0,
                    'popular_hashtags': popular_hashtags
                }
                
                return True
        except Exception as e:
            logger.error(f"❌ 해시태그 통계 조회 실패: {e}")
            return False

    def check_progress_files(self):
        """진행 상황 파일 확인"""
        progress_info = []
        
        # TikTok 진행 상황
        if os.path.exists("progress_tiktok.json"):
            try:
                with open("progress_tiktok.json", 'r', encoding='utf-8') as f:
                    tiktok_progress = json.load(f)
                progress_info.append({
                    'type': 'TikTok',
                    'completed': len(tiktok_progress.get('completed_songs', [])),
                    'failed': len(tiktok_progress.get('failed_songs', [])),
                    'last_update': tiktok_progress.get('last_update', 'Unknown')
                })
            except:
                pass
        
        # YouTube 진행 상황
        if os.path.exists("progress_youtube.json"):
            try:
                with open("progress_youtube.json", 'r', encoding='utf-8') as f:
                    youtube_progress = json.load(f)
                progress_info.append({
                    'type': 'YouTube',
                    'completed': len(youtube_progress.get('completed_songs', [])),
                    'failed': len(youtube_progress.get('failed_songs', [])),
                    'last_update': youtube_progress.get('last_update', 'Unknown')
                })
            except:
                pass
        
        return progress_info

    def print_status_report(self):
        """상태 리포트 출력"""
        print("\n" + "=" * 70)
        print("📊 Music Trend Analyzer - 수집 상태 리포트")
        print("=" * 70)
        print(f"📅 확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎵 총 곡 수: {self.status_data['total_songs']:,}개")
        print()
        
        # TikTok 통계
        tiktok = self.status_data['tiktok_stats']
        print("🎭 TikTok 수집 현황:")
        print(f"   📊 전체 곡: {tiktok['total_songs']}개")
        print(f"   ✅ 수집 완료: {tiktok['collected']}개 ({tiktok['collection_rate']:.1f}%)")
        print(f"   ❌ 미수집: {tiktok['missing']}개")
        if tiktok['ugc_avg'] > 0:
            print(f"   📈 UGC 평균: {tiktok['ugc_avg']:,.0f}개")
            print(f"   📊 UGC 범위: {tiktok['ugc_min']:,}개 ~ {tiktok['ugc_max']:,}개")
        print()
        
        # YouTube 통계
        youtube = self.status_data['youtube_stats']
        print("📺 YouTube 수집 현황:")
        print(f"   📊 전체 곡: {youtube['total_songs']}개")
        print(f"   ✅ 수집 완료: {youtube['collected']}개 ({youtube['collection_rate']:.1f}%)")
        print(f"   ❌ 미수집: {youtube['missing']}개")
        if youtube['ugc_avg'] > 0:
            print(f"   📈 UGC 평균: {youtube['ugc_avg']:,.0f}개")
            print(f"   📊 UGC 범위: {youtube['ugc_min']:,}개 ~ {youtube['ugc_max']:,}개")
        print()
        
        # 해시태그 통계
        hashtag = self.status_data['hashtag_stats']
        print("📌 해시태그 수집 현황:")
        print(f"   🎵 해시태그 보유 곡: {hashtag['songs_with_hashtags']}개")
        print(f"   📊 총 해시태그: {hashtag['total_hashtags']:,}개")
        print(f"   📈 곡당 평균: {hashtag['avg_hashtags_per_song']:.1f}개")
        print()
        
        # 인기 해시태그
        if hashtag['popular_hashtags']:
            print("🔥 인기 해시태그 TOP 5:")
            for i, (tag, count) in enumerate(hashtag['popular_hashtags'][:5], 1):
                print(f"   {i:2d}. #{tag}: {count:,}회")
            print()
        
        # 최근 수집 데이터
        if tiktok['recent_collections']:
            print("🆕 최근 TikTok 수집 데이터:")
            for title, artist, count in tiktok['recent_collections']:
                print(f"   📱 {title} - {artist}: {count:,}개")
            print()
        
        if youtube['recent_collections']:
            print("🆕 최근 YouTube 수집 데이터:")
            for title, artist, count in youtube['recent_collections']:
                print(f"   📺 {title} - {artist}: {count:,}개")
            print()
        
        # 진행 상황 파일 확인
        progress_info = self.check_progress_files()
        if progress_info:
            print("📝 진행 중인 작업:")
            for info in progress_info:
                print(f"   {info['type']}: 완료 {info['completed']}개, 실패 {info['failed']}개")
                print(f"       마지막 업데이트: {info['last_update']}")
            print()
        
        # 전체 요약
        total_collected = tiktok['collected'] + youtube['collected']
        total_possible = tiktok['total_songs'] + youtube['total_songs']
        overall_rate = (total_collected / total_possible * 100) if total_possible > 0 else 0
        
        print("🎯 전체 요약:")
        print(f"   📊 전체 수집률: {overall_rate:.1f}%")
        print(f"   💪 TikTok 상태: {'✅ 완료' if tiktok['missing'] == 0 else f'⏳ {tiktok['missing']}개 남음'}")
        print(f"   💪 YouTube 상태: {'✅ 완료' if youtube['missing'] == 0 else f'⏳ {youtube['missing']}개 남음'}")
        
        print("=" * 70)

    def save_status_json(self):
        """상태 데이터를 JSON 파일로 저장"""
        try:
            os.makedirs("logs", exist_ok=True)
            filename = f"logs/collection_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.status_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 상태 데이터 저장: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ 상태 데이터 저장 실패: {e}")
            return False

    def run_check(self):
        """전체 상태 확인 실행"""
        logger.info("📊 수집 상태 확인 시작")
        
        success = True
        success &= self.get_overall_stats()
        success &= self.get_tiktok_stats()
        success &= self.get_youtube_stats()
        success &= self.get_hashtag_stats()
        
        if success:
            self.print_status_report()
            self.save_status_json()
        else:
            logger.error("❌ 일부 통계 조회에 실패했습니다.")
            return False
        
        return True

def main():
    """메인 실행 함수"""
    checker = CollectionStatusChecker()
    
    try:
        success = checker.run_check()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()