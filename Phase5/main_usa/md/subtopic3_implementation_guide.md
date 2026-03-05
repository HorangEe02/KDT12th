# 소주제 3: 기후·입지와 지역별 가격 격차 — Claude Code 구현 가이드

## 🎯 이 문서의 목적

Claude Code가 이 문서를 읽고 소주제 3(기후·입지와 지역별 가격 격차)의 **전체 파이프라인**을 자동 구현할 수 있도록 작성된 상세 가이드입니다.

---

## 📋 실행 환경

```
DB Host   : 172.30.1.47
DB User   : wonho
DB Pass   : 1111
DB Name   : real_estate_comparison
Charset   : utf8mb4
Python    : pymysql, pandas, numpy, scipy, matplotlib, seaborn
```

---

## 📌 소주제 3 분석 프레임워크

```
┌──────────────────────────────────────────────────────────────┐
│  핵심 질문: 내륙/분지 도시의 기후 특성(폭염·극한기온)이       │
│            ZIP Code/구 단위 가격 격차에 어떤 영향을 미치는가?  │
│                                                              │
│  분석 경로:                                                   │
│                                                              │
│  ① 기후 프로파일 비교                                         │
│     대구 vs Dallas vs Atlanta vs Phoenix vs Charlotte         │
│     → 월평균 기온, 여름 최고기온, 폭염일수, 기온 변동성       │
│                                                              │
│  ② 도시 내부 가격 격차 분석                                   │
│     미국: ZIP Code별 ZHVI / 매물가격 / sqft당 가격            │
│     대구: 구별 아파트 실거래가 / ㎡당 가격                     │
│                                                              │
│  ③ 기후-가격 교차 분석                                        │
│     분지 도시(Phoenix·대구): 고온 지역 = 저가? 쾌적 지역 = 고가?│
│     → 여름 기온 상위 ZIP vs 하위 ZIP의 ZHVI 격차              │
│     → 대구 수성구 쾌적 프리미엄 vs 나머지 구                  │
│                                                              │
│  ④ 시간축 분석                                                │
│     기후변화(온난화)가 장기 가격 추세에 영향?                   │
│     Berkeley Earth 1750~2013 + 주택가격 1996~2025 오버레이     │
└──────────────────────────────────────────────────────────────┘
```

---

## 📂 파일 경로 규칙

```
프로젝트 루트/
├── data/
│   ├── realtor-data.zip.csv                                   ← ZIP별 가격 (소주제1 재사용)
│   ├── Zillow_Economics/
│   │   ├── Zip_time_series.csv                                ← ⭐ 782MB ZIP 시계열
│   │   ├── City_time_series.csv                               ← 도시 시계열
│   │   ├── Metro_time_series.csv                              ← MSA 시계열
│   │   └── cities_crosswalk.csv                               ← ZIP→도시 매핑 보조
│   └── zillow_Housing/
│       └── Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv ← MSA ZHVI (소주제1)
├── kaggle_data/
│   ├── GlobalLandTemperaturesByCity.csv                        ← C3-1 Berkeley Earth
│   ├── city_temperature.csv                                    ← C3-2 Daily Temp Major Cities
│   ├── historical_hourly_weather/                              ← C3-3 (폴더)
│   │   ├── temperature.csv
│   │   └── humidity.csv
│   ├── monthly_mean_temp_us_cities.csv                         ← C3-4
│   ├── us_weather_events.csv                                   ← C3-5
│   └── global_daily_climate.csv                                ← C3-6
├── src/
│   ├── step0_init_db.py                                       ← 공통 모듈 (소주제1)
│   ├── s3_step1_create_tables.py
│   ├── s3_step2_load_climate_berkeley.py
│   ├── s3_step3_load_climate_daily.py
│   ├── s3_step4_load_us_weather_events.py
│   ├── s3_step5_load_zip_prices.py
│   ├── s3_step6_build_daegu_district_prices.py
│   ├── s3_step7_build_climate_price_merged.py
│   ├── s3_step8_analysis_queries.py
│   └── s3_step9_visualization.py
└── output/
```

> **의존성:** 소주제1의 `step0_init_db.py`, `cities`, `us_realtor_listings`, `daegu_housing_prices` 테이블 재사용.

---

## 🔨 STEP 1: 테이블 생성

### 파일: `src/s3_step1_create_tables.py`

```python
"""
STEP 1: 소주제 3 전용 테이블 생성
실행: python src/s3_step1_create_tables.py
의존: step0_init_db.py
"""
from step0_init_db import get_connection, DB_NAME

TABLES = {

    # ══════════════════════════════════════════
    # A. 기후 데이터
    # ══════════════════════════════════════════

    # ── A-1. Berkeley Earth 월평균 기온 (1750~2013) ──
    'climate_monthly_berkeley': """
        CREATE TABLE IF NOT EXISTS climate_monthly_berkeley (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dt DATE COMMENT '관측월 첫날 (YYYY-MM-01)',
            year INT,
            month INT,
            city VARCHAR(100),
            country VARCHAR(100),
            avg_temp DECIMAL(8,3) COMMENT '월 평균 기온 (℃)',
            avg_temp_uncertainty DECIMAL(8,3) COMMENT '기온 불확실성 (℃)',
            latitude VARCHAR(20),
            longitude VARCHAR(20),
            source_dataset VARCHAR(100) DEFAULT 'C3-1 Berkeley Earth',
            INDEX idx_city_date (city, dt),
            INDEX idx_year_month (year, month),
            INDEX idx_city (city)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-2. 주요 도시 일별 기온 ──
    'climate_daily_cities': """
        CREATE TABLE IF NOT EXISTS climate_daily_cities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE,
            year INT,
            month INT,
            city VARCHAR(100),
            country VARCHAR(100),
            state VARCHAR(50),
            avg_temp_celsius DECIMAL(8,2) COMMENT '일 평균 기온 (℃)',
            avg_temp_fahrenheit DECIMAL(8,2) COMMENT '일 평균 기온 (℉)',
            source_dataset VARCHAR(100),
            INDEX idx_city_date (city, date),
            INDEX idx_date (date),
            INDEX idx_city_ym (city, year, month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-3. 미국 기상 이벤트 (폭염·혹한 등) ──
    'us_weather_events': """
        CREATE TABLE IF NOT EXISTS us_weather_events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_id VARCHAR(20),
            event_type VARCHAR(50) COMMENT 'Heat, Cold, Storm 등',
            severity VARCHAR(20) COMMENT 'Severe, Moderate, Light 등',
            start_time DATETIME,
            end_time DATETIME,
            city VARCHAR(100),
            county VARCHAR(100),
            state VARCHAR(50),
            zip_code VARCHAR(10),
            latitude DECIMAL(10,6),
            longitude DECIMAL(10,6),
            airport_code VARCHAR(10),
            source_dataset VARCHAR(100) DEFAULT 'C3-5 US Weather Events',
            INDEX idx_type (event_type),
            INDEX idx_city (city),
            INDEX idx_state (state),
            INDEX idx_zip (zip_code),
            INDEX idx_time (start_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-4. 도시별 기후 프로파일 (분석용 집계) ──
    'city_climate_profile': """
        CREATE TABLE IF NOT EXISTS city_climate_profile (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(100),
            country VARCHAR(50),
            period VARCHAR(30) COMMENT '집계 기간 (예: 2000-2013)',
            annual_avg_temp DECIMAL(8,2) COMMENT '연 평균 기온 (℃)',
            summer_avg_temp DECIMAL(8,2) COMMENT '6~8월 평균 (℃)',
            winter_avg_temp DECIMAL(8,2) COMMENT '12~2월 평균 (℃)',
            summer_max_avg DECIMAL(8,2) COMMENT '7~8월 일 최고 평균 (℃)',
            temp_range DECIMAL(8,2) COMMENT '연교차 (℃)',
            heatwave_days_avg INT COMMENT '연평균 폭염일수 (35℃+)',
            extreme_hot_days INT COMMENT '연평균 극한고온일수 (38℃+)',
            climate_type VARCHAR(50) COMMENT '기후 유형 (내륙분지/아열대습윤 등)',
            INDEX idx_city (city_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ══════════════════════════════════════════
    # B. 지역별 가격 데이터
    # ══════════════════════════════════════════

    # ── B-1. ZIP Code별 가격 (Zillow Zip_time_series) ──
    'us_zip_prices': """
        CREATE TABLE IF NOT EXISTS us_zip_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            zip_code VARCHAR(10),
            city_name VARCHAR(100),
            state VARCHAR(10),
            city_id INT COMMENT 'cities FK',
            date DATE,
            year_month VARCHAR(7),
            zhvi DECIMAL(15,2) COMMENT 'ZHVI_AllHomes',
            zhvi_per_sqft DECIMAL(10,2) COMMENT 'ZHVIPerSqft_AllHomes',
            median_listing_price DECIMAL(15,2),
            median_rental_price DECIMAL(12,2),
            inventory INT COMMENT 'InventorySeasonallyAdjusted',
            days_on_zillow DECIMAL(8,2),
            source_file VARCHAR(100) DEFAULT 'Zip_time_series.csv',
            INDEX idx_zip_date (zip_code, date),
            INDEX idx_city_date (city_id, date),
            INDEX idx_ym (year_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── B-2. ZIP Code별 Realtor 매물 집계 (소주제1 us_realtor_listings에서 파생) ──
    'us_zip_realtor_summary': """
        CREATE TABLE IF NOT EXISTS us_zip_realtor_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            zip_code VARCHAR(10),
            city_name VARCHAR(100),
            state VARCHAR(10),
            city_id INT,
            listing_count INT COMMENT '매물 수',
            avg_price DECIMAL(15,2),
            median_price DECIMAL(15,2),
            avg_house_size DECIMAL(12,2) COMMENT '평균 면적 sqft',
            avg_price_per_sqft DECIMAL(10,2),
            avg_bed DECIMAL(4,1),
            avg_bath DECIMAL(4,1),
            min_price DECIMAL(15,2),
            max_price DECIMAL(15,2),
            INDEX idx_zip (zip_code),
            INDEX idx_city (city_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── B-3. 대구 구별 가격 요약 (소주제1 daegu_housing_prices에서 파생) ──
    'daegu_district_climate_prices': """
        CREATE TABLE IF NOT EXISTS daegu_district_climate_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            district VARCHAR(30) COMMENT '구/군',
            period VARCHAR(30) COMMENT '분석기간',
            avg_price BIGINT COMMENT '평균 거래가 (만원)',
            median_price BIGINT,
            avg_price_per_m2 DECIMAL(12,2) COMMENT '㎡당 평균가 (만원)',
            transaction_count INT,
            avg_exclusive_area DECIMAL(10,2) COMMENT '평균 전용면적 (㎡)',
            price_rank INT COMMENT '가격 순위 (1=최고가)',
            premium_vs_avg DECIMAL(8,4) COMMENT '도시 평균 대비 프리미엄 (%)',
            INDEX idx_district (district)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ══════════════════════════════════════════
    # C. 기후-가격 교차 분석 결과
    # ══════════════════════════════════════════

    # ── C-1. ZIP/구별 기후-가격 통합 ──
    'climate_price_merged': """
        CREATE TABLE IF NOT EXISTS climate_price_merged (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(100),
            country VARCHAR(20),
            sub_region VARCHAR(50) COMMENT 'ZIP Code 또는 구/군',
            region_type ENUM('zip','district') COMMENT '지역 유형',
            avg_price DECIMAL(15,2) COMMENT '평균가 (USD 또는 만원)',
            price_per_unit DECIMAL(10,2) COMMENT 'sqft당 또는 ㎡당 가격',
            summer_avg_temp DECIMAL(8,2) COMMENT '여름 평균 기온 (℃)',
            annual_avg_temp DECIMAL(8,2),
            heatwave_events INT COMMENT '폭염 이벤트 수',
            price_tier ENUM('high','mid','low') COMMENT '가격 등급',
            temp_tier ENUM('hot','mild','cool') COMMENT '기온 등급',
            INDEX idx_city (city_name),
            INDEX idx_type (region_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── C-2. 기후-가격 상관분석 결과 ──
    'climate_price_correlation': """
        CREATE TABLE IF NOT EXISTS climate_price_correlation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50),
            analysis_type VARCHAR(50) COMMENT '분석유형 (cross-sectional/time-series)',
            x_variable VARCHAR(80),
            y_variable VARCHAR(80),
            pearson_r DECIMAL(8,4),
            p_value DECIMAL(12,8),
            n_observations INT,
            significance VARCHAR(5),
            interpretation TEXT,
            INDEX idx_city (city_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
}


def create_all_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for name, ddl in TABLES.items():
        cursor.execute(ddl)
        print(f"  ✅ {name}")
    conn.commit()
    conn.close()
    print("✅ 소주제3 전체 테이블 생성 완료")


if __name__ == '__main__':
    create_all_tables()
    print("🎉 S3 STEP 1 완료")
```

