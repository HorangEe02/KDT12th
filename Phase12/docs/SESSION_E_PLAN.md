# 📝 Session E — AI 챗봇 + Badges + Share Plan 구현 계획

> 작성: 2026-04-17 (Session E 시작)
> 대상: Step 10 (AI 챗봇) + Step 11 (Badges + 공유)

---

## 🎯 목표

| 항목 | 결과물 |
|---|---|
| `/ai` | Gemini 스트리밍 + 6 tool calling + Multi-Agent 모드 + mock 시연 |
| `/badges` | Stadium Tour 10 구장 그리드 + 토글 + Firestore/localStorage 이중화 |
| 공유 | URL query-string 기반 (Firestore 선택적) + 사이드바 공유 버튼 + `/share/[id]` |

---

## 📦 의존성

- **이미 설치**: `ai@6.0.168`, `@ai-sdk/google@3.0.64`, `firebase@12`, `firebase-admin@13`, `zustand@5`
- **추가**: `@ai-sdk/react` — `useChat` 훅 (v6의 클라이언트 스트리밍 파서)

### AI SDK v6 주요 차이점
- `useChat` 는 `@ai-sdk/react` 에 별도 패키지로 분리됨 (v5 `ai/react` 아님)
- `streamText().toUIMessageStreamResponse()` 이 새로운 기본 응답 형식 (SSE-like)
- `tool({...})` 헬퍼는 `ai` 에서 직접 export
- `convertToModelMessages(uiMessages)` 로 UIMessage ↔ ModelMessage 변환

---

## 🧱 아키텍처

### 10. AI 챗봇 데이터 흐름

```
┌──────────────┐   useChat POST    ┌───────────────┐
│ ChatUI       │ ─────────────────▶ │ /api/chat     │
│ (client)     │ ◀─────────────────  │ (nodejs)      │
└──────────────┘   UI message stream └───────────────┘
                                              │
                             ┌────────────────┼─────────────────┐
                             ▼                ▼                 ▼
                    single-agent?       multi-agent?       demo mode?
                    streamText +         supervisor         mock.ts
                    6 tools              → specialists      (즉시 반환)
                                         → synthesizer
                                         (streamText)
```

**Tool 실행 순서**: `ai` SDK 가 자동으로 Gemini 응답의 tool_call 을 파싱 → 해당 `execute` 실행 → 결과를 다시 Gemini 에 주입 → 최종 텍스트 생성. `stopWhen: stepCountIs(5)` 로 무한루프 방지.

### 11. Badges + Share 데이터 흐름

```
localStorage  ←───  Zustand (persist)  ───→  Firestore
(항상 동작)         visited_stadiums[]         (env 있을 때만)

Sidebar "공유" 버튼
  → URL serialize(filters) → ?team=X&start=Y&...
  → (선택) POST /api/plans → Firestore "shared_plans"
  → clipboard.writeText(URL)
```

---

## 📂 파일 트리

