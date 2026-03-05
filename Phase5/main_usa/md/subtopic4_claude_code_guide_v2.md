# 소주제 4: 산업 전환과 부동산 — Claude Code 구현 가이드 (v2)

## 🎯 Claude Code에게 전달할 프로젝트 컨텍스트

> 이 문서는 Claude Code에 복사·붙여넣기하여 소주제 4의 전체 파이프라인을 단계별로 구현하기 위한 가이드입니다.
> **v2 변경점:** 4축 비교 분석 프레임워크 + 대구 인구유지 발전전략 도출 파트 추가

---

## 📋 프로젝트 요약

| 항목 | 내용 |
|------|------|
| **프로젝트명** | 내륙 거점 도시의 부동산 시장 구조 비교: 대구 vs 미국 유사 도시 |
| **소주제 4** | 산업 전환과 부동산 (Industrial Transformation & Real Estate) |
| **분석 목표 A** | 전통 산업(섬유)→하이테크 전환이 부동산에 미치는 영향 분석 |
| **분석 목표 B (v2 신규)** | 4축 비교를 통해 대구가 인구를 유지하며 생존할 수 있는 발전 전략 도출 |

### 🏙️ 4축 비교 프레임워크

| 비교축 | 대구광역시 | 미국 유사 도시 | 주요 공통점 | 분석 핵심 질문 |
|--------|-----------|--------------|-----------|--------------|
| **종합** | 경상도 거점 대도시 | **Dallas** | 내륙 대도시, 보수적 성향, 무더운 여름 | Dallas는 어떻게 인구를 끌어들이는가? |
| **산업** | 자동차 부품, 에너지 | **Atlanta** | 자동차·배터리 허브, 교통 요충지 | Atlanta의 산업 다각화 전략은? |
| **기후** | 분지 지형, 폭염 | **Phoenix** | 미국 내 최고 수준 여름 기온 | Phoenix는 폭염에도 왜 인구가 증가하는가? |
| **변모** | 섬유→첨단 산업 | **Charlotte** | 섬유 역사, 에너지/금융 도시 변모 | Charlotte 전환 성공 요인을 대구에 적용 가능한가? |

### 🎯 최종 산출물: 대구 생존 전략 보고서

```
분석 흐름:
  [데이터 수집] → [4축 비교 분석] → [성공 요인 추출] → [대구 적용 가능성 평가] → [전략 제안]

  1. Dallas 비교   → 인구 유입 메커니즘 (주택 가격 경쟁력 + 기업 유치)
  2. Atlanta 비교  → 산업 허브화 전략 (교통 + 물류 + 제조업 고도화)
  3. Phoenix 비교  → 기후 핸디캡 극복 전략 (인프라 투자 + 생활비 경쟁력)
  4. Charlotte 비교 → 산업 전환 로드맵 (섬유→금융/하이테크 전환 타임라인)
  5. 종합 전략     → 4개 도시의 성공 요인을 대구 맥락에 맞게 통합
```

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
│   ├── realtor-data.zip.csv
│   ├── zillow_Housing/
│   │   ├── Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv
│   │   ├── Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   │   ├── Metro_market_temp_index_uc_sfrcondo_month.csv
│   │   ├── Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   │   ├── Metro_zori_uc_sfrcondomfr_sm_month.csv
│   │   ├── Metro_sales_count_now_uc_sfrcondo_month.csv
│   │   ├── Metro_invt_fs_uc_sfrcondo_sm_month.csv
│   │   └── Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   └── Zillow_Economics/
│       ├── Metro_time_series.csv
│       └── State_time_series.csv
├── kaggle_data/
│   ├── bls_employment/          # U4-1: BLS 고용
│   ├── global_economy/          # G4-1: 글로벌 경제지표
│   ├── macro_economic/          # G4-2: 거시경제
│   ├── world_gdp/               # G4-3: GDP
│   ├── korean_demographics/     # K2-1: 한국 인구통계
│   ├── korea_income/            # K2-2: 한국 소득복지
│   ├── world_population_growth/ # G2-1: 도시별 인구성장률 (v2 추가)
│   ├── daegu_apartment/         # K1-1: 대구 아파트 실거래 (v2 추가)
│   └── daily_temperature/       # C3-2: 도시별 기온 (v2 추가)
├── scripts/
│   └── subtopic4/
│       ├── step0_setup.py
│       ├── step1_download_kaggle.py
│       ├── step2_create_tables.py
│       ├── step3_load_us_zillow.py
│       ├── step4_load_kaggle_bls.py
│       ├── step5_load_kaggle_global.py
│       ├── step6_load_korean_proxy.py
│       ├── step7_analysis_core.py          # 기존 산업전환 분석
│       ├── step8_analysis_4axis.py         # ★ v2: 4축 비교 분석
│       ├── step9_daegu_strategy.py         # ★ v2: 대구 발전전략 도출
│       ├── step10_visualization_core.py    # 기존 차트
│       └── step11_visualization_4axis.py   # ★ v2: 4축 비교 차트
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

# 4개 MSA 정식 명칭
TARGET_METROS = [
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',
    'Phoenix-Mesa-Chandler, AZ',
    'Charlotte-Concord-Gastonia, NC-SC',
]

# 4축 비교 매핑 (v2 추가)
AXIS_MAP = {
    'comprehensive': {  # 종합
        'daegu': '대구', 'us_city': 'Dallas',
        'metro': 'Dallas-Fort Worth-Arlington, TX', 'state': 'Texas', 'state_abbr': 'TX',
        'label_kr': '종합 비교', 'label_en': 'Comprehensive',
        'common': '내륙 대도시, 보수적 성향, 무더운 여름',
    },
    'industry': {  # 산업
        'daegu': '대구', 'us_city': 'Atlanta',
        'metro': 'Atlanta-Sandy Springs-Roswell, GA', 'state': 'Georgia', 'state_abbr': 'GA',
        'label_kr': '산업 비교', 'label_en': 'Industry',
        'common': '자동차·배터리 허브, 교통 요충지',
    },
    'climate': {  # 기후
        'daegu': '대구', 'us_city': 'Phoenix',
        'metro': 'Phoenix-Mesa-Chandler, AZ', 'state': 'Arizona', 'state_abbr': 'AZ',
        'label_kr': '기후 비교', 'label_en': 'Climate',
        'common': '미국 내 최고 수준 여름 기온, 분지 지형',
    },
    'transformation': {  # 변모
        'daegu': '대구', 'us_city': 'Charlotte',
        'metro': 'Charlotte-Concord-Gastonia, NC-SC', 'state': 'North Carolina', 'state_abbr': 'NC',
        'label_kr': '산업 변모 비교', 'label_en': 'Transformation',
        'common': '섬유 산업 역사, 에너지/금융/첨단 도시로 변모',
    },
}

CITY_ID_MAP = {'Dallas': 2, 'Atlanta': 3, 'Phoenix': 4, 'Charlotte': 5}
STATE_MAP = {'Dallas': 'TX', 'Atlanta': 'GA', 'Phoenix': 'AZ', 'Charlotte': 'NC'}

# 도시별 시각화 색상
CITY_COLORS = {
    'Dallas': '#E74C3C',       'Texas': '#E74C3C',
    'Atlanta': '#3498DB',      'Georgia': '#3498DB',
    'Phoenix': '#F39C12',      'Arizona': '#F39C12',
    'Charlotte': '#2ECC71',    'North Carolina': '#2ECC71',
    '대구': '#9B59B6',         'Daegu': '#9B59B6',
    'United States': '#95A5A6',
    # MSA 정식 명칭
    'Dallas-Fort Worth-Arlington, TX': '#E74C3C',
    'Atlanta-Sandy Springs-Roswell, GA': '#3498DB',
    'Phoenix-Mesa-Chandler, AZ': '#F39C12',
    'Charlotte-Concord-Gastonia, NC-SC': '#2ECC71',
}


def get_connection(db_name=None):
    config = DB_CONFIG.copy()
    if db_name:
        config['db'] = db_name
    return pymysql.connect(**config)


def query_to_df(sql, params=None):
    conn = get_connection(DB_NAME)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


def load_csv_to_mysql(csv_path, table_name, db_name=DB_NAME,
                      encoding='utf-8', chunksize=5000):
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
    if target_metros is None:
        target_metros = TARGET_METROS
    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    if 'BaseDate' in df.columns:
        id_cols.append('BaseDate')
    date_cols = [c for c in df.columns if c not in id_cols]
    filter_names = target_metros + ['United States']
    df_f = df[df['RegionName'].isin(filter_names)].copy()
    if df_f.empty:
        print(f"⚠️ 타겟 MSA 없음: {csv_path}")
        return 0
    df_long = df_f.melt(
        id_vars=[c for c in id_cols if c in df_f.columns],
        value_vars=date_cols, var_name='year_month', value_name=value_col_name
    ).dropna(subset=[value_col_name])
    df_long['year_month'] = df_long['year_month'].str[:7]
    conn = get_connection(db_name)
    cursor = conn.cursor()
    sql = f"""INSERT INTO `{table_name}`
              (region_id, region_name, state_name, year_month, `{value_col_name}`)
              VALUES (%s, %s, %s, %s, %s)"""
    data = [(row.get('RegionID'), row['RegionName'], row.get('StateName'),
             row['year_month'], row[value_col_name]) for _, row in df_long.iterrows()]
    cursor.executemany(sql, data)
    conn.commit()
    conn.close()
    print(f"✅ Wide→Long 완료: {os.path.basename(csv_path)} → {table_name} ({len(data)}행)")
    return len(data)
