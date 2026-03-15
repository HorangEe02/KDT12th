# 소주제 4 — 최적 발주 전략 클러스터링 (Regression + Clustering) 구현 가이드

> 원본 E-Grocery 데이터 심화 분석 (보충 데이터 미사용 버전)
> 이전 버전(V2~V3)에서 DataCo·Instacart 등 외부 데이터셋을 병렬 분석하던 방식을 폐기하고,
> **원본 데이터의 풍부한 발주 관련 컬럼을 최대한 활용하는 피처 엔지니어링 중심**으로 재설계하였다.
>
> **최종 수정일:** 2026-03-13
>
> **[변경 이력]** V4 대비 변경사항
>
> - 보충 데이터(pricing_optimization.csv, supply_chain_dataset1.csv) 미사용
> - Phase D(보충 데이터 검증) 삭제
> - EOQ 가정(S=50 USD, H=20%)은 산업 표준으로 유지 (외부 검증 없음)
> - 파생변수 10개, Phase B Enhanced 피처 13개 유지
> - ★ 추가 분석 항목 4종 유지: Learning Curve, Permutation Importance, Residual Analysis, Hopkins Statistic

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열)
- 소주제 4 담당: 박준영 (팀장)

### 1.2 프로젝트 디렉토리 구조

```
Phase8_mini/
├── data/
│   └── Supply Chain Inventory Management Grocery Industry/
│       └── Inventory Management E-Grocery - InventoryData.csv   ← 원본 데이터
├── notebooks/
│   └── 04_Reorder_Strategy_Clustering_V5.ipynb                   ← 본 가이드라인 구현 노트북
├── outputs/
│   ├── figures/    ← 시각화 21종 (*_v5_s4.png)
│   └── models/     ← 학습 모델·스케일러 (*.pkl, *.json)
├── md/
│   ├── subtopic4_guideline_v5.md                                 ← 본 문서
│   └── result_report/
│       └── subtopic4_report_v5.md                                ← 결과 보고서
└── 휴지통/                                                        ← 이전 버전 파일 보관
```

### 1.3 소주제 4 목표

재고 보유일수(Days_of_Inventory)를 예측하는 **회귀 모델(Phase A)**을 구축하고, 제품군을 발주 특성에 따라 **K-Means 클러스터링(Phase B)**으로 군집화하여, 군집별 차별화된 발주 전략을 제안한다. 추가로 **EOQ(경제적 발주량) 시뮬레이션(Phase C)**을 통해 군집별 최적 발주량을 수치로 산출한다.

> 소주제 4는 **지도학습(회귀) + 비지도학습(클러스터링) + 시뮬레이션(EOQ)**을 결합하며,
> 프로젝트 전체의 **최종 액션 플랜**을 도출하는 마무리 역할을 한다.

### 1.4 도출할 인사이트

- 제품 속성만으로 재고 보유일수를 어느 정도 예측할 수 있는가?
- **DOI = QOH / ADS 관계가 존재하는 상황에서, 피처 선택을 어떻게 해야 하는가? (Data Leakage)**
- 제품군은 발주 특성에 따라 몇 개의 군집으로 구분되는가?
- 각 군집의 특성과 군집별 차별화된 발주 전략은?
- ABC 등급별 군집 분포와 발주 전략의 연관성은?
- Baseline(7피처) vs Enhanced(13피처) 클러스터링 — 파생변수 추가가 군집 분리를 개선하는가?
- 소주제 1의 핵심 피처(Available_Stock)가 발주 군집 분류에도 유효한가?
- EOQ 기반 최적 발주량을 군집별로 수치 제안할 수 있는가?
- 소주제 1~3의 결과를 종합하면 어떤 통합적 재고 관리 전략을 도출할 수 있는가?

---

## 2. 데이터 명세

### 2.1 원본 데이터 (유일 사용)

- **파일:** `Inventory Management E-Grocery - InventoryData.csv`
- **경로:** `data/Supply Chain Inventory Management Grocery Industry/`
- **규모:** 1,000행 × 37열
- **결측치:** Notes 컬럼 834건 (분석 미사용), 실질적 결측치 이슈 없음
- **Phase A 타겟:** Days_of_Inventory (연속형, 쉼표 소수점)
- **로케일:** 인도네시아 형식 (쉼표=소수점, 마침표=천단위)

### 2.2 소주제 4 사용 컬럼 (37열 중 선별)

