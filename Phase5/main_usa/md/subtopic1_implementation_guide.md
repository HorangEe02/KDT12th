# 소주제 1: 주택 가격 추이 비교 — Claude Code 구현 가이드

## 🎯 이 문서의 목적

Claude Code가 이 문서를 읽고 소주제 1(주택 가격 추이 비교)의 **전체 파이프라인**을 자동 구현할 수 있도록 작성된 상세 가이드입니다.

---

## 📋 실행 환경

```
DB Host   : 172.30.1.47
DB User   : wonho
DB Pass   : 1111
DB Name   : real_estate_comparison
Charset   : utf8mb4
Python    : pymysql, pandas, numpy, matplotlib, seaborn
```

---

## 📂 파일 경로 규칙

```
프로젝트 루트/
├── data/
│   ├── realtor-data.zip.csv                         ← Realtor.com 개별 매물 (178MB)
│   ├── Zillow_Economics/
│   │   ├── Metro_time_series.csv                    ← MSA Long Format (56MB)
│   │   ├── State_time_series.csv                    ← State Long Format (4.7MB)
│   │   ├── City_time_series.csv                     ← City Long Format (689MB)
│   │   ├── cities_crosswalk.csv                     ← 도시-카운티-주 매핑
│   │   ├── CountyCrossWalk_Zillow.csv               ← 카운티-MSA 매핑
│   │   └── DataDictionary.csv                       ← 변수 사전
│   └── zillow_Housing/
│       ├── Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv   ← ZHVI Wide
│       ├── Metro_zori_uc_sfrcondomfr_sm_month.csv                  ← ZORI Wide
│       ├── Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv ← 예측 Wide
│       └── National_zorf_growth_uc_sfr_sm_month.csv                ← 전국임대예측 Wide
├── kaggle_data/
│   ├── daegu_apartment_transaction.csv              ← K1-1 대구 실거래가
│   ├── daegu_real_estate.csv                        ← K1-2 대구 부동산
│   ├── korean_apartment_deal.csv                    ← K1-3 전국 아파트 거래
│   └── korea_house_data.csv                         ← K1-4 10년간 주택
├── src/
│   ├── step0_init_db.py
│   ├── step1_create_tables.py
│   ├── step2_load_us_zillow_wide.py
│   ├── step3_load_us_zillow_economics.py
│   ├── step4_load_us_realtor.py
│   ├── step5_load_kr_daegu.py
│   ├── step6_analysis_queries.py
│   └── step7_visualization.py
└── output/
    └── (시각화 결과물)
```

> **주의:** `kaggle_data/` 폴더의 파일명은 실제 Kaggle 다운로드 시 다를 수 있음. 실행 전 `os.listdir('kaggle_data/')` 로 확인하고 파일명 매핑 필요.

---

## 🔨 STEP 0: DB 연결 공통 모듈 및 초기화

### 파일: `src/step0_init_db.py`

```python
"""
STEP 0: DB 연결 공통 모듈 + 데이터베이스 생성
실행: python src/step0_init_db.py
"""
import pymysql
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ── DB 접속 정보 ──
DB_CONFIG = {
    'host': '172.30.1.47',
    'user': 'wonho',
    'password': '1111',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
DB_NAME = 'real_estate_comparison'


def get_connection(db_name=None):
    """MySQL 연결 반환"""
    config = DB_CONFIG.copy()
    if db_name:
        config['db'] = db_name
    return pymysql.connect(**config)


def execute_sql(sql, db_name=DB_NAME, fetch=False):
    """단일 SQL 실행 헬퍼"""
    conn = get_connection(db_name)
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return result


def create_database():
    """데이터베이스 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                   f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    conn.close()
    print(f"✅ DB '{DB_NAME}' 생성/확인 완료")


def insert_cities():
    """비교 대상 5개 도시 마스터 데이터 삽입"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 중복 방지
    cursor.execute("SELECT COUNT(*) AS cnt FROM cities")
    if cursor.fetchone()['cnt'] > 0:
        print("ℹ️  cities 테이블에 이미 데이터 존재 — 스킵")
        conn.close()
        return

    cities = [
        ('대구', 'South Korea', '종합/기준', None, 2385412, 35.8714, 128.6014),
        ('Dallas', 'USA', '종합', '대구-Dallas', 1304379, 32.7767, -96.7970),
        ('Atlanta', 'USA', '산업', '대구-Atlanta', 498715, 33.7490, -84.3880),
        ('Phoenix', 'USA', '기후', '대구-Phoenix', 1608139, 33.4484, -112.0740),
        ('Charlotte', 'USA', '변모', '대구-Charlotte', 879709, 35.2271, -80.8431),
    ]

    sql = ("INSERT INTO cities "
           "(city_name, country, category, comparison_pair, population, latitude, longitude) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    cursor.executemany(sql, cities)
    conn.commit()
    conn.close()
    print("✅ 5개 도시 마스터 삽입 완료")


if __name__ == '__main__':
    create_database()
    # 테이블 생성은 step1에서 수행
    print("🎉 STEP 0 완료")
```

---

## 🔨 STEP 1: 테이블 생성

### 파일: `src/step1_create_tables.py`

소주제 1에 필요한 테이블만 생성합니다.

