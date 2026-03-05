# 내륙 거점 도시의 부동산 시장 구조 비교: 대구 vs 미국 유사 도시
## 🔒 Kaggle + Zillow 통합 데이터 프로젝트 (v2)

---

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **주제** | 내륙 거점 도시의 부동산 시장 구조 비교 분석 |
| **DB** | MySQL (172.30.1.47, user: wonho, pw: 1111) |
| **언어** | Python (pymysql, pandas) |
| **🇺🇸 미국 데이터** | `data/` 폴더 CSV (Realtor.com + Zillow Economics + zillow_Housing) |
| **🇰🇷 한국 데이터** | Kaggle CSV |
| **🌍 글로벌 데이터** | Kaggle CSV |

### v1 → v2 주요 변경사항

| 항목 | v1 (기존) | v2 (변경) |
|------|----------|----------|
| 미국 주택 데이터 | Kaggle 5개 데이터셋 | `data/` 폴더 통합 데이터셋 (Realtor 222만건 + Zillow 시계열 + Zillow 최신) |
| 지역 해상도 | MSA 단위 위주 | ZIP → City → County → Metro → State 다계층 |
| 시계열 깊이 | 2018~2024 위주 | 1996~2025 (최대 29년) |
| 지표 다양성 | ZHVI, 매물가 위주 | ZHVI, ZORI, 재고량, 시장온도, 대기일수, 판매건수, 필요소득, 예측성장률 등 |
| 한국/글로벌 | 동일 | 동일 (Kaggle 유지) |

---

## 🏙️ 도시 매칭 테이블

| 비교축 | 대구 ↔ 미국 도시 | 매칭 근거 |
|--------|------------------|-----------|
| 종합 | 대구 ↔ **Dallas** | 내륙 대도시, 보수적, 여름 고온 |
| 산업 | 대구 ↔ **Atlanta** | 자동차·배터리 허브, 교통 결절점 |
| 기후 | 대구 ↔ **Phoenix** | 극심한 여름 더위, 분지 지형 |
| 변모 | 대구 ↔ **Charlotte** | 섬유→하이테크/금융 전환 |

---

## 📂 미국 데이터 소스 총괄 (`data/` 폴더)

### A. Realtor.com 개별 매물 데이터

| 파일 | 행 수 | 크기 | 핵심 열 |
|------|------|------|---------|
| `realtor-data.zip.csv` | ~2,226,382 | 178MB | price, bed, bath, acre_lot, house_size, city, state, zip_code, prev_sold_date |

### B. Zillow Economics Data (Long Format: 행 = 날짜 × 지역)

| 파일 | 지역 단위 | 크기 | 지표 수 | 프로젝트 활용도 |
|------|----------|------|---------|---------------|
| `State_time_series.csv` | 주(State) | 4.7MB | ~80 | ⭐ 주 단위 거시 트렌드 |
| `Metro_time_series.csv` | 대도시권(MSA) | 56MB | ~90 | ⭐ 4개 비교 도시 MSA 분석 |
| `City_time_series.csv` | 도시 | 689MB | ~78 | ⭐ 도시별 세부 분석 |
| `County_time_series.csv` | 카운티 | 112MB | ~80 | 카운티 단위 보조 분석 |
| `Zip_time_series.csv` | 우편번호 | 782MB | ~76 | 소주제3 ZIP별 가격격차 |
| `Neighborhood_time_series.csv` | 동네 | 265MB | ~76 | 동네 단위 미세 분석 (선택) |
| `cities_crosswalk.csv` | 매핑 | 1MB | - | 도시↔카운티↔주 조인 키 |
| `CountyCrossWalk_Zillow.csv` | 매핑 | 232KB | - | 카운티↔MSA↔FIPS 조인 키 |
| `DataDictionary.csv` | 사전 | - | - | 변수명 정의 참조 |

**공통 핵심 지표 (78~90개 중 프로젝트 핵심):**

| 지표 | 설명 | 활용 소주제 |
|------|------|-----------|
| ZHVI_AllHomes | 전체 주택 중간 가치 (계절조정) | 1, 3 |
| ZHVIPerSqft_AllHomes | sqft당 주택 가치 | 1, 3 |
| ZRI_AllHomes | 전체 주택 임대료 지수 (계절조정) | 1 |
| MedianListingPrice_AllHomes | 매물 중간 호가 | 1, 3 |
| MedianRentalPrice_AllHomes | 임대 중간 가격 | 1 |
| InventorySeasonallyAdjusted | 매물 재고량 (계절조정) | 2 |
| DaysOnZillow_AllHomes | 시장 체류 일수 중간값 | 2 |
| Sale_Counts | 월별 판매 건수 | 2 |
| PriceToRentRatio_AllHomes | 가격 대 임대료 비율 | 1 |
| PctOfHomesIncreasingInValues | 가치 상승 주택 비율 | 1, 4 |
| PctOfHomesSellingForLoss | 손해 판매 비율 | 4 |
| PctOfListingsWithPriceReductions | 가격 인하 매물 비율 | 2, 4 |
| MedianPctOfPriceReduction | 가격 인하율 중간값 | 2, 4 |

### C. zillow_Housing Data (Wide Format: 행 = 지역, 열 = 날짜)

| 파일 | 지표 | 기간 | 크기 | 활용 소주제 |
|------|------|------|------|-----------|
| `Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv` | 주택가치지수(ZHVI) | 2000~2025 | 4.3MB | ⭐ 1 |
| `Metro_zori_uc_sfrcondomfr_sm_month.csv` | 임대관측지수(ZORI) | 2015~2025 | 955KB | ⭐ 1 |
| `Metro_invt_fs_uc_sfrcondo_sm_month.csv` | 매물재고량 | 2018~2025 | 557KB | ⭐ 2 |
| `Metro_market_temp_index_uc_sfrcondo_month.csv` | 시장온도지수 | 2018~2025 | 470KB | ⭐ 2 |
| `Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv` | 평균 대기일수 | 2018~2025 | 266KB | 2 |
| `Metro_sales_count_now_uc_sfrcondo_month.csv` | 판매 건수 | 2008~2025 | 140KB | ⭐ 2 |
| `Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv` | 신규건설 판매건수 | 2018~2025 | 181KB | 4 |
| `Metro_new_homeowner_income_needed_...csv` | 주택구매 필요소득 | 2012~2025 | 1.2MB | ⭐ 2, 4 |
| `Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv` | 주택가치 예측성장률 | 예측 | 50KB | 1 |
| `National_zorf_growth_uc_sfr_sm_month.csv` | 전국 임대 예측성장률 | 예측 | 136B | 1 |

---

## 📊 소주제별 데이터셋 매핑

---

### 소주제 1: 주택 가격 추이 비교 (Housing Price Trends)

**분석 목표:** 3~25년간 주거용 부동산 가격 패턴 비교 (v1 대비 시계열 대폭 확장)

#### 🇰🇷 한국(대구) 데이터 — Kaggle

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| K1-1 | ⭐ Daegu Apartment Actual Transaction | `lnoahl/daegu-aptmernt-actual-transaction` | 대구 아파트 실거래가 (핵심) |
| K1-2 | ⭐ Daegu Real Estate Data | `afifanuraini/daegu-real-estate-datacsv` | 대구 부동산 데이터 |
| K1-3 | Korean Apartment Deal Data | `brainer3220/korean-real-estate-transaction-data` | 전국 아파트 거래 (대구 필터링) |
| K1-4 | Korea House Data 10yrs | `gunhee/koreahousedata` | 10년간 주택 데이터 |

#### 🇺🇸 미국 데이터 — `data/` 폴더

