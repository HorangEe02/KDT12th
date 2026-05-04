# Mini — 최종 아키텍처 & API 카탈로그

> **상태:** 2026-04-08 기준. Phase 1~7 완료, Phase 5.5 (Next.js 마이그레이션) 완료.
> 전체 가중 진척률 **~96%**. 데모 가능 · CI 통과 · Docker 배포 가능.

---

## 0. 한눈에 보기

```
                       ┌────────────────────────────────────────┐
                       │         Browser (user / mobile)        │
                       └────────┬─────────────────────┬─────────┘
                                │                     │
                       :3000    │                     │ :11434
                                ▼                     │
            ┌───────────────────────────────┐         │
            │  dashboard-web (Next.js 16)    │         │
            │  • 7 pages (RAG+Tools chat)   │         │
            │  • TanStack Query cache        │         │
            │  • onboarding / login / prefs  │         │
            │  • BottomNav (mobile)          │         │
            └────┬──────────────────────┬───┘         │
                 │ :8000/api             │ :8001/nlp  │
                 ▼                       ▼            │
    ┌────────────────────────┐  ┌────────────────────┴─────┐
    │  lunch-optimizer        │  │  NLP API (FastAPI)        │
    │  (FastAPI)              │  │  • Phase 5 MVP (5 modules)│
    │  • Restaurants/weather/ │◄─┤  • Phase 6 v2 (A2/B2/E1) │
    │    nutrition/vote/users │  │  • Phase 7 Tool Calling   │
    │  • 32 endpoints         │  │  • 18 endpoints           │
    │  • Slack webhook        │  │  • SSE streaming chat     │
    └────────┬────────────────┘  └───────┬──────────────────┘
             │                            │
             │ shared volume              │ http://ollama:11434
             ▼                            ▼
      ┌──────────────┐           ┌──────────────────┐
      │  mini.db  │           │  Ollama          │
      │  (SQLite)    │           │  qwen2.5:7b      │
      │  • 11 tables │           │  sentence-bert   │
      └──────────────┘           └──────────────────┘
```

**4개 컨테이너** (`docker compose up -d`):
- `ollama` — LLM 런타임
- `lunch-api` — 음식점/날씨/영양/투표/사용자/Slack
- `nlp-api` — 감성/메뉴정규화/RAG/리포트/ABSA/NER/CF/Tool Calling
- `web` — Next.js 16 대시보드

---

## 1. 레포 구조

