# 소주제 3 — 폐기 위험도 예측 (Binary Classification) 구현 가이드

> 이 문서는 Claude Code가 소주제 3의 전체 파이프라인을 구현할 때 참조하는 가이드라인입니다.

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열)
- 소주제 3 담당: 권효중

### 1.2 소주제 3 목표

유통기한 내 재고 소진이 가능한지 여부를 판별하는 **이진 분류 모델**을 구축하여, **폐기 위험 제품을 사전에 식별**한다. 타겟 변수(Waste_Risk)는 원본 데이터에 존재하지 않으며, 도메인 지식 기반의 **Feature Engineering으로 직접 생성**하는 것이 이 소주제의 핵심 차별점이다.

### 1.3 도출할 인사이트

- 유통기한 내 재고 소진이 불가능한 "폐기 위험" 제품을 사전에 식별할 수 있는가?
- 전체 제품 중 폐기 위험(Risk)으로 분류되는 비율은 얼마인가?
- 폐기 위험 제품의 공통 특성은 무엇인가? (카테고리, ABC 등급, 가격대, 재고량, FIFO/FEFO 방식 등)
- 실무적으로 Recall(재현율)이 왜 Precision보다 중요한가?
- **카테고리(부패성 vs 비부패성)가 폐기 위험을 거의 결정하는 구조적 이유는 무엇인가?**
- 파손(Damaged_Qty) 및 반품(Returns_Qty)이 폐기 위험에 어떤 영향을 미치는가?
- 소주제 1에서 Expiring Soon / Low Stock으로 분류된 제품과 폐기 위험 간 연관성이 있는가?

---

## 2. 데이터 명세

### 2.1 원본 데이터

- **파일:** `Inventory Management E-Grocery - InventoryData.csv`
- **규모:** 1,000행 × 37열
- **결측치:** Notes 컬럼 834건 (분석 미사용 컬럼), 실질적 결측치 이슈 없음

### 2.2 원본 컬럼 전체 목록 및 소주제 3 사용 여부

| #   | 컬럼명                       | 데이터 타입       | 설명                           | 소주제3 사용 여부                      |
| --- | ---------------------------- | ----------------- | ------------------------------ | -------------------------------------- |
| 1   | SKU_ID                       | object            | 제품 고유 식별 코드            | ❌ 식별용                              |
| 2   | SKU_Name                     | object            | 제품명                         | ❌ 식별용                              |
| 3   | Category                     | object            | 제품 카테고리 (10개 범주)      | ✅ 피처 (인코딩)                       |
| 4   | ABC_Class                    | object            | ABC 분석 등급 (A/B/C)          | ✅ 피처 (인코딩)                       |
| 5   | Supplier_ID                  | object            | 공급업체 식별 코드             | ❌ 식별용                              |
| 6   | Supplier_Name                | object            | 공급업체명                     | ❌ 식별용                              |
| 7   | Warehouse_ID                 | object            | 창고 고유 코드                 | ❌ 미사용                              |
| 8   | Warehouse_Location           | object            | 창고 소재지                    | ❌ 미사용                              |
| 9   | Batch_ID                     | object            | 배치 고유 코드                 | ❌ 식별용                              |
| 10  | Received_Date                | object → datetime | 제품 입고일                    | ✅ 파생변수 생성용                     |
| 11  | Last_Purchase_Date           | object → datetime | 최근 발주일                    | ❌ 소주제3 미사용                      |
| 12  | Expiry_Date                  | object → datetime | 유통기한 만료일                | ✅ 타겟 생성용 (핵심)                  |
| 13  | Stock_Age_Days               | int               | 재고 보유 일수                 | ✅ 피처                                |
| 14  | Quantity_On_Hand             | int               | 현재 보유 재고 수량            | ✅ 피처 + 타겟 생성용                  |
| 15  | Quantity_Reserved            | int               | 예약 재고 수량                 | ❌ 소주제3 미사용                      |
| 16  | Quantity_Committed           | int               | 출고 확정 수량                 | ❌ 소주제3 미사용                      |
| 17  | Damaged_Qty                  | int               | 파손/불량 재고 수량            | ✅ 피처                                |
| 18  | Returns_Qty                  | int               | 반품 수량                      | ✅ 피처                                |
| 19  | Avg_Daily_Sales              | object → float    | 일일 평균 판매량 (쉼표 소수점) | ✅ 피처 + 타겟 생성용                  |
| 20  | Forecast_Next_30d            | float64 (오파싱)  | 향후 30일 수요 예측량          | ❌ 소주제3 미사용                      |
| 21  | Days_of_Inventory            | object → float    | 재고 보유 가능 일수            | ⚠️ **Data Leakage** — DOI ≈ DTD        |
| 22  | Reorder_Point                | float64 (오파싱)  | 재주문 기준점                  | ✅ 피처 (전처리 필요: 천단위 `.` 10건) |
| 23  | Safety_Stock                 | int               | 안전 재고 수준                 | ❌ 소주제3 미사용                      |
| 24  | Lead_Time_Days               | int               | 발주 리드타임                  | ❌ 소주제3 미사용                      |
| 25  | Unit_Cost_USD                | object → float    | 제품 단가 (`$5,81` 형식)       | ✅ 피처 (전처리 필요)                  |
| 26  | Last_Purchase_Price_USD      | object → float    | 최근 구매 단가                 | ❌ 소주제3 미사용                      |
| 27  | Total_Inventory_Value_USD    | object → float    | 총 재고 가치                   | ❌ 소주제3 미사용                      |
| 28  | SKU_Churn_Rate               | object → float    | SKU 이탈률                     | ❌ 소주제3 미사용                      |
| 29  | Order_Frequency_per_month    | object → float    | 월간 발주 빈도                 | ❌ 소주제3 미사용                      |
| 30  | Supplier_OnTime_Pct          | object → float    | 정시 납품률                    | ❌ 소주제3 미사용                      |
| 31  | FIFO_FEFO                    | object            | 출고 방식 (FIFO/FEFO)          | ✅ 피처 (이진 인코딩)                  |
| 32  | Inventory_Status             | object            | 재고 상태 (4클래스)            | ❌ 소주제3 미사용 (소주제1 타겟)       |
| 33  | Count_Variance               | int               | 실사 시 재고 차이              | ❌ 소주제3 미사용                      |
| 34  | Audit_Date                   | object → datetime | 재고 감사일                    | ❌ 소주제3 미사용                      |
| 35  | Audit_Variance_Pct           | object → float    | 감사 차이 비율                 | ❌ 소주제3 미사용                      |
| 36  | Demand_Forecast_Accuracy_Pct | object → float    | 수요 예측 정확도               | ❌ 소주제3 미사용                      |
| 37  | Notes                        | object            | 비고/메모                      | ❌ 미사용 (결측 834건)                 |

