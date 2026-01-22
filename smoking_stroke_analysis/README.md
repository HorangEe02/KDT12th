# 🏥 흡연이 뇌졸중 발생에 미치는 영향 분석

> **의료 통계 미니 프로젝트** | CDC BRFSS 2020 데이터를 활용한 흡연과 뇌졸중의 연관성 분석

## 📋 프로젝트 개요

본 프로젝트는 **흡연이 뇌졸중 발생에 미치는 영향**을 통계적으로 분석하고, 다양한 교란변수를 통제한 후에도 흡연이 독립적인 위험 요인인지 검증합니다. 단순 기술통계부터 다변량 로지스틱 회귀, 머신러닝, 딥러닝까지 다양한 분석 기법을 적용하여 종합적인 결론을 도출합니다.

### 🎯 연구 질문

> *"흡연은 나이, 성별, BMI, 음주, 신체활동 등 다른 요인들을 고려한 후에도 뇌졸중 발생 위험을 높이는가?"*

## 📊 데이터셋

| 항목 | 내용 |
|------|------|
| **데이터 출처** | [Kaggle - Personal Key Indicators of Heart Disease](https://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease) |
| **원본 출처** | CDC BRFSS (Behavioral Risk Factor Surveillance System) 2020 |
| **데이터 크기** | 319,795명 |
| **변수 개수** | 18개 (수치형 4개, 범주형 14개) |
| **결측치** | 0% (완벽한 데이터) |

### 주요 변수 설명

| 역할 | 변수명 | 설명 |
|------|--------|------|
| **종속변수 (Y)** | `Stroke` | 뇌졸중 여부 (Yes/No) |
| **독립변수 (X)** | `Smoking` | 흡연 여부 (Yes/No) |
| **교란변수** | `Sex` | 성별 |
| | `AgeCategory` | 나이대 (18-24 ~ 80+) |
| | `BMI` | 체질량지수 |
| | `PhysicalActivity` | 신체활동 여부 |
| | `AlcoholDrinking` | 음주 여부 |
| | `GenHealth` | 주관적 건강 상태 |

## 🔬 분석 방법론

### 분석 파이프라인

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1-5: 데이터 탐색 및 전처리                                      │
│  ├── 데이터 로드 및 기본 구조 파악                                     │
│  ├── 결측치 확인 (0%)                                                │
│  ├── 이상치 탐지 (IQR 방법) → BMI 이상치 유지 결정                     │
│  └── 변수 인코딩 (범주형 → 수치형)                                    │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 6-7: 기술통계 및 단변량 분석                                    │
│  ├── 흡연 상태별 뇌졸중 발생률 비교                                    │
│  ├── 카이제곱 검정 (χ² test)                                         │
│  ├── Cramér's V (효과 크기)                                          │
│  └── Mann-Whitney U 검정 (BMI)                                       │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 8: 다변량 로지스틱 회귀분석                                      │
│  ├── Model 1: 비보정 모델 (Crude OR)                                 │
│  ├── Model 2: 인구학적 변수 보정 (나이, 성별)                          │
│  └── Model 3: 완전 보정 모델 (Full Model)                             │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 9: 상호작용 효과 분석                                           │
│  ├── Smoking × PhysicalActivity 상호작용 검정                        │
│  ├── 층화 분석 (신체활동 유무별)                                       │
│  └── 4분류 분석 (흡연 × 신체활동 조합)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 10-11: 모델 진단 및 결론                                        │
│  ├── 다중공선성 확인 (VIF)                                            │
│  ├── 모델 적합도 (Pseudo R²)                                         │
│  └── ROC-AUC 평가                                                    │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 12-15: 고급 분석                                               │
│  ├── 상관관계 히트맵, 바이올린 플롯                                    │
│  ├── 머신러닝 모델 비교 (LR, RF, XGBoost, SVM)                        │
│  ├── PyTorch 딥러닝 (Focal Loss, 앙상블)                              │
│  └── 5-Fold 교차검증                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## 📈 주요 분석 결과

### 1. 기술통계

| 그룹 | 뇌졸중 발생률 |
|------|--------------|
| 흡연자 | **5.17%** |
| 비흡연자 | **2.80%** |
| **비율** | 흡연자가 약 **1.85배** 높음 |

### 2. 단변량 분석 (카이제곱 검정)

- **결과**: 흡연과 뇌졸중 간 통계적으로 유의한 연관성 존재
- **p-value**: < 0.05
- **Cramér's V**: 효과 크기 측정

### 3. 다변량 로지스틱 회귀분석

| 모델 | 보정 변수 | Odds Ratio (OR) |
|------|----------|-----------------|
| Model 1 | 없음 (Crude) | ~1.9 |
| Model 2 | 나이, 성별 | ~1.2 |
| Model 3 | 전체 교란변수 | **~1.1** |

> 💡 교란변수(특히 나이)를 통제하면 OR이 감소하지만, 여전히 유의한 연관성 유지

### 4. 상호작용 효과

- **신체활동 있는 그룹**: 흡연의 영향이 상대적으로 낮음
- **신체활동 없는 그룹**: 흡연의 영향이 더 크게 나타남
- 신체활동이 흡연의 부정적 영향을 일부 완화하는 조절 효과 가능성

### 5. 모델 진단

| 지표 | 결과 | 해석 |
|------|------|------|
| VIF | < 5 | 다중공선성 없음 ✅ |
| Pseudo R² | 0.2 ~ 0.4 | 적절한 모델 적합도 |
| AUC | 평가 완료 | 예측력 확인 |

## 🛠️ 기술 스택

### 언어 및 환경
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=flat-square&logo=jupyter&logoColor=white)