---

## 🔨 STEP 2: Berkeley Earth 월평균 기온 로딩

### 파일: `src/s3_step2_load_climate_berkeley.py`

**핵심:** GlobalLandTemperaturesByCity.csv에서 대구 + 미국 4개 도시만 필터

```python
"""
STEP 2: C3-1 Berkeley Earth → climate_monthly_berkeley (대구+미국4도시 필터)
실행: python src/s3_step2_load_climate_berkeley.py

원본 열: dt, AverageTemperature, AverageTemperatureUncertainty, City, Country, Latitude, Longitude
⚠️ City 열 값 확인 필요: 'Daegu' vs '대구' vs 'Taegu'
   미국: 'Dallas', 'Atlanta', 'Phoenix', 'Charlotte'
"""
import pandas as pd
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

# Berkeley Earth에서의 도시 이름 (사전 확인 필요)
# ⚠️ 대구는 'Taegu' 또는 'Daegu'일 수 있음
TARGET_CITIES_BERKELEY = [
    'Daegu', 'Taegu',                 # 대구 (옛 로마자 표기 Taegu 가능)
    'Dallas', 'Atlanta', 'Phoenix', 'Charlotte',
]


def find_berkeley_file():
    """Berkeley Earth CSV 자동 탐색"""
    candidates = [
        'GlobalLandTemperaturesByCity.csv',
        'globallandtemperaturesbycity.csv',
    ]

    # 직접 경로
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            return path

    # 하위 폴더 탐색
    if os.path.isdir(KAGGLE_DIR):
        for root, dirs, files in os.walk(KAGGLE_DIR):
            for f in files:
                if 'temperaturesbycity' in f.lower() or 'globalland' in f.lower():
                    return os.path.join(root, f)

    return None


def verify_city_names(csv_path):
    """CSV에서 타겟 도시 이름 매칭 확인"""
    # 첫 100만행에서 City 유니크 값 확인
    cities_found = set()
    for chunk in pd.read_csv(csv_path, usecols=['City', 'Country'], chunksize=100000):
        for target in TARGET_CITIES_BERKELEY:
            mask = chunk['City'].str.lower() == target.lower()
            if mask.any():
                cities_found.add(target)

        # 한국·미국만 확인
        kr_cities = chunk[chunk['Country'] == 'South Korea']['City'].unique()
        us_match = chunk[
            (chunk['Country'] == 'United States') &
            chunk['City'].str.lower().isin([c.lower() for c in ['Dallas','Atlanta','Phoenix','Charlotte']])
        ]['City'].unique()

        if kr_cities.size > 0:
            print(f"   🇰🇷 한국 도시: {kr_cities[:10]}")
        if us_match.size > 0:
            print(f"   🇺🇸 미국 매칭: {us_match}")

        if len(cities_found) >= 5:
            break

    print(f"   매칭된 도시: {cities_found}")
    return cities_found


def load_berkeley_earth():
    csv_path = find_berkeley_file()
    if csv_path is None:
        print("⚠️ C3-1 Berkeley Earth 파일 미발견 — 스킵")
        print(f"   kaggle_data/ 내용: {os.listdir(KAGGLE_DIR) if os.path.isdir(KAGGLE_DIR) else '없음'}")
        return

    print(f"\n📥 C3-1 Berkeley Earth 로딩: {csv_path}")

    # 도시 이름 확인
    matched = verify_city_names(csv_path)
    target_lower = set(c.lower() for c in TARGET_CITIES_BERKELEY)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO climate_monthly_berkeley
             (dt, year, month, city, country, avg_temp, avg_temp_uncertainty, latitude, longitude)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        # 타겟 도시 필터 (대소문자 무시)
        mask = chunk['City'].str.lower().isin(target_lower)
        chunk = chunk[mask]

        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        rows = []
        for _, r in chunk.iterrows():
            dt = r.get('dt')
            year = int(dt[:4]) if pd.notna(dt) and len(str(dt)) >= 4 else None
            month = int(dt[5:7]) if pd.notna(dt) and len(str(dt)) >= 7 else None

            rows.append((
                dt, year, month,
                r.get('City'), r.get('Country'),
                float(r['AverageTemperature']) if pd.notna(r.get('AverageTemperature')) else None,
                float(r['AverageTemperatureUncertainty']) if pd.notna(r.get('AverageTemperatureUncertainty')) else None,
                r.get('Latitude'), r.get('Longitude'),
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 10000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ climate_monthly_berkeley 적재: {total}행")

    # 적재 확인
    conn = get_connection(DB_NAME)
    df = pd.read_sql("""
        SELECT city, country, COUNT(*) AS months,
               MIN(dt) AS from_dt, MAX(dt) AS to_dt,
               ROUND(AVG(avg_temp),1) AS mean_temp
        FROM climate_monthly_berkeley
        GROUP BY city, country
    """, conn)
    conn.close()
    print("\n📊 적재 현황:")
    print(df.to_string(index=False))


if __name__ == '__main__':
    load_berkeley_earth()
    print("\n🎉 S3 STEP 2 완료")
```

---

## 🔨 STEP 3: 일별 기온 + 월별 기온 로딩

### 파일: `src/s3_step3_load_climate_daily.py`

