# 🧠 nlp_mvp — Mini NLP 레이어 (시나리오 3 MVP)

> **4주 안에 체감 가능한 NLP 기능 4종을 얹는 MVP 구현체**
>
> 본 폴더는 [`GUIDE_NLP_MVP_SCENARIO3.md`](../GUIDE_NLP_MVP_SCENARIO3.md) 에 정의된
> 시나리오 3 의 **실제 코드 스켈레톤**입니다. 각 파일은 비어있는 상태로 생성되어 있으며,
> 가이드의 Claude Code 프롬프트를 순서대로 실행하면서 채워나가는 것을 전제로 합니다.

---

## 🗂️ 모듈 구성

| 폴더 | ID | 역할 |
|------|----|----|
| `sentiment/` | **A1** | 리뷰 감성분석 (KcELECTRA Zero-shot) |
| `menu_normalizer/` | **B1** | 메뉴명 정규화 (규칙 + Levenshtein + Sentence-BERT) |
| `rag_chatbot/` | **D3** | RAG 기반 영양 상담 챗봇 (ChromaDB + Ollama) |
| `nlg_report/` | **D5** | NLG 주간 영양 리포트 (팩트 추출 + LLM) |
| `shared/` | 공용 | DB, Ollama 클라이언트, 로거 |
| `api/` | 서빙 | FastAPI 엔드포인트 (`/nlp/*`) |
| `integration/` | 통합 | Mini 스코어링 엔진 v2 보정 |
| `notebooks/` | EDA | 실험·평가·튜닝 노트북 |

---

## 🚀 시작하기

```bash
# 1. Mini/NLP 디렉토리로 이동
cd Mini/NLP

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r nlp_mvp/requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 편집: OLLAMA_HOST, MINI_DB_PATH 등

# 5. Ollama 준비
ollama serve &
ollama pull qwen2.5:7b-instruct

# 6. 구현 시작 — 가이드 문서의 Step 1 부터 순서대로
less ../GUIDE_NLP_MVP_SCENARIO3.md

# 7. (Step 5 완료 후) NLP API 서버 기동 — 포트 8001
cd ..           # Mini/
uvicorn nlp_mvp.api.main:app --reload --port 8001
curl http://localhost:8001/nlp/health
```

### Step 5 통합 레이어 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET  | `/nlp/health` | 모듈별 준비 상태 |
| GET  | `/nlp/sentiment/top?limit=10&order=desc` | 감성 랭킹 |
| GET  | `/nlp/sentiment/{restaurant_id}` | 식당별 감성 점수 |
| POST | `/nlp/sentiment/refresh` | 감성 파이프라인 비동기 실행 |
| POST | `/nlp/menu/normalize` | 메뉴명 정규화 |
| GET  | `/nlp/menu/stats` | 메서드별 히트율 |
| POST | `/nlp/chatbot/chat` | RAG 영양 상담 |
| POST | `/nlp/chatbot/reset` | 대화 이력 초기화 |
| GET  | `/nlp/chatbot/stats` | 챗봇 통계 |
| GET  | `/nlp/reports/weekly/{user_id}` | 주간 리포트 조회/생성 |
| POST | `/nlp/reports/weekly/{user_id}/regenerate` | 리포트 강제 재생성 |

---

## 📋 구현 순서 (4주)

| 주차 | 모듈 | 상태 |
|------|------|------|
| 1주 | A1 Sentiment (KcELECTRA) | ✅ |
| 2주 | B1 Menu Normalizer (rule + Lev + SBERT) | ✅ |
| 3주 | D3 RAG Chatbot (Chroma + Ollama) | ✅ |
| 4주 | D5 NLG Report (주간 리포트) | ✅ |
| Step 5 | FastAPI `/nlp/*` 11종 + 스코어링 v2 보정 | ✅ |
| Phase 5.5 (M1~M10) | Next.js 16 프런트엔드 마이그레이션 | ✅ |

상세 체크리스트는 [`../GUIDE_NLP_MVP_SCENARIO3.md`](../GUIDE_NLP_MVP_SCENARIO3.md) §12, Phase 5.5는 [`../../dashboard-web/README.md`](../../dashboard-web/README.md) 참고.

---

## 🧪 테스트 실행

```bash
# Mini/NLP 에서
pytest nlp_mvp/ -v --tb=short
```

## 🌐 서비스 실행

```bash
# FastAPI 서버
uvicorn nlp_mvp.api.main:app --reload --port 8001

# Streamlit 챗봇 데모
streamlit run nlp_mvp/rag_chatbot/streamlit_app.py
```

---

## 📎 관련 문서

- **상위 진입점:** [`../README.md`](../README.md)
- **시나리오 3 상세 가이드:** [`../GUIDE_NLP_MVP_SCENARIO3.md`](../GUIDE_NLP_MVP_SCENARIO3.md)
- **시나리오 2 (후속):** [`../GUIDE_NLP_RESEARCH_SCENARIO2.md`](../GUIDE_NLP_RESEARCH_SCENARIO2.md)
- **Mini 전체:** [`../../0README.md`](../../0README.md)
