# 소주제 2 — 일일 판매량 예측 (Regression) 구현 가이드

> 이 문서는 Claude Code가 소주제 2의 전체 파이프라인을 구현할 때 참조하는 가이드라인입니다.

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열)
- 소주제 2 담당: 이현아

### 1.2 소주제 2 목표

제품 속성과 재고 정보를 기반으로 **Avg_Daily_Sales(일일 평균 판매량)**를 예측하는 **회귀 모델**을 구축하고, 판매량에 가장 큰 영향을 미치는 요인을 SHAP 등으로 해석한다.

### 1.3 도출할 인사이트

- 제품 속성과 재고 정보만으로 일일 판매량을 어느 정도 정확하게 예측할 수 있는가?
- 판매량에 가장 큰 영향을 미치는 변수(피처)는 무엇인가?
- 카테고리(10종)별, ABC 등급별 판매량 패턴은 어떻게 다른가?
- 데이터 누수(Data Leakage) 피처를 제거했을 때 모델 성능이 어떻게 변하는가?
- R² Score의 높고 낮음이 의미하는 바는 무엇인가? (내재적 속성 vs 외부 변수)
- 입고월(Received_Month)에 따른 판매량의 계절성 패턴이 존재하는가?

---

## 2. 데이터 명세

### 2.1 원본 데이터

- **파일:** `Inventory Management E-Grocery - InventoryData.csv`
- **규모:** 1,000행 × 37열
- **결측치:** Notes 컬럼 834건 (분석 미사용 컬럼), 실질적 결측치 이슈 없음

### 2.2 원본 컬럼 전체 목록 및 소주제 2 사용 여부

| #   | 컬럼명                       | 데이터 타입       | 설명                                 | 소주제2 사용 여부                      |
| --- | ---------------------------- | ----------------- | ------------------------------------ | -------------------------------------- |
| 1   | SKU_ID                       | object            | 제품 고유 식별 코드 (`SKU0001` 형식) | ❌ 식별용                              |
| 2   | SKU_Name                     | object            | 제품명                               | ❌ 식별용                              |
| 3   | Category                     | object            | 제품 카테고리 (10개 범주)            | ✅ 피처 (인코딩)                       |
| 4   | ABC_Class                    | object            | ABC 분석 등급 (A/B/C)                | ✅ 피처 (인코딩)                       |
| 5   | Supplier_ID                  | object            | 공급업체 식별 코드                   | ❌ 식별용                              |
| 6   | Supplier_Name                | object            | 공급업체명                           | ❌ 식별용                              |
| 7   | Warehouse_ID                 | object            | 창고 고유 코드 (5개 권역)            | ❌ 소주제2 미사용                      |
| 8   | Warehouse_Location           | object            | 창고 소재지                          | ❌ 소주제2 미사용                      |
| 9   | Batch_ID                     | object            | 배치 고유 코드                       | ❌ 식별용                              |
| 10  | Received_Date                | object → datetime | 제품 입고일 (`YYYY-MM-DD`)           | ✅ 파생변수(Received_Month) 생성용     |
| 11  | Last_Purchase_Date           | object → datetime | 최근 발주일                          | ❌ 소주제2 미사용                      |
| 12  | Expiry_Date                  | object → datetime | 유통기한 만료일                      | ❌ 소주제2 미사용                      |
| 13  | Stock_Age_Days               | int               | 재고 보유 일수 (입고 후 경과일)      | ✅ 피처                                |
| 14  | Quantity_On_Hand             | int               | 현재 보유 재고 수량                  | ✅ 피처                                |
| 15  | Quantity_Reserved            | int               | 예약된 재고 수량                     | ❌ 소주제2 미사용                      |
| 16  | Quantity_Committed           | int               | 출고 확정 수량                       | ❌ 소주제2 미사용                      |
| 17  | Damaged_Qty                  | int               | 파손/불량 재고 수량                  | ❌ 소주제2 미사용                      |
| 18  | Returns_Qty                  | int               | 반품 수량                            | ❌ 소주제2 미사용                      |
| 19  | Avg_Daily_Sales              | object → float    | 일일 평균 판매량 (쉼표 소수점 형식)  | 🎯 타겟 변수                           |
| 20  | Forecast_Next_30d            | float64 (오파싱)  | 향후 30일 수요 예측량                | ❌ 소주제2 미사용 (Data Leakage 가능)  |
| 21  | Days_of_Inventory            | object → float    | 재고 보유 가능 일수 (쉼표 소수점)    | ⚠️ **Data Leakage** (타겟 직접 파생)   |
| 22  | Reorder_Point                | float64 (오파싱)  | 재주문 기준점                        | ✅ 피처 (전처리 필요: 천단위 `.` 10건) |
| 23  | Safety_Stock                 | int               | 안전 재고 수준                       | ✅ 피처                                |
| 24  | Lead_Time_Days               | int               | 발주 리드타임 (일)                   | ✅ 피처                                |
| 25  | Unit_Cost_USD                | object → float    | 제품 단가 (`$5,81` 형식)             | ✅ 피처 (전처리 필요)                  |
| 26  | Last_Purchase_Price_USD      | object → float    | 최근 구매 단가                       | ❌ 소주제2 미사용                      |
| 27  | Total_Inventory_Value_USD    | object → float    | 총 재고 가치                         | ❌ 소주제2 미사용                      |
| 28  | SKU_Churn_Rate               | object → float    | SKU 이탈률 (쉼표 소수점)             | ❌ 소주제2 미사용                      |
| 29  | Order_Frequency_per_month    | object → float    | 월간 발주 빈도 (쉼표 소수점)         | ✅ 피처                                |
| 30  | Supplier_OnTime_Pct          | object → float    | 정시 납품률 (`%` + 쉼표 소수점)      | ❌ 소주제2 미사용                      |
| 31  | FIFO_FEFO                    | object            | 출고 방식 (FIFO/FEFO)                | ❌ 소주제2 미사용                      |
| 32  | Inventory_Status             | object            | 재고 상태 (4클래스)                  | ❌ 소주제2 미사용 (소주제1 타겟)       |
| 33  | Count_Variance               | int               | 실사 시 재고 차이                    | ❌ 소주제2 미사용                      |
| 34  | Audit_Date                   | object → datetime | 재고 감사일                          | ❌ 소주제2 미사용                      |
| 35  | Audit_Variance_Pct           | object → float    | 감사 차이 비율                       | ❌ 소주제2 미사용                      |
| 36  | Demand_Forecast_Accuracy_Pct | object → float    | 수요 예측 정확도                     | ❌ 소주제2 미사용                      |
| 37  | Notes                        | object            | 비고/메모                            | ❌ 미사용 (결측 834건)                 |

