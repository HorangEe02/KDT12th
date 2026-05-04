# 05. NLP MVP 모듈 명세 (Phase 5)

## 0. 개요

`NLP/nlp_mvp/`는 Mini의 **자연어 처리 메인 레이어**로, 4개의 모듈이 단일 FastAPI 서비스(`mini-nlp-api`, port 8001)에 통합되어 있습니다. 모든 모듈은 공유 인프라(`shared/db.py`, `shared/ollama_client.py`, `shared/logger.py`)를 통해 SQLite DB와 Ollama LLM에 접근합니다.

### 0.1 모듈 매트릭스
| ID | 이름 | 역할 | 파일 위치 | 주요 모델 |
|---|---|---|---|---|
| **A1** | Sentiment | 리뷰 감성 분석 | `sentiment/` | KcELECTRA Zero-shot |
| **B1** | Menu Normalizer | 메뉴명 정규화 | `menu_normalizer/` | 규칙 + Levenshtein + Sentence-BERT |
| **D3** | RAG Chatbot | 영양 상담 챗봇 | `rag_chatbot/` | ChromaDB + Ollama qwen2.5:7b |
| **D5** | NLG Reports | 주간 리포트 생성 | `nlg_report/` | LLM + 템플릿 폴백 |

### 0.2 기술 스택
| 라이브러리 | 버전 | 용도 |
|---|---|---|
| transformers | 4.44.0 | HF 모델 로딩 |
| torch | * | NN 백엔드 |
| sentence-transformers | 3.0.1 | 임베딩 |
| chromadb | 0.5.0 | 벡터 DB |
| ollama | 0.3.0 | Ollama Python SDK |
| fastapi | 0.112.0 | 서버 |
| sqlalchemy | 2.0.32 | ORM |
| python-Levenshtein | 0.25.1 | 편집거리 |
| slowapi | 0.1.9 | Rate limit |

---

## 1. A1 — Sentiment 감성 분석

### 1.1 목적
음식점 리뷰 텍스트를 Zero-shot KcELECTRA로 분류하여 음식점 단위 감성 점수를 산출하고 `restaurants` 테이블에 영속화한다.

### 1.2 핵심 파일
| 파일 | 설명 | 라인 |
|---|---|---|
| `sentiment/sentiment_pipeline.py` | `SentimentAnalyzer` 클래스 | 219 |
| `sentiment/update_db.py` | DB 통합 + CLI | 318 |
| `sentiment/crawler.py` | 리뷰 소스 (Synthetic / AIHub / Kakao) | - |
| `sentiment/preprocess.py` | 텍스트 전처리 | - |

### 1.3 모델 설정
```python
DEFAULT_MODEL = "nlp04/korean_sentiment_analysis_kcelectra"
FALLBACK_MODEL = "beomi/KcELECTRA-base-v2022"

# 디바이스 자동 선택 + 배치 사이즈
device = "cuda" if torch.cuda.is_available() else "cpu"
batch_size = 32 if device == "cuda" else 8

# 토크나이저
max_length = 256
padding = True
truncation = True
```

### 1.4 라벨 매핑 (Zero-shot 호환)
```python
LABEL_ALIASES = {
    "positive": {"긍정", "positive", "POS", "LABEL_2"},
    "neutral":  {"중립", "neutral", "LABEL_1"},
    "negative": {"부정", "negative", "NEG", "LABEL_0"},
}
```

### 1.5 점수 계산 (집계)
```python
score = (pos_count - neg_count) / total  # ∈ [-1, +1]
pos_ratio = pos_count / total
neg_ratio = neg_count / total
neu_ratio = neutral_count / total

# Cold-start 방어
if total < min_sample (default 5):
    return { score: None, reason: "insufficient_samples" }
```

### 1.6 DB 스키마 확장 (`ensure_schema()`)
**`restaurants` 테이블에 5개 컬럼 추가**:
```sql
ALTER TABLE restaurants ADD COLUMN sentiment_score REAL;
ALTER TABLE restaurants ADD COLUMN sentiment_pos_ratio REAL;
ALTER TABLE restaurants ADD COLUMN sentiment_neg_ratio REAL;
ALTER TABLE restaurants ADD COLUMN sentiment_sample_size INTEGER;
ALTER TABLE restaurants ADD COLUMN sentiment_updated_at DATETIME;
```

