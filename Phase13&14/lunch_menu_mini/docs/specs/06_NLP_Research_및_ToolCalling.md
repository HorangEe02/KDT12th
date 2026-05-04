# 06. NLP Research (Phase 6) 및 Tool Calling (Phase 7)

## 0. 개요

본 문서는 Phase 5 MVP를 기반으로 발전된 두 영역을 다룹니다:

- **Phase 6 (Research)**: 속성기반 감성·음식 NER·임베딩 협업필터링 — 실험 모델 (코드 완료, 학습/실서비스 대기)
- **Phase 7 (Tool Calling)**: LLM이 lunch-api 엔드포인트를 함수처럼 호출 — 실서비스 가능 (23개 테스트 통과)

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 5 (실서비스)                                           │
│  └─ A1 Sentiment   B1 Menu Norm   D3 RAG   D5 NLG           │
│                                                              │
│ Phase 6 (코드 완료)                                          │
│  └─ A2 ABSA   B2 Food NER   E1 Embedding CF   Benchmark     │
│                                                              │
│ Phase 7 (실서비스)                                           │
│  └─ Tool Calling (8 functions, ToolBot)                     │
└─────────────────────────────────────────────────────────────┘
```

### 0.1 디렉터리 구조
```
NLP/
├── nlp_mvp/                            # Phase 5
│   └── rag_chatbot/
│       ├── tool_bot.py                 # Phase 7 ToolCallingBot
│       └── tools/
│           ├── definitions.py          # 8 tool schemas
│           ├── executors.py            # HTTP wrappers
│           ├── fallback.py             # parser
│           ├── router.py               # heuristic intent
│           └── tests/test_tools.py     # 23 tests
└── nlp_research/                       # Phase 6
    ├── models/
    │   ├── absa/                       # A2
    │   ├── food_ner/                   # B2
    │   └── embedding_cf/               # E1
    ├── labeling/                       # LLM 라벨링 파이프라인
    ├── evaluation/                     # 벤치마크 자동화
    └── data/                           # 데이터셋 + 시드
```

---

## 1. Phase 6 — A2 Aspect-Based Sentiment (ABSA)

### 1.1 목적
A1 Sentiment가 리뷰 단위로 +/- 만 분류한다면, A2 ABSA는 **속성별로** 감성을 분리:
> "맛은 좋은데 가격이 비싸요" → `taste:positive`, `price:negative`

### 1.2 5개 속성 카테고리
| 속성 | 의미 |
|---|---|
| `taste` | 음식 맛, 향미 |
| `price` | 가격, 비용 |
| `service` | 직원 태도, 대기시간 |
| `hygiene` | 위생, 청결도 |
| `ambience` | 인테리어, 소음, 분위기 |

### 1.3 핵심 파일
| 파일 | 역할 |
|---|---|
| `models/absa/model.py` | BERT-SPC (Sentence-Pair Classification) |
| `models/absa/dataset.py` | JSONL 로더 + 속성 매핑 |
| `models/absa/train.py` | 학습 루프 (HF Trainer 패턴) |
| `models/absa/inference.py` | `ABSAInferencer` |
| `models/absa/evaluate.py` | F1/precision/recall |

### 1.4 데이터 포맷 (JSONL)
```jsonl
{"text": "맛이 좋은데 가격이 비쌌어요.", "aspects": [
    {"aspect": "taste", "sentiment": "positive"},
    {"aspect": "price", "sentiment": "negative"}
]}
```

### 1.5 BERT-SPC 모델 구조
- **Input**: `[CLS] sentence [SEP] aspect [SEP]`
- **Encoder**: KoBERT 또는 KcELECTRA fine-tune
- **Head**: 3-class (positive/negative/neutral) softmax
- **Loss**: CrossEntropy

### 1.6 LLM 라벨링 파이프라인 (`labeling/llm_label_absa.py`)
```python
# 1. 미라벨 리뷰 추출
SELECT DISTINCT text FROM reviews WHERE id NOT IN (SELECT review_id FROM absa_labels);

# 2. Ollama로 구조화 추출 (low temp)
prompt = """
주어진 리뷰에서 5개 속성 (taste, price, service, hygiene, ambience) 각각에 대해
positive/negative/neutral을 JSON으로 출력하세요. 언급되지 않은 속성은 omit.

리뷰: {text}

JSON:
"""