| # | 파일명 | 형태 | 활용 내용 |
|---|--------|------|----------|
| D1-1 | ⭐ `realtor-data.zip.csv` | 개별매물 | Dallas/Atlanta/Phoenix/Charlotte 매물별 가격·면적·침실수 분석 |
| D1-2 | ⭐ `Metro_zhvi_...month.csv` | Wide | 4개 MSA ZHVI 2000~2025 (25년 추이) |
| D1-3 | ⭐ `Metro_zori_...month.csv` | Wide | 4개 MSA 임대료 2015~2025 |
| D1-4 | `Metro_time_series.csv` | Long | MSA별 ZHVI, ZRI, MedianListingPrice, PriceToRentRatio 등 종합 |
| D1-5 | `State_time_series.csv` | Long | TX/GA/AZ/NC 주 단위 거시 비교 |
| D1-6 | `City_time_series.csv` | Long | 도시 단위 세부 추이 (Dallas, Atlanta 등) |
| D1-7 | `Metro_zhvf_growth_...month.csv` | Wide | 4개 MSA 주택가치 예측 성장률 |
| D1-8 | `National_zorf_growth_...month.csv` | Wide | 전국 임대 예측 성장률 |

#### 핵심 지표 & 분석 포인트
- 월/분기별 ZHVI, 중위가격, 전년동기 대비 변동률 (1996~2025 장기 추세)
- COVID 전후 급등 패턴: 대구 vs 4개 미국 도시 시계열 오버레이
- 금리 인상(2022~) 영향: 가격 인하 매물 비율(PctOfListingsWithPriceReductions) 비교
- PriceToRentRatio 비교 → 투자 vs 실수요 시장 성격 판별
- 주택 유형별(AllHomes, SingleFamily, Condo) 가격 차이 분석

---

### 소주제 2: 인구 이동과 주택 수요 (Population & Housing Demand)

**분석 목표:** 인구 변동과 부동산 가격/거래량/수급 상관관계

#### 🇰🇷 한국(대구) 데이터 — Kaggle

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| K2-1 | ⭐ Korean Demographics 2000-2022 | `alexandrepetit881234/korean-demographics-20002022` | 한국 인구통계 22년간 (시도별) |
| K2-2 | Korea Income and Welfare | `hongsean/korea-income-and-welfare` | 지역별 소득·복지 데이터 |

#### 🇺🇸 미국 데이터 — Kaggle + `data/` 폴더

**인구 데이터 (Kaggle):**

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| U2-1 | ⭐ US Census Demographic Data | `muonneutrino/us-census-demographic-data` | County/Tract 인구통계 (핵심) |
| U2-2 | Population Time Series Data | `census/population-time-series-data` | 인구 시계열 |
| U2-3 | US County & Zipcode Historical Demographics | `bitrook/us-county-historical-demographics` | County별 역사적 인구통계 |
| U2-4 | US County Data | `evangambit/us-county-data` | County 종합 데이터 |

**수요 지표 (`data/` 폴더):**

| # | 파일명 | 활용 내용 |
|---|--------|----------|
| D2-1 | ⭐ `Metro_invt_fs_...month.csv` | 4개 MSA 매물 재고량 2018~2025 → 공급 측 |
| D2-2 | ⭐ `Metro_sales_count_...month.csv` | 4개 MSA 판매 건수 2008~2025 → 수요 측 |
| D2-3 | ⭐ `Metro_market_temp_index_...month.csv` | 시장온도지수 → 과열/냉각 판별 |
| D2-4 | `Metro_mean_doz_pending_...month.csv` | 평균 대기일수 → 수요 강도 |
| D2-5 | ⭐ `Metro_new_homeowner_income_needed_...csv` | 주택구매 필요소득 → 구매 진입장벽 |
| D2-6 | `Metro_time_series.csv` | InventorySeasonallyAdjusted, Sale_Counts, DaysOnZillow 등 |

#### 🌍 글로벌/보완 데이터 — Kaggle

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| G2-1 | World Population Growth Rate by Cities 2024 | `dataanalyst001/world-population-growth-rate-by-cities-2024` | 대구·Dallas 등 도시별 인구성장률 |
| G2-2 | World Cities Database | `max-mind/world-cities-database` | 도시 인구·좌표 정보 |

#### 핵심 지표 & 분석 포인트
- 인구증감률 vs ZHVI 변동률 상관계수 (대구: 인구유출 vs Dallas/Atlanta: 인구유입)
- 시장온도지수(Market Temp Index)로 과열/냉각 국면 비교
- 재고량(Inventory) × 판매건수(Sales Count) → 수급 균형 지표 산출
- 주택구매 필요소득(Income Needed) 추이 → 구매력 격차 시계열 비교
- 평균 대기일수(Days on Zillow) → 수요 흡수 속도 비교

---

### 소주제 3: 기후·입지와 지역별 가격 격차 (Climate & Regional Price Variance)

**분석 목표:** 내륙/분지 도시 특성(폭염, 교통)이 구/ZIP Code별 가격 격차에 미치는 영향

#### 🌡️ 기후 데이터 — Kaggle (한국+미국 공통)

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| C3-1 | ⭐ Climate Change: Earth Surface Temperature (Berkeley) | `berkeleyearth/climate-change-earth-surface-temperature-data` | GlobalLandTemperaturesByCity.csv → 대구+4개 미국도시 포함 (1750~2013) |
| C3-2 | ⭐ Daily Temperature of Major Cities | `sudalairajkumar/daily-temperature-of-major-cities` | 전 세계 주요 도시 일별 기온 |
| C3-3 | Historical Hourly Weather Data 2012-2017 | `selfishgene/historical-hourly-weather-data` | 시간별 기상 (미국 4도시 포함) |
| C3-4 | Monthly Mean Temp US Cities 1948-2022 | `garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022` | 미국 도시 월평균 기온 74년간 |
| C3-5 | US Weather Events 2016-2022 | `sobhanmoosavi/us-weather-events` | 미국 기상 이벤트 (폭염 등) |
| C3-6 | Global Daily Climate Data | `guillemservera/global-daily-climate-data` | 글로벌 일별 기후 |

#### 🏠 지역별 가격 데이터 — `data/` 폴더 + Kaggle

| # | 데이터 | 활용 방법 |
|---|--------|----------|
| D3-1 | ⭐ `realtor-data.zip.csv` | **ZIP Code별 가격 분석** — Dallas/Phoenix/Atlanta/Charlotte 222만건 매물에서 zip_code별 price, house_size 집계 |
| D3-2 | ⭐ `Zip_time_series.csv` | **ZIP Code별 시계열** — ZHVI, MedianListingPrice 등 ZIP 단위 장기 추이 |
| D3-3 | `City_time_series.csv` | 도시 단위 가격 추이 (기후 데이터와 시간축 매칭) |
| D3-4 | `Metro_time_series.csv` | MSA 단위 가격 분포 보조 |
| D3-5 | K1-1 대구 아파트 실거래가 (Kaggle) | 구별(수성구, 달서구 등) 가격 분석 |

#### 핵심 지표 & 분석 포인트
- ZIP Code / 구별 평균가, 여름 최고기온, 폭염일수, 도심 접근성
- Phoenix 열섬지대 vs 대구 수성구 쾌적 프리미엄 → 분지 도시 공통 패턴
- 기온-가격 히트맵: 여름 기온 상위 ZIP vs 하위 ZIP의 ZHVI 격차
- **v2 강화:** ZIP 단위 782MB 시계열로 미세 지역 가격 격차 분석 가능

---

### 소주제 4: 산업 전환과 부동산 (Industrial Transformation & Real Estate)

