#!/usr/bin/env python3
"""
프로젝트 전체에서 사용할 로깅 설정 모듈
일관된 로그 포맷과 레벨을 제공합니다.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

def setup_logging(name: str = None, level: str = "INFO", console_output: bool = True, file_output: bool = True):
    """
    로깅 설정을 초기화합니다.
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: 콘솔 출력 여부
        file_output: 파일 출력 여부
    
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    
    # 로그 디렉토리 생성
    if file_output:
        LOGS_DIR.mkdir(exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name or __name__)
    
    # 이미 핸들러가 있으면 중복 방지
    if logger.handlers:
        return logger
    
    # 로깅 레벨 설정
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # 로그 포맷 설정
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s | %(message)s'
    )
    
    # 콘솔 핸들러 (간단한 포맷)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # 파일 핸들러 (상세한 포맷)
    if file_output:
        # 일반 로그 파일
        log_file = LOGS_DIR / f"trend_analyzer_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 파일에는 모든 레벨 저장
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # 에러 전용 로그 파일
        error_log_file = LOGS_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    # 상위 로거로 전파 방지 (중복 로그 방지)
    logger.propagate = False
    
    return logger

def get_logger(name: str = None):
    """
    간편한 로거 생성 함수
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
    
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    return setup_logging(name)

def log_scraper_start(logger: logging.Logger, scraper_name: str, target_url: str = None):
    """스크래퍼 시작 로그를 기록합니다."""
    logger.info("=" * 60)
    logger.info(f"🔄 {scraper_name} 시작")
    if target_url:
        logger.info(f"📄 대상 URL: {target_url}")
    logger.info(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

def log_scraper_end(logger: logging.Logger, scraper_name: str, success: bool, duration: float = None, count: int = None):
    """스크래퍼 종료 로그를 기록합니다."""
    status = "성공" if success else "실패" 
    emoji = "✅" if success else "❌"
    
    logger.info("-" * 60)
    logger.info(f"{emoji} {scraper_name} {status}")
    if duration:
        logger.info(f"⏱️ 실행 시간: {duration:.1f}초")
    if count is not None:
        logger.info(f"📊 처리된 항목: {count}개")
    logger.info(f"⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 60)

def log_database_operation(logger: logging.Logger, operation: str, table: str, count: int = None, success: bool = True):
    """데이터베이스 작업 로그를 기록합니다."""
    emoji = "💾" if success else "❌"
    status = "성공" if success else "실패"
    
    if count is not None:
        logger.info(f"{emoji} {operation} {table} 테이블 {status}: {count}개")
    else:
        logger.info(f"{emoji} {operation} {table} 테이블 {status}")

def log_performance_metric(logger: logging.Logger, metric_name: str, value: float, unit: str = ""):
    """성능 메트릭 로그를 기록합니다."""
    logger.debug(f"📈 {metric_name}: {value:.2f}{unit}")

def log_error_with_context(logger: logging.Logger, error: Exception, context: str = ""):
    """상세한 에러 로그를 기록합니다."""
    if context:
        logger.error(f"💥 {context}에서 오류 발생: {type(error).__name__}: {str(error)}")
    else:
        logger.error(f"💥 오류 발생: {type(error).__name__}: {str(error)}")
    
    # 디버그 레벨에서 상세한 스택 트레이스 기록
    logger.debug("스택 트레이스:", exc_info=True)

# 환경변수를 통한 로깅 레벨 설정 지원
def get_log_level_from_env():
    """환경변수에서 로깅 레벨을 가져옵니다."""
    return os.getenv('LOG_LEVEL', 'INFO').upper()

# 전역 로거 설정 (모듈 import 시 자동 실행)
_default_logger = None

def get_default_logger():
    """기본 로거를 반환합니다."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging("trend_analyzer", level=get_log_level_from_env())
    return _default_logger

if __name__ == "__main__":
    # 테스트 코드
    test_logger = get_logger(__name__)
    
    test_logger.debug("디버그 메시지입니다")
    test_logger.info("정보 메시지입니다") 
    test_logger.warning("경고 메시지입니다")
    test_logger.error("오류 메시지입니다")
    test_logger.critical("치명적 오류 메시지입니다")
    
    # 헬퍼 함수 테스트
    log_scraper_start(test_logger, "테스트 스크래퍼", "https://example.com")
    log_scraper_end(test_logger, "테스트 스크래퍼", True, 10.5, 100)
    log_database_operation(test_logger, "INSERT", "songs", 50)
    
    print(f"로그 파일이 {LOGS_DIR}에 생성되었습니다.")