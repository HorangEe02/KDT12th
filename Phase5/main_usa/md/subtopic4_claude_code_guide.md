# 소주제 4: 산업 전환과 부동산 — Claude Code 구현 가이드

## 🎯 Claude Code에게 전달할 프로젝트 컨텍스트

> 이 문서는 Claude Code에 복사·붙여넣기하여 소주제 4의 전체 파이프라인을 단계별로 구현하기 위한 가이드입니다.

---

## 📋 프로젝트 요약

| 항목 | 내용 |
|------|------|
| **프로젝트명** | 내륙 거점 도시의 부동산 시장 구조 비교: 대구 vs 미국 유사 도시 |
| **소주제 4** | 산업 전환과 부동산 (Industrial Transformation & Real Estate) |
| **분석 목표** | 전통 산업(섬유)→하이테크 전환이 상업/주거용 부동산에 미치는 영향 분석 |
| **비교 도시** | 대구 ↔ Charlotte(섬유→금융/하이테크 전환), Atlanta(자동차·배터리 허브), Dallas(종합), Phoenix(기후) |
| **핵심 비교축** | Charlotte: 섬유→금융 전환 완료, 대구: 섬유→하이테크 전환 진행 중 |

---

## 🔧 환경 설정

### DB 연결 정보

```python
DB_CONFIG = {
    'host': '172.30.1.47',
    'user': 'wonho',
    'password': '1111',
    'charset': 'utf8mb4'
}
DB_NAME = 'real_estate_comparison'
```

### 디렉토리 구조

```
project/
├── data/
│   ├── realtor-data.zip.csv                          # 222만건 개별매물
│   ├── zillow_Housing/
│   │   ├── Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv
│   │   ├── Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   │   ├── Metro_market_temp_index_uc_sfrcondo_month.csv
│   │   ├── Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   │   └── Metro_sales_count_now_uc_sfrcondo_month.csv
│   └── Zillow_Economics/
│       ├── Metro_time_series.csv
│       └── State_time_series.csv
├── kaggle_data/                                       # Kaggle 다운로드
│   ├── bls_employment/                               # U4-1: BLS 고용데이터
│   ├── global_economy_indicators/                    # G4-1: 글로벌 경제지표
│   ├── macro_economic_indicators/                    # G4-2: 거시경제
│   ├── world_gdp/                                    # G4-3: GDP
│   ├── korean_demographics/                          # K2-1: 한국 인구통계
│   └── korea_income_welfare/                         # K2-2: 한국 소득복지
├── scripts/
│   └── subtopic4/
│       ├── step0_setup.py
│       ├── step1_download_kaggle.py
│       ├── step2_create_tables.py
│       ├── step3_load_us_zillow.py
│       ├── step4_load_kaggle_bls.py
│       ├── step5_load_kaggle_global.py
│       ├── step6_load_korean_proxy.py
│       ├── step7_analysis_queries.py
│       └── step8_visualization.py
└── output/
    └── subtopic4/
```

### 필요 패키지

```bash
pip install pymysql pandas numpy matplotlib seaborn scipy openpyxl kaggle
```

---

## 🗄️ STEP 0: 공통 유틸리티 모듈

> **Claude Code 프롬프트:**
> `scripts/subtopic4/step0_setup.py` 파일을 만들어줘. DB 연결, 범용 CSV→MySQL 로딩, Zillow Wide→Long 변환 함수를 포함해야 해.

### 구현 사양

```python
# === scripts/subtopic4/step0_setup.py ===

import pymysql
import pandas as pd
import numpy as np
import os

# ----- DB 설정 -----
DB_CONFIG = {
    'host': '172.30.1.47',
    'user': 'wonho',
    'password': '1111',
    'charset': 'utf8mb4'
}
DB_NAME = 'real_estate_comparison'

DATA_DIR = 'data/'
KAGGLE_DIR = 'kaggle_data/'
ZILLOW_HOUSING_DIR = f'{DATA_DIR}zillow_Housing/'
ZILLOW_ECONOMICS_DIR = f'{DATA_DIR}Zillow_Economics/'

# 비교 대상 4개 MSA 정식 명칭
TARGET_METROS = [
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',
    'Phoenix-Mesa-Chandler, AZ',
    'Charlotte-Concord-Gastonia, NC-SC',
]

# 도시별 city_id 매핑 (cities 테이블 기준)
CITY_ID_MAP = {
    'Dallas': 2,
    'Atlanta': 3,
    'Phoenix': 4,
    'Charlotte': 5,
}

# 주(State) 약어 매핑
STATE_MAP = {
    'Dallas': 'TX',
    'Atlanta': 'GA',
    'Phoenix': 'AZ',
    'Charlotte': 'NC',
}


def get_connection(db_name=None):
    """MySQL 연결 반환"""
    config = DB_CONFIG.copy()
    if db_name:
        config['db'] = db_name
    return pymysql.connect(**config)


def load_csv_to_mysql(csv_path, table_name, db_name=DB_NAME,
                      encoding='utf-8', chunksize=5000):
    """범용 CSV → MySQL 로딩"""
    conn = get_connection(db_name)
    total_rows = 0
    for chunk in pd.read_csv(csv_path, encoding=encoding, chunksize=chunksize):
        chunk = chunk.where(pd.notnull(chunk), None)
        cols = ', '.join([f'`{c}`' for c in chunk.columns])
        placeholders = ', '.join(['%s'] * len(chunk.columns))
        sql = f"INSERT INTO `{table_name}` ({cols}) VALUES ({placeholders})"
        cursor = conn.cursor()
        data = [tuple(None if pd.isna(v) else v for v in row) for row in chunk.values]
        cursor.executemany(sql, data)
        conn.commit()
        total_rows += len(chunk)
        print(f"  ... {total_rows}행 삽입됨")
    conn.close()
    print(f"✅ '{csv_path}' → '{table_name}' 로딩 완료 (총 {total_rows}행)")
    return total_rows


def load_zillow_wide_to_long(csv_path, table_name, value_col_name,
                             target_metros=None, db_name=DB_NAME):
    """
    zillow_Housing Wide Format → Long Format 변환 후 MySQL 적재
    Wide: 행=지역, 열=날짜 → Long: (region, year_month, value)
    """
    if target_metros is None:
        target_metros = TARGET_METROS

    df = pd.read_csv(csv_path)

    # 식별 열과 날짜 열 분리
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    if 'BaseDate' in df.columns:
        id_cols.append('BaseDate')
    date_cols = [c for c in df.columns if c not in id_cols]

    # 타겟 MSA + 전국 필터
    filter_names = target_metros + ['United States']
    df_filtered = df[df['RegionName'].isin(filter_names)].copy()

    if df_filtered.empty:
        print(f"⚠️ 타겟 MSA 없음: {csv_path}")
        return 0

    # melt
    df_long = df_filtered.melt(
        id_vars=[c for c in id_cols if c in df_filtered.columns],
        value_vars=date_cols,
        var_name='year_month',
        value_name=value_col_name
    )
    df_long = df_long.dropna(subset=[value_col_name])
    df_long['year_month'] = df_long['year_month'].str[:7]

    # 적재
    conn = get_connection(db_name)
    cursor = conn.cursor()
    sql = f"""INSERT INTO `{table_name}`
              (region_id, region_name, state_name, year_month, `{value_col_name}`)
              VALUES (%s, %s, %s, %s, %s)"""
    data = [
        (row.get('RegionID'), row['RegionName'], row.get('StateName'),
         row['year_month'], row[value_col_name])
        for _, row in df_long.iterrows()
    ]
    cursor.executemany(sql, data)
    conn.commit()
    conn.close()
    print(f"✅ Wide→Long 완료: {os.path.basename(csv_path)} → {table_name} ({len(data)}행)")
    return len(data)
```

---

## 🗄️ STEP 1: Kaggle 데이터 다운로드

> **Claude Code 프롬프트:**
> 소주제 4에 필요한 Kaggle 데이터셋을 다운로드하는 스크립트를 만들어줘. kaggle API를 사용하고, 다운로드 후 압축 해제까지 해야 해.

### 다운로드 대상 (6개 데이터셋)

| 코드 | Kaggle ID | 저장 폴더 | 용도 |
|------|-----------|----------|------|
| U4-1 | `bls/employment` | `kaggle_data/bls_employment/` | ⭐ 미국 산업별 고용 (핵심) |
| U4-2 | `bls/bls` | `kaggle_data/bls_bls/` | BLS 종합 |
| G4-1 | `prasad22/global-economy-indicators` | `kaggle_data/global_economy/` | ⭐ 글로벌 경제지표 |
| G4-2 | `veselagencheva/macro-economic-indicators-dataset-country-level` | `kaggle_data/macro_economic/` | 거시경제 |
| G4-3 | `sazidthe1/world-gdp-data` | `kaggle_data/world_gdp/` | GDP |
| K2-1 | `alexandrepetit881234/korean-demographics-20002022` | `kaggle_data/korean_demographics/` | 한국 인구통계 (대구 산업 프록시) |
| K2-2 | `hongsean/korea-income-and-welfare` | `kaggle_data/korea_income/` | 한국 소득복지 (대구 산업 프록시) |