### 2.3 타겟 변수: Waste_Risk (파생변수)

| 항목              | 내용                                                                                   |
| ----------------- | -------------------------------------------------------------------------------------- |
| 타입              | 이진 (0 또는 1)                                                                        |
| 생성 방식         | `Days_To_Deplete > Remaining_Shelf_Days` 이면 1(Risk), 아니면 0(Safe)                  |
| 의미              | 현재 판매 속도로 재고를 소진하는 데 걸리는 일수가 유통기한 잔여일보다 길면 → 폐기 위험 |
| **실제 분포**     | **Safe(0): 575건(57.5%), Risk(1): 425건(42.5%)**                                       |
| **클래스 불균형** | **비교적 균형 잡힘** — 극단적 불균형이 아니므로 `class_weight='balanced'`로 충분       |

> ⚠️ **핵심:** 이 타겟 변수는 원본 데이터에 없으며, Feature Engineering으로 직접 생성해야 한다.

### 2.4 카테고리별 폐기 위험 분포 (사전 분석 결과)

> ⚠️ **매우 중요한 발견 — 타겟이 카테고리에 의해 거의 결정됨**

| 카테고리      | Risk 비율  | 유통기한(DTE) 평균 | 특성                        |
| ------------- | ---------- | ------------------ | --------------------------- |
| Bakery        | **100.0%** | 5일                | 🔴 부패성 (단기 유통기한)   |
| Fresh Produce | **100.0%** | 8일                | 🔴 부패성                   |
| Seafood       | **100.0%** | 7일                | 🔴 부패성                   |
| Meat          | **98.9%**  | 13일               | 🔴 부패성                   |
| Dairy         | **97.9%**  | 18일               | 🔴 부패성                   |
| Beverages     | **0.0%**   | 1,101일            | 🟢 비부패성 (장기 유통기한) |
| Frozen        | **0.0%**   | 270일              | 🟢 비부패성                 |
| Household     | **0.0%**   | 1,092일            | 🟢 비부패성                 |
| Pantry        | **0.0%**   | 1,100일            | 🟢 비부패성                 |
| Personal Care | **0.0%**   | 1,169일            | 🟢 비부패성                 |

> **해석:** 부패성 제품(유통기한 ≤ 30일)은 거의 모두 폐기 위험, 비부패성 제품(유통기한 ≥ 270일)은 폐기 위험 없음.
> 이는 데이터 누수가 아닌 **실제 도메인 특성 반영** — 식료품 유통에서 부패성 제품의 폐기 위험이 높은 것은 자명한 사실.
> 모든 모델이 ~99% 정확도를 달성하는 것은 이 구조적 특성 때문이며, **노트북에서 이를 명확히 설명**해야 한다.

### 2.5 Stock_Age_Days 기준점 (사전 분석 결과)

```
Stock_Age_Days = (2025-09-09 - Received_Date).days   ← 모든 1000행 정확 일치!
```

> **발견:** `Stock_Age_Days`는 **2025-09-09**을 기준으로 계산된 값.
> 따라서 `Remaining_Shelf_Days` = `Days_To_Expiry` - `Stock_Age_Days` - 1 (reference_date = 2025-09-10 기준)
> 이는 모델이 Days_To_Expiry + Stock_Age_Days 조합으로 Remaining_Shelf_Days를 완벽 재구성 가능하다는 의미.
> **그러나** 이는 데이터 누수가 아닌 **도메인 특성** — 두 변수 모두 실제 운영에서 관찰 가능한 값이므로 피처로 사용 정당.

---

## 3. 전처리 파이프라인

### 3.1 공통 전처리 (모든 소주제 공유)

> ⚠️ **인도네시아 로케일 형식 주의:**
>
> - 쉼표(`,`)가 **소수점**으로 사용됨 (예: `28,57` = 28.57)
> - 마침표(`.`)가 **천단위 구분자**로 사용됨 (예: `1.377` = 1377, `2.084,25` = 2084.25)
> - 금액에는 `$` + 마침표 천단위 + 쉼표 소수점의 복합 형식 적용 (예: `$2.084,25`)
> - **일부 컬럼에 천단위+소수점 혼합값 존재** (예: SKU_Churn_Rate의 `2.142,90`)

다음 순서대로 수행:

```python
import pandas as pd
import numpy as np
import csv

# 0. 데이터 로드
csv_path = 'data/.../Inventory Management E-Grocery - InventoryData.csv'
df = pd.read_csv(csv_path)

# 1. 인도네시아 로케일 숫자 변환
#    ⚠️ 반드시 천단위 마침표(.) 제거 → 쉼표 소수점(,) → 마침표(.) 순서!
#    단순 str.replace(',', '.')만 하면 '2.142,90' 같은 혼합값에서 ValueError 발생
comma_decimal_cols = [
    'Avg_Daily_Sales', 'Days_of_Inventory',
    'SKU_Churn_Rate', 'Order_Frequency_per_month'
]
for col in comma_decimal_cols:
    df[col] = (df[col].astype(str)
               .str.replace('.', '', regex=False)   # 천단위 구분 마침표 제거
               .str.replace(',', '.', regex=False)   # 쉼표 소수점 → 마침표
               .astype(float))

# 1-1. Reorder_Point 특수 처리
#      10행에서 천단위 마침표 오파싱 (예: '1.170' → pandas 1.17, 실제는 1170)
raw_rp = []
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        raw_rp.append(row['Reorder_Point'])
df['Reorder_Point'] = [int(v.replace('.', '')) if '.' in v else int(v) for v in raw_rp]

# 2. 금액 컬럼 변환 ($, 천단위 구분 마침표, 쉼표 소수점 처리)
money_cols = ['Unit_Cost_USD', 'Last_Purchase_Price_USD', 'Total_Inventory_Value_USD']
for col in money_cols:
    df[col] = (df[col].astype(str)
               .str.replace('$', '', regex=False)
               .str.replace('.', '', regex=False)   # 천단위 구분 마침표 제거
               .str.replace(',', '.', regex=False)   # 쉼표 소수점 → 마침표
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

### 3.2 소주제 3 전용 파생변수 (핵심 Feature Engineering)

이 단계가 소주제 3의 **가장 중요한 차별점**이다. 도메인 지식을 활용하여 타겟 변수를 직접 설계한다.

| 파생 변수            | 생성 방식                                    | 설명                               | 역할                |
| -------------------- | -------------------------------------------- | ---------------------------------- | ------------------- |
| Days_To_Expiry       | `Expiry_Date - Received_Date` (일수)         | 입고일 기준 유통기한까지 전체 일수 | ✅ 피처 (핵심)      |
| Remaining_Shelf_Days | `Expiry_Date - reference_date` (일수)        | 분석 기준일로부터 유통기한 잔여일  | 타겟 생성 중간 변수 |
| Days_To_Deplete      | `Quantity_On_Hand / Avg_Daily_Sales`         | 현재 재고 소진 예상 일수           | 타겟 생성 중간 변수 |
| **Waste_Risk**       | `Days_To_Deplete > Remaining_Shelf_Days → 1` | **폐기 위험 여부 (타겟)**          | 🎯 타겟 변수        |

```python
# 1. 유통기한 전체 일수 (입고일 기준, 피처로 사용)
df['Days_To_Expiry'] = (df['Expiry_Date'] - df['Received_Date']).dt.days

