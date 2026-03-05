# 내륙 거점 도시의 부동산 시장 구조 비교: 대구 vs 미국 유사 도시
## 🔒 Kaggle 전용 데이터 프로젝트

---

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **주제** | 내륙 거점 도시의 부동산 시장 구조 비교 분석 |
| **DB** | MySQL (172.30.1.47, user: wonho, pw: 1111) |
| **언어** | Python (pymysql, pandas) |
| **데이터 소스** | ✅ Kaggle CSV **전용** (외부 사이트 없음) |

---

## 🏙️ 도시 매칭 테이블

| 비교축 | 대구 ↔ 미국 도시 | 매칭 근거 |
|--------|------------------|-----------|
| 종합 | 대구 ↔ **Dallas** | 내륙 대도시, 보수적, 여름 고온 |
| 산업 | 대구 ↔ **Atlanta** | 자동차·배터리 허브, 교통 결절점 |
| 기후 | 대구 ↔ **Phoenix** | 극심한 여름 더위, 분지 지형 |
| 변모 | 대구 ↔ **Charlotte** | 섬유→하이테크/금융 전환 |

---

## 📊 소주제별 Kaggle 데이터셋

---

### 소주제 1: 주택 가격 추이 비교 (Housing Price Trends)

**분석 목표:** 3~5년간 주거용 부동산 가격 패턴 비교

#### 🇰🇷 한국(대구) 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| K1-1 | ⭐ Daegu Apartment Actual Transaction | https://www.kaggle.com/datasets/lnoahl/daegu-aptmernt-actual-transaction | 대구 아파트 실거래가 (핵심) |
| K1-2 | ⭐ Daegu Real Estate Data | https://www.kaggle.com/datasets/afifanuraini/daegu-real-estate-datacsv | 대구 부동산 데이터 |
| K1-3 | Korean Apartment Deal Data | https://www.kaggle.com/datasets/brainer3220/korean-real-estate-transaction-data | 전국 아파트 거래 (대구 필터링) |
| K1-4 | Korea House Data 10yrs | https://www.kaggle.com/datasets/gunhee/koreahousedata | 10년간 주택 데이터 |

#### 🇺🇸 미국 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| U1-1 | ⭐ Zillow Home Value Index Monthly | https://www.kaggle.com/datasets/robikscube/zillow-home-value-index | ZHVI 월별 (핵심) |
| U1-2 | ⭐ US Cities Housing Market Data | https://www.kaggle.com/datasets/vincentvaseghi/us-cities-housing-market-data | 도시별 주택시장 실시간 |
| U1-3 | USA Real Estate Dataset 2.2M+ | https://www.kaggle.com/datasets/ahmedshahriarsakib/usa-real-estate-dataset | 220만건 매물 (zip code별) |
| U1-4 | US Housing Trends Zillow 2018-2024 | https://www.kaggle.com/datasets/clovisdalmolinvieira/us-housing-trends-values-time-and-price-cuts | 가격 추이+가격 인하율 |
| U1-5 | Zillow House Price Data by Room | https://www.kaggle.com/datasets/paultimothymooney/zillow-house-price-data | 방 수별 가격 데이터 |

#### 핵심 지표
- 월/분기별 평균 거래가, 중위가격, 전년동기 대비 변동률
- COVID 전후 급등 패턴, 금리인상 영향 비교

---

### 소주제 2: 인구 이동과 주택 수요 (Population & Housing Demand)

**분석 목표:** 인구 변동과 부동산 가격/거래량 상관관계

#### 🇰🇷 한국(대구) 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| K2-1 | ⭐ Korean Demographics 2000-2022 | https://www.kaggle.com/datasets/alexandrepetit881234/korean-demographics-20002022 | 한국 인구통계 22년간 (시도별) |
| K2-2 | Korea Income and Welfare | https://www.kaggle.com/datasets/hongsean/korea-income-and-welfare | 지역별 소득·복지 데이터 |

