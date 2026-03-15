# 소주제 3 — 폐기 위험도 예측 (Binary Classification) 구현 가이드 [보강 데이터 통합 버전]

> **[v2.0]** 원본 데이터의 한계를 보완하기 위해 3종의 Kaggle 보강 데이터를 통합한 확장 버전입니다.

---

## 1. 프로젝트 컨텍스트

### 1.1 대주제

**머신러닝 기반 식료품 유통 재고 관리 최적화 시스템**

- 팀명: 굿핏(good fit) | KNU KDT 12기
- 데이터: Kaggle - Inventory Management E-Grocery (1,000행 × 37열) + 보강 데이터 3종
- 소주제 3 담당: 권효중

### 1.2 소주제 3 목표

유통기한 내 재고 소진이 가능한지 여부를 판별하는 **이진 분류 모델**을 구축하여, **폐기 위험 제품을 사전에 식별**한다. 타겟 변수(Waste_Risk)는 원본 데이터에 존재하지 않으며, 도메인 지식 기반의 **Feature Engineering으로 직접 생성**하는 것이 이 소주제의 핵심 차별점이다.

### 1.3 보강 데이터 도입 배경

원본 데이터에는 **카테고리별 유통기한 기준, 식품 소비 패턴, 보관 조건별 차이, 음식 폐기량 결정 요인, 글로벌 폐기 벤치마크** 등이 부재하여, 타겟 변수 생성의 현실성과 분석 맥락의 깊이에 한계가 있다.

| 보강 목적 | 한계점 | 보강 데이터 |
|-----------|--------|------------|
| 식품 유통기한·소비 패턴 분석 프레임워크 | 카테고리별 유통기한 기준 데이터 부재 | ① Food Expiry Tracker |
| 음식 폐기량 결정 요인 다각화 | 이벤트·보관·계절·가격 등 폐기 요인 부재 | ② Food Wastage Data |
| 글로벌 식품 폐기 벤치마크 제공 | 프로젝트 배경의 수치적 근거 부재 | ③ Global Food Wastage Dataset |

> **참고:** `fruit and vegetable dataset for Shelf life/` 폴더도 `data/etc_subtopic3/` 내에 존재하나, 이는 **이미지 분류용 데이터셋**(폴더별 .jpg 파일)이므로 본 분석(정형 데이터 기반)에서는 직접 활용하지 않는다. 다만, 과일·채소의 품질 등급 체계(1~5점, 5~10일, 10~15일 등)를 **유통기한 세분화의 도메인 지식 근거**로 참고할 수 있다.

### 1.4 도출할 인사이트 (확장)

**[기존]**
- 유통기한 내 재고 소진이 불가능한 "폐기 위험" 제품을 사전에 식별할 수 있는가?
- 폐기 위험 제품의 공통 특성은 무엇인가? (카테고리, ABC 등급, 가격대, 재고량, FIFO/FEFO 방식 등)
- 실무적으로 Recall(재현율)이 왜 Precision보다 중요한가?
- 파손(Damaged_Qty) 및 반품(Returns_Qty)이 폐기 위험에 어떤 영향을 미치는가?

**[보강 데이터 추가]**
- 카테고리별 차등 유통기한 가중치를 적용하면 Waste_Risk 타겟이 더 현실적으로 변하는가?
- 보강 전후 모델 성능 비교를 통해, 도메인 지식 기반 피처가 분류에 얼마나 기여하는가?
- 글로벌 식품 폐기 통계와 비교했을 때, 본 데이터의 폐기 위험 패턴이 현실적인가?
- 음식 폐기량에 영향을 미치는 주요 요인(보관 조건, 계절, 가격 등)의 일반적 경향은 어떠한가?

---

## 2. 데이터 명세

### 2.1 원본 데이터 (메인)

- **파일:** `Inventory_Management_E-Grocery_-_InventoryData.csv`
- **출처:** [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/)
- **규모:** 1,000행 × 37열
- **타겟:** Waste_Risk (파생 — `Days_To_Deplete > Remaining_Shelf_Days → 1`)
- **결측치:** Notes 컬럼 834건 (분석 미사용 컬럼), 실질적 결측치 이슈 없음

> 원본 데이터 전체 컬럼 명세는 `subtopic3_guideline.md` (Baseline 버전) 섹션 2.2 참조

---

### 2.2 보강 데이터 ① — Food Expiry Tracker

