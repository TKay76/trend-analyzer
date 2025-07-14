#!/usr/bin/env python3
"""
일일 완전한 음악 트렌드 데이터 수집 마스터 스크립트
매일 실행하여 모든 트렌드 데이터, UGC 카운트, 해시태그를 업데이트합니다.
"""

import sys
import os
import time
import subprocess
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import database_manager as db
from src.utils.logger_config import get_logger

logger = get_logger(__name__)

class DailyCollectionManager:
    def __init__(self):
        self.start_time = time.time()
        self.results = {
            'trend_collection': False,
            'tiktok_ugc_collection': {'success': 0, 'failed': 0},
            'youtube_ugc_collection': {'success': 0, 'failed': 0},
            'total_songs_processed': 0
        }
    
    def run_script(self, script_path, description, timeout=300):
        """스크립트 실행 및 결과 반환"""
        logger.info(f"🚀 {description} 시작...")
        
        try:
            venv_python = os.path.join(os.path.dirname(__file__), 'test_env', 'bin', 'python')
            result = subprocess.run([
                venv_python, script_path
            ], capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                logger.info(f"✅ {description} 완료")
                return True
            else:
                logger.error(f"❌ {description} 실패")
                logger.error(f"   오류: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {description} 타임아웃 ({timeout}초)")
            return False
        except Exception as e:
            logger.error(f"💥 {description} 예외 발생: {e}")
            return False
    
    def collect_trend_data(self):
        """1단계: 트렌드 데이터 수집"""
        logger.info("=" * 60)
        logger.info("📊 1단계: 트렌드 데이터 수집")
        logger.info("=" * 60)
        
        # TikTok 트렌드 수집
        tiktok_success = self.run_script(
            'src/scrapers/tiktok_music_scraper.py', 
            'TikTok 트렌드 수집',
            timeout=600  # 10분
        )
        
        # YouTube 트렌드 수집
        youtube_success = self.run_script(
            'src/scrapers/youtube_csv_scraper.py',
            'YouTube 트렌드 수집', 
            timeout=600  # 10분
        )
        
        self.results['trend_collection'] = tiktok_success and youtube_success
        
        if self.results['trend_collection']:
            logger.info("✅ 트렌드 데이터 수집 완료")
        else:
            logger.warning("⚠️ 일부 트렌드 데이터 수집 실패")
    
    def collect_all_ugc_data(self):
        """2단계: 모든 곡의 UGC 데이터 수집"""
        logger.info("=" * 60)
        logger.info("🎬 2단계: UGC 데이터 수집")
        logger.info("=" * 60)
        
        # TikTok UGC + 해시태그 수집
        logger.info("🎭 TikTok UGC + 해시태그 수집 중...")
        tiktok_success = self.collect_tiktok_ugc_data()
        
        # YouTube UGC 수집
        logger.info("📺 YouTube UGC 수집 중...")
        youtube_success = self.collect_youtube_ugc_data()
        
        total_processed = (self.results['tiktok_ugc_collection']['success'] + 
                          self.results['tiktok_ugc_collection']['failed'] +
                          self.results['youtube_ugc_collection']['success'] + 
                          self.results['youtube_ugc_collection']['failed'])
        
        self.results['total_songs_processed'] = total_processed
        
        if tiktok_success and youtube_success:
            logger.info("✅ 모든 UGC 데이터 수집 완료")
        else:
            logger.warning("⚠️ 일부 UGC 데이터 수집 실패")
    
    def collect_tiktok_ugc_data(self):
        """TikTok 곡들의 UGC + 해시태그 수집"""
        try:
            # 모든 TikTok 곡 조회 (이미 수집된 것도 재수집하여 업데이트)
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, artist, tiktok_id 
                    FROM songs 
                    WHERE tiktok_id IS NOT NULL
                    ORDER BY id
                """)
                tiktok_songs = cursor.fetchall()
            
            logger.info(f"📊 TikTok 수집 대상: {len(tiktok_songs)}개 곡")
            
            success_count = 0
            failed_count = 0
            
            for i, (song_id, title, artist, tiktok_id) in enumerate(tiktok_songs, 1):
                tiktok_url = f"https://www.tiktok.com/music/x-{tiktok_id}"
                
                logger.info(f"[{i}/{len(tiktok_songs)}] {title} - {artist}")
                
                try:
                    venv_python = os.path.join(os.path.dirname(__file__), 'test_env', 'bin', 'python')
                    result = subprocess.run([
                        venv_python, 'src/scrapers/tiktok_ugc_counter.py', tiktok_url, '--save-db'
                    ], capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        success_count += 1
                        logger.info(f"   ✅ 완료")
                    else:
                        failed_count += 1
                        logger.error(f"   ❌ 실패")
                        
                except:
                    failed_count += 1
                    logger.error(f"   💥 오류")
                
                # 요청 간격 조절
                if i < len(tiktok_songs):
                    time.sleep(2)
            
            self.results['tiktok_ugc_collection'] = {
                'success': success_count,
                'failed': failed_count
            }
            
            logger.info(f"🎭 TikTok 수집 완료: 성공 {success_count}개, 실패 {failed_count}개")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"❌ TikTok UGC 수집 중 오류: {e}")
            return False
    
    def collect_youtube_ugc_data(self):
        """YouTube 곡들의 UGC 수집"""
        try:
            # 모든 YouTube 곡 조회 (이미 수집된 것도 재수집하여 업데이트)
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, artist, youtube_id 
                    FROM songs 
                    WHERE youtube_id IS NOT NULL
                    ORDER BY id
                """)
                youtube_songs = cursor.fetchall()
            
            logger.info(f"📊 YouTube 수집 대상: {len(youtube_songs)}개 곡")
            
            success_count = 0
            failed_count = 0
            
            for i, (song_id, title, artist, youtube_id) in enumerate(youtube_songs, 1):
                shorts_url = f"https://www.youtube.com/source/{youtube_id}/shorts"
                
                logger.info(f"[{i}/{len(youtube_songs)}] {title} - {artist}")
                
                try:
                    venv_python = os.path.join(os.path.dirname(__file__), 'test_env', 'bin', 'python')
                    result = subprocess.run([
                        venv_python, 'src/scrapers/youtube_ugc_counter.py', shorts_url, '--save-db'
                    ], capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        success_count += 1
                        logger.info(f"   ✅ 완료")
                    else:
                        failed_count += 1
                        logger.error(f"   ❌ 실패")
                        
                except:
                    failed_count += 1
                    logger.error(f"   💥 오류")
                
                # 요청 간격 조절
                if i < len(youtube_songs):
                    time.sleep(2)
            
            self.results['youtube_ugc_collection'] = {
                'success': success_count,
                'failed': failed_count
            }
            
            logger.info(f"📺 YouTube 수집 완료: 성공 {success_count}개, 실패 {failed_count}개")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"❌ YouTube UGC 수집 중 오류: {e}")
            return False
    
    def generate_daily_report(self):
        """3단계: 수집 완료 보고서 생성"""
        logger.info("=" * 60)
        logger.info("📋 3단계: 수집 완료 보고서 생성")
        logger.info("=" * 60)
        
        try:
            # 향상된 리포트 생성 (백업에서 복원 필요 시)
            if os.path.exists('backup/generate_enhanced_report.py.backup'):
                report_success = self.run_script(
                    'backup/generate_enhanced_report.py.backup',
                    '일일 HTML 리포트 생성',
                    timeout=60
                )
                if report_success:
                    logger.info("✅ 일일 리포트 생성 완료")
                else:
                    logger.warning("⚠️ 리포트 생성 실패")
            else:
                logger.info("ℹ️ 리포트 생성기 없음 (추후 구현 예정)")
                
        except Exception as e:
            logger.error(f"❌ 리포트 생성 중 오류: {e}")
    
    def print_final_summary(self):
        """최종 결과 요약 출력"""
        duration = time.time() - self.start_time
        duration_min = duration / 60
        
        logger.info("=" * 60)
        logger.info("🎉 일일 완전 수집 완료!")
        logger.info("=" * 60)
        logger.info(f"📊 트렌드 데이터: {'✅ 성공' if self.results['trend_collection'] else '❌ 실패'}")
        logger.info(f"🎭 TikTok UGC: 성공 {self.results['tiktok_ugc_collection']['success']}개, "
                   f"실패 {self.results['tiktok_ugc_collection']['failed']}개")
        logger.info(f"📺 YouTube UGC: 성공 {self.results['youtube_ugc_collection']['success']}개, "
                   f"실패 {self.results['youtube_ugc_collection']['failed']}개")
        logger.info(f"⏱️ 총 소요 시간: {duration_min:.1f}분")
        logger.info(f"📈 처리된 곡 수: {self.results['total_songs_processed']}개")
        
        # 성공률 계산
        total_success = (self.results['tiktok_ugc_collection']['success'] + 
                        self.results['youtube_ugc_collection']['success'])
        total_failed = (self.results['tiktok_ugc_collection']['failed'] + 
                       self.results['youtube_ugc_collection']['failed'])
        
        if total_success + total_failed > 0:
            success_rate = (total_success / (total_success + total_failed)) * 100
            logger.info(f"🎯 전체 성공률: {success_rate:.1f}%")
        
        logger.info("=" * 60)

def main():
    """메인 실행 함수"""
    collector = DailyCollectionManager()
    
    logger.info("🌅 일일 완전 음악 트렌드 수집 시작")
    logger.info(f"📅 수집 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1단계: 트렌드 데이터 수집
        collector.collect_trend_data()
        
        # 2단계: UGC 데이터 수집
        collector.collect_all_ugc_data()
        
        # 3단계: 리포트 생성
        collector.generate_daily_report()
        
        # 최종 결과 요약
        collector.print_final_summary()
        
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()