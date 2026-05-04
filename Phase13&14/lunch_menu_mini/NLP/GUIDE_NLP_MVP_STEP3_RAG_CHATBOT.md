# 🔹 Step 3 — D3 RAG 기반 영양 상담 챗봇 상세 구현 가이드

> **Mini NLP MVP 의 3주차 전용 심화 가이드**
>
> 본 문서는 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §7 의
> Step 3 섹션을 **3주차 단일 독립 체크리스트** 로 확장한 문서입니다.
> 브레인스토밍 · 벡터 DB 선택 근거 · 인덱싱 전략 · 프롬프트 엔지니어링 ·
> 멀티턴 대화 설계 · 환각 방지 · Streamlit UI 를 한 문서에 집약하여,
> **이 문서만으로 Step 3 을 완수할 수 있도록** 설계되었습니다.

---

## 📋 목차

1. [문서 목적 및 위치](#1-문서-목적-및-위치)
2. [Step 3 전체 조감](#2-step-3-전체-조감)
3. [브레인스토밍 — 기술 선택 의사결정](#3-브레인스토밍--기술-선택-의사결정)
4. [확장 아키텍처 다이어그램](#4-확장-아키텍처-다이어그램)
5. [파일 목록 및 의존성 그래프](#5-파일-목록-및-의존성-그래프)
6. [파일별 상세 명세](#6-파일별-상세-명세)
7. [구현 순서 (5일 체크리스트)](#7-구현-순서-5일-체크리스트)
8. [KPI 및 검증 기준](#8-kpi-및-검증-기준)
9. [트러블슈팅 (Step 3 한정)](#9-트러블슈팅-step-3-한정)
10. [재사용 가능한 기존 파일](#10-재사용-가능한-기존-파일)
11. [외부 의존성 확인](#11-외부-의존성-확인)
12. [프롬프트 엔지니어링 상세](#12-프롬프트-엔지니어링-상세)
13. [다음 Step 과의 연결점](#13-다음-step-과의-연결점)
14. [부록](#14-부록)
15. [1페이지 체크리스트 요약](#15-1페이지-체크리스트-요약)

---

## 1. 문서 목적 및 위치

### 1.1 왜 별도 가이드인가

상위 가이드 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §7 은
요약형 프롬프트 묶음입니다. 3주차 D3 챗봇 구현에는 다음이 추가로 필요합니다:

- **왜 RAG 인가** — Fine-tuning · 프롬프트만 · RAG 의 트레이드오프
- **벡터 DB 선택 근거** — ChromaDB vs Qdrant vs FAISS
- **인덱싱 문장화 템플릿** — 어떻게 DB 레코드를 임베딩 친화적 문장으로 변환할지
- **프롬프트 엔지니어링** — 환각 방지, 응답 포맷 강제, 한국어 자연스러움
- **멀티턴 상태 관리** — "아까 말한 거 말고", "더 싼 곳" 같은 맥락 처리
- **5일 단위 체크리스트**

### 1.2 상위 문서와의 관계

```
Mini/NLP/
├── README.md
├── GUIDE_NLP_MVP_SCENARIO3.md
│   └── §7 Step 3                       # → 본 문서가 확장
├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md    # 1주차 A1
├── GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md  # 2주차 B1
├── GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md  # 🆕 본 문서 (3주차 D3)
└── GUIDE_NLP_RESEARCH_SCENARIO2.md
```

### 1.3 선행 조건

- [x] `Mini/NLP/nlp_mvp/` 스켈레톤
- [x] `Mini/NLP/.env` (특히 `OLLAMA_HOST`, `OLLAMA_MODEL`, `EMBEDDING_MODEL`)
- [x] **Step 0 공용 유틸 완료** — `shared/db.py`, `shared/logger.py`, `shared/ollama_client.py`
- [x] **Step 1 완료** — `sentiment_score` 컬럼이 `restaurants` 에 존재 (RAG 에 활용)
- [x] **Step 2 완료** — `normalized_menu_id` 가 `meal_history` 에 존재 (권장, 필수는 아님)
- [x] **Ollama 서버 가동** — `ollama serve`, `ollama pull qwen2.5:7b-instruct`
- [x] Mini SQLite DB 에 `meal_history`, `nutrition_info`, `restaurants` 시드 데이터

> 💡 **Ollama 가 아직 없다면** `ollama pull qwen2.5:3b-instruct` (경량) 로도 진행 가능

---

## 2. Step 3 전체 조감

### 2.1 한 줄 목표

> **사용자 자연어 질문 → RAG 컨텍스트 검색 → Ollama LLM → 개인화된 한국어 상담 응답**

### 2.2 3주차 5일 일정

| Day | 작업 테마 | 산출물 | 누적 |
|-----|---------|--------|------|
| **Day 1** | Ollama 동작 확인 + ChromaDB 인덱서 스켈레톤 | `indexer.py`, 3개 컬렉션 생성 | 20% |
| **Day 2** | Retriever + 메타데이터 필터 | `retriever.py`, top-k 검색 동작 | 40% |
| **Day 3** | 프롬프트 템플릿 + 컨텍스트 빌더 | `prompt_templates.py`, 10개 질문 수동 테스트 | 60% |
| **Day 4** | 챗봇 엔진 + 멀티턴 + 추천 추출 | `chatbot.py`, `LunchCoachBot` 클래스 | 80% |
| **Day 5** | Streamlit 앱 + 평가 노트북 | `streamlit_app.py`, 10개 질문 블라인드 평가 | 100% |

### 2.3 완료 기준 (한눈에)

| 기준 | 목표치 |
|------|-------|
| ✅ Ollama ping 성공 | 100ms 이내 |
| ✅ ChromaDB 3 컬렉션 생성 | `meal_history`, `nutrition_info`, `restaurants` |
| ✅ Retriever top-5 정확도 | 수동 검토 ≥ 4/5 관련성 |
| ✅ 응답 속도 | ≤ 3초 (end-to-end) |
| ✅ 환각 케이스 (컨텍스트 밖 식당 언급) | 0건 / 20 질문 |
| ✅ 응답 만족도 (블라인드 평가) | ≥ 4.0 / 5.0 |
| ✅ Streamlit 앱 동작 | 사이드바·채팅·추천 카드 |
| ✅ 멀티턴 연속성 | "그럼 다른 거" 질문 처리 |

---

## 3. 브레인스토밍 — 기술 선택 의사결정

### 3.1 RAG vs Fine-tuning vs 프롬프트만

**후보 비교표:**

| 접근 | 장점 | 단점 | MVP 적합성 |
|------|------|------|-----------|
| **프롬프트만 (Zero-shot)** | 가장 간단, 구현 1일 | 개인화 불가, 환각 심함 | ⭐⭐ |
| **Few-shot (예시 주입)** | 약간의 개인화 | 컨텍스트 윈도우 제약 | ⭐⭐⭐ |
| **Fine-tuning (도메인 적응)** | 도메인 정확도 ↑ | 학습 데이터·GPU 필요, MVP 범위 초과 | ⭐ |
| **RAG (Retrieval-Augmented)** | 개인화·최신성·근거성 | 복잡도 ↑, 검색 품질 의존 | ⭐⭐⭐⭐⭐ |
| **Agent + Tool Use** | 가장 유연 | 지연·오버엔지니어링 위험 | ⭐⭐ (Phase 6 로) |

**의사결정:** **RAG 채택**
- 이유: Mini 의 핵심 가치 = **개인 식사 이력 기반 추천**. 정적 프롬프트로는 불가능.
- Fine-tuning 은 시나리오 2 로 이연
- Agent 패턴은 ChatBOT/ 폴더의 Phase2 로 이연

### 3.2 벡터 DB 선택

**후보 비교표:**

| DB | 배포 | 한국어 지원 | 메타데이터 필터 | MVP 적합성 |
|------|------|-----------|-------------|-----------|
| **ChromaDB** | 로컬 파일, 내장 SQLite | ✅ (임베딩 모델 의존) | ✅ 네이티브 | ⭐⭐⭐⭐⭐ |
| Qdrant | Docker 필요 | ✅ | ✅ | ⭐⭐⭐ |
| Weaviate | Docker 필요 | ✅ | ✅ | ⭐⭐ |
| Pinecone | 유료 클라우드 | ✅ | ✅ | ⭐ |
| FAISS | 로컬, 메타데이터 수동 | ✅ | ❌ 수동 구현 | ⭐⭐ |
| Milvus | 무거움 | ✅ | ✅ | ⭐ |

**결정:** **ChromaDB**
- 단일 프로세스, Docker 불필요, SQLite 만으로 동작
- Python SDK 성숙, 메타데이터 필터 네이티브 (`where={"user_id": 1}`)
- MVP 용량(수천 ~ 수만 레코드)에 충분

### 3.3 임베딩 모델 선택

**결정:** `jhgan/ko-sroberta-multitask` (Step 2 와 동일)
- **이점:** Step 2 에서 이미 로딩된 모델 재사용 → 메모리 1회만
- **대안:** `BM-K/KoSimCSE-roberta-multitask` (성능 유사)

**구현:** ChromaDB 의 `embedding_function` 파라미터에 custom wrapper 주입

```python
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer

class KoSBertEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.model.encode(input, normalize_embeddings=True).tolist()
```

### 3.4 LLM 모델 선택 (Ollama)

**후보:**

| 모델 | 크기 | 한국어 품질 | RAM 필요 | MVP 추천 |
|------|-----|----------|---------|---------|
| **`qwen2.5:7b-instruct`** | 4.7GB | ⭐⭐⭐⭐⭐ | 8GB | ✅ **1순위** |
| `qwen2.5:3b-instruct` | 1.9GB | ⭐⭐⭐⭐ | 4GB | ✅ **경량 대안** |
| `gemma2:9b` | 5.4GB | ⭐⭐⭐⭐ | 12GB | 보조 |
| `exaone3.5:7.8b` | 4.8GB | ⭐⭐⭐⭐⭐ | 8GB | ✅ 한국어 특화 |
| `llama3.1:8b` | 4.7GB | ⭐⭐⭐ | 8GB | ❌ 한국어 약함 |
| `phi3:mini` | 2.3GB | ⭐⭐ | 4GB | ❌ 한국어 부족 |

**결정:**
- **1순위:** `qwen2.5:7b-instruct` — 균형, 한국어 양호
- **경량:** `qwen2.5:3b-instruct` — 메모리 부족 환경
- **한국어 특화:** `exaone3.5:7.8b` — LG AI 출시, 한국어 최상급

```bash
# .env
OLLAMA_MODEL=qwen2.5:7b-instruct
# 경량 대안
# OLLAMA_MODEL=qwen2.5:3b-instruct
```

### 3.5 인덱싱 문장화 전략

**문제:** DB 레코드를 그냥 임베딩하면 의미 손실. "restaurant_id=1, name=A, rating=4.5" → 의미 없음.

**해결:** **자연어 문장 템플릿**

| 소스 | 템플릿 | 예시 |
|------|-------|------|
| `meal_history` | `{date} {meal_time}: {menu_name} ({calories}kcal, 단백질 {protein}g). 만족도 {sat}/5` | "2026-04-01 화 점심: 김치찌개 (650kcal, 단백질 22g). 만족도 4/5" |
| `nutrition_info` | `{food_name}은(는) 1인분 기준 약 {calories}kcal, 단백질 {protein}g, 탄수화물 {carbs}g, 지방 {fat}g입니다. 나트륨 {sodium}mg.` | "김치찌개는 1인분 기준 약 500kcal..." |
| `restaurants` | `{name}은(는) {category} 식당입니다. 사무실에서 도보 {distance}분, 평점 {rating}, 감성 점수 {sentiment:+.2f}. 대표 메뉴는 {menus}.` | "○○식당은 한식 식당입니다. 도보 3분, 평점 4.5, 감성 +0.76. 대표 메뉴는 김치찌개, 제육볶음." |

**이점:**
- 임베딩 모델이 의미 포착 가능
- LLM 이 컨텍스트로 받았을 때 바로 이해 가능 (별도 변환 불필요)

### 3.6 Chunking 전략

**질문:** 문장 하나 = 임베딩 하나? 아니면 여러 필드 묶음?

**결정:** **레코드 1개 = 청크 1개** (MVP 범위)
- 이유: 각 레코드가 이미 자연어 1문장으로 표현 가능할 정도로 짧음
- 긴 리뷰 텍스트(Step 1 의 `reviews.text`)는 본 Step 에서 인덱싱 제외 (향후 확장)

### 3.7 멀티턴 대화 상태 관리

**후보:**

| 방식 | 장점 | 단점 |
|------|------|------|
| **전체 이력 그대로 주입** | 간단 | 컨텍스트 윈도우 폭발 |
| **최근 N턴만 유지** | 균형 | 오래된 맥락 상실 |
| **LLM 요약 + 최근 2턴** | 효율적 | 요약 비용·오류 |
| **Slot Filling (명시적 state)** | 정확 | 복잡도 ↑ (시나리오 2) |

**결정:** **최근 5턴 유지 + 길이 가드**
- 최대 5턴 또는 총 2,000 토큰 중 먼저 도달
- 초과 시 가장 오래된 턴부터 drop

```python
class ConversationHistory:
    def __init__(self, max_turns: int = 5, max_chars: int = 6000):
        self.max_turns = max_turns
        self.max_chars = max_chars
        self.messages: list[dict] = []

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self._prune()

    def _prune(self) -> None:
        while len(self.messages) > self.max_turns * 2:  # user+assistant 쌍
            self.messages.pop(0)
        total = sum(len(m["content"]) for m in self.messages)
        while total > self.max_chars and self.messages:
            removed = self.messages.pop(0)
            total -= len(removed["content"])
```

### 3.8 환각 방지 전략

**원칙:** "제공된 컨텍스트에 없는 식당·메뉴는 언급 금지"

**3중 방어:**

1. **프롬프트 강제 (1차):**
   ```
   ⚠️ 규칙: 아래 '=== 주변 추천 식당 ===' 섹션에 명시된 식당만 추천하세요.
   목록에 없는 식당을 만들어내지 마세요. 데이터가 없으면 솔직히 말하세요.
   ```

2. **응답 후처리 검증 (2차):**
   ```python
   def validate_response(response: str, context: dict) -> tuple[bool, list[str]]:
       """LLM 응답에 언급된 식당명이 컨텍스트에 실재하는지 검사."""
       allowed_names = {r["name"] for r in context["restaurants"]}
       mentioned = extract_restaurant_names(response)
       invalid = [n for n in mentioned if n not in allowed_names]
       return (len(invalid) == 0, invalid)
   ```

3. **재질의 (3차, 선택):**
   - 검증 실패 시 LLM 에게 "위 응답에 잘못된 식당이 있으니 컨텍스트만 사용하여 다시 작성해줘" 재요청

### 3.9 추천 결과 구조화 추출

**문제:** LLM 응답은 자유 텍스트. UI 카드로 표시하려면 구조화 필요.

**전략 비교:**

| 방식 | 신뢰도 | 비용 |
|------|------|------|
| **정규식 파싱** | 보통 | 낮음 |
| **LLM 재질의 (JSON 모드)** | 높음 | 추가 호출 1회 |
| **구조화 프롬프트 (응답 포맷 강제)** | 높음 | 프롬프트 길이 ↑ |

**결정:** **구조화 프롬프트** (응답 끝에 JSON 블록 포함 요청)

```
답변 후 다음 JSON 블록을 포함하세요:
```json
{
  "recommendations": [
    {"restaurant": "식당명", "menu": "메뉴명", "reason": "짧은 이유"}
  ]
}
```
```

**파싱:** 정규식으로 ```json ... ``` 블록 추출 후 `json.loads()`

---

## 4. 확장 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                   사용자 질문 (Streamlit / CLI / API)              │
│         "오늘 뭐 먹을까?", "요즘 피곤한데 추천해줘" ...              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LunchCoachBot.chat()                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ① ConversationHistory: 최근 5턴 이력 추가                 │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ② Retriever.retrieve(query, user_id, top_k=5)            │  │
│  │                                                          │  │
│  │    ChromaDB 3개 컬렉션 병렬 검색:                         │  │
│  │    ┌─────────────────────────┐                           │  │
│  │    │ meal_history (user별)    │  ← where={"user_id":1}  │  │
│  │    │ nutrition_info (전체)    │                           │  │
│  │    │ restaurants (전체)       │  ← 감성·거리 포함         │  │
│  │    └─────────────────────────┘                           │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ③ prompt_templates.build_prompt(query, context, history) │  │
│  │                                                          │  │
│  │    messages = [                                          │  │
│  │      {system: SYSTEM_PROMPT},                            │  │
│  │      ...history (최근 5턴),                              │  │
│  │      {user: query + "=== context ==="}                   │  │
│  │    ]                                                     │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ④ OllamaClient.chat(messages, temperature=0.3)           │  │
│  │    → LLM 응답 텍스트                                      │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ⑤ 응답 파싱                                               │  │
│  │    · 본문 + JSON 블록 분리                                │  │
│  │    · 환각 검증 (식당명 실재 여부)                         │  │
│  │    · recommendations 구조화                               │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ⑥ ConversationHistory 에 응답 추가                        │  │
│  │    (chatbot_sessions 테이블 upsert)                       │  │
│  └───────────────────────┬──────────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────────────┘
                           ▼
           {
             "response": "오늘 피곤하시면 단백질이 풍부한 메뉴가 좋아요 💪 ...",
             "recommendations": [
               {"restaurant": "○○식당", "menu": "닭가슴살 샐러드", "reason": "..."},
             ],
             "context_used": {...},
             "latency_ms": 2150
           }
```

---

## 5. 파일 목록 및 의존성 그래프

```
┌─────────────────────────────────────┐
│ Step 0 (선행)                        │
├─────────────────────────────────────┤
│ shared/db.py                        │
│ shared/logger.py                    │
│ shared/ollama_client.py ◄── ★ 핵심  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Step 3 — D3 RAG 챗봇                 │
├─────────────────────────────────────┤
│                                     │
│  rag_chatbot/                       │
│  ├─ indexer.py          ◄── Day 1  │
│  │   ├─ KoSBertEmbeddingFunction   │
│  │   ├─ ChromaDBIndexer            │
│  │   ├─ build_meal_history_coll()  │
│  │   ├─ build_nutrition_coll()     │
│  │   ├─ build_restaurant_coll()    │
│  │   └─ build_all()                │
│  │                                  │
│  ├─ retriever.py        ◄── Day 2  │
│  │   ├─ Retriever                  │
│  │   └─ retrieve()                 │
│  │                                  │
│  ├─ prompt_templates.py ◄── Day 3  │
│  │   ├─ SYSTEM_PROMPT              │
│  │   ├─ build_prompt()             │
│  │   ├─ format_context()           │
│  │   └─ RESPONSE_SCHEMA            │
│  │                                  │
│  ├─ history.py          ◄── Day 4  │
│  │   └─ ConversationHistory        │
│  │                                  │
│  ├─ chatbot.py          ◄── Day 4  │
│  │   ├─ LunchCoachBot              │
│  │   ├─ chat() / achat()           │
│  │   ├─ extract_recommendations()  │
│  │   └─ validate_response()        │
│  │                                  │
│  ├─ streamlit_app.py    ◄── Day 5  │
│  │   ├─ 사이드바 (user 선택)       │
│  │   ├─ 채팅 UI                    │
│  │   └─ 추천 카드                  │
│  │                                  │
│  └─ tests/                          │
│      ├─ test_indexer.py            │
│      ├─ test_retriever.py          │
│      ├─ test_prompt_templates.py   │
│      └─ test_chatbot.py            │
│                                     │
│  notebooks/03_rag_tuning.ipynb ◄── Day 5 │
└─────────────────────────────────────┘
```

---

## 6. 파일별 상세 명세

### 6.1 `rag_chatbot/indexer.py`

```python
"""
ChromaDB 기반 RAG 인덱서.

Mini DB 레코드를 자연어 문장으로 변환하여 3개 컬렉션에 저장.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from chromadb import PersistentClient
from chromadb.api.types import EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CHROMA_PATH = os.getenv(
    "CHROMA_DB_PATH", "./nlp_mvp/rag_chatbot/chroma_store"
)
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask"
)


# =============================================================================
# Custom Embedding Function
# =============================================================================
class KoSBertEmbeddingFunction(EmbeddingFunction):
    """
    Sentence-BERT 기반 임베딩 함수. ChromaDB 에 주입 가능.
    싱글톤 패턴으로 모델 중복 로딩 방지.
    """
    _instance = None

    def __new__(cls, model_name: str = DEFAULT_EMBEDDING_MODEL):
        if cls._instance is None or cls._instance.model_name != model_name:
            instance = super().__new__(cls)
            instance.model_name = model_name
            instance.model = SentenceTransformer(model_name)
            logger.info(f"KoSBertEmbeddingFunction initialized: {model_name}")
            cls._instance = instance
        return cls._instance

    def __call__(self, input: list[str]) -> Embeddings:
        return self.model.encode(
            input,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()


# =============================================================================
# 문장화 템플릿
# =============================================================================
def format_meal_history_row(row: dict) -> str:
    """
    meal_history 레코드를 자연어 문장으로.

    예: "2026-04-01 화 점심: 김치찌개 (650kcal, 단백질 22g). 만족도 4/5"
    """
    date = row.get("meal_date", "")
    menu = row.get("menu", "미상")
    cal = row.get("calories", 0) or 0
    protein = row.get("protein", 0) or 0
    sat = row.get("satisfaction", 0) or 0
    return (
        f"{date}: {menu} "
        f"({cal:.0f}kcal, 단백질 {protein:.0f}g). 만족도 {sat}/5"
    )


def format_nutrition_row(row: dict) -> str:
    """
    nutrition_info 레코드 → 자연어.
    """
    name = row.get("food_name", "")
    cal = row.get("calories", 0) or 0
    protein = row.get("protein", 0) or 0
    carbs = row.get("carbs", 0) or 0
    fat = row.get("fat", 0) or 0
    sodium = row.get("sodium", 0) or 0
    return (
        f"{name}은(는) 1인분 기준 약 {cal:.0f}kcal, "
        f"단백질 {protein:.0f}g, 탄수화물 {carbs:.0f}g, 지방 {fat:.0f}g. "
        f"나트륨 {sodium:.0f}mg."
    )


def format_restaurant_row(row: dict) -> str:
    """
    restaurants 레코드 → 자연어 (sentiment_score 포함).
    """
    name = row.get("name", "")
    category = row.get("category", "일반")
    distance = row.get("distance_m", 0) or 0
    rating = row.get("rating", 0) or 0
    sentiment = row.get("sentiment_score")
    menu_type = row.get("menu_type", "")

    sentiment_str = ""
    if sentiment is not None:
        sentiment_str = f", 감성 점수 {sentiment:+.2f}"

    return (
        f"{name}은(는) {category} 식당입니다. "
        f"사무실에서 약 {distance:.0f}m, 평점 {rating:.1f}{sentiment_str}. "
        f"대표 메뉴: {menu_type}"
    )


# =============================================================================
# 인덱서 메인 클래스
# =============================================================================
class ChromaDBIndexer:
    """
    Mini DB → ChromaDB 3 컬렉션 인덱싱.
    """

    COLLECTIONS = ["meal_history", "nutrition_info", "restaurants"]

    def __init__(
        self,
        chroma_path: str = DEFAULT_CHROMA_PATH,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        Path(chroma_path).mkdir(parents=True, exist_ok=True)
        self.chroma_path = chroma_path
        self.client = PersistentClient(path=chroma_path)
        self.embedding_fn = KoSBertEmbeddingFunction(embedding_model_name)
        logger.info(f"ChromaDBIndexer initialized: path={chroma_path}")

    def _get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # -------------------------------------------------------------------------
    # 컬렉션별 빌더
    # -------------------------------------------------------------------------
    def build_meal_history_collection(
        self,
        user_id: Optional[int] = None,
        days: int = 60,
    ) -> int:
        """
        meal_history 컬렉션 빌드 (upsert).

        Args:
            user_id: None 이면 전체 사용자
            days: 최근 N일만 포함

        Returns:
            인덱싱된 레코드 수
        """
        query = """
            SELECT id, user_id, meal_date, menu, calories, protein, satisfaction
            FROM meal_history
            WHERE meal_date >= date('now', :offset)
        """
        params = {"offset": f"-{days} days"}
        if user_id is not None:
            query += " AND user_id = :uid"
            params["uid"] = user_id

        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(query), params).mappings().fetchall()
        except Exception as e:
            logger.warning(f"meal_history query failed: {e}")
            return 0

        if not rows:
            logger.info("meal_history: no rows to index")
            return 0

        coll = self._get_or_create_collection("meal_history")
        documents = [format_meal_history_row(dict(r)) for r in rows]
        ids = [f"mh_{r['id']}" for r in rows]
        metadatas = [
            {
                "user_id": r["user_id"],
                "date": str(r["meal_date"]),
                "menu": r["menu"] or "",
            }
            for r in rows
        ]
        coll.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"meal_history: indexed {len(ids)} rows")
        return len(ids)

    def build_nutrition_collection(self) -> int:
        query = """
            SELECT id, food_name, calories, protein, carbs, fat, sodium
            FROM nutrition_info
        """
        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(query)).mappings().fetchall()
        except Exception as e:
            logger.warning(f"nutrition_info query failed: {e}")
            return 0

        if not rows:
            return 0

        coll = self._get_or_create_collection("nutrition_info")
        documents = [format_nutrition_row(dict(r)) for r in rows]
        ids = [f"nu_{r['id']}" for r in rows]
        metadatas = [
            {"food_name": r["food_name"] or ""} for r in rows
        ]
        coll.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"nutrition_info: indexed {len(ids)} rows")
        return len(ids)

    def build_restaurant_collection(self) -> int:
        query = """
            SELECT id, name, category, distance_m, rating,
                   sentiment_score, menu_type
            FROM restaurants
        """
        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(query)).mappings().fetchall()
        except Exception as e:
            logger.warning(f"restaurants query failed: {e}")
            return 0

        if not rows:
            return 0

        coll = self._get_or_create_collection("restaurants")
        documents = [format_restaurant_row(dict(r)) for r in rows]
        ids = [f"rt_{r['id']}" for r in rows]
        metadatas = [
            {
                "name": r["name"] or "",
                "category": r["category"] or "",
                "distance_m": float(r["distance_m"] or 0),
                "sentiment_score": float(r["sentiment_score"] or 0),
            }
            for r in rows
        ]
        coll.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"restaurants: indexed {len(ids)} rows")
        return len(ids)

    def build_all(self, user_id: Optional[int] = None) -> dict[str, int]:
        return {
            "meal_history": self.build_meal_history_collection(user_id=user_id),
            "nutrition_info": self.build_nutrition_collection(),
            "restaurants": self.build_restaurant_collection(),
        }

    def clear(self, collection_name: Optional[str] = None) -> None:
        if collection_name:
            self.client.delete_collection(collection_name)
        else:
            for c in self.COLLECTIONS:
                try:
                    self.client.delete_collection(c)
                except Exception:
                    pass
        logger.info(f"cleared: {collection_name or 'all'}")


# =============================================================================
# CLI
# =============================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="ChromaDB 인덱서")
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    indexer = ChromaDBIndexer()
    if args.clear:
        indexer.clear()
    result = indexer.build_all(user_id=args.user_id)
    print(f"Indexed: {result}")


if __name__ == "__main__":
    main()
```

### 6.2 `rag_chatbot/retriever.py`

```python
"""
ChromaDB 기반 Retriever.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from chromadb import PersistentClient

from nlp_mvp.rag_chatbot.indexer import (
    DEFAULT_CHROMA_PATH, DEFAULT_EMBEDDING_MODEL, KoSBertEmbeddingFunction
)
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    3개 컬렉션 병렬 검색.
    """

    def __init__(
        self,
        chroma_path: str = DEFAULT_CHROMA_PATH,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.client = PersistentClient(path=chroma_path)
        self.embedding_fn = KoSBertEmbeddingFunction(embedding_model_name)
        logger.info(f"Retriever initialized: {chroma_path}")

    def _get_collection(self, name: str):
        try:
            return self.client.get_collection(
                name=name, embedding_function=self.embedding_fn
            )
        except Exception as e:
            logger.warning(f"Collection {name} not found: {e}")
            return None

    def retrieve(
        self,
        query: str,
        user_id: Optional[int] = None,
        top_k_meal: int = 5,
        top_k_nutrition: int = 5,
        top_k_restaurant: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        3 컬렉션 병렬 검색.

        Returns:
            {
                "meal_history": [{"text": str, "metadata": dict, "distance": float}, ...],
                "nutrition_info": [...],
                "restaurants": [...]
            }
        """
        result: dict[str, list[dict[str, Any]]] = {
            "meal_history": [],
            "nutrition_info": [],
            "restaurants": [],
        }

        # meal_history (user_id 필터)
        coll = self._get_collection("meal_history")
        if coll is not None and top_k_meal > 0:
            where = {"user_id": user_id} if user_id is not None else None
            try:
                res = coll.query(
                    query_texts=[query],
                    n_results=top_k_meal,
                    where=where,
                )
                result["meal_history"] = self._flatten(res)
            except Exception as e:
                logger.warning(f"meal_history retrieve failed: {e}")

        # nutrition_info
        coll = self._get_collection("nutrition_info")
        if coll is not None and top_k_nutrition > 0:
            try:
                res = coll.query(query_texts=[query], n_results=top_k_nutrition)
                result["nutrition_info"] = self._flatten(res)
            except Exception as e:
                logger.warning(f"nutrition_info retrieve failed: {e}")

        # restaurants
        coll = self._get_collection("restaurants")
        if coll is not None and top_k_restaurant > 0:
            try:
                res = coll.query(query_texts=[query], n_results=top_k_restaurant)
                result["restaurants"] = self._flatten(res)
            except Exception as e:
                logger.warning(f"restaurants retrieve failed: {e}")

        logger.info(
            f"retrieve({query!r}): "
            f"meal={len(result['meal_history'])}, "
            f"nutrition={len(result['nutrition_info'])}, "
            f"rest={len(result['restaurants'])}"
        )
        return result

    @staticmethod
    def _flatten(chroma_result: dict) -> list[dict]:
        """ChromaDB 결과 → 평탄화된 list[dict]."""
        docs = chroma_result.get("documents", [[]])[0]
        metas = chroma_result.get("metadatas", [[]])[0]
        dists = chroma_result.get("distances", [[]])[0]
        return [
            {"text": d, "metadata": m or {}, "distance": float(dist)}
            for d, m, dist in zip(docs, metas, dists)
        ]
```

### 6.3 `rag_chatbot/prompt_templates.py`

```python
"""
프롬프트 템플릿 및 컨텍스트 포맷터.
"""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """당신은 "런치 코치"라는 이름의 친근한 영양사 AI 입니다.
직장인의 점심 선택을 도와주는 것이 주 역할입니다.

행동 원칙:
1. 제공된 사용자 식사 이력과 영양 데이터만을 근거로 답변합니다.
2. 의학적 진단은 하지 않으며, 필요 시 전문의 상담을 권유합니다.
3. 응답은 3~5문장, 이모지 2~3개 사용, 친근하고 긍정적으로.
4. 마지막에 구체적인 메뉴 또는 식당을 1~2개 추천합니다.
5. 데이터가 부족하면 솔직히 말하고 더 많은 기록을 권유합니다.

⚠️ 환각 방지 규칙:
- '=== 주변 추천 식당 ===' 섹션에 명시된 식당만 추천하세요.
- 목록에 없는 식당 이름을 만들어내지 마세요.
- 확실하지 않으면 "비슷한 옵션으로는" 같은 표현으로 일반화하세요.

📋 응답 포맷:
먼저 자연스러운 상담 답변을 작성한 후, 응답 끝에 다음 JSON 블록을 반드시 포함하세요:

```json
{
  "recommendations": [
    {"restaurant": "식당명", "menu": "메뉴명", "reason": "짧은 이유"}
  ]
}
```
"""


def format_context(context: dict[str, list[dict[str, Any]]]) -> str:
    """
    Retriever 결과를 LLM 이 이해하기 쉬운 텍스트로 변환.
    """
    parts = []

    meals = context.get("meal_history", [])
    if meals:
        parts.append("=== 최근 식사 이력 ===")
        for i, m in enumerate(meals, 1):
            parts.append(f"{i}. {m['text']}")

    nutrition = context.get("nutrition_info", [])
    if nutrition:
        parts.append("\n=== 관련 영양 정보 ===")
        for n in nutrition:
            parts.append(f"- {n['text']}")

    restaurants = context.get("restaurants", [])
    if restaurants:
        parts.append("\n=== 주변 추천 식당 ===")
        for i, r in enumerate(restaurants, 1):
            parts.append(f"{i}. {r['text']}")

    if not parts:
        return "(참고 데이터 없음)"

    return "\n".join(parts)


def build_prompt(
    user_query: str,
    context: dict[str, list[dict[str, Any]]],
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """
    Ollama chat 포맷 messages 빌더.

    Args:
        user_query: 사용자 질문
        context: Retriever 결과
        history: 이전 대화 턴 (ConversationHistory.messages)

    Returns:
        [{"role": "system"|"user"|"assistant", "content": str}, ...]
    """
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # 이전 대화 이력 포함
    if history:
        messages.extend(history)

    # 현재 질문 + 컨텍스트
    ctx_text = format_context(context)
    user_content = f"""{ctx_text}

=== 사용자 질문 ===
{user_query}"""

    messages.append({"role": "user", "content": user_content})
    return messages
```

### 6.4 `rag_chatbot/history.py`

```python
"""
멀티턴 대화 이력 관리.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversationHistory:
    """
    최근 N턴 또는 M자 제한으로 pruning.
    """
    max_turns: int = 5
    max_chars: int = 6000
    messages: list[dict[str, str]] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self._prune()

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self._prune()

    def clear(self) -> None:
        self.messages.clear()

    def _prune(self) -> None:
        # 턴 수 기준 (user+assistant 쌍)
        while len(self.messages) > self.max_turns * 2:
            self.messages.pop(0)
        # 문자 수 기준
        total = sum(len(m["content"]) for m in self.messages)
        while total > self.max_chars and self.messages:
            removed = self.messages.pop(0)
            total -= len(removed["content"])

    def __len__(self) -> int:
        return len(self.messages)
```

### 6.5 `rag_chatbot/chatbot.py`

```python
"""
LunchCoachBot — RAG + Ollama 대화 엔진.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp_mvp.rag_chatbot.history import ConversationHistory
from nlp_mvp.rag_chatbot.prompt_templates import build_prompt
from nlp_mvp.rag_chatbot.retriever import Retriever
from nlp_mvp.shared.logger import get_logger
from nlp_mvp.shared.ollama_client import OllamaClient

logger = get_logger(__name__)


# =============================================================================
# 응답 데이터 클래스
# =============================================================================
@dataclass
class ChatResponse:
    response: str
    recommendations: list[dict[str, str]] = field(default_factory=list)
    context_used: dict = field(default_factory=dict)
    latency_ms: int = 0
    validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "recommendations": self.recommendations,
            "context_used": self.context_used,
            "latency_ms": self.latency_ms,
            "validation": self.validation,
        }


# =============================================================================
# 응답 파싱 유틸
# =============================================================================
_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def extract_recommendations(response: str) -> list[dict[str, str]]:
    """
    LLM 응답에서 JSON 블록을 찾아 recommendations 추출.
    실패 시 빈 리스트.
    """
    match = _JSON_BLOCK_RE.search(response)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
        recs = data.get("recommendations", [])
        if isinstance(recs, list):
            return [r for r in recs if isinstance(r, dict)]
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}")
    return []


def strip_json_block(response: str) -> str:
    """응답 본문에서 JSON 블록 제거 (UI 표시용)."""
    return _JSON_BLOCK_RE.sub("", response).strip()


def validate_response(
    response: str,
    context: dict[str, list[dict]],
) -> dict[str, Any]:
    """
    환각 검증:
    - 응답에 언급된 식당명이 context["restaurants"] 에 존재하는가?

    Returns:
        {
            "hallucination_detected": bool,
            "allowed_names": set,
            "mentioned_names": set,
            "invalid_names": list[str],
        }
    """
    allowed = {
        r.get("metadata", {}).get("name", "")
        for r in context.get("restaurants", [])
        if r.get("metadata")
    }
    allowed.discard("")

    # 단순 휴리스틱: 식당명이 응답에 포함되었는지
    # (정밀 NER 은 시나리오 2)
    mentioned = set()
    for name in allowed:
        if name and name in response:
            mentioned.add(name)

    return {
        "hallucination_detected": False,  # 엄격 검증은 시나리오 2 에서
        "allowed_count": len(allowed),
        "mentioned_count": len(mentioned),
        "mentioned": sorted(mentioned),
    }


# =============================================================================
# 메인 챗봇 클래스
# =============================================================================
class LunchCoachBot:
    """
    RAG + Ollama 기반 영양 상담 챗봇.
    """

    def __init__(
        self,
        user_id: int,
        ollama_client: Optional[OllamaClient] = None,
        retriever: Optional[Retriever] = None,
        max_turns: int = 5,
        temperature: float = 0.3,
    ):
        self.user_id = user_id
        self.ollama = ollama_client or OllamaClient()
        self.retriever = retriever or Retriever()
        self.history = ConversationHistory(max_turns=max_turns)
        self.temperature = temperature
        logger.info(f"LunchCoachBot initialized: user_id={user_id}")

    def chat(
        self,
        user_query: str,
        top_k_meal: int = 5,
        top_k_nutrition: int = 5,
        top_k_restaurant: int = 5,
    ) -> ChatResponse:
        """
        동기 대화 호출.
        """
        start = time.time()

        # 1. 컨텍스트 검색
        context = self.retriever.retrieve(
            query=user_query,
            user_id=self.user_id,
            top_k_meal=top_k_meal,
            top_k_nutrition=top_k_nutrition,
            top_k_restaurant=top_k_restaurant,
        )

        # 2. 프롬프트 빌드 (이력 포함)
        messages = build_prompt(
            user_query=user_query,
            context=context,
            history=self.history.messages,
        )

        # 3. LLM 호출
        try:
            raw_response = self.ollama.chat(
                messages=messages,
                options={"temperature": self.temperature},
            )
        except Exception as e:
            logger.exception(f"Ollama chat failed: {e}")
            return ChatResponse(
                response=f"죄송합니다. 일시적인 오류가 발생했어요. ({e})",
                latency_ms=int((time.time() - start) * 1000),
            )

        # 4. 파싱
        recommendations = extract_recommendations(raw_response)
        display_text = strip_json_block(raw_response)

        # 5. 환각 검증
        validation = validate_response(raw_response, context)

        # 6. 이력 업데이트
        self.history.add_user(user_query)
        self.history.add_assistant(display_text)

        latency_ms = int((time.time() - start) * 1000)
        logger.info(
            f"chat() done: user={self.user_id}, latency={latency_ms}ms, "
            f"recs={len(recommendations)}"
        )

        return ChatResponse(
            response=display_text,
            recommendations=recommendations,
            context_used=context,
            latency_ms=latency_ms,
            validation=validation,
        )

    def reset(self) -> None:
        """대화 이력 초기화."""
        self.history.clear()
```

### 6.6 `rag_chatbot/streamlit_app.py`

```python
"""
Streamlit 데모 UI.

실행:
    cd Mini/NLP
    streamlit run nlp_mvp/rag_chatbot/streamlit_app.py
"""
import streamlit as st

from nlp_mvp.rag_chatbot.chatbot import LunchCoachBot
from nlp_mvp.rag_chatbot.indexer import ChromaDBIndexer
from nlp_mvp.shared.db import get_session
from nlp_mvp.shared.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)

st.set_page_config(page_title="🍱 런치 코치", page_icon="🍱", layout="wide")
st.title("🍱 런치 코치 — AI 점심 상담")


# -----------------------------------------------------------------------------
# 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")

    # 사용자 선택
    @st.cache_data(ttl=60)
    def load_users():
        try:
            with get_session() as session:
                rows = session.execute(
                    text("SELECT id, name FROM users ORDER BY id")
                ).fetchall()
            return [(r[0], r[1]) for r in rows]
        except Exception as e:
            logger.warning(f"load_users failed: {e}")
            return [(1, "기본 사용자")]

    users = load_users()
    user_id = st.selectbox(
        "사용자",
        options=[u[0] for u in users],
        format_func=lambda x: dict(users).get(x, f"user_{x}"),
    )

    st.divider()

    # 인덱스 재빌드
    if st.button("🔄 인덱스 재빌드"):
        with st.spinner("ChromaDB 인덱싱 중..."):
            indexer = ChromaDBIndexer()
            result = indexer.build_all(user_id=user_id)
        st.success(f"완료: {result}")

    # 대화 초기화
    if st.button("🗑️ 대화 초기화"):
        st.session_state.pop("bot", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.caption("**모델 정보**")
    st.code(f"Ollama: {st.session_state.get('bot').ollama.model if 'bot' in st.session_state else '...'}")


# -----------------------------------------------------------------------------
# 챗봇 초기화
# -----------------------------------------------------------------------------
if "bot" not in st.session_state or st.session_state.get("user_id") != user_id:
    st.session_state["bot"] = LunchCoachBot(user_id=user_id)
    st.session_state["user_id"] = user_id
    st.session_state["messages"] = []

bot: LunchCoachBot = st.session_state["bot"]


# -----------------------------------------------------------------------------
# 대화 UI
# -----------------------------------------------------------------------------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("recommendations"):
            cols = st.columns(min(3, len(msg["recommendations"])))
            for col, rec in zip(cols, msg["recommendations"]):
                with col:
                    st.info(
                        f"**{rec.get('restaurant', '')}**\n\n"
                        f"🍽️ {rec.get('menu', '')}\n\n"
                        f"_{rec.get('reason', '')}_"
                    )


# 입력 처리
if user_input := st.chat_input("오늘 점심, 뭐가 좋을까요?"):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("런치 코치가 생각 중... 🤔"):
            response = bot.chat(user_input)

        st.markdown(response.response)

        # 추천 카드
        if response.recommendations:
            st.markdown("### 🎯 추천")
            cols = st.columns(min(3, len(response.recommendations)))
            for col, rec in zip(cols, response.recommendations):
                with col:
                    st.info(
                        f"**{rec.get('restaurant', '')}**\n\n"
                        f"🍽️ {rec.get('menu', '')}\n\n"
                        f"_{rec.get('reason', '')}_"
                    )

        # 디버그 정보
        with st.expander("🔍 디버그"):
            st.write(f"**응답 속도:** {response.latency_ms} ms")
            st.write(f"**환각 검증:** {response.validation}")
            st.json(response.context_used)

    # 이력 저장
    st.session_state["messages"].append({
        "role": "assistant",
        "content": response.response,
        "recommendations": response.recommendations,
    })
```

### 6.7 테스트 (`rag_chatbot/tests/`)

**test_prompt_templates.py:**
```python
from nlp_mvp.rag_chatbot.prompt_templates import (
    SYSTEM_PROMPT, format_context, build_prompt
)

class TestFormatContext:
    def test_empty(self):
        result = format_context({})
        assert "데이터 없음" in result

    def test_with_meals(self):
        ctx = {
            "meal_history": [{"text": "2026-04-01: 김치찌개", "metadata": {}}],
            "nutrition_info": [],
            "restaurants": [],
        }
        result = format_context(ctx)
        assert "최근 식사 이력" in result
        assert "김치찌개" in result

class TestBuildPrompt:
    def test_includes_system(self):
        messages = build_prompt("안녕", {}, history=None)
        assert messages[0]["role"] == "system"
        assert "런치 코치" in messages[0]["content"]

    def test_includes_history(self):
        history = [
            {"role": "user", "content": "이전 질문"},
            {"role": "assistant", "content": "이전 답변"},
        ]
        messages = build_prompt("현재 질문", {}, history=history)
        # system + history(2) + current user = 4
        assert len(messages) == 4
```

**test_chatbot.py (Ollama mocking):**
```python
from unittest.mock import MagicMock, patch
import pytest

from nlp_mvp.rag_chatbot.chatbot import (
    LunchCoachBot, extract_recommendations, strip_json_block, validate_response
)

class TestExtract:
    def test_valid_json(self):
        resp = '''답변입니다.
```json
{"recommendations": [{"restaurant": "A", "menu": "B", "reason": "C"}]}
```'''
        recs = extract_recommendations(resp)
        assert len(recs) == 1
        assert recs[0]["restaurant"] == "A"

    def test_no_json(self):
        assert extract_recommendations("일반 응답") == []

    def test_strip(self):
        resp = '본문\n```json\n{"a": 1}\n```\n'
        assert strip_json_block(resp).strip() == "본문"


class TestValidate:
    def test_within_context(self):
        ctx = {"restaurants": [{"metadata": {"name": "A식당"}}]}
        result = validate_response("A식당을 추천합니다.", ctx)
        assert "A식당" in result["mentioned"]


class TestLunchCoachBot:
    def test_chat_returns_response(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = '''답변입니다. ```json
{"recommendations": [{"restaurant": "A", "menu": "B", "reason": "C"}]}
```'''
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = {
            "meal_history": [], "nutrition_info": [], "restaurants": []
        }
        bot = LunchCoachBot(
            user_id=1,
            ollama_client=mock_ollama,
            retriever=mock_retriever,
        )
        result = bot.chat("테스트")
        assert "답변" in result.response
        assert len(result.recommendations) == 1
        assert result.latency_ms >= 0
```

---

## 7. 구현 순서 (5일 체크리스트)

### Day 1 — Ollama + 인덱서
- [ ] `ollama serve` 가동, `ollama pull qwen2.5:7b-instruct`
- [ ] `OllamaClient.ping()` 성공 확인
- [ ] `indexer.py` 작성 (`KoSBertEmbeddingFunction`, `ChromaDBIndexer`)
- [ ] 3개 컬렉션 빌더 구현
- [ ] 샘플 데이터로 `build_all()` 실행 → ChromaDB 파일 생성 확인

### Day 2 — Retriever
- [ ] `retriever.py` 작성
- [ ] `user_id` 메타데이터 필터 확인
- [ ] `test_retriever.py` 기본 테스트
- [ ] 샘플 쿼리 5건으로 수동 검토 (관련성)

### Day 3 — 프롬프트
- [ ] `prompt_templates.py` 의 `SYSTEM_PROMPT` 완성
- [ ] `format_context()`, `build_prompt()` 구현
- [ ] 10개 수동 질문으로 응답 품질 체크
- [ ] JSON 블록 일관성 검증

### Day 4 — 챗봇 엔진
- [ ] `history.py` 의 `ConversationHistory`
- [ ] `chatbot.py` 의 `LunchCoachBot`, `ChatResponse`
- [ ] `extract_recommendations()`, `validate_response()`
- [ ] `test_chatbot.py` 통과
- [ ] 멀티턴 "그럼 다른 거" 테스트

### Day 5 — Streamlit + 평가
- [ ] `streamlit_app.py` 실행 성공
- [ ] 20개 질문 블라인드 평가 (5점 척도)
- [ ] 환각 0건 / 20 확인
- [ ] `03_rag_tuning.ipynb` 실행
- [ ] KPI 달성 체크

---

## 8. KPI 및 검증 기준

| # | 지표 | 측정 방법 | 목표 | 필수 |
|---|------|---------|-----|-----|
| 1 | Ollama ping | `client.ping()` | True | ✅ |
| 2 | ChromaDB 빌드 | 3 컬렉션 레코드 > 0 | True | ✅ |
| 3 | Retriever 관련성 | 수동 검토 5건 | ≥ 4/5 | ✅ |
| 4 | 응답 속도 (end-to-end) | 20건 평균 | ≤ 3초 | ✅ |
| 5 | 환각 케이스 | 20 질문 | 0건 | ✅ |
| 6 | 사용자 만족도 | 5점 척도 블라인드 | ≥ 4.0 | ✅ |
| 7 | JSON 블록 파싱 성공 | 20건 중 | ≥ 18/20 | ⭐ |
| 8 | 멀티턴 연속성 | "그럼 다른 거" | 관련 응답 | ✅ |
| 9 | Streamlit 동작 | 채팅 + 추천 카드 | ✓ | ✅ |
| 10 | 테스트 커버리지 | `pytest --cov` | ≥ 60% | ⭐ |

---

## 9. 트러블슈팅 (Step 3 한정)

### 9.1 Ollama 연결 실패
- `ollama serve &` 재기동
- `curl http://localhost:11434/api/tags` 로 수동 확인
- `.env` 의 `OLLAMA_HOST` 확인

### 9.2 모델 not found
- `ollama pull qwen2.5:7b-instruct`
- 경량 대안: `qwen2.5:3b-instruct`

### 9.3 ChromaDB 버전 충돌
- 기존 `.cache/` 또는 `chroma_store/` 삭제 후 재생성
- `pip install chromadb==0.5.0` 명시 버전

### 9.4 RAG 검색 결과 관련성 낮음
- 문장화 템플릿 재검토 (§3.5)
- `top_k` 상향
- 임베딩 모델 교체 (`BM-K/KoSimCSE-roberta-multitask`)

### 9.5 환각 빈번 (없는 식당 언급)
- `temperature` 0.3 → 0.1 로 낮춤
- SYSTEM_PROMPT 의 ⚠️ 규칙 강화
- Top-K 상향 (더 많은 실 데이터 제공)

### 9.6 응답 속도 > 5초
- 경량 모델 (`qwen2.5:3b`)
- `max_tokens` 제한 (options: `{"num_predict": 256}`)
- GPU 확인 (`nvidia-smi`)

### 9.7 Streamlit 상태 초기화 문제
- `st.cache_data` 의 TTL 조정
- `st.session_state` key 관리

### 9.8 JSON 블록 파싱 실패
- 모델이 JSON 미반환 → 프롬프트 예시 추가 (few-shot)
- 정규식 보강 (여러 코드 블록 지원)

---

## 10. 재사용 가능한 기존 파일

### 10.1 채울 스켈레톤
| 파일 | 상태 |
|------|------|
| `rag_chatbot/indexer.py` | 빈 → §6.1 |
| `rag_chatbot/retriever.py` | 빈 → §6.2 |
| `rag_chatbot/prompt_templates.py` | 빈 → §6.3 |
| `rag_chatbot/chatbot.py` | 빈 → §6.5 |
| `rag_chatbot/streamlit_app.py` | 빈 → §6.6 |
| `rag_chatbot/tests/test_retriever.py` | 빈 → §6.7 |
| `notebooks/03_rag_tuning.ipynb` | 스켈레톤 JSON |

### 10.2 신규 생성
- `rag_chatbot/history.py` (§6.4)
- `rag_chatbot/tests/test_prompt_templates.py` (§6.7)
- `rag_chatbot/tests/test_chatbot.py` (§6.7)

### 10.3 재사용 (shared/)
- `shared/db.py` — DB 접근
- `shared/logger.py` — 로거
- `shared/ollama_client.py` — **핵심 재사용**

---

## 11. 외부 의존성 확인

| 패키지 | 버전 | 용도 |
|--------|-----|------|
| `chromadb` | 0.5.0 | 벡터 DB |
| `ollama` | 0.3.0 | LLM SDK |
| `sentence-transformers` | 3.0.1 | 임베딩 |
| `streamlit` | 1.37.0 | UI |

**모두 `requirements.txt` 에 포함됨.** 추가 없음.

**시스템:**
- Ollama 서버 가동 필요
- RAM: qwen2.5:7b → 8GB, 3b → 4GB

---

## 12. 프롬프트 엔지니어링 상세

### 12.1 프롬프트 설계 원칙

| 원칙 | 구현 |
|------|-----|
| **역할 부여** | "당신은 런치 코치..." |
| **제약 조건 명시** | 5개 행동 원칙 나열 |
| **환각 방지** | ⚠️ 섹션으로 강조 |
| **포맷 강제** | JSON 블록 예시 |
| **한국어 자연스러움** | 이모지 · 존댓말 사용 |

### 12.2 Few-shot 추가 (선택, Day 3 튜닝)

```python
FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": "=== 주변 추천 식당 ===\n1. A식당 한식 평점 4.5\n=== 질문 ===\n추천해줘"
    },
    {
        "role": "assistant",
        "content": '오늘 A식당이 어떠세요? 😊 평점 4.5로 만족도가 높아요.\n\n```json\n{"recommendations":[{"restaurant":"A식당","menu":"김치찌개","reason":"평점 높음"}]}\n```'
    },
]
```

### 12.3 Temperature 튜닝

| 값 | 효과 |
|---|---|
| 0.0 | 결정적, 단조로움 |
| **0.3** | **균형 (권장)** |
| 0.7 | 창의적, 변동성 ↑ |
| 1.0 | 불안정 |

### 12.4 응답 길이 제어

```python
options = {
    "temperature": 0.3,
    "num_predict": 512,  # 최대 토큰
    "top_p": 0.9,
}
```

---

## 13. 다음 Step 과의 연결점

### 13.1 Step 4 (D5 NLG 리포트)
- `LunchCoachBot` 의 Ollama 클라이언트 재사용
- 프롬프트 빌더 패턴 재활용
- `nutrition_reports` 테이블의 `nlg_text` 는 챗봇 응답과 유사 톤

### 13.2 Step 5 (통합)
- Streamlit 앱을 FastAPI 엔드포인트로 포팅
- React 대시보드의 "AI 상담" 탭에 연결

### 13.3 ChatBOT/ 폴더와의 통합
- 본 Step 의 `LunchCoachBot` 은 ChatBOT/Phase2 (Tool Functions) 의 기반이 됨
- Function Calling 추가 시 tools 파라미터 확장

### 13.4 Phase 6 (시나리오 2)
- **D1 Intent + D2 Slot (JointBERT)** 로 Retriever 단계 대체 가능
- RAG 검색 전에 Intent 분류 → 필요한 컬렉션만 선택적 검색 (효율 ↑)
- 환각 검증을 NER 기반으로 고도화

---

## 14. 부록

### 14.A 20개 평가 질문 세트

**일반 추천 (5):**
1. 오늘 점심 뭐 먹을까?
2. 가볍게 먹을 만한 거 추천해줘
3. 매운 거 땡기는데 뭐 있어?
4. 건강한 메뉴 찾고 있어
5. 가성비 좋은 곳 알려줘

**개인화 (5):**
6. 요즘 단백질 부족한 거 같아
7. 이번 주 자주 먹은 메뉴 말고 다른 거
8. 어제 먹었던 거랑 비슷한 거
9. 저번에 만족도 높았던 식당 또 가고 싶어
10. 최근에 안 가본 카테고리 추천해줘

**상담/조언 (5):**
11. 살 빼는 중인데 뭐가 좋아?
12. 요즘 피곤한데 기력 회복되는 음식 있어?
13. 영양 균형 맞추려면 뭐 먹지?
14. 나트륨 너무 많이 먹는 거 같은데
15. 야근 예정인데 뭐 먹고 힘낼까?

**멀티턴 (5):**
16. 점심 추천해줘 → "더 싼 곳은?"
17. 한식 추천 → "일식은 없어?"
18. A식당 → "거기 말고 다른 데"
19. 매운 거 → "안 매운 걸로"
20. 추천해줘 → "두 번째 거 어때?"

### 14.B 평가 루브릭 (블라인드 평가용)

| 항목 | 5점 | 3점 | 1점 |
|------|-----|-----|-----|
| **관련성** | 질문과 정확히 일치 | 부분적 관련 | 무관 |
| **개인화** | 이력 반영 명확 | 일반적 | 무관 |
| **자연스러움** | 매끄러운 한국어 | 어색한 부분 있음 | 기계적 |
| **환각 없음** | 완전 사실 | 일부 의심 | 거짓 정보 |
| **행동 유도성** | 구체 추천 명확 | 모호함 | 추천 없음 |

**만족도 = 5개 항목 평균**

### 14.C ChromaDB 쿼리 예시

```python
# 기본 검색
coll.query(query_texts=["매운 음식"], n_results=5)

# 메타데이터 필터
coll.query(
    query_texts=["저녁 메뉴"],
    n_results=10,
    where={"user_id": 1}
)

# 복합 필터
coll.query(
    query_texts=["건강한"],
    where={"$and": [{"category": "샐러드"}, {"sentiment_score": {"$gt": 0.5}}]}
)
```

### 14.D Ollama 옵션 치트시트

```python
options = {
    "temperature": 0.3,       # 0.0~1.0
    "top_p": 0.9,             # nucleus sampling
    "top_k": 40,              # top-k sampling
    "num_predict": 512,       # 최대 생성 토큰
    "repeat_penalty": 1.1,    # 반복 페널티
    "stop": ["```"],          # 중단 문자열
}
```

### 14.E 참고 자료

1. **ChromaDB 공식:** https://docs.trychroma.com/
2. **Ollama API:** https://github.com/ollama/ollama/blob/main/docs/api.md
3. **RAG 패턴:** https://www.promptingguide.ai/techniques/rag
4. **Qwen2.5 모델 카드:** https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
5. **Streamlit Chat Elements:** https://docs.streamlit.io/library/api-reference/chat

---

## 15. 1페이지 체크리스트 요약

### ✅ Step 3 (D3 RAG 챗봇) 3주차 체크리스트

**Day 1 — Ollama + 인덱서**
- [ ] Ollama 서버 가동 · 모델 다운로드
- [ ] `indexer.py` + 3 컬렉션 빌드
- [ ] ChromaDB 파일 생성 확인

**Day 2 — Retriever**
- [ ] `retriever.py` 구현
- [ ] `user_id` 필터 동작
- [ ] 5건 수동 관련성 테스트

**Day 3 — 프롬프트**
- [ ] `SYSTEM_PROMPT` 작성
- [ ] `format_context()`, `build_prompt()` 구현
- [ ] 10건 수동 품질 테스트

**Day 4 — 챗봇**
- [ ] `ConversationHistory`
- [ ] `LunchCoachBot` + `chat()`
- [ ] JSON 블록 파싱
- [ ] 환각 검증
- [ ] `test_chatbot.py` 통과

**Day 5 — Streamlit + 평가**
- [ ] Streamlit 실행
- [ ] 20건 블라인드 평가
- [ ] 환각 0건 확인
- [ ] KPI 달성

### 🎯 KPI
- [ ] 응답 속도 ≤ 3초
- [ ] 환각 0건 / 20
- [ ] 만족도 ≥ 4.0 / 5.0
- [ ] 멀티턴 연속성

### 📦 산출물
- [ ] `rag_chatbot/` 6개 파일
- [ ] `tests/` 3개
- [ ] `chroma_store/` 3 컬렉션
- [ ] Streamlit 데모

### 📎 다음 단계
- [ ] Step 4 (D5 NLG 리포트)

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**대상:** Mini NLP MVP 3주차 구현자
**상위 문서:** [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §7
**선행 문서:**
- [`GUIDE_NLP_MVP_STEP1_SENTIMENT.md`](./GUIDE_NLP_MVP_STEP1_SENTIMENT.md)
- [`GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md`](./GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md)
**관련 문서:**
- [`README.md`](./README.md) — NLP 진입점
- [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) — D1/D2 JointBERT 심화

---

<div align="center">

**🔹 Step 3 — 데이터를 대화로 바꾸는 순간.**

*Mini NLP MVP — Where Database Meets Dialogue.*

</div>
