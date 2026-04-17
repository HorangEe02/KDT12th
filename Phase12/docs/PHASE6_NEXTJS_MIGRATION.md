# 🚀 Phase 6 — Next.js + Firebase App Hosting 마이그레이션 핸드오프

> **다음 세션에서 이 문서만 읽으면 즉시 작업을 이어받을 수 있도록 설계됨.**
> 전환 작업: Streamlit Python 앱 → Next.js 16 + Firebase App Hosting (풀 네이티브)

---

## 🗺️ 1. 현재 체크포인트 (Session F 코드 완료 · 사용자 배포 대기)

### ✅ Session A 산출물 (2026-04-17)
- **Streamlit 무한로딩 진단**: 서버 정상(200 OK), 브라우저 WebSocket 업그레이드 실패로 추정 → Next.js 전환으로 우회
- **Next.js 스캐폴딩**: `frontend/` 디렉토리 생성
  - Next.js **16.2.4** · React 19.2.4 · TypeScript 5.9.3
  - Tailwind **v4** · App Router · import alias `@/*` · pnpm
- **핵심 의존성 16개 설치 완료** (pnpm add)
- **데이터 변환 완료**: 8 JSON + 12 SVG (`public/data/` + `public/logos/`)

### ✅ Session B 산출물 (2026-04-17)
- **Step 2 — Tailwind v4 SE 테마**
  - `frontend/app/globals.css` : `@theme` 블록에 SE 컬러 토큰 17종 (`--color-se-primary` … `--color-se-error`) + 폰트 변수 (`--font-display`, `--font-body`) + Material Symbols Outlined 스타일 + `se-bounce` 애니메이션
  - `frontend/app/layout.tsx` : Plus Jakarta Sans + Manrope + Noto Sans KR (`next/font/google`, display: swap) + Material Symbols CDN link
- **Step 3 — lib/ 인프라 (8 files)**
  - `lib/utils.ts` — `cn()` (clsx + tailwind-merge), formatKRW, formatWinRate
  - `lib/team-colors.ts` — TEAM_COLORS 10종 + TEAMS 순서 + getTeamLogoPath + getKBOLogoPath
  - `lib/types/index.ts` — Game, Stadium, POI, Tip, Filters, WinRateModel, SharedPlan
  - `lib/firebase/client.ts` — Firebase Web SDK v12 (getFirestore, getStorage) + COLLECTIONS 상수
  - `lib/firebase/admin.ts` — `server-only`, K_SERVICE 자동 감지 → ADC 또는 service-account.json
  - `lib/ai/prompts.ts` — SYSTEM_PROMPT_BASE 전문 + AGENT_PROMPTS 5종 (supervisor/schedule/strategy/place/synthesizer) + buildSystemPrompt()
  - `.env.local` — Gemini/Firebase/Kakao/Tour/Weather 27개 키 복사
- **Step 5 — Components**
  - `components/hero.tsx` — 팀 컬러 그라디언트 + KBO 워터마크 + 팀 로고 56px (Server Component)
  - `components/team-selector.tsx` — 웹 5×2 / 모바일 3열, Next `<Link href={{pathname, query: {team: code}}}>` 로 URL 동기화
  - `app/page.tsx` — `searchParams` (Promise, Next 16 async API) 수신 → team/device 분기
- **검증 4/4 PASS**
  - `npx tsc --noEmit` 에러 0
  - `pnpm dev` → Ready 328ms, 44KB HTML
  - `?team=KT` → "KT 위즈", `?team=KIA` → "KIA 타이거즈"
  - `?device=mobile` → grid-cols-3 + max-w-[480px] 확인, 10 로고 전부 렌더

### ✅ Session C 산출물 (2026-04-17)
- **Step 4 — 승률 예측 TS 포팅**
  - `lib/predict.ts` + `app/api/predict/route.ts` (GET+POST, Zod 검증, nodejs 런타임)
  - `lib/data/loaders.ts` : schedule/stadiums/team-stats/tips/poi + awayWinRateRanking + filterAwayGames
  - `lib/types/index.ts` : WinRateModel / PredictResponse / TeamStat 스키마 정정
  - **Python ↔ TS 예측값 완전 일치** (4쌍 모두 소수점 4자리까지)