### 구현 사양

```python
# === scripts/subtopic4/step1_download_kaggle.py ===
import os
import zipfile

KAGGLE_DATASETS = {
    'bls/employment':           'kaggle_data/bls_employment',
    'bls/bls':                  'kaggle_data/bls_bls',
    'prasad22/global-economy-indicators': 'kaggle_data/global_economy',
    'veselagencheva/macro-economic-indicators-dataset-country-level': 'kaggle_data/macro_economic',
    'sazidthe1/world-gdp-data': 'kaggle_data/world_gdp',
    'alexandrepetit881234/korean-demographics-20002022': 'kaggle_data/korean_demographics',
    'hongsean/korea-income-and-welfare': 'kaggle_data/korea_income',
}

def download_all():
    for dataset_id, save_dir in KAGGLE_DATASETS.items():
        os.makedirs(save_dir, exist_ok=True)
        cmd = f'kaggle datasets download -d {dataset_id} -p {save_dir} --unzip'
        print(f"📥 다운로드 중: {dataset_id}")
        os.system(cmd)
        # zip 파일 있으면 추가 해제
        for f in os.listdir(save_dir):
            if f.endswith('.zip'):
                with zipfile.ZipFile(os.path.join(save_dir, f), 'r') as z:
                    z.extractall(save_dir)
                print(f"  📦 압축 해제: {f}")
    print("✅ 모든 Kaggle 데이터셋 다운로드 완료")

if __name__ == '__main__':
    download_all()
```

---

## 🗄️ STEP 2: 소주제 4 전용 테이블 생성

> **Claude Code 프롬프트:**
> 소주제 4 분석에 필요한 MySQL 테이블을 생성하는 스크립트를 만들어줘. DB: real_estate_comparison, 연결정보: 172.30.1.47 / wonho / 1111

### 생성할 테이블 목록 (7개)

| 테이블명 | 용도 | 소스 |
|----------|------|------|
| `us_industry_employment` | 미국 산업별 고용 데이터 | BLS Kaggle |
| `economic_indicators` | 글로벌 경제지표 (한국/미국) | Global Economy Kaggle |
| `us_metro_demand` | MSA 수급지표 (신규건설, 필요소득, 시장온도 등) | Zillow Housing (data/) |
| `us_metro_zhvf_growth` | MSA 주택가치 예측 성장률 | Zillow Housing (data/) |
| `industry_housing_impact` | ⭐ 산업-부동산 영향 분석 결과 테이블 | 분석 산출 |
| `zillow_timeseries` | Zillow Economics 종합 시계열 | Zillow Economics (data/) — 기존 테이블 공유 |
| `korean_demographics` | 한국 인구통계 (대구 산업 프록시) | Kaggle — 기존 테이블 공유 |

### 전체 DDL

```python
# === scripts/subtopic4/step2_create_tables.py ===

import pymysql
import sys
sys.path.append('scripts/subtopic4')
from step0_setup import get_connection, DB_NAME

TABLES_SQL = [
    # ----- 미국 산업별 고용 -----
    """
    CREATE TABLE IF NOT EXISTS us_industry_employment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_id INT,
        city_name VARCHAR(50),
        state VARCHAR(10),
        year INT,
        month INT,
        series_id VARCHAR(30),
        industry_code VARCHAR(20),
        industry_name VARCHAR(200),
        employee_count BIGINT,
        avg_weekly_hours DECIMAL(8,2),
        avg_hourly_earnings DECIMAL(10,2),
        source_dataset VARCHAR(100) DEFAULT 'bls/employment',
        INDEX idx_city_year (city_name, year),
        INDEX idx_industry (industry_code, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- 글로벌 경제지표 -----
    """
    CREATE TABLE IF NOT EXISTS economic_indicators (
        id INT AUTO_INCREMENT PRIMARY KEY,
        country VARCHAR(50),
        country_code VARCHAR(10),
        year INT,
        gdp DECIMAL(20,2),
        gdp_growth_rate DECIMAL(8,4),
        gdp_per_capita DECIMAL(15,2),
        manufacturing_pct DECIMAL(8,4),
        services_pct DECIMAL(8,4),
        industry_pct DECIMAL(8,4),
        agriculture_pct DECIMAL(8,4),
        unemployment_rate DECIMAL(8,4),
        inflation_rate DECIMAL(8,4),
        population BIGINT,
        source_dataset VARCHAR(100),
        INDEX idx_country_year (country, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- 미국 MSA 수급지표 (소주제 2와 공유, 소주제 4 컬럼 포함) -----
    """
    CREATE TABLE IF NOT EXISTS us_metro_demand (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- 주택가치 예측 성장률 -----
    """
    CREATE TABLE IF NOT EXISTS us_metro_zhvf_growth (
        id INT AUTO_INCREMENT PRIMARY KEY,
        region_id INT,
        region_name VARCHAR(200),
        state_name VARCHAR(10),
        base_date DATE,
        forecast_date DATE,
        growth_rate DECIMAL(8,4),
        INDEX idx_region (region_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- ⭐ 산업-부동산 영향 분석 결과 -----
    """
    CREATE TABLE IF NOT EXISTS industry_housing_impact (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_id INT,
        city_name VARCHAR(50),
        country VARCHAR(20),
        year INT,
        dominant_industry VARCHAR(100),
        industry_employee_change DECIMAL(8,4),
        manufacturing_employee_pct DECIMAL(8,4),
        service_employee_pct DECIMAL(8,4),
        hightech_employee_pct DECIMAL(8,4),
        housing_price_change DECIMAL(8,4),
        new_construction_sales INT,
        new_construction_sales_change DECIMAL(8,4),
        market_temp_index DECIMAL(8,2),
        market_temp_change DECIMAL(8,2),
        income_needed DECIMAL(15,2),
        income_needed_change DECIMAL(8,4),
        source_dataset VARCHAR(100),
        INDEX idx_city_year (city_name, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- Zillow Economics 종합 시계열 (다른 소주제와 공유) -----
    """
    CREATE TABLE IF NOT EXISTS zillow_timeseries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE,
        region_name VARCHAR(200),
        region_level ENUM('city','county','metro','state','zip','neighborhood'),
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- 한국 인구통계 (대구 산업 프록시) -----
    """
    CREATE TABLE IF NOT EXISTS korean_demographics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT,
        region VARCHAR(50),
        total_population BIGINT,
        population_change BIGINT,
        population_change_rate DECIMAL(8,4),
        birth_rate DECIMAL(8,4),
        death_rate DECIMAL(8,4),
        economic_activity_rate DECIMAL(8,4),
        employment_rate DECIMAL(8,4),
        unemployment_rate DECIMAL(8,4),
        source_dataset VARCHAR(100),
        INDEX idx_region_year (region, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def create_subtopic4_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for i, sql in enumerate(TABLES_SQL):
        try:
            cursor.execute(sql)
            # 테이블명 추출
            tbl = sql.split('EXISTS')[1].split('(')[0].strip() if 'EXISTS' in sql else f'table_{i}'
            print(f"  ✅ {tbl}")
        except Exception as e:
            print(f"  ⚠️ 오류: {e}")
    conn.commit()
    conn.close()
    print("\n✅ 소주제 4 테이블 생성 완료")


if __name__ == '__main__':
    create_subtopic4_tables()
```

---

## 📊 STEP 3: 미국 Zillow 부동산 데이터 로딩 (data/ 폴더)

> **Claude Code 프롬프트:**
> data/ 폴더의 Zillow 데이터에서 소주제 4에 필요한 지표를 추출하여 MySQL에 적재해줘. 4개 MSA(Dallas, Atlanta, Phoenix, Charlotte) + United States를 필터링해야 해.

### 로딩할 파일 & 대상 테이블

| 파일 (zillow_Housing/) | 테이블 | 컬럼명 | 기간 |
|------------------------|--------|--------|------|
| `Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv` | `us_metro_demand` | `new_construction_sales` | 2018~2025 |
| `Metro_new_homeowner_income_needed_...csv` | `us_metro_demand` | `income_needed` | 2012~2025 |
| `Metro_market_temp_index_uc_sfrcondo_month.csv` | `us_metro_demand` | `market_temp_index` | 2018~2025 |
| `Metro_sales_count_now_uc_sfrcondo_month.csv` | `us_metro_demand` | `sales_count` | 2008~2025 |
| `Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv` | `us_metro_zhvi` (참조) | `zhvi` | 2000~2025 |
| `Metro_zhvf_growth_...csv` | `us_metro_zhvf_growth` | `growth_rate` | 예측 |

