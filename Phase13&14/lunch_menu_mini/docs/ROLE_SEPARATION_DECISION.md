# Mini 역할 분리 결정 기록 (NLP vs ChatBOT)

> **결정일:** 2026-04-08
> **결정 사항:** NLP 레이어를 프로젝트의 **메인 대화·언어처리 축**으로 채택.
> ChatBOT 은 **선택적 추가 기능**으로, 구현 시 **React 만** 사용 (Streamlit 제외).

---

## 1. 배경

Mini 에는 자연어 인터페이스를 위한 두 갈래의 가이드가 존재한다:

| 갈래 | 위치 | 특징 |
|---|---|---|
| **NLP** | `Mini/NLP/` | 한국어 NLP 풀스택 (감성분석·메뉴 정규화·RAG 챗봇·NLG) |
| **ChatBOT** | `Mini/ChatBOT/` | Ollama + Function Calling 기반 대화형 챗봇 (Phase 1~4) |

두 경로는 특히 "RAG 기반 챗봇" 영역에서 **기능이 겹친다**:

- **NLP/Step 3 (D3 RAG 챗봇)**: ChromaDB + 벡터 검색 + Ollama
- **ChatBOT/Phase 2 (Tool Functions)**: 8개 Tool + Function Calling + Ollama

---

## 2. 결정 근거

NLP 를 메인으로 선택한 이유:

1. **프로젝트 학습 가치** — NLP MVP 는 감성분석(A1)·메뉴 정규화(B1)·NLG 리포트(D5)
   까지 포함하여 **한국어 자연어 처리 전 영역**을 다룸.
2. **연구·심화 확장성** — 시나리오 2 (Phase 6) 에서 ABSA·Food NER·JointBERT·임베딩 CF
   까지 이어지는 **모델 파인튜닝 경로** 가 이미 설계되어 있음.
3. **Step 0 공용 유틸 완성** — `NLP/nlp_mvp/shared/` 의 `db.py` · `logger.py` ·
   `ollama_client.py` 가 이미 구현 완료되어 **즉시 착수 가능**.
4. **벡터 검색의 일반성** — RAG 패턴은 Function Calling 보다 더 범용적으로 다양한
   데이터 (리뷰·영양 DB·식당 카드) 를 하나의 임베딩 공간에 넣을 수 있음.

ChatBOT 을 완전히 폐기하지 않고 **선택적 추가 기능** 으로 남긴 이유:

1. **Function Calling 패턴의 실용성** — NLP RAG 가 "정보 조회" 에 강한 반면,
   ChatBOT Tool Functions 는 **"행동 실행"** (투표·식사 기록·거부권) 에 강함.
2. **lunch-optimizer 의 28개 엔드포인트를 직접 래핑** 할 수 있는 유일한 경로.
3. **운영 배포 (Phase 4 Docker)** 는 lunch-optimizer 단독으로도 가치 있는 산출물.

---

## 3. 최종 구조

```
Mini/
├── lunch-optimizer/        ✅ 데이터 파이프라인 (Subtopic 1~4 완료)
│   ├── api/                ← 28 FastAPI 엔드포인트
│   ├── database/           ← SQLite 스키마 + 시드
│   ├── engine/recommender.py ← 4축 통합 추천
│   └── ...
│
├── NLP/                    🎯 MAIN — 메인 언어 처리 축
│   ├── nlp_mvp/shared/     ✅ Step 0 공용 유틸 완료
│   ├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md     ← A1 착수 대기
│   ├── GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md ← B1
│   ├── GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md   ← D3 (메인 챗봇)
│   ├── GUIDE_NLP_MVP_STEP4_NLG_REPORT.md    ← D5
│   └── GUIDE_NLP_RESEARCH_SCENARIO2.md      ← 연구 심화
│
└── ChatBOT/                ⚡ 선택적 추가 기능 (Function Calling)
    ├── GUIDE_CHATBOT_INTEGRATION.md         ← 참고용 (전체 아키텍처)
    ├── GUIDE_PHASE1_CHATBOT_IMPLEMENTATION.md ⚠️ React 경로만 사용
    ├── GUIDE_PHASE2_TOOL_FUNCTIONS.md       ← Function Calling (NLP 보완)
    ├── GUIDE_PHASE3_MULTITURN_PERSONALIZATION.md
    └── GUIDE_PHASE4_DOCKER_DEPLOYMENT.md    ← 운영 배포 (독립 가치)
```