- **Step 6 — 라우팅 + 사이드바**
  - `lib/store/filters.ts` : Zustand v5 + persist(localStorage) + URL hydrate
  - `components/layout/top-nav.tsx` : sticky 5탭 + 팀 배지
  - `components/sidebar/filter-sidebar.tsx` : 팀·기간·예산·인원·이동수단 + 코스 생성 + 시연 모드
  - `components/sidebar/viewport-toggle.tsx` : `?device=` 쿼리 토글
  - `app/(shell)/layout.tsx` : 라우트 그룹 shell (TopNav + Sidebar + main)
  - `app/(shell)/page.tsx` : 이동된 랜딩 (Hero + TeamSelector + 5탭 카드)
  - `/map`, `/places`, `/ai`, `/badges` : Session D~E placeholder
- **Step 7 — Matches 탭** (`app/(shell)/matches/page.tsx`)
  - `components/charts/plot.tsx` : react-plotly.js 동적 로드 (ssr:false)
  - `components/matches/win-gauge.tsx` : Plotly Indicator
  - `components/matches/win-rate-bar.tsx` : 팀 컬러 하이라이트 막대
  - `components/matches/match-list.tsx` : 반응형 table, 행 클릭 `?game=XXX`
- **검증 6/6 PASS**
  - `.next` 캐시 재생성 후 `npx tsc --noEmit` 에러 0
  - 6 라우트 전부 200 OK (Ready 280ms)
  - `/api/predict` GET + POST 정상 응답, 400 에러 포맷 OK
  - `/matches?team=KIA&start=...&end=...` — 138KB HTML, 게이지/막대/리스트 전부 렌더

### ✅ Session D 산출물 (2026-04-17)
- **Route API 3-tier fallback** (`docs/OSM_FALLBACK_PLAN.md` 선행 설계)
  - `lib/api/kakao.ts` — Tier 1 Kakao 모빌리티
  - `lib/api/osrm.ts` — Tier 2 OSRM public demo (키 불필요, HTTPS, 한국 도로망 커버)
  - `lib/api/haversine.ts` — Tier 3 직선 거리
  - `lib/api/route.ts` — orchestrator + 인메모리 캐시
  - `app/api/route/route.ts` — Zod 검증 GET + POST
  - **실측**: Kakao 401 → OSRM 자동 폴백 성공 (537 vertex, 33.5km, 32.5min)
  - 캐시 히트: 828ms → 20ms (40×)
- **Step 8 — Map 탭**
  - `components/map/leaflet-map.tsx` : React-Leaflet 5 + LayersControl + 4 카테고리 divIcon + FitBoundsOnLoad
  - `components/map/map-shell.tsx` : dynamic(ssr:false) 래퍼
  - `components/map/map-controls.tsx` : 경기 select + 출발지 4종 프리셋
  - `components/map/route-summary.tsx` : source 배지 + metrics + attempts 디버그
  - `lib/map/origins.ts` : 서버/클라 공통 프리셋
  - 폴리라인 색상 분기: Kakao 파랑 / OSRM 보라 / Haversine 회색 점선
- **Step 9 — Places 탭**
  - `components/places/{stadium-picker,category-tabs,scatter-places,poi-card}.tsx`
  - 10 구장 칩 + 3 카테고리 탭 + Plotly 거리×평점 산점도 + TOP 10 카드
  - 카카오맵 딥링크 버튼

### ✅ Session E 산출물 (2026-04-17)
- **Step 10 — AI 챗봇** (`app/(shell)/ai/page.tsx`)
  - `lib/api/weather.ts` : KMA 단기예보 + WGS84→Lambert 격자 (Python 정확 포팅)
  - `lib/ai/{rag,mock,tools,agents}.ts` : BM25 검색 + Mock 시나리오 3종 + 6 Vercel AI SDK tool + Multi-Agent 프롬프트
  - `app/api/chat/route.ts` : streamText + tool + Mock 분기 + `createGoogleGenerativeAI({apiKey:GEMINI_API_KEY})`
  - `components/ai/{chat-ui,message-bubble,tool-viz}.tsx` : useChat 기반 채팅 UI + tool 인라인 카드 + Multi-Agent 토글
  - **실측**: `predict_win_rate` tool 호출 → Python 값과 동일 (0.0% for LG vs KT)