| 파일 (Zillow_Economics/) | 테이블 | 핵심 컬럼 |
|--------------------------|--------|----------|
| `Metro_time_series.csv` | `zillow_timeseries` | PctOfHomesIncreasingInValues, PctOfHomesSellingForLoss 등 |
| `State_time_series.csv` | `zillow_timeseries` | TX/GA/AZ/NC 주 단위 거시 |

### 구현 사양

```python
# === scripts/subtopic4/step3_load_us_zillow.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *

# =============================================
# 3-1. us_metro_demand 테이블에 수급지표 적재
# =============================================
# 주의: us_metro_demand는 여러 컬럼을 하나의 테이블에 통합함
# 각 Wide CSV에서 하나의 컬럼씩 INSERT 또는 UPDATE

def load_demand_indicator(csv_path, col_name):
    """
    Wide CSV → 4개 MSA 필터 → Long 변환 →
    us_metro_demand 테이블의 특정 컬럼에 INSERT
    
    ※ 같은 (region_name, year_month)에 대해 여러 지표가 별도 행으로 들어감.
      나중에 분석 시 JOIN 또는 집계 필요.
      또는: 첫 지표 INSERT, 이후 지표는 UPDATE 방식도 가능.
    """
    df = pd.read_csv(csv_path)
    
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    if 'BaseDate' in df.columns:
        id_cols.append('BaseDate')
    date_cols = [c for c in df.columns if c not in id_cols]
    
    filter_names = TARGET_METROS + ['United States']
    df_f = df[df['RegionName'].isin(filter_names)].copy()
    
    if df_f.empty:
        print(f"⚠️ 타겟 MSA 없음: {csv_path}")
        return
    
    df_long = df_f.melt(
        id_vars=[c for c in id_cols if c in df_f.columns],
        value_vars=date_cols,
        var_name='year_month',
        value_name=col_name
    ).dropna(subset=[col_name])
    df_long['year_month'] = df_long['year_month'].str[:7]
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    sql = f"""INSERT INTO us_metro_demand
              (region_id, region_name, state_name, year_month, `{col_name}`)
              VALUES (%s, %s, %s, %s, %s)"""
    data = [
        (row.get('RegionID'), row['RegionName'], row.get('StateName'),
         row['year_month'], row[col_name])
        for _, row in df_long.iterrows()
    ]
    cursor.executemany(sql, data)
    conn.commit()
    conn.close()
    print(f"✅ {col_name}: {len(data)}행 → us_metro_demand")


# =============================================
# 3-2. 주택가치 예측 성장률 (ZHVF)
# =============================================

def load_zhvf_growth():
    """Metro_zhvf_growth CSV → us_metro_zhvf_growth 테이블"""
    csv_path = f'{ZILLOW_HOUSING_DIR}Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
    df = pd.read_csv(csv_path)
    
    filter_names = TARGET_METROS + ['United States']
    df_f = df[df['RegionName'].isin(filter_names)].copy()
    
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    date_cols = [c for c in df_f.columns if c not in id_cols]
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    rows = 0
    for _, region_row in df_f.iterrows():
        base_date = region_row.get('BaseDate')
        for dc in date_cols:
            val = region_row[dc]
            if pd.notna(val):
                sql = """INSERT INTO us_metro_zhvf_growth
                         (region_id, region_name, state_name, base_date, forecast_date, growth_rate)
                         VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (
                    region_row.get('RegionID'), region_row['RegionName'],
                    region_row.get('StateName'), base_date, dc, val
                ))
                rows += 1
    
    conn.commit()
    conn.close()
    print(f"✅ ZHVF 성장률: {rows}행 → us_metro_zhvf_growth")


# =============================================
# 3-3. Zillow Economics Metro/State 시계열
# =============================================

def load_metro_timeseries():
    """Metro_time_series.csv에서 소주제 4 핵심 지표 로딩"""
    csv_path = f'{ZILLOW_ECONOMICS_DIR}Metro_time_series.csv'
    
    # 소주제 4 핵심 지표
    selected_cols = [
        'ZHVI_AllHomes',
        'PctOfHomesIncreasingInValues_AllHomes',
        'PctOfHomesDecreasingInValues_AllHomes',
        'PctOfHomesSellingForLoss_AllHomes',
        'PctOfListingsWithPriceReductions_AllHomes',
        'MedianPctOfPriceReduction_AllHomes',
        'Sale_Counts',
    ]
    
    # Metro_time_series의 RegionName은 MSA 코드(숫자)
    # → CountyCrossWalk로 MSA 이름 매핑 필요하거나, 직접 코드 확인 필요
    # 대안: State_time_series.csv 사용 (RegionName = 주 이름, 더 직관적)
    
    print("ℹ️ Metro_time_series는 RegionName이 MSA 코드(숫자)입니다.")
    print("   소주제 4에서는 State_time_series.csv (주 단위) 위주로 활용합니다.")


def load_state_timeseries():
    """State_time_series.csv에서 TX/GA/AZ/NC 주 시계열 로딩"""
    csv_path = f'{ZILLOW_ECONOMICS_DIR}State_time_series.csv'
    target_states = ['Texas', 'Georgia', 'Arizona', 'North Carolina']
    
    selected_cols = [
        'ZHVI_AllHomes', 'ZHVIPerSqft_AllHomes',
        'PctOfHomesIncreasingInValues_AllHomes',
        'PctOfHomesDecreasingInValues_AllHomes',
        'PctOfHomesSellingForLoss_AllHomes',
        'PctOfListingsWithPriceReductions_AllHomes',
        'MedianPctOfPriceReduction_AllHomes',
        'Sale_Counts', 'Sale_Counts_Seas_Adj',
    ]
    use_cols = ['Date', 'RegionName'] + selected_cols
    
    df = pd.read_csv(csv_path, usecols=lambda c: c in use_cols)
    df = df[df['RegionName'].isin(target_states)]
    df = df.where(pd.notnull(df), None)
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    rows = 0
    
    for _, row in df.iterrows():
        sql = """INSERT INTO zillow_timeseries
                 (date, region_name, region_level,
                  zhvi_all, zhvi_per_sqft,
                  pct_homes_increasing, pct_homes_decreasing,
                  pct_homes_selling_for_loss,
                  pct_listings_price_reduction, median_pct_price_reduction,
                  sale_counts, sale_counts_seas_adj, source_file)
                 VALUES (%s,%s,'state',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor.execute(sql, (
            row.get('Date'), row['RegionName'],
            row.get('ZHVI_AllHomes'), row.get('ZHVIPerSqft_AllHomes'),
            row.get('PctOfHomesIncreasingInValues_AllHomes'),
            row.get('PctOfHomesDecreasingInValues_AllHomes'),
            row.get('PctOfHomesSellingForLoss_AllHomes'),
            row.get('PctOfListingsWithPriceReductions_AllHomes'),
            row.get('MedianPctOfPriceReduction_AllHomes'),
            row.get('Sale_Counts'), row.get('Sale_Counts_Seas_Adj'),
            'State_time_series.csv'
        ))
        rows += 1
    
    conn.commit()
    conn.close()
    print(f"✅ State 시계열: {rows}행 → zillow_timeseries (state)")


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 3: 미국 Zillow 부동산 데이터 로딩")
    print("=" * 60)
    
    # 3-1. 수급 지표 (us_metro_demand)
    demand_files = [
        ('Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv', 'new_construction_sales'),
        ('Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv', 'income_needed'),
        ('Metro_market_temp_index_uc_sfrcondo_month.csv', 'market_temp_index'),
        ('Metro_sales_count_now_uc_sfrcondo_month.csv', 'sales_count'),
    ]
    for fname, col in demand_files:
        load_demand_indicator(f'{ZILLOW_HOUSING_DIR}{fname}', col)
    
    # 3-2. 예측 성장률
    load_zhvf_growth()
    
    # 3-3. State 시계열
    load_state_timeseries()
    
    print("\n🎉 STEP 3 완료!")
```

---

## 📊 STEP 4: BLS 고용 데이터 로딩 (Kaggle → MySQL)

> **Claude Code 프롬프트:**
> BLS 고용 데이터(bls/employment)를 MySQL에 적재해줘. 4개 비교 도시가 포함된 MSA의 산업별 고용 데이터를 추출해야 해. 특히 제조업(Manufacturing), 서비스업(Service), 정보·기술(Information/Professional) 산업을 구분해서 넣어줘.

### BLS 데이터 구조 예상

`bls/employment` 데이터셋은 CES(Current Employment Statistics) 기반으로 주로 다음 파일을 포함:

- `survey.csv` 또는 `ce.data.*.csv` — 시계열 고용 데이터
- `ce.series` — series_id별 메타 (area, industry 등)
- `ce.industry` — 산업 코드 정의

### 핵심 산업 분류