#### 🇺🇸 미국 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| U2-1 | ⭐ US Census Demographic Data | https://www.kaggle.com/datasets/muonneutrino/us-census-demographic-data | County/Tract 인구통계 (핵심) |
| U2-2 | Population Time Series Data | https://www.kaggle.com/datasets/census/population-time-series-data | 인구 시계열 |
| U2-3 | US County & Zipcode Historical Demographics | https://www.kaggle.com/datasets/bitrook/us-county-historical-demographics | County별 역사적 인구통계 |
| U2-4 | US County Data | https://www.kaggle.com/datasets/evangambit/us-county-data | County 종합 데이터 |

#### 🌍 글로벌/보완 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| G2-1 | World Population Growth Rate by Cities 2024 | https://www.kaggle.com/datasets/dataanalyst001/world-population-growth-rate-by-cities-2024 | 대구·Dallas 등 도시별 인구성장률 |
| G2-2 | World Cities Database | https://www.kaggle.com/datasets/max-mind/world-cities-database | 도시 인구·좌표 정보 |

#### 핵심 지표
- 순이동 인구, 인구증감률, 인구-가격 상관계수
- 대구(인구유출) vs Dallas/Atlanta(인구유입) → 반대 방향 가격 영향

---

### 소주제 3: 기후·입지와 지역별 가격 격차 (Climate & Regional Price Variance)

**분석 목표:** 내륙/분지 도시 특성(폭염, 교통)이 구/zip code별 가격 격차에 미치는 영향

#### 🌡️ 기후 데이터 (한국+미국 공통)

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| C3-1 | ⭐ Climate Change: Earth Surface Temperature Data (Berkeley) | https://www.kaggle.com/datasets/berkeleyearth/climate-change-earth-surface-temperature-data | **GlobalLandTemperaturesByCity.csv** → 대구+Dallas+Phoenix+Atlanta+Charlotte 모두 포함 (1750~2013) |
| C3-2 | ⭐ Daily Temperature of Major Cities | https://www.kaggle.com/datasets/sudalairajkumar/daily-temperature-of-major-cities | 전 세계 주요 도시 일별 기온 (한국+미국) |
| C3-3 | Historical Hourly Weather Data 2012-2017 | https://www.kaggle.com/datasets/selfishgene/historical-hourly-weather-data | 시간별 기상 (Dallas, Phoenix, Atlanta, Charlotte 포함) |
| C3-4 | Monthly Mean Temp US Cities 1948-2022 | https://www.kaggle.com/datasets/garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022 | 미국 도시 월평균 기온 74년간 |
| C3-5 | US Weather Events 2016-2022 | https://www.kaggle.com/datasets/sobhanmoosavi/us-weather-events | 미국 기상 이벤트(폭염 등) |
| C3-6 | Global Daily Climate Data | https://www.kaggle.com/datasets/guillemservera/global-daily-climate-data | 글로벌 일별 기후 |

#### 🏠 지역별 가격 데이터 (소주제 1 데이터 재활용)

| 데이터 | 활용 방법 |
|--------|----------|
| K1-1 대구 아파트 실거래가 | 구별(수성구, 달서구 등) 가격 분석 |
| U1-3 USA Real Estate 2.2M+ | zip code별 가격 분석 (Dallas, Phoenix, Atlanta, Charlotte) |
| U1-1 Zillow ZHVI | 도시·지역별 가격 추이 |

#### 핵심 지표
- 구/zip code별 평균가, 여름 최고기온, 폭염일수, 도심 접근성
- Phoenix 열섬지대 vs 대구 수성구 쾌적 프리미엄, 분지 도시 공통 패턴

---

### 소주제 4: 산업 전환과 부동산 (Industrial Transformation & Real Estate)

**분석 목표:** 전통 산업(섬유)→하이테크 전환이 상업/주거용 부동산에 미치는 영향

#### 🇺🇸 미국 고용·산업 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| U4-1 | ⭐ BLS National Employment, Hours, Earnings | https://www.kaggle.com/datasets/bls/employment | 산업별 고용 (핵심) |
| U4-2 | USA Bureau of Labor Statistics BigQuery | https://www.kaggle.com/datasets/bls/bls | BLS 종합 데이터 |

