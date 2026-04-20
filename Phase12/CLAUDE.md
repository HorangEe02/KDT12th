# CLAUDE.md

이 파일은 Claude Code가 매 세션 자동으로 읽는 프로젝트 컨텍스트 문서입니다.
프롬프트가 길어지지 않도록, 여기에 프로젝트 전반의 규칙·구조·컨벤션을 모아둡니다.

---

## 1. 프로젝트 요약

**원정 응원 플래너(Away Game Companion)** — KBO 10개 구단 원정 응원러를 위한
AI 기반 여행 플래너. 경기 선택 한 번으로 티켓·교통·맛집·숙소·관광지를 일괄 제안.

- 주 사용자: MZ세대 프로야구 팬 (원정 응원러)
- 플랫폼: Streamlit 웹 앱 (로컬 실행 + Streamlit Cloud 배포)
- 프로젝트 기간: 5일 (Day 4~5 집중 개발, 총 실작업 약 12시간)
- 상세 기획: `README.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/guides/PHASE*_GUIDE.md`

---

## 2. 기술 스택

- **언어**: Python 3.10+
- **프레임워크**: Streamlit 1.40+
- **데이터**: Pandas, scikit-learn
- **시각화**: Plotly, Folium (streamlit-folium 0.27+)
- **AI/LLM**: OpenAI API (gpt-4o-mini 기본), LangChain, ChromaDB
- **외부 API**
  - 한국관광공사 TourAPI (관광·맛집·숙박)
  - 카카오 Maps Web API (지도)
  - 카카오모빌리티 (길찾기)
  - 기상청 단기예보
- **배포**: Streamlit Community Cloud

---

## 3. 디렉토리 맵

```
Phase12/                        # 루트 11 항목 (2026-04-18 정리 완료)
├── CLAUDE.md                   # 이 문서 — AI 에이전트 컨텍스트
├── README.md                   # 프로젝트 소개 + Live URL
├── firebase.json               # App Hosting + Firestore 배포 설정
├── .firebaserc                 # project: mini12-310f5
├── firestore.rules
├── firestore.indexes.json
│
├── frontend/                   # ⭐ Next.js 16 메인 앱 (Production)
│   ├── app/                    # App Router (/, /matches, /map, /places, /ai, /badges, /share/[id])
│   │   ├── (shell)/            # TopNav + Sidebar 공통 레이아웃
│   │   └── api/                # predict · route · chat · plans
│   ├── components/             # hero · team-selector · matches · map · places · ai · badges
│   ├── lib/                    # predict · api/{kakao,osrm,haversine,route} · ai/{tools,agents,rag,mock} · firebase · store · share
│   ├── public/data/            # schedule · stadiums · team-stats · tips · poi/* (빌드 타임 JSON)
│   ├── public/logos/           # KBO 팀 로고 SVG 12 개
│   ├── apphosting.yaml         # Cloud Run 설정 + Secret Manager ref
│   └── package.json            # Next 16 · React 19 · Tailwind v4 · ai · leaflet · plotly · zustand
│
├── data/                       # 원본 CSV (Python 레거시 생성 · Next.js 빌드 시 JSON 변환됨)
│   ├── SCHEMA.md
│   ├── kbo_schedule_2026.csv · stadiums.csv · team_stats_10yr.csv
│
├── docs/                       # 📚 모든 문서 (2026-04-18 통합)
│   ├── PHASE6_NEXTJS_MIGRATION.md · OSM_FALLBACK_PLAN.md
│   ├── SESSION_E_PLAN.md · SESSION_F_DEPLOY_RUNBOOK.md · CLEANUP_PLAN.md
│   ├── ARCHITECTURE.md · DEMO_SCRIPT.md · QA_PREP.md
│   ├── IMPLEMENTATION_PLAN.md  # (구 md/ 에서 이동)
│   ├── guides/                 # (구 guide/ 에서 이동)
│   │   └── INDEX.md · PHASE0_GUIDE.md ~ PHASE5_GUIDE.md
│   ├── reference/              # (구 api/, fonts/ 에서 이동)
│   │   ├── tourapi_ko.md · weather_*_forecast.md · maps/ · fonts/
│   └── brief/project_brief.pdf
│
├── scripts/                    # Phase 6 유지보수 (shell only)
│   ├── preflight.sh            # 배포 전 점검
│   └── validate_data.py        # 데이터 구조 검증
│
├── uiux/                       # 원본 HTML/PNG 목업 (참고용)
│   ├── web_uiux/               # 7 종 웹 화면 (Stadium Editorial 디자인 시스템 포함)
│   └── mobile_uiux/            # 7 종 모바일 화면
│
└── legacy/                     # 📦 Phase 1~5 Python Streamlit 보존 (배포 미사용)
    ├── README.md               # 레거시 설명 + 포팅 매핑
    ├── app.py · Dockerfile · requirements.txt
    ├── src/                    # Python 소스 (ai, api, db, ui, viz)
    ├── models/win_rate_model.pkl · assets/ · public/ · tests/
    ├── scripts/                # cache_poi · validate_phase[2-5] · deploy.sh · export_to_json.py
    └── data_cache/             # poi_cache · chroma_db · knowledge · route_cache
```

