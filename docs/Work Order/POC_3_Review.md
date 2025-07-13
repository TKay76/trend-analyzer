# PoC Review: YouTube Music Shorts Popular Songs Data Scraping (`youtube_music_scraper.py`)

## 1. 기능 요약

`youtube_music_scraper.py` 스크립트는 YouTube Music의 'Charts & Insights' 페이지에서 'Daily Shorts Popular Songs' 섹션의 세 가지 카테고리('Most popular (Trending)', 'Biggest movers (Top rising)', 'Highest debut (Most popular new releases)')에서 음악 랭킹 데이터를 성공적으로 스크래핑하여 구조화된 JSON 형태로 출력하는 기능을 구현했습니다.

주요 기능은 다음과 같습니다:
- **대상 URL:** `https://charts.youtube.com/charts/TopShortsSongs/kr/daily`에 직접 접근하여 한국 일일 차트 데이터를 수집합니다.
- **동적 UI 상호작용:** 드롭다운 메뉴를 통해 세 가지 카테고리를 순차적으로 선택하며 각각의 데이터를 스크래핑합니다.
- **무한 스크롤 처리:** 페이지 전체 콘텐츠를 로드하기 위한 자동 스크롤링 로직을 구현했습니다.
- **데이터 추출:** 각 음악 항목에서 랭크, 제목, 아티스트, 썸네일 URL, 일일 조회수 변동 지표를 추출합니다.
- **아티스트 이름 정리:** 중복 제거와 다양한 구분자 처리를 위한 `clean_artist_name()` 함수를 구현하여 데이터 품질을 향상시켰습니다.

이 PoC는 YouTube Music 플랫폼에서 Shorts 관련 음악 트렌드 데이터를 기술적으로 안정적으로 수집할 수 있음을 성공적으로 검증했습니다.

## 2. 기술적 성과 및 해결된 문제

### 2.1. Playwright 환경 문제 해결
- **문제:** 초기에 `playwright` 브라우저 실행 실패 및 타임아웃 오류가 반복적으로 발생했습니다.
- **해결:** `playwright install-deps` 명령어를 통한 시스템 종속성 설치로 환경 문제를 완전히 해결했습니다.

### 2.2. 복잡한 UI 상호작용 구현
- **드롭다운 선택 최적화:** 각 카테고리 선택 시 적절한 대기 시간(`wait_for_timeout`, `wait_for_load_state`)과 요소 가시성 확인을 통해 안정적인 UI 상호작용을 구현했습니다.
- **네트워크 상태 모니터링:** `networkidle` 상태 대기를 통해 동적 콘텐츠 로딩 완료를 정확히 감지했습니다.

### 2.3. 데이터 품질 개선
- **아티스트 이름 중복 해결:** 정규표현식과 세트 기반 중복 제거 로직을 통해 "Connie Francis Connie Francis"와 같은 중복 문제를 대폭 개선했습니다.
- **다양한 구분자 처리:** featuring, &, 쉼표 등 다양한 아티스트 구분자를 정확히 파싱하도록 구현했습니다.

## 3. 향후 과제 및 발전 방향

### 3.1. 아티스트 이름 파싱 완전성 확보
- **잔여 중복 문제:** 일부 아티스트 이름에서 여전히 중복이 발생하고 있어, YouTube Music의 HTML 구조를 더 정밀하게 분석하여 근본적인 해결책이 필요합니다.
- **복합 아티스트명 처리:** 그룹명과 개별 멤버명이 혼재된 경우, 브랜드명과 아티스트명이 함께 표시되는 경우 등에 대한 더 정교한 파싱 로직이 필요합니다.

### 3.2. 견고성 및 확장성 강화
- **headless 모드 전환:** 현재 디버깅을 위해 `headless=False`로 설정되어 있으나, 프로덕션 환경에서는 `headless=True`로 전환하여 리소스 효율성을 높여야 합니다.
- **셀렉터 견고성:** YouTube Music의 UI 변경에 대비하여 CSS 셀렉터의 견고성을 지속적으로 모니터링하고, 필요시 XPath나 텍스트 기반 셀렉터 대안을 준비해야 합니다.
- **오류 처리 강화:** 네트워크 오류, 요소 찾기 실패, 드롭다운 선택 실패 등에 대한 더 구체적이고 복구 가능한 예외 처리 로직을 추가해야 합니다.

### 3.3. 데이터 활용 및 저장
- **데이터베이스 연동:** 현재 JSON 콘솔 출력에서 데이터베이스(PostgreSQL, MongoDB 등) 저장으로 확장하여 데이터 영속성과 분석 활용성을 높여야 합니다.
- **메트릭 파싱 고도화:** `daily_metrics` 필드의 "-", 숫자 등 다양한 형태를 표준화된 형식으로 파싱하는 `parse_metric()` 함수 활용을 확대해야 합니다.
- **스케줄링 자동화:** 일일 차트 데이터의 특성상 정기적인 수집을 위한 cron job이나 스케줄러 연동이 필요합니다.

### 3.4. 성능 최적화
- **수집 효율성:** 현재 약 72개 항목(Trending 50 + Top rising 21 + New releases 1)을 수집하는데, 브라우저 인스턴스 재사용이나 세션 유지를 통해 수집 속도를 개선할 수 있습니다.
- **메모리 최적화:** 대용량 HTML 파싱 시 메모리 사용량 최적화와 가비지 컬렉션 효율성을 고려해야 합니다.

## 4. 전체 프로젝트에서의 위치

이 PoC는 'Short-form Music Trend Analysis Service'의 세 번째 데이터 소스로서 YouTube Music Shorts 트렌드 데이터를 제공하며, TikTok Sound 데이터(PoC 1)와 TikTok Creative Center 데이터(PoC 2)와 함께 종합적인 숏폼 음악 트렌드 분석을 위한 핵심 구성 요소로 성공적으로 기능할 것으로 평가됩니다.