| 산업 코드 범위 | 산업명 | 소주제 4 의미 |
|---------------|--------|-------------|
| 31-33 (NAICS) | Manufacturing (제조업) | 전통 산업 (섬유 포함) |
| 42-81 (NAICS) | Service-Providing | 서비스업 전반 |
| 51 | Information | IT/기술 |
| 52 | Finance and Insurance | 금융 (Charlotte 핵심) |
| 54 | Professional, Scientific, Technical | 하이테크 |
| 62 | Health Care | 의료 |
| 72 | Accommodation and Food Services | 관광·서비스 |

### 구현 사양

```python
# === scripts/subtopic4/step4_load_kaggle_bls.py ===

import sys
import os
import glob
sys.path.append('scripts/subtopic4')
from step0_setup import *

KAGGLE_BLS_DIR = 'kaggle_data/bls_employment/'

# BLS MSA area codes (CES 기준, 확인 후 수정 필요)
# 형식: S{state_fips}{area_code} 또는 MSA FIPS
TARGET_MSA_AREAS = {
    'Dallas':    ['D1900', '19100'],   # Dallas-Fort Worth-Arlington
    'Atlanta':   ['A1200', '12060'],   # Atlanta-Sandy Springs
    'Phoenix':   ['P3800', '38060'],   # Phoenix-Mesa-Chandler
    'Charlotte': ['C1580', '16740'],   # Charlotte-Concord-Gastonia
}

# 핵심 산업 코드 (NAICS supersector)
KEY_INDUSTRIES = {
    '05000000': 'Total Private',
    '06000000': 'Goods-Producing',
    '07000000': 'Service-Providing',
    '08000000': 'Mining and Logging',
    '10000000': 'Construction',
    '20000000': 'Manufacturing',
    '30000000': 'Manufacturing - Durable',
    '31000000': 'Manufacturing - Nondurable',
    '40000000': 'Trade, Transportation, Utilities',
    '50000000': 'Information',
    '55000000': 'Financial Activities',
    '60000000': 'Professional and Business Services',
    '65000000': 'Education and Health Services',
    '70000000': 'Leisure and Hospitality',
    '80000000': 'Other Services',
    '90000000': 'Government',
}


def explore_bls_files():
    """BLS 다운로드 파일 구조 탐색 (실행 전 반드시 확인)"""
    print(f"📂 BLS 파일 목록 ({KAGGLE_BLS_DIR}):")
    for f in sorted(os.listdir(KAGGLE_BLS_DIR)):
        fpath = os.path.join(KAGGLE_BLS_DIR, f)
        size = os.path.getsize(fpath) / (1024*1024)
        print(f"  {f:50s} ({size:.1f} MB)")
        if f.endswith('.csv'):
            df_sample = pd.read_csv(fpath, nrows=3)
            print(f"    열: {list(df_sample.columns)}")
            print(f"    {df_sample.head(2).to_string()}\n")


def load_bls_employment():
    """
    BLS 고용 데이터 로딩
    
    ⚠️ 실제 BLS 파일 구조에 따라 로직 조정 필요!
    아래는 일반적인 BLS CES 데이터 구조 기반 코드입니다.
    먼저 explore_bls_files()로 파일 구조를 확인하세요.
    """
    # --- 파일 탐색 ---
    csv_files = glob.glob(os.path.join(KAGGLE_BLS_DIR, '*.csv'))
    if not csv_files:
        print("⚠️ BLS CSV 파일을 찾을 수 없습니다. 파일 구조를 확인하세요.")
        explore_bls_files()
        return
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0
    
    for csv_path in csv_files:
        print(f"\n처리 중: {os.path.basename(csv_path)}")
        
        try:
            df = pd.read_csv(csv_path, low_memory=False)
        except Exception as e:
            print(f"  ⚠️ 읽기 실패: {e}")
            continue
        
        # 열 이름 정규화 (공백, 대소문자)
        df.columns = df.columns.str.strip()
        
        print(f"  열: {list(df.columns)[:10]}...")
        print(f"  행수: {len(df):,}")
        
        # === BLS CES 데이터 처리 로직 ===
        # 일반적으로 series_id, year, period, value 열이 있음
        # series_id 형식: CEU{area}{industry}{datatype}
        #   area: 0000000 = 전국, 기타 = 주/MSA
        #   industry: 위 KEY_INDUSTRIES 참조
        #   datatype: 01 = 고용수, 02 = 주간근무시간, 03 = 시간당임금
        
        if 'series_id' in df.columns and 'year' in df.columns and 'value' in df.columns:
            # 전국 데이터 또는 MSA 데이터 필터
            for _, row in df.iterrows():
                sid = str(row.get('series_id', '')).strip()
                year = row.get('year')
                period = str(row.get('period', '')).strip()
                value = row.get('value')
                
                if not sid.startswith('CE') or pd.isna(value):
                    continue
                
                # 월 추출 (M01~M12)
                month = None
                if period.startswith('M') and period[1:].isdigit():
                    month = int(period[1:])
                    if month < 1 or month > 12:
                        continue
                
                # 산업코드 추출 (series_id 파싱)
                # 간단히 전국 데이터만 우선 적재
                sql = """INSERT INTO us_industry_employment
                         (series_id, year, month, employee_count, source_dataset)
                         VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(sql, (sid, year, month, value, 'bls/employment'))
                total += 1
                
                if total % 10000 == 0:
                    conn.commit()
                    print(f"  ... {total:,}행")
        
        # === 대안: 단순 열 구조 (year, industry, employees 등) ===
        elif 'year' in [c.lower() for c in df.columns]:
            print("  ℹ️ 단순 열 구조 감지 — 범용 로딩 시도")
            # 이 경우 탐색 결과를 기반으로 적절히 매핑
            pass
    
    conn.commit()
    conn.close()
    print(f"\n✅ BLS 고용 데이터 로딩 완료 (총 {total:,}행)")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 4: BLS 고용 데이터 로딩")
    print("=" * 60)
    
    # 먼저 파일 구조 탐색
    explore_bls_files()
    
    # 실제 로딩
    # load_bls_employment()
    
    print("\n⚠️ 주의: explore_bls_files() 결과를 확인한 후")
    print("   load_bls_employment()의 파싱 로직을 조정하고 주석 해제하세요.")
```

---

## 🌍 STEP 5: 글로벌 경제지표 로딩 (Kaggle → MySQL)

> **Claude Code 프롬프트:**
> Global Economy Indicators, Macro Economic Indicators, World GDP 데이터를 MySQL에 적재해줘. 한국(South Korea)과 미국(United States)만 필터링해서 economic_indicators 테이블에 넣어줘.

### 구현 사양