| #   | 컬럼명                    | 타입         | 전처리             | Phase A |  Phase B  | Phase C |
| --- | ------------------------- | ------------ | ------------------ | :-----: | :-------: | :-----: |
| 3   | Category                  | object       | 인코딩             | ✅ OHE  |  ✅ 해석  | ✅ 해석 |
| 4   | ABC_Class                 | object       | 인코딩             | ✅ OHE  |  ✅ 해석  | ✅ 해석 |
| 14  | Quantity_On_Hand          | int          | -                  | ⚠️ 누수 |  ✅ 피처  | ✅ EOQ  |
| 19  | Avg_Daily_Sales           | object→float | 쉼표→마침표        | ⚠️ 누수 | ✅ 피처\* | ✅ EOQ  |
| 21  | **Days_of_Inventory**     | object→float | 쉼표→마침표        | 🎯 타겟 |  ✅ 피처  |    -    |
| 22  | Reorder_Point             | float→int    | 천단위 오파싱 수정 | ✅ 피처 |  ✅ 피처  |    -    |
| 23  | Safety_Stock              | int          | -                  | ✅ 피처 |  ✅ 피처  | ✅ EOQ  |
| 24  | Lead_Time_Days            | int          | -                  | ✅ 피처 |  ✅ 피처  |    -    |
| 25  | Unit_Cost_USD             | object→float | $, 쉼표, 마침표    | ✅ 피처 |     -     | ✅ EOQ  |
| 29  | Order_Frequency_per_month | object→float | 쉼표→마침표        | ✅ 피처 |  ✅ 피처  |    -    |
| 30  | Supplier_OnTime_Pct       | object→float | % 제거, 쉼표       | ✅ 피처 |  ✅ 피처  |    -    |

> \*Phase B에서 Avg_Daily_Sales 사용 가능: 비지도학습은 타겟이 없으므로 Leakage 개념 비적용

### 2.3 Phase A 타겟 변수: Days_of_Inventory

| 항목     | 내용                                                             |
| -------- | ---------------------------------------------------------------- |
| 타입     | 연속형 (float, 쉼표 소수점 → 전처리 필요)                        |
| 의미     | 현재 재고로 판매 지속 가능 일수                                  |
| **수식** | **DOI = Quantity_On_Hand / Avg_Daily_Sales** (97.2% 일치 확인)   |
| **분포** | mean=9.99, median=9.98, std=3.80, min=0.00, max=21.95, skew=0.12 |
| 해석     | 값이 높을수록 재고 장기 보유, 낮을수록 빠른 소진                 |

> ⚠️ **핵심 — DOI = QOH / ADS 관계 (Data Leakage)**
>
> - QOH와 ADS를 동시에 Phase A 피처로 사용 → R²=0.92 (Leakage: 나눗셈 공식 학습)
> - QOH+ADS 제거 + Category+ABC → **R²≈0.25** (실질적 예측력)
> - 노트북에서 Leakage 진단 → 시나리오 비교 → 대응 과정을 반드시 시연

---

## 3. 전처리 파이프라인

### 3.1 공통 전처리 (인도네시아 로케일)

```python
import pandas as pd
import numpy as np
import csv
import os
import warnings
warnings.filterwarnings('ignore')

# ── 경로 설정 ──
DATA_DIR = '../data/Supply Chain Inventory Management Grocery Industry'
FIG_DIR = '../outputs/figures'
MODEL_DIR = '../outputs/models'
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# 0. 데이터 로드
csv_path = f'{DATA_DIR}/Inventory Management E-Grocery - InventoryData.csv'
df = pd.read_csv(csv_path)

# 1. 인도네시아 로케일 숫자 변환
#    ⚠️ 순서 중요: 천단위 마침표(.) 제거 → 쉼표 소수점(,) → 마침표(.)
comma_decimal_cols = [
    'Avg_Daily_Sales', 'Days_of_Inventory',
    'SKU_Churn_Rate', 'Order_Frequency_per_month'
]
for col in comma_decimal_cols:
    df[col] = (df[col].astype(str)
               .str.replace('.', '', regex=False)
               .str.replace(',', '.', regex=False)
               .astype(float))

# 1-1. Reorder_Point 특수 처리
raw_rp = []
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        raw_rp.append(row['Reorder_Point'])
df['Reorder_Point'] = [int(v.replace('.', '')) if '.' in v else int(v) for v in raw_rp]

# 2. 금액 컬럼 변환
money_cols = ['Unit_Cost_USD', 'Last_Purchase_Price_USD', 'Total_Inventory_Value_USD']
for col in money_cols:
    df[col] = (df[col].astype(str)
               .str.replace('$', '', regex=False)
               .str.replace('.', '', regex=False)
               .str.replace(',', '.', regex=False)
               .astype(float))

# 3. 퍼센트 컬럼 변환
pct_cols = ['Supplier_OnTime_Pct', 'Audit_Variance_Pct', 'Demand_Forecast_Accuracy_Pct']
for col in pct_cols:
    df[col] = (df[col].astype(str)
               .str.replace('%', '', regex=False)
               .str.replace(',', '.', regex=False)
               .astype(float))

# 4. 날짜 컬럼 파싱
for col in ['Received_Date', 'Last_Purchase_Date', 'Expiry_Date', 'Audit_Date']:
    df[col] = pd.to_datetime(df[col])
```