**분석 목표:** 전통 산업(섬유)→하이테크 전환이 상업/주거용 부동산에 미치는 영향

#### 🇺🇸 미국 고용·산업 데이터 — Kaggle

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| U4-1 | ⭐ BLS National Employment, Hours, Earnings | `bls/employment` | 산업별 고용 (핵심) |
| U4-2 | USA Bureau of Labor Statistics BigQuery | `bls/bls` | BLS 종합 데이터 |

#### 🇺🇸 미국 부동산 영향 데이터 — `data/` 폴더

| # | 파일명 | 활용 내용 |
|---|--------|----------|
| D4-1 | ⭐ `Metro_new_con_sales_count_...month.csv` | Charlotte/Atlanta/Dallas 신규건설 판매건수 → 산업전환에 따른 개발 활성화 |
| D4-2 | ⭐ `Metro_new_homeowner_income_needed_...csv` | 주택구매 필요소득 변화 → 산업전환에 따른 소득수준 변화 반영 |
| D4-3 | `Metro_market_temp_index_...month.csv` | 시장온도지수 → 산업전환 전후 시장 과열/냉각 비교 |
| D4-4 | `Metro_time_series.csv` | PctOfHomesIncreasingInValues, PctOfHomesSellingForLoss → 전환기 시장 건전성 |
| D4-5 | `State_time_series.csv` | TX/GA/AZ/NC 주 단위 거시 트렌드 보조 |

#### 🌍 글로벌/보완 데이터 — Kaggle

| # | 데이터셋명 | Kaggle ID | 비고 |
|---|-----------|-----------|------|
| G4-1 | ⭐ Global Economy Indicators | `prasad22/global-economy-indicators` | 국가별 경제지표 (한국 포함) |
| G4-2 | Macro-Economic Indicators (Country-Level) | `veselagencheva/macro-economic-indicators-dataset-country-level` | 거시경제 지표 |
| G4-3 | World GDP by Country, Region | `sazidthe1/world-gdp-data` | GDP 데이터 |

#### ⚠️ 소주제 4 한국 산업 데이터 한계 및 대안

Kaggle에 **대구 시도별 산업·고용 데이터**가 직접적으로 없으므로 다음 전략 사용:

1. **K2-1 Korean Demographics 2000-2022** → 지역별 경제활동인구, 고용률 추출
2. **K2-2 Korea Income and Welfare** → 지역별 산업분류 소득 데이터 활용
3. **K1-1~K1-4 주택 데이터** → 산업단지 인근 지역 가격 변화 프록시로 활용
4. **G4-1 Global Economy Indicators** → 한국 전체 제조업→서비스업 전환 거시 트렌드

#### 핵심 지표 & 분석 포인트
- 산업별 고용 변동(제조→서비스→하이테크) vs 신규건설 판매건수 상관
- Charlotte 섬유→금융 전환기: 시장온도지수 + 필요소득 변화 추이
- 대구 섬유→하이테크 진행 중인 전환: 구별 가격 차별화 패턴
- **v2 강화:** 신규건설 판매건수, 필요소득, 시장온도지수로 산업전환 영향을 다차원 분석

---

## 🗄️ 데이터베이스 스키마

### 데이터베이스: `real_estate_comparison`

```sql
-- =============================================
-- 마스터 테이블
-- =============================================

CREATE TABLE cities (
    city_id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(50) NOT NULL,
    country VARCHAR(20) NOT NULL,
    category VARCHAR(30),
    comparison_pair VARCHAR(50),
    population BIGINT,
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6)
);

CREATE TABLE data_sources (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(200) NOT NULL,
    source_url VARCHAR(500),
    kaggle_dataset_id VARCHAR(200),
    data_format VARCHAR(20) DEFAULT 'CSV',
    source_type ENUM('kaggle', 'data_folder') DEFAULT 'kaggle',
    file_path VARCHAR(300),
    description TEXT,
    sub_topic INT
);

-- Zillow 지역 매핑 (Crosswalk)
CREATE TABLE zillow_region_crosswalk (
    id INT AUTO_INCREMENT PRIMARY KEY,
    county_name VARCHAR(100),
    state_name VARCHAR(50),
    state_fips VARCHAR(5),
    county_fips VARCHAR(5),
    fips VARCHAR(10),
    metro_name_zillow VARCHAR(200),
    cbsa_name VARCHAR(200),
    cbsa_code VARCHAR(10),
    county_region_id_zillow INT,
    metro_region_id_zillow INT
);

CREATE TABLE cities_crosswalk (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unique_city_id VARCHAR(200),
    city VARCHAR(100),
    county VARCHAR(100),
    state VARCHAR(10)
);

-- =============================================
-- 소주제 1: 주택 가격 추이
-- =============================================

-- 대구 주택 가격 (Kaggle)
CREATE TABLE daegu_housing_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year_month VARCHAR(7),
    district VARCHAR(30),
    apt_name VARCHAR(100),
    exclusive_area DECIMAL(10,2),
    deal_amount BIGINT,
    floor INT,
    build_year INT,
    deal_type VARCHAR(20),
    source_dataset VARCHAR(100)
);

-- 미국 개별 매물 (realtor-data.zip.csv)
CREATE TABLE us_realtor_listings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    brokered_by DOUBLE,
    status VARCHAR(30),
    price DECIMAL(15,2),
    bed INT,
    bath INT,
    acre_lot DECIMAL(10,4),
    street DOUBLE,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    house_size DECIMAL(12,2),
    prev_sold_date VARCHAR(20),
    FOREIGN KEY (city_id) REFERENCES cities(city_id),
    INDEX idx_city_state (city, state),
    INDEX idx_zip (zip_code)
);

-- 미국 MSA 주택가치지수 ZHVI (zillow_Housing Wide → Long 변환 후 적재)
CREATE TABLE us_metro_zhvi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    size_rank INT,
    region_name VARCHAR(200),
    region_type VARCHAR(30),
    state_name VARCHAR(10),
    year_month VARCHAR(7),
    zhvi DECIMAL(15,2),
    INDEX idx_region_date (region_name, year_month)
);

-- 미국 MSA 임대관측지수 ZORI
CREATE TABLE us_metro_zori (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    region_name VARCHAR(200),
    state_name VARCHAR(10),
    year_month VARCHAR(7),
    zori DECIMAL(12,2),
    INDEX idx_region_date (region_name, year_month)
);

-- Zillow Economics 시계열 (Long Format, Metro/City/State 레벨)
CREATE TABLE zillow_timeseries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    region_name VARCHAR(200),
    region_level ENUM('city', 'county', 'metro', 'state', 'zip', 'neighborhood'),
    zhvi_all DECIMAL(15,2),
    zhvi_per_sqft DECIMAL(10,2),
    zri_all DECIMAL(12,2),
    median_listing_price DECIMAL(15,2),
    median_rental_price DECIMAL(12,2),
    inventory_seasonally_adj INT,
    days_on_zillow DECIMAL(8,2),
    sale_counts INT,
    sale_counts_seas_adj INT,
    price_to_rent_ratio DECIMAL(8,4),
    pct_homes_increasing DECIMAL(8,4),
    pct_homes_decreasing DECIMAL(8,4),
    pct_homes_selling_for_loss DECIMAL(8,4),
    pct_listings_price_reduction DECIMAL(8,4),
    median_pct_price_reduction DECIMAL(8,4),
    source_file VARCHAR(100),
    INDEX idx_region_date (region_name, date),
    INDEX idx_level_date (region_level, date)
);

-- =============================================
-- 소주제 2: 인구 이동과 주택 수요
-- =============================================

CREATE TABLE korean_demographics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT,
    region VARCHAR(50),
    total_population BIGINT,
    population_change BIGINT,
    population_change_rate DECIMAL(8,4),
    birth_rate DECIMAL(8,4),
    death_rate DECIMAL(8,4),
    economic_activity_rate DECIMAL(8,4),
    source_dataset VARCHAR(100)
);

CREATE TABLE us_demographics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    county VARCHAR(100),
    state VARCHAR(50),
    total_population BIGINT,
    population_change_rate DECIMAL(8,4),
    median_income DECIMAL(15,2),
    unemployment_rate DECIMAL(8,4),
    poverty_rate DECIMAL(8,4),
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

CREATE TABLE city_population_growth (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100),
    country VARCHAR(50),
    population_2023 BIGINT,
    population_2024 BIGINT,
    growth_rate DECIMAL(8,4),
    source_dataset VARCHAR(100)
);

-- 미국 MSA 수요 지표 (zillow_Housing Wide → Long 변환 후 적재)
CREATE TABLE us_metro_demand (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    region_name VARCHAR(200),
    state_name VARCHAR(10),
    year_month VARCHAR(7),
    inventory_count INT,
    market_temp_index DECIMAL(8,2),
    mean_days_pending DECIMAL(8,2),
    sales_count INT,
    new_construction_sales INT,
    income_needed DECIMAL(15,2),
    INDEX idx_region_date (region_name, year_month)
);

CREATE TABLE migration_housing_correlation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    year INT,
    population_change_rate DECIMAL(8,4),
    avg_housing_price DECIMAL(15,2),
    transaction_count INT,
    market_temp_index DECIMAL(8,2),
    inventory_count INT,
    correlation_coefficient DECIMAL(8,4),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

-- =============================================
-- 소주제 3: 기후·입지와 가격 격차
-- =============================================

CREATE TABLE climate_temperature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100),
    country VARCHAR(50),
    year_month VARCHAR(7),
    avg_temperature DECIMAL(8,3),
    avg_temp_uncertainty DECIMAL(8,3),
    latitude VARCHAR(20),
    longitude VARCHAR(20),
    source_dataset VARCHAR(100)
);

CREATE TABLE daily_temperature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100),
    country VARCHAR(50),
    date DATE,
    avg_temp_fahrenheit DECIMAL(8,2),
    avg_temp_celsius DECIMAL(8,2),
    source_dataset VARCHAR(100)
);

CREATE TABLE daegu_district_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year_month VARCHAR(7),
    district VARCHAR(30),
    avg_price BIGINT,
    transaction_count INT,
    avg_area DECIMAL(10,2),
    source_dataset VARCHAR(100)
);

-- ZIP Code별 가격 (realtor-data + Zip_time_series 통합)
CREATE TABLE us_zipcode_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    zip_code VARCHAR(10),
    city_name VARCHAR(50),
    state VARCHAR(10),
    year_month VARCHAR(7),
    zhvi DECIMAL(15,2),
    median_listing_price DECIMAL(15,2),
    avg_deal_price DECIMAL(15,2),
    listing_count INT,
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id),
    INDEX idx_zip_date (zip_code, year_month)
);

-- =============================================
-- 소주제 4: 산업 전환과 부동산
-- =============================================

CREATE TABLE us_industry_employment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    city_name VARCHAR(50),
    year INT,
    month INT,
    industry_code VARCHAR(20),
    industry_name VARCHAR(200),
    employee_count BIGINT,
    avg_weekly_hours DECIMAL(8,2),
    avg_hourly_earnings DECIMAL(10,2),
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

CREATE TABLE economic_indicators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(50),
    year INT,
    gdp DECIMAL(20,2),
    gdp_growth_rate DECIMAL(8,4),
    manufacturing_pct DECIMAL(8,4),
    services_pct DECIMAL(8,4),
    unemployment_rate DECIMAL(8,4),
    source_dataset VARCHAR(100)
);

-- 미국 MSA 주택가치 예측 성장률
CREATE TABLE us_metro_zhvf_growth (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    region_name VARCHAR(200),
    state_name VARCHAR(10),
    base_date DATE,
    forecast_date DATE,
    growth_rate DECIMAL(8,4),
    INDEX idx_region (region_name)
);

CREATE TABLE industry_housing_impact (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    year INT,
    dominant_industry VARCHAR(100),
    industry_employee_change DECIMAL(8,4),
    housing_price_change DECIMAL(8,4),
    new_construction_sales_change DECIMAL(8,4),
    market_temp_change DECIMAL(8,2),
    income_needed_change DECIMAL(8,4),
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);
```