```python
# === scripts/subtopic4/step5_load_kaggle_global.py ===

import sys
import os
import glob
sys.path.append('scripts/subtopic4')
from step0_setup import *

TARGET_COUNTRIES = ['South Korea', 'Korea, Rep.', 'Korea', 'United States', 'USA']


def load_global_economy_indicators():
    """
    G4-1: prasad22/global-economy-indicators
    국가별 GDP, 산업구조(제조업/서비스업 비율), 실업률 등
    """
    base_dir = 'kaggle_data/global_economy/'
    csv_files = glob.glob(os.path.join(base_dir, '**/*.csv'), recursive=True)
    
    if not csv_files:
        print(f"⚠️ {base_dir}에 CSV 없음")
        return
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0
    
    for csv_path in csv_files:
        print(f"\n📄 처리: {os.path.basename(csv_path)}")
        try:
            df = pd.read_csv(csv_path, low_memory=False)
        except:
            continue
        
        df.columns = df.columns.str.strip()
        print(f"  열: {list(df.columns)[:8]}...")
        
        # 국가 필터 (열 이름은 실제 데이터에 맞게 조정)
        country_col = None
        for candidate in ['Country', 'country', 'Country Name', 'country_name', 'CountryName']:
            if candidate in df.columns:
                country_col = candidate
                break
        
        if country_col is None:
            print("  ⚠️ 국가 열 미발견 — 건너뜀")
            continue
        
        # 한국/미국 필터
        mask = df[country_col].isin(TARGET_COUNTRIES)
        df_f = df[mask].copy()
        
        if df_f.empty:
            print("  ⚠️ 한국/미국 데이터 없음")
            continue
        
        print(f"  필터 후: {len(df_f)}행")
        
        # 열 매핑 (실제 데이터 구조에 맞게 조정)
        col_map = {
            'Year': 'year', 'year': 'year',
            'GDP': 'gdp', 'gdp': 'gdp',
            'GDP growth': 'gdp_growth_rate', 'GDP_growth': 'gdp_growth_rate',
            'GDP per capita': 'gdp_per_capita',
            'Manufacturing': 'manufacturing_pct',
            'Services': 'services_pct',
            'Industry': 'industry_pct',
            'Agriculture': 'agriculture_pct',
            'Unemployment': 'unemployment_rate',
            'Inflation': 'inflation_rate',
            'Population': 'population',
        }
        
        for _, row in df_f.iterrows():
            country = row[country_col]
            # 국가명 통일
            if country in ['Korea, Rep.', 'Korea']:
                country = 'South Korea'
            elif country in ['USA']:
                country = 'United States'
            
            year_val = None
            for yc in ['Year', 'year', 'date']:
                if yc in df_f.columns:
                    year_val = row.get(yc)
                    break
            
            if year_val is None or pd.isna(year_val):
                continue
            
            sql = """INSERT INTO economic_indicators
                     (country, year, gdp, gdp_growth_rate, gdp_per_capita,
                      manufacturing_pct, services_pct, industry_pct, agriculture_pct,
                      unemployment_rate, inflation_rate, population, source_dataset)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            
            def safe_get(col_candidates):
                for c in col_candidates:
                    for orig, mapped in col_map.items():
                        if mapped == c and orig in df_f.columns:
                            v = row.get(orig)
                            return None if pd.isna(v) else v
                return None
            
            cursor.execute(sql, (
                country, int(year_val),
                safe_get(['gdp']),
                safe_get(['gdp_growth_rate']),
                safe_get(['gdp_per_capita']),
                safe_get(['manufacturing_pct']),
                safe_get(['services_pct']),
                safe_get(['industry_pct']),
                safe_get(['agriculture_pct']),
                safe_get(['unemployment_rate']),
                safe_get(['inflation_rate']),
                safe_get(['population']),
                os.path.basename(csv_path)
            ))
            total += 1
        
        conn.commit()
    
    conn.close()
    print(f"\n✅ 글로벌 경제지표 로딩 완료 (총 {total}행)")


def load_world_gdp():
    """G4-3: sazidthe1/world-gdp-data"""
    base_dir = 'kaggle_data/world_gdp/'
    csv_files = glob.glob(os.path.join(base_dir, '**/*.csv'), recursive=True)
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0
    
    for csv_path in csv_files:
        print(f"\n📄 처리: {os.path.basename(csv_path)}")
        df = pd.read_csv(csv_path, low_memory=False)
        df.columns = df.columns.str.strip()
        
        # 국가 필터
        for cc in ['Country', 'country', 'Country Name']:
            if cc in df.columns:
                df_f = df[df[cc].isin(TARGET_COUNTRIES)]
                if not df_f.empty:
                    print(f"  한국/미국: {len(df_f)}행")
                    # GDP 데이터 적재 (열 구조에 맞게 조정)
                    for _, row in df_f.iterrows():
                        sql = """INSERT INTO economic_indicators
                                 (country, year, gdp, source_dataset)
                                 VALUES (%s, %s, %s, %s)"""
                        # 연도 열 탐색
                        for yc in ['Year', 'year']:
                            if yc in df_f.columns:
                                cursor.execute(sql, (
                                    row[cc], row.get(yc),
                                    row.get('GDP', row.get('gdp')),
                                    'world_gdp'
                                ))
                                total += 1
                                break
                break
    
    conn.commit()
    conn.close()
    print(f"✅ World GDP 로딩 완료 ({total}행)")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 5: 글로벌 경제지표 로딩")
    print("=" * 60)
    load_global_economy_indicators()
    load_world_gdp()
    print("\n🎉 STEP 5 완료!")
```

---

## 🇰🇷 STEP 6: 한국(대구) 산업 프록시 데이터 로딩

> **Claude Code 프롬프트:**
> Kaggle에 대구 산업·고용 데이터가 직접 없으므로, Korean Demographics + Korea Income and Welfare 데이터에서 대구 경제활동인구, 고용률, 소득 데이터를 추출하여 MySQL에 적재해줘. 이것을 대구 산업 전환의 프록시 지표로 사용할 거야.

### 한국 데이터 한계 및 대안 전략

```
⚠️ Kaggle에 대구 시도별 산업·고용 데이터 직접 없음

대안 전략:
1. K2-1 Korean Demographics → 대구광역시 경제활동인구, 고용률 추출
2. K2-2 Korea Income and Welfare → 대구 지역 산업분류 소득 추출
3. 한국 전체 제조업→서비스업 전환 거시 트렌드 (economic_indicators)
4. 대구 아파트 가격 데이터(K1-1)를 산업단지 인근 가격 프록시로 활용
```

### 구현 사양

```python
# === scripts/subtopic4/step6_load_korean_proxy.py ===

import sys
import os
import glob
sys.path.append('scripts/subtopic4')
from step0_setup import *


def load_korean_demographics():
    """
    K2-1: Korean Demographics 2000-2022
    대구광역시의 인구·경제활동 데이터 추출
    
    ⚠️ 실제 CSV 열 이름은 다운로드 후 확인 필요!
    가능한 열: 시도, 연도, 총인구, 경제활동인구, 고용률, 실업률 등
    인코딩: cp949 또는 euc-kr (한국 데이터)
    """
    base_dir = 'kaggle_data/korean_demographics/'
    csv_files = glob.glob(os.path.join(base_dir, '**/*.csv'), recursive=True)
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0
    
    for csv_path in csv_files:
        print(f"\n📄 처리: {os.path.basename(csv_path)}")
        
        # 인코딩 시도
        df = None
        for enc in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
            try:
                df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
                print(f"  인코딩: {enc}")
                break
            except:
                continue
        
        if df is None:
            print("  ⚠️ 읽기 실패")
            continue
        
        df.columns = df.columns.str.strip()
        print(f"  열: {list(df.columns)}")
        print(f"  행수: {len(df)}")
        print(f"  샘플:\n{df.head(2).to_string()}\n")
        
        # 대구 필터링 (실제 열 이름에 맞게 조정)
        # 가능한 지역 열: '시도', 'region', 'Region', '지역'
        region_col = None
        for rc in ['시도', 'region', 'Region', '지역', 'area', 'province']:
            if rc in df.columns:
                region_col = rc
                break
        
        if region_col:
            # '대구' 또는 '대구광역시' 필터
            mask = df[region_col].astype(str).str.contains('대구|Daegu', case=False, na=False)
            df_daegu = df[mask]
            print(f"  대구 데이터: {len(df_daegu)}행")
            
            if not df_daegu.empty:
                for _, row in df_daegu.iterrows():
                    # 실제 열 이름에 맞게 매핑
                    year_val = None
                    for yc in ['연도', 'year', 'Year', '년도']:
                        if yc in df.columns:
                            year_val = row.get(yc)
                            break
                    
                    sql = """INSERT INTO korean_demographics
                             (year, region, total_population, 
                              economic_activity_rate, employment_rate,
                              unemployment_rate, source_dataset)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                    
                    cursor.execute(sql, (
                        year_val, '대구',
                        row.get('총인구', row.get('total_population')),
                        row.get('경제활동참가율', row.get('economic_activity_rate')),
                        row.get('고용률', row.get('employment_rate')),
                        row.get('실업률', row.get('unemployment_rate')),
                        os.path.basename(csv_path)
                    ))
                    total += 1
    
    conn.commit()
    conn.close()
    print(f"\n✅ 한국 인구통계(대구) 로딩 완료 ({total}행)")


def load_korea_income():
    """
    K2-2: Korea Income and Welfare
    대구 지역 소득 데이터 추출 → 산업 전환 프록시
    """
    base_dir = 'kaggle_data/korea_income/'
    csv_files = glob.glob(os.path.join(base_dir, '**/*.csv'), recursive=True)
    
    if not csv_files:
        print(f"⚠️ {base_dir}에 CSV 없음")
        return
    
    for csv_path in csv_files:
        print(f"\n📄 탐색: {os.path.basename(csv_path)}")
        for enc in ['utf-8', 'cp949', 'euc-kr']:
            try:
                df = pd.read_csv(csv_path, encoding=enc, nrows=5)
                print(f"  인코딩: {enc}")
                print(f"  열: {list(df.columns)}")
                print(f"  샘플:\n{df.head(2).to_string()}\n")
                break
            except:
                continue
    
    print("ℹ️ 파일 구조 확인 후 로딩 로직을 구현하세요.")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 6: 한국(대구) 산업 프록시 데이터")
    print("=" * 60)
    load_korean_demographics()
    load_korea_income()
    print("\n🎉 STEP 6 완료!")
```

---

## 📈 STEP 7: 분석 쿼리 (SQL JOIN + Python 후처리)

> **Claude Code 프롬프트:**
> 소주제 4의 핵심 분석 쿼리 4개를 구현해줘. pymysql로 SQL 실행 후 pandas DataFrame으로 변환하고, industry_housing_impact 테이블에 분석 결과를 적재해줘.

### 분석 쿼리 목록