```

---

## 🗄️ STEP 1: Kaggle 데이터 다운로드

> **Claude Code 프롬프트:**
> 소주제 4에 필요한 Kaggle 데이터셋을 다운로드하는 스크립트를 만들어줘. v2에서 4축 비교 분석용 데이터셋이 추가되었어.

### 다운로드 대상 (v1: 7개 + v2 추가: 3개 = 10개)

| 코드 | Kaggle ID | 용도 | v2 추가 |
|------|-----------|------|---------|
| U4-1 | `bls/employment` | ⭐ 미국 산업별 고용 | |
| U4-2 | `bls/bls` | BLS 종합 | |
| G4-1 | `prasad22/global-economy-indicators` | ⭐ 글로벌 경제지표 | |
| G4-2 | `veselagencheva/macro-economic-indicators-dataset-country-level` | 거시경제 | |
| G4-3 | `sazidthe1/world-gdp-data` | GDP | |
| K2-1 | `alexandrepetit881234/korean-demographics-20002022` | ⭐ 한국 인구통계 | |
| K2-2 | `hongsean/korea-income-and-welfare` | 한국 소득복지 | |
| G2-1 | `dataanalyst001/world-population-growth-rate-by-cities-2024` | ⭐ 도시별 인구성장률 비교 | ✅ |
| K1-1 | `lnoahl/daegu-aptmernt-actual-transaction` | ⭐ 대구 아파트 실거래 | ✅ |
| C3-2 | `sudalairajkumar/daily-temperature-of-major-cities` | ⭐ 도시별 기온 (기후축) | ✅ |

```python
# === scripts/subtopic4/step1_download_kaggle.py ===
import os, zipfile

KAGGLE_DATASETS = {
    # 기존 (v1)
    'bls/employment':           'kaggle_data/bls_employment',
    'bls/bls':                  'kaggle_data/bls_bls',
    'prasad22/global-economy-indicators': 'kaggle_data/global_economy',
    'veselagencheva/macro-economic-indicators-dataset-country-level': 'kaggle_data/macro_economic',
    'sazidthe1/world-gdp-data': 'kaggle_data/world_gdp',
    'alexandrepetit881234/korean-demographics-20002022': 'kaggle_data/korean_demographics',
    'hongsean/korea-income-and-welfare': 'kaggle_data/korea_income',
    # v2 추가 (4축 비교용)
    'dataanalyst001/world-population-growth-rate-by-cities-2024': 'kaggle_data/world_population_growth',
    'lnoahl/daegu-aptmernt-actual-transaction': 'kaggle_data/daegu_apartment',
    'sudalairajkumar/daily-temperature-of-major-cities': 'kaggle_data/daily_temperature',
}

def download_all():
    for dataset_id, save_dir in KAGGLE_DATASETS.items():
        os.makedirs(save_dir, exist_ok=True)
        cmd = f'kaggle datasets download -d {dataset_id} -p {save_dir} --unzip'
        print(f"📥 다운로드 중: {dataset_id}")
        os.system(cmd)
        for f in os.listdir(save_dir):
            if f.endswith('.zip'):
                with zipfile.ZipFile(os.path.join(save_dir, f), 'r') as z:
                    z.extractall(save_dir)
    print("✅ 모든 Kaggle 데이터셋 다운로드 완료")

if __name__ == '__main__':
    download_all()
```

---

## 🗄️ STEP 2: 테이블 생성 (v2 확장)

> **Claude Code 프롬프트:**
> 소주제 4 테이블을 생성해줘. v2에서 4축 비교 분석용 테이블 3개가 추가되었어. DB: real_estate_comparison, 172.30.1.47, wonho, 1111

### 테이블 목록 (v1: 7개 + v2 추가: 3개 = 10개)

| 테이블명 | 용도 | v2 |
|----------|------|----|
| `us_industry_employment` | 미국 산업별 고용 | |
| `economic_indicators` | 글로벌 경제지표 | |
| `us_metro_demand` | MSA 수급지표 | |
| `us_metro_zhvf_growth` | MSA 예측 성장률 | |
| `industry_housing_impact` | 산업-부동산 영향 분석 | |
| `zillow_timeseries` | Zillow 종합 시계열 | |
| `korean_demographics` | 한국 인구통계 | |
| `city_comparison_population` | ⭐ 도시별 인구성장률 비교 | ✅ |
| `daegu_housing_prices` | ⭐ 대구 아파트 실거래 | ✅ |
| `city_axis_scorecard` | ⭐ 4축 비교 종합 스코어카드 | ✅ |

```python
# === scripts/subtopic4/step2_create_tables.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import get_connection, DB_NAME

TABLES_SQL = [
    # ==================== 기존 (v1) ====================

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

    # ----- MSA 수급지표 -----
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

    # ----- 산업-부동산 영향 분석 결과 -----
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

    # ----- Zillow 종합 시계열 -----
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

    # ----- 한국 인구통계 -----
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

    # ==================== v2 추가 ====================

    # ----- ⭐ 도시별 인구성장률 비교 (대구+미국4도시) -----
    """
    CREATE TABLE IF NOT EXISTS city_comparison_population (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_name VARCHAR(100),
        country VARCHAR(50),
        comparison_axis VARCHAR(30) COMMENT '종합/산업/기후/변모',
        year INT,
        population BIGINT,
        population_growth_rate DECIMAL(8,4),
        net_migration BIGINT COMMENT '순이동 (양수=유입, 음수=유출)',
        median_age DECIMAL(5,2),
        source_dataset VARCHAR(100),
        INDEX idx_city_year (city_name, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- ⭐ 대구 아파트 실거래 -----
    """
    CREATE TABLE IF NOT EXISTS daegu_housing_prices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year_month VARCHAR(7),
        year INT,
        district VARCHAR(30) COMMENT '구/군 (수성구, 달서구 등)',
        apt_name VARCHAR(100),
        exclusive_area DECIMAL(10,2) COMMENT '전용면적 (㎡)',
        deal_amount BIGINT COMMENT '거래금액 (만원)',
        floor INT,
        build_year INT,
        jibun VARCHAR(50),
        source_dataset VARCHAR(100),
        INDEX idx_district_year (district, year),
        INDEX idx_year_month (year_month)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ----- ⭐ 4축 비교 종합 스코어카드 (분석 산출물) -----
    """
    CREATE TABLE IF NOT EXISTS city_axis_scorecard (
        id INT AUTO_INCREMENT PRIMARY KEY,
        comparison_axis VARCHAR(30) COMMENT '종합/산업/기후/변모',
        daegu_metric_name VARCHAR(100),
        daegu_value DECIMAL(15,4),
        us_city_name VARCHAR(50),
        us_metric_name VARCHAR(100),
        us_value DECIMAL(15,4),
        metric_category VARCHAR(50) COMMENT '인구/주택가격/고용/기후/소득 등',
        year_or_period VARCHAR(20),
        gap_ratio DECIMAL(8,4) COMMENT '대구/미국 비율 (1.0=동일)',
        insight TEXT COMMENT '비교 인사이트',
        strategy_implication TEXT COMMENT '대구 전략 시사점',
        INDEX idx_axis (comparison_axis),
        INDEX idx_category (metric_category)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
]


def create_subtopic4_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for sql in TABLES_SQL:
        try:
            cursor.execute(sql)
            tbl = sql.split('EXISTS')[1].split('(')[0].strip()
            print(f"  ✅ {tbl}")
        except Exception as e:
            print(f"  ⚠️ 오류: {e}")
    conn.commit()
    conn.close()
    print("\n✅ 소주제 4 테이블 생성 완료 (v2: 10개)")


if __name__ == '__main__':
    create_subtopic4_tables()
```

---

## 📊 STEP 3: 미국 Zillow 부동산 데이터 로딩

> **Claude Code 프롬프트:**
> data/ 폴더의 Zillow 데이터에서 소주제 4에 필요한 지표를 추출하여 MySQL에 적재해줘. v2에서 ZHVI, ZORI, 재고량도 추가 로딩하여 4축 비교에 활용할 거야.

### 로딩 파일 (v1 + v2 확장)

| 파일 | 테이블 | 컬럼명 | v2 |
|------|--------|--------|----|
| `Metro_new_con_sales_count_...csv` | `us_metro_demand` | `new_construction_sales` | |
| `Metro_new_homeowner_income_needed_...csv` | `us_metro_demand` | `income_needed` | |
| `Metro_market_temp_index_...csv` | `us_metro_demand` | `market_temp_index` | |
| `Metro_sales_count_now_...csv` | `us_metro_demand` | `sales_count` | |
| `Metro_invt_fs_...csv` | `us_metro_demand` | `inventory_count` | ✅ |
| `Metro_zhvi_...csv` | `us_metro_zhvi` | `zhvi` | ✅ |
| `Metro_zori_...csv` | `us_metro_zori` | `zori` | ✅ |
| `Metro_zhvf_growth_...csv` | `us_metro_zhvf_growth` | `growth_rate` | |
| `State_time_series.csv` | `zillow_timeseries` | 종합 | |

```python
# === scripts/subtopic4/step3_load_us_zillow.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *


def load_demand_indicator(csv_path, col_name):
    """Wide CSV → 4개 MSA 필터 → Long → us_metro_demand 적재"""
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
        value_vars=date_cols, var_name='year_month', value_name=col_name
    ).dropna(subset=[col_name])
    df_long['year_month'] = df_long['year_month'].str[:7]
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = f"""INSERT INTO us_metro_demand
              (region_id, region_name, state_name, year_month, `{col_name}`)
              VALUES (%s, %s, %s, %s, %s)"""
    data = [(row.get('RegionID'), row['RegionName'], row.get('StateName'),
             row['year_month'], row[col_name]) for _, row in df_long.iterrows()]
    cursor.executemany(sql, data)
    conn.commit()
    conn.close()
    print(f"✅ {col_name}: {len(data)}행 → us_metro_demand")


def load_zhvf_growth():
    csv_path = f'{ZILLOW_HOUSING_DIR}Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
    df = pd.read_csv(csv_path)
    filter_names = TARGET_METROS + ['United States']
    df_f = df[df['RegionName'].isin(filter_names)].copy()
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    date_cols = [c for c in df_f.columns if c not in id_cols]
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    rows = 0
    for _, rr in df_f.iterrows():
        for dc in date_cols:
            val = rr[dc]
            if pd.notna(val):
                cursor.execute(
                    """INSERT INTO us_metro_zhvf_growth
                       (region_id, region_name, state_name, base_date, forecast_date, growth_rate)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (rr.get('RegionID'), rr['RegionName'], rr.get('StateName'),
                     rr.get('BaseDate'), dc, val))
                rows += 1
    conn.commit()
    conn.close()
    print(f"✅ ZHVF 성장률: {rows}행")