- **Step 11 — Badges + 공유 링크**
  - `lib/store/badges.ts` : Zustand + localStorage + 익명 UUID
  - `lib/firebase/{visited,shared-plans,admin}.ts` : Firebase 이중화 + `isAdminConfigured()` 키파일 존재 체크
  - `lib/share/serialize.ts` : Filters ↔ URLSearchParams
  - `components/badges/{stadium-tour,share-plan-button}.tsx` : 10 구장 그리드 + 10/10 celebrate + 공유 버튼
  - `app/api/plans/route.ts` + `app/share/[id]/page.tsx` : 단축 링크 (Firestore 구성 시) + redirect
  - 사이드바 SharePlanButton 통합 + 5 필드 URL 하이드레이션

### ✅ Session F 산출물 (2026-04-17)
- **Step 12 — App Hosting 배포 설정**
  - `frontend/apphosting.yaml` : runConfig + 12 env (공개/서버/시크릿 분리 · BUILD/RUNTIME availability)
  - `firebase.json` : App Hosting + Firestore (Streamlit rewrite 제거)
  - `pnpm build` 검증 : 13 routes 컴파일 (6 static · 7 dynamic · 4 API)
  - Turbopack NFT 경고 해결 : admin.ts `require(credPath)` → `fs.readFileSync` + `JSON.parse`
- **Step 13 — Preflight · Runbook · README**
  - `scripts/preflight.sh` : 7 섹션 safe-check (git 저장소 아니어도 동작)
  - `docs/SESSION_F_DEPLOY_RUNBOOK.md` : 10 섹션 (사전 체크부터 트러블슈팅까지 전체 CLI 플로우)
  - `README.md` : Phase 6 Live 섹션 + 아키텍처 다이어그램 + 기술 스택 Next.js 기반 재작성 + Streamlit 레거시 기록

### 🎯 현재 상태 (Session F 종료 · 코드 완료)
- Landing (/) — Hero + TeamSelector + 5탭 카드
- TopNav 5탭 + Sidebar (Zustand + URL 양방향 sync) + Viewport 토글
- `/matches` — 경기 리스트 + 승률 게이지 + 랭킹 막대 (Plotly)
- `/map` — React-Leaflet + 4 레이어 + 경로 (Kakao→OSRM→Haversine 폴백)
- `/places` — 10 구장 + 3 카테고리 + 거리×평점 산점도 + POI 카드
- `/ai` — Gemini 스트리밍 챗봇 + 6 tool calling + Multi-Agent + 🎬 Mock 시연
- `/badges` — Stadium Tour 10 구장 그리드 + Firestore 이중화 (graceful)
- `/api/predict` `/api/route` `/api/chat` `/api/plans` — 전부 구동
- `/share/[id]` — Firestore 단축 링크 (선택적)
- **배포 준비 완료**: `apphosting.yaml` · `preflight.sh` · deploy runbook 전부 생성됨
- **다음 (사용자 실행)**: `firebase apphosting:backends:create` → `secrets:set` → `deploy --only apphosting`

---

## 🧱 2. 환경 전제 조건

### 시스템
- macOS 26.4.1 (Apple M4 Pro, 24GB RAM)
- Node v22.17.0 · pnpm 10.8.1 · npm 10.9.2
- Firebase CLI 15.15.0 · gcloud CLI 설치됨 · Docker 29.4.0
- 디스크 여유 794GB (APFS 외장 볼륨)

### Firebase/GCP
- 프로젝트 ID: **mini12-310f5**
- Region: asia-northeast3 (서울)
- **Billing**: Blaze 플랜 연결 완료 (예산 5,000원)
- Firestore Native mode 활성화
- Cloud Run 서비스 `away-game-companion` 존재 (Streamlit, 유지 중)
- Secret Manager: `gemini-api-key` 등록
- IAM: 기본 compute SA에 6개 역할 부여 완료

