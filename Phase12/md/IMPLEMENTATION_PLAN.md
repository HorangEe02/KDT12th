# 🛠️ 원정 응원 플래너 — 상세 구현 계획 (Claude Code 기반)

> **목표**: 5일간 Streamlit 기반 AI 원정 응원 플래너를 완성하고 발표까지 마친다.
> **실행 도구**: Claude Code (Anthropic)
> **총 실작업 시간 추정**: 약 12시간 (Day 4 4시간 + Day 5 8시간)

---

## 📋 전체 Phase 개요

| Phase | 이름 | 예상 시간 | 담당 역할 | 완료 조건 |
|---|---|---|---|---|
| **Phase 0** | 프로젝트 부트스트랩 | 30분 | 전원 | `streamlit run app.py` 실행 확인 |
| **Phase 1** | 데이터 파이프라인 구축 | 2시간 | 데이터 엔지니어 | 모든 CSV 로딩 성공 |
| **Phase 2** | Streamlit UI 골격 | 2시간 | 프론트/UX | 5개 탭 + 사이드바 필터 작동 |
| **Phase 3** | 지도 & 시각화 | 2시간 | 지도·시각화 | 경기장 마커·경로·차트 렌더링 |
| **Phase 4** | AI 기능 구현 | 3시간 | AI·분석 | 챗봇 + 승률 예측 + Multi-Agent 응답 |
| **Phase 5** | 브랜딩·배포·발표 | 2시간 | 전원 | 배포 URL + 발표 자료 완성 |

**원칙**: 각 Phase는 **독립적으로 머지 가능**하도록 설계했습니다. Phase 2~4는 병렬 작업 가능, Phase 5는 전원 참여.

---

## 🚀 Phase 0. 프로젝트 부트스트랩 (30분)

### 목표
개발 환경·저장소·디렉토리 구조를 표준화하여 팀원 간 충돌 없이 개발할 수 있는 기반을 만든다.

### 선행 조건
- 팀원 GitHub 계정 확보
- Python 3.10+ 설치
- Claude Code 설치 완료
- API Key 준비: 공공데이터포털(TourAPI·기상청), 카카오 개발자, OpenAI 또는 Gemini

### 구체 작업

**0-1. Git 저장소 & 디렉토리 구조 세팅**

최종 디렉토리 구조는 다음과 같습니다.

```
away-game-companion/
├── app.py                      # Streamlit 엔트리 포인트
├── requirements.txt
├── README.md
├── IMPLEMENTATION_PLAN.md
├── CLAUDE.md                   # Claude Code 컨텍스트 문서
├── .env.example
├── .gitignore
├── data/
│   ├── kbo_schedule_2026.csv
│   ├── stadiums.csv
│   ├── team_stats_10yr.csv
│   └── poi_cache/              # TourAPI 응답 캐시
├── src/
│   ├── __init__.py
│   ├── config.py               # 상수·경로 관리
│   ├── data_loader.py          # CSV·API 로더 (@st.cache_data)
│   ├── api/
│   │   ├── tour_api.py
│   │   ├── kakao_map.py
│   │   └── weather_api.py
│   ├── ui/
│   │   ├── sidebar.py
│   │   ├── hero.py
│   │   └── tabs/
│   │       ├── tab1_games.py
│   │       ├── tab2_map.py
│   │       ├── tab3_places.py
│   │       ├── tab4_ai.py
│   │       └── tab5_badges.py
│   ├── viz/
│   │   ├── folium_map.py
│   │   └── plotly_charts.py
│   ├── ai/
│   │   ├── agents.py           # Multi-Agent 오케스트레이션
│   │   ├── tools.py            # Function Calling 도구 정의
│   │   ├── rag.py              # 지식베이스 검색
│   │   └── predict.py          # 승률 예측 모델
│   └── utils.py
├── models/
│   └── win_rate_model.pkl
├── assets/
│   ├── css/style.css
│   └── images/
└── tests/
    └── test_data_loader.py
```

**0-2. `CLAUDE.md` 작성** — Claude Code가 프로젝트 맥락을 자동으로 읽도록 하는 필수 문서

**0-3. `requirements.txt` 초기화**
```
streamlit>=1.40
streamlit-folium>=0.27
folium
pandas
plotly
scikit-learn
requests
httpx
openai        # 또는 google-genai
langchain
langgraph
chromadb
python-dotenv
```