```python
"""
STEP 3: C3-2 Daily Temperature + C3-4 Monthly Mean Temp → climate_daily_cities
실행: python src/s3_step3_load_climate_daily.py

C3-2 원본 열 (예상): Region, Country, State, City, Month, Day, Year, AvgTemperature
C3-4 원본 열 (예상): City, Year, Month, AvgTemp 등
"""
import pandas as pd
import numpy as np
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

TARGET_CITIES_DAILY = {
    'dallas', 'atlanta', 'phoenix', 'charlotte',
    'daegu', 'taegu',
}

# C3-2 국가/주 필터 (효율 위해)
TARGET_COUNTRIES = {'US', 'United States', 'South Korea', 'Korea'}
TARGET_STATES_US = {'Texas', 'TX', 'Georgia', 'GA', 'Arizona', 'AZ', 'North Carolina', 'NC'}


def find_daily_temp_file():
    """C3-2 Daily Temperature of Major Cities 파일 탐색"""
    for fname in ['city_temperature.csv', 'daily_temperature.csv',
                   'daily-temperature-of-major-cities.csv']:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            return path

    if os.path.isdir(KAGGLE_DIR):
        for f in os.listdir(KAGGLE_DIR):
            if 'temperature' in f.lower() and 'daily' in f.lower():
                return os.path.join(KAGGLE_DIR, f)
            if 'city_temperature' in f.lower():
                return os.path.join(KAGGLE_DIR, f)
    return None


def load_daily_temperature():
    """C3-2: Daily Temperature of Major Cities"""
    csv_path = find_daily_temp_file()
    if csv_path is None:
        print("⚠️ C3-2 Daily Temperature 파일 미발견 — 스킵")
        return

    print(f"\n📥 C3-2 Daily Temperature 로딩: {csv_path}")

    df_sample = pd.read_csv(csv_path, nrows=5)
    print(f"   열: {df_sample.columns.tolist()}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO climate_daily_cities
             (date, year, month, city, country, state,
              avg_temp_celsius, avg_temp_fahrenheit, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    total = 0

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        # 열 이름 정규화
        chunk.columns = [c.strip() for c in chunk.columns]

        # 도시 열 탐색
        city_col = next((c for c in chunk.columns if c.lower() == 'city'), None)
        country_col = next((c for c in chunk.columns if c.lower() in ['country', 'region']), None)
        state_col = next((c for c in chunk.columns if c.lower() == 'state'), None)

        if city_col is None:
            print("   ⚠️ City 열 없음 — 스킵")
            break

        # 타겟 도시 필터 (대소문자 무시)
        mask = chunk[city_col].str.lower().isin(TARGET_CITIES_DAILY)

        # 또는 국가/주 필터
        if country_col:
            mask_country = chunk[country_col].isin(TARGET_COUNTRIES)
            mask = mask | (mask_country & chunk[city_col].str.lower().isin(TARGET_CITIES_DAILY))

        chunk = chunk[mask]
        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        # 날짜 처리
        year_col = next((c for c in chunk.columns if c.lower() == 'year'), None)
        month_col = next((c for c in chunk.columns if c.lower() == 'month'), None)
        day_col = next((c for c in chunk.columns if c.lower() == 'day'), None)
        temp_col = next((c for c in chunk.columns if 'avgtemp' in c.lower() or 'average' in c.lower()), None)

        rows = []
        for _, r in chunk.iterrows():
            year = int(r[year_col]) if year_col and pd.notna(r.get(year_col)) else None
            month = int(r[month_col]) if month_col and pd.notna(r.get(month_col)) else None
            day = int(r[day_col]) if day_col and pd.notna(r.get(day_col)) else None

            try:
                date_str = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}" if year and month and day else None
            except Exception:
                date_str = None

            temp_f = float(r[temp_col]) if temp_col and pd.notna(r.get(temp_col)) else None
            # -99 등 이상치 제거
            if temp_f is not None and (temp_f < -60 or temp_f > 150):
                temp_f = None

            temp_c = round((temp_f - 32) * 5 / 9, 2) if temp_f is not None else None

            rows.append((
                date_str, year, month,
                r.get(city_col), r.get(country_col), r.get(state_col),
                temp_c, temp_f,
                'C3-2 Daily Temperature',
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 50000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ climate_daily_cities 적재: {total}행")


def load_monthly_mean_temp():
    """C3-4: Monthly Mean Temp US Cities 1948-2022"""
    candidates = [
        'monthly_mean_temp_us_cities.csv',
        'temp-data-of-prominent-us-cities-from-1948-to-2022.csv',
    ]
    csv_path = None
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        print("\n⚠️ C3-4 Monthly Mean Temp 미발견 — 스킵")
        return

    print(f"\n📥 C3-4 Monthly Mean Temp 로딩: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   열: {df.columns.tolist()[:15]}")

    # ⚠️ 이 데이터셋은 열 구조가 다양. Claude Code: 실제 열을 확인 후 매핑 조정
    # 최소한 city, year, month, temperature 열이 있을 것으로 기대

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 타겟 도시 필터 후 climate_daily_cities에 월 단위로 적재
    # (월 데이터이므로 day=15로 가운데 날짜 설정)
    city_col = next((c for c in df.columns if 'city' in c.lower()), None)

    if city_col:
        mask = df[city_col].str.lower().isin(TARGET_CITIES_DAILY)
        df = df[mask]

    df = df.where(pd.notnull(df), None)

    sql = """INSERT INTO climate_daily_cities
             (date, year, month, city, country, state,
              avg_temp_celsius, avg_temp_fahrenheit, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        year = r.get('year') or r.get('Year')
        month = r.get('month') or r.get('Month')
        city = r.get(city_col) if city_col else None
        temp = None
        for c in df.columns:
            if 'temp' in c.lower() and 'avg' in c.lower():
                temp = r.get(c)
                break
            if 'temp' in c.lower():
                temp = r.get(c)

        temp_c = float(temp) if pd.notna(temp) else None
        temp_f = round(temp_c * 9 / 5 + 32, 2) if temp_c is not None else None

        try:
            date_str = f"{int(year)}-{str(int(month)).zfill(2)}-15" if pd.notna(year) and pd.notna(month) else None
        except Exception:
            date_str = None

        rows.append((
            date_str,
            int(year) if pd.notna(year) else None,
            int(month) if pd.notna(month) else None,
            city, 'United States', None,
            temp_c, temp_f,
            'C3-4 Monthly Mean Temp',
        ))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    conn.close()
    print(f"   ✅ C3-4 적재: {len(rows)}행")


if __name__ == '__main__':
    load_daily_temperature()
    load_monthly_mean_temp()
    print("\n🎉 S3 STEP 3 완료")
```

---

## 🔨 STEP 4: 미국 기상 이벤트 (폭염) 로딩

### 파일: `src/s3_step4_load_us_weather_events.py`

```python
"""
STEP 4: C3-5 US Weather Events 2016-2022 → us_weather_events (폭염·혹한 중심)
실행: python src/s3_step4_load_us_weather_events.py

⚠️ 이 데이터셋은 대용량 (수백만행 가능) → 4개 주(TX/GA/AZ/NC) + Heat/Cold 이벤트만 필터
"""
import pandas as pd
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

TARGET_STATES = {'Texas', 'TX', 'Georgia', 'GA', 'Arizona', 'AZ', 'North Carolina', 'NC'}
TARGET_EVENT_TYPES = {'Heat', 'Cold', 'Severe-Cold', 'Extreme-Cold',
                       'heat', 'cold', 'Heatwave', 'Extreme Heat'}


def load_weather_events():
    candidates = [
        'us_weather_events.csv',
        'WeatherEvents_Jan2016-Dec2022.csv',
        'US_WeatherEvents_2016-2022.csv',
    ]
    csv_path = None
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        if os.path.isdir(KAGGLE_DIR):
            for f in os.listdir(KAGGLE_DIR):
                if 'weather' in f.lower() and 'event' in f.lower():
                    csv_path = os.path.join(KAGGLE_DIR, f)
                    break

    if csv_path is None:
        print("⚠️ C3-5 US Weather Events 미발견 — 스킵")
        return

    print(f"\n📥 C3-5 US Weather Events 로딩: {csv_path}")

    df_sample = pd.read_csv(csv_path, nrows=5)
    print(f"   열: {df_sample.columns.tolist()}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO us_weather_events
             (event_id, event_type, severity, start_time, end_time,
              city, county, state, zip_code, latitude, longitude, airport_code)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 열 이름 매핑 후보
    col_candidates = {
        'event_id': ['EventId', 'event_id', 'EventID'],
        'event_type': ['Type', 'EventType', 'event_type', 'type'],
        'severity': ['Severity', 'severity'],
        'start_time': ['StartTime(UTC)', 'StartTime', 'start_time'],
        'end_time': ['EndTime(UTC)', 'EndTime', 'end_time'],
        'city': ['City', 'city'],
        'county': ['County', 'county'],
        'state': ['State', 'state'],
        'zip_code': ['ZipCode', 'zip_code', 'Zipcode'],
        'latitude': ['LocationLat', 'Latitude', 'latitude'],
        'longitude': ['LocationLng', 'Longitude', 'longitude'],
        'airport_code': ['AirportCode', 'airport_code'],
    }

    def resolve_col(cols, target_key):
        for c in col_candidates.get(target_key, []):
            if c in cols:
                return c
        return None

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        cols = chunk.columns.tolist()

        # 주 필터
        state_c = resolve_col(cols, 'state')
        if state_c:
            chunk = chunk[chunk[state_c].isin(TARGET_STATES)]

        # 이벤트 타입 필터 (Heat/Cold)
        type_c = resolve_col(cols, 'event_type')
        if type_c:
            chunk = chunk[chunk[type_c].str.lower().str.contains('heat|cold', na=False)]

        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        rows = []
        for _, r in chunk.iterrows():
            rows.append((
                r.get(resolve_col(cols, 'event_id')),
                r.get(resolve_col(cols, 'event_type')),
                r.get(resolve_col(cols, 'severity')),
                r.get(resolve_col(cols, 'start_time')),
                r.get(resolve_col(cols, 'end_time')),
                r.get(resolve_col(cols, 'city')),
                r.get(resolve_col(cols, 'county')),
                r.get(resolve_col(cols, 'state')),
                str(r.get(resolve_col(cols, 'zip_code'), ''))[:10] if pd.notna(r.get(resolve_col(cols, 'zip_code'))) else None,
                r.get(resolve_col(cols, 'latitude')),
                r.get(resolve_col(cols, 'longitude')),
                r.get(resolve_col(cols, 'airport_code')),
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 20000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ us_weather_events 적재: {total}행")

    # 확인
    conn = get_connection(DB_NAME)
    df = pd.read_sql("""
        SELECT state, event_type, COUNT(*) AS cnt
        FROM us_weather_events
        GROUP BY state, event_type
        ORDER BY state, cnt DESC
    """, conn)
    conn.close()
    print("\n📊 이벤트 현황:")
    print(df.to_string(index=False))


if __name__ == '__main__':
    load_weather_events()
    print("\n🎉 S3 STEP 4 완료")
```

