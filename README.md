# 🎵 Music Trend Analyzer

TikTok과 YouTube의 인기 음악 트렌드를 자동으로 수집하고, UGC(User Generated Content) 동영상 개수를 추적하여 음악의 바이럴 정도를 분석하는 도구입니다.

## 🚀 주요 기능

- **📊 트렌드 데이터 수집**: TikTok Creative Center와 YouTube Music Charts에서 실시간 음악 순위 데이터 수집
- **📈 순위 변화 추적**: 일별 순위 변화를 데이터베이스에 저장하여 트렌드 분석 가능
- **🎬 UGC 카운트 모니터링**: 각 음원을 사용한 YouTube Shorts와 TikTok 동영상 개수 추적
- **🔄 자동화 지원**: 스케줄링을 통한 정기적 데이터 수집
- **📋 대화형 데이터 뷰어**: 수집된 데이터를 쉽게 확인할 수 있는 CLI 도구

## 📁 프로젝트 구조

```
📁 tiktok music/
├── 📁 src/
│   ├── 📁 scrapers/     # 스크래핑 모듈들
│   │   ├── tiktok_music_scraper.py     # TikTok 트렌드 수집
│   │   ├── youtube_music_scraper.py    # YouTube 차트 수집
│   │   ├── tiktok_ugc_counter.py       # TikTok UGC 카운트
│   │   ├── youtube_ugc_counter.py      # YouTube UGC 카운트
│   │   └── ugc_data_updater.py         # UGC 데이터 통합 업데이트
│   └── 📁 database/     # 데이터베이스 관련
│       ├── database_manager.py         # 데이터베이스 관리
│       └── view_database.py           # 데이터 조회 도구
├── 📁 data/            # 데이터베이스 파일들 (gitignore)
├── 📁 docs/            # 개발 문서
├── 📁 tests/           # 테스트 및 POC 파일들
├── 📁 scripts/         # 유틸리티 스크립트들
├── run_trend_analysis.py              # 메인 실행 파일
└── requirements.txt                   # 의존성 패키지
```

## 🔧 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd "tiktok music"
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. Playwright 브라우저 설치
```bash
playwright install chromium
```

## 🎯 사용법

### 기본 사용법 (권장)
```bash
# 가상환경 활성화
source venv/bin/activate

# 전체 데이터 수집 실행
python run_trend_analysis.py
```

### 개별 모듈 실행
```bash
# TikTok 트렌드만 수집
python src/scrapers/tiktok_music_scraper.py

# YouTube 트렌드만 수집
python src/scrapers/youtube_music_scraper.py

# UGC 데이터만 업데이트
python src/scrapers/ugc_data_updater.py

# 특정 플랫폼 UGC만 업데이트
python src/scrapers/ugc_data_updater.py youtube
python src/scrapers/ugc_data_updater.py tiktok
```

### 데이터 확인
```bash
# 대화형 데이터베이스 뷰어 실행
python src/database/view_database.py
```

## 📊 수집되는 데이터

### 트렌드 데이터
- **TikTok**: Popular, Breakout 카테고리별 음악 순위
- **YouTube**: Trending, Top Rising, New Releases 순위

### UGC 데이터
- **YouTube Shorts**: 해당 음원을 사용한 쇼츠 동영상 개수
- **TikTok Videos**: 해당 음원을 사용한 동영상 개수

### 데이터베이스 스키마
- **songs**: 곡 정보 (제목, 아티스트, 플랫폼 ID, UGC 카운트 등)
- **daily_trends**: 일별 순위 데이터 (플랫폼, 카테고리, 순위, 날짜)

## 🔄 자동화 설정

### Cron을 이용한 일정 실행 (Linux/Mac)
```bash
# crontab 편집
crontab -e

# 매일 오전 9시 실행
0 9 * * * cd "/path/to/tiktok music" && source venv/bin/activate && python run_trend_analysis.py
```

### Windows 작업 스케줄러
1. 작업 스케줄러 열기
2. 기본 작업 만들기
3. 동작: 프로그램 시작
4. 프로그램: `python.exe`
5. 인수: `run_trend_analysis.py`
6. 시작 위치: 프로젝트 폴더 경로

## 🛠 기술 스택

- **Python 3.8+**
- **Playwright**: 웹 스크래핑 및 브라우저 자동화
- **BeautifulSoup4**: HTML 파싱
- **Pandas**: 데이터 처리 및 표시
- **SQLite**: 데이터베이스

## ⚠️ 주의사항

1. **웹 스크래핑 정책**: TikTok과 YouTube의 서비스 약관을 준수하세요
2. **API 제한**: 과도한 요청으로 인한 차단을 방지하기 위해 적절한 딜레이가 설정되어 있습니다
3. **브라우저 리소스**: Playwright는 실제 브라우저를 사용하므로 시스템 리소스를 많이 사용합니다
4. **데이터 개인정보**: 수집된 데이터는 공개 가능한 트렌드 정보만 포함합니다

## 📈 활용 사례

- **음악 산업 분석**: 플랫폼별 음악 트렌드 비교 분석
- **마케팅 인사이트**: 바이럴 성장 패턴 파악
- **콘텐츠 전략**: 인기 음원 기반 콘텐츠 기획
- **시장 조사**: 음악 트렌드 변화 모니터링

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🔗 참고 링크

- [TikTok Creative Center](https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en)
- [YouTube Music Charts](https://charts.youtube.com/charts/TopShortsSongs/kr/daily)
- [Playwright Documentation](https://playwright.dev/python/)

---

**⭐ 이 프로젝트가 도움이 되셨다면 스타를 눌러주세요!**