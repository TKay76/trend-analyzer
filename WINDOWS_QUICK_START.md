# 🚀 Windows 빠른 시작 가이드

Music Trend Analyzer를 Windows에서 원클릭으로 실행하기 위한 간단한 설정 가이드입니다.

## 📋 필수 사전 준비

1. **Python 3.8 이상** 설치 ([python.org](https://www.python.org/downloads/))
2. **안정적인 인터넷 연결**
3. **관리자 권한** (선택사항 - 자동 스케줄링용)

## 🐍 0단계: Python 설치 확인 (첫 실행 시)

Python이 설치되어 있는지 확인하려면 **check_python.bat** 파일을 실행하세요:

```cmd
# Windows 탐색기에서 check_python.bat 더블클릭
check_python.bat
```

Python이 설치되지 않은 경우 다음 방법 중 하나를 선택하세요:

### 방법 1: 공식 웹사이트 설치 (권장)
1. [python.org/downloads](https://www.python.org/downloads/) 접속
2. 최신 Python 3.11 또는 3.12 다운로드
3. **중요**: 설치 시 "Add Python to PATH" 체크박스 꼭 체크!

### 방법 2: Microsoft Store 설치 (간편)
1. `Windows 키 + S`로 Microsoft Store 검색
2. "Python 3.11" 검색하여 설치

### 방법 3: 이미 설치된 경우 PATH 설정
1. `Windows 키 + R` → `sysdm.cpl` 실행
2. "고급" 탭 → "환경 변수" 클릭
3. "Path" 변수에 Python 설치 경로 추가

## 🔧 1단계: 초기 환경 설정

프로젝트 폴더에서 **setup_environment.bat** 파일을 실행하세요:

```cmd
# Windows 탐색기에서 setup_environment.bat 더블클릭
# 또는 명령 프롬프트에서:
setup_environment.bat
```

이 스크립트가 자동으로:
- ✅ Python 가상환경 생성
- ✅ 필요한 패키지 설치
- ✅ Playwright 브라우저 다운로드
- ✅ 데이터베이스 연결 확인

## 🎵 2단계: 데이터 수집 실행

환경 설정이 완료되면 **run_complete_collection.bat** 파일을 실행하세요:

```cmd
# Windows 탐색기에서 run_complete_collection.bat 더블클릭
# 또는 명령 프롬프트에서:
run_complete_collection.bat
```

이 스크립트가 자동으로:
- 🎭 TikTok 트렌드 데이터 수집
- 📺 YouTube 트렌드 데이터 수집
- 🎬 UGC 카운트 수집 (안전한 배치 처리)
- 📌 해시태그 데이터 수집
- 📊 수집 결과 리포트 생성
- 🔧 **UTF-8 인코딩 자동 설정**으로 안정적 실행

## 📊 3단계: 결과 확인

수집 완료 후 다음으로 결과를 확인할 수 있습니다:

```cmd
# 가상환경 활성화
venv\Scripts\activate

# 수집 상태 확인
python scripts/check_collection_status.py

# 또는 가상환경 직접 사용
venv\Scripts\python.exe scripts/check_collection_status.py

# 데이터베이스 직접 보기
venv\Scripts\python.exe src/database/view_database.py
```

## ⏰ 4단계: 자동 스케줄링 (선택사항)

매일 자동으로 데이터를 수집하려면:

1. **관리자 권한**으로 명령 프롬프트 실행
2. 다음 명령어 입력:

```cmd
# Windows 작업 스케줄러에 작업 등록
schtasks /create /xml "windows_scheduler_task.xml" /tn "Music Trend Analyzer Daily"
```

또는 수동으로:
1. `Win + R` → `taskschd.msc` 실행
2. 작업 스케줄러에서 **"작업 가져오기"** 선택
3. `windows_scheduler_task.xml` 파일 선택

## 🔍 문제 해결

### 환경 설정 실패
```cmd
# Python 설치 확인
python --version

# 가상환경 재생성
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Python 경로 문제
```cmd
# 시스템 Python이 없는 경우 가상환경 직접 사용
venv\Scripts\python.exe --version
venv\Scripts\python.exe scripts/check_collection_status.py
```

### 수집 중 오류 발생
- 📁 `logs/` 폴더의 로그 파일 확인
- 인터넷 연결 상태 확인
- 방화벽/보안 프로그램 예외 설정

### 타임아웃 문제
- 새로운 배치 시스템이 자동으로 재시도합니다
- `logs/progress_tiktok.json`, `logs/progress_youtube.json` 파일로 진행 상황 추적
- 중단된 지점부터 재시작 가능

## 📁 주요 파일 설명

| 파일명 | 용도 |
|--------|------|
| `setup_environment.bat` | 초기 환경 설정 |
| `run_complete_collection.bat` | 메인 실행 파일 |
| `scripts/check_collection_status.py` | 수집 상태 확인 |
| `windows_scheduler_task.xml` | 자동 스케줄링 설정 |
| `logs/` | 실행 로그 및 진행상황 저장 |
| `scripts/` | 모든 실행 스크립트 통합 |

## 🎯 특징

### ✅ 개선된 안정성
- **작은 배치 단위** 처리로 타임아웃 방지
- **자동 재시도** 시스템으로 실패율 최소화
- **진행 상황 저장**으로 중단 지점부터 재시작

### ✅ 사용자 친화적
- **원클릭 실행** - 복잡한 명령어 불필요
- **실시간 진행 상황** 표시
- **상세한 결과 리포트** 제공

### ✅ Windows 최적화
- Windows 경로 구조 자동 감지
- 가상환경 자동 관리
- 작업 스케줄러 완벽 지원

## 📞 지원

문제가 발생하면:
1. `logs/` 폴더의 최신 로그 파일 확인
2. `venv\Scripts\python.exe scripts/check_collection_status.py` 실행하여 현재 상태 파악
3. 필요시 `setup_environment.bat` 재실행으로 환경 재설정

---

**🎉 축하합니다!** 이제 Windows에서 Music Trend Analyzer를 완전히 자동화된 방식으로 사용할 수 있습니다!