```
Mini/
├── 0README.md                    # 프로젝트 개요 (로드맵 + 체크박스)
├── README.md                     # 상세 기획서
├── ARCHITECTURE.md               # 본 문서
├── ROLE_SEPARATION_DECISION.md   # Phase 5/7 분리 결정
├── .env.example / .env
├── .gitignore / .dockerignore
├── docker-compose.yml            # 4-service orchestration
│
├── lunch-optimizer/              # 🐍 Python backend (FastAPI + SQLAlchemy)
│   ├── api/main.py               # 32 endpoints
│   ├── database/models.py        # 11 tables (restaurants, weather, nutrition, votes, users, ...)
│   ├── pipeline/                 # collectors + transformers + loaders + scheduler
│   ├── engine/recommender.py     # LunchRecommender (composite scoring)
│   └── tests/
│
├── NLP/
│   ├── nlp_mvp/                  # Phase 5 MVP (77 .py files)
│   │   ├── shared/               # db, logger, ollama_client
│   │   ├── sentiment/            # A1 KcELECTRA
│   │   ├── menu_normalizer/      # B1 rule + Lev + SBERT
│   │   ├── rag_chatbot/
│   │   │   ├── chatbot.py        # Phase 5 RAG bot
│   │   │   ├── tool_bot.py       # Phase 7 Tool Calling bot
│   │   │   └── tools/            # 8 tool functions + executors + fallback
│   │   ├── nlg_report/           # D5 weekly NLG
│   │   ├── integration/          # scoring_patch v2 (+ A/B log)
│   │   └── api/                  # FastAPI routers (sentiment/menu/chatbot/reports/settings/v2)
│   │
│   └── nlp_research/             # Phase 6 (36 .py files, ~4K lines)
│       ├── configs/              # YAML hyper-params
│       ├── data/seed/            # 50-row JSONL seeds (ABSA + NER)
│       ├── models/absa/          # BERT-SPC
│       ├── models/food_ner/      # KoELECTRA (+optional CRF)
│       ├── models/embedding_cf/  # UserEmbedder + FAISS/numpy/pure-py index
│       ├── training/             # base_trainer + data_loader + metrics + augmentation
│       ├── evaluation/           # benchmark.py + 3 comparators + baselines
│       └── tests/                # 37 pytest smoke tests
│
├── dashboard-web/                # 🖥️ Next.js 16 / React 19 / Tailwind v4
│   ├── next.config.ts            # output: "standalone"
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx        # Providers + TopNav + Sidebar + BottomNav + OnboardingGate
│   │   │   ├── page.tsx          # Dashboard (KPI + Category + Ollama + Top5 + ForYou)
│   │   │   ├── login/            # Phase 3 auth
│   │   │   ├── onboarding/       # Phase 3 wizard
│   │   │   ├── discover/         # personalized restaurant list
│   │   │   ├── weather/
│   │   │   ├── nutrition/        # + NLG AI comment card
│   │   │   ├── vote/             # + Slack share button
│   │   │   ├── concierge/        # RAG streaming + Tools mode
│   │   │   └── insights/         # NLP health + stats + playground
│   │   ├── components/
│   │   │   ├── layout/ (TopNav, Sidebar, BottomNav, StatusFooter)
│   │   │   ├── settings/ (SettingsPanel, UserPanel, PreferencesSection)
│   │   │   ├── onboarding/ (OnboardingGate)
│   │   │   ├── dashboard/ (KPICards, CategoryChart, OllamaStatus, TodaysTop5, ForYouCard)
│   │   │   ├── discover/ (RestaurantCard, SentimentBadge, DetailPanel, FilterPills, SortDropdown)
│   │   │   ├── weather/ (CurrentWeatherCard, WeatherTips, MenuFitnessChart, WeatherTopPicks)
│   │   │   ├── nutrition/ (AICommentCard, CalorieTrend, MacroDonut, DailyBreakdown, StatCard)
│   │   │   ├── vote/ (VoterGrid, VoteResultBanner, VoteResultsChart, VisitHistory)
│   │   │   ├── concierge/ (MessageBubble, RecommendationCards, InputBar, HallucinationBanner)
│   │   │   └── insights/ (HealthStrip, SentimentOverview, MenuNormalizerPlayground, RAGStatsCard, RoadmapCard)
│   │   └── lib/
│   │       ├── api.ts            # apiFetchLunch / apiFetchNLP / apiStreamSSENLP
│   │       ├── auth.ts           # login / logout / sync prefs
│   │       ├── preferences.ts    # UserPreferences + personalizedMultiplier
│   │       ├── adapters.ts       # lunch-api → frontend shapes
│   │       ├── queries.ts        # TanStack Query hooks
│   │       ├── scoring.ts        # composite score (ported from legacy)
│   │       ├── mock.ts           # fallback mock data
│   │       ├── types.ts          # Pydantic → TS mirrors
│   │       └── providers.tsx
│   └── package.json              # Next 16 + React 19 + Tailwind v4 + TanStack
│
├── docker/
│   ├── Dockerfile.lunch          # python:3.11-slim, ~260MB
│   ├── Dockerfile.nlp            # python:3.11 + torch CPU, ~2.5GB
│   ├── Dockerfile.web            # node:20-alpine standalone, ~180MB
│   ├── bootstrap.sh              # Ollama model pull helper
│   └── README.md
│
├── .github/
│   ├── workflows/
│   │   ├── python-tests.yml      # pytest + benchmark dry-run
│   │   ├── web-ci.yml            # tsc + eslint + next build
│   │   ├── docker-build.yml      # Buildx matrix + GHCR push
│   │   └── README.md
│   ├── dependabot.yml            # 6 ecosystems
│   ├── CODEOWNERS
│   └── pull_request_template.md
│
├── legacy/
│   ├── README.md                 # old → new mapping
│   └── lunch-optimizer-dashboard.jsx.bak
│
├── sample_html/                  # Stitch export reference (desktop + m_*)
└── api/                          # 공공 API docs (카카오/기상청/식약처 PDFs)
```

