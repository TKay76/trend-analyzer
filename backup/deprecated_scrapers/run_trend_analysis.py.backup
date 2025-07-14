#!/usr/bin/env python3
"""
통합 트렌드 분석 스크립트
TikTok → YouTube 스크래핑 후 UGC 데이터 업데이트를 순차적으로 실행합니다.
"""

import sys
import subprocess
import time
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(__file__))
from src.utils.logger_config import get_logger, log_scraper_start, log_scraper_end, log_error_with_context

# 로거 설정
logger = get_logger(__name__)

def run_script(script_name, description):
    """
    스크립트를 실행하고 결과를 반환합니다.
    """
    logger.info("=" * 60)
    logger.info(f"🔄 {description} 시작...")
    logger.info(f"📄 실행 파일: {script_name}")
    logger.info(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=1800  # 30분 타임아웃
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"📊 {description} 결과:")
        logger.info(f"⏱️ 실행 시간: {duration:.1f}초")
        logger.info(f"🔄 반환 코드: {result.returncode}")
        
        if result.stdout:
            logger.debug(f"📝 출력:\n{result.stdout}")
            
        if result.stderr:
            logger.warning(f"⚠️ 오류:\n{result.stderr}")
            
        if result.returncode == 0:
            logger.info(f"✅ {description} 성공!")
            return True
        else:
            logger.error(f"❌ {description} 실패!")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {description} 타임아웃 (30분 초과)")
        return False
    except Exception as e:
        log_error_with_context(logger, e, f"{description} 실행")
        return False

def main():
    """
    메인 실행 함수
    """
    log_scraper_start(logger, "통합 트렌드 분석 시스템")
    
    scripts = [
        ("src/scrapers/tiktok_music_scraper.py", "TikTok 음악 트렌드 스크래핑"),
        ("src/scrapers/youtube_music_scraper.py", "YouTube 음악 차트 스크래핑"),
        ("src/scrapers/ugc_data_updater.py", "UGC 데이터 업데이트")
    ]
    
    results = []
    total_start_time = time.time()
    
    # 각 스크립트 순차 실행
    for script_name, description in scripts:
        success = run_script(script_name, description)
        results.append((script_name, description, success))
        
        if not success:
            logger.warning(f"⚠️ {description}에서 오류가 발생했습니다.")
            # 자동화 환경에서는 사용자 입력 대신 계속 진행
            logger.info("🔄 다음 스크립트로 계속 진행합니다...")
        
        # 스크립트 간 대기 시간 (브라우저 리소스 정리)
        if script_name != scripts[-1][0]:  # 마지막 스크립트가 아니면
            logger.info("⏳ 다음 스크립트 실행을 위해 5초 대기...")
            time.sleep(5)
    
    # 최종 결과 요약
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    logger.info("=" * 60)
    logger.info("📊 최종 실행 결과")
    logger.info("=" * 60)
    logger.info(f"⏱️ 총 실행 시간: {total_duration:.1f}초 ({total_duration/60:.1f}분)")
    
    successful_count = 0
    for script_name, description, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        logger.info(f"{status} {description}")
        if success:
            successful_count += 1
    
    success_rate = successful_count/len(results)*100 if results else 0
    logger.info(f"📈 성공률: {successful_count}/{len(results)} ({success_rate:.1f}%)")
    
    if successful_count == len(results):
        logger.info("🎉 모든 스크립트가 성공적으로 완료되었습니다!")
        logger.info("💾 데이터베이스에 최신 트렌드 데이터와 UGC 카운트가 저장되었습니다.")
        logger.info("👀 결과 확인: python src/database/view_database.py")
    else:
        failed_count = len(results) - successful_count
        logger.warning(f"⚠️ {failed_count}개의 스크립트에서 오류가 발생했습니다.")
        logger.info("🔍 로그 파일을 확인하여 문제를 해결해주세요.")
    
    log_scraper_end(logger, "통합 트렌드 분석 시스템", successful_count > 0, total_duration, successful_count)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("⛔ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        log_error_with_context(logger, e, "메인 실행")
        sys.exit(1)