### 2.3 타겟 변수: Avg_Daily_Sales

| 항목         | 내용                                                             |
| ------------ | ---------------------------------------------------------------- |
| 원본 타입    | 문자열 (object) — 인도네시아 로케일 쉼표 소수점 형식 (`"28,57"`) |
| 변환 후 타입 | 연속형 (float)                                                   |
| 전처리       | 쉼표(`,`) → 마침표(`.`) 변환 후 float 캐스팅                     |
| Mean         | 26.58                                                            |
| Std          | 21.25                                                            |
| Min / Max    | 1.01 / 99.50                                                     |
| Median       | 20.23                                                            |
| Skewness     | 1.2292 (양의 왜도 — 오른쪽 꼬리)                                 |
| Kurtosis     | 0.9751                                                           |

> **주의:** 원본 데이터에서 `Avg_Daily_Sales`는 `"28,57"` 형태의 문자열이므로 반드시 전처리 후 사용

### 2.4 카테고리(Category) 분포 — 10개 범주

| 카테고리      | 건수 | 비율  |
| ------------- | ---- | ----- |
| Pantry        | 137  | 13.7% |
| Personal Care | 126  | 12.6% |
| Beverages     | 120  | 12.0% |
| Fresh Produce | 110  | 11.0% |
| Household     | 103  | 10.3% |
| Dairy         | 96   | 9.6%  |
| Meat          | 87   | 8.7%  |
| Frozen        | 86   | 8.6%  |
| Bakery        | 69   | 6.9%  |
| Seafood       | 66   | 6.6%  |

### 2.5 ABC 등급(ABC_Class) 분포

| 등급 | 의미                         | 건수 | 비율  |
| ---- | ---------------------------- | ---- | ----- |
| A    | 고가치 제품 (매출 기여 상위) | 200  | 20.0% |
| B    | 중간 가치 제품               | 300  | 30.0% |
| C    | 저가치 제품 (품목 수 多)     | 500  | 50.0% |

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

# 1-1. Forecast_Next_30d 특수 처리
#      pandas가 float64로 자동 파싱하면서 천단위 마침표를 소수점으로 오해
#      (예: CSV의 '1.377' → pandas 1.377, 실제는 1377)
#      원본 CSV에서 raw 문자열 재추출 필요
raw_fn30 = []
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        raw_fn30.append(row['Forecast_Next_30d'])
df['Forecast_Next_30d'] = [float(v.replace('.', '').replace(',', '.')) for v in raw_fn30]

# 1-2. Reorder_Point 특수 처리
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

### 3.2 소주제 2 전용 파생변수

| 파생 변수      | 생성 방식                | 설명                      |
| -------------- | ------------------------ | ------------------------- |
| Received_Month | `Received_Date.dt.month` | 입고월 (계절성 반영 목적) |

```python
df['Received_Month'] = df['Received_Date'].dt.month
```

> **참고:** `Received_Month`는 소주제 2에서만 사용하는 고유 파생변수로, 계절적 판매 패턴을 포착하기 위한 목적.

### 3.3 카테고리 & ABC 등급 인코딩

