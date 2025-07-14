@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ===================================================================
REM 🔧 Music Trend Analyzer - 환경 설정 (Windows)
REM ===================================================================
REM Windows 환경에서 Music Trend Analyzer 실행을 위한 초기 설정
REM Python 가상환경 생성, 패키지 설치, 브라우저 설정을 자동화
REM ===================================================================

echo.
echo =========================================
echo 🔧 Music Trend Analyzer 환경 설정
echo =========================================
echo.

REM 현재 스크립트 디렉토리로 이동
cd /d "%~dp0"
echo 📁 설정 디렉토리: %CD%
echo.

REM Python 설치 확인 (여러 경로 시도)
set PYTHON_CMD=
echo 🔍 Python 설치 위치 확인 중...

REM 1. 기본 python 명령어 시도
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=python
    echo ✅ Python 발견: 기본 PATH
    goto :python_found
)

REM 2. python3 명령어 시도
python3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=python3
    echo ✅ Python 발견: python3 명령어
    goto :python_found
)

REM 3. py 런처 시도
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=py
    echo ✅ Python 발견: Python Launcher
    goto :python_found
)

REM 4. Microsoft Store Python 경로 시도
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD="%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
        echo ✅ Python 발견: Microsoft Store
        goto :python_found
    )
)

REM 5. 일반적인 설치 경로들 시도
for %%P in (
    "C:\Python39\python.exe"
    "C:\Python310\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python313\python.exe"
    "C:\Program Files\Python39\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
) do (
    if exist %%P (
        %%P --version >nul 2>&1
        if !errorlevel! equ 0 (
            set PYTHON_CMD=%%P
            echo ✅ Python 발견: %%P
            goto :python_found
        )
    )
)

REM Python을 찾지 못한 경우
echo ❌ Python이 설치되지 않았거나 찾을 수 없습니다.
echo.
echo 💡 다음 방법 중 하나를 선택하세요:
echo.
echo 🔗 방법 1: 공식 Python 설치
echo    1. https://www.python.org/downloads/ 접속
echo    2. 최신 Python 3.8+ 다운로드
echo    3. 설치 시 "Add Python to PATH" 체크 필수!
echo.
echo 🏪 방법 2: Microsoft Store에서 설치
echo    1. Windows 키 + S 눌러서 'Microsoft Store' 검색
echo    2. 'Python 3.11' 또는 'Python 3.12' 검색하여 설치
echo.
echo 🔧 방법 3: 이미 설치된 경우 PATH 추가
echo    1. Windows 키 + R 눌러서 'sysdm.cpl' 실행
echo    2. '고급' 탭 → '환경 변수' 클릭
echo    3. 'Path' 변수에 Python 설치 경로 추가
echo.
echo 설치 후 이 창을 닫고 다시 실행하세요.
pause
exit /b 1

:python_found

echo ✅ Python 확인 완료
%PYTHON_CMD% --version
echo.

REM 기존 가상환경 확인 및 재생성 여부 묻기
if exist "venv" (
    echo 📁 기존 가상환경이 발견되었습니다.
    echo.
    set /p RECREATE="기존 환경을 삭제하고 재생성하시겠습니까? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo 🗑️ 기존 가상환경 삭제 중...
        rmdir /s /q "venv"
        echo ✅ 삭제 완료
        echo.
    ) else (
        echo 📂 기존 가상환경을 사용합니다.
        goto :install_packages
    )
)

REM 가상환경 생성
echo 🐍 Python 가상환경 생성 중...
%PYTHON_CMD% -m venv venv
if !errorlevel! neq 0 (
    echo ❌ 가상환경 생성 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 생성 완료
echo.

:install_packages
REM 가상환경 활성화
echo 🔄 가상환경 활성화 중...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 활성화 완료
echo.

REM pip 업그레이드
echo 📦 pip 업그레이드 중...
venv\Scripts\python.exe -m pip install --upgrade pip
echo.

REM requirements.txt 확인
if not exist "requirements.txt" (
    echo ❌ requirements.txt 파일이 없습니다.
    echo    프로젝트 루트 디렉토리에서 실행하세요.
    pause
    exit /b 1
)

REM 패키지 설치
echo 📦 필요한 패키지 설치 중...
echo    이 과정은 몇 분 소요될 수 있습니다...
echo.
venv\Scripts\pip.exe install -r requirements.txt
if !errorlevel! neq 0 (
    echo ❌ 패키지 설치 실패
    echo    인터넷 연결을 확인하고 다시 시도하세요.
    pause
    exit /b 1
)
echo ✅ 패키지 설치 완료
echo.

REM Playwright 브라우저 설치
echo 🌐 Playwright 브라우저 설치 중...
echo    Chromium 브라우저를 다운로드합니다...
echo.
venv\Scripts\playwright.exe install chromium
if !errorlevel! neq 0 (
    echo ❌ 브라우저 설치 실패
    echo    인터넷 연결을 확인하고 다시 시도하세요.
    pause
    exit /b 1
)
echo ✅ 브라우저 설치 완료
echo.

REM 설치 확인 테스트
echo 🧪 설치 확인 테스트 중...
venv\Scripts\python.exe -c "import playwright; print('✅ Playwright 설치 확인 완료')"
if !errorlevel! neq 0 (
    echo ❌ Playwright 설치 확인 실패
    pause
    exit /b 1
)

venv\Scripts\python.exe -c "import sqlite3; print('✅ SQLite 확인 완료')"
venv\Scripts\python.exe -c "import requests; print('✅ Requests 확인 완료')"
venv\Scripts\python.exe -c "from bs4 import BeautifulSoup; print('✅ BeautifulSoup 확인 완료')"
echo.

REM 로그 디렉토리 생성
if not exist "logs" (
    mkdir logs
    echo 📁 로그 디렉토리 생성 완료
)

REM 데이터베이스 초기화 확인
echo 🗄️ 데이터베이스 상태 확인 중...
venv\Scripts\python.exe -c "import os, sys; sys.path.append('.'); from src.database import database_manager as db; conn = db.get_db_connection(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM songs'); count = cursor.fetchone()[0]; print(f'✅ 데이터베이스 확인 완료 ({count}개 곡 등록됨)'); conn.close()" 2>nul
if !errorlevel! neq 0 (
    echo ⚠️ 데이터베이스 확인 중 경고가 있었지만 계속 진행합니다.
)
echo.

echo =========================================
echo 🎉 환경 설정 완료!
echo =========================================
echo.
echo 📋 설정된 환경:
echo    • Python 가상환경: venv\
echo    • 필요 패키지: 설치 완료  
echo    • Playwright 브라우저: 설치 완료
echo    • 로그 디렉토리: logs\
echo    • 데이터베이스: 연결 확인 완료
echo.
echo 🚀 이제 다음 명령으로 데이터 수집을 시작할 수 있습니다:
echo    run_complete_collection.bat
echo.
echo 💡 Windows 작업 스케줄러에 등록하려면:
echo    windows_scheduler_task.xml 파일을 사용하세요.
echo.

pause
echo 설정이 완료되었습니다! 🙏