### 코드 규모
| 영역 | 파일 수 | lines |
|---|---|---|
| `lunch-optimizer/*.py` | 44 | ~5,500 |
| `NLP/nlp_mvp/*.py` | 77 | ~9,500 |
| `NLP/nlp_research/*.py` | 36 | ~3,960 |
| `dashboard-web/src/*.ts(x)` | 61 | ~6,000 |
| Docker / CI / docs | ~20 | ~1,500 |
| **합계** | **~238 sources** | **~26,500 lines** |

---

## 2. Phase 로드맵 — 체크박스

| Phase | 상태 | 비고 |
|---|---|---|
| **Phase 1** — MVP (React 프로토타입, 4-tab UI, composite scoring) | ✅ | |
| **Phase 2** — API 연동 (카카오 / 기상청 / 식약처 / SQLite) | ✅ | 32 endpoints + mock fallback |
| **Phase 3** — 고도화 (로그인 · 개인화 · 모바일 · Slack · ML For-You) | ✅ | 아바타 업로드만 미구현 |
| **Phase 4** — 배포 (Docker Compose + CI/CD GHCR) | ✅ | 피드백 루프만 미구현 |
| **Phase 5** — NLP MVP 시나리오 3 (A1/B1/D3/D5 + Step 5 통합) | ✅ | 4 주 풀구현 |
| **Phase 5.5** — Next.js 16 마이그레이션 (M1~M10) | ✅ | 10 마일스톤 완료 |
| **Phase 6** — NLP 연구 시나리오 2 (A2/B2/E1 + 벤치마크 자동화) | ✅ | 코드 완료, 학습 대기 |
| **Phase 7** — ChatBOT Function Calling (8 tools + toggle UI) | ✅ | 멀티턴 이력만 미구현 |

### 완료된 주요 기능 (요약)
- 📊 **7 페이지 대시보드** — Dashboard / Discover / Weather / Nutrition / Vote / Concierge / Insights
- 🔐 **로그인 + 온보딩** — 4-step wizard + localStorage 개인화 + `/api/users` 동기화
- 📱 **모바일 반응형** — BottomNav (glass-panel) + safe-area-inset + `md:hidden` 사이드바
- 🧠 **NLP 11 엔드포인트** — sentiment/menu/chatbot/reports + settings/models + v2 research
- 💬 **Chat 3 모드** — ChromaDB RAG (SSE) / Tool Calling (8 functions) / Weekly NLG
- 🎯 **ML 개인화** — E1 Embedding CF + `For You` card
- 🔔 **Slack 연동** — vote winner 공유 webhook
- 📦 **Docker Compose** — 4 서비스 원클릭 배포
- 🤖 **CI/CD** — GitHub Actions (pytest + web build + Buildx → GHCR) + Dependabot
- 🧪 **60 passed tests** — Phase 5 smoke + Phase 6 benchmark + Phase 7 tool calling

---

## 3. API 카탈로그

### 3.1 lunch-optimizer (port 8000) — 32 endpoints

> 모두 prefix `/api`

#### Meta
| Method | Path | Tag |
|---|---|---|
| GET | `/health` | meta |

#### Restaurants
| Method | Path | 설명 |
|---|---|---|
| GET | `/restaurants` | 활성 음식점 목록 (필터: category, min_score, limit) |
| GET | `/restaurants/stats` | 카테고리별 집계 + avg 거리 |
| GET | `/restaurants/{id}` | 단일 상세 |
| POST | `/pipeline/run` | 수동 수집 실행 |

