# Phase 2 - 흡연이 뇌졸중 발생에 미치는 영향 분석

> **과정**: KDT12 의료 통계 미니 프로젝트
> **팀명**: J와 P (박준영, 이창민)
> **기간**: 2025년 1월
> **연구 질문**: "흡연은 나이, 성별, BMI, 음주, 신체활동 등 다른 요인들을 고려한 후에도 뇌졸중 발생 위험을 높이는가?"

---

## 목차

1. [폴더 구조](#폴더-구조)
2. [파일 분류](#파일-분류)
   - [분석 코드](#1-분석-코드)
   - [데이터](#2-데이터)
   - [시각화 결과물](#3-시각화-결과물-대시보드-png)
   - [보고서 및 문서](#4-보고서-및-문서)
   - [발표 자료](#5-발표-자료)
   - [환경 설정 스크립트](#6-환경-설정-스크립트)
3. [데이터셋 정보](#데이터셋-정보)
4. [분석 파이프라인](#분석-파이프라인)
5. [핵심 분석 결과](#핵심-분석-결과)
6. [기술 스택](#기술-스택)
7. [실행 방법](#실행-방법)

---

## 폴더 구조

```
phase2/
└── smoking_stroke_analysis/
    │
    ├── README.md                        # 프로젝트 설명서
    ├── requirements.txt                 # Python 패키지 목록
    │
    ├── code/                            # 분석 코드
    │   └── smoking_stroke_analysis_reorganized.ipynb  # 메인 분석 노트북 (94셀)
    │
    ├── data/                            # 데이터
    │   ├── heart_2020_cleaned.csv       #   루트에서 이동된 2020 데이터 복사본 (24MB)
    │   ├── 2020/
    │   │   └── heart_2020_cleaned.csv   #   2020 BRFSS 데이터 (24MB)
    │   ├── 2022/
    │   │   ├── heart_2022_no_nans.csv   #   2022 데이터 - 결측치 없음 (78MB)
    │   │   └── heart_2022_with_nans.csv #   2022 데이터 - 결측치 포함 (133MB)
    │   └── Indicators of Heart Disease (2022 UPDATE).zip  # 2022 원본 ZIP (21MB)
    │
    ├── images/                          # 시각화 결과물 (대시보드 PNG)
    │   ├── dataset_overview_dashboard.png       # 데이터셋 개요
    │   ├── data_quality_dashboard.png           # 데이터 품질
    │   ├── variable_distribution_dashboard.png  # 변수 분포
    │   ├── relationship_dashboard.png           # 변수 간 관계
    │   └── stratified_dashboard.png             # 층화 분석
    │
    ├── docs/                            # 보고서 및 문서
    │   ├── smoking_stroke_research_report.md            # 연구 보고서 (학술 형식, 540줄)
    │   ├── smoking_stroke_analysis_reorganized.md       # 노트북 구조 설명 (311줄)
    │   └── J와 P_흡연과 뇌졸증의 상관관계 분석_보고서.docx  # Word 보고서 (136KB)
    │
    ├── presentation/                    # 발표 자료
    │   ├── J와 P_박준영_이창민_KDT12_미니프로젝트.pptx  # 슬라이드 원본 (9.3MB)
    │   └── J와 P_박준영_이창민_KDT12_미니프로젝트.pdf   # 슬라이드 PDF (4.5MB)
    │
    └── scripts/                         # 환경 설정 및 실행 스크립트
        ├── setup.sh                     #   초기 환경 설정 (1회)
        └── run_analysis.sh              #   분석 실행 (3가지 옵션)
```

---

## 파일 분류

### 1. 분석 코드

| 파일 | 용량 | 설명 |
|------|------|------|
| `code/smoking_stroke_analysis_reorganized.ipynb` | 1.6MB | 메인 분석 Jupyter 노트북 (94셀, 6개 파트) |

**노트북 구조 (6개 파트)**

| PART | 제목 | 주요 내용 |
|------|------|----------|
| 1 | 환경 설정 | 라이브러리 import, GPU/MPS 자동 감지 |
| 2 | 데이터 전처리 | 데이터 로드, 기본 탐색, 범주형 → 수치형 인코딩 |
| 3 | 시각화 (EDA) | 통합 대시보드 5종 생성 |
| 4 | 통계 분석 | 카이제곱 검정, 로지스틱 회귀, 상호작용 효과 |
| 5 | 머신러닝 | sklearn 모델 비교, PyTorch 딥러닝, 앙상블 |
| 6 | 결론 | 종합 요약 |

---

### 2. 데이터

| 파일 | 용량 | 출처 | 설명 |
|------|------|------|------|
| `data/2020/heart_2020_cleaned.csv` | 24MB | CDC BRFSS 2020 | 319,795명, 18변수, 결측치 0% |
| `data/2022/heart_2022_no_nans.csv` | 78MB | CDC BRFSS 2022 | 2022 업데이트 (결측치 제거) |
| `data/2022/heart_2022_with_nans.csv` | 133MB | CDC BRFSS 2022 | 2022 업데이트 (결측치 포함) |
| `data/Indicators of Heart Disease (2022 UPDATE).zip` | 21MB | Kaggle | 2022 원본 압축 파일 |
| `data/heart_2020_cleaned.csv` | 24MB | - | 2020 데이터 복사본 (루트에서 이동) |

**주 분석 대상**: `data/2020/heart_2020_cleaned.csv` (319,795건)

---

### 3. 시각화 결과물 (대시보드 PNG)

| 파일 | 용량 | 내용 |
|------|------|------|
| `images/dataset_overview_dashboard.png` | 272KB | 데이터셋 규모, 변수 유형, 역할별 분류 |
| `images/data_quality_dashboard.png` | 236KB | 결측치 패턴, BMI 이상치, 완성도 |
| `images/variable_distribution_dashboard.png` | 276KB | 종속/독립/교란변수 분포 |
| `images/relationship_dashboard.png` | 272KB | 변수 간 관계, 상관관계 |
| `images/stratified_dashboard.png` | 168KB | 흡연 x 신체활동 층화 분석 |

---

### 4. 보고서 및 문서

| 파일 | 라인 수 | 설명 |
|------|---------|------|
| `README.md` (루트) | 224줄 | 프로젝트 개요, 분석 방법론, 결과 요약 |
| `docs/smoking_stroke_research_report.md` | 540줄 | 학술 논문 형식 연구 보고서 (초록~결론) |
| `docs/smoking_stroke_analysis_reorganized.md` | 311줄 | 노트북 셀 구조 및 대시보드 레이아웃 설명 |

**연구 보고서 구성** (`smoking_stroke_research_report.md`)
1. 초록 (Abstract)
2. 서론 - 연구 배경, 목적, 가설
3. 연구 방법 - 데이터 출처, 변수 정의, 분석 방법
4. 결과 - 기술통계, 통계 검정, 회귀분석, ML 모델
5. 고찰 - 주요 발견, 기존 연구 비교, 한계점
6. 결론

---

### 5. 발표 자료

| 파일 | 용량 | 설명 |
|------|------|------|
| `presentation/J와 P_박준영_이창민_KDT12_미니프로젝트.pptx` | 9.3MB | 발표 슬라이드 원본 |
| `presentation/J와 P_박준영_이창민_KDT12_미니프로젝트.pdf` | 4.5MB | 발표 슬라이드 PDF 변환 |
| `docs/J와 P_흡연과 뇌졸증의 상관관계 분석_보고서.docx` | 136KB | Word 보고서 |

---

### 6. 환경 설정 스크립트

| 파일 | 설명 |
|------|------|
| `requirements.txt` (루트) | Python 패키지 목록 (pandas, numpy, matplotlib, seaborn, scipy, statsmodels, scikit-learn, xgboost, imbalanced-learn, torch, jupyter 등) |
| `scripts/setup.sh` | 초기 1회 환경 설정 (가상환경 생성, 패키지 설치, Jupyter 커널 등록, 데이터 폴더 구조 생성) |
| `scripts/run_analysis.sh` | 분석 실행 스크립트 (3가지 옵션: Jupyter 브라우저 / nbconvert 직접 실행 / Python 스크립트 변환) |

---

## 데이터셋 정보

**출처**: CDC BRFSS (Behavioral Risk Factor Surveillance System) 2020
**Kaggle**: Personal Key Indicators of Heart Disease
**규모**: 319,795명 / 18개 변수 / 결측치 0%

### 주요 변수

| 역할 | 변수명 | 설명 |
|------|--------|------|
| 종속변수 (Y) | `Stroke` | 뇌졸중 여부 (Yes/No) |
| 독립변수 (X) | `Smoking` | 흡연 여부 - 생애 100개비 이상 (Yes/No) |
| 교란변수 | `AgeCategory` | 나이대 (18-24 ~ 80+, 13개 범주) |
| | `Sex` | 성별 (Male/Female) |
| | `BMI` | 체질량지수 |
| | `PhysicalActivity` | 신체활동 여부 |
| | `AlcoholDrinking` | 음주 여부 |
| | `GenHealth` | 주관적 건강 상태 |

---

## 분석 파이프라인

```
STEP 1-5   데이터 탐색 및 전처리
           ├── 데이터 로드 및 기본 구조 파악
           ├── 결측치 확인 (0%)
           ├── 이상치 탐지 (IQR 방법) → BMI 이상치 유지 결정
           └── 변수 인코딩 (범주형 → 수치형)

STEP 6-7   기술통계 및 단변량 분석
           ├── 흡연 상태별 뇌졸중 발생률 비교
           ├── 카이제곱 검정
           ├── Cramer's V (효과 크기)
           └── Mann-Whitney U 검정 (BMI)

STEP 8     다변량 로지스틱 회귀분석
           ├── Model 1: 비보정 모델 (Crude OR)
           ├── Model 2: 인구학적 변수 보정 (나이, 성별)
           └── Model 3: 완전 보정 모델 (Full Model)

STEP 9     상호작용 효과 분석
           ├── Smoking x PhysicalActivity 상호작용 검정
           ├── 층화 분석 (신체활동 유무별)
           └── 4분류 분석 (흡연 x 신체활동 조합)

STEP 10-11 모델 진단 및 결론
           ├── 다중공선성 확인 (VIF)
           ├── 모델 적합도 (Pseudo R-squared)
           └── ROC-AUC 평가

STEP 12-15 고급 분석
           ├── 상관관계 히트맵, 바이올린 플롯
           ├── 머신러닝 모델 비교 (LR, RF, XGBoost, SVM)
           ├── PyTorch 딥러닝 (Focal Loss, 앙상블)
           └── 5-Fold 교차검증
```

---

## 핵심 분석 결과

### 기술통계

| 그룹 | 뇌졸중 발생률 |
|------|--------------|
| 흡연자 | 5.17% |
| 비흡연자 | 2.80% |
| 비율 | 흡연자가 약 **1.85배** 높음 |

### 다변량 로지스틱 회귀

| 모델 | 보정 변수 | Odds Ratio (OR) |
|------|----------|-----------------|
| Model 1 | 없음 (Crude) | ~1.9 |
| Model 2 | 나이, 성별 | ~1.2 |
| Model 3 | 전체 교란변수 | ~1.1 |

- 교란변수(특히 나이)를 통제하면 OR이 감소하지만, 여전히 유의한 연관성 유지

### 상호작용 효과

- 신체활동 있는 그룹: 흡연의 영향이 상대적으로 낮음
- 신체활동 없는 그룹: 흡연의 영향이 더 크게 나타남
- 신체활동이 흡연의 부정적 영향을 일부 완화하는 조절 효과 가능성

### 모델 진단

| 지표 | 결과 |
|------|------|
| VIF | < 5 (다중공선성 없음) |
| Pseudo R-squared | 0.2 ~ 0.4 (적절한 적합도) |
| AUC | 평가 완료 |

### 핵심 결론

> "흡연은 나이, 성별, BMI, 음주, 신체활동 등을 통제한 후에도 뇌졸중 발생 위험을 높이는 **독립적인 위험 요인**이다."

### 연구 가설 검증

| 가설 | 결과 |
|------|------|
| H1: 흡연자의 뇌졸중 발생률이 높다 | 지지됨 (1.85배) |
| H2: 교란변수 보정 후에도 연관성 유지 | 지지됨 (OR ~1.1, p < 0.05) |
| H3: 흡연 + 신체활동 부족 시 위험 최대 | 지지됨 |

### 연구 한계

| 한계 | 설명 |
|------|------|
| 횡단면 데이터 | 인과관계 추론 불가 (연관성만 확인) |
| 자기보고 데이터 | 흡연/뇌졸중 여부의 정확성 문제 |
| 잔여 교란 | 유전적 요인 등 미측정 변수 존재 가능 |
| 클래스 불균형 | 뇌졸중 환자가 전체의 3.8%로 매우 적음 |

---

## 기술 스택

### 데이터 분석

| 라이브러리 | 용도 |
|-----------|------|
| Pandas | 데이터 처리 및 조작 |
| NumPy | 수치 연산 |
| Statsmodels | 통계 분석 및 로지스틱 회귀 |
| SciPy | 통계 검정 (카이제곱, Mann-Whitney U) |

### 시각화

| 라이브러리 | 용도 |
|-----------|------|
| Matplotlib | 기본 시각화 |
| Seaborn | 통계적 시각화 |

### 머신러닝 및 딥러닝

| 라이브러리 | 용도 |
|-----------|------|
| Scikit-learn | Logistic Regression, Random Forest, SVM |
| XGBoost | 그래디언트 부스팅 |
| PyTorch | 딥러닝 신경망 (GPU/MPS 가속 지원) |
| imbalanced-learn | SMOTE (클래스 불균형 처리) |

---

## 실행 방법

### 방법 1: 자동 스크립트

```bash
# 초기 설정 (1회)
chmod +x scripts/setup.sh && ./scripts/setup.sh

# 분석 실행
chmod +x scripts/run_analysis.sh && ./scripts/run_analysis.sh
```

### 방법 2: 수동 실행

```bash
# 패키지 설치
pip install -r requirements.txt

# Jupyter 실행
jupyter notebook code/smoking_stroke_analysis_reorganized.ipynb
```

### 실행 환경별 설정

| 환경 | 설정 |
|------|------|
| Google Colab | 드라이브 마운트 후 경로 설정 |
| 로컬 (Mac) | MPS 가속 자동 감지 |
| 로컬 (NVIDIA GPU) | CUDA 가속 자동 감지 |
