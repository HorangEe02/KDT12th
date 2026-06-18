**한국어** | [English](./README.en.md)

# 박준영 · Data Scientist Portfolio

> **통계학 학사 + AI/빅데이터 실전 프로젝트 13선**
>
> 계명대학교 통계학과를 졸업하고, 경북대학교 **K-Digital Training 12기 AI·빅데이터 전문가 양성 과정**(고용노동부 주관, 2025.12~2026.06)에서
> 통계 분석 → 머신러닝 → 딥러닝 → 컴퓨터 비전 → 자연어 처리 → 풀스택 AI 서비스까지
> 데이터의 전 생애주기를 **13개 미니 프로젝트**로 직접 구현했습니다.
> 통계적 추론으로 문제를 정의하고, ML/DL로 모델링하며, 서비스로 배포해 가치를 검증하는 것이 제 강점입니다.

<br>

| | |
|------|------|
| **이름** | 박준영 (Junyeong Park) |
| **전공** | 계명대학교 통계학과 (졸업) |
| **과정** | K-Digital Training 12기 · AI/빅데이터 전문가 양성 (경북대학교 · 고용노동부) |
| **기간** | 2025.12 ~ 2026.06 |
| **GitHub** | [github.com/HorangEe02](https://github.com/HorangEe02) |
| **포트폴리오** | [Notion 포트폴리오](https://www.notion.so/31879104c6f38039a53cfaa4b64ef712) |

---

## 🎯 한눈에 보는 강점

- **통계적 엄밀함** — 가설검정·교란변수 통제·다변량 회귀로 "상관"과 "인과"를 구분 (전공 기반)
- **End-to-End 모델링** — 분류·회귀·비지도학습·딥러닝·NLP를 데이터 특성에 맞게 선택·조합
- **인사이트 → 의사결정** — SHAP/Feature Importance로 모델을 해석하고 비즈니스 액션으로 연결
- **서비스화 역량** — 모델을 Streamlit·FastAPI·Next.js로 배포해 실제 동작하는 제품으로 완성
- **팀 리딩** — 2개 프로젝트(Phase 8·9) 팀장으로 주제 기획·역할 분담·통합 담당

---

## 🧰 기술 스택 (증거 프로젝트 매핑)

| 영역 | 기술 | 대표 프로젝트 |
|------|------|--------------|
| **언어 · 기초** | Python, SQL, Git, OOP | Phase 1 · 전 과정 |
| **통계 · 분석** | Pandas, NumPy, statsmodels, 로지스틱 회귀, 카이제곱·ANOVA·t-test, 효과크기 | Phase 2 · 5 · 7 |
| **시각화** | Matplotlib, Seaborn, Plotly, Streamlit | Phase 5 · 8 · 9 · 10 |
| **데이터 수집** | Selenium, BeautifulSoup, 공공 API 연동 | Phase 4 · 6 · 12 · 13&14 |
| **머신러닝** | Scikit-learn, XGBoost, LightGBM, K-Means, SHAP | Phase 2 · 8 · 9 |
| **딥러닝 · CV** | PyTorch, CNN, ResNet, U-Net, YOLOv8, Autoencoder, OpenCV | Phase 9 · 10 |
| **NLP · LLM** | HuggingFace Transformers, KcELECTRA, BERT, NER, 감성분석, RAG(ChromaDB), Ollama, Gemini, Tool Calling | Phase 6 · 10 · 11 · 13&14 |
| **웹 · 배포 · 인프라** | FastAPI, Next.js 16, React, Docker Compose, Firebase, Cloudflare Tunnel | Phase 11 · 12 · 13&14 |

---

## ⭐ Featured Projects

> 13개 중 데이터 사이언티스트 역량을 가장 잘 보여주는 **대표 6선**입니다.
> 전체 목록은 [📚 전체 프로젝트](#-전체-프로젝트-13선)에서 확인할 수 있습니다.

### 1. 직장인 점심 추천 통합 AI 대시보드 — *Phase 13 & 14* 🏆

> **"오늘 뭐 먹지?"를 데이터로 해결한 KDT 전 과정 통합 캡스톤급 풀스택 AI 서비스**

| | |
|------|------|
| **문제** | 직장인의 반복되는 점심 의사결정 피로(Decision Fatigue), 편향된 식사 패턴, 주간 영양 불균형 |
| **접근** | 날씨·영양·팀 선호도·음식점 4축을 하나의 파이프라인으로 통합 + 가중 점수 추천 + NLP 7모듈 |
| **NLP** | KcELECTRA 감성분석 · 메뉴 정규화 · RAG 챗봇(ChromaDB) · ABSA · Food NER · Multi-turn Tool Calling · NLG 주간 리포트 |
| **규모** | FastAPI ×2 (50 엔드포인트) · 음식점 **17,402개** SQLite · Next.js 16 PWA 7페이지 |
| **인프라** | Docker Compose 5-서비스(api·nlp·web·ollama·caddy) · Cloudflare Tunnel · LLM 런타임 토글(Ollama ↔ Gemini) · 데모 배포 자동화 |
| **기술** | FastAPI · Next.js 16 · KcELECTRA · ChromaDB · Ollama/Gemini · Docker · Caddy · TanStack Query |
| **역할** | 팀 |

📂 [Phase13&14 폴더](./Phase13%2614)

---

### 2. OpenCV & ML 하이브리드 부품 결함 자동 검수 — *Phase 9* (팀장)

> **철강 표면 4종 결함 2-Stage 자동 검수 + "데이터 > 아키텍처"를 실증한 교차 도메인 검증**

| | |
|------|------|
| **문제** | 제조 품질검사 자동화 — 산업 규모(15만 장+) 이미지 결함 분류 파이프라인 구축 |
| **데이터** | Kaggle Severstal 12,568장 → **150,816 패치**(256×256, stride=128, 50% 오버랩) |
| **접근** | 2-Stage(이진 → 4종 분류) · OpenCV 전처리 · ML 7종 · DL(ResNet-18) · Autoencoder 이상탐지 |
| **성과** | Stage1 DL **90.87%** / Stage2 DL **86.01%** / AE Recall **96.0%** · Streamlit 8탭 대시보드 |
| **핵심 인사이트** | Severstal→NEU 교차 도메인 검증에서 ML **51.6%** > DL **14.4%** → 일반화에는 *아키텍처보다 데이터가 중요*함을 실증 |
| **기술** | OpenCV · Scikit-learn · PyTorch · Autoencoder · Streamlit |
| **역할** | **팀장** (Vision-Q) |

📂 [Phase9 폴더](./Phase9)

---

### 3. 머신러닝 기반 재고 관리 최적화 WMS — *Phase 8* (팀장)

> **하나의 데이터셋으로 분류·회귀·비지도학습을 아우른 중소 유통 재고 최적화 시스템**

| | |
|------|------|
| **문제** | 중소 유통업체의 WMS 부재(ERP 도입률 16.3%) → 과잉 재고 폐기·품절 반복 |
| **접근** | 4개 소주제 — 재고상태 분류 · 판매량 예측 · 폐기위험 예측 · 발주전략 클러스터링 + EOQ 시뮬레이션 |
| **성과** | LightGBM Acc **99%** · XGBoost **R²=0.948** · K-Means 군집별 발주전략 · Feature Importance 3중 교차검증 · SHAP 해석 |
| **산출물** | Streamlit WMS v3.5 — 7페이지, 듀얼 모드, 20+ ML 모델 탑재 대시보드 |
| **기술** | Scikit-learn · XGBoost · LightGBM · K-Means · SHAP · Streamlit |
| **역할** | **팀장** (굿핏) |

📂 [Phase8 폴더](./Phase8)

---

### 4. 흡연과 뇌졸중 상관관계 분석 — *Phase 2*

> **통계학 전공 강점을 살린 의료 통계 — 교란변수 통제 후에도 흡연이 독립 위험요인인지 검증**

| | |
|------|------|
| **연구 질문** | 나이·성별·BMI·음주·신체활동을 통제한 후에도 흡연은 뇌졸중 위험을 높이는가? |
| **데이터** | CDC BRFSS 2020 — **319,795명** × 18변수 (결측치 0%) |
| **접근** | 카이제곱·Cramér's V → 다변량 로지스틱 회귀(Crude → 완전보정 OR) → 상호작용·층화 분석 → VIF → ML/DL 비교 |
| **성과** | 흡연자 발생률 **5.17%** vs 비흡연자 2.80%(1.85배) · 완전보정 후에도 유의 · XGBoost AUC **0.808** · PyTorch(Focal Loss) 앙상블 · SHAP 해석 |
| **기술** | Pandas · statsmodels · Scikit-learn · XGBoost · PyTorch · SHAP |
| **역할** | 팀 |

📂 [Phase2 폴더](./Phase2)

---

### 5. 헬창지피티 — NLP 피트니스 코칭 — *Phase 11*

> **자연어 한 문장을 프로필 분석, 식단 생성, 운동 루틴, 피드백까지 연결한 4단계 NLP 코칭 서비스**

| | |
|------|------|
| **문제** | 운동을 시작하고 싶지만 전문 지식이 부족한 사용자가 식단·운동·피드백 정보를 각각 따로 찾아야 하는 불편 |
| **접근** | 자연어 입력 → 프로필 분석 → 식단 생성 → 운동 루틴 설계 → 운동 일지 감성 분석 및 동기부여 피드백 |
| **NLP** | NER · 목표 유형 분류 · 키워드 추출 · 식단/운동 텍스트 생성 · 감성 분석 · 요약 · 검색 기반 운동 정보 제공 |
| **LLM/검색** | Ollama 기반 로컬 LLM · EXAONE 계열 모델 활용 · sentence-transformers/FAISS · BM25 검색 구조 |
| **산출물** | React 기반 피트니스 코칭 UI, 4단계 NLP 파이프라인, 모델/파라미터 비교 대시보드 설계 |
| **기술** | React · Tailwind CSS · FastAPI · Ollama LLM · NER · 감성분석 · sentence-transformers · BM25 |
| **역할** | 팀 |

📂 [Phase11 폴더](./Phase11)

---

### 6. KBO 원정 응원 플래너 — *Phase 12* 🌐

> **데이터 모델을 실서비스로 — Gemini Tool Calling 챗봇이 탑재된 라이브 풀스택 웹앱**

| | |
|------|------|
| **주제** | KBO 10개 구단·전국 8개 도시·연간 720경기 원정 응원러를 위한 올인원 플래너 (6페이지) |
| **데이터 → 서비스** | scikit-learn 승률 예측 모델을 TypeScript로 이식 · 3-tier 길찾기 폴백(Kakao → OSRM → Haversine) |
| **AI 통합** | Gemini 2.5 Flash Lite 스트리밍 챗봇 + 6 Tool Calling + Multi-Agent |
| **성과** | Firebase App Hosting **라이브 배포** · 모바일 자동 테스트 **138/138 PASS** · Secret Manager 7종 · GitHub auto-rollout |
| **기술** | Next.js 16 · React 19 · Gemini 2.5 · React-Leaflet · Cloud Firestore · Firebase App Hosting |
| **역할** | 팀 |

📂 [Phase12 폴더](./Phase12) · 🌐 [Live Demo](https://my-web-app--mini12-310f5.asia-east1.hosted.app)

---

## 📚 전체 프로젝트 (13선)

| Phase | 프로젝트 | 기간 | 분야 | 핵심 기술 | 역할 |
|-------|---------|------|------|----------|------|
| **[1](./Phase1)** | Python 기초 (Pygame FPS·미니게임·tkinter GUI) | 2025.12~2026.01 | Python | Pygame 레이캐스팅, tkinter, OOP | 개인 |
| **[2](./Phase2)** ⭐ | 흡연과 뇌졸중 상관관계 분석 | 2026.01 | 의료 통계 | 로지스틱 회귀, XGBoost(AUC 0.808), SHAP | 팀 |
| **[3](./Phase3)** | Esports 분석 (경제·평등·의료 3관점) | 2026.01~02 | 데이터 분석 | Pandas, 통계 분석, 시각화 | 팀 |
| **[4](./Phase4)** | 기후변화가 소스류 원재료에 미치는 영향 | 2026.02 | 데이터 수집 | 크롤링, 시계열 분석 | 팀 |
| **[5](./Phase5)** | 글로벌 내륙 거점 도시 비교 (대구) | 2026.02 | 데이터 시각화 | Matplotlib, Seaborn, Plotly | 팀 |
| **[6](./Phase6)** | 의료 AI 취업동향 크롤링·분석 | 2026.02 | 웹 크롤링 | Selenium, BeautifulSoup, 형태소 분석 | 팀 |
| **[7](./Phase7)** | MBTI/혈액형 성격 이론 검증 | 2026.03 | 통계 검정 | NumPy, 카이제곱, ANOVA, t-test | 팀 |
| **[8](./Phase8)** ⭐ | ML 재고 관리 최적화 WMS | 2026.03 | 머신러닝 | LightGBM, XGBoost, K-Means, SHAP, Streamlit | **팀장** |
| **[9](./Phase9)** ⭐ | OpenCV & ML 결함 자동 검수 | 2026.03 | 컴퓨터 비전 | OpenCV, PyTorch, Autoencoder, Streamlit | **팀장** |
| **[10](./Phase10)** | AI 스마트 팩토리 품질관리 | 2026.04 | 딥러닝 | CNN, U-Net, YOLOv8, BERT | 팀 |
| **[11](./Phase11)** ⭐ | 헬창지피티 — NLP 피트니스 코칭 | 2026.04 | 자연어 처리 | Ollama LLM, NER, 감성분석, React | 팀 |
| **[12](./Phase12)** ⭐ | 원정 응원 플래너 (KBO) | 2026.04 | 풀스택/Cloud | Next.js 16, Firebase, Gemini Tool Calling | 팀 |
| **[13&14](./Phase13%2614)** ⭐ | 직장인 점심 추천 통합 AI 대시보드 | 2026.04~05 | 풀스택 AI | FastAPI×2, Next.js, RAG, KcELECTRA, Docker | 팀 |

> ⭐ = Featured (상세는 위 [Featured Projects](#-featured-projects) 참고)

---

## 🛠️ 역량 성장 로드맵

```
Phase 1     Python 기초          Pygame · tkinter · OOP
   │
Phase 2~3   통계·데이터 분석      로지스틱 회귀 · XGBoost · 다관점 분석
   │
Phase 4~6   수집·시각화·크롤링    Selenium · BeautifulSoup · Plotly
   │
Phase 7     통계 검정            NumPy · 카이제곱 · ANOVA · t-test
   │
Phase 8     머신러닝             LightGBM · XGBoost · K-Means · SHAP
   │
Phase 9     컴퓨터 비전          OpenCV · ResNet-18 · Autoencoder
   │
Phase 10    딥러닝               CNN · U-Net · YOLOv8 · BERT
   │
Phase 11    자연어 처리          Ollama LLM · NER · 감성분석
   │
Phase 12    풀스택/Cloud         Next.js 16 · Firebase · Gemini Tool Calling
   │
Phase 13&14 통합 AI 서비스       FastAPI ×2 · RAG · KcELECTRA · Docker · Tunnel
```

---

## 📊 프로젝트 규모

| Phase | 파일 수 | 주요 산출물 |
|-------|---------|-----------|
| 1 | 73 | FPS 게임, 미니게임 6종, 의료관리 GUI |
| 2 | 22 | 분석 보고서, 시각화 차트 |
| 3 | 271 | 경제/평등/의료 3관점 분석 |
| 4 | 55 | 크롤링 데이터, 분석 보고서 |
| 5 | 163 | 인터랙티브 시각화, 발표자료 |
| 6 | 370 | 크롤링 파이프라인, NLP 분석 |
| 7 | 153 | 통계 검정 보고서, 시각화 |
| 8 | 428 | Streamlit WMS v3.5, 4개 소주제 보고서 |
| 9 | 162 | 12개 노트북, Streamlit 8탭, 5개 보고서 |
| 10 | 150 | 4개 소주제 DL 모델, Streamlit 대시보드 |
| 11 | 149 | NLP 파이프라인, React 프론트엔드 |
| 12 | 443 | Next.js 16 풀스택, Firebase 라이브 배포 |
| 13&14 | 457 | FastAPI ×2, Next.js PWA, RAG 챗봇, Docker 5-서비스 |
| **합계** | **~2,900** | **13개 Phase 프로젝트 완성** |

---

## 📫 Contact

| | |
|------|------|
| **GitHub** | [github.com/HorangEe02](https://github.com/HorangEe02) |
| **Email** | catlife9029@gmail.com |
| **Notion 포트폴리오** | [바로가기](https://www.notion.so/31879104c6f38039a53cfaa4b64ef712) |

---

*본 레포지토리는 경북대학교 K-Digital Training AI/빅데이터 전문가 양성 12기 과정에서 수행한 미니 프로젝트 모음입니다. 각 Phase 폴더에 상세 README가 포함되어 있습니다.*