```python
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

> One-Hot Encoding 사용, `drop_first=True`로 다중공선성 방지
>
> - Category: 10개 → 9개 더미 (Bakery가 baseline)
> - ABC_Class: 3개 → 2개 더미 (A가 baseline)

---

## 4. 데이터 누수(Data Leakage) 진단

> ⚠️ **소주제 1에서도 발견된 데이터 누수 패턴이 소주제 2에도 존재한다.**

### 4.1 Days_of_Inventory = Quantity_On_Hand / Avg_Daily_Sales

실제 데이터 검증 결과:

| 검증 항목                     | 결과                                                        |
| ----------------------------- | ----------------------------------------------------------- |
| 수식 일치 행 수 (diff < 0.01) | **972 / 1,000행** (97.2%)                                   |
| 최대 차이                     | 21.93 (반올림 등 미세 오차)                                 |
| DOI + QOH → ADS 선형 R²       | 0.471 (비선형 관계이므로 낮지만 트리 모델은 완벽 학습 가능) |

```
Days_of_Inventory = Quantity_On_Hand / Avg_Daily_Sales
→ 따라서 Avg_Daily_Sales = Quantity_On_Hand / Days_of_Inventory (역산 가능!)
```

**문제:** `Days_of_Inventory`를 피처로 사용하면 `Quantity_On_Hand`와 조합하여 타겟 변수를 거의 완벽히 역산할 수 있으므로, 트리 기반 모델이 이 관계를 학습하여 비현실적으로 높은 R²를 달성

**해결:** 소주제 1의 접근 방식과 동일하게 **Scenario A (전체 피처)** vs **Scenario B (누수 피처 제거)** 비교 실험 수행

### 4.2 Scenario 정의

| Scenario      | 피처 구성                                            | 목적                            |
| ------------- | ---------------------------------------------------- | ------------------------------- |
| **A** (Full)  | Days_of_Inventory 포함 (9 수치 + 11 범주 = 20개)     | 누수 포함 시 성능 확인 (참고용) |
| **B** (Clean) | Days_of_Inventory 제거 (8 수치 + 11 범주 = **19개**) | 실질적 예측 성능 평가 (메인)    |

> **Scenario B가 메인 분석 대상.** Scenario A는 누수의 영향을 보여주기 위한 비교군.

### 4.3 Order_Frequency_per_month 준누수(Quasi-Leakage) 검증 ★

> ⚠️ **소주제 1에서의 Days_of_Inventory 추가 검증과 동일한 취지의 분석**

| 검증 항목 | 내용 |
|-----------|------|
| 상관계수 | 타겟(Avg_Daily_Sales)과 **0.9225** — 압도적 1위 |
| 우려 | "많이 팔리는 제품을 더 자주 발주" → 발주 빈도는 판매량의 **결과**일 가능성 |
| 핵심 질문 | 이 변수가 예측 시점에 사전에 알 수 있는 정보인가? |

**검증 방법:**

```python
# 1. Order_Frequency 제거 전/후 모델 성능 비교
# Scenario B-1: Order_Frequency 포함 (기존 Scenario B)
# Scenario B-2: Order_Frequency 제거

