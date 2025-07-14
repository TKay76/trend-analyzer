# 🎵 Music Trend Analyzer

TikTok과 YouTube의 인기 음악 트렌드를 자동으로 수집하고, UGC(User Generated Content) 동영상 개수를 추적하여 음악의 바이럴 정도를 분석하는 **production-ready** 도구입니다.

## 🚀 주요 기능

- **📊 고성능 트렌드 데이터 수집**: TikTok Creative Center와 YouTube Music Charts에서 실시간 음악 순위 데이터 수집
- **📈 효율적인 순위 변화 추적**: 최적화된 데이터베이스와 인덱스로 빠른 트렌드 분석
- **🎬 UGC 카운트 모니터링**: 각 음원을 사용한 YouTube Shorts와 TikTok 동영상 개수 추적
- **🔄 완전 자동화**: Windows 작업 스케줄러 또는 Cron을 통한 무인 데이터 수집
- **📋 구조화된 로깅**: 전문적인 로그 시스템으로 모니터링 및 디버깅 지원
- **🗄️ 확장 가능한 데이터베이스**: 수백만 레코드까지 최적화된 SQLite 스키마

## 📁 프로젝트 구조

```
📁 trend-analyzer/
├── 📁 src/
│   ├── 📁 scrapers/     # 스크래핑 모듈들
│   │   ├── tiktok_music_scraper.py     # TikTok 트렌드 수집
│   │   ├── youtube_music_scraper.py    # YouTube 차트 수집
│   │   ├── tiktok_ugc_counter.py       # TikTok UGC 카운트
│   │   ├── youtube_ugc_counter.py      # YouTube UGC 카운트
│   │   └── ugc_data_updater.py         # UGC 데이터 통합 업데이트
│   ├── 📁 database/     # 데이터베이스 관련
│   │   ├── database_manager.py         # 데이터베이스 관리 (인덱스 최적화 포함)
│   │   └── view_database.py           # 데이터 조회 도구
│   └── 📁 utils/        # 유틸리티 모듈들
│       └── logger_config.py           # 중앙화된 로깅 설정
├── 📁 data/            # 데이터베이스 파일들 (gitignore)
├── 📁 docs/            # 문서화
│   └── Windows_Scheduler_Setup.md     # Windows 자동화 설정 가이드
├── 📁 logs/            # 로그 파일들 (자동 생성)
├── 📁 tests/           # 테스트 및 POC 파일들
├── 📁 scripts/         # 데이터베이스 최적화 스크립트들
│   ├── improve_database_schema.py     # 스키마 마이그레이션
│   ├── fix_business_approval_column.py # NULL 값 수정
│   └── optimize_database_indexes.py   # 인덱스 최적화
├── run_trend_analysis.py              # 메인 실행 파일
├── run_daily_scraping.bat             # Windows 자동화 배치 파일
└── requirements.txt                   # 의존성 패키지 (버전 고정)
```

## 🔧 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd trend-analyzer
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

### 5. 데이터베이스 최적화 (권장)
```bash
# 처음 설치 후 인덱스 최적화 실행
python scripts/optimize_database_indexes.py
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
- **TikTok**: Popular, Breakout 카테고리별 음악 순위 + 비즈니스 승인 정보
- **YouTube**: Trending, Top Rising, New Releases 순위 + 급상승/신곡 태그

### UGC 데이터 (실시간 수집)
- **YouTube Shorts**: 해당 음원을 사용한 쇼츠 동영상 개수
- **TikTok Videos**: 해당 음원을 사용한 동영상 개수

### 해시태그 데이터 (v4.0 신규)
- **TikTok 해시태그**: 각 곡별 상위 10개 해시태그와 사용 빈도수
- **트렌드 분석**: #fyp, #viral 등 바이럴 패턴 추적

### 데이터베이스 스키마 (v4.0 확장)
- **songs**: 곡 정보 (제목, 아티스트, 플랫폼 ID, **UGC 카운트**, 비즈니스 승인 여부)
- **daily_trends**: 일별 순위 데이터 (플랫폼, 카테고리, 순위, 날짜, 구조화된 조회수 데이터)
- **song_hashtags**: 곡별 해시태그 정보 (해시태그명, 빈도수, 순위, 수집일자)

### 성능 최적화 기능
- **🚀 고성능 쿼리**: 조회수 기준 정렬 및 필터링 (100-1000배 빠름)
- **📊 효율적인 분석**: 숫자 기반 메트릭으로 통계 연산 가능
- **🔍 빠른 검색**: 곡별, 날짜별, 플랫폼별 인덱스 최적화

## 🔄 자동화 설정

### 🪟 Windows 작업 스케줄러 (권장)
**완전 자동화된 설정을 위해 상세한 가이드를 제공합니다:**

📖 **[Windows 자동화 설정 가이드](docs/Windows_Scheduler_Setup.md)** - 매일 새벽 2시 자동 실행

```bash
# 제공된 배치 파일 사용
run_daily_scraping.bat
```

#### 주요 기능:
- ✅ 자동 환경 검증 및 오류 처리
- ✅ 상세한 실행 로그 및 결과 확인
- ✅ 수동/자동 실행 모드 지원
- ✅ 로그 파일 및 데이터베이스 상태 확인

### 🐧 Linux/Mac Cron
```bash
# crontab 편집
crontab -e