#### 🌍 글로벌/보완 데이터

| # | 데이터셋명 | Kaggle URL | 비고 |
|---|-----------|-----------|------|
| G4-1 | ⭐ Global Economy Indicators | https://www.kaggle.com/datasets/prasad22/global-economy-indicators | 국가별 경제지표 (한국 포함) |
| G4-2 | Macro-Economic Indicators (Country-Level) | https://www.kaggle.com/datasets/veselagencheva/macro-economic-indicators-dataset-country-level | 거시경제 지표 |
| G4-3 | World GDP by Country, Region | https://www.kaggle.com/datasets/sazidthe1/world-gdp-data | GDP 데이터 |

#### ⚠️ 소주제 4 한국 산업 데이터 한계 및 대안

Kaggle에 **대구 시도별 산업·고용 데이터**가 직접적으로 없으므로 다음 전략 사용:

1. **K2-1 Korean Demographics 2000-2022** → 지역별 경제활동인구, 고용률 추출
2. **K2-2 Korea Income and Welfare** → 지역별 산업분류 소득 데이터 활용
3. **K1-1~K1-4 주택 데이터** → 산업단지 인근 지역 가격 변화 프록시로 활용
4. **G4-1 Global Economy Indicators** → 한국 전체 제조업→서비스업 전환 거시 트렌드

#### 핵심 지표
- 산업별 고용 변동(제조→서비스→하이테크), 산업단지 인근 부동산 가격 변화
- Charlotte 섬유→금융 전환 부동산 붐 vs 대구 섬유→하이테크 진행 중인 전환

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
    description TEXT,
    sub_topic INT
);

-- =============================================
-- 소주제 1: 주택 가격 추이
-- =============================================

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

CREATE TABLE us_housing_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    city_name VARCHAR(50),
    year_month VARCHAR(7),
    zhvi DECIMAL(15,2),
    median_list_price DECIMAL(15,2),
    median_sale_price DECIMAL(15,2),
    price_change_rate DECIMAL(8,4),
    inventory_count INT,
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
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

CREATE TABLE migration_housing_correlation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    year INT,
    population_change_rate DECIMAL(8,4),
    avg_housing_price DECIMAL(15,2),
    transaction_count INT,
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

CREATE TABLE us_zipcode_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    zip_code VARCHAR(10),
    city_name VARCHAR(50),
    year_month VARCHAR(7),
    median_price DECIMAL(15,2),
    avg_price DECIMAL(15,2),
    listing_count INT,
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
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

CREATE TABLE industry_housing_impact (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT,
    year INT,
    dominant_industry VARCHAR(100),
    industry_employee_change DECIMAL(8,4),
    nearby_housing_price_change DECIMAL(8,4),
    source_dataset VARCHAR(100),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);
```

---

## 🐍 Python 구현 코드

```python
import pymysql
import pandas as pd
import os

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
    
    # 위 SQL 스키마를 여기에 넣어 실행
    # (각 CREATE TABLE 문을 cursor.execute()로 실행)
    
    tables = [
        # cities 테이블
        """CREATE TABLE IF NOT EXISTS cities (
            city_id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50) NOT NULL,
            country VARCHAR(20) NOT NULL,
            category VARCHAR(30),
            comparison_pair VARCHAR(50),
            population BIGINT,
            latitude DECIMAL(10,6),
            longitude DECIMAL(10,6)
        )""",
        # data_sources 테이블
        """CREATE TABLE IF NOT EXISTS data_sources (
            source_id INT AUTO_INCREMENT PRIMARY KEY,
            source_name VARCHAR(200) NOT NULL,
            source_url VARCHAR(500),
            kaggle_dataset_id VARCHAR(200),
            data_format VARCHAR(20) DEFAULT 'CSV',
            description TEXT,
            sub_topic INT
        )""",
        # ... (나머지 테이블은 위 스키마 참조)
    ]
    
    for sql in tables:
        cursor.execute(sql)
    
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
# 4. Kaggle 데이터 소스 등록
# =============================================

