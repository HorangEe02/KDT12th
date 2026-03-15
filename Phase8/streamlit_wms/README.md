# E-Grocery WMS v3.5 — ML 기반 재고 최적화 시스템

> **Streamlit 기반 Warehouse Management System**
> 4개 ML 모델을 활용한 실시간 재고 분석 · 판매 예측 · 폐기 위험 탐지 · 발주 전략 최적화

<br>

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [핵심 기능](#핵심-기능)
- [기술 스택](#기술-스택)
- [ML 모델 성능](#ml-모델-성능)
- [시스템 아키텍처](#시스템-아키텍처)
- [페이지별 상세 기능](#페이지별-상세-기능)
- [UI/UX 설계](#uiux-설계)
- [데이터 파이프라인](#데이터-파이프라인)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [향후 계획](#향후-계획)

<br>

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | E-Grocery WMS (Warehouse Management System) |
| **버전** | v3.5 (Phase 8 mini) |
| **데이터** | Kaggle E-Grocery — 1,000 SKU × 37 컬럼 |
| **대상** | 식료품 유통 물류 창고 (인도네시아 5개 도시) |
| **목적** | ML 기반 재고 최적화로 폐기 손실 최소화, 품절 방지, 발주 비용 절감 |
| **개발 기간** | 2025.12 ~ 2026.03 |

### 프로젝트 배경

식료품 유통업에서 **과잉 재고로 인한 폐기 손실**과 **품절로 인한 매출 기회 손실**은 양대 핵심 과제입니다.
이 프로젝트는 4개의 ML 모델을 훈련시켜 재고 상태 분류, 판매량 예측, 폐기 위험 탐지, 발주 전략 수립을 자동화하고,
비전공 실무자도 사용할 수 있는 인터랙티브 대시보드를 제공합니다.

<br>

---

## 핵심 기능

### ML 기반 의사결정 지원
- **재고 상태 자동 분류** — LightGBM이 제품별 재고 상태(충분/부족/품절/유통기한 임박)를 98.8% 정확도로 분류
- **판매량 예측** — XGBoost가 향후 30일 판매량을 R² 0.9477로 예측
- **폐기 위험 탐지** — Logistic Regression이 폐기 위험 제품을 99% 정확도로 식별
- **발주 전략 최적화** — K-Means 클러스터링 + EOQ/Safety Stock 연산으로 최적 발주량 산출

### 인터랙티브 시뮬레이션
- **What-If 시뮬레이터** — 재고 수량, 리드타임, 발주점 등 파라미터를 실시간으로 조정하며 결과 확인
- **발주 시뮬레이터** — 제품별 발주 필요성 평가, EOQ 비용 계산, 타임라인 비교 시각화
- **조건 변경 시뮬레이션** — 판매 예측 모델에 다양한 시나리오를 적용하여 결과 비교

### 듀얼 모드 시스템
- **WMS 시뮬레이터 모드** — 비전공자/실무자를 위한 직관적 인터페이스 (시뮬레이션 중심)
- **알고리즘 인사이트 모드** — 데이터 분석가/ML 엔지니어를 위한 상세 분석 (모델 해석 중심)

<br>

---

## 기술 스택

### Backend & ML

| 기술 | 용도 | 버전 |
|------|------|------|
| **Python** | 메인 언어 | 3.10+ |
| **scikit-learn** | 전처리, Logistic Regression, K-Means, DBSCAN, GMM | ≥1.3.0 |
| **XGBoost** | 판매량 예측 (회귀) | ≥2.0.0 |
| **LightGBM** | 재고 상태 분류 | ≥4.0.0 |
| **SHAP** | 모델 해석 (feature importance 설명) | ≥0.43.0 |

### Frontend & Visualization

| 기술 | 용도 | 버전 |
|------|------|------|
| **Streamlit** | 웹 앱 프레임워크 | ≥1.30.0 |
| **Plotly** | 인터랙티브 차트 (3D 산점도, 바, 히트맵) | ≥5.18.0 |
| **Matplotlib** | 정적 시각화 (혼동 행렬 등) | ≥3.7.0 |
| **커스텀 CSS** | Liquid Glass 디자인 시스템, 반응형 UI | - |

### Data Processing

| 기술 | 용도 |
|------|------|
| **Pandas** | 데이터 조작 · 파생변수 생성 · 그룹 분석 |
| **NumPy** | 수치 연산 · 통계 계산 |
| **SciPy** | 정규분포 기반 안전재고 계산 |

<br>

---

## ML 모델 성능

### 모델별 성능 지표

| 모델 | 알고리즘 | 태스크 | 주요 지표 | 피처 수 |
|------|----------|--------|-----------|---------|
| **재고 상태 분류** | LightGBM | 다중 분류 (4 클래스) | Accuracy **98.8%** | 23개 |
| **판매량 예측** | XGBoost (Optuna 튜닝) | 회귀 | R² **0.9477**, RMSE 3.72 | 19개 |
| **폐기 위험 탐지** | Logistic Regression | 이진 분류 | Accuracy **99%**, AUC 0.99 | 20개 |
| **재고 소진일 예측** | Random Forest | 회귀 | R² 0.258 | 17개 |
| **재고 클러스터링** | K-Means (k=3) | 비지도 학습 | Silhouette **0.26** | 7개 |

### 피처 엔지니어링

원본 37개 컬럼에서 태스크별로 최적화된 피처셋을 구성:

```
원본 데이터 (37 컬럼)
  ├─ 인도네시아 로케일 파싱 (2.084,25 → 2084.25)
  ├─ 날짜 파생변수 (Days_To_Expiry, Days_Since_Last_Order)
  ├─ 재고 파생변수 (Stock_Gap, Available_Stock, Reorder_Urgency)
  ├─ 재무 파생변수 (EOQ, Demand_Variability, Supply_Risk)
  ├─ 원-핫 인코딩 (Category 9개 + ABC_Class 2개)
  └─ 태스크별 피처 선택 (17~23개)
```

<br>

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │  Data    │ │Inventory │ │  Sales   │       │
│  │  개요    │ │ Explorer │ │  Status  │ │Prediction│       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│  ┌────┴─────┐ ┌────┴─────┐                                  │
│  │  Waste   │ │ Reorder  │   ← 듀얼 모드 (WMS / 알고리즘)   │
│  │  Risk    │ │ Strategy │                                   │
│  └────┬─────┘ └────┬─────┘                                   │
├───────┼────────────┼────────────────────────────────────────┤
│       ▼            ▼          Utility Layer                  │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐   │
│  │  styles │ │data_load │ │preprocess │ │ descriptions │   │
│  │ (UI/CSS)│ │ (CSV/PKL)│ │(features) │ │(docs/glossary│   │
│  └─────────┘ └────┬─────┘ └─────┬─────┘ └──────────────┘   │
├────────────────────┼────────────┼───────────────────────────┤
│                    ▼            ▼          Model Layer       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │LightGBM  │ │ XGBoost  │ │ Logistic │ │ K-Means  │       │
│  │분류 98.8%│ │회귀 94.8%│ │분류  99% │ │클러스터링│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  + DBSCAN, GMM (Sub-clustering) + Random Forest (DOI)       │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                                │
│  CSV: 1,000 SKU × 37 columns (Kaggle E-Grocery)            │
│  PKL: 10+ trained models + scalers + label encoders         │
│  JSON: feature_info configs (v1~v5)                         │
└─────────────────────────────────────────────────────────────┘
```

<br>

---

## 페이지별 상세 기능

### 0. 홈 (app.py)
통합 소개 페이지 — 6개 분석 모듈과 4개 ML 모델의 성능 요약을 한눈에 확인

### 1. 대시보드 개요 (Dashboard)

| 모드 | 기능 |
|------|------|
| **WMS 시뮬레이터** | KPI 카드 (4종), 재고 상태 분포 (도넛), 카테고리별 재고 (바) |
| **알고리즘 인사이트** | KPI 카드, 3D 클러스터링 시각화, 판매 예측 시뮬레이터, 위험 제품 테이블, 분포 차트 |

### 2. 데이터 탐색 (Data Explorer)

| 모드 | 기능 |
|------|------|
| **WMS 시뮬레이터** | 사이드바 필터링, KPI 카드, 데이터 테이블, 컬럼별 분석, 산점도 비교 |
| **알고리즘 인사이트** | + 기술 통계 (describe), 분포 히스토그램/박스플롯, 상관관계 히트맵, AI 알고리즘 소개, 용어 사전 |

### 3. 재고 상태 분류 (Inventory Status)

| 모드 | 기능 |
|------|------|
| **WMS 시뮬레이터** | 제품 선택 → AI 분류 결과 (확률 바) → What-If 시뮬레이션 |
| **알고리즘 인사이트** | 혼동 행렬, 클래스별 성능 (P/R/F1), LightGBM 피처 중요도, SHAP 분석, 개별 제품 예측, 용어 사전 |

### 4. 판매량 예측 (Sales Prediction)

| 모드 | 기능 |
|------|------|
| **WMS 시뮬레이터** | 제품별 AI 예측 결과, 실제 vs 예측 비교, 조건 변경 시뮬레이션, 비교 차트 |
| **알고리즘 인사이트** | 예측 정확도 (산점도/잔차), XGBoost 피처 중요도, SHAP 분석, 구간별 성능 분석, 용어 사전 |

### 5. 폐기 위험 탐지 (Waste Risk)

| 모드 | 기능 |
|------|------|
| **WMS 시뮬레이터** | KPI 카드, 카테고리별 위험 분석, 위험 제품 목록, What-If 시뮬레이터 |
| **알고리즘 인사이트** | 위험 SKU 분석, 신선식품 분석 (FIFO/FEFO), AI 모델 분석, SHAP, 개별 예측, 용어 사전 |

### 6. 발주 전략 (Reorder Strategy) — 가장 복잡한 페이지

| 모드 | 기능 |
|------|------|
| **WMS 시뮬레이터** | 제품별 발주 시뮬레이터 (KPI 9종, 상태 평가, 권장 조치, 타임라인), 긴급 발주 TOP 5, 해석 가이드, 빠른 시뮬레이터, 발주 긴급도 테이블 |
| **알고리즘 인사이트** | 발주 긴급도, 3-Tier 분류 체계, Safety Stock & EOQ 분석, 알고리즘 비교 (K-Means/DBSCAN/GMM), S×H 민감도 분석, t-SNE/UMAP 시각화, Phase A 회귀 개선 (Optuna), AI 모델 분석, 용어 사전 |

<br>

---

## UI/UX 설계

### 디자인 시스템

| 요소 | 구현 |
|------|------|
| **Liquid Glass 아이콘** | SVG 기반 커스텀 아이콘 (그라디언트 + 글래스모피즘) — 15종 |
| **KPI 카드** | 아이콘 + 라벨 + 수치 + 툴팁 + 팝오버 상세 정보 |
| **사이드바 네비게이션** | 다크 테마, 현재 페이지 하이라이트 (초록색 배경 + 좌측 바) |
| **듀얼 모드 토글** | WMS 시뮬레이터 / 알고리즘 인사이트 버튼 전환 |
| **커스텀 탭** | `session_state` 기반 버튼 탭 — 탭 전환 시 서버 리렌더링 |

### 플로팅 리모컨 TOC (v3.5 신규)

페이지 우측에 고정된 투명 미니 목차:

- **`<details>/<summary>` 네이티브 HTML** — JS 없이 접기/펼치기
- **투명 배경** — 뒤 콘텐츠가 비쳐 보이는 글래스 효과
- **앵커 이동** — 클릭 시 해당 섹션으로 즉시 스크롤
- **탭 연동 동적 TOC** — 커스텀 탭 전환 시 리모컨 내용이 자동 업데이트
- **미니멀 유니코드 심볼** — ◈ ◉ ◎ ◇ △ ◔ ▸ ▪ ▤ ▦

### 반응형 요소

- 모든 차트: `use_container_width=True`
- KPI 카드: `st.columns(4)` 그리드
- 시뮬레이터: 슬라이더 + ±버튼 조합
- 데이터 테이블: 15개 핵심 컬럼 자동 선택

<br>

---

## 데이터 파이프라인

```
1. 데이터 로드
   CSV (인도네시아 로케일) → parse_id_number() → Pandas DataFrame

2. 파생변수 생성 (data_loader.py)
   ├─ Days_To_Expiry = Expiry_Date - today
   ├─ EOQ = √(2 × Annual_Demand × Ordering_Cost / Holding_Cost)
   ├─ Reorder_Urgency = (QOH - Dynamic_ROP) / Safety_Stock
   ├─ Stock_Coverage_Days = (QOH - SS) / Avg_Daily_Sales
   └─ Waste_Risk = 1 if (Days_To_Expiry < 30 & Days_of_Inventory > 45)

3. 피처 준비 (preprocessor.py)
   ├─ 원-핫 인코딩: Category (9) + ABC_Class (2)
   ├─ 표준화: StandardScaler per task
   └─ 태스크별 피처 선택: 17~23개

4. 모델 추론
   ├─ LightGBM → 재고 상태 (4 classes + probabilities)
   ├─ XGBoost  → 판매량 예측 (연속값)
   ├─ LogReg   → 폐기 위험 (0/1 + probability)
   └─ K-Means  → 클러스터 라벨 (0/1/2)

5. 시각화 & 인터랙션
   └─ Streamlit widgets → Plotly 차트 → 실시간 업데이트
```

<br>

---

## 프로젝트 구조

```
Phase8_mini/                               # 프로젝트 루트
├── README.md                              # 프로젝트 전체 문서
├── data/                                  # 데이터셋
│   └── Supply Chain.../InventoryData.csv  # 메인 데이터
├── notebooks/                             # Jupyter 분석 노트북 (4+α)
├── outputs/
│   ├── figures/                           # 시각화 이미지 (127개)
│   └── models/                            # 학습된 모델 (pkl/json)
├── md/                                    # 분석 문서 · 가이드라인
│
└── streamlit_wms/                         # ★ Streamlit WMS 앱
    ├── app.py                             # 홈 — 프로젝트 소개 페이지
    ├── requirements.txt                   # Python 패키지 의존성
    ├── README.md                          # 대시보드 상세 문서 (이 파일)
    ├── .streamlit/config.toml             # Streamlit 설정 (테마, 서버)
    ├── static/                            # 정적 파일 디렉토리
    │
    ├── pages/
    │   ├── 1_Dashboard.py                 # 대시보드 개요 (KPI, 클러스터링, 시뮬레이터)
    │   ├── 2_Data_Explorer.py             # 데이터 탐색 (필터링, 통계, 시각화)
    │   ├── 3_Inventory_Status.py          # 재고 상태 분류 (LightGBM)
    │   ├── 4_Sales_Prediction.py          # 판매량 예측 (XGBoost)
    │   ├── 5_Waste_Risk.py                # 폐기 위험 탐지 (Logistic Regression)
    │   └── 6_Reorder_Strategy.py          # 발주 전략 (K-Means + EOQ/SS)
    │
    └── utils/
        ├── __init__.py
        ├── data_loader.py                 # 데이터 로드, 파생변수 생성, 모델 로드
        ├── preprocessor.py                # 피처 엔지니어링 (원-핫, 스케일링)
        ├── descriptions.py                # 컬럼 설명, 알고리즘 정보, 용어 사전
        └── styles.py                      # 디자인 시스템 (CSS, SVG 아이콘, 컴포넌트)
```

<br>

---

## 설치 및 실행

### 요구 사항
- Python 3.10+
- pip

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd streamlit_wms

# 패키지 설치
pip install -r requirements.txt
```

### 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

<br>

---

## 버전 이력

| 버전 | 주요 변경 사항 |
|------|---------------|
| **v1.0** | 기본 데이터 로드 + EDA 페이지 |
| **v2.0** | 4개 ML 모델 통합 (분류/회귀/위험/클러스터링) |
| **v3.0** | 듀얼 모드 (WMS 시뮬레이터 / 알고리즘 인사이트) 도입 |
| **v3.5** | Liquid Glass UI 디자인, 플로팅 리모컨 TOC, 커스텀 탭 시스템, 동적 TOC, 발주 시뮬레이터 확장 |

<br>

---

## 향후 계획

- [ ] 실시간 데이터 연동 (DB/API 기반)
- [ ] 사용자 인증 및 권한 관리
- [ ] 알림 시스템 (재고 부족 / 폐기 임박 자동 알림)
- [ ] 모델 재학습 파이프라인 (MLOps)
- [ ] 다국어 지원 (영어/한국어/인도네시아어)
- [ ] 모바일 반응형 최적화

<br>

---

## 기술적 차별점

### 1. 엔드투엔드 ML 파이프라인
> 데이터 수집 → 전처리 → 피처 엔지니어링 → 모델 학습 → 배포 → 시각화를 단일 프로젝트에서 완결

### 2. 실무 지향 시뮬레이터
> 단순 예측 결과 표시가 아닌, 파라미터를 조정하며 **"만약 ~하면?"** 시나리오를 실시간 탐색

### 3. 듀얼 모드 설계
> 비전공 실무자(WMS 모드)와 데이터 분석가(알고리즘 모드)를 동시에 타겟팅하는 UX 설계

### 4. SHAP 기반 모델 해석
> Black-box 모델의 예측 근거를 피처별로 시각화하여 **의사결정 신뢰도 향상**

### 5. 커스텀 디자인 시스템
> Liquid Glass SVG 아이콘, 반투명 플로팅 리모컨, 동적 탭 연동 TOC 등 Streamlit 한계를 넘는 UI/UX 구현

<br>

---

<div align="center">

**E-Grocery WMS v3.5** · ML 기반 재고 최적화 · Phase8_mini

</div>
