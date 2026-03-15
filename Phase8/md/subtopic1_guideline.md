# 소주제 1 — 재고 상태 분류 (Multi-class Classification) 구현 가이드

> 이 문서는 Claude Code가 소주제 1의 전체 파이프라인을 구현할 때 참조하는 가이드라인입니다.

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열)
- 소주제 1 담당: 정이랑

### 1.2 소주제 1 목표

제품의 재고·판매·공급 정보를 기반으로 현재 재고 상태(In Stock / Low Stock / Out of Stock / Expiring Soon)를 예측하는 **다중 클래스 분류 모델**을 구축하고, 상태를 결정짓는 핵심 요인을 도출한다.

### 1.3 도출할 인사이트

- 제품의 재고 상태(Inventory_Status)를 결정짓는 핵심 피처는 무엇인가?
- Out of Stock이 2건(0.2%)에 불과한 극심한 클래스 불균형 상황에서, 어떤 전략이 효과적인가?
- Confusion Matrix에서 가장 혼동이 많은 클래스 조합은 무엇이며, 그 이유는?
- Feature Importance 상위 변수가 실무적으로 어떤 의미를 갖는가?
- ABC 등급(A/B/C)에 따라 재고 상태 분류 패턴이 달라지는가?

---

## 2. 데이터 명세

### 2.1 원본 데이터

- **파일:** `Inventory Management E-Grocery - InventoryData.csv`
- **출처:** [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/)
- **규모:** 1,000행 × 37열
- **결측치:** Notes 컬럼 834건 (분석 미사용 컬럼) — 실질적 결측치 이슈 없음
- **데이터 특성:** 인도네시아(자카르타, 반둥, 수라바야, 덴파사르, 메단) 소재 E-Grocery 운영 데이터

### 2.2 전체 컬럼 목록 및 소주제1 활용 여부

| #   | 컬럼명                       | 데이터 타입 | 설명                                 | 소주제1 사용 여부  |
| --- | ---------------------------- | ----------- | ------------------------------------ | ------------------ |
| 1   | SKU_ID                       | object      | 제품 고유 식별 코드 (`SKU0001` 형식) | ❌ 식별용          |
| 2   | SKU_Name                     | object      | 제품명 (카테고리+번호 형식)          | ❌ 식별용          |
| 3   | Category                     | object      | 제품 카테고리 (10개 범주)            | ✅ 피처            |
| 4   | ABC_Class                    | object      | ABC 분석 등급 (A/B/C)                | ✅ 피처            |
| 5   | Supplier_ID                  | object      | 공급업체 식별 코드                   | ❌ 식별용          |
| 6   | Supplier_Name                | object      | 공급업체명 (인도네시아 기업)         | ❌ 식별용          |
| 7   | Warehouse_ID                 | object      | 창고 고유 코드 (5개 권역)            | ❌ 미사용          |
| 8   | Warehouse_Location           | object      | 창고 소재지 (도시 - 세부지역)        | ❌ 미사용          |
| 9   | Batch_ID                     | object      | 배치(입고 단위) 고유 코드            | ❌ 식별용          |
| 10  | Received_Date                | object      | 제품 입고일 (`YYYY-MM-DD`)           | ✅ 파생변수 생성용 |
| 11  | Last_Purchase_Date           | object      | 가장 최근 발주(구매)일               | ✅ 파생변수 생성용 |
| 12  | Expiry_Date                  | object      | 제품 유통기한 만료일                 | ✅ 파생변수 생성용 |
| 13  | Stock_Age_Days               | int         | 재고 보유 일수 (입고 후 경과 일수)   | ✅ 피처            |
| 14  | Quantity_On_Hand             | int         | 현재 보유 재고 수량                  | ✅ 피처            |
| 15  | Quantity_Reserved            | int         | 예약(확보)된 재고 수량               | ✅ 피처            |
| 16  | Quantity_Committed           | int         | 출고 확정된 재고 수량                | ✅ 피처            |
| 17  | Damaged_Qty                  | int         | 파손/불량 재고 수량                  | ❌ 소주제3 활용    |
| 18  | Returns_Qty                  | int         | 반품 수량                            | ❌ 소주제3 활용    |
| 19  | Avg_Daily_Sales              | object      | 일일 평균 판매량 (쉼표 소수점)       | ✅ 피처 (전처리)   |
| 20  | Forecast_Next_30d            | object      | 향후 30일 수요 예측량 (쉼표 소수점)  | ❌ 미사용          |
| 21  | Days_of_Inventory            | object      | 재고 보유 가능 일수 (쉼표 소수점)    | ✅ 피처 (전처리)   |
| 22  | Reorder_Point                | int         | 재주문 기준점                        | ✅ 피처            |
| 23  | Safety_Stock                 | int         | 안전 재고 수준                       | ✅ 피처            |
| 24  | Lead_Time_Days               | int         | 발주 리드타임 (일)                   | ✅ 피처            |
| 25  | Unit_Cost_USD                | object      | 제품 단가 (`$5,81` 형태)             | ✅ 피처 (전처리)   |
| 26  | Last_Purchase_Price_USD      | object      | 최근 구매 단가                       | ❌ 미사용          |
| 27  | Total_Inventory_Value_USD    | object      | 총 재고 가치                         | ❌ 미사용          |
| 28  | SKU_Churn_Rate               | object      | SKU 이탈률 (쉼표 소수점)             | ❌ 미사용          |
| 29  | Order_Frequency_per_month    | object      | 월간 발주 빈도 (쉼표 소수점)         | ❌ 소주제4 활용    |
| 30  | Supplier_OnTime_Pct          | object      | 공급업체 정시 납품률 (`%` 포함)      | ❌ 소주제4 활용    |
| 31  | FIFO_FEFO                    | object      | 재고 출고 방식 (FIFO/FEFO)           | ❌ 소주제3 활용    |
| 32  | Inventory_Status             | object      | 재고의 현재 운영 상태 (4클래스)      | 🎯 타겟 변수       |
| 33  | Count_Variance               | int         | 실사 시 재고 차이                    | ❌ 미사용          |
| 34  | Audit_Date                   | object      | 재고 감사(실사)일                    | ❌ 미사용          |
| 35  | Audit_Variance_Pct           | object      | 감사 차이 비율 (`%` 포함)            | ❌ 미사용          |
| 36  | Demand_Forecast_Accuracy_Pct | object      | 수요 예측 정확도 (`%` 포함)          | ❌ 미사용          |
| 37  | Notes                        | object      | 비고/메모 (결측치 834건)             | ❌ 미사용          |