```python
"""
STEP 1: 소주제 1 관련 테이블 생성
실행: python src/step1_create_tables.py
의존: step0_init_db.py
"""
from step0_init_db import get_connection, DB_NAME, create_database, insert_cities


TABLES = {

    # ── 마스터: 도시 ──
    'cities': """
        CREATE TABLE IF NOT EXISTS cities (
            city_id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50) NOT NULL,
            country VARCHAR(20) NOT NULL,
            category VARCHAR(30),
            comparison_pair VARCHAR(50),
            population BIGINT,
            latitude DECIMAL(10,6),
            longitude DECIMAL(10,6)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-A. 대구 아파트 실거래가 (Kaggle K1-1, K1-2) ──
    'daegu_housing_prices': """
        CREATE TABLE IF NOT EXISTS daegu_housing_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year_month VARCHAR(7) COMMENT 'YYYY-MM',
            district VARCHAR(30) COMMENT '구/군 (수성구, 달서구 등)',
            dong VARCHAR(50) COMMENT '동',
            apt_name VARCHAR(100) COMMENT '아파트명',
            exclusive_area DECIMAL(10,2) COMMENT '전용면적 m²',
            deal_amount BIGINT COMMENT '거래금액 (만원)',
            floor INT COMMENT '층',
            build_year INT COMMENT '건축년도',
            deal_date DATE COMMENT '거래일자',
            deal_type VARCHAR(20) COMMENT '거래유형',
            source_dataset VARCHAR(100) COMMENT '원본 데이터셋명',
            INDEX idx_ym (year_month),
            INDEX idx_district (district),
            INDEX idx_date (deal_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-B. 대구 월별 집계 (분석 편의용 요약 테이블) ──
    'daegu_monthly_summary': """
        CREATE TABLE IF NOT EXISTS daegu_monthly_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year_month VARCHAR(7),
            district VARCHAR(30),
            avg_price BIGINT COMMENT '평균 거래금액 (만원)',
            median_price BIGINT COMMENT '중위 거래금액 (만원)',
            min_price BIGINT,
            max_price BIGINT,
            transaction_count INT COMMENT '거래 건수',
            avg_area DECIMAL(10,2) COMMENT '평균 전용면적 m²',
            avg_price_per_m2 DECIMAL(12,2) COMMENT '㎡당 평균가 (만원)',
            yoy_change_rate DECIMAL(8,4) COMMENT '전년동기 대비 변동률',
            INDEX idx_ym_district (year_month, district)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-C. 미국 Realtor.com 개별 매물 ──
    'us_realtor_listings': """
        CREATE TABLE IF NOT EXISTS us_realtor_listings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_id INT COMMENT 'cities 테이블 FK',
            brokered_by DOUBLE,
            status VARCHAR(30) COMMENT '매물상태 (for_sale 등)',
            price DECIMAL(15,2) COMMENT '매물가격 USD',
            bed INT COMMENT '침실 수',
            bath INT COMMENT '욕실 수',
            acre_lot DECIMAL(10,4) COMMENT '부지 면적 (에이커)',
            street DOUBLE,
            city VARCHAR(100),
            state VARCHAR(50),
            zip_code VARCHAR(10),
            house_size DECIMAL(12,2) COMMENT '주택면적 sqft',
            prev_sold_date VARCHAR(20) COMMENT '이전 판매일',
            FOREIGN KEY (city_id) REFERENCES cities(city_id),
            INDEX idx_city_state (city(50), state(10)),
            INDEX idx_zip (zip_code),
            INDEX idx_state (state(10)),
            INDEX idx_price (price)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-D. 미국 MSA ZHVI (zillow_Housing Wide → Long 변환) ──
    'us_metro_zhvi': """
        CREATE TABLE IF NOT EXISTS us_metro_zhvi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT COMMENT 'Zillow RegionID',
            size_rank INT COMMENT '지역크기 순위',
            region_name VARCHAR(200) COMMENT 'MSA명 (예: Dallas-Fort Worth-Arlington, TX)',
            region_type VARCHAR(30) COMMENT 'country 또는 msa',
            state_name VARCHAR(10) COMMENT '주 약어',
            year_month VARCHAR(7) COMMENT 'YYYY-MM',
            zhvi DECIMAL(15,2) COMMENT '주택가치지수 USD',
            INDEX idx_region_ym (region_name(100), year_month),
            INDEX idx_ym (year_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-E. 미국 MSA ZORI (zillow_Housing Wide → Long 변환) ──
    'us_metro_zori': """
        CREATE TABLE IF NOT EXISTS us_metro_zori (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT,
            size_rank INT,
            region_name VARCHAR(200),
            region_type VARCHAR(30),
            state_name VARCHAR(10),
            year_month VARCHAR(7),
            zori DECIMAL(12,2) COMMENT '임대관측지수 USD/월',
            INDEX idx_region_ym (region_name(100), year_month),
            INDEX idx_ym (year_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-F. 미국 MSA 예측 성장률 (ZHVF) ──
    'us_metro_zhvf_growth': """
        CREATE TABLE IF NOT EXISTS us_metro_zhvf_growth (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT,
            region_name VARCHAR(200),
            region_type VARCHAR(30),
            state_name VARCHAR(10),
            base_date VARCHAR(10) COMMENT '예측 기준일',
            forecast_date VARCHAR(10) COMMENT '예측 대상일',
            growth_rate DECIMAL(8,4) COMMENT '누적 예측 성장률 %',
            INDEX idx_region (region_name(100))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-G. 전국 임대 예측 성장률 (ZORF) ──
    'us_national_zorf_growth': """
        CREATE TABLE IF NOT EXISTS us_national_zorf_growth (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT,
            region_name VARCHAR(200),
            base_date VARCHAR(10),
            forecast_date VARCHAR(10),
            growth_rate DECIMAL(8,4) COMMENT '누적 예측 성장률 %'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-H. Zillow Economics 시계열 (Long Format — Metro/State/City) ──
    'zillow_economics_ts': """
        CREATE TABLE IF NOT EXISTS zillow_economics_ts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE COMMENT '관측일',
            region_name VARCHAR(200) COMMENT '지역명 (MSA코드/주명/도시명)',
            region_level ENUM('metro','state','city') COMMENT '지역 레벨',
            zhvi_all DECIMAL(15,2) COMMENT 'ZHVI_AllHomes',
            zhvi_sfr DECIMAL(15,2) COMMENT 'ZHVI_SingleFamilyResidence',
            zhvi_condo DECIMAL(15,2) COMMENT 'ZHVI_CondoCoop',
            zhvi_per_sqft DECIMAL(10,2) COMMENT 'ZHVIPerSqft_AllHomes',
            zri_all DECIMAL(12,2) COMMENT 'ZRI_AllHomes',
            zri_per_sqft DECIMAL(10,2) COMMENT 'ZriPerSqft_AllHomes',
            median_listing_price DECIMAL(15,2) COMMENT 'MedianListingPrice_AllHomes',
            median_listing_price_sqft DECIMAL(10,2) COMMENT 'MedianListingPricePerSqft_AllHomes',
            median_rental_price DECIMAL(12,2) COMMENT 'MedianRentalPrice_AllHomes',
            price_to_rent_ratio DECIMAL(8,4) COMMENT 'PriceToRentRatio_AllHomes',
            pct_price_reduction DECIMAL(8,4) COMMENT 'PctOfListingsWithPriceReductions_AllHomes',
            median_pct_price_reduction DECIMAL(8,4) COMMENT 'MedianPctOfPriceReduction_AllHomes',
            pct_homes_increasing DECIMAL(8,4) COMMENT 'PctOfHomesIncreasingInValues_AllHomes',
            pct_homes_decreasing DECIMAL(8,4) COMMENT 'PctOfHomesDecreasingInValues_AllHomes',
            sale_counts INT COMMENT 'Sale_Counts',
            sale_prices DECIMAL(15,2) COMMENT 'Sale_Prices',
            source_file VARCHAR(100),
            INDEX idx_region_date (region_name(100), date),
            INDEX idx_level_date (region_level, date),
            INDEX idx_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-I. 미국 월별 집계 (분석 편의용 — Realtor 기반) ──
    'us_monthly_summary': """
        CREATE TABLE IF NOT EXISTS us_monthly_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_id INT,
            city_name VARCHAR(50),
            state VARCHAR(10),
            year_month VARCHAR(7),
            avg_price DECIMAL(15,2) COMMENT '평균 매물가 USD',
            median_price DECIMAL(15,2) COMMENT '중위 매물가 USD',
            listing_count INT COMMENT '매물 건수',
            avg_house_size DECIMAL(12,2) COMMENT '평균 면적 sqft',
            avg_price_per_sqft DECIMAL(10,2) COMMENT 'sqft당 평균가 USD',
            avg_bed DECIMAL(4,1),
            avg_bath DECIMAL(4,1),
            FOREIGN KEY (city_id) REFERENCES cities(city_id),
            INDEX idx_city_ym (city_name, year_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-J. Crosswalk: CountyCrossWalk_Zillow ──
    'zillow_county_crosswalk': """
        CREATE TABLE IF NOT EXISTS zillow_county_crosswalk (
            id INT AUTO_INCREMENT PRIMARY KEY,
            CountyName VARCHAR(100),
            StateName VARCHAR(50),
            StateFIPS VARCHAR(5),
            CountyFIPS VARCHAR(5),
            FIPS VARCHAR(10),
            MetroName_Zillow VARCHAR(200),
            CBSAName VARCHAR(200),
            CBSACode VARCHAR(10),
            CountyRegionID_Zillow INT,
            MetroRegionID_Zillow INT,
            INDEX idx_metro (MetroName_Zillow(100)),
            INDEX idx_fips (FIPS)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-K. Crosswalk: cities_crosswalk ──
    'zillow_cities_crosswalk': """
        CREATE TABLE IF NOT EXISTS zillow_cities_crosswalk (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Unique_City_ID VARCHAR(200),
            City VARCHAR(100),
            County VARCHAR(100),
            State VARCHAR(10),
            INDEX idx_city (City),
            INDEX idx_state (State)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
}


def create_all_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for table_name, ddl in TABLES.items():
        cursor.execute(ddl)
        print(f"  ✅ {table_name}")
    conn.commit()
    conn.close()
    print("✅ 소주제1 전체 테이블 생성 완료")


if __name__ == '__main__':
    create_database()
    create_all_tables()
    insert_cities()
    print("🎉 STEP 1 완료")
```

---

## 🔨 STEP 2: Zillow Housing (Wide Format) 로딩

### 파일: `src/step2_load_us_zillow_wide.py`

**핵심 로직:** Wide(행=지역, 열=날짜) → Long(행=지역×날짜) 변환 후 MySQL 적재