---

## 🐍 Python 구현 코드

```python
import pymysql
import pandas as pd
import numpy as np
import os
import glob

# =============================================
# 1. DB 연결 설정
# =============================================

DB_CONFIG = {
    'host': '172.30.1.47',
    'user': 'wonho',
    'password': '1111',
    'charset': 'utf8mb4'
}
DB_NAME = 'real_estate_comparison'

DATA_DIR = 'data/'                    # data/ 폴더 경로
KAGGLE_DIR = 'kaggle_data/'           # Kaggle 다운로드 경로
ZILLOW_HOUSING_DIR = f'{DATA_DIR}zillow_Housing/'
ZILLOW_ECONOMICS_DIR = f'{DATA_DIR}Zillow_Economics/'

def get_connection(db_name=None):
    config = DB_CONFIG.copy()
    if db_name:
        config['db'] = db_name
    return pymysql.connect(**config)

# =============================================
# 2. DB 및 테이블 생성
# =============================================

def create_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4")
    conn.commit()
    conn.close()
    print(f"✅ 데이터베이스 '{DB_NAME}' 생성 완료")

def create_all_tables():
    """위 스키마의 모든 테이블 생성"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    # (위 SQL 스키마의 각 CREATE TABLE 문을 cursor.execute()로 실행)
    # ... 생략 (위 스키마 참조)
    conn.commit()
    conn.close()
    print("✅ 모든 테이블 생성 완료")

# =============================================
# 3. 초기 도시 데이터 삽입
# =============================================

def insert_cities():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cities = [
        ('대구', 'South Korea', '종합/기준', None, 2385412, 35.8714, 128.6014),
        ('Dallas', 'USA', '종합', '대구-Dallas', 1304379, 32.7767, -96.7970),
        ('Atlanta', 'USA', '산업', '대구-Atlanta', 498715, 33.7490, -84.3880),
        ('Phoenix', 'USA', '기후', '대구-Phoenix', 1608139, 33.4484, -112.0740),
        ('Charlotte', 'USA', '변모', '대구-Charlotte', 879709, 35.2271, -80.8431),
    ]
    sql = """INSERT INTO cities 
             (city_name, country, category, comparison_pair, population, latitude, longitude)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    cursor.executemany(sql, cities)
    conn.commit()
    conn.close()
    print("✅ 도시 데이터 삽입 완료")

# =============================================
# 4. 데이터 소스 등록
# =============================================

def insert_data_sources():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    sources = [
        # ===== data/ 폴더 소스 (미국) =====
        # Realtor.com
        ('Realtor.com USA Real Estate', None, None, 'CSV', 'data_folder',
         'data/realtor-data.zip.csv', '미국 222만건 개별 매물 (가격, 면적, 위치)', 1),
        
        # zillow_Housing Data (Wide)
        ('Zillow ZHVI Metro Monthly', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
         'MSA 주택가치지수 2000-2025', 1),
        ('Zillow ZORI Metro Monthly', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_zori_uc_sfrcondomfr_sm_month.csv',
         'MSA 임대관측지수 2015-2025', 1),
        ('Zillow Inventory Metro Monthly', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_invt_fs_uc_sfrcondo_sm_month.csv',
         'MSA 매물재고량 2018-2025', 2),
        ('Zillow Market Temp Index Metro', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_market_temp_index_uc_sfrcondo_month.csv',
         'MSA 시장온도지수 2018-2025', 2),
        ('Zillow Mean Days Pending Metro', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv',
         'MSA 평균대기일수 2018-2025', 2),
        ('Zillow Sales Count Metro', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_sales_count_now_uc_sfrcondo_month.csv',
         'MSA 판매건수 2008-2025', 2),
        ('Zillow New Construction Sales', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv',
         'MSA 신규건설 판매건수 2018-2025', 4),
        ('Zillow Income Needed Metro', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
         'MSA 주택구매 필요소득 2012-2025', 2),
        ('Zillow ZHVF Growth Metro', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
         'MSA 주택가치 예측성장률', 1),
        ('Zillow National ZORF Growth', None, None, 'CSV', 'data_folder',
         'data/zillow_Housing/National_zorf_growth_uc_sfr_sm_month.csv',
         '전국 임대 예측성장률', 1),
        
        # Zillow Economics Data (Long)
        ('Zillow Metro Time Series', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/Metro_time_series.csv',
         'MSA 종합 시계열 ~90 지표 1996-', 1),
        ('Zillow State Time Series', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/State_time_series.csv',
         '주 단위 종합 시계열 ~80 지표', 1),
        ('Zillow City Time Series', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/City_time_series.csv',
         '도시 단위 종합 시계열 ~78 지표', 1),
        ('Zillow County Time Series', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/County_time_series.csv',
         '카운티 단위 시계열 ~80 지표', 3),
        ('Zillow Zip Time Series', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/Zip_time_series.csv',
         'ZIP Code 단위 시계열 ~76 지표', 3),
        ('Zillow Cities Crosswalk', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/cities_crosswalk.csv',
         '도시-카운티-주 매핑', 0),
        ('Zillow County Crosswalk', None, None, 'CSV', 'data_folder',
         'data/Zillow_Economics/CountyCrossWalk_Zillow.csv',
         '카운티-MSA-FIPS 매핑', 0),
        
        # ===== Kaggle 소스 (한국/글로벌) =====
        # 소주제 1: 한국 주택
        ('Daegu Apartment Actual Transaction', 
         'https://www.kaggle.com/datasets/lnoahl/daegu-aptmernt-actual-transaction',
         'lnoahl/daegu-aptmernt-actual-transaction', 'CSV', 'kaggle', None,
         '대구 아파트 실거래가', 1),
        ('Daegu Real Estate Data',
         'https://www.kaggle.com/datasets/afifanuraini/daegu-real-estate-datacsv',
         'afifanuraini/daegu-real-estate-datacsv', 'CSV', 'kaggle', None,
         '대구 부동산 데이터', 1),
        ('Korean Apartment Deal Data',
         'https://www.kaggle.com/datasets/brainer3220/korean-real-estate-transaction-data',
         'brainer3220/korean-real-estate-transaction-data', 'CSV', 'kaggle', None,
         '전국 아파트 거래 (대구 필터링)', 1),
        ('Korea House Data 10yrs',
         'https://www.kaggle.com/datasets/gunhee/koreahousedata',
         'gunhee/koreahousedata', 'CSV', 'kaggle', None,
         '10년간 주택 데이터', 1),
        
        # 소주제 2: 인구·수요
        ('Korean Demographics 2000-2022',
         'https://www.kaggle.com/datasets/alexandrepetit881234/korean-demographics-20002022',
         'alexandrepetit881234/korean-demographics-20002022', 'CSV', 'kaggle', None,
         '한국 인구통계 22년간 (시도별)', 2),
        ('Korea Income and Welfare',
         'https://www.kaggle.com/datasets/hongsean/korea-income-and-welfare',
         'hongsean/korea-income-and-welfare', 'CSV', 'kaggle', None,
         '한국 소득·복지', 2),
        ('US Census Demographic Data',
         'https://www.kaggle.com/datasets/muonneutrino/us-census-demographic-data',
         'muonneutrino/us-census-demographic-data', 'CSV', 'kaggle', None,
         '미국 County/Tract 인구통계', 2),
        ('Population Time Series Data',
         'https://www.kaggle.com/datasets/census/population-time-series-data',
         'census/population-time-series-data', 'CSV', 'kaggle', None,
         '인구 시계열', 2),
        ('US County Historical Demographics',
         'https://www.kaggle.com/datasets/bitrook/us-county-historical-demographics',
         'bitrook/us-county-historical-demographics', 'CSV', 'kaggle', None,
         'County별 역사적 인구통계', 2),
        ('US County Data',
         'https://www.kaggle.com/datasets/evangambit/us-county-data',
         'evangambit/us-county-data', 'CSV', 'kaggle', None,
         'County 종합 데이터', 2),
        ('World Population Growth Rate by Cities 2024',
         'https://www.kaggle.com/datasets/dataanalyst001/world-population-growth-rate-by-cities-2024',
         'dataanalyst001/world-population-growth-rate-by-cities-2024', 'CSV', 'kaggle', None,
         '도시별 인구성장률', 2),
        ('World Cities Database',
         'https://www.kaggle.com/datasets/max-mind/world-cities-database',
         'max-mind/world-cities-database', 'CSV', 'kaggle', None,
         '도시 인구·좌표', 2),
        
        # 소주제 3: 기후
        ('Climate Change: Earth Surface Temperature (Berkeley)',
         'https://www.kaggle.com/datasets/berkeleyearth/climate-change-earth-surface-temperature-data',
         'berkeleyearth/climate-change-earth-surface-temperature-data', 'CSV', 'kaggle', None,
         '전세계 도시별 월평균 기온 (대구+미국 4도시 포함)', 3),
        ('Daily Temperature of Major Cities',
         'https://www.kaggle.com/datasets/sudalairajkumar/daily-temperature-of-major-cities',
         'sudalairajkumar/daily-temperature-of-major-cities', 'CSV', 'kaggle', None,
         '세계 주요도시 일별 기온', 3),
        ('Historical Hourly Weather Data 2012-2017',
         'https://www.kaggle.com/datasets/selfishgene/historical-hourly-weather-data',
         'selfishgene/historical-hourly-weather-data', 'CSV', 'kaggle', None,
         '시간별 기상 (미국 4도시 포함)', 3),
        ('Monthly Mean Temp US Cities 1948-2022',
         'https://www.kaggle.com/datasets/garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022',
         'garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022', 'CSV', 'kaggle', None,
         '미국 도시 월평균 기온 74년', 3),
        ('US Weather Events 2016-2022',
         'https://www.kaggle.com/datasets/sobhanmoosavi/us-weather-events',
         'sobhanmoosavi/us-weather-events', 'CSV', 'kaggle', None,
         '폭염 등 기상이벤트', 3),
        ('Global Daily Climate Data',
         'https://www.kaggle.com/datasets/guillemservera/global-daily-climate-data',
         'guillemservera/global-daily-climate-data', 'CSV', 'kaggle', None,
         '글로벌 일별 기후', 3),
        
        # 소주제 4: 산업전환
        ('BLS National Employment Hours Earnings',
         'https://www.kaggle.com/datasets/bls/employment',
         'bls/employment', 'CSV', 'kaggle', None,
         '미국 산업별 고용·임금', 4),
        ('USA Bureau of Labor Statistics',
         'https://www.kaggle.com/datasets/bls/bls',
         'bls/bls', 'CSV', 'kaggle', None,
         'BLS 종합 데이터', 4),
        ('Global Economy Indicators',
         'https://www.kaggle.com/datasets/prasad22/global-economy-indicators',
         'prasad22/global-economy-indicators', 'CSV', 'kaggle', None,
         '국가별 경제지표 (한국 포함)', 4),
        ('Macro-Economic Indicators',
         'https://www.kaggle.com/datasets/veselagencheva/macro-economic-indicators-dataset-country-level',
         'veselagencheva/macro-economic-indicators-dataset-country-level', 'CSV', 'kaggle', None,
         '거시경제 지표', 4),
        ('World GDP by Country Region',
         'https://www.kaggle.com/datasets/sazidthe1/world-gdp-data',
         'sazidthe1/world-gdp-data', 'CSV', 'kaggle', None,
         'GDP 데이터', 4),
    ]
    
    sql = """INSERT INTO data_sources 
             (source_name, source_url, kaggle_dataset_id, data_format, 
              source_type, file_path, description, sub_topic)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.executemany(sql, sources)
    conn.commit()
    conn.close()
    print(f"✅ 데이터 소스 {len(sources)}개 등록 완료 (data/폴더: 18개, Kaggle: {len(sources)-18}개)")

# =============================================
# 5. CSV → MySQL 범용 로딩 함수
# =============================================

def load_csv_to_mysql(csv_path, table_name, db_name=DB_NAME,
                      encoding='utf-8', chunksize=5000):
    """CSV 파일을 MySQL 테이블로 로딩"""
    conn = get_connection(db_name)
    total_rows = 0
    for chunk in pd.read_csv(csv_path, encoding=encoding, chunksize=chunksize):
        chunk = chunk.where(pd.notnull(chunk), None)
        cols = ', '.join([f'`{c}`' for c in chunk.columns])
        placeholders = ', '.join(['%s'] * len(chunk.columns))
        sql = f"INSERT INTO `{table_name}` ({cols}) VALUES ({placeholders})"
        cursor = conn.cursor()
        data = [tuple(row) for row in chunk.values]
        cursor.executemany(sql, data)
        conn.commit()
        total_rows += len(chunk)
        print(f"  ... {total_rows}행 삽입됨")
    conn.close()
    print(f"✅ '{csv_path}' → '{table_name}' 로딩 완료 (총 {total_rows}행)")

# =============================================
# 6. Zillow Wide Format → Long Format 변환 로딩
# =============================================

TARGET_METROS = [
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',
    'Phoenix-Mesa-Chandler, AZ',
    'Charlotte-Concord-Gastonia, NC-SC',
]

def load_zillow_wide_to_long(csv_path, table_name, value_col_name,
                             target_metros=TARGET_METROS, db_name=DB_NAME):
    """
    zillow_Housing Wide Format CSV를 Long Format으로 변환하여 MySQL에 적재
    - Wide: 행=지역, 열=날짜 → Long: (region, year_month, value)
    - target_metros로 4개 비교 도시 MSA + United States(전국) 필터링
    """
    df = pd.read_csv(csv_path)
    
    # 식별 열과 날짜 열 분리
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    if 'BaseDate' in df.columns:
        id_cols.append('BaseDate')
    date_cols = [c for c in df.columns if c not in id_cols]
    
    # 타겟 MSA + 전국 필터링
    filter_names = target_metros + ['United States']
    df_filtered = df[df['RegionName'].isin(filter_names)].copy()
    
    if df_filtered.empty:
        print(f"⚠️ 타겟 MSA를 찾을 수 없습니다: {csv_path}")
        return
    
    # Wide → Long 변환 (melt)
    df_long = df_filtered.melt(
        id_vars=[c for c in id_cols if c in df_filtered.columns],
        value_vars=date_cols,
        var_name='year_month',
        value_name=value_col_name
    )
    df_long = df_long.dropna(subset=[value_col_name])
    df_long['year_month'] = df_long['year_month'].str[:7]  # YYYY-MM
    
    # MySQL 적재
    conn = get_connection(db_name)
    cursor = conn.cursor()
    for _, row in df_long.iterrows():
        sql = f"""INSERT INTO `{table_name}` 
                  (region_id, region_name, state_name, year_month, `{value_col_name}`)
                  VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (
            row.get('RegionID'), row['RegionName'],
            row.get('StateName'), row['year_month'], row[value_col_name]
        ))
    conn.commit()
    conn.close()
    print(f"✅ Wide→Long 변환 적재 완료: {csv_path} → {table_name} ({len(df_long)}행)")

# =============================================
# 7. Zillow Economics Long Format 선택적 로딩
# =============================================

def load_zillow_economics_timeseries(csv_path, region_level, 
                                      target_regions=None, 
                                      selected_cols=None,
                                      db_name=DB_NAME, chunksize=10000):
    """
    Zillow Economics Long Format 시계열을 선택적으로 로딩
    - 대용량 파일(City 689MB, Zip 782MB)은 target_regions + selected_cols로 필터링
    
    Parameters:
        csv_path: CSV 파일 경로
        region_level: 'city', 'county', 'metro', 'state', 'zip', 'neighborhood'
        target_regions: 필터링할 RegionName 리스트 (None이면 전체)
        selected_cols: 로딩할 지표 열 리스트 (None이면 핵심 지표만)
    """
    if selected_cols is None:
        selected_cols = [
            'ZHVI_AllHomes', 'ZHVIPerSqft_AllHomes',
            'ZRI_AllHomes', 'MedianListingPrice_AllHomes',
            'MedianRentalPrice_AllHomes', 'InventorySeasonallyAdjusted',
            'DaysOnZillow_AllHomes', 'Sale_Counts',
            'Sale_Counts_Seas_Adj', 'PriceToRentRatio_AllHomes',
            'PctOfHomesIncreasingInValues_AllHomes',
            'PctOfHomesDecreasingInValues_AllHomes',
            'PctOfHomesSellingForLoss_AllHomes',
            'PctOfListingsWithPriceReductions_AllHomes',
            'MedianPctOfPriceReduction_AllHomes',
        ]
    
    use_cols = ['Date', 'RegionName'] + selected_cols
    
    conn = get_connection(db_name)
    total_rows = 0
    
    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in use_cols + ['Date', 'RegionName'],
                              chunksize=chunksize):
        if target_regions:
            chunk = chunk[chunk['RegionName'].isin(target_regions)]
        
        if chunk.empty:
            continue
        
        chunk = chunk.where(pd.notnull(chunk), None)
        
        for _, row in chunk.iterrows():
            sql = """INSERT INTO zillow_timeseries 
                     (date, region_name, region_level,
                      zhvi_all, zhvi_per_sqft, zri_all,
                      median_listing_price, median_rental_price,
                      inventory_seasonally_adj, days_on_zillow,
                      sale_counts, sale_counts_seas_adj,
                      price_to_rent_ratio, pct_homes_increasing,
                      pct_homes_decreasing, pct_homes_selling_for_loss,
                      pct_listings_price_reduction, median_pct_price_reduction,
                      source_file)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor = conn.cursor()
            cursor.execute(sql, (
                row.get('Date'), row['RegionName'], region_level,
                row.get('ZHVI_AllHomes'), row.get('ZHVIPerSqft_AllHomes'),
                row.get('ZRI_AllHomes'), row.get('MedianListingPrice_AllHomes'),
                row.get('MedianRentalPrice_AllHomes'),
                row.get('InventorySeasonallyAdjusted'),
                row.get('DaysOnZillow_AllHomes'), row.get('Sale_Counts'),
                row.get('Sale_Counts_Seas_Adj'),
                row.get('PriceToRentRatio_AllHomes'),
                row.get('PctOfHomesIncreasingInValues_AllHomes'),
                row.get('PctOfHomesDecreasingInValues_AllHomes'),
                row.get('PctOfHomesSellingForLoss_AllHomes'),
                row.get('PctOfListingsWithPriceReductions_AllHomes'),
                row.get('MedianPctOfPriceReduction_AllHomes'),
                os.path.basename(csv_path)
            ))
        
        conn.commit()
        total_rows += len(chunk)
        print(f"  ... {total_rows}행 삽입됨")
    
    conn.close()
    print(f"✅ '{csv_path}' → zillow_timeseries ({region_level}) 로딩 완료 (총 {total_rows}행)")

# =============================================
# 8. Realtor.com 매물 데이터 로딩 (4개 도시 필터)
# =============================================

def load_realtor_data(csv_path, db_name=DB_NAME, chunksize=10000):
    """
    realtor-data.zip.csv에서 4개 비교 도시가 포함된 주(State)의 매물을 필터링하여 로딩
    """
    target_cities = {
        'Dallas': ('TX', 2),
        'Atlanta': ('GA', 3),
        'Phoenix': ('AZ', 4),
        'Charlotte': ('NC', 5),
    }
    target_states = [v[0] for v in target_cities.values()]
    
    conn = get_connection(db_name)
    total_rows = 0
    
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):
        # 타겟 주 필터링
        chunk = chunk[chunk['state'].isin(target_states)]
        if chunk.empty:
            continue
        
        chunk = chunk.where(pd.notnull(chunk), None)
        
        cursor = conn.cursor()
        for _, row in chunk.iterrows():
            # city_id 매핑
            city_id = None
            city_name = str(row.get('city', ''))
            for cname, (st, cid) in target_cities.items():
                if row.get('state') == st and cname.lower() in city_name.lower():
                    city_id = cid
                    break
            
            sql = """INSERT INTO us_realtor_listings 
                     (city_id, brokered_by, status, price, bed, bath, 
                      acre_lot, street, city, state, zip_code, house_size, prev_sold_date)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql, (
                city_id, row.get('brokered_by'), row.get('status'),
                row.get('price'), row.get('bed'), row.get('bath'),
                row.get('acre_lot'), row.get('street'),
                row.get('city'), row.get('state'),
                row.get('zip_code'), row.get('house_size'),
                row.get('prev_sold_date')
            ))
        
        conn.commit()
        total_rows += len(chunk)
        print(f"  ... {total_rows}행 삽입됨")
    
    conn.close()
    print(f"✅ Realtor.com 매물 데이터 로딩 완료 (총 {total_rows}행)")

# =============================================
# 9. Crosswalk 테이블 로딩
# =============================================

def load_crosswalk_tables():
    """Zillow 지역 매핑 테이블 로딩"""
    # CountyCrossWalk
    load_csv_to_mysql(
        f'{ZILLOW_ECONOMICS_DIR}CountyCrossWalk_Zillow.csv',
        'zillow_region_crosswalk'
    )
    # cities_crosswalk
    load_csv_to_mysql(
        f'{ZILLOW_ECONOMICS_DIR}cities_crosswalk.csv',
        'cities_crosswalk'
    )

# =============================================
# 10. 소주제별 데이터 로딩 실행
# =============================================

# --- Crosswalk ---
# load_crosswalk_tables()

# --- 소주제 1: 주택 가격 추이 ---
# Realtor.com
# load_realtor_data(f'{DATA_DIR}realtor-data.zip.csv')

# Zillow ZHVI (Wide → Long)
# load_zillow_wide_to_long(
#     f'{ZILLOW_HOUSING_DIR}Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
#     'us_metro_zhvi', 'zhvi'
# )

# Zillow ZORI (Wide → Long)
# load_zillow_wide_to_long(
#     f'{ZILLOW_HOUSING_DIR}Metro_zori_uc_sfrcondomfr_sm_month.csv',
#     'us_metro_zori', 'zori'
# )

# Zillow Economics Metro 시계열 (Long)
# load_zillow_economics_timeseries(
#     f'{ZILLOW_ECONOMICS_DIR}Metro_time_series.csv',
#     region_level='metro'
# )

# Zillow Economics State 시계열
# load_zillow_economics_timeseries(
#     f'{ZILLOW_ECONOMICS_DIR}State_time_series.csv',
#     region_level='state',
#     target_regions=['Texas', 'Georgia', 'Arizona', 'North Carolina']
# )

# --- 소주제 2: 인구 이동과 수요 ---
# Zillow 수급 지표 (Wide → Long)
# for fpath, tbl, col in [
#     ('Metro_invt_fs_uc_sfrcondo_sm_month.csv', 'us_metro_demand', 'inventory_count'),
#     ('Metro_market_temp_index_uc_sfrcondo_month.csv', 'us_metro_demand', 'market_temp_index'),
#     ('Metro_sales_count_now_uc_sfrcondo_month.csv', 'us_metro_demand', 'sales_count'),
#     ('Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv', 'us_metro_demand', 'mean_days_pending'),
# ]:
#     load_zillow_wide_to_long(f'{ZILLOW_HOUSING_DIR}{fpath}', tbl, col)

# Kaggle 인구 데이터
# load_csv_to_mysql('kaggle_data/korean_demographics.csv', 'korean_demographics', encoding='cp949')
# load_csv_to_mysql('kaggle_data/us_census_demographic.csv', 'us_demographics')

# --- 소주제 3: 기후·가격격차 ---
# Zillow ZIP 시계열 (대용량 — 필터링 필수)
# Dallas ZIP codes, Phoenix ZIPs 등 사전 조사 필요
# load_zillow_economics_timeseries(
#     f'{ZILLOW_ECONOMICS_DIR}Zip_time_series.csv',
#     region_level='zip',
#     target_regions=['75201','75202',...,'85001','85003',...]  # 대상 ZIP 코드
# )

# Kaggle 기후 데이터
# load_csv_to_mysql('kaggle_data/GlobalLandTemperaturesByCity.csv', 'climate_temperature')

# --- 소주제 4: 산업 전환 ---
# Zillow 신규건설 (Wide → Long)
# load_zillow_wide_to_long(
#     f'{ZILLOW_HOUSING_DIR}Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv',
#     'us_metro_demand', 'new_construction_sales'
# )

# Kaggle BLS
# load_csv_to_mysql('kaggle_data/bls_employment.csv', 'us_industry_employment')

# =============================================
# 11. 실행
# =============================================

if __name__ == '__main__':
    create_database()
    create_all_tables()
    insert_cities()
    insert_data_sources()
    print("\n🎉 프로젝트 초기화 완료! (data/ 폴더 + Kaggle 통합)")
```