```
frontend/
├── lib/
│   ├── ai/
│   │   ├── tools.ts          # 6 tool 정의 (Vercel AI SDK tool())
│   │   ├── agents.ts         # Multi-Agent orchestrator
│   │   ├── rag.ts            # 인메모리 키워드 검색 (tips.json 45 items)
│   │   └── mock.ts           # demo mode 시연 응답 3종
│   ├── api/
│   │   └── weather.ts        # KMA 단기예보 + WGS84→기상청 격자 변환
│   ├── firebase/
│   │   ├── visited.ts        # visited_stadiums CRUD (try/catch로 실패 시 조용)
│   │   └── shared-plans.ts   # shared_plans CRUD
│   ├── store/
│   │   └── badges.ts         # Zustand: visited: string[], toggleVisit(short)
│   └── share/
│       └── serialize.ts      # Filters ↔ URLSearchParams
├── app/
│   ├── api/
│   │   ├── chat/route.ts     # POST streamText + tools + multi-agent 분기
│   │   └── plans/
│   │       ├── route.ts      # POST 생성 (Firestore 또는 URL 반환)
│   │       └── [id]/route.ts # GET 조회
│   ├── (shell)/
│   │   ├── ai/page.tsx       # ChatUI shell
│   │   └── badges/page.tsx   # StadiumTour shell
│   └── share/
│       └── [id]/page.tsx     # redirect to / with query hydration
├── components/
│   ├── ai/
│   │   ├── chat-ui.tsx       # useChat 래퍼 + UI
│   │   ├── message-bubble.tsx
│   │   ├── tool-viz.tsx      # tool call 인라인 카드
│   │   ├── agent-log.tsx     # Multi-Agent 진행 로그
│   │   └── chat-input.tsx    # textarea + 전송 + multi-agent 토글
│   └── badges/
│       ├── stadium-tour.tsx      # 10 구장 그리드 + 토글
│       ├── celebrate-banner.tsx  # 10/10 축하
│       ├── share-plan-button.tsx # 사이드바/Badges 공유 버튼
│       └── share-toast.tsx       # 복사 완료 토스트
```

---

## 🔧 10. AI 챗봇 상세

### 10-1. Tool 스키마 (lib/ai/tools.ts)

6 tool, 모두 `ai` SDK `tool({description, inputSchema, execute})` 형식:

| name | 파라미터 | 반환 | 비고 |
|---|---|---|---|
| `search_game` | team, startDate?, endDate? | Game[] | schedule.json 필터 (최대 8) |
| `predict_win_rate` | team, opponent | {prob, source} | lib/predict.ts 재사용 |
| `get_weather` | stadium, targetDate? | {sky, POP, tempMin, tempMax} | lib/api/weather.ts |
| `find_places` | stadium, category, limit? | POI[] | lib/data/loaders.ts |
| `get_route` | origin(preset or "lat,lng"), destinationStadium | {distanceKm, durationMin, toll} | lib/api/route.ts 재사용 |
| `search_knowledge` | query, stadium? | tip[] | lib/ai/rag.ts (키워드 매칭) |

### 10-2. Multi-Agent (lib/ai/agents.ts)

포팅 원본: `src/ai/agents.py`

1. **Supervisor**: `generateText` (non-streaming) + 저온도 → JSON `{agents: ["schedule", "place"]}` 결정
2. **Specialists** (schedule / strategy / place): 병렬 `generateText` + tools (각 agent별 system_prompt)
3. **Synthesizer**: `streamText` (streaming) + findings 주입 → 최종 답변

클라이언트로 전송: `result.toUIMessageStreamResponse()` + 에이전트 중간 결과를 `dataStream` 청크로 병합.

### 10-3. Mock 모드 (lib/ai/mock.ts)

- `filters.demoMode === true` 시 미리 준비된 Markdown 응답 반환 (LLM 호출 없음)
- 케이스 3종: 광주가족원정 / 부산맛집 / 우천실내

### 10-4. RAG (lib/ai/rag.ts)

- 단순화: ChromaDB/bge-m3 없이 tips.json 45개 대상 **BM25-lite + stadium 필터**
- `score = keywordHits(query, tip.tip) + (stadium === tip.stadium ? 2 : 0)`
- top 3 반환

### 10-5. `/api/chat/route.ts` 엔드포인트 계약

```typescript
POST { messages: UIMessage[], filters: Filters, multiAgent?: boolean }

→ if filters.demoMode: Response( stream( mock.ts ) )
→ if multiAgent: agents.runPipeline(messages, filters) → UIMessageStreamResponse
→ else: streamText({ model: google("gemini-2.5-flash-lite"), messages, tools, stopWhen: stepCountIs(5), system: buildSystemPrompt(filters) }).toUIMessageStreamResponse()
```

### 10-6. Chat UI (components/ai/chat-ui.tsx)