```python
"""
STEP 2: zillow_Housing Wide Format CSV → Long 변환 → MySQL 적재
실행: python src/step2_load_us_zillow_wide.py

처리 파일:
  - Metro_zhvi_...csv  → us_metro_zhvi
  - Metro_zori_...csv  → us_metro_zori
  - Metro_zhvf_growth_...csv → us_metro_zhvf_growth
  - National_zorf_growth_...csv → us_national_zorf_growth
"""
import pandas as pd
import pymysql
from step0_init_db import get_connection, DB_NAME

# ── 필터 대상 MSA (RegionName 정확히 일치해야 함) ──
# ⚠️ 실행 전 CSV에서 실제 RegionName 을 확인하세요:
#     df = pd.read_csv(파일); print(df['RegionName'].unique())
#     아래 이름이 정확하지 않으면 필터 결과가 0행이 됩니다.
TARGET_METROS = [
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',     # 또는 'Atlanta-Sandy Springs-Alpharetta, GA'
    'Phoenix-Mesa-Chandler, AZ',             # 또는 'Phoenix-Mesa-Scottsdale, AZ'
    'Charlotte-Concord-Gastonia, NC-SC',
    'United States',                          # 전국 기준선
]

# ── 경로 ──
ZILLOW_HOUSING_DIR = 'data/zillow_Housing/'


def check_and_fix_metro_names(csv_path):
    """
    CSV에서 실제 RegionName을 읽어 TARGET_METROS와 매칭 확인.
    매칭 실패 시 후보를 출력하여 수동 수정 가능하게 함.
    """
    df = pd.read_csv(csv_path, nrows=0)  # 열 이름만
    df_full = pd.read_csv(csv_path, usecols=['RegionName'])
    all_names = df_full['RegionName'].unique().tolist()

    matched = [m for m in TARGET_METROS if m in all_names]
    unmatched = [m for m in TARGET_METROS if m not in all_names]

    if unmatched:
        print(f"⚠️  매칭 실패: {unmatched}")
        for um in unmatched:
            keyword = um.split('-')[0].split(',')[0].strip()
            candidates = [n for n in all_names if keyword.lower() in n.lower()]
            print(f"   '{um}' 후보: {candidates[:5]}")
    else:
        print(f"✅ 전체 매칭 성공: {matched}")

    return matched, unmatched


def load_zhvi(csv_path=None):
    """
    ZHVI Wide → us_metro_zhvi Long

    Wide 구조:
        RegionID | SizeRank | RegionName | RegionType | StateName | 2000-01-31 | 2000-02-29 | ...
        102001   | 0        | United States | country | NaN       | 120438.3   | 120889.7   | ...

    Long 변환 결과:
        region_id | size_rank | region_name | region_type | state_name | year_month | zhvi
    """
    if csv_path is None:
        csv_path = f'{ZILLOW_HOUSING_DIR}Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'

    print(f"\n📥 ZHVI 로딩: {csv_path}")

    df = pd.read_csv(csv_path)

    # 식별 열
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    date_cols = [c for c in df.columns if c not in id_cols]

    # 필터
    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()
    print(f"   필터 결과: {len(df_f)}개 MSA")

    if df_f.empty:
        print("   ⚠️ 필터 결과 0행 — TARGET_METROS 이름 확인 필요")
        check_and_fix_metro_names(csv_path)
        return

    # Wide → Long
    df_long = df_f.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name='date_raw',
        value_name='zhvi'
    )
    df_long = df_long.dropna(subset=['zhvi'])
    df_long['year_month'] = df_long['date_raw'].str[:7]

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO us_metro_zhvi
             (region_id, size_rank, region_name, region_type, state_name, year_month, zhvi)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r['RegionID']) else None,
            int(r['SizeRank']) if pd.notna(r['SizeRank']) else None,
            r['RegionName'],
            r.get('RegionType'),
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r['year_month'],
            float(r['zhvi'])
        ))

    # 배치 삽입 (5000행씩)
    batch_size = 5000
    for i in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[i:i+batch_size])
        conn.commit()
        print(f"   ... {min(i+batch_size, len(rows))}/{len(rows)} 삽입")

    conn.close()
    print(f"   ✅ us_metro_zhvi 적재 완료: {len(rows)}행")


def load_zori(csv_path=None):
    """
    ZORI Wide → us_metro_zori Long
    구조 동일 (ZHVI와 같은 Wide Format), 기간: 2015~2025
    """
    if csv_path is None:
        csv_path = f'{ZILLOW_HOUSING_DIR}Metro_zori_uc_sfrcondomfr_sm_month.csv'

    print(f"\n📥 ZORI 로딩: {csv_path}")

    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()
    print(f"   필터 결과: {len(df_f)}개 MSA")

    if df_f.empty:
        check_and_fix_metro_names(csv_path)
        return

    df_long = df_f.melt(id_vars=id_cols, value_vars=date_cols,
                         var_name='date_raw', value_name='zori')
    df_long = df_long.dropna(subset=['zori'])
    df_long['year_month'] = df_long['date_raw'].str[:7]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO us_metro_zori
             (region_id, size_rank, region_name, region_type, state_name, year_month, zori)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r['RegionID']) else None,
            int(r['SizeRank']) if pd.notna(r['SizeRank']) else None,
            r['RegionName'], r.get('RegionType'),
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r['year_month'], float(r['zori'])
        ))

    batch_size = 5000
    for i in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[i:i+batch_size])
        conn.commit()
    conn.close()
    print(f"   ✅ us_metro_zori 적재 완료: {len(rows)}행")


def load_zhvf_growth(csv_path=None):
    """
    ZHVF Growth Wide → us_metro_zhvf_growth Long

    이 파일만 특수 구조:
        RegionID | SizeRank | RegionName | RegionType | StateName | BaseDate | 2026-01-31 | 2026-02-28 | ...

    BaseDate = 예측 기준일, 이후 열 = 예측 대상 날짜, 셀 값 = 누적 성장률 %
    """
    if csv_path is None:
        csv_path = f'{ZILLOW_HOUSING_DIR}Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'

    print(f"\n📥 ZHVF Growth 로딩: {csv_path}")

    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()

    if df_f.empty:
        print("   ⚠️ 필터 결과 0행")
        return

    df_long = df_f.melt(id_vars=id_cols, value_vars=date_cols,
                         var_name='forecast_date', value_name='growth_rate')
    df_long = df_long.dropna(subset=['growth_rate'])

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO us_metro_zhvf_growth
             (region_id, region_name, region_type, state_name, base_date, forecast_date, growth_rate)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r['RegionID']) else None,
            r['RegionName'], r.get('RegionType'),
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r.get('BaseDate'), r['forecast_date'], float(r['growth_rate'])
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ us_metro_zhvf_growth 적재 완료: {len(rows)}행")


def load_zorf_growth(csv_path=None):
    """
    National ZORF Growth (전국 1행짜리) → us_national_zorf_growth
    """
    if csv_path is None:
        csv_path = f'{ZILLOW_HOUSING_DIR}National_zorf_growth_uc_sfr_sm_month.csv'

    print(f"\n📥 National ZORF Growth 로딩: {csv_path}")

    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    id_cols = [c for c in id_cols if c in df.columns]
    date_cols = [c for c in df.columns if c not in id_cols]

    df_long = df.melt(id_vars=id_cols, value_vars=date_cols,
                       var_name='forecast_date', value_name='growth_rate')
    df_long = df_long.dropna(subset=['growth_rate'])

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO us_national_zorf_growth
             (region_id, region_name, base_date, forecast_date, growth_rate)
             VALUES (%s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r.get('RegionID')) else None,
            r.get('RegionName', 'United States'),
            r.get('BaseDate'), r['forecast_date'], float(r['growth_rate'])
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ us_national_zorf_growth 적재 완료: {len(rows)}행")


if __name__ == '__main__':
    load_zhvi()
    load_zori()
    load_zhvf_growth()
    load_zorf_growth()
    print("\n🎉 STEP 2 완료: Zillow Housing Wide → Long 적재")
```

---

## 🔨 STEP 3: Zillow Economics (Long Format) 로딩

### 파일: `src/step3_load_us_zillow_economics.py`

**핵심:** 대용량 Long Format 파일에서 **필요한 지역 + 필요한 열만** 청크 단위로 필터 적재