---

## 🔨 STEP 5: ZIP Code별 가격 로딩

### 파일: `src/s3_step5_load_zip_prices.py`

**핵심:** `Zip_time_series.csv` (782MB) → 4개 도시 ZIP만 필터 적재

```python
"""
STEP 5: Zillow Zip_time_series.csv → us_zip_prices + Realtor ZIP 집계 → us_zip_realtor_summary
실행: python src/s3_step5_load_zip_prices.py

⚠️ Zip_time_series.csv는 782MB — 반드시 타겟 ZIP 목록으로 필터 필요!
   타겟 ZIP 확보 전략:
   1. 소주제1 us_realtor_listings에서 city_id별 zip_code 추출
   2. 또는 사전에 도시별 대표 ZIP 범위를 지정
"""
import pandas as pd
import numpy as np
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

ZILLOW_ECONOMICS_DIR = 'data/Zillow_Economics/'

# ── 소주제1 핵심 가격 지표 ──
ZIP_PRICE_COLS = [
    'Date', 'RegionName',
    'ZHVI_AllHomes', 'ZHVIPerSqft_AllHomes',
    'MedianListingPrice_AllHomes',
    'MedianRentalPrice_AllHomes',
    'InventorySeasonallyAdjusted',
    'DaysOnZillow_AllHomes',
]

# 도시→주 매핑 (ZIP 필터용)
CITY_STATE_MAP = {2: 'TX', 3: 'GA', 4: 'AZ', 5: 'NC'}


def get_target_zips_from_realtor():
    """
    소주제1 us_realtor_listings에서 city_id별 상위 ZIP 코드 추출
    → Zip_time_series 필터 목록으로 사용
    """
    print("🔍 Realtor 데이터에서 타겟 ZIP 추출")
    conn = get_connection(DB_NAME)

    try:
        df = pd.read_sql("""
            SELECT city_id, zip_code, COUNT(*) AS cnt
            FROM us_realtor_listings
            WHERE city_id IS NOT NULL AND zip_code IS NOT NULL
            GROUP BY city_id, zip_code
            HAVING cnt >= 5
            ORDER BY city_id, cnt DESC
        """, conn)
    except Exception as e:
        print(f"   ⚠️ Realtor 테이블 조회 실패: {e}")
        conn.close()
        return []

    conn.close()

    if df.empty:
        print("   ⚠️ Realtor ZIP 없음 — 대표 ZIP 범위 사용")
        return get_fallback_zips()

    zips = df['zip_code'].astype(str).str.zfill(5).unique().tolist()
    print(f"   ✅ {len(zips)}개 ZIP 추출 (city별: {df.groupby('city_id').size().to_dict()})")

    return zips


def get_fallback_zips():
    """Realtor 미적재 시 대표 ZIP 범위"""
    # 주요 도시 ZIP 코드 범위 (대략적)
    zips = []
    # Dallas: 750xx~753xx
    zips += [str(z) for z in range(75001, 75399)]
    # Atlanta: 303xx~312xx
    zips += [str(z) for z in range(30301, 31299)]
    # Phoenix: 850xx~853xx
    zips += [str(z) for z in range(85001, 85399)]
    # Charlotte: 280xx~282xx
    zips += [str(z) for z in range(28001, 28299)]
    return zips


def load_zip_timeseries():
    """Zip_time_series.csv → us_zip_prices (타겟 ZIP 필터)"""
    csv_path = f'{ZILLOW_ECONOMICS_DIR}Zip_time_series.csv'
    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 Zip_time_series 로딩: {csv_path}")
    print("   ⚠️ 782MB 대용량 — 타겟 ZIP 필터 적용")

    target_zips = get_target_zips_from_realtor()
    target_zips_set = set(target_zips)
    print(f"   타겟 ZIP 수: {len(target_zips_set)}")

    # 사용 가능 열 확인
    df_sample = pd.read_csv(csv_path, nrows=5)
    avail = [c for c in ZIP_PRICE_COLS if c in df_sample.columns]
    print(f"   사용 열: {avail}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO us_zip_prices
             (zip_code, date, year_month, zhvi, zhvi_per_sqft,
              median_listing_price, median_rental_price,
              inventory, days_on_zillow)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in avail,
                              chunksize=30000):
        # RegionName = ZIP 코드 (문자열)
        chunk['RegionName'] = chunk['RegionName'].astype(str).str.zfill(5)
        chunk = chunk[chunk['RegionName'].isin(target_zips_set)]

        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        rows = []
        for _, r in chunk.iterrows():
            date = r.get('Date')
            ym = str(date)[:7] if pd.notna(date) else None

            rows.append((
                r['RegionName'], date, ym,
                r.get('ZHVI_AllHomes'), r.get('ZHVIPerSqft_AllHomes'),
                r.get('MedianListingPrice_AllHomes'),
                r.get('MedianRentalPrice_AllHomes'),
                r.get('InventorySeasonallyAdjusted'),
                r.get('DaysOnZillow_AllHomes'),
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 30000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ us_zip_prices 적재: {total}행")


def build_zip_realtor_summary():
    """소주제1 us_realtor_listings → us_zip_realtor_summary (ZIP별 매물 집계)"""
    print("\n📊 ZIP별 Realtor 매물 집계")

    conn = get_connection(DB_NAME)

    try:
        df = pd.read_sql("""
            SELECT
                zip_code,
                city AS city_name,
                state,
                city_id,
                COUNT(*) AS listing_count,
                AVG(price) AS avg_price,
                AVG(house_size) AS avg_house_size,
                AVG(CASE WHEN house_size > 0 THEN price / house_size END) AS avg_price_per_sqft,
                AVG(bed) AS avg_bed,
                AVG(bath) AS avg_bath,
                MIN(price) AS min_price,
                MAX(price) AS max_price
            FROM us_realtor_listings
            WHERE zip_code IS NOT NULL AND price > 0 AND city_id IS NOT NULL
            GROUP BY zip_code, city, state, city_id
            HAVING listing_count >= 3
        """, conn)
    except Exception as e:
        print(f"   ⚠️ 조회 실패: {e}")
        conn.close()
        return

    if df.empty:
        print("   ⚠️ 집계 결과 0행")
        conn.close()
        return

    # 중위가격 별도 계산
    df_median = pd.read_sql("""
        SELECT zip_code, price
        FROM us_realtor_listings
        WHERE zip_code IS NOT NULL AND price > 0 AND city_id IS NOT NULL
    """, conn)

    median_by_zip = df_median.groupby('zip_code')['price'].median().reset_index()
    median_by_zip.columns = ['zip_code', 'median_price']

    df = df.merge(median_by_zip, on='zip_code', how='left')

    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE us_zip_realtor_summary")

    sql = """INSERT INTO us_zip_realtor_summary
             (zip_code, city_name, state, city_id, listing_count,
              avg_price, median_price, avg_house_size, avg_price_per_sqft,
              avg_bed, avg_bath, min_price, max_price)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            r['zip_code'], r['city_name'], r['state'],
            int(r['city_id']),
            int(r['listing_count']),
            round(r['avg_price'], 2) if pd.notna(r['avg_price']) else None,
            round(r['median_price'], 2) if pd.notna(r['median_price']) else None,
            round(r['avg_house_size'], 2) if pd.notna(r['avg_house_size']) else None,
            round(r['avg_price_per_sqft'], 2) if pd.notna(r['avg_price_per_sqft']) else None,
            round(r['avg_bed'], 1) if pd.notna(r['avg_bed']) else None,
            round(r['avg_bath'], 1) if pd.notna(r['avg_bath']) else None,
            round(r['min_price'], 2) if pd.notna(r['min_price']) else None,
            round(r['max_price'], 2) if pd.notna(r['max_price']) else None,
        ))

    batch = 3000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   ✅ us_zip_realtor_summary: {len(rows)}행 ({len(df['city_id'].unique())}개 도시)")


if __name__ == '__main__':
    load_zip_timeseries()
    build_zip_realtor_summary()
    print("\n🎉 S3 STEP 5 완료")
```