---

## 📦 데이터셋 총 정리

### `data/` 폴더 데이터 (미국) — 18개 파일

| 구분 | 파일 | 형태 | 크기 | 핵심 |
|------|------|------|------|------|
| Realtor | `realtor-data.zip.csv` | 개별매물 | 178MB | ⭐ |
| Zillow Housing | `Metro_zhvi_...month.csv` | Wide | 4.3MB | ⭐ |
| Zillow Housing | `Metro_zori_...month.csv` | Wide | 955KB | ⭐ |
| Zillow Housing | `Metro_invt_...month.csv` | Wide | 557KB | ⭐ |
| Zillow Housing | `Metro_market_temp_...month.csv` | Wide | 470KB | ⭐ |
| Zillow Housing | `Metro_mean_doz_...month.csv` | Wide | 266KB | |
| Zillow Housing | `Metro_sales_count_...month.csv` | Wide | 140KB | ⭐ |
| Zillow Housing | `Metro_new_con_...month.csv` | Wide | 181KB | |
| Zillow Housing | `Metro_new_homeowner_...csv` | Wide | 1.2MB | ⭐ |
| Zillow Housing | `Metro_zhvf_growth_...month.csv` | Wide | 50KB | |
| Zillow Housing | `National_zorf_growth_...month.csv` | Wide | 136B | |
| Zillow Economics | `Metro_time_series.csv` | Long | 56MB | ⭐ |
| Zillow Economics | `State_time_series.csv` | Long | 4.7MB | ⭐ |
| Zillow Economics | `City_time_series.csv` | Long | 689MB | ⭐ |
| Zillow Economics | `County_time_series.csv` | Long | 112MB | |
| Zillow Economics | `Zip_time_series.csv` | Long | 782MB | ⭐ |
| Zillow Economics | `cities_crosswalk.csv` | 매핑 | 1MB | |
| Zillow Economics | `CountyCrossWalk_Zillow.csv` | 매핑 | 232KB | |

