# 04. API 명세 (lunch-api 45 + nlp-api 18)

## 0. 개요

Mini 시스템은 두 개의 독립된 FastAPI 서비스로 구성됩니다:
- **lunch-api** (`mini-lunch-api`, port 8000) — 데이터 수집·추천·투표·소셜
- **nlp-api** (`mini-nlp-api`, port 8001) — 감성·메뉴 정규화·RAG·NLG·Tool Calling

두 서비스는 **공유 SQLite 볼륨**(mini-db)을 통해 동일한 데이터를 읽고 씁니다.

### 0.1 공통 사양
- **Content-Type**: application/json
- **CORS**: `http://localhost:3000`, `http://localhost:5173` (env로 확장 가능)
- **Security Headers**: 모든 응답에 X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- **인증**: 미구현 (사용자는 ID 기반)
- **에러 포맷**: `{ "detail": "...", "error_code"?: "..." }` (FastAPI HTTPException 표준)
- **Rate Limit** (NLP): slowapi `@rate_limit("10/minute")` 일부 엔드포인트

---

## 1. lunch-api — Meta & Health (2)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/health` | 헬스체크 (DB 연결, 마지막 수집 시각) |
| POST | `/api/pipeline/run` | 수동 파이프라인 트리거 |

### 1.1 `GET /api/health`
**Response 200**
```json
{
  "status": "ok",
  "db": "connected",
  "last_restaurant_collection": "2026-04-27T01:00:00+09:00",
  "last_weather_collection": "2026-04-27T08:05:00+09:00"
}
```

### 1.2 `POST /api/pipeline/run`
**Request**
```json
{ "target": "daily" | "restaurant" | "weather" | "nutrition" }
```
**Response 200**: `{ "status": "started", "job_id": "...", "target": "daily" }`

---

## 2. lunch-api — Restaurants (5)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/restaurants` | 활성 음식점 리스트 (필터/limit) |
| GET | `/api/restaurants/stats` | 집계 통계 (카테고리/평균거리/점수) |
| GET | `/api/restaurants/nearby` | 사용자 위치 기반 검색 (on-demand Kakao 캐시) |
| GET | `/api/restaurants/{id}` | 단건 상세 |
| POST | `/api/pipeline/run` | (Meta 섹션 중복) |

### 2.1 `GET /api/restaurants`
**Query**: `limit=200`, `category=한식`, `min_score=50`, `is_active=true`
**Response 200**
```json
[
  {
    "id": "kakao_12345",
    "name": "김치찌개 명가",
    "category": "한식",
    "sub_category": "찌개,전골",
    "lat": 37.5670,
    "lng": 126.9785,
    "address": "서울시 종로구 ...",
    "place_url": "https://place.map.kakao.com/...",
    "distance_m": 145,
    "distance_score": 85,
    "rating": 4.2,
    "visit_count": 12,
    "is_active": true,
    "menuType": "한식"
  }
]
```

### 2.2 `GET /api/restaurants/nearby`
**Query**: `lat`, `lng` (필수), `radius=800`, `limit=50`
- TTL 캐시 5min, 100m grid 양자화
- 캐시 미스 시 Kakao Local API 호출

### 2.3 `GET /api/restaurants/stats`
```json
{
  "total_active": 234,
  "categories": [
    { "name": "한식", "count": 95 },
    { "name": "중식", "count": 42 }
  ],
  "avg_distance_m": 312,
  "avg_score": 67.5
}
```

---

## 3. lunch-api — Weather (5)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/weather/current` | 현재 기상 + 가이드 팁 |
| GET | `/api/weather/history` | 시간 단위 이력 |
| GET | `/api/weather/menu-ranking` | 메뉴 유형별 적합 점수 정렬 |
| GET | `/api/weather/ranked-restaurants` | 음식점 weather score 정렬 |
| POST | `/api/weather/refresh` | 즉시 갱신 |

### 3.1 `GET /api/weather/current`
**Query**: `lat?`, `lng?` (없으면 사무실 기본 좌표)
**Response 200**
```json
{
  "temp": 16.4,
  "humidity": 62,
  "rain_type": 0,
  "rain_type_str": "없음",
  "rain_1h": 0.0,
  "wind_speed": 2.1,
  "sky": 1,
  "sky_str": "맑음",
  "pop": 10,
  "dust_grade": "보통",
  "pm10": 45,
  "pm25": 22,
  "outdoor_comfort": 78,
  "tips": ["야외 활동 적합", "면류 또는 가벼운 식사 추천"]
}
```