| 항목 | 내용 |
|------|------|
| **출처** | [Kaggle - Food Expiry Tracker](https://www.kaggle.com/datasets/prekshad2166/food-expiry-tracker) |
| **파일 경로** | `data/etc_subtopic3/food_expiry_tracker.csv` |
| **규모** | 500행 × 15열 |
| **설명** | 가정 내 식품별 구매·소비·유통기한 추적 데이터 (전처리 완료: 정규화 + One-Hot 인코딩 상태) |

#### 왜 추가해야 하는가?

현재 Waste_Risk 타겟 생성에서 모든 카테고리에 동일한 `Avg_Daily_Sales` 기준을 적용하고 있다. 그러나 현실에서 Seafood는 3~5일, Dairy는 7~14일, Pantry(곡류 등)는 180일 이상의 유통기한을 가진다. Food Expiry Tracker는 **식품 유형별 유통기한 패턴과 보관 조건별 차이, 유통기한 내 소비 성공률**을 제공하여, 카테고리별 차등 기준의 도메인 근거를 확보할 수 있다.

#### 주요 컬럼 (실제 파일 형식)

> ⚠️ **주의:** 이 데이터는 이미 **정규화(Min-Max) + One-Hot 인코딩이 적용된 상태**로 제공된다. 원시 카테고리명이나 날짜가 아닌, 수치형/이진형 값이다.

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | purchase_month | float (0~1) | 구매 월 (정규화) | ✅ 계절성 패턴 참고 |
| 2 | purchase_day_of_week | float (0~1) | 구매 요일 (정규화) | ✅ 요일별 패턴 참고 |
| 3 | days_until_expiry | float (0~1) | 유통기한까지 남은 일수 (정규화) | ✅ **핵심 — 유통기한 분포** |
| 4 | quantity | float (0~1) | 구매 수량 (정규화) | ✅ 구매량 패턴 |
| 5 | used_before_expiry | int (0/1) | 유통기한 내 소비 여부 | ✅ **핵심 — 폐기율 참고** |
| 6~12 | item_beverage ~ item_vegetable | bool | 식품 유형 One-Hot (7종) | ✅ **핵심 — 카테고리 매핑** |
| 13~15 | storage_freezer/fridge/pantry | bool | 보관 조건 One-Hot (3종) | ✅ **핵심 — 보관 조건별 차이** |

**식품 유형 One-Hot 컬럼 (7종):**
- `item_beverage`, `item_dairy`, `item_fruit`, `item_grain`, `item_meat`, `item_snack`, `item_vegetable`

**보관 조건 One-Hot 컬럼 (3종):**
- `storage_freezer`, `storage_fridge`, `storage_pantry`

#### 활용 방식: 식품 유형별 유통기한 통계 + 소비 성공률 + 보관 조건별 차이 분석

```python
import pandas as pd
import numpy as np

df_fet = pd.read_csv('data/etc_subtopic3/food_expiry_tracker.csv')

# One-Hot → 원래 카테고리 역변환
item_cols = [c for c in df_fet.columns if c.startswith('item_')]
df_fet['food_type'] = df_fet[item_cols].idxmax(axis=1).str.replace('item_', '')

storage_cols = [c for c in df_fet.columns if c.startswith('storage_')]
df_fet['storage_type'] = df_fet[storage_cols].idxmax(axis=1).str.replace('storage_', '')

# 1. 식품 유형별 유통기한(정규화) 분포
shelf_by_type = df_fet.groupby('food_type')['days_until_expiry'].agg(['mean', 'median', 'std'])
print("식품 유형별 유통기한 분포 (정규화):")
print(shelf_by_type)

# 2. 유통기한 내 소비 성공률
consume_rate = df_fet.groupby('food_type')['used_before_expiry'].mean()
print("\n식품 유형별 유통기한 내 소비 성공률:")
print(consume_rate)

# 3. 보관 조건별 유통기한 차이
shelf_by_storage = df_fet.groupby(['food_type', 'storage_type'])['days_until_expiry'].mean()
print("\n보관 조건별 유통기한:")
print(shelf_by_storage)
```

> **해석 유의사항:** `days_until_expiry`가 정규화(0~1)되어 있으므로, 절대적 일수가 아닌 **상대적 비율과 유형 간 차이**에 초점을 맞춰 분석한다. 실제 유통기한 일수는 도메인 지식으로 보완한다.

---

### 2.3 보강 데이터 ② — Food Wastage Data (레스토랑 음식 폐기 데이터)

| 항목 | 내용 |
|------|------|
| **출처** | [Kaggle - Food Wastage Data](https://www.kaggle.com/) |
| **파일 경로** | `data/etc_subtopic3/food_wastage_data.csv` |
| **규모** | 1,782행 × 11열 |
| **설명** | 레스토랑·이벤트 환경에서 음식 유형별 폐기량과 관련 요인 데이터 |

#### 왜 추가해야 하는가?

원본 데이터는 재고 관점에서만 폐기 위험을 산출하지만, 실제 음식 폐기에는 **보관 조건, 계절성, 조리 방법, 가격, 이벤트 유형** 등 다양한 요인이 관여한다. 이 데이터는 음식 폐기량에 영향을 미치는 **다차원적 요인 분석 프레임워크**를 제공하여, 원본 데이터의 폐기 위험 예측에 도메인 지식을 보강한다.

#### 주요 컬럼 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | **Type of Food** | object | 음식 유형 (Meat, Dairy 등) | ✅ **핵심 — 카테고리 매핑** |
| 2 | **Number of Guests** | int | 손님 수 | ⬜ 참고 (규모 요인) |
| 3 | **Event Type** | object | 이벤트 유형 (Corporate, Birthday 등) | ⬜ 참고 |
| 4 | **Quantity of Food** | int | 음식 수량 | ✅ 폐기량 대비 비율 분석 |
| 5 | **Storage Conditions** | object | 보관 조건 (Refrigerated, Room Temperature) | ✅ **핵심 — 보관 조건별 폐기량** |
| 6 | **Purchase History** | object | 구매 이력 (Regular, Occasional) | ⬜ 참고 |
| 7 | **Seasonality** | object | 계절 (Spring/Summer/Fall/Winter/All) | ✅ **핵심 — 계절별 폐기 패턴** |
| 8 | **Preparation Method** | object | 조리 방법 (Buffet, Plated 등) | ⬜ 참고 |
| 9 | **Geographical Location** | object | 지역 (Urban, Suburban, Rural) | ⬜ 참고 |
| 10 | **Pricing** | object | 가격대 (Low, Medium, High) | ✅ **핵심 — 가격과 폐기 관계** |
| 11 | **Wastage Food Amount** | int | 음식 폐기량 | ✅ **핵심 — 타겟 변수** |

#### 활용 방식: 음식 유형별·보관 조건별·계절별 폐기 패턴 분석 → 도메인 파생변수 근거

```python
df_fw = pd.read_csv('data/etc_subtopic3/food_wastage_data.csv')

# 1. 음식 유형별 평균 폐기량
waste_by_type = df_fw.groupby('Type of Food')['Wastage Food Amount'].agg(['mean', 'median', 'std'])
print("음식 유형별 폐기량:")
print(waste_by_type.sort_values('mean', ascending=False))

# 2. 보관 조건별 폐기량 차이
waste_by_storage = df_fw.groupby('Storage Conditions')['Wastage Food Amount'].mean()
print("\n보관 조건별 평균 폐기량:")
print(waste_by_storage)

# 3. 계절별 폐기 패턴
waste_by_season = df_fw.groupby('Seasonality')['Wastage Food Amount'].mean()
print("\n계절별 평균 폐기량:")
print(waste_by_season)

# 4. 가격대별 폐기량 (가격과 폐기의 관계)
waste_by_price = df_fw.groupby('Pricing')['Wastage Food Amount'].mean()
print("\n가격대별 평균 폐기량:")
print(waste_by_price)

# 5. 폐기 비율 = 폐기량 / 전체 음식량
df_fw['Wastage_Ratio'] = df_fw['Wastage Food Amount'] / df_fw['Quantity of Food']
waste_ratio_by_type = df_fw.groupby('Type of Food')['Wastage_Ratio'].mean()
print("\n음식 유형별 평균 폐기 비율:")
print(waste_ratio_by_type.sort_values(ascending=False))
```

---

### 2.4 보강 데이터 ③ — Global Food Wastage Dataset (2018-2024)

| 항목 | 내용 |
|------|------|
| **출처** | [Kaggle - Global Food Wastage](https://www.kaggle.com/datasets/atharvasoundankar/global-food-wastage-dataset-2018-2024) |
| **파일 경로** | `data/etc_subtopic3/global_food_wastage_dataset.csv` |
| **규모** | 5,000행 × 8열 |
| **설명** | 20개국, 7년간, 8개 식품 카테고리의 음식물 낭비 데이터 |

#### 왜 추가해야 하는가?

프로젝트의 배경·문제 인식 섹션에서 **"전 세계적으로 식품 폐기가 얼마나 심각한 문제인가"**를 수치로 뒷받침할 근거가 필요하다. 또한, 카테고리별 글로벌 폐기 비율을 비교하여 소주제 3 결과의 현실성을 외부 벤치마크로 검증할 수 있다.

#### 주요 컬럼 및 활용 계획

| # | 컬럼명 | 타입 | 설명 | 활용 방식 |
|---|--------|------|------|-----------|
| 1 | **Country** | object | 국가 | ✅ 한국/인도네시아 필터링 |
| 2 | **Year** | int | 연도 (2018~2024) | ✅ 트렌드 분석 |
| 3 | **Food Category** | object | 식품 카테고리 (8종) | ✅ **핵심 — Category 대응 비교** |
| 4 | **Total Waste (Tons)** | float | 총 폐기량 (톤) | ✅ **핵심 — 카테고리별 폐기 규모** |
| 5 | **Economic Loss (Million $)** | float | 경제적 손실 | ✅ **배경 섹션 근거** |
| 6 | **Avg Waste per Capita (Kg)** | float | 1인당 평균 폐기량 | ✅ 참고 |
| 7 | **Population (Million)** | float | 인구 | ⬜ 참고 |
| 8 | **Household Waste (%)** | float | 가정 폐기 비율 | ✅ 참고 |

#### 활용 방식: 프로젝트 배경 근거 + 결과 벤치마크 + 카테고리별 폐기 위험 가중치

```python
df_gfw = pd.read_csv('data/etc_subtopic3/global_food_wastage_dataset.csv')

# 1. 전체 현황: 카테고리별 글로벌 폐기 규모
cat_waste = df_gfw.groupby('Food Category')['Total Waste (Tons)'].sum().sort_values(ascending=False)
print("글로벌 카테고리별 총 폐기량 (톤):")
print(cat_waste)

# 2. 연도별 트렌드
yearly = df_gfw.groupby('Year')['Total Waste (Tons)'].sum()
print("\n연도별 글로벌 식품 폐기량 추이:")
print(yearly)

# 3. 경제적 손실 규모 (프로젝트 배경 근거)
total_loss = df_gfw['Economic Loss (Million $)'].sum()
print(f"\n글로벌 총 경제적 손실: ${total_loss:,.0f}M")

# 4. 카테고리별 1인당 폐기량 (비율 비교에 유용)
per_capita = df_gfw.groupby('Food Category')['Avg Waste per Capita (Kg)'].mean()
print("\n카테고리별 1인당 평균 폐기량:")
print(per_capita.sort_values(ascending=False))
```

---

### 2.5 참고 데이터 — Fruit & Vegetable Dataset for Shelf Life (이미지)

| 항목 | 내용 |
|------|------|
| **파일 경로** | `data/etc_subtopic3/fruit and vegetable dataset for Shelf life/` |
| **형식** | 이미지 데이터셋 (폴더별 .jpg 파일) |
| **구조** | `Apple(1-5)/`, `Banana(5-10)/`, `Tomato(10-15)/`, `Expired/` 등 폴더로 구분 |

> **직접 활용 불가:** 정형 데이터(CSV/테이블) 기반 분석이므로 이미지 데이터를 직접 피처로 사용하지 않는다.

> **간접 활용:** 폴더명에 포함된 유통기한 범위(예: `Apple(1-5)` = 유통기한 1~5일차, `Banana(10-15)` = 10~15일차)를 **과일·채소 품목별 유통기한의 도메인 참고 자료**로 활용한다. `Expired` 폴더는 유통기한 초과 상태를 나타낸다.

```python
# 이미지 데이터 구조 확인 (탐색 목적)
import os

shelf_life_dir = 'data/etc_subtopic3/fruit and vegetable dataset for Shelf life/'
folders = sorted(os.listdir(shelf_life_dir))
print("Shelf Life 이미지 데이터셋 폴더 구조:")
for f in folders:
    if os.path.isdir(os.path.join(shelf_life_dir, f)):
        n_images = len(os.listdir(os.path.join(shelf_life_dir, f)))
        print(f"  {f}: {n_images}장")

# 도메인 참고: 폴더명에서 유통기한 범위 추출
# Apple(1-5) → 사과 유통기한 1~5일차 품질 상태
# Banana(10-15) → 바나나 유통기한 10~15일차 품질 상태
# Expired → 유통기한 초과 상태
```

---

## 3. 보강 데이터 통합 전략

### 3.1 통합 방식 개요

```
┌──────────────────────────────────────────────────────────────────┐
│                    보강 데이터 통합 3가지 방식                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  방식 A: 도메인 기반 Waste_Risk 타겟 정밀화                         │
│  → Food Expiry Tracker의 식품별 유통기한 패턴으로 타겟 재설계         │
│  → 주 활용: ① Food Expiry Tracker                                │
│                                                                  │
│  방식 B: 카테고리별 폐기 위험 가중치 매핑                            │
│  → Food Wastage + Global Wastage 통계로 카테고리별 가중치 부여       │
│  → 주 활용: ② Food Wastage Data + ③ Global Wastage               │
│                                                                  │
│  방식 C: 글로벌 벤치마크 비교 분석                                   │
│  → Global Wastage 데이터를 독립 분석하여 원본 결과의 현실성 검증       │
│  → 주 활용: ③ Global Food Wastage Dataset                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 방식 A — Waste_Risk 타겟 정밀화 (① Food Expiry Tracker 활용)

#### Step 1: Food Expiry Tracker에서 식품 유형별 유통기한 통계 추출

```python
df_fet = pd.read_csv('data/etc_subtopic3/food_expiry_tracker.csv')

# One-Hot → 원래 카테고리 역변환
item_cols = [c for c in df_fet.columns if c.startswith('item_')]
df_fet['food_type'] = df_fet[item_cols].idxmax(axis=1).str.replace('item_', '')

storage_cols = [c for c in df_fet.columns if c.startswith('storage_')]
df_fet['storage_type'] = df_fet[storage_cols].idxmax(axis=1).str.replace('storage_', '')

# 유형별 유통기한 분포 (정규화 값 — 상대적 비교용)
shelf_by_type = df_fet.groupby('food_type')['days_until_expiry'].agg(['mean', 'median', 'std'])
print("식품 유형별 유통기한 분포 (정규화 기준):")
print(shelf_by_type.sort_values('mean'))

# 유통기한 내 소비 성공률 (1이면 유통기한 내 소비)
consume_rate = df_fet.groupby('food_type')['used_before_expiry'].mean()
print("\n식품 유형별 유통기한 내 소비 성공률:")
print(consume_rate.sort_values())

# 보관 조건별 차이
shelf_by_storage = df_fet.groupby(['food_type', 'storage_type'])['days_until_expiry'].mean()
print("\n보관 조건별 유통기한:")
print(shelf_by_storage.unstack())
```

> **해석 방법:** `days_until_expiry`가 정규화(0~1)되어 있으므로, 유형 간의 **상대적 크기 관계**를 활용한다. 예를 들어 meat의 정규화 평균이 0.1이고 grain이 0.8이면, grain이 상대적으로 유통기한이 훨씬 길다는 도메인 근거로 활용한다.

#### Step 2: 카테고리 매핑 및 차등 판매 기간 설정

```python
# Food Expiry Tracker의 7개 식품 유형 → E-Grocery의 10개 Category 매핑
# (분석 결과 + 도메인 지식 결합)
expiry_to_egrocery = {
    'meat':      ['Meat', 'Seafood'],       # 육류·해산물: 유통기한 짧음
    'dairy':     ['Dairy'],                  # 유제품
    'fruit':     ['Fresh Produce'],          # 과일·채소 → Fresh Produce
    'vegetable': ['Fresh Produce'],          # 과일·채소 → Fresh Produce
    'grain':     ['Bakery', 'Pantry'],       # 곡류 → 제과·식료품
    'beverage':  ['Beverages'],              # 음료
    'snack':     ['Frozen', 'Household', 'Personal Care'],  # 간식·기타
}

# 카테고리별 유통기한 특성에 기반한 차등 판매 기간 설정
# (Food Expiry Tracker 분석 결과 + Shelf Life 이미지 데이터 도메인 참고)
category_sales_period = {
    'Seafood':        7,    # 유통기한 매우 짧음 — 주단위 판매
    'Fresh Produce':  10,   # 신선식품 — 10일 사이클
    'Dairy':          14,   # 유제품 — 2주 사이클
    'Bakery':         7,    # 제과 — 주단위 판매
    'Meat':           10,   # 육류 — 10일 사이클
    'Frozen':         60,   # 냉동식품 — 장기
    'Beverages':      60,   # 음료 — 장기
    'Pantry':         90,   # 식료품(곡류 등) — 매우 긴 유통기한
    'Household':      180,  # 생활용품 — 비식품
    'Personal Care':  180,  # 개인위생 — 비식품
}
```

> **매핑 근거 문서화 필수:** 각 `category_sales_period` 값이 왜 해당 수치인지를 노트북에 명시. Food Expiry Tracker의 정규화된 유통기한 비율, Shelf Life 이미지 데이터의 폴더 구조(예: Apple(1-5) = 5일 이내), 일반적 도메인 지식을 결합하여 근거를 제시한다.

#### Step 3: Enhanced 타겟 생성

```python
# Enhanced 타겟 생성 (카테고리별 차등 판매 기간 기반)
df['Sales_Period'] = df['Category'].map(category_sales_period)

# Enhanced Daily Sales Estimation:
# Avg_Daily_Sales를 직접 사용하되, 카테고리별 판매 기간으로 조정
# → 실제 소진 일수 = 보유 재고 / 일일 판매량 (Baseline과 동일)
# → 하지만 유통기한 잔여일에 카테고리별 가중치를 적용하여 폐기 위험 기준을 차등화

# 방법: 카테고리별 유통기한 효율성 가중치
# 판매 기간이 짧은 카테고리는 Remaining_Shelf_Days가 같아도 "더 위험"
df['Adjusted_Remaining_Days'] = df['Remaining_Shelf_Days'] * (df['Sales_Period'] / 30)

# Enhanced Waste Risk: 가중 잔여일 기준
df['Waste_Risk_Enhanced'] = (df['Days_To_Deplete'] > df['Adjusted_Remaining_Days']).astype(int)
```

> ⚠️ **2종류의 타겟 비교:** 기존(균일 기준) Waste_Risk와 보강(카테고리 차등) Waste_Risk_Enhanced를 모두 생성하여 **분포 차이 및 모델 성능 차이를 비교 분석**한다.

### 3.3 방식 B — 카테고리별 폐기 위험 가중치 매핑 (② + ③ 활용)

Food Wastage Data + Global Wastage 통계를 결합하여 파생변수를 생성한다.

```python
# ── Food Wastage Data에서 음식 유형별 폐기 통계 추출 ──
df_fw = pd.read_csv('data/etc_subtopic3/food_wastage_data.csv')

# 폐기 비율 계산
df_fw['Wastage_Ratio'] = df_fw['Wastage Food Amount'] / df_fw['Quantity of Food']
fw_stats = df_fw.groupby('Type of Food').agg(
    avg_wastage=('Wastage Food Amount', 'mean'),
    avg_wastage_ratio=('Wastage_Ratio', 'mean')
)
print("음식 유형별 폐기 통계:")
print(fw_stats)

# ── Global Wastage에서 카테고리별 통계 추출 ──
df_gfw = pd.read_csv('data/etc_subtopic3/global_food_wastage_dataset.csv')

gfw_stats = df_gfw.groupby('Food Category').agg(
    total_waste=('Total Waste (Tons)', 'sum'),
    avg_per_capita=('Avg Waste per Capita (Kg)', 'mean'),
    avg_household_pct=('Household Waste (%)', 'mean')
)
print("\n글로벌 카테고리별 폐기 통계:")
print(gfw_stats.sort_values('total_waste', ascending=False))
```

```python
# ── 카테고리별 종합 폐기 위험 프로파일 ──
# Food Wastage Data + Global Wastage + Shelf Life 도메인 지식 결합
category_waste_profile = {
    # (추정 평균 유통기한(일), 글로벌 폐기 비중, 부패 위험도 1~5)
    'Seafood':        {'avg_shelf_life': 5,   'perishability': 5},
    'Fresh Produce':  {'avg_shelf_life': 10,  'perishability': 4},
    'Dairy':          {'avg_shelf_life': 14,  'perishability': 4},
    'Meat':           {'avg_shelf_life': 10,  'perishability': 4},
    'Bakery':         {'avg_shelf_life': 5,   'perishability': 3},
    'Frozen':         {'avg_shelf_life': 90,  'perishability': 2},
    'Beverages':      {'avg_shelf_life': 180, 'perishability': 1},
    'Pantry':         {'avg_shelf_life': 365, 'perishability': 1},
    'Household':      {'avg_shelf_life': 730, 'perishability': 0},
    'Personal Care':  {'avg_shelf_life': 730, 'perishability': 0},
}

for col, key in [('Avg_Shelf_Life', 'avg_shelf_life'),
                 ('Perishability_Score', 'perishability')]:
    df[col] = df['Category'].map({c: v[key] for c, v in category_waste_profile.items()})

# 복합 파생변수
# 1. 유통기한 잔여율: 실제 유통기한 잔여일 / 카테고리 평균 유통기한
df['Shelf_Life_Ratio'] = df['Remaining_Shelf_Days'] / df['Avg_Shelf_Life']

# 2. 폐기 위험 복합 점수: 부패도 × (재고/일일판매) 비율
df['Waste_Risk_Score'] = df['Perishability_Score'] * (
    df['Quantity_On_Hand'] / df['Avg_Daily_Sales'].replace(0, 1)
)

# 3. 카테고리 조정 재고 커버리지: Days_of_Inventory / 카테고리 평균 유통기한
df['Adjusted_Coverage'] = df['Days_of_Inventory'] / df['Avg_Shelf_Life']
```

### 3.4 방식 C — 글로벌 벤치마크 비교 분석

```python
# Global Food Wastage Dataset 독립 분석 (별도 섹션)
df_gfw = pd.read_csv('data/etc_subtopic3/global_food_wastage_dataset.csv')

# 1. 전체 현황: 카테고리별 글로벌 폐기 규모
cat_waste = df_gfw.groupby('Food Category')['Total Waste (Tons)'].sum().sort_values(ascending=False)
print("글로벌 카테고리별 총 폐기량 (톤):")
print(cat_waste)

# 2. 연도별 트렌드
yearly = df_gfw.groupby('Year')['Total Waste (Tons)'].sum()
print("\n연도별 글로벌 식품 폐기량 추이:")
print(yearly)

# 3. 경제적 손실 규모 (프로젝트 배경 근거)
total_loss = df_gfw['Economic Loss (Million $)'].sum()
print(f"\n글로벌 총 경제적 손실: ${total_loss:,.0f}M")

# 4. 원본 데이터 결과와 비교
# → 원본에서 Risk 비율이 높은 카테고리 vs 글로벌에서 폐기가 많은 카테고리 비교

# 5. Food Wastage Data와의 크로스 참조
# → 레스토랑 환경의 폐기 패턴 vs 글로벌 통계 일치 여부 확인
```

---

## 4. 전처리 파이프라인 (보강 버전)

### 4.1 공통 전처리 (모든 소주제 공유)

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

### 4.2 소주제 3 기본 파생변수 (Baseline 타겟 생성)

```python
# 1. 유통기한 전체 일수 (입고일 기준, 피처로 사용)
df['Days_To_Expiry'] = (df['Expiry_Date'] - df['Received_Date']).dt.days

# 2. 유통기한 잔여일 (분석 기준일 설정)
reference_date = pd.Timestamp('2025-09-10')  # 분석 기준일
df['Remaining_Shelf_Days'] = (df['Expiry_Date'] - reference_date).dt.days

# 3. 현재 재고 소진 예상 일수 (0 나눗셈 방지)
avg_sales = df['Avg_Daily_Sales'].replace(0, np.nan)
df['Days_To_Deplete'] = df['Quantity_On_Hand'] / avg_sales
df['Days_To_Deplete'] = df['Days_To_Deplete'].fillna(float('inf'))

# 4. Baseline 폐기 위험 타겟 생성
df['Waste_Risk'] = (df['Days_To_Deplete'] > df['Remaining_Shelf_Days']).astype(int)
```

### 4.3 보강 파생변수 + Enhanced 타겟

```python
# ── 방식 A: Enhanced 타겟 생성 (카테고리별 차등 기준) ──
category_sales_period = {
    'Seafood': 7,  'Fresh Produce': 10, 'Dairy': 14, 'Bakery': 7,
    'Meat': 10, 'Frozen': 60, 'Beverages': 60,
    'Pantry': 90, 'Household': 180, 'Personal Care': 180
}
df['Sales_Period'] = df['Category'].map(category_sales_period)

# 카테고리별 가중 잔여일
df['Adjusted_Remaining_Days'] = df['Remaining_Shelf_Days'] * (df['Sales_Period'] / 30)
df['Waste_Risk_Enhanced'] = (df['Days_To_Deplete'] > df['Adjusted_Remaining_Days']).astype(int)

# ── 방식 B: 카테고리별 폐기 프로파일 매핑 ──
category_waste_profile = {
    'Seafood':       {'avg_shelf_life': 5,   'perishability': 5},
    'Fresh Produce': {'avg_shelf_life': 10,  'perishability': 4},
    'Dairy':         {'avg_shelf_life': 14,  'perishability': 4},
    'Meat':          {'avg_shelf_life': 10,  'perishability': 4},
    'Bakery':        {'avg_shelf_life': 5,   'perishability': 3},
    'Frozen':        {'avg_shelf_life': 90,  'perishability': 2},
    'Beverages':     {'avg_shelf_life': 180, 'perishability': 1},
    'Pantry':        {'avg_shelf_life': 365, 'perishability': 1},
    'Household':     {'avg_shelf_life': 730, 'perishability': 0},
    'Personal Care': {'avg_shelf_life': 730, 'perishability': 0},
}
for col, key in [('Avg_Shelf_Life', 'avg_shelf_life'),
                 ('Perishability_Score', 'perishability')]:
    df[col] = df['Category'].map({c: v[key] for c, v in category_waste_profile.items()})

df['Shelf_Life_Ratio'] = df['Remaining_Shelf_Days'] / df['Avg_Shelf_Life']
df['Waste_Risk_Score'] = df['Perishability_Score'] * (
    df['Quantity_On_Hand'] / df['Avg_Daily_Sales'].replace(0, 1)
)
df['Adjusted_Coverage'] = df['Days_of_Inventory'] / df['Avg_Shelf_Life']
```

### 4.4 카테고리 & ABC 등급 & FIFO/FEFO 인코딩

```python
# FIFO_FEFO 이진 인코딩
df['FIFO_FEFO_encoded'] = (df['FIFO_FEFO'] == 'FEFO').astype(int)  # FEFO=1, FIFO=0

# Category & ABC_Class One-Hot 인코딩
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

---

## 5. 모델링 상세 설계 (보강 버전)

### 5.1 2×2 비교 실험 설계

소주제 3에서는 **피처셋과 타겟을 동시에 2단계로 비교**하는 것이 핵심이다.

| 실험 | 타겟 | 피처셋 | 설명 |
|------|------|--------|------|
| **Exp A** | Waste_Risk (균일 기준) | Baseline 피처 | 기존 방식 그대로 |
| **Exp B** | Waste_Risk (균일 기준) | Enhanced 피처 | 기존 타겟 + 보강 피처 |
| **Exp C** | Waste_Risk_Enhanced (카테고리 차등) | Baseline 피처 | 보강 타겟 + 기존 피처 |
| **Exp D** | Waste_Risk_Enhanced (카테고리 차등) | Enhanced 피처 | 보강 타겟 + 보강 피처 |

#### Baseline 피처셋 (21개)

```python
baseline_features = [
    # 수치형 (8개)
    'Unit_Cost_USD', 'Quantity_On_Hand', 'Reorder_Point',
    'Avg_Daily_Sales', 'Days_of_Inventory', 'Stock_Age_Days',
    'Damaged_Qty', 'Returns_Qty',
    # 파생 (1개)
    'Days_To_Expiry',
    # + Category One-Hot (9개, Bakery baseline)
    # + ABC_Class One-Hot (2개, A baseline)
    # + FIFO_FEFO_encoded (1개)
]
# 총: 9 + 9 + 2 + 1 = 21개
```

#### Enhanced 피처셋 (최대 25개)

```python
enhanced_features = baseline_features + [
    'Avg_Shelf_Life',         # 카테고리 평균 유통기한 (방식 B)
    'Perishability_Score',    # 부패 위험도 0~5 (방식 B)
    'Shelf_Life_Ratio',       # 잔여일/평균유통기한 (방식 B)
    'Waste_Risk_Score',       # 폐기 위험 복합 점수 (방식 B)
    # 'Adjusted_Coverage',    # 선택적 — 조정 커버리지 (방식 B)
    # 'Sales_Period',         # 카테고리별 판매 기간 (Category에서 결정론적 매핑)
]
# 총: 21 + 4 = 25개 (선택 포함 최대 27개)
```

> ⚠️ **Data Leakage 방지:**
> - `Days_To_Deplete`, `Remaining_Shelf_Days` → Baseline 타겟 생성에 사용, 피처 제외
> - `Adjusted_Remaining_Days` → Enhanced 타겟 생성에 사용, 피처 제외
> - `Sales_Period` → Category에서 결정론적 매핑이므로 leakage 아님, 피처 사용 가능
> - `Avg_Daily_Sales`, `Quantity_On_Hand` → 각각 Days_To_Deplete의 구성 요소이지만 비선형 변환 후 타겟과의 관계가 간접적이므로 피처 사용 가능 (단, 노트북에서 명시적 정당화 필요)

### 5.2 학습 모델 (3종 × 4실험 = 12회)

| # | 모델 | 핵심 설정 |
|---|------|-----------|
| 1 | Logistic Regression | `class_weight='balanced'`, `max_iter=1000`, `random_state=42` |
| 2 | SVM (RBF) | `class_weight='balanced'`, `probability=True`, `random_state=42` |
| 3 | XGBoost Classifier | `scale_pos_weight=비율`, `eval_metric='logloss'`, `random_state=42` |

### 5.3 평가 지표

| 지표 | 핵심 |
|------|------|
| **Recall (Risk)** | **최우선** — 폐기 위험 놓치면 실제 비용 발생 |
| **Precision (Risk)** | 오탐 비용 평가 |
| **F1 (Risk)** | 종합 |
| **ROC-AUC** | 임계값 독립 성능 |
| **PR-AUC** | 불균형 시 더 정직한 지표 |

---

## 6. ML 분석 파이프라인

```
STEP 1: 원본 데이터 EDA + 공통 전처리 (인도네시아 로케일 변환 포함)
STEP 2: 보강 데이터 3종 탐색
  ├── ① Food Expiry Tracker: 식품 유형별 유통기한·소비율 분석 (정규화 데이터 역변환)
  ├── ② Food Wastage Data: 음식 유형별·보관 조건별·계절별 폐기 패턴 분석
  └── ③ Global Wastage: 카테고리별 글로벌 폐기 규모·경제적 손실 분석
STEP 3: 도메인 근거 문서화 (카테고리→판매기간 매핑 근거)
STEP 4: Baseline 타겟(균일 기준) + Enhanced 타겟(카테고리 차등) 생성
STEP 5: 두 타겟의 클래스 분포 비교 분석
STEP 6: 보강 파생변수 생성 (방식 B — 폐기 프로파일)
STEP 7: 4가지 실험 수행 (Exp A/B/C/D)
STEP 8: 4실험 성능 비교 분석
STEP 9: 최적 실험의 심층 분석 (ROC/PR Curve, Feature Importance)
STEP 10: 글로벌 벤치마크 비교 (방식 C)
STEP 11: 인사이트 도출
```

---

## 7. 시각화 요구사항 (보강 버전, 총 15종)

| # | 시각화 | 파일명 |
|---|--------|--------|
| 1 | **Baseline vs Enhanced 타겟 분포 비교** | `waste_risk_distribution_comparison.png` |
| 2 | 카테고리별(10종) 폐기 위험 비율 | `category_risk_ratio.png` |
| 3 | ABC 등급별 폐기 위험 비율 | `abc_risk_ratio.png` |
| 4 | Remaining_Shelf_Days vs Days_To_Deplete 산점도 (핵심) | `expiry_vs_deplete_scatter.png` |
| 5 | **식품 유형별 유통기한 분포 (Food Expiry Tracker)** | `food_type_shelf_life.png` |
| 6 | **음식 유형별 폐기량·폐기율 (Food Wastage Data)** | `food_wastage_by_type.png` |
| 7 | 위험 여부별 피처 분포 boxplot | `risk_feature_boxplots.png` |
| 8 | **보강 피처별 Risk 분포 boxplot** | `enhanced_risk_features.png` |
| 9 | **4실험 성능 비교 히트맵** | `experiment_comparison_heatmap.png` |
| 10 | Confusion Matrix (최적 실험) | `confusion_matrix_best.png` |
| 11 | ROC Curve (3모델 비교) | `roc_curve.png` |
| 12 | PR Curve (3모델 비교) | `pr_curve.png` |
| 13 | Feature Importance (최적 모델) | `feature_importance_risk.png` |
| 14 | **글로벌 카테고리별 폐기량 vs 원본 Risk 비율** | `global_benchmark_comparison.png` |
| 15 | **글로벌 경제적 손실 규모 차트** | `global_economic_loss.png` |

---

## 8. Jupyter Notebook 구조

```
03_Waste_Risk_Prediction_Enhanced.ipynb
│
├── 0. 라이브러리 임포트 & 설정
│   ├── 필수 라이브러리 import
│   ├── 시각화 한글 폰트 설정 (matplotlib)
│   └── 경고 메시지 숨김, 시드 고정
│
├── 1. 데이터 로드 & 기본 확인
│   ├── 원본 CSV 로드 (1,000행 × 37열)
│   ├── df.shape, df.info(), df.describe()
│   └── 결측치 확인
│
├── 2. 보강 데이터 탐색 ★
│   ├── 2.1 ① Food Expiry Tracker (정규화 데이터 역변환 → 식품별 유통기한·소비율)
│   ├── 2.2 ② Food Wastage Data (음식 유형별·보관·계절별 폐기 패턴)
│   ├── 2.3 ③ Global Food Wastage (글로벌 폐기 현황·경제적 손실)
│   └── 2.4 (참고) Shelf Life 이미지 데이터 구조 확인
│
├── 3. 데이터 전처리
│   ├── 3.1 공통 전처리 (인도네시아 로케일 변환, 금액·퍼센트 변환, 날짜 파싱)
│   ├── 3.2 기본 파생변수 생성 (Days_To_Expiry, Remaining_Shelf_Days)
│   └── 3.3 카테고리·ABC·FIFO/FEFO 인코딩
│
├── 4. 타겟 변수 생성 (핵심 Feature Engineering) ★
│   ├── 4.1 Baseline 타겟: Waste_Risk (균일 기준)
│   ├── 4.2 도메인 근거 문서화 (카테고리→판매기간 매핑)
│   ├── 4.3 Enhanced 타겟: Waste_Risk_Enhanced (카테고리 차등) ★
│   └── 4.4 두 타겟 분포 비교 & 시각화
│
├── 5. 보강 파생변수 생성 (방식 B) ★
│   ├── Avg_Shelf_Life, Perishability_Score 매핑
│   ├── Shelf_Life_Ratio, Waste_Risk_Score, Adjusted_Coverage 계산
│   └── 보강 피처별 Risk 분포 확인
│
├── 6. EDA (Baseline + Enhanced)
│   ├── 카테고리별(10종) 폐기 위험 비율
│   ├── ABC 등급별 폐기 위험 비율
│   ├── Remaining_Shelf_Days vs Days_To_Deplete 산점도 (핵심)
│   ├── 위험 여부별 주요 피처 분포 (boxplot)
│   ├── FIFO vs FEFO 출고 방식별 위험 비율
│   └── 상관관계 히트맵
│
├── 7. 4가지 실험 수행 ★
│   ├── 7.1 Exp A: Baseline 타겟 + Baseline 피처
│   ├── 7.2 Exp B: Baseline 타겟 + Enhanced 피처
│   ├── 7.3 Exp C: Enhanced 타겟 + Baseline 피처
│   ├── 7.4 Exp D: Enhanced 타겟 + Enhanced 피처
│   └── 7.5 4실험 성능 비교표 & 히트맵
│
├── 8. 최적 실험 심층 분석
│   ├── Confusion Matrix 히트맵
│   ├── Classification Report 출력
│   ├── ROC Curve (3모델 비교)
│   ├── Precision-Recall Curve (3모델 비교)
│   ├── Feature Importance 시각화
│   └── (선택) 최적 Threshold 탐색
│
├── 9. 글로벌 벤치마크 비교 ★
│   ├── 카테고리별 글로벌 폐기량 vs 원본 Risk 비율 비교
│   ├── 경제적 손실 규모 시각화
│   └── 현실성 검증 인사이트
│
└── 10. 결론 및 인사이트
    ├── 보강 전후 모델 성능 차이 분석
    ├── 카테고리별·ABC 등급별 위험 집중도 분석
    ├── 도메인 지식 기반 피처의 기여도 평가
    ├── FIFO vs FEFO 출고 방식별 폐기 위험 분석
    ├── 다른 소주제와의 연결점
    └── 한계점 및 개선 방향
```

---

## 9. 핵심 유의사항

### 9.1 데이터 관련

- 데이터가 1,000행으로 **소규모**이므로 과적합에 주의
- **인도네시아 로케일 형식:** `Avg_Daily_Sales`가 `"28,57"` 형태 → 쉼표→마침표 변환 후 float 캐스팅 필수
- **금액 컬럼 복합 형식:** `Unit_Cost_USD`가 `"$5,81"` 형태 → `$` 제거, 천단위`.` 제거, 쉼표→마침표 변환 필수
- `Category` 컬럼은 올바른 철자 (이전 데이터의 `Catagory` 오타 아님), 10개 범주
- `Avg_Daily_Sales`가 0인 경우 **0 나눗셈 처리** 필수
- `Remaining_Shelf_Days`가 음수인 경우 존재 가능 → 이미 유통기한 초과 제품
- 새 데이터에 `Damaged_Qty`, `Returns_Qty`, `ABC_Class`, `FIFO_FEFO`가 있어 분석에 활용

### 9.2 보강 데이터 관련

- **Food Expiry Tracker (①):** 정규화/One-Hot 상태이므로 절대값 해석 불가. 유형 간 **상대적 비교**와 **소비 성공률(used_before_expiry)** 활용에 초점. One-Hot 역변환 필수.
- **Food Wastage Data (②):** 레스토랑/이벤트 환경 데이터이므로, 유통 재고와는 맥락이 다름. 음식 유형별 폐기 경향의 **일반적 패턴 참고**로만 활용하고, 직접 매핑은 주의.
- **Global Food Wastage (③):** 국가 단위 거시 데이터이므로 개별 제품 수준의 직접 비교는 부적절. **프로젝트 배경 근거 + 카테고리 수준의 벤치마크**로 활용.
- **Shelf Life 이미지 데이터:** 직접 피처로 사용 불가 (이미지 데이터셋). 폴더 구조에서 유통기한 범위 정보를 **도메인 근거**로만 참고.

### 9.3 타겟 정밀화 관련

- Enhanced 타겟의 `category_sales_period` 값은 **Food Expiry Tracker 분석 결과 + Shelf Life 도메인 참고 + 일반 지식**에 기반하므로 매핑 근거를 노트북에 명시적으로 문서화
- Baseline vs Enhanced 타겟의 **클래스 분포가 달라질 수 있음** → 불균형 대응 전략도 각각 재설정
- 두 타겟의 일치율을 확인하여, "어떤 제품이 기준 변경으로 Safe→Risk 또는 Risk→Safe로 바뀌는지" 분석
- **분석 기준일(reference_date = 2025-09-10)** 설정 근거를 문서화

### 9.4 Data Leakage 방지

- `Days_To_Deplete`, `Remaining_Shelf_Days` → Baseline 타겟 생성에 사용, 피처 제외
- `Adjusted_Remaining_Days` → Enhanced 타겟 생성에 사용, 피처 제외
- `Sales_Period` → Category에서 결정론적 매핑, leakage 아님, 피처 사용 가능
- `Avg_Daily_Sales`, `Quantity_On_Hand` → Days_To_Deplete의 구성 요소이나 비선형 변환 후 간접적 관계이므로 피처 사용 가능 (명시적 정당화 필요)

### 9.5 평가 관련

- **Recall(Risk) 최우선** — 폐기 위험 제품을 놓치면(FN) 실제 폐기 비용 발생
- 오탐(FP) — Safe를 Risk로 잘못 분류해도, 추가 점검 비용만 발생 (상대적으로 저렴)
- ROC-AUC vs PR-AUC: 불균형이 심하면 **PR-AUC가 더 정직한 지표**
- 최적 Threshold를 0.5가 아닌 다른 값으로 조정하여 Recall을 높이는 것도 고려
- 4실험 비교 시 **동일한 train/test 분할** 유지 (random_state 고정)

### 9.6 다른 소주제와의 연결

- **소주제 1 → 소주제 3:**
  - 소주제 1에서 Expiring Soon / Low Stock으로 분류된 제품이 소주제 3에서도 Risk로 분류되는지 교차 분석
  - 연결 시사점: Inventory_Status가 폐기 위험과 관련이 있었는지 사후 검증

- **소주제 2 → 소주제 3:**
  - 소주제 2에서 예측한 Avg_Daily_Sales를 사용하면 `Days_To_Deplete`가 더 정밀해짐
  - 더 정밀한 판매량 예측 → 더 정밀한 폐기 위험 예측으로 이어지는 파이프라인

- **소주제 3 → 소주제 4:**
  - Risk로 분류된 제품이 소주제 4의 어떤 군집(Fast Mover / Slow Mover 등)에 속하는지 확인
  - 군집별 폐기 위험 비율 비교 → 발주 전략에 폐기 위험 감소 로직 반영

- 보강 파생변수(Perishability_Score, Shelf_Life_Ratio 등) → 소주제 4 클러스터링 피처 후보
- 소주제 3의 결과를 README.md 3.3절의 결과 테이블에 기입

---

## 10. 기대 산출물 체크리스트

- [ ] `03_Waste_Risk_Prediction_Enhanced.ipynb`
- [ ] 보강 데이터 3종 탐색 결과 요약 (각 데이터의 핵심 통계)
- [ ] 도메인 근거 문서화 (카테고리→판매기간 매핑 근거표)
- [ ] Baseline vs Enhanced 타겟 분포 비교 분석
- [ ] 4실험 성능 비교표 (Recall, Precision, F1, AUC)
- [ ] 글로벌 벤치마크 비교 인사이트
- [ ] 시각화 파일 15종 (`outputs/figures/`)
- [ ] 최적 모델 저장 (`outputs/models/best_risk_model_enhanced.pkl`)
- [ ] 핵심 인사이트 5~7개

---

## 부록 A: 보강 데이터 파일 경로

| # | 데이터 | 파일 경로 |
|---|--------|-----------|
| ① | Food Expiry Tracker | `data/etc_subtopic3/food_expiry_tracker.csv` |
| ② | Food Wastage Data | `data/etc_subtopic3/food_wastage_data.csv` |
| ③ | Global Food Wastage | `data/etc_subtopic3/global_food_wastage_dataset.csv` |
| (참고) | Shelf Life 이미지 | `data/etc_subtopic3/fruit and vegetable dataset for Shelf life/` |

## 부록 B: 카테고리 매핑 참조표 (10종)

| E-Grocery Category | 건수 | Food Expiry 매핑 | Food Wastage 매핑 | Global Wastage 매핑 | 부패 위험도 | 추정 유통기한(일) |
|--------------------|------|-------------------|-------------------|---------------------|-------------|-------------------|
| Pantry | 137 | grain | Grains | Cereals | 1 | 90~365 |
| Personal Care | 126 | snack (유사) | — | — | 0 | 730+ |
| Beverages | 120 | beverage | Beverages | — | 1 | 60~180 |
| Fresh Produce | 110 | fruit, vegetable | Vegetables, Fruits | Fruits & Vegetables | 4 | 5~14 |
| Household | 103 | snack (유사) | — | — | 0 | 730+ |
| Dairy | 96 | dairy | Dairy | Dairy Products | 4 | 7~21 |
| Meat | 87 | meat | Meat | Meat & Poultry | 4 | 5~10 |
| Frozen | 86 | snack (유사) | Frozen Food | — | 2 | 60~180 |
| Bakery | 69 | grain (유사) | Bakery | — | 3 | 3~7 |
| Seafood | 66 | meat (유사) | Seafood | Seafood | 5 | 2~5 |

> **매핑 한계:** 보강 데이터의 카테고리 분류 체계가 E-Grocery와 완전히 일치하지 않으므로, 유사한 카테고리로 매핑한다. Household/Personal Care는 비식품이므로 식품 관련 보강 데이터에서 대응 카테고리가 없다.

## 부록 C: 전체 파이프라인 요약 흐름도

```
CSV 로드 (1,000행 × 37열)
  ↓
공통 전처리 (인도네시아 로케일 변환, 금액 변환, 퍼센트 변환, 날짜 파싱)
  ↓
보강 데이터 3종 탐색 & 분석
  ├── ① Food Expiry Tracker (정규화 역변환 → 유형별 유통기한·소비율)
  ├── ② Food Wastage Data (유형별·보관·계절·가격별 폐기 패턴)
  └── ③ Global Wastage (카테고리별 글로벌 폐기량·경제적 손실)
  ↓
★ 핵심 Feature Engineering ★
  ├── Days_To_Expiry 계산 (Expiry_Date - Received_Date)
  ├── Remaining_Shelf_Days 계산 (Expiry_Date - reference_date)
  ├── Days_To_Deplete 계산 (Quantity_On_Hand / Avg_Daily_Sales, 0 나눗셈 방지)
  ├── Baseline Waste_Risk 타겟 생성 (균일 기준)
  ├── Enhanced Waste_Risk_Enhanced 타겟 생성 (카테고리 차등 기준) ★
  └── 두 타겟 분포 비교
  ↓
보강 파생변수 생성 (방식 B)
  ├── Avg_Shelf_Life, Perishability_Score 매핑
  ├── Shelf_Life_Ratio, Waste_Risk_Score 계산
  └── Adjusted_Coverage 계산
  ↓
EDA (클래스 분포, 카테고리별·ABC별 위험 비율, 피처 분포, 핵심 산점도)
  ↓
피처 선택 & 인코딩 (Category, ABC_Class One-Hot + FIFO/FEFO 이진, Data Leakage 방지)
  ↓
4가지 실험 수행 ★
  ├── Exp A: Baseline 타겟 + Baseline 피처
  ├── Exp B: Baseline 타겟 + Enhanced 피처
  ├── Exp C: Enhanced 타겟 + Baseline 피처
  └── Exp D: Enhanced 타겟 + Enhanced 피처
  ↓ (각 실험마다)
Train/Test Split (80:20, stratified) → StandardScaler → 3모델 학습 → 평가
  ↓
4실험 성능 비교 분석 & 히트맵
  ↓
최적 실험 심층 분석 (Confusion Matrix, ROC/PR Curve, Feature Importance)
  ↓
글로벌 벤치마크 비교 (방식 C)
  ↓
인사이트 도출 & 결론 (보강 효과 분석, 폐기 위험 특성, 소주제 간 연결)
```
