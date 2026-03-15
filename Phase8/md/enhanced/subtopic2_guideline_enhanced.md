# 소주제 2 — 일일 판매량 예측 (Regression) 구현 가이드 [보강 데이터 통합 버전]

> **[v2.0]** 원본 데이터의 한계를 보완하기 위해 3종의 Kaggle 보강 데이터를 통합한 확장 버전입니다.

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열) + 보강 데이터 3종
- 소주제 2 담당: 이현아

### 1.2 소주제 2 목표

제품 속성과 재고 정보를 기반으로 **Avg_Daily_Sales(일일 평균 판매량)**를 예측하는 **회귀 모델**을 구축하고, 판매량에 가장 큰 영향을 미치는 요인을 SHAP 등으로 해석한다.

### 1.3 보강 데이터 도입 배경

원본 데이터만으로는 판매량을 결정하는 **매장 특성(규모, 도시 유형), 진열 전략(Visibility), 가격 정책(MRP, 할인율), 시계열 패턴(일별/월별 추이)** 등이 부재하여 R² Score에 한계가 존재한다. 이를 보완하기 위해 3종의 외부 데이터를 도입한다.

| 보강 목적 | 한계점 | 보강 데이터 |
|-----------|--------|------------|
| 매장·제품 속성 관점 추가 | 매장 규모, 도시 유형, 진열 비율 등 부재 | ① BigMart Sales Data |
| 시계열·계절성·할인 분석 프레임워크 | 일별 판매 추이, 할인 효과 데이터 부재 | ② Supermarket Sales Data |
| 할인·이익률 관점 추가 | 할인율, 이익(Profit) 정보 부재 | ③ Supermart Grocery Sales |

### 1.4 도출할 인사이트 (확장)

**[기존]**
- 판매량에 가장 큰 영향을 미치는 변수는 무엇인가?
- R²가 낮다면 외부 변수 부재 때문인가?

**[보강 데이터 추가]**
- BigMart 참고 파생변수(매장 규모 대리, 진열 비율 대리)가 예측력을 향상시키는가?
- Supermarket Sales Data의 시계열·할인 패턴 파생변수의 기여도는 어느 정도인가?
- 보강 전후 R² 비교를 통해, Avg_Daily_Sales에 매장/마케팅 요인이 얼마나 기여하는지 정량화

---

## 2. 데이터 명세

### 2.1 원본 데이터 (메인)

- **파일:** `Inventory_Management_E-Grocery_-_InventoryData.csv`
- **출처:** [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/)
- **규모:** 1,000행 × 37열
- **타겟:** Avg_Daily_Sales (연속형, 원본은 쉼표 소수점 문자열 → float 변환 필요)

---

### 2.2 보강 데이터 ① — BigMart Sales Data