### 3.2 전처리 결과 검증

```python
print("=== 전처리 검증 ===")
print(f"Shape: {df.shape}")
print(f"\nDays_of_Inventory: mean={df['Days_of_Inventory'].mean():.2f}, "
      f"min={df['Days_of_Inventory'].min():.2f}, max={df['Days_of_Inventory'].max():.2f}")
print(f"Avg_Daily_Sales: mean={df['Avg_Daily_Sales'].mean():.2f}")
print(f"Unit_Cost_USD: mean={df['Unit_Cost_USD'].mean():.2f}")
print(f"Reorder_Point: mean={df['Reorder_Point'].mean():.1f}, max={df['Reorder_Point'].max()}")
```

---

## 4. 파생변수 엔지니어링

> **핵심 원칙:** 모든 파생변수는 **원본 37열의 실측치**에서 산출한다.

### 4.1 발주 전략 파생변수 (10개)

```python
# 1. Dynamic_ROP = ADS × LT + SS
df['Dynamic_ROP'] = df['Avg_Daily_Sales'] * df['Lead_Time_Days'] + df['Safety_Stock']

# 2. ROP_Gap = RP - Dynamic_ROP
df['ROP_Gap'] = df['Reorder_Point'] - df['Dynamic_ROP']

# 3. Stock_Coverage_Days = (QOH - SS) / ADS
ads_safe = df['Avg_Daily_Sales'].replace(0, np.nan)
df['Stock_Coverage_Days'] = (
    (df['Quantity_On_Hand'] - df['Safety_Stock']) / ads_safe
).fillna(0).clip(-100, 365)

# 4. Demand_Variability (카테고리 내 수요 CV)
#    ⚠️ 한계: CV 0.52~0.56으로 매우 균질 → 변별력 낮음
cat_stats = df.groupby('Category')['Avg_Daily_Sales'].agg(['mean', 'std'])
cat_stats['CV'] = cat_stats['std'] / cat_stats['mean']
df['Demand_Variability'] = df['Category'].map(cat_stats['CV'])

# 5. EOQ = √(2×D×S/H)
ORDERING_COST = 50   # USD (산업 표준 가정)
HOLDING_RATE = 0.20  # 단가 대비 보유비용 비율 (산업 표준 가정)
df['Annual_Demand'] = df['Avg_Daily_Sales'] * 365
df['Holding_Cost'] = df['Unit_Cost_USD'] * HOLDING_RATE
df['EOQ'] = np.sqrt(2 * df['Annual_Demand'] * ORDERING_COST / df['Holding_Cost'].replace(0, 1))

# 6. Reorder_Urgency = (QOH ≤ RP)
df['Reorder_Urgency'] = (df['Quantity_On_Hand'] <= df['Reorder_Point']).astype(int)

# 7. Supply_Risk = LT × (1 - SOTP/100)
df['Supply_Risk'] = df['Lead_Time_Days'] * (1 - df['Supplier_OnTime_Pct'] / 100)

# 8. Order_Efficiency = QOH / EOQ
df['Order_Efficiency'] = (df['Quantity_On_Hand'] / df['EOQ'].replace(0, np.nan)).fillna(1).clip(0, 10)

# 9. Available_Stock = QOH - RP (소주제 1 연계)
df['Available_Stock'] = df['Quantity_On_Hand'] - df['Reorder_Point']

# 10. RP_SS_Ratio = RP / SS
df['RP_SS_Ratio'] = (df['Reorder_Point'] / df['Safety_Stock'].replace(0, np.nan)).fillna(0).clip(0, 10)
```

### 4.2 파생변수 요약