### 2.3 카테고리(Category) 10종

| 카테고리      | 설명                             | 건수  |
| ------------- | -------------------------------- | ----- |
| Pantry        | 식료품 저장 식품 (쌀, 통조림 등) | 137건 |
| Personal Care | 개인 위생용품                    | 126건 |
| Beverages     | 음료류 (커피, 주스 등)           | 120건 |
| Fresh Produce | 신선 과일 및 채소류              | 110건 |
| Household     | 가정용품                         | 103건 |
| Dairy         | 유제품 (우유, 치즈, 요거트 등)   | 96건  |
| Meat          | 육류 (소고기, 돼지고기 등)       | 87건  |
| Frozen        | 냉동 식품류                      | 86건  |
| Bakery        | 베이커리류 (빵, 과자 등)         | 69건  |
| Seafood       | 수산물 (생선, 해산물 등)         | 66건  |

### 2.4 타겟 변수: Inventory_Status 분포

| 상태          | 의미                             | 건수  | 비율  |
| ------------- | -------------------------------- | ----- | ----- |
| In Stock      | 현재 정상 재고 보유 중           | 428건 | 42.8% |
| Expiring Soon | 유통기한 임박 제품               | 329건 | 32.9% |
| Low Stock     | 재고 수준이 재주문점 이하로 하락 | 241건 | 24.1% |
| Out of Stock  | 재고 완전 소진 (품절)            | 2건   | 0.2%  |

> ⚠️ **극심한 클래스 불균형** — Out of Stock이 2건(0.2%)에 불과하므로, **클래스 불균형 처리 전략**이 필수
>
> - 방안 1: Out of Stock → Low Stock에 병합하여 **3클래스**로 축소
> - 방안 2: SMOTE / class_weight 조정으로 **4클래스** 유지
> - 방안 3: Out of Stock을 **이상치(Anomaly)**로 취급하여 제외 후 3클래스 분류

### 2.5 ABC 등급(ABC_Class) 분포

| 등급 | 의미                         | 건수  | 비율  |
| ---- | ---------------------------- | ----- | ----- |
| A    | 고가치 제품 (매출 기여 상위) | 200건 | 20.0% |
| B    | 중간 가치 제품               | 300건 | 30.0% |
| C    | 저가치 제품 (매출 기여 하위) | 500건 | 50.0% |

---

## 3. 전처리 파이프라인

### 3.1 공통 전처리 (모든 소주제 공유)

> ⚠️ **인도네시아 로케일 형식 주의:** 쉼표(`,`)가 소수점으로 사용됨. 금액에는 `$` 기호 + 마침표(`.`) 천단위 구분 + 쉼표(`,`) 소수점의 복합 형식 적용.

