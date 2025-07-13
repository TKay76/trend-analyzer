# 🕐 Windows 작업 스케줄러 자동화 설정 가이드

Music Trend Analyzer를 Windows 11에서 매일 새벽 2시에 자동으로 실행하는 방법을 안내합니다.

## 📋 목차

1. [사전 준비](#1️⃣-사전-준비)
2. [프로젝트 이동](#2️⃣-프로젝트-이동)
3. [Python 환경 설정](#3️⃣-python-환경-설정)
4. [배치 파일 확인](#4️⃣-배치-파일-확인)
5. [작업 스케줄러 설정](#5️⃣-작업-스케줄러-설정)
6. [테스트 및 검증](#6️⃣-테스트-및-검증)
7. [모니터링 및 관리](#7️⃣-모니터링-및-관리)
8. [문제 해결](#8️⃣-문제-해결)

---

## 1️⃣ 사전 준비

### 필요 환경
- ✅ Windows 11
- ✅ Python 3.8+ 설치됨
- ✅ 관리자 권한 (작업 스케줄러 설정용)
- ✅ 안정적인 인터넷 연결

### 확인사항
```cmd
# Python 버전 확인
python --version

# pip 확인
pip --version
```

---

## 2️⃣ 프로젝트 이동

### WSL에서 Windows로 복사
```bash
# WSL에서 실행
cp -r "/mnt/d/_Unity Project/trend-analyzer" "/mnt/c/Users/[사용자명]/Desktop/"
```

### 수동 복사 방법
1. WSL 경로: `/mnt/d/_Unity Project/trend-analyzer`
2. Windows 대상 경로: `C:\Users\[사용자명]\Desktop\trend-analyzer`
3. 폴더 전체를 복사

**⚠️ 중요**: `[사용자명]` 부분을 실제 Windows 사용자명으로 변경하세요.

---

## 3️⃣ Python 환경 설정

### 명령 프롬프트에서 실행

```cmd
# 1. 프로젝트 디렉토리로 이동
cd C:\Users\[사용자명]\Desktop\trend-analyzer

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
venv\Scripts\activate

# 4. 패키지 설치
pip install -r requirements.txt

# 5. Playwright 브라우저 설치
playwright install chromium

# 6. 설치 확인
python -c "import playwright; print('Playwright 설치 완료')"
```

### 디렉토리 구조 확인
```
C:\Users\[사용자명]\Desktop\trend-analyzer\
├── venv\                           # 가상환경
├── src\                           # 소스 코드
├── data\                          # 데이터베이스 파일
├── logs\                          # 로그 파일 (자동 생성)
├── requirements.txt               # 의존성
├── run_trend_analysis.py         # 메인 실행 파일
└── run_daily_scraping.bat        # 배치 파일 (제공됨)
```

---

## 4️⃣ 배치 파일 확인

프로젝트에 포함된 `run_daily_scraping.bat` 파일을 사용합니다.

### 배치 파일 경로
```
C:\Users\[사용자명]\Desktop\trend-analyzer\run_daily_scraping.bat
```

### 배치 파일 내용 확인
배치 파일을 텍스트 에디터로 열어서 경로가 올바른지 확인하세요:
- `C:\Users\[사용자명]` 부분이 실제 사용자명과 일치하는지 확인

---

## 5️⃣ 작업 스케줄러 설정

### A. 작업 스케줄러 열기
1. `Win + R` 키 조합
2. `taskschd.msc` 입력
3. Enter 키 또는 확인 클릭

### B. 기본 작업 만들기
1. 오른쪽 **"작업"** 패널에서 **"기본 작업 만들기"** 클릭

### C. 일반 정보 입력
- **이름**: `Music Trend Analyzer Daily`
- **설명**: `매일 새벽 2시에 TikTok과 YouTube 음악 트렌드 데이터를 자동 수집합니다.`
- **다음** 클릭

### D. 트리거 설정
- **시작 시기**: `매일` 선택
- **다음** 클릭
- **시작 날짜**: 오늘 날짜 (기본값)
- **시작 시간**: `02:00:00` (새벽 2시)
- **간격**: `1일마다 되풀이` (기본값)
- **다음** 클릭

### E. 동작 설정
- **수행할 작업**: `프로그램 시작` 선택
- **다음** 클릭
- **프로그램/스크립트**: 
  ```
  C:\Users\[사용자명]\Desktop\trend-analyzer\run_daily_scraping.bat
  ```
- **시작 위치(선택 사항)**:
  ```
  C:\Users\[사용자명]\Desktop\trend-analyzer
  ```
- **다음** 클릭

### F. 완료 및 고급 설정
1. **마침** 클릭 전에 **"마침을 클릭할 때 이 작업에 대한 속성 대화 상자 열기"** 체크
2. **마침** 클릭

### G. 고급 설정 (속성 대화 상자)

#### 일반 탭:
- ☑️ **"사용자가 로그온했는지 여부에 관계없이 실행"**
- ☑️ **"가장 높은 권한으로 실행"**
- **보안 옵션**: "Windows Vista, Windows Server 2008"

#### 조건 탭:
- ☑️ **"컴퓨터의 전원이 켜져 있는 경우에만 작업 시작"**
- ☑️ **"AC 전원에 연결된 경우에만 시작"** (노트북인 경우)
- ☑️ **"다음 네트워크 연결이 사용 가능한 경우에만 시작"**: "임의 연결"

#### 설정 탭:
- ☑️ **"요청 시 작업 실행 허용"**
- ☑️ **"예약된 시작 시간을 놓친 경우 가능한 한 빨리 작업 시작"**
- ☑️ **"작업이 실패할 경우 다시 시작 간격"**: `1분`
- **다시 시작 시도**: `3회`
- **작업 중지 조건**: `1시간`

3. **확인** 클릭하여 설정 완료

---

## 6️⃣ 테스트 및 검증

### A. 수동 배치 파일 테스트
```cmd
# 명령 프롬프트에서 실행
cd C:\Users\[사용자명]\Desktop\trend-analyzer
run_daily_scraping.bat
```

**예상 결과:**
- 브라우저가 자동으로 열림
- TikTok과 YouTube 데이터 스크래핑 진행
- 로그 파일 생성됨

### B. 작업 스케줄러에서 테스트
1. 작업 스케줄러에서 **"Music Trend Analyzer Daily"** 작업 찾기
2. 작업 우클릭 → **"실행"** 선택
3. 실행 상태 확인

### C. 결과 확인
**로그 파일 위치:**
```
C:\Users\[사용자명]\Desktop\trend-analyzer\logs\
├── trend_analyzer_20250713.log    # 전체 실행 로그
└── errors_20250713.log            # 에러 로그 (있는 경우)
```

**데이터베이스 확인:**
```cmd
# 데이터 확인 도구 실행
cd C:\Users\[사용자명]\Desktop\trend-analyzer
venv\Scripts\activate
python src/database/view_database.py
```

---

## 7️⃣ 모니터링 및 관리

### A. 작업 실행 기록 확인
1. 작업 스케줄러에서 작업 선택
2. 하단 **"기록"** 탭 클릭
3. 실행 성공/실패 기록 확인

### B. 정기적 점검사항

**매일 오전 확인:**
- [ ] 로그 파일이 새로 생성되었는가?
- [ ] 에러 로그에 치명적 오류가 있는가?
- [ ] 데이터베이스에 새 데이터가 추가되었는가?

**주간 확인:**
- [ ] 로그 폴더 용량 관리 (오래된 로그 정리)
- [ ] 데이터베이스 백업
- [ ] 시스템 리소스 사용량 확인

### C. 로그 관리
```cmd
# 30일 이상 된 로그 파일 수동 정리 (PowerShell)
Get-ChildItem "C:\Users\[사용자명]\Desktop\trend-analyzer\logs" -Filter "*.log" | Where-Object {$_.CreationTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

---

## 8️⃣ 문제 해결

### A. 일반적인 문제

#### 1. 작업이 실행되지 않음
**확인사항:**
- [ ] 컴퓨터가 해당 시간에 켜져 있었는가?
- [ ] 작업 스케줄러 서비스가 실행 중인가?
- [ ] 배치 파일 경로가 올바른가?

**해결방법:**
```cmd
# 작업 스케줄러 서비스 재시작
net stop "Task Scheduler"
net start "Task Scheduler"
```

#### 2. Python 환경 오류
**확인사항:**
- [ ] 가상환경이 올바르게 생성되었는가?
- [ ] requirements.txt의 모든 패키지가 설치되었는가?

**해결방법:**
```cmd
# 가상환경 재생성
cd C:\Users\[사용자명]\Desktop\trend-analyzer
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. 브라우저 실행 오류
**해결방법:**
```cmd
# Playwright 브라우저 재설치
playwright install chromium --force
```

#### 4. 권한 문제
**해결방법:**
- 작업 스케줄러에서 **"가장 높은 권한으로 실행"** 옵션 확인
- 관리자 권한으로 명령 프롬프트 실행 후 테스트

### B. 로그 분석

#### 에러 로그 확인
```cmd
# 최신 에러 로그 열기
notepad C:\Users\[사용자명]\Desktop\trend-analyzer\logs\errors_*.log
```

#### 일반 로그 확인
```cmd
# 최신 실행 로그 열기
notepad C:\Users\[사용자명]\Desktop\trend-analyzer\logs\trend_analyzer_*.log
```

### C. 긴급 복구

#### 설정 백업
작업 스케줄러 설정을 XML로 내보내기:
1. 작업 우클릭 → **"내보내기"**
2. 안전한 위치에 저장

#### 설정 복원
1. 작업 스케줄러에서 **"작업 가져오기"**
2. 백업한 XML 파일 선택

---

## 📞 지원 및 참고

### 유용한 명령어
```cmd
# 현재 실행 중인 Python 프로세스 확인
tasklist | findstr python

# 작업 스케줄러 작업 목록 (PowerShell)
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Music*"}

# 디스크 공간 확인
dir C:\Users\[사용자명]\Desktop\trend-analyzer /s
```

### 참고 링크
- [Windows 작업 스케줄러 공식 문서](https://docs.microsoft.com/ko-kr/windows/win32/taskschd/task-scheduler-start-page)
- [Playwright Python 문서](https://playwright.dev/python/)

---

## ✅ 설정 완료 체크리스트

- [ ] 프로젝트를 Windows 데스크톱으로 이동 완료
- [ ] Python 가상환경 설정 및 패키지 설치 완료
- [ ] 배치 파일 경로 확인 완료
- [ ] 작업 스케줄러에 작업 등록 완료
- [ ] 수동 테스트 실행 성공
- [ ] 로그 파일 생성 확인
- [ ] 데이터베이스에 데이터 저장 확인
- [ ] 모니터링 방법 숙지

축하합니다! 🎉 이제 매일 새벽 2시에 자동으로 음악 트렌드 데이터가 수집됩니다.

---

**📧 문제 발생 시 확인할 파일들:**
- `logs/trend_analyzer_YYYYMMDD.log` - 전체 실행 로그
- `logs/errors_YYYYMMDD.log` - 에러 로그
- Windows 이벤트 뷰어 - 시스템 수준 오류
- 작업 스케줄러 기록 탭 - 작업 실행 상태