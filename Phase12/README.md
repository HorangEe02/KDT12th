# ⚾ 원정 응원 플래너 (Away Game Companion)

> **"내 팀 원정 경기 하나만 고르면, 티켓·교통·맛집·숙소·관광을 AI가 한 번에 짜주는 스포츠 관광 플래너"**

KBO 10개 구단, 전국 8개 도시, 연간 720경기 — 원정 응원러를 위한 올인원 웹 서비스입니다.

---

## 🚀 Phase 6 — Live (Next.js 16 + Firebase App Hosting)

**배포 완료** (2026-04-17) — 전 세션 smoke test 통과 ✅

```
┌──────────────────────────────────────────────────────────────┐
│  Browser (React 19.2 · Tailwind v4 · Zustand · React-Leaflet) │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS · SSR · UIMessageStream
┌───────────────────────────┴──────────────────────────────────┐
│  Firebase App Hosting (Next.js 16 / Cloud Run asia-east1)     │
│  ├ App Router: /matches /map /places /ai /badges /share/[id]  │
│  ├ API Routes: /api/{predict,route,chat,plans}                │
│  └ Static data: /public/data/*.json (schedule·stadiums·POI)   │
└───────────────────────────┬──────────────────────────────────┘
              ┌─────────────┼─────────────┬──────────────────┐
              ▼             ▼             ▼                  ▼
        Gemini 2.5    Kakao / OSRM    KMA / TourAPI     Cloud Firestore
        (Tool SDK)    (3-tier route)  (단기예보)         (visited · plans)
```

### 🌐 라이브 URL (Production)

| 서비스 | URL | 상태 |
|---|---|---|
| **Next.js (Phase 6 · 현재)** | https://my-web-app--mini12-310f5.asia-east1.hosted.app | ✅ Live |
| 레거시 Streamlit (Phase 5a · 참고용) | https://away-game-companion-262552815882.asia-northeast3.run.app | 🟡 Legacy |

### ✅ 배포 smoke test 결과 (2026-04-17)

| 엔드포인트 | 응답 | 확인 사항 |
|---|---|---|
| 6 페이지 (`/`, `/matches`, `/map`, `/places`, `/ai`, `/badges`) | 200 OK | SSR 렌더 · Hero · Sidebar 정상 |
| `GET /api/predict?team=LG&opponent=KT` | `{"prob":0,"source":"logreg"}` | Python 모델 계수 TS 포팅 일치 |
| `POST /api/route` 잠실→수원 | `source: "osrm"`, 33.5km, 537 polyline pts | Kakao 401 → OSRM 자동 폴백 |
| `POST /api/chat` (Gemini) | Tool `predict_win_rate` 호출 + 텍스트 스트리밍 | "LG가 KT를 상대로 승리할 확률은 0%입니다." |
| `POST /api/chat` (🎬 demoMode) | Mock 시나리오 "광주 가족 원정" 즉시 스트리밍 | LLM 호출 없이 사전 녹화 응답 |
| `/logos/LG.svg`, `/data/schedule.json` | 5.6KB · 133KB | 정적 에셋 서빙 |

### 🗺️ 배포 설정