```python
"""
STEP 3: Zillow Economics Long Format 시계열 → MySQL 적재
실행: python src/step3_load_us_zillow_economics.py

처리 파일:
  - Metro_time_series.csv  (56MB)  → zillow_economics_ts (region_level='metro')
  - State_time_series.csv  (4.7MB) → zillow_economics_ts (region_level='state')
  - City_time_series.csv   (689MB) → zillow_economics_ts (region_level='city')
  + Crosswalk 테이블 2개
"""
import pandas as pd
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

ZILLOW_ECONOMICS_DIR = 'data/Zillow_Economics/'

# ── 소주제1 핵심 지표 열 ──
SELECTED_COLS = [
    'Date', 'RegionName',
    'ZHVI_AllHomes', 'ZHVI_SingleFamilyResidence', 'ZHVI_CondoCoop',
    'ZHVIPerSqft_AllHomes',
    'ZRI_AllHomes', 'ZriPerSqft_AllHomes',
    'MedianListingPrice_AllHomes', 'MedianListingPricePerSqft_AllHomes',
    'MedianRentalPrice_AllHomes',
    'PriceToRentRatio_AllHomes',
    'PctOfListingsWithPriceReductions_AllHomes',
    'MedianPctOfPriceReduction_AllHomes',
    'PctOfHomesIncreasingInValues_AllHomes',
    'PctOfHomesDecreasingInValues_AllHomes',
    'Sale_Counts', 'Sale_Prices',
]

# ── 지역 필터 ──
# Metro_time_series: RegionName = MSA 코드 (예: '19100', '12060')
# → CountyCrossWalk에서 Dallas 등의 MetroRegionID_Zillow 또는 CBSACode를 확인 필요
# → 또는 전체 로딩 후 Crosswalk JOIN
#
# State_time_series: RegionName = 주 이름 (예: 'Texas')
TARGET_STATES = ['Texas', 'Georgia', 'Arizona', 'North Carolina']
#
# City_time_series: RegionName = 도시 식별자 (예: 'dallasdallasstx')
# → cities_crosswalk.csv의 Unique_City_ID 형식
# → 사전에 확인 필요. 아래는 예시:
TARGET_CITIES_APPROX = ['dallas', 'atlanta', 'phoenix', 'charlotte']


def load_crosswalk_county():
    """CountyCrossWalk_Zillow.csv → zillow_county_crosswalk"""
    csv_path = f'{ZILLOW_ECONOMICS_DIR}CountyCrossWalk_Zillow.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 County Crosswalk 로딩: {csv_path}")
    df = pd.read_csv(csv_path)
    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO zillow_county_crosswalk
             (CountyName, StateName, StateFIPS, CountyFIPS, FIPS,
              MetroName_Zillow, CBSAName, CBSACode,
              CountyRegionID_Zillow, MetroRegionID_Zillow)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = [tuple(r) for r in df[['CountyName','StateName','StateFIPS','CountyFIPS',
                                   'FIPS','MetroName_Zillow','CBSAName','CBSACode',
                                   'CountyRegionID_Zillow','MetroRegionID_Zillow']].values]

    batch = 1000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
    conn.close()
    print(f"   ✅ zillow_county_crosswalk 적재: {len(rows)}행")

    # Dallas 등의 Metro RegionID 확인 출력
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT MetroName_Zillow, MetroRegionID_Zillow, CBSACode
        FROM zillow_county_crosswalk
        WHERE MetroName_Zillow LIKE '%Dallas%'
           OR MetroName_Zillow LIKE '%Atlanta%'
           OR MetroName_Zillow LIKE '%Phoenix%'
           OR MetroName_Zillow LIKE '%Charlotte%'
    """)
    results = cursor.fetchall()
    print("\n   🔍 타겟 MSA 매핑 확인:")
    for row in results:
        print(f"      {row}")
    conn.close()


def load_crosswalk_cities():
    """cities_crosswalk.csv → zillow_cities_crosswalk"""
    csv_path = f'{ZILLOW_ECONOMICS_DIR}cities_crosswalk.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 Cities Crosswalk 로딩: {csv_path}")
    df = pd.read_csv(csv_path)
    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO zillow_cities_crosswalk
             (Unique_City_ID, City, County, State)
             VALUES (%s,%s,%s,%s)"""

    rows = [tuple(r) for r in df[['Unique_City_ID','City','County','State']].values]
    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
    conn.close()
    print(f"   ✅ zillow_cities_crosswalk 적재: {len(rows)}행")

    # 타겟 도시 ID 확인
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for city in TARGET_CITIES_APPROX:
        cursor.execute(f"SELECT Unique_City_ID, City, State FROM zillow_cities_crosswalk "
                       f"WHERE City LIKE '%{city}%' LIMIT 5")
        print(f"   🔍 '{city}' 매칭: {cursor.fetchall()}")
    conn.close()


def load_state_timeseries():
    """
    State_time_series.csv → zillow_economics_ts (region_level='state')
    4.7MB → TX/GA/AZ/NC 4개 주만 필터
    """
    csv_path = f'{ZILLOW_ECONOMICS_DIR}State_time_series.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 State 시계열 로딩: {csv_path}")

    # 열 이름 사전 확인
    df_sample = pd.read_csv(csv_path, nrows=5)
    available_cols = [c for c in SELECTED_COLS if c in df_sample.columns]
    print(f"   사용 가능 열: {len(available_cols)}/{len(SELECTED_COLS)}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in available_cols,
                              chunksize=10000):
        chunk = chunk[chunk['RegionName'].isin(TARGET_STATES)]
        if chunk.empty:
            continue
        chunk = chunk.where(pd.notnull(chunk), None)

        sql = """INSERT INTO zillow_economics_ts
                 (date, region_name, region_level,
                  zhvi_all, zhvi_sfr, zhvi_condo, zhvi_per_sqft,
                  zri_all, zri_per_sqft,
                  median_listing_price, median_listing_price_sqft,
                  median_rental_price, price_to_rent_ratio,
                  pct_price_reduction, median_pct_price_reduction,
                  pct_homes_increasing, pct_homes_decreasing,
                  sale_counts, sale_prices, source_file)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            rows.append((
                r.get('Date'), r['RegionName'], 'state',
                r.get('ZHVI_AllHomes'), r.get('ZHVI_SingleFamilyResidence'),
                r.get('ZHVI_CondoCoop'), r.get('ZHVIPerSqft_AllHomes'),
                r.get('ZRI_AllHomes'), r.get('ZriPerSqft_AllHomes'),
                r.get('MedianListingPrice_AllHomes'),
                r.get('MedianListingPricePerSqft_AllHomes'),
                r.get('MedianRentalPrice_AllHomes'),
                r.get('PriceToRentRatio_AllHomes'),
                r.get('PctOfListingsWithPriceReductions_AllHomes'),
                r.get('MedianPctOfPriceReduction_AllHomes'),
                r.get('PctOfHomesIncreasingInValues_AllHomes'),
                r.get('PctOfHomesDecreasingInValues_AllHomes'),
                r.get('Sale_Counts'), r.get('Sale_Prices'),
                'State_time_series.csv'
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ State 시계열 적재 완료: {total}행")


def load_metro_timeseries():
    """
    Metro_time_series.csv → zillow_economics_ts (region_level='metro')
    56MB — Crosswalk의 MetroRegionID를 RegionName으로 사용
    ⚠️ RegionName이 MSA 코드(숫자)임. Crosswalk JOIN으로 도시 매핑 필요.
    → 일단 전체 로딩 후, SQL JOIN으로 분석 시 필터.
    → 또는 사전에 타겟 MSA 코드를 확인하여 필터 가능.
    """
    csv_path = f'{ZILLOW_ECONOMICS_DIR}Metro_time_series.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 Metro 시계열 로딩: {csv_path}")
    print("   ⚠️ 56MB 파일 — 타겟 MSA 코드 사전 확인 권장")

    # 타겟 MSA 코드 조회 (Crosswalk 적재 후)
    target_codes = get_target_metro_codes()
    if not target_codes:
        print("   ℹ️ Crosswalk 미적재 → 전체 로딩 (시간 소요)")

    df_sample = pd.read_csv(csv_path, nrows=5)
    available_cols = [c for c in SELECTED_COLS if c in df_sample.columns]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in available_cols,
                              chunksize=10000):
        if target_codes:
            chunk = chunk[chunk['RegionName'].isin(target_codes)]
        if chunk.empty:
            continue
        chunk = chunk.where(pd.notnull(chunk), None)

        sql = """INSERT INTO zillow_economics_ts
                 (date, region_name, region_level,
                  zhvi_all, zhvi_sfr, zhvi_condo, zhvi_per_sqft,
                  zri_all, zri_per_sqft,
                  median_listing_price, median_listing_price_sqft,
                  median_rental_price, price_to_rent_ratio,
                  pct_price_reduction, median_pct_price_reduction,
                  pct_homes_increasing, pct_homes_decreasing,
                  sale_counts, sale_prices, source_file)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            rows.append((
                r.get('Date'), str(r['RegionName']), 'metro',
                r.get('ZHVI_AllHomes'), r.get('ZHVI_SingleFamilyResidence'),
                r.get('ZHVI_CondoCoop'), r.get('ZHVIPerSqft_AllHomes'),
                r.get('ZRI_AllHomes'), r.get('ZriPerSqft_AllHomes'),
                r.get('MedianListingPrice_AllHomes'),
                r.get('MedianListingPricePerSqft_AllHomes'),
                r.get('MedianRentalPrice_AllHomes'),
                r.get('PriceToRentRatio_AllHomes'),
                r.get('PctOfListingsWithPriceReductions_AllHomes'),
                r.get('MedianPctOfPriceReduction_AllHomes'),
                r.get('PctOfHomesIncreasingInValues_AllHomes'),
                r.get('PctOfHomesDecreasingInValues_AllHomes'),
                r.get('Sale_Counts'), r.get('Sale_Prices'),
                'Metro_time_series.csv'
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        if total % 50000 == 0:
            print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ Metro 시계열 적재 완료: {total}행")


def load_city_timeseries():
    """
    City_time_series.csv → zillow_economics_ts (region_level='city')
    ⚠️ 689MB 대용량 — 반드시 타겟 도시 필터링 필요!
    RegionName = 도시식별자 (예: 'dallasdallasstx')
    → cities_crosswalk에서 사전 확인 후 필터 리스트 설정
    """
    csv_path = f'{ZILLOW_ECONOMICS_DIR}City_time_series.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 City 시계열 로딩: {csv_path}")
    print("   ⚠️ 689MB 대용량 — 타겟 도시 필터 적용")

    # 타겟 도시 ID 조회
    target_city_ids = get_target_city_ids()
    if not target_city_ids:
        print("   ❌ Crosswalk 미적재 또는 타겟 도시 없음 — 스킵")
        print("   → 먼저 load_crosswalk_cities()를 실행하세요")
        return

    print(f"   필터 대상: {target_city_ids}")

    df_sample = pd.read_csv(csv_path, nrows=5)
    available_cols = [c for c in SELECTED_COLS if c in df_sample.columns]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in available_cols,
                              chunksize=20000):
        chunk = chunk[chunk['RegionName'].isin(target_city_ids)]
        if chunk.empty:
            continue
        chunk = chunk.where(pd.notnull(chunk), None)

        sql = """INSERT INTO zillow_economics_ts
                 (date, region_name, region_level,
                  zhvi_all, zhvi_sfr, zhvi_condo, zhvi_per_sqft,
                  zri_all, zri_per_sqft,
                  median_listing_price, median_listing_price_sqft,
                  median_rental_price, price_to_rent_ratio,
                  pct_price_reduction, median_pct_price_reduction,
                  pct_homes_increasing, pct_homes_decreasing,
                  sale_counts, sale_prices, source_file)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            rows.append((
                r.get('Date'), r['RegionName'], 'city',
                r.get('ZHVI_AllHomes'), r.get('ZHVI_SingleFamilyResidence'),
                r.get('ZHVI_CondoCoop'), r.get('ZHVIPerSqft_AllHomes'),
                r.get('ZRI_AllHomes'), r.get('ZriPerSqft_AllHomes'),
                r.get('MedianListingPrice_AllHomes'),
                r.get('MedianListingPricePerSqft_AllHomes'),
                r.get('MedianRentalPrice_AllHomes'),
                r.get('PriceToRentRatio_AllHomes'),
                r.get('PctOfListingsWithPriceReductions_AllHomes'),
                r.get('MedianPctOfPriceReduction_AllHomes'),
                r.get('PctOfHomesIncreasingInValues_AllHomes'),
                r.get('PctOfHomesDecreasingInValues_AllHomes'),
                r.get('Sale_Counts'), r.get('Sale_Prices'),
                'City_time_series.csv'
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        if total % 10000 == 0:
            print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ City 시계열 적재 완료: {total}행")


# ── 헬퍼: 타겟 MSA 코드 조회 ──
def get_target_metro_codes():
    """Crosswalk에서 Dallas/Atlanta/Phoenix/Charlotte의 MSA 코드(RegionName) 반환"""
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT CAST(MetroRegionID_Zillow AS CHAR) AS code
            FROM zillow_county_crosswalk
            WHERE MetroName_Zillow LIKE '%Dallas%'
               OR MetroName_Zillow LIKE '%Atlanta%'
               OR MetroName_Zillow LIKE '%Phoenix%'
               OR MetroName_Zillow LIKE '%Charlotte%'
        """)
        codes = [r['code'] for r in cursor.fetchall() if r['code']]
        conn.close()
        # CBSACode도 추가
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT CBSACode
            FROM zillow_county_crosswalk
            WHERE MetroName_Zillow LIKE '%Dallas%'
               OR MetroName_Zillow LIKE '%Atlanta%'
               OR MetroName_Zillow LIKE '%Phoenix%'
               OR MetroName_Zillow LIKE '%Charlotte%'
        """)
        cbsa = [r['CBSACode'] for r in cursor.fetchall() if r['CBSACode']]
        conn.close()
        return list(set(codes + cbsa))
    except Exception:
        return []


def get_target_city_ids():
    """Crosswalk에서 Dallas/Atlanta/Phoenix/Charlotte의 Unique_City_ID 반환"""
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Unique_City_ID
            FROM zillow_cities_crosswalk
            WHERE City IN ('Dallas', 'Atlanta', 'Phoenix', 'Charlotte')
        """)
        ids = [r['Unique_City_ID'] for r in cursor.fetchall() if r['Unique_City_ID']]
        conn.close()
        return ids
    except Exception:
        return []


if __name__ == '__main__':
    # 순서 중요: Crosswalk 먼저 → 시계열 로딩 시 필터에 활용
    load_crosswalk_county()
    load_crosswalk_cities()
    load_state_timeseries()
    load_metro_timeseries()
    load_city_timeseries()        # 대용량 주의
    print("\n🎉 STEP 3 완료: Zillow Economics 시계열 적재")
```