### Kaggle 데이터 (한국/글로벌) — 24개

| 소주제 | 구분 | 데이터셋 | Kaggle ID | 핵심 |
|--------|------|---------|-----------|------|
| 1 | 🇰🇷 | Daegu Apartment Actual Transaction | `lnoahl/daegu-aptmernt-actual-transaction` | ⭐ |
| 1 | 🇰🇷 | Daegu Real Estate Data | `afifanuraini/daegu-real-estate-datacsv` | ⭐ |
| 1 | 🇰🇷 | Korean Apartment Deal Data | `brainer3220/korean-real-estate-transaction-data` | |
| 1 | 🇰🇷 | Korea House Data 10yrs | `gunhee/koreahousedata` | |
| 2 | 🇰🇷 | Korean Demographics 2000-2022 | `alexandrepetit881234/korean-demographics-20002022` | ⭐ |
| 2 | 🇰🇷 | Korea Income and Welfare | `hongsean/korea-income-and-welfare` | |
| 2 | 🇺🇸 | US Census Demographic Data | `muonneutrino/us-census-demographic-data` | ⭐ |
| 2 | 🇺🇸 | Population Time Series Data | `census/population-time-series-data` | |
| 2 | 🇺🇸 | US County Historical Demographics | `bitrook/us-county-historical-demographics` | |
| 2 | 🇺🇸 | US County Data | `evangambit/us-county-data` | |
| 2 | 🌍 | World Population Growth Rate by Cities 2024 | `dataanalyst001/world-population-growth-rate-by-cities-2024` | |
| 2 | 🌍 | World Cities Database | `max-mind/world-cities-database` | |
| 3 | 🌍 | Climate Change: Earth Surface Temperature | `berkeleyearth/climate-change-earth-surface-temperature-data` | ⭐ |
| 3 | 🌍 | Daily Temperature of Major Cities | `sudalairajkumar/daily-temperature-of-major-cities` | ⭐ |
| 3 | 🇺🇸 | Historical Hourly Weather 2012-2017 | `selfishgene/historical-hourly-weather-data` | |
| 3 | 🇺🇸 | Monthly Mean Temp US Cities 1948-2022 | `garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022` | |
| 3 | 🇺🇸 | US Weather Events 2016-2022 | `sobhanmoosavi/us-weather-events` | |
| 3 | 🌍 | Global Daily Climate Data | `guillemservera/global-daily-climate-data` | |
| 4 | 🇺🇸 | BLS National Employment | `bls/employment` | ⭐ |
| 4 | 🇺🇸 | USA Bureau of Labor Statistics | `bls/bls` | |
| 4 | 🌍 | Global Economy Indicators | `prasad22/global-economy-indicators` | ⭐ |
| 4 | 🌍 | Macro-Economic Indicators | `veselagencheva/macro-economic-indicators-dataset-country-level` | |
| 4 | 🌍 | World GDP by Country Region | `sazidthe1/world-gdp-data` | |

