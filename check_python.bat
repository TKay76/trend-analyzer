@echo off
chcp 65001 >nul

echo ===================================
echo 🐍 Python 설치 상태 확인
echo ===================================
echo.

echo 🔍 Python 설치 확인 중...
echo.

set FOUND_PYTHON=0

REM 1. 기본 python 명령어 확인
echo [1] 기본 python 명령어 테스트:
python --version 2>nul
if !errorlevel! equ 0 (
    echo    ✅ 사용 가능
    set FOUND_PYTHON=1
) else (
    echo    ❌ 사용 불가능
)
echo.

REM 2. python3 명령어 확인
echo [2] python3 명령어 테스트:
python3 --version 2>nul
if !errorlevel! equ 0 (
    echo    ✅ 사용 가능
    set FOUND_PYTHON=1
) else (
    echo    ❌ 사용 불가능
)
echo.

REM 3. py 런처 확인
echo [3] Python Launcher (py) 테스트:
py --version 2>nul
if !errorlevel! equ 0 (
    echo    ✅ 사용 가능
    set FOUND_PYTHON=1
) else (
    echo    ❌ 사용 불가능
)
echo.

REM 4. Microsoft Store Python 확인
echo [4] Microsoft Store Python 테스트:
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" --version 2>nul
    if !errorlevel! equ 0 (
        echo    ✅ 사용 가능
        set FOUND_PYTHON=1
    ) else (
        echo    ❌ 실행 불가능
    )
) else (
    echo    ❌ 설치되지 않음
)
echo.

REM 5. 일반적인 설치 경로 확인
echo [5] 일반적인 설치 경로 확인:
for %%P in (
    "C:\Python39\python.exe"
    "C:\Python310\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Program Files\Python39\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
) do (
    if exist %%P (
        echo    📁 발견: %%P
        %%P --version 2>nul
        if !errorlevel! equ 0 (
            echo       ✅ 실행 가능
            set FOUND_PYTHON=1
        ) else (
            echo       ❌ 실행 불가능
        )
    )
)

echo.
echo ===================================
if %FOUND_PYTHON% equ 1 (
    echo 🎉 Python이 설치되어 있습니다!
    echo    setup_environment.bat를 실행하세요.
) else (
    echo ❌ Python이 설치되지 않았습니다.
    echo.
    echo 💡 Python 설치 방법:
    echo.
    echo 🔗 방법 1: 공식 웹사이트에서 설치
    echo    1. https://www.python.org/downloads/ 접속
    echo    2. 최신 Python 다운로드
    echo    3. 설치 시 "Add Python to PATH" 체크!
    echo.
    echo 🏪 방법 2: Microsoft Store에서 설치
    echo    1. Windows 키 + S로 Microsoft Store 검색
    echo    2. "Python 3.11" 검색하여 설치
    echo.
    echo 📋 설치 후 이 파일을 다시 실행하여 확인하세요.
)
echo ===================================

pause