# 2. 유통기한 잔여일 (분석 기준일 설정)
#    Stock_Age_Days = (2025-09-09 - Received_Date) 확인됨
#    → reference_date = 2025-09-10 (데이터 생성 다음 날)
reference_date = pd.Timestamp('2025-09-10')
df['Remaining_Shelf_Days'] = (df['Expiry_Date'] - reference_date).dt.days

# 3. 현재 재고 소진 예상 일수
#    ⚠️ Avg_Daily_Sales가 0인 경우는 없음 (min=1.01) — 별도 처리 불필요
df['Days_To_Deplete'] = df['Quantity_On_Hand'] / df['Avg_Daily_Sales']

# 4. 폐기 위험 여부: 소진 일수 > 유통기한 잔여일 → Risk(1)
df['Waste_Risk'] = (df['Days_To_Deplete'] > df['Remaining_Shelf_Days']).astype(int)
```

> **논리 해석:**
>
> - `Days_To_Deplete = 60일` 이고 `Remaining_Shelf_Days = 40일` → 재고를 다 팔려면 60일 걸리는데 유통기한은 40일 → **폐기 위험(1)**
> - `Days_To_Deplete = 20일` 이고 `Remaining_Shelf_Days = 40일` → 재고를 20일이면 다 파는데 유통기한이 40일 남음 → **안전(0)**

> **reference_date = 2025-09-10 선택 근거:**
>
> - `Stock_Age_Days = (2025-09-09 - Received_Date)` → 데이터가 2025-09-09에 생성된 것으로 확인
> - 분석 기준일을 데이터 생성 다음 날인 2025-09-10으로 설정

> **특이사항:**
>
> - `Avg_Daily_Sales`가 0인 행: **0건** (min=1.01) → 0 나눗셈 처리 불필요
> - `Remaining_Shelf_Days < 0` (이미 유통기한 초과): **406건** → 자동으로 Risk 분류
> - 이미 만료된 제품 406건이 Risk 425건의 대부분을 차지

### 3.3 타겟 생성 후 반드시 확인할 사항

```python
# 1. Waste_Risk 클래스 분포 확인
print(df['Waste_Risk'].value_counts())
print(df['Waste_Risk'].value_counts(normalize=True))
# → Safe(0): 575건(57.5%), Risk(1): 425건(42.5%)
# → 비교적 균형 잡힌 분포 — 극단적 불균형 아님

# 2. 카테고리별 Risk 비율 확인
print(pd.crosstab(df['Category'], df['Waste_Risk'], normalize='index'))
# → 부패성(Bakery/Fresh/Seafood/Meat/Dairy): ~100% Risk
# → 비부패성(Beverages/Frozen/Household/Pantry/Personal Care): ~0% Risk
```

---

## 4. 데이터 누수(Data Leakage) 진단

> ⚠️ **소주제 1, 2에서 발견된 데이터 누수 패턴이 소주제 3에도 존재한다.**

### 4.1 Days_of_Inventory = Days_To_Deplete (직접 누수)

실제 데이터 검증 결과:

| 검증 항목                               | 결과                          |
| --------------------------------------- | ----------------------------- |
| `Days_of_Inventory ≈ QOH / ADS` 일치 행 | **972 / 1,000행** (97.2%)     |
| `Days_of_Inventory ≈ Days_To_Deplete`   | 동일한 수식 → **동일한 변수** |

```
Days_of_Inventory = Quantity_On_Hand / Avg_Daily_Sales = Days_To_Deplete
→ Days_To_Deplete는 타겟(Waste_Risk) 생성의 직접 좌변!
→ Days_of_Inventory를 피처에 포함하면 타겟 산출 직접 변수를 넣는 것과 동일!
```

**결론:** `Days_of_Inventory`를 피처에서 **반드시 제거**

### 4.2 Remaining_Shelf_Days 재구성 가능성

```
Remaining_Shelf_Days = Days_To_Expiry - Stock_Age_Days - 1
  (reference_date = 2025-09-10, Stock_Age_Days 기준 = 2025-09-09)
```

모델이 `Days_To_Expiry`와 `Stock_Age_Days`를 피처로 가지면 `Remaining_Shelf_Days`를 완벽히 재구성 가능.
결합하면 `QOH/ADS > DTE - SA - 1` 관계를 학습하여 타겟을 거의 완벽히 예측.

**단, 이것은 누수(Leakage)가 아닌 정당한 도메인 특성:**

- `Days_To_Expiry`: 제품의 유통기한(입고 시 이미 알려진 정보)
- `Stock_Age_Days`: 재고 보유 기간(관찰 가능 변수)
- `Quantity_On_Hand`, `Avg_Daily_Sales`: 현재 재고/판매 정보
- 실제 운영에서도 이 4개 변수를 모두 알 수 있으므로 **피처 사용 정당**

### 4.3 근본 원인: 카테고리가 타겟을 결정

| 피처              | Waste_Risk 상관계수 | 비고                       |
| ----------------- | ------------------- | -------------------------- |
| Days_To_Expiry    | **-0.7798**         | 🔥 가장 강한 예측 변수     |
| Unit_Cost_USD     | -0.3834             | 부패성 제품이 저가인 경향  |
| Quantity_On_Hand  | +0.1990             | 약한 양의 상관             |
| Avg_Daily_Sales   | +0.1608             | 약한 양의 상관             |
| Reorder_Point     | +0.0946             | 미미                       |
| Stock_Age_Days    | +0.0270             | 거의 무관                  |
| Returns_Qty       | -0.0244             | 거의 무관                  |
| Damaged_Qty       | -0.0037             | 거의 무관                  |
| Days_of_Inventory | -0.0027             | **🔒 LEAKAGE (DOI ≈ DTD)** |

> **핵심 인사이트:** `Days_To_Expiry`(유통기한)가 상관 -0.78로 압도적.
> 유통기한이 짧은 부패성 제품 = Risk, 유통기한이 긴 비부패성 제품 = Safe.
> **Category만으로도 RF Accuracy 99.0% 달성** — 이는 도메인 특성 반영이지 모델 오류가 아님.

### 4.4 Days_To_Expiry 지배력 검증 (Ablation Study) ★

> **목적:** Days_To_Expiry(DTE)가 타겟과 상관 -0.78로 압도적이며, 카테고리와 강하게 연관됨.
> DTE 제거 시 성능 변화를 측정하여 단일 피처 의존도를 정량적으로 검증한다.

| 시나리오 | 피처 구성 | 목적 |
|----------|----------|------|
| **Full** | 전체 피처 (DOI 제거 후) | 기준선 |
| **No-DTE** | DTE 제거 | DTE 지배력 정량화 |

```python
# Ablation Study: DTE 제거 시 성능 변화
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier  # 비교용
from sklearn.metrics import f1_score, recall_score