# 3. 결과 검증 + 중복 제거
# 4. JSONL 저장: data/labeled/absa/gold_llm.jsonl
```

### 1.7 학습 명령
```bash
python -m nlp_research.models.absa.train \
    --train data/labeled/absa/gold_llm.jsonl \
    --model klue/bert-base \
    --batch-size 16 \
    --epochs 5 \
    --lr 3e-5 \
    --output models/absa/checkpoints/
```

### 1.8 추론 API (활성 시)
```python
absa = ABSAInferencer.load("models/absa/checkpoints/best/")
result = absa.predict("맛은 좋은데 가격이 너무 비싸요")
# → [
#     {"aspect": "taste", "sentiment": "positive", "confidence": 0.92},
#     {"aspect": "price", "sentiment": "negative", "confidence": 0.88}
#   ]
```

### 1.9 통합 시 영향
- 음식점별 `aspect_score` 5축 추가 (taste/price/service/hygiene/ambience)
- 추천 엔진의 가중치 다양화: 사용자가 "분위기 좋은 곳" 요청 → ambience 비중↑
- Discover 페이지의 6축 레이더 차트 데이터 소스로 활용

---

## 2. Phase 6 — B2 Food NER (개체명 인식)

### 2.1 목적
리뷰/메뉴 텍스트에서 음식·재료·알레르기 유발물질을 자동 추출하여, 정규화·알레르기 필터·트렌드 분석에 활용.

### 2.2 3개 개체 유형
| 유형 | 예시 |
|---|---|
| `FOOD` | 카레, 스파게티, 김치찌개 |
| `INGREDIENT` | 치즈, 버터, 양파 |
| `ALLERGEN` | 우유, 계란, 땅콩, 새우 |

### 2.3 핵심 파일
| 파일 | 역할 |
|---|---|
| `models/food_ner/model.py` | KoELECTRA + Token Classification + (optional) CRF |
| `models/food_ner/dataset.py` | BIO tagging + DataLoader |
| `models/food_ner/train.py` | 학습 |
| `models/food_ner/inference.py` | 토큰 → 개체 매핑 |
| `models/food_ner/evaluate.py` | seqeval F1 |

### 2.4 BIO Tagging 예시
```
토큰:  치즈가  들어간  스파게티를  먹었다
태그:  B-INGR  O      B-FOOD     O
```

### 2.5 모델 구조
- **Backbone**: `monologg/koelectra-base-v3-discriminator`
- **Head**: 7 classes (B-FOOD/I-FOOD/B-INGR/I-INGR/B-ALLG/I-ALLG/O)
- **CRF**: `pytorch-crf` 라이브러리 (선택, 시퀀스 의존성 강화)
- **Loss**: NLL (with CRF) 또는 CrossEntropy

### 2.6 데이터셋 형식
```jsonl
{
  "tokens": ["치즈가", "들어간", "스파게티를", "먹었다"],
  "tags":   ["B-INGREDIENT", "O", "B-FOOD", "O"]
}
```

### 2.7 학습
```bash
python -m nlp_research.models.food_ner.train \
    --train data/labeled/ner/gold.jsonl \
    --model monologg/koelectra-base-v3-discriminator \
    --use-crf \
    --batch-size 32 --epochs 10
