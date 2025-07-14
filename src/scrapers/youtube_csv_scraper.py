#!/usr/bin/env python3
"""
YouTube Charts CSV Scraper
YouTube Charts 페이지에서 CSV 파일을 다운로드하여 정확한 차트 데이터를 수집합니다.
"""

import os
import sys
import csv
import time
import tempfile
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database import database_manager as db
from src.utils.logger_config import get_logger, log_scraper_start, log_scraper_end, log_error_with_context

# 로거 설정
logger = get_logger(__name__)

def extract_youtube_id_from_url(youtube_url):
    """
    YouTube URL에서 비디오 ID를 추출합니다.
    예: https://www.youtube.com/watch?v=983bBbJx0Mk -> 983bBbJx0Mk
    """
    if not youtube_url:
        return None
    
    if 'watch?v=' in youtube_url:
        return youtube_url.split('watch?v=')[1].split('&')[0]
    return None

def generate_shorts_url(youtube_id):
    """
    YouTube ID로부터 Shorts 검색 URL을 생성합니다.
    예: 983bBbJx0Mk -> https://www.youtube.com/source/983bBbJx0Mk/shorts
    """
    if not youtube_id:
        return None
    return f"https://www.youtube.com/source/{youtube_id}/shorts"

def analyze_chart_position(current_rank, previous_rank, periods_on_chart):
    """
    차트 순위 변화를 분석하여 태그를 생성합니다.
    
    Returns:
        tuple: (is_trending, is_new_hit)
    """
    is_trending = False
    is_new_hit = False
    
    # 신곡 판단: 이전 순위가 "n/a"
    if previous_rank == "n/a":
        is_new_hit = True
    
    # 인기급상승 판단: 이전 순위보다 5위 이상 상승
    try:
        if previous_rank != "n/a" and previous_rank.isdigit():
            prev_rank_num = int(previous_rank)
            curr_rank_num = int(current_rank)
            if prev_rank_num - curr_rank_num >= 5:  # 순위가 상승 (숫자가 작아짐)
                is_trending = True
    except (ValueError, TypeError):
        pass
    
    return is_trending, is_new_hit

def download_youtube_csv():
    """
    YouTube Charts 페이지에서 CSV 파일을 다운로드합니다.
    
    Returns:
        str: 다운로드된 CSV 파일 경로, 실패시 None
    """
    target_url = "https://charts.youtube.com/charts/TopShortsSongs/kr/daily"
    
    # CSV 저장 폴더 설정
    csv_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'csv_downloads')
    os.makedirs(csv_dir, exist_ok=True)
    
    logger.info(f"📊 YouTube Charts CSV 다운로드 시작: {target_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 디버깅을 위해 브라우저 표시
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        try:
            # 페이지 로딩
            logger.info("🌐 페이지 로딩 중...")
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            # 다운로드 버튼 찾기 및 클릭
            logger.info("🔽 CSV 다운로드 버튼 클릭 중...")
            
            # 페이지의 모든 버튼 요소들을 확인
            logger.info("🔍 페이지에서 다운로드 관련 요소 찾는 중...")
            
            # 모든 버튼과 링크 요소 확인
            all_buttons = page.locator("button, a, .button, [role='button']").all()
            logger.info(f"총 {len(all_buttons)}개의 클릭 가능한 요소 발견")
            
            # 실제 발견된 다운로드 버튼 선택자들
            download_selectors = [
                "#download-button",  # 실제 발견된 ID
                "paper-icon-button#download-button",  # 정확한 태그와 ID
                "paper-icon-button[title='download']",  # title 속성으로 찾기
                "paper-icon-button[icon='ytmc-icons-ext:download-white-fill']",  # 아이콘으로 찾기
                ".ytmc-top-banner paper-icon-button",  # 클래스 컨테이너 내에서 찾기
                "paper-icon-button[role='button'][title='download']",  # 복합 속성
                "[title='download']",  # title만으로
                "button[title='download']",  # 일반 버튼 형태
                "#download",  # 혹시 모를 다른 ID
                "button[aria-label*='Download']",
                "button[aria-label*='다운로드']"
            ]
            
            download_clicked = False
            
            # 다운로드 버튼 직접 클릭 시도 (상단 메뉴에 위치)
            for selector in download_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"🔽 다운로드 버튼 시도: {selector}")
                        
                        # 버튼이 보이는지 확인
                        if page.locator(selector).is_visible():
                            # 다운로드 시작 대기
                            with page.expect_download() as download_info:
                                page.locator(selector).click(timeout=10000)
                            
                            download = download_info.value
                            
                            # 파일 저장
                            csv_filename = f"youtube_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            csv_path = os.path.join(csv_dir, csv_filename)
                            download.save_as(csv_path)
                            
                            logger.info(f"✅ CSV 다운로드 완료: {csv_path}")
                            download_clicked = True
                            break
                        else:
                            logger.debug(f"선택자 {selector}는 존재하지만 보이지 않음")
                        
                except Exception as e:
                    logger.debug(f"선택자 {selector} 시도 실패: {e}")
                    continue
            
            if not download_clicked:
                logger.error("❌ 다운로드 버튼을 찾을 수 없습니다")
                return None
                
            return csv_path
            
        except Exception as e:
            log_error_with_context(logger, e, "CSV 다운로드")
            return None
        finally:
            browser.close()