def insert_kaggle_sources():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    sources = [
        # 소주제 1: 주택 가격
        ('Daegu Apartment Actual Transaction', 'https://www.kaggle.com/datasets/lnoahl/daegu-aptmernt-actual-transaction', 'lnoahl/daegu-aptmernt-actual-transaction', 'CSV', '대구 아파트 실거래가', 1),
        ('Daegu Real Estate Data', 'https://www.kaggle.com/datasets/afifanuraini/daegu-real-estate-datacsv', 'afifanuraini/daegu-real-estate-datacsv', 'CSV', '대구 부동산 데이터', 1),
        ('Korean Apartment Deal Data', 'https://www.kaggle.com/datasets/brainer3220/korean-real-estate-transaction-data', 'brainer3220/korean-real-estate-transaction-data', 'CSV', '전국 아파트 거래', 1),
        ('Korea House Data 10yrs', 'https://www.kaggle.com/datasets/gunhee/koreahousedata', 'gunhee/koreahousedata', 'CSV', '10년간 주택 데이터', 1),
        ('Zillow Home Value Index Monthly', 'https://www.kaggle.com/datasets/robikscube/zillow-home-value-index', 'robikscube/zillow-home-value-index', 'CSV', 'ZHVI 월별 미국 도시', 1),
        ('US Cities Housing Market Data', 'https://www.kaggle.com/datasets/vincentvaseghi/us-cities-housing-market-data', 'vincentvaseghi/us-cities-housing-market-data', 'CSV', '미국 도시별 주택시장', 1),
        ('USA Real Estate Dataset 2.2M+', 'https://www.kaggle.com/datasets/ahmedshahriarsakib/usa-real-estate-dataset', 'ahmedshahriarsakib/usa-real-estate-dataset', 'CSV', '220만건 미국 매물', 1),
        ('US Housing Trends Zillow 2018-2024', 'https://www.kaggle.com/datasets/clovisdalmolinvieira/us-housing-trends-values-time-and-price-cuts', 'clovisdalmolinvieira/us-housing-trends-values-time-and-price-cuts', 'CSV', '가격추이+인하율', 1),
        ('Zillow House Price Data by Room', 'https://www.kaggle.com/datasets/paultimothymooney/zillow-house-price-data', 'paultimothymooney/zillow-house-price-data', 'CSV', '방수별 가격', 1),
        
        # 소주제 2: 인구·수요
        ('Korean Demographics 2000-2022', 'https://www.kaggle.com/datasets/alexandrepetit881234/korean-demographics-20002022', 'alexandrepetit881234/korean-demographics-20002022', 'CSV', '한국 인구통계 22년간', 2),
        ('Korea Income and Welfare', 'https://www.kaggle.com/datasets/hongsean/korea-income-and-welfare', 'hongsean/korea-income-and-welfare', 'CSV', '한국 소득·복지', 2),
        ('US Census Demographic Data', 'https://www.kaggle.com/datasets/muonneutrino/us-census-demographic-data', 'muonneutrino/us-census-demographic-data', 'CSV', '미국 County/Tract 인구통계', 2),
        ('Population Time Series Data', 'https://www.kaggle.com/datasets/census/population-time-series-data', 'census/population-time-series-data', 'CSV', '인구 시계열', 2),
        ('US County Historical Demographics', 'https://www.kaggle.com/datasets/bitrook/us-county-historical-demographics', 'bitrook/us-county-historical-demographics', 'CSV', 'County 역사적 인구통계', 2),
        ('US County Data', 'https://www.kaggle.com/datasets/evangambit/us-county-data', 'evangambit/us-county-data', 'CSV', 'County 종합 데이터', 2),
        ('World Population Growth Rate by Cities 2024', 'https://www.kaggle.com/datasets/dataanalyst001/world-population-growth-rate-by-cities-2024', 'dataanalyst001/world-population-growth-rate-by-cities-2024', 'CSV', '도시별 인구성장률', 2),
        ('World Cities Database', 'https://www.kaggle.com/datasets/max-mind/world-cities-database', 'max-mind/world-cities-database', 'CSV', '도시 인구·좌표', 2),
        
        # 소주제 3: 기후·가격격차
        ('Climate Change: Earth Surface Temperature (Berkeley)', 'https://www.kaggle.com/datasets/berkeleyearth/climate-change-earth-surface-temperature-data', 'berkeleyearth/climate-change-earth-surface-temperature-data', 'CSV', '전세계 도시별 월평균 기온 1750-2013 (대구+미국 4개 도시 포함)', 3),
        ('Daily Temperature of Major Cities', 'https://www.kaggle.com/datasets/sudalairajkumar/daily-temperature-of-major-cities', 'sudalairajkumar/daily-temperature-of-major-cities', 'CSV', '세계 주요도시 일별 기온', 3),
        ('Historical Hourly Weather Data 2012-2017', 'https://www.kaggle.com/datasets/selfishgene/historical-hourly-weather-data', 'selfishgene/historical-hourly-weather-data', 'CSV', '시간별 기상 (미국 4도시 포함)', 3),
        ('Monthly Mean Temp US Cities 1948-2022', 'https://www.kaggle.com/datasets/garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022', 'garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022', 'CSV', '미국 도시 월평균 기온 74년', 3),
        ('US Weather Events 2016-2022', 'https://www.kaggle.com/datasets/sobhanmoosavi/us-weather-events', 'sobhanmoosavi/us-weather-events', 'CSV', '폭염 등 기상이벤트', 3),
        ('Global Daily Climate Data', 'https://www.kaggle.com/datasets/guillemservera/global-daily-climate-data', 'guillemservera/global-daily-climate-data', 'CSV', '글로벌 일별 기후', 3),
        
        # 소주제 4: 산업전환
        ('BLS National Employment Hours Earnings', 'https://www.kaggle.com/datasets/bls/employment', 'bls/employment', 'CSV', '미국 산업별 고용·임금', 4),
        ('USA Bureau of Labor Statistics', 'https://www.kaggle.com/datasets/bls/bls', 'bls/bls', 'CSV', 'BLS 종합 데이터', 4),
        ('Global Economy Indicators', 'https://www.kaggle.com/datasets/prasad22/global-economy-indicators', 'prasad22/global-economy-indicators', 'CSV', '국가별 경제지표', 4),
        ('Macro-Economic Indicators', 'https://www.kaggle.com/datasets/veselagencheva/macro-economic-indicators-dataset-country-level', 'veselagencheva/macro-economic-indicators-dataset-country-level', 'CSV', '거시경제 지표', 4),
        ('World GDP by Country Region', 'https://www.kaggle.com/datasets/sazidthe1/world-gdp-data', 'sazidthe1/world-gdp-data', 'CSV', 'GDP 데이터', 4),
    ]
    
    sql = """INSERT INTO data_sources 
             (source_name, source_url, kaggle_dataset_id, data_format, description, sub_topic)
             VALUES (%s, %s, %s, %s, %s, %s)"""
    cursor.executemany(sql, sources)
    conn.commit()
    conn.close()
    print(f"✅ Kaggle 데이터 소스 {len(sources)}개 등록 완료")

