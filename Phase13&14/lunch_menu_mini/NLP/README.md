# 🧠 NLP 레이어 — Mini 자연어 처리 확장 모듈 · 🎯 메인

> **Mini "직장인 점심 최적화 파이프라인" 의 메인 언어 처리 축**
>
> 2026-04-08 결정에 따라 **NLP 레이어가 프로젝트의 메인 대화·언어 처리 축**으로 채택되었습니다.
> (`ChatBOT/` 폴더는 선택적 추가 기능으로 유지 — 상세는
> [`../ROLE_SEPARATION_DECISION.md`](../ROLE_SEPARATION_DECISION.md))
>
> 기존 4개 서브토픽 (음식점·날씨·영양·팀투표) 과 결합하여,
> **리뷰 텍스트 이해 · 메뉴명 정규화 · 대화형 상담 · 자연어 리포트** 기능을 제공합니다.

---

## 📋 목차

1. [폴더 위치 및 역할](#1-폴더-위치-및-역할)
2. [왜 NLP 레이어가 필요한가?](#2-왜-nlp-레이어가-필요한가)
3. [기존 Mini 과의 관계](#3-기존-mini-과의-관계)
4. [두 가지 시나리오 개요](#4-두-가지-시나리오-개요)
5. [진행 순서 권장안](#5-진행-순서-권장안)
6. [모듈 매핑 표](#6-모듈-매핑-표)
7. [파이프라인 통합 지점](#7-파이프라인-통합-지점)
8. [폴더 구조](#8-폴더-구조)
9. [문서 네비게이션](#9-문서-네비게이션)
10. [시작하기](#10-시작하기)
11. [FAQ](#11-faq)

---

## 1. 폴더 위치 및 역할

```
Mini/
├── 0README.md                       # 프로젝트 전체 개요
├── README.md                         # 상세 기획서
├── lunch-optimizer-dashboard.jsx     # React 대시보드 (Phase 1 MVP)
├── api/                              # 공공 API 키 보관
├── GUIDE/                            # 🧩 4개 서브토픽 구현 가이드
│   ├── GUIDE_SUBTOPIC_1_RESTAURANT_COLLECTOR.md
│   ├── GUIDE_SUBTOPIC_2_WEATHER_RECOMMENDATION.md
│   ├── GUIDE_SUBTOPIC_3_NUTRITION_ANALYSIS.md
│   └── GUIDE_SUBTOPIC_4_TEAM_VOTING.md
├── ChatBOT/                          # 🤖 LLM 기반 대화형 확장 (Ollama)
│   ├── GUIDE_CHATBOT_INTEGRATION.md
│   ├── GUIDE_PHASE1_CHATBOT_IMPLEMENTATION.md
│   ├── GUIDE_PHASE2_TOOL_FUNCTIONS.md
│   ├── GUIDE_PHASE3_MULTITURN_PERSONALIZATION.md
│   └── GUIDE_PHASE4_DOCKER_DEPLOYMENT.md
└── NLP/                              ← 🧠 본 폴더 (NLP 확장 레이어)
    ├── README.md                     ← 본 문서 (진입점)
    ├── GUIDE_NLP_MVP_SCENARIO3.md    ← 시나리오 3 (MVP, 4주)
    └── GUIDE_NLP_RESEARCH_SCENARIO2.md ← 시나리오 2 (연구형, 10주)
```

### 역할 구분

| 폴더 | 성격 | 목적 |
|------|------|------|
| `GUIDE/` | **데이터 파이프라인** | 4개 공공 데이터 소스 수집·정제·스코어링 |
| `ChatBOT/` | **대화 인터페이스** | Ollama 기반 LLM 챗봇, 함수 호출, 프롬프트 엔지니어링 |
| `NLP/` | **언어 이해·생성** | 감성분석, 메뉴 정규화, RAG, NLG, 파인튜닝 |

**요약:** `GUIDE/` 는 "숫자를 모으는 곳", `ChatBOT/` 은 "대화를 구동하는 곳",
`NLP/` 는 "텍스트를 이해하고 생성하는 곳" 입니다.

---

## 2. 왜 NLP 레이어가 필요한가?

### 기존 Mini 의 한계

기존 Mini 은 **정형 수치 데이터 기반 가중 점수 모델**에 집중되어 있습니다.
이는 추천 엔진으로서는 견고하지만, 다음과 같은 약점이 존재합니다:

| # | 한계 | 영향 |
|---|------|------|
| 1 | 리뷰 텍스트를 활용하지 않음 | 평점만으로는 "맛은 좋은데 서비스는 별로" 같은 **질적 평가**가 무시됨 |
| 2 | 메뉴명이 제각각 | "김찌", "김치찌개(大)", "묵은지찌개" 가 **영양 DB 와 조인되지 않음** |
| 3 | 사용자 자연어 질의 불가 | "요즘 피곤한데 뭐 먹을까?" 같은 **맥락 질문에 응답 못 함** |
| 4 | 수치 리포트의 가독성 낮음 | 영양소 수치 덩어리 → 사용자가 **해석 부담** |
| 5 | 팀 대화·소셜 데이터 무활용 | 슬랙·블로그에 숨어있는 **실제 선호 신호 누락** |

### NLP 가 해결하는 것

```
┌───────────────────────────────────┬──────────────────────────┐
│  기존 Mini                      │  NLP 레이어 추가 후          │
├───────────────────────────────────┼──────────────────────────┤
│ 평점 4.2 / 리뷰 수 120              │ 평점 4.2 + 감성 88% 긍정      │
│ "김치찌개(大)" → 조인 실패           │ → 표준 "김치찌개" 자동 매핑     │
│ "오늘 뭐 먹지?" → 4탭 탐색 필요       │ → 한 문장 질의로 응답         │
│ "단백질 48g, 목표 60g"              │ → "단백질이 살짝 부족해요 😊"    │
│ 내부 DB 만 활용                     │ → 리뷰·SNS 텍스트 활용 가능    │
└───────────────────────────────────┴──────────────────────────┘
```

---

## 3. 기존 Mini 과의 관계

NLP 레이어는 **기존 시스템을 교체하지 않고 확장**합니다.
기존 `GUIDE/` 모듈의 출력물을 입력으로 받아, NLP 결과를 **보정값·증분 데이터** 로
제공합니다.

### 데이터 흐름

```
┌──────────────────────────────────────────────────────────────┐
│                   GUIDE/ (Mini 기존)                       │
│                                                              │
│   [수집]      [정제]      [스코어링]       [저장]             │
│   4개 API  →  ETL    →    가중 점수    →  SQLite             │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      │ (1) 기존 데이터 읽기
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    NLP/ (본 확장 레이어)                      │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ A1/A2 감성   │  │ B1/B2 메뉴   │  │ D1~D5 대화   │        │
│  │ 분석         │  │ 정규화·NER   │  │ NLU/NLG/RAG  │        │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                │                  │                │
│         ▼                ▼                  ▼                │
│  ┌──────────────────────────────────────────────────┐       │
│  │   NLP 결과를 Mini DB 에 UPSERT (보정·증분)      │       │
│  │   · sentiment_score                              │       │
│  │   · normalized_menu_id                           │       │
│  │   · nutrition_reports (NLG 텍스트)                │       │
│  └──────────────────────┬───────────────────────────┘       │
└─────────────────────────┼────────────────────────────────────┘
                          │ (2) 보정된 데이터 재사용
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              통합 스코어링 v2 (NLP 반영)                       │
│                                                              │
│  종합점수_v2 = 거리 + 날씨 + 영양 + 팀선호 + 감성(0.15~0.20)   │
│                                                              │
│         ↓                              ↓                    │
│  React 대시보드 (확장)          ChatBOT/ (RAG 고도화)          │
└──────────────────────────────────────────────────────────────┘
```

### ChatBOT/ 과의 차이

ChatBOT/ 은 "**Ollama 를 호출해서 함수를 실행하는 프레임워크**"에 집중하고,
NLP/ 는 "**언어 자체를 이해하고 생성하는 모델 계층**"을 다룹니다.

| 영역 | ChatBOT/ | NLP/ |
|------|---------|------|
| 초점 | Function Calling / Tool Use | 감성·NER·RAG·NLG |
| 모델 | Ollama (기성 LLM 그대로 호출) | Ollama + 파인튜닝 모델 (KcELECTRA, KoELECTRA, Sentence-BERT) |
| 데이터 | 사용자 발화 + 내부 DB | 리뷰·메뉴명·SNS 텍스트 |
| 평가 | 대화 품질, Intent 정확도 | F1, NDCG, ROUGE, 만족도 |
| 산출 | 대화 시스템 | 학습된 모델 + 자연어 파이프라인 |

**두 레이어는 서로 보완적**이며, 최종 통합 MVP 에서는 NLP/ 의 모델이
ChatBOT/ 의 함수 호출에 주입되는 구조가 됩니다.

---

## 4. 두 가지 시나리오 개요

본 폴더는 **2개의 시나리오**를 제공하며, 목적에 따라 선택하거나 순차 진행할 수 있습니다.

### 🚀 시나리오 3 — MVP (실용·빠른 출시)

> **"4주 안에 사용자가 체감할 수 있는 NLP 기능 4종을 붙인다."**

- **기간:** 4주
- **난이도:** ⭐⭐⭐
- **GPU:** 불필요 (추론만)
- **라벨링:** 거의 없음 (Zero-shot 활용)
- **산출물:** 작동하는 MVP + 확장된 대시보드
- **대상 독자:** 빠른 데모·포트폴리오·실사용 체험이 필요한 경우

**포함 모듈:**

| ID | 이름 | 요약 |
|----|------|------|
| **A1** | 리뷰 감성분석 (Zero-shot) | KcELECTRA 사전학습 모델로 리뷰 → 평점 보정 |
| **B1** | 메뉴명 정규화 | 규칙 + Levenshtein + Sentence-BERT 하이브리드 |
| **D3** | RAG 영양 상담 챗봇 | ChromaDB + Ollama Qwen2.5 로 개인화 대화 |
| **D5** | NLG 주간 영양 리포트 | 수치 → 친근한 한국어 코멘트 자동 생성 |

📄 **상세 가이드:** [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md)

---

### 🔬 시나리오 2 — 연구/심화 (파인튜닝·평가·논문 지향)

> **"MVP 위에 자체 학습 모델 5종을 얹어 NLP 풀스택 역량을 증명한다."**

- **기간:** 10주
- **난이도:** ⭐⭐⭐⭐
- **GPU:** 필수 (파인튜닝)
- **라벨링:** 약 3,500건 직접 작업
- **산출물:** 학습 모델 5종 + 벤치마크 리포트 + 논문 초안
- **대상 독자:** 졸업 프로젝트·연구·ML 엔지니어 트랙

**포함 모듈:**

| ID | 이름 | 요약 |
|----|------|------|
| **A2** | ABSA (속성별 감성분석) | 맛/가격/서비스/청결 4축 분리 평가 |
| **B2** | Food NER | 재료·조리법·맛·알레르겐 개체 인식 |
| **D1** | Intent Classifier | DistilKoBERT 파인튜닝, Ollama 대비 벤치마크 |
| **D2** | Slot Filling | JointBERT 방식 (Intent + Slot 통합) |
| **E1** | 임베딩 기반 개인화 CF | Sentence-BERT + FAISS 로 유사 사용자 추천 |

📄 **상세 가이드:** [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md)

---

### 시나리오 비교표

| 항목 | 시나리오 3 (MVP) | 시나리오 2 (연구) |
|------|-----------------|-----------------|
| **목표** | 사용자 체감 기능 출시 | NLP 풀스택 역량 증명 |
| **기간** | 4주 | 10주 |
| **난이도** | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **GPU 필요성** | ❌ 불필요 | ✅ 필수 |
| **데이터 라벨링** | 최소 | 3,500건 |
| **기본 접근** | Zero-shot + 로컬 LLM | 파인튜닝 + 임베딩 |
| **모듈 수** | 4개 (A1, B1, D3, D5) | 5개 (A2, B2, D1, D2, E1) |
| **평가 중심** | 사용자 만족도 | F1, NDCG, Accuracy |
| **산출물** | MVP v1.0 | 모델 5종 + 논문 초안 |
| **트랙** | 풀스택 / 제품 | ML 엔지니어 / 연구 |

---

## 5. 진행 순서 권장안

### ✅ 권장: 시나리오 3 → 시나리오 2 순차 진행

```
Week 1-4   │ 시나리오 3 (MVP) 완성
           │ └─ 작동하는 시스템 확보, 초기 사용자 피드백
           │
Week 5-6   │ A1 → A2 교체 (ABSA 파인튜닝)
           │ └─ 맛/가격/서비스/청결 속성별 분석
           │
Week 7     │ B1 → B2 추가 (Food NER)
           │ └─ 재료·알레르겐 인식
           │
Week 8-9   │ D3 → D1 + D2 결합 (JointBERT)
           │ └─ Ollama 대비 속도/정확도 벤치마크
           │
Week 10    │ E1 개인화 CF 통합
           │ └─ 임베딩 기반 사용자 유사도 추천
```

### 이 순서의 장점

1. **항상 동작하는 시스템** — MVP 가 기준점이 되어, 연구형 모델이 실패해도 롤백 가능
2. **Before/After 비교** — 동일 인터페이스에서 MVP 대비 성능 향상을 수치로 증명 → 논문 소재
3. **라벨링 데이터 확보 용이** — MVP 로 수집된 리뷰·대화 로그가 시나리오 2 학습 데이터로 전환
4. **위험 분산** — 초기 4주에 가시적 성과를 내고, 이후 심화 연구에 집중

### 시나리오 교체 매핑

| MVP (시나리오 3) | → | 연구형 (시나리오 2) | 교체 효과 |
|------|---|------|---------|
| A1 Zero-shot | → | A2 ABSA 파인튜닝 | 속성별 세밀한 분석 |
| B1 규칙/임베딩 | → | B2 Food NER 추가 | 재료·알레르겐 인식 |
| D3 RAG 챗봇 | → | D1+D2 JointBERT | 경량·고속 NLU |
| D5 NLG 리포트 | → | E1 개인화 CF 연결 | 리포트 내 개인 추천 |

---

## 6. 모듈 매핑 표

NLP 모듈이 **기존 Mini 서브토픽과 어떻게 연결되는지** 한눈에 정리합니다.

| Mini 서브토픽 | 관련 NLP 모듈 | 연결 방식 | 기대 효과 |
|----------------|-------------|----------|----------|
| **1. 음식점 수집** (GUIDE/Subtopic 1) | A1 감성분석 / A2 ABSA | `restaurants` 테이블에 `sentiment_score` 컬럼 추가 | 평점 신뢰도 보정, 랭킹 품질↑ |
| **2. 날씨 추천** (GUIDE/Subtopic 2) | (직접 연관 없음) | — | — |
| **3. 영양 분석** (GUIDE/Subtopic 3) | B1 메뉴 정규화 / B2 Food NER | `meal_history.menu` ↔ `nutrition_info` 조인 | 조인율 40% → 85%, 재료 기반 필터 |
| **3. 영양 분석** (리포트) | D5 NLG 리포트 | `nutrition_reports` 신규 테이블 | 수치 → 자연어 코멘트 |
| **4. 팀 투표** (GUIDE/Subtopic 4) | E1 임베딩 CF | 사용자 임베딩 기반 유사도 | 팀 선호 예측 고도화 |
| **ChatBOT 전체** (ChatBOT/Phase1~4) | D1 Intent / D2 Slot / D3 RAG | Ollama 대체 또는 보강 | NLU 정확도·속도↑ |

---

## 7. 파이프라인 통합 지점

NLP 결과는 다음 세 지점에서 기존 Mini 파이프라인에 병합됩니다.

### (1) 스코어링 엔진 v2

기존 공식을 유지하되, **감성 점수를 추가**합니다.

```
# 기존 (v1)
종합점수 = 거리(0.3) + 날씨(0.2) + 영양(0.2) + 팀선호(0.3)

# NLP 추가 (v2)
종합점수 = 거리(0.25) + 날씨(0.15) + 영양(0.15) + 팀선호(0.25) + 감성(0.20)
```

또는 기존 공식을 유지한 채 **곱 보정** 방식도 제공 (A/B 선택):

```
종합점수_v2 = 종합점수_v1 × (1 + 0.15 × sentiment_score)
```

### (2) DB 스키마 확장

| 테이블 | 신규 컬럼/테이블 | 도입 시점 | 용도 |
|--------|---------------|----------|------|
| `restaurants` | `sentiment_score` REAL | 시나리오 3 (A1) | A1/A2 감성 결과 |
| `restaurants` | `sentiment_pos_ratio`, `sentiment_neg_ratio`, `sentiment_sample_size` | 시나리오 3 (A1) | 감성 분포 |
| `restaurants` | `extracted_allergens` JSON | 시나리오 2 (B2) | Food NER 추출 알레르겐 |
| `reviews` (신규) | id, restaurant_id, source, text, sentiment_label, sentiment_confidence | 시나리오 3 (A1) | 리뷰 원문·분석 결과 |
| `meal_history` | `normalized_menu_id` TEXT | 시나리오 3 (B1) | B1/B2 정규화 메뉴 |
| `menu_normalization` (신규) | raw_name, normalized_id, confidence, method, updated_at | 시나리오 3 (B1) | 정규화 캐시 |
| `nutrition_reports` (신규) | id, user_id, week_start, facts JSON, nlg_text | 시나리오 3 (D5) | D5 NLG 리포트 |
| `chatbot_sessions` (신규) | id, user_id, messages JSON, created_at | 시나리오 3 (D3) | D3 대화 이력 |
| `ab_test_logs` (신규) | request_id, endpoint, version, latency_ms, timestamp, user_id | 시나리오 2 (Step 5) | MVP vs Research A/B 테스트 로그 |

### (3) API 엔드포인트 확장

| 엔드포인트 | 모듈 | 설명 |
|-----------|------|------|
| `GET  /nlp/sentiment/{restaurant_id}` | A1/A2 | 식당 감성 점수 조회 |
| `POST /nlp/sentiment/refresh` | A1/A2 | 감성 파이프라인 실행 |
| `POST /nlp/menu/normalize` | B1/B2 | 원시 메뉴명 → 표준 ID |
| `POST /nlp/chatbot/chat` | D3 | RAG 챗봇 대화 |
| `GET  /nlp/reports/weekly/{user_id}` | D5 | 주간 NLG 리포트 |

---

## 8. 폴더 구조

### 현재 (문서만 존재)

```
NLP/
├── README.md                              ← 본 문서
├── GUIDE_NLP_MVP_SCENARIO3.md             ← 시나리오 3 상세 가이드
└── GUIDE_NLP_RESEARCH_SCENARIO2.md        ← 시나리오 2 상세 가이드
```

### 시나리오 3 구현 후 (Claude Code 결과물)

```
NLP/
├── README.md
├── GUIDE_NLP_MVP_SCENARIO3.md
├── GUIDE_NLP_RESEARCH_SCENARIO2.md
└── nlp_mvp/                               ← 시나리오 3 구현물
    ├── README.md
    ├── requirements.txt
    ├── .env.example
    ├── shared/                            # 공용 유틸
    │   ├── db.py
    │   ├── ollama_client.py
    │   └── logger.py
    ├── sentiment/                         # 🔹 A1
    │   ├── crawler.py
    │   ├── preprocess.py
    │   ├── sentiment_pipeline.py
    │   ├── update_db.py
    │   └── tests/
    ├── menu_normalizer/                   # 🔹 B1
    │   ├── rules.py
    │   ├── synonym_dict.json
    │   ├── embedding_matcher.py
    │   ├── normalizer.py
    │   └── evaluate.py
    ├── rag_chatbot/                       # 🔹 D3
    │   ├── indexer.py
    │   ├── retriever.py
    │   ├── prompt_templates.py
    │   ├── chatbot.py
    │   ├── streamlit_app.py
    │   └── chroma_store/                  # .gitignore
    ├── nlg_report/                        # 🔹 D5
    │   ├── fact_extractor.py
    │   ├── prompt.py
    │   └── generator.py
    ├── api/                               # FastAPI 서빙
    │   ├── main.py
    │   └── routers/
    ├── integration/                       # Mini 스코어링 통합
    │   └── scoring_patch.py
    ├── notebooks/                         # EDA / 실험
    │   ├── 01_sentiment_eda.ipynb
    │   ├── 02_menu_normalizer_eval.ipynb
    │   ├── 03_rag_tuning.ipynb
    │   └── 04_nlg_samples.ipynb
    ├── evaluate_all.py
    └── benchmark.py
```

### 시나리오 2 구현 후 (추가분)

```
NLP/
└── nlp_research/                          ← 시나리오 2 구현물
    ├── data/
    │   ├── raw/
    │   ├── labeled/
    │   └── augmented/
    ├── models/
    │   ├── absa/                          # 🔬 A2
    │   ├── food_ner/                      # 🔬 B2
    │   ├── joint_bert/                    # 🔬 D1 + D2
    │   └── embedding_cf/                  # 🔬 E1
    ├── configs/                           # 학습 하이퍼파라미터
    ├── training/                          # 학습 스크립트
    ├── evaluation/                        # 모델 평가
    └── report/                            # 논문·벤치마크 문서
```

---

## 9. 문서 네비게이션

### 시작 순서

**새로 들어온 사람 / 처음 보는 경우:**
```
1. Mini/0README.md         → 전체 프로젝트 이해
2. Mini/README.md           → 상세 기획
3. Mini/NLP/README.md       → 본 문서 (NLP 레이어 개요)
4. Mini/NLP/GUIDE_NLP_MVP_SCENARIO3.md  → 시나리오 3 구현
```

**이미 Mini 을 알고 있고 NLP 를 추가하려는 경우:**
```
1. Mini/NLP/README.md                     → 본 문서
2. Mini/NLP/GUIDE_NLP_MVP_SCENARIO3.md    → 시나리오 3 착수
```

**연구·논문 목적인 경우:**
```
1. Mini/NLP/README.md
2. Mini/NLP/GUIDE_NLP_MVP_SCENARIO3.md    → 4주 MVP
3. Mini/NLP/GUIDE_NLP_RESEARCH_SCENARIO2.md  → 10주 연구
```

### 관련 문서 링크

| 문서 | 위치 | 설명 |
|------|------|------|
| 전체 개요 | `Mini/0README.md` | 프로젝트 전체 소개 |
| 상세 기획서 | `Mini/README.md` | 트렌드·데이터·알고리즘 상세 |
| 음식점 수집 | `Mini/GUIDE/GUIDE_SUBTOPIC_1_RESTAURANT_COLLECTOR.md` | 카카오맵 연동 |
| 날씨 추천 | `Mini/GUIDE/GUIDE_SUBTOPIC_2_WEATHER_RECOMMENDATION.md` | 기상청 연동 |
| 영양 분석 | `Mini/GUIDE/GUIDE_SUBTOPIC_3_NUTRITION_ANALYSIS.md` | 식약처 연동 |
| 팀 투표 | `Mini/GUIDE/GUIDE_SUBTOPIC_4_TEAM_VOTING.md` | 투표·통합 엔진 |
| 챗봇 통합 | `Mini/ChatBOT/GUIDE_CHATBOT_INTEGRATION.md` | Ollama 기반 대화형 |
| **NLP MVP (전체)** | `Mini/NLP/GUIDE_NLP_MVP_SCENARIO3.md` | **본 폴더 — 4주 요약** |
| **NLP MVP (Step 1 상세)** | `Mini/NLP/GUIDE_NLP_MVP_STEP1_SENTIMENT.md` | **1주차 A1 감성분석 심화** |
| **NLP MVP (Step 2 상세)** | `Mini/NLP/GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md` | **2주차 B1 메뉴 정규화 심화** |
| **NLP MVP (Step 3 상세)** | `Mini/NLP/GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md` | **3주차 D3 RAG 챗봇 심화** |
| **NLP MVP (Step 4 상세)** | `Mini/NLP/GUIDE_NLP_MVP_STEP4_NLG_REPORT.md` | **4주차 D5 NLG 리포트 심화** |
| **NLP Research** | `Mini/NLP/GUIDE_NLP_RESEARCH_SCENARIO2.md` | 10주 연구 가이드 |

---

## 10. 시작하기

### 10.1 사전 조건

아래 중 **최소 하나**는 완료되어 있어야 합니다:

- ✅ **추천:** 기존 Mini 파이프라인 (GUIDE/ 의 서브토픽 1~4) 이 일부라도 구현되어 있음
- 🆗 **최소:** Mini DB 스키마(SQLite)와 시드 데이터가 존재함
- 🧪 **완전 처음:** `lunch-optimizer-dashboard.jsx` 의 mock 데이터만으로도 진행 가능

### 10.2 환경 준비 (공통)

```bash
# 1. Python 가상환경
cd Mini
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. NLP 의존성 설치 (시나리오 3 기준)
pip install transformers==4.44.0 torch sentence-transformers==3.0.1 \
            chromadb==0.5.0 ollama==0.3.0 fastapi==0.112.0 \
            streamlit==1.37.0 sqlalchemy==2.0.32

# 3. Ollama 설치 및 모델 다운로드
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5:7b-instruct

# 4. 환경 변수
cp NLP/.env.example NLP/.env
# .env 편집
```

### 10.3 시나리오 3 첫 단계 (Quick Start)

```bash
# NLP 폴더로 이동
cd Mini/NLP

# 가이드 문서 읽기
less GUIDE_NLP_MVP_SCENARIO3.md

# Step 1 (A1 감성분석) 의 Claude Code 프롬프트를 그대로 실행
# → nlp_mvp/sentiment/ 모듈 자동 생성
```

자세한 단계는 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) 참고.

---

## 11. FAQ

**Q1. 기존 Mini 파이프라인이 없어도 NLP 레이어만 독립 실행할 수 있나요?**
A. 가능합니다. 시나리오 3 의 A1 과 D5 는 외부 리뷰 데이터 + 가상 사용자 이력만 있으면
   독립 동작합니다. 단, 효과를 제대로 보려면 Mini DB 스키마가 있는 편이 좋습니다.

**Q2. ChatBOT/ 폴더와 중복되지 않나요?**
A. 아닙니다. ChatBOT/ 은 Ollama 호출 프레임워크 · 함수 호출 구조에 집중하고,
   NLP/ 는 언어 모델 자체 (감성·NER·RAG·NLG) 에 집중합니다.
   최종 통합 시 NLP/ 의 모델이 ChatBOT/ 의 Tool 로 주입됩니다.

**Q3. GPU 없이도 시나리오 2를 진행할 수 있나요?**
A. 제한적으로 가능합니다. 작은 모델(DistilKoBERT 등)은 CPU 파인튜닝이 가능하나
   학습 속도가 수십 배 느립니다. 시나리오 2 는 Google Colab Pro 또는 런팟(runpod) 등
   클라우드 GPU 를 권장합니다.

**Q4. 리뷰 크롤링이 법적으로 안전한가요?**
A. 카카오·네이버 리뷰는 저작권 및 ToS 대상입니다. 본 가이드는 **학습·연구 목적의
   공개 데이터 수집만** 다루며, 상업적 재배포는 금지됩니다. 실 서비스 배포 시
   공식 파트너 API 계약이 필요합니다.

**Q5. 시나리오 3 만 하고 멈춰도 되나요?**
A. 네. 시나리오 3 자체가 완결된 MVP 입니다. 포트폴리오·실사용·시연 목적이라면
   시나리오 3 만으로도 충분한 가치를 지닙니다. 시나리오 2 는 ML 엔지니어 · 연구자
   트랙을 원할 때만 추가하세요.

**Q6. 한국어가 아닌 다른 언어 지원은 가능한가요?**
A. 본 가이드는 한국어 특화 모델 (KcELECTRA, ko-sroberta, Ollama 한국어 모델) 기반입니다.
   다국어 지원을 원하면 `xlm-roberta-base`, `NLLB-200` 등으로 교체 가능하나
   별도 작업이 필요합니다.

**Q7. 시나리오 3 MVP 완성 후 시나리오 2 로 갈아탈 때, 기존 코드는 버리나요?**
A. 아닙니다. 시나리오 3 코드는 **fallback·A/B 비교용**으로 유지합니다.
   동일 FastAPI 엔드포인트를 유지한 채 내부 구현만 교체하며,
   두 버전의 성능을 비교하는 것 자체가 시나리오 2 의 논문 소재가 됩니다.

**Q8. 진행 중 막히면 어떻게 도움을 받을 수 있나요?**
A. 각 가이드 문서의 **"트러블슈팅"** 섹션에 주요 오류 사례와 해결책이 정리되어
   있습니다. 그 외의 경우 프로젝트 Issues 탭이나 Claude Code 에게 직접 질문하세요.

---

## 🗺️ 전체 로드맵 속 NLP 레이어 위치

```
Phase 1 ✅  │ MVP 대시보드 (React + Mock)              ─ 완료
Phase 2 🔄  │ 4개 공공 API 실연동 + SQLite              ─ GUIDE/
Phase 3 🔄  │ 사용자 로그인 · 개인화 · 슬랙봇            ─ ChatBOT/
Phase 4 🔄  │ Docker · CI/CD · 배포                    ─ ChatBOT/Phase4
Phase 5 🆕  │ NLP 레이어 — 시나리오 3 (MVP, 4주)         ─ NLP/ ← 현재
Phase 6 🆕  │ NLP 레이어 — 시나리오 2 (연구, 10주)        ─ NLP/
```

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**대상:** Mini NLP 레이어 착수자
**후속 문서:**
- [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) — 시나리오 3 상세 구현 가이드
- [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) — 시나리오 2 상세 구현 가이드

---

<div align="center">

**🧠 언어의 힘으로 점심 추천을 한 단계 더 깊게.**

*Mini × NLP — From Numbers to Narratives.*

</div>