# Full 피처 모델
lr_full = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
lr_full.fit(X_train_scaled, y_train)
f1_full = f1_score(y_test, lr_full.predict(X_test_scaled))

# DTE 제거 모델
dte_idx = list(feature_names).index('Days_To_Expiry')
X_train_no_dte = np.delete(X_train_scaled, dte_idx, axis=1)
X_test_no_dte = np.delete(X_test_scaled, dte_idx, axis=1)
lr_no_dte = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
lr_no_dte.fit(X_train_no_dte, y_train)
f1_no_dte = f1_score(y_test, lr_no_dte.predict(X_test_no_dte))

print(f"ΔF1 (Full → No-DTE): {f1_full - f1_no_dte:+.4f}")
# → DTE 제거 시에도 F1 유지되면 Category One-Hot이 보완,
#   F1 크게 하락하면 DTE 단독 지배력 확인
```

> **기대 결과:** DTE 제거 시에도 성능이 크게 떨어지지 않을 수 있음 (Category One-Hot이 유통기한 정보를 내포).
> 이는 **DTE ↔ Category 공선성**을 보여주는 증거이며, 실무적으로는 두 변수 모두 보유가 유리함을 시사.

### 4.5 노트북에서 보여줄 진단 내용

1. `Days_of_Inventory ≈ Days_To_Deplete` 수치 검증 → DOI 피처 제거 근거
2. Category만으로 99% 예측 가능 → 카테고리별 유통기한 구조적 차이 시각화
3. Days_To_Expiry의 카테고리별 분포 → 부패성/비부패성 이분법
4. ★ Days_To_Expiry Ablation Study → DTE 지배력 정량화
5. 최종 피처셋 결정 근거 문서화

---

## 5. 모델링 상세 설계

### 5.1 피처 목록 (최종 입력 변수 — DOI 제거)

**수치형 피처 (8개):**

- Unit_Cost_USD (전처리: `$` 제거, 천단위`.` 제거, 쉼표→마침표)
- Quantity_On_Hand
- Reorder_Point (전처리: 천단위 `.` 10건 수정 필요)
- Avg_Daily_Sales (전처리: 천단위`.` 제거 → 쉼표→마침표)
- Stock_Age_Days
- Damaged_Qty
- Returns_Qty
- Days_To_Expiry (파생: `Expiry_Date - Received_Date`)

**범주형 피처 (인코딩 후):**

- Category (One-Hot, 9개, Bakery baseline)
- ABC_Class (One-Hot, 2개, A baseline)
- FIFO_FEFO_encoded (이진, FEFO=1, FIFO=0)

> **총 피처 수:** 8(수치) + 9(카테고리) + 2(ABC) + 1(FIFO/FEFO) = **20개**

### 5.2 누수 피처 제외 목록

| 제외 변수            | 이유                                | 처리                         |
| -------------------- | ----------------------------------- | ---------------------------- |
| Days_of_Inventory    | **DOI ≈ DTD (타겟 산출 직접 변수)** | ❌ 피처에서 제외             |
| Days_To_Deplete      | 타겟 생성 좌변                      | ❌ 피처에서 제외 (중간 변수) |
| Remaining_Shelf_Days | 타겟 생성 우변                      | ❌ 피처에서 제외 (중간 변수) |
| Waste_Risk           | 타겟 변수 자체                      | 🎯 y로 분리                  |

> **참고:** `Avg_Daily_Sales`, `Quantity_On_Hand`, `Days_To_Expiry`, `Stock_Age_Days`는 타겟 산출 요소이지만,
> 실제 운영 시점에 모두 관측 가능한 독립 변수이므로 **피처 사용 정당**. 노트북에서 이를 명시적으로 문서화할 것.

### 5.3 Train/Test Split

```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

- 비율: 80:20
- `stratify=y` 로 클래스 비율 유지
- `random_state=42` 고정

### 5.4 스케일링

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### 5.5 클래스 불균형 대응 전략

Waste_Risk 분포: Safe 57.5% / Risk 42.5% — **비교적 균형 잡힘**.

| 전략                        | 방법                                    | 적용                                       |
| --------------------------- | --------------------------------------- | ------------------------------------------ |
| **class_weight='balanced'** | 모델 내부에서 소수 클래스에 높은 가중치 | LR, SVM — **적용**                         |
| **scale_pos_weight**        | 양성 클래스 가중치                      | XGBoost — **적용**                         |
| **SMOTE**                   | 합성 오버샘플링                         | ❌ **불필요** (42.5%는 심각한 불균형 아님) |

> ⚠️ SMOTE는 본 데이터셋에서 불필요. `class_weight='balanced'` / `scale_pos_weight`로 충분.

> ⚠️ **LightGBM 대신 XGBoost를 선택한 이유:**
> 데이터 1,000행으로 소규모이므로 LightGBM의 leaf-wise 전략이 과적합 위험이 있으며,
> XGBoost의 level-wise + max_depth 제어가 소규모 데이터에 더 안정적.

### 5.6 학습할 모델 (3종) — Default → CV → Tuned

| #   | 모델                | 라이브러리 | Default 파라미터                                                                 | 비고     |
| --- | ------------------- | ---------- | -------------------------------------------------------------------------------- | -------- |
| 1   | Logistic Regression | sklearn    | `class_weight='balanced'`, `max_iter=1000`, `random_state=42`                    | Baseline |
| 2   | SVM (RBF kernel)    | sklearn    | `kernel='rbf'`, `class_weight='balanced'`, `probability=True`, `random_state=42` | 비선형   |
| 3   | XGBoost Classifier  | xgboost    | `scale_pos_weight=neg/pos`, `eval_metric='logloss'`, `random_state=42`           | 앙상블   |

### 5.7 하이퍼파라미터 튜닝

| 모델    | 튜닝 파라미터 | 범위/값                      | 목적         |
| ------- | ------------- | ---------------------------- | ------------ |
| LR      | C             | [0.01, 0.1, 1, 10, 100]      | 정규화 강도  |
| SVM     | C             | [0.1, 1, 10]                 | 마진 폭 조절 |
| SVM     | gamma         | ['scale', 'auto', 0.01, 0.1] | RBF 커널 폭  |
| XGBoost | max_depth     | [3, 5, 7]                    | 과적합 방지  |
| XGBoost | learning_rate | [0.01, 0.05, 0.1]            | 학습 속도    |
| XGBoost | n_estimators  | [100, 200]                   | 트리 수      |
| XGBoost | subsample     | [0.7, 0.8, 0.9]              | 샘플링       |