def parse_csv_data(csv_path):
    """
    다운로드된 CSV 파일을 파싱합니다.
    
    Returns:
        list: 파싱된 곡 데이터 리스트
    """
    if not csv_path or not os.path.exists(csv_path):
        logger.error("❌ CSV 파일이 존재하지 않습니다")
        return []
    
    songs_data = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    # 기본 데이터 추출
                    rank = row.get('Rank', '').strip()
                    previous_rank = row.get('Previous Rank', '').strip()
                    title = row.get('Track Name', '').strip()
                    artist = row.get('Artist Names', '').strip()
                    periods_on_chart = row.get('Periods on Chart', '0').strip()
                    youtube_url = row.get('YouTube URL', '').strip()
                    
                    # YouTube ID 추출 (없어도 저장함)
                    youtube_id = extract_youtube_id_from_url(youtube_url)
                    
                    # Shorts URL 생성
                    shorts_url = generate_shorts_url(youtube_id)
                    
                    # 태그 분석
                    is_trending, is_new_hit = analyze_chart_position(
                        rank, previous_rank, periods_on_chart
                    )
                    
                    song_data = {
                        'rank': rank,
                        'previous_rank': previous_rank,
                        'title': title,
                        'artist': artist,
                        'periods_on_chart': periods_on_chart,
                        'youtube_url': youtube_url,
                        'youtube_id': youtube_id,  # None일 수 있음
                        'shorts_url': shorts_url,  # UGC 카운터용 URL
                        'is_trending': is_trending,
                        'is_new_hit': is_new_hit
                    }
                    
                    songs_data.append(song_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 행 파싱 실패: {row}, 오류: {e}")
                    continue
        
        logger.info(f"✅ CSV 파싱 완료: {len(songs_data)}곡 처리됨")
        return songs_data
        
    except Exception as e:
        log_error_with_context(logger, e, "CSV 파싱")
        return []

def save_to_database(songs_data):
    """
    파싱된 데이터를 데이터베이스에 저장합니다.
    YouTube ID가 없어도 곡 정보는 저장됩니다.
    """
    if not songs_data:
        logger.error("❌ 저장할 데이터가 없습니다")
        return 0
    
    logger.info(f"💾 데이터베이스에 {len(songs_data)}곡 저장 중...")
    
    total_saved = 0
    trending_count = 0
    new_hit_count = 0
    no_id_count = 0
    
    for song in songs_data:
        try:
            # 곡 저장 (YouTube ID가 None이어도 저장)
            song_id = db.add_song_and_get_id(
                title=song['title'],
                artist=song['artist'],
                youtube_id=song['youtube_id']  # None일 수 있음
            )
            
            if song_id:
                # 트렌드 데이터 저장
                db.add_trend(
                    song_id=song_id,
                    source='youtube',
                    category='trending',
                    rank=song['rank'],
                    metrics={
                        'previous_rank': song['previous_rank'],
                        'periods_on_chart': song['periods_on_chart'],
                        'youtube_url': song['youtube_url'],
                        'shorts_url': song['shorts_url']
                    }
                )
                
                # 태그 업데이트
                if song['is_trending'] or song['is_new_hit']:
                    db.update_song_tags(
                        title=song['title'],
                        artist=song['artist'],
                        is_trending=song['is_trending'],
                        is_new_hit=song['is_new_hit']
                    )
                    
                    if song['is_trending']:
                        trending_count += 1
                    if song['is_new_hit']:
                        new_hit_count += 1
                
                # YouTube ID 없는 곡 카운트
                if not song['youtube_id']:
                    no_id_count += 1
                
                total_saved += 1
                
        except Exception as e:
            log_error_with_context(logger, e, f"곡 저장: {song['title']}")
    
    logger.info(f"✅ 데이터 저장 완료:")
    logger.info(f"  📊 총 저장: {total_saved}곡")
    logger.info(f"  🔥 인기급상승: {trending_count}곡")
    logger.info(f"  ⭐ 신곡: {new_hit_count}곡")
    logger.info(f"  ⚠️ YouTube ID 없음: {no_id_count}곡 (UGC 수집 불가)")
    
    return total_saved

def scrape_youtube_charts_csv():
    """
    YouTube Charts CSV 스크래핑 메인 함수
    """
    start_time = time.time()
    log_scraper_start(logger, "YouTube Charts CSV 스크래퍼", "CSV Download")
    
    try:
        # 1. CSV 다운로드
        csv_path = download_youtube_csv()
        if not csv_path:
            return False
        
        # 2. CSV 파싱
        songs_data = parse_csv_data(csv_path)
        if not songs_data:
            return False
        
        # 3. 데이터베이스 저장
        saved_count = save_to_database(songs_data)
        
        # 4. CSV 파일 보존 (임시 파일이 아니므로 삭제하지 않음)
        logger.info(f"📁 CSV 파일 저장 위치: {csv_path}")
        
        # 결과 로깅
        duration = time.time() - start_time
        log_scraper_end(logger, "YouTube Charts CSV 스크래퍼", saved_count > 0, duration, saved_count)
        
        return saved_count > 0
        
    except Exception as e:
        log_error_with_context(logger, e, "YouTube CSV 스크래핑")
        return False

if __name__ == "__main__":
    # 데이터베이스 초기화
    logger.info("💾 데이터베이스 초기화 중...")
    db.create_tables()
    logger.info("✅ 데이터베이스 준비 완료.")
    
    # CSV 스크래핑 실행
    success = scrape_youtube_charts_csv()
    
    if success:
        logger.info("🎉 YouTube CSV 스크래핑 완료!")
    else:
        logger.error("❌ YouTube CSV 스크래핑 실패!")
        sys.exit(1)