**`reviews` 테이블 신규 생성**:
```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id TEXT NOT NULL,
    source TEXT NOT NULL,                -- synthetic | aihub | kakao_public
    text TEXT NOT NULL,
    sentiment_label TEXT,                -- positive | negative | neutral
    sentiment_confidence REAL,
    external_id TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_reviews_restaurant ON reviews(restaurant_id);
CREATE INDEX idx_reviews_source ON reviews(source);
```

### 1.7 CLI 사용
```bash
python -m nlp_mvp.sentiment.update_db \
    --limit 100 \
    --min-reviews 5 \
    --source synthetic \
    --refresh-after-days 7 \
    --skip-model        # 캐시된 라벨만 집계
```

### 1.8 실행 흐름
```
[Crawler] → fetch reviews (synthetic/aihub/kakao)
     ↓
[Preprocessor] → unicode 정규화, 소문자, 구두점
     ↓
[SentimentAnalyzer] → KcELECTRA batch 분류
     ↓
[Aggregator] → 음식점 단위 (pos-neg)/total
     ↓
[DB UPSERT] → restaurants.sentiment_*
```

### 1.9 공개 엔드포인트
| Method | Path |
|---|---|
| GET | `/nlp/sentiment/top?limit=10` |
| GET | `/nlp/sentiment/{restaurant_id}` |
| POST | `/nlp/sentiment/refresh` |

### 1.10 테스트
- `test_sentiment_pipeline.py` — 모델 로딩, 배치 추론
- `test_update_db.py` — 스키마 마이그레이션, UPSERT
- `test_crawler.py` — 소스별 통합
- `test_preprocess.py` — 텍스트 정규화

---

## 2. B1 — Menu Normalizer 메뉴 정규화

### 2.1 목적
사용자가 입력한 raw 메뉴명("김찌", "자장면" 등)을 표준 메뉴 ID로 매핑하여, 영양 DB(`nutrition_info`)와의 join hit rate를 40%→85%로 향상.

### 2.2 핵심 파일
| 파일 | 설명 |
|---|---|
| `menu_normalizer/normalizer.py` | `MenuNormalizer` 메인 (348 라인) |
| `menu_normalizer/rules.py` | 전처리 + synonym 확장 |
| `menu_normalizer/levenshtein.py` | 편집거리 매칭 |
| `menu_normalizer/embedding_matcher.py` | Sentence-BERT 임베딩 매칭 |
| `menu_normalizer/loader.py` | StandardMenuLoader (Synthetic / NutritionDB) |
| `menu_normalizer/synonym_dict.json` | 165+ 동의어 사전 |
| `menu_normalizer/evaluate.py` | Gold-set 평가 |

### 2.3 3단계 캐스케이드 파이프라인

```
Stage 1 (Rule + Synonym)
  raw → preprocess → apply_synonyms → exact match?
                                      ✓ → return (confidence=1.0, method="rule")
                                      ✗ ↓
Stage 2 (Levenshtein)
  cleaned → find_candidates(adaptive cutoff) → best?
                                                ✓ → return (method="levenshtein", confidence=sim)
                                                ✗ ↓
Stage 3 (Embedding, optional)
  cleaned → SBert match (threshold 0.85) → best?
                                            ✓ → return (method="embedding")
                                            ✗ ↓
Fallback: { method: "none", confidence: 0.0 }
```

### 2.4 NormalizationResult
```python
@dataclass
class NormalizationResult:
    raw: str                      # 원본 입력
    cleaned: str                  # 전처리 + 동의어 치환 후
    matched_id: str | None        # 표준 메뉴 ID
    matched_name: str | None      # 표준 메뉴명
    confidence: float             # [0.0, 1.0]
    method: Literal["rule", "levenshtein", "embedding", "none", "error"]
```