**합계: `data/` 폴더 18개 + Kaggle 24개 = 총 42개 데이터 파일**

---

## ⚠️ 주의사항 및 전략

### 1. 대용량 파일 처리 전략

| 파일 | 크기 | 전략 |
|------|------|------|
| `Zip_time_series.csv` | 782MB | `target_regions` 필터로 대상 ZIP만 로딩 |
| `City_time_series.csv` | 689MB | Dallas/Atlanta/Phoenix/Charlotte 도시만 필터 |
| `realtor-data.zip.csv` | 178MB | 4개 주(TX/GA/AZ/NC) 필터, chunksize=10000 |
| `County_time_series.csv` | 112MB | 필요 카운티만 Crosswalk 기반 필터 |

### 2. Wide → Long 변환 시 주의

- `zillow_Housing` 파일들은 **행=지역, 열=날짜** Wide Format
- `RegionName` 값으로 4개 MSA 필터링 후 `pd.melt()` 변환
- MSA 이름은 정확히 매칭 필요 (예: `Dallas-Fort Worth-Arlington, TX`)

### 3. 소주제 4 한국 산업 데이터 한계 (v1과 동일)

- Kaggle에 대구 시도별 산업·고용 데이터 직접 없음
- **대안:** Korean Demographics + Korea Income and Welfare로 간접 분석
- Global Economy Indicators로 한국 전체 거시 트렌드 활용