# 2. 성능 차이(ΔR²)를 계산하여 이 변수의 기여도 정량화
# 3. 만약 ΔR² > 0.3이면 → 이 변수에 대한 과도한 의존 경고
# 4. ΔR² 결과와 무관하게 Scenario B를 메인으로 유지 (실무적으로 발주 빈도는 관측 가능)
```

**판단 기준:**
- 수학적 파생 관계(DOI = QOH/ADS)가 아니므로 **엄밀한 데이터 누수는 아님**
- 단, 인과관계의 방향(발주→판매 vs 판매→발주)에 대한 논의가 필요
- 결론적으로 Scenario B에 포함하되, **과도한 의존도**에 대한 해석을 결과 보고서에 명시

---

## 5. 모델링 상세 설계

### 5.1 피처 목록 (최종 입력 변수 — Scenario B 기준)

**수치형 피처 (8개):**

- Unit_Cost_USD (전처리: `$` 제거, 천단위`.` 제거, 쉼표→마침표)
- Quantity_On_Hand
- Reorder_Point (전처리: 천단위 `.` 10건 수정 필요)
- Safety_Stock
- Lead_Time_Days
- Stock_Age_Days
- Order_Frequency_per_month (전처리: 쉼표→마침표)
- Received_Month (파생)

**범주형 피처 (One-Hot 인코딩 후):**

- Category_Beverages, Category_Dairy, Category_Fresh Produce, Category_Frozen, Category_Household, Category_Meat, Category_Pantry, Category_Personal Care, Category_Seafood (9개, Bakery baseline)
- ABC_Class_B, ABC_Class_C (2개, A baseline)

> **총 피처 수 (Scenario B):** 8(수치) + 9(카테고리) + 2(ABC) = **19개**

### 5.2 피처-타겟 상관관계 (사전 분석 결과)

| 피처                      | 상관계수    | 비고                           |
| ------------------------- | ----------- | ------------------------------ |
| Order_Frequency_per_month | **0.9225**  | 🔥 매우 강한 양의 상관         |
| Quantity_On_Hand          | **0.6537**  | 재고 수량 ↑ → 판매량 ↑         |
| Reorder_Point             | **0.6507**  | 재주문점 ↑ → 판매량 ↑          |
| Safety_Stock              | **0.6495**  | 안전재고 ↑ → 판매량 ↑          |
| Unit_Cost_USD             | **-0.3688** | 가격 ↑ → 판매량 ↓              |
| Lead_Time_Days            | -0.0028     | 거의 무관                      |
| Stock_Age_Days            | 0.0065      | 거의 무관                      |
| Received_Month            | -0.0122     | 거의 무관 (뚜렷한 계절성 없음) |

> **핵심:** `Order_Frequency_per_month`(0.92)가 압도적으로 높은 상관관계를 보임.
> 이는 판매량이 높을수록 발주 빈도가 올라가는 자연스러운 관계이며,
> 수학적 파생변수가 아니므로 **데이터 누수가 아닌 강한 예측 변수**로 판단.

### 5.3 타겟 변수

```python
y = df['Avg_Daily_Sales']  # 연속형 (float), 전처리 후 사용
```

### 5.4 Train/Test Split

```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
```

- 비율: 80:20
- `random_state=42` 고정
- 회귀 문제이므로 `stratify` 미사용

### 5.5 스케일링

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

> Linear Regression, Ridge, Lasso 등 정규화 기반 모델을 위해 StandardScaler 적용 필수
> 트리 기반 모델은 스케일링 없이도 동작하지만, 일관성을 위해 동일 데이터 사용

### 5.6 학습할 모델 (5종)

| #   | 모델                    | 라이브러리 | 주요 하이퍼파라미터                               | 비고                      |
| --- | ----------------------- | ---------- | ------------------------------------------------- | ------------------------- |
| 1   | Linear Regression       | sklearn    | 기본값                                            | Baseline 모델             |
| 2   | Ridge Regression        | sklearn    | `alpha=1.0` (기본) → 탐색 가능                    | L2 정규화                 |
| 3   | Lasso Regression        | sklearn    | `alpha=1.0` (기본) → 탐색 가능, `max_iter=10000`  | L1 정규화, 피처 선택 효과 |
| 4   | Random Forest Regressor | sklearn    | `n_estimators=100`, `random_state=42`             | 앙상블 (배깅)             |
| 5   | XGBoost Regressor       | xgboost    | `objective='reg:squarederror'`, `random_state=42` | 앙상블 (부스팅)           |

> **참고:** 소주제 1에서는 LightGBM이 최종 모델로 선정되었으나, 소주제 2에서는 SHAP 해석에 최적화된 XGBoost를 중심으로 분석하며, 모델 수를 5종으로 유지한다.

> - Default 학습 후 Cross-Validation 수행
> - 이후 하이퍼파라미터 튜닝하여 Default vs Tuned 비교
> - 소규모 데이터(1,000행)이므로 트리 기반 모델의 **과적합에 주의** (max_depth 제한, min_samples_leaf 증가 등)

### 5.7 하이퍼파라미터 튜닝 (과적합 방지)

| 모델          | 튜닝 파라미터    | 범위/값                       | 목적                 |
| ------------- | ---------------- | ----------------------------- | -------------------- |
| Ridge         | alpha            | [0.01, 0.1, 1.0, 10.0, 100.0] | 정규화 강도 탐색     |
| Lasso         | alpha            | [0.001, 0.01, 0.1, 1.0]       | 피처 선택 강도       |
| Random Forest | max_depth        | 5~15                          | 과적합 방지          |
| Random Forest | min_samples_leaf | 3~10                          | 리프 노드 최소 샘플  |
| XGBoost       | max_depth        | 3~6                           | 과적합 방지          |
| XGBoost       | learning_rate    | 0.01~0.1                      | 학습 속도 조절       |
| XGBoost       | subsample        | 0.7~0.9                       | 샘플링으로 분산 감소 |
| XGBoost       | reg_alpha        | 0.0~1.0                       | L1 정규화            |

### 5.8 평가 지표

| 지표               | 수식/설명                      | 선택 이유                                            |
| ------------------ | ------------------------------ | ---------------------------------------------------- |
| **RMSE**           | √(MSE), 큰 오차에 더 큰 패널티 | 예측 오차의 스케일을 타겟과 동일하게 해석 가능       |
| **MAE**            | 절대 오차 평균                 | 이상치에 강건한 오차 지표                            |
| **R² Score**       | 1 - (SS_res / SS_tot)          | 모델이 분산의 몇 %를 설명하는지 (0~1, 높을수록 좋음) |
| **Train-Test Gap** | Train R² - Test R²             | 과적합 정도 판단 (낮을수록 좋음)                     |

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
```

### 5.9 기대 성능 범위 (사전 분석 기반)

| 모델              | 예상 Test R² | 비고                                      |
| ----------------- | ------------ | ----------------------------------------- |
| Linear Regression | ~0.88        | Baseline                                  |
| Ridge / Lasso     | ~0.88        | LR과 유사 (피처 수 적어 정규화 효과 미미) |
| Random Forest     | ~0.91        | 비선형 관계 포착                          |
| XGBoost           | ~0.94        | 최고 성능 기대                            |

> `Order_Frequency_per_month`(상관 0.92)와 재고 관련 피처(QOH, Reorder_Point, Safety_Stock) 덕분에 비교적 높은 R² 달성 가능.
> R²가 예상보다 낮게 나올 경우: 프로모션, 할인, 매장 위치 등 **외부 변수 부재**가 원인.

---

## 6. 시각화 및 해석 요구사항

### 6.1 EDA 시각화 (모델링 전)

1. **타겟 변수(Avg_Daily_Sales) 분포**
   - `histplot` 또는 `displot` (KDE 포함)
   - 정규성 확인, 왜도(skewness=1.23) 표기