# =============================================
# 5. CSV → MySQL 로딩 함수
# =============================================

def load_csv_to_mysql(csv_path, table_name, db_name=DB_NAME, 
                      encoding='utf-8', chunksize=5000):
    """
    Kaggle CSV 파일을 MySQL 테이블로 로딩
    
    Parameters:
        csv_path: CSV 파일 경로
        table_name: 대상 테이블명
        db_name: 데이터베이스명
        encoding: CSV 인코딩 (한국어: 'cp949' 또는 'utf-8')
        chunksize: 한 번에 삽입할 행 수
    """
    conn = get_connection(db_name)
    
    # CSV 읽기 (청크 단위)
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
# 6. 소주제별 데이터 로딩 예시
# =============================================

# --- 소주제 1: 대구 아파트 실거래가 ---
# load_csv_to_mysql(
#     'kaggle_data/daegu_apartment_transaction.csv',
#     'daegu_housing_prices',
#     encoding='cp949'  # 한국어 CSV
# )

# --- 소주제 1: Zillow ZHVI ---
# load_csv_to_mysql(
#     'kaggle_data/zillow_zhvi.csv',
#     'us_housing_prices'
# )

# --- 소주제 2: Korean Demographics ---
# load_csv_to_mysql(
#     'kaggle_data/korean_demographics.csv',
#     'korean_demographics'
# )