# 매일 새벽 2시 실행 (Windows와 동일한 시간)
0 2 * * * cd "/path/to/trend-analyzer" && source venv/bin/activate && python run_trend_analysis.py
```

## 🛠 기술 스택

- **Python 3.8+** (가상환경 지원)
- **Playwright**: 웹 스크래핑 및 브라우저 자동화
- **BeautifulSoup4**: HTML 파싱
- **Pandas**: 데이터 처리 및 표시
- **SQLite**: 최적화된 데이터베이스 (인덱스 포함)
- **구조화된 로깅**: 파일 기반 로깅 시스템

## ⚠️ 주의사항

1. **웹 스크래핑 정책**: TikTok과 YouTube의 서비스 약관을 준수하세요
2. **API 제한**: 과도한 요청으로 인한 차단을 방지하기 위해 적절한 딜레이가 설정되어 있습니다
3. **브라우저 리소스**: Playwright는 실제 브라우저를 사용하므로 시스템 리소스를 많이 사용합니다
4. **데이터 개인정보**: 수집된 데이터는 공개 가능한 트렌드 정보만 포함합니다

## 🆕 최신 개선사항 (v2.0)

### 🚀 성능 최적화
- **데이터베이스 스키마 개선**: JSON → 구조화된 숫자 컬럼으로 100-1000배 성능 향상
- **인덱스 최적화**: 대용량 데이터 처리를 위한 포괄적인 인덱스 시스템
- **NULL 값 처리**: 데이터 일관성을 위한 기본값 설정

### 📊 로깅 시스템
- **중앙화된 로깅**: 272개 print문을 구조화된 로깅으로 전환
- **파일 기반 로그**: 일별 로그 파일 자동 생성 및 관리
- **에러 추적**: 상세한 에러 로그 및 디버깅 정보

### 🔧 데이터베이스 마이그레이션 도구
- `scripts/improve_database_schema.py`: 기존 데이터를 안전하게 새 스키마로 이전
- `scripts/fix_business_approval_column.py`: NULL 값 문제 해결
- `scripts/optimize_database_indexes.py`: 성능 최적화 인덱스 생성

## 📈 활용 사례

- **🎼 음악 산업 분석**: 플랫폼별 음악 트렌드 비교 분석
- **📊 마케팅 인사이트**: 바이럴 성장 패턴 파악 및 예측
- **🎬 콘텐츠 전략**: 데이터 기반 인기 음원 콘텐츠 기획
- **📈 시장 조사**: 실시간 음악 트렌드 변화 모니터링
- **🔢 정량적 분석**: 조회수, 순위 변화 등 숫자 기반 분석

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

## 📝 업데이트 히스토리

### 🆕 v0.4 - 고급 UGC 분석 및 리포트 시스템 (2025-01-14)
#### 🚀 주요 신기능
- **📊 Enhanced HTML 리포트**: UGC 카운트와 해시태그 Top3가 포함된 고급 시각화 리포트
- **🔄 통합 데이터베이스**: UGC 카운트 자동 저장 및 해시태그 연동 시스템
- **🎯 스마트 스크래퍼**: `--save-db` 옵션으로 수집과 동시에 데이터베이스 저장
- **📈 실시간 메트릭**: TikTok/YouTube 동영상 개수 실시간 추적

#### 🛠️ 기술적 개선
- **스크래퍼 확장**: `tiktok_ugc_counter.py`, `youtube_ugc_counter.py`에 DB 저장 기능 추가
- **데이터베이스 스키마 확장**: `youtube_ugc_count`, `tiktok_ugc_count` 컬럼 활용
- **해시태그 테이블 완성**: `song_hashtags` 테이블로 곡별 해시태그 Top10 저장
- **리포트 생성기**: `generate_enhanced_report.py`로 종합 분석 리포트 제공

#### 🎨 새로운 사용법
```bash
# UGC 데이터 수집 (데이터베이스 저장 포함)
python src/scrapers/tiktok_ugc_counter.py "https://www.tiktok.com/music/x-ID" --save-db
python src/scrapers/youtube_ugc_counter.py "https://www.youtube.com/source/ID/shorts" --save-db