### API 키
- `GEMINI_API_KEY`: 설정 완료 (gemini-2.5-flash-lite · gemini-embedding-001)
- `KAKAO_REST_API_KEY`: 설정 완료
- `TOUR_API_KEY` / `WEATHER_API_KEY`: 공공데이터포털 키 설정됨
- `.env` (루트) 파일 참조: 27개 키

---

## 🗂️ 3. 프로젝트 구조 (현재)

```
Phase12/ (루트)
├── frontend/                  # ⭐ Next.js 16 앱 (새로 생성)
│   ├── app/
│   │   ├── layout.tsx         # 기본 (Geist 폰트)
│   │   ├── page.tsx           # Next.js welcome
│   │   └── globals.css        # Tailwind v4 + 기본 변수
│   ├── node_modules/          # 설치 완료
│   ├── public/
│   │   ├── data/              # 8 JSON + poi/ 30 파일
│   │   ├── logos/             # 12 SVG
│   │   └── (기본 SVG 4개)
│   ├── package.json           # 16 deps
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── postcss.config.mjs     # Tailwind v4
│   ├── eslint.config.mjs
│   └── AGENTS.md              # ⚠️ Next.js 16 주의사항
│
├── src/                       # 🔒 Phase 1~5 Python (참고용, 그대로 유지)
│   ├── ai/ (predict, rag, agents, prompts, tools, llm_client, gemini_client, ollama_client, mock_responses)
│   ├── api/ (kakao_map, tour_api, weather_api)
│   ├── db/ (firestore_client, storage_client)
│   ├── ui/ (Streamlit — Next.js 전환 후 참조용)
│   └── viz/ (folium_map, plotly_charts, popup_builder)
│
├── docs/                      # 📖 발표 자료 + 이 문서
├── guide/                     # Phase 0~5 가이드
├── data/ (CSV, POI cache, 지식 베이스, chroma_db)
├── models/ (win_rate_model.pkl)
├── uiux/ (웹/모바일 HTML 참고용)
├── scripts/
│   ├── export_to_json.py      # ⭐ Phase 6 신규 (CSV→JSON 변환)
│   └── deploy.sh              # Cloud Run + Firebase Hosting
├── app.py                     # 기존 Streamlit (유지)
├── Dockerfile                 # Streamlit용 (유지, 향후 삭제)
├── firebase.json              # Cloud Run rewrite (Streamlit용)
├── .firebaserc                # project: mini12-310f5
└── .env                       # 27개 환경변수
```

---

## 🚢 4. 재사용 자산 매트릭스

### ✅ 100% 그대로 사용 (frontend/에 복사됨 또는 참조)
| 자산 | 위치 | 비고 |
|---|---|---|
| 팀 로고 SVG 12개 | `frontend/public/logos/` | 복사 완료 |
| 구장 데이터 | `frontend/public/data/stadiums.json` | 10 rows |
| 경기 일정 | `frontend/public/data/schedule.json` | 714 games |
| 팀 전적 | `frontend/public/data/team-stats.json` | 110 rows |
| POI 캐시 | `frontend/public/data/poi/*.json` | 30 파일 |
| 원정 팁 | `frontend/public/data/tips.json` | 45 tips (RAG용) |
| 팀 컬러 | `frontend/public/data/team-colors.json` | 10 teams |
| 승률 모델 계수 | `frontend/public/data/model.json` | 5 features |