---

## 🔨 STEP 6: 대구 구별 가격 집계

### 파일: `src/s3_step6_build_daegu_district_prices.py`

```python
"""
STEP 6: 소주제1 daegu_housing_prices → daegu_district_climate_prices (구별 가격 요약)
실행: python src/s3_step6_build_daegu_district_prices.py
"""
import pandas as pd
import numpy as np
from step0_init_db import get_connection, DB_NAME


def build_daegu_district_prices():
    print("\n📊 대구 구별 가격 요약 생성")
    conn = get_connection(DB_NAME)

    df = pd.read_sql("""
        SELECT district, deal_amount, exclusive_area
        FROM daegu_housing_prices
        WHERE district IS NOT NULL AND deal_amount > 0
    """, conn)

    if df.empty:
        print("   ⚠️ 대구 데이터 없음")
        conn.close()
        return

    df['price_per_m2'] = np.where(
        df['exclusive_area'] > 0,
        df['deal_amount'] / df['exclusive_area'],
        None
    )

    grouped = df.groupby('district').agg(
        avg_price=('deal_amount', 'mean'),
        median_price=('deal_amount', 'median'),
        avg_price_per_m2=('price_per_m2', 'mean'),
        transaction_count=('deal_amount', 'count'),
        avg_exclusive_area=('exclusive_area', 'mean'),
    ).reset_index()

    # 순위 + 프리미엄
    grouped = grouped.sort_values('avg_price', ascending=False).reset_index(drop=True)
    grouped['price_rank'] = range(1, len(grouped) + 1)
    city_avg = grouped['avg_price'].mean()
    grouped['premium_vs_avg'] = ((grouped['avg_price'] - city_avg) / city_avg * 100).round(4)

    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE daegu_district_climate_prices")

    sql = """INSERT INTO daegu_district_climate_prices
             (district, period, avg_price, median_price, avg_price_per_m2,
              transaction_count, avg_exclusive_area, price_rank, premium_vs_avg)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in grouped.iterrows():
        rows.append((
            r['district'], '전체기간',
            int(r['avg_price']), int(r['median_price']),
            round(r['avg_price_per_m2'], 2) if pd.notna(r['avg_price_per_m2']) else None,
            int(r['transaction_count']),
            round(r['avg_exclusive_area'], 2) if pd.notna(r['avg_exclusive_area']) else None,
            int(r['price_rank']),
            float(r['premium_vs_avg']),
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ daegu_district_climate_prices: {len(rows)}개 구")
    print(f"   🏆 최고가 구: {grouped.iloc[0]['district']} (프리미엄: +{grouped.iloc[0]['premium_vs_avg']:.1f}%)")


if __name__ == '__main__':
    build_daegu_district_prices()
    print("\n🎉 S3 STEP 6 완료")
```

---

## 🔨 STEP 7: 기후-가격 교차분석 테이블 구축

### 파일: `src/s3_step7_build_climate_price_merged.py`

```python
"""
STEP 7: 기후 프로파일 구축 + 기후-가격 교차분석 + 상관분석
실행: python src/s3_step7_build_climate_price_merged.py
"""
import pandas as pd
import numpy as np
from scipy import stats
from step0_init_db import get_connection, DB_NAME


def build_city_climate_profiles():
    """도시별 기후 프로파일 집계 → city_climate_profile"""
    print("\n📊 도시별 기후 프로파일 구축")
    conn = get_connection(DB_NAME)

    # ── Berkeley Earth: 2000~2013 기준 집계 ──
    df = pd.read_sql("""
        SELECT
            city, country,
            ROUND(AVG(avg_temp), 2) AS annual_avg_temp,
            ROUND(AVG(CASE WHEN month IN (6,7,8) THEN avg_temp END), 2) AS summer_avg_temp,
            ROUND(AVG(CASE WHEN month IN (12,1,2) THEN avg_temp END), 2) AS winter_avg_temp,
            ROUND(MAX(avg_temp), 2) AS summer_max_avg,
            ROUND(MAX(avg_temp) - MIN(avg_temp), 2) AS temp_range
        FROM climate_monthly_berkeley
        WHERE year >= 2000 AND avg_temp IS NOT NULL
        GROUP BY city, country
    """, conn)

    if df.empty:
        print("   ⚠️ Berkeley 데이터 없음 — 일별 데이터에서 시도")

    # ── Daily: 폭염일수 집계 ──
    df_heat = pd.read_sql("""
        SELECT
            city,
            ROUND(AVG(heat_days), 0) AS heatwave_days_avg,
            ROUND(AVG(extreme_days), 0) AS extreme_hot_days
        FROM (
            SELECT
                city,
                year,
                SUM(CASE WHEN avg_temp_celsius >= 35 THEN 1 ELSE 0 END) AS heat_days,
                SUM(CASE WHEN avg_temp_celsius >= 38 THEN 1 ELSE 0 END) AS extreme_days
            FROM climate_daily_cities
            WHERE avg_temp_celsius IS NOT NULL
            GROUP BY city, year
        ) sub
        GROUP BY city
    """, conn)

    if not df.empty and not df_heat.empty:
        merged = df.merge(df_heat, on='city', how='left')
    elif not df.empty:
        merged = df
        merged['heatwave_days_avg'] = None
        merged['extreme_hot_days'] = None
    else:
        print("   ⚠️ 기후 데이터 부족")
        conn.close()
        return

    # 기후 유형
    climate_map = {
        'Dallas': '아열대 습윤 (내륙)', 'Atlanta': '아열대 습윤',
        'Phoenix': '고온 사막 (분지)', 'Charlotte': '아열대 습윤 (피드몬트)',
        'Daegu': '대륙성 (분지)', 'Taegu': '대륙성 (분지)',
    }

    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE city_climate_profile")

    sql = """INSERT INTO city_climate_profile
             (city_name, country, period, annual_avg_temp, summer_avg_temp,
              winter_avg_temp, summer_max_avg, temp_range,
              heatwave_days_avg, extreme_hot_days, climate_type)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for _, r in merged.iterrows():
        cursor.execute(sql, (
            r['city'], r['country'], '2000-2013',
            r.get('annual_avg_temp'), r.get('summer_avg_temp'),
            r.get('winter_avg_temp'), r.get('summer_max_avg'),
            r.get('temp_range'),
            int(r['heatwave_days_avg']) if pd.notna(r.get('heatwave_days_avg')) else None,
            int(r['extreme_hot_days']) if pd.notna(r.get('extreme_hot_days')) else None,
            climate_map.get(r['city'], '기타'),
        ))

    conn.commit()
    conn.close()
    print(f"   ✅ city_climate_profile: {len(merged)}개 도시")


def build_us_zip_price_tiers():
    """미국 ZIP별 가격 등급 + 폭염 이벤트 수 → climate_price_merged"""
    print("\n📊 미국 ZIP-가격-기후 교차 테이블 구축")
    conn = get_connection(DB_NAME)

    # ── ZIP 가격 (Realtor 기반) ──
    df_price = pd.read_sql("""
        SELECT z.zip_code, z.city_name, z.state, z.city_id,
               z.avg_price, z.avg_price_per_sqft, z.listing_count
        FROM us_zip_realtor_summary z
        WHERE z.avg_price > 0
    """, conn)

    if df_price.empty:
        print("   ⚠️ ZIP 가격 데이터 없음")
        conn.close()
        return

    # ── ZIP별 폭염 이벤트 수 ──
    df_heat = pd.read_sql("""
        SELECT zip_code, COUNT(*) AS heatwave_events
        FROM us_weather_events
        WHERE LOWER(event_type) LIKE '%heat%'
          AND zip_code IS NOT NULL
        GROUP BY zip_code
    """, conn)

    merged = df_price.merge(df_heat, on='zip_code', how='left')
    merged['heatwave_events'] = merged['heatwave_events'].fillna(0).astype(int)

    # 가격 등급 (도시 내 3분위)
    for cid in merged['city_id'].unique():
        mask = merged['city_id'] == cid
        q33 = merged.loc[mask, 'avg_price'].quantile(0.33)
        q66 = merged.loc[mask, 'avg_price'].quantile(0.67)
        merged.loc[mask & (merged['avg_price'] <= q33), 'price_tier'] = 'low'
        merged.loc[mask & (merged['avg_price'] > q33) & (merged['avg_price'] <= q66), 'price_tier'] = 'mid'
        merged.loc[mask & (merged['avg_price'] > q66), 'price_tier'] = 'high'

    # 기온 등급 (폭염 이벤트 기반)
    merged['temp_tier'] = pd.cut(
        merged['heatwave_events'],
        bins=[-1, 0, 5, 9999],
        labels=['cool', 'mild', 'hot']
    )

    # 도시 기후 프로파일에서 여름 평균 기온
    df_climate = pd.read_sql("SELECT city_name, summer_avg_temp, annual_avg_temp FROM city_climate_profile", conn)
    city_name_map = {2: 'Dallas', 3: 'Atlanta', 4: 'Phoenix', 5: 'Charlotte'}
    merged['city_label'] = merged['city_id'].map(city_name_map)
    merged = merged.merge(df_climate.rename(columns={'city_name': 'city_label'}),
                           on='city_label', how='left')

    cursor = conn.cursor()

    sql = """INSERT INTO climate_price_merged
             (city_name, country, sub_region, region_type,
              avg_price, price_per_unit, summer_avg_temp, annual_avg_temp,
              heatwave_events, price_tier, temp_tier)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in merged.iterrows():
        rows.append((
            r.get('city_label'), 'USA', r['zip_code'], 'zip',
            r['avg_price'], r.get('avg_price_per_sqft'),
            r.get('summer_avg_temp'), r.get('annual_avg_temp'),
            int(r['heatwave_events']),
            r.get('price_tier'), str(r.get('temp_tier', '')),
        ))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    conn.close()
    print(f"   ✅ climate_price_merged (ZIP): {len(rows)}행")


def build_daegu_district_climate():
    """대구 구별 가격을 climate_price_merged에 추가"""
    print("\n📊 대구 구별 기후-가격 교차 데이터 추가")
    conn = get_connection(DB_NAME)

    df = pd.read_sql("SELECT * FROM daegu_district_climate_prices", conn)
    df_climate = pd.read_sql("""
        SELECT summer_avg_temp, annual_avg_temp
        FROM city_climate_profile
        WHERE city_name IN ('Daegu', 'Taegu')
        LIMIT 1
    """, conn)

    summer_temp = df_climate['summer_avg_temp'].iloc[0] if not df_climate.empty else None
    annual_temp = df_climate['annual_avg_temp'].iloc[0] if not df_climate.empty else None

    cursor = conn.cursor()
    sql = """INSERT INTO climate_price_merged
             (city_name, country, sub_region, region_type,
              avg_price, price_per_unit, summer_avg_temp, annual_avg_temp,
              heatwave_events, price_tier, temp_tier)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 가격 등급
    q33 = df['avg_price'].quantile(0.33)
    q66 = df['avg_price'].quantile(0.67)

    rows = []
    for _, r in df.iterrows():
        tier = 'low' if r['avg_price'] <= q33 else ('mid' if r['avg_price'] <= q66 else 'high')
        rows.append((
            '대구', 'South Korea', r['district'], 'district',
            r['avg_price'], r.get('avg_price_per_m2'),
            summer_temp, annual_temp,
            None,  # 대구 폭염 이벤트 (Weather Events에 없음)
            tier, 'hot',  # 대구 분지 = hot
        ))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    conn.close()
    print(f"   ✅ climate_price_merged (대구 구): {len(rows)}행")


def compute_climate_price_correlations():
    """기후-가격 상관분석 → climate_price_correlation"""
    print("\n📊 기후-가격 상관분석")
    conn = get_connection(DB_NAME)

    df = pd.read_sql("SELECT * FROM climate_price_merged WHERE avg_price IS NOT NULL", conn)

    results = []

    # 도시별: 폭염 이벤트 수 vs 가격
    for city in df[df['region_type'] == 'zip']['city_name'].dropna().unique():
        sub = df[(df['city_name'] == city) & (df['region_type'] == 'zip')].dropna(subset=['heatwave_events', 'avg_price'])
        if len(sub) < 10:
            continue

        r, p = stats.pearsonr(sub['heatwave_events'], sub['avg_price'])
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        direction = '양의' if r > 0 else '음의'
        strength = '강한' if abs(r) > 0.5 else '보통' if abs(r) > 0.3 else '약한'

        results.append({
            'city_name': city, 'analysis_type': 'cross-sectional',
            'x_variable': 'heatwave_events (ZIP)',
            'y_variable': 'avg_price',
            'pearson_r': round(r, 4), 'p_value': round(p, 8),
            'n_observations': len(sub), 'significance': sig,
            'interpretation': f'{city} ZIP 폭염이벤트↔가격: {strength} {direction} 상관 (r={r:.3f})',
        })

    # 시계열 상관: Berkeley 연평균기온 vs ZHVI (소주제1 데이터 필요)
    # → 간접적으로 city_climate_profile의 여름기온 vs 전체 가격수준 비교
    df_city = pd.read_sql("""
        SELECT cp.city_name, cp.summer_avg_temp,
               AVG(cm.avg_price) AS avg_price_all_zips
        FROM city_climate_profile cp
        LEFT JOIN climate_price_merged cm ON cp.city_name = cm.city_name
        WHERE cm.region_type = 'zip'
        GROUP BY cp.city_name, cp.summer_avg_temp
    """, conn)

    if len(df_city) >= 3:
        r, p = stats.pearsonr(df_city['summer_avg_temp'], df_city['avg_price_all_zips'])
        results.append({
            'city_name': 'ALL', 'analysis_type': 'cross-city',
            'x_variable': 'summer_avg_temp',
            'y_variable': 'avg_zip_price',
            'pearson_r': round(r, 4), 'p_value': round(p, 8),
            'n_observations': len(df_city), 'significance': '*' if p < 0.05 else '',
            'interpretation': f'도시간 여름기온↔평균가격 상관 (r={r:.3f})',
        })

    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE climate_price_correlation")
    sql = """INSERT INTO climate_price_correlation
             (city_name, analysis_type, x_variable, y_variable,
              pearson_r, p_value, n_observations, significance, interpretation)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for res in results:
        cursor.execute(sql, tuple(res.values()))

    conn.commit()
    conn.close()
    print(f"   ✅ 상관분석 결과: {len(results)}건")
    for r in results:
        print(f"      {r['city_name']:10s} | {r['x_variable']:30s} → r={r['pearson_r']:+.3f} {r['significance']}")


if __name__ == '__main__':
    build_city_climate_profiles()
    build_us_zip_price_tiers()
    build_daegu_district_climate()
    compute_climate_price_correlations()
    print("\n🎉 S3 STEP 7 완료")
```