```python
import pandas as pd
import numpy as np

# 0. 데이터 로드
df = pd.read_csv('Inventory Management E-Grocery - InventoryData.csv')

# 1. 인도네시아 로케일 숫자 변환 (쉼표 소수점 → 마침표 소수점)
comma_decimal_cols = [
    'Avg_Daily_Sales', 'Forecast_Next_30d', 'Days_of_Inventory',
    'SKU_Churn_Rate', 'Order_Frequency_per_month'
]
for col in comma_decimal_cols:
    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)

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

### 3.2 소주제 1 전용 파생변수

| 파생 변수             | 생성 방식                                                   | 설명                                            |
| --------------------- | ----------------------------------------------------------- | ----------------------------------------------- |
| Days_To_Expiry        | `Expiry_Date − Received_Date` (일수)                        | 입고일 기준 유통기한까지 남은 일수              |
| Days_Since_Last_Order | `Received_Date − Last_Purchase_Date` (일수)                 | 최근 발주 후 입고까지 경과 일수 (리드타임 추정) |
| Stock_Gap             | `Reorder_Point − Quantity_On_Hand`                          | 양수면 재고 부족, 음수면 재고 여유              |
| Available_Stock       | `Quantity_On_Hand − Quantity_Reserved − Quantity_Committed` | 실가용 재고 수량                                |

```python
# 소주제 1 파생변수 생성
df['Days_To_Expiry'] = (df['Expiry_Date'] - df['Received_Date']).dt.days
df['Days_Since_Last_Order'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days
df['Stock_Gap'] = df['Reorder_Point'] - df['Quantity_On_Hand']
df['Available_Stock'] = df['Quantity_On_Hand'] - df['Quantity_Reserved'] - df['Quantity_Committed']
```

### 3.3 클래스 불균형 처리

```python
# 방안 1 (권장): Out of Stock → Low Stock에 병합하여 3클래스
df['Inventory_Status_3cls'] = df['Inventory_Status'].replace('Out of Stock', 'Low Stock')
print(df['Inventory_Status_3cls'].value_counts())
# In Stock       428
# Expiring Soon  329
# Low Stock      243  (241 + 2)

# 방안 2: 4클래스 유지 + class_weight 조정
# → 모델 학습 시 class_weight='balanced' 옵션 사용
```

> **권장:** 방안 1(3클래스 통합)과 방안 2(4클래스 유지)를 모두 실험하여 비교 분석

### 3.4 카테고리 인코딩

```python
# Category + ABC_Class 인코딩
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

> One-Hot Encoding 사용, `drop_first=True`로 다중공선성 방지

### 3.5 데이터 누수(Data Leakage) 진단

> ⚠️ **핵심 단계:** 파생변수 중 타겟 변수의 정의 규칙에 해당하는 피처가 존재하면, 모델이 "예측"이 아닌 "규칙 재현"을 학습하게 된다. 반드시 모델 학습 전에 누수 여부를 진단해야 한다.

#### 3.5.1 단일 피처 분류력 진단

```python
from sklearn.tree import DecisionTreeClassifier

# 각 수치형 피처 1개만으로 타겟을 분류했을 때 정확도 측정
for feat in num_features_all:
    dt = DecisionTreeClassifier(max_depth=3, random_state=42)
    dt.fit(df[[feat]], y_temp)
    acc = dt.score(df[[feat]], y_temp)
    # Acc >= 0.70이면 누수 의심
```

> 판정 기준: 단일 피처 Acc ≥ 0.99 → 완벽 분리(Data Leakage), ≥ 0.90 → 매우 높은 분류력(누수 의심), ≥ 0.70 → 높은 분류력(추가 검증 필요)

#### 3.5.2 누수 피처 식별 결과

| 피처 | 타겟 클래스 | 관계 | 판정 |
|------|------------|------|------|
| `Days_To_Expiry` ≤ 30일 | Expiring Soon | 329/329건 = 100% 대응 | 🔴 **Data Leakage** |
| `Stock_Gap` > 0 | Low Stock | 238/243건 = 97.9% 대응 | 🔴 **Data Leakage** |

> - `Days_To_Expiry`는 Expiring Soon 레이블의 **정의 그 자체** (유통기한까지 30일 이내)
> - `Stock_Gap = Reorder_Point − Quantity_On_Hand`이 양수이면 Low Stock이 되는 **비즈니스 규칙**
> - 이 피처들을 포함하면 모델이 Acc=1.0을 달성하지만, 이는 예측 능력이 아닌 규칙 암기

#### 3.5.3 Days_of_Inventory 추가 누수 검증

> ⚠️ `Days_of_Inventory = Quantity_On_Hand / Avg_Daily_Sales`는 재고 보유 가능 일수로, Inventory_Status 결정에 간접적으로 관여할 수 있다. 단일 피처 분류력이 높지 않더라도(Acc ≈ 0.50), Feature Importance에서 1위를 차지하므로 추가 검증이 필요하다.

```python
# Days_of_Inventory와 Inventory_Status 간 관계 분석
for status in ['In Stock', 'Expiring Soon', 'Low Stock']:
    subset = df[df['Status_3cls'] == status]
    print(f'{status}: Days_of_Inventory 중앙값={subset["Days_of_Inventory"].median():.1f}, '
          f'범위={subset["Days_of_Inventory"].min():.1f}~{subset["Days_of_Inventory"].max():.1f}')

# Permutation Importance로 실질적 예측 기여도 검증 (섹션 4.7 참조)
```

> - 단일 분류력이 낮으므로 즉시 제거 대상은 아니지만, Permutation Importance 결과와 교차 검증하여 최종 판단
> - 만약 Days_of_Inventory 제거 시 성능이 크게 하락하면 실질적 예측력이 있는 피처
> - 제거해도 성능 변화가 미미하면 다른 피처와의 조합으로 인한 과대 중요도 가능성

#### 3.5.4 Scenario 설계

| 시나리오 | 포함 피처 | 목적 |
|----------|-----------|------|
| **A (Full)** | 전체 14개 수치형 + 범주형 | 비즈니스 규칙 학습 확인 (참고용) |
| **B (Leakage-Free)** | Days_To_Expiry, Stock_Gap 제거 (12개 + 범주형) | **실질적 예측 모델** |

```python
# 누수 피처 제거
leakage_cols = ['Days_To_Expiry', 'Stock_Gap']
num_features_clean = [f for f in num_features_all if f not in leakage_cols]
```

> 이후 모든 모델링은 **Scenario B (Leakage-Free)** 기준으로 진행

---

## 4. 모델링 상세 설계

### 4.1 피처 목록 (Scenario B — 누수 피처 제거 후)

**수치형 피처 (12개):**

- Quantity_On_Hand — 현재 보유 재고 수량
- Reorder_Point — 재주문 기준점
- Safety_Stock — 안전 재고 수준
- Unit_Cost_USD — 제품 단가
- Avg_Daily_Sales — 일일 평균 판매량
- Days_of_Inventory — 재고 보유 가능 일수 ⚠️ (추가 누수 검증 대상, Permutation Importance로 확인)
- Stock_Age_Days — 재고 보유 일수
- Lead_Time_Days — 발주 리드타임
- Quantity_Reserved — 예약된 재고 수량
- Quantity_Committed — 출고 확정 재고 수량
- Days_Since_Last_Order — 최근 발주 후 경과 일수 (파생)
- Available_Stock — 실가용 재고 수량 (파생)

**제거된 누수 피처 (2개):**

- ~~Days_To_Expiry~~ — Expiring Soon 레이블 정의 규칙 (🔴 Data Leakage)
- ~~Stock_Gap~~ — Low Stock 레이블 정의 규칙 (🔴 Data Leakage)

**범주형 피처 (One-Hot 인코딩 후):**

- Category_Beverages, Category_Dairy, Category_Fresh Produce, ... (9개, drop_first 적용 → Bakery baseline)
- ABC_Class_B, ABC_Class_C (2개, drop_first 적용 → A baseline)

### 4.2 타겟 변수 인코딩

```python
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()

# 3클래스 버전 (권장)
y_3cls = le.fit_transform(df['Inventory_Status_3cls'])
# Expiring Soon=0, In Stock=1, Low Stock=2

# 4클래스 버전
y_4cls = le.fit_transform(df['Inventory_Status'])
# Expiring Soon=0, In Stock=1, Low Stock=2, Out of Stock=3
```

### 4.3 Train/Test Split

```python
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

- 비율: 80:20
- `stratify=y`로 클래스 비율 유지
- `random_state=42` 고정

### 4.4 스케일링

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

> Logistic Regression 등 거리 기반 모델을 위해 StandardScaler 적용
> 트리 기반 모델은 스케일링 없이도 사용 가능하지만, 일관성을 위해 동일 데이터 사용

### 4.5 학습할 모델 (4종)

| #   | 모델                     | 라이브러리 | 주요 하이퍼파라미터                                                                                     |
| --- | ------------------------ | ---------- | ------------------------------------------------------------------------------------------------------- |
| 1   | Logistic Regression      | sklearn    | `multi_class='multinomial'`, `max_iter=1000`, `class_weight='balanced'`, `random_state=42`              |
| 2   | Random Forest Classifier | sklearn    | `n_estimators=100`, `class_weight='balanced'`, `random_state=42`                                        |
| 3   | XGBoost Classifier       | xgboost    | `objective='multi:softmax'`, `num_class=3(또는 4)`, `eval_metric='mlogloss'`, `random_state=42`         |
| 4   | LightGBM Classifier      | lightgbm   | `objective='multiclass'`, `num_class=3(또는 4)`, `is_unbalance=True`, `random_state=42`, `verbosity=-1` |

> - 3클래스 버전과 4클래스 버전을 모두 실험하여 비교
> - 초기에는 기본 하이퍼파라미터로 학습 후, 필요 시 GridSearchCV 또는 RandomizedSearchCV로 튜닝

### 4.6 평가 지표

| 지표                      | 설명                         | 선택 이유                         |
| ------------------------- | ---------------------------- | --------------------------------- |
| **Accuracy**              | 전체 정답률                  | 3클래스 통합 시 유효한 기본 지표  |
| **Macro F1-Score**        | 각 클래스 F1의 단순 평균     | 모든 클래스에 동등한 가중치 부여  |
| **Weighted F1-Score**     | 클래스 비율 반영 F1          | 4클래스 불균형 시 보조 지표       |
| **Classification Report** | 클래스별 Precision/Recall/F1 | 클래스별 상세 성능 확인           |
| **Confusion Matrix**      | 예측 vs 실제 교차표          | 어떤 클래스 간 혼동이 있는지 파악 |

### 4.7 과적합 검증 — 교차검증 & Learning Curve

> ⚠️ 데이터가 1,000행 소규모이므로, Train/Test 단일 분할만으로는 과적합 여부를 정확히 판단하기 어렵다. 교차검증과 Learning Curve를 함께 활용한다.

#### 4.7.1 5-Fold Stratified 교차검증

```python
from sklearn.model_selection import StratifiedKFold, cross_validate

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_result = cross_validate(
    model, X_train_scaled, y_train, cv=cv,
    scoring=['accuracy', 'f1_macro'],
    return_train_score=True, n_jobs=-1
)

train_mean = cv_result['train_accuracy'].mean()
val_mean = cv_result['test_accuracy'].mean()
gap = train_mean - val_mean
# Gap > 0.05 → 과적합 의심, Gap > 0.03 → 주의
```

> - Train=1.0인데 Val과의 Gap이 5% 이상이면 **과적합 의심**
> - Gap 3~5%면 **주의** 수준, 하이퍼파라미터 튜닝으로 개선 시도

#### 4.7.2 Learning Curve (학습 곡선)

```python
from sklearn.model_selection import learning_curve

train_sizes, train_scores, val_scores = learning_curve(
    model, X_train_scaled, y_train,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5, scoring='f1_macro', n_jobs=-1
)

# 시각화: x축=학습 데이터 크기, y축=F1 Score
# Train 곡선과 Val 곡선의 수렴/발산 패턴으로 과적합 판단
```

> **해석 가이드:**
> - Train ≈ Val (수렴) → 적합 (Good Fit)
> - Train >> Val (발산, 큰 갭) → 과적합 (Overfitting) → 정규화 강화 또는 데이터 증강 필요
> - Train ≈ Val but 둘 다 낮음 → 과소적합 (Underfitting) → 모델 복잡도 증가 필요
> - 데이터 크기 증가에 따라 Val이 계속 상승 → 더 많은 데이터가 도움이 될 수 있음

### 4.8 피처 기여도 검증 — Permutation Importance

> ⚠️ 트리 기반 모델의 `feature_importances_`는 **불순도 감소(impurity-based)**로 계산되어, 높은 카디널리티 피처나 수치형 피처에 편향될 수 있다. Permutation Importance로 실제 예측 기여도를 교차 검증한다.

```python
from sklearn.inspection import permutation_importance

perm_result = permutation_importance(
    model, X_test_scaled, y_test,
    n_repeats=30, random_state=42, scoring='f1_macro'
)

# 피처별 중요도 및 표준편차
for feat, imp, std in sorted(
    zip(X.columns, perm_result.importances_mean, perm_result.importances_std),
    key=lambda x: x[1], reverse=True
)[:10]:
    print(f'{feat:25s}: {imp:.4f} ± {std:.4f}')
```

> **활용 목적:**
> 1. `feature_importances_`와 비교하여 **Days_of_Inventory**의 실제 기여도 재검증
>    - Permutation Importance도 높으면 → 실질적 예측력이 있는 피처 (유지)
>    - Permutation Importance가 낮으면 → 불순도 기반 과대 평가, 다른 피처와의 상관으로 인한 허상 가능성
> 2. 두 방법 간 순위 불일치가 큰 피처 식별 → 해당 피처의 역할에 대한 도메인 해석 필요
> 3. Permutation Importance ≈ 0인 피처 → 제거 후보 (모델 단순화 가능)

---

## 5. 시각화 및 해석 요구사항

### 5.1 필수 시각화 목록

1. **Inventory_Status 분포 바 차트** (EDA)
   - 4클래스의 불균형 현황 시각화
   - Out of Stock의 극소 비율 강조

2. **수치형 피처별 Inventory_Status 분포 boxplot** (EDA)
   - 주요 피처별(Quantity_On_Hand, Avg_Daily_Sales, Days_of_Inventory, Stock_Age_Days, Days_To_Expiry, Stock_Gap 등) 상태별 분포 비교
   - `boxplot` 또는 `violinplot` 사용

3. **카테고리별 Inventory_Status 분포** (EDA)
   - `countplot` with `hue='Inventory_Status'`
   - 10개 카테고리별 상태 비율 차이 확인

4. **ABC 등급별 Inventory_Status 분포** (EDA)
   - ABC 등급에 따른 상태 분류 패턴 확인

5. **피처 간 상관관계 히트맵** (EDA)
   - `seaborn.heatmap` with `annot=True`
   - 수치형 피처 간 상관 확인

6. **모델별 성능 비교 바 차트**
   - x축: 모델명, y축: Accuracy & Macro F1
   - 4개 모델 비교 (3클래스/4클래스 각각)

7. **Confusion Matrix 히트맵** (최적 모델)
   - `seaborn.heatmap` + `annot=True`
   - 행: 실제(True), 열: 예측(Predicted)
   - 클래스 라벨 표시 (In Stock, Expiring Soon, Low Stock 등)

8. **Feature Importance (트리 기반 모델)**
   - Random Forest / XGBoost / LightGBM의 `feature_importances_` 활용
   - 수평 바 차트, 상위 10~15개 피처
   - 최적 모델 기준으로 1개 이상 생성

9. **Learning Curve (학습 곡선)** — 과적합 검증
   - 4개 모델 각각의 Learning Curve를 2×2 subplot으로 시각화
   - x축: 학습 데이터 크기, y축: F1 Score
   - Train 곡선(파란색)과 Validation 곡선(빨간색) 동시 표시
   - 두 곡선 사이 영역을 `fill_between`으로 표시하면 Gap 직관적 확인 가능

10. **Permutation Importance vs Feature Importance 비교**
    - 최적 모델 기준으로 두 방법의 상위 10개 피처를 나란히 비교
    - 순위 불일치가 큰 피처 하이라이트
    - Days_of_Inventory의 두 방법 간 순위 차이 확인

11. **Default vs Tuned 성능 비교 차트**
    - 모델별 Default/Tuned의 Train Acc, Test Acc, Gap을 그룹 바 차트로 비교
    - 과적합 개선 정도를 시각적으로 확인

12. **데이터 누수 진단 시각화**
    - Days_To_Expiry, Stock_Gap의 상태별 분포 boxplot
    - 누수 피처가 타겟을 거의 완벽하게 분리하는 모습을 시각적으로 확인

### 5.2 선택 시각화 (추가 분석)

- SHAP Summary Plot (XGBoost 또는 LightGBM 모델 기준)
- ROC Curve (One-vs-Rest 방식)
- 3클래스 vs 4클래스 성능 비교 차트

---

## 6. 코드 구조 및 출력 형식

### 6.1 Jupyter Notebook 구조

```
01_Inventory_Status_Classification.ipynb
│
├── 0. 라이브러리 임포트 & 설정
│   ├── 필수 라이브러리 import
│   ├── 시각화 한글 폰트 설정 (matplotlib)
│   └── 경고 메시지 숨김, 시드 고정
│
├── 1. 데이터 로드 & 기본 확인
│   ├── CSV 로드 (Inventory Management E-Grocery - InventoryData.csv)
│   ├── df.shape, df.info(), df.describe()
│   ├── 결측치 확인
│   ├── Inventory_Status 클래스 분포 확인
│   └── ABC_Class 분포 확인
│
├── 2. 데이터 전처리
│   ├── 인도네시아 로케일 숫자 변환 (쉼표 → 마침표)
│   ├── 금액 컬럼 변환 ($, 천단위 구분)
│   ├── 퍼센트 컬럼 변환 (% 제거)
│   ├── 날짜 컬럼 파싱
│   ├── 파생변수 생성 (Days_To_Expiry, Days_Since_Last_Order, Stock_Gap, Available_Stock)
│   └── 클래스 불균형 처리 (Out of Stock → Low Stock 병합, 3클래스)
│
├── 3. EDA (탐색적 데이터 분석)
│   ├── 타겟 변수 분포 시각화 (4클래스 불균형 확인)
│   ├── 수치형 피처별 Inventory_Status 분포 (boxplot)
│   ├── 카테고리별 Inventory_Status 분포 (countplot)
│   ├── ABC 등급별 Inventory_Status 분포
│   └── 피처 간 상관관계 히트맵
│
├── 4. 데이터 누수(Data Leakage) 진단          ★ 추가
│   ├── 4.1 단일 피처 분류력 진단 (DecisionTree, max_depth=3)
│   ├── 4.2 Days_To_Expiry ↔ Expiring Soon 관계 분석
│   ├── 4.3 Stock_Gap ↔ Low Stock 관계 분석
│   ├── 4.4 Days_of_Inventory 추가 누수 검증    ★ 추가
│   ├── 4.5 누수 진단 시각화
│   └── 4.6 Scenario A/B 설계 및 누수 피처 제거
│
├── 5. 피처/타겟 분리 & Train/Test Split (Scenario B)
│   ├── 피처 선택 (누수 피처 제거)
│   ├── One-Hot 인코딩 (Category, ABC_Class)
│   ├── 타겟 인코딩 (LabelEncoder)
│   ├── train_test_split (80:20, stratify)
│   └── StandardScaler 적용
│
├── 6. 모델 학습 & 평가 (Default 하이퍼파라미터)
│   ├── 6.1 Logistic Regression
│   ├── 6.2 Random Forest
│   ├── 6.3 XGBoost
│   ├── 6.4 LightGBM
│   └── 6.5 모델 성능 비교 종합표 & 바 차트
│
├── 7. 과적합 검증                              ★ 추가
│   ├── 7.1 5-Fold Stratified 교차검증
│   │   └── Train/Val Gap 기반 과적합 판정
│   └── 7.2 Learning Curve (학습 곡선) 시각화    ★ 추가
│       └── 4개 모델 2×2 subplot
│
├── 8. 하이퍼파라미터 튜닝 (과적합 방지)
│   ├── 8.1 Logistic Regression (C=0.1)
│   ├── 8.2 Random Forest (max_depth, min_samples_leaf 제한)
│   ├── 8.3 XGBoost (max_depth, reg_alpha/lambda, subsample)
│   ├── 8.4 LightGBM (num_leaves, min_child_samples)
│   └── 8.5 Default vs Tuned 비교표 & 시각화
│
├── 9. 최적 모델 심층 분석
│   ├── 9.1 Confusion Matrix 히트맵
│   ├── 9.2 Classification Report 출력
│   ├── 9.3 Feature Importance (Impurity-based)
│   ├── 9.4 Permutation Importance                ★ 추가
│   │   └── Feature Importance와 비교 분석
│   │   └── Days_of_Inventory 실질 기여도 검증
│   ├── 9.5 전체 모델 Confusion Matrix 비교
│   └── (선택) SHAP 분석
│
├── 10. 모델 저장
│   └── 최적 모델, Scaler, LabelEncoder 저장 (joblib)
│
└── 11. 결론 및 인사이트
    ├── 데이터 누수 발견 및 대응 정리
    ├── 최적 모델 성능 요약
    ├── Feature Importance vs Permutation Importance 비교 결론
    ├── 과적합 검증 결과 (CV Gap, Learning Curve 기반)
    ├── 핵심 인사이트 3~5개
    ├── 한계점 및 개선 방향
    └── 다른 소주제와의 연결점
```

### 6.2 코딩 컨벤션

- **언어:** Python 3.10+
- **필수 라이브러리:**
  ```
  pandas, numpy, matplotlib, seaborn,
  scikit-learn, xgboost, lightgbm, shap (선택)
  ```
- **한글 폰트 설정:** macOS 환경 (`AppleGothic`) 또는 `NanumGothic` 사용
  ```python
  import matplotlib.pyplot as plt
  plt.rcParams['font.family'] = 'AppleGothic'  # macOS
  plt.rcParams['axes.unicode_minus'] = False
  ```
- **시드 고정:** 모든 모델에 `random_state=42`
- **셀 출력:** 각 단계마다 중간 결과를 `print()` 또는 `display()`로 확인
- **마크다운 셀:** 각 섹션마다 설명 마크다운 포함 (한국어)
- **그래프 제목/라벨:** 한국어 사용 권장 (한글 폰트 설정 전제)
- **그래프 저장:** 주요 시각화는 `plt.savefig('outputs/figures/파일명.png', dpi=150, bbox_inches='tight')` 로 저장

### 6.3 모델 성능 결과 테이블 출력 형식

```python
import pandas as pd

results = pd.DataFrame({
    '모델': ['Logistic Regression', 'Random Forest', 'XGBoost', 'LightGBM'],
    'Accuracy': [lr_acc, rf_acc, xgb_acc, lgb_acc],
    'Macro F1': [lr_f1, rf_f1, xgb_f1, lgb_f1]
})
results = results.sort_values('Macro F1', ascending=False)
display(results)
```

---

## 7. 핵심 유의사항

### 7.1 데이터 관련

- **인도네시아 로케일 형식:** 쉼표(`,`)가 소수점으로 사용되므로 반드시 전처리 필요
- **금액 컬럼 복합 형식:** `$2.084,25` → `$`·`.`(천단위) 제거, `,` → `.` 변환
- **퍼센트 컬럼:** `%` 기호 제거 + 쉼표→마침표 변환
- **클래스 불균형:** Out of Stock 2건(0.2%) — 3클래스 통합이 현실적 방안
- 데이터가 1,000행으로 **소규모**이므로 과적합에 주의
- Notes 컬럼 결측치 834건은 분석 미사용 → 실질적 결측치 이슈 없음

### 7.2 모델링 관련

- **3클래스 통합 시** (In Stock / Expiring Soon / Low Stock): 비교적 균형적이므로 class_weight 조정 선택적
- **4클래스 유지 시:** 반드시 `class_weight='balanced'` 또는 SMOTE 적용
- Logistic Regression은 **스케일링 필수**, 트리 기반은 선택적
- 모델 비교 시 **동일한 train/test 분할** 사용 (random_state=42 고정)
- stratify 시 Out of Stock 2건만 있으면 test set에 0건이 될 수 있으므로, 3클래스 통합이 안정적
- **데이터 누수 진단은 모델 학습 전에 반드시 수행** — 누수 피처(Days_To_Expiry, Stock_Gap)를 포함하면 모델이 비즈니스 규칙을 암기하여 Acc=1.0이 나오지만, 이는 예측 능력이 아님
- **과적합 검증은 3단계로 수행:** ① Train/Test Gap 확인 → ② 5-Fold CV Gap 확인 → ③ Learning Curve 시각화

### 7.3 해석 관련

- 단순 성능 비교에 그치지 말고, **Feature Importance 또는 SHAP**을 통해 비즈니스 인사이트 도출
- **Feature Importance는 반드시 Permutation Importance와 교차 검증** — Impurity-based 방법만 사용하면 연속형 피처가 과대 평가될 수 있음
- Confusion Matrix에서 **어떤 클래스 간 혼동이 심한지** 반드시 분석하고 이유 추론
- 예: Expiring Soon과 In Stock이 혼동된다면 → Stock_Age_Days 등 시간 관련 피처의 영향력 확인
- ABC 등급별로 분류 패턴이 달라지는지 분석 → 등급별 차별화된 관리 전략 제안
- 성능이 98~99%로 매우 높게 나오면, **남아있는 피처 중 간접 누수 가능성**도 점검 (Days_of_Inventory 등)
- 성능이 낮게 나올 경우, "Inventory_Status가 제품 내재적 속성 외에 경영 판단·시장 변화 등 외부 요인에 의해 결정된다"는 인사이트로 해석

### 7.4 다른 소주제와의 연결

- 소주제 1에서 파악한 **Expiring Soon 제품의 특성** → 소주제 3에서 폐기 위험과의 연관성 검증에 활용
- **Low Stock 제품의 특성** → 소주제 4에서 발주 전략 수립 시 참고
- Feature Importance 결과 → 소주제 2(판매량 예측)·소주제 4(클러스터링) 피처 선정에 참고 가능
- 소주제 1의 결과를 README.md 3.1절의 결과 테이블에 기입

---

## 8. 기대 산출물 체크리스트

- [ ] `01_Inventory_Status_Classification.ipynb` — 전체 분석 노트북
- [ ] `outputs/figures/eda_status_distribution.png` — Inventory_Status 분포 시각화
- [ ] `outputs/figures/eda_feature_boxplots.png` — 주요 피처별 상태 분포
- [ ] `outputs/figures/eda_category_status.png` — 카테고리별 상태 분포
- [ ] `outputs/figures/eda_correlation_heatmap_s1.png` — 상관관계 히트맵
- [ ] `outputs/figures/leakage_diagnosis.png` — 데이터 누수 진단 시각화
- [ ] `outputs/figures/confusion_matrix.png` — 최적 모델 Confusion Matrix
- [ ] `outputs/figures/model_comparison.png` — 모델 성능 비교 차트
- [ ] `outputs/figures/model_comparison_default_vs_tuned.png` — Default vs Tuned 비교 차트
- [ ] `outputs/figures/feature_importance.png` — Feature Importance 차트 (Impurity-based)
- [ ] `outputs/figures/permutation_importance.png` — Permutation Importance 차트
- [ ] `outputs/figures/learning_curve.png` — Learning Curve (4개 모델)
- [ ] `outputs/models/best_classification_model.pkl` — 최적 모델 저장 (joblib)
- [ ] `outputs/models/scaler_classification.pkl` — StandardScaler 저장
- [ ] `outputs/models/label_encoder.pkl` — LabelEncoder 저장
- [ ] 모델 성능 결과 요약 (Accuracy, Macro F1, Train/Test Gap)
- [ ] 데이터 누수 진단 결과 정리
- [ ] Feature Importance vs Permutation Importance 비교 결론
- [ ] 과적합 검증 결과 (CV Gap, Learning Curve 기반 판정)
- [ ] 핵심 인사이트 3~5개 정리

---

## 부록: 전체 파이프라인 요약 흐름도

```
CSV 로드 (1,000행 × 37열)
  ↓
공통 전처리
  ├── 인도네시아 로케일 숫자 변환 (쉼표 → 마침표)
  ├── 금액 컬럼 변환 ($, 천단위, 쉼표 소수점)
  ├── 퍼센트 컬럼 변환 (% 제거)
  └── 날짜 컬럼 파싱 (4개 컬럼)
  ↓
파생변수 생성 (Days_To_Expiry, Days_Since_Last_Order, Stock_Gap, Available_Stock)
  ↓
클래스 불균형 처리 (Out of Stock → Low Stock 병합, 3클래스)
  ↓
EDA (타겟 분포, 피처별 분포, 카테고리·ABC별 분포, 상관관계)
  ↓
★ 데이터 누수 진단 (Days_To_Expiry, Stock_Gap → 누수 확인 및 제거)
  ├── 단일 피처 분류력 진단 (DecisionTree, max_depth=3)
  ├── Days_of_Inventory 추가 누수 검증
  └── Scenario A(Full) / B(Leakage-Free) 설계
  ↓
피처 선택 (Scenario B: 누수 피처 제거) & One-Hot 인코딩
  ↓
타겟 인코딩 (LabelEncoder) → Train/Test Split → StandardScaler
  ↓
4개 모델 학습 — Default 하이퍼파라미터 (LR, RF, XGB, LGBM)
  ↓
★ 과적합 검증
  ├── 5-Fold Stratified 교차검증 (Train/Val Gap 확인)
  └── Learning Curve 시각화 (4개 모델)
  ↓
하이퍼파라미터 튜닝 (과적합 방지)
  └── Default vs Tuned 성능 비교
  ↓
최적 모델 심층 분석
  ├── Confusion Matrix & Classification Report
  ├── Feature Importance (Impurity-based)
  └── ★ Permutation Importance (실질적 기여도 검증)
  ↓
인사이트 도출 & 결론
```