### 🔄 참고 후 TypeScript 재작성 (Python 원본은 `src/` 유지)
| Python 원본 | TS 이식 대상 | 우선순위 |
|---|---|---|
| `src/ai/prompts.py` — `SYSTEM_PROMPT_BASE` | `frontend/lib/ai/prompts.ts` | 🔴 |
| `src/ai/tools.py` — TOOL_SCHEMAS 6종 | `frontend/lib/ai/tools.ts` | 🔴 |
| `src/ai/agents.py` — Multi-Agent 로직 | `frontend/lib/ai/agents.ts` | 🔴 |
| `src/ai/rag.py` — 검색 로직 | `frontend/lib/ai/rag.ts` (인메모리) | 🟡 |
| `src/ai/mock_responses.py` | `frontend/lib/ai/mock.ts` | 🟡 |
| `src/ai/predict.py` — 예측 함수 | `frontend/lib/predict.ts` | 🔴 |
| `src/api/kakao_map.py` | `frontend/lib/api/kakao.ts` | 🔴 |
| `src/api/weather_api.py` | `frontend/lib/api/weather.ts` | 🟡 |
| `src/viz/popup_builder.py` | `frontend/lib/map/popup.ts` | 🟢 |
| `src/db/firestore_client.py` | `frontend/lib/firebase/client.ts` | 🔴 |
| `src/ui/components/hero.py` + TEAM_COLORS | `frontend/components/hero.tsx` | 🔴 |
| `src/ui/components/team_selector.py` | `frontend/components/team-selector.tsx` | 🔴 |
| `src/ui/components/badges.py` | `frontend/components/badges/*.tsx` | 🟡 |
| `assets/css/style.css` Stadium Editorial 토큰 | `frontend/app/globals.css` (@theme) | 🔴 |

### 🎨 UI 레퍼런스 (그대로 React 컴포넌트 변환)
| 위치 | 용도 |
|---|---|
| `uiux/web_uiux/*/code.html` | 7종 웹 페이지 Tailwind HTML (Hero, Matches, Map, Eats, AI, Badges 등) |
| `uiux/mobile_uiux/*/code.html` | 7종 모바일 Tailwind HTML |
| `uiux/web_uiux/grand_slam_voyage/DESIGN.md` | Stadium Editorial 디자인 시스템 상세 |

### ❌ 폐기
- `src/ui/` Streamlit UI 전체 (`sidebar.py`, `tabs/*.py`, `components/*.py` 래퍼)
- `src/ai/ollama_client.py` (클라우드에선 사용 불가)
- `app.py` (Streamlit entry)
- 현재 Streamlit Cloud Run 서비스 (당분간 유지, 최종 단계에서 삭제)

---

## ⚠️ 5. Next.js 16 주의사항 (훈련 데이터 이후 최신)

**반드시 매 작업마다 확인**: `frontend/AGENTS.md` + `node_modules/next/dist/docs/`

### 5-1. 주요 변경
1. **Tailwind v4**: `@tailwind base; ...` 없음. `@import "tailwindcss";` + `@theme` 블록
2. **App Router 기본**: Pages Router 아님
3. **React 19 canary**: Server Components 기본
4. **`unstable_instant` export**: 빠른 네비게이션 제어
5. **`mcp.md`, `ai-agents.md`**: AI 에이전트 친화적 가이드 존재
6. **Turbopack 선택적**: 이 프로젝트는 `--no-turbopack` (안정성)

### 5-2. 필수 참조 docs
```
frontend/node_modules/next/dist/docs/01-app/
├── 01-getting-started/
│   ├── 01-installation.md
│   ├── 03-layouts-and-pages.md
│   ├── 05-server-and-client-components.md   ⭐
│   ├── 06-fetching-data.md
│   ├── 07-mutating-data.md                   ⭐ (Server Actions)
│   ├── 11-css.md                             ⭐ (Tailwind v4)
│   ├── 13-fonts.md                           ⭐ (next/font)
│   ├── 15-route-handlers.md                  ⭐ (API Routes)
│   └── 18-upgrading.md
└── 02-guides/
    ├── ai-agents.md                          ⭐
    ├── authentication.md
    ├── deploying-to-platforms.md
    ├── environment-variables.md
    ├── forms.md
    ├── instant-navigation.md                 ⭐
    └── mcp.md
```

### 5-3. Tailwind v4 설정 예시 (globals.css)
```css
@import "tailwindcss";

@theme {
  --color-se-primary: #00193c;
  --color-se-secondary: #1b6d24;
  --color-se-surface: #f8f9fa;
  --font-display: "Plus Jakarta Sans", sans-serif;
  --font-body: "Manrope", sans-serif;
}
```
Tailwind v3의 `tailwind.config.ts`는 더 이상 기본 필수 아님 — `@theme`가 주 설정.

---

