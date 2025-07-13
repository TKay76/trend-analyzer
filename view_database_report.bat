@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo  Music Trend Analyzer - Database Report
echo ==========================================
echo.

REM 프로젝트 디렉토리로 이동
cd /d "%~dp0"

REM 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

REM 리포트 메뉴 표시
:menu
echo.
echo 보고싶은 리포트를 선택하세요:
echo.
echo 1. 전체 리포트 (모든 정보)
echo 2. 데이터베이스 개요
echo 3. 플랫폼별 통계
echo 4. 인기 곡 TOP 10
echo 5. 해시태그 분석
echo 6. 차트 트렌드
echo 7. 크로스 플랫폼 분석
echo 8. 요약 리포트
echo 9. 종료
echo.
set /p choice=선택 (1-9): 

if "%choice%"=="1" (
    echo.
    echo 전체 리포트 생성 중...
    python database_report.py
) else if "%choice%"=="2" (
    echo.
    python database_report.py overview
) else if "%choice%"=="3" (
    echo.
    python database_report.py platforms
) else if "%choice%"=="4" (
    echo.
    python database_report.py songs
) else if "%choice%"=="5" (
    echo.
    python database_report.py hashtags
) else if "%choice%"=="6" (
    echo.
    python database_report.py trends
) else if "%choice%"=="7" (
    echo.
    python database_report.py cross
) else if "%choice%"=="8" (
    echo.
    python database_report.py summary
) else if "%choice%"=="9" (
    echo 종료합니다.
    goto :end
) else (
    echo 잘못된 선택입니다. 1-9 사이의 숫자를 입력하세요.
    goto :menu
)

echo.
echo ==========================================
echo.
set /p continue=다른 리포트를 보시겠습니까? (y/n): 
if /i "%continue%"=="y" goto :menu
if /i "%continue%"=="yes" goto :menu

:end
echo.
echo 감사합니다!
pause