# 향상된 HTML 리포트 생성
python generate_enhanced_report.py
```

#### 📋 리포트에 포함되는 정보
- **TikTok Popular/Breakout**: 순위, 곡정보, UGC 동영상 수, 비즈니스 승인 태그, 해시태그 Top3
- **YouTube Shorts**: 순위, 곡정보, UGC 동영상 수, 급상승/신곡 태그
- **반응형 디자인**: 모바일/데스크톱 최적화된 현대적 UI

#### 🎯 비즈니스 가치
- **정량적 분석**: 실제 UGC 생성량으로 바이럴 정도 측정
- **해시태그 인사이트**: 곡별 주요 해시태그로 마케팅 전략 수립
- **트렌드 예측**: UGC 증가율과 해시태그 패턴으로 미래 인기도 예측
- **경쟁 분석**: 플랫폼별 성과 비교 및 최적 전략 도출

### 🆕 v0.3 - 해시태그 트렌드 분석 (2025-01-13)
#### 🏷️ 주요 기능 추가
- **TikTok 해시태그 수집**: 각 음원별 상위 10개 해시태그와 빈도수 수집
- **양방향 검색 시스템**: 해시태그로 음원 찾기, 음원으로 해시태그 찾기
- **해시태그 트렌드 분석**: 음원별 해시태그 패턴 및 장르별 특성 분석

#### 🔧 기술적 개선
- `tiktok_ugc_counter.py` 확장: 비디오 개수 + 해시태그 동시 수집
- `song_hashtags` 테이블 추가: 해시태그 빈도수 및 순위 저장
- `collect_song_hashtags.py` 스크립트: 배치 해시태그 수집 도구
- 해시태그 관련 데이터베이스 인덱스 최적화

##### 📊 분석 가능 데이터
- 음원별 주요 해시태그 Top 10 (빈도수 포함)
- 해시태그별 인기 음원 랭킹
- 장르별 해시태그 패턴 (예: K-pop → #kpop, #dance)
- 바이럴 해시태그 트렌드 (#fyp, #viral 등)

#### 🎯 활용 사례
- **음악 마케팅**: 해시태그 기반 콘텐츠 전략 수립
- **트렌드 예측**: 해시태그 패턴을 통한 바이럴 가능성 분석  
- **장르 분석**: 음악 스타일별 해시태그 선호도 파악
- **콘텐츠 기획**: 인기 해시태그 조합 발굴

### v0.2 - 성능 최적화 및 프로덕션 준비 (2024년)
- 데이터베이스 스키마 개선 (JSON → 구조화된 컬럼)
- 포괄적인 로깅 시스템 구축 (272개 print문 → 구조화된 로그)
- Windows 자동화 설정 및 배치 스크립트
- 데이터베이스 인덱스 최적화 (100-1000배 성능 향상)

### v0.1 - 초기 릴리즈
- TikTok, YouTube 음악 트렌드 수집
- UGC 동영상 개수 추적
- 기본 데이터베이스 스키마

---

**⭐ 이 프로젝트가 도움이 되셨다면 스타를 눌러주세요!**