---

## 🔨 STEP 4: Realtor.com 매물 데이터 로딩

### 파일: `src/step4_load_us_realtor.py`

```python
"""
STEP 4: realtor-data.zip.csv → us_realtor_listings + us_monthly_summary
실행: python src/step4_load_us_realtor.py

원본 구조:
  brokered_by | status | price | bed | bath | acre_lot | street | city | state | zip_code | house_size | prev_sold_date

⚠️ 178MB / 222만행 — 4개 주(TX, GA, AZ, NC) 필터 적용
"""
import pandas as pd
import numpy as np
import pymysql
from step0_init_db import get_connection, DB_NAME

REALTOR_PATH = 'data/realtor-data.zip.csv'

# state 열 값이 약어인지 풀네임인지 사전 확인 필요
# → head로 확인: pd.read_csv(REALTOR_PATH, nrows=5)['state'].unique()
# 아래는 풀네임 기준. 약어면 {'TX','GA','AZ','NC'}로 변경
TARGET_STATES_FULL = {
    'Texas', 'Georgia', 'Arizona', 'North Carolina',
    # 약어 버전도 추가 (안전장치)
    'TX', 'GA', 'AZ', 'NC',
}

# city_id 매핑 (cities 테이블 기준)
CITY_ID_MAP = {
    # (state, city_keyword) → city_id
    ('TX', 'dallas'): 2, ('Texas', 'dallas'): 2,
    ('GA', 'atlanta'): 3, ('Georgia', 'atlanta'): 3,
    ('AZ', 'phoenix'): 4, ('Arizona', 'phoenix'): 4,
    ('NC', 'charlotte'): 5, ('North Carolina', 'charlotte'): 5,
}


def resolve_city_id(state, city):
    """state + city로 city_id 매핑. 매칭 안되면 None"""
    if not city or not state:
        return None
    city_lower = str(city).lower().strip()
    state_str = str(state).strip()
    for (st, kw), cid in CITY_ID_MAP.items():
        if state_str == st and kw in city_lower:
            return cid
    return None


def load_realtor_listings():
    """개별 매물 적재 (4개 주 필터)"""
    print(f"\n📥 Realtor.com 매물 로딩: {REALTOR_PATH}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0
    filtered = 0

    for chunk in pd.read_csv(REALTOR_PATH, chunksize=10000, low_memory=False):
        # 주 필터
        chunk = chunk[chunk['state'].isin(TARGET_STATES_FULL)]
        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        sql = """INSERT INTO us_realtor_listings
                 (city_id, brokered_by, status, price, bed, bath,
                  acre_lot, street, city, state, zip_code, house_size, prev_sold_date)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            cid = resolve_city_id(r.get('state'), r.get('city'))
            rows.append((
                cid,
                r.get('brokered_by'),
                r.get('status'),
                r.get('price'),
                int(r['bed']) if pd.notna(r.get('bed')) else None,
                int(r['bath']) if pd.notna(r.get('bath')) else None,
                r.get('acre_lot'),
                r.get('street'),
                r.get('city'),
                r.get('state'),
                str(int(r['zip_code'])) if pd.notna(r.get('zip_code')) else None,
                r.get('house_size'),
                r.get('prev_sold_date'),
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        if total % 50000 == 0:
            print(f"   ... {total}행 삽입")

    conn.close()
    print(f"   ✅ us_realtor_listings 적재 완료: {total}행")


def build_us_monthly_summary():
    """
    us_realtor_listings에서 도시별 월별 요약 집계 → us_monthly_summary
    ⚠️ prev_sold_date로 year_month 추출. 없으면 집계 불가 → status='for_sale' 기준으로 대체
    """
    print("\n📊 US 월별 요약 집계 생성")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # prev_sold_date 기반 year_month 추출이 가능한지 확인
    cursor.execute("""
        SELECT prev_sold_date, COUNT(*) as cnt
        FROM us_realtor_listings
        WHERE prev_sold_date IS NOT NULL
        LIMIT 5
    """)
    samples = cursor.fetchall()
    print(f"   prev_sold_date 샘플: {samples}")

    # prev_sold_date가 있는 경우 → year_month 기반 집계
    # 없는 경우 → 도시별 전체 집계만 가능
    sql_insert = """
        INSERT INTO us_monthly_summary
        (city_id, city_name, state, year_month,
         avg_price, median_price, listing_count,
         avg_house_size, avg_price_per_sqft, avg_bed, avg_bath)
        SELECT
            city_id,
            city,
            state,
            LEFT(prev_sold_date, 7) AS year_month,
            ROUND(AVG(price), 2),
            ROUND((SELECT price FROM us_realtor_listings sub
                    WHERE sub.city = main.city AND sub.state = main.state
                    AND LEFT(sub.prev_sold_date, 7) = LEFT(main.prev_sold_date, 7)
                    AND sub.price IS NOT NULL
                    ORDER BY price LIMIT 1 OFFSET
                    (SELECT FLOOR(COUNT(*)/2) FROM us_realtor_listings sub2
                     WHERE sub2.city = main.city AND sub2.state = main.state
                     AND LEFT(sub2.prev_sold_date, 7) = LEFT(main.prev_sold_date, 7)
                     AND sub2.price IS NOT NULL)), 2),
            COUNT(*),
            ROUND(AVG(house_size), 2),
            ROUND(AVG(CASE WHEN house_size > 0 THEN price / house_size END), 2),
            ROUND(AVG(bed), 1),
            ROUND(AVG(bath), 1)
        FROM us_realtor_listings main
        WHERE prev_sold_date IS NOT NULL
          AND city_id IS NOT NULL
          AND price IS NOT NULL
          AND price > 0
        GROUP BY city_id, city, state, LEFT(prev_sold_date, 7)
    """

    # 위 중위값 서브쿼리는 MySQL에서 느릴 수 있으므로 Python 집계 대안 사용
    print("   → Python pandas 기반 집계로 전환 (MySQL 중위값 한계)")

    df = pd.read_sql("""
        SELECT city_id, city, state, prev_sold_date, price, house_size, bed, bath
        FROM us_realtor_listings
        WHERE city_id IS NOT NULL AND price IS NOT NULL AND price > 0
          AND prev_sold_date IS NOT NULL
    """, conn)

    if df.empty:
        print("   ⚠️ 집계 대상 0행 — prev_sold_date 미존재 가능")
        conn.close()
        return

    df['year_month'] = df['prev_sold_date'].str[:7]

    grouped = df.groupby(['city_id', 'city', 'state', 'year_month']).agg(
        avg_price=('price', 'mean'),
        median_price=('price', 'median'),
        listing_count=('price', 'count'),
        avg_house_size=('house_size', 'mean'),
        avg_bed=('bed', 'mean'),
        avg_bath=('bath', 'mean'),
    ).reset_index()

    grouped['avg_price_per_sqft'] = np.where(
        grouped['avg_house_size'] > 0,
        grouped['avg_price'] / grouped['avg_house_size'],
        None
    )

    cursor2 = conn.cursor()
    sql = """INSERT INTO us_monthly_summary
             (city_id, city_name, state, year_month,
              avg_price, median_price, listing_count,
              avg_house_size, avg_price_per_sqft, avg_bed, avg_bath)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in grouped.iterrows():
        rows.append((
            int(r['city_id']), r['city'], r['state'], r['year_month'],
            round(r['avg_price'], 2) if pd.notna(r['avg_price']) else None,
            round(r['median_price'], 2) if pd.notna(r['median_price']) else None,
            int(r['listing_count']),
            round(r['avg_house_size'], 2) if pd.notna(r['avg_house_size']) else None,
            round(r['avg_price_per_sqft'], 2) if pd.notna(r['avg_price_per_sqft']) else None,
            round(r['avg_bed'], 1) if pd.notna(r['avg_bed']) else None,
            round(r['avg_bath'], 1) if pd.notna(r['avg_bath']) else None,
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor2.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   ✅ us_monthly_summary 집계 완료: {len(rows)}행")


if __name__ == '__main__':
    load_realtor_listings()
    build_us_monthly_summary()
    print("\n🎉 STEP 4 완료: Realtor.com 적재 + 월별 요약")
```

