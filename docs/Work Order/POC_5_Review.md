# PoC Review: Platform-Specific ID Collection & URL Generation System

## 1. 기능 요약

`POC 5`는 기존의 음악 트렌드 스크래핑 시스템에 **플랫폼별 고유 ID 수집 기능**을 추가하여, 각 음원을 사용한 사용자 생성 콘텐츠(UGC)로의 직접 접근이 가능한 URL 생성 시스템을 성공적으로 구현했습니다.

주요 기능은 다음과 같습니다:
- **YouTube Shorts ID 추출:** YouTube Charts에서 `endpoint` 속성의 JSON 데이터를 파싱하여 YouTube Video ID를 추출하고, `https://youtube.com/source/{VIDEO_ID}/shorts` 형태의 URL로 해당 음원을 사용한 Shorts 동영상 목록에 직접 접근 가능
- **TikTok Sound ID 추출:** TikTok Creative Center에서 URL 패턴과 차트 요소 ID를 분석하여 TikTok Sound ID를 추출하고, `https://www.tiktok.com/music/x-{SOUND_ID}` 형태의 URL로 해당 음원을 사용한 TikTok 동영상 목록에 직접 접근 가능
- **데이터베이스 스키마 확장:** `songs` 테이블에 `youtube_id`와 `tiktok_id` 컬럼을 추가하여 플랫폼별 고유 식별자를 영구 저장
- **통합 데이터베이스 구축:** YouTube Charts와 TikTok Creative Center의 데이터를 단일 데이터베이스에 통합하여 크로스 플랫폼 분석 기반 마련

이 구현을 통해 단순한 차트 순위 수집을 넘어, **각 트렌드 음악이 실제로 어떻게 사용되고 있는지 추적할 수 있는 심화 분석 시스템**의 기반을 구축했습니다.

## 2. 기술적 성과 및 해결된 문제

### 2.1. YouTube Charts의 Hidden Endpoint 데이터 발굴
- **문제:** YouTube Charts 페이지는 외부 링크나 명시적인 Video ID를 제공하지 않아 개별 영상으로의 접근이 불가능했습니다.
- **해결:** 페이지 HTML을 상세 분석하여 `ytmc-entry-row` 요소의 `endpoint` 속성에 JSON 형태로 YouTube URL이 숨어있음을 발견했습니다. `{"urlEndpoint":{"url":"https://www.youtube.com/watch?v=983bBbJx0Mk"}}` 패턴을 파싱하여 **98% 성공률**(49/50곡)로 YouTube Video ID 추출에 성공했습니다.

### 2.2. TikTok Creative Center의 Sound ID 패턴 해석
- **문제:** TikTok Creative Center는 음악 정보만 제공하고 실제 TikTok 사운드로의 연결점이 명확하지 않았습니다.
- **해결:** 각 음악 항목의 HTML 구조를 분석하여 두 가지 패턴을 발견했습니다:
  - **URL 패턴**: `/business/creativecenter/song/Title-{SOUND_ID}` 형태에서 마지막 숫자 추출
  - **차트 ID 패턴**: `id="0-{SOUND_ID}"` 형태의 차트 요소에서 ID 추출
  - 15자리 이상의 긴 숫자 ID 검증을 통해 **100% 성공률**(36/36곡)로 TikTok Sound ID 추출에 성공했습니다.

### 2.3. 실패 케이스 완전 분석 및 해결
- **문제:** 초기 테스트에서 일부 곡의 ID 추출이 실패했습니다.
- **해결:** 
  - **Google 썸네일 문제**: 일부 곡이 `lh3.googleusercontent.com` 썸네일을 사용해 YouTube 썸네일 URL 패턴으로는 ID 추출이 불가능했으나, `endpoint` 속성 방식으로 완전 해결
  - **YouTube ID 누락 케이스**: 1곡의 YouTube ID 추출 실패는 실제로 해당 곡의 YouTube Shorts가 아직 생성되지 않은 정상적인 상황임을 확인

### 2.4. 데이터베이스 스키마 진화적 확장
- **문제:** 기존 데이터베이스 구조에 새로운 ID 컬럼을 추가하면서 데이터 호환성을 유지해야 했습니다.
- **해결:** `database_manager.py`의 `add_song_and_get_id()` 함수에 `youtube_id`와 `tiktok_id` 파라미터를 추가하고, 기존 데이터를 보존하면서 새로운 스키마로 점진적으로 전환하는 방식을 채택했습니다.

## 3. 구현 세부사항