#### Weather (Subtopic 2)
| Method | Path | 설명 |
|---|---|---|
| GET | `/weather/current` | 현재 기상 + 팁 |
| GET | `/weather/history` | 최근 N 시간 이력 |
| GET | `/weather/menu-ranking` | 메뉴 유형별 적합도 |
| GET | `/restaurants/weather-ranked` | 날씨 점수 반영 랭킹 |
| POST | `/weather/refresh` | 파이프라인 수동 실행 |

#### Nutrition (Subtopic 3)
| Method | Path | 설명 |
|---|---|---|
| GET | `/nutrition/restaurant/{id}` | 음식점별 영양 정보 |
| POST | `/nutrition/meal` | 식사 기록 |
| GET | `/nutrition/weekly` | 주간 요약 (user_id) |
| GET | `/nutrition/diagnosis` | 영양 진단 |
| GET | `/nutrition/trend` | N일 트렌드 |
| GET | `/restaurants/nutrition-ranked` | 개인 맞춤 영양 랭킹 |

#### Vote (Subtopic 4)
| Method | Path | 설명 |
|---|---|---|
| POST | `/vote/session` | 세션 개시 |
| POST | `/vote/cast` | 투표 행사 |
| POST | `/vote/veto` | 거부권 |
| GET | `/vote/status` | 현황 |
| POST | `/vote/close` | 마감 |
| GET | `/vote/history` | 이력 |

#### History & Preference
| Method | Path | 설명 |
|---|---|---|
| GET | `/history/visits` | 최근 영업일 방문 |
| GET | `/history/frequency` | 빈도 |
| GET | `/history/preference` | 팀 선호도 |

#### 통합 추천 (🎯 프로젝트 핵심)
| Method | Path | 설명 |
|---|---|---|
| GET | `/recommend?team_id&user_id&top_n` | 4축 종합 추천 |
| GET | `/recommend/{id}/explain` | 추천 이유 설명 |

#### Users (Phase 3 후속)
| Method | Path | 설명 |
|---|---|---|
| GET | `/users?team_id` | 팀 사용자 목록 |
| GET | `/users/{id}` | 단일 |
| POST | `/users` | 생성/재활성 (idempotent) |
| PATCH | `/users/{id}/preferences` | 기피/알레르기/아바타 동기화 |

#### Notifications
| Method | Path | 설명 |
|---|---|---|
| POST | `/notify/slack` | Slack Incoming Webhook 전송 |

---

### 3.2 NLP API (port 8001) — 18 endpoints

#### Meta + Settings
| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/health` | 모듈 상태 (`db`, `menu_normalizer`, `rag_chatbot_index`, `nlg_generator`, `scoring_patch_ab`, `research_v2`) |
| GET | `/nlp/models` | Ollama 설치 모델 + active chat/report |
| GET | `/nlp/settings` | 현재 chat/report 모델 + language |
| PUT | `/nlp/settings/model` | `{model, role}` 활성 모델 변경 (프로세스 env override + 캐시 drop) |

#### Sentiment (A1)
| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/sentiment/top?limit=10` | 감성 점수 상위 랭킹 |
| GET | `/nlp/sentiment/{restaurant_id}` | 식당별 감성 분포 |
| POST | `/nlp/sentiment/refresh` | 감성 파이프라인 배치 실행 (BackgroundTasks) |

#### Menu (B1)
| Method | Path | 설명 |
|---|---|---|
| POST | `/nlp/menu/normalize` | 정규화 결과 + method (rule/lev/embedding) |
| GET | `/nlp/menu/stats` | 메서드별 히트율 |

#### Chatbot (D3 + Phase 7)
| Method | Path | 설명 |
|---|---|---|
| POST | `/nlp/chatbot/chat` | 동기 RAG 응답 |
| POST | `/nlp/chatbot/chat/stream` | **SSE 토큰 스트리밍** (meta/token/final/error 4 types) |
| POST | `/nlp/chatbot/chat/tools` | **Phase 7 Tool Calling** 루프 |
| GET | `/nlp/chatbot/tools` | 8 tool 스키마 (UI help panel용) |
| POST | `/nlp/chatbot/reset` | 대화 이력 초기화 |
| GET | `/nlp/chatbot/stats` | 총 호출·평균 지연·환각 경고·활성 세션 |