```tsx
"use client";
const { messages, sendMessage, status, stop } = useChat({
  transport: new DefaultChatTransport({
    api: "/api/chat",
    body: () => ({ filters: useFilters.getState(), multiAgent: useChatUI(s => s.multiAgent) })
  })
});
```

---

## 🏆 11. Badges & Share 상세

### 11-1. Stadium Tour (components/badges/stadium-tour.tsx)

- 10 구장 카드 (웹 5×2 / 모바일 2×5)
- `visited[short_name: string]` 상태 Zustand 저장 + localStorage 영속
- Firestore 동기화: 로드 시 merge(localStorage, firestore), 토글 시 양쪽 동시 write (try/catch)
- 방문 수 ≥ 10 → `<CelebrateBanner>` 표시 ("🏆 All Stadiums Conquered!")

### 11-2. Share Plan

**MVP: URL-only (no server)**
- 사이드바 "공유" 버튼 클릭 → 현재 filters 를 URL query string 으로 직렬화
- `navigator.clipboard.writeText(url)` + 토스트
- 링크 수신 측: `hydrateFromUrl(params)` (이미 구현됨)

**옵션: Firestore 단축**
- Firebase 환경 변수 존재 시 POST `/api/plans` → `{id: uuid}` → 짧은 URL `/share/{id}` 반환
- `/share/[id]` 페이지: Firestore 조회 → filters 를 `/?team=X&...` 로 `redirect()`

### 11-3. Firestore 스키마

```
visited_stadiums/{userId}
  stadiums: string[]           // ["잠실", "수원", ...]
  updatedAt: Timestamp

shared_plans/{planId}
  filters: {...}
  createdAt: Timestamp
  title?: string
```

`userId` 는 브라우저별 UUID (localStorage `uid` 키, Anonymous Auth 대신 간단화).

### 11-4. Graceful degradation

Firebase env 미설정 시 (`NEXT_PUBLIC_FIREBASE_API_KEY` 없음):
- Zustand + localStorage 만 동작
- UI 는 "🌐 로컬 저장 중 · Firebase 미구성" 배지 표시
- 공유는 URL query-string 전용 (Firestore 단축 없음)

---

## ✅ 검증 플랜

| # | 항목 | 기대값 |
|---|---|---|
| 1 | `tsc --noEmit` | 에러 0 |
| 2 | `/ai` 페이지 로드 | 200 |
| 3 | POST `/api/chat` (일반) | UIMessageStream OK |
| 4 | "LG 다음 원정 언제?" | search_game 호출 → 실제 날짜 반환 |
| 5 | "LG vs KT 승률" | predict_win_rate 호출 → 0~1 값 |
| 6 | `demoMode:true` | mock 응답 즉시 반환 (< 100ms) |
| 7 | `multiAgent:true` | supervisor → specialists → synthesizer 순차 로그 |
| 8 | `/badges` 구장 토글 | localStorage 저장 + UI 반영 |
| 9 | 사이드바 "공유" | clipboard URL 복사 + 토스트 |
| 10 | 공유 URL 타 탭 로드 | filters 복원 |

---

## 🧭 구현 순서

1. `pnpm add @ai-sdk/react` (완료)
2. Weather util (lib/api/weather.ts)
3. RAG + Mock (lib/ai/rag.ts, mock.ts)
4. 6 Tools (lib/ai/tools.ts)
5. Multi-Agent (lib/ai/agents.ts)
6. Chat API route (/api/chat/route.ts)
7. Chat UI 4 컴포넌트 (chat-ui, message-bubble, tool-viz, chat-input)
8. AI page shell
9. Badges store + stadium-tour component
10. Badges page
11. Share: serialize util + share-plan-button + share-toast
12. Share page `/share/[id]` + API `/api/plans`
13. Sidebar: add share button
14. Verify 10/10
15. Update CLAUDE.md + PHASE6 doc

---

*작성: 2026-04-17 · Phase 6 Session E 시작 시점*