---

## 4. lunch-api — Nutrition (6)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/nutrition/restaurants/{id}` | 음식점 영양 정보 |
| POST | `/api/nutrition/record-meal` | 사용자 식사 기록 |
| GET | `/api/nutrition/weekly-summary` | 주간 요약 |
| GET | `/api/nutrition/diagnosis` | 영양 건강도 진단 |
| GET | `/api/nutrition/trend` | 7일 추이 |
| GET | `/api/nutrition/ranked-restaurants` | 영양 점수 정렬 |

### 4.1 `POST /api/nutrition/record-meal`
**Request**
```json
{
  "user_id": 1,
  "restaurant_id": "kakao_12345",
  "menu_name": "김치찌개",
  "meal_date": "2026-04-27",
  "satisfaction": 5
}
```

### 4.2 `GET /api/nutrition/weekly-summary?user_id=1`
```json
{
  "user_id": 1,
  "week_start": "2026-04-21",
  "days": [
    {"day": "2026-04-21", "calories": 720, "protein": 28, "carbs": 95, "fat": 18, "target": 800},
    ...
  ],
  "avg_calories": 680,
  "avg_protein": 24.5,
  "balance_status": "단백질 부족"
}
```

### 4.3 `GET /api/nutrition/diagnosis?user_id=1`
LLM/규칙 기반 종합 진단:
```json
{
  "user_id": 1,
  "verdict": "단백질 섭취가 권장량 70%에 머물러 있습니다.",
  "actions": ["단백질 위주 메뉴 추천", "고지방 점심 회피"],
  "data_warning": false
}
```

---

## 5. lunch-api — Vote (7)

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/vote/session` | 일일 투표 세션 생성 |
| POST | `/api/vote/cast` | 투표 행사 (1인 1표) |
| POST | `/api/vote/veto` | 거부권 |
| GET | `/api/vote/status` | 현재 세션 상태 |
| POST | `/api/vote/close` | 마감 + 우승자 확정 |
| GET | `/api/vote/history` | 최근 결과 |
| GET | `/api/history/visits` | 팀 방문이력 |

### 5.1 `POST /api/vote/cast`
**Request**
```json
{
  "user_id": 1,
  "restaurant_id": "kakao_12345",
  "vote_date": "2026-04-27"
}
```
**제약**: (user_id, vote_date) 유니크 — 같은 날 한 번만 투표

### 5.2 `GET /api/vote/status?team_id=team1&date=2026-04-27`
```json
{
  "team_id": "team1",
  "vote_date": "2026-04-27",
  "status": "open" | "closed",
  "total_votes": 5,
  "votes": [
    { "restaurant_id": "kakao_12345", "name": "김치찌개 명가", "count": 3 },
    { "restaurant_id": "kakao_67890", "name": "비빔밥 식당", "count": 2 }
  ]
}
```

---

## 6. lunch-api — Recommendation & Mood (3)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/recommend` | 4축 종합 추천 |
| GET | `/api/mood/options` | 날씨 기반 무드 옵션 |
| GET | `/api/mood/recommendation` | 무드별 그룹화 추천 |

### 6.1 `GET /api/recommend?team_id=team1&user_id=1&top_n=5`
```json
[
  {
    "restaurant_id": "kakao_12345",
    "name": "김치찌개 명가",
    "category": "한식",
    "distance_m": 145,
    "distance_score": 85,
    "weather_score": 78,
    "nutrition_score": 65,
    "team_score": 90,
    "composite_score": 81.2,
    "reason": "거리 가깝고, 비 오는 날 국물 적합"
  }
]
```

---

## 7. lunch-api — Users (4)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/users` | 팀원 리스트 |
| GET | `/api/users/{id}` | 단건 |
| POST | `/api/users` | 생성/upsert |
| PATCH | `/api/users/{id}/preferences` | 선호도 갱신 |

### 7.1 `POST /api/users`
**Request**
```json
{
  "id": "user_abc",
  "name": "홍길동",
  "team_id": "team1",
  "avatar_emoji": "🐱"
}
```
**Response**: 멱등 — 동일 id면 업데이트