### 5.8 평가 지표

| 지표                 | 설명                               | 선택 이유                             |
| -------------------- | ---------------------------------- | ------------------------------------- |
| **Precision (Risk)** | Risk로 예측한 것 중 실제 Risk 비율 | 오탐(FP) 비용 평가                    |
| **Recall (Risk)**    | 실제 Risk 중 모델이 잡아낸 비율    | **핵심 지표** — 놓치면 폐기 비용 발생 |
| **F1-Score (Risk)**  | Precision과 Recall의 조화평균      | 종합 성능                             |
| **ROC-AUC**          | 양성/음성 구분 능력 전반           | 임계값 독립적 성능                    |
| **PR-AUC**           | Precision-Recall 곡선 아래 면적    | 불균형 데이터에서 유용                |

> **Recall 중심 평가 근거:**
> 실무에서 폐기 위험 제품을 놓치는 것(FN)은 실제 폐기 비용을 발생시키므로,
> 오탐(FP)보다 **훨씬 큰 비용**을 유발한다.

### 5.9 기대 성능 범위 (사전 분석 결과)

| 모델                | 예상 Test Accuracy | 예상 Recall(Risk) | 비고                    |
| ------------------- | ------------------ | ----------------- | ----------------------- |
| Logistic Regression | ~0.99              | ~1.00             | Days_To_Expiry가 지배적 |
| SVM (RBF)           | ~0.99              | ~1.00             | 동일 이유               |
| XGBoost             | ~0.99              | ~1.00             | 동일 이유               |

> **99% 정확도의 원인:** 데이터 누수가 아닌 **카테고리별 유통기한 구조적 차이**.
> 부패성 제품(DTE ≤ 30일)은 거의 100% Risk, 비부패성(DTE ≥ 270일)은 0% Risk.
> 이는 식료품 유통의 **자명한 도메인 특성**이며, 노트북에서 이를 분석 인사이트로 활용.

---

## 6. 시각화 및 해석 요구사항

### 6.1 EDA 시각화 (모델링 전)

1. **Waste_Risk 클래스 분포** — `countplot` + 비율 표시
2. **카테고리별(10종) 폐기 위험 비율** — `stacked bar` 또는 `heatmap` (핵심 시각화)
3. **ABC 등급별 폐기 위험 비율** — A/B/C 간 위험 비율 차이
4. **폐기 위험 여부별 주요 피처 분포** — `boxplot` with `hue='Waste_Risk'`
   - 대상: QOH, ADS, Days_To_Expiry, Unit_Cost_USD, Stock_Age_Days
5. **Remaining_Shelf_Days vs Days_To_Deplete 산점도** (핵심!)
   - 색상: Waste_Risk (Safe=파랑, Risk=빨강)
   - 대각선(y=x) 기준선 → 기준선 위가 Risk
6. **카테고리별 Days_To_Expiry 분포** — 부패성/비부패성 이분법 시각화
7. **피처 간 상관관계 히트맵** — `heatmap` with `annot=True`

### 6.2 데이터 누수 진단 시각화

8. **DOI vs DTD 일치 검증** — 산점도 + 일치 비율
9. **카테고리별 DTE 분포** — 왜 Category만으로 99% 예측 가능한지 근거

### 6.3 모델링 후 시각화

10. **Confusion Matrix 히트맵** (최적 모델)
11. **모델별 성능 비교 바 차트** — Precision, Recall, F1, AUC
12. **Default vs Tuned 비교 차트**
13. **ROC Curve** (3개 모델 비교)
14. **Precision-Recall Curve** (3개 모델 비교)
15. **Feature Importance** (XGBoost `feature_importances_`)
16. **SHAP Summary Plot** (Bar + Dot) — XGBoost 기준

### 6.4 Learning Curve (과적합 진단) ★

> **목적:** 학습 데이터 크기에 따른 Train/Validation 성능 변화를 추적하여 과적합 여부를 진단한다.

```python
from sklearn.model_selection import learning_curve

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

models_lc = {
    'Logistic Regression': tuned_trained['Logistic Regression'],
    'SVM (RBF)': tuned_trained['SVM (RBF)'],
    'XGBoost': tuned_trained['XGBoost']
}

for ax, (name, model) in zip(axes, models_lc.items()):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train_scaled, y_train,
        cv=5, scoring='f1', n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 10),
        random_state=42
    )
    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    val_mean = val_scores.mean(axis=1)
    val_std = val_scores.std(axis=1)

    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
    ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.1, color='orange')
    ax.plot(train_sizes, train_mean, 'o-', color='blue', label='Train F1')
    ax.plot(train_sizes, val_mean, 'o-', color='orange', label='Validation F1')
    ax.set_title(name)
    ax.set_xlabel('학습 데이터 크기')
    ax.set_ylabel('F1 Score')
    ax.legend(loc='lower right')
    ax.set_ylim([0.8, 1.05])
    ax.grid(True, alpha=0.3)

plt.suptitle('Learning Curve — 과적합 진단 ★', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'learning_curve_s3.png'), dpi=150, bbox_inches='tight')
plt.show()
```

> **해석 가이드:**
> - Train/Val 곡선이 수렴하면 → 과적합 없음 (정상)
> - Train ≈ 1.0인데 Val이 크게 낮으면 → 과적합
> - 분류 문제이므로 scoring='f1' 사용 (R² 대신)

### 6.5 Permutation Importance (피처 중요도 교차검증) ★

> **목적:** Impurity-based Feature Importance(XGBoost 기본)와 Permutation Importance를 비교하여
> 피처 중요도 순위의 일관성을 검증한다.