| # | 분석명 | 데이터 소스 | 핵심 JOIN |
|---|--------|-----------|----------|
| Q1 | 산업별 고용 변동 vs 신규건설 판매건수 상관 | us_industry_employment × us_metro_demand | year 기준 |
| Q2 | Charlotte 섬유→금융 전환기 시장온도+필요소득 추이 | us_metro_demand (Charlotte 필터) | 시계열 |
| Q3 | 4개 도시 산업전환 전후 시장 건전성 비교 | zillow_timeseries × us_metro_demand | region+date |
| Q4 | 대구 vs Charlotte 산업전환 타임라인 비교 | korean_demographics × us_metro_demand × economic_indicators | year |

### 구현 사양

```python
# === scripts/subtopic4/step7_analysis_queries.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *
from scipy import stats


def query_to_df(sql, params=None):
    """SQL 실행 → pandas DataFrame"""
    conn = get_connection(DB_NAME)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# =============================================
# Q1: 산업별 고용 변동 vs 신규건설 판매건수 상관분석
# =============================================

def analysis_q1_employment_vs_construction():
    """
    분석: 제조업 고용 감소 / 서비스업 고용 증가와
          신규건설 판매건수의 상관관계
    """
    print("\n" + "=" * 60)
    print("Q1: 산업별 고용 변동 vs 신규건설 판매건수")
    print("=" * 60)
    
    # 신규건설 판매건수 (연도별 집계)
    sql_construction = """
        SELECT 
            region_name,
            LEFT(year_month, 4) AS year,
            AVG(new_construction_sales) AS avg_new_construction,
            SUM(new_construction_sales) AS total_new_construction
        FROM us_metro_demand
        WHERE new_construction_sales IS NOT NULL
          AND region_name IN (
              'Dallas-Fort Worth-Arlington, TX',
              'Atlanta-Sandy Springs-Roswell, GA',
              'Phoenix-Mesa-Chandler, AZ',
              'Charlotte-Concord-Gastonia, NC-SC'
          )
        GROUP BY region_name, LEFT(year_month, 4)
        ORDER BY region_name, year
    """
    df_const = query_to_df(sql_construction)
    print(f"\n신규건설 데이터: {len(df_const)}행")
    print(df_const.head(10))
    
    # BLS 고용 데이터 (연도별 집계) — 전국 수준
    sql_employment = """
        SELECT 
            year,
            industry_name,
            AVG(employee_count) AS avg_employees
        FROM us_industry_employment
        WHERE industry_name IN ('Manufacturing', 'Financial Activities',
                                'Professional and Business Services', 'Information')
          AND year >= 2018
        GROUP BY year, industry_name
        ORDER BY year, industry_name
    """
    # ⚠️ 실제 BLS 데이터 구조에 따라 쿼리 수정 필요
    try:
        df_emp = query_to_df(sql_employment)
        print(f"\n고용 데이터: {len(df_emp)}행")
    except Exception as e:
        print(f"⚠️ 고용 쿼리 오류 (BLS 데이터 구조 확인 필요): {e}")
        df_emp = pd.DataFrame()
    
    # 상관분석
    if not df_emp.empty and not df_const.empty:
        # 연도별 JOIN
        df_merged = df_const.merge(df_emp, on='year', how='inner')
        
        # 산업별 상관계수 계산
        for industry in df_merged['industry_name'].unique():
            subset = df_merged[df_merged['industry_name'] == industry]
            if len(subset) >= 3:
                corr, pval = stats.pearsonr(
                    subset['avg_employees'], subset['avg_new_construction']
                )
                print(f"\n  {industry} vs 신규건설: r={corr:.3f}, p={pval:.4f}")
    
    return df_const


# =============================================
# Q2: Charlotte 섬유→금융 전환기 분석
# =============================================

def analysis_q2_charlotte_transition():
    """
    Charlotte의 산업전환에 따른 시장온도+필요소득+신규건설 추이
    """
    print("\n" + "=" * 60)
    print("Q2: Charlotte 산업전환기 시장 분석")
    print("=" * 60)
    
    sql = """
        SELECT 
            year_month,
            market_temp_index,
            income_needed,
            new_construction_sales,
            sales_count
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
          AND (market_temp_index IS NOT NULL
               OR income_needed IS NOT NULL
               OR new_construction_sales IS NOT NULL)
        ORDER BY year_month
    """
    df = query_to_df(sql)
    print(f"\nCharlotte 수급 데이터: {len(df)}행")
    
    if not df.empty:
        # 연도별 요약
        df['year'] = df['year_month'].str[:4].astype(int)
        summary = df.groupby('year').agg({
            'market_temp_index': 'mean',
            'income_needed': 'mean',
            'new_construction_sales': 'sum',
            'sales_count': 'sum',
        }).round(2)
        print(f"\n연도별 요약:\n{summary}")
    
    return df


# =============================================
# Q3: 4개 도시 시장 건전성 비교
# =============================================

def analysis_q3_market_health():
    """
    4개 도시의 가치상승비율, 손해판매비율, 가격인하비율 비교
    (zillow_timeseries State 데이터 활용)
    """
    print("\n" + "=" * 60)
    print("Q3: 4개 도시(주) 시장 건전성 비교")
    print("=" * 60)
    
    sql = """
        SELECT 
            region_name,
            YEAR(date) AS year,
            AVG(pct_homes_increasing) AS avg_pct_increasing,
            AVG(pct_homes_selling_for_loss) AS avg_pct_loss,
            AVG(pct_listings_price_reduction) AS avg_pct_reduction,
            AVG(zhvi_all) AS avg_zhvi
        FROM zillow_timeseries
        WHERE region_level = 'state'
          AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
          AND date >= '2000-01-01'
        GROUP BY region_name, YEAR(date)
        ORDER BY region_name, year
    """
    df = query_to_df(sql)
    print(f"\n시장 건전성 데이터: {len(df)}행")
    
    if not df.empty:
        # 최근 5년 요약
        recent = df[df['year'] >= 2020]
        pivot = recent.pivot_table(
            index='year',
            columns='region_name',
            values='avg_zhvi',
            aggfunc='mean'
        ).round(0)
        print(f"\n2020~최근 ZHVI 비교:\n{pivot}")
    
    return df


# =============================================
# Q4: 대구 vs Charlotte 비교
# =============================================

def analysis_q4_daegu_vs_charlotte():
    """
    대구의 경제활동 데이터 vs Charlotte의 부동산 수급 데이터 비교
    + 한국/미국 거시경제 제조업→서비스업 전환 비교
    """
    print("\n" + "=" * 60)
    print("Q4: 대구 vs Charlotte 산업전환 비교")
    print("=" * 60)
    
    # 대구 경제활동 데이터
    sql_daegu = """
        SELECT year, total_population, economic_activity_rate, 
               employment_rate, unemployment_rate
        FROM korean_demographics
        WHERE region LIKE '%대구%'
        ORDER BY year
    """
    try:
        df_daegu = query_to_df(sql_daegu)
        print(f"\n대구 인구통계: {len(df_daegu)}행")
        if not df_daegu.empty:
            print(df_daegu.tail(5))
    except:
        df_daegu = pd.DataFrame()
        print("⚠️ 대구 데이터 없음")
    
    # Charlotte 부동산 수급
    sql_charlotte = """
        SELECT 
            LEFT(year_month, 4) AS year,
            AVG(market_temp_index) AS avg_market_temp,
            AVG(income_needed) AS avg_income_needed,
            SUM(new_construction_sales) AS total_new_construction
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """
    df_charlotte = query_to_df(sql_charlotte)
    print(f"\nCharlotte 수급: {len(df_charlotte)}행")
    
    # 한국 vs 미국 거시경제 비교
    sql_macro = """
        SELECT country, year, 
               manufacturing_pct, services_pct, 
               gdp_growth_rate, unemployment_rate
        FROM economic_indicators
        WHERE country IN ('South Korea', 'United States')
          AND year >= 2000
        ORDER BY country, year
    """
    try:
        df_macro = query_to_df(sql_macro)
        print(f"\n거시경제 비교: {len(df_macro)}행")
    except:
        df_macro = pd.DataFrame()
    
    return df_daegu, df_charlotte, df_macro


# =============================================
# 분석 결과 → industry_housing_impact 적재
# =============================================

def save_impact_analysis():
    """분석 결과를 industry_housing_impact 테이블에 저장"""
    
    # Charlotte 연도별 수급 변화율 계산
    sql = """
        SELECT 
            LEFT(year_month, 4) AS year,
            AVG(market_temp_index) AS market_temp,
            AVG(income_needed) AS income_needed,
            SUM(new_construction_sales) AS new_con_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
          AND new_construction_sales IS NOT NULL
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """
    df = query_to_df(sql)
    
    if df.empty:
        print("⚠️ Charlotte 데이터 없음")
        return
    
    # 전년 대비 변화율 계산
    df['year'] = df['year'].astype(int)
    df['market_temp_change'] = df['market_temp'].diff()
    df['income_change'] = df['income_needed'].pct_change()
    df['construction_change'] = df['new_con_sales'].pct_change()
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        if pd.isna(row.get('market_temp_change')):
            continue
        sql = """INSERT INTO industry_housing_impact
                 (city_id, city_name, country, year,
                  dominant_industry, new_construction_sales,
                  new_construction_sales_change, market_temp_index,
                  market_temp_change, income_needed, income_needed_change,
                  source_dataset)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor.execute(sql, (
            5, 'Charlotte', 'USA', row['year'],
            'Finance/Tech Transition',
            row.get('new_con_sales'),
            row.get('construction_change'),
            row.get('market_temp'),
            row.get('market_temp_change'),
            row.get('income_needed'),
            row.get('income_change'),
            'zillow_housing_analysis'
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Charlotte 영향 분석 결과 저장 완료")


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 7: 소주제 4 분석 쿼리 실행")
    print("=" * 60)
    
    df_q1 = analysis_q1_employment_vs_construction()
    df_q2 = analysis_q2_charlotte_transition()
    df_q3 = analysis_q3_market_health()
    df_q4_daegu, df_q4_charlotte, df_q4_macro = analysis_q4_daegu_vs_charlotte()
    
    # 분석 결과 저장
    save_impact_analysis()
    
    print("\n🎉 STEP 7 분석 완료!")
```

