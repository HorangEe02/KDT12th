# 소주제 1 — 재고 상태 분류 (Multi-class Classification) 구현 가이드 [보강 데이터 통합 버전]

> 이 문서는 Claude Code가 소주제 1의 전체 파이프라인을 구현할 때 참조하는 가이드라인입니다.
> **[v2.0]** 원본 데이터의 한계를 보완하기 위해 3종의 Kaggle 보강 데이터를 통합한 확장 버전입니다.

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열) + 보강 데이터 3종
- 소주제 1 담당: 정이랑

### 1.2 소주제 1 목표

제품의 재고·판매·공급 정보를 기반으로 현재 재고 상태(In Stock / Low Stock / Out of Stock / Expiring Soon)를 예측하는 **다중 클래스 분류 모델**을 구축하고, 상태를 결정짓는 핵심 요인을 도출한다.

### 1.3 보강 데이터 도입 배경

원본 데이터만으로는 Inventory_Status를 결정짓는 **공급망 요인(백오더 리스크, 공급자 품질, 물류 지연 등)**이 부재하여 분류 성능에 한계가 존재한다. 이를 보완하기 위해 3종의 외부 데이터를 도입한다.

| 보강 목적 | 한계점 | 보강 데이터 |
|-----------|--------|------------|
| Low Stock/Out of Stock 예측력 강화 | 품절·재고 부족을 유발하는 수요·공급 변수 부재 | ① Back Order Prediction Dataset |
| 공급망 리스크 관점 추가 | 공급자 품질·결함·비용 정보 부재 | ② Supply Chain Dataset |
| 물류 지연·배송 리스크 변수 도입 | 배송 지연, 리드타임 변동성, 물류 리스크 정보 부재 | ③ Dynamic Supply Chain Logistics Dataset |

### 1.4 도출할 인사이트 (확장)

**[기존]**
- 제품의 재고 상태(Inventory_Status)를 결정짓는 핵심 피처는 무엇인가?
- Out of Stock이 2건에 불과한 극심한 불균형에서 어떤 전략이 효과적인가?
- Confusion Matrix에서 가장 혼동이 많은 클래스 조합과 그 이유는?

**[보강 데이터 추가]**
- 외부 데이터에서 파생한 공급망 리스크 변수가 분류 성능을 유의미하게 향상시키는가?
- 보강 전후 모델 성능 비교를 통해, Inventory_Status 결정에 공급망 요인이 얼마나 기여하는지 정량화
- Low Stock 분류에서 리드타임·공급자 성과 관련 파생변수가 혼동을 줄이는 데 기여하는가?

---

## 2. 데이터 명세

### 2.1 원본 데이터 (메인)

- **파일:** `Inventory Management E-Grocery - InventoryData.csv`
- **출처:** [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/)
- **규모:** 1,000행 × 37열
- **결측치:** Notes 컬럼 834건 (분석 미사용) — 실질적 결측치 이슈 없음
- **데이터 특성:** 인도네시아(자카르타, 반둥, 수라바야, 덴파사르, 메단) 소재 E-Grocery 운영 데이터

#### 소주제1 활용 컬럼 요약

| 구분 | 컬럼 | 소주제1 역할 |
|------|------|-------------|
| 수치형 피처 | Quantity_On_Hand, Reorder_Point, Safety_Stock, Unit_Cost_USD, Avg_Daily_Sales, Days_of_Inventory, Stock_Age_Days, Lead_Time_Days, Quantity_Reserved, Quantity_Committed | ✅ 입력 피처 |
| 범주형 피처 | Category (10종), ABC_Class (A/B/C) | ✅ 입력 피처 (인코딩) |
| 날짜 컬럼 | Received_Date, Last_Purchase_Date, Expiry_Date | ✅ 파생변수 생성용 |
| 타겟 변수 | Inventory_Status (4클래스) | 🎯 타겟 |

#### 타겟 변수: Inventory_Status 분포

| 상태          | 의미                               | 건수  | 비율  |
| ------------- | ---------------------------------- | ----- | ----- |
| In Stock      | 현재 정상 재고 보유 중             | 428건 | 42.8% |
| Expiring Soon | 유통기한 임박 제품                 | 329건 | 32.9% |
| Low Stock     | 재고 수준이 재주문점 이하로 하락   | 241건 | 24.1% |
| Out of Stock  | 재고 완전 소진 (품절)              | 2건   | 0.2%  |

> ⚠️ **극심한 클래스 불균형** — Out of Stock 2건(0.2%). 3클래스 통합 또는 class_weight 조정 필요

---

### 2.2 보강 데이터 ① — Back Order Prediction Dataset

#### 기본 정보