### 7.2 `PATCH /api/users/{id}/preferences`
```json
{
  "dislike_categories": ["일식", "양식"],
  "allergy_info": ["우유", "땅콩"]
}
```

---

## 8. lunch-api — Chat (2 + WebSocket)

| Method | Path | 설명 |
|---|---|---|
| WS | `/ws/chat/{team_id}` | 실시간 팀 채팅 |
| GET | `/api/chat/messages` | 메시지 히스토리 (페이지네이션) |

### 8.1 WebSocket 메시지 포맷
**Client → Server**
```json
{
  "user_id": "user_abc",
  "user_name": "홍길동",
  "avatar_emoji": "🐱",
  "message": "오늘 김치찌개 어때요?"
}
```
**Server broadcast**
```json
{
  "id": 1234,
  "team_id": "team1",
  "user_id": "user_abc",
  "user_name": "홍길동",
  "avatar_emoji": "🐱",
  "message": "오늘 김치찌개 어때요?",
  "created_at": "2026-04-27T11:24:13+09:00"
}
```

---

## 9. lunch-api — Buddy (밥친구, 7)

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/buddy/posts` | 모집 글 작성 |
| GET | `/api/buddy/posts` | 리스트 (team/date 필터) |
| GET | `/api/buddy/posts/{id}` | 단건 |
| POST | `/api/buddy/posts/{id}/join` | 참여 |
| DELETE | `/api/buddy/posts/{id}/join` | 탈퇴 |
| PATCH | `/api/buddy/posts/{id}` | 수정 (작성자만) |
| GET | `/api/buddy/posts/{id}/participants` | 참여자 |

### 9.1 `POST /api/buddy/posts`
```json
{
  "team_id": "team1",
  "author_id": "user_abc",
  "restaurant_id": "kakao_12345",
  "restaurant_name": "김치찌개 명가",
  "meal_date": "2026-04-27",
  "meal_time": "12:30",
  "max_buddies": 4,
  "message": "같이 가실 분?"
}
```

---

## 10. lunch-api — Slack Notification (1)

| Method | Path | 설명 |
|---|---|---|
| POST | `/notify/slack` | Slack 메시지 푸시 |

### 10.1 Request
```json
{
  "event": "vote_result",
  "title": "오늘의 점심: 김치찌개 명가",
  "body": "김치찌개 명가 — 5표 · 한식 · 145m",
  "emoji": "🎉"
}
```
**Response**
```json
{ "sent": true, "status_code": 200 }
```
- 환경 변수 `SLACK_WEBHOOK_URL` 미설정 시 `{ "sent": false, "error": "no webhook" }`

---

## 11. nlp-api — Health & Settings (2)

| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/health` | 모듈 헬스 (4 components) |
| PUT | `/nlp/settings/model` | Ollama 모델 핫 스왑 |

### 11.1 `GET /nlp/health`
```json
{
  "status": "ok",
  "version": "0.1.0",
  "modules": {
    "db": "ok",
    "menu_normalizer": "ok",
    "rag_chatbot_index": "ok",
    "nlg_generator": "ok",
    "scoring_patch_ab": "skipped",
    "research_v2": "skipped"
  }
}
```
- `pending`: 모델 로딩 중 (503 응답 가능)
- `degraded`: 일부 기능 동작
- `error`: 사용 불가

### 11.2 `PUT /nlp/settings/model?model=qwen3.5:9b`
- `OLLAMA_MODEL` 환경 변수 갱신 + 모든 챗봇 세션 초기화

---

## 12. nlp-api — Sentiment (3)

| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/sentiment/top?limit=10` | TOP 감성 점수 |
| GET | `/nlp/sentiment/{restaurant_id}` | 단건 |
| POST | `/nlp/sentiment/refresh` | 배치 업데이트 |

### 12.1 `GET /nlp/sentiment/{id}`
```json
{
  "restaurant_id": "kakao_12345",
  "score": 0.62,        // (pos - neg) / total ∈ [-1, +1]
  "pos_ratio": 0.78,
  "neu_ratio": 0.10,
  "neg_ratio": 0.12,
  "review_count": 84,
  "updated_at": "2026-04-26T22:00:00+09:00"
}
```
- `score: null` && `reason: "insufficient_samples"` (sample < 5)

### 12.2 `POST /nlp/sentiment/refresh`
- Rate Limit: 1/minute
- Body: `{ "limit": 100, "min_reviews": 5, "source": "synthetic" }`

---

## 13. nlp-api — Menu Normalization (2)

| Method | Path | 설명 |
|---|---|---|
| POST | `/nlp/menu/normalize` | 메뉴명 정규화 |
| GET | `/nlp/menu/stats` | 배치 통계 |

### 13.1 `POST /nlp/menu/normalize`
**Request**: `{ "raw_name": "김찌" }`
**Response**
```json
{
  "raw": "김찌",
  "cleaned": "김치찌개",
  "matched_id": "menu_001",
  "matched_name": "김치찌개",
  "confidence": 1.0,
  "method": "rule",       // rule | levenshtein | embedding | none | error
  "latency_ms": 3
}
```

### 13.2 `GET /nlp/menu/stats`
```json
{
  "total": 1248,
  "matched": 1062,
  "hit_rate": 0.851,
  "by_method": {
    "rule": 412,
    "levenshtein": 380,
    "embedding": 270,
    "none": 186
  }
}
```

---

## 14. nlp-api — Chatbot (4 + SSE)

| Method | Path | 설명 |
|---|---|---|
| POST | `/nlp/chatbot/chat` | 동기 단발 |
| POST | `/nlp/chatbot/chat/stream` | SSE 스트리밍 |
| POST | `/nlp/chatbot/chat/tools` | Tool Calling 모드 (Phase 7) |
| POST | `/nlp/chatbot/reset` | 세션 초기화 |
| GET | `/nlp/chatbot/stats` | 통계 (latency, hallucination 등) |

### 14.1 `POST /nlp/chatbot/chat`
**Request**: `{ "user_id": "user_abc", "query": "오늘 비 오는데 뭐 먹지?" }`
**Response (200)**
```json
{
  "response": "비 오는 날엔 따뜻한 국물이 좋겠죠. 🍲 ...",
  "recommendations": [
    {"restaurant": "김치찌개 명가", "menu": "김치찌개", "reason": "가깝고 따뜻한 국물"}
  ],
  "context_summary": {
    "meal_history_count": 12,
    "nutrition_info_count": 84,
    "restaurants_count": 234
  },
  "validation": {
    "valid": true,
    "mentioned_count": 1,
    "issues": []
  },
  "latency_ms": 1240
}
```
- Rate Limit: 10/min

### 14.2 `POST /nlp/chatbot/chat/stream` (SSE)
Frame 시퀀스:
```
data: {"type":"meta","context_summary":{...}}\n\n
data: {"type":"token","text":"비 "}\n\n
data: {"type":"token","text":"오는 "}\n\n
...
data: {"type":"final","recommendations":[...],"validation":{...},"latency_ms":1240}\n\n
data: [DONE]\n\n
```

### 14.3 `POST /nlp/chatbot/chat/tools`
**Request**
```json
{
  "user_id": "user_abc",
  "query": "오늘 점심 뭐 먹을까? 비 와서 가까운 곳",
  "temperature": 0.2,
  "max_iterations": 3
}
```
**Response**
```json
{
  "response": "비 오니까 가까운 김치찌개 명가가 좋겠어요.",
  "tool_calls": [
    { "name": "get_current_weather", "args": {} },
    { "name": "get_lunch_recommendations", "args": {"team_id": "team1", "top_n": 3} }
  ],
  "tool_results": [
    { "ok": true, "tool": "get_current_weather", "data": {...} },
    { "ok": true, "tool": "get_lunch_recommendations", "data": [...] }
  ],
  "iterations": 2,
  "latency_ms": 2150,
  "fallback_used": false
}
```

---

## 15. nlp-api — Reports (2)

| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/reports/weekly/{user_id}` | 주간 리포트 조회 |
| POST | `/nlp/reports/weekly/{user_id}/regenerate` | LLM 재생성 |

### 15.1 응답 스키마
```json
{
  "user_id": 1,
  "week_start": "2026-04-21",
  "week_label": "4월 4주차",
  "text": "이번 주 평균 단백질 24g으로 살짝 부족했어요. 🍳 ...",
  "generation_method": "llm" | "template" | "minimal",
  "validation": {
    "valid": true,
    "length": 268,
    "emoji_count": 3,
    "issues": []
  }
}
```