## 🧭 6. 전체 세션 로드맵 (Session B~F)

### 📅 Session B — 디자인 시스템 + 인프라 (2~3시간)
**목표**: 테마 적용 + 기본 인프라 구축 + Hero/TeamSelector 완성

**Step 2**: Tailwind Stadium Editorial 테마 + 폰트
- `frontend/app/globals.css` — `@theme` 블록에 SE 컬러 토큰
- `frontend/app/layout.tsx` — Pretendard + Plus Jakarta Sans + Manrope (`next/font/google`)
- Material Symbols Outlined 링크 추가
- `lib/utils.ts` (cn helper), `lib/team-colors.ts`

**Step 3**: 타입·Firebase·LLM 인프라
- `lib/types/index.ts` — Game, Stadium, POI, Tip 등 공통 타입
- `lib/firebase/client.ts` — Firebase v11 SDK (브라우저)
- `lib/firebase/admin.ts` — firebase-admin (서버용)
- `lib/ai/prompts.ts` — 시스템 프롬프트 포팅
- `.env.local` — GEMINI_API_KEY, FIREBASE_* 복사

**Step 5**: Hero + TeamSelector (uiux HTML 참고)
- `components/hero.tsx` — 팀 컬러 그라디언트 + KBO 로고
- `components/team-selector.tsx` — 5×2 로고 카드 그리드
- `app/page.tsx` — Hero + TeamSelector 렌더

**검증**: `pnpm dev` → http://localhost:3000 에서 Hero+팀 선택기 확인

---

### 📅 Session C — 예측 모델 + 라우팅 + 탭 1 (2~3시간)
**Step 4**: 승률 예측 TS 포팅
- `lib/predict.ts` — model.json 로드 + StandardScaler + LogReg 수식 직접 구현
- `app/api/predict/route.ts` — POST `/api/predict` 엔드포인트
- 검증: LG vs KT 예측 결과 Python과 비교

**Step 6**: 5개 탭 App Router + Sidebar
- `app/matches/page.tsx`, `map/page.tsx`, `places/page.tsx`, `ai/page.tsx`, `badges/page.tsx`
- `components/sidebar/filter-sidebar.tsx` — 응원팀 + 기간 + 예산 + 인원 + 이동수단
- `components/sidebar/viewport-toggle.tsx`
- Zustand 스토어 `lib/store/filters.ts`

**Step 7**: 탭 1 — Matches + 승률 게이지
- `components/matches/match-list.tsx` — schedule.json 필터링
- `components/matches/win-gauge.tsx` — Plotly.js Indicator
- `components/matches/win-rate-bar.tsx` — 구단별 원정 승률 막대

---

### 📅 Session D — 지도 + 맛집 (2~3시간)
**Step 8**: 탭 2 — React-Leaflet 지도 ⭐
- `dynamic(() => import('...'), { ssr: false })` 필수
- `components/map/folium-map.tsx` — 4개 레이어 + LayerControl
- `components/map/place-popup.tsx`
- `app/api/route/route.ts` — 카카오 길찾기 + fallback
- `lib/api/kakao.ts` — 포팅

**Step 9**: 탭 3 — Places
- `components/places/stadium-picker.tsx`
- `components/places/scatter-places.tsx` (Plotly.js)
- `components/places/poi-card.tsx`

---

### 📅 Session E — AI + 뱃지 ⭐ (2~3시간)
**Step 10**: 탭 4 — AI 챗봇 (Vercel AI SDK)
- `components/ai/chat-ui.tsx` — `useChat` 훅 SSE
- `app/api/chat/route.ts` — Gemini stream response
- `lib/ai/tools.ts` — 6 tool schemas
- `lib/ai/agents.ts` — Multi-Agent
- `components/ai/tool-viz.tsx` — Thought-Action-Observation
- `components/ai/agent-log.tsx`
- `lib/ai/mock.ts` — 시연 안전장치

**Step 11**: 탭 5 — Badges + Firestore 실시간
- `components/badges/stadium-tour.tsx` — 10구장 SVG 그리드
- Firebase client SDK로 `visited_stadiums` CRUD
- 공유 계획 `shared_plans` + `/share/[planId]/page.tsx`

