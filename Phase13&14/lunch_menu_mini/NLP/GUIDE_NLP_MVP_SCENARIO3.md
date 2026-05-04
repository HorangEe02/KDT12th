# 🧠 NLP MVP (시나리오 3) — Claude Code 구현 가이드라인

> **목표**: 기존 Mini "직장인 점심 최적화 파이프라인"에 **실용 NLP 레이어**를 4주 안에
> 얹어, 사용자가 체감 가능한 MVP로 완성합니다. 자체 모델 학습 없이 **사전학습 모델
> (Zero-shot)** 과 **로컬 LLM (Ollama)** 을 적극 활용하여 빠르고 저렴하게 구축합니다.
>
> 본 문서는 Claude Code 에게 전달할 수 있는 **단계별 구현 프롬프트**로 작성되었으며,
> 기존 `GUIDE/` · `ChatBOT/` 스타일과 동일한 포맷을 따릅니다.

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [사전 준비](#2-사전-준비)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [프로젝트 초기화](#4-프로젝트-초기화)
5. [Step 1 — 모듈 A1: 리뷰 감성분석 파이프라인](#5-step-1--모듈-a1-리뷰-감성분석-파이프라인)
6. [Step 2 — 모듈 B1: 메뉴명 정규화 파이프라인](#6-step-2--모듈-b1-메뉴명-정규화-파이프라인)
7. [Step 3 — 모듈 D3: RAG 기반 영양 상담 챗봇](#7-step-3--모듈-d3-rag-기반-영양-상담-챗봇)
8. [Step 4 — 모듈 D5: NLG 주간 영양 리포트](#8-step-4--모듈-d5-nlg-주간-영양-리포트)
9. [Step 5 — Mini 통합 및 대시보드 연동](#9-step-5--mini-통합-및-대시보드-연동)
10. [Step 6 — 테스트 및 평가](#10-step-6--테스트-및-평가)
11. [트러블슈팅 가이드](#11-트러블슈팅-가이드)
12. [체크리스트](#12-체크리스트)
13. [다음 단계 (시나리오 2 연결)](#13-다음-단계-시나리오-2-연결)

---

## 1. 프로젝트 개요

### 1.1 목표

기존 Mini 파이프라인 (카카오맵 · 기상청 · 식약처 · 팀 투표)에 **NLP 레이어 4종**을 추가하여:

1. **리뷰 감성** 기반 평점 보정으로 추천 품질 향상
2. **메뉴명 정규화** 로 영양 DB 조인율 개선
3. **RAG 챗봇** 으로 대화형 영양 상담 제공
4. **NLG 리포트** 로 수치를 친근한 한국어 코멘트로 변환

### 1.2 범위 (IN / OUT)

✅ **포함 (IN)**
- 사전학습 모델 Zero-shot 활용
- 로컬 LLM (Ollama) 추론
- SQLite 스키마 확장
- React 대시보드 UI 연동
- Streamlit 챗봇 데모

❌ **제외 (OUT)** — 시나리오 2에서 다룸
- 자체 모델 파인튜닝
- 대규모 데이터 라벨링
- ABSA · Food NER · Intent/Slot 학습
- GPU 기반 학습 인프라

### 1.3 성공 지표 (KPI)

| 지표 | 측정 방법 | 목표치 |
|------|----------|--------|
| 감성분석 처리량 | 리뷰/시간 | ≥ 1,000건 |
| 메뉴 정규화 정확도 | 수동 검증 200건 | ≥ 85% |
| 영양 DB 조인 성공률 | 전체 메뉴 대비 | 40% → 85% |
| RAG 응답 만족도 | 사용자 설문 (5점) | ≥ 4.0 |
| RAG 응답 속도 | 평균 latency | ≤ 3초 |
| NLG 리포트 자연스러움 | 블라인드 평가 | ≥ 4.0 |
| 점심 결정 시간 단축 | Before/After 설문 | 15분 → 5분 |

### 1.4 타임라인 (4주)

| 주차 | 작업 | 주요 산출물 |
|------|------|-----------|
| 1주 | A1 감성분석 구축 | 리뷰 DB · 감성점수 컬럼 |
| 2주 | B1 메뉴 정규화 구축 | 동의어 사전 · 매칭 모듈 |
| 3주 | D3 RAG 챗봇 구축 | ChromaDB · Streamlit 데모 |
| 4주 | D5 NLG + 통합 + 테스트 | 리포트 모듈 · React 연동 · v1.0 |

---

## 2. 사전 준비

### 2.1 필수 환경

| 항목 | 요구사항 | 비고 |
|------|---------|------|
| Claude Code | Claude Pro($20/월) 이상 | 구현 자동화 |
| Python | 3.10 이상 | 모든 NLP 모듈 |
| Node.js | 18.x 이상 | React 대시보드 연동 |
| OS | macOS 13+ / Ubuntu 20.04+ / WSL2 | - |
| Ollama | 0.3+ | 로컬 LLM 호스팅 |
| 디스크 | 10GB 이상 여유 | LLM 모델 저장 |
| RAM | 16GB 권장 (최소 8GB) | Qwen2.5-7B 구동 |
| GPU | 선택 사항 (있으면 가속) | CPU만으로도 동작 |

### 2.2 Python 패키지

```bash
pip install \
  transformers==4.44.0 \
  torch \
  sentence-transformers==3.0.1 \
  chromadb==0.5.0 \
  ollama==0.3.0 \
  fastapi==0.112.0 \
  uvicorn==0.30.0 \
  streamlit==1.37.0 \
  sqlalchemy==2.0.32 \
  pandas==2.2.2 \
  requests==2.32.3 \
  beautifulsoup4==4.12.3 \
  python-Levenshtein==0.25.1 \
  pydantic==2.8.2 \
  python-dotenv==1.0.1
```

### 2.3 Ollama 설치 및 모델 다운로드

```bash
# 1. Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh

# 2. 서비스 시작
ollama serve &

# 3. 한국어 특화 모델 다운로드 (택 1)
ollama pull qwen2.5:7b-instruct      # ⭐ 권장 (균형)
ollama pull gemma2:9b                 # 대안 (품질 우선)
ollama pull exaone3.5:7.8b            # LG 한국어 특화

# 4. 임베딩 모델 (별도 불필요 — Sentence-BERT 사용)

# 5. 동작 확인
ollama run qwen2.5:7b-instruct "안녕하세요"
```

### 2.4 환경 변수 (`.env` 파일)

```bash
# Mini/NLP/.env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
SENTIMENT_MODEL=nlp04/korean_sentiment_analysis_kcelectra
MINI_DB_PATH=../data/mini.db    # Mini/NLP/ 기준 → Mini/data/
CHROMA_DB_PATH=./nlp_mvp/rag_chatbot/chroma_store
```

⚠️ **주의:** `.env` 는 반드시 `.gitignore` 에 추가할 것.

### 2.5 작업 디렉토리 규칙

본 가이드의 모든 CLI 명령 (`streamlit`, `pytest`, `uvicorn`, `python -m` 등) 은
**`Mini/NLP/` 디렉토리에서 실행**하는 것을 전제로 합니다. 이 위치에 `.env`,
`nlp_mvp/` 가 모두 존재하므로 상대 경로가 자연스럽게 맞습니다.

```bash
cd Mini/NLP
# 이후 모든 명령어 실행
```

---

## 3. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                 MINI 기존 DATA SOURCES                         │
│    카카오맵 · 기상청 · 식약처 · 사용자 입력                          │
└──────────┬────────────────────────────────────────┬────────────┘
           │                                        │
           ▼                                        ▼
  ┌─────────────────┐                      ┌─────────────────┐
  │   A1: 감성분석    │                      │  B1: 메뉴 정규화  │
  │  (Zero-shot)    │                      │  (규칙+임베딩)    │
  │                 │                      │                 │
  │ 리뷰 크롤 → 분류  │                      │ 원시명 → 표준 ID  │
  │ → sentiment 점수 │                      │ → 영양DB 조인    │
  └────────┬────────┘                      └────────┬────────┘
           │                                        │
           └────────────────┬───────────────────────┘
                            ▼
          ┌─────────────────────────────────────┐
          │    확장된 SQLite (Mini 공용)       │
          │  + sentiment_score 컬럼              │
          │  + normalized_menu_id 컬럼           │
          │  + nutrition_reports 테이블          │
          └──────────────┬──────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐
   │  D5: NLG 리포트   │       │  D3: RAG 챗봇    │
   │  (LLM + 템플릿)   │       │  (ChromaDB +    │
   │                 │       │   Ollama)       │
   │ 팩트 → 한국어 문장│       │ 질문 → 상담 응답  │
   └────────┬────────┘       └────────┬────────┘
            │                         │
            └────────────┬────────────┘
                         ▼
           ┌──────────────────────────────┐
           │  React 대시보드 + Streamlit 챗 │
           │   (기존 Mini UI 확장)        │
           └──────────────────────────────┘
```

---

## 4. 프로젝트 초기화

### 4.1 폴더 구조 생성

Claude Code 프롬프트:

```
Mini/NLP/ 아래에 `nlp_mvp` 폴더를 생성하고 다음 구조로 초기화해줘:

nlp_mvp/
├── README.md
├── requirements.txt
├── .env.example
├── shared/
│   ├── __init__.py
│   ├── db.py                  # Mini SQLite 공용 접근
│   ├── ollama_client.py       # Ollama 호출 래퍼
│   └── logger.py              # 공용 로깅
├── sentiment/                 # A1 모듈
│   ├── __init__.py
│   ├── crawler.py
│   ├── preprocess.py
│   ├── sentiment_pipeline.py
│   ├── update_db.py
│   └── tests/
├── menu_normalizer/           # B1 모듈
│   ├── __init__.py
│   ├── rules.py
│   ├── synonym_dict.json
│   ├── embedding_matcher.py
│   ├── normalizer.py
│   ├── evaluate.py
│   └── tests/
├── rag_chatbot/               # D3 모듈
│   ├── __init__.py
│   ├── indexer.py
│   ├── retriever.py
│   ├── prompt_templates.py
│   ├── chatbot.py
│   ├── streamlit_app.py
│   └── chroma_store/          # gitignore
├── nlg_report/                # D5 모듈
│   ├── __init__.py
│   ├── fact_extractor.py
│   ├── prompt.py
│   ├── generator.py
│   └── templates/
├── api/                       # FastAPI 서빙
│   ├── main.py
│   ├── routers/
│   │   ├── sentiment.py
│   │   ├── chatbot.py
│   │   └── reports.py
│   └── schemas.py
├── integration/               # Mini 통합 지점
│   ├── __init__.py
│   └── scoring_patch.py       # 스코어링 v2 (감성 반영)
└── notebooks/                 # EDA 및 실험
    ├── 01_sentiment_eda.ipynb
    ├── 02_menu_normalizer_eval.ipynb
    ├── 03_rag_tuning.ipynb
    └── 04_nlg_samples.ipynb

각 `__init__.py` 는 빈 파일로, `README.md` 에는 간단한 소개 섹션을
포함시켜줘.
```

### 4.2 공용 유틸 구현

Claude Code 프롬프트:

```
nlp_mvp/shared/ 아래에 다음 유틸을 작성해줘:

1. db.py
   - Mini SQLite DB 경로를 .env에서 읽어옴
   - SQLAlchemy engine, sessionmaker 제공
   - `get_session()` 컨텍스트 매니저
   - 기존 Mini 테이블 (restaurants, meal_history, nutrition_info 등)을
     reflect 방식으로 로드

2. ollama_client.py
   - `OllamaClient` 클래스
   - .env에서 host / model 읽기
   - `chat(messages: list[dict]) -> str` 메서드 (ollama 공식 SDK 사용)
   - `embed(text: str) -> list[float]` (Sentence-BERT는 별도이므로 이 부분은 선택)
   - 타임아웃, 재시도 로직 포함
   - 로깅 포함

3. logger.py
   - 루트 로거 설정 (`nlp_mvp` 네임스페이스)
   - 파일 핸들러 + 콘솔 핸들러
   - 로그 포맷: %(asctime)s [%(name)s] %(levelname)s: %(message)s

모두 타입 힌트와 docstring 포함.
```

---

## 5. Step 1 — 모듈 A1: 리뷰 감성분석 파이프라인

> 📘 **상세 구현 가이드:** [`GUIDE_NLP_MVP_STEP1_SENTIMENT.md`](./GUIDE_NLP_MVP_STEP1_SENTIMENT.md)
> 2,015 라인 · 15 섹션 · 5일 체크리스트 · 브레인스토밍 · 50건 합성 리뷰 시드 포함

### 5.1 한 줄 요약

리뷰 텍스트 → KcELECTRA Zero-shot 감성분석 → 음식점별 `sentiment_score` (−1 ~ +1)
→ Mini 스코어링 엔진에 보정값으로 반영

### 5.2 핵심 파이프라인

```
crawler → preprocess → SentimentAnalyzer → aggregate → DB UPSERT
```

### 5.3 핵심 파일

- `nlp_mvp/sentiment/crawler.py` — 플러거블 데이터 소스 (Synthetic · AIHub · KakaoPublic)
- `nlp_mvp/sentiment/preprocess.py` — URL/이모지/중복 제거 순수 함수
- `nlp_mvp/sentiment/sentiment_pipeline.py` — `SentimentAnalyzer` + `aggregate()`
- `nlp_mvp/sentiment/update_db.py` — `ensure_schema()` + `run_sentiment_update()` + CLI

### 5.4 DB 스키마 영향

- `restaurants` 테이블에 5개 컬럼 추가 (`sentiment_score`, `sentiment_pos_ratio`, `sentiment_neg_ratio`, `sentiment_sample_size`, `sentiment_updated_at`)
- `reviews` 신규 테이블 생성

### 5.5 완료 기준 (KPI)

- 처리량 ≥ 1,000 리뷰/hr (CPU)
- 스모크 정확도 ≥ 11/12 (명확한 긍/부정)
- 100 식당 end-to-end 실행 (errors=0)
- 테스트 커버리지 ≥ 70%

👉 **구현 시작:** [`GUIDE_NLP_MVP_STEP1_SENTIMENT.md`](./GUIDE_NLP_MVP_STEP1_SENTIMENT.md) §7 (5일 체크리스트) 부터

---

## 6. Step 2 — 모듈 B1: 메뉴명 정규화 파이프라인

> 📘 **상세 구현 가이드:** [`GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md`](./GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md)
> 2,098 라인 · 15 섹션 · 3단계 하이브리드 매칭 설계 · 100건 합성 표준 메뉴 시드 포함

### 6.1 한 줄 요약

원시 메뉴명 → **규칙 → 편집거리 → 임베딩** 3단계 하이브리드 매칭 → 표준 메뉴 ID
→ Mini 영양 DB 조인율 **40% → 85%** 달성

### 6.2 핵심 파이프라인

```
원시명 → rules(전처리+동의어) → Levenshtein(편집거리≤2) → Sentence-BERT(유사도≥0.85) → 표준 ID
```

### 6.3 핵심 파일

- `nlp_mvp/menu_normalizer/rules.py` — 전처리 + 동의어 사전 (150+ 엔트리)
- `nlp_mvp/menu_normalizer/synonym_dict.json` — 섹션 분리 사전 (축약어/변형/복합어)
- `nlp_mvp/menu_normalizer/levenshtein.py` — adaptive cutoff 편집거리 매칭
- `nlp_mvp/menu_normalizer/embedding_matcher.py` — Sentence-BERT + Pickle 캐싱
- `nlp_mvp/menu_normalizer/loader.py` — `StandardMenuLoader` (Synthetic/NutritionDB/File)
- `nlp_mvp/menu_normalizer/normalizer.py` — `MenuNormalizer` 통합 클래스
- `nlp_mvp/menu_normalizer/evaluate.py` — F1 평가 + 실패 분석

### 6.4 DB 스키마 영향

- `menu_normalization` 신규 테이블 (raw_name, normalized_id, confidence, method, UPSERT)
- `meal_history.normalized_menu_id` 컬럼 추가 (선택)

### 6.5 완료 기준 (KPI)

- 전체 정확도 **F1 ≥ 0.85**
- 매칭률 ≥ 90%
- 동의어 사전 ≥ 150 엔트리
- 임베딩 캐시 로딩 < 2초

👉 **구현 시작:** [`GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md`](./GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md) §7 (5일 체크리스트) 부터

---

## 7. Step 3 — 모듈 D3: RAG 기반 영양 상담 챗봇

> 📘 **상세 구현 가이드:** [`GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md`](./GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md)
> 1,796 라인 · 15 섹션 · 환각 방지 3중 방어 · 20개 평가 질문 세트 · 멀티턴 관리 포함

### 7.1 한 줄 요약

사용자 자연어 질문 → ChromaDB 3 컬렉션 검색 → Ollama Qwen2.5 → 개인화된 한국어 상담 응답
+ Streamlit 채팅 UI

### 7.2 핵심 파이프라인

```
query → Retriever(meal_history+nutrition+restaurants) → prompt_builder → Ollama → 파싱+환각검증 → history
```

### 7.3 핵심 파일

- `nlp_mvp/rag_chatbot/indexer.py` — `ChromaDBIndexer` + 3 컬렉션 문장화 템플릿
- `nlp_mvp/rag_chatbot/retriever.py` — 메타데이터 필터 기반 병렬 검색
- `nlp_mvp/rag_chatbot/prompt_templates.py` — `SYSTEM_PROMPT` (환각 방지 규칙 포함)
- `nlp_mvp/rag_chatbot/history.py` — `ConversationHistory` (최근 5턴 + 길이 가드)
- `nlp_mvp/rag_chatbot/chatbot.py` — `LunchCoachBot` + JSON 블록 파싱
- `nlp_mvp/rag_chatbot/streamlit_app.py` — 사이드바 + 채팅 UI + 추천 카드

### 7.4 의존성

- **Ollama 서버 가동 필수** (`ollama serve` + `ollama pull qwen2.5:7b-instruct`)
- `chromadb==0.5.0`, `sentence-transformers==3.0.1`, `streamlit==1.37.0`

### 7.5 완료 기준 (KPI)

- 응답 속도 end-to-end ≤ 3초
- 환각 케이스 **0건** / 20 질문
- 블라인드 만족도 ≥ 4.0 / 5.0
- 멀티턴 연속성 ("그럼 다른 거" 처리)

👉 **구현 시작:** [`GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md`](./GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md) §7 (5일 체크리스트) 부터

---

## 8. Step 4 — 모듈 D5: NLG 주간 영양 리포트

> 📘 **상세 구현 가이드:** [`GUIDE_NLP_MVP_STEP4_NLG_REPORT.md`](./GUIDE_NLP_MVP_STEP4_NLG_REPORT.md)
> 1,870 라인 · 15 섹션 · 하이브리드 NLG 설계 · 문체 가이드 · 10건 샘플 평가 포함

### 8.1 한 줄 요약

주간 `meal_history` 수치 → **규칙 기반 팩트 추출** (100% 정확) → **LLM 자연어 변환**
→ 친근한 한국어 리포트 (환각 방지) + 템플릿 fallback

### 8.2 핵심 파이프라인

```
extract_weekly_facts → build_report_prompt → Ollama → validate → (template fallback) → DB UPSERT
```

### 8.3 핵심 파일

- `nlp_mvp/nlg_report/fact_extractor.py` — `WeeklyFacts` + SQL 집계 + 균형 점수
- `nlp_mvp/nlg_report/prompt.py` — `REPORT_SYSTEM_PROMPT` (문체 규칙 5개 + 금기 사항)
- `nlp_mvp/nlg_report/generator.py` — `ReportGenerator` + 3단계 fallback (LLM → 템플릿 → 최소)
- `nlp_mvp/nlg_report/templates/fallback.txt` — f-string 템플릿
- `nlp_mvp/api/routers/reports.py` — FastAPI 엔드포인트 2종

### 8.4 DB 스키마 영향

- `nutrition_reports` 신규 테이블 (user_id, week_start, facts JSON, nlg_text, UPSERT)

### 8.5 완료 기준 (KPI)

- 자연스러움 평가 ≥ 4.0 / 5.0 (블라인드)
- 유용성 평가 ≥ 4.0 / 5.0
- 팩트 오류 0건 / 10 샘플
- 생성 속도 ≤ 5초
- Template fallback 동작 (LLM 강제 실패 시)

👉 **구현 시작:** [`GUIDE_NLP_MVP_STEP4_NLG_REPORT.md`](./GUIDE_NLP_MVP_STEP4_NLG_REPORT.md) §7 (5일 체크리스트) 부터

---

## 9. Step 5 — Mini 통합 및 대시보드 연동

### 9.1 통합 스코어링 엔진 업데이트

Claude Code 프롬프트:

```
기존 Mini 의 통합 추천 엔진에 NLP 보정을 추가해줘.

Mini/NLP/nlp_mvp/integration/scoring_patch.py 를 신규 작성:

def compute_composite_score_v2(
    restaurant: dict,
    weather: dict,
    nutrition: dict,
    team: dict,
    sentiment: dict = None
) -> float:
    """
    기존: 거리(0.3) + 날씨(0.2) + 영양(0.2) + 팀선호(0.3)

    신규 v2 (NLP 반영):
    거리(0.25) + 날씨(0.15) + 영양(0.15) + 팀선호(0.25) + 감성(0.20)

    또는:
    기존 공식 × (1 + 0.15 × sentiment_score) 형태 보정 (A/B 옵션)
    """

scoring_patch_ab.py:
- 기존 스코어링과 신규 스코어링을 병렬 계산
- A/B 테스트 로그 기록
```

### 9.2 FastAPI 라우터 추가

Claude Code 프롬프트:

```
nlp_mvp/api/main.py 및 routers/ 를 작성해줘.

FastAPI 앱:
- 엔드포인트:
  · GET /nlp/sentiment/{restaurant_id}
      → 해당 식당의 감성 점수 및 분포
  · POST /nlp/sentiment/refresh
      → 감성분석 파이프라인 실행 (비동기)
  · POST /nlp/chatbot/chat
      body: {"user_id": int, "query": str}
      → RAG 챗봇 응답
  · GET /nlp/reports/weekly/{user_id}
      → 이번 주 NLG 리포트 (없으면 생성)
  · POST /nlp/menu/normalize
      body: {"raw_name": str}
      → 메뉴 정규화 결과

- CORS 설정: React 대시보드 도메인 허용
- 에러 핸들러
- 로깅 미들웨어
- uvicorn 구동: uvicorn nlp_mvp.api.main:app --reload --port 8001
```

### 9.3 React 대시보드 확장

Claude Code 프롬프트:

```
lunch-optimizer-dashboard.jsx 를 기반으로 다음 기능을 추가해줘
(기존 4개 탭은 유지, 내부 로직만 확장):

1. 음식점 탐색 탭:
   - 각 카드에 감성 뱃지 추가
     😊 XX% / 😐 XX% / 😞 XX%
   - 감성 점수 기준 정렬 옵션 추가

2. 영양 리포트 탭:
   - 상단에 "AI 코멘트" 카드 추가
     · /nlp/reports/weekly/{user_id} 호출
     · NLG 텍스트 표시 + 생성 일시
     · "다시 생성" 버튼

3. 신규 탭 "💬 AI 상담":
   - 우측 사이드 채팅 UI
   - /nlp/chatbot/chat 호출
   - 대화 이력 표시
   - 추천 식당 카드 하단 표시

4. API 베이스 URL 을 환경 변수 (.env) 로 분리
   REACT_APP_NLP_API=http://localhost:8001

기존 더미 데이터 부분은 유지하되,
fetchFromNLP(endpoint) 유틸 함수를 만들어 재사용.
```

---

## 10. Step 6 — 테스트 및 평가

### 10.1 단위 테스트

Claude Code 프롬프트:

```
nlp_mvp/ 의 각 모듈에 대해 pytest 테스트를 작성해줘.

테스트 대상:
1. sentiment/tests/test_preprocess.py
   - clean_text, is_valid_review, deduplicate
2. sentiment/tests/test_sentiment_pipeline.py
   - 긍정/부정 샘플 10건
3. menu_normalizer/tests/test_rules.py
   - 전처리 20 케이스
4. menu_normalizer/tests/test_normalizer.py
   - end-to-end 매칭 15 케이스
5. rag_chatbot/tests/test_retriever.py
   - 컬렉션별 top_k 검증
6. nlg_report/tests/test_fact_extractor.py
   - 더미 meal_history 검증

모두 pytest 로 한 번에 실행:
pytest nlp_mvp/ -v --tb=short

커버리지 목표: 핵심 로직 70% 이상
```

### 10.2 통합 평가 스크립트

Claude Code 프롬프트:

```
nlp_mvp/evaluate_all.py 를 작성해줘.

실행 내용:
1. 감성분석: 샘플 200건 수동 라벨 vs 예측 비교 → accuracy
2. 메뉴 정규화: menu_test_set.csv → F1
3. RAG 챗봇: 10개 질문 세트 → 응답 시간 및 관련성 체크
4. NLG 리포트: 10개 샘플 → 길이, 금칙어, 이모지 개수 검증

출력:
- nlp_mvp/evaluation_report.md
  각 모듈별 결과 테이블 + 코멘트

KPI 달성 여부를 ✅ / ❌ 로 표시
```

### 10.3 성능 벤치마크

Claude Code 프롬프트:

```
nlp_mvp/benchmark.py 를 작성해줘.

측정 항목:
1. 감성분석 처리량 (batch_size 별)
2. 임베딩 매칭 응답 시간
3. RAG 챗봇 end-to-end latency
4. NLG 리포트 생성 시간

실행:
python nlp_mvp/benchmark.py --runs 50

출력:
- nlp_mvp/benchmark_results.json
- 평균, p50, p95, p99
```

---

## 11. 트러블슈팅 가이드

### 11.1 Ollama 연결 실패

| 증상 | 원인 | 해결 |
|------|------|------|
| `ConnectionError: localhost:11434` | Ollama 미실행 | `ollama serve &` |
| `model not found` | 모델 미다운로드 | `ollama pull qwen2.5:7b-instruct` |
| 응답 매우 느림 (10초+) | CPU 추론 | GPU 확인 또는 더 작은 모델 (`qwen2.5:3b`) |

### 11.2 감성분석 분류 이상

| 증상 | 원인 | 해결 |
|------|------|------|
| 모든 리뷰 긍정으로 분류 | 모델이 한국어 감성에 약함 | 모델 교체 (`nlp04/...`) |
| confidence 평균 < 0.5 | 입력 전처리 부족 | preprocess 강화 |
| OOM 에러 | 배치 사이즈 과다 | `batch_size=8` 축소 |

### 11.3 메뉴 정규화 낮은 매칭률

| 증상 | 원인 | 해결 |
|------|------|------|
| 매칭률 50% 이하 | 동의어 사전 부족 | synonym_dict.json 확장 |
| 긴 메뉴명 미스매치 | 전처리 토큰화 필요 | 형태소 분석기 (konlpy) 추가 |
| 임베딩 유사도 모두 낮음 | 표준 메뉴 DB 부족 | 식약처 CSV 직접 적재 |

### 11.4 RAG 챗봇 환각 (Hallucination)

| 증상 | 원인 | 해결 |
|------|------|------|
| 존재하지 않는 식당 언급 | 프롬프트 제약 약함 | SYSTEM_PROMPT 에 "제공된 컨텍스트만 사용" 강조 |
| 관련 없는 답변 | retriever top_k 낮음 | top_k 를 5→10 으로 증가 |
| 응답 일관성 없음 | temperature 높음 | temperature=0.3 으로 낮춤 |

### 11.5 ChromaDB 속도 이슈

| 증상 | 원인 | 해결 |
|------|------|------|
| 인덱싱 매우 느림 | 임베딩 모델 CPU | 배치 임베딩 + cache |
| 검색 결과 부정확 | 문장화 품질 낮음 | 템플릿 재설계 |

---

## 12. 체크리스트

### 12.1 Step 1 — 감성분석 (A1)

- [ ] `nlp_mvp/sentiment/` 폴더 구조 생성
- [ ] `crawler.py` 작성 및 ToS 주석 포함
- [ ] `preprocess.py` 및 단위 테스트 통과
- [ ] `sentiment_pipeline.py` 배치 추론 동작
- [ ] DB 스키마 `ensure_schema()` 멱등 동작 확인
- [ ] `update_db.py` dry-run 성공
- [ ] 실제 데이터 100 식당 처리 완료
- [ ] EDA 노트북 실행 및 정확도 추정
- [ ] KPI: 처리량 ≥ 1,000건/hr 확인

### 12.2 Step 2 — 메뉴 정규화 (B1)

- [ ] `rules.py` + synonym_dict 100+ 엔트리
- [ ] `embedding_matcher.py` 캐싱 동작
- [ ] `normalizer.py` 3단계 파이프라인 통합
- [ ] `menu_test_set.csv` 100건 수동 라벨
- [ ] `evaluate.py` 결과 F1 ≥ 0.85
- [ ] 전체 음식점 메뉴 정규화 배치 실행
- [ ] 영양 DB 조인율 측정 (목표 85%)

### 12.3 Step 3 — RAG 챗봇 (D3)

- [ ] Ollama 모델 동작 확인
- [ ] ChromaDB 3개 컬렉션 구축
- [ ] `retriever.py` 관련성 테스트
- [ ] `prompt_templates.py` SYSTEM_PROMPT 확정
- [ ] `chatbot.py` 10개 샘플 질문 응답 확인
- [ ] Streamlit 앱 로컬 실행 성공
- [ ] 응답 속도 ≤ 3초
- [ ] 환각 검증 (컨텍스트 외 응답 0건)

### 12.4 Step 4 — NLG 리포트 (D5)

- [ ] `fact_extractor.py` 더미 데이터 검증
- [ ] `prompt.py` SYSTEM_PROMPT 작성
- [ ] `generator.py` end-to-end 동작
- [ ] `nutrition_reports` 테이블 생성
- [ ] 샘플 10건 생성 및 저장
- [ ] 블라인드 평가 4.0/5 이상

### 12.5 Step 5 — 통합

- [ ] FastAPI 라우터 5개 엔드포인트 동작
- [ ] React 대시보드 감성 뱃지 표시
- [ ] AI 코멘트 카드 렌더링
- [ ] AI 상담 탭 채팅 UI 동작
- [ ] CORS 및 에러 처리 검증

### 12.6 Step 6 — 테스트/평가

- [ ] pytest 전체 통과
- [ ] `evaluate_all.py` 리포트 생성
- [ ] `benchmark.py` 결과 저장
- [ ] KPI 달성 여부 문서화
- [ ] v1.0 릴리즈 태그

---

## 13. 다음 단계 (시나리오 2 연결)

본 시나리오 3 MVP 완료 후, **시나리오 2 (연구형 심화)** 로 확장합니다:

| MVP 모듈 | 시나리오 2 교체/확장 | 비고 |
|---------|---------------------|------|
| A1 Zero-shot 감성분석 | **A2** ABSA (속성별 파인튜닝) | 맛/가격/서비스/청결 4축 분리 |
| B1 규칙/임베딩 정규화 | **B2** Food NER 추가 | 재료·맛·알레르겐 추출 |
| D3 RAG 챗봇 | **D1+D2** JointBERT (Intent+Slot) | Ollama 대비 벤치마크 |
| D5 NLG 리포트 | **E1** 임베딩 기반 개인화 CF | 리포트에 개인 추천 통합 |

**마이그레이션 전략:**
- MVP 코드는 유지 (fallback 및 A/B 비교용)
- `models/` 폴더 신설 → 학습 모델 분리
- 동일 FastAPI 엔드포인트 유지, 내부 구현만 교체
- 전/후 벤치마크 비교 자동화

자세한 내용은 [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) 참고.

---

## 📎 부록

### A. 참고 자료

| 주제 | 링크 |
|------|------|
| Hugging Face 한국어 감성 모델 | https://huggingface.co/nlp04/korean_sentiment_analysis_kcelectra |
| KoSentenceBERT | https://huggingface.co/jhgan/ko-sroberta-multitask |
| Ollama | https://ollama.com/ |
| ChromaDB | https://docs.trychroma.com/ |
| LangChain RAG | https://python.langchain.com/docs/tutorials/rag/ |
| Streamlit 챗 UI | https://docs.streamlit.io/library/api-reference/chat |
| FastAPI | https://fastapi.tiangolo.com/ |

### B. 용어집

| 용어 | 설명 |
|------|------|
| Zero-shot | 별도 파인튜닝 없이 사전학습 모델을 그대로 사용하는 방식 |
| RAG | Retrieval-Augmented Generation, 검색 증강 생성 |
| NLG | Natural Language Generation, 자연어 생성 |
| Sentence-BERT | 문장 단위 임베딩을 생성하는 BERT 변형 모델 |
| Hallucination | LLM 이 근거 없는 정보를 만들어내는 현상 |
| ChromaDB | 로컬 파일 기반 벡터 데이터베이스 |

### C. 폴더 구조 최종본

```
Mini/
├── 0README.md
├── README.md
├── lunch-optimizer-dashboard.jsx
├── api/                         # API 키 PDF (기존)
├── GUIDE/                       # 기존 서브토픽 가이드
├── ChatBOT/                     # 기존 챗봇 가이드
└── NLP/                         ← NLP 확장 레이어
    ├── README.md                        ← NLP 진입점
    ├── GUIDE_NLP_MVP_SCENARIO3.md       ← 본 문서 (시나리오 3)
    ├── GUIDE_NLP_RESEARCH_SCENARIO2.md  ← 시나리오 2 (연구, 10주)
    └── nlp_mvp/                         ← 본 시나리오 구현 결과물
        ├── shared/
        ├── sentiment/       (A1)
        ├── menu_normalizer/ (B1)
        ├── rag_chatbot/     (D3)
        ├── nlg_report/      (D5)
        ├── api/             (FastAPI)
        ├── integration/     (scoring_patch)
        ├── notebooks/
        ├── evaluate_all.py
        └── benchmark.py
```

---

**문서 버전:** v1.1
**작성일:** 2026-04-07
**대상:** Claude Code 기반 구현
**예상 소요 기간:** 4주 (1인 기준)
**상위 문서:** [`README.md`](./README.md) (NLP 레이어 진입점)
**후속 문서:** [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) (연구/심화, 10주)