---

## 16. nlp-api — Insights (보조, 2)

| Method | Path | 설명 |
|---|---|---|
| GET | `/nlp/rag/stats` | RAG 인덱스 통계 |
| GET | `/nlp/models` | Ollama 모델 리스트 |

### 16.1 `GET /nlp/models`
```json
{
  "active_model": "qwen2.5:7b",
  "available": [
    { "name": "qwen2.5:7b", "size_gb": 4.7, "loaded": true },
    { "name": "qwen3.5:9b", "size_gb": 5.5, "loaded": false }
  ]
}
```

---

## 17. nlp-api — Research V2 (선택, 옵션)

`PYTHONPATH`에 `nlp_research`가 있을 때만 활성화. 그 외에는 `_MODULE_STATUS["research_v2"] = "skipped"`.

| Method | Path | 설명 |
|---|---|---|
| POST | `/nlp/v2/absa` | ABSA 추론 (속성기반 감성) |
| POST | `/nlp/v2/menu/extract` | Food NER (FOOD/INGREDIENT/ALLERGEN) |
| GET | `/nlp/v2/recommendations/{user_id}` | 임베딩 기반 추천 |

---

## 18. 호출 흐름 다이어그램 (대표 시나리오)

### 18.1 Discover 페이지 로딩
```
Browser                                     lunch-api      nlp-api
  │                                              │             │
  │ useGeolocation() → { lat, lng }              │             │
  │ GET /api/restaurants/nearby?lat&lng&r=800   →│             │
  │                                              │ Kakao 캐시  │
  │ ←─ 50건 음식점 ──────────────────────────────│             │
  │ for each: GET /nlp/sentiment/{id} ──────────┼────────────→│
  │                                              │             │ DB 조회
  │ ←─ 감성 점수 (병렬) ─────────────────────────┼─────────────│
  │ → 정렬·필터·렌더링                            │             │
```

### 18.2 Vote 종료 + Slack
```
Browser                                     lunch-api      Slack Webhook
  │                                              │
  │ POST /api/vote/close { team_id, date } ────→ │
  │                                              │ DB 업데이트
  │                                              │ winner 결정
  │ ←─ { winner, votes } ────────────────────────│
  │                                              │
  │ POST /notify/slack { event, title, ... } ─→  │ ──→ webhook
  │ ←─ { sent: true } ───────────────────────────│
```

### 18.3 Concierge SSE
```
Browser                                  nlp-api      Ollama
  │                                         │            │
  │ POST /nlp/chatbot/chat/stream ─────────→│            │
  │                                         │ ChromaDB query
  │                                         │ → context
  │                                         │ ollama.chat(stream=True) →│
  │ ← data:{"type":"meta",...}              │ ←──── token stream ──────│
  │ ← data:{"type":"token","text":"비 "}    │                          │
  │ ← data:{"type":"token","text":"오는 "}  │                          │
  │ ...                                     │                          │
  │ ← data:{"type":"final",...}             │                          │
  │ ← data:[DONE]                           │                          │
```

---

## 19. 운영자 도구

### 19.1 OpenAPI/Swagger UI
- lunch-api: `http://localhost:8000/docs`
- nlp-api:   `http://localhost:8001/docs`
- Try-it-out으로 모든 엔드포인트 인터랙티브 테스트

### 19.2 ReDoc
- `http://localhost:8000/redoc`

### 19.3 Health 모니터링
```bash
# 1줄 헬스체크
curl -s http://localhost:8000/api/health | jq .
curl -s http://localhost:8001/nlp/health | jq .
```

---

## 20. 베스트 프랙티스

1. **클라이언트 캐싱**: TanStack Query staleTime을 활용 — 60s ~ 5min에 따라 부하 분산
2. **위치 양자화**: lat/lng 100m 격자로 반올림하여 캐시 hit rate 향상
3. **NLP Warming 핸들링**: 503 응답을 폴백 → 지수 백오프 → mock 데이터 표출
4. **Rate Limit 대응**: 챗봇 응답에 `Retry-After` 헤더 준수
5. **WebSocket 재연결**: 5회 실패 후 사용자에게 명시적 재시도 버튼 노출

---

> *각 NLP 엔드포인트의 내부 알고리즘은 「05. NLP MVP」, 데이터 모델은 「07. 데이터 모델」 참고.*