---

### 📅 Session F — 배포 + 검증 (1~2시간)
**Step 12**: Firebase App Hosting 배포
- `apphosting.yaml` 작성
- `firebase init apphosting`
- Secret Manager 연결
- `firebase deploy --only apphosting`
- 도메인 설정 검토

**Step 13**: 최종 검증
- 전 탭 smoke test
- 발표용 녹화 + 스크린샷 5종
- README.md 업데이트 (배포 URL)
- Streamlit Cloud Run 서비스 결정 (유지/삭제)
- `scripts/validate_phase6.ts` (선택)

---

## 🤖 7. 다음 세션 시작 프롬프트 (복붙용)

### Session B 시작 시
```
프로젝트 경로: /Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12

Phase 6 Next.js 마이그레이션 중. Session A에서 스캐폴딩·데이터 변환·의존성 설치를 완료했습니다.
이번 Session B에서는 docs/PHASE6_NEXTJS_MIGRATION.md 의 "Session B" 항목에 따라
Step 2(Tailwind Stadium Editorial 테마)·Step 3(lib 인프라)·Step 5(Hero + TeamSelector)를
진행해주세요.

주의사항:
1. Next.js 16은 훈련 데이터 이후 최신 버전이므로 frontend/node_modules/next/dist/docs/01-app/
   아래의 해당 가이드를 각 기능 구현 전에 확인할 것
2. Tailwind v4 사용 — @theme 블록 + CSS 변수 방식
3. 디자인 시스템 원본: uiux/web_uiux/grand_slam_voyage/DESIGN.md + src/ui/components/hero.py
4. 팀 로고는 /logos/{TEAM}.svg 에서 로드 (이미 배치됨)

Session B 완료 시 pnpm dev 로 Hero + TeamSelector UI 확인 가능해야 함.
```

### Session C~F 시작 시 (공통 템플릿)
```
프로젝트 경로: /Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12

Phase 6 Next.js 마이그레이션 Session [C/D/E/F].
이전 세션들은 docs/PHASE6_NEXTJS_MIGRATION.md 확인.
이번 세션 목표: [해당 Session 섹션 복사].

진행 전 CLAUDE.md와 docs/PHASE6_NEXTJS_MIGRATION.md를 먼저 읽어 컨텍스트 파악.
```

---

## 🎯 8. 각 세션 완료 기준 (검증 체크리스트)

### Session B ✅ (2026-04-17)
- [x] `frontend/app/globals.css` 에 SE 컬러 토큰 정의 (`@theme`) — 17 color tokens + font-display/font-body
- [x] `frontend/app/layout.tsx` 폰트 3종 로드 완료 (Plus Jakarta Sans + Manrope + Noto Sans KR)
- [x] `pnpm dev` → Hero 렌더 (팀 컬러 그라디언트) — HTTP 200 OK, Ready 328ms
- [x] TeamSelector 클릭 → URL `?team=KT` 반영 — Hero "KT 위즈" 렌더 확인
- [x] 모바일 뷰포트 `?device=mobile` → 3열 그리드 + 480px 컨테이너 확인
- [x] `npx tsc --noEmit` 에러 0

### Session C ✅ (2026-04-17)
- [x] `curl -X POST http://localhost:3000/api/predict -d '{"team":"LG","opponent":"KT"}'` 응답 — `{"prob":0, "source":"logreg"}`
- [x] 5개 탭 라우팅 (/matches, /map, /places, /ai, /badges) 동작 — 전부 200 OK
- [x] 탭 1에서 경기 리스트 + 게이지 + 막대 표시 — 138KB HTML
- [x] Python ↔ TS 예측값 4쌍 모두 소수점 4자리까지 일치
- [x] `.next` 캐시 재생성 후 `npx tsc --noEmit` 에러 0
- [x] Zustand + URL 양방향 동기화 (Sidebar → router.replace, Hero는 searchParams)