---

## 🔨 STEP 8: 분석 쿼리

### 파일: `src/s3_step8_analysis_queries.py`

```python
"""
STEP 8: 소주제3 분석 SQL 쿼리 모음
실행: python src/s3_step8_analysis_queries.py
"""
import pandas as pd
import os
from step0_init_db import get_connection, DB_NAME

def query_to_df(sql):
    conn = get_connection(DB_NAME)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

# ============================================================
# Q1: 도시별 기후 프로파일 비교
# ============================================================
Q1_CLIMATE_PROFILE = """
SELECT city_name, country, climate_type,
       annual_avg_temp, summer_avg_temp, winter_avg_temp,
       temp_range, heatwave_days_avg, extreme_hot_days
FROM city_climate_profile
ORDER BY summer_avg_temp DESC
"""

# ============================================================
# Q2: 월별 기온 패턴 비교 (5도시 1~12월)
# ============================================================
Q2_MONTHLY_PATTERN = """
SELECT city, month,
       ROUND(AVG(avg_temp), 2) AS avg_temp,
       ROUND(MIN(avg_temp), 2) AS min_temp,
       ROUND(MAX(avg_temp), 2) AS max_temp
FROM climate_monthly_berkeley
WHERE year >= 2000 AND avg_temp IS NOT NULL
GROUP BY city, month
ORDER BY city, month
"""

# ============================================================
# Q3: 기온 장기 트렌드 (온난화 확인)
# ============================================================
Q3_WARMING_TREND = """
SELECT city,
       FLOOR(year / 10) * 10 AS decade,
       ROUND(AVG(avg_temp), 2) AS decade_avg_temp,
       ROUND(AVG(CASE WHEN month IN (6,7,8) THEN avg_temp END), 2) AS decade_summer
FROM climate_monthly_berkeley
WHERE year >= 1900 AND avg_temp IS NOT NULL
GROUP BY city, decade
ORDER BY city, decade
"""

# ============================================================
# Q4: 대구 구별 가격 순위 + 프리미엄
# ============================================================
Q4_DAEGU_DISTRICT_RANK = """
SELECT district, avg_price, median_price, avg_price_per_m2,
       transaction_count, price_rank, premium_vs_avg
FROM daegu_district_climate_prices
ORDER BY price_rank
"""

# ============================================================
# Q5: 미국 도시별 ZIP 가격 분포 통계
# ============================================================
Q5_ZIP_PRICE_DISTRIBUTION = """
SELECT
    c.city_name,
    COUNT(z.zip_code) AS zip_count,
    ROUND(AVG(z.avg_price), 0) AS city_avg,
    ROUND(MIN(z.avg_price), 0) AS cheapest_zip,
    ROUND(MAX(z.avg_price), 0) AS priciest_zip,
    ROUND(MAX(z.avg_price) / NULLIF(MIN(z.avg_price), 0), 1) AS price_gap_ratio,
    ROUND(STDDEV(z.avg_price), 0) AS price_stddev
FROM us_zip_realtor_summary z
JOIN cities c ON z.city_id = c.city_id
GROUP BY c.city_name
ORDER BY price_gap_ratio DESC
"""

# ============================================================
# Q6: 가격 등급별 평균 — 기후 교차
# ============================================================
Q6_TIER_COMPARISON = """
SELECT
    city_name, region_type,
    price_tier,
    COUNT(*) AS zone_count,
    ROUND(AVG(avg_price), 0) AS tier_avg_price,
    ROUND(AVG(price_per_unit), 2) AS tier_avg_per_unit,
    ROUND(AVG(heatwave_events), 1) AS avg_heatwave_events
FROM climate_price_merged
WHERE avg_price IS NOT NULL
GROUP BY city_name, region_type, price_tier
ORDER BY city_name, price_tier DESC
"""

# ============================================================
# Q7: Phoenix ZIP 폭염이벤트 상위 vs 하위 가격 비교
# ============================================================
Q7_PHOENIX_HEAT_PRICE = """
SELECT
    CASE
        WHEN heatwave_events >= 10 THEN '고폭염 ZIP (10+ events)'
        WHEN heatwave_events >= 3 THEN '중폭염 ZIP (3~9 events)'
        ELSE '저폭염 ZIP (0~2 events)'
    END AS heat_group,
    COUNT(*) AS zip_count,
    ROUND(AVG(avg_price), 0) AS avg_price,
    ROUND(AVG(price_per_unit), 2) AS avg_per_sqft,
    ROUND(AVG(heatwave_events), 1) AS avg_events
FROM climate_price_merged
WHERE city_name = 'Phoenix' AND region_type = 'zip'
GROUP BY heat_group
ORDER BY avg_events DESC
"""

# ============================================================
# Q8: 대구 수성구 vs 나머지 구 프리미엄 비교
# ============================================================
Q8_SUSEONG_PREMIUM = """
SELECT
    CASE WHEN sub_region = '수성구' THEN '수성구 (쾌적 프리미엄)'
         ELSE '기타 구 평균'
    END AS category,
    ROUND(AVG(avg_price), 0) AS avg_price,
    ROUND(AVG(price_per_unit), 2) AS avg_per_m2,
    COUNT(*) AS district_count
FROM climate_price_merged
WHERE city_name = '대구' AND region_type = 'district'
GROUP BY CASE WHEN sub_region = '수성구' THEN '수성구 (쾌적 프리미엄)' ELSE '기타 구 평균' END
"""

# ============================================================
# Q9: 미국 4개 주 폭염 이벤트 통계 (연도별)
# ============================================================
Q9_HEATWAVE_STATS = """
SELECT
    state,
    YEAR(start_time) AS year,
    COUNT(*) AS heat_events,
    COUNT(DISTINCT zip_code) AS affected_zips
FROM us_weather_events
WHERE LOWER(event_type) LIKE '%heat%'
  AND start_time IS NOT NULL
GROUP BY state, YEAR(start_time)
ORDER BY state, year
"""

# ============================================================
# Q10: 기후-가격 상관분석 결과
# ============================================================
Q10_CORRELATION = """
SELECT city_name, analysis_type, x_variable, y_variable,
       pearson_r, p_value, significance, interpretation
FROM climate_price_correlation
ORDER BY ABS(pearson_r) DESC
"""

if __name__ == '__main__':
    queries = {
        'S3_Q1_CLIMATE_PROFILE': Q1_CLIMATE_PROFILE,
        'S3_Q2_MONTHLY_PATTERN': Q2_MONTHLY_PATTERN,
        'S3_Q3_WARMING_TREND': Q3_WARMING_TREND,
        'S3_Q4_DAEGU_DISTRICT_RANK': Q4_DAEGU_DISTRICT_RANK,
        'S3_Q5_ZIP_PRICE_DISTRIBUTION': Q5_ZIP_PRICE_DISTRIBUTION,
        'S3_Q6_TIER_COMPARISON': Q6_TIER_COMPARISON,
        'S3_Q7_PHOENIX_HEAT_PRICE': Q7_PHOENIX_HEAT_PRICE,
        'S3_Q8_SUSEONG_PREMIUM': Q8_SUSEONG_PREMIUM,
        'S3_Q9_HEATWAVE_STATS': Q9_HEATWAVE_STATS,
        'S3_Q10_CORRELATION': Q10_CORRELATION,
    }

    os.makedirs('output', exist_ok=True)
    for name, sql in queries.items():
        print(f"\n{'='*60}\n📊 {name}\n{'='*60}")
        try:
            df = query_to_df(sql)
            print(df.head(15).to_string(index=False))
            print(f"... 총 {len(df)}행")
            df.to_csv(f'output/{name}.csv', index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"   ❌ 에러: {e}")

    print("\n🎉 S3 STEP 8 완료")
```

