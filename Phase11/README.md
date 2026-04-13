# 💪 헬창지피티 (HelChangGPT)

### AI가 설계하는 나만의 피트니스 라이프 코치

> **LLM 및 자연어 처리 기반 실무 서비스 구현 — 미니프로젝트**  
> K-Digital Training 빅데이터 분석가 교육과정 | 자연어처리 과목 12기

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기획 의도 및 기대 효과](#2-기획-의도-및-기대-효과)
3. [트렌드 조사 및 분석](#3-트렌드-조사-및-분석)
4. [파이프라인 설계 (기승전결)](#4-파이프라인-설계-기승전결)
5. [수집 데이터 및 활용 모델](#5-수집-데이터-및-활용-모델)
6. [기술 스택](#6-기술-스택)
7. [UI 화면 구성](#7-ui-화면-구성)
8. [파라미터 튜닝 계획](#8-파라미터-튜닝-계획)
9. [프로젝트 구조](#9-프로젝트-구조)
10. [실행 방법](#10-실행-방법)
11. [팀 구성 및 역할](#11-팀-구성-및-역할)
12. [참고 자료](#12-참고-자료)

---

## 1. 프로젝트 개요

**헬창지피티(HelChangGPT)** 는 운동과 건강 관리에 관심이 있지만 전문 지식이 부족한 일반 사용자를 위한 **자연어 기반 맞춤형 피트니스 토탈 코칭 서비스**입니다.

사용자가 자연어로 신체 정보와 운동 목표를 입력하면, **4단계 NLP 파이프라인**을 통해 프로필 분석 → 식단 생성 → 운동 루틴 설계 → 동기부여 피드백까지 하나의 일관된 흐름으로 제공합니다.

```
"25세 남성, 178cm 82kg이에요. 체지방을 줄이고 근육을 늘리고 싶어요. 운동은 주 3회 가능합니다."
```

위와 같은 한 문장의 입력으로, AI가 개인 맞춤형 식단과 운동 계획을 설계하고, 운동 일지의 감성까지 분석하여 코칭 메시지를 생성합니다.

### 주제 선정 이유

| 구분 | 내용 |
|------|------|
| **시의성** | 2025~2026년 건강관리 트렌드에서 '근력운동 루틴', '체지방률 기준 건강관리' 검색이 급증하며 피트니스 AI 수요 폭발 |
| **NLP 적합성** | 텍스트 분류, NER, 키워드 추출, 텍스트 생성, 감성 분석, 요약, 검색 등 거의 모든 NLP 기법을 하나의 서비스에서 자연스럽게 활용 가능 |
| **재미 요소** | '헬창' + 'GPT'의 조합으로 MZ세대에 친숙한 네이밍, 팀원 모두가 공감 가능한 일상적 주제 |
| **교육적 가치** | 복수 NLP 기법을 하나의 파이프라인으로 통합 설계하는 실무 경험 |

---

## 2. 기획 의도 및 기대 효과

### 기획 의도

현재 AI 피트니스 앱들은 대부분 **식단 기록** 또는 **운동 추천** 중 하나에만 특화되어 있습니다. 본 프로젝트는 이를 통합하여 **'목표 설정 → 식단 → 운동 → 피드백'** 이라는 하나의 일관된 파이프라인을 구축하고, 각 단계에서 서로 다른 NLP 기법과 LLM을 비교·분석하는 것을 목표로 합니다.

### 도출할 인사이트

- LLM(EXAONE, OpenAI) 및 NLP 모델의 피트니스 도메인 적용 시 성능 차이 분석
- `temperature`, `top_p` 등 파라미터 조정에 따른 식단/운동 추천 품질 변화 분석
- 텍스트 분류(목표 설정), 텍스트 생성(식단/운동), 감성 분석(피드백) 등 다양한 NLP 기법의 실무 적용 경험
- 프롬프트 엔지니어링을 통한 출력 품질 최적화 방법론 도출

### 활용 방안 및 기대 효과

| 구분 | 내용 |
|------|------|
| **목표 사용자** | 운동을 시작하고 싶지만 방법을 모르는 일반인, 식단과 운동을 함께 관리하고 싶은 헬스장 초보자 |
| **해결 문제** | 분산된 운동/식단 정보를 통합하여 개인 맞춤형 피트니스 라이프 코치 제공 |
| **기대 효과** | 사용자 맞춤형 경험 제공으로 운동 지속률 향상 및 NLP 파이프라인 설계 역량 강화 |
| **기술적 가치** | 복수 NLP 기법을 하나의 서비스로 통합하는 파이프라인 설계 경험 |

---

## 3. 트렌드 조사 및 분석

### 시장 환경

- 헬스케어 NLP 시장은 **2024년 45.82억 달러 → 2035년 230.3억 달러** (CAGR 15.81%)로 폭발적 성장 전망
- **환자 참여(Patient Engagement)** 분야가 가장 빠르게 성장하는 세그먼트로, 개인 건강 관리에 대한 AI 수요 급증
- AI 헬스케어 시장은 2030년까지 **1,817억 달러** 규모로 성장 예상 (CAGR 41.8%)

### 주요 트렌드

| 트렌드 | 설명 |
|--------|------|
| **초개인화 AI 코칭** | 사용자의 성향과 상태를 진단하고 데이터 기반 맞춤 솔루션을 제공하는 추세가 2026년 마케팅의 표준으로 자리잡는 중 |
| **저마찰 AI** | 사진만 찍으면 영양 데이터가 나오는 방식이 식단 관리 앱의 새로운 트렌드로 대두 |
| **AI 에이전트 확산** | AI 에이전트가 디지털 팀원처럼 기능하며 업무 및 의사결정을 지원하는 방향으로 발전 |
| **운동+식단 통합 관리** | 식단 기록, 운동 트래킹, 혈당 모니터링 등을 하나의 앱에서 통합 관리하는 웰니스 플랫폼 성장 |

### 관련 리서치 자료

- [MRFR — NLP in Healthcare & Life Science Market Report 2035](https://www.marketresearchfuture.com/reports/nlp-in-healthcare-life-science-market-33949)
- [ETRI — LLM 기반 헬스케어 AI 기술 동향](https://ettrends.etri.re.kr/ettrends/214/0905214005/)
- [Microsoft — 2026년 7대 AI 트렌드](https://news.microsoft.com/source/asia/2025/12/16/whats-next-in-ai-7-trends-to-watch-in-2026/?lang=ko)
- [헬스경향 — AI가 분석한 2025 한국인 건강관리 10대 트렌드](https://www.k-health.com/news/articleView.html?idxno=88142)
- [삼정KPMG — AI로 촉발된 헬스케어 산업의 대전환](https://assets.kpmg.com/content/dam/kpmg/kr/pdf/2024/insight/kpmg-korea-ai-healthcare-20240625.pdf)
- [오픈서베이 — 2026년 트렌드 전망](https://blog.opensurvey.co.kr/news/trendreport-2026-trend-1/)

---

## 4. 파이프라인 설계 (기승전결)

본 프로젝트는 **기승전결(起承轉結)** 구조의 4단계 파이프라인으로 설계되어, 각 단계가 자연스럽게 다음 단계로 연결됩니다.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  기(起)          │     │  승(承)          │     │  전(轉)          │     │  결(結)          │
│  나를 알자       │ ──▶ │  뭘 먹지?        │ ──▶ │  어떻게 운동하지? │ ──▶ │  잘 하고 있나?   │
│                 │     │                 │     │                 │     │                 │
│ 사용자 프로필    │     │ AI 식단 생성     │     │ 운동 루틴 생성   │     │ 감성 분석 &     │
│ 분석 & 목표 설정 │     │ & 영양소 분석    │     │ & 정보 검색      │     │ 동기부여 피드백  │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 소주제 1: 기(起) — 나를 알자

> 사용자의 자연어 입력에서 신체 정보와 운동 목표를 분석하여 프로필을 생성합니다.

- **입력**: 자연어 텍스트 (예: "25세 남성, 178cm 82kg, 체지방 줄이고 근육 늘리고 싶어요")
- **처리**:
  - **NER (개체명 인식)**: 나이, 성별, 키, 몸무게, 운동 빈도 추출
  - **텍스트 분류**: 목표 유형 분류 (근력 증가 / 체지방 감소 / 체력 향상 / 체중 관리)
  - **키워드 추출**: 핵심 운동 관련 키워드 추출
  - BMI, TDEE 등 기초 지표 자동 계산
- **출력**: 구조화된 사용자 프로필 (JSON)
- **활용 모델**: KoBERT, KcBERT, KeyBERT

### 소주제 2: 승(承) — 뭘 먹지?

> 1단계에서 분석한 사용자 프로필을 기반으로 목표에 맞는 맞춤형 식단을 생성합니다.

- **입력**: 사용자 프로필 (목표 칼로리, 탄단지 비율, 식이 제한 등)
- **처리**:
  - **LLM 기반 식단 생성**: EXAONE vs OpenAI 비교 분석
  - **영양소 키워드 추출**: 탄수화물, 단백질, 지방, 칼로리 등 자동 파싱
  - **식단 요약**: 생성된 식단의 핵심 영양 정보 요약 제공
  - `temperature` 조정에 따른 식단 다양성/정확성 비교 실험
- **출력**: 일일 식단표 + 영양소 분석 카드
- **활용 모델**: EXAONE 3.5, OpenAI GPT, mT5, BART

### 소주제 3: 전(轉) — 어떻게 운동하지?

> 사용자의 목표와 신체 조건에 맞는 운동 루틴을 생성하고, 운동 정보를 검색 기반으로 제공합니다.

- **입력**: 사용자 프로필 + 목표 유형 + 운동 가능 횟수
- **처리**:
  - **LLM 기반 운동 루틴 생성**: 부위별 운동, 세트/횟수/시간 설계
  - **임베딩 검색**: 운동 정보 문서 기반 유사도 검색 (sentence-transformers + FAISS)
  - **BM25 키워드 검색**: 운동명, 부위, 난이도 등 키워드 기반 검색
  - 검색 결과와 LLM 생성 결과 비교 분석
- **출력**: 요일별 운동 계획 + 운동 상세 정보
- **활용 모델**: EXAONE 3.5, OpenAI GPT, sentence-transformers, BM25

### 소주제 4: 결(結) — 잘 하고 있나?

> 사용자가 작성한 운동 일지를 분석하여 감성 상태를 파악하고, 개인화된 동기부여 피드백을 생성합니다.

- **입력**: 사용자 운동 일지 텍스트
- **처리**:
  - **감성 분석**: 운동 일지의 긍정/부정 감성 분석 (BERT 계열)
  - **텍스트 요약**: 주간 운동 기록 자동 요약
  - **LLM 기반 동기부여 피드백**: 감성 분석 결과를 반영한 맞춤 코칭 메시지 생성
    - 부정 감성 감지 시 → 격려 + 대안 운동 추천
    - 긍정 감성 감지 시 → 성취 칭찬 + 다음 목표 제시
- **출력**: 감성 분석 결과 + AI 동기부여 메시지
- **활용 모델**: KoBERT, KcBERT, mT5, BART, EXAONE 3.5, OpenAI GPT

---

## 5. 수집 데이터 및 활용 모델

### 수집할 데이터

| 단계 | 데이터 종류 | 형식 | 출처 |
|------|-----------|------|------|
| 기(起) | 사용자 입력 텍스트 샘플 (신체정보, 목표) | 텍스트 / JSON | 직접 작성 / 커뮤니티 수집 |
| 승(承) | 한국 음식 영양성분 데이터, 식단 레시피 | CSV / JSON | 식품의약품안전처, 공공데이터포털 |
| 전(轉) | 운동 정보 문서 (운동명, 부위, 방법, 세트수) | 텍스트 / JSON | ExRx.net, Muscle Wiki, 직접 작성 |
| 결(結) | 운동 일지 텍스트 샘플 (감성 표현 포함) | 텍스트 | 직접 작성 / 커뮤니티 수집 |

### 데이터 출처 상세

| 출처 | URL | 설명 |
|------|-----|------|
| 식품의약품안전처 식품영양성분 DB | [data.mfds.go.kr](https://data.mfds.go.kr) | 한국 음식 칼로리/영양소 정보 |
| 공공데이터포털 | [data.go.kr](https://data.go.kr) | 건강 및 운동 관련 공공 데이터셋 |
| Hugging Face Datasets | [huggingface.co/datasets](https://huggingface.co/datasets) | 한국어 감성 분석 데이터셋 (nsmc 등) |
| ExRx.net | [exrx.net](https://exrx.net) | 운동 정보 참고 자료 |
| Muscle Wiki | [musclewiki.com](https://musclewiki.com) | 부위별 운동 정보 |

### 활용 모델 요약

| 단계 | 모델 유형 | 모델명 | 역할 |
|------|---------|--------|------|
| 기(起) | NLP 모델 | KoBERT / KcBERT | 텍스트 분류, NER |
| | NLP 모델 | KeyBERT | 키워드 추출 |
| 승(承) | 생성 모델 | EXAONE 3.5 / OpenAI GPT | 식단 생성, 영양 분석 |
| | NLP 모델 | mT5 / BART | 식단 요약 |
| 전(轉) | 생성 모델 | EXAONE 3.5 / OpenAI GPT | 운동 루틴 생성 |
| | 검색 모델 | sentence-transformers / BM25 | 운동 정보 검색 |
| 결(結) | 감성 분석 | KoBERT / KcBERT | 운동 일지 감성 분석 |
| | 생성 모델 | EXAONE 3.5 / OpenAI GPT | 동기부여 피드백 생성 |
| | NLP 모델 | mT5 / BART | 주간 운동 기록 요약 |

---

## 6. 기술 스택

| 구분 | 기술 |
|------|------|
| **Frontend** | React + Tailwind CSS |
| **Backend / API** | Python (FastAPI) + EXAONE API + OpenAI API |
| **NLP 모델** | KoBERT, KcBERT, KeyBERT, mT5, BART, sentence-transformers |
| **검색 엔진** | BM25 (rank_bm25) + FAISS (sentence-transformers) |
| **데이터 처리** | Pandas, NumPy |
| **보조 UI** | Streamlit 또는 Gradio (선택적) |
| **환경** | Google Colab / Local Python 3.10+ |

---

## 7. UI 화면 구성

React 기반의 4페이지 + 비교 대시보드로 구성합니다.

```
┌──────────────────────────────────────────────────────┐
│  🏠 HelChangGPT                                      │
├──────┬──────┬──────┬──────┬──────────────────────────┤
│ 프로필 │ 식단  │ 운동  │ 일지  │ 비교 대시보드            │
└──────┴──────┴──────┴──────┴──────────────────────────┘
```

| 페이지 | 설명 |
|--------|------|
| **온보딩 (프로필)** | 사용자 신체 정보 및 목표 입력 (자연어 입력 또는 폼) |
| **식단 추천** | 생성된 식단 + 영양소 분석 카드 |
| **운동 루틴** | 요일별 운동 계획 + 운동 상세 정보 검색 |
| **운동 일지 & 피드백** | 일지 작성 + AI 감성 분석 + 동기부여 메시지 |
| **비교 대시보드** | LLM 모델별, 파라미터별 결과 비교 시각화 |

---

## 8. 파라미터 튜닝 계획

동일한 테스트 입력 세트로 다음 파라미터를 조정하며 결과를 비교합니다.

| 파라미터 | 조정 범위 | 기대 효과 |
|---------|---------|---------|
| `temperature` | 0.3 / 0.7 / 1.0 | 식단/운동 추천의 다양성 vs 정확성 비교 |
| `top_p` | 0.5 / 0.8 / 0.95 | 출력 문장의 자연스러움 및 정보 포함도 비교 |
| `max_tokens` | 500 / 1000 / 2000 | 응답 길이에 따른 정보 품질 비교 |
| 프롬프트 설계 | Zero-shot / Few-shot / CoT | 프롬프트 방식에 따른 출력 품질 비교 |

---

## 9. 프로젝트 구조

```
helchanggpt/
├── README.md
├── requirements.txt
├── data/
│   ├── nutrition/          # 영양성분 데이터
│   ├── exercises/          # 운동 정보 데이터
│   ├── user_samples/       # 사용자 입력 샘플
│   └── diary_samples/      # 운동 일지 샘플
├── notebooks/
│   ├── 01_profile_analysis.ipynb    # 기(起) 프로필 분석
│   ├── 02_diet_generation.ipynb     # 승(承) 식단 생성
│   ├── 03_workout_routine.ipynb     # 전(轉) 운동 루틴
│   ├── 04_feedback_analysis.ipynb   # 결(結) 피드백 분석
│   └── 05_comparison.ipynb          # 모델/파라미터 비교
├── src/
│   ├── profile/            # 프로필 분석 모듈
│   ├── diet/               # 식단 생성 모듈
│   ├── workout/            # 운동 루틴 모듈
│   ├── feedback/           # 피드백 분석 모듈
│   └── utils/              # 유틸리티
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── pages/
│   │   └── components/
│   └── package.json
├── api/                    # FastAPI 백엔드
│   └── main.py
└── docs/
    └── report.docx         # 최종 보고서
```

---

## 10. 실행 방법

### 백엔드

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# API 서버 실행
cd api
uvicorn main:app --reload --port 8000
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

### 노트북 실행 (Colab)

각 단계별 노트북을 Google Colab에서 순서대로 실행합니다.

```
01_profile_analysis.ipynb → 02_diet_generation.ipynb → 03_workout_routine.ipynb → 04_feedback_analysis.ipynb
```

---

## 11. 팀 구성 및 역할

| 역할 | 담당 업무 |
|------|---------|
| **PM / 기획** | 프로젝트 기획, 파이프라인 설계, 보고서 작성 |
| **NLP 모델링** | KoBERT/KcBERT 감성분석, KeyBERT 키워드 추출, mT5/BART 요약 |
| **LLM 연동** | EXAONE/OpenAI API 연동, 프롬프트 설계, 파라미터 튜닝 |
| **프론트엔드** | React UI 개발, 비교 대시보드 시각화 |
| **데이터** | 데이터 수집/전처리, 운동 정보 DB 구축, 검색 엔진 구현 |

---

## 12. 참고 자료

### 리서치 자료
- MRFR — [NLP in Healthcare & Life Science Market Report 2035](https://www.marketresearchfuture.com/reports/nlp-in-healthcare-life-science-market-33949)
- ETRI — [LLM 기반 헬스케어 AI 기술 동향](https://ettrends.etri.re.kr/ettrends/214/0905214005/)
- Microsoft — [2026년 7대 AI 트렌드](https://news.microsoft.com/source/asia/2025/12/16/whats-next-in-ai-7-trends-to-watch-in-2026/?lang=ko)
- 헬스경향 — [AI가 분석한 2025 한국인 건강관리 10대 트렌드](https://www.k-health.com/news/articleView.html?idxno=88142)
- 삼정KPMG — [AI로 촉발된 헬스케어 산업의 대전환](https://assets.kpmg.com/content/dam/kpmg/kr/pdf/2024/insight/kpmg-korea-ai-healthcare-20240625.pdf)

### 활용 모델 참고
- [KoBERT — SKTBrain](https://github.com/SKTBrain/KoBERT)
- [KcBERT — Beomi](https://github.com/Beomi/KcBERT)
- [KeyBERT](https://github.com/MaartenGr/KeyBERT)
- [sentence-transformers](https://www.sbert.net/)
- [EXAONE — LG AI Research](https://www.lgresearch.ai/exaone)
- [OpenAI API](https://platform.openai.com/docs)

### 데이터 출처
- [식품의약품안전처 식품영양성분 DB](https://data.mfds.go.kr)
- [공공데이터포털](https://data.go.kr)
- [Hugging Face Datasets](https://huggingface.co/datasets)
- [ExRx.net](https://exrx.net)
- [Muscle Wiki](https://musclewiki.com)

---

## 📄 라이선스

본 프로젝트는 교육 목적으로 제작되었습니다.

---

<p align="center">
  <b>💪 헬창지피티와 함께 오운완! 💪</b><br>
  <i>HelChangGPT — Your AI Fitness Life Coach</i>
</p>
