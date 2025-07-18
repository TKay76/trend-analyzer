@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ===================================================================
REM 🎵 Music Trend Analyzer - Complete Collection (Windows)
REM ===================================================================
REM 일일 완전한 음악 트렌드 데이터 수집을 위한 Windows 배치 파일
REM TikTok, YouTube UGC 카운트 및 해시태그를 안전하게 수집합니다.
REM ===================================================================

echo.
echo =========================================
echo 🌅 Music Trend Analyzer 시작
echo 📅 시작 시간: %date% %time%
echo =========================================
echo.

REM 현재 스크립트 디렉토리로 이동
cd /d "%~dp0"
echo 📁 작업 디렉토리: %CD%
echo.

REM Python 실행 파일 경로 설정 (Windows 가상환경)
set PYTHON_EXE="%CD%\venv\Scripts\python.exe"

REM Python 인코딩 환경변수 설정 (UTF-8 강제)
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONPATH=%CD%
set PATH=%CD%\venv\Scripts;%PATH%

REM Python 실행 파일 존재 확인
if not exist %PYTHON_EXE% (
    echo ❌ Python 가상환경이 없습니다: %PYTHON_EXE%
    echo.
    echo 💡 다음 명령으로 가상환경을 설정하세요:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo    playwright install chromium
    echo.
    pause
    exit /b 1
)

echo ✅ Python 환경 확인: %PYTHON_EXE%
echo.

REM 로그 디렉토리 생성
if not exist "logs" mkdir logs

REM 시작 시간 기록
set START_TIME=%time%

REM ==============================================
REM 1단계: 트렌드 데이터 수집 (TikTok + YouTube)
REM ==============================================
echo ========================================
echo 📊 1단계: 트렌드 데이터 수집
echo ========================================
echo.

echo 🎭 TikTok 트렌드 수집 중...
%PYTHON_EXE% src\scrapers\tiktok_music_scraper.py 2>nul
if !errorlevel! neq 0 (
    echo ❌ TikTok 트렌드 수집 실패
    echo 계속 진행합니다...
    echo.
) else (
    echo ✅ TikTok 트렌드 수집 완료
    echo.
)

echo 📺 YouTube 트렌드 수집 중...
%PYTHON_EXE% src\scrapers\youtube_csv_scraper.py 2>nul
if !errorlevel! neq 0 (
    echo ❌ YouTube 트렌드 수집 실패
    echo 계속 진행합니다...
    echo.
) else (
    echo ✅ YouTube 트렌드 수집 완료
    echo.
)

REM ==============================================
REM 2단계: UGC 데이터 수집 (배치 단위로 안전하게)
REM ==============================================
echo ========================================
echo 🎬 2단계: UGC 데이터 수집
echo ========================================
echo.

echo 🎭 TikTok UGC + 해시태그 수집 중...
echo    - 안전한 배치 단위로 수집합니다
echo    - 실패 시 자동 재시도됩니다
echo.
%PYTHON_EXE% scripts\collect_tiktok_batch_safe.py 2>nul
if !errorlevel! neq 0 (
    echo ⚠️ TikTok UGC 수집에서 일부 오류 발생
    echo 계속 진행합니다...
    echo.
) else (
    echo ✅ TikTok UGC 수집 완료
    echo.
)

echo 📺 YouTube UGC 수집 중...
echo    - 안전한 배치 단위로 수집합니다
echo    - 실패 시 자동 재시도됩니다
echo.
%PYTHON_EXE% scripts\collect_youtube_batch_safe.py 2>nul
if !errorlevel! neq 0 (
    echo ⚠️ YouTube UGC 수집에서 일부 오류 발생
    echo 계속 진행합니다...
    echo.
) else (
    echo ✅ YouTube UGC 수집 완료
    echo.
)

REM ==============================================
REM 3단계: 수집 결과 리포트 생성
REM ==============================================
echo ========================================
echo 📋 3단계: 수집 완료 리포트
echo ========================================
echo.

echo 📊 수집 결과 확인 중...
%PYTHON_EXE% scripts\check_collection_status.py 2>nul
echo.

REM 완료 시간 계산
set END_TIME=%time%
echo ========================================
echo 🎉 전체 수집 완료!
echo ========================================
echo 📅 시작: %START_TIME%
echo 📅 완료: %END_TIME%
echo.
echo 💾 결과 확인:
echo    - 로그: logs\ 폴더
echo    - 데이터베이스: src\database\view_database.py 실행
echo.

REM 성공 시 5초 후 자동 종료, 실패 시 수동 확인 대기
if %errorlevel% equ 0 (
    echo ✅ 모든 작업이 성공적으로 완료되었습니다.
    echo 5초 후 자동으로 종료됩니다...
    timeout /t 5 /nobreak >nul
) else (
    echo ⚠️ 일부 작업에서 오류가 발생했습니다.
    echo 로그를 확인하세요.
    echo.
    pause
)

echo.
echo 감사합니다! 🙏