---

## 🔨 STEP 9: 시각화

### 파일: `src/s3_step9_visualization.py`

```python
"""
STEP 9: 소주제3 시각화 (7개 차트)
실행: python src/s3_step9_visualization.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
from step0_init_db import get_connection, DB_NAME
from s3_step8_analysis_queries import query_to_df
from s3_step8_analysis_queries import (
    Q1_CLIMATE_PROFILE, Q2_MONTHLY_PATTERN, Q3_WARMING_TREND,
    Q4_DAEGU_DISTRICT_RANK, Q5_ZIP_PRICE_DISTRIBUTION,
    Q6_TIER_COMPARISON, Q7_PHOENIX_HEAT_PRICE,
)

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
os.makedirs('output', exist_ok=True)

COLORS = {
    'Dallas': '#E74C3C', 'Atlanta': '#3498DB',
    'Phoenix': '#E67E22', 'Charlotte': '#2ECC71',
    '대구': '#9B59B6', 'Daegu': '#9B59B6', 'Taegu': '#9B59B6',
}


def viz1_monthly_temp_radar():
    """차트 1: 5도시 월별 기온 패턴 (레이더 or 라인 차트)"""
    df = query_to_df(Q2_MONTHLY_PATTERN)
    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    fig, ax = plt.subplots(figsize=(12, 6))
    for city in df['city'].unique():
        sub = df[df['city'] == city].sort_values('month')
        ax.plot(sub['month'], sub['avg_temp'],
                color=COLORS.get(city, 'gray'), label=city,
                marker='o', linewidth=2)
        # 최고·최저 범위 표시
        ax.fill_between(sub['month'], sub['min_temp'], sub['max_temp'],
                         color=COLORS.get(city, 'gray'), alpha=0.1)

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['1월','2월','3월','4월','5월','6월',
                         '7월','8월','9월','10월','11월','12월'])
    ax.axhline(y=35, color='red', linewidth=0.8, linestyle=':', label='폭염 기준 (35℃)')
    ax.set_ylabel('월평균 기온 (℃)')
    ax.set_title('5개 비교 도시 월별 기온 패턴 (2000~2013 평균)', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/s3_viz1_monthly_temp.png', dpi=150)
    plt.close()
    print("✅ s3_viz1_monthly_temp.png")


def viz2_warming_trend():
    """차트 2: 10년 단위 온난화 트렌드"""
    df = query_to_df(Q3_WARMING_TREND)
    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    fig, ax = plt.subplots(figsize=(14, 6))
    for city in df['city'].unique():
        sub = df[df['city'] == city]
        ax.plot(sub['decade'], sub['decade_summer'],
                color=COLORS.get(city, 'gray'), label=f'{city} (여름)',
                marker='s', linewidth=2)

    ax.set_xlabel('연대')
    ax.set_ylabel('여름 평균 기온 (℃)')
    ax.set_title('10년 단위 여름 기온 변화 추이 (온난화 확인)', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/s3_viz2_warming_trend.png', dpi=150)
    plt.close()
    print("✅ s3_viz2_warming_trend.png")


def viz3_climate_profile_bar():
    """차트 3: 도시별 기후 프로파일 비교 (막대)"""
    df = query_to_df(Q1_CLIMATE_PROFILE)
    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 여름 기온
    colors_list = [COLORS.get(c, 'gray') for c in df['city_name']]
    axes[0].barh(df['city_name'], df['summer_avg_temp'], color=colors_list)
    axes[0].set_title('여름 평균 기온 (℃)')
    axes[0].set_xlabel('℃')

    # 연교차
    axes[1].barh(df['city_name'], df['temp_range'], color=colors_list)
    axes[1].set_title('연교차 (℃)')
    axes[1].set_xlabel('℃')

    # 폭염일수
    heat_data = df['heatwave_days_avg'].fillna(0)
    axes[2].barh(df['city_name'], heat_data, color=colors_list)
    axes[2].set_title('연평균 폭염일수 (35℃+)')
    axes[2].set_xlabel('일')

    plt.suptitle('내륙 거점 도시 기후 프로파일 비교', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig('output/s3_viz3_climate_profile.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ s3_viz3_climate_profile.png")


def viz4_zip_price_boxplot():
    """차트 4: 도시별 ZIP 가격 분포 (박스플롯)"""
    conn = get_connection(DB_NAME)
    df = pd.read_sql("""
        SELECT c.city_name, z.avg_price
        FROM us_zip_realtor_summary z
        JOIN cities c ON z.city_id = c.city_id
        WHERE z.avg_price > 0 AND z.avg_price < 5000000
    """, conn)
    conn.close()

    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    fig, ax = plt.subplots(figsize=(12, 6))
    order = df.groupby('city_name')['avg_price'].median().sort_values(ascending=False).index
    palette = {c: COLORS.get(c, 'gray') for c in order}
    sns.boxplot(data=df, x='city_name', y='avg_price', order=order,
                palette=palette, ax=ax, showfliers=False)

    ax.set_ylabel('ZIP별 평균 매물가 (USD)')
    ax.set_xlabel('')
    ax.set_title('도시 내부 ZIP Code별 가격 분포 (격차 비교)', fontsize=13)
    ax.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('output/s3_viz4_zip_boxplot.png', dpi=150)
    plt.close()
    print("✅ s3_viz4_zip_boxplot.png")


def viz5_daegu_district_bar():
    """차트 5: 대구 구별 가격 순위 + 프리미엄"""
    df = query_to_df(Q4_DAEGU_DISTRICT_RANK)
    if df.empty:
        print("⚠️ 대구 구별 데이터 없음 — 스킵"); return

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ['#9B59B6' if p > 0 else '#95A5A6' for p in df['premium_vs_avg']]
    # 수성구 강조
    for i, d in enumerate(df['district']):
        if d == '수성구':
            colors[i] = '#E74C3C'

    bars = ax.barh(df['district'], df['avg_price'] / 10000, color=colors)

    # 프리미엄 % 표시
    for i, (bar, prem) in enumerate(zip(bars, df['premium_vs_avg'])):
        sign = '+' if prem > 0 else ''
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f'{sign}{prem:.1f}%', va='center', fontsize=9)

    ax.set_xlabel('평균 거래가 (억원)')
    ax.set_title('대구 구별 평균 아파트 거래가 순위 (도시 평균 대비 프리미엄)', fontsize=13)
    ax.grid(alpha=0.3, axis='x')

    # 범례
    patches = [
        mpatches.Patch(color='#E74C3C', label='수성구 (쾌적 프리미엄)'),
        mpatches.Patch(color='#9B59B6', label='평균 이상'),
        mpatches.Patch(color='#95A5A6', label='평균 이하'),
    ]
    ax.legend(handles=patches, loc='lower right')

    plt.tight_layout()
    plt.savefig('output/s3_viz5_daegu_district.png', dpi=150)
    plt.close()
    print("✅ s3_viz5_daegu_district.png")


def viz6_heat_price_heatmap():
    """차트 6: 기온등급 × 가격등급 교차 히트맵"""
    df = query_to_df(Q6_TIER_COMPARISON)
    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    # 도시별 파셋
    cities = df['city_name'].dropna().unique()
    n = len(cities)
    if n == 0:
        return

    fig, axes = plt.subplots(1, min(n, 4), figsize=(5*min(n,4), 5))
    if n == 1:
        axes = [axes]

    for i, city in enumerate(cities[:4]):
        sub = df[df['city_name'] == city]
        pivot = sub.pivot_table(index='price_tier', columns='city_name',
                                 values='tier_avg_price', aggfunc='mean')
        # 단순 바 차트로 대체
        ax = axes[i]
        tier_order = ['high', 'mid', 'low']
        sub_sorted = sub.set_index('price_tier').reindex(tier_order).dropna(subset=['tier_avg_price'])
        colors = ['#E74C3C', '#F39C12', '#3498DB'][:len(sub_sorted)]
        ax.barh(sub_sorted.index, sub_sorted['tier_avg_price'], color=colors)
        ax.set_title(f'{city}', fontsize=11)
        ax.set_xlabel('평균가')

    plt.suptitle('도시별 가격등급 평균 비교', fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig('output/s3_viz6_tier_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ s3_viz6_tier_heatmap.png")


def viz7_phoenix_heat_analysis():
    """차트 7: Phoenix 폭염 지역 vs 비폭염 지역 가격 비교"""
    df = query_to_df(Q7_PHOENIX_HEAT_PRICE)
    if df.empty:
        print("⚠️ Phoenix 데이터 없음 — 스킵"); return

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#E74C3C', '#F39C12', '#3498DB'][:len(df)]
    bars = ax.bar(df['heat_group'], df['avg_price'], color=colors)

    for bar, cnt, per_sqft in zip(bars, df['zip_count'], df['avg_per_sqft']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000,
                f'{cnt} ZIPs\n${per_sqft:.0f}/sqft', ha='center', fontsize=9)

    ax.set_ylabel('ZIP 평균 매물가 (USD)')
    ax.set_title('Phoenix: 폭염 빈도별 ZIP 가격 비교 (분지 도시 열섬 효과)', fontsize=13)
    ax.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('output/s3_viz7_phoenix_heat.png', dpi=150)
    plt.close()
    print("✅ s3_viz7_phoenix_heat.png")


if __name__ == '__main__':
    viz1_monthly_temp_radar()
    viz2_warming_trend()
    viz3_climate_profile_bar()
    viz4_zip_price_boxplot()
    viz5_daegu_district_bar()
    viz6_heat_price_heatmap()
    viz7_phoenix_heat_analysis()
    print("\n🎉 S3 STEP 9 완료: 시각화 → output/")
```