---

## 4. 역할 분담 상세

| 기능 영역 | NLP | ChatBOT |
|---|---|---|
| **감성분석 (리뷰 → 평점 보정)** | ✅ A1 Zero-shot → A2 ABSA | ❌ 범위 외 |
| **메뉴 정규화** | ✅ B1 (규칙+Levenshtein+임베딩) | ❌ 범위 외 |
| **정보 조회 챗봇** | ✅ D3 RAG (ChromaDB + Ollama) | ⚡ 보조 (Function Calling) |
| **행동 실행 (투표/기록)** | ❌ 범위 외 | ✅ Phase 2 Tool Functions |
| **NLG 리포트** | ✅ D5 (주간 영양 리포트) | ❌ 범위 외 |
| **멀티턴·개인화** | ⚠️ 기본 대화 이력만 | ✅ Phase 3 상태머신·선호학습 |
| **운영 배포** | ⚠️ 단독 배포 가이드 없음 | ✅ Phase 4 Docker Compose |

---

## 5. 구현 순서 권장

### 우선순위 1: NLP MVP Step 1~4 (4주)
- Step 1 — A1 감성분석
- Step 2 — B1 메뉴 정규화
- Step 3 — **D3 RAG 챗봇** (메인 대화형 인터페이스)
- Step 4 — D5 NLG 주간 리포트

### 우선순위 2 (선택): ChatBOT Phase 2 + React UI
- ChatBOT/Phase 1 의 **Track A (Streamlit) 는 건너뛰고**, **Track B (React + FastAPI) 만** 채택
- Phase 2 의 **8 Tool Functions** 를 lunch-optimizer 의 기존 엔드포인트에 직접 래핑
- React 대시보드 (`lunch-optimizer-dashboard.jsx`) 에 **"AI 상담" 탭** 을 추가하여
  NLP RAG 챗봇 + ChatBOT Tool 호출을 **하나의 UI 에서** 제공

### 우선순위 3 (선택): ChatBOT Phase 4 Docker 배포
- NLP + ChatBOT + lunch-optimizer 를 Docker Compose 로 통합 배포

---

## 6. Streamlit 경로 폐기 이유

- Mini 의 메인 프론트엔드는 `lunch-optimizer-dashboard.jsx` (React) 로 이미 구축됨
- Streamlit 은 **프로토타입용** 으로만 가치가 있으며, 이미 React 대시보드가 존재하므로 중복
- React 단일 경로로 통일하여 유지보수 단순화

**ChatBOT/GUIDE_PHASE1_CHATBOT_IMPLEMENTATION.md 의 "Track A (Streamlit)" 섹션은
참고용으로 보존** 하되 구현 대상 아님을 명시.

---

## 7. UI 통합 방향

React 대시보드의 기존 5 탭:

| 탭 | 데이터 소스 |
|---|---|
| 🍽️ 음식점 탐색 | Mock (기존) |
| 🌤️ 날씨 추천 | Mock (기존) |
| 📊 영양 리포트 | Mock (기존) |
| 🗳️ 팀 투표 | Mock (기존) |
| 🎯 AI 추천 | ✅ 실 FastAPI `/api/recommend` (이전 턴에서 연결) |

**향후 추가할 탭 (NLP + ChatBOT 완성 후):**

| 탭 | 데이터 소스 | 구현 |
|---|---|---|
| 💬 AI 상담 | NLP/D3 RAG + ChatBOT Phase2 Tool | Streamlit 대신 React chat UI |

---

## 8. 결정 요약

> **NLP = 메인, ChatBOT = 선택적 추가 + React 전용**

이 결정은 다음 작업의 방향성을 결정짓는다:

- ✅ 다음 우선 작업: **NLP MVP Step 1 (A1 감성분석)** 착수
- ⚡ 선택적 후속 작업: ChatBOT Phase 2 (Tool Functions) 를 React chat 컴포넌트로 구현
- ❌ 명시적 폐기: Streamlit 경로 (Phase 1 Track A)

---

**문서 버전:** v1.0
**작성일:** 2026-04-08
**관련 문서:**
- `Mini/NLP/README.md` (NLP 레이어 진입점)
- `Mini/ChatBOT/GUIDE_CHATBOT_INTEGRATION.md` (ChatBOT 전체 계획)
- `Mini/lunch-optimizer/PHASE0_DECISIONS.md` (Phase 0 결정)
- `Mini/0README.md` (로드맵)