| 항목 | 내용 |
|------|------|
| **파일** | `data/etc_subtopic1/Back Order Prediction Dataset/Training_BOP.csv` |
| **출처** | [Kaggle - Back Order Prediction Dataset](https://www.kaggle.com/datasets/gowthammiryala/back-order-prediction-dataset) |
| **규모** | 약 1,687,861행 × 23열 |
| **설명** | 8주간의 제품별 재고·판매·예측·리스크 데이터로, 품절(Backorder) 여부를 예측하는 대규모 데이터셋 |
| **타겟** | `went_on_backorder` (Yes/No) |

#### 왜 추가해야 하는가?

원본 데이터의 **Low Stock(241건)**과 **Out of Stock(2건)** 상태를 유발하는 근본 원인 변수(수요 예측, 리드타임, 공급 성과 등)가 원본에 충분히 존재하지 않는다. 이 데이터셋은 Backorder 발생의 핵심 예측 변수를 다수 포함하고 있어, **재고 부족 관련 클래스의 분류 근거를 보강**하는 데 활용한다.

#### 전체 컬럼 목록 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | sku | object | 제품 식별자 | ❌ 제외 |
| 2 | **national_inv** | float | 현재 전국 재고 수준 | ✅ Quantity_On_Hand와 대응 |
| 3 | **lead_time** | float | 공급 리드타임 (일) | ✅ **핵심 — Lead_Time_Days 보강 설계 기준** |
| 4 | in_transit_qty | float | 운송 중 수량 | ✅ 피처 설계 참고 |
| 5 | forecast_3_month | float | 향후 3개월 판매 예측 | ✅ **수요 예측 변수 설계 기준** |
| 6 | forecast_6_month | float | 향후 6개월 판매 예측 | ✅ 피처 설계 참고 |
| 7 | forecast_9_month | float | 향후 9개월 판매 예측 | ⚠️ 선택적 |
| 8 | sales_1_month | float | 직전 1개월 판매량 | ✅ **판매 추세 변수 설계 기준** |
| 9 | sales_3_month | float | 직전 3개월 판매량 | ✅ 피처 설계 참고 |
| 10 | sales_6_month | float | 직전 6개월 판매량 | ⚠️ 선택적 |
| 11 | sales_9_month | float | 직전 9개월 판매량 | ⚠️ 선택적 |
| 12 | min_bank | float | 최소 권장 재고 수준 | ✅ Reorder_Point와 대응 |
| 13 | pieces_past_due | float | 기한 초과 부품 수 | ✅ **공급 지연 변수 설계 기준** |
| 14 | **perf_6_month_avg** | float | 6개월 평균 공급 성과 | ✅ **핵심 — 공급자 성과 피처 설계** |
| 15 | **perf_12_month_avg** | float | 12개월 평균 공급 성과 | ✅ **핵심 — 공급자 성과 피처 설계** |
| 16 | local_bo_qty | float | 기존 백오더 수량 | ✅ 피처 설계 참고 |
| 17 | potential_issue | binary | 잠재적 이슈 플래그 | ✅ 리스크 플래그 설계 참고 |
| 18 | deck_risk | binary | 데크 리스크 플래그 | ⚠️ 선택적 |
| 19 | oe_constraint | binary | OE 제약 조건 플래그 | ✅ 리스크 플래그 설계 참고 |
| 20 | ppap_risk | binary | PPAP 리스크 플래그 | ⚠️ 선택적 |
| 21 | stop_auto_buy | binary | 자동 구매 중단 플래그 | ✅ 재고 관리 전략과 연관 |
| 22 | rev_stop | binary | 리비전 중단 플래그 | ⚠️ 선택적 |
| 23 | **went_on_backorder** | binary | 백오더 발생 여부 (타겟) | ✅ **참조 타겟 — 분석 비교용** |

#### 활용 방식: 직접 병합이 아닌 "피처 설계 프레임워크"로 활용

> ⚠️ **중요:** 이 데이터는 원본 데이터와 **제품 ID가 매칭되지 않으므로 직접 JOIN/MERGE가 불가능**하다.
> 대신, 이 데이터의 변수 구조를 참고하여 **원본 데이터에서 유사한 파생변수를 설계**하는 방식으로 활용한다.

---

### 2.3 보강 데이터 ② — Supply Chain Dataset

#### 기본 정보

| 항목 | 내용 |
|------|------|
| **파일** | `data/etc_subtopic1/supply_chain_data.csv` |
| **출처** | [Kaggle - Supply Chain Dataset](https://www.kaggle.com/datasets/amirmotefaker/supply-chain-dataset) |
| **규모** | 100행 × 24열 |
| **설명** | 제조-물류 공급망의 제품별 판매·제조·물류 데이터 |

#### 왜 추가해야 하는가?

원본 데이터에는 **공급자의 품질(결함률), 비용 구조(제조비·배송비), 검수 결과** 등이 전혀 없다. 이 데이터셋은 공급자 품질과 비용 관점의 변수를 포함하고 있어, **재고 상태 결정에 공급자 품질·비용이 미치는 영향**을 분석하는 데 활용한다.

#### 주요 컬럼 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | Product type | object | 제품 유형 (skincare, haircare, cosmetics) | ✅ 카테고리 매핑 참고 |
| 2 | Number of products sold | int | 판매 수량 | ✅ Avg_Daily_Sales 대응 |
| 3 | Stock levels | int | 재고 수준 | ✅ Quantity_On_Hand 대응 |
| 4 | **Lead times** | int | 공급 리드타임 (일) | ✅ **핵심 — Lead_Time_Days 대응** |
| 5 | Order quantities | int | 주문 수량 | ✅ 참고 |
| 6 | **Shipping costs** | float | 배송 비용 | ✅ **비용 관련 파생변수 참고** |
| 7 | Supplier name | object | 공급업체명 | ✅ Supplier_Name 대응 |
| 8 | **Defect rates** | float | 결함률 (%) | ✅ **핵심 — 공급자 품질 피처 설계** |
| 9 | **Manufacturing costs** | float | 제조 비용 | ✅ **비용 관련 파생변수 참고** |
| 10 | **Inspection results** | object | 검수 결과 (Pass/Fail/Pending) | ✅ **핵심 — 품질 리스크 플래그** |
| 11 | Manufacturing lead time | int | 제조 리드타임 | ✅ 리드타임 세분화 참고 |

#### 활용 방식: 카테고리 수준의 통계적 매핑 + 시뮬레이션 피처 생성

> 이 데이터의 **제품 유형별 평균 결함률, 평균 리드타임, 평균 배송 비용** 등을 참고하여,
> 원본 데이터의 Category에 대응하는 **시뮬레이션 기반 파생변수**를 생성한다.

---

### 2.4 보강 데이터 ③ — Dynamic Supply Chain Logistics Dataset

#### 기본 정보

| 항목 | 내용 |
|------|------|
| **파일** | `data/etc_subtopic1/dynamic_supply_chain_logistics_dataset.csv` |
| **출처** | [Kaggle - Logistics and Supply Chain Dataset](https://www.kaggle.com/) |
| **규모** | 약 32,065행 × 26열 |
| **설명** | 물류·공급망의 실시간 리스크 데이터 (GPS, 날씨, 교통, 배송 지연, 공급자 신뢰도 등) |

#### 왜 추가해야 하는가?

원본 데이터에는 **배송 지연 확률, 물류 리스크, 공급자 신뢰도 점수** 등 물류 관련 변수가 전혀 없다. 이 데이터셋은 공급망 리스크와 배송 지연 변수를 포함하고 있어, **Inventory_Status 중 Low Stock/Out of Stock이 물류 문제에 의해 유발될 가능성**을 분석하는 관점을 추가한다.

#### 주요 컬럼 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | timestamp | datetime | 데이터 수집 시점 | ❌ 참조용 |
| 2 | warehouse_inventory_level | float | 창고 재고 수준 | ✅ Quantity_On_Hand 대응 |
| 3 | **supplier_reliability_score** | float | 공급자 신뢰도 점수 (0~1) | ✅ **핵심 — 공급자 성과 파생변수 설계** |
| 4 | **lead_time_days** | float | 공급 리드타임 (일) | ✅ **핵심 — Lead_Time_Days 대응** |
| 5 | historical_demand | float | 과거 수요량 | ✅ 수요 변수 참고 |
| 6 | **delay_probability** | float | 배송 지연 확률 (0~1) | ✅ **핵심 — 지연 리스크 플래그 설계** |
| 7 | **risk_classification** | object | 리스크 등급 (Low/Moderate/High Risk) | ✅ **핵심 — 리스크 등급 매핑** |
| 8 | **delivery_time_deviation** | float | 실제 배송 시간 편차 | ✅ **핵심 — 지연일수 파생변수** |
| 9 | order_fulfillment_status | float | 주문 이행률 (0~1) | ✅ 공급 성과 참고 |
| 10 | disruption_likelihood_score | float | 공급 중단 가능성 점수 | ✅ 리스크 파생변수 참고 |
| 11 | shipping_costs | float | 배송 비용 | ✅ 비용 참고 |

#### 활용 방식: 물류 리스크 파생변수 설계 근거 + 비교 분석

> 이 데이터의 **delay_probability, risk_classification, supplier_reliability_score** 개념을 참고하여,
> 원본 데이터에서 `Lead_Time_Days`, `Supplier_OnTime_Pct`, 날짜 컬럼 간 차이를 활용한 **물류 리스크 추정 변수**를 설계한다.

---

## 3. 보강 데이터 통합 전략

### 3.1 통합 방식 개요

세 보강 데이터셋은 원본과 **제품 ID가 매칭되지 않으므로**, 직접 JOIN/MERGE가 아닌 다음 3가지 방식으로 통합한다.

```
┌──────────────────────────────────────────────────────────────────┐
│                    보강 데이터 통합 3가지 방식                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  방식 A: 피처 설계 프레임워크 (Feature Design Framework)            │
│  → 보강 데이터의 변수 구조를 참고하여 원본에서 유사 파생변수 생성       │
│  → 주 활용: ① Back Order Prediction Dataset                      │
│                                                                  │
│  방식 B: 카테고리별 통계 매핑 (Statistical Mapping)                 │
│  → 보강 데이터에서 카테고리별 평균 통계를 추출하여 원본에 시뮬레이션 반영│
│  → 주 활용: ② Supply Chain Dataset                                │
│                                                                  │
│  방식 C: 독립 비교 분석 (Comparative Analysis)                      │
│  → 보강 데이터를 별도로 분석한 후, 원본 결과와 비교·대조하여 인사이트 도출│
│  → 주 활용: ③ Dynamic Supply Chain Logistics Dataset              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 방식 A — 피처 설계 프레임워크 (① Back Order Dataset 활용)

Back Order Dataset의 핵심 변수 구조를 참고하여, 원본 데이터의 기존 컬럼에서 **6개 파생변수**를 추가 설계한다.

| 파생변수명 | 설계 근거 (Back Order 참고 변수) | 원본 활용 컬럼 | 계산식 |
|-----------|-------------------------------|---------------|--------|
| **Supply_Lead_Gap** | `lead_time` | Received_Date, Last_Purchase_Date | `(Received_Date - Last_Purchase_Date).dt.days` |
| **Demand_Supply_Ratio** | `forecast / national_inv` | Avg_Daily_Sales, Quantity_On_Hand | `Avg_Daily_Sales * 30 / Quantity_On_Hand` |
| **Stock_Coverage_Days** | `national_inv / sales` | Quantity_On_Hand, Avg_Daily_Sales | `Quantity_On_Hand / Avg_Daily_Sales` |
| **Reorder_Urgency** | `min_bank - national_inv` | Reorder_Point, Quantity_On_Hand | `(Reorder_Point - Quantity_On_Hand) / Reorder_Point` |
| **Supply_Performance_Proxy** | `perf_6_month_avg` | Supplier_OnTime_Pct | `Supplier_OnTime_Pct / Supplier_OnTime_Pct.mean()` |
| **Overdue_Risk_Flag** | `pieces_past_due > 0` | Days_To_Expiry, Stock_Age_Days | `1 if Days_To_Expiry < Stock_Age_Days else 0` |

```python
# 방식 A: Back Order Dataset 참고 파생변수 생성

# 1. Supply_Lead_Gap: 리드타임 추정 (입고일 - 최종발주일)
df['Supply_Lead_Gap'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days

# 2. Demand_Supply_Ratio: 월간 수요/공급 비율
#    Back Order의 forecast/national_inv 개념 차용
df['Demand_Supply_Ratio'] = (df['Avg_Daily_Sales'] * 30) / df['Quantity_On_Hand'].replace(0, np.nan)
df['Demand_Supply_Ratio'] = df['Demand_Supply_Ratio'].fillna(df['Demand_Supply_Ratio'].median())

# 3. Stock_Coverage_Days: 현재 재고가 버틸 수 있는 일수
#    Back Order의 national_inv / sales 개념
df['Stock_Coverage_Days'] = df['Quantity_On_Hand'] / df['Avg_Daily_Sales'].replace(0, np.nan)
df['Stock_Coverage_Days'] = df['Stock_Coverage_Days'].fillna(df['Stock_Coverage_Days'].median())

# 4. Reorder_Urgency: 재고 부족 긴급도 (정규화)
#    Back Order의 min_bank 대비 재고 차이 개념
df['Reorder_Urgency'] = (df['Reorder_Point'] - df['Quantity_On_Hand']) / df['Reorder_Point'].replace(0, 1)

# 5. Supply_Performance_Proxy: 공급 성과 대리 변수
#    Back Order의 perf_6_month_avg 개념 — Supplier_OnTime_Pct를 평균 대비 정규화
df['Supply_Performance_Proxy'] = df['Supplier_OnTime_Pct'] / df['Supplier_OnTime_Pct'].mean()

# 6. Overdue_Risk_Flag: 유통기한 초과 리스크 플래그
#    Back Order의 pieces_past_due 개념
df['Overdue_Risk_Flag'] = (df['Days_To_Expiry'] < df['Stock_Age_Days']).astype(int)
```

### 3.3 방식 B — 카테고리별 통계 매핑 (② Supply Chain Dataset 활용)

Supply Chain Dataset에서 제품 유형별 평균 통계를 추출하고, 원본 Category에 매핑하여 시뮬레이션 파생변수를 생성한다.

#### Step 1: Supply Chain Dataset 분석

```python
# Supply Chain Dataset 로드
df_sc = pd.read_csv('data/etc_subtopic1/supply_chain_data.csv')

# 제품 유형별 핵심 통계 추출
sc_stats = df_sc.groupby('Product type').agg({
    'Defect rates': 'mean',
    'Lead times': 'mean',
    'Shipping costs': 'mean',
    'Manufacturing costs': 'mean'
}).reset_index()

print(sc_stats)
```

#### Step 2: 원본 Category에 시뮬레이션 매핑

```python
# 원본 10개 카테고리 → Supply Chain 통계 기반 시뮬레이션 매핑
# (실제 매핑은 Supply Chain Dataset EDA 결과 + 도메인 지식에 따라 조정)

category_risk_mapping = {
    # 카테고리: (추정 결함률, 추정 리드타임, 추정 배송비용)
    # 부패 위험 높은 카테고리 → 높은 결함률, 짧은 리드타임 필요
    'Seafood':        {'est_defect_rate': 4.5, 'est_lead_time': 3,  'est_shipping_cost': 12.0},
    'Fresh Produce':  {'est_defect_rate': 4.0, 'est_lead_time': 3,  'est_shipping_cost': 10.0},
    'Meat':           {'est_defect_rate': 3.8, 'est_lead_time': 4,  'est_shipping_cost': 11.0},
    'Dairy':          {'est_defect_rate': 3.5, 'est_lead_time': 5,  'est_shipping_cost': 8.0},
    'Bakery':         {'est_defect_rate': 3.0, 'est_lead_time': 2,  'est_shipping_cost': 5.0},
    'Frozen':         {'est_defect_rate': 2.5, 'est_lead_time': 7,  'est_shipping_cost': 9.0},
    'Beverages':      {'est_defect_rate': 1.5, 'est_lead_time': 10, 'est_shipping_cost': 7.0},
    'Pantry':         {'est_defect_rate': 1.0, 'est_lead_time': 15, 'est_shipping_cost': 6.0},
    'Personal Care':  {'est_defect_rate': 0.8, 'est_lead_time': 12, 'est_shipping_cost': 5.5},
    'Household':      {'est_defect_rate': 0.5, 'est_lead_time': 14, 'est_shipping_cost': 6.5},
}

# 매핑 적용
for col_suffix, key in [('Est_Defect_Rate', 'est_defect_rate'),
                         ('Est_Lead_Time', 'est_lead_time'),
                         ('Est_Shipping_Cost', 'est_shipping_cost')]:
    df[col_suffix] = df['Category'].map(
        {cat: vals[key] for cat, vals in category_risk_mapping.items()}
    )
```

> ⚠️ **매핑 근거 문서화 필수:** 노트북에서 Supply Chain Dataset의 분석 결과를 먼저 제시하고, 해당 통계를 기반으로 매핑한 근거를 마크다운 셀로 설명할 것.

#### Step 3: 복합 파생변수 생성

```python
# 품질 리스크 점수: 결함률 × 단가 (결함이 비싼 제품일수록 리스크 높음)
df['Quality_Risk_Score'] = df['Est_Defect_Rate'] * df['Unit_Cost_USD']

# 공급 비용 효율: 배송비 / 단가 (비용 대비 가격이 낮으면 비효율)
df['Cost_Efficiency_Ratio'] = df['Est_Shipping_Cost'] / df['Unit_Cost_USD'].replace(0, np.nan)
df['Cost_Efficiency_Ratio'] = df['Cost_Efficiency_Ratio'].fillna(df['Cost_Efficiency_Ratio'].median())
```

### 3.4 방식 C — 독립 비교 분석 (③ Dynamic Supply Chain Logistics Dataset 활용)

Dynamic Supply Chain Logistics Dataset을 별도로 분석하여, 원본 데이터의 분석 결과와 **비교·대조하는 독립 섹션**으로 활용한다.

#### Step 1: Logistics Dataset에서 물류 리스크 분석

```python
# Dynamic Supply Chain Logistics Dataset 분석 (별도 셀)
df_logistics = pd.read_csv('data/etc_subtopic1/dynamic_supply_chain_logistics_dataset.csv')

# 리스크 등급별 배송 지연 확률 분석
risk_delay = df_logistics.groupby('risk_classification').agg({
    'delay_probability': 'mean',
    'delivery_time_deviation': 'mean',
    'supplier_reliability_score': 'mean'
}).round(3)
print("리스크 등급별 평균 지연 확률·편차·공급자 신뢰도:")
print(risk_delay)

# 공급자 신뢰도와 배송 지연 확률 간 상관관계
corr = df_logistics[['supplier_reliability_score', 'delay_probability',
                      'delivery_time_deviation', 'lead_time_days']].corr()
print("\n물류 핵심 변수 간 상관관계:")
print(corr.round(3))
```

#### Step 2: 원본 데이터에 물류 리스크 추정 변수 적용

```python
# Logistics Dataset의 delay_probability / risk_classification 개념을 원본에 적용
# 원본에서 가용한 변수: Lead_Time_Days, Supplier_OnTime_Pct, Supply_Lead_Gap

# 리드타임 기반 지연 리스크 플래그 (리드타임 중위값 × 1.5 초과 시 지연으로 추정)
lead_time_median = df['Lead_Time_Days'].median()
df['Delivery_Delay_Flag'] = (df['Lead_Time_Days'] > lead_time_median * 1.5).astype(int)

# 공급자 신뢰도 기반 리스크 등급 (Supplier_OnTime_Pct 기준)
df['Supply_Risk_Level'] = pd.cut(
    df['Supplier_OnTime_Pct'],
    bins=[0, 70, 85, 100],
    labels=['High_Risk', 'Moderate_Risk', 'Low_Risk']
)
```

#### Step 3: 비교 분석 인사이트 도출

```python
# 원본 데이터: Inventory_Status별 물류 리스크 변수 분포
delay_by_status = pd.crosstab(
    df['Inventory_Status'], df['Delivery_Delay_Flag'], normalize='index'
)
print("원본 데이터 — Inventory_Status별 배송 지연 추정 비율:")
print(delay_by_status)

risk_by_status = pd.crosstab(
    df['Inventory_Status'], df['Supply_Risk_Level'], normalize='index'
)
print("\n원본 데이터 — Inventory_Status별 공급 리스크 등급 분포:")
print(risk_by_status)

# Logistics Dataset과 비교:
# "Logistics 데이터에서 High Risk 등급의 평균 지연 확률이 X%였는데,
#  원본 데이터에서도 Low Stock 제품이 높은 리드타임/낮은 공급자 신뢰도를 보이는가?"
```

---

## 4. 전처리 파이프라인 (보강 버전)

### 4.1 공통 전처리

```python
import pandas as pd
import numpy as np

# 0. 데이터 로드
df = pd.read_csv('data/Supply Chain Inventory Management Grocery Industry/Inventory Management E-Grocery - InventoryData.csv')

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

### 4.2 기본 파생변수 (원본 기반)

```python
# 원본 기반 파생변수
df['Days_To_Expiry'] = (df['Expiry_Date'] - df['Received_Date']).dt.days
df['Days_Since_Last_Order'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days
df['Stock_Gap'] = df['Reorder_Point'] - df['Quantity_On_Hand']
df['Available_Stock'] = df['Quantity_On_Hand'] - df['Quantity_Reserved'] - df['Quantity_Committed']
```

### 4.3 보강 파생변수 (보강 데이터 참고)

```python
# ── 방식 A: Back Order Dataset 참고 ──

df['Supply_Lead_Gap'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days

df['Demand_Supply_Ratio'] = (df['Avg_Daily_Sales'] * 30) / df['Quantity_On_Hand'].replace(0, np.nan)
df['Demand_Supply_Ratio'] = df['Demand_Supply_Ratio'].fillna(df['Demand_Supply_Ratio'].median())

df['Stock_Coverage_Days'] = df['Quantity_On_Hand'] / df['Avg_Daily_Sales'].replace(0, np.nan)
df['Stock_Coverage_Days'] = df['Stock_Coverage_Days'].fillna(df['Stock_Coverage_Days'].median())

df['Reorder_Urgency'] = (df['Reorder_Point'] - df['Quantity_On_Hand']) / df['Reorder_Point'].replace(0, 1)

df['Supply_Performance_Proxy'] = df['Supplier_OnTime_Pct'] / df['Supplier_OnTime_Pct'].mean()

df['Overdue_Risk_Flag'] = (df['Days_To_Expiry'] < df['Stock_Age_Days']).astype(int)

# ── 방식 B: Supply Chain Dataset 참고 ──

category_risk_mapping = {
    'Seafood':        {'est_defect_rate': 4.5, 'est_lead_time': 3,  'est_shipping_cost': 12.0},
    'Fresh Produce':  {'est_defect_rate': 4.0, 'est_lead_time': 3,  'est_shipping_cost': 10.0},
    'Meat':           {'est_defect_rate': 3.8, 'est_lead_time': 4,  'est_shipping_cost': 11.0},
    'Dairy':          {'est_defect_rate': 3.5, 'est_lead_time': 5,  'est_shipping_cost': 8.0},
    'Bakery':         {'est_defect_rate': 3.0, 'est_lead_time': 2,  'est_shipping_cost': 5.0},
    'Frozen':         {'est_defect_rate': 2.5, 'est_lead_time': 7,  'est_shipping_cost': 9.0},
    'Beverages':      {'est_defect_rate': 1.5, 'est_lead_time': 10, 'est_shipping_cost': 7.0},
    'Pantry':         {'est_defect_rate': 1.0, 'est_lead_time': 15, 'est_shipping_cost': 6.0},
    'Personal Care':  {'est_defect_rate': 0.8, 'est_lead_time': 12, 'est_shipping_cost': 5.5},
    'Household':      {'est_defect_rate': 0.5, 'est_lead_time': 14, 'est_shipping_cost': 6.5},
}

for col_suffix, key in [('Est_Defect_Rate', 'est_defect_rate'),
                         ('Est_Lead_Time', 'est_lead_time'),
                         ('Est_Shipping_Cost', 'est_shipping_cost')]:
    df[col_suffix] = df['Category'].map(
        {cat: vals[key] for cat, vals in category_risk_mapping.items()}
    )

df['Quality_Risk_Score'] = df['Est_Defect_Rate'] * df['Unit_Cost_USD']
df['Cost_Efficiency_Ratio'] = df['Est_Shipping_Cost'] / df['Unit_Cost_USD'].replace(0, np.nan)
df['Cost_Efficiency_Ratio'] = df['Cost_Efficiency_Ratio'].fillna(df['Cost_Efficiency_Ratio'].median())

# ── 방식 C: Dynamic Supply Chain Logistics Dataset 참고 ──

lead_time_median = df['Lead_Time_Days'].median()
df['Delivery_Delay_Flag'] = (df['Lead_Time_Days'] > lead_time_median * 1.5).astype(int)
```

### 4.4 클래스 불균형 처리

```python
# Out of Stock → Low Stock에 병합하여 3클래스 (권장)
df['Inventory_Status_3cls'] = df['Inventory_Status'].replace('Out of Stock', 'Low Stock')
```

### 4.5 카테고리 인코딩

```python
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

---

## 5. 모델링 상세 설계 (보강 버전)

### 5.1 피처 목록 — 2단계 비교 설계

> **핵심:** 보강 전/후 피처셋을 각각 학습하여 **성능 향상 정도를 정량적으로 비교**한다.

#### Baseline 피처셋 (원본만)

```python
baseline_features = [
    # 수치형 (14개)
    'Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock',
    'Unit_Cost_USD', 'Avg_Daily_Sales', 'Days_of_Inventory',
    'Stock_Age_Days', 'Lead_Time_Days',
    'Quantity_Reserved', 'Quantity_Committed',
    'Days_To_Expiry', 'Days_Since_Last_Order',
    'Stock_Gap', 'Available_Stock',
    # 범주형 One-Hot (Category 9개 + ABC_Class 2개, drop_first 적용 후)
]
```

#### Enhanced 피처셋 (원본 + 보강)

```python
enhanced_features = baseline_features + [
    # 방식 A: Back Order 참고 파생 (6개)
    'Supply_Lead_Gap',
    'Demand_Supply_Ratio',
    'Stock_Coverage_Days',
    'Reorder_Urgency',
    'Supply_Performance_Proxy',
    'Overdue_Risk_Flag',
    # 방식 B: Supply Chain 참고 매핑 (5개)
    'Est_Defect_Rate',
    'Est_Lead_Time',
    'Est_Shipping_Cost',
    'Quality_Risk_Score',
    'Cost_Efficiency_Ratio',
    # 방식 C: Logistics 참고 (1개)
    'Delivery_Delay_Flag',
]
```

### 5.2 타겟 인코딩

```python
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()

# 3클래스 (권장)
y = le.fit_transform(df['Inventory_Status_3cls'])
# Expiring Soon=0, In Stock=1, Low Stock=2
```

### 5.3 Train/Test Split

```python
from sklearn.model_selection import train_test_split

# Baseline
X_base = df_encoded[baseline_feature_cols]
X_train_b, X_test_b, y_train, y_test = train_test_split(
    X_base, y, test_size=0.2, random_state=42, stratify=y
)

# Enhanced
X_enh = df_encoded[enhanced_feature_cols]
X_train_e, X_test_e, _, _ = train_test_split(
    X_enh, y, test_size=0.2, random_state=42, stratify=y
)
```

> ⚠️ **동일한 random_state=42, stratify=y**로 분할하여 공정한 비교 보장

### 5.4 스케일링

```python
from sklearn.preprocessing import StandardScaler

scaler_b = StandardScaler()
X_train_b_scaled = scaler_b.fit_transform(X_train_b)
X_test_b_scaled = scaler_b.transform(X_test_b)

scaler_e = StandardScaler()
X_train_e_scaled = scaler_e.fit_transform(X_train_e)
X_test_e_scaled = scaler_e.transform(X_test_e)
```

### 5.5 학습할 모델 (4종 × 2셋 = 8회)

| # | 모델 | 라이브러리 | 주요 하이퍼파라미터 |
|---|------|-----------|---------------------|
| 1 | Logistic Regression | sklearn | `multi_class='multinomial'`, `max_iter=1000`, `class_weight='balanced'` |
| 2 | Random Forest Classifier | sklearn | `n_estimators=100`, `class_weight='balanced'` |
| 3 | XGBoost Classifier | xgboost | `objective='multi:softmax'`, `num_class=3`, `eval_metric='mlogloss'` |
| 4 | LightGBM Classifier | lightgbm | `objective='multiclass'`, `num_class=3`, `is_unbalance=True`, `verbosity=-1` |

> 각 모델을 Baseline 피처셋과 Enhanced 피처셋으로 **2회씩** 학습하여 비교

### 5.6 평가 지표

| 지표 | 용도 |
|------|------|
| **Accuracy** | 전체 정답률 |
| **Macro F1-Score** | 클래스 균등 가중 F1 |
| **Classification Report** | 클래스별 상세 Precision/Recall/F1 |
| **Confusion Matrix** | 클래스 간 혼동 패턴 |
| **성능 향상률** | `(Enhanced_F1 - Baseline_F1) / Baseline_F1 × 100%` |

---

## 6. ML 분석 파이프라인 (보강 반영)

### 6.1 분석 단계 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    전체 분석 흐름 (7단계)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STEP 1: 원본 데이터 EDA + 기본 전처리                        │
│  STEP 2: 보강 데이터 3종 탐색 및 분석                         │
│  STEP 3: 보강 파생변수 생성 (방식 A + B + C)                   │
│  STEP 4: Baseline 모델 학습 (원본 피처만)                     │
│  STEP 5: Enhanced 모델 학습 (원본 + 보강 피처)                │
│  STEP 6: 성능 비교 분석 (Baseline vs Enhanced)               │
│  STEP 7: 인사이트 도출 + Logistics 비교 분석                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 STEP별 상세 가이드

#### STEP 1 — 원본 데이터 EDA + 기본 전처리

- CSV 로드 (1,000행 × 37열), 인도네시아 로케일 전처리
- 기본 통계(shape, info, describe)
- Inventory_Status 분포 확인 (4클래스 불균형 → 3클래스 통합 검토)
- ABC_Class 분포 확인
- 수치형 피처별 Inventory_Status 분포 boxplot
- 카테고리별 Inventory_Status 분포 countplot
- 상관관계 히트맵 (수치형 피처 간)
- 기본 파생변수 생성 (Days_To_Expiry, Days_Since_Last_Order, Stock_Gap, Available_Stock)

#### STEP 2 — 보강 데이터 탐색 및 분석

```python
# ── ① Back Order Dataset 탐색 ──
df_bo = pd.read_csv('data/etc_subtopic1/Back Order Prediction Dataset/Training_BOP.csv')
print(f"Back Order 데이터 크기: {df_bo.shape}")
print(f"Backorder 비율:\n{df_bo['went_on_backorder'].value_counts(normalize=True)}")

# 핵심 변수 분포 확인
print("\n핵심 변수 기초 통계:")
print(df_bo[['national_inv', 'lead_time', 'perf_6_month_avg', 'perf_12_month_avg']].describe())

# ── ② Supply Chain Dataset 탐색 ──
df_sc = pd.read_csv('data/etc_subtopic1/supply_chain_data.csv')
print(f"\nSupply Chain 데이터 크기: {df_sc.shape}")

# 제품 유형별 핵심 통계
sc_stats = df_sc.groupby('Product type').agg({
    'Defect rates': 'mean',
    'Lead times': 'mean',
    'Shipping costs': 'mean'
}).round(2)
print("\n제품 유형별 평균 결함률·리드타임·배송비:")
print(sc_stats)

# ── ③ Dynamic Supply Chain Logistics Dataset 탐색 ──
df_logistics = pd.read_csv('data/etc_subtopic1/dynamic_supply_chain_logistics_dataset.csv')
print(f"\nLogistics 데이터 크기: {df_logistics.shape}")

# 리스크 등급별 핵심 통계
risk_stats = df_logistics.groupby('risk_classification').agg({
    'delay_probability': 'mean',
    'supplier_reliability_score': 'mean',
    'delivery_time_deviation': 'mean'
}).round(3)
print("\n리스크 등급별 지연 확률·공급자 신뢰도·배송 편차:")
print(risk_stats)
```

#### STEP 3 — 보강 파생변수 생성

- 섹션 4.3의 코드 실행
- 생성된 파생변수의 기초 통계 확인
- Inventory_Status별 보강 파생변수 분포 boxplot

```python
# 보강 파생변수의 Inventory_Status 분리력 확인
enhanced_vars = [
    'Supply_Lead_Gap', 'Demand_Supply_Ratio', 'Stock_Coverage_Days',
    'Reorder_Urgency', 'Quality_Risk_Score', 'Cost_Efficiency_Ratio'
]

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for i, var in enumerate(enhanced_vars):
    ax = axes[i // 3, i % 3]
    df.boxplot(column=var, by='Inventory_Status_3cls', ax=ax)
    ax.set_title(f'{var} by Status')
    ax.set_xlabel('')
plt.suptitle('보강 파생변수의 Inventory_Status별 분포', fontsize=14)
plt.tight_layout()
plt.savefig('outputs/figures/subtopic1_classification/enhanced_features_by_status.png',
            dpi=150, bbox_inches='tight')
plt.show()
```

#### STEP 4 — Baseline 모델 학습

- Baseline 피처셋(원본만)으로 4개 모델 학습
- 성능 기록: Accuracy, Macro F1
- 최적 모델의 Confusion Matrix 저장

#### STEP 5 — Enhanced 모델 학습

- Enhanced 피처셋(원본 + 보강)으로 동일 4개 모델 학습
- 성능 기록: Accuracy, Macro F1
- 최적 모델의 Confusion Matrix 저장

#### STEP 6 — 성능 비교 분석

```python
# Baseline vs Enhanced 비교 테이블
comparison = pd.DataFrame({
    '모델': ['LR', 'RF', 'XGB', 'LGBM'] * 2,
    '피처셋': ['Baseline'] * 4 + ['Enhanced'] * 4,
    'Accuracy': [lr_b_acc, rf_b_acc, xgb_b_acc, lgb_b_acc,
                 lr_e_acc, rf_e_acc, xgb_e_acc, lgb_e_acc],
    'Macro F1': [lr_b_f1, rf_b_f1, xgb_b_f1, lgb_b_f1,
                 lr_e_f1, rf_e_f1, xgb_e_f1, lgb_e_f1]
})

# 성능 향상률 계산
for model_name in ['LR', 'RF', 'XGB', 'LGBM']:
    base_f1 = comparison[(comparison['모델']==model_name) & (comparison['피처셋']=='Baseline')]['Macro F1'].values[0]
    enh_f1  = comparison[(comparison['모델']==model_name) & (comparison['피처셋']=='Enhanced')]['Macro F1'].values[0]
    improvement = (enh_f1 - base_f1) / base_f1 * 100 if base_f1 > 0 else 0
    print(f"{model_name}: F1 향상률 = {improvement:.1f}%")
```

```python
# 비교 시각화: 그룹형 바 차트
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for i, metric in enumerate(['Accuracy', 'Macro F1']):
    ax = axes[i]
    pivot = comparison.pivot(index='모델', columns='피처셋', values=metric)
    pivot[['Baseline', 'Enhanced']].plot(kind='bar', ax=ax, color=['#4A90D9', '#E74C3C'])
    ax.set_title(f'{metric} 비교: Baseline vs Enhanced')
    ax.set_ylabel(metric)
    ax.set_ylim(0, 1)
    ax.legend(title='피처셋')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

plt.tight_layout()
plt.savefig('outputs/figures/subtopic1_classification/baseline_vs_enhanced_comparison.png',
            dpi=150, bbox_inches='tight')
plt.show()
```

#### STEP 7 — 인사이트 도출 + Logistics 비교 분석

- Enhanced 최적 모델의 Feature Importance → 보강 피처의 기여도 확인
- Confusion Matrix 비교: 보강 전후 혼동 패턴 변화 (특히 In Stock ↔ Expiring Soon, In Stock ↔ Low Stock)
- Logistics 비교 분석: 물류 리스크와 Inventory_Status 간 관계가 두 데이터셋에서 유사한 패턴을 보이는지

---

## 7. 시각화 및 해석 요구사항

### 7.1 필수 시각화 목록 (보강 버전, 총 10종)

| # | 시각화 | 설명 | 파일명 |
|---|--------|------|--------|
| 1 | Inventory_Status 분포 바 차트 | 4클래스 불균형 확인 | `eda_status_distribution.png` |
| 2 | 수치형 피처별 Status boxplot | 원본 피처의 분리력 확인 | `eda_feature_boxplots.png` |
| 3 | 카테고리별 Status 분포 | countplot with hue | `eda_category_status.png` |
| 4 | **보강 파생변수별 Status boxplot** | 보강 피처의 분리력 확인 | `enhanced_features_by_status.png` |
| 5 | 상관관계 히트맵 (전체 피처) | 원본+보강 피처 간 상관 | `correlation_heatmap_full.png` |
| 6 | **Baseline vs Enhanced 성능 비교** | 그룹형 바 차트 | `baseline_vs_enhanced_comparison.png` |
| 7 | Confusion Matrix (Baseline 최적) | 보강 전 혼동 패턴 | `confusion_matrix_baseline.png` |
| 8 | **Confusion Matrix (Enhanced 최적)** | 보강 후 혼동 패턴 변화 | `confusion_matrix_enhanced.png` |
| 9 | **Feature Importance (Enhanced 최적)** | 보강 피처 기여도 확인 | `feature_importance_enhanced.png` |
| 10 | **Logistics 비교 분석 차트** | 물류 리스크 vs 재고 상태 교차 비교 | `dataco_comparison.png` |

> 모든 시각화는 `outputs/figures/subtopic1_classification/` 폴더에 저장

### 7.2 선택 시각화 (추가 분석)

- SHAP Summary Plot (Enhanced XGBoost/LightGBM 기준)
- Confusion Matrix 차이 히트맵 (Enhanced - Baseline)
- 보강 데이터 탐색 결과 (Supply Chain 통계, Back Order 분포, Logistics 리스크 분석)
- ROC Curve One-vs-Rest (Enhanced 모델 기준)
- ABC 등급별 분류 성능 차이 분석

---

## 8. 코드 구조 (보강 버전)

### 8.1 Jupyter Notebook 구조

```
01_Product_Status_Classification_Enhanced.ipynb
│
├── 0. 라이브러리 임포트 & 설정
│
├── 1. 데이터 로드 & 기본 확인
│   ├── 원본 데이터 로드 (1,000행 × 37열)
│   ├── 인도네시아 로케일 전처리
│   └── 기본 통계 확인
│
├── 2. 보강 데이터 탐색 ★ (신규 섹션)
│   ├── 2.1 ① Back Order Prediction Dataset 탐색
│   │   ├── 데이터 크기·구조 확인 (~168만행)
│   │   ├── went_on_backorder 분포 (극심한 불균형)
│   │   ├── 핵심 변수 분포 (national_inv, lead_time, perf_avg)
│   │   └── 주요 발견: 피처 설계에 참고할 변수 목록 정리
│   │
│   ├── 2.2 ② Supply Chain Dataset 탐색
│   │   ├── 데이터 크기·구조 확인 (100행)
│   │   ├── 제품 유형별 결함률·리드타임·배송비 통계
│   │   └── 주요 발견: 카테고리 매핑 근거 도출
│   │
│   └── 2.3 ③ Dynamic Supply Chain Logistics Dataset 탐색
│       ├── 데이터 크기·구조 확인 (~3.2만행)
│       ├── 리스크 등급별 지연 확률·공급자 신뢰도 분석
│       └── 주요 발견: 물류 리스크 플래그 설계 근거
│
├── 3. 데이터 전처리
│   ├── 3.1 공통 전처리 (로케일 변환, 금액, %, 날짜)
│   ├── 3.2 기본 파생변수 (Days_To_Expiry, Days_Since_Last_Order, Stock_Gap, Available_Stock)
│   ├── 3.3 보강 파생변수 — 방식 A (Back Order 참고) ★
│   ├── 3.4 보강 파생변수 — 방식 B (Supply Chain 매핑) ★
│   ├── 3.5 보강 파생변수 — 방식 C (Logistics 참고) ★
│   ├── 3.6 클래스 불균형 처리 (Out of Stock 병합)
│   └── 3.7 카테고리 인코딩 (One-Hot)
│
├── 4. EDA (탐색적 데이터 분석)
│   ├── 4.1 타겟 분포 시각화 (4클래스 불균형 → 3클래스 통합)
│   ├── 4.2 원본 피처별 Inventory_Status 분포 (boxplot)
│   ├── 4.3 보강 피처별 Inventory_Status 분포 (boxplot) ★
│   ├── 4.4 카테고리별 Inventory_Status 분포 (countplot)
│   ├── 4.5 ABC 등급별 Inventory_Status 분포
│   └── 4.6 전체 피처 상관관계 히트맵
│
├── 5. Baseline 모델 학습 (원본 피처만)
│   ├── 피처 선택 (Baseline 피처셋)
│   ├── Train/Test Split (80:20, stratify)
│   ├── StandardScaler 적용
│   ├── 4개 모델 학습 (LR, RF, XGB, LGBM)
│   └── 성능 기록 (Accuracy, Macro F1)
│
├── 6. Enhanced 모델 학습 (원본 + 보강 피처) ★
│   ├── 피처 선택 (Enhanced 피처셋)
│   ├── Train/Test Split (동일 random_state)
│   ├── StandardScaler 적용
│   ├── 4개 모델 학습 (LR, RF, XGB, LGBM)
│   └── 성능 기록 (Accuracy, Macro F1)
│
├── 7. 성능 비교 분석 ★ (핵심 섹션)
│   ├── 7.1 Baseline vs Enhanced 종합표
│   ├── 7.2 성능 향상률 계산
│   ├── 7.3 비교 바 차트
│   ├── 7.4 Confusion Matrix 비교 (보강 전후)
│   └── 7.5 Feature Importance (Enhanced 최적 모델)
│
├── 8. Logistics 비교 분석 ★
│   ├── Logistics Dataset 리스크 등급 vs 물류 지표 분석
│   ├── 원본 데이터 배송 지연 추정 vs Inventory_Status 분석
│   └── 두 데이터셋 간 패턴 비교 인사이트
│
└── 9. 결론 및 인사이트
    ├── 9.1 핵심 발견 사항 (보강 전후 비교 포함)
    ├── 9.2 보강 데이터 기여도 평가
    ├── 9.3 한계점 및 개선 방향
    └── 9.4 다른 소주제와의 연결점
```

### 8.2 코딩 컨벤션

- **언어:** Python 3.10+
- **필수 라이브러리:**
  ```
  pandas, numpy, matplotlib, seaborn,
  scikit-learn, xgboost, lightgbm, shap (선택)
  ```
- **한글 폰트 설정:**
  ```python
  import matplotlib.pyplot as plt
  plt.rcParams['font.family'] = 'AppleGothic'  # macOS
  plt.rcParams['axes.unicode_minus'] = False
  ```
- **시드 고정:** 모든 모델에 `random_state=42`
- **그래프 저장:** `plt.savefig('outputs/figures/subtopic1_classification/파일명.png', dpi=150, bbox_inches='tight')`

### 8.3 결과 테이블 출력 형식

```python
# Baseline vs Enhanced 종합 비교표
results = pd.DataFrame({
    '모델': ['LR', 'RF', 'XGB', 'LGBM'] * 2,
    '피처셋': ['Baseline'] * 4 + ['Enhanced'] * 4,
    'Accuracy': [...],
    'Macro F1': [...]
})

pivot = results.pivot_table(
    index='모델', columns='피처셋', values=['Accuracy', 'Macro F1']
)
pivot['F1 향상률(%)'] = (
    (pivot[('Macro F1', 'Enhanced')] - pivot[('Macro F1', 'Baseline')])
    / pivot[('Macro F1', 'Baseline')] * 100
).round(1)

display(pivot)
```

---

## 9. 핵심 유의사항

### 9.1 데이터 관련

- **인도네시아 로케일 형식:** 쉼표(`,`)가 소수점, 금액은 `$2.084,25` 형식 → 반드시 전처리
- **클래스 불균형:** Out of Stock 2건(0.2%) → 3클래스 통합이 현실적
- 데이터가 1,000행으로 **소규모**이므로 과적합에 주의
- Back Order Dataset(~168만행)은 **전체를 로드할 필요 없음** — 구조 탐색 및 통계 확인 후 피처 설계 근거만 활용
- Logistics Dataset(~3.2만행)도 마찬가지로 전체 모델링이 아닌 **비교 분석 목적**으로만 사용

### 9.2 보강 데이터 관련

- 보강 데이터 3종은 원본과 **제품 ID 매칭이 불가**하므로, 직접 JOIN/MERGE가 아닌 **피처 설계 프레임워크·통계 매핑·비교 분석** 방식으로 활용
- 방식 B(카테고리 매핑)의 시뮬레이션 값은 **도메인 가정**에 기반하므로, 매핑 근거를 노트북에 명시적으로 문서화해야 함
- 카테고리 매핑 시 원본은 **10개 카테고리**(식료품 중심)인 반면, Supply Chain Dataset은 **3개 유형**(skincare/haircare/cosmetics)이므로 직접 대응이 아닌 유사 속성 기반 추정 매핑

### 9.3 모델링 관련

- Baseline vs Enhanced **동일 분할**(random_state=42, stratify=y)로 공정 비교
- 보강 피처가 12개 추가되므로, **과적합 리스크 증가** → 교차검증(5-fold) 권장
- Enhanced에서 성능이 오히려 떨어지면 → 불필요한 피처가 노이즈를 추가한 것. 이 경우 **피처 선택(Feature Selection)** 수행
- 카테고리 매핑 기반 피처(Est_Defect_Rate 등)는 같은 카테고리 내 분산이 0이므로 → 다른 피처와의 **상호작용 효과**로만 기여 가능

### 9.4 해석 관련

- **Feature Importance에서 보강 피처가 상위에 오르는지**가 핵심 분석 포인트
- 보강 전후 Confusion Matrix를 나란히 비교하여, **어떤 클래스 간 혼동이 줄었는지** 구체적으로 분석
- 성능 향상이 미미하더라도, "Inventory_Status가 데이터에 포함된 변수 외의 요인(경영 판단, 시장 변화)에 의해 결정됨을 보강 데이터로 한번 더 확인"이라는 인사이트로 해석
- Logistics 비교 분석에서 "두 데이터셋 모두 물류 리스크가 재고 상태에 유의미한 영향"이 확인되면 → 물류 관리의 중요성 강조

### 9.5 다른 소주제와의 연결

- 소주제 1에서 생성한 **보강 파생변수 일부**(Supply_Lead_Gap, Demand_Supply_Ratio, Stock_Coverage_Days 등)를 소주제 3·4에서도 피처로 활용 가능
- Feature Importance 결과에서 보강 피처가 중요하면 → 소주제 4 클러스터링 피처에 추가 검토
- 소주제 1에서 파악한 **Expiring Soon 제품의 특성** → 소주제 3 폐기 위험과의 연관성 검증
- 소주제 1 결과를 README.md 3.1절에 기입 (Baseline/Enhanced 성능 모두 기재)

---

## 10. 기대 산출물 체크리스트

### 보강 데이터 탐색 산출물
- [ ] 보강 데이터 ① Back Order Prediction Dataset 탐색 결과 요약
- [ ] 보강 데이터 ② Supply Chain Dataset 카테고리별 통계표
- [ ] 보강 데이터 ③ Dynamic Supply Chain Logistics Dataset 리스크 분석 결과

### 분석 산출물
- [ ] `01_Product_Status_Classification_Enhanced.ipynb` — 전체 분석 노트북
- [ ] `outputs/figures/subtopic1_classification/eda_status_distribution.png`
- [ ] `outputs/figures/subtopic1_classification/eda_feature_boxplots.png`
- [ ] `outputs/figures/subtopic1_classification/eda_category_status.png`
- [ ] `outputs/figures/subtopic1_classification/enhanced_features_by_status.png` ★
- [ ] `outputs/figures/subtopic1_classification/correlation_heatmap_full.png`
- [ ] `outputs/figures/subtopic1_classification/baseline_vs_enhanced_comparison.png` ★
- [ ] `outputs/figures/subtopic1_classification/confusion_matrix_baseline.png`
- [ ] `outputs/figures/subtopic1_classification/confusion_matrix_enhanced.png` ★
- [ ] `outputs/figures/subtopic1_classification/feature_importance_enhanced.png` ★
- [ ] `outputs/figures/subtopic1_classification/dataco_comparison.png` ★
- [ ] `outputs/models/best_model_baseline.pkl`
- [ ] `outputs/models/best_model_enhanced.pkl`
- [ ] `outputs/models/scaler_enhanced.pkl`
- [ ] `outputs/models/label_encoder_enhanced.pkl`

### 결과 산출물
- [ ] Baseline vs Enhanced 성능 비교표 (Accuracy, Macro F1, 향상률)
- [ ] Feature Importance 상위 15개 피처 (보강 피처 기여도 표시)
- [ ] 핵심 인사이트 5~7개 (보강 전후 비교 포함)

---

## 부록 A: 보강 데이터 파일 배치

### 파일 배치 구조

```
📦 Phase8_mini/
├── data/
│   ├── Supply Chain Inventory Management Grocery Industry/
│   │   └── Inventory Management E-Grocery - InventoryData.csv  ← 원본 (메인)
│   └── etc_subtopic1/                                          ← 보강 데이터 폴더
│       ├── Back Order Prediction Dataset/
│       │   ├── Training_BOP.csv                                ← ① Back Order (학습용)
│       │   └── Testing_BOP.csv                                 ← ① Back Order (테스트용)
│       ├── supply_chain_data.csv                               ← ② Supply Chain
│       └── dynamic_supply_chain_logistics_dataset.csv          ← ③ Logistics
```

---

## 부록 B: 전체 파이프라인 요약 흐름도

```
원본 CSV 로드 (1,000행 × 37열)
  ↓
인도네시아 로케일 전처리 (쉼표 소수점, 금액, 퍼센트)
  ↓
보강 데이터 3종 탐색 (별도 셀)
  ├── ① Back Order: 피처 구조 분석 → 파생변수 설계 근거
  ├── ② Supply Chain: 카테고리별 통계 → 매핑 테이블 생성
  └── ③ Logistics: 물류 리스크 분석 → 지연 플래그 설계 근거
  ↓
기본 파생변수 생성 (Days_To_Expiry, Days_Since_Last_Order, Stock_Gap, Available_Stock)
  ↓
보강 파생변수 생성 (12개 추가)
  ├── 방식 A: Supply_Lead_Gap, Demand_Supply_Ratio, Stock_Coverage_Days, ...
  ├── 방식 B: Est_Defect_Rate, Est_Lead_Time, Quality_Risk_Score, ...
  └── 방식 C: Delivery_Delay_Flag
  ↓
클래스 불균형 처리 (Out of Stock → Low Stock 병합 → 3클래스)
  ↓
EDA (원본 + 보강 피처 분포 확인, 카테고리·ABC별 분석)
  ↓
피처셋 분리: Baseline (14개+인코딩) vs Enhanced (26개+인코딩)
  ↓
동일 조건 Train/Test Split (80:20, stratify, seed=42)
  ↓
Baseline 학습 (4모델) → 성능 기록
  ↓
Enhanced 학습 (4모델) → 성능 기록
  ↓
★ 성능 비교 분석 (핵심) ★
  ├── 비교표 + 향상률 계산
  ├── Confusion Matrix 비교 (보강 전후)
  └── Feature Importance (보강 피처 기여도)
  ↓
Logistics 비교 분석 (독립 섹션)
  ↓
인사이트 도출 & 결론
```