### 4. Zillow Economics vs zillow_Housing 중복 관리

- **Zillow Economics** (Long): 1996~ 장기 시계열, 지표 다양
- **zillow_Housing** (Wide): 최신, MSA 특화, 일부 고유 지표 (시장온도, 필요소득 등)
- 중복 지표(ZHVI 등)는 **zillow_Housing 우선** (더 최신), Economics는 장기 추세 보조

---

## 🔄 프로젝트 워크플로우

```
1. 데이터 준비
   ├→ data/ 폴더: Realtor.com + Zillow (이미 확보)
   └→ Kaggle: kaggle datasets download -d {dataset_id} (24개)

2. DB 초기화
   └→ python init_project.py
       ├→ DB/테이블 생성
       ├→ 도시 마스터 삽입
       ├→ 데이터 소스 등록
       └→ Crosswalk 테이블 로딩

3. 데이터 전처리 & 로딩
   ├→ Realtor.com: 4개 주 필터 → us_realtor_listings
   ├→ Zillow Wide: 4개 MSA 필터 → Wide→Long 변환 → us_metro_zhvi, us_metro_zori, us_metro_demand
   ├→ Zillow Economics: 핵심 지표 선택 + 지역 필터 → zillow_timeseries
   ├→ 한국 데이터: 대구 필터, 날짜/금액 통일, encoding='cp949'
   ├→ 기후 데이터: 5개 도시(대구+미국4) 필터
   └→ 글로벌 데이터: 한국/미국 필터

4. 분석 쿼리 (SQL JOIN)
   ├→ 소주제1: ZHVI 25년 시계열 + Realtor 매물가 + 대구 실거래가 비교
   ├→ 소주제2: 인구변동률 vs 시장온도×재고×판매건수 다변량 분석
   ├→ 소주제3: ZIP 시계열 + 기온 데이터 JOIN → 기온-가격 히트맵
   └→ 소주제4: BLS 고용 vs 신규건설+필요소득+시장온도 다차원 분석

5. 시각화 (matplotlib/seaborn)
   ├→ 가격 추이: 대구 vs 4도시 25년 오버레이 선형차트
   ├→ 수급 대시보드: 시장온도 + 재고량 + 판매건수 복합 차트
   ├→ 기온-가격 히트맵: ZIP/구별 교차표
   ├→ 산업전환 타임라인: 고용변화 + 신규건설 + 필요소득 동시 표시
   └→ 예측 성장률: ZHVF/ZORF 미래 전망 비교

6. 인사이트 도출
   └→ 소주제별 결론 + 종합 비교분석 리포트
```