```

### 2.8 활용 시나리오
1. **알레르기 필터** — 메뉴 텍스트에서 ALLERGEN 추출 → 사용자 `allergy_info`와 매칭 → 추천 제외
2. **재료 트렌드** — 주간/월간 리뷰에서 INGREDIENT 빈도 분석
3. **메뉴 정규화 강화** — B1 Normalizer가 raw text에서 FOOD 토큰만 추출 후 매칭

---

## 3. Phase 6 — E1 Embedding Collaborative Filtering

### 3.1 목적
Sentence-BERT 임베딩 + FAISS 인덱스로 의미적 유사도 기반 음식점 추천. 사용자 식사 이력 → 비슷한 패턴 음식점 추천.

### 3.2 핵심 파일
| 파일 | 역할 |
|---|---|
| `models/embedding_cf/embedder.py` | `SBertEmbedder` 래퍼 |
| `models/embedding_cf/index.py` | FAISS 인덱스 빌더 |
| `models/embedding_cf/recommender.py` | 유사도 검색 → 랭킹 |
| `models/embedding_cf/evaluate.py` | Recall@K, NDCG |

### 3.3 임베딩 대상
- 사용자: 최근 식사 이력 텍스트 concat ("김치찌개 비빔밥 라멘 ...")
- 음식점: 메뉴 + 카테고리 + 감성 점수 컨텍스트

### 3.4 FAISS 인덱스
- 모델: `jhgan/ko-sroberta-multitask` (768-dim)
- 인덱스 타입: 
  - 소규모 (<10K): IndexFlatIP (cosine via L2 normalization)
  - 대규모: IndexIVFFlat (속도/메모리 trade-off)

### 3.5 추천 흐름
```python
def recommend(user_id: int, k: int = 10) -> list[Restaurant]:
    # 1. 사용자 식사 이력 텍스트 추출
    history = get_recent_meal_text(user_id, days=14)
    
    # 2. 임베딩
    user_vec = embedder.encode(history)
    
    # 3. FAISS 검색
    distances, indices = index.search(user_vec, k * 2)  # 여유분
    
    # 4. 후처리: 이미 방문한 곳 제외, 거리/평점 필터
    candidates = [restaurants[i] for i in indices[0]]
    return filter_and_rank(candidates, exclude_visited=True)[:k]
```

### 3.6 평가
```bash
python -m nlp_research.models.embedding_cf.evaluate \
    --user-history data/eval/user_meals.jsonl \
    --gold data/eval/visited.jsonl \
    --metric recall_at_10 ndcg_at_10
```

### 3.7 dashboard-web 연동
프론트엔드의 `useV2Recommendations(userId, topN, enabled)` 훅이 `/nlp/v2/recommendations/{user_id}` 엔드포인트와 매핑 (Phase 6 활성 시).

---

## 4. Phase 6 — 라벨링 파이프라인 & 평가

### 4.1 LLM-driven 라벨링 (`labeling/`)
- `llm_label_absa.py` — ABSA 라벨링
- `llm_label_ner.py` — NER 라벨링 (예정)
- 공통 패턴:
  ```python
  for review in unlabeled_reviews:
      prompt = build_prompt(review)
      response = ollama.chat([{"role":"user","content":prompt}], temperature=0.1)
      labels = parse_json_strict(response)
      validate_and_save(labels)
  ```

### 4.2 Label Studio 변환
`tests/test_convert_labelstudio.py` — Label Studio XML export → JSONL 표준 포맷

### 4.3 Benchmark 자동화 (`evaluation/benchmark.py`)
A2/B2/E1 모델 일괄 평가:
```bash
python -m nlp_research.evaluation.benchmark \
    --models absa food_ner embedding_cf \
    --output reports/benchmark_$(date +%Y%m%d).json