---

## 🔨 STEP 5: 대구 주택 데이터 (Kaggle) 로딩

### 파일: `src/step5_load_kr_daegu.py`

```python
"""
STEP 5: Kaggle 대구 주택 데이터 → daegu_housing_prices + daegu_monthly_summary
실행: python src/step5_load_kr_daegu.py

⚠️ Kaggle 파일의 실제 열 이름은 다운로드 후 반드시 확인!
    pd.read_csv('파일', nrows=3, encoding='cp949').columns.tolist()
    한글 열명 / 영문 열명 모두 가능 → 아래 매핑 딕셔너리에서 조정
"""
import pandas as pd
import numpy as np
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

# ── K1-1: Daegu Apartment Actual Transaction ──
# ⚠️ 열 이름 예상 (실제와 다를 수 있음 — 반드시 확인)
K1_1_COL_MAP = {
    # '원본 열명': '타겟 열명'
    # 한글 버전 (예시)
    '시군구': 'district',       # 또는 '구'
    '단지명': 'apt_name',       # 또는 '아파트'
    '전용면적': 'exclusive_area',  # 또는 '전용면적(㎡)'
    '거래금액': 'deal_amount',    # 만원 단위
    '층': 'floor',
    '건축년도': 'build_year',
    '년': 'year',
    '월': 'month',
    '일': 'day',
    '거래유형': 'deal_type',
    '동': 'dong',

    # 영문 버전 (예시)
    'district': 'district',
    'apt_name': 'apt_name',
    'exclusive_area': 'exclusive_area',
    'deal_amount': 'deal_amount',
    'floor': 'floor',
    'build_year': 'build_year',
    'year': 'year',
    'month': 'month',
    'day': 'day',
    'deal_type': 'deal_type',
    'dong': 'dong',
}


def detect_and_load_daegu(csv_path, source_name, encoding='utf-8'):
    """
    대구 CSV 파일을 자동 감지하여 로딩.
    1. 열 이름 확인
    2. 매핑 적용
    3. daegu_housing_prices에 적재
    """
    # 인코딩 자동 시도
    for enc in [encoding, 'cp949', 'euc-kr', 'utf-8-sig']:
        try:
            df = pd.read_csv(csv_path, nrows=3, encoding=enc)
            encoding = enc
            break
        except Exception:
            continue
    else:
        print(f"   ❌ 인코딩 감지 실패: {csv_path}")
        return

    print(f"\n📥 대구 데이터 로딩: {csv_path} (encoding={encoding})")
    print(f"   원본 열: {df.columns.tolist()}")

    df = pd.read_csv(csv_path, encoding=encoding, low_memory=False)

    # 열 매핑 시도
    col_map = {}
    for orig_col in df.columns:
        normalized = orig_col.strip()
        if normalized in K1_1_COL_MAP:
            col_map[normalized] = K1_1_COL_MAP[normalized]

    if col_map:
        df = df.rename(columns=col_map)
    print(f"   매핑 후 열: {df.columns.tolist()}")

    # ── year_month 생성 ──
    if 'year' in df.columns and 'month' in df.columns:
        df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
        if 'day' in df.columns:
            df['deal_date'] = pd.to_datetime(
                df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2) + '-' + df['day'].astype(str).str.zfill(2),
                errors='coerce'
            )
        else:
            df['deal_date'] = None
    elif '계약년월' in df.columns:
        df['year_month'] = df['계약년월'].astype(str).str[:4] + '-' + df['계약년월'].astype(str).str[4:6]
        df['deal_date'] = None
    else:
        print("   ⚠️ 날짜 열 감지 실패 — year_month=None으로 진행")
        df['year_month'] = None
        df['deal_date'] = None

    # ── 거래금액 정리 (쉼표 제거, 정수 변환) ──
    if 'deal_amount' in df.columns:
        df['deal_amount'] = (
            df['deal_amount']
            .astype(str)
            .str.replace(',', '')
            .str.strip()
        )
        df['deal_amount'] = pd.to_numeric(df['deal_amount'], errors='coerce')

    # ── district 정리: '대구광역시 수성구' → '수성구' ──
    if 'district' in df.columns:
        df['district'] = df['district'].astype(str).str.extract(r'([가-힣]+구|[가-힣]+군)')[0]

    df = df.where(pd.notnull(df), None)

    # ── MySQL 적재 ──
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO daegu_housing_prices
             (year_month, district, dong, apt_name, exclusive_area,
              deal_amount, floor, build_year, deal_date, deal_type, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            r.get('year_month'),
            r.get('district'),
            r.get('dong'),
            r.get('apt_name'),
            r.get('exclusive_area'),
            int(r['deal_amount']) if pd.notna(r.get('deal_amount')) else None,
            int(r['floor']) if pd.notna(r.get('floor')) else None,
            int(r['build_year']) if pd.notna(r.get('build_year')) else None,
            str(r['deal_date'])[:10] if pd.notna(r.get('deal_date')) else None,
            r.get('deal_type'),
            source_name,
        ))

    batch = 5000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
        print(f"   ... {min(i+batch, len(rows))}/{len(rows)}")

    conn.close()
    print(f"   ✅ daegu_housing_prices 적재: {len(rows)}행 ({source_name})")


def build_daegu_monthly_summary():
    """daegu_housing_prices → daegu_monthly_summary 집계"""
    print("\n📊 대구 월별 요약 집계")

    conn = get_connection(DB_NAME)

    df = pd.read_sql("""
        SELECT year_month, district, deal_amount, exclusive_area
        FROM daegu_housing_prices
        WHERE deal_amount IS NOT NULL AND deal_amount > 0
          AND year_month IS NOT NULL
    """, conn)

    if df.empty:
        print("   ⚠️ 집계 대상 0행")
        conn.close()
        return

    df['price_per_m2'] = np.where(
        df['exclusive_area'] > 0,
        df['deal_amount'] / df['exclusive_area'],
        None
    )

    grouped = df.groupby(['year_month', 'district']).agg(
        avg_price=('deal_amount', 'mean'),
        median_price=('deal_amount', 'median'),
        min_price=('deal_amount', 'min'),
        max_price=('deal_amount', 'max'),
        transaction_count=('deal_amount', 'count'),
        avg_area=('exclusive_area', 'mean'),
        avg_price_per_m2=('price_per_m2', 'mean'),
    ).reset_index()

    # YoY 변동률 계산
    grouped['year'] = grouped['year_month'].str[:4].astype(int)
    grouped['month'] = grouped['year_month'].str[5:7].astype(int)
    grouped = grouped.sort_values(['district', 'year_month'])

    # 전년동기 매칭
    grouped['prev_ym'] = (grouped['year'] - 1).astype(str) + '-' + grouped['month'].astype(str).str.zfill(2)
    prev_map = grouped.set_index(['district', 'year_month'])['avg_price'].to_dict()
    grouped['prev_price'] = grouped.apply(
        lambda r: prev_map.get((r['district'], r['prev_ym'])), axis=1
    )
    grouped['yoy_change_rate'] = np.where(
        grouped['prev_price'] > 0,
        (grouped['avg_price'] - grouped['prev_price']) / grouped['prev_price'],
        None
    )

    cursor = conn.cursor()
    sql = """INSERT INTO daegu_monthly_summary
             (year_month, district, avg_price, median_price, min_price, max_price,
              transaction_count, avg_area, avg_price_per_m2, yoy_change_rate)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in grouped.iterrows():
        rows.append((
            r['year_month'], r['district'],
            int(r['avg_price']), int(r['median_price']),
            int(r['min_price']), int(r['max_price']),
            int(r['transaction_count']),
            round(r['avg_area'], 2) if pd.notna(r['avg_area']) else None,
            round(r['avg_price_per_m2'], 2) if pd.notna(r['avg_price_per_m2']) else None,
            round(r['yoy_change_rate'], 4) if pd.notna(r['yoy_change_rate']) else None,
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ daegu_monthly_summary 집계 완료: {len(rows)}행")


if __name__ == '__main__':
    # 파일 존재 확인 후 로딩
    kaggle_files = {
        'daegu_apartment_transaction.csv': 'K1-1 Daegu Apt Transaction',
        'daegu_real_estate.csv': 'K1-2 Daegu Real Estate',
        'korean_apartment_deal.csv': 'K1-3 Korean Apt Deal (대구 필터)',
        'korea_house_data.csv': 'K1-4 Korea House Data',
    }

    print("📂 Kaggle 파일 확인:")
    for fname, desc in kaggle_files.items():
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            print(f"   ✅ {fname} 발견")
            detect_and_load_daegu(path, desc)
        else:
            print(f"   ⚠️ {fname} 미발견 — 스킵")
            print(f"      실제 파일명 확인: {os.listdir(KAGGLE_DIR) if os.path.isdir(KAGGLE_DIR) else 'kaggle_data/ 폴더 없음'}")

    build_daegu_monthly_summary()
    print("\n🎉 STEP 5 완료: 대구 데이터 적재 + 월별 요약")
```

