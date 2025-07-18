#!/usr/bin/env python3
"""
YouTube 안전한 배치 수집 스크립트 (Windows 지원)
타임아웃 문제 해결을 위해 작은 배치 단위로 안전하게 수집하고,
실패한 곡들을 자동으로 재시도하는 시스템
"""

import sys
import os
import time
import subprocess
import json
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database import database_manager as db
from src.utils.logger_config import get_logger

logger = get_logger(__name__)

class YouTubeBatchCollector:
    def __init__(self):
        self.batch_size = 12  # 한 번에 처리할 곡 수 (YouTube가 약간 더 빠름)
        self.max_retries = 3  # 실패 시 최대 재시도 횟수
        self.timeout_per_song = 180  # 곡당 타임아웃 (3분)
        self.progress_file = "progress_youtube.json"
        
        # Python 실행 파일 경로 (Windows/Linux 자동 감지)
        project_root = os.path.join(os.path.dirname(__file__), '..')
        if os.name == 'nt':  # Windows
            self.python_exe = os.path.join(project_root, 'venv', 'Scripts', 'python.exe')
        else:  # Linux/WSL
            self.python_exe = os.path.join(project_root, 'venv', 'bin', 'python')
        
        # Python 실행 파일 존재 확인
        if not os.path.exists(self.python_exe):
            self.python_exe = 'python'  # 시스템 기본 Python 사용
        
        self.results = {
            'total_songs': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'batches_completed': 0,
            'failed_songs': [],
            'start_time': time.time()
        }

    def load_progress(self):
        """이전 진행 상황 로드"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                logger.info(f"📂 이전 진행 상황 로드: {len(progress.get('completed_songs', []))}개 완료")
                return progress
            except Exception as e:
                logger.warning(f"⚠️ 진행 상황 로드 실패: {e}")
        return {'completed_songs': [], 'failed_songs': []}

    def save_progress(self, completed_songs, failed_songs):
        """진행 상황 저장"""
        progress = {
            'completed_songs': completed_songs,
            'failed_songs': failed_songs,
            'last_update': datetime.now().isoformat()
        }
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ 진행 상황 저장 실패: {e}")

    def get_songs_to_collect(self):
        """수집할 YouTube 곡 목록 조회"""
        try:
            with db.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, artist, youtube_id 
                    FROM songs 
                    WHERE youtube_id IS NOT NULL
                    ORDER BY id
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ 곡 목록 조회 실패: {e}")
            return []

    def collect_single_song(self, song_id, title, artist, youtube_id, retry_count=0):
        """개별 곡 수집 (재시도 포함)"""
        shorts_url = f"https://www.youtube.com/source/{youtube_id}/shorts"
        song_info = f"{title} - {artist}"
        
        try:
            logger.info(f"🎵 수집 시작: {song_info}")
            if retry_count > 0:
                logger.info(f"   📝 재시도 {retry_count}/{self.max_retries}")
            
            # YouTube UGC 카운터 실행
            project_root = os.path.join(os.path.dirname(__file__), '..')
            script_path = os.path.join(project_root, 'src', 'scrapers', 'youtube_ugc_counter.py')
            
            # 환경변수 설정
            env = os.environ.copy()
            env['PYTHONPATH'] = project_root
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            result = subprocess.run([
                self.python_exe, script_path, shorts_url, '--save-db'
            ], capture_output=True, text=True, timeout=self.timeout_per_song, 
               cwd=project_root, env=env)
            
            if result.returncode == 0:
                # 성공한 경우 UGC 카운트 추출 시도
                try:
                    ugc_count = int(result.stdout.strip().split('\n')[0])
                    logger.info(f"   ✅ 수집 완료: {song_info} → {ugc_count:,}개")
                except:
                    logger.info(f"   ✅ 수집 완료: {song_info}")
                return True, None
            else:
                error_msg = result.stderr.strip() if result.stderr else "알 수 없는 오류"
                logger.error(f"   ❌ 수집 실패: {song_info} - {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            logger.error(f"   ⏰ 타임아웃: {song_info} ({self.timeout_per_song}초)")
            return False, "타임아웃"
        except Exception as e:
            logger.error(f"   💥 예외 발생: {song_info} - {e}")
            return False, str(e)

    def collect_with_retry(self, song_data):
        """재시도 로직이 포함된 곡 수집"""
        song_id, title, artist, youtube_id = song_data
        
        for retry in range(self.max_retries):
            success, error = self.collect_single_song(song_id, title, artist, youtube_id, retry)
            
            if success:
                return True, None
            
            # 재시도 전 대기 (2초 * 재시도 횟수)
            if retry < self.max_retries - 1:
                wait_time = (retry + 1) * 2
                logger.info(f"   ⏳ {wait_time}초 대기 후 재시도...")
                time.sleep(wait_time)
        
        # 모든 재시도 실패
        return False, error

    def process_batch(self, batch_songs, batch_num, total_batches):
        """배치 단위 처리"""
        logger.info(f"📦 배치 {batch_num}/{total_batches} 처리 중 ({len(batch_songs)}개 곡)")
        logger.info("=" * 50)
        
        batch_success = 0
        batch_failed = 0
        
        for i, song_data in enumerate(batch_songs, 1):
            song_id, title, artist, youtube_id = song_data
            
            logger.info(f"[{i}/{len(batch_songs)}] 처리 중...")
            
            success, error = self.collect_with_retry(song_data)
            
            if success:
                batch_success += 1
                self.results['success_count'] += 1
            else:
                batch_failed += 1
                self.results['failed_count'] += 1
                self.results['failed_songs'].append({
                    'id': song_id,
                    'title': title,
                    'artist': artist,
                    'youtube_id': youtube_id,
                    'error': error
                })
            
            # 배치 내 곡 간 간격 (서버 부하 방지)
            if i < len(batch_songs):
                time.sleep(2)
        
        logger.info(f"📊 배치 {batch_num} 완료: 성공 {batch_success}개, 실패 {batch_failed}개")
        logger.info("=" * 50)
        
        return batch_success, batch_failed

    def run_collection(self):
        """전체 수집 실행"""
        start_time = time.time()
        
        logger.info("🚀 YouTube 안전한 배치 수집 시작")
        logger.info("=" * 60)
        
        # 진행 상황 로드
        progress = self.load_progress()
        completed_songs = set(progress.get('completed_songs', []))
        
        # 수집할 곡 목록 조회
        all_songs = self.get_songs_to_collect()
        
        if not all_songs:
            logger.info("✅ 수집할 YouTube 곡이 없습니다.")
            return
        
        # 이미 완료된 곡 제외
        songs_to_collect = [song for song in all_songs if song[0] not in completed_songs]
        
        if not songs_to_collect:
            logger.info("✅ 모든 YouTube 곡이 이미 수집되었습니다!")
            return
        
        self.results['total_songs'] = len(songs_to_collect)
        logger.info(f"📊 수집 대상: {len(songs_to_collect)}개 곡")
        logger.info(f"⚙️ 배치 크기: {self.batch_size}개씩")
        logger.info(f"⏱️ 곡당 타임아웃: {self.timeout_per_song}초")
        logger.info("=" * 60)
        
        # 배치 단위로 처리
        total_batches = (len(songs_to_collect) + self.batch_size - 1) // self.batch_size
        
        for batch_num in range(1, total_batches + 1):
            start_idx = (batch_num - 1) * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(songs_to_collect))
            batch_songs = songs_to_collect[start_idx:end_idx]
            
            batch_success, batch_failed = self.process_batch(batch_songs, batch_num, total_batches)
            
            # 진행 상황 저장
            completed_song_ids = [song[0] for song in batch_songs if batch_success > 0]
            completed_songs.update(completed_song_ids)
            self.save_progress(list(completed_songs), self.results['failed_songs'])
            
            self.results['batches_completed'] += 1
            
            # 배치 간 휴식 (마지막 배치가 아닌 경우)
            if batch_num < total_batches:
                logger.info("⏳ 5초 휴식 후 다음 배치 진행...")
                time.sleep(5)
        
        # 최종 결과 출력
        self.print_final_summary(start_time)

    def print_final_summary(self, start_time):
        """최종 결과 요약"""
        duration = time.time() - start_time
        duration_min = duration / 60
        
        logger.info("=" * 60)
        logger.info("🎉 YouTube 배치 수집 완료!")
        logger.info("=" * 60)
        logger.info(f"📊 총 처리 곡수: {self.results['total_songs']}개")
        logger.info(f"✅ 성공: {self.results['success_count']}개")
        logger.info(f"❌ 실패: {self.results['failed_count']}개")
        logger.info(f"📦 완료 배치: {self.results['batches_completed']}개")
        logger.info(f"⏱️ 총 소요 시간: {duration_min:.1f}분")
        
        if self.results['total_songs'] > 0:
            success_rate = (self.results['success_count'] / self.results['total_songs']) * 100
            logger.info(f"🎯 성공률: {success_rate:.1f}%")
        
        # 실패한 곡들 정보
        if self.results['failed_songs']:
            logger.warning(f"⚠️ 실패한 곡들 ({len(self.results['failed_songs'])}개):")
            for failed in self.results['failed_songs'][:5]:  # 최대 5개만 표시
                logger.warning(f"   - {failed['title']} - {failed['artist']}: {failed['error']}")
            if len(self.results['failed_songs']) > 5:
                logger.warning(f"   ... 외 {len(self.results['failed_songs']) - 5}개")
        
        logger.info("=" * 60)
        
        # 진행 상황 파일 정리 (성공적으로 완료된 경우)
        if self.results['failed_count'] == 0:
            try:
                os.remove(self.progress_file)
                logger.info("🧹 진행 상황 파일 정리 완료")
            except:
                pass

def main():
    """메인 실행 함수"""
    collector = YouTubeBatchCollector()
    
    try:
        collector.run_collection()
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()