```

### 4.4 시드 데이터셋
- `data/seed/absa_seed.jsonl` (50건)
- `data/seed/ner_seed.jsonl` (50건)
- 1,000+ 라벨 확장 시 학습 → 실서비스 투입 (currently 대기)

---

## 5. Phase 7 — Tool Calling 개요

### 5.1 목적
LLM이 단순 응답 생성을 넘어, **lunch-api 엔드포인트를 함수처럼 호출**하여 실시간 데이터로 답변하거나 쓰기 작업(투표, 식사 기록)을 수행.

### 5.2 vs RAG 모드 차이
| | RAG Mode (D3) | Tool Mode (Phase 7) |
|---|---|---|
| 데이터 소스 | ChromaDB 색인 (정적) | lunch-api 호출 (실시간) |
| 쓰기 작업 | 불가 | 가능 (cast_vote, record_meal) |
| 응답 방식 | SSE 스트리밍 | non-streaming, 다중 iteration |
| 응답 시간 | ~1–2초 | ~2–5초 (도구 호출 포함) |

---

## 6. 8개 Tool 정의 (`tools/definitions.py`)

JSON Schema 포맷 (Ollama / OpenAI tool-use 호환):

### 6.1 Read Tools (조회 — 6개)

| 이름 | 매핑 엔드포인트 | 인자 |
|---|---|---|
| `get_lunch_recommendations` | GET `/api/recommend` | team_id, user_id, top_n |
| `get_current_weather` | GET `/api/weather/current` | (없음) |
| `get_nutrition_diagnosis` | GET `/api/nutrition/diagnosis` | user_id |
| `get_restaurant_info` | GET `/api/restaurants/{id}` | restaurant_id |
| `get_vote_status` | GET `/api/vote/status` | team_id |
| `get_visit_history` | GET `/api/history/visits` | team_id, days |

### 6.2 Write Tools (쓰기 — 2개)

| 이름 | 매핑 엔드포인트 | 인자 |
|---|---|---|
| `cast_vote` | POST `/api/vote/cast` | user_id, restaurant_id |
| `record_meal` | POST `/api/nutrition/record-meal` | user_id, restaurant_id, menu_name?, satisfaction? |

**보안 정책**: 시스템 프롬프트에 "쓰기 도구는 사용자가 명시적으로 요청할 때만 호출" 명시.

### 6.3 예시 정의 스키마
```python
{
    "type": "function",
    "function": {
        "name": "get_lunch_recommendations",
        "description": "4축 종합 점심 추천 (거리+날씨+영양+팀선호)",
        "parameters": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "default": "team1"},
                "user_id": {"type": "string", "default": "user1"},
                "top_n":   {"type": "integer", "default": 5}
            }
        }
    }
}
```

---

## 7. ToolExecutor (`tools/executors.py`)

### 7.1 클래스 책임
```python
class ToolExecutor:
    def __init__(
        self,
        base_url: str = "http://localhost:8000/api",
        http_get:    Callable | None = None,    # 의존성 주입 (테스트)
        http_post:   Callable | None = None,
        http_patch:  Callable | None = None,
    )
    
    def execute(self, name: str, args: dict) -> dict:
        """Dispatch by name → return {"ok": bool, "data|error": Any, "tool": str}"""
```

### 7.2 Dispatch 매핑 (예시)
```python
def execute(self, name, args):
    if name == "get_lunch_recommendations":
        return self.tool_get_lunch_recommendations(**args)
    elif name == "cast_vote":
        return self.tool_cast_vote(**args)
    # ... 8개 분기
```

### 7.3 에러 처리
- `ToolExecutionError` — HTTP 비정상 응답
- `TypeError` — 인자 검증 실패
- 모두 `{"ok": False, "tool": name, "error": str(e)}`로 변환되어 LLM에게 전달 (모델이 에러를 인지하고 다음 호출 결정)

---

## 8. Fallback Parser (`tools/fallback.py`)

### 8.1 목적
Ollama가 native function-calling을 지원하지 않거나 모델이 구조화 호출을 emit하지 않을 때, 텍스트에서 수동 파싱.

### 8.2 지원 문법
```
[TOOL: get_current_weather]
[TOOL: get_lunch_recommendations(team_id="team1", top_n=3)]
[TOOL: cast_vote(user_id="u1", restaurant_id=R001)]
```

### 8.3 Regex
```python
_BLOCK_RE = r"\[\s*TOOL\s*:\s*([^\[\]]+?)\s*\]"
_CALL_RE  = r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\((?P<args>.*)\))?\s*$"
_ARG_RE   = r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<val>\"[^\"]*\"|'[^']*'|[^,]+)"
```

### 8.4 함수
```python
def parse_tool_calls(text: str) -> list[dict]:
    """[{'name': 'get_current_weather', 'args': {}}, ...]"""

def strip_tool_calls(text: str) -> str:
    """Remove [TOOL: ...] blocks for display"""
```

---

## 9. Heuristic Router (`tools/router.py`)

### 9.1 목적
LLM이 도구를 전혀 호출하지 않을 때, 키워드 기반으로 1개 도구를 추측.

### 9.2 매핑 예시
| 사용자 쿼리 | 추천 도구 |
|---|---|
| "오늘 비 와?", "날씨 어때" | `get_current_weather` |
| "뭐 먹지?", "추천", "점심" | `get_lunch_recommendations` |
| "단백질 부족", "영양", "다이어트" | `get_nutrition_diagnosis` |
| "투표", "결과" | `get_vote_status` |
| (매칭 없음) | None (RAG로 폴백) |

```python
def guess_tool_from_query(query: str) -> dict | None:
    if any(kw in query for kw in ["날씨", "비", "더워"]):
        return {"name": "get_current_weather", "args": {}}
    if any(kw in query for kw in ["뭐 먹", "추천", "점심"]):
        return {"name": "get_lunch_recommendations", "args": {}}
    # ...