```python
from sklearn.inspection import permutation_importance

# XGBoost Tuned 모델 기준
xgb_tuned = tuned_results['XGBoost']['model']

# Permutation Importance
perm_result = permutation_importance(
    xgb_tuned, X_test_scaled, y_test,
    n_repeats=10, random_state=42, scoring='f1'
)

# Impurity-based
imp_impurity = pd.Series(xgb_tuned.feature_importances_, index=feature_names)
imp_perm = pd.Series(perm_result.importances_mean, index=feature_names)

# 순위 비교 테이블
rank_df = pd.DataFrame({
    'Impurity Rank': imp_impurity.rank(ascending=False).astype(int),
    'Permutation Rank': imp_perm.rank(ascending=False).astype(int),
    'Impurity Value': imp_impurity.round(4),
    'Permutation Value': imp_perm.round(4)
})
rank_df['Rank Δ'] = rank_df['Impurity Rank'] - rank_df['Permutation Rank']
rank_df = rank_df.sort_values('Permutation Rank')
display(rank_df)

# 시각화: Side-by-side comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
top_n = 10
imp_top = imp_impurity.nlargest(top_n)
perm_top = imp_perm.nlargest(top_n)

axes[0].barh(range(top_n), imp_top.values, color='steelblue')
axes[0].set_yticks(range(top_n))
axes[0].set_yticklabels(imp_top.index)
axes[0].set_title('Impurity-based Importance')
axes[0].invert_yaxis()

axes[1].barh(range(top_n), perm_top.values, color='coral')
axes[1].set_yticks(range(top_n))
axes[1].set_yticklabels(perm_top.index)
axes[1].set_title('Permutation Importance')
axes[1].invert_yaxis()

plt.suptitle('Feature Importance 교차검증 — Impurity vs Permutation ★', fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'permutation_vs_impurity_importance_s3.png'), dpi=150, bbox_inches='tight')
plt.show()
```

> **해석 가이드:**
> - 두 방법의 Top-3 순위가 일치하면 → 피처 중요도 신뢰성 높음
> - Impurity는 높은 카디널리티 피처에 편향될 수 있음 → Permutation이 더 공정
> - Days_To_Expiry가 양쪽 모두 1위면 → DTE 지배력 재확인

### 6.6 Calibration Curve + Brier Score (확률 신뢰도 검정) ★

> **목적:** 분류 모델이 출력하는 예측 확률이 실제 확률과 얼마나 일치하는지 검정한다.
> 회귀의 Shapiro-Wilk(잔차 정규성)에 대응하는 분류의 진단 기법.

```python
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

fig, ax = plt.subplots(figsize=(8, 7))

for name, info in tuned_results.items():
    model = info['model']
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    brier = brier_score_loss(y_test, y_prob)
    fraction_pos, mean_predicted = calibration_curve(y_test, y_prob, n_bins=10)
    ax.plot(mean_predicted, fraction_pos, 's-', label=f'{name} (Brier={brier:.4f})')

ax.plot([0, 1], [0, 1], 'k--', label='Perfectly Calibrated')
ax.set_xlabel('예측 확률 (Mean Predicted)')
ax.set_ylabel('실제 양성 비율 (Fraction of Positives)')
ax.set_title('Calibration Curve — 예측 확률 신뢰도 검정 ★')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'calibration_curve_s3.png'), dpi=150, bbox_inches='tight')
plt.show()

# Brier Score 요약
print("\n=== Brier Score (낮을수록 좋음, 0=완벽) ===")
for name, info in tuned_results.items():
    y_prob = info['model'].predict_proba(X_test_scaled)[:, 1]
    brier = brier_score_loss(y_test, y_prob)
    print(f"  {name}: {brier:.4f}")
```

> **해석 가이드:**
> - 대각선(y=x)에 가까울수록 → 확률 보정이 잘됨
> - Brier Score: 0에 가까울수록 좋음 (MSE of probabilities)
> - SVM은 probability=True 사용 시 Platt Scaling으로 보정 → 곡선이 덜 매끄러울 수 있음
> - 99% 정확도의 모델이므로 대부분 0 또는 1 근처에 확률이 집중될 것

### 6.7 선택 시각화 (기존)

---

## 7. 코드 구조 및 출력 형식

### 7.1 Jupyter Notebook 구조

```
03_Waste_Risk_Prediction.ipynb
│
├── 0. 라이브러리 임포트 & 설정
│   ├── 필수 라이브러리 import
│   ├── 시각화 한글 폰트 설정 (Malgun Gothic)
│   └── 경고 메시지 숨김, 시드 고정
│
├── 1. 데이터 로드 & 기본 확인
│   ├── CSV 로드
│   ├── df.shape, df.info(), df.describe()
│   └── 결측치 확인
│
├── 2. 데이터 전처리
│   ├── 인도네시아 로케일 숫자 변환 (천단위`.` 제거 → 쉼표`,`→마침표`.`)
│   ├── Reorder_Point 천단위 오파싱 수정 (10건)
│   ├── 금액 컬럼 변환 ($, 천단위 구분 제거, 쉼표→마침표)
│   ├── 날짜 컬럼 파싱
│   └── 전처리 결과 검증
│
├── 3. 타겟 변수 생성 (핵심 Feature Engineering)
│   ├── Days_To_Expiry 계산 (Expiry_Date - Received_Date)
│   ├── Stock_Age_Days 기준점 검증 (2025-09-09 확인)
│   ├── reference_date 설정 근거 문서화 (2025-09-10)
│   ├── Remaining_Shelf_Days 계산
│   ├── Days_To_Deplete 계산 (QOH / ADS)
│   ├── Waste_Risk 생성 (이진)
│   ├── 클래스 분포 확인 & 시각화
│   └── 타겟 생성 논리 설명 마크다운
│
├── 4. EDA (탐색적 데이터 분석)
│   ├── Waste_Risk 클래스 분포
│   ├── 카테고리별(10종) 폐기 위험 비율 (핵심)
│   ├── 카테고리별 Days_To_Expiry 분포 (부패성/비부패성)
│   ├── ABC 등급별 폐기 위험 비율
│   ├── 폐기 위험 여부별 주요 피처 분포 (boxplot)
│   ├── Remaining_Shelf_Days vs Days_To_Deplete 산점도 (핵심)
│   └── 피처 간 상관관계 히트맵
│
├── 5. 데이터 누수(Data Leakage) 진단
│   ├── DOI ≈ DTD 수치 검증 → DOI 피처 제거 근거
│   ├── Remaining_Shelf_Days = DTE - SA - 1 검증
│   ├── Category만으로 99% 예측 가능 → 근본 원인 분석
│   └── 최종 피처셋 결정 (DOI 제거, DTE 유지)
│
├── 6. 피처/타겟 분리 & Train/Test Split
│   ├── 피처 선택 (X) — 누수 변수(DOI) 제외 확인
│   ├── 카테고리·ABC·FIFO/FEFO 인코딩
│   ├── 타겟 지정 (y = Waste_Risk)
│   ├── train_test_split (80:20, stratify)
│   └── StandardScaler 적용
│
├── 7. 모델 학습 & 평가
│   ├── 7.1 Default 모델 학습 (3종: LR, SVM, XGBoost)
│   ├── 7.2 교차검증 (5-Fold CV)
│   ├── 7.3 하이퍼파라미터 튜닝 (GridSearchCV)
│   ├── 7.4 Default vs Tuned 비교
│   ├── 7.5 모델 성능 비교 종합표 & 바 차트
│   └── 7.6 Learning Curve ★
│
├── 8. 최적 모델 심층 분석
│   ├── 8.1 Confusion Matrix 히트맵
│   ├── 8.2 Classification Report 출력
│   ├── 8.3 ROC Curve (3개 모델 비교)
│   ├── 8.4 Precision-Recall Curve (3개 모델 비교)
│   ├── 8.5 Feature Importance 시각화
│   ├── 8.6 Permutation Importance ★
│   ├── 8.7 Calibration Curve + Brier Score ★
│   └── 8.8 SHAP Summary Plot (Bar + Dot)
│
├── 9. 모델 저장
│   ├── 최적 모델 joblib 저장
│   ├── Scaler 저장
│   └── 피처 정보 저장
│
└── 10. 결론 및 인사이트
    ├── 핵심 발견: 카테고리(부패성 vs 비부패성)가 폐기 위험을 결정
    ├── Days_To_Expiry의 역할과 도메인 해석
    ├── 99% 정확도의 의미: 누수가 아닌 구조적 패턴
    ├── Recall 중심 평가의 실무적 의미
    ├── 한계점 및 개선 방향
    └── 다른 소주제와의 연결점
```