### 2.5 synonym_dict.json 구조 (210+ 항목)
```json
{
  "_meta": {
    "version": "0.2.0",
    "by_category": {
      "한식_찌개국": 35,
      "중식": 18,
      "일식": 24,
      "양식": 30,
      "분식": 14,
      "동남아_기타": 12
    }
  },
  "synonyms": {
    "김찌": "김치찌개",
    "자장면": "짜장면",
    "돈가스": "돈까스",
    "쌀국수": "쌀국수",
    ...
  }
}
```

### 2.6 임베딩 캐시
- 모델: `jhgan/ko-sroberta-multitask` (default)
- 표준 메뉴 임베딩 사전 계산 → `.cache/{model_name}_{count}_{hash}.pkl`
- 모델 변경 또는 메뉴 추가 시 자동 invalidate

### 2.7 정규화 결과 영속화 (`menu_normalization` 테이블)
```sql
CREATE TABLE menu_normalization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name TEXT NOT NULL,
    normalized_id TEXT,
    normalized_name TEXT,
    confidence REAL,
    method TEXT,
    source_table TEXT,        -- 'meal_history' | 'nutrition_info' 등
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_norm_raw ON menu_normalization(raw_name);
```

### 2.8 공개 엔드포인트
| Method | Path |
|---|---|
| POST | `/nlp/menu/normalize` |
| GET | `/nlp/menu/stats` |

### 2.9 평가 (`evaluate.py`)
```bash
python -m nlp_mvp.menu_normalizer.evaluate \
    --gold gold_set.jsonl \
    --output report.json
```
- Precision / Recall / F1
- method별 hit rate 집계

---

## 3. D3 — RAG Chatbot 영양 상담

### 3.1 목적
사용자의 식사 이력 + 음식점 메타 + 영양 DB를 ChromaDB로 색인하여, Ollama qwen2.5:7b이 컨텍스트 기반 영양 코칭을 제공한다. 환각(hallucination) 최소화 + SSE 토큰 스트리밍.

### 3.2 핵심 파일
| 파일 | 설명 | 라인 |
|---|---|---|
| `rag_chatbot/chatbot.py` | `LunchCoachBot` 메인 | 204 |
| `rag_chatbot/indexer.py` | ChromaDB 인덱서 | 296 |
| `rag_chatbot/retriever.py` | 3-collection 시멘틱 검색 | 116 |
| `rag_chatbot/prompt_templates.py` | 시스템 프롬프트 + 가이드 | 88 |
| `rag_chatbot/history.py` | 대화 메모리 (max 5 turn) | - |
| `rag_chatbot/tool_bot.py` | Phase 7 Tool Calling | 205 |

### 3.3 ChromaDB 컬렉션
| 컬렉션 | 포맷 | 용도 |
|---|---|---|
| `meal_history` | "YYYY-MM-DD: menu (cal, protein, satisfaction)" | 사용자 식사 이력 |
| `nutrition_info` | "food_name (cal, protein, carbs, fat, sodium)" | 영양 DB |
| `restaurants` | "name (category, distance, rating, sentiment, menu_type)" | 음식점 메타 |

저장 경로: `./chroma_store/` (env `CHROMA_DB_PATH`)
임베딩: `jhgan/ko-sroberta-multitask`

### 3.4 시스템 프롬프트 (발췌)
```
당신은 "런치 코치"라는 이름의 친근한 영양사 AI 입니다.

행동 원칙:
1. 제공된 사용자 식사 이력과 영양 데이터만을 근거로 답변합니다.
2. 의학적 진단은 하지 않으며, 필요 시 전문의 상담을 권유합니다.
3. 응답은 3~5문장, 이모지 2~3개 사용, 친근하고 긍정적으로.
4. 마지막에 1~2개의 메뉴/음식점을 추천합니다.

환각 방지 규칙:
- 컨텍스트에 없는 음식점/메뉴는 언급하지 않습니다.
- 정보가 부족하면 "데이터가 충분하지 않습니다"로 답변합니다.

출력 형식:
자연스러운 답변 + 마지막에 JSON 블록:
{"recommendations": [{"restaurant": "...", "menu": "...", "reason": "..."}]}
```

