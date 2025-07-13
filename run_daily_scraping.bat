@echo off
setlocal EnableDelayedExpansion
REM =====================================================
REM Music Trend Analyzer - Daily Scraping Batch Script
REM 매일 자동 실행되는 음악 트렌드 데이터 수집 스크립트
REM =====================================================

echo.
echo ==========================================
echo  Music Trend Analyzer Starting
echo ==========================================
echo Start Time: %date% %time%
echo.

REM 현재 배치 파일의 위치를 기준으로 프로젝트 디렉토리 설정
cd /d "%~dp0"

REM 프로젝트 디렉토리 확인
echo Current Directory: %cd%

REM 가상환경 존재 여부 확인
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run the following commands first:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo   playwright install chromium
    echo.
    pause
    exit /b 1
)

REM 가상환경 활성화
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Python 환경 확인
echo Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found in virtual environment!
    pause
    exit /b 1
)

REM 로그 디렉토리 생성 (없는 경우)
if not exist "logs" (
    echo Creating logs directory...
    mkdir logs
)

REM 데이터 디렉토리 생성 (없는 경우)
if not exist "data" (
    echo Creating data directory...
    mkdir data
)

echo.
echo ==========================================
echo  Starting Music Trend Analysis
echo ==========================================
echo.

REM 메인 스크래핑 스크립트 실행
python run_trend_analysis.py

REM 실행 결과 확인
if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo  SUCCESS: Scraping completed successfully
    echo ==========================================
    echo End Time: %date% %time%
    echo.
    
    REM 로그 파일 생성 확인
    if exist "logs\*.log" (
        echo Log files created in: %cd%\logs\
        
        REM 최신 로그 파일 찾기 및 마지막 몇 줄 표시
        for /f %%i in ('dir /b /o:d logs\trend_analyzer_*.log 2^>nul') do set latest_log=%%i
        if defined latest_log (
            echo.
            echo Latest log file: !latest_log!
            echo Last 5 lines:
            type "logs\!latest_log!" | find /v "" | more +5
        )
    ) else (
        echo WARNING: No log files found
    )
    
    REM 데이터베이스 파일 확인
    if exist "data\trend_analysis.db" (
        echo Database file exists: %cd%\data\trend_analysis.db
        for %%i in ("data\trend_analysis.db") do echo Database size: %%~zi bytes
    ) else (
        echo WARNING: Database file not found
    )
    
) else (
    echo.
    echo ==========================================
    echo  ERROR: Scraping failed with code %errorlevel%
    echo ==========================================
    echo End Time: %date% %time%
    echo.
    echo Please check the error logs in: %cd%\logs\
    
    REM 에러 로그 파일이 있다면 마지막 몇 줄 표시
    for /f %%i in ('dir /b /o:d logs\errors_*.log 2^>nul') do set latest_error_log=%%i
    if defined latest_error_log (
        echo.
        echo Latest error log: !latest_error_log!
        echo Last 10 lines:
        type "logs\!latest_error_log!" | find /v "" | more +10
    )
)

echo.
echo ==========================================
echo  Batch Script Completed
echo ==========================================

REM 스케줄러에서 실행될 때는 자동으로 종료
REM 수동 실행 시에는 결과 확인을 위해 잠시 대기
if /i "%1"=="--no-pause" goto :end
if defined SESSIONNAME (
    REM 사용자 세션에서 실행된 경우 (수동 실행)
    echo.
    echo Press any key to close this window...
    pause >nul
) else (
    REM 백그라운드에서 실행된 경우 (스케줄러)
    timeout /t 3 /nobreak >nul
)

:end
echo Script finished at %date% %time%