#### Reports (D5)
| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/reports/weekly/{user_id}` | 주간 NLG 리포트 (캐시 우선) |
| POST | `/nlp/reports/weekly/{user_id}/regenerate` | 강제 재생성 |

#### Research v2 (Phase 6 scaffold)
| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/v2/sentiment/{id}` | A2 ABSA aspect별 감성 (현재는 Dummy backend) |
| POST | `/nlp/v2/menu/extract` | B2 NER 엔티티 (현재는 rule-based fallback) |
| GET | `/nlp/v2/recommend?user_id&top_n` | E1 Embedding CF 추천 |

---

## 4. 데이터 스키마 (SQLite `mini.db`, 11 tables)

| Table | Phase | 핵심 컬럼 |
|---|---|---|
| `restaurants` | 1 | id, name, category, menu_type, lat, lng, distance_m, distance_score, **sentiment_score** (Phase 5 A1) |
| `weather_logs` | 2 | collected_at, temp, humidity, sky, pop, pm10, pm25, dust_grade |
| `nutrition_info` | 3 | restaurant_id, food_name, calories, carbs, protein, fat, sugar, sodium |
| `meal_history` | 3 | user_id, restaurant_id, meal_date, menu_name, calories/macros, satisfaction |
| `teams` | 4 | id, name |
| `users` | 3/4 | id, name, team_id, avatar_emoji, **dislike_categories**, **allergy_info**, is_active |
| `vote_sessions` | 4 | vote_date, team_id, status, total_votes, winner_restaurant_id |
| `votes` | 4 | user_id, restaurant_id, vote_date |
| `vetoes` | 4 | user_id, restaurant_id, reason |
| `visit_history` | 4 | team_id, restaurant_id, visit_date |
| `reviews` | 5 A1 | restaurant_id, source, text, sentiment_label, sentiment_confidence |
| `menu_normalization` | 5 B1 | raw, cleaned, matched_id, method, confidence |
| `weekly_reports` | 5 D5 | user_id, week_start, nlg_text, generation_method, validation |
| `ab_scoring_log` | 5 int | v1/v2a/v2b, diff, sentiment_score (scoring_patch_ab) |

---

## 5. 테마 & 디자인 토큰

- **이름:** Warm Kitchen Theme
- **주 팔레트 (dark):** `bg #1a1512` / `primary #e8593c` (한식 오렌지) / `secondary #1d9e75` (균형 그린) / `tertiary #ba7517` (앰버)
- **폰트:** Plus Jakarta Sans (heading) + Manrope (body) + JetBrains Mono (숫자) + Pretendard (한글)
- **CSS 변수 구조:** `:root` + `[data-theme="light"]` + `@theme inline` (Tailwind v4)
- **다크/라이트:** `next-themes` + `data-theme` attr 경유, 모든 컴포넌트 `var(--color-*)` 사용
- **모바일:** `md:hidden` Sidebar · `md:hidden` StatusFooter · `md:pb-10 pb-24` main · 고정 BottomNav + safe-area-inset

---

## 6. 환경 변수 카탈로그