### 7.2 코딩 컨벤션

- **언어:** Python 3.10+
- **필수 라이브러리:**
  ```
  pandas, numpy, matplotlib, seaborn,
  scikit-learn, xgboost, shap
  ```
- **한글 폰트 설정:** `Malgun Gothic` (matplotlib 내장 폰트 디렉토리에 사전 설치됨)
  ```python
  import matplotlib.pyplot as plt
  import matplotlib.font_manager as fm
  fm._load_fontmanager(try_read_cache=False)
  plt.rcParams['font.family'] = 'Malgun Gothic'
  plt.rcParams['axes.unicode_minus'] = False
  ```
- **시드 고정:** 모든 모델에 `random_state=42`
- **셀 출력:** 각 단계마다 중간 결과를 `print()` 또는 `display()`로 확인
- **마크다운 셀:** 각 섹션마다 설명 마크다운 포함 (한국어)
- **그래프 제목/라벨:** 한국어 사용 권장 (한글 폰트 설정 전제)
- **그래프 저장:** 주요 시각화는 `plt.savefig('outputs/figures/파일명_s3.png', dpi=150, bbox_inches='tight')` 로 저장

### 7.3 모델 성능 결과 테이블 출력 형식

```python
results = pd.DataFrame({
    '모델': ['Logistic Regression', 'SVM (RBF)', 'XGBoost'],
    'Train Acc': [...],
    'Test Acc': [...],
    'Precision(Risk)': [...],
    'Recall(Risk)': [...],
    'F1(Risk)': [...],
    'ROC-AUC': [...],
    'Gap': [...]  # Train Acc - Test Acc
})
results = results.sort_values('Recall(Risk)', ascending=False)
display(results)
```

---

## 8. ROC Curve & PR Curve 구현 가이드

### 8.1 ROC Curve (3개 모델 비교)

```python
from sklearn.metrics import roc_curve, roc_auc_score

fig, ax = plt.subplots(figsize=(8, 6))

models = {
    'Logistic Regression': lr_model,
    'SVM (RBF)': svm_model,
    'XGBoost': xgb_model
}

for name, model in models.items():
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)
    ax.plot(fpr, tpr, label=f'{name} (AUC={auc:.3f})')

ax.plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curve 비교')
ax.legend()
plt.tight_layout()
plt.savefig('outputs/figures/roc_curve_s3.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 8.2 Precision-Recall Curve (3개 모델 비교)

```python
from sklearn.metrics import precision_recall_curve, average_precision_score

fig, ax = plt.subplots(figsize=(8, 6))

for name, model in models.items():
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    ap = average_precision_score(y_test, y_prob)
    ax.plot(recall, precision, label=f'{name} (AP={ap:.3f})')