| #      | 변수명              | 원본 컬럼 사용  | 발주 전략 의미                  |  Phase B 사용  |
| ------ | ------------------- | --------------- | ------------------------------- | :------------: |
| 1      | Dynamic_ROP         | ADS, LT, SS     | 수요 기반 재주문점              |       ✅       |
| 2      | ROP_Gap             | RP, Dynamic_ROP | 재주문 설정 보수성              |       -        |
| 3      | Stock_Coverage_Days | QOH, SS, ADS    | 안전재고 초과 커버 일수         |       -        |
| 4      | Demand_Variability  | ADS, Category   | 수요 불확실성                   | ⚠️ 낮은 변별력 |
| 5      | EOQ                 | ADS, Unit_Cost  | 비용 최적 발주량                |       ✅       |
| 6      | Reorder_Urgency     | QOH, RP         | 즉시 발주 필요 여부             |       -        |
| 7      | Supply_Risk         | LT, SOTP        | 공급 리스크                     |       ✅       |
| 8      | Order_Efficiency    | QOH, EOQ        | EOQ 대비 재고 비율              |       -        |
| **9**  | **Available_Stock** | **QOH, RP**     | **재주문점 대비 재고 여유**     |     **✅**     |
| **10** | **RP_SS_Ratio**     | **RP, SS**      | **안전재고 대비 재주문점 비율** |     **✅**     |

> ⚠️ **EOQ 가정 문서화:**
>
> - 발주 비용(S) = 50 USD/회: 식료품 유통의 일반적 발주 처리 비용 가정
> - 보유 비용(H) = Unit_Cost_USD × 20%: 산업 표준 15~25% 범위 중간값
> - V5에서는 외부 데이터를 사용하지 않으므로, 산업 표준 가정으로 유지

### 4.3 인코딩

```python
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

---

## 5. 데이터 누수(Data Leakage) 진단

> ⚠️ **Phase A의 핵심 이슈: DOI = QOH / ADS**

### 5.1 검증 결과

| 시나리오 | 포함 피처                      |    R²    | 해석                          |
| -------- | ------------------------------ | :------: | ----------------------------- |
| S1       | 전체 8개 수치 (QOH+ADS 포함)   |   0.92   | 🔴 Leakage — 나눗셈 공식 학습 |
| S2       | ADS 제거 (QOH만 포함)          |   0.55   | 🟡 부분 Leakage               |
| S3       | QOH 제거 (ADS만 포함)          |  -0.04   | ❌ 예측력 없음                |
| S4       | QOH+ADS 모두 제거              |  -0.08   | ❌ 예측력 없음                |
| **S5**   | **S4 + Category + ABC 인코딩** | **0.25** | **✅ 채택**                   |

### 5.2 노트북에서 보여줄 진단 내용

1. `DOI ≈ QOH / ADS` 수치 검증 (산점도 + 일치율 97.2%)
2. Scenario별 R² 비교 바 차트 (S1~S5)
3. QOH+ADS 포함/제거 시 Feature Importance 변화
4. 최종 피처셋 결정 근거 문서화

---

## 6. Phase A — 재고 보유일수 예측 (Regression)

### 6.1 목표

제품 속성을 기반으로 **Days_of_Inventory**를 예측하고, **Feature Importance를 통해 보유일수 결정 요인을 파악**한다.

> Phase A의 핵심 가치는 R² 높이기가 아니라, **어떤 변수가 DOI에 영향을 주는지** 해석하는 것

### 6.2 피처 목록 — Baseline vs Enhanced

#### Baseline 피처셋 (17개)

```python
baseline_numeric_A = [
    'Unit_Cost_USD', 'Reorder_Point', 'Safety_Stock',
    'Lead_Time_Days', 'Order_Frequency_per_month', 'Supplier_OnTime_Pct'
]
# + Category OHE 9개 + ABC OHE 2개 = 17개
```

#### Enhanced 피처셋 (최대 22개)

```python
enhanced_numeric_A = baseline_numeric_A + [
    'Demand_Variability',   # ⚠️ 변별력 낮음
    'Supply_Risk',
    'EOQ',
    'Reorder_Urgency',
    'RP_SS_Ratio',          # 재주문점/안전재고 비율
]
# + Category OHE 9개 + ABC OHE 2개 = 최대 22개
```

### 6.3 학습 모델 (3종) — Default → Tuned

| #   | 모델              | Default 파라미터                                  | 역할            |
| --- | ----------------- | ------------------------------------------------- | --------------- |
| 1   | Linear Regression | default                                           | Baseline        |
| 2   | Random Forest     | `n_estimators=100`, `random_state=42`             | 앙상블 (배깅)   |
| 3   | XGBoost           | `objective='reg:squarederror'`, `random_state=42` | 앙상블 (부스팅) |

### 6.4 하이퍼파라미터 튜닝 (GridSearchCV)

| 모델 | 파라미터         | 범위              |
| ---- | ---------------- | ----------------- |
| RF   | n_estimators     | [100, 200, 300]   |
| RF   | max_depth        | [5, 10, 15, None] |
| RF   | min_samples_leaf | [2, 5, 10]        |
| XGB  | max_depth        | [3, 5, 7]         |
| XGB  | learning_rate    | [0.01, 0.05, 0.1] |
| XGB  | n_estimators     | [100, 200]        |
| XGB  | reg_alpha        | [0, 0.5, 1.0]     |
| XGB  | reg_lambda       | [1.0, 5.0, 10.0]  |

### 6.5 평가 지표

| 지표         | 설명                             |
| ------------ | -------------------------------- |
| **R² Score** | 분산 설명력                      |
| **RMSE**     | 예측 오차 크기                   |
| **MAE**      | 평균 절대 오차                   |
| **Gap**      | Train R² - Test R² (과적합 정도) |

### 6.6 Learning Curve (과적합 시각 진단) ★

```python
from sklearn.model_selection import learning_curve

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
models_lc = {
    'LR': LinearRegression(),
    'RF': RandomForestRegressor(**best_rf_params, random_state=42),
    'XGB': XGBRegressor(**best_xgb_params, random_state=42, verbosity=0),
}
for ax, (name, model) in zip(axes, models_lc.items()):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_enhanced_scaled, y, cv=5, scoring='r2',
        train_sizes=np.linspace(0.1, 1.0, 10), random_state=42
    )
    # Train / Val 학습 곡선 + 신뢰구간 시각화