def load_state_timeseries():
    csv_path = f'{ZILLOW_ECONOMICS_DIR}State_time_series.csv'
    target_states = ['Texas', 'Georgia', 'Arizona', 'North Carolina']
    selected_cols = [
        'ZHVI_AllHomes', 'ZHVIPerSqft_AllHomes',
        'ZRI_AllHomes', 'MedianListingPrice_AllHomes',
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
        cursor.execute(
            """INSERT INTO zillow_timeseries
               (date, region_name, region_level,
                zhvi_all, zhvi_per_sqft, zri_all, median_listing_price,
                pct_homes_increasing, pct_homes_decreasing,
                pct_homes_selling_for_loss, pct_listings_price_reduction,
                median_pct_price_reduction, sale_counts, sale_counts_seas_adj,
                source_file)
               VALUES (%s,%s,'state',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (row.get('Date'), row['RegionName'],
             row.get('ZHVI_AllHomes'), row.get('ZHVIPerSqft_AllHomes'),
             row.get('ZRI_AllHomes'), row.get('MedianListingPrice_AllHomes'),
             row.get('PctOfHomesIncreasingInValues_AllHomes'),
             row.get('PctOfHomesDecreasingInValues_AllHomes'),
             row.get('PctOfHomesSellingForLoss_AllHomes'),
             row.get('PctOfListingsWithPriceReductions_AllHomes'),
             row.get('MedianPctOfPriceReduction_AllHomes'),
             row.get('Sale_Counts'), row.get('Sale_Counts_Seas_Adj'),
             'State_time_series.csv'))
        rows += 1
    conn.commit()
    conn.close()
    print(f"✅ State 시계열: {rows}행")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 3: Zillow 부동산 데이터 로딩")
    print("=" * 60)

    # 수급 지표
    demand_files = [
        ('Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv', 'new_construction_sales'),
        ('Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv', 'income_needed'),
        ('Metro_market_temp_index_uc_sfrcondo_month.csv', 'market_temp_index'),
        ('Metro_sales_count_now_uc_sfrcondo_month.csv', 'sales_count'),
        ('Metro_invt_fs_uc_sfrcondo_sm_month.csv', 'inventory_count'),  # v2 추가
    ]
    for fname, col in demand_files:
        load_demand_indicator(f'{ZILLOW_HOUSING_DIR}{fname}', col)

    # ZHVI / ZORI (v2: 4축 비교용)
    load_zillow_wide_to_long(
        f'{ZILLOW_HOUSING_DIR}Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
        'us_metro_zhvi', 'zhvi')
    load_zillow_wide_to_long(
        f'{ZILLOW_HOUSING_DIR}Metro_zori_uc_sfrcondomfr_sm_month.csv',
        'us_metro_zori', 'zori')

    load_zhvf_growth()
    load_state_timeseries()
    print("\n🎉 STEP 3 완료!")
```

---

## 📊 STEP 4~6: Kaggle 데이터 로딩 (BLS, 글로벌, 한국)

> STEP 4 (BLS), 5 (글로벌 경제), 6 (한국 프록시) 코드는 v1과 동일합니다.
> 단, **v2에서 대구 아파트 실거래 + 도시 인구성장률 + 기온 데이터** 로딩이 추가됩니다.

### STEP 6 v2 추가분: 대구 아파트 + 인구성장률 + 기온

> **Claude Code 프롬프트:**
> v2 추가 데이터를 로딩해줘:
> 1) kaggle_data/daegu_apartment/ → daegu_housing_prices 테이블
> 2) kaggle_data/world_population_growth/ → city_comparison_population 테이블 (대구, Dallas, Atlanta, Phoenix, Charlotte 필터)
> 3) kaggle_data/daily_temperature/ → 5개 도시 기온 데이터 (기후축 비교용, 메모리에서 분석)

```python
# === scripts/subtopic4/step6b_load_v2_data.py ===

import sys, os, glob
sys.path.append('scripts/subtopic4')
from step0_setup import *


def load_daegu_apartment():
    """K1-1: 대구 아파트 실거래 데이터 → daegu_housing_prices"""
    base_dir = 'kaggle_data/daegu_apartment/'
    csv_files = glob.glob(os.path.join(base_dir, '**/*.csv'), recursive=True)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for csv_path in csv_files:
        print(f"\n📄 처리: {os.path.basename(csv_path)}")
        for enc in ['utf-8', 'cp949', 'euc-kr']:
            try:
                df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
                break
            except:
                continue
        else:
            continue

        df.columns = df.columns.str.strip()
        print(f"  열: {list(df.columns)}")
        print(f"  행수: {len(df):,}")

        # ⚠️ 실제 열 이름에 맞게 아래 매핑 수정 필요
        # 일반적인 한국 실거래가 데이터 열: 시군구, 법정동, 아파트, 전용면적, 거래금액, 층, 건축년도, 년, 월
        for _, row in df.iterrows():
            year_val = row.get('년', row.get('year', row.get('거래년도')))
            month_val = row.get('월', row.get('month', row.get('거래월')))
            if year_val and month_val:
                ym = f"{int(year_val)}-{int(month_val):02d}"
            else:
                ym = None

            district = row.get('시군구', row.get('district', row.get('구')))
            # "대구광역시 수성구" → "수성구"
            if district and '대구' in str(district):
                parts = str(district).split()
                district = parts[-1] if len(parts) > 1 else district

            sql = """INSERT INTO daegu_housing_prices
                     (year_month, year, district, apt_name, exclusive_area,
                      deal_amount, floor, build_year, source_dataset)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql, (
                ym, year_val, district,
                row.get('아파트', row.get('apt_name', row.get('단지명'))),
                row.get('전용면적', row.get('exclusive_area')),
                row.get('거래금액', row.get('deal_amount')),
                row.get('층', row.get('floor')),
                row.get('건축년도', row.get('build_year')),
                os.path.basename(csv_path)
            ))
            total += 1
            if total % 5000 == 0:
                conn.commit()
                print(f"  ... {total:,}행")

    conn.commit()
    conn.close()
    print(f"\n✅ 대구 아파트 실거래: {total:,}행")


def load_world_population_growth():
    """G2-1: 도시별 인구성장률 → city_comparison_population"""
    base_dir = 'kaggle_data/world_population_growth/'
    csv_files = glob.glob(os.path.join(base_dir, '**/*.csv'), recursive=True)

    # 5개 도시 검색 키워드
    target_keywords = {
        'Daegu': ('대구', 'comprehensive'),
        'Dallas': ('Dallas', 'comprehensive'),
        'Atlanta': ('Atlanta', 'industry'),
        'Phoenix': ('Phoenix', 'climate'),
        'Charlotte': ('Charlotte', 'transformation'),
    }

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for csv_path in csv_files:
        df = pd.read_csv(csv_path, low_memory=False)
        df.columns = df.columns.str.strip()
        print(f"📄 {os.path.basename(csv_path)} — 열: {list(df.columns)[:8]}")

        # 도시명 열 찾기
        city_col = None
        for cc in ['City', 'city', 'city_name', 'Name', 'name']:
            if cc in df.columns:
                city_col = cc
                break
        if not city_col:
            continue

        for city_key, (search_term, axis) in target_keywords.items():
            mask = df[city_col].astype(str).str.contains(search_term, case=False, na=False)
            city_rows = df[mask]
            if not city_rows.empty:
                print(f"  ✅ {city_key}: {len(city_rows)}행")
                for _, row in city_rows.iterrows():
                    sql = """INSERT INTO city_comparison_population
                             (city_name, country, comparison_axis, population,
                              population_growth_rate, source_dataset)
                             VALUES (%s,%s,%s,%s,%s,%s)"""
                    cursor.execute(sql, (
                        city_key,
                        row.get('Country', row.get('country', '')),
                        axis,
                        row.get('Population', row.get('population_2024', row.get('population'))),
                        row.get('Growth Rate', row.get('growth_rate')),
                        os.path.basename(csv_path)
                    ))
                    total += 1

    conn.commit()
    conn.close()
    print(f"\n✅ 도시별 인구성장률: {total}행")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 6b: v2 추가 데이터 로딩")
    print("=" * 60)
    load_daegu_apartment()
    load_world_population_growth()
    print("\n🎉 STEP 6b 완료!")
```

---

## 📈 STEP 7: 기존 산업전환 분석 (v1 유지)

> v1의 Q1~Q4 분석은 그대로 유지합니다. (BLS 고용 vs 신규건설, Charlotte 전환기, 시장건전성, 대구 vs Charlotte)
> 코드는 v1 가이드의 step7_analysis_queries.py와 동일합니다.

---

## ⭐ STEP 8: 4축 비교 분석 (v2 신규)

> **Claude Code 프롬프트:**
> 4축(종합/산업/기후/변모) 프레임워크로 대구와 4개 미국 도시를 비교 분석해줘. 각 축마다 핵심 지표를 비교하고, 대구가 미국 도시에서 배울 수 있는 인구유지 전략을 도출해줘. 결과는 city_axis_scorecard 테이블에 저장해줘.

### 4축별 분석 설계

```
축 1 — 종합 (대구 vs Dallas)
  ├─ 인구성장률 비교 (대구 유출 vs Dallas 유입)
  ├─ 주택가격 경쟁력 비교 (ZHVI vs 대구 아파트 평균가)
  ├─ 주택구매 필요소득 비교
  └─ 인사이트: Dallas의 "저렴한 주택 + 기업 유치" 모델

축 2 — 산업 (대구 vs Atlanta)
  ├─ 산업 구조 비교 (제조업 비중 vs 서비스업 비중)
  ├─ 신규건설 판매건수 (산업 투자 활성화 지표)
  ├─ 시장온도지수 변화
  └─ 인사이트: Atlanta의 "교통 허브 + 산업 다각화" 모델

축 3 — 기후 (대구 vs Phoenix)
  ├─ 여름 평균기온 / 폭염일수 비교
  ├─ 기온 핸디캡에도 인구 증가하는 Phoenix의 비결
  ├─ 주택가격 대비 소득 비율 비교
  └─ 인사이트: Phoenix의 "생활비 경쟁력 + 인프라 투자" 모델

축 4 — 변모 (대구 vs Charlotte)
  ├─ 산업 전환 타임라인 비교 (섬유→금융/하이테크)
  ├─ 전환기 전후 부동산 지표 변화
  ├─ 고용 구조 변화 vs 주택 수요 변화
  └─ 인사이트: Charlotte 전환 성공 요인 → 대구 적용
```

### 구현 사양

```python
# === scripts/subtopic4/step8_analysis_4axis.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *
from scipy import stats

# =============================================
# 축 1: 종합 비교 — 대구 vs Dallas
# =============================================

def axis1_comprehensive_daegu_vs_dallas():
    """
    핵심 질문: Dallas는 어떻게 인구를 끌어들이는가?
    비교 지표: 인구성장률, 주택가격, 주택구매 필요소득, 시장온도
    """
    print("\n" + "=" * 70)
    print("축 1: 종합 비교 — 대구 vs Dallas")
    print("=" * 70)

    results = []

    # --- 1-1. 대구 인구 추이 ---
    df_daegu_pop = query_to_df("""
        SELECT year, total_population, population_change_rate,
               economic_activity_rate
        FROM korean_demographics
        WHERE region LIKE '%대구%'
        ORDER BY year
    """)
    if not df_daegu_pop.empty:
        latest = df_daegu_pop.iloc[-1]
        print(f"\n  대구 최근 인구: {latest.get('total_population'):,.0f}")
        print(f"  대구 인구변화율: {latest.get('population_change_rate')}%")

    # --- 1-2. Dallas 부동산 지표 ---
    df_dallas = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Dallas-Fort Worth-Arlington, TX'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # --- 1-3. Dallas ZHVI (주택가격) ---
    df_dallas_zhvi = query_to_df("""
        SELECT LEFT(year_month, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = 'Dallas-Fort Worth-Arlington, TX'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # --- 1-4. 대구 아파트 평균가 ---
    df_daegu_price = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price_manwon,
               COUNT(*) AS transaction_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    """)

    # --- 스코어카드 생성 ---
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 주택가격 비교 (가장 최근 연도)
    if not df_dallas_zhvi.empty and not df_daegu_price.empty:
        dallas_price_usd = df_dallas_zhvi.iloc[-1]['avg_zhvi']
        daegu_price_manwon = df_daegu_price.iloc[-1]['avg_price_manwon']
        daegu_price_usd = daegu_price_manwon * 10000 / 1350  # 원→달러 환산 (환율 1350원 기준)

        cursor.execute("""
            INSERT INTO city_axis_scorecard
            (comparison_axis, daegu_metric_name, daegu_value,
             us_city_name, us_metric_name, us_value,
             metric_category, year_or_period, gap_ratio, insight, strategy_implication)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            ('종합', '대구 아파트 평균가(USD 환산)', round(daegu_price_usd, 2),
             'Dallas', 'Dallas ZHVI 평균', round(dallas_price_usd, 2),
             '주택가격', str(df_dallas_zhvi.iloc[-1]['year']),
             round(daegu_price_usd / dallas_price_usd, 4) if dallas_price_usd else None,
             f'대구 아파트 평균가는 Dallas ZHVI의 약 {daegu_price_usd/dallas_price_usd*100:.0f}% 수준'
                if dallas_price_usd else '',
             'Dallas의 주택 가격 경쟁력이 기업 유치와 인구 유입의 핵심 동력. '
             '대구도 수도권 대비 주택 가격 경쟁력을 적극 마케팅해야 함'))

    # 인구 트렌드 비교
    if not df_daegu_pop.empty:
        daegu_growth = df_daegu_pop.iloc[-1].get('population_change_rate', 0)
        cursor.execute("""
            INSERT INTO city_axis_scorecard
            (comparison_axis, daegu_metric_name, daegu_value,
             us_city_name, us_metric_name, us_value,
             metric_category, year_or_period, insight, strategy_implication)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            ('종합', '대구 인구변화율(%)', daegu_growth,
             'Dallas', 'Dallas MSA 인구성장률(%)', None,  # 별도 데이터로 채움
             '인구', str(df_daegu_pop.iloc[-1].get('year', '')),
             '대구는 인구 유출 추세, Dallas는 지속적 인구 유입',
             'Dallas 모델: ①법인세 없는 TX주 세제 혜택 ②풍부한 토지+저렴한 주택 '
             '③대기업 본사 유치(Toyota, AT&T) → 대구 적용: 혁신도시 확장 + 기업 인센티브 강화'))

    conn.commit()
    conn.close()
    print("  ✅ 축 1 스코어카드 저장 완료")
    return df_daegu_pop, df_dallas, df_dallas_zhvi, df_daegu_price


# =============================================
# 축 2: 산업 비교 — 대구 vs Atlanta
# =============================================

def axis2_industry_daegu_vs_atlanta():
    """
    핵심 질문: Atlanta의 산업 다각화 전략은?
    비교 지표: 산업구조, 신규건설, 시장온도, 교통인프라 영향
    """
    print("\n" + "=" * 70)
    print("축 2: 산업 비교 — 대구 vs Atlanta")
    print("=" * 70)

    # Atlanta 부동산 수급
    df_atlanta = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(new_construction_sales) AS total_new_construction,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Atlanta-Sandy Springs-Roswell, GA'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # 한국 vs 미국 제조업 비중 비교
    df_mfg = query_to_df("""
        SELECT country, year, manufacturing_pct, services_pct, industry_pct
        FROM economic_indicators
        WHERE country IN ('South Korea', 'United States')
          AND year >= 2000
        ORDER BY country, year
    """)

    # 스코어카드
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    if not df_mfg.empty:
        kr_latest = df_mfg[df_mfg['country'] == 'South Korea'].iloc[-1] if len(df_mfg[df_mfg['country'] == 'South Korea']) > 0 else None
        us_latest = df_mfg[df_mfg['country'] == 'United States'].iloc[-1] if len(df_mfg[df_mfg['country'] == 'United States']) > 0 else None

        if kr_latest is not None and us_latest is not None:
            cursor.execute("""
                INSERT INTO city_axis_scorecard
                (comparison_axis, daegu_metric_name, daegu_value,
                 us_city_name, us_metric_name, us_value,
                 metric_category, year_or_period, insight, strategy_implication)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                ('산업', '한국 제조업 비중(%)', kr_latest.get('manufacturing_pct'),
                 'Atlanta', '미국 제조업 비중(%)', us_latest.get('manufacturing_pct'),
                 '산업구조', str(kr_latest.get('year', '')),
                 '한국은 미국 대비 제조업 비중이 여전히 높음 → 대구 제조업 의존도는 더 높을 가능성',
                 'Atlanta 모델: ①세계 최대 공항(하츠필드) 활용한 물류 허브 '
                 '②자동차(현대, 기아) + 영화/미디어(스튜디오) 산업 유치 '
                 '③Georgia Tech 산학협력 → 대구 적용: 대구공항 확장 + 자동차부품 고도화 + 대학 연계'))

    conn.commit()
    conn.close()
    print("  ✅ 축 2 스코어카드 저장 완료")
    return df_atlanta, df_mfg


# =============================================
# 축 3: 기후 비교 — 대구 vs Phoenix
# =============================================

def axis3_climate_daegu_vs_phoenix():
    """
    핵심 질문: Phoenix는 폭염에도 왜 인구가 증가하는가?
    비교 지표: 여름 기온, 주택가격 경쟁력, 생활비, 인프라 투자
    """
    print("\n" + "=" * 70)
    print("축 3: 기후 비교 — 대구 vs Phoenix")
    print("=" * 70)

    # Phoenix 부동산
    df_phoenix = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               AVG(inventory_count) AS avg_inventory,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Phoenix-Mesa-Chandler, AZ'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # Phoenix ZHVI
    df_phoenix_zhvi = query_to_df("""
        SELECT LEFT(year_month, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = 'Phoenix-Mesa-Chandler, AZ'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # 기온 데이터 (Kaggle daily_temperature)
    # ⚠️ 이 데이터는 메모리에서 직접 처리 (DB 적재 선택적)
    temp_path = 'kaggle_data/daily_temperature/'
    df_temp = None
    csv_files = glob.glob(os.path.join(temp_path, '**/*.csv'), recursive=True) if os.path.exists(temp_path) else []
    for f in csv_files:
        try:
            df_t = pd.read_csv(f, low_memory=False)
            # 대구 + Phoenix 필터
            city_col = [c for c in df_t.columns if 'city' in c.lower() or 'City' in c]
            if city_col:
                mask = df_t[city_col[0]].astype(str).str.contains('Daegu|Phoenix', case=False, na=False)
                df_temp = df_t[mask]
                if not df_temp.empty:
                    print(f"  기온 데이터: {len(df_temp)}행 (대구+Phoenix)")
                    break
        except:
            continue

    # 스코어카드
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 기온 비교
    if df_temp is not None and not df_temp.empty:
        cursor.execute("""
            INSERT INTO city_axis_scorecard
            (comparison_axis, daegu_metric_name, daegu_value,
             us_city_name, us_metric_name, us_value,
             metric_category, insight, strategy_implication)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            ('기후', '대구 여름 평균기온(℃)', None,  # 데이터로 채움
             'Phoenix', 'Phoenix 여름 평균기온(℃)', None,
             '기후',
             '대구와 Phoenix 모두 분지 지형으로 여름 폭염이 극심. '
             'Phoenix는 연평균 40℃ 이상 폭염에도 매년 인구 유입',
             'Phoenix 모델: ①캘리포니아 대비 1/3 수준 주택 가격 ②낮은 소득세(AZ) '
             '③반도체(TSMC, Intel) 대규모 공장 유치 ④에어컨 인프라+실내 생활 문화 '
             '→ 대구 적용: 수도권 대비 주택 가격 경쟁력 강조 + 첨단산업단지 유치 + 도시 냉방 인프라'))

    # 주택가격 경쟁력
    if not df_phoenix_zhvi.empty:
        latest_phoenix = df_phoenix_zhvi.iloc[-1]['avg_zhvi']
        cursor.execute("""
            INSERT INTO city_axis_scorecard
            (comparison_axis, daegu_metric_name, daegu_value,
             us_city_name, us_metric_name, us_value,
             metric_category, year_or_period, insight, strategy_implication)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            ('기후', '대구 아파트 평균가(USD)', None,
             'Phoenix', 'Phoenix ZHVI', round(latest_phoenix, 2),
             '주택가격', str(df_phoenix_zhvi.iloc[-1]['year']),
             'Phoenix는 LA/SF 대비 저렴한 주택이 인구 유입의 핵심',
             '대구도 서울 대비 주택 가격 경쟁력(약 1/3~1/4 수준)을 적극 활용해야 함'))

    conn.commit()
    conn.close()
    print("  ✅ 축 3 스코어카드 저장 완료")
    return df_phoenix, df_phoenix_zhvi, df_temp


# =============================================
# 축 4: 변모 비교 — 대구 vs Charlotte
# =============================================

def axis4_transformation_daegu_vs_charlotte():
    """
    핵심 질문: Charlotte 산업 전환 성공 요인은 대구에 적용 가능한가?
    비교: 섬유→금융/하이테크 전환 타임라인, 부동산 영향, 인구 변화
    """
    print("\n" + "=" * 70)
    print("축 4: 변모 비교 — 대구 vs Charlotte")
    print("=" * 70)

    # Charlotte 전환기 부동산
    df_charlotte = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(new_construction_sales) AS total_new_construction,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # Charlotte ZHVI 추이
    df_charlotte_zhvi = query_to_df("""
        SELECT LEFT(year_month, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
        GROUP BY LEFT(year_month, 4)
        ORDER BY year
    """)

    # 대구 아파트 가격 추이
    df_daegu_price = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price_manwon,
               COUNT(*) AS transaction_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)

    # 대구 인구
    df_daegu_pop = query_to_df("""
        SELECT year, total_population, economic_activity_rate
        FROM korean_demographics
        WHERE region LIKE '%대구%' ORDER BY year
    """)

    # 스코어카드 — 전환 타임라인 비교
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO city_axis_scorecard
        (comparison_axis, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value,
         metric_category, year_or_period, insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        ('변모', '대구 산업전환 단계', None,
         'Charlotte', 'Charlotte 산업전환 단계', None,
         '산업전환',
         '1980~2025',
         'Charlotte: 1980년대 섬유 쇠퇴 → 1990년대 Bank of America/Wachovia 본사 유치 '
         '→ 2000년대 에너지(Duke Energy) + 금융 확립 → 2010년대 Tech 허브로 확장. '
         '약 30년에 걸친 단계적 전환. '
         '대구: 1990년대 섬유 쇠퇴 시작 → 2000년대 자동차부품 성장 → 2010년대 첨단산업단지 조성 → 현재 진행 중',
         'Charlotte 성공의 3대 요인: '
         '①금융업 본사 유치로 고소득 일자리 창출 (→ 대구: 대기업 지역본사 유치 전략) '
         '②대학(UNC Charlotte) 중심 인재 공급 (→ 대구: 경북대+DGIST 산학 협력 강화) '
         '③공항 허브화(CLT)로 접근성 확보 (→ 대구: KTX+공항 연계 광역 교통망 구축). '
         '핵심 교훈: 산업 전환은 20~30년 장기 프로젝트이며, "앵커 기업" 유치가 결정적'))

    # 주택가격 전환기 변화 비교
    if not df_charlotte_zhvi.empty:
        # Charlotte 2000→2025 가격 변화율
        if len(df_charlotte_zhvi) >= 2:
            first = df_charlotte_zhvi.iloc[0]['avg_zhvi']
            last = df_charlotte_zhvi.iloc[-1]['avg_zhvi']
            change = (last - first) / first * 100 if first else 0

            cursor.execute("""
                INSERT INTO city_axis_scorecard
                (comparison_axis, daegu_metric_name, daegu_value,
                 us_city_name, us_metric_name, us_value,
                 metric_category, year_or_period, gap_ratio, insight, strategy_implication)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                ('변모', '대구 전환기 아파트 가격변화율(%)', None,
                 'Charlotte', 'Charlotte ZHVI 누적변화율(%)', round(change, 2),
                 '주택가격변화',
                 f"{df_charlotte_zhvi.iloc[0]['year']}~{df_charlotte_zhvi.iloc[-1]['year']}",
                 None,
                 f'Charlotte 주택가치 {df_charlotte_zhvi.iloc[0]["year"]}→{df_charlotte_zhvi.iloc[-1]["year"]}: '
                 f'+{change:.1f}% 상승. 산업 전환 성공이 부동산 가치 상승으로 이어짐',
                 '산업 전환 성공 → 고소득 일자리 유입 → 주택 수요 증가 → 가격 상승의 선순환. '
                 '대구가 산업 전환에 성공하면 유사한 부동산 상승 기대 가능'))

    conn.commit()
    conn.close()
    print("  ✅ 축 4 스코어카드 저장 완료")
    return df_charlotte, df_charlotte_zhvi, df_daegu_price, df_daegu_pop


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 8: 4축 비교 분석")
    print("=" * 60)

    r1 = axis1_comprehensive_daegu_vs_dallas()
    r2 = axis2_industry_daegu_vs_atlanta()
    r3 = axis3_climate_daegu_vs_phoenix()
    r4 = axis4_transformation_daegu_vs_charlotte()

    print("\n🎉 STEP 8 완료! city_axis_scorecard에 결과 저장됨")
```

---

## ⭐ STEP 9: 대구 발전전략 종합 도출 (v2 신규)

> **Claude Code 프롬프트:**
> 4축 분석 결과를 종합하여 "대구가 인구를 유지하며 살아남을 수 있는 발전 전략 보고서"를 자동 생성하는 스크립트를 만들어줘. city_axis_scorecard 테이블에서 데이터를 읽어 전략을 종합하고, Markdown 보고서로 출력해줘.

```python
# === scripts/subtopic4/step9_daegu_strategy.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *


def generate_strategy_report():
    """city_axis_scorecard → 대구 발전전략 종합 보고서 생성"""

    print("\n" + "=" * 70)
    print("대구 생존 전략 보고서 생성")
    print("=" * 70)

    # 스코어카드 전체 조회
    df = query_to_df("""
        SELECT comparison_axis, metric_category,
               daegu_metric_name, daegu_value,
               us_city_name, us_metric_name, us_value,
               gap_ratio, insight, strategy_implication
        FROM city_axis_scorecard
        ORDER BY FIELD(comparison_axis, '종합', '산업', '기후', '변모'),
                 metric_category
    """)

    if df.empty:
        print("⚠️ 스코어카드 데이터 없음. STEP 8을 먼저 실행하세요.")
        return

    # 보고서 생성
    report = []
    report.append("# 대구광역시 생존 전략 보고서")
    report.append("> 미국 4개 유사 도시 비교 분석 기반\n")
    report.append("---\n")

    # 축별 정리
    for axis in ['종합', '산업', '기후', '변모']:
        axis_df = df[df['comparison_axis'] == axis]
        if axis_df.empty:
            continue

        us_city = axis_df.iloc[0]['us_city_name']
        axis_info = {
            '종합': ('Dallas', '내륙 대도시, 보수적 성향, 무더운 여름'),
            '산업': ('Atlanta', '자동차·배터리 허브, 교통 요충지'),
            '기후': ('Phoenix', '분지 지형, 극심한 폭염'),
            '변모': ('Charlotte', '섬유→에너지/금융/첨단 도시 변모'),
        }

        report.append(f"## {axis} 비교: 대구 vs {us_city}")
        report.append(f"**공통점:** {axis_info[axis][1]}\n")

        for _, row in axis_df.iterrows():
            report.append(f"### 📊 {row['metric_category']}")
            report.append(f"- **대구:** {row['daegu_metric_name']} = {row['daegu_value']}")
            report.append(f"- **{us_city}:** {row['us_metric_name']} = {row['us_value']}")
            if row['gap_ratio']:
                report.append(f"- **격차 비율:** {row['gap_ratio']}")
            report.append(f"\n**인사이트:** {row['insight']}\n")
            report.append(f"**🎯 대구 전략 시사점:** {row['strategy_implication']}\n")
            report.append("---\n")

    # 종합 전략
    report.append("## 🏆 대구 인구유지 종합 전략\n")
    report.append("### 미국 4개 도시에서 배운 5대 핵심 전략\n")
    report.append("""
| # | 전략 | 벤치마크 도시 | 대구 적용 방안 |
|---|------|-------------|--------------|
| 1 | **주택 가격 경쟁력 마케팅** | Dallas, Phoenix | 수도권 대비 1/3~1/4 가격을 적극 홍보, 원격근무자 유치 |
| 2 | **앵커 기업 유치** | Charlotte, Dallas | 대기업 지역본사/R&D센터 유치 인센티브 (세제 혜택+부지 제공) |
| 3 | **교통 인프라 혁신** | Atlanta | KTX 30분 생활권 확대, 대구공항 국제선 확충, 광역교통망 |
| 4 | **산학 협력 생태계** | Charlotte, Atlanta | 경북대+DGIST+영남대 중심 산학클러스터, 스타트업 지원 |
| 5 | **기후 핸디캡 극복** | Phoenix | 도시 냉방 인프라, 실내 문화시설, 그린 인프라 투자 |

### 타임라인 제안

```
단기 (1~3년): 원격근무자 유치 + 주택 가격 경쟁력 마케팅
중기 (3~7년): 앵커 기업 유치 + 교통 인프라 착공
장기 (7~15년): 산업 전환 완성 + 인구 안정화
```

### Charlotte에서 배운 교훈
Charlotte의 산업 전환은 약 30년이 소요되었습니다.
대구는 1990년대부터 전환을 시작했으므로, 2025년 현재 약 30년째입니다.
Charlotte가 전환 완성기(2000년대 중반)에 보인 신호들:
- 신규건설 판매건수 급증
- 시장온도지수 상승 (판매자 우위)
- 주택구매 필요소득 증가 (고소득 유입)

대구가 이 신호들을 보이기 시작한다면, 전환 성공의 초기 징후로 볼 수 있습니다.
""")

    # 파일 저장
    os.makedirs('output/subtopic4', exist_ok=True)
    report_path = 'output/subtopic4/daegu_strategy_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n✅ 보고서 저장: {report_path}")
    return report_path


if __name__ == '__main__':
    generate_strategy_report()
```

---

## 📊 STEP 10: 기존 시각화 (v1 유지)

> v1의 V1~V5 차트는 그대로 유지합니다. 코드는 v1 가이드의 step8_visualization.py와 동일합니다.

---

## ⭐ STEP 11: 4축 비교 시각화 (v2 신규)

> **Claude Code 프롬프트:**
> 4축 비교 분석 결과를 시각화해줘. 총 6개 차트를 만들어줘: 레이더차트, 4축 대시보드, 인구-주택가격 이중축, 산업전환 타임라인, 기후-부동산 비교, 종합 전략 인포그래픽

### 시각화 목록 (v2 추가: 6개)

| # | 차트명 | 유형 | 데이터 |
|---|--------|------|--------|
| V6 | 4축 레이더 차트: 대구 vs 4도시 종합 비교 | Radar/Spider | 스코어카드 |
| V7 | 4축 대시보드: 축별 핵심 지표 2×2 패널 | Subplot 4패널 | 각 축 데이터 |
| V8 | 인구 흐름 vs 주택가격: 대구 유출 vs 4도시 유입 | 이중축 선형 | 인구+ZHVI |
| V9 | 산업 전환 타임라인: 대구 vs Charlotte 나란히 | 듀얼 타임라인 | 전환 단계별 |
| V10 | 기후 핸디캡 극복: 대구 vs Phoenix 비교 | 막대+선형 | 기온+부동산 |
| V11 | 대구 발전전략 로드맵 인포그래픽 | 흐름도/매트릭스 | 종합 전략 |

```python
# === scripts/subtopic4/step11_visualization_4axis.py ===

import sys
sys.path.append('scripts/subtopic4')
from step0_setup import *
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.gridspec import GridSpec

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

OUTPUT_DIR = 'output/subtopic4/'
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================
# V6: 4축 레이더 차트
# =============================================

def viz_v6_radar_chart():
    """대구 vs 4도시 종합 비교 레이더 차트"""
    import numpy as np

    # 비교 차원 (정규화된 점수, 0~100)
    categories = [
        'Housing\nAffordability',
        'Population\nGrowth',
        'Industry\nDiversity',
        'Infrastructure\n(Transport)',
        'Job\nCreation',
        'Climate\nLivability'
    ]

    # 점수는 분석 결과 기반으로 조정 (예시값, 실제 데이터로 대체)
    scores = {
        'Daegu':     [75, 25, 40, 55, 35, 40],
        'Dallas':    [65, 85, 75, 70, 80, 50],
        'Atlanta':   [60, 70, 80, 90, 75, 60],
        'Phoenix':   [55, 80, 60, 65, 70, 30],
        'Charlotte': [60, 75, 70, 70, 75, 65],
    }

    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # 닫기

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    for city, vals in scores.items():
        values = vals + vals[:1]
        color = CITY_COLORS.get(city, 'gray')
        ax.plot(angles, values, 'o-', linewidth=2, color=color, label=city)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=8)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    ax.set_title('Daegu vs US Peer Cities\n4-Axis Comparison Radar',
                 fontsize=15, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v6_radar_4axis.png', bbox_inches='tight')
    plt.close()
    print("✅ V6 레이더 차트 저장")


# =============================================
# V7: 4축 대시보드 (2×2 패널)
# =============================================

def viz_v7_4axis_dashboard():
    """축별 핵심 지표를 2×2 패널로 표시"""

    fig = plt.figure(figsize=(18, 14))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    # --- 패널 1: 종합 (Dallas) — ZHVI 추이 ---
    ax1 = fig.add_subplot(gs[0, 0])
    df1 = query_to_df("""
        SELECT LEFT(year_month, 4) AS year, AVG(zhvi) AS avg_zhvi, region_name
        FROM us_metro_zhvi
        WHERE region_name IN ('Dallas-Fort Worth-Arlington, TX', 'United States')
        GROUP BY region_name, LEFT(year_month, 4) ORDER BY year
    """)
    if not df1.empty:
        for name in df1['region_name'].unique():
            sub = df1[df1['region_name'] == name]
            label = name.split(',')[0] if ',' in name else name
            ax1.plot(sub['year'], sub['avg_zhvi'], marker='.', label=label,
                     color=CITY_COLORS.get(name, 'gray'), linewidth=2)
        ax1.set_title('Axis 1 [Comprehensive]: Dallas ZHVI Trend', fontsize=12, fontweight='bold')
        ax1.set_ylabel('ZHVI (USD)')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

    # --- 패널 2: 산업 (Atlanta) — 신규건설+시장온도 ---
    ax2 = fig.add_subplot(gs[0, 1])
    df2 = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS temp,
               SUM(new_construction_sales) AS new_con
        FROM us_metro_demand
        WHERE region_name = 'Atlanta-Sandy Springs-Roswell, GA'
        GROUP BY LEFT(year_month, 4) ORDER BY year
    """)
    if not df2.empty:
        ax2_twin = ax2.twinx()
        ax2.bar(df2['year'], df2['new_con'], color='#3498DB', alpha=0.5, label='New Construction')
        ax2_twin.plot(df2['year'], df2['temp'], color='#E74C3C', marker='o', linewidth=2, label='Market Temp')
        ax2_twin.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        ax2.set_title('Axis 2 [Industry]: Atlanta Construction & Market Temp',
                      fontsize=12, fontweight='bold')
        ax2.set_ylabel('New Construction Sales', color='#3498DB')
        ax2_twin.set_ylabel('Market Temp Index', color='#E74C3C')
        ax2.tick_params(axis='x', rotation=45)

    # --- 패널 3: 기후 (Phoenix) — 필요소득 추이 ---
    ax3 = fig.add_subplot(gs[1, 0])
    df3 = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(income_needed) AS income, region_name
        FROM us_metro_demand
        WHERE region_name IN (
            'Phoenix-Mesa-Chandler, AZ',
            'Dallas-Fort Worth-Arlington, TX',
            'Charlotte-Concord-Gastonia, NC-SC'
        ) AND income_needed IS NOT NULL
        GROUP BY region_name, LEFT(year_month, 4) ORDER BY year
    """)
    if not df3.empty:
        for name in df3['region_name'].unique():
            sub = df3[df3['region_name'] == name]
            label = name.split(',')[0] if ',' in name else name
            ax3.plot(sub['year'], sub['income'], marker='.', label=label,
                     color=CITY_COLORS.get(name, 'gray'), linewidth=2)
        ax3.set_title('Axis 3 [Climate]: Income Needed to Buy Home',
                      fontsize=12, fontweight='bold')
        ax3.set_ylabel('Annual Income (USD)')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)

    # --- 패널 4: 변모 (Charlotte) — 매물재고+판매건수 ---
    ax4 = fig.add_subplot(gs[1, 1])
    df4 = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               SUM(sales_count) AS sales,
               AVG(inventory_count) AS inventory
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
        GROUP BY LEFT(year_month, 4) ORDER BY year
    """)
    if not df4.empty:
        ax4_twin = ax4.twinx()
        ax4.bar(df4['year'], df4['sales'], color='#2ECC71', alpha=0.5, label='Sales Count')
        ax4_twin.plot(df4['year'], df4['inventory'], color='#9B59B6', marker='s',
                      linewidth=2, label='Inventory')
        ax4.set_title('Axis 4 [Transformation]: Charlotte Sales & Inventory',
                      fontsize=12, fontweight='bold')
        ax4.set_ylabel('Sales Count', color='#2ECC71')
        ax4_twin.set_ylabel('Inventory Count', color='#9B59B6')
        ax4.tick_params(axis='x', rotation=45)

    fig.suptitle('4-Axis Comparison Dashboard\nDaegu Peer City Analysis',
                 fontsize=16, fontweight='bold')
    plt.savefig(f'{OUTPUT_DIR}v7_4axis_dashboard.png', bbox_inches='tight')
    plt.close()
    print("✅ V7 4축 대시보드 저장")


# =============================================
# V8: 인구 vs 주택가격 이중축
# =============================================

def viz_v8_population_vs_housing():
    """대구 인구유출 vs 4도시 주택가격 비교"""

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(16, 12))

    # 상단: 4개 미국 도시 ZHVI 추이
    df_zhvi = query_to_df("""
        SELECT LEFT(year_month, 4) AS year, AVG(zhvi) AS avg_zhvi, region_name
        FROM us_metro_zhvi
        WHERE region_name != 'United States'
        GROUP BY region_name, LEFT(year_month, 4) ORDER BY year
    """)
    if not df_zhvi.empty:
        for name in df_zhvi['region_name'].unique():
            sub = df_zhvi[df_zhvi['region_name'] == name]
            label = name.split(',')[0]
            ax_top.plot(sub['year'], sub['avg_zhvi'], marker='.', label=label,
                       color=CITY_COLORS.get(name, 'gray'), linewidth=2)
        ax_top.set_title('US Peer Cities: Home Value Index (ZHVI) Trend', fontsize=13, fontweight='bold')
        ax_top.set_ylabel('ZHVI (USD)')
        ax_top.legend()
        ax_top.grid(True, alpha=0.3)
        ax_top.tick_params(axis='x', rotation=45)

    # 하단: 대구 인구 + 아파트 가격
    df_pop = query_to_df("""
        SELECT year, total_population FROM korean_demographics
        WHERE region LIKE '%대구%' ORDER BY year
    """)
    df_price = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price
        FROM daegu_housing_prices WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)

    if not df_pop.empty:
        ax_bot.plot(df_pop['year'], df_pop['total_population'], color='#9B59B6',
                    marker='o', linewidth=2, label='Daegu Population')
        ax_bot.set_ylabel('Population', color='#9B59B6', fontsize=12)
    if not df_price.empty:
        ax_r = ax_bot.twinx()
        ax_r.plot(df_price['year'], df_price['avg_price'], color='#E67E22',
                  marker='s', linewidth=2, linestyle='--', label='Daegu Apt Price (만원)')
        ax_r.set_ylabel('Avg Apt Price (만원)', color='#E67E22', fontsize=12)

    ax_bot.set_title('Daegu: Population Decline vs Housing Price', fontsize=13, fontweight='bold')
    ax_bot.set_xlabel('Year')
    lines1, labels1 = ax_bot.get_legend_handles_labels()
    if not df_price.empty:
        lines2, labels2 = ax_r.get_legend_handles_labels()
        ax_bot.legend(lines1 + lines2, labels1 + labels2)
    ax_bot.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v8_population_vs_housing.png', bbox_inches='tight')
    plt.close()
    print("✅ V8 인구 vs 주택가격 저장")