### 3.5 Chat 흐름
```python
def chat(user_query: str) -> ChatResponse:
    # 1. 컨텍스트 검색 (병렬)
    context = retriever.retrieve(
        query=user_query,
        user_id=self.user_id,
        top_k_meal=5, top_k_nutrition=5, top_k_restaurant=5
    )
    
    # 2. 프롬프트 빌드
    messages = build_prompt(user_query, context, self.history)
    
    # 3. LLM 호출
    response = ollama.chat(
        messages, temperature=0.3,
        num_predict=512, num_ctx=2048
    )
    
    # 4. 추천 추출 + 환각 검증
    recommendations = extract_recommendations(response)
    validation = validate_response(response, context)
    
    # 5. 히스토리 갱신
    self.history.add_user(user_query)
    self.history.add_assistant(response)
    
    return ChatResponse(
        response=response,
        recommendations=recommendations,
        context_used=context,
        latency_ms=...,
        validation=validation
    )
```

### 3.6 환각 검증
```python
def validate_response(response, context) -> dict:
    mentioned_restaurants = extract_restaurant_mentions(response)
    context_restaurants = {r["name"] for r in context["restaurants"]}
    
    return {
        "valid": all(m in context_restaurants for m in mentioned_restaurants),
        "mentioned_count": len(mentioned_restaurants),
        "issues": [m for m in mentioned_restaurants if m not in context_restaurants]
    }
```

UI는 `validation.mentioned_count == 0 && recommendations.length > 0` 시 경고 배너 표시.

### 3.7 SSE 스트리밍 모드
```python
@router.post("/nlp/chatbot/chat/stream")
async def chat_stream(req: ChatIn):
    async def event_generator():
        yield f"data: {json.dumps({'type': 'meta', 'context_summary': ...})}\n\n"
        for token in ollama.stream(messages, ...):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        yield f"data: {json.dumps({'type': 'final', 'recommendations': ..., 'validation': ...})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 3.8 공개 엔드포인트
| Method | Path | Rate |
|---|---|---|
| POST | `/nlp/chatbot/chat` | 10/min |
| POST | `/nlp/chatbot/chat/stream` | 10/min |
| POST | `/nlp/chatbot/chat/tools` | 10/min |
| POST | `/nlp/chatbot/reset` | — |
| GET | `/nlp/chatbot/stats` | — |

### 3.9 테스트 (4 모듈)
- `test_chatbot.py` (190 라인) — chat 흐름, 히스토리, 검증
- `test_indexer.py` (95) — 컬렉션 구축
- `test_retriever.py` (39) — 3-컬렉션 검색
- `test_prompt_templates.py` (90) — 컨텍스트 포맷팅

---

## 4. D5 — NLG Reports 주간 리포트

### 4.1 목적
사용자별 주간 영양 데이터(meal_history 집계)를 LLM이 자연어로 생성. LLM 실패 시 템플릿, 그것도 실패 시 minimal 메시지로 graceful degrade.

### 4.2 핵심 파일
| 파일 | 설명 |
|---|---|
| `nlg_report/generator.py` | `ReportGenerator` (150+ 라인) |
| `nlg_report/fact_extractor.py` | 주간 사실 집계 |
| `nlg_report/prompt.py` | LLM 프롬프트 빌더 |

### 4.3 DB 스키마 (`nutrition_reports`)
```sql
CREATE TABLE nutrition_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    week_start DATE NOT NULL,
    facts JSON NOT NULL,
    nlg_text TEXT NOT NULL,
    generation_method TEXT NOT NULL,    -- llm | template | minimal
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, week_start)
);
CREATE INDEX idx_reports_user ON nutrition_reports(user_id);
```

### 4.4 WeeklyFacts (집계 사실)
```python
@dataclass
class WeeklyFacts:
    user_id: int
    week_start: date
    meal_count: int
    avg_calories: float
    avg_protein: float
    avg_carbs: float
    avg_fat: float
    avg_sodium: float
    likely_lack: str | None     # "단백질" | "철분" | None
    favorite_categories: list[str]