### 데이터 분석
- **Pandas**: 데이터 처리 및 조작
- **NumPy**: 수치 연산
- **Statsmodels**: 통계 분석 및 로지스틱 회귀
- **SciPy**: 통계 검정 (카이제곱, Mann-Whitney U)

### 시각화
- **Matplotlib**: 기본 시각화
- **Seaborn**: 통계적 시각화

### 머신러닝 & 딥러닝
- **Scikit-learn**: ML 모델 (Logistic Regression, Random Forest, SVM)
- **XGBoost**: 그래디언트 부스팅
- **PyTorch**: 딥러닝 신경망 (GPU/MPS 가속 지원)
- **imbalanced-learn**: SMOTE (클래스 불균형 처리)

## 📁 프로젝트 구조

```
smoking_stroke_analysis/
│
├── 📓 smoking_stroke_analysis.ipynb    # 메인 분석 노트북
│
├── 📂 data/
│   └── 2020/
│       └── heart_2020_cleaned.csv      # 원본 데이터
│
├── 📂 images/                          # 시각화 결과물
│   ├── data_overview.png               # 데이터 전체 구조
│   ├── missing_value.png               # 결측치 분석
│   ├── find_outliers.png               # 이상치 탐지
│   └── use_plot.png                    # 변수 분포
│
└── 📄 README.md                        # 프로젝트 설명서
```

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 필수 라이브러리 설치
pip install pandas numpy matplotlib seaborn statsmodels scipy
pip install scikit-learn xgboost imbalanced-learn
pip install torch  # PyTorch (GPU 가속 시 CUDA 버전 설치)
```

### 2. 데이터 다운로드

[Kaggle 데이터셋](https://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease)에서 `heart_2020_cleaned.csv` 파일을 다운로드하여 `data/2020/` 폴더에 저장합니다.

### 3. 노트북 실행

```bash
jupyter notebook smoking_stroke_analysis.ipynb
```

### 4. 환경별 설정

| 환경 | 설정 |
|------|------|
| **Google Colab** | 드라이브 마운트 후 경로 설정 |
| **로컬 (Mac)** | MPS 가속 자동 감지 |
| **로컬 (NVIDIA GPU)** | CUDA 가속 자동 감지 |

## 📌 핵심 결론

> ### 💡 "흡연은 나이, 성별, BMI, 음주, 신체활동 등을 통제한 후에도 뇌졸중 발생 위험을 높이는 **독립적인 위험 요인**이다."

### 주요 발견

1. **흡연자의 뇌졸중 발생률**이 비흡연자보다 약 1.85배 높음
2. 교란변수 통제 후에도 **유의한 연관성 유지** (OR ≈ 1.1)
3. **신체활동**이 흡연의 부정적 영향을 일부 완화할 가능성
4. **나이**가 가장 강력한 교란변수로 작용

## ⚠️ 연구의 한계점

| 한계 | 설명 |
|------|------|
| **횡단면 데이터** | 인과관계 추론에 제한 (연관성만 확인 가능) |
| **자기보고 데이터** | 흡연, 뇌졸중 여부 등이 자기보고 방식으로 수집되어 정확성 문제 |
| **잔여 교란** | 측정되지 않은 교란변수(유전적 요인 등)의 영향 가능성 |
| **클래스 불균형** | 뇌졸중 환자가 전체의 3.8%로 매우 적음 |

## 📚 참고 자료

- [CDC BRFSS](https://www.cdc.gov/brfss/index.html) - 원본 데이터 출처
- [Kaggle Dataset](https://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease) - 정제된 데이터
- [Statsmodels Documentation](https://www.statsmodels.org/) - 로지스틱 회귀
- [PyTorch Documentation](https://pytorch.org/docs/) - 딥러닝 모델

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 작성되었습니다.

---

**📅 작성일**: 2025년 1월  
**🔧 분석 도구**: Python, Pandas, Scikit-learn, PyTorch, Statsmodels  
**👤 작성자**: Yeong