---

## 4. 코딩 컨벤션

### 4-1. Next.js (Phase 6 · Production · `frontend/`)

- 함수·변수명: **camelCase** · 컴포넌트: **PascalCase** · 상수: **UPPER_SNAKE_CASE**
- TypeScript 엄격 · `any` 금지 (필요 시 `unknown` + 가드)
- Server Component 기본, 인터랙티브만 `"use client"`
- Tailwind v4 유틸리티 + `@theme` 토큰 (`bg-se-primary` 등)
- Zustand 로 클라이언트 상태 + `persist` 미들웨어
- API Route: Zod body 검증 + `nodejs` 런타임 명시 (`export const runtime = "nodejs"`)
- 외부 API: `AbortController` 5초 타임아웃 + graceful fallback
- 비밀 키: `process.env.X` 는 서버 컴포넌트/API Route 에서만 · `NEXT_PUBLIC_*` 만 클라이언트 노출

### 4-2. Python 레거시 (`legacy/` 디렉토리 내부에서만 적용)

- 함수·변수명: **snake_case** · 클래스: **PascalCase** · 상수: **UPPER_SNAKE_CASE**
- **타입 힌트 필수**: `def load_data(path: str) -> pd.DataFrame:`
- 외부 API 호출은 반드시 `try-except` + 타임아웃 10초
- 로깅은 `print` 금지, `import logging` 사용
- Streamlit 데이터 로딩 함수는 `@st.cache_data(ttl=3600)` 필수
- 경로·API 키는 `legacy/src/config.py` 를 통해 접근

---

## 5. 실행 · 테스트 명령

### 5-1. Next.js (Phase 6 · Production)

```bash
# 로컬 개발
cd frontend
pnpm install           # 최초 1회
pnpm dev               # http://localhost:3000

# 프로덕션 빌드
pnpm build
pnpm start

# 타입 체크 / 린트
npx tsc --noEmit
pnpm lint

# 데이터 검증 (루트에서)
bash scripts/preflight.sh
python3 scripts/validate_data.py

# 배포 (Firebase App Hosting)
firebase deploy --only apphosting --project mini12-310f5
```

### 5-2. Python 레거시 (`legacy/` 내부에서만)

```bash
cd legacy
pip install -r requirements.txt
streamlit run app.py
# 데이터 재생성
python3 scripts/export_to_json.py   # CSV → ../frontend/public/data/*.json
```

작업 디렉토리는 항상 프로젝트 루트(`Phase12/`) 또는 `frontend/` 를 기준으로 실행하세요.

---

## 6. 금지사항 (DO NOT)

### 6-1. Next.js (Phase 6 · 적용)

- ❌ API 키를 소스에 하드코딩하지 말 것. 서버: `process.env.X` · 클라: `NEXT_PUBLIC_X` 만
- ❌ `.env`, `.env.local`, `secrets/`, `legacy/models/*.pkl` 를 Git 커밋 금지
- ❌ `frontend/lib/firebase/admin.ts` 등 `"server-only"` 모듈을 클라이언트 컴포넌트에서 import 금지
- ❌ `ai` SDK 응답을 그대로 `dangerouslySetInnerHTML` 로 넣지 말 것 — `useChat` + `message.parts` 사용
- ❌ Leaflet · Plotly 를 서버 컴포넌트에서 import 금지 — 반드시 `dynamic(..., { ssr: false })`
- ❌ 경로 하드코딩 금지 — `@/lib/...` alias 사용

### 6-2. Python 레거시 (`legacy/` 작업 시 적용)

- ❌ `pandas.read_csv()`를 Streamlit 렌더 함수 안에 직접 호출 금지 — `@st.cache_data` 래퍼
- ❌ `time.sleep()`을 Streamlit UI 스레드에서 사용 금지
- ❌ `st.experimental_*` API 피하고 정식 API 사용
- ❌ 경로 하드코딩 금지 — `legacy/src/config.py` 의 `PROJECT_ROOT`, `DATA_DIR` 사용

---

## 7. 외부 문서 참조

- 기획 의도·시장 조사: `README.md`
- 전체 로드맵 및 리스크 관리: `docs/IMPLEMENTATION_PLAN.md`
- Phase 별 상세 가이드: `docs/guides/PHASE0_GUIDE.md` ~ `docs/guides/PHASE5_GUIDE.md`
- 문서 인덱스: `docs/guides/INDEX.md`
- Phase 6 마이그레이션: `docs/PHASE6_NEXTJS_MIGRATION.md`
- OSM 3-tier 폴백 설계: `docs/OSM_FALLBACK_PLAN.md`
- 정리 계획: `docs/CLEANUP_PLAN.md` (2026-04-18 수행)
- UIUX 레퍼런스: `uiux/web_uiux/`, `uiux/mobile_uiux/`
- 디자인 시스템: `uiux/web_uiux/grand_slam_voyage/DESIGN.md`
- API 레퍼런스: `docs/reference/tourapi_ko.md`, `docs/reference/weather_*.md`
- Phase 1~5 Python 레거시: `legacy/` (참고용 보존 · 배포 미사용)