2. **카테고리별 판매량 분포**
   - `boxplot` with `x='Category'`, `y='Avg_Daily_Sales'`
   - 10개 카테고리 간 판매량 차이 확인

3. **ABC 등급별 판매량 분포**
   - `boxplot` with `x='ABC_Class'`, `y='Avg_Daily_Sales'`
   - A/B/C 등급 간 판매량 차이 확인

4. **수치형 피처 vs Avg_Daily_Sales 산점도**
   - `scatterplot` 또는 `pairplot`
   - 주요 피처(Unit_Cost_USD, Quantity_On_Hand, Order_Frequency_per_month 등)와 Avg_Daily_Sales 간 관계

5. **피처 간 상관관계 히트맵**
   - `heatmap` with `annot=True`
   - Avg_Daily_Sales와 높은 상관관계를 보이는 피처 확인

6. **Received_Month별 판매량 추이**
   - `barplot` 또는 `lineplot`
   - 월별 판매량 패턴 (계절성) 확인

### 6.2 데이터 누수 진단 시각화

7. **Days_of_Inventory vs Avg_Daily_Sales 관계**
   - `scatterplot`으로 역비례 관계 시각화 (ADS = QOH / DOI)
   - 누수 포함 vs 제거 시 R² 비교 바 차트

### 6.3 모델링 후 시각화

8. **모델별 성능 비교 바 차트**
   - x축: 모델명 (5종), y축: RMSE, MAE, R²
   - Default vs Tuned 비교
   - 3개 지표를 서브플롯 또는 그룹형 바 차트로 비교

9. **실제값 vs 예측값 산점도** (최적 모델 기준)
   - x축: 실제 Avg_Daily_Sales, y축: 예측값
   - 대각선(y=x) 기준선 추가
   - 이상적이면 점들이 대각선 근처에 분포

10. **잔차(Residual) 분석** (최적 모델 기준)
    - 잔차 분포: `histplot` (정규분포 여부 확인)
    - 잔차 vs 예측값: `scatterplot` (등분산성 확인, 패턴 없어야 정상)

11. **Feature Importance (트리 기반 모델)**
    - Random Forest / XGBoost의 `feature_importances_` 활용
    - 수평 바 차트, 상위 10~15개 피처

12. **SHAP Summary Plot** (XGBoost 기준, 핵심 시각화)
    - 피처별 SHAP value 분포
    - 각 피처가 판매량 예측에 미치는 방향(+/-)과 크기 해석

### 6.4 Learning Curve (과적합 시각적 진단) ★

> 소주제 1에서 추가한 분석과 동일한 목적. Train/Test Gap 수치만으로는 과적합의 **원인**(데이터 부족 vs 모델 복잡도)을 구분할 수 없으므로, 학습 데이터 크기별 성능 변화를 시각화한다.

13. **Learning Curve (5개 모델)**
    - `sklearn.model_selection.learning_curve` 활용
    - x축: 학습 데이터 크기 (비율), y축: R² 또는 Neg-RMSE
    - Train/Validation 점수를 std band와 함께 표시
    - 2×3 또는 3×2 subplot (5개 모델)
    - **해석 포인트:**
      - Train과 Val 곡선이 수렴하면 → 데이터 충분, 과적합 아님
      - 둘 사이 Gap이 크면 → 과적합 (모델 복잡도 축소 필요)
      - Val 곡선이 계속 상승 중이면 → 데이터 추가 시 성능 향상 기대

```python
from sklearn.model_selection import learning_curve

train_sizes, train_scores, val_scores = learning_curve(
    model, X_train_scaled, y_train,
    cv=5, scoring='r2',
    train_sizes=np.linspace(0.1, 1.0, 10),
    random_state=42, n_jobs=-1
)
```

### 6.5 Permutation Importance (Impurity 편향 검증) ★

> 소주제 1에서 Impurity-based와 Permutation Importance 순위 역전(Days_of_Inventory 1위→2위)을 발견한 것과 동일한 검증. 특히 Order_Frequency_per_month의 실제 기여도를 검증한다.

14. **Permutation Importance (XGBoost + Random Forest)**
    - `sklearn.inspection.permutation_importance` 활용
    - `n_repeats=10`, `random_state=42`, `scoring='r2'`
    - **Impurity-based vs Permutation 순위 비교 테이블** 포함
    - 수평 바 차트 (side-by-side 비교)

```python
from sklearn.inspection import permutation_importance

perm_imp = permutation_importance(
    model, X_test_scaled, y_test,
    n_repeats=10, random_state=42, scoring='r2'
)
```

**해석 포인트:**
- 고 카디널리티 수치형 변수(QOH, Reorder_Point 등)가 Impurity에서 과대평가되는지 확인
- Permutation에서 Order_Frequency_per_month가 여전히 1위인지 확인
- 범주형 변수(Category, ABC_Class)의 순위 변화 확인

### 6.6 잔차 정규성 검정 (Shapiro-Wilk) ★

> 잔차의 정규분포 여부를 시각적으로만 판단하지 않고, 통계적 검정으로 정량화한다.

15. **Shapiro-Wilk Test**
    - `scipy.stats.shapiro(residuals)`
    - p-value < 0.05 → 잔차가 정규분포를 따르지 않음
    - Q-Q Plot과 함께 제시