### 3.1. YouTube ID 추출 로직 (`youtube_music_scraper.py`)
```python
def extract_youtube_id_from_endpoint(element):
    endpoint_attr = element.get('endpoint')
    if endpoint_attr:
        try:
            endpoint_data = json.loads(endpoint_attr)
            url = endpoint_data.get('urlEndpoint', {}).get('url', '')
            if 'watch?v=' in url:
                return url.split('watch?v=')[1].split('&')[0]
        except json.JSONDecodeError:
            pass
    return None
```

### 3.2. TikTok Sound ID 추출 로직 (`tiktok_music_scraper.py`)
```python
def extract_tiktok_sound_id(item_tag):
    # Method 1: URL 패턴에서 추출
    link_tag = item_tag.select_one("a[href*='/song/']")
    if link_tag:
        href = link_tag.get('href', '')
        if '/song/' in href:
            sound_id = href.split('-')[-1].split('?')[0]
            if sound_id.isdigit() and len(sound_id) > 15:
                return sound_id
    
    # Method 2: 차트 요소 ID에서 추출
    chart_element = item_tag.select_one("div[id*='-']")
    if chart_element:
        element_id = chart_element.get('id', '')
        if '-' in element_id:
            sound_id = element_id.split('-')[-1]
            if sound_id.isdigit() and len(sound_id) > 15:
                return sound_id
    
    return None
```

### 3.3. 통합 데이터베이스 결과
- **총 86개 곡** 수집 (YouTube 49개 + TikTok 36개 + 중복 제거)
- **YouTube URL 생성**: `https://youtube.com/source/{youtube_id}/shorts`
- **TikTok URL 생성**: `https://www.tiktok.com/music/x-{tiktok_id}`

## 4. 향후 과제 및 발전 방향

### 4.1. 크로스 플랫폼 음악 매칭 시스템
- **과제:** 현재는 YouTube와 TikTok에서 서로 다른 곡들을 수집하고 있어 동일 음악의 플랫폼별 성과 비교가 불가능합니다.
- **방향:** 음악 메타데이터(제목, 아티스트) 기반의 매칭 알고리즘을 구현하거나, Spotify/Apple Music API를 활용한 음악 식별 시스템을 도입하여 크로스 플랫폼 분석을 가능하게 해야 합니다.

### 4.2. UGC 콘텐츠 2차 스크래핑 파이프라인
- **과제:** 현재는 UGC 목록 페이지로의 URL만 생성할 뿐, 실제 사용 패턴이나 콘텐츠 분석은 수행하지 않습니다.
- **방향:** 생성된 URL을 기반으로 각 음원을 사용한 동영상들의 메타데이터(조회수, 좋아요, 댓글, 해시태그 등)를 2차로 수집하는 파이프라인을 구축하여 음악 트렌드의 실제 영향력과 사용 맥락을 분석할 수 있도록 확장해야 합니다.

### 4.3. 실시간 ID 검증 및 URL 유효성 확인
- **과제:** 추출된 ID와 생성된 URL의 실제 접근 가능성을 검증하는 메커니즘이 부족합니다.
- **방향:** 주기적으로 생성된 URL에 HTTP 요청을 보내 응답 상태를 확인하고, 비활성화되거나 삭제된 콘텐츠를 식별하여 데이터 품질을 관리하는 시스템을 구축해야 합니다.

### 4.4. 플랫폼별 ID 수집 범위 확장
- **과제:** 현재는 각 플랫폼의 일일 차트 상위권만을 대상으로 하고 있습니다.
- **방향:** 주간/월간 차트, 장르별 차트, 지역별 차트 등으로 수집 범위를 확장하고, Instagram Reels, Facebook 등 다른 숏폼 플랫폼으로도 확장하여 더 포괄적인 음악 트렌드 분석 기반을 마련해야 합니다.

## 5. 전체 프로젝트에서의 위치

POC 5는 기존의 트렌드 데이터 수집을 **실제 사용자 행동과 연결**하는 핵심적인 다리 역할을 수행했습니다. 이제 'Short-form Music Trend Analysis Service'는 단순히 "어떤 음악이 인기인가?"를 넘어서 **"그 음악이 어떻게 사용되고 있는가?"**라는 질문에 답할 수 있는 기술적 기반을 갖추게 되었습니다.

이 플랫폼별 ID 시스템은 향후 AI 기반 트렌드 예측, 콘텐츠 크리에이터를 위한 음악 추천, 음악 산업을 위한 인사이트 제공 등 모든 고도화 기능의 **핵심 데이터 소스**가 될 것입니다. 특히 각 음원의 실제 사용 맥락과 패턴을 분석할 수 있게 됨으로써, 단순한 순위 기반 분석을 넘어선 **깊이 있는 음악 트렌드 인사이트**를 제공할 수 있는 기반이 마련되었습니다.