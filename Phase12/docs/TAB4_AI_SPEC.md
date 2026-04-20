# 🤖 Tab 4. AI 플래너 — 기능 설명서

> **"이번 주말 수원 원정 가는데 비 올까? 경기는 몇 시고, 근처 아이랑 갈 만한 곳은?"**
> 이런 질문 서너 개를 한 번에 물어보면, 실제 경기 일정 · 기상청 예보 · 공공 관광 데이터를 조합해 답을 들려주는 **원정 응원 전용 AI 컨시어지** 입니다.

**라우트**: `/ai` · **배포 URL**: [my-web-app--mini12-310f5.asia-east1.hosted.app/ai](https://my-web-app--mini12-310f5.asia-east1.hosted.app/ai)

---

## 📖 起 (기) — 왜 필요한가? 문제 제기

### 일반 AI 챗봇은 왜 원정 응원에 부족한가?

ChatGPT·Gemini 같은 AI 챗봇에 "이번 주말 한화 원정 경기 알려줘" 라고 물으면 이런 답이 돌아옵니다:

> "정확한 KBO 2026 시즌 일정은 실시간으로 확인이 어렵습니다.
> 공식 홈페이지를 참고하세요."

### 왜 그럴까?

일반 AI는 **"책에서 배운 지식"** 은 풍부하지만, **"지금 이 순간의 실제 데이터"** 는 모릅니다:
- 오늘 날씨 🌦
- KBO 경기 일정 ⚾
- 내 위치에서 구장까지 거리 🗺
- 경기장 주변 실제 맛집 리스트 🍽

이건 야구팬에게 치명적입니다. "이번 주말 수원 경기 비 올까?" 같은 실용적 질문이 **대부분의 원정 고민** 이기 때문입니다.

### 이 탭의 약속

> **"AI에게 '실제 데이터에 접근할 수 있는 손'을 달아 줍니다."**

사용자가 질문하면 AI가 스스로 판단해서 **앱 안의 실제 기능(도구)을 호출** → 경기 데이터 조회, 승률 계산, 날씨 확인, 맛집 검색, 길찾기, 원정 팁 검색을 수행한 뒤 자연어로 답변합니다.

---

## 🚀 承 (승) — 무엇을 하는가? 기능 소개

### 기능 6가지

#### 1. 자연어 멀티턴 대화
- ChatGPT처럼 **이어지는 대화** 가능
- "근처 맛집 알려줘" → "그 중에 가족용은?" → "주차 가능한 곳만" 같은 연속 질문 OK

#### 2. 6개 도구 호출 (function calling)
AI가 질문 의도에 따라 **스스로 선택**해 호출하는 6가지 기능:

| 도구 | 언제 호출? | 예시 |
|---|---|---|
| `search_game` | 경기 일정 질문 | "이번 주말 원정 경기?" |
| `predict_win_rate` | 승률 질문 | "LG vs KT 이길 확률?" |
| `get_weather` | 날씨 질문 | "수원 경기 비 올까?" |
| `find_places` | 맛집·숙박·관광 | "고척 근처 분식집?" |
| `get_route` | 길찾기 | "서울역에서 사직구장까지?" |
| `search_knowledge` | 원정 팁 검색 | "광주 원정 꿀팁?" |

#### 3. Multi-Agent 모드 — "여러 전문가 AI 협업"
체크박스 켜면, 한 명의 AI가 아니라 **4명의 전문 AI가 협업**합니다:

```
사용자: "광주 원정 가족끼리 맛집 추천"
   │
   ▼
[총괄 매니저] 어떤 전문가가 필요한가 판단
   │
   ├─ [일정 전문가] 광주 다음 원정 일정 조회
   └─ [맛집 전문가] 광주 구장 주변 가족용 음식점 조회
        │
        ▼
[작성자] 두 전문가 결과를 통합 → 4~5문장 최종 답변
```

#### 4. Mock 시연 모드 🎬
- 체크박스 켜면 **발표용 고정 답변** 사용
- 3가지 시나리오: 광주 가족 원정 · 부산 맛집 · 우천 실내
- 네트워크 불안정한 발표장에서도 안정적으로 데모 가능

#### 5. 도구 호출 시각화
- AI가 도구를 부를 때마다 **인라인 카드**로 진행 상황 표시
- 예: 🔧 `search_game` 도구 실행 중 → ✅ 결과: 3경기 조회 완료

#### 6. 실시간 스트리밍
- 답변이 ChatGPT처럼 **타이핑되듯 실시간** 흘러나옴
- 전체가 완성되기 전에 먼저 읽을 수 있어 체감 속도 ↑

### 화면 예시

**📱 모바일**
```
┌─ 🤖 AI 플래너 ───────────────────┐
│ 🟢 삼성 라이온즈 · 04-19~05-19    │
├─ Messages ──────────────────────┤
│ 🤖 KBO 원정 컨시어지              │
│    경기·날씨·맛집·길찾기·팁 물어   │
│                                   │
│ [이번 주말 원정 경기?]             │
│ [오늘 수원 경기 비 올까?]          │
│ [LG vs KT 승률은?]                │
│                                   │
│   — 대화 시작 후 —                 │
│ 👤 광주 원정 가족코스 짜줘          │
│ 🤖 (도구 호출 중...)               │
│    🔧 search_game  ✅ 3경기        │
│    🔧 find_places  ✅ 5곳           │
│ 🤖 어이~ 광주 원정 가족코스...      │
├─ 💬 컨시어지에게 물어보세요... [▶]┤
└──────────────────────────────────┘
```

---

## ⚙️ 轉 (전) — 어떻게 만들었는가? 기술과 원리

> AI 기술을 **비유와 예시**로 풀어씁니다.

### 🧠 LLM (Large Language Model) — "엄청난 글을 학습한 AI 뇌"

**쉽게 말하면**:
> "책·위키·기사 **수조 단어**를 학습해서, 사람이 쓰는 자연스러운 언어로 답할 수 있게 된 AI 시스템."

대표 예: ChatGPT · Google Gemini · Claude 등.

이 프로젝트는 **Google Gemini 2.5 Flash Lite** 를 사용합니다.
- 왜 Gemini? → **무료 티어가 넉넉** (분당 15회 호출), 한국어 이해도 우수, 도구 호출 안정
- 왜 "Flash Lite"? → Gemini 제품군 중 **가장 빠르고 저렴한 모델**, 간단한 질문-답변에 충분

### 🔧 도구 호출 (Function Calling) — "AI에게 손 달아주기"

**쉽게 말하면**:
> "AI가 혼자 상상해서 답하지 않고, **'이 질문은 경기 일정 조회가 필요해'** 라고 판단해서 앱 안의 실제 함수를 호출합니다. 결과를 받은 뒤 자연어로 정리해서 답변."

**작동 순서**:
```
사용자: "LG가 이번 주말 KT랑 이길 확률?"
  │
  ▼
[LLM 판단]
"승률 질문이네. `predict_win_rate` 도구 호출해야겠다."
  │
  ▼
[도구 실행]
predict_win_rate(team="LG", opponent="KT")
→ { prob: 0.985, source: "logreg" }
  │
  ▼
[LLM 답변 작성]
"LG가 KT를 상대로 이길 확률은 약 98.5%로 매우 높게 예측됩니다.
 다만 모델은 과거 데이터 기반이니 참고용으로 활용해 주세요."
```

**도구 정의 방식 (Zod 스키마)**:
```ts
tool({
  description: "특정 팀의 원정 경기를 날짜 범위로 검색합니다.",
  inputSchema: z.object({
    team: z.string(),
    startDate: z.string().optional(),
    endDate: z.string().optional(),
  }),
  execute: async ({ team, startDate, endDate }) => {
    // 실제 데이터 조회
  },
})
```

LLM은 `description` 을 읽고 **"언제 이 도구를 부를지"** 를 스스로 판단합니다.

### 👥 Multi-Agent — "여러 전문가 AI 협업"

**쉽게 말하면**:
> "변호사·의사·세무사에게 각각 묻고 한 사람이 종합 답변 주는 것처럼, **AI를 역할별로 여러 명 띄워 역할 분담**."

4단계 파이프라인:

```
[1] Supervisor (총괄 매니저)
    → 사용자 질문 분석
    → JSON 반환: {"agents": ["schedule", "place"]}
[2] 전문가들 병렬 실행
    - schedule: search_game 도구 전담
    - strategy: predict + weather 전담
    - place: find_places 전담
[3] Synthesizer (통합 작성자)
    → 전문가 결과를 자연스러운 한국어로 통합
    → 지역 방언 1회 · 가격·시간 포함 · 4~5문장
```

**왜?**: 한 AI가 모든 걸 하는 것보다, **역할 분리** 하면 각 전문가 프롬프트를 짧고 명확하게 유지할 수 있고, 결과 품질이 더 일관됩니다.

### 📚 RAG (Retrieval-Augmented Generation) — "참고 자료 먼저, 답변 나중"

**쉽게 말하면**:
> "AI에게 답을 시키기 전, **우리가 준비한 지식 문서**에서 관련 내용을 먼저 찾아서 같이 주는 방식."

이 프로젝트에서는 **45개 구장별 원정 팁** 을 지식 베이스로 둡니다:
- "잠실은 2·3루 외야가 햇빛 덜 듭니다"
- "광주는 경기 전 송정역시장 간식 추천"
- ... (45개)

`search_knowledge("광주 원정 팁")` 호출 시:
1. 45개 팁 중 **"광주"** 관련 + 키워드 매칭 상위 3개 추출
2. 그 3개를 LLM 프롬프트에 함께 주입
3. LLM이 그 팁을 근거로 답변 작성

**장점**: AI가 일반 상식으로 답하는 대신, **우리가 직접 큐레이션한 정보**로 답합니다.

### 🌧 기상청 API 이식 — "Python 수학 공식을 TypeScript로"

기상청 단기예보 API는 WGS84 위경도가 아닌 **Lambert 격자 좌표** 를 요구합니다. 변환 공식을 Python 원본에서 TypeScript로 정확히 옮겨왔습니다.

```
(위도 37.5, 경도 127.0) → Lambert 변환 → (nx=60, ny=127) → 기상청 API 호출
```

비유: "네이버 지도는 km 단위로 말하는데, 기상청만 '격자 좌표' 로 말하는 고집이 있어서 번역기를 만든 셈."

### ⚡ 스트리밍 — "ChatGPT처럼 실시간 타이핑"

AI 답변이 완성되길 기다리지 않고, **한 글자씩 흘러나오듯** 보여줍니다 (Server-Sent Events 기반).

- 체감 속도 ↑ (첫 글자가 1초 이내 등장)
- 긴 답변도 지루하지 않게 읽기 가능
- 도구 호출 결과도 실시간 카드로 삽입됨

구현: Vercel AI SDK의 `streamText` + `UIMessageStream`.

### 📱 모바일 전용 뷰 — Glass-Pill 입력창

iOS 의 Messages 앱 입력창을 참고한 **둥근 유리 느낌의 입력바**. 모바일에서 키보드가 올라와도 자연스럽게 위로 뜨며, 40×40 전송 버튼은 44px 터치 타깃을 충족합니다.

### 🔗 데이터 흐름 한눈에 보기

```
👤 사용자 질문
   │
   ▼
[1] Gemini LLM 이 질문 의도 분석
   │
   ├─ 도구가 필요한가? → 예
   │    │
   │    ▼
   │  [2] 도구 호출 (search_game · get_weather · ...)
   │    │ 실제 데이터 조회
   │    ▼
   │  [3] 결과를 LLM 에 다시 주입
   │
   └─ RAG 가 필요한가? → 예
        │
        ▼
      45 팁 중 관련 3개 추출 → 프롬프트에 삽입
   │
   ▼
[4] LLM 이 모든 재료 종합 → 스트리밍 답변
   │
   ▼
📱 UI 에 실시간 타이핑 표시
```

---

## 🎯 結 (결) — 어떤 가치를 만들었는가? 결과와 의미

### 숫자로 본 성과

| 지표 | 결과 |
|---|---|
| AI 모델 | **Google Gemini 2.5 Flash Lite** (무료 티어) |
| 도구 수 | **6개** (경기·승률·날씨·맛집·길찾기·팁) |
| Multi-Agent | **4단계** 파이프라인 (총괄·일정·전략·맛집·작성자) |
| RAG 팁 | **45개** 구장별 원정 팁 |
| 스트리밍 | ChatGPT급 실시간 타이핑 |
| 0건 응답 처리 | "해당 원정 경기 일정은 없습니다" 명시적 메시지 ✅ |
| Mock 시연 | 3 시나리오 즉시 응답 · 네트워크 불안정 무관 |
| 라이브 주소 | [배포 완료 ✅](https://my-web-app--mini12-310f5.asia-east1.hosted.app/ai) |

### 사용자에게 남기는 것

**"질문 하나에 · 실제 데이터를 조회해서 · 한국어로 자연스럽게 · 근거까지 제시하는 전용 AI."**

- ChatGPT는 **"실시간 데이터를 몰라서"** 답 못하는 질문에 답합니다
- 구단 앱은 **"자연어 대화"** 가 불가능한 걸 이 탭이 해결합니다
- 대화 속에서 "다음 원정 일정 → 그날 날씨 → 근처 맛집 → 서울역에서 경로" 를 **하나의 흐름** 으로 이어갈 수 있습니다

### 기술적 의의

- **실무급 AI 에이전트 시스템 구축**: 단순 챗봇을 넘어 **tool calling + multi-agent + RAG + 스트리밍** 4대 기술을 한 프로젝트에서 통합
- **무료 티어로 운영 가능**: Gemini Flash Lite의 관대한 무료 할당을 활용 → 학생·개인 프로젝트에서도 AI 서비스 운영 가능함을 증명
- **Python → TypeScript 이식**: 기상청 Lambert 격자 변환, 로지스틱 회귀 모델 등 **Python 원본의 수학을 정확히 재현**
- **발표·시연 견고성**: Mock 모드로 네트워크·API 실패와 무관하게 3 시나리오 안정 재현

---

## 🔍 부록 — 개발자용 상세 정보

아래는 코드를 다루는 개발자를 위한 참조입니다. 일반 독자는 건너뛰어도 좋습니다.

### A. API 명세

**`POST /api/chat`**

Request body:
```ts
{
  id: string,                    // conversation id
  messages: UIMessage[],         // chat history
  multiAgent: boolean,
  filters: {
    team: string,
    dateRange: [string, string],
    budget: number,
    party: "solo" | "couple" | "family" | "friends",
    transport: "train" | "car" | "bus",
    demoMode: boolean,
  },
}
```

Response: `text/event-stream` (UIMessageStream)
- `text-delta` 청크 → 본문
- `tool-input-available`, `tool-output-available` → 도구 호출
- `finish` → 종료

503 Graceful: `GEMINI_API_KEY` 미등록 시. Mock 모드는 무관하게 작동.

### B. 6 도구 상세

| 도구 | 입력 | 출력 |
|---|---|---|
| `search_game` | team · startDate? · endDate? | `{ count, summary, games, message? }` (0건 시 message 포함) |
| `predict_win_rate` | team · opponent | `{ win_probability, win_percentage, source }` |
| `get_weather` | stadium | `{ temp_c, sky, pty, rain_mm, hours[] }` |
| `find_places` | stadium · category · maxCount? | POI 상위 N건 |
| `get_route` | origin · destination | Tab 2 3-tier 재사용 |
| `search_knowledge` | query · stadium? | BM25-lite 상위 3~5 팁 |

### C. 시스템 프롬프트 답변 원칙 (`lib/ai/prompts.ts`)

1. 반드시 한국어로만
2. 3~5문장 이내 간결
3. 구체적 장소명·가격·시간
4. 앱 내 기능 연결 ("지도 탭에서 확인")
5. 모르는 정보는 추측 금지
6. 금액은 "3만원대" · 시간은 "15분"
7. **도구 결과 0건 시 "해당 원정 경기 일정은 없습니다" 명시**

### D. 컴포넌트 매핑

| 컴포넌트 | 파일 | 역할 |
|---|---|---|
| `ChatUI` | `components/ai/chat-ui.tsx` | 상태 소유 · 양쪽 뷰 라우팅 |
| `AiMobileView` | `components/ai/ai-mobile-view.tsx` | 모바일 · glass-pill 입력 |
| `AiDesktopView` | `components/ai/ai-desktop-view.tsx` | 데스크톱 · textarea 입력 |
| `MessageBubble` | `components/ai/message-bubble.tsx` | 말풍선 + 도구 카드 |
| 챗 API | `app/api/chat/route.ts` | streamText 진입점 |
| 도구 정의 | `lib/ai/tools.ts` | 6 tool + Zod 스키마 |
| Multi-Agent | `lib/ai/agents.ts` | 4단계 파이프라인 |
| 프롬프트 | `lib/ai/prompts.ts` | 시스템·에이전트별 |
| RAG | `lib/ai/rag.ts` | BM25-lite + 45 팁 인덱싱 |
| Mock | `lib/ai/mock.ts` | 3 시나리오 키워드 매칭 |
| 기상 | `lib/api/weather.ts` | Lambert 격자 변환 + KMA API |

### E. 기술 스택

| 계층 | 기술 |
|---|---|
| LLM | Google Gemini 2.5 Flash Lite |
| SDK | Vercel AI SDK v6 (`ai`, `@ai-sdk/google`, `@ai-sdk/react`) |
| 도구 정의 | `tool()` + Zod 스키마 |
| RAG | 인메모리 BM25-lite (자체 구현) |
| 기상 | 기상청 단기예보 API · Lambert 격자 변환 |
| 상태 관리 | Zustand (filters) + `useChat` (Vercel AI) |
| UI | Tailwind v4 + SE 디자인 토큰 |
| 토스트 | sonner |

### F. 관련 문서

- [SESSION_E_PLAN.md](./SESSION_E_PLAN.md) — AI 챗봇 구현 설계 원본
- [TAB1_MATCHES_SPEC.md](./TAB1_MATCHES_SPEC.md) — `predict_win_rate` 연동
- [TAB2_MAP_SPEC.md](./TAB2_MAP_SPEC.md) — `get_route` 연동
- [TAB3_PLACES_SPEC.md](./TAB3_PLACES_SPEC.md) — `find_places` 연동
- `frontend/lib/ai/tools.ts` — 6 도구 구현
- `frontend/lib/ai/agents.ts` — Multi-Agent 파이프라인
- `frontend/lib/ai/prompts.ts` — 시스템 프롬프트 + 답변 원칙
- `frontend/app/api/chat/route.ts` — streamText 진입점
- `frontend/components/ai/chat-ui.tsx` — 얇은 라우터
- `frontend/components/ai/ai-mobile-view.tsx` / `ai-desktop-view.tsx`
