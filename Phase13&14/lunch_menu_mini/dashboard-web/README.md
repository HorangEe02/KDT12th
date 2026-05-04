# 오늘 뭐 먹지 — Dashboard (Next.js 16 / React 19)

직장인 점심 결정 도우미. `NLP/nlp_mvp/api`(포트 8001)와 `lunch-optimizer/api`(포트 8000) 위에서 동작하는 프런트엔드.

**Milestone 상태:** ✅ **M1 ~ M10 전부 완료** (2026-04-08).
CAD Vision(`01_CAD/web`) 구조를 포팅하여 레거시 단일 jsx를 production-grade Next.js 앱으로 전환 완료.

---

## 기술 스택

| 기술 | 버전 | 용도 |
|---|---|---|
| Next.js | 16.2.1 | App Router, Turbopack |
| React | 19.2.4 | UI 프레임워크 |
| Tailwind CSS | v4 | `@theme inline` CSS 변수 기반 테마 |
| TanStack Query | v5 | 서버 상태 + 자동 폴링 |
| next-themes | 0.4 | 다크/라이트 (`data-theme`) |
| Recharts | v3 | Weather/Nutrition 차트 (M6) |
| lucide-react | 1.7 | 아이콘 |
| TypeScript | 5 | 타입 안전 |

## 페이지

| 경로 | 페이지 | 주요 기능 |
|---|---|---|
| `/` | Dashboard | KPI 4카드 (restaurants · meals · avg sentiment · chat latency) · CategoryChart · OllamaStatus · Today's Top5 |
| `/discover` | 음식점 탐색 | `useQueries` 병렬 `/nlp/sentiment/{id}` · 5종 정렬 · 6축 Recharts 레이더 (거리·날씨·영양·평점·가격·**감성**) |
| `/weather` | 날씨 추천 | 현재 날씨 카드 · 팁 박스 · 메뉴 유형별 BarChart · Top 5 |
| `/nutrition` | 영양 리포트 | **AI Comment Card** (`/nlp/reports/weekly/{userId}` + 재생성 mutation) · 4 StatCard · AreaChart · Donut · Daily BarChart |
| `/vote` | 팀 투표 | 5명 투표 그리드 · Random/Confirm/Reset · 실시간 수평 BarChart · 우승자 배너 · 방문 이력 |
| `/concierge` | AI 상담 | **SSE 토큰 스트리밍** (`/nlp/chatbot/chat/stream`) · 4-type 프레임 · 추천 카드 · 환각 경고 배너 |
| `/insights` | NLP Insights | HealthStrip · Sentiment Top 10 · **Menu Normalizer Playground** · RAG Stats · Roadmap |

## 폴더 구조

```
dashboard-web/
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── tsconfig.json
├── eslint.config.mjs
├── .env.local.example
├── public/
│   └── logo/
└── src/
    ├── app/
    │   ├── layout.tsx            # TopNav + Sidebar + main + Footer
    │   ├── globals.css           # Warm Kitchen theme (@theme inline)
    │   ├── page.tsx              # Dashboard /
    │   ├── discover/page.tsx     # (stub M5)
    │   ├── weather/page.tsx      # (stub M6)
    │   ├── nutrition/page.tsx    # (stub M6)
    │   ├── vote/page.tsx         # (stub M6)
    │   ├── concierge/page.tsx    # (stub M7)
    │   └── insights/page.tsx     # (stub M8)
    ├── components/
    │   ├── layout/
    │   │   ├── TopNav.tsx
    │   │   ├── Sidebar.tsx
    │   │   └── StatusFooter.tsx
    │   ├── settings/
    │   │   ├── SettingsPanel.tsx  # theme + model + lang + user id
    │   │   └── UserPanel.tsx
    │   ├── dashboard/
    │   │   ├── KPICards.tsx
    │   │   ├── CategoryChart.tsx
    │   │   ├── OllamaStatus.tsx
    │   │   └── TodaysTop5.tsx
    │   ├── discover/             # (M5)
    │   ├── weather/              # (M6)
    │   ├── nutrition/            # (M6)
    │   ├── vote/                 # (M6)
    │   ├── concierge/            # (M7)
    │   └── insights/             # (M8)
    └── lib/
        ├── providers.tsx         # QueryClient + ThemeProvider
        ├── api.ts                # apiFetchLunch / apiFetchNLP / apiStreamSSENLP
        ├── types.ts              # 모든 Pydantic 스키마의 TS 미러
        ├── queries.ts            # useNLPHealth / useSentimentTop / ...
        ├── scoring.ts            # legacy jsx 스코어링 함수 포팅
        └── mock.ts               # 시드 데이터 (실 API 연동 전 fallback)
```