| 항목 | 값 |
|---|---|
| Firebase Project | `mini12-310f5` |
| App Hosting Backend | `my-web-app` |
| Primary Region | `asia-east1` (Taiwan) |
| GitHub Source | [HorangEe02/KNU_KDT_12th](https://github.com/HorangEe02/KNU_KDT_12th) · main branch |
| Root Directory | `/Phase12/frontend` |
| Secrets (Secret Manager) | `GEMINI_API_KEY` · `KAKAO_REST_API_KEY` · `WEATHER_API_KEY_ENCODED` · `TOUR_API_KEY_ENCODED` |
| Runtime | Node.js 22 · Next.js 16.2.4 · React 19.2.4 |
| Auto rollout | 사용 설정됨 (main 브랜치 push 시 자동 재배포) |

**주요 기능**:
- **/matches**: Plotly 승률 게이지 + 최근 3년 원정 승률 막대 (scikit-learn 모델 계수 → TS 이식)
- **/map**: React-Leaflet 4 레이어 지도 + **3-tier 길찾기 폴백** (Kakao → OSRM → Haversine)
- **/places**: 10 구장별 맛집 · 숙소 · 관광지 POI + 거리×평점 산점도
- **/ai**: Gemini 2.5 Flash Lite 스트리밍 챗봇 + 6 tool calling + Multi-Agent + 🎬 Mock 시연
- **/badges**: Stadium Tour 10 구장 체크 + Firestore 이중화 (graceful localStorage fallback)
- **공유**: URL 직렬화 primary + Firestore 단축 링크 optional

**핵심 설계 문서** (모두 `docs/` 하위):
- `docs/PHASE6_NEXTJS_MIGRATION.md` — 6 세션 마이그레이션 로드맵
- `docs/OSM_FALLBACK_PLAN.md` — 길찾기 3-tier 폴백 설계 (Kakao → OSRM → Haversine)
- `docs/SESSION_E_PLAN.md` — AI 챗봇 + Badges 구현 설계
- `docs/SESSION_F_DEPLOY_RUNBOOK.md` — App Hosting 배포 단계별 가이드
- `docs/CLEANUP_PLAN.md` — 디렉토리 정리 계획 (2026-04-18 수행)
- `docs/IMPLEMENTATION_PLAN.md` — 전체 로드맵 (구 `md/` 에서 이동)
- `docs/guides/PHASE[0-5]_GUIDE.md` — Phase 별 상세 가이드 (구 `guide/` 에서 이동)
- `docs/reference/` — KBO · Tour · 기상청 API 레퍼런스 (구 `api/` 에서 이동)
- `legacy/` — Phase 1~5 Python 레거시 (참고용 보존)

**개발/배포**:
```bash
# 로컬 개발
cd frontend && pnpm install && pnpm dev

# 배포 전 검증
bash scripts/preflight.sh

# 배포 (최초 1회 백엔드 생성 후 반복)
firebase deploy --only apphosting --project mini12-310f5
```

---

## 📌 1. 프로젝트 주제 및 기획 의도

### 1-1. 주제

공공데이터(KBO 경기일정 · 한국관광공사 TourAPI · 기상청 예보)와 카카오 지도/길찾기 API, LLM 기반 AI 에이전트를 결합하여 **프로야구 원정 응원을 위한 맞춤형 여행 코스 추천 대시보드**를 구현합니다.

단순한 경기 일정 조회나 여행 앱이 아니라, **"원정 응원러"라는 구체적 타깃에 특화된 좁고 깊은 큐레이션 서비스**입니다. 여행 앱은 경기 일정을 모르고, 구단 앱은 맛집을 모릅니다 — 그 빈틈을 메우는 것이 이 프로젝트의 핵심입니다.

### 1-2. 도출할 인사이트

| 인사이트 카테고리 | 구체 질문 |
|---|---|
| **구단별 원정 패턴** | 어떤 구단 팬이 가장 원정을 많이 가는가? 어느 원정지에서 승률이 높은가? |
| **지역경제 기여도** | 특정 원정 시리즈가 개최지의 맛집·숙박에 얼마만큼의 유동 인구를 만드는가? |
| **팬 행동 패턴** | 1박 원정 vs 당일치기 비율, 평균 지출, 선호 이동수단 |
| **구장별 원정 친화도** | 경기장 접근성·주변 인프라·숙박 가격을 종합한 "원정 가성비 지수" |
| **관람 × 관광 상관관계** | 경기 승패와 주변 상권 소비의 관계, 우천·계절 변수의 영향 |

### 1-3. 활용 방안 및 기대 효과

**B2C 서비스 가치**
- 원정 응원러의 여행 플래닝 시간을 **평균 3시간 → 5분**으로 단축
- "원정 뱃지 시스템"으로 전국 10개 구장 컴플릿 도전 동기 부여
- AI 챗봇 기반 자연어 추천("아이랑 광주 1박 2일, 예산 30만원")

**B2B 확장 가치**
- **지자체**: 스포츠관광 정책 수립용 팬 동선·소비 데이터 라이선스
- **구단**: 원정 팬 패턴 기반 마케팅·굿즈 판매 인사이트
- **숙박·요식업**: 경기 일정 기반 수요 예측, 타기팅 프로모션

**사회적 가치**
- 지방 중소도시(광주·대구·창원·수원) 지역경제 활성화
- 스포츠관광이라는 신규 여행 카테고리의 디지털 인프라 구축
- 한국스포츠과학원 2025 트렌드 리포트가 제시한 "스포츠를 통한 지역경제 활성화" 과제에 직접 기여

---

## 📊 2. 트렌드 조사 및 분석

### 2-1. 시장 환경 — "수요는 이미 폭발했는데 전용 서비스가 없다"

**① 스포츠 직관 인구 급증**
- 2024년 K리그·KBO 상반기 누적 관중 **100만 명 돌파**
- 한국프로스포츠협회 『2023 프로스포츠 관람객 성향조사』: 고관여 팬의 **약 50%가 MZ세대**
- 남자 프로농구 신규 유입고객 비중 31.6%, 전 종목 평균 21.5%

**② 원정 응원 = 지역 여행 트렌드화**
- 강원도민일보 인터뷰: "서울→광주 직관, 원정지에서 숙소 예약하고 경기 없는 날 지역 맛집·관광지 방문"이 일반화된 패턴
- 국민일보: 런트립(Run+Trip), 스포츠 직관 투어, 셀럽 투어가 2030 전용 여행 상품으로 **완판 행진**

**③ 2026 KBO 시즌 규모**
- **3월 28일 개막, 팀당 144경기, 총 720경기**
- 10개 구단이 잠실·대전·문학·대구·창원·수원·광주·고척 등 8개 도시에 분포
- 원정 조합이 720경기 × 10팀 = 충분한 데이터 규모

**④ 국내외 산업 동향**
- 한국스포츠과학원 『2025 스포츠산업 트렌드』 10대 키워드에 **"팬덤 이코노미"**, **"스포츠를 통한 지역경제 활성화"** 포함
- 2022년 기준 국내 스포츠산업 규모 **78조 1,069억 원**(전년 대비 +22.3%)
- 글로벌 Fantasy Sports 시장: 2023년 $32.5B → 2030년 **$68.9B** 전망 (CAGR 12.6%)

**⑤ 수익 모델 & AI 트렌드**
- 맥킨지: AI 기반 개인화가 디지털 수익을 **10~20% 증대**
- Fantasy Baseball 업계: AI 추천으로 전환율 **최대 35% 향상**, 제휴 파트너십이 피크 시즌 매출의 **20%** 차지
- 2025~2026년 표준 아키텍처: **Multi-Agent + Agentic RAG + Function Calling**

### 2-2. 리서치 자료 링크

| 구분 | 제목 | 출처 |
|---|---|---|
| 시장 동향 | 2026 KBO 정규시즌 경기 일정 발표 | [KBO 공식](https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11794) |
| 팬덤 트렌드 | MZ세대, 원정 응원으로 지역 여행까지 | [강원도민일보](https://www.kado.net/news/articleView.html?idxno=1278045) |
| 여행 트렌드 | MZ 세대의 새로운 여행 트렌드 (런트립·직관 투어) | [국민일보](https://www.kmib.co.kr/article/view.asp?arcid=1739946898) |
| 산업 전망 | 2025 스포츠산업 10대 트렌드 | [스포츠경향](https://sports.khan.co.kr/article/202502060951003) |
| 글로벌 전망 | 2025 글로벌 스포츠 산업 트렌드 | [Deloitte Korea](https://www.deloitte.com/kr/ko/Industries/tmt/analysis/global-sports-trends-2025.html) |
| 수익 모델 | Sports App Monetization Models 2026 | [SportsFirst](https://www.sportsfirst.net/post/sports-app-monetization-models-that-actually-work) |
| 수익 모델 | Monetization of Gen Z Sports Fans | [WSC Sports](https://wsc-sports.com/blog/industry-insights/fan-activation-the-monetization-of-gen-sports-z-fans/) |
| 수익 모델 | Fantasy Sports App Revenue Strategies 2025 | [Arka Softwares](https://www.arkasoftwares.com/blog/how-do-fantasy-sports-apps-make-money/) |
| AI 아키텍처 | Developing AI Travel Agents: Hands-On | [AltexSoft](https://www.altexsoft.com/blog/ai-travel-agent/) |
| AI 아키텍처 | LangGraph + Bedrock Multi-Agent 여행 시스템 | [AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/build-multi-agent-systems-with-langgraph-and-amazon-bedrock/) |
| AI 아키텍처 | What is Agentic RAG? | [Weaviate](https://weaviate.io/blog/what-is-agentic-rag) |

---

## 🗃️ 3. 수집할 데이터 및 활용 모델

### 3-1. 수집할 데이터

| 데이터 | 규모 | 형식 | 용도 |
|---|---|---|---|
| KBO 2026 경기 일정 | 720경기 | CSV | 경기 검색·필터링 |
| 10개 구단 홈구장 정보 | 10개 | JSON (위경도 포함) | 지도 마커·경로 기점 |
| 팀별 과거 10년 전적 | 약 14,400경기 | CSV | 승률 예측 모델 학습 |
| 경기장 반경 3km POI (맛집·숙박·관광) | 경기장당 200~500건 | JSON | 추천·지도 시각화 |
| 지역별 숙박 평균 가격 | 8개 도시 × 계절 | CSV | 예산 필터·가성비 지수 |
| 기상청 단기예보 | 일일 갱신 | JSON | 우천 확률·야외 관광 추천 |
| 경로·소요시간·통행료 | 실시간 | API 응답 | 이동 비용 계산·동선 표시 |
| 구장별 원정 응원 노하우 | 수기 큐레이션 | Markdown → Vector DB | Agentic RAG 지식베이스 |

### 3-2. 데이터 출처

**공공데이터 (필수)**
- **KBO 경기일정** — [koreabaseball.com](https://www.koreabaseball.com/schedule/schedule.aspx) (웹 스크래핑 또는 CSV 수기 수집)
- **한국관광공사 TourAPI** — [공공데이터포털](https://www.data.go.kr/data/15101578/openapi.do) (위치기반 관광·숙박·음식점 정보, **약 26만 건** 무료 제공)
- **기상청 단기예보 API** — 공공데이터포털 (경기 당일 우천 확률)

**상업 API (무료 쿼터 활용)**
- **카카오 지도 Web API** — [apis.map.kakao.com](https://apis.map.kakao.com/) (지도 표시, 장소 검색)
- **카카오모빌리티 길찾기 API** — [developers.kakaomobility.com](https://developers.kakaomobility.com/product/api) (자동차 경로, 경유지 최대 5개)

**수기/크롤링 데이터**
- 구장별 응원 문화·주변 맛집 노하우 (야구 커뮤니티·블로그 크롤링 → Vector DB 저장)
- 구단별 응원가·팀 컬러·마스코트 정보

### 3-3. 활용 모델

| 모델 | 용도 | 라이브러리 |
|---|---|---|
| **로지스틱 회귀** | 경기 승률 예측 (홈/원정, 선발 ERA, 최근 10경기 폼) | scikit-learn |
| **Random Forest** | 원정 가성비 지수 계산 (다변수 조합) | scikit-learn |
| **OpenAI GPT-4o / Gemini 2.0** | Supervisor·Strategist Agent (복잡 추론) | openai, google-genai |
| **GPT-4o-mini / Gemini Flash** | 단순 필터링·파싱 Agent (비용 최적화) | 동일 |
| **text-embedding-3-small** | RAG 벡터 임베딩 | openai |
| **Chroma / FAISS** | 벡터 DB (원정 노하우 지식베이스) | chromadb, faiss-cpu |
| **LangGraph** | Multi-Agent 워크플로우 오케스트레이션 | langgraph |

---

## 🛠️ 4. 필요한 기술적 스택 및 사전 지식

### 4-1. 핵심 기술 스택 (Phase 6 — 현재)

**프론트엔드 / UI**
- **Next.js 16.2** (App Router · React Server Components · Turbopack)
- **React 19.2** · **TypeScript 5.9**
- **Tailwind CSS v4** (`@theme` 블록 + Stadium Editorial 디자인 토큰 17 종)
- **Zustand v5** — 사이드바 필터/뱃지 상태 + localStorage 영속
- **React-Leaflet v5** — 동적 로드(ssr:false) 지도 + 4 레이어
- **react-plotly.js / plotly.js-dist-min** — 게이지 · 막대 · 산점도
- **@ai-sdk/react** — `useChat` 훅 (Vercel AI SDK v6 UIMessage 프로토콜)

**백엔드 / API**
- **Node.js 22** (App Hosting 기본 런타임)
- **Next.js API Routes** (`/api/predict` `/api/route` `/api/chat` `/api/plans`)
- **Zod v4** — request body 검증
- **Firebase Admin SDK v13** — Firestore 서버 호출 (선택)

**AI / LLM 레이어**
- **Gemini 2.5 Flash Lite** (`@ai-sdk/google` + `createGoogleGenerativeAI`)
- **Vercel AI SDK v6** `streamText` + `tool()` + `stepCountIs(5)`
- **6 tool calling**: search_game · predict_win_rate · get_weather · find_places · get_route · search_knowledge
- **Multi-Agent 프롬프트** (일정/전략/장소 + 최종 Synthesizer)
- **인메모리 BM25-lite RAG** (ChromaDB 대신 tips.json 45 items 대상 경량화)
- **🎬 Mock 시연 모드** (네트워크 장애 대비 사전 녹화 응답)

**외부 API (서버 사이드 · Secret Manager)**
- **Kakao 모빌리티** (Tier 1) — 있을 때 자동 사용
- **OSRM public demo** (Tier 2) — 키 불필요 OSM 기반 폴백 (상세: `docs/OSM_FALLBACK_PLAN.md`)
- **Haversine** (Tier 3) — 오프라인 최후의 보루
- **한국관광공사 TourAPI** (공공데이터포털)
- **기상청 단기예보** + WGS84 → Lambert 격자 변환

**배포 / 인프라**
- **Firebase App Hosting** (Cloud Build + Cloud Run + CDN · `asia-northeast3`)
- **Secret Manager** — API 키 보관 (`firebase apphosting:secrets:set`)
- **Firestore Native mode** — visited_stadiums · shared_plans
- **pnpm 10** — 의존성 관리
- **GitHub** — 코드 관리, Issue·PR 기반 협업
- **Notion** — 기획·회의록

### 4-1-bis. 레거시 스택 (Phase 1~5 · 참고용, `src/` 유지)

Phase 6 이전 Streamlit 버전은 `src/` 에 보존되어 있으며 로컬 실행 가능:

- **Streamlit 1.40+** · **Python 3.10+** · **Pandas / scikit-learn**
- **streamlit-folium** / **Plotly** (Python 바인딩)
- **LangChain / ChromaDB / bge-m3** (Phase 4 RAG 원본)
- **Ollama gemma4** 로컬 LLM (오프라인 데모용)
- 실행: `streamlit run app.py` (레거시 Cloud Run URL 여전히 접근 가능)

### 4-2. 사전 학습이 필요한 개념

| 개념 | 왜 필요한가 | 학습 리소스 |
|---|---|---|
| Streamlit `session_state` | 챗봇 대화 기록·유저 필터 상태 유지 | [공식 문서](https://docs.streamlit.io/develop/concepts/architecture/session-state) |
| `st.chat_message` / `st.chat_input` | AI 챗봇 UI 구현 | [Streamlit Chat 튜토리얼](https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps) |
| Folium Marker · Popup · Polyline | 지도 위 경기장·맛집 표시, 경로 그리기 | [streamlit-folium PyPI](https://pypi.org/project/streamlit-folium/) |
| Function Calling / Tool Use | AI가 TourAPI·길찾기 API를 자동 호출 | [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling) |
| RAG (Retrieval Augmented Generation) | 원정 노하우 지식베이스 검색 | [Weaviate Agentic RAG](https://weaviate.io/blog/what-is-agentic-rag) |
| 벡터 임베딩 & 유사도 검색 | RAG의 핵심 원리 | OpenAI / LangChain 공식 예제 |
| 로지스틱 회귀 기초 | 승률 예측 모델의 원리 이해 | 기존 강의 자료 |

### 4-3. 팀원 역할별 필수 스킬

- **팀장 / 데이터 엔지니어**: Pandas, API 호출, 데이터 파이프라인
- **프론트 / UX 담당**: Streamlit 레이아웃, HTML/CSS, Figma
- **지도·시각화 담당**: Folium, Plotly, 좌표계 이해
- **AI / 분석 담당**: LLM API, LangChain, 프롬프트 엔지니어링

---

## 🎨 5. 웹 UI 기획 및 설계

### 5-1. 내비게이션 설계

서비스는 **"팀 선택 → 원정 경기 고르기 → AI 코스 생성 → 저장 및 공유"** 4단계 사용자 흐름을 따르며, 각 단계는 Streamlit의 탭과 사이드바로 자연스럽게 구분됩니다.

```
┌─────────────────────────────────────────────────────────┐
│  🏠 HERO (랜딩)                                          │
│  → 응원팀 선택 CTA                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌──────────────┬──────────────────────────────────────────┐
│              │                                          │
│  [사이드바]   │   [메인 콘텐츠]                            │
│              │                                          │
│  - 응원팀      │   ┌─ Tab 1: 경기 & 예측 ──────────────┐    │
│  - 원정 기간   │   │  원정 일정 / 승률 / 우천 예보 / 티켓 │    │
│  - 예산       │   └─────────────────────────────────┘    │
│  - 인원       │   ┌─ Tab 2: 동선 지도 ───────────────┐    │
│  - 이동수단   │   │  Folium 지도 + 경로 + POI 마커     │    │
│              │   └─────────────────────────────────┘    │
│              │   ┌─ Tab 3: 맛집·숙소 ───────────────┐    │
│              │   │  필터 + 평점 차트 + 카드 리스트     │    │
│              │   └─────────────────────────────────┘    │
│              │   ┌─ Tab 4: AI 플래너 ───────────────┐    │
│              │   │  챗봇 대화창 (Multi-Agent)         │    │
│              │   └─────────────────────────────────┘    │
│              │   ┌─ Tab 5: 내 뱃지·기록 ─────────────┐    │
│              │   │  원정 이력 타임라인 + 지도 + 뱃지    │    │
│              │   └─────────────────────────────────┘    │
└──────────────┴──────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  📄 FOOTER: 데이터 출처 / 팀 소개 / GitHub 링크            │
└─────────────────────────────────────────────────────────┘
```

### 5-2. 와이어프레임 (메인 화면)

```
╔═══════════════════════════════════════════════════════════════╗
║ ⚾ 원정 응원 플래너                              [로그인] [뱃지🏅]  ║
╠═══════════════════════════════════════════════════════════════╣
║┌─ SIDEBAR ────────┐┌─ MAIN ──────────────────────────────────┐║
║│                  ││ [경기&예측] [지도] [맛집] [AI] [내뱃지]    │║
║│ 🎽 응원팀          ││━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│║
║│ [LG 트윈스 ▼]     ││                                         │║
║│                  ││ 📅 이번 주 원정: 4/19(토) 창원 NC전       │║
║│ 📅 기간            ││                                         │║
║│ [4/17 ~ 4/20]   ││ ┌─ 경기 정보 ──┐ ┌─ 승률 예측 ──┐         │║
║│                  ││ │ 17:00 창원   │ │ LG 46%      │         │║
║│ 💰 예산            ││ │ 선발: 엔스   │ │ NC 54%      │         │║
║│ [────●────] 30만 ││ │ 날씨: 맑음   │ │ (로지스틱회귀)│         │║
║│                  ││ └──────────────┘ └──────────────┘         │║
║│ 👥 인원            ││                                         │║
║│ [◉ 혼자 ○ 커플    ││ 📊 구단별 창원 원정 승률 (최근 5년)        │║
║│  ○ 가족]          ││ ┌──────────────────────────────────────┐ │║
║│                  ││ │ [Plotly 막대그래프]                   │ │║
║│ 🚗 이동수단         ││ └──────────────────────────────────────┘ │║
║│ [◉ KTX ○ 자차    ││                                         │║
║│  ○ 버스]          ││ 🎫 [티켓 예매하러 가기] ← 제휴 CTA           │║
║│                  ││                                         │║
║│ [코스 생성]         ││                                         │║
║└──────────────────┘└─────────────────────────────────────────┘║
╚═══════════════════════════════════════════════════════════════╝
```

### 5-3. 주요 화면별 구성 요소

**Tab 1. 경기 & 예측**
- 원정 경기 리스트 (Pandas DataFrame + 필터링)
- 승률 예측 게이지 차트 (Plotly Indicator)
- 우천 확률 · 선발투수 · 최근 전적 (columns 레이아웃)
- 구단별 원정 승률 비교 (Plotly 막대그래프)

**Tab 2. 동선 지도**
- Folium 지도 (경기장 + 숙소 + 맛집 + 관광지 4종 레이어)
- 카카오모빌리티 경로 폴리라인 (출발지 → 경기장 → 숙소 → 맛집)
- 마커 클릭 시 우측 컬럼에 상세 정보 패널
- 이동 시간·비용 요약 카드

**Tab 3. 맛집 · 숙소**
- 카테고리 필터 (한식·일식·야식·카페 등 multiselect)
- 평점 × 거리 산점도 (Plotly)
- 카드 리스트 (expander로 펼치기)
- 제휴 할인 쿠폰 배지

**Tab 4. AI 플래너 챗봇**
- `st.chat_message` 기반 대화 UI
- Multi-Agent 워크플로우 시각화 (Thought-Action-Observation 로그)
- 예시 프롬프트 버튼 3종 ("1박 2일 가족여행", "당일치기 가성비", "우천 대비 실내 코스")

**Tab 5. 내 뱃지 · 기록**
- 10개 구장 컴플릿 진행률 (전국 지도 + 체크마크)
- 원정 타임라인 (방문 이력, 승패 기록)
- 공유용 이미지 자동 생성 (SNS 바이럴 유도)

### 5-4. 활용 언어 및 도구

| 단계 | 도구 | 산출물 |
|---|---|---|
| **기획** | Notion, Miro | PRD, 유저 플로우 다이어그램 |
| **와이어프레임** | Figma | Low-fi 와이어프레임 (5개 화면) |
| **프로토타입** | Figma Prototype | 탭 전환·버튼 클릭 인터랙션 |
| **디자인 시스템** | Figma (Auto Layout) | 컬러 팔레트, 타이포그래피, 컴포넌트 |
| **구현 (메인)** | Streamlit, Python | `app.py` + 모듈 파일들 |
| **구현 (브랜딩)** | HTML5, CSS3, Vanilla JS | 히어로 섹션, 팀 컬러 테마 |
| **지도 UI** | Folium, streamlit-folium | 인터랙티브 지도 컴포넌트 |
| **차트** | Plotly Express | 승률·평점·가격 시각화 |
| **AI UI** | Streamlit Chat Elements | 챗봇 대화창 |
| **협업** | GitHub, Notion, Slack | 코드·문서·커뮤니케이션 |
| **배포** | Streamlit Community Cloud | 공개 URL |

---

## 📅 개발 일정 (5일 계획)

| 일자 | 차시 | 주요 활동 |
|---|---|---|
| 4/17(금) | 4차시 | 팀 빌딩 · 주제 확정 · 데이터 수집 · 와이어프레임 |
| 4/20(월) | 5차시 | 핵심 기능 구현 · AI 연동 · 발표 리허설 · 최종 발표 |

---

## 👥 팀 구성 및 역할

| 역할 | 담당 | 주요 작업 |
|---|---|---|
| 팀장 / 데이터 엔지니어 | TBD | KBO 데이터셋 구축, TourAPI 래퍼, 캐싱 |
| 프론트 / UX | TBD | 사이드바·탭 레이아웃, HTML/CSS 브랜딩 |
| 지도 · 시각화 | TBD | Folium 지도, 경로 표시, Plotly 차트 |
| AI · 분석 | TBD | LLM 챗봇, Multi-Agent, 승률 모델 |

---

## 📎 최종 제출물

- [ ] `app.py` (Streamlit 메인 파일)
- [ ] 데이터 파일 (`data/` 디렉토리 내 CSV)
- [ ] 발표 자료 (화면 시연 포함 PDF/PPTX)
- [ ] `README.md` (본 문서)
- [ ] `requirements.txt`

---

## 📚 참고 문서

본 README에서 인용한 리서치 자료 외에도 다음 기술 문서를 주요 참고자료로 활용합니다.

- [Streamlit 공식 문서](https://docs.streamlit.io/)
- [streamlit-folium GitHub](https://github.com/randyzwitch/streamlit-folium)
- [Kakao Maps Web API 가이드](https://apis.map.kakao.com/web/guide/)
- [한국관광공사 TourAPI](https://api.visitkorea.or.kr/)
- [공공데이터포털](https://www.data.go.kr/)

---

*Last updated: 2026-04-17*
