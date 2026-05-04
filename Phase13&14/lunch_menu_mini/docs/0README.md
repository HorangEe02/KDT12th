# 🍱 직장인 점심 최적화 파이프라인

> **"오늘 뭐 먹지?"를 데이터로 해결합니다.**
>
> 날씨, 영양 밸런스, 팀 선호도, 음식점 정보를 통합 분석하여
> 매일 반복되는 점심 의사결정 피로를 줄여주는 데이터 파이프라인 & 대시보드 프로젝트

![python-tests](https://github.com/OWNER/REPO/actions/workflows/python-tests.yml/badge.svg)
![web-ci](https://github.com/OWNER/REPO/actions/workflows/web-ci.yml/badge.svg)
![docker-build](https://github.com/OWNER/REPO/actions/workflows/docker-build.yml/badge.svg)

> 배지의 `OWNER/REPO` 는 GitHub 푸시 후 실제 값으로 교체하세요.

📘 **[ARCHITECTURE.md](./ARCHITECTURE.md)** — 전체 아키텍처 · API 카탈로그 · 운영 체크포인트 · 환경 변수 · 테스트 인벤토리 · 로드맵 상태

---

## 📌 프로젝트 개요

### 배경 및 문제 정의

직장인이 하루 중 가장 자주 마주하는 소소한 스트레스 중 하나가 **"점심 뭐 먹지?"**입니다.
매일 같은 고민을 반복하면서도, 결국 익숙한 곳만 방문하거나 팀원 간 의견이 엇갈려
불필요한 시간을 소모하게 됩니다.

이 프로젝트는 다음과 같은 **실생활 불편함**을 해결합니다.

- 매일 반복되는 점심 메뉴 선택의 **의사결정 피로(Decision Fatigue)**
- 같은 음식점만 반복 방문하는 **편향된 식사 패턴**
- 날씨·미세먼지를 고려하지 않은 **비효율적인 외출**
- 주간 단위 **영양 불균형** 누적 (단백질 부족, 탄수화물 과다 등)
- 팀 단위 식사 시 **의견 수렴의 비효율성**

### 해결 방안

4개의 공공 API 및 사용자 데이터를 **하나의 파이프라인**으로 통합하고,
가중 점수 알고리즘을 통해 **오늘의 최적 점심**을 추천하는 시스템을 구축합니다.

---

## 🏗️ 시스템 아키텍처

### 전체 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (수집)                        │
├────────────┬────────────┬────────────────┬──────────────────────┤
│ 카카오맵    │ 기상청     │ 식품안전나라    │ 사용자 입력           │
│ /네이버 API │ 날씨 API   │ 영양성분 API   │ 투표/선호도           │
└─────┬──────┴─────┬──────┴───────┬────────┴──────────┬───────────┘
      │            │              │                   │
      ▼            ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ETL (변환/정제)                          │
├────────────┬────────────┬────────────────┬──────────────────────┤
│ 거리/평점   │ 환경 점수   │ 영양소 매핑    │ 선호도 집계           │
│ 필터링     │ 산출        │               │                      │
└─────┬──────┴─────┬──────┴───────┬────────┴──────────┬───────────┘
      │            │              │                   │
      ▼            ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    통합 추천 엔진 (Integration)                  │
│  종합점수 = 거리(0.3) + 날씨(0.2) + 영양(0.2) + 팀선호(0.3)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ SQLite/PostgreSQL│
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DASHBOARD (시각화/인터랙션)                      │
├────────────┬────────────┬────────────────┬──────────────────────┤
│ 🍽️ 음식점   │ 🌤️ 날씨    │ 📊 영양       │ 🗳️ 팀 투표           │
│ 탐색       │ 추천        │ 리포트         │                      │
└────────────┴────────────┴────────────────┴──────────────────────┘
```

### 대주제 및 4개 소주제

| # | 소주제 | 데이터 소스 | 핵심 기능 |
|---|--------|------------|----------|
| 1 | **주변 음식점 데이터 수집** | 카카오맵 / 네이버 지도 API | 반경 내 음식점 검색, 카테고리·거리·평점 기반 필터링 |
| 2 | **날씨 연동 메뉴 추천** | 기상청 단기예보 API, 에어코리아 API | 기온·미세먼지·강수확률에 따른 메뉴 유형 매칭 |
| 3 | **영양 균형 분석** | 식품안전나라 영양성분 DB API | 주간 탄·단·지 비율 트래킹, 영양 밸런스 진단 |
| 4 | **팀 투표 & 히스토리 관리** | 사용자 입력 (내부 DB) | 실시간 투표, 중복 방문 방지, 선호도 학습 |

---

## 🧮 핵심 알고리즘

### 가중 점수 모델 (Weighted Scoring Model)

각 음식점에 대해 4개 축의 점수를 산출하고, 가중합으로 최종 추천 점수를 계산합니다.

```
종합점수 = (거리점수 × 0.3) + (날씨적합도 × 0.2) + (영양균형 × 0.2) + (팀선호도 × 0.3)
```

#### 1. 거리 점수 (Distance Score)

| 거리 | 점수 |
|------|------|
| ~100m | 100 |
| ~200m | 85 |
| ~300m | 70 |
| ~400m | 50 |
| 400m~ | 30 |

#### 2. 날씨 적합도 (Weather Fitness)

기본 50점에서 조건 매칭 시 가산하는 방식입니다.

- 기온 < 10°C + 국물/죽 메뉴 → +30
- 기온 > 28°C + 면류/초밥 메뉴 → +25
- 미세먼지 "나쁨" + 실내 식당 → +15
- 강수확률 > 50% + 200m 이내 → +20

#### 3. 영양 균형 점수 (Nutrition Balance)

이번 주 섭취 이력 기반으로 부족한 영양소를 보충하는 메뉴에 가산합니다.

- 평균 단백질 < 25g + 고단백 메뉴(30g+) → +20
- 평균 지방 > 30g + 저지방 메뉴(15g-) → +20
- 적정 칼로리 범위(400~700kcal) → +10

#### 4. 팀 선호도 (Team Preference)

팀원 투표 수에 비례하여 점수를 부여합니다.

```
팀선호 점수 = min(투표수 × 25 + 25, 100)
```

---

## 📊 대시보드 기능 상세

### 탭 1: 🍽️ 음식점 탐색

- 카테고리 필터(한식/일식/양식/동남아)
- 종합 점수 기반 랭킹 리스트
- 음식점 선택 시 5축 레이더 차트(거리/날씨/영양/평점/가격) 상세 분석
- 방문 이력 및 최근 방문일 표시

### 탭 2: 🌤️ 날씨 추천

- 오늘의 기상 정보 요약(기온/습도/미세먼지/하늘상태/강수확률)
- 날씨 기반 맞춤 팁 자동 생성
- 메뉴 유형별 날씨 적합도 수평 바 차트
- 오늘 날씨 TOP 5 추천 리스트

### 탭 3: 📊 영양 리포트

- 주간 칼로리 추이 (Area Chart + 목표선)
- 탄수화물·단백질·지방 비율 (Donut Chart)
- 일별 영양소 섭취량 (Grouped Bar Chart)
- 영양 밸런스 자동 진단 (단백질 부족/과다/균형 양호)

### 탭 4: 🗳️ 팀 투표

- 팀원별 투표 인터페이스
- 랜덤 시뮬레이션 버튼
- 실시간 투표 현황 바 차트
- 결과 확정 시 "오늘의 점심" 배너 표시
- 최근 방문 기록 히스토리

---

## 🛠️ 기술 스택

### Frontend (대시보드)

| 기술 | 용도 |
|------|------|
| **React 18** | SPA 프레임워크 |
| **Recharts** | 데이터 시각화 (Area, Bar, Radar, Pie Chart) |
| **Tailwind CSS** | 유틸리티 기반 스타일링 |

### Backend (파이프라인) — 확장 시

| 기술 | 용도 |
|------|------|
| **Python 3.10+** | 데이터 수집 및 ETL 스크립트 |
| **FastAPI** | REST API 서버 |
| **SQLite / PostgreSQL** | 데이터 저장소 |
| **APScheduler** | 주기적 데이터 수집 스케줄링 |

### 외부 API

| API | 제공처 | 용도 |
|-----|--------|------|
| 카카오 로컬 API | Kakao Developers | 주변 음식점 검색 |
| 기상청 단기예보 API | 공공데이터포털 | 날씨 정보 |
| 에어코리아 API | 공공데이터포털 | 미세먼지 정보 |
| 식품영양성분 DB API | 식품안전나라 | 메뉴별 영양성분 |

---

## 📁 프로젝트 구조

```
Mini/
├── 0README.md                   # 프로젝트 개요 (현재 파일)
├── README.md                    # 상세 기획서
├── dashboard-web/               # 🖥️ Next.js 16 + React 19 + Tailwind v4 프런트엔드
│   ├── src/
│   │   ├── app/                 # App Router (/, /discover, /weather, ...)
│   │   ├── components/          # layout · settings · dashboard · 6 feature dirs
│   │   └── lib/                 # api · types · queries · scoring · mock · providers
│   ├── package.json
│   └── README.md
├── legacy/
│   └── lunch-optimizer-dashboard.jsx.bak   # 마이그레이션 이전 단일 jsx
├── lunch-optimizer/             # 🐍 Python 백엔드 (FastAPI + SQLAlchemy)
│   └── pipeline/
│   ├── collectors/
│   │   ├── restaurant_collector.py    # 음식점 데이터 수집
│   │   ├── weather_collector.py       # 날씨 데이터 수집
│   │   ├── nutrition_collector.py     # 영양성분 데이터 수집
│   │   └── vote_collector.py          # 투표 데이터 수집
│   ├── transformers/
│   │   ├── distance_scorer.py         # 거리 점수 산출
│   │   ├── weather_scorer.py          # 날씨 적합도 산출
│   │   ├── nutrition_scorer.py        # 영양 균형 점수 산출
│   │   └── team_scorer.py             # 팀 선호도 점수 산출
│   ├── engine/
│   │   └── recommender.py             # 통합 추천 엔진
│   └── scheduler.py                   # 파이프라인 스케줄러
├── database/
│   ├── schema.sql                     # DB 스키마 정의
│   └── seed_data.sql                  # 초기 시드 데이터
├── api/
│   └── main.py                        # FastAPI 서버
├── docs/
│   ├── architecture.md                # 아키텍처 상세 문서
│   └── api-spec.md                    # API 명세서
├── tests/
│   ├── test_collectors.py
│   ├── test_scorers.py
│   └── test_recommender.py
├── GUIDE/                             # 🧩 4개 서브토픽 Claude Code 구현 가이드
├── ChatBOT/                           # 🤖 Ollama 기반 대화형 확장 가이드 (Phase1~4)
├── NLP/                               # 🧠 자연어 처리 확장 레이어 (Phase 5~6)
│   ├── README.md                            # NLP 레이어 진입점
│   ├── GUIDE_NLP_MVP_SCENARIO3.md           # 4주 전체 요약 (MVP)
│   ├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md     # 1주차 A1 감성분석 상세
│   ├── GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md  # 2주차 B1 메뉴 정규화 상세
│   ├── GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md   # 3주차 D3 RAG 챗봇 상세
│   ├── GUIDE_NLP_MVP_STEP4_NLG_REPORT.md    # 4주차 D5 NLG 리포트 상세
│   ├── GUIDE_NLP_RESEARCH_SCENARIO2.md      # 시나리오 2 (연구, 10주)
│   └── nlp_mvp/                             # 구현 스켈레톤 + Step 0 공용 유틸
└── .env.example                       # 환경변수 템플릿
```

---

## 🚀 시작하기

### 사전 요구사항

- Node.js 18+ / npm 9+
- Python 3.10+ (백엔드 확장 시)
- 공공데이터포털 API 인증키

### 1. 대시보드 실행 (Next.js 16 + React 19)

```bash
cd Mini/dashboard-web

# 최초 1회
cp .env.local.example .env.local     # API 주소 확인
npm install

# 개발 서버
npm run dev
# → http://localhost:3000
```

`.env.local` 예:
```env
NEXT_PUBLIC_LUNCH_API=http://localhost:8000/api
NEXT_PUBLIC_NLP_API=http://localhost:8001
NEXT_PUBLIC_DEFAULT_USER_ID=1
```

### 1-b. 동시에 백엔드 2종 기동 (풀 기능)

```bash
# 터미널 1 — lunch-optimizer (8000)
cd Mini/lunch-optimizer && uvicorn api.main:app --reload --port 8000

# 터미널 2 — NLP (8001)
cd Mini && uvicorn nlp_mvp.api.main:app --reload --port 8001

# 터미널 3 — Next.js
cd Mini/dashboard-web && npm run dev
```

NLP API가 꺼져 있어도 Dashboard UI는 graceful degradation 으로 렌더됩니다 (Disconnected 배지·pending 스켈레톤).

### 1-c. 🐳 Docker Compose — 원클릭 전체 스택 (Phase 4)

```bash
cd Mini
cp .env.example .env              # API 키 입력
docker compose build              # ~15~20분 (최초만)
./docker/bootstrap.sh              # Ollama 모델 pull
docker compose up -d
open http://localhost:3000
```

4개 서비스가 한 번에 뜹니다: `ollama` + `lunch-api` + `nlp-api` + `web`. 상세: [`docker/README.md`](./docker/README.md)

### 2. 파이프라인 실행 (Python, 확장 시)

```bash
cd lunch-optimizer/pipeline

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp ../.env.example ../.env
# .env 파일에 API 키 입력

# 파이프라인 실행
python scheduler.py
```

### 3. 환경변수 설정

```env
# .env.example
KAKAO_REST_API_KEY=your_kakao_api_key
DATA_GO_KR_API_KEY=your_public_data_api_key
FOOD_SAFETY_API_KEY=your_food_safety_api_key
DB_URL=sqlite:///lunch_optimizer.db
OFFICE_LAT=37.5665      # 사무실 위도
OFFICE_LNG=126.9780     # 사무실 경도
SEARCH_RADIUS=500        # 검색 반경 (미터)
```

---

## 📈 기대 효과 및 활용 시나리오

### 정량적 효과

| 지표 | 기존 | 개선 후 |
|------|------|---------|
| 점심 메뉴 결정 시간 | 평균 15분 | 평균 3분 |
| 같은 음식점 재방문율 | 70% | 40% |
| 주간 영양 균형 인지율 | 10% | 80% |
| 팀 식사 합의 소요시간 | 평균 20분 | 평균 5분 |

### 활용 시나리오

- **중소기업 사내 복지 도구**: 직원 식사 만족도 향상 및 건강 관리
- **공유 오피스 커뮤니티**: 입주사 간 점심 네트워킹 촉진
- **건강관리 앱 연동**: 개인 식단 데이터 기반 맞춤 추천 확장
- **프랜차이즈 본사 분석**: 상권 내 직장인 메뉴 선호도 트렌드 파악
- **지자체 상권 분석**: 점심 시간대 유동인구 기반 소상공인 지원 정책 수립

---

## 🗺️ 로드맵

### Phase 1 — MVP (현재)
- [x] 파이프라인 아키텍처 설계
- [x] React 대시보드 프로토타입 (Mock 데이터)
- [x] 4개 탭 UI 구현
- [x] 가중 점수 알고리즘 구현

### Phase 2 — API 연동
- [ ] 카카오맵 API 실시간 연동
- [ ] 기상청 단기예보 API 연동
- [ ] 식품안전나라 영양성분 API 연동
- [ ] SQLite 데이터 영속화

### Phase 3 — 고도화
- [x] 모바일 반응형 최적화 — `md:hidden` Sidebar · BottomNav (glass-panel) · safe-area-inset
- [x] 개인화 설정 — `UserPreferences` (favoriteCategories / allergies / maxPrice / recencyPenalty) + 5-step Onboarding wizard
- [x] 사용자 로그인 — `/api/users` 4엔드포인트 + `/login` 페이지 + `useAuth` 훅 + UserPanel 로그아웃
- [x] ML 기반 개인 선호도 — `/nlp/v2/recommend` (E1) `<ForYouCard />` Dashboard 통합
- [x] Slack 봇 연동 — `POST /api/notify/slack` + Vote 페이지 "Share to Slack" 버튼
- [ ] Teams 봇 (Phase 4 에서 Docker Compose 와 함께)
- [ ] 프로필 아바타 이미지 업로드

### Phase 4 — 배포
> 상세: [`docker/README.md`](./docker/README.md)
- [x] Docker 컨테이너화 — 4-서비스 (`ollama` + `lunch-api` + `nlp-api` + `web`) `docker compose up -d`
- [x] `docker/Dockerfile.{lunch,nlp,web}` 3종 + `docker-compose.yml` + `.dockerignore` + `bootstrap.sh`
- [x] Next.js `output: "standalone"` 활성화 (runtime 이미지 ~180MB)
- [x] 공유 볼륨 (`mini-db`, `mini-chroma`, `mini-hf`, `ollama-models`) + HTTP health checks
- [x] ~~Streamlit 버전~~ → `ROLE_SEPARATION_DECISION.md`에서 폐기 (React 전용)
- [x] **CI/CD 파이프라인 (GitHub Actions)** — `python-tests` · `web-ci` · `docker-build (GHCR)` + Dependabot + CODEOWNERS · 상세: [`.github/workflows/README.md`](./.github/workflows/README.md)
- [ ] 사용자 피드백 루프 (추후)

### 🎯 역할 분리 (2026-04-08 결정)
> **NLP = 메인 언어 처리 축 · ChatBOT = 선택적 추가 기능 (React 전용)**
> 상세: [`ROLE_SEPARATION_DECISION.md`](./ROLE_SEPARATION_DECISION.md)

### Phase 5 — 🎯 NLP 레이어 / 시나리오 3 (MVP, 4주) — **메인**
> **진입점:** [`NLP/README.md`](./NLP/README.md)
> **전체 요약:** [`NLP/GUIDE_NLP_MVP_SCENARIO3.md`](./NLP/GUIDE_NLP_MVP_SCENARIO3.md)
- [x] **Step 0** 공용 유틸 — `shared/db.py` · `logger.py` · `ollama_client.py` ([구현 완료](./NLP/nlp_mvp/shared/))
- [x] **Step 1 / 1주차** — A1 리뷰 감성분석 (KcELECTRA Zero-shot) · [`STEP1_SENTIMENT.md`](./NLP/GUIDE_NLP_MVP_STEP1_SENTIMENT.md)
- [x] **Step 2 / 2주차** — B1 메뉴명 정규화 (규칙 + Levenshtein + Sentence-BERT) · [`STEP2_MENU_NORMALIZER.md`](./NLP/GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md)
- [x] **Step 3 / 3주차** — D3 RAG 영양 상담 챗봇 (ChromaDB + Ollama Qwen2.5) · [`STEP3_RAG_CHATBOT.md`](./NLP/GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md)
- [x] **Step 4 / 4주차** — D5 NLG 주간 영양 리포트 (수치 → 자연어) · [`STEP4_NLG_REPORT.md`](./NLP/GUIDE_NLP_MVP_STEP4_NLG_REPORT.md)
- [x] **Step 5 통합** — FastAPI `/nlp/*` 라우터 11종 + lunch-optimizer 스코어링 v2 보정 + `lunch-optimizer-dashboard.jsx` 6탭 확장

### Phase 5.5 — 🖥️ Next.js 마이그레이션 (M1~M10, 완료)
> **디렉토리:** [`dashboard-web/`](./dashboard-web/) · [`dashboard-web/README.md`](./dashboard-web/README.md)
> **참조 프로젝트:** `01_CAD/web` (CAD Vision v5.6, Next.js 16 + React 19 + Tailwind v4 + TanStack Query v5)
- [x] **M1** Scaffold (Next.js 16 · configs · layout · globals.css Warm Kitchen theme)
- [x] **M2** `src/lib/` — api · types · queries · scoring · mock · providers
- [x] **M3** Layout shell — TopNav · Sidebar(7 nav) · StatusFooter · SettingsPanel · UserPanel
- [x] **M4** `/` Dashboard — KPI 4카드 · CategoryChart · OllamaStatus · TodaysTop5
- [x] **M5** `/discover` — useQueries 병렬 감성 로드 · 6축 레이더 DetailPanel
- [x] **M6** `/weather` `/nutrition` `/vote` — AI Comment Card (NLG) · Recharts 5종 · 실시간 집계
- [x] **M7** `/concierge` — **SSE 토큰 스트리밍** (백엔드 `POST /nlp/chatbot/chat/stream` + `OllamaClient.chat_stream()`)
- [x] **M8** `/insights` — HealthStrip · Sentiment Top10 · Normalizer Playground · RAG Stats · Roadmap
- [x] **M9** Ollama 모델 선택 — `/nlp/models` · `PUT /nlp/settings/model` · chat/report 용도별 env 분리 · SettingsPanel 실연결
- [x] **M10** Cleanup — legacy jsx → [`legacy/`](./legacy/) · 문서 갱신 · `.env` `gemma4` 오류 수정

### Phase 6 — NLP 레이어 / 시나리오 2 (연구·심화)
> 상세: [`NLP/GUIDE_NLP_RESEARCH_SCENARIO2.md`](./NLP/GUIDE_NLP_RESEARCH_SCENARIO2.md) · 구현: [`NLP/nlp_research/README.md`](./NLP/nlp_research/README.md)
- [x] **A2** ABSA — BERT-SPC 코드 스캐폴드 + 50건 시드 + 5 aspect × 3 sentiment 분리 평가 (학습 대기)
- [x] **B2** Food NER — KoELECTRA + 13 BIO 태그 + 50건 시드 + 알레르겐 필터 + Rule-based fallback
- [ ] **D1 + D2** JointBERT — 본 단계 제외
- [x] **E1** 임베딩 기반 개인화 CF — UserEmbedder + (FAISS / Numpy / Pure-Py) + LOO 평가 + 4 베이스라인 비교
- [x] **벤치마크 자동화** — `evaluation/benchmark.py` 단일 진입점 (A2/B2/E1, `--smoke` dry-run, summary.md/json 출력)
- [x] **Phase 5 v2 통합** — `nlp_mvp/api/routers/v2.py` 신규 (`/nlp/v2/sentiment/{id}` · `/nlp/v2/menu/extract` · `/nlp/v2/recommend`)
- [ ] 논문 초안

### Phase 7 — ⚡ ChatBOT Function Calling 레이어
> 상세: [`ChatBOT/GUIDE_CHATBOT_INTEGRATION.md`](./ChatBOT/GUIDE_CHATBOT_INTEGRATION.md)
> 구현: `NLP/nlp_mvp/rag_chatbot/tools/` · `nlp_mvp/rag_chatbot/tool_bot.py`
> ⚠️ **별도 ChatBOT 디렉토리 대신 기존 `rag_chatbot/` 에 통합** — `ROLE_SEPARATION_DECISION.md` 원칙 반영
- [x] **8 Tool Functions** 스키마 + `ToolExecutor` HTTP 래퍼 (`tools/definitions.py`, `executors.py`)
- [x] **프롬프트 fallback 파서** (`tools/fallback.py`) — `[TOOL: name(args)]` 패턴 + 규칙 라우터
- [x] **Tool 결과 포맷터** (`tools/formatter.py`) — 8 tool별 Korean summary
- [x] **ToolCallingBot** (`tool_bot.py`) — Ollama 루프 + max_iterations + 세션 캐시
- [x] **`POST /nlp/chatbot/chat/tools`** + `GET /nlp/chatbot/tools` FastAPI 라우터
- [x] **Concierge 모드 토글** — React `Tab: RAG / Tools` 스위치 + 호출 트레이스 칩
- [x] **23 pytest 통과** — definitions · fallback · router · executors · formatter
- [ ] 멀티턴 대화 이력 보존 (Phase 8 후속)

---

## 🤝 기여 방법

1. 이 저장소를 Fork합니다.
2. 기능 브랜치를 생성합니다. (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다. (`git commit -m 'feat: add amazing feature'`)
4. 브랜치에 Push합니다. (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다.

### 커밋 컨벤션

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드 추가
chore: 빌드/설정 변경
```

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 📞 문의

프로젝트에 대한 질문이나 제안이 있다면 Issues 탭을 이용해주세요.

---

<div align="center">

**🍱 점심 고민, 이제 데이터에게 맡기세요.**

*Built with data, served with love.*

</div>