```

---

## 10. ToolCallingBot (`tool_bot.py`)

### 10.1 클래스 시그니처
```python
class ToolCallingBot:
    def __init__(
        self,
        user_id: int | str = 1,
        ollama_client=None,
        executor: ToolExecutor | None = None,
        max_iterations: int = 3,
        temperature: float = 0.2,
    )
    
    def chat(self, user_query: str) -> ToolChatResponse
```

### 10.2 시스템 프롬프트
```
당신은 Mini 점심 최적화 챗봇입니다. 사용자 질문에 답하기 위해
필요할 때 아래 도구를 호출하세요.

도구 호출 방식:
- 한 줄에 [TOOL: 도구이름(인자1=값1, 인자2=값2)] 형식
- 여러 도구 동시 호출 가능
- 결과 받은 후 최종 답변 작성

규칙:
- 쓰기 도구(cast_vote, record_meal)는 사용자가 명시적으로 요청할 때만
- 도구 호출 전에 왜 그 도구를 쓰는지 한 문장 설명
- 최종 답변은 자연스러운 한국어 대화체

사용 가능 도구:
{TOOL_LIST}
```

### 10.3 Multi-turn Loop
```
iteration 1:
  ollama.chat([system, user]) → response1
  parse_tool_calls(response1) → [tools]
  if tools:
      execute_each → results1
      messages.extend([assistant: response1, tool: results1])
  else:
      return response1

iteration 2:
  ollama.chat(messages + ...)
  ...

repeat until: tools.empty() OR iterations >= max_iterations
```

### 10.4 ToolChatResponse 구조
```python
@dataclass
class ToolChatResponse:
    response: str                       # 최종 답변
    tool_calls: list[dict]              # 누적 호출 내역
    tool_results: list[dict]            # HTTP 응답 결과
    iterations: int                     # 실행 라운드 수
    latency_ms: int
    fallback_used: bool                 # heuristic router 사용 여부
```

### 10.5 Fallback 발동 시나리오
- iteration 1에 LLM이 도구 호출 없이 일반 텍스트만 emit
- 텍스트에 추천/날씨/영양 키워드 포함 → heuristic router 작동 → tool 1개 강제 호출 → iteration 2

---

## 11. 테스트 (`tools/tests/test_tools.py`, 23개)

### 11.1 카테고리별 분포
| 카테고리 | 개수 | 검증 항목 |
|---|---|---|
| **definitions** | 4 | 도구 8개 정의됨, 스키마 유효, 이름 lookup |
| **fallback parser** | 8 | 단순/kwargs/multiple/bare/empty/error |
| **strip_tool_calls** | 2 | JSON 블록 제거, 도구 블록 제거 |
| **router** | 3 | 날씨/영양/기본 추천 의도 |
| **executor** | 6 | HTTP dispatch, 에러 핸들, 의존성 주입 |
| **integration** | 0 | (live lunch-api 필요, 별도 폴더) |

### 11.2 실행
```bash
pytest NLP/nlp_mvp/rag_chatbot/tools/tests/ -v
# ============== 23 passed ==============
```

### 11.3 통합 테스트 (선택)
```bash
# Mini 스택 기동 후
docker compose up -d
pytest NLP/nlp_mvp/rag_chatbot/tools/tests/test_integration.py
```

---

## 12. dashboard-web 통합

### 12.1 Concierge 페이지 모드 토글
```typescript
// /concierge — RAG ↔ Tools 토글
const [mode, setMode] = useState<"rag" | "tools">("rag")

