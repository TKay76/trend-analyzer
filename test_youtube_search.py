#!/usr/bin/env python3
"""
YouTube 검색을 통한 UGC 카운트 수집 테스트
"""

import sys
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

def test_youtube_search_approach(youtube_id, title):
    """YouTube 검색으로 UGC 카운트 찾기"""
    
    # 검색 쿼리 생성
    search_query = f"{title} shorts {youtube_id}"
    search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    
    print(f"🔍 YouTube 검색 테스트")
    print(f"곡: {title}")
    print(f"검색 URL: {search_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(search_url, wait_until="domcontentloaded")
            print("  ⏳ 페이지 로딩 중...")
            time.sleep(5)
            
            # 스크롤하여 더 많은 결과 로딩
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 페이지 텍스트에서 결과 개수 찾기
            all_text = soup.get_text()
            
            # YouTube 검색 결과 패턴들
            patterns = [
                r'(\d+[.,]?\d*[KMB]?)\s*(?:results|결과)',
                r'About\s+(\d+[.,]?\d*[KMB]?)\s*results',
                r'약\s+(\d+[.,]?\d*[KMB]?)\s*개의?\s*결과',
            ]
            
            print(f"  🔍 페이지 텍스트 샘플: {all_text[:300].strip()}...")
            
            for pattern in patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    print(f"  📊 검색 결과 패턴 발견: {matches}")
                    return matches[0]
            
            # Shorts 관련 링크 개수 세기
            shorts_links = soup.find_all('a', href=re.compile(r'/shorts/'))
            if shorts_links:
                print(f"  📺 Shorts 링크 발견: {len(shorts_links)}개")
                return len(shorts_links)
            
            print("  ❌ 결과를 찾을 수 없음")
            return 0
            
        except Exception as e:
            print(f"  💥 오류: {e}")
            return 0
        finally:
            browser.close()

def test_direct_url_approach(youtube_id):
    """기존 방식으로 테스트"""
    
    url = f"https://youtube.com/source/{youtube_id}/shorts"
    print(f"\n🔗 Direct URL 테스트: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            print("  ⏳ 페이지 로딩 중...")
            time.sleep(8)
            
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            all_text = soup.get_text()
            
            print(f"  🔍 페이지 상태: {page.url}")
            print(f"  📄 페이지 제목: {page.title()}")
            print(f"  📝 페이지 텍스트 샘플: {all_text[:300].strip()}...")
            
            # 리다이렉션 확인
            if "youtube.com/watch" in page.url:
                print("  🔄 단일 비디오로 리다이렉션됨")
            elif "youtube.com/results" in page.url:
                print("  🔍 검색 결과로 리다이렉션됨")
            
            return 0
            
        except Exception as e:
            print(f"  💥 오류: {e}")
            return 0
        finally:
            browser.close()

if __name__ == "__main__":
    # 테스트 데이터
    test_cases = [
        ("983bBbJx0Mk", "Soda Pop"),
        ("A1MdThqGarI", "Pretty Little Baby"),
        ("g6NQW3WT9pQ", "Happy Boy"),
    ]
    
    for youtube_id, title in test_cases:
        print("=" * 60)
        print(f"테스트: {title} (ID: {youtube_id})")
        print("=" * 60)
        
        # 방법 1: YouTube 검색
        search_result = test_youtube_search_approach(youtube_id, title)
        
        # 방법 2: Direct URL
        direct_result = test_direct_url_approach(youtube_id)
        
        print(f"\n📊 결과 요약:")
        print(f"  검색 방식: {search_result}")
        print(f"  Direct URL: {direct_result}")
        print()