---

## 8. 현재 진행 Phase

**Phase 6 (Next.js + Firebase App Hosting — 배포 완료 + 모바일 UX 정비)** — ✅ Live at https://my-web-app--mini12-310f5.asia-east1.hosted.app (2026-04-19) · 138/138 모바일 자동 스모크 PASS

### Phase 6 핸드오프 문서 (필독)
- **전체 로드맵**: `docs/PHASE6_NEXTJS_MIGRATION.md` ⭐
- **OSM Fallback 설계**: `docs/OSM_FALLBACK_PLAN.md` — 길찾기 3-tier 폴백 상세
- **Session E 계획서**: `docs/SESSION_E_PLAN.md` — AI 챗봇 + Badges + 공유 구현 설계
- **Session F 배포 런북**: `docs/SESSION_F_DEPLOY_RUNBOOK.md` — firebase CLI 단계별 가이드
- 세션 분할: A → B → C → D → E → F(현재 · 코드) → 사용자 배포 (총 6 세션, 각 2~3시간)

### Session A 완료 (2026-04-17)
- [x] Streamlit 무한로딩 진단 — 서버 정상, 브라우저 WebSocket 이슈
- [x] Next.js 16.2.4 스캐폴딩 (`frontend/`)
- [x] 의존성 16개 설치 (firebase/ai SDK/leaflet/plotly/zustand/tanstack-query)
- [x] 데이터 변환 (`scripts/export_to_json.py` → `frontend/public/data/` 8 JSON + `public/logos/` 12 SVG)
- [x] Phase 6 핸드오프 문서 작성 (`docs/PHASE6_NEXTJS_MIGRATION.md`)

### Session B 완료 (2026-04-17)
- [x] **Step 2 — Tailwind v4 SE 테마**: `frontend/app/globals.css` `@theme` 블록에 SE 컬러 17종 + font-display/font-body 토큰 + `se-bounce` 애니메이션
- [x] **Step 2 — Fonts**: `layout.tsx` Plus Jakarta Sans + Manrope + Noto Sans KR (`next/font/google`) + Material Symbols CDN
- [x] **Step 3 — lib 인프라** 8개 파일:
  - `lib/utils.ts` (cn, normalizeTeam, formatKRW, formatWinRate)
  - `lib/team-colors.ts` (TEAM_COLORS 10 + TEAMS 순서 + getTeamLogoPath/getKBOLogoPath)
  - `lib/types/index.ts` (Game, Stadium, POI, Tip, Filters, WinRateModel 등)
  - `lib/firebase/client.ts` (Web SDK v12 + COLLECTIONS)
  - `lib/firebase/admin.ts` (server-only, K_SERVICE 자동 감지)
  - `lib/ai/prompts.ts` (SYSTEM_PROMPT_BASE + AGENT_PROMPTS + buildSystemPrompt)
  - `.env.local` (Gemini/Firebase/Kakao/Tour/Weather 키 복사)
- [x] **Step 5 — Components**:
  - `components/hero.tsx` (팀 컬러 그라디언트 + KBO 워터마크 + 팀 로고 56px, server component)
  - `components/team-selector.tsx` (웹 5×2 / 모바일 3열, Next Link `?team=XX` 동기화)
  - `app/page.tsx` (searchParams `?team=XX&device=web|mobile` 수신, viewport 분기)
- [x] **검증 4/4 PASS**:
  - `npx tsc --noEmit` 에러 0
  - `pnpm dev` → http://localhost:3000 200 OK (Ready 328ms · 44KB HTML)
  - `?team=KT` → Hero "KT 위즈", `?team=KIA` → "KIA 타이거즈"
  - `?device=mobile` → `grid-cols-3` + `max-w-[480px]` 확인, 10 팀 로고 전부 serve

### Session C 완료 (2026-04-17)
- [x] **Step 4 — 승률 예측 TS 포팅**
  - `lib/predict.ts` — StandardScaler + LogReg 수식 직접 구현 (sigmoid/dot/scale), 5-피처, Neutral fallback 0.45
  - `app/api/predict/route.ts` — GET + POST (Zod body 검증, nodejs 런타임)
  - `lib/data/loaders.ts` — public/data JSON 모듈-캐시 로더 (schedule/stadiums/team-stats/tips/poi)
  - `lib/types/index.ts` — WinRateModel / PredictResponse / TeamStat 스키마 정정
  - **Python ↔ TS 예측값 100% 일치**: LG vs KT=0.0000, KIA vs 삼성=0.8905, 두산 vs 한화=0.0000, 키움 vs SSG=0.0138