## 실행 방법

```bash
# 1) 의존성 설치
cd Mini/dashboard-web
npm install

# 2) 환경 변수
cp .env.local.example .env.local
# 필요 시 NEXT_PUBLIC_* 수정

# 3) 개발 서버
npm run dev
# → http://localhost:3000

# 4) 프로덕션 빌드
npm run build
npm start
```

### 동시에 필요한 백엔드 3종

```bash
# 터미널 1: lunch-optimizer
cd Mini/lunch-optimizer
uvicorn api.main:app --reload --port 8000

# 터미널 2: NLP
cd Mini
uvicorn nlp_mvp.api.main:app --reload --port 8001

# 터미널 3: Next.js
cd Mini/dashboard-web
npm run dev
```

NLP API가 꺼져 있어도 UI는 렌더됩니다(“Disconnected”·pending 뱃지). Dashboard의 감성 평균·챗봇 지연 KPI만 `—` 로 표시됩니다.

## 디자인 언어

- **Warm Kitchen Theme** — CAD Vision의 Engineering Terminal 구조를 그대로 차용하고, 색상만 음식 도메인에 맞게 오렌지/그린/앰버 팔레트로 튜닝
- 타이포: `Plus Jakarta Sans`(heading) + `Manrope`(body) + `JetBrains Mono`(numbers) + `Pretendard`(한글)
- CSS 변수는 `globals.css`의 `@theme inline` 블록 한 곳에만 정의 — 색 변경은 변수 값만 수정하면 전 페이지에 반영
- 다크 모드가 기본 · 우측 Settings에서 라이트 전환

## Milestone 전체 이력

| Milestone | 내용 | 상태 |
|---|---|---|
| M1 | Next.js 16 scaffold · configs · layout · globals.css Warm Kitchen theme | ✅ |
| M2 | `src/lib/` — api · types · queries · scoring · mock · providers | ✅ |
| M3 | Layout shell (TopNav · Sidebar 7-nav · StatusFooter · SettingsPanel · UserPanel) | ✅ |
| M4 | Dashboard `/` — KPI 4카드 · CategoryChart · OllamaStatus · TodaysTop5 | ✅ |
| M5 | `/discover` — useQueries 병렬 감성 로드 · 6축 레이더 · 5 정렬 옵션 | ✅ |
| M6 | `/weather` `/nutrition` `/vote` 전면 구현 · NLG AI Comment 연동 | ✅ |
| M7 | `/concierge` SSE 스트리밍 · 백엔드 `/nlp/chatbot/chat/stream` + `OllamaClient.chat_stream()` | ✅ |
| M8 | `/insights` — HealthStrip · Sentiment Top · Normalizer Playground · RAG Stats · Roadmap | ✅ |
| M9 | 백엔드 `/nlp/models` + `PUT /nlp/settings/model` + chat/report env 분리 + SettingsPanel 실연결 | ✅ |
| M10 | legacy jsx 이동 · 문서 갱신 · `.env` `gemma4` 오류 수정 | ✅ |

## 신규 API 엔드포인트 (Phase 5.5)

M7 / M9에서 추가된 백엔드 엔드포인트:

| Method | Path | 설명 |
|---|---|---|
| POST | `/nlp/chatbot/chat/stream` | SSE 스트리밍 챗 응답 (4-type frames: meta/token/final/error) |
| GET | `/nlp/models` | Ollama 설치 모델 목록 + 활성 chat/report |
| GET | `/nlp/settings` | 현재 chat/report 모델 + host + 언어 pref |
| PUT | `/nlp/settings/model` | 활성 모델 변경 (role: chat/report/both) |

## 레거시 참조

마이그레이션 이전 단일 `.jsx` 파일은 [`../legacy/lunch-optimizer-dashboard.jsx.bak`](../legacy/) 에 보존. 기능별 위치 매핑은 [`../legacy/README.md`](../legacy/README.md) 참고.