---

## 📊 STEP 8: 시각화

> **Claude Code 프롬프트:**
> 소주제 4 분석 결과를 시각화해줘. matplotlib/seaborn으로 다음 5개 차트를 만들어줘: (1) 산업전환 타임라인, (2) Charlotte 전환기 대시보드, (3) 4도시 시장건전성 비교, (4) 대구 vs Charlotte 비교, (5) 예측 성장률

### 시각화 목록

| # | 차트명 | 차트 유형 | 데이터 |
|---|--------|----------|--------|
| V1 | 산업전환 타임라인: 고용변화+신규건설+필요소득 | 다축 복합 선형차트 | Q1 결과 |
| V2 | Charlotte 전환기: 시장온도+필요소득+신규건설 | 3축 대시보드 | Q2 결과 |
| V3 | 4개 주 시장건전성: 가치상승/손해판매/가격인하 비율 | 히트맵 + 선형차트 | Q3 결과 |
| V4 | 대구 vs Charlotte 비교: 경제활동률 vs 시장온도 | 이중축 비교 차트 | Q4 결과 |
| V5 | 4개 MSA 주택가치 예측 성장률 | 막대+선형 복합 | ZHVF 데이터 |

### 구현 사양

```python
# === scripts/subtopic4/step8_visualization.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *
from step7_analysis_queries import query_to_df
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# 한글 폰트 설정 (환경에 맞게 조정)
plt.rcParams['font.family'] = 'DejaVu Sans'  # 또는 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['figure.dpi'] = 150

OUTPUT_DIR = 'output/subtopic4/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 도시별 색상
CITY_COLORS = {
    'Dallas-Fort Worth-Arlington, TX': '#E74C3C',
    'Atlanta-Sandy Springs-Roswell, GA': '#3498DB',
    'Phoenix-Mesa-Chandler, AZ': '#F39C12',
    'Charlotte-Concord-Gastonia, NC-SC': '#2ECC71',
    'United States': '#95A5A6',
    'Texas': '#E74C3C',
    'Georgia': '#3498DB',
    'Arizona': '#F39C12',
    'North Carolina': '#2ECC71',
}


# =============================================
# V1: 산업전환 타임라인
# =============================================

def viz_v1_industry_timeline():
    """고용변화 + 신규건설 + 필요소득 동시 표시"""
    
    sql = """
        SELECT 
            region_name,
            LEFT(year_month, 4) AS year,
            AVG(new_construction_sales) AS avg_new_construction,
            AVG(income_needed) AS avg_income_needed,
            AVG(market_temp_index) AS avg_market_temp
        FROM us_metro_demand
        WHERE region_name IN (
            'Dallas-Fort Worth-Arlington, TX',
            'Atlanta-Sandy Springs-Roswell, GA',
            'Phoenix-Mesa-Chandler, AZ',
            'Charlotte-Concord-Gastonia, NC-SC'
        )
        GROUP BY region_name, LEFT(year_month, 4)
        HAVING avg_new_construction IS NOT NULL
        ORDER BY region_name, year
    """
    df = query_to_df(sql)
    
    if df.empty:
        print("⚠️ V1 데이터 없음")
        return
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 14), sharex=True)
    
    for metro in df['region_name'].unique():
        subset = df[df['region_name'] == metro]
        color = CITY_COLORS.get(metro, 'gray')
        label = metro.split(',')[0]  # 약칭
        
        axes[0].plot(subset['year'], subset['avg_new_construction'],
                     marker='o', color=color, label=label, linewidth=2)
        axes[1].plot(subset['year'], subset['avg_income_needed'],
                     marker='s', color=color, label=label, linewidth=2)
        axes[2].plot(subset['year'], subset['avg_market_temp'],
                     marker='^', color=color, label=label, linewidth=2)
    
    axes[0].set_title('New Construction Sales (Monthly Avg)', fontsize=13)
    axes[0].set_ylabel('Sales Count')
    axes[0].legend(loc='upper left')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].set_title('Income Needed to Buy Home (Annual, USD)', fontsize=13)
    axes[1].set_ylabel('USD / Year')
    axes[1].legend(loc='upper left')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].set_title('Market Temperature Index', fontsize=13)
    axes[2].set_ylabel('Index (50=Balanced)')
    axes[2].axhline(y=50, color='black', linestyle='--', alpha=0.5, label='Balanced')
    axes[2].legend(loc='upper left')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_xlabel('Year')
    
    fig.suptitle('Sub-topic 4: Industrial Transformation & Real Estate Impact\n'
                 '4 Metro Areas Comparison', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v1_industry_timeline.png', bbox_inches='tight')
    plt.close()
    print("✅ V1 저장 완료")


# =============================================
# V2: Charlotte 전환기 대시보드
# =============================================

def viz_v2_charlotte_dashboard():
    """Charlotte 시장온도 + 필요소득 + 신규건설 복합 차트"""
    
    sql = """
        SELECT year_month, market_temp_index, income_needed, new_construction_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
          AND (market_temp_index IS NOT NULL 
               OR income_needed IS NOT NULL)
        ORDER BY year_month
    """
    df = query_to_df(sql)
    
    if df.empty:
        print("⚠️ V2 데이터 없음")
        return
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # 시장온도 (좌축)
    mask_temp = df['market_temp_index'].notna()
    ax1.fill_between(df.loc[mask_temp, 'year_month'],
                     50, df.loc[mask_temp, 'market_temp_index'],
                     alpha=0.3, color='#2ECC71')
    ax1.plot(df.loc[mask_temp, 'year_month'],
             df.loc[mask_temp, 'market_temp_index'],
             color='#2ECC71', linewidth=2, label='Market Temp Index')
    ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Market Temp Index', color='#2ECC71', fontsize=12)
    ax1.set_xlabel('Year-Month')
    
    # 필요소득 (우축)
    ax2 = ax1.twinx()
    mask_income = df['income_needed'].notna()
    ax2.plot(df.loc[mask_income, 'year_month'],
             df.loc[mask_income, 'income_needed'],
             color='#E74C3C', linewidth=2, linestyle='--', label='Income Needed')
    ax2.set_ylabel('Income Needed (USD/Year)', color='#E74C3C', fontsize=12)
    
    # x축 간소화
    tick_positions = range(0, len(df), max(1, len(df)//12))
    ax1.set_xticks([df.iloc[i]['year_month'] for i in tick_positions if i < len(df)])
    plt.xticks(rotation=45, ha='right')
    
    ax1.set_title('Charlotte: Textile→Finance/Tech Transition Period\n'
                  'Market Temperature & Income Required',
                  fontsize=14, fontweight='bold')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v2_charlotte_dashboard.png', bbox_inches='tight')
    plt.close()
    print("✅ V2 저장 완료")


# =============================================
# V3: 4개 주 시장건전성 히트맵
# =============================================

def viz_v3_market_health_heatmap():
    """가치상승/손해판매/가격인하 비율 히트맵"""
    
    sql = """
        SELECT 
            region_name,
            YEAR(date) AS year,
            AVG(pct_homes_increasing) AS pct_increasing,
            AVG(pct_homes_selling_for_loss) AS pct_loss,
            AVG(pct_listings_price_reduction) AS pct_reduction
        FROM zillow_timeseries
        WHERE region_level = 'state'
          AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
          AND date >= '2005-01-01'
        GROUP BY region_name, YEAR(date)
        ORDER BY region_name, year
    """
    df = query_to_df(sql)
    
    if df.empty:
        print("⚠️ V3 데이터 없음")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    metrics = [
        ('pct_increasing', 'Homes Increasing in Value (%)', 'Greens'),
        ('pct_loss', 'Homes Selling for Loss (%)', 'Reds'),
        ('pct_reduction', 'Listings with Price Reduction (%)', 'Oranges'),
    ]
    
    for ax, (col, title, cmap) in zip(axes, metrics):
        pivot = df.pivot_table(index='year', columns='region_name',
                               values=col, aggfunc='mean')
        if not pivot.empty:
            sns.heatmap(pivot, ax=ax, cmap=cmap, annot=True, fmt='.2f',
                       linewidths=0.5, cbar_kws={'shrink': 0.8})
            ax.set_title(title, fontsize=11)
            ax.set_xlabel('')
    
    fig.suptitle('Market Health Indicators: TX vs GA vs AZ vs NC',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v3_market_health_heatmap.png', bbox_inches='tight')
    plt.close()
    print("✅ V3 저장 완료")


# =============================================
# V4: 대구 vs Charlotte 비교
# =============================================

def viz_v4_daegu_vs_charlotte():
    """대구 경제활동률 vs Charlotte 시장온도 이중 비교"""
    
    # 대구
    sql_daegu = """
        SELECT year, economic_activity_rate, employment_rate
        FROM korean_demographics
        WHERE region LIKE '%대구%'
        ORDER BY year
    """
    
    # Charlotte
    sql_charlotte = """
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """
    
    try:
        df_daegu = query_to_df(sql_daegu)
        df_charlotte = query_to_df(sql_charlotte)
    except:
        print("⚠️ V4 데이터 조회 실패")
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 대구 경제활동률
    if not df_daegu.empty:
        ax1.plot(df_daegu['year'], df_daegu['economic_activity_rate'],
                 color='#9B59B6', marker='o', linewidth=2, label='Daegu Economic Activity Rate')
        ax1.set_title('Daegu: Economic Activity Rate (Textile→Hightech Transition)',
                      fontsize=13)
        ax1.set_ylabel('Economic Activity Rate (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
    
    # Charlotte 시장온도
    if not df_charlotte.empty:
        ax2.plot(df_charlotte['year'], df_charlotte['market_temp'],
                 color='#2ECC71', marker='s', linewidth=2, label='Charlotte Market Temp')
        ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        ax2.set_title('Charlotte: Market Temperature (Textile→Finance Transition Complete)',
                      fontsize=13)
        ax2.set_ylabel('Market Temp Index')
        ax2.set_xlabel('Year')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    fig.suptitle('Daegu vs Charlotte: Industrial Transformation Comparison',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v4_daegu_vs_charlotte.png', bbox_inches='tight')
    plt.close()
    print("✅ V4 저장 완료")


# =============================================
# V5: 예측 성장률
# =============================================

def viz_v5_forecast_growth():
    """4개 MSA 주택가치 예측 성장률"""
    
    sql = """
        SELECT region_name, forecast_date, growth_rate
        FROM us_metro_zhvf_growth
        WHERE region_name != 'United States'
        ORDER BY region_name, forecast_date
    """
    df = query_to_df(sql)
    
    if df.empty:
        print("⚠️ V5 데이터 없음")
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for metro in df['region_name'].unique():
        subset = df[df['region_name'] == metro]
        color = CITY_COLORS.get(metro, 'gray')
        label = metro.split(',')[0]
        ax.plot(subset['forecast_date'], subset['growth_rate'],
                marker='o', color=color, label=label, linewidth=2)
    
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_title('ZHVF: Forecasted Home Value Growth Rate (%)\n'
                 '4 Metro Areas', fontsize=14, fontweight='bold')
    ax.set_ylabel('Growth Rate (%)')
    ax.set_xlabel('Forecast Date')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v5_forecast_growth.png', bbox_inches='tight')
    plt.close()
    print("✅ V5 저장 완료")


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 8: 소주제 4 시각화")
    print("=" * 60)
    
    viz_v1_industry_timeline()
    viz_v2_charlotte_dashboard()
    viz_v3_market_health_heatmap()
    viz_v4_daegu_vs_charlotte()
    viz_v5_forecast_growth()
    
    print(f"\n🎉 모든 차트 저장 완료: {OUTPUT_DIR}")
```