```

### 4.5 LLM 프롬프트 패턴
```
다음은 사용자의 이번 주 식사 사실입니다 (JSON):
{facts}

규칙:
- 50~600자, 이모지 1~6개
- "병"·"진단"·"처방"·"의사"·"약" 사용 금지 (의료 관련)
- 부족한 영양소를 친근하게 권유
- 마지막에 다음 주 추천 1줄

예시:
"이번 주 평균 단백질 24g으로 살짝 부족했어요 🥚 ..."
```

### 4.6 품질 검증 (`validate_report`)
| 검사 항목 | 통과 기준 |
|---|---|
| length | 50~600자 |
| emoji_count | 1~6개 |
| forbidden_words | "병", "진단", "처방", "의사", "약" 부재 |

실패 시 `issues` 배열에 사유 누적, `generation_method = "template"`로 폴백.

### 4.7 폴백 체인
```
1. LLM 호출 → validate_report
   - PASS → save("llm")
2. 템플릿 렌더 (f-string)
   "이번 주는 {meal_count}회 식사하셨고, 평균 단백질 {avg_protein}g..."
   - PASS → save("template")
3. minimal_message
   "이번 주 식사 데이터가 충분하지 않습니다."
   → save("minimal")
```

### 4.8 공개 엔드포인트
| Method | Path |
|---|---|
| GET | `/nlp/reports/weekly/{user_id}` |
| POST | `/nlp/reports/weekly/{user_id}/regenerate` |

### 4.9 응답 스키마
```json
{
  "user_id": 1,
  "week_start": "2026-04-21",
  "week_label": "4월 4주차",
  "text": "이번 주 평균 단백질 24g으로 살짝 부족했어요 🥚 ...",
  "generation_method": "llm",
  "validation": {
    "valid": true,
    "length": 268,
    "emoji_count": 3,
    "issues": []
  }
}
```

---

## 5. 공유 인프라 (`nlp_mvp/shared/`)

### 5.1 `db.py` — SQLite 추상화
```python
@lru_cache
def get_engine(db_path: Optional[str] = None, echo: bool = False) -> Engine:
    """프로세스당 단일 엔진"""
    
@contextmanager
def get_session() -> Iterator[Session]:
    """세션 누수 방지 컨텍스트 매니저"""
    
def _resolve_db_url(db_path: Optional[str] = None) -> str:
    """우선순위: arg > MINI_DB_PATH > .env > default"""
```

기본 경로: `../lunch-optimizer/database/mini.db` (NLP/ 디렉터리 기준)

### 5.2 `ollama_client.py` — LLM 클라이언트
```python
class OllamaClient:
    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        timeout: Optional[float] = None,
        max_retries: int = 2,
    ) -> str: ...
    
    def stream(self, messages, ...) -> Iterator[str]: ...
```

| 환경 변수 | 기본값 |
|---|---|
| `OLLAMA_HOST` | http://localhost:11434 |
| `OLLAMA_MODEL` | qwen3.5:9b |
| `OLLAMA_MODEL_CHAT` | (override for /chatbot) |

**예외 계층**:
- `OllamaError` (base)
- `OllamaConnectionError` (서버 다운, 타임아웃)
- `OllamaModelNotFoundError` (모델 미pull)

### 5.3 `logger.py` — 구조화 로깅
싱글톤 `get_logger(name)` — Python `logging` 표준 + 파일 + 콘솔 핸들러.

---

## 6. API 진입점 (`nlp_mvp/api/main.py`)

### 6.1 Lifespan (Startup 순서)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _init_db()                  # 스키마 검증
    _init_menu_normalizer()     # 임베딩 캐시 로딩
    _init_nlg_generator()       # 리포트 테이블 생성
    _init_scoring_patch()       # (옵션) lunch-api 추천 monkey patch
    _init_rag_index()           # ChromaDB 인덱싱 (env로 스킵 가능)
    yield
    # Shutdown — 자원 정리
```