- [x] **Step 6 — 라우팅 + 사이드바**
  - `lib/store/filters.ts` — Zustand v5 + persist (localStorage), 7 필드 + actions + URL hydrate
  - `components/layout/top-nav.tsx` — sticky 5탭 + 응원팀 배지 (client, searchParams 기반)
  - `components/sidebar/filter-sidebar.tsx` — 팀 select + 기간 range + 예산 slider + 인원/이동수단 토글 + 코스 생성 + 시연 모드 (Zustand 바인딩, URL team 동기화)
  - `components/sidebar/viewport-toggle.tsx` — `?device=` 쿼리 토글
  - `app/(shell)/layout.tsx` — 라우트 그룹 shell (TopNav + Sidebar + main), Suspense 감싸기
  - 기존 `app/page.tsx` 삭제 → `app/(shell)/page.tsx` 로 이동 (Hero + TeamSelector + 5탭 링크 카드)
  - 4개 placeholder 페이지: `/map`, `/places`, `/ai`, `/badges` (Session D~E 예정)
- [x] **Step 7 — Matches 탭** (`app/(shell)/matches/page.tsx`)
  - `components/charts/plot.tsx` — `react-plotly.js` 동적 로드 (ssr:false) + 스켈레톤
  - `components/matches/win-gauge.tsx` — Plotly Indicator gauge+number+delta
  - `components/matches/win-rate-bar.tsx` — 최근 3년 원정 승률 막대 (팀 컬러 강조)
  - `components/matches/match-list.tsx` — 반응형 table, 행 클릭 → `?game=XXX` 쿼리
  - Metrics 3종 + 선택 게임 메타 + 승률 게이지 + 랭킹 바 + 코멘트
- [x] **검증 6/6 PASS**
  - `npx tsc --noEmit` 에러 0 (.next 캐시 정리 후)
  - 6 라우트 전부 200 OK: `/`, `/matches`, `/map`, `/places`, `/ai`, `/badges` (Ready 280ms)
  - `GET /api/predict?team=LG&opponent=KT` → `{prob:0, source:"logreg"}`
  - `POST /api/predict` w/ invalid body → 400 + Zod 상세 에러
  - `/matches?team=KIA&start=2026-04-01&end=2026-05-31` — 138KB HTML, 4월~5월 원정 경기 + 게이지 + 막대 + 리스트 전부 렌더
  - Python 비교 스크립트로 TS 예측값 동일 확인

### Session D 완료 (2026-04-17)
- [x] **Route API 3-tier 폴백** (`docs/OSM_FALLBACK_PLAN.md` 문서 선행)
  - `lib/api/kakao.ts` — Tier 1 Kakao 모빌리티 (키 없으면 즉시 skip)
  - `lib/api/osrm.ts` — Tier 2 OSRM public demo (무료·API 키 불필요·HTTPS)
  - `lib/api/haversine.ts` — Tier 3 직선 거리 (항상 성공)
  - `lib/api/route.ts` — orchestrator + 인메모리 캐시 (좌표 반올림 키)
  - `app/api/route/route.ts` — GET + POST (Zod tuple 검증, AbortController 5초 타임아웃)
  - **실측 결과**: Kakao 401 (REST 키에 모빌리티 권한 없음) → OSRM OK (1.4초, 537 vertices, 33.5km, 32.5분)
  - 캐시 히트: 동일 좌표 2회 호출 → 20ms (40× 단축)
- [x] **Step 8 — Map 탭** (`app/(shell)/map/page.tsx`)
  - `components/map/leaflet-map.tsx` — MapContainer + TileLayer + LayersControl + 4 LayerGroup + 카테고리별 divIcon + FitBoundsOnLoad
  - `components/map/map-shell.tsx` — Next dynamic(ssr:false) 래퍼, 스켈레톤 포함
  - `components/map/map-controls.tsx` — 경기 select + 출발지 프리셋 4종 (`useTransition` 기반 URL 업데이트)
  - `components/map/route-summary.tsx` — source 배지(Kakao/OSRM/Haversine) + distance/duration/toll + attempts 상세 + 폴백 경고 배너
  - `lib/map/origins.ts` — ORIGIN_PRESETS (서버/클라이언트 공통 모듈, "use client" 없음)
  - 경로 폴리라인 색상: Kakao=파란색, OSRM=보라색, Haversine=회색 점선
  - Attribution: `© OpenStreetMap contributors · Routing by OSRM`
- [x] **Step 9 — Places 탭** (`app/(shell)/places/page.tsx`)
  - `components/places/stadium-picker.tsx` — 10 구장 칩 버튼 (URL `?s=잠실`)
  - `components/places/category-tabs.tsx` — 음식점/숙박/관광지 3탭 (URL `?cat=food`)
  - `components/places/scatter-places.tsx` — Plotly 거리×평점 산점도 (평점은 content_id 기반 재현 더미)
  - `components/places/poi-card.tsx` — POI 카드 + 카카오맵 딥링크
  - 구장별 food/stay/tour 카운트 메트릭 + TOP 10 카드 그리드