const send = async (query: string) => {
  if (mode === "rag") {
    apiStreamSSENLP("/nlp/chatbot/chat/stream", { user_id, query }, callbacks)
  } else {
    const res = await apiFetchNLP<ToolChatOut>("/nlp/chatbot/chat/tools", {
      method: "POST",
      body: JSON.stringify({ user_id, query, temperature: 0.2, max_iterations: 3 })
    })
    appendMessage({ role: "assistant", text: res.response, toolCalls: res.tool_calls, toolResults: res.tool_results })
  }
}
```

### 12.2 UI 차이
| | RAG | Tools |
|---|---|---|
| 스트리밍 | ✅ token-by-token | ❌ 일괄 |
| 추천 카드 | ✅ recommendations[] | ❌ |
| 도구 실행 표시 | ❌ | ✅ tool_calls + tool_results |
| 환각 경고 | ✅ validation 기반 | (도구 결과는 사실) |

---

## 13. 구현 과정 (Phase 7 타임라인)

1. **8개 도구 정의** — JSON Schema, lunch-api 매핑 검증
2. **ToolExecutor HTTP 래퍼** — 의존성 주입 가능 구조 (테스트 격리)
3. **Fallback parser** — Ollama가 native tool-use 미지원 모델일 때 대비
4. **Heuristic router** — fallback의 fallback (안전망)
5. **ToolCallingBot 멀티턴 loop** — max_iterations 제약
6. **23개 unit test 통과** — 핵심 경로 보호
7. **dashboard-web Concierge 연동** — 모드 토글 UI

---

## 14. 운영 / 배포

### 14.1 환경 변수
```bash
LUNCH_API_BASE=http://localhost:8000/api    # ToolExecutor base URL
OLLAMA_MODEL_TOOLS=qwen3.5:9b               # 도구 호출 전용 모델 (선택)
TOOL_MAX_ITERATIONS=3                        # 안전 한도
TOOL_DEFAULT_TEAM_ID=team1
TOOL_DEFAULT_USER_ID=user1
```

### 14.2 추천 모델
| 모델 | 도구 호출 품질 | 속도 |
|---|---|---|
| `qwen3.5:9b` | ★★★★ | 보통 |
| `qwen2.5:7b` | ★★★ | 빠름 |
| `llama3.1:8b` | ★★★ | 빠름 |

### 14.3 헬스 모니터링
- `GET /nlp/chatbot/stats` — `tool_calls_count`, `fallback_count`, `avg_latency_ms`
- 도구 호출 실패율 > 10% 시 alarm

---

## 15. 보안 고려

### 15.1 쓰기 도구 가드
1. 시스템 프롬프트 명시 ("명시적 요청 시만")
2. `record_meal` / `cast_vote`는 user_id가 인증된 사용자와 일치해야 함 (lunch-api 측 검증)
3. 향후 OAuth 연동 시 token scope로 read/write 분리

### 15.2 Prompt Injection 대비
- 사용자 입력은 system prompt와 분리된 `user` role로만 주입
- 도구 결과는 `tool` role로 격리
- LLM이 자체 system prompt를 변경하려는 시도는 무시 (기본 ollama 동작)

### 15.3 Rate Limit
- `/nlp/chatbot/chat/tools` 10/min per user_id (slowapi)
- iteration 폭주 방지: max_iterations 3 hard cap

---

## 16. 향후 로드맵

### 16.1 Phase 6 (Research) → Phase 8 (Production)
1. **1,000+ 라벨 확보** (Label Studio + LLM 보조)
2. **A2 ABSA 미세조정** → 음식점 6축 점수 (taste/price/service/hygiene/ambience + 종합)
3. **B2 NER → 알레르기 자동 필터** 통합
4. **E1 임베딩 CF → /nlp/v2/recommendations** 활성화
5. **벤치마크 자동화** — GitHub Actions로 F1/Recall@K 추적

### 16.2 Phase 7 확장
1. **추가 도구**: `get_team_chat`, `set_user_preference`, `recommend_buddy_post`
2. **OpenAI native tool-use 호환**: `tool_choice: "auto"`
3. **도구 결과 캐싱**: 동일 인자 반복 호출 시 30s TTL
4. **다중 에이전트**: 추천 봇 + 영양사 봇 + 스케줄러 봇 협업

---

> *Phase 5 RAG 챗봇 + 환각 방지 전략은 「05. NLP MVP」를, lunch-api 엔드포인트 시그니처는 「04. API 명세」를 참고.*