ax.set_xlabel('Recall')
ax.set_ylabel('Precision')
ax.set_title('Precision-Recall Curve 비교')
ax.legend()
plt.tight_layout()
plt.savefig('outputs/figures/pr_curve_s3.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## 9. SHAP 분석 상세 가이드

### 9.1 SHAP 적용 (XGBoost 기준)

```python
import shap

explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test_df)  # DataFrame으로 전달하여 피처명 보존
```

### 9.2 SHAP 시각화

```python
# 1. Summary Plot (Bar) — 피처 중요도 순위
shap.summary_plot(shap_values, X_test_df, plot_type="bar", show=False)
plt.title("SHAP Feature Importance (폐기 위험 예측)")
plt.tight_layout()
plt.savefig('outputs/figures/shap_importance_bar_s3.png', dpi=150, bbox_inches='tight')
plt.show()

# 2. Summary Plot (Dot/Beeswarm) — 피처별 영향 방향 + 크기
shap.summary_plot(shap_values, X_test_df, show=False)
plt.title("SHAP Summary Plot (폐기 위험 예측)")
plt.tight_layout()
plt.savefig('outputs/figures/shap_summary_dot_s3.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 9.3 SHAP 해석 포인트

- **Days_To_Expiry가 가장 중요한 피처로 나올 것** (상관 -0.78)
- **SHAP value < 0 (DTE 작을수록):** 유통기한이 짧을수록 → Risk 확률 ↑
- Category One-Hot이 DTE 다음으로 중요할 가능성
- QOH, ADS는 동일 카테고리 내에서의 미세 차이 구분에 기여

---

## 10. 기대 산출물 체크리스트

- [ ] `03_Waste_Risk_Prediction.ipynb` — 전체 분석 노트북
- [ ] `outputs/figures/waste_risk_distribution_s3.png` — 클래스 분포
- [ ] `outputs/figures/category_risk_ratio_s3.png` — 카테고리별 폐기 위험 비율
- [ ] `outputs/figures/category_dte_distribution_s3.png` — 카테고리별 DTE 분포
- [ ] `outputs/figures/abc_risk_ratio_s3.png` — ABC 등급별 폐기 위험 비율
- [ ] `outputs/figures/risk_feature_boxplots_s3.png` — 위험 여부별 피처 분포
- [ ] `outputs/figures/expiry_vs_deplete_scatter_s3.png` — 핵심 산점도
- [ ] `outputs/figures/correlation_heatmap_s3.png` — 피처 상관관계
- [ ] `outputs/figures/data_leakage_diagnosis_s3.png` — DOI ≈ DTD 진단
- [ ] `outputs/figures/confusion_matrix_s3.png` — Confusion Matrix
- [ ] `outputs/figures/model_comparison_s3.png` — 모델 성능 비교 차트
- [ ] `outputs/figures/model_comparison_default_vs_tuned_s3.png` — Default vs Tuned
- [ ] `outputs/figures/roc_curve_s3.png` — ROC Curve (3개 모델)
- [ ] `outputs/figures/pr_curve_s3.png` — Precision-Recall Curve
- [ ] `outputs/figures/feature_importance_s3.png` — Feature Importance
- [ ] `outputs/figures/shap_importance_bar_s3.png` — SHAP Bar
- [ ] `outputs/figures/shap_summary_dot_s3.png` — SHAP Dot
- [ ] `outputs/figures/dte_ablation_study_s3.png` — ★ DTE Ablation Study
- [ ] `outputs/figures/learning_curve_s3.png` — ★ Learning Curve
- [ ] `outputs/figures/permutation_vs_impurity_importance_s3.png` — ★ Permutation Importance
- [ ] `outputs/figures/calibration_curve_s3.png` — ★ Calibration Curve
- [ ] `outputs/models/best_risk_model.pkl` — 최적 모델 저장
- [ ] `outputs/models/scaler_risk.pkl` — StandardScaler 저장
- [ ] `outputs/models/feature_info_risk.json` — 피처 정보 저장
- [ ] 모델 성능 결과 요약 (Precision, Recall, F1, AUC 수치)
- [ ] 핵심 인사이트 3~5개 정리

---

## 11. 핵심 유의사항

### 11.1 데이터 관련

- 데이터가 1,000행으로 **소규모**이므로 과적합에 주의
- **인도네시아 로케일 형식 주의:**
  - `Avg_Daily_Sales`: `"28,57"` → 쉼표→마침표 변환
  - `Days_of_Inventory`: `"12,57"` → 동일 변환
  - `SKU_Churn_Rate`: `"2.142,90"` 같은 **혼합 형식** 1건 → 반드시 천단위 마침표 먼저 제거!
- **Reorder_Point 오파싱:** 10행에서 `'1.170'` → pandas 1.17 (실제 1170) → raw CSV 재추출 필수
- **금액 컬럼 복합 형식:** `Unit_Cost_USD`가 `"$5,81"` 형태 → `$` 제거, 천단위`.` 제거, 쉼표→마침표
- `Avg_Daily_Sales`가 0인 행: **0건** (min=1.01) → 0 나눗셈 처리 불필요
- `Remaining_Shelf_Days < 0` (이미 만료): **406건** → 자동으로 Risk 분류

### 11.2 데이터 누수 관련 (핵심)

- **`Days_of_Inventory` ≈ `Days_To_Deplete`** — 동일 수식(`QOH/ADS`), 97.2% 일치
  - **반드시 피처에서 제거!**
- **`Days_To_Deplete`, `Remaining_Shelf_Days`** — 타겟 생성 중간 변수
  - 피처에서 제외 (타겟 생성에만 사용)
- **`Days_To_Expiry`, `Stock_Age_Days`** — 피처 사용 정당
  - Remaining_Shelf_Days = DTE - SA - 1 재구성 가능하지만
  - 실제 운영에서도 관찰 가능한 독립 변수이므로 정당

### 11.3 모델링 관련

- **99% 정확도는 정상** — 카테고리별 유통기한 구조적 차이 때문
- 클래스 불균형 **심하지 않음** (57.5% vs 42.5%) → `class_weight='balanced'`로 충분
- SVM에 `probability=True` 설정 필수 (ROC-AUC, predict_proba 계산)
- 모델 비교 시 **동일한 train/test 분할** 사용 (random_state 고정)

### 11.4 해석 관련 (핵심)

- **99% 정확도의 해석이 소주제 3의 핵심 포인트:**
  - "모델이 정확하게 예측한다" + "왜 정확한가 = 카테고리(유통기한) 결정적"
  - 부패성 제품 5종(Bakery/Fresh/Seafood/Meat/Dairy) → 거의 모두 Risk
  - 비부패성 제품 5종(Beverages/Frozen/Household/Pantry/Personal Care) → 거의 모두 Safe
- **실무적 인사이트:**
  - 부패성 제품의 재고 관리를 강화해야 함
  - FEFO(유통기한 임박 우선 출고) 방식을 부패성 카테고리에 적극 도입
  - 부패성 제품의 재주문량과 빈도를 판매 속도에 맞춰 최적화

### 11.5 다른 소주제와의 연결

- **소주제 1 → 소주제 3:**
  - 소주제 1에서 Expiring Soon으로 분류된 제품이 소주제 3에서도 Risk인지 교차 분석
- **소주제 2 → 소주제 3:**
  - 소주제 2에서 예측한 Avg_Daily_Sales를 사용하면 Days_To_Deplete가 더 정밀해짐
- **소주제 3 → 소주제 4:**
  - Risk 제품이 소주제 4의 어떤 군집에 속하는지 확인
  - 군집별 폐기 위험 비율 비교

---

## 부록: 전체 파이프라인 요약 흐름도

```
CSV 로드 (1,000행 × 37열)
  ↓
공통 전처리
  ├── 인도네시아 로케일 숫자 변환 (천단위`.` 제거 → 쉼표`,`→마침표`.`)
  ├── Reorder_Point 천단위 오파싱 수정 (10건, raw CSV 재추출)
  ├── 금액 컬럼 변환 ($, 천단위, 쉼표 소수점)
  └── 날짜 컬럼 파싱
  ↓
★ 핵심 Feature Engineering ★
  ├── Days_To_Expiry 계산 (Expiry_Date - Received_Date)
  ├── Stock_Age_Days 기준점 검증 (2025-09-09)
  ├── Remaining_Shelf_Days 계산 (Expiry_Date - 2025-09-10)
  ├── Days_To_Deplete 계산 (QOH / ADS)
  └── Waste_Risk 타겟 생성 (DTD > RSD → Risk)
  ↓
클래스 분포 확인 (Safe 57.5% / Risk 42.5%)
  ↓
EDA (클래스 분포, 카테고리별 위험 비율, DTE 분포, 피처 분포, 핵심 산점도)
  ↓
데이터 누수 진단 (DOI ≈ DTD 검증, 카테고리 결정력 분석)
  ↓
피처 선택 & 인코딩 (DOI 제거, Category/ABC One-Hot, FIFO/FEFO 이진)
  ↓
Train/Test Split (80:20, stratified)
  ↓
StandardScaler 적용
  ↓
3개 모델 학습 (LR, SVM, XGB) — class_weight/scale_pos_weight
  ├── Default → Cross-Validation
  └── Tuned (GridSearchCV)
  ↓
성능 평가 (Precision, Recall, F1, ROC-AUC, PR-AUC)
  ↓
★ Learning Curve (과적합 진단)
  ↓
최적 모델 선정 & 심층 분석 (Confusion Matrix, ROC/PR Curve, Feature Importance, SHAP)
  ↓
★ Permutation Importance (피처 중요도 교차검증)
  ↓
★ Calibration Curve + Brier Score (확률 신뢰도 검정)
  ↓
모델 저장 (joblib)
  ↓
인사이트 도출 & 결론 (카테고리 결정력, 99% 정확도 해석, 소주제 간 연결)
```
