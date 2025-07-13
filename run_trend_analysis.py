#!/usr/bin/env python3
"""
통합 트렌드 분석 스크립트
TikTok → YouTube 스크래핑 후 UGC 데이터 업데이트를 순차적으로 실행합니다.
"""

import sys
import subprocess
import time
from datetime import datetime

def run_script(script_name, description):
    """
    스크립트를 실행하고 결과를 반환합니다.
    """
    print(f"\n{'='*60}")
    print(f"🔄 {description} 시작...")
    print(f"📄 실행 파일: {script_name}")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
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
        
        print(f"\n📊 {description} 결과:")
        print(f"⏱️ 실행 시간: {duration:.1f}초")
        print(f"🔄 반환 코드: {result.returncode}")
        
        if result.stdout:
            print(f"\n📝 출력:")
            print(result.stdout)
            
        if result.stderr:
            print(f"\n⚠️ 오류:")
            print(result.stderr)
            
        if result.returncode == 0:
            print(f"✅ {description} 성공!")
            return True
        else:
            print(f"❌ {description} 실패!")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} 타임아웃 (30분 초과)")
        return False
    except Exception as e:
        print(f"💥 {description} 실행 중 오류: {e}")
        return False

def main():
    """
    메인 실행 함수
    """
    print("🎵 통합 트렌드 분석 시스템 시작")
    print(f"📅 실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
            print(f"\n⚠️ {description}에서 오류가 발생했습니다.")
            user_input = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
            if user_input != 'y':
                print("❌ 사용자가 중단을 선택했습니다.")
                break
        
        # 스크립트 간 대기 시간 (브라우저 리소스 정리)
        if script_name != scripts[-1][0]:  # 마지막 스크립트가 아니면
            print(f"\n⏳ 다음 스크립트 실행을 위해 5초 대기...")
            time.sleep(5)
    
    # 최종 결과 요약
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    print(f"\n{'='*60}")
    print("📊 최종 실행 결과")
    print(f"{'='*60}")
    print(f"⏱️ 총 실행 시간: {total_duration:.1f}초 ({total_duration/60:.1f}분)")
    
    successful_count = 0
    for script_name, description, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} {description}")
        if success:
            successful_count += 1
    
    print(f"\n📈 성공률: {successful_count}/{len(results)} ({successful_count/len(results)*100:.1f}%)")
    
    if successful_count == len(results):
        print("\n🎉 모든 스크립트가 성공적으로 완료되었습니다!")
        print("💾 데이터베이스에 최신 트렌드 데이터와 UGC 카운트가 저장되었습니다.")
        print("👀 결과 확인: python src/database/view_database.py")
    else:
        print(f"\n⚠️ {len(results) - successful_count}개의 스크립트에서 오류가 발생했습니다.")
        print("🔍 로그를 확인하여 문제를 해결해주세요.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⛔ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)