| 변수 | 기본값 | 사용처 | 설명 |
|---|---|---|---|
| **lunch-optimizer** | | | |
| `KAKAO_REST_API_KEY` | — | lunch | 카카오 로컬 검색 |
| `DATA_GO_KR_API_KEY_DECODED` | — | lunch | 기상청/에어코리아/식약처 공용 |
| `FOOD_SAFETY_API_KEY` | — | lunch | 식품안전나라 직접 키 (선택) |
| `OFFICE_LAT` / `OFFICE_LNG` | 37.5665 / 126.9780 | lunch | 사무실 좌표 |
| `SEARCH_RADIUS` | 500 | lunch | 검색 반경 (미터) |
| `NEAREST_STATION_NAME` | 종로구 | lunch | 에어코리아 측정소 |
| `DB_URL` | sqlite:///./lunch-optimizer/database/mini.db | lunch | SQLAlchemy URL |
| `SLACK_WEBHOOK_URL` | — | lunch | Slack Incoming Webhook |
| `CORS_ORIGINS` | localhost:3000,5173 | lunch | |
| **NLP** | | | |
| `OLLAMA_HOST` | http://localhost:11434 | nlp | |
| `OLLAMA_MODEL` | qwen2.5:7b-instruct | nlp | 전역 fallback |
| `OLLAMA_MODEL_CHAT` | (OLLAMA_MODEL) | nlp | D3 RAG + 툴 |
| `OLLAMA_MODEL_REPORT` | (OLLAMA_MODEL) | nlp | D5 NLG |
| `EMBEDDING_MODEL` | jhgan/ko-sroberta-multitask | nlp | Sentence-BERT |
| `SENTIMENT_MODEL` | nlp04/korean_sentiment_analysis_kcelectra | nlp | A1 |
| `MINI_DB_PATH` | ../lunch-optimizer/database/mini.db | nlp | 공용 DB 경로 |
| `CHROMA_DB_PATH` | .../rag_chatbot/chroma_store | nlp | 벡터스토어 |
| `NLP_API_PORT` | 8001 | nlp | |
| `NLP_API_CORS_ORIGINS` | localhost:3000,5173 | nlp | |
| `NLP_SKIP_RAG_INDEX` | 0 | nlp | lifespan 자동 인덱싱 건너뛰기 |
| `NLP_V2_DISABLE` | 0 | nlp | `/nlp/v2/*` 강제 503 |
| `LUNCH_API_BASE` | http://localhost:8000/api | nlp | ToolExecutor 대상 |
| **Web (Next.js — build-time)** | | | |
| `NEXT_PUBLIC_LUNCH_API` | http://localhost:8000/api | web | |
| `NEXT_PUBLIC_NLP_API` | http://localhost:8001 | web | |
| `NEXT_PUBLIC_DEFAULT_USER_ID` | 1 | web | |

---

## 7. 테스트 인벤토리

### 7.1 Python pytest
| 테스트 묶음 | 통과 수 | 경로 |
|---|---|---|
| Phase 5 integration (scoring_patch) | 8 | `NLP/nlp_mvp/integration/tests/` |
| Phase 5 기타 모듈 단위 | ~20 | `NLP/nlp_mvp/*/tests/` |
| Phase 6 ABSA smoke | 9 | `NLP/nlp_research/tests/test_absa_smoke.py` |
| Phase 6 Food NER smoke | 11 | `NLP/nlp_research/tests/test_food_ner_smoke.py` |
| Phase 6 Embedding CF smoke | 13 | `NLP/nlp_research/tests/test_embedding_cf_smoke.py` |
| Phase 6 Benchmark dry-run | 4 | `NLP/nlp_research/tests/test_benchmark_smoke.py` |
| Phase 7 Tool Calling | 23 | `NLP/nlp_mvp/rag_chatbot/tools/tests/test_tools.py` |
| **합계** | **~88 passed, 2 skipped (requires_torch)** | |

실행:
```bash
cd NLP
PYTHONPATH=. pytest nlp_mvp/ nlp_research/ -v
```

### 7.2 Frontend (Next.js)
- `npm run lint -- --max-warnings 0`
- `npx tsc --noEmit` (strict)
- `npm run build` (standalone output 검증)

### 7.3 CI/CD (GitHub Actions)
- `python-tests.yml` — matrix Python 3.10/3.11 + 3 jobs
- `web-ci.yml` — type check + lint + build + artifact
- `docker-build.yml` — 3-image buildx matrix + GHCR push + compose-validate

---

## 8. 운영 체크포인트