### 6.2 모듈 헬스 추적
```python
_MODULE_STATUS = {
    "db": "ok|error",
    "menu_normalizer": "ok|error",
    "rag_chatbot_index": "ok|error|skipped",
    "nlg_generator": "ok|error",
    "scoring_patch_ab": "ok|error|skipped",
    "research_v2": "ok|error|skipped",
}
```
`/nlp/health`가 이 맵을 반환.

### 6.3 미들웨어 스택
1. **Security headers** (X-Frame-Options 등)
2. **CORS** (allowlist)
3. **Rate limit** (slowapi, 미설치 시 noop)
4. **Request logging** (method, path, status, latency_ms)

### 6.4 라우터 분리
```python
app.include_router(sentiment_router,  prefix="/nlp/sentiment")
app.include_router(menu_router,       prefix="/nlp/menu")
app.include_router(chatbot_router,    prefix="/nlp/chatbot")
app.include_router(reports_router,    prefix="/nlp/reports")
app.include_router(settings_router,   prefix="/nlp/settings")
app.include_router(v2_router,         prefix="/nlp/v2")  # 옵션
```

---

## 7. 구현 과정 (시간순)

### 7.1 Phase 5 진행 단계
1. **Week 1**: 모듈 골격 + DB 통합 (`shared/db.py`)
2. **Week 2**: A1 sentiment + B1 normalizer 1차
3. **Week 3**: D3 RAG 챗봇 + 환각 방지 가드
4. **Week 4**: D5 NLG 리포트 + 전체 통합 + 테스트

### 7.2 핵심 의사결정
- **Streamlit 배제**: 초기 D3는 Streamlit UI 구현 → React Concierge로 단일화 (`ROLE_SEPARATION_DECISION.md` 2026-04-08)
- **Sentence-BERT 모델 선택**: `jhgan/ko-sroberta-multitask` 한국어 미세조정 모델 (속도/품질 트레이드오프)
- **ChromaDB 영속 모드**: 메모리 모드 → 파일 시스템 (재기동 후 인덱스 보존)
- **SSE 채택**: WebSocket 대신 단순 HTTP 기반 토큰 스트리밍 (CORS 단순)
- **Rate limit**: slowapi 의존성 — 부재 시 graceful no-op

---

## 8. 운영 / 배포

### 8.1 단일 컨테이너
```bash
uvicorn nlp_mvp.api.main:app --host 0.0.0.0 --port 8001
```

### 8.2 환경 변수 (요약)
```bash
MINI_DB_PATH=../lunch-optimizer/database/mini.db
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
NLP_API_PORT=8001
NLP_API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
NLP_SKIP_RAG_INDEX=0
SENTIMENT_MODEL=nlp04/korean_sentiment_analysis_kcelectra
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
CHROMA_DB_PATH=./chroma_store
```

### 8.3 워밍업 시간
- ChromaDB 인덱스 빌드: ~10–30초 (데이터량 의존)
- HF 모델 로드 (KcELECTRA + Sentence-BERT): ~5–15초
- Ollama 첫 응답: ~5–20초 (모델 메모리 적재)

### 8.4 모니터링
- `/nlp/health` 폴링 (대시보드 10초 주기)
- Ollama가 `/api/tags`로 활성 모델 확인
- ChromaDB는 자체 `peek()` API로 collection 상태 확인

---

## 9. 알려진 제약 / 확장 포인트

| 항목 | 현황 | 향후 |
|---|---|---|
| Sentiment 정확도 | Zero-shot ~70% | Phase 6 ABSA fine-tune (속성별) |
| Menu hit rate | ~85% (3-stage) | NER 통합으로 raw 추출 정확도↑ |
| RAG 검색 품질 | top_k=5 cosine | re-ranker 추가, BM25 hybrid |
| NLG 일관성 | 템플릿 fallback | RLHF 또는 fine-tuned 한국어 LLM |
| 다국어 | 한국어 전용 | en/ja 확장 시 모델 다중화 |

---

> *Phase 6 ABSA·NER·E1과 Phase 7 Tool Calling 상세는 「06. NLP Research + Tool Calling」 참고.*