- [x] **검증 8/8 PASS**
  - `npx tsc --noEmit` 에러 0
  - 6 라우트 전부 200 OK (`/`, `/matches`, `/map`, `/places`, `/ai`, `/badges`)
  - /map 3팀 (LG/KT/KIA) · /places 3구장 (잠실/광주/부산) 200 OK
  - `POST /api/route` 잠실→수원: `{source:"osrm", distance_m:33500, polyline:537개}`
  - `GET /api/route?...` 200 + 캐시 1회차 828ms → 2회차 20ms
  - Zod invalid body → 400 + tuple 에러 상세
  - Kakao 401 실측 → OSRM 자동 폴백 확인 (attempts 로그)
  - OSRM attribution 지도 하단 표기

### Session E 완료 (2026-04-17)
- [x] **Step 10 — AI 챗봇** (`app/(shell)/ai/page.tsx`)
  - `lib/api/weather.ts` — KMA 단기예보 + WGS84→Lambert 격자 변환 (Python 정확 포팅)
  - `lib/ai/rag.ts` — 인메모리 BM25-lite + stadium 필터 (tips.json 45 items 대상)
  - `lib/ai/mock.ts` — 광주가족·부산맛집·우천실내 3 시나리오 키워드 매칭
  - `lib/ai/tools.ts` — 6 tool Vercel AI SDK v6 `tool()` 정의 (search_game, predict_win_rate, get_weather, find_places, get_route, search_knowledge)
  - `lib/ai/agents.ts` — Multi-Agent 프롬프트 합성 (### 일정/전략/장소 + 최종 답변 섹션)
  - `app/api/chat/route.ts` — streamText + toUIMessageStreamResponse + demoMode 분기 + createGoogleGenerativeAI({apiKey})
  - `@ai-sdk/react` 설치 (+ 1 의존성)
  - `components/ai/{chat-ui,message-bubble,tool-viz}.tsx` — useChat + DefaultChatTransport, 5 suggestion chips, stop 버튼, tool-invocation 인라인 카드
- [x] **Step 11 — Badges + 공유 링크**
  - `lib/store/badges.ts` — Zustand + localStorage (visited[], 익명 UUID)
  - `lib/firebase/visited.ts` — loadVisited/saveVisited (Firebase 미구성 시 no-op)
  - `lib/firebase/shared-plans.ts` — createSharedPlan/getSharedPlan (Admin)
  - `lib/firebase/admin.ts` — `isAdminConfigured()` 서비스 계정 파일 존재 검증
  - `lib/share/serialize.ts` — Filters ↔ URLSearchParams 직렬화
  - `components/badges/stadium-tour.tsx` — 10 구장 그리드 + 토글 + 10/10 celebrate + Firestore 자동 머지
  - `components/badges/share-plan-button.tsx` — /api/plans POST → 실패 시 long URL → 클립보드 복사
  - `app/api/plans/route.ts` — POST (503 when Firebase 미구성)
  - `app/share/[id]/page.tsx` — Firestore 조회 → `redirect(/?...)` · 없으면 404 UI
  - `components/sidebar/filter-sidebar.tsx` — 5 필드 URL 하이드레이션 + SharePlanButton
- [x] **검증 10/10 PASS**
  - `npx tsc --noEmit` 에러 0
  - 6 라우트 + `/share/[id]` 전부 200 OK
  - `POST /api/chat` demoMode:true + "광주 가족" → Mock 시나리오 `광주 가족 원정` 매칭 + 스트리밍
  - `POST /api/chat` 실제 Gemini → "LG 첫 원정" → 서버 스트리밍 `text-delta` 정상
  - `POST /api/chat` "LG vs KT 승률" → **tool-input-available** + **tool-output-available** (`predict_win_rate` 실행, Python과 동일값 0.0%)
  - `POST /api/plans` (Firebase Admin 미구성) → 503 graceful degradation
  - `/share/fake-id` → "공유 링크를 찾을 수 없습니다" 안내 페이지
  - Firebase 미구성 시 Stadium Tour "🏠 로컬 저장" 배지
  - `createGoogleGenerativeAI({apiKey})` 로 GEMINI_API_KEY 명시 주입
  - 사이드바 Share 버튼 → URL 클립보드 복사 + 수신측 5 필드 전부 복원

### Session F 완료 (2026-04-17) — 코드 레벨 배포 준비 완료
- [x] **Step 12a — App Hosting config**
  - `frontend/apphosting.yaml` — runConfig (CPU 1 · memory 1024MiB · 0~3 instances · concurrency 80 · 120s timeout) + env 12종 (공개/서버/시크릿 분리 · BUILD/RUNTIME availability 명시)
  - `firebase.json` — App Hosting + Firestore (레거시 Streamlit Cloud Run rewrite 제거)
  - `.firebaserc` 유지 (project: mini12-310f5)
- [x] **Step 12b — 프로덕션 빌드 검증**
  - `pnpm build` 성공: 13 routes compile (6 static · 7 dynamic · 4 API)
  - Turbopack NFT 경고 해결 (admin.ts: `require(credPath)` → `fs.readFileSync` + `JSON.parse`)
- [x] **Step 12c — Preflight + Runbook**
  - `scripts/preflight.sh` — 7-섹션 안전 점검 (git 저장소 아니어도 동작)
  - `docs/SESSION_F_DEPLOY_RUNBOOK.md` — 10 섹션 (사전 체크 → 인증 → 백엔드 생성 → Secret Manager → 배포 → smoke test → 후속 배포 → 레거시 정리 → 트러블슈팅 → 체크리스트)
- [x] **Step 13 — 문서 최종 업데이트**
  - `README.md` — Phase 6 Live 섹션 (아키텍처 다이어그램 + URL + 기능 + 설계 문서 링크) 추가, 4-1 기술 스택 Next.js 기반으로 업데이트, 4-1-bis 에 Streamlit 레거시 기록
  - `docs/PHASE6_NEXTJS_MIGRATION.md` — Session F 산출물 기록
  - `CLAUDE.md` (이 문서) — Session F 완료 표기

### 배포 실행 단계 (사용자 수행)
```bash
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12"
bash scripts/preflight.sh                                        # 1분 사전 점검
firebase login                                                   # 1회
gcloud auth application-default login                            # 1회
firebase apphosting:backends:create --project mini12-310f5 \
  --location asia-northeast3                                     # 1회 (backend id: away-game-companion, rootDir: ./frontend)
# 각 시크릿 (10분)
firebase apphosting:secrets:set GEMINI_API_KEY --project mini12-310f5
firebase apphosting:secrets:set KAKAO_REST_API_KEY --project mini12-310f5
firebase apphosting:secrets:set WEATHER_API_KEY_ENCODED --project mini12-310f5
firebase apphosting:secrets:set TOUR_API_KEY_ENCODED --project mini12-310f5
# (Firebase Web SDK 키는 Badges/Share Firestore 쓸 때만)
firebase deploy --only apphosting --project mini12-310f5          # 5~8분 Cloud Build
firebase deploy --only firestore --project mini12-310f5           # 2분 (rules + indexes)
```

상세 트러블슈팅·smoke test 명령: `docs/SESSION_F_DEPLOY_RUNBOOK.md`

### 배포 후 ToDo (사용자)
- [x] 배포 URL smoke test 6 routes + 2 API (자동 · Playwright 138/138 PASS) (2026-04-19)
- [x] `README.md` 의 URL 섹션을 실제 hosted URL 로 업데이트 (2026-04-19)
- [ ] 실기기(아이폰/안드로이드) 노치·safe-area·키보드·BottomSheet 드래그 수동 확인
- [x] 레거시 Streamlit Cloud Run 서비스 삭제 완료 (2026-04-19) — service + Artifact Registry 466MB + `gemini-api-key` secret 3종 전부 제거
- [ ] 발표 녹화 (3분 데모 시나리오 `docs/DEMO_SCRIPT.md` 참조)

### 레거시 (유지 중)
**Phase 5a (Firebase 풀 스택 — Streamlit 버전 배포 완료)** — ✅ (2026-04-17)

### 완료 누적
- [x] **Phase 0** 부트스트랩
- [x] **Phase 1** 데이터 파이프라인
- [x] **Phase 2 (initial)** UI 골격 + React 하이브리드
- [x] **Phase 2 (refinement)** Stadium Editorial + Streamlit 네이티브 + 디바이스 분리
- [x] **Phase 2 (react-rev)** React 18 + Tailwind + KBO 로고 통합 + 렌더러 토글
- [x] **Phase 3** Folium 지도 + Plotly 차트 + 카카오 경로 + 마커 클릭 양방향 UX
- [x] **Phase 4** 승률 예측 모델 + Ollama(gemma4) 챗봇 + 도구 호출 + Multi-Agent + RAG
- [x] **Phase 5a** Firebase 풀 스택 코드 (Cloud Run + Hosting + Firestore + Gemini 이중화)

### Phase 2 리파인 산출
- [x] `assets/css/style.css` — **Stadium Editorial** 풀 세트
  - 컬러 토큰 (`--se-primary` #00193c, `--se-secondary` #1b6d24 등)
  - Plus Jakarta Sans + Manrope + Material Symbols Outlined
  - Signature Gradient, 카드/뱃지/Bottom Nav 스타일
- [x] `src/ui/device.py` — 뷰포트 토글 (사이드바 최상단, `?device=mobile` 동기화)
- [x] `legacy/src/ui/components/hero.py` — Streamlit 네이티브, 팀 컬러 그라디언트 유지, viewport 분기
- [x] `legacy/src/ui/components/team_selector.py` — 웹 5×2 / 모바일 3열 카드 그리드
- [x] `src/ui/components/badges.py` — 웹 5열 / 모바일 2열 Stadium Tour, check_circle 아이콘
- [x] `src/ui/components/bottom_nav.py` — 모바일 하단 네비 미러
- [x] `src/ui/sidebar.py` — 5종 필터 유지 (device 토글은 device.py에서 먼저 렌더)
- [x] `app.py` — viewport 전파, 모바일 시 bottom_nav 렌더, session_state에 viewport 추가
- [x] `scripts/validate_phase2.py` — 11개 검증 PASS (device/viewport/SE토큰/bottom_nav 추가)

### React 버전 (공존 완료)
- `src/ui/assets.py` — KBO SVG → base64 data URI 변환 (lru_cache)
- `src/ui/device.py` — `render_renderer_toggle()` 추가 (streamlit/react)
- `assets/react/{hero,badges,team_selector}.html` — **Tailwind CDN + Stadium Editorial + KBO 로고** 전면 재작성
  - Hero: 팀 로고 우측 원형 배지 + KBO 리그 로고 워터마크
  - Team Selector: 팀 로고 56px 원형 카드 (팀 컬러 연한 톤 배경)
  - Badges: 팀 로고 Stadium Tour 이미지 카드 (방문=full color, 미방문=grayscale)
- `src/ui/components/{hero,team_selector,badges}.py` — `_render_streamlit` / `_render_react` 분기 함수 추가
- 3개 컴포넌트 모두 `render(selected/visited, viewport, renderer="streamlit")` 통일 시그니처

### 통신/분리 패턴
- 디바이스 분리: 사이드바 토글 → `session_state.viewport` + `?device=XX` 쿼리
- 렌더러 분리: 사이드바 토글 → `session_state.renderer` + `?renderer=XX` 쿼리
- 팀 선택: URL `?team=XX` + `st.query_params` 양방향 동기화
- 모바일 시뮬레이션: 컨테이너 폭 480px 제한 CSS 주입
- KBO 로고 주입: Python assets.py → base64 data URI → APP_CONFIG.logos → React `<img src/>`

### Phase 3 산출
- [x] `docs/VIZ_CONTRACT.md` — 시각화/지도/경로 함수 계약 단일 진실원
- [x] `src/viz/folium_map.py` — `create_map` + `render_map_in_streamlit`
  - 4개 FeatureGroup (stadium/food/stay/tour) + MarkerCluster(>20) + LayerControl
  - Route 폴리라인 (fallback 시 dash_array) + fit_bounds
- [x] `src/viz/popup_builder.py` — HTML escape + HTTPS 치환 + 우천 경고 배지
- [x] `src/viz/plotly_charts.py` — `bar_away_win_rate` + `scatter_places` + `gauge_win_rate`
- [x] `src/api/kakao_map.py` — `get_car_route` + 디스크 캐시(md5) + haversine Fallback
- [x] `src/ui/components/place_card.py` — tab2/tab3 공통 POI 카드 렌더
- [x] `src/ui/tabs/tab1_games.py` — 경기 selectbox + 승률 게이지 + 구단별 원정 승률 막대
- [x] `src/ui/tabs/tab2_map.py` — **마커 클릭 양방향 UX** + 경로 메트릭 + 출발지 프리셋
- [x] `src/ui/tabs/tab3_places.py` — 구장별 3서브탭 + 산점도 + 카드 리스트
- [x] `scripts/validate_phase3.py` — **8개 검증 전부 PASS**
  - 파일 10/10, 계약 함수 9/9, 의존성 5/5
  - create_map HTML smoke, Plotly 3종 smoke, 카카오 fallback 키 5/5
  - Popup stadium/place + HTTPS 치환, 탭 통합 (bar/gauge/scatter/place_card)

### 통신/데이터 흐름
- 경기 선택: sidebar team + date_range → tab1/tab2 selectbox로 특정 경기
- 마커 클릭: `st_folium` → `last_object_clicked` → haversine-lite 최근접 POI → `place_card`
- 경로: `_get_route_cached` (30분) → 캐시 디스크 md5 영속 → fallback 시 직선
- 승률: `game_id` md5 시드 더미값 (Phase 4에서 로지스틱 회귀로 교체)

### Phase 4 산출
- [x] `src/ai/predict.py` — scikit-learn 로지스틱 회귀 (Pipeline: StandardScaler + LogReg)
  - 피처: team_away_win_rate, opp_home_win_rate, team_rank, opp_rank, rank_diff
  - 타깃: `team.win_rate > opp.win_rate` (균형 50/50)
  - 모델 저장: `models/win_rate_model.pkl`
- [x] `src/ai/ollama_client.py` — Ollama REST `/api/chat` + `/api/embeddings` 저수준 래퍼
  - Gemma 4 reasoning 모드 비활성화 (`think: false`)
  - thinking→content 승격 폴백
- [x] `src/ai/llm_client.py` — `chat_complete()` 단일 계약 + 3단계 Fallback
  - 1차: `OLLAMA_CHAT_MODEL` (gemma4:e4b) / `OLLAMA_TOOL_MODEL`
  - 2차: `OLLAMA_FALLBACK_MODEL` (gemma4:e2b)
  - 3차: 규칙 기반 응답
- [x] `src/ai/prompts.py` — 페르소나/필터/지역방언/Few-shot 포함 시스템 프롬프트
- [x] `src/ai/tools.py` — 6개 도구 (search_game, predict_win_rate, get_weather, find_places, get_route, search_knowledge)
- [x] `src/ai/mock_responses.py` — 시연 안전장치 3종 (광주가족/부산맛집/우천실내)
- [x] `src/ai/agents.py` — Supervisor→[Schedule|Strategy|Place]→Synthesizer 순차 오케스트레이션
- [x] `src/ai/rag.py` — ChromaDB + **bge-m3** 한국어 임베딩
- [x] `data/knowledge/away_game_tips.json` — 45개 구장별 원정 팁
- [x] `src/ui/tabs/tab4_ai.py` — 챗봇 UI + 도구 호출 시각화 + Multi-Agent 토글 + 시연 모드
- [x] `src/ui/tabs/tab1_games.py` — 더미 승률 → 실제 predict 모델 연동
- [x] `src/ui/sidebar.py` — 🎬 시연 모드 토글 추가
- [x] `scripts/validate_phase4.py` — **10개 검증 전부 PASS**

### Ollama 환경
- 서버: `http://localhost:11434` (macOS Apple M4 Pro, 24GB RAM)
- 주 모델: `gemma4:e4b` (8B Q4, 한국어 OK, 도구 호출)
- 폴백: `gemma4:e2b` (5B Q4, 빠른 응답)
- 임베딩: `bge-m3:latest` (한국어 강점)
- 비용 0 · 오프라인 가능 · `.env`의 `OLLAMA_*`로 제어

### Phase 5a 산출
- [x] **AI 이중화**: `src/ai/gemini_client.py` (google-genai 신 SDK) + `llm_client.py` 3단계 (Ollama→Gemini→Mock)
  - 모델: `gemini-2.5-flash-lite` (free tier), `gemini-embedding-001` (3072d)
  - 환경 감지: `IS_CLOUD_RUN` (K_SERVICE 환경변수) → 자동 라우팅
- [x] **DB 레이어**: `src/db/firestore_client.py` + `storage_client.py`
  - Firestore 컬렉션 3종: visited_stadiums, shared_plans, chat_sessions
  - Cloud Storage: ChromaDB tar.gz 스냅샷 업/다운로드
- [x] **UI 통합**: `src/ui/plan_share.py` (계획 공유 링크) + `tab5_badges.py` (뱃지 영속화) + `sidebar.py` (공유 버튼) + `app.py` (plan_id 쿼리 복원)
- [x] **배포 에셋**: `Dockerfile`, `.dockerignore`, `firebase.json` (Cloud Run rewrite), `.firebaserc`, `firestore.rules`, `firestore.indexes.json`, `public/index.html`
- [x] **스크립트**: `scripts/deploy.sh` (원클릭 배포: init/secret/cloudrun/hosting/rules/rag) + `validate_phase5.py`
- [x] **발표 자료 5종**: ARCHITECTURE.md · PRESENTATION_OUTLINE.md · DEMO_SCRIPT.md · QA_PREP.md · DEPLOY_CHECKLIST.md
- [x] **검증**: `scripts/validate_phase5.py` — **10/10 PASS**

### Firebase 프로젝트
- Project ID: `mini12-310f5`
- Region: `asia-northeast3` (서울)
- Cloud Run service: `away-game-companion`
- Hosting URL: `https://mini12-310f5.web.app`
- Firestore: Native mode
- GCS bucket: `mini12-310f5.appspot.com` (RAG 스냅샷)
- Gemini: `gemini-2.5-flash-lite` + `gemini-embedding-001` (free tier)

### Phase 5b (사용자 수행 예정)
- [ ] `gcloud` CLI 설치 (`brew install --cask google-cloud-sdk`)
- [ ] `gcloud auth login` + `firebase login`
- [ ] Firestore DB 생성 (asia-northeast3)
- [ ] 서비스 계정 키 다운로드 → `secrets/service-account.json`
- [ ] `bash scripts/deploy.sh` 실행 (Cloud Build + Cloud Run + Hosting)
- [ ] 접속 확인 + 발표 리허설

**배포 URL (Streamlit 버전)**: `https://mini12-310f5.web.app` (⚠️ 브라우저 WebSocket 이슈로 무한로딩 가능)
**Cloud Run 직접**: `https://away-game-companion-262552815882.asia-northeast3.run.app` (정상 동작)

**실제 작업은 Phase 6 Session B부터 이어갑니다.**