---

## 🔨 STEP 6: 분석 쿼리

### 파일: `src/step6_analysis_queries.py`

```python
"""
STEP 6: 소주제1 분석 SQL 쿼리 모음
실행: python src/step6_analysis_queries.py
"""
import pandas as pd
import pymysql
from step0_init_db import get_connection, DB_NAME


def query_to_df(sql):
    """SQL → DataFrame"""
    conn = get_connection(DB_NAME)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============================================================
# Q1: ZHVI 장기 추이 (2000~2025) — 4개 MSA + 전국
# ============================================================
Q1_ZHVI_TREND = """
SELECT
    year_month,
    region_name,
    zhvi
FROM us_metro_zhvi
WHERE region_name IN (
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',
    'Phoenix-Mesa-Chandler, AZ',
    'Charlotte-Concord-Gastonia, NC-SC',
    'United States'
)
ORDER BY region_name, year_month
"""

# ============================================================
# Q2: ZHVI 전년동기 대비 변동률 (YoY%)
# ============================================================
Q2_ZHVI_YOY = """
SELECT
    a.year_month,
    a.region_name,
    a.zhvi AS current_zhvi,
    b.zhvi AS prev_year_zhvi,
    ROUND((a.zhvi - b.zhvi) / b.zhvi * 100, 2) AS yoy_pct
FROM us_metro_zhvi a
LEFT JOIN us_metro_zhvi b
    ON a.region_name = b.region_name
    AND CONCAT(CAST(SUBSTRING(a.year_month, 1, 4) AS UNSIGNED) - 1,
               SUBSTRING(a.year_month, 5)) = b.year_month
WHERE a.region_name != 'United States'
  AND b.zhvi IS NOT NULL
ORDER BY a.region_name, a.year_month
"""

# ============================================================
# Q3: ZORI 임대료 추이 (2015~2025)
# ============================================================
Q3_ZORI_TREND = """
SELECT
    year_month,
    region_name,
    zori
FROM us_metro_zori
WHERE region_name IN (
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',
    'Phoenix-Mesa-Chandler, AZ',
    'Charlotte-Concord-Gastonia, NC-SC',
    'United States'
)
ORDER BY region_name, year_month
"""

# ============================================================
# Q4: PriceToRentRatio 비교 (Zillow Economics)
# ============================================================
Q4_PRICE_TO_RENT = """
SELECT
    date,
    region_name,
    region_level,
    price_to_rent_ratio,
    zhvi_all,
    zri_all
FROM zillow_economics_ts
WHERE region_level = 'state'
  AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
  AND price_to_rent_ratio IS NOT NULL
ORDER BY region_name, date
"""

# ============================================================
# Q5: 대구 구별 평균가 추이
# ============================================================
Q5_DAEGU_DISTRICT = """
SELECT
    year_month,
    district,
    avg_price,
    median_price,
    transaction_count,
    avg_price_per_m2,
    yoy_change_rate
FROM daegu_monthly_summary
ORDER BY district, year_month
"""

# ============================================================
# Q6: 대구 vs 미국 4도시 — 가격 변동률 비교 (정규화)
# 대구는 만원 → USD 환산 또는 지수화 비교
# ============================================================
Q6_CROSS_COMPARISON = """
-- 대구 연도별 중위가
SELECT
    LEFT(year_month, 4) AS year,
    '대구' AS city,
    ROUND(AVG(median_price)) AS annual_median_price,
    'KRW_10K' AS currency
FROM daegu_monthly_summary
WHERE district IS NOT NULL
GROUP BY LEFT(year_month, 4)

UNION ALL

-- 미국 4도시 연도별 ZHVI 평균
SELECT
    LEFT(year_month, 4) AS year,
    CASE
        WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
        WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
        WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
        WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
    END AS city,
    ROUND(AVG(zhvi)) AS annual_median_price,
    'USD' AS currency
FROM us_metro_zhvi
WHERE region_name != 'United States'
GROUP BY LEFT(year_month, 4), city

ORDER BY city, year
"""

# ============================================================
# Q7: COVID 전후 급등 분석 (2019 vs 2021 비교)
# ============================================================
Q7_COVID_IMPACT = """
SELECT
    region_name,
    MAX(CASE WHEN year_month = '2019-12' THEN zhvi END) AS pre_covid,
    MAX(CASE WHEN year_month = '2021-12' THEN zhvi END) AS post_covid,
    ROUND(
        (MAX(CASE WHEN year_month = '2021-12' THEN zhvi END)
       - MAX(CASE WHEN year_month = '2019-12' THEN zhvi END))
       / MAX(CASE WHEN year_month = '2019-12' THEN zhvi END) * 100, 2
    ) AS covid_surge_pct
FROM us_metro_zhvi
WHERE region_name != 'United States'
  AND year_month IN ('2019-12', '2021-12')
GROUP BY region_name
"""

# ============================================================
# Q8: 가격 인하 매물 비율 추이 (금리 인상기 2022~)
# ============================================================
Q8_PRICE_REDUCTION = """
SELECT
    date,
    region_name,
    pct_price_reduction,
    median_pct_price_reduction
FROM zillow_economics_ts
WHERE region_level = 'state'
  AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
  AND date >= '2020-01-01'
  AND pct_price_reduction IS NOT NULL
ORDER BY region_name, date
"""

# ============================================================
# Q9: Realtor.com 매물 기본 통계 (4개 도시)
# ============================================================
Q9_REALTOR_STATS = """
SELECT
    c.city_name,
    COUNT(*) AS total_listings,
    ROUND(AVG(r.price), 0) AS avg_price,
    ROUND(AVG(r.house_size), 0) AS avg_sqft,
    ROUND(AVG(r.bed), 1) AS avg_bed,
    ROUND(AVG(r.bath), 1) AS avg_bath,
    ROUND(AVG(CASE WHEN r.house_size > 0 THEN r.price / r.house_size END), 2) AS avg_price_per_sqft
FROM us_realtor_listings r
JOIN cities c ON r.city_id = c.city_id
WHERE r.price > 0
GROUP BY c.city_name
"""

# ============================================================
# Q10: 예측 성장률 (ZHVF)
# ============================================================
Q10_FORECAST = """
SELECT
    region_name,
    base_date,
    forecast_date,
    growth_rate
FROM us_metro_zhvf_growth
ORDER BY region_name, forecast_date
"""


# ── 실행 ──
if __name__ == '__main__':
    queries = {
        'Q1_ZHVI_TREND': Q1_ZHVI_TREND,
        'Q2_ZHVI_YOY': Q2_ZHVI_YOY,
        'Q3_ZORI_TREND': Q3_ZORI_TREND,
        'Q4_PRICE_TO_RENT': Q4_PRICE_TO_RENT,
        'Q5_DAEGU_DISTRICT': Q5_DAEGU_DISTRICT,
        'Q6_CROSS_COMPARISON': Q6_CROSS_COMPARISON,
        'Q7_COVID_IMPACT': Q7_COVID_IMPACT,
        'Q8_PRICE_REDUCTION': Q8_PRICE_REDUCTION,
        'Q9_REALTOR_STATS': Q9_REALTOR_STATS,
        'Q10_FORECAST': Q10_FORECAST,
    }

    for name, sql in queries.items():
        print(f"\n{'='*60}")
        print(f"📊 {name}")
        print(f"{'='*60}")
        try:
            df = query_to_df(sql)
            print(df.head(10).to_string(index=False))
            print(f"... 총 {len(df)}행")

            # CSV 저장
            os.makedirs('output', exist_ok=True)
            df.to_csv(f'output/{name}.csv', index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"   ❌ 에러: {e}")

    print("\n🎉 STEP 6 완료: 분석 쿼리 실행 + CSV 저장")
```

---

## 🔨 STEP 7: 시각화

### 파일: `src/step7_visualization.py`