# --- 소주제 2: US Census ---
# load_csv_to_mysql(
#     'kaggle_data/us_census_demographic.csv',
#     'us_demographics'
# )

# --- 소주제 3: Berkeley Earth Temperature ---
# load_csv_to_mysql(
#     'kaggle_data/GlobalLandTemperaturesByCity.csv',
#     'climate_temperature'
# )

# --- 소주제 4: BLS Employment ---
# load_csv_to_mysql(
#     'kaggle_data/bls_employment.csv',
#     'us_industry_employment'
# )

# =============================================
# 7. 실행
# =============================================

if __name__ == '__main__':
    create_database()
    create_all_tables()
    insert_cities()
    insert_kaggle_sources()
    print("\n🎉 Kaggle 전용 프로젝트 초기화 완료!")
```

---

## 📦 Kaggle 데이터셋 총 정리 (29개)

### 소주제 1: 주택 가격 (9개)
| 구분 | 데이터셋 | Kaggle ID |
|------|---------|-----------|
| 🇰🇷 | Daegu Apartment Actual Transaction ⭐ | `lnoahl/daegu-aptmernt-actual-transaction` |
| 🇰🇷 | Daegu Real Estate Data ⭐ | `afifanuraini/daegu-real-estate-datacsv` |
| 🇰🇷 | Korean Apartment Deal Data | `brainer3220/korean-real-estate-transaction-data` |
| 🇰🇷 | Korea House Data 10yrs | `gunhee/koreahousedata` |
| 🇺🇸 | Zillow Home Value Index Monthly ⭐ | `robikscube/zillow-home-value-index` |
| 🇺🇸 | US Cities Housing Market Data ⭐ | `vincentvaseghi/us-cities-housing-market-data` |
| 🇺🇸 | USA Real Estate Dataset 2.2M+ | `ahmedshahriarsakib/usa-real-estate-dataset` |
| 🇺🇸 | US Housing Trends Zillow 2018-2024 | `clovisdalmolinvieira/us-housing-trends-values-time-and-price-cuts` |
| 🇺🇸 | Zillow House Price Data by Room | `paultimothymooney/zillow-house-price-data` |

### 소주제 2: 인구·수요 (8개)
| 구분 | 데이터셋 | Kaggle ID |
|------|---------|-----------|
| 🇰🇷 | Korean Demographics 2000-2022 ⭐ | `alexandrepetit881234/korean-demographics-20002022` |
| 🇰🇷 | Korea Income and Welfare | `hongsean/korea-income-and-welfare` |
| 🇺🇸 | US Census Demographic Data ⭐ | `muonneutrino/us-census-demographic-data` |
| 🇺🇸 | Population Time Series Data | `census/population-time-series-data` |
| 🇺🇸 | US County Historical Demographics | `bitrook/us-county-historical-demographics` |
| 🇺🇸 | US County Data | `evangambit/us-county-data` |
| 🌍 | World Population Growth Rate by Cities 2024 | `dataanalyst001/world-population-growth-rate-by-cities-2024` |
| 🌍 | World Cities Database | `max-mind/world-cities-database` |

### 소주제 3: 기후·가격격차 (6개)
| 구분 | 데이터셋 | Kaggle ID |
|------|---------|-----------|
| 🌍 | Climate Change: Earth Surface Temperature ⭐ | `berkeleyearth/climate-change-earth-surface-temperature-data` |
| 🌍 | Daily Temperature of Major Cities ⭐ | `sudalairajkumar/daily-temperature-of-major-cities` |
| 🇺🇸 | Historical Hourly Weather 2012-2017 | `selfishgene/historical-hourly-weather-data` |
| 🇺🇸 | Monthly Mean Temp US Cities 1948-2022 | `garrickhague/temp-data-of-prominent-us-cities-from-1948-to-2022` |
| 🇺🇸 | US Weather Events 2016-2022 | `sobhanmoosavi/us-weather-events` |
| 🌍 | Global Daily Climate Data | `guillemservera/global-daily-climate-data` |

### 소주제 4: 산업전환 (5개)
| 구분 | 데이터셋 | Kaggle ID |
|------|---------|-----------|
| 🇺🇸 | BLS National Employment ⭐ | `bls/employment` |
| 🇺🇸 | USA Bureau of Labor Statistics | `bls/bls` |
| 🌍 | Global Economy Indicators ⭐ | `prasad22/global-economy-indicators` |
| 🌍 | Macro-Economic Indicators | `veselagencheva/macro-economic-indicators-dataset-country-level` |
| 🌍 | World GDP by Country Region | `sazidthe1/world-gdp-data` |

**+ 소주제 1 데이터 재활용** (소주제 3, 4에서 가격 데이터로 활용)

---

## ⚠️ Kaggle 전용 전환 시 주의사항

### 1. 소주제 4 한국 산업 데이터 한계
- Kaggle에 대구 시도별 산업·고용 데이터가 **직접 없음**
- **대안:** Korean Demographics + Korea Income and Welfare로 경제활동인구·소득 기반 간접 분석
- Global Economy Indicators로 한국 전체 제조업→서비스업 전환 거시 트렌드 활용

### 2. 소주제 2 한국 인구이동 상세 데이터 한계
- KOSIS 수준의 시도별 전입·전출 상세 데이터 Kaggle에 없음
- **대안:** Korean Demographics 2000-2022의 지역별 인구변동 + World Population Growth Rate로 보완
- 인구 "이동"이 아닌 인구 "변동(증감)"으로 분석 프레임 조정

### 3. 소주제 3 한국 기후 데이터
- 기상자료개방포털 수준의 ASOS 상세 관측 데이터 Kaggle에 없음
- **대안:** Berkeley Earth 데이터의 GlobalLandTemperaturesByCity.csv에 **대구(Daegu) 포함** → 월평균 기온 시계열 분석 가능
- Daily Temperature of Major Cities에서도 한국 도시 데이터 활용 가능

---

## 🔄 프로젝트 워크플로우

```
1. Kaggle 데이터 다운로드 (29개 데이터셋)
   └→ kaggle datasets download -d {dataset_id}

2. 데이터 전처리 (pandas)
   ├→ 대구 데이터: 구별 필터링, 날짜 통일, 금액 단위 정리
   ├→ 미국 데이터: Dallas/Atlanta/Phoenix/Charlotte 필터링
   ├→ 기후 데이터: 5개 도시 필터링 (대구+미국4)
   └→ 컬럼명 통일, 결측치 처리, 환율 적용

3. DB 구축 (pymysql)
   └→ 테이블 생성 & 데이터 로딩

4. 분석 쿼리 (SQL JOIN)
   ├→ 소주제1: 도시별 가격 추이 시계열 비교
   ├→ 소주제2: 인구변동률 vs 부동산 가격변동률 상관분석
   ├→ 소주제3: 기온범위별 지역가격 분포
   └→ 소주제4: 산업고용 변화 vs 부동산 가격 변화

5. 시각화 (matplotlib/seaborn)
   ├→ 가격 추이 선형 차트 (대구 vs 미국 4도시)
   ├→ 인구-부동산 산점도 + 회귀선
   ├→ 기온-가격 히트맵
   └→ 산업 전환 타임라인 차트

6. 인사이트 도출
   └→ 소주제별 결론 + 종합 비교분석 리포트
```