plt.savefig(f'{FIG_DIR}/learning_curve_phaseA_v5_s4.png', dpi=150, bbox_inches='tight')
```

> **해석 기준:** Gap > 0.15이면 과적합 의심.

### 6.7 Permutation Importance (피처 중요도 교차검증) ★

```python
from sklearn.inspection import permutation_importance

perm_result = permutation_importance(
    best_model_enhanced, X_test_enh_scaled, y_test,
    n_repeats=10, random_state=42, scoring='r2'
)
# Impurity 기반 vs Permutation 비교 (side-by-side barh)
```

> **목적:** Impurity 기반 Feature Importance는 높은 카디널리티 피처에 편향될 수 있음.
> Permutation Importance는 이를 교차검증.

### 6.8 Residual Analysis (잔차 정규성 검정) ★

```python
from scipy.stats import shapiro

residuals = y_test - best_model_enhanced.predict(X_test_enh_scaled)
# Q-Q Plot + 잔차 히스토그램 + 잔차 vs 예측값 산점도 (1×3 서브플롯)
stat, p_value = shapiro(residuals)
# Shapiro-Wilk 검정 결과 출력
plt.savefig(f'{FIG_DIR}/residual_analysis_phaseA_v5_s4.png', dpi=150, bbox_inches='tight')
```

### 6.9 기대 성능

| 피처셋                 |  예상 R²   | 비고                 |
| ---------------------- | :--------: | -------------------- |
| Leakage 포함 (QOH+ADS) |   ~0.92    | ⚠️ 비현실적 (진단용) |
| Baseline (17피처)      |   ~0.25    | 실질적 예측력        |
| Enhanced (22피처)      | ~0.28~0.32 | 파생변수 기여도 확인 |

---

## 7. Phase B — 발주 전략 클러스터링 (핵심)

### 7.1 목표

제품을 발주 관련 속성에 따라 **자연스러운 군집**으로 분류하고, 군집별 특성을 해석하여 **차별화된 발주 전략**을 제안한다.

> Phase B가 소주제 4의 **핵심 분석**이다.

### 7.2 클러스터링 피처 — Baseline vs Enhanced

#### Baseline 피처 (7개)

```python
baseline_cluster_features = [
    'Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock',
    'Days_of_Inventory', 'Order_Frequency_per_month',
    'Lead_Time_Days', 'Supplier_OnTime_Pct',
]
```

#### Enhanced 피처 (13개)

```python
enhanced_cluster_features = baseline_cluster_features + [
    'Dynamic_ROP', 'Demand_Variability', 'EOQ',
    'Supply_Risk', 'Available_Stock', 'RP_SS_Ratio',
]
```

### 7.3 Hopkins Statistic (클러스터링 경향성 검정) ★

> 데이터에 실제 군집 구조가 존재하는지 통계적으로 검증한다. K-Means를 적용하기 **전에** 수행해야 하는 사전 검정.

```python
from sklearn.neighbors import NearestNeighbors