```python
from scipy.stats import shapiro
stat, p_value = shapiro(residuals)
print(f"Shapiro-Wilk: W={stat:.4f}, p-value={p_value:.4e}")
```

### 6.7 선택 시각화 (추가 분석)

- Ridge/Lasso 정규화 경로 (alpha vs 계수 변화)
- Lasso에서 계수가 0이 된 피처 확인 (피처 선택 효과)

---

## 7. 코드 구조 및 출력 형식

### 7.1 Jupyter Notebook 구조

```
02_Avg_Daily_Sales_Prediction.ipynb
│
├── 0. 라이브러리 임포트 & 설정
│   ├── 필수 라이브러리 import
│   ├── 시각화 한글 폰트 설정 (Malgun Gothic)
│   └── 경고 메시지 숨김, 시드 고정
│
├── 1. 데이터 로드 & 기본 확인
│   ├── CSV 로드
│   ├── df.shape, df.info(), df.describe()
│   ├── 결측치 확인
│   └── Avg_Daily_Sales 기초 통계 확인 (mean, std, min, max, 왜도, 첨도)
│
├── 2. 데이터 전처리
│   ├── 인도네시아 로케일 숫자 변환 (천단위 `.` 제거 → 쉼표 소수점 `.` 변환)
│   ├── Reorder_Point 천단위 오파싱 수정 (10건)
│   ├── 금액 컬럼 변환 ($, 천단위 구분 제거, 쉼표→마침표)
│   ├── 날짜 컬럼 파싱
│   ├── 파생변수 생성 (Received_Month)
│   └── 전처리 결과 검증
│
├── 3. EDA (탐색적 데이터 분석)
│   ├── 타겟 변수(Avg_Daily_Sales) 분포 시각화
│   ├── 카테고리별 판매량 분포 (boxplot)
│   ├── ABC 등급별 판매량 분포 (boxplot)
│   ├── 수치형 피처 vs Avg_Daily_Sales 산점도
│   ├── Received_Month별 판매량 추이
│   └── 피처 간 상관관계 히트맵
│
├── 4. 데이터 누수(Data Leakage) 진단
│   ├── Days_of_Inventory = QOH / ADS 수식 검증
│   ├── 누수 피처 단독 예측력 테스트
│   ├── 시각화: DOI vs ADS 관계, 누수 영향도
│   └── Scenario A(Full) vs Scenario B(Clean) 정의
│
├── 5. 피처/타겟 분리 & Train/Test Split
│   ├── 피처 선택 (누수 피처 제거한 Scenario B)
│   ├── One-Hot 인코딩 (Category + ABC_Class)
│   ├── train_test_split (80:20)
│   └── StandardScaler 적용
│
├── 6. 모델 학습 & 평가
│   ├── 6.1 Default 모델 학습 (5종)
│   ├── 6.2 교차검증 (5-Fold CV)
│   ├── 6.3 하이퍼파라미터 튜닝 (과적합 방지)
│   ├── 6.4 Default vs Tuned 비교
│   ├── 6.5 모델 성능 비교 종합표 & 바 차트
│   └── 6.6 Learning Curve (과적합 시각적 진단) ★
│
├── 7. 최적 모델 심층 분석
│   ├── 실제값 vs 예측값 산점도
│   ├── 잔차(Residual) 분석
│   ├── Feature Importance (Impurity-based) 시각화
│   ├── Permutation Importance & 순위 비교 ★
│   ├── SHAP Summary Plot (Bar + Dot)
│   └── 잔차 정규성 검정 (Shapiro-Wilk) ★
│
├── 8. 모델 저장
│   ├── 최적 모델 joblib 저장
│   ├── Scaler 저장
│   └── 피처 정보 저장
│
└── 9. 결론 및 인사이트
    ├── 핵심 발견 사항 정리 (데이터 누수 진단 포함)
    ├── 판매량 예측의 한계와 원인 분석
    ├── 카테고리별·ABC 등급별 판매 패턴 요약
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
- **그래프 저장:** 주요 시각화는 `plt.savefig('outputs/figures/파일명.png', dpi=150, bbox_inches='tight')` 로 저장

### 7.3 모델 성능 결과 테이블 출력 형식

```python
import pandas as pd

