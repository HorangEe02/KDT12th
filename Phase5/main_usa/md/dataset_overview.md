# USA 부동산 데이터셋 소개

본 문서는 `data/` 폴더에 포함된 각 데이터셋의 구조와 열(Column)의 의미를 설명합니다.

---

## 목차

1. [realtor-data.zip.csv](#1-realtor-datazipcsv)
2. [Zillow Economics Data](#2-zillow-economics-data)
   - [City_time_series.csv](#21-city_time_seriescsv)
   - [County_time_series.csv](#22-county_time_seriescsv)
   - [Metro_time_series.csv](#23-metro_time_seriescsv)
   - [State_time_series.csv](#24-state_time_seriescsv)
   - [Neighborhood_time_series.csv](#25-neighborhood_time_seriescsv)
   - [Zip_time_series.csv](#26-zip_time_seriescsv)
   - [cities_crosswalk.csv](#27-cities_crosswalkcsv)
   - [CountyCrossWalk_Zillow.csv](#28-countycrosswalk_zillowcsv)
   - [DataDictionary.csv](#29-datadictionarycsv)
3. [zillow_Housing Data](#3-zillow_housing-data)
   - [Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv](#31-주택-가치-지수-zhvi)
   - [Metro_zori_uc_sfrcondomfr_sm_month.csv](#32-임대-관측-지수-zori)
   - [Metro_invt_fs_uc_sfrcondo_sm_month.csv](#33-매물-재고량)
   - [Metro_market_temp_index_uc_sfrcondo_month.csv](#34-시장-온도-지수)
   - [Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv](#35-평균-매물-대기일수)
   - [Metro_sales_count_now_uc_sfrcondo_month.csv](#36-판매-건수)
   - [Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv](#37-신규-건설-판매-건수)
   - [Metro_new_homeowner_income_needed...csv](#38-신규-주택-구매-필요-소득)
   - [Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv](#39-주택-가치-예측-성장률)
   - [National_zorf_growth_uc_sfr_sm_month.csv](#310-전국-임대-예측-성장률)

---

## 1. realtor-data.zip.csv

**출처**: Realtor.com
**행 수**: 약 2,226,382건
**파일 크기**: 약 178MB
**설명**: 미국 전역의 부동산 매물 정보를 담은 데이터셋. 개별 매물 단위의 상세 정보를 포함합니다.

| 열 이름 | 데이터 타입 | 설명 |
|---------|-----------|------|
| `brokered_by` | float | 중개 업체 ID |
| `status` | string | 매물 상태 (예: `for_sale` - 판매 중) |
| `price` | float | 매물 가격 (USD) |
| `bed` | int | 침실 수 |
| `bath` | int | 욕실 수 |
| `acre_lot` | float | 부지 면적 (에이커 단위) |
| `street` | float | 도로 주소 ID |
| `city` | string | 도시명 |
| `state` | string | 주(State) 이름 |
| `zip_code` | int | 우편번호 |
| `house_size` | float | 주택 면적 (제곱피트, sqft) |
| `prev_sold_date` | string | 이전 판매일 |

---

## 2. Zillow Economics Data

**출처**: Zillow Research
**설명**: Zillow에서 제공하는 종합 부동산 경제 지표 데이터. 도시, 카운티, 메트로, 주, 동네, 우편번호 등 다양한 지역 레벨로 집계된 시계열 데이터입니다.

### 공통 지표 설명 (DataDictionary 기반)

아래 지표들은 시계열 CSV 파일들에서 공통적으로 사용됩니다:

| 지표 | 설명 |
|------|------|
| **ZHVI** (Zillow Home Value Index) | 특정 지역 및 주택 유형의 중간 추정 주택 가치를 계절 조정한 평활 지표 |
| **ZHVIPerSqft** | 제곱피트당 주택 가치 중간값 |
| **ZRI** (Zillow Rent Index) | 특정 지역 및 주택 유형의 중간 추정 임대료를 계절 조정한 평활 지표 |
| **ZriPerSqft** | 제곱피트당 월 추정 임대 가격 중간값 |
| **MedianListingPrice** | Zillow에 등록된 매물의 중간 호가 |
| **MedianListingPricePerSqft** | 제곱피트당 호가 중간값 |
| **MedianRentalPrice** | Zillow에 등록된 임대 매물의 중간 임대 가격 |
| **MedianRentalPricePerSqft** | 제곱피트당 임대 가격 중간값 |
| **MedianPctOfPriceReduction** | 가격 인하된 매물의 인하율 중간값 |
| **MedianPriceCutDollar** | 가격 인하된 매물의 인하 금액 중간값 (USD) |
| **InventorySeasonallyAdjusted** | 계절 조정된 매물 재고량 (월별 주간 스냅샷 중간값) |
| **InventoryRaw** | 비조정 매물 재고량 |
| **DaysOnZillow** | 해당 월에 판매된 주택의 시장 체류 일수 중간값 |
| **PctOfHomesDecreasingInValues** | 지난 1년간 가치가 하락한 주택의 비율 |
| **PctOfHomesIncreasingInValues** | 지난 1년간 가치가 상승한 주택의 비율 |
| **PctOfHomesSellingForGain** | 이전 판매가보다 높은 가격에 판매된 주택 비율 |
| **PctOfHomesSellingForLoss** | 이전 판매가보다 낮은 가격에 판매된 주택 비율 |
| **PctOfListingsWithPriceReductions** | 해당 월에 가격 인하가 있었던 매물 비율 |
| **PctOfListingsWithPriceReductionsSeasAdj** | 위 지표의 계절 조정 버전 |
| **PriceToRentRatio** | 주택 가치를 연간 임대료로 나눈 가격 대 임대료 비율 |
| **Sale_Counts** | 월별 주택 판매 건수 |
| **Sale_Counts_Seas_Adj** | 계절 조정된 월별 판매 건수 |
| **Sale_Prices** | 판매 가격 |

**주택 유형 접미사**:
- `_AllHomes`: 모든 주택 유형
- `_SingleFamilyResidence`: 단독 주택
- `_CondoCoop`: 콘도/협동조합
- `_DuplexTriplex`: 다세대 주택
- `_MultiFamilyResidence5PlusUnits`: 5가구 이상 다세대 주택

**침실 수 접미사**:
- `_1Bedroom` ~ `_5BedroomOrMore`: 침실 수별 분류
- `_Studio`: 원룸

**가격 계층 접미사**:
- `_BottomTier`: 하위 가격대 (하위 1/3)
- `_MiddleTier`: 중간 가격대 (중간 1/3)
- `_TopTier`: 상위 가격대 (상위 1/3)

---

### 2.1 City_time_series.csv

**파일 크기**: 약 689MB
**설명**: **도시(City)** 단위의 시계열 데이터. 1996년 4월부터 시작.

| 열 이름 | 설명 |
|---------|------|
| `Date` | 날짜 (YYYY-MM-DD) |
| `RegionName` | 도시명 (예: `abbottstownadamspa`) |
| 이후 열들 | 위 공통 지표 참조 (ZHVI, ZRI, MedianListingPrice 등 약 78개 지표) |

---

### 2.2 County_time_series.csv

**파일 크기**: 약 112MB
**설명**: **카운티(County)** 단위의 시계열 데이터. FIPS 코드로 지역 구분.

| 열 이름 | 설명 |
|---------|------|
| `Date` | 날짜 (YYYY-MM-DD) |
| `RegionName` | FIPS 코드 (예: `10001`, `10003`) |
| `DaysOnZillow_AllHomes` | 시장 체류 일수 중간값 |
| 이후 열들 | 위 공통 지표 참조 (약 80개 지표) |

---

### 2.3 Metro_time_series.csv

**파일 크기**: 약 56MB
**설명**: **대도시권(Metro/MSA)** 단위의 시계열 데이터. 가장 상세한 지표를 포함.

| 열 이름 | 설명 |
|---------|------|
| `Date` | 날짜 (YYYY-MM-DD) |
| `RegionName` | MSA 코드 (예: `10180`, `10220`) |
| `AgeOfInventory` | 매물 재고 나이 (활성 매물의 게시 일수 중간값) |
| `InventoryTierShare_*` | 가격 계층별 재고 비율 |
| `Sale_Counts_Msa` | MSA 기준 판매 건수 |
| 이후 열들 | 위 공통 지표 참조 (약 90개 지표) |

---

### 2.4 State_time_series.csv

**파일 크기**: 약 4.7MB
**설명**: **주(State)** 단위의 시계열 데이터.

| 열 이름 | 설명 |
|---------|------|
| `Date` | 날짜 (YYYY-MM-DD) |
| `RegionName` | 주 이름 (예: `Alabama`, `Arizona`) |
| 이후 열들 | 위 공통 지표 참조 (약 80개 지표) |

---

### 2.5 Neighborhood_time_series.csv

**파일 크기**: 약 265MB
**설명**: **동네(Neighborhood)** 단위의 시계열 데이터.

| 열 이름 | 설명 |
|---------|------|
| `Date` | 날짜 (YYYY-MM-DD) |
| `RegionName` | 동네 식별자 (예: `10007`, `10329`) |
| 이후 열들 | 위 공통 지표 참조 (약 76개 지표) |

---

### 2.6 Zip_time_series.csv

**파일 크기**: 약 782MB (가장 큰 파일)
**설명**: **우편번호(ZIP Code)** 단위의 시계열 데이터. 가장 세밀한 지역 단위.

| 열 이름 | 설명 |
|---------|------|
| `Date` | 날짜 (YYYY-MM-DD) |
| `RegionName` | 우편번호 (예: `01001`, `01002`) |
| 이후 열들 | 위 공통 지표 참조 (약 76개 지표) |

---

### 2.7 cities_crosswalk.csv

**파일 크기**: 약 1MB
**설명**: 도시-카운티-주 간 매핑 테이블. 시계열 데이터와 조인할 때 사용.

| 열 이름 | 설명 |
|---------|------|
| `Unique_City_ID` | 도시 고유 식별자 (예: `oak_grovechristianky`) |
| `City` | 도시명 (예: `Oak Grove`) |
| `County` | 카운티명 (예: `Christian`) |
| `State` | 주 약어 (예: `KY`) |

---

### 2.8 CountyCrossWalk_Zillow.csv

**파일 크기**: 약 232KB
**설명**: 카운티-주-메트로 지역 간 매핑 테이블. FIPS 코드, CBSA 코드, Zillow 내부 ID를 연결.

| 열 이름 | 설명 |
|---------|------|
| `CountyName` | 카운티명 (예: `Pike`) |
| `StateName` | 주명 (예: `Pennsylvania`) |
| `StateFIPS` | 주 FIPS 코드 (예: `42`) |
| `CountyFIPS` | 카운티 FIPS 코드 (예: `103`) |
| `MetroName_Zillow` | Zillow 대도시권 이름 (예: `New York, NY`) |
| `CBSAName` | CBSA(핵심기반통계지역) 이름 |
| `CountyRegionID_Zillow` | Zillow 카운티 지역 ID |
| `MetroRegionID_Zillow` | Zillow 메트로 지역 ID |
| `FIPS` | 전체 FIPS 코드 (주 + 카운티, 예: `42103`) |
| `CBSACode` | CBSA 코드 (예: `35620`) |

---

### 2.9 DataDictionary.csv

**설명**: 위 시계열 파일들에서 사용되는 모든 변수명과 정의를 정리한 데이터 사전.

---

## 3. zillow_Housing Data

**출처**: Zillow Research (최신 버전)
**설명**: Zillow에서 제공하는 최신 주택 시장 데이터. **메트로(MSA) 단위**로 제공되며, 열이 날짜(Wide Format) 형태로 구성된 것이 특징입니다.

### 공통 열 구조

모든 파일이 다음 식별 열을 공유합니다:

| 열 이름 | 설명 |
|---------|------|
| `RegionID` | Zillow 지역 고유 ID (예: `102001` = 미국 전체) |
| `SizeRank` | 지역 크기 순위 (0 = 미국 전체, 1 = 가장 큰 MSA) |
| `RegionName` | 지역명 (예: `United States`, `New York, NY`) |
| `RegionType` | 지역 유형 (`country`, `msa`) |
| `StateName` | 주 약어 (예: `NY`) |

식별 열 이후에 **날짜별 열** (예: `2000-01-31`, `2000-02-29`, ...) 이 이어지며, 각 셀에 해당 월의 지표 값이 기록됩니다.

---

### 3.1 주택 가치 지수 (ZHVI)
**파일**: `Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
**파일 크기**: 약 4.3MB
**기간**: 2000-01 ~ 2025-12
**설명**: Zillow Home Value Index. 중간 가격대(33~67% 분위) 단독주택/콘도의 **평활 계절 조정** 추정 주택 가치 중간값.
**단위**: USD (예: `120438.3` = $120,438)

---

### 3.2 임대 관측 지수 (ZORI)
**파일**: `Metro_zori_uc_sfrcondomfr_sm_month.csv`
**파일 크기**: 약 955KB
**기간**: 2015-01 ~ 2025-12
**설명**: Zillow Observed Rent Index. 단독주택/콘도/다세대 주택의 **평활 월별** 임대료 관측 지수.
**단위**: USD/월 (예: `1140.79` = 월 $1,140.79)

---

### 3.3 매물 재고량
**파일**: `Metro_invt_fs_uc_sfrcondo_sm_month.csv`
**파일 크기**: 약 557KB
**기간**: 2018-03 ~ 2025-12
**설명**: 매물로 등록된(For Sale) 단독주택/콘도의 **평활** 재고 수량.
**단위**: 건 (예: `1421529` = 약 142만 건)

---

### 3.4 시장 온도 지수
**파일**: `Metro_market_temp_index_uc_sfrcondo_month.csv`
**파일 크기**: 약 470KB
**기간**: 2018-01 ~ 2025-12
**설명**: 주택 시장의 과열/냉각 정도를 나타내는 지수. 값이 높을수록 **판매자 우위(Seller's Market)**, 낮을수록 **구매자 우위(Buyer's Market)**.
**단위**: 지수 (예: `50` = 균형 시장, `80+` = 과열 시장)

---

### 3.5 평균 매물 대기일수
**파일**: `Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv`
**파일 크기**: 약 266KB
**기간**: 2018-03 ~ 2025-12
**설명**: 매물이 게시된 후 계약 체결(Pending)까지 걸리는 **평균 일수**를 평활 처리한 값.
**단위**: 일 (예: `51` = 평균 51일)

---

### 3.6 판매 건수
**파일**: `Metro_sales_count_now_uc_sfrcondo_month.csv`
**파일 크기**: 약 140KB
**기간**: 2008-02 ~ 2025-12
**설명**: 단독주택/콘도의 월별 **실제 판매 건수**.
**단위**: 건 (예: `203871` = 약 20만 건)

---

### 3.7 신규 건설 판매 건수
**파일**: `Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv`
**파일 크기**: 약 181KB
**기간**: 2018-01 ~ 2025-11
**설명**: 신규 건설된 단독주택/콘도의 월별 **원시(비조정) 판매 건수**.
**단위**: 건 (예: `44892` = 약 4.5만 건)

---

### 3.8 신규 주택 구매 필요 소득
**파일**: `Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
**파일 크기**: 약 1.2MB
**기간**: 2012-01 ~ 2025-12
**설명**: 중간 가격대 주택을 **계약금 20%** 조건으로 구매하기 위해 필요한 **연간 소득** 추정치. 평활 계절 조정.
**단위**: USD/년 (예: `36613.03` = 연 $36,613)

---

### 3.9 주택 가치 예측 성장률
**파일**: `Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
**파일 크기**: 약 50KB
**설명**: Zillow에서 예측한 주택 가치 **성장률(%)**.

| 특수 열 | 설명 |
|---------|------|
| `BaseDate` | 예측 기준일 (예: `2025-12-31`) |
| 날짜 열 (`2026-01-31` 등) | 기준일 대비 누적 예측 성장률 (%) |

**단위**: % (예: `0.3` = 0.3%, `2.1` = 2.1%)

---

### 3.10 전국 임대 예측 성장률
**파일**: `National_zorf_growth_uc_sfr_sm_month.csv`
**파일 크기**: 약 136B (매우 작음, 전국 1행만 존재)
**설명**: **미국 전체** 단독주택 임대료의 예측 성장률.

| 특수 열 | 설명 |
|---------|------|
| `BaseDate` | 예측 기준일 |
| 날짜 열 | 기준일 대비 누적 예측 성장률 (%) |

**단위**: % (예: `0.2` = 0.2%, `1.6` = 1.6%)

---

## 데이터 관계도

```
┌──────────────────────────────────────────────────────────┐
│                    Crosswalk Tables                       │
│  cities_crosswalk.csv ←→ City_time_series.csv            │
│  CountyCrossWalk_Zillow.csv ←→ County_time_series.csv    │
│                            ←→ Metro_time_series.csv      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              Zillow Economics Data (Long Format)          │
│  행: 날짜 × 지역  |  열: 지표명                          │
│                                                          │
│  City  →  County  →  Metro  →  State (세분화 수준)       │
│  Zip   →  Neighborhood (별도 지역 체계)                  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              zillow_Housing Data (Wide Format)            │
│  행: 지역  |  열: 날짜별 값                               │
│  Metro(MSA) 단위 집계                                     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              realtor-data.zip.csv                         │
│  개별 매물 단위 (약 222만 건)                             │
│  Zillow 데이터와 city, state, zip_code로 연결 가능       │
└──────────────────────────────────────────────────────────┘
```

---

## 요약

| 데이터셋 | 지역 단위 | 데이터 형태 | 주요 내용 | 기간 |
|----------|----------|------------|----------|------|
| realtor-data.zip.csv | 개별 매물 | 개별 레코드 | 매물 가격, 규모, 위치 | - |
| City_time_series.csv | 도시 | Long (행=날짜×지역) | 종합 부동산 지표 | 1996~ |
| County_time_series.csv | 카운티 | Long | 종합 부동산 지표 | 1996~ |
| Metro_time_series.csv | 대도시권(MSA) | Long | 종합 부동산 지표 (가장 상세) | 1996~ |
| State_time_series.csv | 주 | Long | 종합 부동산 지표 | 1996~ |
| Neighborhood_time_series.csv | 동네 | Long | 종합 부동산 지표 | 1996~ |
| Zip_time_series.csv | 우편번호 | Long | 종합 부동산 지표 | 1996~ |
| Metro_zhvi_*.csv | MSA | Wide (행=지역) | 주택 가치 지수 | 2000~ |
| Metro_zori_*.csv | MSA | Wide | 임대 관측 지수 | 2015~ |
| Metro_invt_*.csv | MSA | Wide | 매물 재고량 | 2018~ |
| Metro_market_temp_*.csv | MSA | Wide | 시장 온도 지수 | 2018~ |
| Metro_mean_doz_*.csv | MSA | Wide | 매물 대기일수 | 2018~ |
| Metro_sales_count_*.csv | MSA | Wide | 판매 건수 | 2008~ |
| Metro_new_con_*.csv | MSA | Wide | 신규 건설 판매 건수 | 2018~ |
| Metro_new_homeowner_*.csv | MSA | Wide | 주택 구매 필요 소득 | 2012~ |
| Metro_zhvf_growth_*.csv | MSA | Wide | 주택 가치 예측 성장률 | 예측 |
| National_zorf_growth_*.csv | 전국 | Wide | 임대 예측 성장률 | 예측 |