| 항목 | 내용 |
|------|------|
| **파일 경로** | `data/etc_subtopic2/BigMart Sales Data/Train.csv`, `Test.csv` |
| **출처** | [Kaggle - BigMart Sales Data](https://www.kaggle.com/datasets/brijbhushannanda1979/bigmart-sales-data) |
| **규모** | Train: 8,523행 × 12열 |
| **설명** | 1,559개 제품 × 10개 매장의 판매 데이터, 매장 규모·도시 유형·진열 비율 포함 |

#### 왜 추가해야 하는가?

원본 데이터에는 **매장 특성(크기, 위치, 유형)**과 **제품 진열 비율(Visibility)** 이 전혀 없다. BigMart 데이터는 판매량 예측 벤치마크로 가장 널리 사용되는 데이터셋으로, "어떤 매장·제품 속성이 판매에 영향을 주는가"에 대한 피처 설계 프레임워크를 제공한다.

#### 주요 컬럼 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | Item_Identifier | object | 제품 ID | ❌ 식별용 |
| 2 | **Item_Weight** | float | 제품 무게 | ✅ **피처 설계 참고** — 카테고리별 대리 변수 |
| 3 | **Item_Fat_Content** | object | 저지방/일반 (Low Fat, Regular) | ✅ 카테고리 세분화 참고 |
| 4 | **Item_Visibility** | float | 매장 내 진열 비율 (%) | ✅ **핵심 — 진열 비율 대리 변수 설계** |
| 5 | **Item_Type** | object | 제품 유형 (16종) | ✅ Category 매핑 참고 |
| 6 | **Item_MRP** | float | 최대 소매 가격 | ✅ **핵심 — 가격 전략 변수 설계** |
| 7 | Outlet_Identifier | object | 매장 ID | ❌ 식별용 |
| 8 | **Outlet_Establishment_Year** | int | 매장 설립 연도 | ✅ 매장 성숙도 변수 참고 |
| 9 | **Outlet_Size** | object | 매장 규모 (Small/Medium/High) | ✅ **핵심 — 매장 규모 대리 변수** |
| 10 | **Outlet_Location_Type** | object | 도시 유형 (Tier 1/2/3) | ✅ **핵심 — 위치 기반 변수** |
| 11 | **Outlet_Type** | object | 매장 유형 (Grocery/Supermarket 등) | ✅ 매장 유형 변수 참고 |
| 12 | **Item_Outlet_Sales** | float | 판매량 (타겟) | ✅ 참조 타겟 — 비교 분석용 |

#### 활용 방식: 피처 설계 프레임워크 + 독립 비교 분석

> BigMart의 핵심 변수 구조를 참고하여 원본에서 유사 파생변수를 설계하고, BigMart 자체 분석 결과를 비교 인사이트로 활용한다.

---

### 2.3 보강 데이터 ② — Supermarket Sales Data (중국 슈퍼마켓 거래 데이터)

| 항목 | 내용 |
|------|------|
| **파일 경로** | `data/etc_subtopic2/Supermarket Sales Data/annex1.csv` ~ `annex4.csv` |
| **출처** | [Kaggle - Supermarket Sales Data](https://www.kaggle.com/) |
| **규모** | annex1: 251행 (품목 마스터), annex2: 878,503행 (거래 내역), annex3: 55,982행 (도매가), annex4: 251행 (손실률) |
| **설명** | 중국 슈퍼마켓의 일별 거래 데이터로, 판매량·가격·할인·반품 정보를 포함하는 대규모 실거래 데이터 |

#### 파일별 구조

**annex1.csv — 품목 마스터 (251행 × 4열)**

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 1 | Item Code | object | 품목 코드 |
| 2 | Item Name | object | 품목명 |
| 3 | Category Code | object | 카테고리 코드 |
| 4 | Category Name | object | 카테고리명 |

**annex2.csv — 일별 거래 내역 (878,503행 × 7열)**

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | **Date** | date | 거래 일자 | ✅ **시간 피처 설계 기준** |
| 2 | Time | time | 거래 시각 | ✅ 시간대별 판매 패턴 |
| 3 | **Item Code** | object | 품목 코드 | ✅ 품목 마스터(annex1) 조인 키 |
| 4 | **Quantity Sold (kilo)** | float | 판매량 (kg) | ✅ **핵심 — 일별 판매량 패턴 학습** |
| 5 | **Unit Selling Price (RMB/kg)** | float | 판매 단가 (위안/kg) | ✅ 가격 피처 참고 |
| 6 | **Sale or Return** | object | 판매/반품 여부 | ✅ 반품률 분석 |
| 7 | **Discount (Yes/No)** | object | 할인 적용 여부 | ✅ **핵심 — 할인 효과 분석** |

**annex3.csv — 도매가 (55,982행 × 3열)**

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 1 | Date | date | 일자 |
| 2 | Item Code | object | 품목 코드 |
| 3 | Wholesale Price (RMB/kg) | float | 도매 가격 |

**annex4.csv — 손실률 (251행 × 2열)**

| # | 컬럼명 | 타입 | 설명 |
|---|--------|------|------|
| 1 | Item Code | object | 품목 코드 |
| 2 | Loss Rate (%) | float | 폐기/손실률 |

#### 왜 추가해야 하는가?

원본 데이터에서 시간 정보는 Received_Date 단일 컬럼뿐이고, **일별 판매 추이, 계절성, 할인 효과, 반품 패턴**을 반영할 수 없다. 이 데이터셋은 약 87만 건의 실거래 데이터를 포함하여 **시간 기반 피처 엔지니어링 기법(월별 패턴, 요일별 패턴, 할인 효과)**을 학습하고 원본 데이터에 적용하는 근거를 제공한다.

#### 활용 방식: 시계열·할인 피처 엔지니어링 기법 학습 + 원본 적용

> Supermarket Sales Data의 시계열 및 할인 패턴을 분석한 뒤, 원본 데이터의 날짜 변수에서 가능한 범위 내에서 적용한다.

---

### 2.4 보강 데이터 ③ — Supermart Grocery Sales

| 항목 | 내용 |
|------|------|
| **파일 경로** | `data/etc_subtopic2/Supermart Grocery Sales - Retail Analytics Dataset.csv` |
| **출처** | [Kaggle - Supermart Grocery Sales](https://www.kaggle.com/datasets/mohamedharris/supermart-grocery-sales-retail-analytics-dataset) |
| **규모** | 약 9,994행 × 11열 |
| **설명** | 인도 식료품 매장 판매 데이터, 지역·할인율·이익(Profit) 포함 |

#### 왜 추가해야 하는가?

원본 데이터에는 **할인(Discount), 이익(Profit), 지역(Region)** 정보가 없다. "가격 대비 판매량" 분석에서 할인 효과를 논의하려면 할인율 변수의 구조와 영향을 이해해야 한다.

#### 주요 컬럼 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | **Sub Category** | object | 세부 카테고리 | ✅ Category 세분화 참고 |
| 2 | **Category** | object | 대분류 카테고리 | ✅ 카테고리 매핑 참고 |
| 3 | **Sales** | float | 판매액 | ✅ 비교 타겟 |
| 4 | **Discount** | float | 할인율 (%) | ✅ **핵심 — 할인 효과 변수 설계** |
| 5 | **Profit** | float | 이익 | ✅ **핵심 — 수익성 변수 설계** |
| 6 | **Region** | object | 지역 | ✅ 지역 효과 참고 |

#### 활용 방식: 할인·수익성 관련 파생변수 설계 근거 + 비교 분석

---

## 3. 보강 데이터 통합 전략

### 3.1 통합 방식 개요

```
┌──────────────────────────────────────────────────────────────────┐
│                    보강 데이터 통합 3가지 방식                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  방식 A: 피처 설계 프레임워크 (Feature Design Framework)            │
│  → BigMart의 변수 구조를 참고하여 원본에서 유사 파생변수 생성          │
│  → 주 활용: ① BigMart Sales Data                                 │
│                                                                  │
│  방식 B: 시계열·할인 기법 학습 & 적용 (Time Feature Engineering)    │
│  → Supermarket Sales Data의 시계열·할인 분석 기법을 학습하여 적용     │
│  → 주 활용: ② Supermarket Sales Data                             │
│                                                                  │
│  방식 C: 카테고리별 통계 매핑 + 독립 비교 분석                       │
│  → Supermart의 할인율·이익률 통계를 카테고리에 시뮬레이션 매핑         │
│  → 주 활용: ③ Supermart Grocery Sales                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 방식 A — 피처 설계 프레임워크 (① BigMart 활용)

BigMart의 핵심 변수 구조를 참고하여 원본 데이터에서 **5개 파생변수**를 설계한다.

| 파생변수명 | 설계 근거 (BigMart 참고 변수) | 원본 활용 컬럼 | 계산식 |
|-----------|-------------------------------|---------------|--------|
| **Price_Per_Category_Rank** | `Item_MRP`의 카테고리 내 순위 | Unit_Cost_USD, Category | 카테고리 내 가격 백분위 순위 |
| **Visibility_Proxy** | `Item_Visibility` | Avg_Daily_Sales, Category | 카테고리 내 판매 비중 (= 진열 비율 대리) |
| **Price_Sensitivity** | `Item_MRP / Item_Outlet_Sales` | Unit_Cost_USD, Avg_Daily_Sales | `Unit_Cost_USD / Avg_Daily_Sales` |
| **Category_Sales_Mean** | `Item_Type`별 평균 매출 | Category, Avg_Daily_Sales | 카테고리 평균 판매량 (Target Encoding 유사) |
| **Stock_Turnover_Efficiency** | `Outlet_Size` 효과 | Quantity_On_Hand, Days_of_Inventory | `Days_of_Inventory / Quantity_On_Hand` (낮을수록 빠른 소진) |

```python
# 방식 A: BigMart 참고 파생변수

# 1. Price_Per_Category_Rank: 카테고리 내 가격 순위 (백분위)
df['Price_Per_Category_Rank'] = df.groupby('Category')['Unit_Cost_USD'].rank(pct=True)

# 2. Visibility_Proxy: 카테고리 내 판매 비중 (진열 비율 대리)
category_total_sales = df.groupby('Category')['Avg_Daily_Sales'].transform('sum')
df['Visibility_Proxy'] = df['Avg_Daily_Sales'] / category_total_sales

# 3. Price_Sensitivity: 단가 대비 판매량 비율 (가격 민감도)
df['Price_Sensitivity'] = df['Unit_Cost_USD'] / df['Avg_Daily_Sales'].replace(0, 1)

# 4. Category_Sales_Mean: 카테고리 평균 판매량 (주의: Data Leakage 가능성)
# → Train 데이터에서만 계산하여 적용해야 함 (아래 모델링 섹션에서 처리)

# 5. Stock_Turnover_Efficiency: 재고 대비 소진 효율
df['Stock_Turnover_Efficiency'] = (
    df['Days_of_Inventory'] / df['Quantity_On_Hand'].replace(0, 1)
)
```

> ⚠️ **Data Leakage 주의:** `Category_Sales_Mean`과 `Visibility_Proxy`는 타겟(Avg_Daily_Sales)의 정보를 포함하므로, 반드시 Train 데이터에서만 계산하여 Test에 매핑해야 한다. 노트북에서 이 처리를 명시적으로 문서화할 것.

### 3.3 방식 B — 시계열·할인 피처 엔지니어링 (② Supermarket Sales Data 활용)

Supermarket Sales Data의 시계열 및 할인 패턴을 학습한 후, 원본의 Received_Date에서 가능한 범위 내에서 적용한다.

#### Step 1: Supermarket Sales Data 시계열·할인 패턴 학습 (별도 셀)

```python
# Supermarket Sales Data 탐색
df_annex1 = pd.read_csv('data/etc_subtopic2/Supermarket Sales Data/annex1.csv')
df_annex2 = pd.read_csv('data/etc_subtopic2/Supermarket Sales Data/annex2.csv',
                          parse_dates=['Date'])

# annex1과 annex2 조인 (카테고리 정보 결합)
df_super = df_annex2.merge(df_annex1, on='Item Code', how='left')

# 월별 판매량 패턴
monthly = df_super.groupby(df_super['Date'].dt.month)['Quantity Sold (kilo)'].mean()
print("월별 평균 판매량 패턴:")
print(monthly)

# 요일별 판매량 패턴
daily = df_super.groupby(df_super['Date'].dt.dayofweek)['Quantity Sold (kilo)'].mean()
print("\n요일별 평균 판매량 패턴:")
print(daily)

# 할인 효과 분석
discount_effect = df_super.groupby('Discount (Yes/No)')['Quantity Sold (kilo)'].mean()
print("\n할인 유무별 평균 판매량:")
print(discount_effect)

# 반품률 분석
return_rate = (df_super['Sale or Return'] == 'return').mean()
print(f"\n반품률: {return_rate:.2%}")

# 카테고리별 할인 적용 비율
cat_discount = df_super.groupby('Category Name')['Discount (Yes/No)'].apply(
    lambda x: (x == 'Yes').mean()
)
print("\n카테고리별 할인 적용 비율:")
print(cat_discount)
```

#### Step 2: 원본 데이터에 시간 파생변수 적용

```python
# 방식 B: Supermarket Sales Data 참고 시간 파생변수

# 1. Received_Month: 입고 월 (계절성)
df['Received_Month'] = df['Received_Date'].dt.month

# 2. Received_Quarter: 입고 분기
df['Received_Quarter'] = df['Received_Date'].dt.quarter

# 3. Is_Peak_Season: 성수기 여부 (Supermarket Sales Data에서 확인된 패턴 기반)
# → 실제 패턴 확인 후 성수기 월 조정 가능
df['Is_Peak_Season'] = df['Received_Month'].isin([11, 12, 1]).astype(int)

# 4. Days_Since_Last_Order: 최근 발주 후 경과일 (공급 빈도 대리)
df['Days_Since_Last_Order'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days
```

### 3.4 방식 C — 카테고리별 통계 매핑 (③ Supermart 활용)

#### Step 1: Supermart 할인·이익 통계 분석

```python
df_sm = pd.read_csv(
    'data/etc_subtopic2/Supermart Grocery Sales - Retail Analytics Dataset.csv'
)

# 서브카테고리별 평균 할인율·이익률
sm_stats = df_sm.groupby('Sub Category').agg({
    'Discount': 'mean',
    'Profit': 'mean',
    'Sales': 'mean'
}).round(2)
sm_stats['Profit_Margin'] = (sm_stats['Profit'] / sm_stats['Sales'] * 100).round(1)
print("Supermart 서브카테고리별 통계:")
print(sm_stats)
```

#### Step 2: 원본 카테고리에 시뮬레이션 매핑

```python
# Supermart + Supermarket Sales Data 분석 결과를 기반으로
# 원본 10개 카테고리별 추정 할인율·이익률 매핑
category_discount_mapping = {
    'Pantry':         {'est_discount': 0.08, 'est_profit_margin': 0.28},
    'Personal Care':  {'est_discount': 0.12, 'est_profit_margin': 0.35},
    'Beverages':      {'est_discount': 0.12, 'est_profit_margin': 0.32},
    'Fresh Produce':  {'est_discount': 0.15, 'est_profit_margin': 0.25},
    'Household':      {'est_discount': 0.10, 'est_profit_margin': 0.30},
    'Dairy':          {'est_discount': 0.10, 'est_profit_margin': 0.30},
    'Meat':           {'est_discount': 0.05, 'est_profit_margin': 0.28},
    'Frozen':         {'est_discount': 0.08, 'est_profit_margin': 0.26},
    'Bakery':         {'est_discount': 0.20, 'est_profit_margin': 0.20},
    'Seafood':        {'est_discount': 0.05, 'est_profit_margin': 0.35},
}

for col, key in [('Est_Discount', 'est_discount'),
                 ('Est_Profit_Margin', 'est_profit_margin')]:
    df[col] = df['Category'].map(
        {cat: vals[key] for cat, vals in category_discount_mapping.items()}
    )

# 복합 파생변수: 할인 적용 추정 가격
df['Discounted_Price_Est'] = df['Unit_Cost_USD'] * (1 - df['Est_Discount'])

# 복합 파생변수: 추정 이익
df['Est_Profit_Per_Unit'] = df['Unit_Cost_USD'] * df['Est_Profit_Margin']
```

---

## 4. 전처리 파이프라인 (보강 버전)

### 4.1 공통 전처리

```python
import pandas as pd
import numpy as np

# 0. 데이터 로드
df = pd.read_csv('Inventory_Management_E-Grocery_-_InventoryData.csv')

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

### 4.2 기본 파생변수

```python
df['Received_Month'] = df['Received_Date'].dt.month
```

### 4.3 보강 파생변수

```python
# ── 방식 A: BigMart 참고 (5개) ──
df['Price_Per_Category_Rank'] = df.groupby('Category')['Unit_Cost_USD'].rank(pct=True)
category_total_sales = df.groupby('Category')['Avg_Daily_Sales'].transform('sum')
df['Visibility_Proxy'] = df['Avg_Daily_Sales'] / category_total_sales
df['Price_Sensitivity'] = df['Unit_Cost_USD'] / df['Avg_Daily_Sales'].replace(0, 1)
df['Stock_Turnover_Efficiency'] = df['Days_of_Inventory'] / df['Quantity_On_Hand'].replace(0, 1)
# Category_Sales_Mean → Train에서만 계산 (STEP 5에서 처리)

# ── 방식 B: Supermarket Sales Data 참고 (4개) ──
df['Received_Quarter'] = df['Received_Date'].dt.quarter
df['Is_Peak_Season'] = df['Received_Month'].isin([11, 12, 1]).astype(int)
df['Days_Since_Last_Order'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days

# ── 방식 C: Supermart 참고 (4개) ──
category_discount_mapping = {
    'Pantry':         {'est_discount': 0.08, 'est_profit_margin': 0.28},
    'Personal Care':  {'est_discount': 0.12, 'est_profit_margin': 0.35},
    'Beverages':      {'est_discount': 0.12, 'est_profit_margin': 0.32},
    'Fresh Produce':  {'est_discount': 0.15, 'est_profit_margin': 0.25},
    'Household':      {'est_discount': 0.10, 'est_profit_margin': 0.30},
    'Dairy':          {'est_discount': 0.10, 'est_profit_margin': 0.30},
    'Meat':           {'est_discount': 0.05, 'est_profit_margin': 0.28},
    'Frozen':         {'est_discount': 0.08, 'est_profit_margin': 0.26},
    'Bakery':         {'est_discount': 0.20, 'est_profit_margin': 0.20},
    'Seafood':        {'est_discount': 0.05, 'est_profit_margin': 0.35},
}
for col, key in [('Est_Discount', 'est_discount'), ('Est_Profit_Margin', 'est_profit_margin')]:
    df[col] = df['Category'].map({c: v[key] for c, v in category_discount_mapping.items()})
df['Discounted_Price_Est'] = df['Unit_Cost_USD'] * (1 - df['Est_Discount'])
df['Est_Profit_Per_Unit'] = df['Unit_Cost_USD'] * df['Est_Profit_Margin']
```

### 4.4 카테고리 & ABC 등급 인코딩

```python
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

---

## 5. 모델링 상세 설계 (보강 버전)

### 5.1 피처 목록 — 2단계 비교 설계

#### Baseline 피처셋 (원본만)

```python
baseline_features = [
    'Unit_Cost_USD', 'Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock',
    'Days_of_Inventory', 'Lead_Time_Days', 'Stock_Age_Days',
    'Order_Frequency_per_month', 'Received_Month',
    # + Category One-Hot (9개) + ABC_Class One-Hot (2개)
]
# 총: 9(수치) + 9(카테고리) + 2(ABC) = 20개
```

#### Enhanced 피처셋 (원본 + 보강, 최대 33개)

```python
enhanced_features = baseline_features + [
    # 방식 A: BigMart 참고 (4개, Category_Sales_Mean은 별도 처리)
    'Price_Per_Category_Rank', 'Visibility_Proxy',
    'Price_Sensitivity', 'Stock_Turnover_Efficiency',
    # 방식 B: Supermarket Sales Data 참고 (3개)
    'Received_Quarter', 'Is_Peak_Season', 'Days_Since_Last_Order',
    # 방식 C: Supermart 참고 (4개)
    'Est_Discount', 'Est_Profit_Margin',
    'Discounted_Price_Est', 'Est_Profit_Per_Unit',
]
# 총: 20(기본) + 11(보강) + 2(카테고리/ABC) = 최대 33개
```

> ⚠️ `Visibility_Proxy`와 `Price_Sensitivity`는 Avg_Daily_Sales 정보를 포함하므로 **Data Leakage 주의**. 필요 시 Train에서만 계산하여 적용하거나, 이 변수 제외 후 비교 실험도 수행.

### 5.2 학습 모델 (5종 × 2셋 = 10회)

| # | 모델 | 비고 |
|---|------|------|
| 1 | Linear Regression | Baseline |
| 2 | Ridge Regression | L2 정규화 |
| 3 | Lasso Regression | L1 정규화 + 피처 선택 |
| 4 | Random Forest Regressor | 앙상블(배깅) |
| 5 | XGBoost Regressor | 앙상블(부스팅) |

### 5.3 평가 지표

| 지표 | 용도 |
|------|------|
| **RMSE** | 예측 오차 크기 |
| **MAE** | 이상치에 강건한 오차 |
| **R² Score** | 분산 설명력 |
| **R² 향상률** | `(Enhanced_R² - Baseline_R²) / |Baseline_R²| × 100%` |

---

## 6. ML 분석 파이프라인 (보강 반영)

```
STEP 1: 원본 데이터 EDA + 기본 전처리
STEP 2: 보강 데이터 3종 탐색
  ├── ① BigMart: Item_Visibility·MRP·Outlet_Size 분석 → 피처 설계 근거
  ├── ② Supermarket Sales: 월별·요일별 판매 패턴 + 할인 효과 분석 → 시간·할인 피처 설계
  └── ③ Supermart: 할인율·이익률 분석 → 카테고리 매핑 근거
STEP 3: 보강 파생변수 생성 (방식 A+B+C)
STEP 4: Baseline 모델 학습 (원본 피처만, 5모델)
STEP 5: Enhanced 모델 학습 (원본+보강 피처, 5모델)
STEP 6: 성능 비교 분석 (Baseline vs Enhanced)
STEP 7: SHAP 분석 (Enhanced 최적 모델) + BigMart 비교 인사이트
```

---

## 7. 시각화 요구사항 (보강 버전, 총 12종)

| # | 시각화 | 파일명 |
|---|--------|--------|
| 1 | Avg_Daily_Sales 분포 (histplot) | `avg_daily_sales_distribution.png` |
| 2 | 카테고리별(10종) 판매량 boxplot | `category_sales_boxplot.png` |
| 3 | ABC 등급별 판매량 boxplot | `abc_class_sales_boxplot.png` |
| 4 | 상관관계 히트맵 (전체 피처) | `correlation_heatmap_full.png` |
| 5 | **보강 파생변수 vs Avg_Daily_Sales 산점도** | `enhanced_features_scatter.png` |
| 6 | **월별/분기별 판매량 패턴** (Supermarket Sales 참고) | `monthly_sales_pattern.png` |
| 7 | **Baseline vs Enhanced 성능 비교** | `baseline_vs_enhanced_regression.png` |
| 8 | 실제값 vs 예측값 산점도 (Enhanced 최적) | `actual_vs_predicted_enhanced.png` |
| 9 | 잔차 분석 (Enhanced 최적) | `residual_analysis_enhanced.png` |
| 10 | **SHAP Summary Plot (Enhanced)** | `shap_summary_enhanced.png` |
| 11 | **SHAP Bar Plot (보강 피처 기여도)** | `shap_importance_enhanced.png` |
| 12 | **BigMart 비교 분석 차트** | `bigmart_comparison.png` |

---

## 8. Jupyter Notebook 구조 (보강 버전)

```
02_Avg_Daily_Sales_Prediction_Enhanced.ipynb
│
├── 0. 라이브러리 임포트 & 설정
├── 1. 데이터 로드 & 기본 확인
├── 2. 보강 데이터 탐색 ★
│   ├── 2.1 ① BigMart Sales Data 탐색
│   ├── 2.2 ② Supermarket Sales Data 시계열·할인 패턴 분석
│   └── 2.3 ③ Supermart 할인·이익률 분석
├── 3. 데이터 전처리 + 보강 파생변수 생성
├── 4. EDA (원본 + 보강 피처)
├── 5. Baseline 모델 학습 (5모델)
├── 6. Enhanced 모델 학습 (5모델) ★
├── 7. 성능 비교 분석 (Baseline vs Enhanced) ★
├── 8. SHAP 분석 (Enhanced 최적 모델) ★
├── 9. BigMart 비교 인사이트 ★
└── 10. 결론 및 인사이트
```

---

## 9. 핵심 유의사항

### 9.1 Data Leakage 주의

- `Visibility_Proxy`, `Price_Sensitivity`, `Category_Sales_Mean`은 Avg_Daily_Sales 정보를 사용하므로 **Train에서만 계산 → Test에 매핑** 처리 필수
- Leakage 의심 변수 포함/제외 양쪽 실험 결과를 모두 기록

### 9.2 인도네시아 로케일 전처리 필수

- `Avg_Daily_Sales`를 포함한 5개 컬럼이 쉼표 소수점 형식 → 반드시 변환 후 피처/타겟으로 사용
- `Unit_Cost_USD`는 `$` + 천단위`.` + 쉼표소수점의 복합 형식 → 3단계 변환 필수

### 9.3 카테고리 매핑의 한계

- 방식 C(Supermart 매핑)의 할인율·이익률은 시뮬레이션 값이므로 노트북에 **근거 문서화 필수**
- 같은 카테고리 내 분산이 0이 되므로, 단독으로는 회귀 기여도가 낮을 수 있음 → **다른 피처와의 상호작용**으로 기여
- 원본 10개 카테고리에 대해 Supermart(인도 데이터)와 Supermarket Sales(중국 데이터) 양쪽의 통계를 교차 검증하여 매핑 신뢰도를 높일 것

### 9.4 Supermarket Sales Data 활용 시 주의

- annex2.csv가 약 87만 행으로 대용량 → 메모리 관리 주의 (필요 시 샘플링 또는 집계 후 활용)
- 중국 위안(RMB) 기준 가격이므로, 원본 USD 가격과 직접 비교 불가 → **패턴**과 **비율** 기준으로 활용
- 할인 효과 분석에서 할인 유무(Yes/No)만 있고 할인율은 없음 → Supermart의 할인율 분석과 상호 보완

### 9.5 다른 소주제와의 연결

- 소주제 2의 SHAP 결과 → 소주제 4 클러스터링 피처 선정 참고
- 소주제 2의 판매량 예측값 → 소주제 3의 `Days_To_Deplete = Quantity_On_Hand / Avg_Daily_Sales` 정밀화에 활용 가능
- 보강 파생변수 중 유용한 것은 소주제 3·4에서도 활용 검토

---

## 10. 기대 산출물 체크리스트

- [ ] `02_Avg_Daily_Sales_Prediction_Enhanced.ipynb`
- [ ] 보강 데이터 3종 탐색 결과 요약
- [ ] Baseline vs Enhanced 성능 비교표 (RMSE, MAE, R², 향상률)
- [ ] SHAP Summary Plot (보강 피처 기여도 표시)
- [ ] 시각화 파일 12종 (`outputs/figures/`)
- [ ] 최적 모델 저장 (`outputs/models/best_regressor_enhanced.pkl`)
- [ ] 핵심 인사이트 5~7개

---

## 부록: 보강 데이터 파일 경로

| # | 데이터 | 프로젝트 내 경로 | 비고 |
|---|--------|-----------------|------|
| ① | BigMart Sales Data | `data/etc_subtopic2/BigMart Sales Data/Train.csv`, `Test.csv` | 8,523행 × 12열 |
| ② | Supermarket Sales Data | `data/etc_subtopic2/Supermarket Sales Data/annex1.csv` ~ `annex4.csv` | annex2가 878,503행 (대용량) |
| ③ | Supermart Grocery Sales | `data/etc_subtopic2/Supermart Grocery Sales - Retail Analytics Dataset.csv` | 약 9,994행 × 11열 |