results = pd.DataFrame({
    '모델': ['Linear Regression', 'Ridge', 'Lasso', 'Random Forest', 'XGBoost'],
    'Train R²': [lr_tr2, ridge_tr2, lasso_tr2, rf_tr2, xgb_tr2],
    'Test R²': [lr_r2, ridge_r2, lasso_r2, rf_r2, xgb_r2],
    'RMSE': [lr_rmse, ridge_rmse, lasso_rmse, rf_rmse, xgb_rmse],
    'MAE': [lr_mae, ridge_mae, lasso_mae, rf_mae, xgb_mae],
    'Gap': [lr_gap, ridge_gap, lasso_gap, rf_gap, xgb_gap]
})
results = results.sort_values('Test R²', ascending=False)
display(results)
```

---

## 8. 핵심 유의사항

### 8.1 데이터 관련

- 데이터가 1,000행으로 **소규모**이므로 과적합에 주의 (특히 트리 기반 모델)
- **인도네시아 로케일 형식 주의:**
  - `Avg_Daily_Sales`: `"28,57"` → 쉼표→마침표 변환
  - `Days_of_Inventory`: `"12,57"` → 동일 변환
  - `Order_Frequency_per_month`: `"5,00"` → 동일 변환
  - `SKU_Churn_Rate`: `"2.142,90"` 같은 **혼합 형식** 1건 존재 → 반드시 천단위 마침표 먼저 제거!
- **Reorder_Point 오파싱:** 10행에서 `'1.170'` → pandas 1.17 (실제 1170) → raw CSV 재추출 필수
- **Forecast_Next_30d 오파싱:** 276행에서 `'1.377'` → pandas 1.377 (실제 1377) → 소주제2 미사용이므로 영향 없음
- **금액 컬럼 복합 형식:** `Unit_Cost_USD`가 `"$5,81"` 형태 → `$` 제거, 천단위`.` 제거, 쉼표→마침표 변환 필수
- `Category` 컬럼은 올바른 철자 (이전 데이터의 `Catagory` 오타 아님)

### 8.2 데이터 누수 관련 (핵심)

- **`Days_of_Inventory` = `Quantity_On_Hand` / `Avg_Daily_Sales`** → 타겟의 직접 파생변수!
  - 972/1000행에서 정확히 일치 (차이 < 0.01)
  - 트리 기반 모델이 이 관계를 학습하면 비현실적으로 높은 R² 달성
  - **반드시 Scenario B (DOI 제거)를 메인 분석으로 사용**
- `Forecast_Next_30d`도 사용하지 않음 — 실제 운영 시 미래 예측값은 입력 불가능

### 8.3 모델링 관련

- **Linear Regression은 Baseline** — 이 모델의 성능을 기준으로 다른 모델의 개선 정도를 평가
- **Ridge vs Lasso 비교:** Ridge는 모든 피처를 유지하면서 계수를 축소, Lasso는 불필요한 피처 계수를 0으로 만들어 피처 선택 효과
- 스케일링은 Linear/Ridge/Lasso에 **필수**, 트리 기반에는 선택적이나 일관성을 위해 적용
- 모델 비교 시 **동일한 train/test 분할** 사용 (random_state 고정)
- R²가 음수일 수 있음 → 모델이 단순 평균보다 나쁜 예측을 한다는 의미

### 8.4 해석 관련 (핵심)

- **SHAP 분석이 소주제 2의 핵심 해석 도구** — 단순 Feature Importance보다 피처가 예측에 미치는 방향(+/-)까지 파악 가능
- `Order_Frequency_per_month`가 가장 중요한 피처로 나올 가능성 높음 (상관 0.92)
  - **해석:** 판매량이 높은 제품은 더 자주 발주해야 하므로 발주 빈도와 판매량의 강한 양의 관계는 자연스러움
  - 이 피처를 제외하면 R²가 상당히 하락할 수 있음 → 추가 실험으로 검증
- R² Score 해석 방향:
  - R² ≈ 0.88~0.94: 재고 및 발주 관련 피처만으로도 판매량의 88~94% 설명 가능
  - 나머지 6~12%: 마케팅, 계절성, 매장 위치, 프로모션 등 **외부 변수**의 영향
  - 현재 데이터셋에 이러한 외부 변수가 부재하므로 한계 명시
- 카테고리별(10종) 판매량 패턴이 유의미하게 다르다면, **카테고리 특화 모델**의 가능성 언급
- ABC 등급별(A/B/C) 판매량 패턴 비교 — A등급 고가치 제품의 판매 특성 분석
- Lasso에서 계수가 0이 된 피처가 있다면 → 해당 피처는 판매량 예측에 기여도가 낮음

### 8.5 다른 소주제와의 연결

- 소주제 2에서 예측한 **Avg_Daily_Sales** → 소주제 3의 `Days_To_Deplete = Quantity_On_Hand / Avg_Daily_Sales` 계산에 활용 가능
  - 더 정밀한 판매량 예측이 → 더 정밀한 폐기 위험 예측으로 이어짐
- SHAP에서 중요하다고 나온 피처 → 소주제 4의 클러스터링 피처 선정에 참고
- 소주제 2의 결과를 README.md 3.2절의 결과 테이블에 기입

---

## 9. SHAP 분석 상세 가이드

> 소주제 2에서 SHAP은 핵심 해석 도구이므로 별도 섹션으로 상세 안내

### 9.1 SHAP 설치 및 임포트

```python
import shap
```

### 9.2 SHAP 적용 (XGBoost 기준)

```python
# XGBoost 모델 학습 후
# ⚠️ SHAP TreeExplainer에는 스케일링되지 않은 피처명이 필요
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test_df)  # DataFrame으로 전달하여 피처명 보존
```

### 9.3 SHAP 시각화

```python
# 1. Summary Plot (Bar) — 피처 중요도 순위
shap.summary_plot(shap_values, X_test_df, plot_type="bar", show=False)
plt.title("SHAP Feature Importance (일일 판매량 예측)")
plt.tight_layout()
plt.savefig('outputs/figures/shap_importance_bar_s2.png', dpi=150, bbox_inches='tight')
plt.show()