def hopkins_statistic(X, sample_size=None, random_state=42):
    """Hopkins Statistic 계산 (0.5=균일분포, 1.0=강한 군집 경향)"""
    # ... 10회 반복 평균·표준편차 보고
```

> **해석 기준:**
>
> - H > 0.75: 강한 군집 경향 → K-Means 적용 적절
> - 0.5 < H ≤ 0.75: 약한 군집 경향
> - H ≤ 0.5: 균일 분포 → 클러스터링 무의미

### 7.4 스케일링 + 최적 K 탐색

- StandardScaler 정규화 (전체 1,000행)
- K=2~7 범위에서 Elbow Method + Silhouette Score
- Silhouette 샘플 분석 (군집별 음수 비율)
- 클러스터링 안정성 검증 (랜덤 시드 5회)

### 7.5 군집 해석 + 발주 전략 제안

- Z-Score 기반 군집 네이밍 (데이터 드리븐)
- 레이더 차트로 군집별 프로파일 시각화
- 카테고리별·ABC별 군집 분포 교차 분석
- 군집별 수치 기반 발주 전략 제안

---

## 8. Phase C — EOQ 시뮬레이션 + 군집별 최적 발주량

### 8.1 EOQ 공식

$$
EOQ = \sqrt{\frac{2 \times D \times S}{H}}
$$

| 파라미터                  | 값                    | 근거                            |
| ------------------------- | --------------------- | ------------------------------- |
| D (연간 수요)             | Avg_Daily_Sales × 365 | 원본 실측치                     |
| S (1회 발주 비용)         | 50 USD                | 식료품 유통 업계 산업 표준 가정 |
| H (단위당 연간 보유 비용) | Unit_Cost_USD × 20%   | 산업 표준 15~25% 중간값         |

### 8.2 분석 내용

- 군집별 EOQ·연간발주횟수·총비용 산출
- EOQ 민감도 분석 (S = 25/50/75/100 USD 변화)

---

## 9. 시각화 요구사항 (총 21종)

### EDA & 진단 (5종)

| #   | 시각화                                    | 파일명                            |
| --- | ----------------------------------------- | --------------------------------- |
| 1   | Days_of_Inventory 분포 (히스토그램 + KDE) | `doi_distribution_v5_s4.png`      |
| 2   | 카테고리별·ABC별 보유일수 분포 (boxplot)  | `category_abc_doi_v5_s4.png`      |
| 3   | DOI vs QOH/ADS 일치 검증 산점도           | `leakage_diagnosis_v5_s4.png`     |
| 4   | Scenario별 R² 비교 바 차트 (S1~S5)        | `leakage_scenarios_v5_s4.png`     |
| 5   | 파생변수 분포 요약 (2×5 서브플롯)         | `derived_features_dist_v5_s4.png` |

### Phase A (4종)

| #   | 시각화                                   | 파일명                                  |
| --- | ---------------------------------------- | --------------------------------------- |
| 6   | Baseline vs Enhanced R² 비교 (그룹 막대) | `phaseA_baseline_vs_enhanced_v5_s4.png` |
| 7   | Default vs Tuned R² 비교                 | `phaseA_default_vs_tuned_v5_s4.png`     |
| 8   | 실제 vs 예측 산점도 (Enhanced 최적 모델) | `phaseA_actual_vs_predicted_v5_s4.png`  |
| 9   | Feature Importance (Enhanced 최적 모델)  | `phaseA_feature_importance_v5_s4.png`   |

### Phase A 추가 진단 ★ (3종)

| #   | 시각화                                 | 파일명                                     |
| --- | -------------------------------------- | ------------------------------------------ |
| 19  | Learning Curve (1×3 서브플롯) ★        | `learning_curve_phaseA_v5_s4.png`          |
| 20  | Permutation vs Impurity Importance ★   | `permutation_vs_impurity_phaseA_v5_s4.png` |
| 21  | Residual Analysis (Q-Q + 히스토그램) ★ | `residual_analysis_phaseA_v5_s4.png`       |

### Phase B (7종)

| #   | 시각화                                 | 파일명                              |
| --- | -------------------------------------- | ----------------------------------- |
| 10  | Elbow Method (Baseline + Enhanced)     | `phaseB_elbow_v5_s4.png`            |
| 11  | Silhouette Score (Baseline + Enhanced) | `phaseB_silhouette_v5_s4.png`       |
| 12  | PCA 2D 산점도 — Baseline               | `phaseB_pca_baseline_v5_s4.png`     |
| 13  | PCA 2D 산점도 — Enhanced               | `phaseB_pca_enhanced_v5_s4.png`     |
| 14  | 군집별 레이더 차트 (Enhanced)          | `phaseB_radar_enhanced_v5_s4.png`   |
| 15  | 카테고리별 군집 분포 (Stacked Bar)     | `phaseB_category_cluster_v5_s4.png` |
| 16  | ABC 등급별 군집 분포 (Stacked Bar)     | `phaseB_abc_cluster_v5_s4.png`      |

### Phase C + 종합 (2종)

| #   | 시각화                                       | 파일명                            |
| --- | -------------------------------------------- | --------------------------------- |
| 17  | 군집별 EOQ·안전재고·Dynamic ROP 비교 바 차트 | `phaseC_eoq_comparison_v5_s4.png` |
| 18  | 소주제 1~4 종합 연결 다이어그램              | `project_synthesis_v5_s4.png`     |

---

## 10. Jupyter Notebook 구조

```
04_Reorder_Strategy_Clustering_V5.ipynb
│
├── 0. 라이브러리 임포트 & 설정
├── 1. 데이터 로드 & 전처리 (인도네시아 로케일)
├── 2. EDA (#1~#2, 상관관계 히트맵)
├── 3. Data Leakage 진단 (#3~#4)
├── 4. 파생변수 엔지니어링 (#5)
│
│ ═══ Phase A: 재고 보유일수 예측 (Regression) ═══
├── 5. 피처/타겟 분리 & 전처리
├── 6. 모델 학습 & 평가
│   ├── Baseline / Enhanced 학습 (#6)
│   ├── GridSearchCV 튜닝 (#7)
│   ├── 최적 모델 선택 (#8, #9)
│   ├── ★ Learning Curve (#19)
│   ├── ★ Permutation Importance (#20)
│   └── ★ Residual Analysis (#21)
│
│ ═══ Phase B: 발주 전략 클러스터링 (핵심) ═══
├── 7. 클러스터링 피처 준비
├── 8. 최적 K 탐색
│   ├── ★ Hopkins Statistic
│   ├── Elbow + Silhouette (#10, #11)
│   └── 안정성 검증
├── 9. 클러스터링 실행 & 비교 (#12, #13)
├── 10. 군집 해석 & 발주 전략 (#14~#16)
│
│ ═══ Phase C: EOQ 시뮬레이션 ═══
├── 11. EOQ 군집별 산출 & 민감도 (#17)
│
│ ═══ 종합 ═══
├── 12. 소주제 1~4 연결 인사이트 (#18)
├── 13. 모델 저장
└── 14. 결론 & 최종 액션 플랜
```

---

## 11. 코딩 컨벤션

- **언어:** Python 3.10+
- **필수 라이브러리:** pandas, numpy, matplotlib, seaborn, scikit-learn, xgboost
- **한글 폰트:** Malgun Gothic
- **시드 고정:** `random_state=42`
- **EOQ 상수:** `ORDERING_COST=50`, `HOLDING_RATE=0.20`
- **그래프 저장:** `plt.savefig(f'{FIG_DIR}/파일명_v5_s4.png', dpi=150, bbox_inches='tight')`

---

## 12. 기대 산출물 체크리스트

### EDA & 진단

- [ ] 시각화 #1~#5 (5종)
- [ ] Leakage 진단 결과 문서화

### Phase A

- [ ] Baseline vs Enhanced 성능 비교표
- [ ] Default vs Tuned 비교표
- [ ] Feature Importance — 파생변수 기여도 확인
- [ ] 시각화 #6~#9 (4종)
- [ ] ★ Learning Curve (#19)
- [ ] ★ Permutation Importance (#20)
- [ ] ★ Residual Analysis (#21)

### Phase B

- [ ] ★ Hopkins Statistic
- [ ] Baseline(7피처) vs Enhanced(13피처) Silhouette 비교
- [ ] 군집 요약 테이블
- [ ] **군집별 발주 전략 수치표 (핵심 산출물)**
- [ ] 시각화 #10~#16 (7종)

### Phase C

- [ ] 군집별 EOQ·연간발주횟수·총비용 테이블
- [ ] EOQ 민감도 분석 (S 변화)
- [ ] 시각화 #17 (1종)

### 종합

- [ ] 소주제 1~4 연결 인사이트
- [ ] 최종 액션 플랜
- [ ] 시각화 #18 (1종)

### 파일 목록

- [ ] `notebooks/04_Reorder_Strategy_Clustering_V5.ipynb`
- [ ] `outputs/figures/` — 시각화 21종 (`*_v5_s4.png`)
- [ ] `outputs/models/phase_a_best_model_v5.pkl`
- [ ] `outputs/models/phase_a_scaler_v5.pkl`
- [ ] `outputs/models/phase_b_kmeans_baseline_v5.pkl`
- [ ] `outputs/models/phase_b_kmeans_enhanced_v5.pkl`
- [ ] `outputs/models/phase_b_scaler_baseline_v5.pkl`
- [ ] `outputs/models/phase_b_scaler_enhanced_v5.pkl`
- [ ] `outputs/models/feature_info_v5.json`

---

## 13. 핵심 유의사항

### 13.1 데이터 관련

- 인도네시아 로케일 형식 주의 (쉼표=소수점, 마침표=천단위)
- `Category` 10개 범주, `ABC_Class` A(200)/B(300)/C(500)
- DOI: 높을수록 재고 장기 보유

### 13.2 Phase A 관련

- **DOI = QOH / ADS (97.2% 일치)** → QOH+ADS 동시 사용 = Leakage
- QOH+ADS 제거 후 R²≈0.25 → 정상 수준
- **R²보다 Feature Importance 해석이 핵심**

### 13.3 Phase B 관련

- **스케일링 필수** (K-Means는 유클리드 거리 기반)
- **전체 1,000행 사용** (비지도학습이므로 train/test 분할 불필요)
- Phase B에서 QOH, ADS, DOI 사용 OK
- 피처 13개 시 **차원의 저주** 가능 → PCA 설명 분산 확인

### 13.4 Phase C 관련

- EOQ S=50 USD, H=Unit_Cost×20%는 **산업 표준 가정값**
- V5에서는 외부 데이터 검증 없이 가정으로 유지
- 민감도 분석으로 가정 변화의 영향 정량화

---

## 부록: 전체 파이프라인 흐름도

```
CSV 로드 (1,000행 × 37열)
  ↓
공통 전처리 (인도네시아 로케일, 금액, 퍼센트, Reorder_Point)
  ↓
EDA (DOI 분포, 카테고리·ABC별 분석)
  ↓
★ Data Leakage 진단 ★
  ├── DOI ≈ QOH / ADS 검증 (97.2%)
  ├── Scenario별 R² 비교 (S1~S5)
  └── 최종 피처셋 결정
  ↓
★ 파생변수 엔지니어링 (10개) ★
  ↓
═══════════════════════════════════
  Phase A: 재고 보유일수 예측
═══════════════════════════════════
  ├── Baseline (17피처) → LR, RF, XGB
  ├── Enhanced (22피처) → LR, RF, XGB
  ├── GridSearchCV 튜닝
  ├── Feature Importance 해석
  ├── ★ Learning Curve (과적합 시각 진단)
  ├── ★ Permutation Importance (피처 중요도 교차검증)
  └── ★ Residual Analysis (잔차 정규성 검정)
  ↓
═══════════════════════════════════
  Phase B: 발주 전략 클러스터링 (핵심)
═══════════════════════════════════
  ├── ★ Hopkins Statistic (클러스터링 경향성 검정)
  ├── Baseline (7피처) vs Enhanced (13피처)
  ├── Elbow + Silhouette → 최적 K
  ├── K-Means 실행 + PCA 2D
  ├── Z-Score 기반 군집 해석
  └── ★ 군집별 발주 전략 수치 제안 ★
  ↓
═══════════════════════════════════
  Phase C: EOQ 시뮬레이션
═══════════════════════════════════
  ├── 군집별 EOQ·발주횟수·총비용
  └── 민감도 분석 (S 변화)
  ↓
═══════════════════════════════════
  종합
═══════════════════════════════════
  ├── 소주제 1~4 연결 인사이트
  └── ★ 최종 액션 플랜 ★
```