**0-4. `.gitignore` 및 `.env.example`** — API 키 보호

### Claude Code 프롬프트 예시

```
/init

프로젝트 이름은 away-game-companion이고, README.md를 읽은 뒤
IMPLEMENTATION_PLAN.md의 Phase 0에 명시된 디렉토리 구조대로
빈 파일과 디렉토리를 만들어줘. requirements.txt와 .gitignore,
.env.example도 같이 생성하고, CLAUDE.md에는 이 프로젝트의
목표·주요 기술 스택·개발 컨벤션을 정리해줘.
```

### 검증 기준
- [ ] `git status`에 모든 필수 파일이 생성됨
- [ ] `pip install -r requirements.txt` 성공
- [ ] `streamlit run app.py`로 빈 "Hello" 페이지 뜨기
- [ ] 팀원 전원이 `git clone` 후 동일 환경 구축 확인

---

## 📦 Phase 1. 데이터 파이프라인 구축 (2시간)

### 목표
공공데이터 4종(KBO 일정·구장·팀 전적·관광 POI)을 수집하고 표준화된 CSV/JSON으로 저장하여 UI 레이어가 즉시 사용할 수 있게 만든다.

### 구체 작업

**1-1. KBO 2026 경기일정 수집 (30분)**
- 출처: [KBO 공식](https://www.koreabaseball.com/schedule/schedule.aspx) / 나무위키 보조
- 방법: 나무위키 2026 KBO 리그 페이지에서 표 파싱 → `data/kbo_schedule_2026.csv`
- 스키마: `game_id`, `date`, `day_of_week`, `home_team`, `away_team`, `stadium`, `start_time`

**1-2. 구장 좌표 데이터 (15분)**
- 10개 구장 위경도 수기 입력 (카카오맵 좌표 조회)
- `data/stadiums.csv`: `stadium_name`, `home_team`, `city`, `lat`, `lng`, `capacity`, `subway_station`

**1-3. 팀 전적 데이터 (30분)**
- KBO 기록실에서 팀별 최근 10년 성적 수집 (스크래핑 또는 수기)
- `data/team_stats_10yr.csv`: 승률 예측 모델 학습용 피처

**1-4. TourAPI 연동 스크립트 (30분)**
- `src/api/tour_api.py`에 `get_nearby_places(lat, lng, radius, content_type)` 함수 구현
- 각 구장 반경 3km 내 맛집·숙박·관광지 사전 캐싱 → `data/poi_cache/*.json`
- `@st.cache_data(ttl=3600)` 적용

**1-5. 기상청 단기예보 연동 (15분)**
- `src/api/weather_api.py`에 `get_forecast(lat, lng, date)` 함수
- 경기일 우천 확률 반환

### 산출물
- `data/` 디렉토리 내 4개 CSV + POI JSON 캐시
- `src/data_loader.py` — 통합 로더 함수 `load_all_data()`
- `src/api/tour_api.py`, `src/api/weather_api.py`

### Claude Code 프롬프트 예시

```
Phase 1의 1-4를 진행해줘. src/api/tour_api.py에 한국관광공사 TourAPI를
호출하는 클라이언트를 만들어줘. 요구사항:

1. base URL은 http://apis.data.go.kr/B551011/KorService1
2. 엔드포인트 /locationBasedList1 사용
3. .env의 TOUR_API_KEY 읽기
4. 함수 시그니처: get_nearby_places(lat: float, lng: float, radius: int = 3000,
   content_type: int = 39) -> list[dict]
5. content_type: 음식점=39, 숙박=32, 관광지=12
6. requests 대신 httpx 사용, 타임아웃 10초
7. 실패 시 빈 리스트 반환, 로깅은 print 대신 logging.warning

그리고 scripts/cache_poi.py를 만들어서 data/stadiums.csv를 읽어
모든 구장 반경의 POI를 data/poi_cache/{stadium_name}_{type}.json으로
저장하는 일회성 스크립트도 작성해줘.
```

### 검증 기준
- [ ] `python -c "from src.data_loader import load_all_data; print(load_all_data())"` 성공
- [ ] 구장 10곳 × 3개 카테고리 = 30개 JSON 캐시 파일 생성
- [ ] 각 CSV에 결측치 없음 (pandas `.isna().sum()` 체크)

---

## 🎨 Phase 2. Streamlit UI 골격 (2시간)

### 목표
사이드바 필터와 5개 탭 구조를 완성하여, 데이터는 비어있어도 **전체 네비게이션이 작동**하는 상태를 만든다.

### 구체 작업

**2-1. `app.py` 메인 엔트리 (30분)**
- `st.set_page_config()` 설정 (제목, 아이콘, layout="wide")
- 헤더 섹션 (로고·프로젝트명)
- 사이드바 + 5개 탭 레이아웃
- `session_state` 초기화 블록

**2-2. 사이드바 필터 (30분)**
- `src/ui/sidebar.py`에 `render_sidebar() -> dict` 함수
- 필터 항목:
  - 응원팀 `st.selectbox` (10개 구단)
  - 원정 기간 `st.date_input` (range)
  - 예산 `st.slider` (10~100만원)
  - 인원 구성 `st.radio` (혼자/커플/가족)
  - 이동수단 `st.radio` (KTX/자차/버스)
- 반환 dict를 session_state에 저장

**2-3. 탭 1: 경기 & 예측 (30분)**
- 사이드바 필터로 원정 경기 DataFrame 필터링
- 경기 리스트 표시 (`st.dataframe`)
- 선택된 경기 상세 카드 (`st.columns` 분할)

**2-4. 탭 2~5 스캐폴딩 (30분)**
- 각 탭은 `render()` 함수 하나만 export
- Placeholder 내용으로 채우기 (`st.info("Tab 3 coming soon")`)
- Phase 3, 4에서 점진적 구현

### 산출물
- `app.py` (완성도 60%, 네비게이션 작동)
- `src/ui/sidebar.py`, `src/ui/tabs/*.py` 5개 파일

### Claude Code 프롬프트 예시

```
Phase 2의 2-2 작업을 진행해줘. src/ui/sidebar.py를 만들고,
render_sidebar() 함수에서 다음을 구현해줘:

- st.sidebar.selectbox로 응원팀 선택 (10개 구단, 기본값 LG 트윈스)
- st.sidebar.date_input으로 원정 기간 range 입력
- st.sidebar.slider로 예산 10~100 (단위 만원, step 5)
- st.sidebar.radio로 인원 구성 3지선다
- st.sidebar.radio로 이동수단 3지선다
- "코스 생성" 버튼 클릭 시 st.session_state["filters"]에 dict로 저장

그리고 app.py에서 이 함수를 호출해서 받은 값을
현재 선택된 조건 요약으로 메인 영역 상단에 표시해줘.
```

### 검증 기준
- [ ] 5개 탭 모두 클릭 시 오류 없이 전환
- [ ] 사이드바 필터 변경 시 메인 영역에 즉시 반영
- [ ] session_state 값이 탭 전환 후에도 유지됨

---

## 🗺️ Phase 3. 지도 & 시각화 (2시간)

### 목표
Folium 인터랙티브 지도와 Plotly 차트를 완성하여, 원정 동선을 시각적으로 확인할 수 있게 한다.

### 구체 작업

**3-1. Folium 지도 컴포넌트 (60분)**
- `src/viz/folium_map.py`에 `create_away_game_map(game_info, places) -> folium.Map`
- 레이어 구성:
  - 🏟️ 경기장 (빨간 야구 아이콘)
  - 🍽️ 맛집 (주황 포크 아이콘)
  - 🏨 숙소 (파랑 침대 아이콘)
  - 🎡 관광지 (녹색 카메라 아이콘)
- `folium.FeatureGroup`으로 레이어 토글 지원
- `st_folium()`으로 탭 2에 렌더링, 마커 클릭 이벤트 → 우측 상세 패널

**3-2. 카카오모빌리티 경로 표시 (30분)**
- `src/api/kakao_map.py`에 `get_directions(origin, destination, waypoints)` 함수
- 응답의 vertexes 배열 → `folium.PolyLine`으로 그리기
- 총 소요시간·거리·통행료 요약 박스

**3-3. Plotly 차트 2종 (30분)**
- `src/viz/plotly_charts.py`:
  - `plot_away_win_rate(team, stats)` — 구단별 원정 승률 막대그래프
  - `plot_places_scatter(places)` — 평점 × 거리 산점도 (탭 3)
- Plotly Express 사용, 한글 폰트 대응

### 산출물
- `src/viz/folium_map.py`, `plotly_charts.py`
- `src/api/kakao_map.py`
- 탭 2와 탭 3의 실제 데이터 렌더링

### Claude Code 프롬프트 예시

```
Phase 3의 3-1을 구현해줘. src/viz/folium_map.py를 만들고
create_away_game_map(game: dict, places: dict[str, list]) -> folium.Map
함수를 작성해.

요구사항:
- 초기 중심: 경기장 좌표, zoom_start=14
- tiles: OpenStreetMap
- 4개 FeatureGroup: 경기장/맛집/숙소/관광지
- 경기장 마커: folium.Marker with icon=folium.Icon(color='red', icon='baseball', prefix='fa')
- 나머지 마커도 각각 다른 색상·아이콘
- Popup에는 이름, 평점, 거리 표시
- folium.LayerControl() 추가

그리고 src/ui/tabs/tab2_map.py에서 이 함수를 호출하고
st_folium(m, width=800, height=600, returned_objects=["last_object_clicked"])로 렌더링,
반환값 last_object_clicked가 있으면 우측 columns에 상세 정보 표시해줘.
```

### 검증 기준
- [ ] 탭 2에서 지도가 렌더링되고 레이어 토글 작동
- [ ] 마커 클릭 시 popup 및 우측 상세 정보 표시
- [ ] 경로 폴리라인이 지도 위에 그려짐
- [ ] Plotly 차트 2개가 반응형으로 렌더링

---

## 🤖 Phase 4. AI 기능 구현 (3시간)

### 목표
승률 예측 모델, 기본 LLM 챗봇, Multi-Agent 오케스트레이션을 단계적으로 구축한다. **시간이 부족하면 기본 챗봇까지만 구현**하고 Multi-Agent는 Phase 5 이후 확장.

### 구체 작업

**4-1. 승률 예측 모델 (30분)**
- `src/ai/predict.py`에 scikit-learn 로지스틱 회귀
- 피처: 홈팀·원정팀·홈팀 최근 10경기 승률·원정팀 최근 10경기 승률·헤드투헤드 승률
- 학습 → `models/win_rate_model.pkl` 저장
- `predict_win_rate(home, away) -> float` 함수

**4-2. 기본 LLM 챗봇 (60분)** *(MVP)*
- `src/ui/tabs/tab4_ai.py`에 `st.chat_message` + `st.chat_input` 구현
- OpenAI API 호출 (streaming)
- `session_state["messages"]`에 대화 기록 저장
- System Prompt: "당신은 KBO 원정 응원 플래너입니다..."
- 사이드바 필터 값을 system prompt에 자동 주입

**4-3. Function Calling 도구 정의 (45분)** *(고도화)*
- `src/ai/tools.py`에 8개 도구 함수 + JSON Schema
  - `search_game`, `get_weather`, `find_restaurants`, `find_accommodation`
  - `get_route`, `predict_win_rate`, `save_user_preference`, `get_badge_progress`
- OpenAI `tools` 파라미터로 전달

**4-4. Multi-Agent 오케스트레이션 (45분)** *(최고급, 시간 남을 때만)*
- `src/ai/agents.py`에 LangGraph 기반 5개 에이전트
  - Supervisor, Schedule, Transport, Place, Strategist
- `StateGraph` 정의, 에이전트 간 메시지 전달
- 최종 답변 생성 로그를 UI에 시각화

### 산출물
- `src/ai/predict.py`, `agents.py`, `tools.py`
- `models/win_rate_model.pkl`
- 탭 4에서 작동하는 챗봇

### Claude Code 프롬프트 예시

```
Phase 4의 4-2 (기본 챗봇)부터 시작해줘. src/ui/tabs/tab4_ai.py를
다음처럼 구현해:

1. st.session_state["messages"] 초기화 (첫 메시지: 어시스턴트 환영 인사)
2. 이전 메시지 전체 렌더링 (for msg in messages: st.chat_message...)
3. st.chat_input("원정 계획을 알려드릴게요!") 입력 받기
4. OpenAI gpt-4o-mini 호출, stream=True로 스트리밍
5. System prompt는 src/ai/prompts.py에서 import, 사이드바 필터
   (st.session_state["filters"])를 동적으로 주입
6. .env의 OPENAI_API_KEY 사용
7. try-except로 API 에러 시 st.error 표시

src/ai/prompts.py도 같이 만들어서 SYSTEM_PROMPT_BASIC 상수를 정의하고,
이 상수 안에 "당신은 KBO 원정 응원 전문가"라는 페르소나와
응원팀·기간·예산 등 필터 정보를 포맷팅할 수 있는 {team}, {budget} 같은
placeholder를 넣어줘.
```

### 검증 기준
- [ ] 챗봇에 "광주 원정 1박 2일" 입력 시 LLM이 맥락에 맞는 답변 생성
- [ ] 승률 예측값이 탭 1 카드에 표시됨
- [ ] (선택) Multi-Agent 호출 시 Thought-Action-Observation 로그 UI 노출

---

## ✨ Phase 5. 브랜딩 · 배포 · 발표 준비 (2시간)

### 목표
UX 마감, Streamlit Cloud 배포, 발표 자료·데모 시나리오까지 완성한다.

### 구체 작업

**5-1. 브랜딩 & UX 마감 (45분)**
- `assets/css/style.css`에 팀 컬러 테마 (선택된 응원팀 컬러로 헤더 변경)
- `src/ui/hero.py`에 HTML 히어로 섹션 (`st.components.v1.html`)
- 뱃지 시스템 UI (탭 5): 10개 구장 컴플릿 진행률 시각화
- 로딩 spinner, 빈 상태 메시지, try-except 예외 처리 전반 점검

**5-2. Streamlit Cloud 배포 (30분)**
- `secrets.toml`에 API 키 설정
- GitHub → Streamlit Cloud 연결
- 배포 URL 확보 후 README에 추가

**5-3. 발표 자료 작성 (45분)**
- 슬라이드 10장 이내 구성:
  1. 표지
  2. 문제 정의 (원정 응원러 Pain Point)
  3. 시장 근거 (MZ 50%, 직관 100만)
  4. 서비스 소개 (한 줄 + 타깃)
  5. 핵심 기능 시연 (스크린샷)
  6. 기술 아키텍처 (Multi-Agent 다이어그램)
  7. 수익 모델 8단 구조
  8. 사회적 가치 (지역경제 활성화)
  9. 개발 후기 & 한계
  10. Q&A

- 데모 시나리오 3분 스크립트 작성

### 산출물
- 배포된 Streamlit 앱 URL
- 발표 PPT/PDF
- 데모 시나리오 스크립트

### Claude Code 프롬프트 예시

```
Phase 5의 5-1을 진행해줘. assets/css/style.css에 다음을 구현해:

1. 전체 폰트를 'Pretendard' 또는 'Noto Sans KR'로 변경
2. 팀 컬러 변수 정의 (LG=자홍, KIA=빨강, 두산=남색 등 10개 구단)
3. .hero-section 클래스에 그라디언트 배경 + 패딩
4. .stadium-badge 클래스에 야구공 모양 원형 뱃지 스타일
5. Streamlit 기본 스타일은 유지하되 헤더·버튼만 커스텀

그리고 src/ui/hero.py에 render_hero(selected_team: str) 함수를 만들어서
st.components.v1.html()로 히어로 HTML을 렌더링하되,
선택된 팀 컬러가 그라디언트에 반영되도록 해줘.
```

### 검증 기준
- [ ] 배포 URL에서 모든 기능 작동
- [ ] 모바일 브라우저에서 레이아웃 깨지지 않음
- [ ] 발표 스크린샷 촬영 완료
- [ ] 팀원 전원 데모 시연 리허설 1회 이상

---

## 🎯 Claude Code 활용 팁

### ① `CLAUDE.md`를 프로젝트 컨텍스트의 단일 진실로 관리
프로젝트 루트의 `CLAUDE.md`는 Claude Code가 매 세션 자동으로 읽는 문서입니다. 다음 정보를 명시해두면 프롬프트가 훨씬 짧아집니다.
- 프로젝트 개요 1~2문장
- 주요 기술 스택 및 제약 사항
- 디렉토리 구조
- 명명 규칙 (예: 함수는 snake_case, 한글 주석 허용)
- 테스트·린트 실행 명령어
- "하지 말아야 할 것" (예: `print` 대신 `logging` 사용)

### ② 작업 단위는 "한 파일·한 기능" 원칙으로 쪼개기
"Phase 3 전체 해줘"보다 "src/viz/folium_map.py의 create_away_game_map 함수를 구현해줘"가 훨씬 정확한 결과를 냅니다. 한 번에 2~3개 파일까지가 적정선입니다.

### ③ `/plan` 모드로 설계 먼저, 구현은 그다음
큰 작업은 `/plan` 슬래시 커맨드로 먼저 계획을 세우고 리뷰한 뒤 실행에 들어가세요. 잘못된 방향으로 500줄 쓰는 사고를 방지합니다.

### ④ 팀원 간 병렬 작업 전략
Phase 2~4는 다음처럼 병렬 가능합니다.
- **프론트 담당**: Phase 2 (UI 골격)
- **지도 담당**: Phase 3 (Phase 1의 stadiums.csv만 있으면 시작 가능)
- **AI 담당**: Phase 4 (모델 학습은 Phase 1과 독립)
- **데이터 담당**: Phase 1 마무리 + 데이터 품질 QA

각자 별도 브랜치에서 작업 → PR 기반 머지.

### ⑤ 테스트와 커밋은 Phase 단위로
각 Phase 종료 시 `pytest` 또는 최소한 수동 시연을 하고 커밋 메시지를 `feat(phase-3): add folium map component` 형태로 명확하게.

### ⑥ API 키 관리
`.env`는 절대 커밋하지 말고, `.env.example`에 어떤 키가 필요한지만 명시. Streamlit Cloud 배포 시에는 Secrets 관리 기능 사용.

---

## 👥 팀원 역할 × Phase 매핑

| 팀원 역할 | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 팀장 / 데이터 엔지니어 | ✅ 주도 | ✅ 주도 | 지원 | 지원 | - | ✅ 참여 |
| 프론트 / UX | ✅ 참여 | - | ✅ 주도 | 지원 | - | ✅ 주도 |
| 지도 · 시각화 | ✅ 참여 | 지원 | 지원 | ✅ 주도 | - | ✅ 참여 |
| AI · 분석 | ✅ 참여 | 지원 | - | - | ✅ 주도 | ✅ 참여 |

---

## ⚠️ 리스크 & 완화 전략

| 리스크 | 발생 확률 | 영향 | 완화 전략 |
|---|---|---|---|
| 공공데이터포털 API 승인 지연 | 중 | 높음 | 팀원 전원 첫날 오전 신청, 대체 더미 CSV 준비 |
| 카카오 API 쿼터 초과 | 낮음 | 중 | 경로 데이터 캐싱, 하드코딩 대체 경로 준비 |
| LLM API 비용 초과 | 중 | 중 | gpt-4o-mini 기본, 데모는 녹화 영상 보조 |
| Streamlit Cloud 배포 실패 | 낮음 | 높음 | 로컬 시연 영상 백업, 발표 당일 네트워크 안정화 |
| 팀원 간 Git 충돌 | 중 | 중 | 파일 단위 역할 분담, 매일 오전 main 브랜치 동기화 |
| 시간 부족 (Phase 4 AI) | 높음 | 중 | MVP(기본 챗봇)까지 필수, Multi-Agent는 선택 |

---

## ✅ 최종 체크리스트

### 기능 완성도
- [ ] 사이드바 필터 2개 이상 (요구: 2개) — **5개 구현 예정**
- [ ] `@st.cache_data` 적용
- [ ] Plotly 차트 2개 이상 (요구: 2개) — **2개 구현**
- [ ] 탭·컬럼·익스팬더 레이아웃 2개 이상 (요구: 2개) — **4개 이상 구현**
- [ ] 분석 결과 텍스트 해석 포함
- [ ] `session_state` 활용
- [ ] 예외 처리 (`try-except`)
- [ ] 데이터 없을 때 경고 메시지

### 제출물
- [ ] `app.py` 실행 파일
- [ ] `data/` 디렉토리 CSV 파일
- [ ] 발표 자료 (화면 시연 포함)
- [ ] `README.md` 완성본
- [ ] 배포 URL

### 발표 준비
- [ ] 각 팀원이 담당 부분 설명 가능
- [ ] 데모 시나리오 3분 스크립트 숙지
- [ ] 예상 질문 Q&A 리허설

---

*This plan is designed to be executed with Claude Code. Update as needed during sprint.*
*Last updated: 2026-04-17*