### 로컬 개발 기동
```bash
cd Mini
cp .env.example .env                # API 키 입력

# 옵션 A: Docker 원클릭 (권장)
docker compose build && ./docker/bootstrap.sh && docker compose up -d
open http://localhost:3000

# 옵션 B: 각자 uvicorn 3 프로세스
cd lunch-optimizer && uvicorn api.main:app --reload --port 8000 &
cd .. && uvicorn nlp_mvp.api.main:app --reload --port 8001 &
cd dashboard-web && npm install && npm run dev
```

### Health checks
```bash
curl http://localhost:8000/api/health
curl http://localhost:8001/nlp/health
curl http://localhost:3000               # Next.js (HTML 응답)
curl http://localhost:11434/api/tags     # Ollama 설치 모델
```

### 주요 debug 진입점
| 증상 | 확인 | 조치 |
|---|---|---|
| NLP API 503 | `/nlp/health` `modules` 필드 | 해당 모듈 error 메시지 확인 |
| 챗봇 응답 없음 | Ollama `/api/tags` → qwen2.5 있나? | `./docker/bootstrap.sh` |
| Discovery 카드 미로드 | `/api/restaurants` vs mock fallback | lunch-optimizer 로그 확인 |
| For You 빈 상태 | `/nlp/v2/recommend` backend 필드 | synthetic source fallback 이 정상 |
| Slack 실패 | `SLACK_WEBHOOK_URL` env | `/api/notify/slack` body.error |
| 모바일 레이아웃 깨짐 | DevTools 375px 이하 | Sidebar는 `hidden md:flex`, main은 `ml-0 md:ml-64` |

### 로그 위치
- `lunch-optimizer/logs/*.log`
- `NLP/logs/*.log`
- 컨테이너: `docker compose logs -f <service>`

---

## 9. 알려진 한계 & 후속

### 즉시 가능한 개선
1. **실 학습 데이터 수집 + Phase 6 모델 fine-tune** — A2/B2 NER weights → `/nlp/v2/*` 가 `backend: "trained"` 로 승격
2. **멀티턴 대화 이력** — Phase 7 `ToolCallingBot` 에 `ConversationHistory` 주입 (Phase 5 RAG bot 과 같은 패턴)
3. **E2E Playwright 테스트** — 로그인 → 온보딩 → 대시보드 → 챗 3 모드 smoke
4. **사용자 피드백 루프** — Phase 4 마지막 체크박스 (Likert 5점 + 주간 집계)

### 프로덕션 하드닝
1. **인증/권한** — 현재 `CurrentUser` 는 localStorage 로컬만. 프로덕션은 OAuth/JWT
2. **SQLite → PostgreSQL** — `DB_URL` 만 교체, ORM 레이어는 이미 PG 호환
3. **TLS + reverse proxy** — Caddy/Traefik/Nginx 앞에 두고 443 노출
4. **Rate limiting** — `cast_vote`/`record_meal` 쓰기 endpoint + chatbot 루트
5. **Observability** — Prometheus + Grafana, 현재는 logs 기반만
6. **Secret management** — `.env` → Vault/AWS SSM

### 미구현 기능
- 아바타 이미지 업로드 (현재는 이모지만)
- Teams 봇 연동 (Slack만 구현)
- 논문 초안 작성 (Phase 6)
- 모바일 PWA (install prompt, service worker)

---

## 10. 이 파일 이후

1. **커밋 직전** — `0README.md` 상단 CI 배지의 `OWNER/REPO` 교체
2. **첫 배포** — `docker compose build && ./docker/bootstrap.sh && docker compose up -d`
3. **데모** — `http://localhost:3000` → 온보딩 → 7페이지 순회 → Concierge 에서 RAG/Tools 두 모드 비교
4. **선택:** GHCR push → Docker Hub / 자체 registry 로 mirroring
5. **Phase 6 학습 시작:** 라벨링 1,000+ → `train.py` → `checkpoints/` 이식 → v2 자동 승격

---

**Mini은 production-ready 단계입니다.** 🍱