# =============================================
# V9: 산업 전환 타임라인 비교
# =============================================

def viz_v9_transformation_timeline():
    """대구 vs Charlotte 전환 타임라인 나란히"""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # Charlotte 타임라인 (데이터 기반)
    df_ch = query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS temp,
               AVG(income_needed) AS income,
               SUM(new_construction_sales) AS new_con
        FROM us_metro_demand
        WHERE region_name = 'Charlotte-Concord-Gastonia, NC-SC'
        GROUP BY LEFT(year_month, 4) ORDER BY year
    """)

    if not df_ch.empty:
        ax1_t = ax1.twinx()
        ax1.bar(df_ch['year'], df_ch['new_con'], color='#2ECC71', alpha=0.4, label='New Construction')
        ax1_t.plot(df_ch['year'], df_ch['income'], color='#E74C3C', marker='o',
                   linewidth=2, label='Income Needed')
        ax1.set_title('Charlotte\nTextile → Finance/Tech Transition\n(Completed)',
                      fontsize=13, fontweight='bold', color='#2ECC71')
        ax1.set_ylabel('New Construction Sales', color='#2ECC71')
        ax1_t.set_ylabel('Income Needed (USD)', color='#E74C3C')
        ax1.tick_params(axis='x', rotation=45)
        # 전환 이벤트 주석
        ax1.axvline(x='2019', color='blue', linestyle=':', alpha=0.5)
        ax1.text(df_ch['year'].iloc[len(df_ch)//2], ax1.get_ylim()[1]*0.9,
                'Bank of America HQ\nDuke Energy\nTech Hub Growth',
                fontsize=9, ha='center', style='italic',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 대구 타임라인 (아파트 가격 + 인구)
    df_dg = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price, COUNT(*) AS tx_count
        FROM daegu_housing_prices WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    df_pop = query_to_df("""
        SELECT year, total_population FROM korean_demographics
        WHERE region LIKE '%대구%' ORDER BY year
    """)

    if not df_dg.empty:
        ax2_t = ax2.twinx()
        ax2.bar(df_dg['year'].astype(str), df_dg['tx_count'], color='#9B59B6', alpha=0.4,
                label='Transactions')
        ax2_t.plot(df_dg['year'].astype(str), df_dg['avg_price'], color='#E74C3C',
                   marker='o', linewidth=2, label='Avg Price (만원)')
        ax2.set_title('Daegu\nTextile → Hightech Transition\n(In Progress)',
                      fontsize=13, fontweight='bold', color='#9B59B6')
        ax2.set_ylabel('Transaction Count', color='#9B59B6')
        ax2_t.set_ylabel('Avg Apt Price (만원)', color='#E74C3C')
        ax2.tick_params(axis='x', rotation=45)
        ax2.text(df_dg['year'].astype(str).iloc[len(df_dg)//2], ax2.get_ylim()[1]*0.9,
                'Auto Parts Growth\nDGIST Founded\nNat\'l Innovation Cluster',
                fontsize=9, ha='center', style='italic',
                bbox=dict(boxstyle='round', facecolor='plum', alpha=0.5))

    fig.suptitle('Industrial Transformation Timeline\nCharlotte (Complete) vs Daegu (In Progress)',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}v9_transformation_timeline.png', bbox_inches='tight')
    plt.close()
    print("✅ V9 전환 타임라인 저장")


# =============================================
# V10: 전략 로드맵 인포그래픽
# =============================================

def viz_v10_strategy_roadmap():
    """대구 발전전략 로드맵 시각화"""

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 타이틀
    ax.text(50, 97, 'Daegu Survival Strategy Roadmap', fontsize=18,
            fontweight='bold', ha='center', va='top')
    ax.text(50, 93, 'Lessons from Dallas · Atlanta · Phoenix · Charlotte',
            fontsize=12, ha='center', va='top', color='gray')

    # 타임라인 화살표
    ax.annotate('', xy=(90, 50), xytext=(10, 50),
                arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=3))
    ax.text(10, 47, 'NOW', fontsize=10, fontweight='bold', color='#E74C3C')
    ax.text(38, 47, '3 YEARS', fontsize=10, fontweight='bold', color='#F39C12')
    ax.text(62, 47, '7 YEARS', fontsize=10, fontweight='bold', color='#2ECC71')
    ax.text(85, 47, '15 YEARS', fontsize=10, fontweight='bold', color='#3498DB')

    # 단기 전략 (좌)
    strategies_short = [
        ('Housing Price\nCompetitiveness\nMarketing', 'Dallas\nModel', '#E74C3C'),
        ('Remote Worker\nAttraction\nProgram', 'Phoenix\nModel', '#F39C12'),
    ]
    for i, (strat, model, color) in enumerate(strategies_short):
        y = 72 - i * 18
        rect = mpatches.FancyBboxPatch((5, y-5), 28, 12, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(19, y+1, strat, fontsize=9, ha='center', va='center', fontweight='bold')
        ax.text(19, y-4, model, fontsize=7, ha='center', va='center', color=color, style='italic')

    # 중기 전략 (중)
    strategies_mid = [
        ('Anchor Company\nHQ Attraction', 'Charlotte\nModel', '#2ECC71'),
        ('Transport Infra\nKTX + Airport', 'Atlanta\nModel', '#3498DB'),
    ]
    for i, (strat, model, color) in enumerate(strategies_mid):
        y = 72 - i * 18
        rect = mpatches.FancyBboxPatch((37, y-5), 28, 12, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(51, y+1, strat, fontsize=9, ha='center', va='center', fontweight='bold')
        ax.text(51, y-4, model, fontsize=7, ha='center', va='center', color=color, style='italic')

    # 장기 전략 (우)
    strategies_long = [
        ('Industry\nTransformation\nComplete', 'Charlotte\nModel', '#9B59B6'),
        ('Population\nStabilization\n& Growth', 'All 4\nModels', '#2C3E50'),
    ]
    for i, (strat, model, color) in enumerate(strategies_long):
        y = 72 - i * 18
        rect = mpatches.FancyBboxPatch((68, y-5), 28, 12, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.15, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(82, y+1, strat, fontsize=9, ha='center', va='center', fontweight='bold')
        ax.text(82, y-4, model, fontsize=7, ha='center', va='center', color=color, style='italic')

    # 범례 박스
    legend_y = 18
    cities = [('Dallas', '#E74C3C', 'Affordability'),
              ('Atlanta', '#3498DB', 'Hub Strategy'),
              ('Phoenix', '#F39C12', 'Climate Resilience'),
              ('Charlotte', '#2ECC71', 'Transformation')]
    for i, (city, color, keyword) in enumerate(cities):
        x = 12 + i * 22
        ax.add_patch(mpatches.FancyBboxPatch((x-2, legend_y-3), 20, 8,
                     boxstyle="round,pad=0.5", facecolor=color, alpha=0.2,
                     edgecolor=color, linewidth=1.5))
        ax.text(x+8, legend_y+2, city, fontsize=9, ha='center', fontweight='bold', color=color)
        ax.text(x+8, legend_y-1, keyword, fontsize=8, ha='center', color='gray')

    plt.savefig(f'{OUTPUT_DIR}v10_strategy_roadmap.png', bbox_inches='tight')
    plt.close()
    print("✅ V10 전략 로드맵 저장")


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 11: 4축 비교 시각화 (v2)")
    print("=" * 60)

    viz_v6_radar_chart()
    viz_v7_4axis_dashboard()
    viz_v8_population_vs_housing()
    viz_v9_transformation_timeline()
    viz_v10_strategy_roadmap()

    print(f"\n🎉 모든 v2 차트 저장: {OUTPUT_DIR}")
```

---

## 🚀 전체 실행 순서 요약

```bash
# 0. 패키지 설치
pip install pymysql pandas numpy matplotlib seaborn scipy openpyxl kaggle

# 1. Kaggle 데이터 다운로드 (v2: 10개 데이터셋)
python scripts/subtopic4/step1_download_kaggle.py

# 2. MySQL 테이블 생성 (v2: 10개 테이블)
python scripts/subtopic4/step2_create_tables.py

# 3. Zillow 부동산 데이터 로딩 (v2: ZHVI+ZORI+재고량 추가)
python scripts/subtopic4/step3_load_us_zillow.py

# 4. BLS 고용 데이터 (⚠️ 파일 구조 확인 후 실행)
python scripts/subtopic4/step4_load_kaggle_bls.py

# 5. 글로벌 경제지표
python scripts/subtopic4/step5_load_kaggle_global.py

# 6. 한국 프록시 데이터
python scripts/subtopic4/step6_load_korean_proxy.py

# 6b. ★ v2 추가: 대구 아파트 + 인구성장률
python scripts/subtopic4/step6b_load_v2_data.py

# 7. 기존 산업전환 분석 (Q1~Q4)
python scripts/subtopic4/step7_analysis_core.py

# 8. ★ v2: 4축 비교 분석
python scripts/subtopic4/step8_analysis_4axis.py

# 9. ★ v2: 대구 발전전략 보고서 생성
python scripts/subtopic4/step9_daegu_strategy.py

# 10. 기존 시각화 (V1~V5)
python scripts/subtopic4/step10_visualization_core.py

# 11. ★ v2: 4축 비교 시각화 (V6~V10)
python scripts/subtopic4/step11_visualization_4axis.py
```

---

## ⚠️ Claude Code 사용 시 주의사항

### 1. Kaggle 데이터 구조 불확실성

```
모든 Kaggle 데이터는 다운로드 전까지 정확한 열 이름을 모릅니다.
Claude Code에게: "먼저 explore 함수로 파일 구조를 확인하고, 파싱 로직을 조정해줘"
```

### 2. 레이더 차트 점수 산출 기준

V6 레이더 차트의 점수는 **분석 결과 기반으로 정규화**해야 합니다:

| 차원 | 산출 기준 | 정규화 방법 |
|------|----------|-----------|
| Housing Affordability | 중위소득 대비 주택가격 비율 역수 | 5개 도시 중 min-max 스케일링 |
| Population Growth | 인구 변화율 | 양수→100, 음수→0 기준 선형 |
| Industry Diversity | 제조업+서비스업+하이테크 분산도 | HHI 역수 정규화 |
| Infrastructure | 공항 이용객 수 + KTX/고속도로 접근성 | 정성 평가 (별도 리서치) |
| Job Creation | 신규건설 판매건수 + 고용변화율 | 5개 도시 중 순위 기반 |
| Climate Livability | 여름 폭염일수 역수 + 쾌적일수 | 기온 데이터 기반 |

> **Claude Code 프롬프트:** "V6 레이더 차트의 점수를 실제 DB 데이터로 계산해줘. step8에서 분석한 결과와 city_axis_scorecard 데이터를 활용해서 0~100 점수로 정규화해줘."

### 3. 환율 처리

대구 vs 미국 도시 가격 비교 시 환율 변환 필요:
```python
KRW_TO_USD = 1350  # 기준 환율 (필요시 조정)
daegu_price_usd = daegu_price_manwon * 10000 / KRW_TO_USD
```

### 4. Claude Code 단계별 프롬프트 예시

```
[STEP 8 — 4축 분석]
4축 비교 분석을 실행해줘:
- 축1(종합): 대구 인구 vs Dallas ZHVI+필요소득 비교
- 축2(산업): 한국/미국 제조업 비중 + Atlanta 신규건설 비교
- 축3(기후): 대구/Phoenix 기온 데이터 + 주택가격 비교
- 축4(변모): 대구/Charlotte 산업전환 타임라인 비교
결과를 city_axis_scorecard 테이블에 저장해줘.
각 축마다 "대구 전략 시사점"을 strategy_implication 컬럼에 넣어줘.

[STEP 9 — 전략 보고서]
city_axis_scorecard에서 데이터를 읽어서
"대구가 인구를 유지하며 살아남을 수 있는 5대 전략" 보고서를
output/subtopic4/daegu_strategy_report.md로 생성해줘.
각 전략마다 어떤 미국 도시에서 배운 것인지 명시해줘.

[STEP 11 — 4축 시각화]
V6 레이더 차트: 대구와 4개 미국 도시를 6개 차원으로 비교
V7 2×2 대시보드: 축별 핵심 지표
V8: 대구 인구유출 vs 미국 4도시 주택가격 상승 비교
V9: 대구 vs Charlotte 산업전환 타임라인 나란히
V10: 전략 로드맵 인포그래픽
```

---

## 📑 산출물 체크리스트

### 테이블 (v1: 7개 + v2: 3개 = 10개)

| # | 테이블명 | v2 | 상태 |
|---|---------|-----|------|
| T1 | `us_industry_employment` | | ☐ |
| T2 | `economic_indicators` | | ☐ |
| T3 | `us_metro_demand` | | ☐ |
| T4 | `us_metro_zhvf_growth` | | ☐ |
| T5 | `zillow_timeseries` (state) | | ☐ |
| T6 | `korean_demographics` (대구) | | ☐ |
| T7 | `industry_housing_impact` | | ☐ |
| T8 | `city_comparison_population` | ✅ | ☐ |
| T9 | `daegu_housing_prices` | ✅ | ☐ |
| T10 | `city_axis_scorecard` | ✅ | ☐ |

### 시각화 (v1: 5개 + v2: 5개 = 10개)

| # | 차트명 | v2 | 상태 |
|---|--------|-----|------|
| V1 | 산업전환 타임라인 (4도시) | | ☐ |
| V2 | Charlotte 전환기 대시보드 | | ☐ |
| V3 | 시장건전성 히트맵 | | ☐ |
| V4 | 대구 vs Charlotte 비교 | | ☐ |
| V5 | 예측 성장률 | | ☐ |
| V6 | ⭐ 4축 레이더 차트 | ✅ | ☐ |
| V7 | ⭐ 4축 대시보드 (2×2) | ✅ | ☐ |
| V8 | ⭐ 인구 vs 주택가격 이중축 | ✅ | ☐ |
| V9 | ⭐ 산업전환 타임라인 (대구 vs Charlotte) | ✅ | ☐ |
| V10 | ⭐ 전략 로드맵 인포그래픽 | ✅ | ☐ |

### 보고서 (v2 신규)

| # | 산출물 | 파일 | 상태 |
|---|--------|------|------|
| R1 | 대구 생존 전략 보고서 | `output/subtopic4/daegu_strategy_report.md` | ☐ |