```python
"""
STEP 7: 소주제1 시각화
실행: python src/step7_visualization.py
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import seaborn as sns
import os
from step0_init_db import get_connection, DB_NAME
from step6_analysis_queries import query_to_df, Q1_ZHVI_TREND, Q2_ZHVI_YOY, Q3_ZORI_TREND, Q5_DAEGU_DISTRICT, Q7_COVID_IMPACT

# ── 한글 폰트 ──
# Windows: 'Malgun Gothic', Mac: 'AppleGothic', Linux: 'NanumGothic'
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

os.makedirs('output', exist_ok=True)

# 도시별 색상
COLORS = {
    'Dallas-Fort Worth-Arlington, TX': '#E74C3C',
    'Atlanta-Sandy Springs-Roswell, GA': '#3498DB',
    'Phoenix-Mesa-Chandler, AZ': '#E67E22',
    'Charlotte-Concord-Gastonia, NC-SC': '#2ECC71',
    'United States': '#95A5A6',
    'Dallas': '#E74C3C',
    'Atlanta': '#3498DB',
    'Phoenix': '#E67E22',
    'Charlotte': '#2ECC71',
}

SHORT_NAMES = {
    'Dallas-Fort Worth-Arlington, TX': 'Dallas',
    'Atlanta-Sandy Springs-Roswell, GA': 'Atlanta',
    'Phoenix-Mesa-Chandler, AZ': 'Phoenix',
    'Charlotte-Concord-Gastonia, NC-SC': 'Charlotte',
    'United States': 'US Average',
}


def viz1_zhvi_trend():
    """차트 1: ZHVI 25년 장기 추이 (4도시 + 전국)"""
    df = query_to_df(Q1_ZHVI_TREND)
    df['date'] = pd.to_datetime(df['year_month'])
    df['label'] = df['region_name'].map(SHORT_NAMES)

    fig, ax = plt.subplots(figsize=(14, 7))
    for name, group in df.groupby('region_name'):
        ax.plot(group['date'], group['zhvi'],
                color=COLORS.get(name, 'gray'),
                label=SHORT_NAMES.get(name, name),
                linewidth=2 if name != 'United States' else 1.5,
                linestyle='-' if name != 'United States' else '--')

    ax.set_title('주택 가치 지수(ZHVI) 장기 추이: 대구 비교 4도시 vs 미국 전체', fontsize=14)
    ax.set_ylabel('ZHVI (USD)')
    ax.set_xlabel('')
    ax.legend(loc='upper left')
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(alpha=0.3)

    # COVID / 금리인상 구간 표시
    ax.axvspan(pd.Timestamp('2020-03'), pd.Timestamp('2021-06'), alpha=0.1, color='red', label='COVID 급등기')
    ax.axvspan(pd.Timestamp('2022-03'), pd.Timestamp('2023-12'), alpha=0.1, color='blue', label='금리인상기')

    plt.tight_layout()
    plt.savefig('output/viz1_zhvi_trend.png', dpi=150)
    plt.close()
    print("✅ viz1_zhvi_trend.png 저장")


def viz2_zhvi_yoy():
    """차트 2: ZHVI 전년동기 대비 변동률"""
    df = query_to_df(Q2_ZHVI_YOY)
    df['date'] = pd.to_datetime(df['year_month'])
    df['label'] = df['region_name'].map(SHORT_NAMES)

    fig, ax = plt.subplots(figsize=(14, 6))
    for name, group in df.groupby('region_name'):
        ax.plot(group['date'], group['yoy_pct'],
                color=COLORS.get(name, 'gray'),
                label=SHORT_NAMES.get(name, name))

    ax.axhline(y=0, color='black', linewidth=0.8)
    ax.set_title('ZHVI 전년동기 대비 변동률 (%)', fontsize=14)
    ax.set_ylabel('YoY 변동률 (%)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/viz2_zhvi_yoy.png', dpi=150)
    plt.close()
    print("✅ viz2_zhvi_yoy.png 저장")


def viz3_zori_trend():
    """차트 3: 임대료(ZORI) 추이"""
    df = query_to_df(Q3_ZORI_TREND)
    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for name, group in df.groupby('region_name'):
        ax.plot(group['date'], group['zori'],
                color=COLORS.get(name, 'gray'),
                label=SHORT_NAMES.get(name, name))

    ax.set_title('임대 관측 지수(ZORI) 추이: 4도시 vs 전국', fontsize=14)
    ax.set_ylabel('ZORI (USD/월)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/viz3_zori_trend.png', dpi=150)
    plt.close()
    print("✅ viz3_zori_trend.png 저장")


def viz4_daegu_district():
    """차트 4: 대구 구별 평균가 추이"""
    df = query_to_df(Q5_DAEGU_DISTRICT)

    if df.empty:
        print("⚠️ 대구 데이터 없음 — 스킵")
        return

    df['date'] = pd.to_datetime(df['year_month'])

    top_districts = df.groupby('district')['transaction_count'].sum().nlargest(6).index

    fig, ax = plt.subplots(figsize=(14, 6))
    for dist in top_districts:
        sub = df[df['district'] == dist]
        ax.plot(sub['date'], sub['avg_price'], label=dist)

    ax.set_title('대구 주요 구별 평균 아파트 거래가 추이', fontsize=14)
    ax.set_ylabel('평균 거래가 (만원)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/viz4_daegu_district.png', dpi=150)
    plt.close()
    print("✅ viz4_daegu_district.png 저장")


def viz5_covid_bar():
    """차트 5: COVID 전후 가격 급등 비교 (막대 차트)"""
    df = query_to_df(Q7_COVID_IMPACT)

    if df.empty:
        print("⚠️ COVID 비교 데이터 없음 — 스킵")
        return

    df['label'] = df['region_name'].map(SHORT_NAMES)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 좌: 절대가격
    x_pos = range(len(df))
    w = 0.35
    axes[0].bar([p - w/2 for p in x_pos], df['pre_covid'], w, label='2019.12', color='#3498DB')
    axes[0].bar([p + w/2 for p in x_pos], df['post_covid'], w, label='2021.12', color='#E74C3C')
    axes[0].set_xticks(list(x_pos))
    axes[0].set_xticklabels(df['label'])
    axes[0].set_ylabel('ZHVI (USD)')
    axes[0].set_title('COVID 전후 주택 가치')
    axes[0].legend()

    # 우: 상승률
    colors = ['#E74C3C' if v > 30 else '#E67E22' if v > 20 else '#2ECC71' for v in df['covid_surge_pct']]
    axes[1].barh(df['label'], df['covid_surge_pct'], color=colors)
    axes[1].set_xlabel('상승률 (%)')
    axes[1].set_title('COVID 급등률 (2019.12 → 2021.12)')
    for i, v in enumerate(df['covid_surge_pct']):
        axes[1].text(v + 0.5, i, f'{v}%', va='center')

    plt.tight_layout()
    plt.savefig('output/viz5_covid_impact.png', dpi=150)
    plt.close()
    print("✅ viz5_covid_impact.png 저장")


if __name__ == '__main__':
    viz1_zhvi_trend()
    viz2_zhvi_yoy()
    viz3_zori_trend()
    viz4_daegu_district()
    viz5_covid_bar()
    print("\n🎉 STEP 7 완료: 시각화 저장 → output/ 폴더")
```

---

## 🚀 실행 순서 요약

```bash
# 0. 사전 준비
pip install pymysql pandas numpy matplotlib seaborn

# 1. DB + 테이블 생성
python src/step0_init_db.py
python src/step1_create_tables.py

# 2. 미국 데이터 적재 (data/ 폴더)
python src/step2_load_us_zillow_wide.py       # ZHVI, ZORI, 예측 (Wide→Long)
python src/step3_load_us_zillow_economics.py  # Crosswalk + State/Metro/City 시계열
python src/step4_load_us_realtor.py           # Realtor.com 222만건 (4개 주 필터)

# 3. 한국 데이터 적재 (kaggle_data/)
python src/step5_load_kr_daegu.py             # 대구 실거래가 + 월별 요약

# 4. 분석 + 시각화
python src/step6_analysis_queries.py          # SQL 10개 쿼리 → CSV
python src/step7_visualization.py             # 차트 5개 → PNG
```

---

## ⚠️ Claude Code 실행 시 체크리스트

### 반드시 사전 확인할 것

| # | 확인 사항 | 확인 방법 |
|---|----------|----------|
| 1 | **MySQL 접속 가능 여부** | `mysql -h 172.30.1.47 -u wonho -p1111 -e "SELECT 1"` |
| 2 | **`data/` 폴더 파일 존재** | `ls data/zillow_Housing/`, `ls data/Zillow_Economics/` |
| 3 | **`kaggle_data/` 폴더 파일명** | `ls kaggle_data/` → 실제 파일명으로 step5 수정 |
| 4 | **Wide CSV의 RegionName 값** | `pd.read_csv(파일, nrows=5)['RegionName']` → TARGET_METROS 매칭 확인 |
| 5 | **Kaggle CSV 인코딩** | `cp949` / `utf-8` / `euc-kr` 중 어떤 것인지 확인 |
| 6 | **Kaggle CSV 열 이름** | `pd.read_csv(파일, nrows=3).columns` → K1_1_COL_MAP 수정 |
| 7 | **Realtor CSV state 열 값** | 약어(`TX`) vs 풀네임(`Texas`) 확인 |

### 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| `filter 결과 0행` | TARGET_METROS 이름 불일치 | `check_and_fix_metro_names()` 실행 후 수정 |
| `UnicodeDecodeError` | 인코딩 불일치 | `encoding='cp949'` 등으로 변경 |
| `Table doesn't exist` | step1 미실행 | `python src/step1_create_tables.py` |
| `Duplicate entry` | 중복 실행 | `TRUNCATE TABLE 테이블명` 후 재실행 |
| `pymysql.OperationalError: can't connect` | DB 접속 실패 | host/port/user/password 확인 |
| `Memory Error (City 689MB)` | 대용량 | chunksize 줄이기, 또는 City 스킵 |

---

## 📊 최종 산출물

| 산출물 | 파일 | 설명 |
|--------|------|------|
| DB 테이블 11개 | MySQL | cities, daegu_housing_prices, daegu_monthly_summary, us_realtor_listings, us_metro_zhvi, us_metro_zori, us_metro_zhvf_growth, us_national_zorf_growth, zillow_economics_ts, us_monthly_summary, zillow_county_crosswalk, zillow_cities_crosswalk |
| 분석 CSV 10개 | `output/Q1~Q10_*.csv` | 각 쿼리 결과 |
| 시각화 5개 | `output/viz1~5_*.png` | ZHVI 추이, YoY, ZORI, 대구 구별, COVID |
