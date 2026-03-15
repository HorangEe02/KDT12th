# 🏪. 머신러닝 기반 식료품 유통 재고 관리 최적화 시스템

> 하나의 데이터셋으로 분류·회귀·비지도학습을 아우르며, 식료품 유통의 전 주기를 데이터 기반으로 진단하고 최적화하는 미니 프로젝트

---

## 📌 프로젝트 개요

| 항목              | 내용                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| **프로젝트 기간** | 2026.03.02(or 09) ~ 2026.03.16                                                                                   |
| **팀 구성**       | 4명 (박준영, 이현아, 권효중, 정이랑)                                                                             |
| **데이터 출처**   | [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/) _(정확한 URL은 데이터셋 페이지 확인 후 교체)_ |
| **데이터 규모**   | 1,000행 × 37열 (10개 카테고리, 4개 상태 레이블, 3개 ABC 등급)                                                    |
| **기술 스택**     | Python, Pandas, Scikit-learn, XGBoost, LightGBM, Matplotlib, Seaborn, SHAP                                       |
| **개발 환경**     | Jupyter Notebook / Python / VS Code                                                                              |

---

## 목차

- [팀 빌딩](#0-팀-빌딩)
- [기(起) — 프로젝트 시작](#1-기起--프로젝트-시작)
- [승(承) — 프로젝트 전개](#2-승承--프로젝트-전개)
- [전(轉) — 분석 결과와 발견](#3-전轉--분석-결과와-발견)
- [결(結) — 자체 평가 및 회고](#4-결結--자체-평가-및-회고)

---

## 0. 팀 빌딩

### 0.1 팀 정보

| 항목     | 내용                   |
| -------- | ---------------------- |
| **팀명** | 굿핏(good fit)         |
| **팀장** | 박준영                 |
| **팀원** | 이현아, 권효중, 정이랑 |
| **소속** | KNU - KDT 12기         |

### 0.2 팀 역할 분담

| 이름   | 역할 | 담당 소주제 및 업무                                                                                                          |
| ------ | ---- | ---------------------------------------------------------------------------------------------------------------------------- |
| 정이랑 | 팀원 | 소주제 1 — 재고 상태 분류 (Multi-class Classification) (LR/RF/XGBoost/LightGBM) · 기획 의도 제안                             |
| 이현아 | 팀원 | 소주제 2 — 일일 판매량 예측 (Regression) (Linear/Ridge/Lasso/RF/XGBoost) · SHAP 분석                                         |
| 권효중 | 팀원 | 소주제 3 — 폐기 위험도 예측 (Binary Classification) (LR/SVM/XGBoost) · 2×2 실험 설계                                         |
| 박준영 | 팀장 | 소주제 4 — 최적 발주 전략 클러스터링 (Regression + Clustering) (RF/XGBoost/K-Means) · 소주제 통합 · EOQ 전략 · 프로젝트 관리 |

### 0.3 프로젝트 주제 및 기획 의도

**주제:** 머신러닝 기반 식료품 유통 재고 관리 최적화 시스템

**기획 의도:**

본 프로젝트의 기획은 팀원 정이랑의 실제 경험에서 출발하였다. 정이랑 팀원은 평소 자주 방문하던 이마트에서 좋아하는 커피 브랜드를 구매하곤 했는데, 초기에는 해당 제품의 재고가 항상 적었다. 그런데 같은 시간대에 반복적으로 방문하여 재고를 모두 구매하는 패턴이 지속되자, 어느 순간부터 해당 시간대에 해당 제품의 재고가 눈에 띄게 늘어나 있는 것을 경험하게 되었다.

이 경험을 통해 정이랑 팀원은 **WMS(Warehouse Management System, 창고 관리 시스템)**의 존재와 그 작동 원리에 대해 관심을 갖게 되었다. 이마트와 같은 대형 유통업체는 이미 정교한 WMS를 갖추고 있어, 고객의 구매 패턴을 분석하고 시간대·요일별 수요에 맞춰 재고를 자동으로 조정하는 시스템이 운영되고 있다.

그러나 여기서 한 가지 의문이 생겼다. **"중소·중견 규모의 식료품 유통업체도 이러한 시스템을 갖추고 있을까?"** 실제로 국내 중소기업의 ERP 도입률은 16.3%에 불과하며(대기업 95.5%), WMS와 같은 고도화된 시스템의 도입률은 이보다 더 낮은 것으로 추정된다. 대부분의 중소 유통업체는 여전히 수기 또는 엑셀 기반의 재고 관리에 의존하고 있어, 과잉 재고로 인한 폐기 손실과 재고 부족으로 인한 판매 기회 상실이 반복되고 있다.

이러한 문제의식에서 팀원들은 **머신러닝을 활용한 재고 관리 최적화 시스템을 직접 구축해 보자**는 목표를 세웠다. 단순히 하나의 모델을 만드는 것이 아니라, 분류·회귀·비지도학습을 아우르는 4개 소주제를 통해 식료품 유통의 전 주기를 데이터로 진단하고 최적화하는 경험을 쌓고자 하였다.

**도출할 인사이트:**

1. **상태 진단** — 제품의 현재 재고 상태(In Stock/Low Stock/Out of Stock/Expiring Soon)를 결정짓는 핵심 요인은 무엇인가?
2. **수요 예측** — 제품 속성과 재고 정보만으로 일일 판매량(Avg_Daily_Sales)을 어느 정도 정확하게 예측할 수 있는가?
3. **위험 감지** — 유통기한 내 재고 소진이 불가능한 "폐기 위험" 제품을 사전에 식별할 수 있는가?
4. **전략 수립** — 제품군별 최적의 발주 전략은 무엇이며, 군집별로 어떤 차별화된 접근이 필요한가?
5. **종합 연결** — 4개 소주제의 결과를 연결하면 어떤 통합적 재고 관리 전략을 도출할 수 있는가?

### 0.4 트렌드 조사 및 분석

#### WMS 및 AI 기반 재고 관리 시장 환경

**글로벌 WMS 시장:**

| 항목             | 수치                                 |
| ---------------- | ------------------------------------ |
| 2024년 시장 규모 | 약 USD 43.9억 (약 5.9조 원)          |
| 2033년 전망      | 약 USD 109~160억 (약 14.6~21.4조 원) |
| 연평균 성장률    | 18~22% (CAGR)                        |
| 최고 성장 지역   | 아시아-태평양 (CAGR 18.74%)          |

- 클라우드 기반 Tier-II WMS의 중소기업 도입이 전년 대비 18.5% 증가
- 주요 글로벌 솔루션: Manhattan Associates, Blue Yonder, SAP, Oracle
- 국내 주요 플레이어: Samsung SDS (스마트 물류 솔루션)

**AI/ML 기반 소매 재고 관리 동향:**

- AI 소매 시장에서 **수요 예측(Demand Forecasting)**이 전체의 28.3%를 차지하며 1위 활용 사례
- McKinsey 추정: 생성형 AI가 소매 부문에 연간 USD 4,000~6,600억 가치 창출 가능
- 한국 AI 소매 시장 규모: 2024년 USD 1.89억 → 2031년 USD 10.95억 전망

**국내외 주요 사례:**

| 기업/사례                | 성과                                                                             |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Walmart**              | AI 도입 후 재고 부족(품절) 사례 30% 감소, 야간 작업 계획 시간 90분→30분          |
| **Coupang**              | ML 기반 예측 배치로 주문 후 평균 12시간 내 배송, AI·로봇 활용 분류 작업 65% 절감 |
| **온라인 신선식품 업체** | AI 수요 예측 도입 후 식품 폐기·손상 49% 감소                                     |
| **중견 슈퍼마켓 체인**   | 신선식품 폐기 20% 감소, 전체 재고 폐기 10% 감소                                  |

**국내 중소기업의 현실:**

| 시스템/기술      | 중소기업 도입률 | 대기업 도입률 |
| ---------------- | --------------- | ------------- |
| ERP              | 16.3%           | 95.5%         |
| 스마트 팩토리    | 18.6%           | 상당히 높음   |
| AI/빅데이터 분석 | ~11%            | 3~7배 높음    |

- 중소기업의 WMS 도입률은 ERP보다 더 낮은 것으로 추정
- 주요 장벽: 비용 부담, IT 인력 부족, 레거시 시스템과의 통합 어려움
- 대부분 수기·엑셀 기반 재고 관리에 의존 → 과잉 재고 및 품절의 반복

**식품 폐기 및 재고 비효율 현황:**

- 한국 1인당 음식물 폐기량: 연간 약 **95kg** (글로벌 평균 79kg 대비 높음)
- 음식물 폐기물 처리 비용: 2024년 기준 약 **8,235억 원**
- 수집·운반·처리·환경 피해를 포함한 총 경제적 영향: 연간 약 **20조 원**
- 식품 제조 폐기물: 2017년 3,203톤/일 → 2019년 5,066톤/일로 급증 (HMR·밀키트 시장 성장 영향)

#### 관련 리서치 자료 링크

| 분류                    | 출처명                     | 자료 제목                                                                                   | 링크                                                                                                                                                             |
| ----------------------- | -------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WMS 시장 분석           | Grand View Research        | _Warehouse Management System Market Size, Share & Trends Analysis Report, 2025-2033_        | [바로가기](https://www.grandviewresearch.com/industry-analysis/warehouse-management-system-wms-market)                                                           |
| WMS 시장 전망           | MarketsandMarkets          | _Warehouse Management System Market - Global Forecast to 2030_                              | [바로가기](https://www.marketsandmarkets.com/Market-Reports/warehouse-management-system-market-41614951.html)                                                    |
| WMS 시장 동향           | Mordor Intelligence        | _Warehouse Management System Market Size & Share Analysis - Growth Trends & Forecasts_      | [바로가기](https://www.mordorintelligence.com/industry-reports/warehouse-management-system-market)                                                               |
| AI 소매 적용            | SupplyChainBrain           | _Three Ways AI Is Helping Grocers Cut Waste and Boost Profits_                              | [바로가기](https://www.supplychainbrain.com/articles/41698-three-ways-ai-is-helping-grocers-cut-waste-and-boost-profits)                                         |
| ML 소매 사례            | ArticSledge                | _Machine Learning in Retail: Walmart & Target Case Studies_                                 | [바로가기](https://www.articsledge.com/post/machine-learning-retail-case-studies)                                                                                |
| 쿠팡 AI 활용            | BusinessWire               | _Coupang Presents Its Vision to Accelerate AI-driven Commerce at APEC CEO Summit (2025.10)_ | [바로가기](https://www.businesswire.com/news/home/20251028081302/en/)                                                                                            |
| 한국 AI 소매 시장       | Ken Research               | _South Korea AI-Powered Smart Retail Stores Market Outlook, 2024-2031_                      | [바로가기](https://www.kenresearch.com/south-korea-ai-powered-smart-retail-stores-market)                                                                        |
| 한국 ERP 도입률         | Data101                    | _국내 중소기업 ERP 도입 현황 및 시사점_                                                     | [바로가기](https://www.blog.data101.io/305)                                                                                                                      |
| 음식물 쓰레기 통계      | Greenium (그리니엄)        | _한국 1인당 음식물 쓰레기 배출량 현황_                                                      | [바로가기](https://greenium.kr/news/32032/)                                                                                                                      |
| 식품 폐기물 관리        | KREI (한국농촌경제연구원)  | _농식품 감모 및 폐기 실태와 정책과제_                                                       | [바로가기](https://www.krei.re.kr/krei/page/53?cmd=view&biblioId=103586)                                                                                         |
| 한국 식품 폐기 순환경제 | Frost & Sullivan Institute | _South Korea's Recipe for Managing Food Waste: From Crisis to Circular Success_             | [바로가기](https://frostandsullivaninstitute.org/south-koreas-recipe-for-managing-food-waste-from-crisis-to-circular-success/)                                   |
| 한국 AI 소매 비용 절감  | Nucamp                     | _How AI Is Helping Retail Companies in South Korea Cut Costs and Improve Efficiency_        | [바로가기](https://www.nucamp.co/blog/coding-bootcamp-south-korea-kor-retail-how-ai-is-helping-retail-companies-in-south-korea-cut-costs-and-improve-efficiency) |

### 0.5 소주제별 수집 데이터 및 활용 ML 모델

#### 공통 데이터

- **데이터셋:** [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/) _(정확한 URL은 데이터셋 페이지 확인 후 교체)_
- **규모:** 1,000행 × 37열
- **카테고리:** Pantry, Personal Care, Beverages, Fresh Produce, Household, Dairy, Meat, Frozen, Bakery, Seafood (10종)
- **ABC 등급:** A (200건), B (300건), C (500건)
- **데이터 특성:** 인도네시아(자카르타, 반둥, 수라바야, 덴파사르, 메단) 소재 E-Grocery 운영 데이터

#### 소주제별 상세

| 소주제 | 수집/활용 데이터 (피처)                                                                                                                                                                      | 타겟 변수                                         | 활용 ML 모델                                                                | 평가 지표                                            |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------- |
| **1**  | Quantity_On_Hand, Reorder_Point, Safety_Stock, Unit_Cost_USD, Avg_Daily_Sales, Days_of_Inventory, Category, ABC_Class, Stock_Age_Days, Lead_Time_Days, Quantity_Reserved, Quantity_Committed | Inventory_Status (4클래스)                        | Logistic Regression, Random Forest, XGBoost, LightGBM                       | Accuracy, Macro F1-Score, Confusion Matrix           |
| **2**  | Category, ABC_Class, Unit_Cost_USD, Quantity_On_Hand, Reorder_Point, Safety_Stock, Days_of_Inventory, Lead_Time_Days, Stock_Age_Days, Order_Frequency_per_month                              | Avg_Daily_Sales (연속형)                          | Linear Regression, Ridge, Lasso, Random Forest Regressor, XGBoost Regressor | RMSE, MAE, R² Score                                  |
| **3**  | Unit_Cost_USD, Quantity_On_Hand, Reorder_Point, Avg_Daily_Sales, Days_of_Inventory, Category, ABC_Class, Stock_Age_Days, Days_To_Expiry(파생), Damaged_Qty, Returns_Qty                      | Waste_Risk (이진, 파생변수)                       | Logistic Regression, SVM (RBF), XGBoost (class_weight 조정)                 | Precision, Recall, F1 (Risk 중심), ROC-AUC, PR Curve |
| **4**  | Category, ABC_Class, Unit_Cost_USD, Avg_Daily_Sales, Quantity_On_Hand, Reorder_Point, Safety_Stock, Lead_Time_Days, Order_Frequency_per_month, Supplier_OnTime_Pct, Days_of_Inventory        | Days_of_Inventory(회귀) + 군집 레이블(클러스터링) | Random Forest Regressor, XGBoost Regressor, K-Means Clustering              | RMSE, R², Silhouette Score, Elbow Method             |

#### 소주제별 파생 변수

| 파생 변수                | 생성 방식                                                               | 활용 소주제 |
| ------------------------ | ----------------------------------------------------------------------- | ----------- |
| Days_To_Expiry           | Expiry_Date − Received_Date (일수)                                      | 1, 2, 3     |
| Days_Since_Last_Order    | Received_Date − Last_Purchase_Date (일수)                               | 1, 4        |
| Stock_Gap                | Reorder_Point − Quantity_On_Hand (양수 = 재고 부족)                     | 1           |
| Received_Month           | Received_Date에서 월 추출                                               | 2           |
| Days_To_Deplete          | Quantity_On_Hand / Avg_Daily_Sales (재고 소진 예상 일수)                | 3           |
| Remaining_Shelf_Days     | Expiry_Date − 기준일 (유통기한 잔여일, 기준일은 분석 시점으로 설정)     | 3           |
| Waste_Risk               | Days_To_Deplete > Remaining_Shelf_Days → 1 (위험)                       | 3           |
| Available_Stock          | Quantity_On_Hand − Quantity_Reserved − Quantity_Committed (실가용 재고) | 1, 4        |
| Inventory_Value_per_Unit | Total_Inventory_Value_USD / Quantity_On_Hand (단위당 재고 가치)         | 4           |

---

## 1. 기(起) — 프로젝트 시작

### 1.1 배경 및 문제 인식

식료품 유통업에서 **재고 관리의 비효율**은 곧 비용 손실로 직결된다. 과잉 재고는 유통기한 초과로 인한 폐기 비용을 발생시키고, 재고 부족은 판매 기회 상실과 고객 이탈을 초래한다. 특히 식료품은 유통기한이라는 시간적 제약이 존재하기 때문에, 일반 제조업 대비 재고 관리의 난이도가 높다.

본 프로젝트는 이러한 문제의식에서 출발하여, **데이터 기반의 재고 관리 의사결정 지원 시스템**을 머신러닝으로 구현하는 것을 목표로 한다.

### 1.2 데이터셋 소개

본 프로젝트의 공통 데이터는 인도네시아 E-Grocery 업체의 재고 관리 데이터로, SKU(Stock Keeping Unit) 단위의 재고·판매·공급·감사 정보를 포함하는 실무형 데이터셋이다.

**데이터셋 기본 정보:**

| 항목      | 내용                                                                                                             |
| --------- | ---------------------------------------------------------------------------------------------------------------- |
| 출처      | [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/) _(정확한 URL은 데이터셋 페이지 확인 후 교체)_ |
| 행 수     | 1,000행 (SKU 1,000개)                                                                                            |
| 열 수     | 37열 (원본 기준)                                                                                                 |
| 파일 형식 | CSV                                                                                                              |
| 결측치    | Notes 컬럼 834건 (분석 미사용 컬럼)                                                                              |

**전체 변수 상세 설명:**

| #   | 컬럼명                       | 데이터 타입     | 설명                                                                  | 예시 값                                       | 비고                                                                  |     |     |     |     |
| --- | ---------------------------- | --------------- | --------------------------------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------- | --- | --- | --- | --- | --- | --- |
| 1   | SKU_ID                       | 문자열 (object) | 제품 고유 식별 코드.`SKU0001` 형식                                    | `SKU0001`, `SKU0500`                          | 분석에 직접 사용하지 않음 (식별 용도)                                 |     |     |     |     |
| 2   | SKU_Name                     | 문자열 (object) | 제품명. 카테고리+번호 형식                                            | `Pantry Product 13`, `Fresh Product 112`      | 분석에 직접 사용하지 않음 (식별 용도)                                 |     |     |     |     |
| 3   | Category                     | 문자열 (object) | 제품 카테고리. 10개 범주로 구분                                       | `Pantry`, `Fresh Produce`, `Dairy`            | 원본 컬럼명이 올바른 `Category`로 표기                                |     |     |     |     |
| 4   | ABC_Class                    | 문자열 (object) | ABC 분석 등급 (A: 고가치, B: 중간, C: 저가치)                         | `A`, `B`, `C`                                 | A=200건, B=300건, C=500건                                             |     |     |     |     |
| 5   | Supplier_ID                  | 문자열 (object) | 공급업체 고유 식별 코드.`S001`~`S00X` 형식                            | `S005`, `S004`                                | 분석에 직접 사용하지 않음 (식별 용도)                                 |     |     |     |     |
| 6   | Supplier_Name                | 문자열 (object) | 공급업체명 (인도네시아 기업)                                          | `PT Agro Raya`, `PT Nusantara Supplier`       | 분석에 직접 사용하지 않음 (식별 용도)                                 |     |     |     |     |
| 7   | Warehouse_ID                 | 문자열 (object) | 창고 고유 코드. 5개 권역별 창고                                       | `WHJKT`, `WHBDG`, `WHSBY`                     | 지역 기반 분석 시 활용 가능                                           |     |     |     |     |
| 8   | Warehouse_Location           | 문자열 (object) | 창고 소재지 (도시 - 세부지역)                                         | `Jakarta - Cengkareng`, `Bandung - Rancaekek` | 5개 권역: Jakarta, Bandung, Surabaya, Denpasar, Medan                 |     |     |     |     |
| 9   | Batch_ID                     | 문자열 (object) | 배치(입고 단위) 고유 코드                                             | `BATCH2679`, `BATCH4257`                      | 분석에 직접 사용하지 않음 (식별 용도)                                 |     |     |     |     |
| 10  | Received_Date                | 문자열 (object) | 제품 입고일.`YYYY-MM-DD` 형식                                         | `2025-07-14`, `2025-04-08`                    | datetime 파싱 필요, 파생변수 생성의 기준일                            |     |     |     |     |
| 11  | Last_Purchase_Date           | 문자열 (object) | 가장 최근 발주(구매)일                                                | `2025-06-01`, `2025-02-22`                    | datetime 파싱 필요                                                    |     |     |     |     |
| 12  | Expiry_Date                  | 문자열 (object) | 제품 유통기한 만료일                                                  | `2027-04-25`, `2025-04-11`                    | datetime 파싱 필요, 폐기 위험도 예측(소주제 3)의 핵심 변수            |     |     |     |     |
| 13  | Stock_Age_Days               | 정수 (int)      | 재고 보유 일수 (입고 후 경과 일수)                                    | `57`, `154`                                   | 재고 신선도 지표, 소주제 1·3에서 활용                                 |     |     |     |     |
| 14  | Quantity_On_Hand             | 정수 (int)      | 현재 보유 재고 수량 (단위: 개)                                        | `359`, `314`                                  | 재고 관리의 핵심 변수, 소주제 1·3·4에서 활용                          |     |     |     |     |
| 15  | Quantity_Reserved            | 정수 (int)      | 예약(확보)된 재고 수량                                                | `100`, `64`                                   | 실가용 재고 산출에 활용                                               |     |     |     |     |
| 16  | Quantity_Committed           | 정수 (int)      | 출고 확정된 재고 수량                                                 | `36`, `0`                                     | 실가용 재고 산출에 활용                                               |     |     |     |     |
| 17  | Damaged_Qty                  | 정수 (int)      | 파손/불량 재고 수량                                                   | `0`, `4`                                      | 폐기 위험 분석(소주제 3)에서 활용                                     |     |     |     |     |
| 18  | Returns_Qty                  | 정수 (int)      | 반품 수량                                                             | `0`, `1`                                      | 폐기 위험 분석(소주제 3)에서 활용                                     |     |     |     |     |
| 19  | Avg_Daily_Sales              | 문자열 (object) | 일일 평균 판매량. 쉼표 소수점 형식                                    | `"28,57"`, `"34,99"`                          | **전처리 필요:** 쉼표→마침표 변환 후 float 변환, 소주제 2의 타겟 변수 |     |     |     |     |
| 20  | Forecast_Next_30d            | 문자열 (object) | 향후 30일 수요 예측량. 쉼표 소수점 형식                               | `971`, `796`                                  | **전처리 필요:** 쉼표→마침표 변환 후 float/int 변환                   |     |     |     |     |
| 21  | Days_of_Inventory            | 문자열 (object) | 재고 보유 가능 일수 (= Quantity_On_Hand / Avg_Daily_Sales)            | `"12,57"`, `"8,97"`                           | **전처리 필요:** 쉼표→마침표 변환, 재고 회전 속도 지표                |     |     |     |     |
| 22  | Reorder_Point                | 정수 (int)      | 재주문 기준점. 재고가 이 수준 이하이면 재주문 필요                    | `51`, `744`                                   | Stock_Gap 파생변수 생성에 활용                                        |     |     |     |     |
| 23  | Safety_Stock                 | 정수 (int)      | 안전 재고 수준. 수요 변동 및 리드타임 불확실성에 대비하는 최소 재고량 | `22`, `254`                                   | 발주 전략 분석(소주제 4)의 핵심 변수                                  |     |     |     |     |
| 24  | Lead_Time_Days               | 정수 (int)      | 발주 리드타임 (주문부터 입고까지 소요 일수)                           | `1`, `14`                                     | 발주 전략 분석(소주제 4)에서 활용                                     |     |     |     |     |
| 25  | Unit_Cost_USD                | 문자열 (object) | 제품 단가 (USD).`$` 기호 + 쉼표 소수점 형식                           | `"$5,81"`, `"$1,45"`                          | **전처리 필요:** `$` 제거, 쉼표→마침표 변환 후 float 변환             |     |     |     |     |     |     |
| 26  | Last_Purchase_Price_USD      | 문자열 (object) | 최근 구매 단가 (USD).`$` 기호 + 쉼표 소수점 형식                      | `"$5,71"`, `"$1,33"`                          | **전처리 필요:** `$` 제거, 쉼표→마침표 변환 후 float 변환             |     |     |     |     |     |     |
| 27  | Total_Inventory_Value_USD    | 문자열 (object) | 총 재고 가치 (USD).`$` 기호 + 마침표 천단위 구분 + 쉼표 소수점        | `"$2.084,25"`, `"$456,71"`                    | **전처리 필요:** `$`·`.`(천단위) 제거, 쉼표→마침표 변환               |     |     |     |     |     |     |
| 28  | SKU_Churn_Rate               | 문자열 (object) | SKU 이탈률 (단종·비활성화 비율). 쉼표 소수점 형식                     | `"2,39"`, `"3,34"`                            | **전처리 필요:** 쉼표→마침표 변환                                     |     |     |     |     |
| 29  | Order_Frequency_per_month    | 문자열 (object) | 월간 발주 빈도. 쉼표 소수점 형식                                      | `"5,00"`, `"12,00"`                           | **전처리 필요:** 쉼표→마침표 변환, 소주제 4에서 활용                  |     |     |     |     |
| 30  | Supplier_OnTime_Pct          | 문자열 (object) | 공급업체 정시 납품률 (%). 쉼표 소수점 +`%` 형식                       | `"70,68%"`, `"84,61%"`                        | **전처리 필요:** `%` 제거, 쉼표→마침표 변환                           |     |     |     |     |
| 31  | FIFO_FEFO                    | 문자열 (object) | 재고 출고 방식 (FIFO: 선입선출 / FEFO: 유통기한 임박 우선 출고)       | `FIFO`, `FEFO`                                | 이진 인코딩 가능, 소주제 3에서 활용 가능                              |     |     |     |     |
| 32  | Inventory_Status             | 문자열 (object) | 재고의 현재 운영 상태 (4개 클래스)                                    | `In Stock`, `Low Stock`, `Expiring Soon`      | 소주제 1의 타겟 변수                                                  |     |     |     |     |
| 33  | Count_Variance               | 정수 (int)      | 실사 시 재고 차이 (시스템 재고 vs 실물 재고)                          | `0`, `4`                                      | 재고 정확도 분석에 활용 가능                                          |     |     |     |     |
| 34  | Audit_Date                   | 문자열 (object) | 재고 감사(실사)일                                                     | `2025-06-26`, `2025-08-12`                    | datetime 파싱 필요                                                    |     |     |     |     |
| 35  | Audit_Variance_Pct           | 문자열 (object) | 감사 차이 비율 (%). 쉼표 소수점 +`%` 형식, 음수 가능                  | `"-7,14%"`, `"2,15%"`                         | **전처리 필요:** `%` 제거, 쉼표→마침표 변환                           |     |     |     |     |
| 36  | Demand_Forecast_Accuracy_Pct | 문자열 (object) | 수요 예측 정확도 (%). 쉼표 소수점 +`%` 형식                           | `"95,67%"`, `"86,00%"`                        | **전처리 필요:** `%` 제거, 쉼표→마침표 변환                           |     |     |     |     |
| 37  | Notes                        | 문자열 (object) | 비고/메모 (자유 텍스트)                                               | (빈 값이 대부분)                              | 결측치 834건, 분석에 미사용                                           |     |     |     |     |

**카테고리(Category) 분포:**

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

**Inventory_Status(재고 상태) 분포:**

| 상태          | 의미                             | 건수  | 비율  |
| ------------- | -------------------------------- | ----- | ----- |
| In Stock      | 현재 정상 재고 보유 중           | 428건 | 42.8% |
| Expiring Soon | 유통기한 임박 제품               | 329건 | 32.9% |
| Low Stock     | 재고 수준이 재주문점 이하로 하락 | 241건 | 24.1% |
| Out of Stock  | 재고 완전 소진 (품절)            | 2건   | 0.2%  |

**ABC 등급(ABC_Class) 분포:**

| 등급 | 의미                                     | 건수  | 비율  |
| ---- | ---------------------------------------- | ----- | ----- |
| A    | 고가치 제품 (매출 기여 상위)             | 200건 | 20.0% |
| B    | 중간 가치 제품                           | 300건 | 30.0% |
| C    | 저가치 제품 (매출 기여 하위, 품목 수 多) | 500건 | 50.0% |

**데이터 특성 및 전처리 포인트:**

- Inventory_Status 레이블이 **불균형** → Out of Stock이 2건(0.2%)에 불과하므로, **클래스 불균형 처리 전략** 필요 (SMOTE, class_weight 조정, 또는 3클래스로 통합 검토)
- 분석에 직접 사용하지 않는 결측치(Notes 834건)만 존재하여, 실질적 결측치 이슈는 없음
- **숫자 컬럼의 인도네시아 로케일 형식:** 쉼표(`,`)가 소수점으로 사용됨 → 쉼표→마침표 변환 필요 (Avg_Daily_Sales, Days_of_Inventory, SKU_Churn_Rate, Order_Frequency_per_month 등)
- **금액 컬럼의 복합 형식:** `$` 기호 + 마침표(`.`)가 천단위 구분 + 쉼표(`,`)가 소수점 → `$`·`.`(천단위) 제거, 쉼표→마침표 변환 필요 (Unit_Cost_USD, Last_Purchase_Price_USD, Total_Inventory_Value_USD)
- **퍼센트 컬럼:** `%` 기호 제거 + 쉼표→마침표 변환 필요 (Supplier_OnTime_Pct, Audit_Variance_Pct, Demand_Forecast_Accuracy_Pct)
- **날짜 컬럼 4개** (`Received_Date`, `Last_Purchase_Date`, `Expiry_Date`, `Audit_Date`)를 활용한 파생변수 생성 가능 — 기존 데이터 대비 `Audit_Date`가 추가
- **Warehouse_Location**이 도시-세부지역 형식으로 구조화되어 있어, Warehouse_ID(5개 권역)를 통한 지역 기반 분석이 가능

### 1.3 프로젝트 목표 및 소주제 구성

**대주제:** 머신러닝 기반 식료품 유통 재고 관리 최적화 시스템

하나의 데이터셋에서 식료품 유통의 전 주기를 아우르는 4개 소주제를 설정하였다.

```
 상태 진단          수요 예측          위험 감지          전략 수립
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 소주제 1  │ →  │ 소주제 2  │ →  │ 소주제 3  │ →  │ 소주제 4  │
│ 재고 상태 │    │ 일일     │    │ 폐기 위험 │    │ 발주 전략 │
│ 분류     │    │ 판매량   │    │ 예측     │    │ 클러스터링│
│ (다중분류)│    │ 예측(회귀)│    │ (이진분류)│    │ (회귀+비지도)│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

| 소주제 | 주제명                         | ML 유형           | 타겟 변수                                                        |
| ------ | ------------------------------ | ----------------- | ---------------------------------------------------------------- |
| 1      | 재고 상태 분류                 | 다중 클래스 분류  | Inventory_Status (In Stock/Low Stock/Out of Stock/Expiring Soon) |
| 2      | 일일 판매량 예측               | 회귀              | Avg_Daily_Sales                                                  |
| 3      | 유통기한 기반 폐기 위험도 예측 | 이진 분류         | Waste_Risk (파생변수)                                            |
| 4      | 최적 발주 전략 클러스터링      | 회귀 + 비지도학습 | Days_of_Inventory + 군집                                         |

---

## 2. 승(承) — 프로젝트 전개

### 2.1 데이터 전처리 (공통)

모든 소주제에 앞서 다음과 같은 공통 전처리를 수행하였다.

```python
import pandas as pd

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

# 5. 파생 변수 생성
df['Days_To_Expiry'] = (df['Expiry_Date'] - df['Received_Date']).dt.days
df['Days_Since_Last_Order'] = (df['Received_Date'] - df['Last_Purchase_Date']).dt.days
df['Stock_Gap'] = df['Reorder_Point'] - df['Quantity_On_Hand']  # 양수면 재고 부족
df['Received_Month'] = df['Received_Date'].dt.month
df['Available_Stock'] = df['Quantity_On_Hand'] - df['Quantity_Reserved'] - df['Quantity_Committed']

# 6. 카테고리 & ABC 등급 인코딩
df_encoded = pd.get_dummies(df, columns=['Category', 'ABC_Class'], drop_first=True)
```

### 2.2 소주제 1 — 재고 상태 분류 (Multi-class Classification)

**목표:** 제품의 재고·판매·공급 정보를 기반으로 현재 재고 상태(In Stock/Low Stock/Out of Stock/Expiring Soon)를 예측

**접근 방법:**

1. **피처 선정:** Quantity_On_Hand, Reorder_Point, Safety_Stock, Unit_Cost_USD, Avg_Daily_Sales, Days_of_Inventory, Category(인코딩), ABC_Class(인코딩), Stock_Age_Days, Lead_Time_Days, Quantity_Reserved, Quantity_Committed, Stock_Gap
2. **타겟 인코딩:** Inventory_Status → LabelEncoder (Expiring Soon=0, In Stock=1, Low Stock=2, Out of Stock=3)
3. **클래스 불균형 대응:** Out of Stock이 2건(0.2%)에 불과하므로, 3클래스로 통합(Out of Stock → Low Stock에 병합) 또는 SMOTE/class_weight 조정 검토
4. **Train/Test 분리:** 80:20, stratified split
5. **모델 학습 및 비교:**
   - Baseline: Logistic Regression (multinomial)
   - Random Forest Classifier
   - XGBoost Classifier
   - LightGBM Classifier
6. **평가 지표:** Accuracy, Macro F1-Score, Confusion Matrix, Classification Report
7. **해석:** Feature Importance (트리 기반), Confusion Matrix 히트맵 시각화

### 2.3 소주제 2 — 일일 판매량 예측 (Regression)

**목표:** 제품 속성과 재고 정보를 기반으로 Avg_Daily_Sales를 예측

**접근 방법:**

1. **피처 선정:** Category(인코딩), ABC_Class(인코딩), Unit_Cost_USD, Quantity_On_Hand, Reorder_Point, Safety_Stock, Days_of_Inventory, Lead_Time_Days, Stock_Age_Days, Order_Frequency_per_month, Received_Month
2. **타겟:** Avg_Daily_Sales (연속형)
3. **Train/Test 분리:** 80:20
4. **모델 학습 및 비교:**
   - Baseline: Linear Regression
   - Ridge / Lasso Regression (정규화 비교)
   - Random Forest Regressor
   - XGBoost Regressor
5. **평가 지표:** RMSE, MAE, R² Score
6. **해석:** SHAP Summary Plot으로 피처별 판매량 기여도 시각화, 카테고리별·ABC 등급별 판매량 분포 분석

### 2.4 소주제 3 — 폐기 위험도 예측 (Binary Classification)

**목표:** 유통기한 내 재고 소진이 가능한지 여부를 이진 분류

**접근 방법:**

1. **타겟 변수 생성 (핵심 Feature Engineering):**

   ```python
   # 현재 재고 소진 예상 일수 (일일 판매량 기준)
   df['Days_To_Deplete'] = df['Quantity_On_Hand'] / df['Avg_Daily_Sales']

   # 유통기한 잔여일 (분석 기준일 설정)
   reference_date = pd.Timestamp('2025-09-10')  # 분석 기준일
   df['Remaining_Shelf_Days'] = (df['Expiry_Date'] - reference_date).dt.days

   # 폐기 위험 여부: 소진 일수 > 유통기한 잔여일이면 Risk
   df['Waste_Risk'] = (df['Days_To_Deplete'] > df['Remaining_Shelf_Days']).astype(int)
   ```

2. **피처 선정:** Unit_Cost_USD, Quantity_On_Hand, Reorder_Point, Avg_Daily_Sales, Days_of_Inventory, Category(인코딩), ABC_Class(인코딩), Stock_Age_Days, Days_To_Expiry, Damaged_Qty, Returns_Qty
3. **클래스 불균형 확인 및 대응:** SMOTE 또는 class_weight 조정
4. **모델 학습 및 비교:**
   - Logistic Regression
   - SVM (RBF kernel)
   - XGBoost (scale_pos_weight 조정)

5. **평가 지표:** Precision, Recall, F1-Score (Risk 클래스 중심), ROC-AUC, PR Curve
6. **해석:** 폐기 위험 제품의 공통 특성 분석 (카테고리·ABC 등급·가격대·재고량·FIFO/FEFO 방식 기준)

### 2.5 소주제 4 — 최적 발주 전략 클러스터링 (Regression + Clustering)

**목표:** 재고 보유일수(Days_of_Inventory)를 예측하고, 제품군을 발주 특성에 따라 군집화

**접근 방법:**

**[Phase A] 재고 보유일수 예측 (Regression)**

1. **타겟:** Days_of_Inventory
2. **피처:** Category, ABC_Class, Unit_Cost_USD, Avg_Daily_Sales, Quantity_On_Hand, Reorder_Point, Safety_Stock, Lead_Time_Days, Order_Frequency_per_month, Supplier_OnTime_Pct
3. **모델:** Random Forest / XGBoost Regressor
4. **평가:** RMSE, R² Score

**[Phase B] 발주 패턴 클러스터링 (Unsupervised)**

1. **클러스터링 피처:** Quantity_On_Hand, Reorder_Point, Safety_Stock, Days_of_Inventory, Order_Frequency_per_month, Lead_Time_Days, Supplier_OnTime_Pct (StandardScaler 정규화)
2. **최적 K 탐색:** Elbow Method + Silhouette Score
3. **모델:** K-Means Clustering
4. **군집 해석 및 네이밍:**
   - 예시: "고회전-빈번발주(Fast Mover)", "저회전-장기보유(Slow Mover)", "균형형(Balanced)" 등
5. **시각화:** PCA 2D 산점도, 군집별 레이더 차트, 카테고리·ABC 등급별 군집 분포

---

## 3. 전(轉) — 분석 결과와 발견

### 3.1 소주제 1 결과 — 재고 상태 분류

> Out of Stock 2건(0.2%)을 Low Stock에 병합하여 **3클래스**(In Stock / Expiring Soon / Low Stock)로 재구성.
> 데이터 누수 피처(Days_To_Expiry, Stock_Gap) 제거 후 **Scenario B(12개 수치형 + 범주형 = 23개 피처)**로 학습.

| 모델                        | Test Accuracy | Macro F1   | Train-Test Gap |
| --------------------------- | ------------- | ---------- | -------------- |
| Logistic Regression (Tuned) | 0.9800        | 0.9782     | -0.0012        |
| Random Forest (Tuned)       | 0.9550        | 0.9503     | 0.0338         |
| XGBoost (Tuned)             | 0.9850        | 0.9820     | 0.0138         |
| **LightGBM (Tuned)**        | **0.9900**    | **0.9879** | **0.0100**     |

**최적 모델: LightGBM (Tuned)** — Macro F1 최고(0.9879), Gap 최소 수준(0.01), ROC-AUC = 0.9997

| 클래스 (LightGBM) | Precision | Recall | F1-Score | Support |
| ------------------ | --------- | ------ | -------- | ------- |
| Expiring Soon      | 0.9706    | 1.0000 | 0.9851   | 66      |
| In Stock           | 1.0000    | 1.0000 | 1.0000   | 86      |
| Low Stock          | 1.0000    | 0.9583 | 0.9787   | 48      |
| **Macro Avg**      | **0.9902**| **0.9861** | **0.9879** | **200** |

**주요 발견:**

- **데이터 누수 발견 및 대응:** Days_To_Expiry(Expiring Soon과 100% 대응)와 Stock_Gap(Low Stock과 97.9% 대응)이 타겟 정의 규칙과 직접 대응되는 누수 피처로 확인되어 제거. RP+QOH 조합의 잔존 누수 검증(2-피처 Acc=0.606)도 수행하여 잔존 누수 없음 확인
- **Feature Importance 3중 교차검증 결과 (Impurity / Permutation / SHAP):**
  - 1위: **Lead_Time_Days** (Permutation + SHAP 모두 1위, 납품 리드타임이 진정한 핵심 피처)
  - 2위: **Days_of_Inventory** (Impurity 1위이나 연속형 변수 편향)
  - 3~5위: Category_Beverages, Category_Frozen, Unit_Cost_USD
- **Confusion Matrix:** 유일한 오분류 패턴은 **Low Stock → Expiring Soon 2건**. In Stock과 Expiring Soon은 100% 정확 분류
- **3단계 과적합 검증:** Train/Test Gap → 5-Fold CV → Learning Curve로 체계적 검증 완료
- **RandomizedSearchCV(50 조합):** 수동 튜닝과 동일 성능 확인 (LightGBM F1=0.9879)

### 3.2 소주제 2 결과 — 일일 판매량 예측

> 데이터 누수 피처(Days_of_Inventory = QOH/ADS) 제거 후 **19개 피처**로 학습.
> Order_Frequency_per_month는 수학적 누수가 아닌 비즈니스 상관(상관계수 0.92)으로 판정, 유지.

| 모델                    | RMSE  | MAE  | R²     | Train-Test Gap |
| ----------------------- | ----- | ---- | ------ | -------------- |
| Linear Regression       | 7.15  | 5.46 | 0.8832 | 0.0245         |
| Ridge (Tuned)           | 7.14  | 5.46 | 0.8840 | 0.0242         |
| Lasso (Tuned)           | 7.52  | 5.61 | 0.8841 | 0.0184         |
| Random Forest (Tuned)   | 6.47  | 4.50 | 0.9045 | 0.0543         |
| **XGBoost (Tuned)**     | **4.79** | **3.32** | **0.9477** | **0.0436** |

**최적 모델: XGBoost (Tuned)** — R²=0.9477, RMSE=4.79, MAE=3.32 (모든 지표 1위). CV R²=0.9458 ± 0.0110

> RandomizedSearchCV(50 조합) 결과: XGBoost R²=0.9659/RMSE=3.86, RF R²=0.9290/RMSE=5.58로 수동 튜닝 대비 추가 개선 확인

**주요 발견:**

- **Feature Importance 3중 교차검증 (Impurity / Permutation / SHAP):**
  - 1위: **Order_Frequency_per_month** — 3가지 방법 **모두** 1위. SHAP 평균값(8.81)이 2위(3.65)의 2.4배
  - 2위: Reorder_Point (Permutation/SHAP 2위)
  - 3~5위: Quantity_On_Hand, Lead_Time_Days, Safety_Stock
- **카테고리별 판매량:** Beverages(53.09) > Fresh Produce(33.58) > ... > Household(10.98), 약 5배 차이
- **ABC 등급별 판매량:** A등급(37.69) > B등급(28.49) > C등급(21.00)
- **구간별 성능:** 저판매(0~20) RMSE=2.78 vs 초고판매(70+) RMSE=9.13, 고판매량 구간 과소예측 경향(Bias=+6.94)
- **Lasso 변수 선택:** Safety_Stock의 계수를 0으로 → Reorder_Point/QOH와 정보 중복 확인
- **비선형 모델 우위:** 선형 모델 R²≈0.88 vs 트리 모델 R²=0.90~0.95 → 비선형 패턴 존재 확인

### 3.3 소주제 3 결과 — 폐기 위험도 예측

> 타겟 변수 Waste_Risk를 도메인 지식으로 직접 설계: Days_To_Deplete(QOH/ADS) > Remaining_Shelf_Days이면 Risk(1).
> 클래스 분포: Safe 575건(57.5%) / Risk 425건(42.5%). 누수 피처(DOI, Days_To_Deplete, Remaining_Shelf_Days) 제거, **20개 피처**로 학습.

| 모델                        | Test Acc | Precision(Risk) | Recall(Risk) | F1     | AUC    | Gap    |
| --------------------------- | -------- | --------------- | ------------ | ------ | ------ | ------ |
| **Logistic Regression (Tuned)** | **0.9900** | **0.98**    | **1.0000**   | **0.9884** | **0.9932** | **0.0088** |
| SVM-RBF (Tuned)             | 0.9900   | 0.98            | 1.0000       | 0.9884 | 0.9916 | 0.0088 |
| XGBoost (Tuned)             | 0.9900   | 0.98            | 1.0000       | 0.9884 | 0.9999 | 0.0088 |

**최적 모델: Logistic Regression (Tuned)** — 3개 모델 성능 동일, 해석 가능성+경량성(1,039 bytes) 우위로 선정 (오컴의 면도날 원칙)

| 클래스 (LR)   | Precision | Recall   | F1-Score | Support |
| ------------- | --------- | -------- | -------- | ------- |
| Safe (0)      | 1.00      | 0.98     | 0.99     | 115     |
| Risk (1)      | 0.98      | **1.00** | 0.99     | 85      |
| **Macro Avg** | **0.99**  | **0.99** | **0.99** | **200** |

**Confusion Matrix:** TN=113, FP=2, FN=**0**, TP=85 — **False Negative 0건** (Risk 제품을 단 한 건도 놓치지 않음)

**주요 발견:**

- **폐기 위험 비율:** 전체 제품 중 **42.5%** (425건)가 Risk로 분류
- **카테고리별 이분법적 구조:**
  - **부패성 (Risk ~100%):** Bakery(100%), Fresh Produce(100%), Seafood(100%), Meat(98.9%), Dairy(97.9%) — DTE ≤ 30일
  - **비부패성 (Safe 100%):** Beverages, Frozen, Household, Pantry, Personal Care — DTE > 270일
- **99% 정확도는 데이터 누수가 아닌 구조적 패턴:** Ablation Study에서 DTE를 제거해도 Category One-Hot만으로 동일 성능(F1=0.9884) 달성 확인
- **Feature Importance:** Days_To_Expiry가 3개 방법 모두 압도적 1위 (Impurity 0.9992). 나머지 피처의 기여도 사실상 0
- **확률 보정:** Brier Score — SVM 0.0101(최우수), LR 0.0332, XGBoost 0.0403 (모두 < 0.05로 신뢰 가능)
- **부패성 내부 Safe 케이스:** Meat 1건, Dairy 2건 (총 428건 중 3건만 Safe — 예외적으로 유통기한이 길거나 판매 속도가 빠른 제품)

### 3.4 소주제 4 결과 — 발주 전략 클러스터링

> 3단계 연결 분석: Phase A(회귀) → Phase B(클러스터링) → Phase C(EOQ 시뮬레이션).
> Phase A에서 DOI 타겟의 구성 요소(QOH, ADS) 제거 후 **Enhanced 피처셋(22개)**으로 학습.

**[Phase A] 재고 보유일수(DOI) 예측 성능:**

| 모델                     | Train R² | Test R² | RMSE  | Train-Test Gap |
| ------------------------ | -------- | ------- | ----- | -------------- |
| Linear Regression        | 0.37     | 0.3260  | —     | 0.05           |
| Random Forest (Tuned)    | 0.87     | 0.3710  | —     | 0.47           |
| **XGBoost (Tuned)**      | **0.74** | **0.4218** | — | **0.33**       |

> R²=0.42로 예측 성능 자체는 낮으나, **이는 누수 대응(QOH+ADS 제거)의 당연한 결과**. Phase A의 핵심 가치는 예측 정확도가 아니라 **Feature Importance를 통한 DOI 핵심 결정 요인 도출**에 있다.

**Phase A Feature Importance 3중 교차검증:**
- 1위: **ABC_Class_C** (3개 방법 모두 1위 — C등급 여부가 DOI를 가장 잘 설명)
- 2위: Unit_Cost_USD / Reorder_Urgency (방법별 2~3위 교차)
- 3위: Reorder_Urgency — 파생변수(QOH/RP) 중 가장 높은 중요도, 파생변수 엔지니어링 가치 입증

**[Phase B] 클러스터링 결과:**

- **Hopkins Statistic:** Baseline 0.8610 / Enhanced 0.8584 (> 0.75, 강한 군집 경향 확인)
- **최적 K = 2** (Elbow Method + Silhouette Score 모두 지지)
- **Silhouette Score:** Baseline 0.3848 / Enhanced 0.3561
- **안정성 검증:** 5개 랜덤 시드 반복 결과 표준편차 = 0.0009 (극히 안정적)

| 군집      | 프로필             | 제품 수 | 비율  | Available_Stock | Low Stock 비율 | 평균 EOQ |
| --------- | ------------------ | ------- | ----- | --------------- | -------------- | -------- |
| Cluster 0 | 일반 제품군        | 818개   | 81.8% | 양수 (+103.6)   | 17.1%          | 974      |
| Cluster 1 | 고관리 필요 제품군 | 182개   | 18.2% | **음수 (-102.3)** | **55.5%**    | 2,129    |

> Cluster 1 특징: 높은 재주문점(z=+1.63), 높은 안전재고(z=+1.63), 높은 공급 리스크(z=+0.88), Available_Stock 음수 비율 **64.8%**. A등급(고매출) 비율 높음 → "수요는 많고 공급은 불안정한 고위험 제품군"

**[Phase C] EOQ 시뮬레이션 기반 군집별 발주 전략:**

| 항목             | Cluster 0 (일반 제품) | Cluster 1 (고관리 제품)       |
| ---------------- | --------------------- | ----------------------------- |
| **전략명**       | EOQ 기반 정기 발주    | 안전재고 강화 + 즉시 보충     |
| 평균 EOQ         | 974개                 | 2,129개                       |
| 핵심 관리 포인트 | 과재고 방지           | **결품 방지** (음수 재고 해소) |

**주요 발견:**

- **Phase A:** QOH+ADS 제거로 R²=0.42까지 하락했으나, ABC 등급·재주문 긴급도·단가·리드타임이 DOI의 핵심 결정 요인임을 3중 검증으로 확인
- **Phase B:** 제품이 **2개 군집**(일반 82% vs 고관리 18%)으로 자연스럽게 분리. Cluster 1에 Beverages(고회전), A등급(고매출) 제품이 편중
- **Phase C:** Cluster 0은 정기 발주(EOQ=974), Cluster 1은 안전재고 강화+긴급 보충(EOQ=2,129)이라는 **차별화된 발주 전략**을 수치적 근거와 함께 제시
- **4개 소주제 통합:** 상태 진단(1) → 수요 예측(2) → 위험 감지(3) → 전략 수립(4)의 **완전한 재고 관리 의사결정 사이클** 구성

### 3.5 소주제 간 종합 인사이트

```
┌─────────────────────────────────────────────────────┐
│               종합 인사이트 연결 구조                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  소주제1 (상태분류)                                   │
│    → Expiring Soon / Low Stock 제품의 특성 파악        │
│    → 소주제3에서 해당 특성이 폐기위험과 연관되는지 검증    │
│                                                     │
│  소주제2 (판매예측)                                   │
│    → 예측된 판매량을 소주제3의 Days_To_Deplete에 활용 가능│
│    → 더 정밀한 폐기 위험 예측으로 이어짐                 │
│                                                     │
│  소주제3 (폐기위험)                                   │
│    → Risk 제품이 소주제4의 어떤 군집에 속하는지 확인      │
│    → 군집별 폐기위험 비율 비교                          │
│    → FIFO/FEFO 출고 방식의 효과성 검증                  │
│                                                     │
│  소주제4 (발주전략)                                   │
│    → 최종적으로 군집별 맞춤 발주 전략 제안               │
│    → 소주제1~3의 결과를 종합한 액션 플랜 도출            │
│    → ABC 등급별 차별화된 재고 관리 전략 수립             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 4. 결(結) — 자체 평가 및 회고

### 4.1 프로젝트 달성도

| 평가 항목                | 목표                                        | 달성 여부 | 비고                                                    |
| ------------------------ | ------------------------------------------- | :-------: | ------------------------------------------------------- |
| 다중 분류 모델 구현      | Inventory_Status 3클래스 분류               | ✅        | LightGBM Accuracy 99.0%, Macro F1 0.9879               |
| 회귀 모델 구현           | Avg_Daily_Sales 예측                        | ✅        | XGBoost R²=0.9477, RMSE=4.79                           |
| Feature Engineering      | 폐기 위험 타겟 생성                         | ✅        | Waste_Risk 이진 타겟 설계, Acc 99.0%                    |
| 비지도 학습 적용         | K-Means 클러스터링                          | ✅        | K=2 + Sub-clustering (3-Tier), DBSCAN/GMM 비교          |
| 모델 해석                | SHAP / Feature Importance                   | ✅        | 전 소주제 3중 교차검증 (Impurity/Permutation/SHAP)       |
| 소주제 간 연결           | 종합 인사이트 도출                          | ✅        | 상태 진단→수요 예측→위험 감지→전략 수립 사이클 완성      |
| 수정/보완                | 7개 공통 항목 적용                          | ✅        | 잔존 누수 검증, RandomizedSearchCV, CV/LC, SHAP 등      |
| **대시보드 구현**        | Streamlit WMS 대시보드                      | ✅        | v3.5 — 7페이지, 듀얼 모드, 20+ ML 모델 통합             |

### 4.2 잘한 점 (Strengths)

- 하나의 데이터셋(1,000행 × 37열)에서 **분류·회귀·비지도학습**을 모두 적용하여 ML 방법론의 다양성을 확보
- **데이터 누수 체계적 대응:** 4개 소주제 모두에서 누수 피처를 식별·제거하고, 잔존 누수 검증(단일/조합 피처 Acc 검사)까지 수행
- 인도네시아 로케일 데이터(쉼표 소수점, `$` 기호, `%` 기호)의 전처리 경험을 통해 **실무 데이터 핸들링 역량** 강화
- **Feature Importance 3중 교차검증**(Impurity/Permutation/SHAP)으로 모든 소주제에서 피처 중요도의 일관성을 객관적으로 검증
- **Streamlit WMS v3.5 대시보드** 구현으로 분석 결과를 실무 활용 가능한 인터랙티브 시스템으로 발전시킴
- 37개 컬럼의 풍부한 데이터를 활용하여, 소주제별로 최적화된 피처셋(17~23개) 구성
- ABC 분석 등급과 K-Means 클러스터링을 결합하여 **우선순위 기반 차별화된 재고 관리 전략** 수립

### 4.3 아쉬운 점 (Weaknesses)

- Inventory_Status의 **클래스 불균형**(Out of Stock 2건, 0.2%)으로 4클래스 분류가 불가하여 3클래스로 통합
- **시계열 요소 미반영:** 날짜 컬럼이 단일 시점 스냅샷으로, 계절성·트렌드·판매 패턴 변화를 분석하지 못함
- 소주제 4 Phase A의 **DOI 예측 R²=0.42:** 누수 대응(QOH+ADS 제거) 후 예측 성능이 낮아 예측 모델 자체의 실무 활용은 제한적
- 인도네시아 E-Grocery 데이터이므로, **국내 식료품 유통 환경**과의 직접적 비교에 한계
- 소주제 3에서 전 모델 F1=0.9884로 동일 — **모델 간 성능 차별화 부족**, 데이터 구조가 단순하여 분류 난이도가 낮음

### 4.4 개선 방향 및 후속 과제

1. **시계열 확장:** 실제 POS 데이터나 일별 판매 데이터와 결합하여 LSTM/Prophet 기반 시계열 예측 도입
2. **데이터 규모 확장:** 현재 1,000건 → 실무 수만 건 데이터로 확장 시 모델 성능 변화 및 스케일링 검증
3. **실시간 데이터 연동:** DB/API 기반 실시간 재고 모니터링으로 정적 CSV → 동적 데이터 파이프라인 전환
4. **알림 시스템:** 재고 부족/폐기 임박 자동 알림 기능 추가 (이메일, Slack 연동)
5. **모델 재학습 파이프라인:** MLOps 기반 자동 재학습 + 모델 성능 모니터링
6. **국내 데이터 적용:** 한국 유통업체 데이터에 동일 파이프라인 적용하여 일반화 가능성 검증

### 4.5 배운 점 (Lessons Learned)

- **데이터 누수의 위험성:** 겉보기 높은 정확도가 실무 의미 없는 결과일 수 있음을 경험. Scenario 기반 체계적 검증의 중요성 체득
- **모델 선택의 원칙:** 성능이 동일할 때 단순한 모델(LR)을 선택하는 오컴의 면도날 원칙의 실무적 의미 이해
- **비지도학습의 가치:** 레이블이 없는 상황에서 K-Means + Sub-clustering으로 실질적 비즈니스 전략(3-Tier 분류)을 도출할 수 있음을 확인
- **EDA → ML → 시각화 → 배포의 전체 워크플로우:** Jupyter 분석에서 Streamlit 대시보드까지 엔드투엔드 프로젝트 경험
- **피처 엔지니어링의 중요성:** 원본 데이터에 없는 Waste_Risk 타겟 설계, EOQ/Safety Stock 파생변수 생성 등 도메인 지식 기반 피처 설계 역량 강화
- **팀 협업과 문서화:** 소주제별 가이드라인 → 수정 가이드 → 결과 보고서의 체계적 문서화가 프로젝트 관리와 소통에 핵심적임을 체험

---

## 📁 프로젝트 구조

```
📦 Phase8_mini/
├── README.md                                # 프로젝트 전체 가이드 (본 문서)
├── .gitignore                               # Git 제외 항목
│
├── data/                                    # 데이터셋
│   ├── Supply Chain Inventory Management Grocery Industry/
│   │   ├── InventoryData.csv                # 메인 데이터 (1,000행 × 37열)
│   │   └── _Dashboard.pdf                   # 원본 대시보드 문서
│   ├── subtopic2_etc/                       # 소주제 2 추가 데이터 (FMCG)
│   ├── subtopic3_etc/                       # 소주제 3 추가 데이터 (Food Wastage)
│   └── subtopic4_etc/                       # 소주제 4 추가 데이터 (Logistics)
│
├── notebooks/                               # Jupyter 분석 노트북
│   ├── 01_Inventory_Status_Classification.ipynb
│   ├── 02_Avg_Daily_Sales_Prediction.ipynb
│   ├── 03_Waste_Risk_Prediction.ipynb
│   ├── 04_Reorder_Strategy_Clustering.ipynb
│   ├── 04d_Subtopic4_Improvements.ipynb     # 소주제 4 개선 분석
│   ├── before/                              # 수정 전 원본 노트북
│   ├── etc/                                 # 추가 분석 (TimeSeries, Benchmarking 등)
│   └── outputs/                             # 노트북 출력 (figures, tables)
│
├── outputs/                                 # ML 산출물
│   ├── figures/                             # 시각화 이미지 (127개)
│   └── models/                              # 학습된 모델 (pkl, json)
│       ├── subtopic1_inventory_status/
│       ├── subtopic2_sales_prediction/
│       ├── subtopic3_waste_risk/
│       └── subtopic4_reorder_clustering/
│
├── md/                                      # 분석 문서
│   ├── data_set/                            # 데이터셋 상세 설명
│   ├── enhanced/                            # 강화 가이드라인 (v2.0)
│   ├── modification_summary/                # 수정/보완 결과 요약
│   ├── result_report/                       # 소주제별 최종 결과 보고서
│   ├── subtopic{1~4}_guideline.md           # 소주제별 구현 가이드
│   └── subtopic{1~4}_modification_guideline.md  # 수정 가이드
│
├── streamlit_wms/                           # Streamlit WMS 대시보드 (v3.5)
│   ├── app.py                               # 홈 페이지
│   ├── requirements.txt                     # Python 패키지 의존성
│   ├── .streamlit/config.toml               # Streamlit 설정
│   ├── pages/                               # 6개 분석 페이지
│   │   ├── 1_Dashboard.py                   # 대시보드 개요
│   │   ├── 2_Data_Explorer.py               # 데이터 탐색
│   │   ├── 3_Inventory_Status.py            # 재고 상태 분류 (LightGBM)
│   │   ├── 4_Sales_Prediction.py            # 판매량 예측 (XGBoost)
│   │   ├── 5_Waste_Risk.py                  # 폐기 위험 탐지 (LR)
│   │   └── 6_Reorder_Strategy.py            # 발주 전략 (K-Means+EOQ)
│   └── utils/                               # 유틸리티
│       ├── data_loader.py                   # 데이터/모델 로딩
│       ├── preprocessor.py                  # 피처 전처리
│       ├── descriptions.py                  # 컬럼 설명, 용어 사전
│       └── styles.py                        # 디자인 시스템 (CSS, SVG)
│
├── etc/                                     # 조별 보고서 PDF (1~7조)
├── ppt/                                     # 프레젠테이션
├── scripts/                                 # 유틸리티 스크립트
├── result/                                  # 최종 보고서 초안
└── Dashboard/                               # 대시보드 기획 자료
```

---

## 5. Streamlit WMS 대시보드 (v3.5)

> 분석 결과를 실무에서 활용할 수 있는 인터랙티브 대시보드로 구현

### 5.1 시스템 개요

| 항목           | 내용                                                    |
| -------------- | ------------------------------------------------------- |
| **프레임워크** | Streamlit (Python 기반 웹 앱)                           |
| **페이지 수**  | 7개 (홈 + 6개 분석 모듈)                                 |
| **ML 모델**    | 20+ 학습된 모델 통합 (pkl/json)                          |
| **디자인**     | Liquid Glass SVG 아이콘 + 커스텀 CSS                     |
| **모드 시스템** | 듀얼 모드 (WMS 시뮬레이터 / 알고리즘 인사이트)           |

### 5.2 듀얼 모드 시스템

| 모드                    | 대상                       | 주요 기능                                    |
| ----------------------- | -------------------------- | -------------------------------------------- |
| **WMS 시뮬레이터**      | 비전공자/실무자            | 제품 선택, 파라미터 조정, What-If 시뮬레이션 |
| **알고리즘 인사이트**   | 데이터 분석가/ML 엔지니어 | 모델 해석, SHAP 분석, 피처 중요도, 용어 사전 |

### 5.3 UI/UX 특징

- **Liquid Glass 아이콘:** 15종 SVG 커스텀 아이콘 (그라디언트 + 글래스모피즘)
- **KPI 카드:** 아이콘 + 라벨 + 수치 + 팝오버 상세 정보
- **플로팅 리모컨 TOC:** 페이지 우측에 고정된 투명 미니 목차 (접기/펼치기, 앵커 이동)
- **커스텀 탭 시스템:** `session_state` 기반 탭 전환 + 동적 TOC 업데이트
- **사이드바 네비게이션:** 다크 테마, 현재 페이지 하이라이트

### 5.4 실행 방법

```bash
cd streamlit_wms
pip install -r requirements.txt
streamlit run app.py
# 브라우저에서 http://localhost:8501 접속
```

---

📚 참고 자료

**프로젝트 문서:**

| 문서                                       | 설명                               |
| ------------------------------------------ | ---------------------------------- |
| [`README.md`](README.md)                   | 프로젝트 전체 가이드 (본 문서)     |
| [`md/subtopic{1~4}_guideline.md`](md/)     | 소주제별 구현 가이드               |
| [`md/result_report/`](md/result_report/)   | 소주제별 최종 결과 보고서          |
| [`md/modification_summary/`](md/modification_summary/) | 수정/보완 결과 요약     |
| [`streamlit_wms/README.md`](streamlit_wms/README.md) | Streamlit WMS 상세 문서   |

**외부 자료:**

- 데이터셋: [Kaggle - Inventory Management E-Grocery](https://www.kaggle.com/datasets/fatihilhan/inventory-management-e-grocery)
- Scikit-learn: [https://scikit-learn.org/](https://scikit-learn.org/)
- XGBoost: [https://xgboost.readthedocs.io/](https://xgboost.readthedocs.io/)
- LightGBM: [https://lightgbm.readthedocs.io/](https://lightgbm.readthedocs.io/)
- SHAP: [https://shap.readthedocs.io/](https://shap.readthedocs.io/)
- Streamlit: [https://docs.streamlit.io/](https://docs.streamlit.io/)

---

<div align="center">

**KNU KDT 12기 AI/BigData — 미니 프로젝트 (Phase 8)**
팀 굿핏(good fit) · 2026.03

</div>