# 2. Summary Plot (Dot/Beeswarm) — 피처별 영향 방향 + 크기
shap.summary_plot(shap_values, X_test_df, show=False)
plt.title("SHAP Summary Plot (일일 판매량 예측)")
plt.tight_layout()
plt.savefig('outputs/figures/shap_summary_dot_s2.png', dpi=150, bbox_inches='tight')
plt.show()

# 3. (선택) Dependence Plot — 핵심 피처의 SHAP 값 분석
shap.dependence_plot("Order_Frequency_per_month", shap_values, X_test_df, show=False)
plt.savefig('outputs/figures/shap_dependence_s2.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 9.4 SHAP 해석 포인트

- **SHAP value > 0:** 해당 피처 값이 판매량을 **높이는** 방향으로 기여
- **SHAP value < 0:** 해당 피처 값이 판매량을 **낮추는** 방향으로 기여
- **색상 (Dot Plot):** 빨간색 = 피처 값이 큰 경우, 파란색 = 피처 값이 작은 경우
- 예: Order_Frequency_per_month가 높을수록(빨간색) SHAP value가 양수 → 발주 빈도가 높을수록 판매량이 높음
- 예: Unit_Cost_USD가 높을수록(빨간색) SHAP value가 음수 → 단가가 비싼 제품일수록 판매량이 낮음

---

## 10. 기대 산출물 체크리스트

- [ ] `02_Avg_Daily_Sales_Prediction.ipynb` — 전체 분석 노트북
- [ ] `outputs/figures/eda_target_distribution_s2.png` — 타겟 변수 분포
- [ ] `outputs/figures/eda_category_sales_boxplot_s2.png` — 카테고리별 판매량 분포
- [ ] `outputs/figures/eda_abc_sales_boxplot_s2.png` — ABC 등급별 판매량 분포
- [ ] `outputs/figures/eda_scatter_features_s2.png` — 수치형 피처 vs 타겟 산점도
- [ ] `outputs/figures/eda_monthly_sales_s2.png` — 월별 판매량 추이
- [ ] `outputs/figures/eda_correlation_heatmap_s2.png` — 피처 상관관계 히트맵
- [ ] `outputs/figures/data_leakage_diagnosis_s2.png` — 데이터 누수 진단
- [ ] `outputs/figures/model_comparison_s2.png` — 모델 성능 비교 차트
- [ ] `outputs/figures/model_comparison_default_vs_tuned_s2.png` — Default vs Tuned 비교
- [ ] `outputs/figures/actual_vs_predicted_s2.png` — 실제값 vs 예측값 산점도
- [ ] `outputs/figures/residual_analysis_s2.png` — 잔차 분석
- [ ] `outputs/figures/feature_importance_s2.png` — Feature Importance 차트 (Impurity-based)
- [ ] `outputs/figures/permutation_vs_impurity_importance_s2.png` — Permutation vs Impurity 비교 ★
- [ ] `outputs/figures/learning_curve_s2.png` — Learning Curve (5개 모델) ★
- [ ] `outputs/figures/order_freq_quasi_leakage_s2.png` — Order_Frequency 준누수 검증 ★
- [ ] `outputs/figures/shap_importance_bar_s2.png` — SHAP Feature Importance
- [ ] `outputs/figures/shap_summary_dot_s2.png` — SHAP Summary Plot (Dot)
- [ ] `outputs/models/best_regressor.pkl` — 최적 모델 저장 (joblib)
- [ ] `outputs/models/scaler_regression.pkl` — StandardScaler 저장
- [ ] `outputs/models/feature_info_regression.json` — 피처 정보 저장
- [ ] 모델 성능 결과 요약 (RMSE, MAE, R² 수치)
- [ ] 잔차 정규성 검정 결과 (Shapiro-Wilk) ★
- [ ] 핵심 인사이트 3~5개 정리 (추가 분석 반영)

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
파생변수 생성 (Received_Month)
  ↓
EDA (타겟 분포, 카테고리별 분포, ABC 등급별 분포, 상관관계, 월별 추이)
  ↓
데이터 누수 진단 (Days_of_Inventory = QOH / ADS 검증)
  ↓
Scenario B 피처 선택 (DOI 제거) & One-Hot 인코딩
  ↓
Train/Test Split (80:20)
  ↓
StandardScaler 적용
  ↓
5개 모델 학습 (LR, Ridge, Lasso, RF, XGB)
  ├── Default → Cross-Validation
  └── Tuned (과적합 방지 하이퍼파라미터)
  ↓
성능 평가 (RMSE, MAE, R², Train-Test Gap)
  ↓
★ Order_Frequency 준누수 검증 (제거 전/후 ΔR² 비교)
  ↓
★ Learning Curve (5개 모델, 과적합 시각적 진단)
  ↓
최적 모델 선정 & 심층 분석
  ├── 실제값 vs 예측값 산점도
  ├── 잔차 분석 + ★ Shapiro-Wilk 정규성 검정
  ├── Feature Importance (Impurity-based)
  ├── ★ Permutation Importance (순위 비교)
  └── SHAP Summary Plot (Bar + Dot)
  ↓
모델 저장 (joblib)
  ↓
인사이트 도출 & 결론
```
