# Phase 7 — Tool Calling (`rag_chatbot/tools/`)

RAG 챗봇(Phase 5 D3) 위에 얹는 Function-Calling 레이어. 8 개의 Tool Function 으로 `lunch-optimizer` REST API 를 LLM 이 직접 호출할 수 있다.

## 모듈

| 파일 | 역할 |
|---|---|
| `definitions.py` | 8 Tool 의 JSON Schema (Ollama/OpenAI 호환) |
| `executors.py` | 각 tool → lunch-optimizer HTTP 호출 wrapper. 테스트 용 `http_get/post` 인젝션 지원 |
| `fallback.py` | `[TOOL: name(args)]` regex 파서 — native tool calling 미지원 모델 폴백 |
| `router.py` | 한글 키워드 → tool 휴리스틱 라우터 (최후의 안전망) |
| `formatter.py` | tool 결과 → 짧은 Korean summary (LLM 재주입용) |
| `../tool_bot.py` | `ToolCallingBot` 클래스 — LLM → 파싱 → 실행 → 재호출 루프 |

## 8 Tool Functions

| # | 이름 | 종류 | lunch-optimizer endpoint |
|---|---|---|---|
| 1 | `get_lunch_recommendations` | 읽기 | `GET /api/recommend` |
| 2 | `get_current_weather` | 읽기 | `GET /api/weather/current` |
| 3 | `get_nutrition_diagnosis` | 읽기 | `GET /api/nutrition/diagnosis` |
| 4 | `get_restaurant_info` | 읽기 | `GET /api/restaurants/{id}` (+ `/nutrition/restaurant/{id}`) |
| 5 | `cast_vote` | 쓰기 | `POST /api/vote/cast` |
| 6 | `get_vote_status` | 읽기 | `GET /api/vote/status` |
| 7 | `record_meal` | 쓰기 | `POST /api/nutrition/meal` |
| 8 | `get_visit_history` | 읽기 | `GET /api/history/visits` |

## 호출 루프

```
user → ToolCallingBot.chat()
  ↓ LLM (system prompt with tool list)
  ↓ raw response: "날씨를 확인할게요. [TOOL: get_current_weather]"
  ↓ parse_tool_calls() → [{name, args}]
  ↓ ToolExecutor.execute() → HTTP call → dict
  ↓ format_tool_result() → short Korean summary
  ↓ inject back into messages
  ↓ LLM (final answer with data)
  ↓ strip_tool_calls(raw) → clean response text
```

`max_iterations=3` 로 무한루프 방어.

## API 엔드포인트

```bash
# Tool calling chat turn
curl -X POST http://localhost:8001/nlp/chatbot/chat/tools \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"user1","query":"오늘 날씨 어때? 추운 날 뭐 먹지?"}'

# Tool schemas (for UI help panel)
curl http://localhost:8001/nlp/chatbot/tools
```

응답 shape:

```json
{
  "response": "오늘은 18°C 흐림입니다. 따뜻한 국물 요리로 ...",
  "tool_calls": [
    {"name": "get_current_weather", "args": {}},
    {"name": "get_lunch_recommendations", "args": {"top_n": 3}}
  ],
  "tool_results": [
    {"ok": true, "tool": "get_current_weather", "data": {...}},
    {"ok": true, "tool": "get_lunch_recommendations", "data": [...]}
  ],
  "iterations": 2,
  "latency_ms": 1842,
  "fallback_used": false
}
```

## 테스트

```bash
cd NLP
PYTHONPATH=. pytest nlp_mvp/rag_chatbot/tools/tests/ -v
# → 23 passed
```

모든 테스트는 HTTP 를 mock 해서 네트워크 없이 동작한다.

## React Concierge 통합

`dashboard-web/src/app/concierge/page.tsx` 에 모드 토글 추가:

- **RAG 모드** (기본): 기존 SSE 토큰 스트리밍 (`/chat/stream`)
- **Tools 모드**: 본 엔드포인트 (`/chat/tools`) 호출 후 tool 호출 트레이스를 칩으로 표시

`MessageBubble` 이 `toolResults` 배열을 받으면 ✓/✗ 칩으로 렌더링, `fallbackUsed=true` 시 `⚡ heuristic` 경고 칩 추가.

## 한계 및 후속

- **네이티브 tool calling 미구현** — Ollama 0.5+ 가 `tools` 파라미터를 지원하지만 본 구현은 프롬프트 파싱 방식만 사용 (호환성 최대화). 후속에서 Qwen 3/GPT 호환 native 경로 추가 예정.
- **멀티턴 이력 미보존** — 매 `chat()` 호출이 독립. 세션 히스토리는 Phase 8 로 유예.
- **Tool 권한 제어 없음** — 현재 모든 사용자가 `cast_vote`/`record_meal` 호출 가능. 프로덕션에서는 user_id 검증 필요.