---

## 🚀 전체 실행 순서 요약

```bash
# 0. 패키지 설치
pip install pymysql pandas numpy matplotlib seaborn scipy openpyxl kaggle

# 1. Kaggle 데이터 다운로드
python scripts/subtopic4/step1_download_kaggle.py

# 2. MySQL 테이블 생성
python scripts/subtopic4/step2_create_tables.py

# 3. Zillow 부동산 데이터 로딩 (data/ 폴더)
python scripts/subtopic4/step3_load_us_zillow.py

# 4. BLS 고용 데이터 로딩 (⚠️ 파일 구조 확인 후 실행)
python scripts/subtopic4/step4_load_kaggle_bls.py

# 5. 글로벌 경제지표 로딩
python scripts/subtopic4/step5_load_kaggle_global.py

# 6. 한국(대구) 프록시 데이터 로딩
python scripts/subtopic4/step6_load_korean_proxy.py

# 7. 분석 쿼리 실행 + 결과 적재
python scripts/subtopic4/step7_analysis_queries.py

# 8. 시각화 생성
python scripts/subtopic4/step8_visualization.py
```

---

## ⚠️ Claude Code 사용 시 주의사항

### 1. Kaggle 데이터 구조 불확실성

BLS, Global Economy 등 Kaggle 데이터는 **다운로드 전까지 정확한 열 이름을 모릅니다.**
각 STEP에 `explore_*_files()` 탐색 함수를 포함했으니, Claude Code에게 다음과 같이 지시하세요:

```
먼저 explore_bls_files()를 실행해서 파일 구조를 확인하고,
그 결과를 기반으로 load_bls_employment() 함수의 파싱 로직을 수정해줘.
```

### 2. 대용량 파일 처리

| 파일 | 크기 | 전략 |
|------|------|------|
| Metro_time_series.csv | 56MB | MSA 코드 필터 (Crosswalk 필요) |
| State_time_series.csv | 4.7MB | TX/GA/AZ/NC 4개 주 필터 |
| 나머지 Wide 파일 | <5MB | TARGET_METROS 필터로 충분 |

### 3. us_metro_demand 테이블 설계 주의

현재 설계는 **각 지표를 별도 행으로 INSERT**합니다.
따라서 같은 (region_name, year_month)에 여러 행이 존재할 수 있습니다.
분석 시 다음과 같이 집계하세요:

```sql
SELECT year_month,
       MAX(market_temp_index) AS market_temp,
       MAX(income_needed) AS income_needed,
       MAX(new_construction_sales) AS new_construction,
       MAX(sales_count) AS sales_count
FROM us_metro_demand
WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
GROUP BY year_month
```

### 4. Claude Code 단계별 프롬프트 예시

```
[STEP 2] 
소주제 4 테이블을 생성해줘. 
DB: real_estate_comparison (172.30.1.47, wonho, 1111)
위 가이드의 step2_create_tables.py 코드를 실행해줘.

[STEP 3]
data/zillow_Housing/ 폴더에서 다음 4개 파일을 4개 MSA로 필터링해서 
us_metro_demand 테이블에 적재해줘:
- Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv → new_construction_sales
- Metro_new_homeowner_income_needed_...csv → income_needed  
- Metro_market_temp_index_uc_sfrcondo_month.csv → market_temp_index
- Metro_sales_count_now_uc_sfrcondo_month.csv → sales_count

[STEP 4]
kaggle_data/bls_employment/ 폴더의 파일 구조를 먼저 탐색하고,
산업별 고용 데이터를 us_industry_employment 테이블에 적재해줘.
제조업, 금융, IT, 전문서비스 산업을 구분해서 넣어줘.

[STEP 7]
Charlotte의 산업전환기(2018~2025) 시장온도, 필요소득, 신규건설 추이를 분석하고,
결과를 industry_housing_impact 테이블에 저장해줘.
4개 도시 비교 차트도 그려줘.
```

---

## 📑 산출물 체크리스트

| # | 산출물 | 파일 | 상태 |
|---|--------|------|------|
| T1 | us_industry_employment 테이블 | MySQL | ☐ |
| T2 | economic_indicators 테이블 | MySQL | ☐ |
| T3 | us_metro_demand 테이블 (4개 수급지표) | MySQL | ☐ |
| T4 | us_metro_zhvf_growth 테이블 | MySQL | ☐ |
| T5 | zillow_timeseries (state 레벨) | MySQL | ☐ |
| T6 | korean_demographics (대구) | MySQL | ☐ |
| T7 | industry_housing_impact (분석결과) | MySQL | ☐ |
| V1 | 산업전환 타임라인 차트 | PNG | ☐ |
| V2 | Charlotte 전환기 대시보드 | PNG | ☐ |
| V3 | 시장건전성 히트맵 | PNG | ☐ |
| V4 | 대구 vs Charlotte 비교 | PNG | ☐ |
| V5 | 예측 성장률 차트 | PNG | ☐ |