### Session D ✅ (2026-04-17)
- [x] 탭 2 지도에 4레이어 + 마커 클릭 → 팝업 카드 (LayersControl 우상단)
- [x] 탭 3 Places 산점도 + 카드 리스트 (10 구장 · 3 카테고리 전환)
- [x] **보너스**: Kakao 실패 시 OSRM(OSM) 자동 폴백 — 실측으로 Kakao 401 → OSRM 537 vertex 폴백 성공 (docs/OSM_FALLBACK_PLAN.md)
- [x] 캐시 히트 40× 단축 (828ms → 20ms)
- [x] `npx tsc --noEmit` 에러 0

### Session E ✅ (2026-04-17)
- [x] 탭 4 "LG 원정 언제?" → Gemini 스트리밍 응답 (`text-delta` SSE)
- [x] tool calling: `predict_win_rate` 실행 확인 (tool-input/output-available 이벤트, Python 값과 일치)
- [x] 탭 5 방문 구장 — localStorage persistence (Firestore 선택적 · `isAdminConfigured()` 로 가드)
- [x] 공유 링크 — URL 직렬화 방식 primary + Firestore 단축 선택적, `/share/[id]` 리다이렉트
- [x] Mock 시연 모드 — demoMode + 광주/부산/우천 키워드 매칭
- [x] Multi-Agent 프롬프트 — ### 섹션 기반 (일정/전략/장소/최종)
- [x] `npx tsc --noEmit` 에러 0

### Session F ✅ 코드 레벨 완료 (2026-04-17) — 배포는 사용자 실행
- [x] `frontend/apphosting.yaml` — runConfig + 12 env (공개/서버/시크릿 분리)
- [x] `firebase.json` — Streamlit Cloud Run rewrite 제거, App Hosting 지정
- [x] `pnpm build` 성공: 13 routes compile
- [x] Turbopack NFT 경고 해결 (admin.ts fs.readFileSync)
- [x] `scripts/preflight.sh` — 7 섹션 pre-deploy 점검
- [x] `docs/SESSION_F_DEPLOY_RUNBOOK.md` — 10 섹션 런북
- [x] `README.md` Phase 6 Live 섹션 업데이트
- [ ] (사용자) 배포 URL smoke test 통과
- [ ] (사용자) Cold start 후 5초 이내 Hero 렌더
- [ ] (사용자) 발표 녹화 영상 생성

---

## 📎 9. 주요 명령 모음

```bash
# 로컬 개발 (모든 세션 공통)
cd "/Volumes/Corsair EX300U Media/00_work_out/01_complete/Phase12/frontend"
pnpm dev                  # http://localhost:3000

# 데이터 재변환 (CSV 변경 시)
cd "../"
python3 scripts/export_to_json.py

# shadcn/ui 추가 (필요 시)
cd frontend
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button dialog card

# 빌드 테스트
pnpm build

# 배포 (Session F)
firebase init apphosting
firebase apphosting:secrets:set GEMINI_API_KEY
firebase deploy --only apphosting

# Streamlit 서비스 (레거시, 유지중)
# https://mini12-310f5.web.app (무한로딩 이슈 있음)
# https://away-game-companion-262552815882.asia-northeast3.run.app (직접 접속은 OK)
```

---

## 📚 10. 참고 문서 (프로젝트 내)

- `docs/ARCHITECTURE.md` — Phase 5 아키텍처 다이어그램
- `docs/DEPLOY_CHECKLIST.md` — Streamlit Cloud Run 배포 이력
- `docs/PRESENTATION_OUTLINE.md` — 발표 슬라이드 구조
- `docs/DEMO_SCRIPT.md` — 3분 데모 시나리오
- `docs/QA_PREP.md` — Q&A 10개
- `docs/VIZ_CONTRACT.md` — 시각화/지도 함수 계약
- `guide/PHASE0_GUIDE.md` ~ `PHASE5_GUIDE.md`
- `frontend/AGENTS.md` — Next.js 16 주의사항 (필수)
- `frontend/node_modules/next/dist/docs/` — Next.js 16 공식 docs

---

*작성: 2026-04-17 Session A — 갱신: Session B, C, D, E, F 종료 시점*
*코드 레벨 Phase 6 완료. 다음: 사용자가 `docs/SESSION_F_DEPLOY_RUNBOOK.md` 따라 배포 실행.*