---

## 🚀 실행 순서 요약

```bash
# 사전: 소주제1(cities, us_realtor_listings, daegu_housing_prices) 완료 필수
pip install pymysql pandas numpy scipy matplotlib seaborn

# 1. 테이블 생성
python src/s3_step1_create_tables.py

# 2~4. 기후 데이터 (Kaggle)
python src/s3_step2_load_climate_berkeley.py      # Berkeley Earth 1750-2013
python src/s3_step3_load_climate_daily.py          # Daily + Monthly 기온
python src/s3_step4_load_us_weather_events.py      # 미국 폭염 이벤트

# 5~6. 가격 데이터
python src/s3_step5_load_zip_prices.py             # ⚠️ 782MB Zip_time_series + Realtor ZIP 집계
python src/s3_step6_build_daegu_district_prices.py  # 대구 구별 가격

# 7. 기후-가격 교차분석 + 상관분석
python src/s3_step7_build_climate_price_merged.py

# 8~9. 분석 + 시각화
python src/s3_step8_analysis_queries.py            # SQL 10개 → CSV
python src/s3_step9_visualization.py               # 차트 7개 → PNG
```

---

## ⚠️ Claude Code 실행 시 체크리스트

| # | 확인 사항 | 확인 방법 |
|---|----------|----------|
| 1 | **소주제1 완료 여부** | `SELECT COUNT(*) FROM us_realtor_listings`, `daegu_housing_prices` 확인 |
| 2 | **Berkeley Earth 도시명** | `'Daegu'` vs `'Taegu'` — csv 내 City 열 값 확인 |
| 3 | **Daily Temp 기온 단위** | 화씨(℉) vs 섭씨(℃) — 변환 로직 확인 |
| 4 | **Daily Temp 이상치** | −99, 0 등 비정상 값 필터 적용 여부 |
| 5 | **Zip_time_series 782MB** | 반드시 target_zips 필터 적용! 전체 로딩 시 메모리 초과 |
| 6 | **Realtor ZIP 코드 형식** | 정수(75001) vs 문자열('75001') vs zfill 필요 여부 |
| 7 | **US Weather Events 열명** | `Type` vs `EventType` vs `event_type` — 자동 감지 내장 |
| 8 | **Weather Events 크기** | 수백만행 가능 → 4개 주 + Heat/Cold만 필터 |

### 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| `Berkeley에서 대구 0행` | 도시명 불일치 | `Taegu` 추가 또는 `City LIKE '%aegu%'` |
| `Zip 필터 결과 0행` | ZIP 코드 형식 불일치 | `str.zfill(5)` 적용 + RegionName 샘플 확인 |
| `MemoryError (Zip 782MB)` | 필터 없이 전체 로딩 | `target_zips_set` 필수, `chunksize=20000` |
| `폭염일수 0 (Daily)` | 기온 단위 오류 | ℉→℃ 변환 누락 확인 |
| `상관분석 결과 없음` | 데이터 부족 | `n >= 10` 조건 완화 또는 데이터 점검 |

---

## 📊 최종 산출물

| 산출물 | 위치 | 설명 |
|--------|------|------|
| **DB 테이블 9개** | MySQL | climate_monthly_berkeley, climate_daily_cities, us_weather_events, city_climate_profile, us_zip_prices, us_zip_realtor_summary, daegu_district_climate_prices, climate_price_merged, climate_price_correlation |
| **분석 CSV 10개** | `output/S3_Q1~Q10_*.csv` | 기후 프로파일, 월별 패턴, 온난화, 구별 순위, ZIP 분포, 가격등급, Phoenix 폭염, 수성구 프리미엄, 폭염통계, 상관분석 |
| **시각화 7개** | `output/s3_viz1~7_*.png` | 월별 기온, 온난화 트렌드, 기후 프로파일, ZIP 박스플롯, 대구 구별, 가격등급, Phoenix 폭염 |

### 핵심 인사이트 기대값

| 분석 | 기대 결과 |
|------|----------|
| **Phoenix 열섬 효과** | 폭염 빈번 ZIP = 저가 / 산간·수변 ZIP = 고가 → 분지 도시 기후-가격 역상관 |
| **대구 수성구 프리미엄** | 쾌적한 주거환경 → 도시 평균 대비 +20~40% 프리미엄 → Phoenix와 동일 패턴 |
| **온난화 장기 트렌드** | 1900→2013 여름 기온 +1~2℃ 상승 → 분지 도시일수록 상승폭 큼 |
| **도시 내부 격차** | Phoenix > Dallas > Atlanta > Charlotte 순서로 ZIP간 가격 격차(분산) 클 것 |
| **분지 도시 공통 패턴** | 대구·Phoenix 모두 "고온 지역 = 저가, 쾌적 지역 = 고가" 구조 공유 |
