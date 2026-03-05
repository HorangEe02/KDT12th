# 소주제 2: 인구 이동과 주택 수요 — Claude Code 구현 가이드

## 🎯 이 문서의 목적

Claude Code가 이 문서를 읽고 소주제 2(인구 이동과 주택 수요)의 **전체 파이프라인**을 자동 구현할 수 있도록 작성된 상세 가이드입니다.

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

## 📌 소주제 2 분석 프레임워크

```
┌─────────────────────────────────────────────────────────┐
│  인구 변동 (독립변수)          부동산 수급 (종속변수)     │
│  ─────────────────          ─────────────────────       │
│  🇰🇷 대구 인구유출             대구 거래량·가격 하락?    │
│  🇺🇸 Dallas/Atlanta 인구유입   수요↑ 재고↓ 가격↑?       │
│  🇺🇸 Phoenix 폭발적 성장       과열 시장?                │
│  🇺🇸 Charlotte 산업전환 유입   구매력 변화?              │
│                                                         │
│  핵심 질문: 인구 증감은 부동산 시장에 어떤 경로로         │
│            영향을 미치는가?                               │
│                                                         │
│  경로 모델:                                              │
│  인구변동 → 수요(판매건수) → 재고 소진 → 시장온도 상승   │
│         → 대기일수 단축 → 가격 상승 → 필요소득 상승      │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 파일 경로 규칙

```
프로젝트 루트/
├── data/
│   ├── zillow_Housing/
│   │   ├── Metro_invt_fs_uc_sfrcondo_sm_month.csv               ← 매물 재고량
│   │   ├── Metro_market_temp_index_uc_sfrcondo_month.csv        ← 시장 온도 지수
│   │   ├── Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv      ← 평균 대기일수
│   │   ├── Metro_sales_count_now_uc_sfrcondo_month.csv          ← 판매 건수
│   │   └── Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   │                                                            ← 주택 구매 필요 소득
│   └── Zillow_Economics/
│       ├── Metro_time_series.csv       ← InventorySeasonallyAdjusted, Sale_Counts, DaysOnZillow
│       └── State_time_series.csv       ← 주 단위 수급 지표
├── kaggle_data/
│   ├── korean_demographics_2000_2022.csv    ← K2-1 한국 인구통계
│   ├── korea_income_welfare.csv             ← K2-2 한국 소득·복지
│   ├── us_census_demographic/               ← U2-1 US Census (폴더 가능)
│   │   ├── acs2015_county_data.csv
│   │   └── acs2017_county_data.csv
│   ├── population_time_series.csv           ← U2-2 인구 시계열
│   ├── us_county_historical_demographics.csv ← U2-3
│   ├── us_county_data.csv                   ← U2-4
│   ├── world_population_growth_2024.csv     ← G2-1 도시별 인구성장률
│   └── world_cities_database.csv            ← G2-2 도시 인구·좌표
├── src/
│   ├── step0_init_db.py                     ← 소주제1에서 생성한 공통 모듈 재사용
│   ├── s2_step1_create_tables.py
│   ├── s2_step2_load_zillow_demand.py
│   ├── s2_step3_load_zillow_economics_demand.py
│   ├── s2_step4_load_kr_demographics.py
│   ├── s2_step5_load_us_demographics.py
│   ├── s2_step6_load_global_population.py
│   ├── s2_step7_build_correlation.py
│   ├── s2_step8_analysis_queries.py
│   └── s2_step9_visualization.py
└── output/
    └── (시각화 결과물)
```

> **의존성:** 소주제1의 `step0_init_db.py`(DB 연결 공통 모듈), `cities` 테이블, `us_metro_zhvi` 테이블을 재사용합니다.
> 소주제1이 먼저 실행되어 있어야 합니다.

---

## 🔨 STEP 1: 테이블 생성

### 파일: `src/s2_step1_create_tables.py`

```python
"""
STEP 1: 소주제 2 전용 테이블 생성
실행: python src/s2_step1_create_tables.py
의존: step0_init_db.py, 소주제1 cities 테이블
"""
from step0_init_db import get_connection, DB_NAME

TABLES = {

    # ══════════════════════════════════════════
    # A. 인구 데이터 (독립변수 측)
    # ══════════════════════════════════════════

    # ── A-1. 한국 인구통계 (K2-1: Korean Demographics 2000-2022) ──
    'korean_demographics': """
        CREATE TABLE IF NOT EXISTS korean_demographics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT COMMENT '연도',
            region VARCHAR(50) COMMENT '시도명 (대구광역시 등)',
            total_population BIGINT COMMENT '총 인구',
            male_population BIGINT COMMENT '남성 인구',
            female_population BIGINT COMMENT '여성 인구',
            population_change BIGINT COMMENT '전년 대비 인구 변동',
            population_change_rate DECIMAL(8,4) COMMENT '인구변동률 (%)',
            birth_count INT COMMENT '출생 수',
            death_count INT COMMENT '사망 수',
            birth_rate DECIMAL(8,4) COMMENT '출생률',
            death_rate DECIMAL(8,4) COMMENT '사망률',
            natural_increase INT COMMENT '자연증감',
            economic_activity_rate DECIMAL(8,4) COMMENT '경제활동참가율 (%)',
            employment_rate DECIMAL(8,4) COMMENT '고용률 (%)',
            source_dataset VARCHAR(100) DEFAULT 'K2-1 Korean Demographics',
            INDEX idx_year (year),
            INDEX idx_region (region),
            INDEX idx_yr (year, region)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-2. 한국 소득·복지 (K2-2: Korea Income and Welfare) ──
    'korean_income_welfare': """
        CREATE TABLE IF NOT EXISTS korean_income_welfare (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT,
            region VARCHAR(50),
            household_income DECIMAL(15,2) COMMENT '가구 소득 (만원)',
            disposable_income DECIMAL(15,2) COMMENT '가처분 소득 (만원)',
            consumption_expenditure DECIMAL(15,2) COMMENT '소비지출 (만원)',
            income_quintile INT COMMENT '소득 분위 (1~5)',
            gini_coefficient DECIMAL(6,4) COMMENT '지니계수',
            poverty_rate DECIMAL(8,4) COMMENT '빈곤율 (%)',
            source_dataset VARCHAR(100) DEFAULT 'K2-2 Korea Income Welfare',
            INDEX idx_yr (year, region)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-3. 대구 인구 연도별 요약 (korean_demographics에서 대구만 추출·집계) ──
    'daegu_population_summary': """
        CREATE TABLE IF NOT EXISTS daegu_population_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT,
            total_population BIGINT,
            population_change BIGINT,
            population_change_rate DECIMAL(8,4),
            natural_increase INT,
            economic_activity_rate DECIMAL(8,4),
            avg_household_income DECIMAL(15,2) COMMENT '평균 가구소득 (만원, K2-2 조인)',
            INDEX idx_year (year)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-4. 미국 Census 인구통계 (U2-1: US Census Demographic Data) ──
    'us_census_demographics': """
        CREATE TABLE IF NOT EXISTS us_census_demographics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            census_year INT COMMENT 'ACS 조사 연도 (2015, 2017 등)',
            county VARCHAR(100),
            state VARCHAR(50),
            total_population BIGINT,
            men BIGINT,
            women BIGINT,
            hispanic DECIMAL(8,4),
            white DECIMAL(8,4),
            black DECIMAL(8,4),
            asian DECIMAL(8,4),
            median_income DECIMAL(15,2) COMMENT '가구 중위소득 USD',
            income_per_capita DECIMAL(15,2) COMMENT '1인당 소득 USD',
            poverty DECIMAL(8,4) COMMENT '빈곤율 %',
            unemployment DECIMAL(8,4) COMMENT '실업률 %',
            professional DECIMAL(8,4) COMMENT '전문직 비율 %',
            service DECIMAL(8,4) COMMENT '서비스직 비율 %',
            construction DECIMAL(8,4) COMMENT '건설직 비율 %',
            production DECIMAL(8,4) COMMENT '생산직 비율 %',
            drive DECIMAL(8,4) COMMENT '자가용 통근 %',
            transit DECIMAL(8,4) COMMENT '대중교통 통근 %',
            walk DECIMAL(8,4) COMMENT '도보 통근 %',
            mean_commute DECIMAL(8,2) COMMENT '평균 통근시간 (분)',
            city_id INT COMMENT 'cities FK (매핑된 경우)',
            source_dataset VARCHAR(100),
            INDEX idx_state (state),
            INDEX idx_county_state (county, state),
            INDEX idx_city (city_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-5. 미국 인구 시계열 (U2-2: Population Time Series Data) ──
    'us_population_timeseries': """
        CREATE TABLE IF NOT EXISTS us_population_timeseries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date VARCHAR(10) COMMENT '날짜 또는 연도',
            region_name VARCHAR(200) COMMENT '지역명 (MSA, County 등)',
            region_type VARCHAR(30) COMMENT '지역 유형',
            population BIGINT,
            population_change BIGINT,
            population_change_rate DECIMAL(8,4),
            source_dataset VARCHAR(100) DEFAULT 'U2-2 Population Time Series',
            INDEX idx_region_date (region_name(100), date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-6. 미국 County 역사적 인구통계 (U2-3) ──
    'us_county_historical': """
        CREATE TABLE IF NOT EXISTS us_county_historical (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT,
            county_fips VARCHAR(10),
            county_name VARCHAR(100),
            state VARCHAR(50),
            total_population BIGINT,
            population_change_rate DECIMAL(8,4),
            median_household_income DECIMAL(15,2),
            unemployment_rate DECIMAL(8,4),
            city_id INT,
            source_dataset VARCHAR(100) DEFAULT 'U2-3 County Historical',
            INDEX idx_state_year (state, year),
            INDEX idx_fips (county_fips)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-7. 글로벌 도시 인구성장률 (G2-1) ──
    'world_city_population_growth': """
        CREATE TABLE IF NOT EXISTS world_city_population_growth (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(100),
            country VARCHAR(50),
            population_2023 BIGINT,
            population_2024 BIGINT,
            growth_rate DECIMAL(8,4) COMMENT '연간 성장률 %',
            rank_global INT,
            source_dataset VARCHAR(100) DEFAULT 'G2-1 World Pop Growth',
            INDEX idx_city (city_name),
            INDEX idx_country (country)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ══════════════════════════════════════════
    # B. 주택 수급 지표 (종속변수 측)
    # ══════════════════════════════════════════

    # ── B-1. MSA 수급 종합 (zillow_Housing Wide → Long) ──
    'us_metro_demand': """
        CREATE TABLE IF NOT EXISTS us_metro_demand (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT COMMENT 'Zillow RegionID',
            size_rank INT,
            region_name VARCHAR(200) COMMENT 'MSA명',
            region_type VARCHAR(30),
            state_name VARCHAR(10),
            year_month VARCHAR(7),
            inventory DECIMAL(15,2) COMMENT '매물 재고량 (건)',
            market_temp_index DECIMAL(8,2) COMMENT '시장온도지수 (0~100)',
            mean_days_pending DECIMAL(8,2) COMMENT '평균 대기일수',
            sales_count INT COMMENT '월별 판매 건수',
            income_needed DECIMAL(15,2) COMMENT '주택구매 필요소득 (USD/년)',
            INDEX idx_region_ym (region_name(100), year_month),
            INDEX idx_ym (year_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── B-2. Zillow Economics 수급 지표 (Long Format) ──
    'zillow_demand_timeseries': """
        CREATE TABLE IF NOT EXISTS zillow_demand_timeseries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE,
            region_name VARCHAR(200),
            region_level ENUM('metro','state','city'),
            inventory_sa INT COMMENT 'InventorySeasonallyAdjusted',
            inventory_raw INT COMMENT 'InventoryRaw',
            days_on_zillow DECIMAL(8,2) COMMENT 'DaysOnZillow_AllHomes',
            sale_counts INT COMMENT 'Sale_Counts',
            sale_counts_sa INT COMMENT 'Sale_Counts_Seas_Adj',
            pct_selling_for_gain DECIMAL(8,4) COMMENT 'PctOfHomesSellingForGain',
            pct_selling_for_loss DECIMAL(8,4) COMMENT 'PctOfHomesSellingForLoss',
            pct_price_reduction DECIMAL(8,4) COMMENT 'PctOfListingsWithPriceReductions_AllHomes',
            pct_price_reduction_sa DECIMAL(8,4) COMMENT 'PctOfListingsWithPriceReductionsSeasAdj',
            age_of_inventory DECIMAL(8,2) COMMENT 'AgeOfInventory (Metro only)',
            source_file VARCHAR(100),
            INDEX idx_region_date (region_name(100), date),
            INDEX idx_level_date (region_level, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ══════════════════════════════════════════
    # C. 상관분석 결과 테이블
    # ══════════════════════════════════════════

    # ── C-1. 인구-부동산 상관 분석 결과 ──
    'population_housing_correlation': """
        CREATE TABLE IF NOT EXISTS population_housing_correlation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50),
            country VARCHAR(20),
            analysis_period VARCHAR(30) COMMENT '분석기간 (예: 2000-2022)',
            x_variable VARCHAR(80) COMMENT '독립변수명',
            y_variable VARCHAR(80) COMMENT '종속변수명',
            pearson_r DECIMAL(8,4) COMMENT '피어슨 상관계수',
            p_value DECIMAL(12,8) COMMENT 'p-value',
            n_observations INT COMMENT '관측 수',
            significance VARCHAR(5) COMMENT '유의수준 (* / ** / ***)',
            interpretation TEXT COMMENT '해석',
            INDEX idx_city (city_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── C-2. 연도별 인구-수급 통합 뷰 (분석용 집계) ──
    'annual_pop_housing_merged': """
        CREATE TABLE IF NOT EXISTS annual_pop_housing_merged (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50),
            country VARCHAR(20),
            year INT,
            population BIGINT,
            pop_change_rate DECIMAL(8,4) COMMENT '인구변동률 %',
            median_income DECIMAL(15,2) COMMENT '중위/평균 소득',
            zhvi DECIMAL(15,2) COMMENT '연평균 ZHVI (USD) — 소주제1 재사용',
            zhvi_change_rate DECIMAL(8,4) COMMENT 'ZHVI 변동률 %',
            avg_sales_count DECIMAL(12,2) COMMENT '연평균 월 판매건수',
            avg_inventory DECIMAL(12,2) COMMENT '연평균 재고량',
            avg_market_temp DECIMAL(8,2) COMMENT '연평균 시장온도',
            avg_days_pending DECIMAL(8,2) COMMENT '연평균 대기일수',
            avg_income_needed DECIMAL(15,2) COMMENT '연평균 구매필요소득',
            supply_demand_ratio DECIMAL(8,4) COMMENT '재고/판매건수 비율 (월수)',
            INDEX idx_city_year (city_name, year)
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
    print("✅ 소주제2 전체 테이블 생성 완료")


if __name__ == '__main__':
    create_all_tables()
    print("🎉 S2 STEP 1 완료")
```

---

## 🔨 STEP 2: Zillow Housing 수급 지표 (Wide → Long) 로딩

### 파일: `src/s2_step2_load_zillow_demand.py`

5개 Wide Format 파일을 하나의 `us_metro_demand` 테이블로 통합합니다.

```python
"""
STEP 2: zillow_Housing 수급 지표 5개 파일 → us_metro_demand 통합 적재
실행: python src/s2_step2_load_zillow_demand.py

파일 → 컬럼 매핑:
  Metro_invt_fs_...csv              → inventory        (2018~2025)
  Metro_market_temp_index_...csv    → market_temp_index (2018~2025)
  Metro_mean_doz_pending_...csv     → mean_days_pending (2018~2025)
  Metro_sales_count_now_...csv      → sales_count       (2008~2025)
  Metro_new_homeowner_income_...csv → income_needed     (2012~2025)

전략: 각 파일을 독립 Long 변환 후 → year_month + region_name 기준 MERGE → 일괄 적재
"""
import pandas as pd
import numpy as np
import pymysql
from step0_init_db import get_connection, DB_NAME

ZILLOW_HOUSING_DIR = 'data/zillow_Housing/'

TARGET_METROS = [
    'Dallas-Fort Worth-Arlington, TX',
    'Atlanta-Sandy Springs-Roswell, GA',
    'Phoenix-Mesa-Chandler, AZ',
    'Charlotte-Concord-Gastonia, NC-SC',
    'United States',
]

# ── 5개 파일 정의 ──
FILES = {
    'inventory': {
        'file': 'Metro_invt_fs_uc_sfrcondo_sm_month.csv',
        'desc': '매물 재고량 (건)',
    },
    'market_temp_index': {
        'file': 'Metro_market_temp_index_uc_sfrcondo_month.csv',
        'desc': '시장온도지수 (0~100, 50=균형, 80+=과열)',
    },
    'mean_days_pending': {
        'file': 'Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv',
        'desc': '평균 대기일수',
    },
    'sales_count': {
        'file': 'Metro_sales_count_now_uc_sfrcondo_month.csv',
        'desc': '월별 판매 건수',
    },
    'income_needed': {
        'file': 'Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
        'desc': '주택구매 필요 연소득 (USD)',
    },
}


def wide_to_long(csv_path, value_col_name):
    """
    Wide CSV → Long DataFrame 변환 + 타겟 MSA 필터
    반환: DataFrame[region_id, size_rank, region_name, region_type, state_name, year_month, {value_col}]
    """
    df = pd.read_csv(csv_path)

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    id_cols = [c for c in id_cols if c in df.columns]
    date_cols = [c for c in df.columns if c not in id_cols]

    # 타겟 필터
    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()

    if df_f.empty:
        # 부분 매칭 시도
        all_names = df['RegionName'].unique()
        for target in TARGET_METROS:
            keyword = target.split('-')[0].split(',')[0].strip().lower()
            matches = [n for n in all_names if keyword.lower() in str(n).lower()]
            if matches:
                print(f"   ℹ️ '{target}' 미매칭 → 후보: {matches[:3]}")
        return pd.DataFrame()

    df_long = df_f.melt(
        id_vars=id_cols, value_vars=date_cols,
        var_name='date_raw', value_name=value_col_name
    )
    df_long = df_long.dropna(subset=[value_col_name])
    df_long['year_month'] = df_long['date_raw'].str[:7]
    df_long.drop(columns=['date_raw'], inplace=True)

    return df_long


def load_all_demand_metrics():
    """5개 파일을 각각 Long 변환 → year_month + region_name 기준 MERGE → MySQL"""

    print("📥 Zillow Housing 수급 지표 5개 파일 로딩 시작\n")

    dfs = {}
    for col_name, info in FILES.items():
        csv_path = f"{ZILLOW_HOUSING_DIR}{info['file']}"
        print(f"  📂 {info['desc']}: {info['file']}")

        df = wide_to_long(csv_path, col_name)
        if df.empty:
            print(f"     ⚠️ 필터 결과 0행 — 스킵")
            continue

        print(f"     ✅ {len(df)}행 변환 완료")
        dfs[col_name] = df

    if not dfs:
        print("❌ 로딩된 파일 없음")
        return

    # ── MERGE: year_month + RegionName 기준 ──
    # 첫 번째 df를 기준으로 나머지를 outer join
    keys = ['RegionID', 'RegionName', 'year_month']
    merged = None

    for col_name, df in dfs.items():
        # 필수 키 + 값 열만 추출
        cols_keep = [c for c in keys if c in df.columns] + [col_name]
        # 추가 식별 열도 가져옴 (첫 번째만)
        if merged is None:
            extra = [c for c in ['SizeRank', 'RegionType', 'StateName'] if c in df.columns]
            df_slim = df[cols_keep + extra].copy()
            merged = df_slim
        else:
            df_slim = df[cols_keep].copy()
            merge_keys = [c for c in keys if c in merged.columns and c in df_slim.columns]
            merged = merged.merge(df_slim, on=merge_keys, how='outer')

    print(f"\n  📊 Merge 결과: {len(merged)}행 × {len(merged.columns)}열")
    print(f"     열: {merged.columns.tolist()}")

    # ── MySQL 적재 ──
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 기존 데이터 초기화
    cursor.execute("TRUNCATE TABLE us_metro_demand")
    conn.commit()

    sql = """INSERT INTO us_metro_demand
             (region_id, size_rank, region_name, region_type, state_name, year_month,
              inventory, market_temp_index, mean_days_pending, sales_count, income_needed)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in merged.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r.get('RegionID')) else None,
            int(r['SizeRank']) if pd.notna(r.get('SizeRank')) else None,
            r['RegionName'],
            r.get('RegionType') if pd.notna(r.get('RegionType')) else None,
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r['year_month'],
            float(r['inventory']) if pd.notna(r.get('inventory')) else None,
            float(r['market_temp_index']) if pd.notna(r.get('market_temp_index')) else None,
            float(r['mean_days_pending']) if pd.notna(r.get('mean_days_pending')) else None,
            int(r['sales_count']) if pd.notna(r.get('sales_count')) else None,
            float(r['income_needed']) if pd.notna(r.get('income_needed')) else None,
        ))

    batch = 5000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
        print(f"   ... {min(i+batch, len(rows))}/{len(rows)} 삽입")

    conn.close()
    print(f"\n✅ us_metro_demand 적재 완료: {len(rows)}행")

    # 적재 확인
    conn = get_connection(DB_NAME)
    df_check = pd.read_sql("""
        SELECT region_name,
               COUNT(*) as months,
               MIN(year_month) as from_ym,
               MAX(year_month) as to_ym,
               SUM(CASE WHEN inventory IS NOT NULL THEN 1 ELSE 0 END) as inv_cnt,
               SUM(CASE WHEN market_temp_index IS NOT NULL THEN 1 ELSE 0 END) as mti_cnt,
               SUM(CASE WHEN sales_count IS NOT NULL THEN 1 ELSE 0 END) as sales_cnt,
               SUM(CASE WHEN income_needed IS NOT NULL THEN 1 ELSE 0 END) as income_cnt
        FROM us_metro_demand
        GROUP BY region_name
    """, conn)
    conn.close()
    print("\n📊 적재 현황:")
    print(df_check.to_string(index=False))


if __name__ == '__main__':
    load_all_demand_metrics()
    print("\n🎉 S2 STEP 2 완료")
```

---

## 🔨 STEP 3: Zillow Economics 수급 시계열 (Long Format)

### 파일: `src/s2_step3_load_zillow_economics_demand.py`

```python
"""
STEP 3: Zillow Economics Long Format에서 수급 관련 지표 추출 → zillow_demand_timeseries
실행: python src/s2_step3_load_zillow_economics_demand.py

대상 파일: Metro_time_series.csv, State_time_series.csv
핵심 열: InventorySeasonallyAdjusted, InventoryRaw, DaysOnZillow_AllHomes,
         Sale_Counts, Sale_Counts_Seas_Adj, PctOfHomesSellingForGain/Loss,
         PctOfListingsWithPriceReductions, AgeOfInventory
"""
import pandas as pd
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

ZILLOW_ECONOMICS_DIR = 'data/Zillow_Economics/'

# ── 수급 관련 열 선택 ──
DEMAND_COLS = [
    'Date', 'RegionName',
    'InventorySeasonallyAdjusted', 'InventoryRaw',
    'DaysOnZillow_AllHomes',
    'Sale_Counts', 'Sale_Counts_Seas_Adj',
    'PctOfHomesSellingForGain_AllHomes',
    'PctOfHomesSellingForLoss_AllHomes',
    'PctOfListingsWithPriceReductions_AllHomes',
    'PctOfListingsWithPriceReductionsSeasAdj_AllHomes',
    'AgeOfInventory',
]

TARGET_STATES = ['Texas', 'Georgia', 'Arizona', 'North Carolina']


def get_target_metro_codes():
    """소주제1 step3에서 적재한 Crosswalk로부터 MSA 코드 반환"""
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
        return codes
    except Exception:
        return []


def load_demand_timeseries(csv_path, region_level, target_regions=None):
    """Long Format 시계열에서 수급 지표만 추출·적재"""

    if not os.path.exists(csv_path):
        print(f"⚠️ 파일 없음: {csv_path}")
        return

    print(f"\n📥 수급 시계열 로딩: {csv_path} (level={region_level})")

    # 사용 가능한 열 확인
    df_sample = pd.read_csv(csv_path, nrows=5)
    avail = [c for c in DEMAND_COLS if c in df_sample.columns]
    print(f"   사용 열: {len(avail)}/{len(DEMAND_COLS)} → {avail}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in avail,
                              chunksize=10000):
        if target_regions:
            chunk = chunk[chunk['RegionName'].isin(target_regions)]
        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        sql = """INSERT INTO zillow_demand_timeseries
                 (date, region_name, region_level,
                  inventory_sa, inventory_raw, days_on_zillow,
                  sale_counts, sale_counts_sa,
                  pct_selling_for_gain, pct_selling_for_loss,
                  pct_price_reduction, pct_price_reduction_sa,
                  age_of_inventory, source_file)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            rows.append((
                r.get('Date'), str(r['RegionName']), region_level,
                r.get('InventorySeasonallyAdjusted'),
                r.get('InventoryRaw'),
                r.get('DaysOnZillow_AllHomes'),
                r.get('Sale_Counts'),
                r.get('Sale_Counts_Seas_Adj'),
                r.get('PctOfHomesSellingForGain_AllHomes'),
                r.get('PctOfHomesSellingForLoss_AllHomes'),
                r.get('PctOfListingsWithPriceReductions_AllHomes'),
                r.get('PctOfListingsWithPriceReductionsSeasAdj_AllHomes'),
                r.get('AgeOfInventory'),
                os.path.basename(csv_path),
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        if total % 30000 == 0:
            print(f"   ... {total}행")

    conn.close()
    print(f"   ✅ {region_level} 수급 시계열 적재: {total}행")


if __name__ == '__main__':
    # State (4개 주)
    load_demand_timeseries(
        f'{ZILLOW_ECONOMICS_DIR}State_time_series.csv',
        region_level='state',
        target_regions=TARGET_STATES
    )

    # Metro (MSA 코드 기반)
    metro_codes = get_target_metro_codes()
    load_demand_timeseries(
        f'{ZILLOW_ECONOMICS_DIR}Metro_time_series.csv',
        region_level='metro',
        target_regions=metro_codes if metro_codes else None
    )

    print("\n🎉 S2 STEP 3 완료")
```

---

## 🔨 STEP 4: 한국 인구통계 (Kaggle) 로딩

### 파일: `src/s2_step4_load_kr_demographics.py`

```python
"""
STEP 4: Kaggle 한국 인구통계 → korean_demographics + korean_income_welfare + daegu_population_summary
실행: python src/s2_step4_load_kr_demographics.py

⚠️ Kaggle CSV의 실제 열명은 다운로드 후 확인 필수!
   pd.read_csv(파일, nrows=3, encoding='cp949').columns.tolist()
"""
import pandas as pd
import numpy as np
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

# ══════════════════════════════════════════
# K2-1: Korean Demographics 2000-2022
# ══════════════════════════════════════════

# ⚠️ 열 이름 예상 매핑 (실제와 다를 수 있음)
K2_1_COL_MAP_KR = {
    '연도': 'year', '시도': 'region', '총인구': 'total_population',
    '남자인구': 'male_population', '여자인구': 'female_population',
    '출생아수': 'birth_count', '사망자수': 'death_count',
    '출생률': 'birth_rate', '사망률': 'death_rate',
    '자연증감': 'natural_increase',
    '경제활동참가율': 'economic_activity_rate',
    '고용률': 'employment_rate',
}
K2_1_COL_MAP_EN = {
    'year': 'year', 'region': 'region', 'total_population': 'total_population',
    'male_population': 'male_population', 'female_population': 'female_population',
    'birth_count': 'birth_count', 'death_count': 'death_count',
    'birth_rate': 'birth_rate', 'death_rate': 'death_rate',
    'natural_increase': 'natural_increase',
    'economic_activity_rate': 'economic_activity_rate',
    'employment_rate': 'employment_rate',
    'Year': 'year', 'Region': 'region', 'Population': 'total_population',
}


def detect_encoding(csv_path):
    for enc in ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']:
        try:
            pd.read_csv(csv_path, nrows=2, encoding=enc)
            return enc
        except Exception:
            continue
    return 'utf-8'


def load_korean_demographics():
    """K2-1: Korean Demographics 2000-2022 로딩"""

    # 파일 자동 탐색
    candidates = [
        'korean_demographics_2000_2022.csv',
        'korean-demographics-20002022.csv',
        'korean_demographics.csv',
    ]

    csv_path = None
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        # 디렉토리 전체 탐색
        if os.path.isdir(KAGGLE_DIR):
            all_files = os.listdir(KAGGLE_DIR)
            demo_files = [f for f in all_files if 'demograph' in f.lower() or 'korean' in f.lower()]
            if demo_files:
                csv_path = os.path.join(KAGGLE_DIR, demo_files[0])
                print(f"   ℹ️ 자동 탐지: {demo_files[0]}")

    if csv_path is None:
        print("⚠️ K2-1 한국 인구통계 파일 미발견 — 스킵")
        print(f"   kaggle_data/ 내용: {os.listdir(KAGGLE_DIR) if os.path.isdir(KAGGLE_DIR) else '폴더 없음'}")
        return

    enc = detect_encoding(csv_path)
    print(f"\n📥 K2-1 로딩: {csv_path} (encoding={enc})")

    df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
    print(f"   원본 열: {df.columns.tolist()}")
    print(f"   크기: {df.shape}")

    # 열 매핑
    col_map = {}
    for orig in df.columns:
        key = orig.strip()
        if key in K2_1_COL_MAP_KR:
            col_map[orig] = K2_1_COL_MAP_KR[key]
        elif key in K2_1_COL_MAP_EN:
            col_map[orig] = K2_1_COL_MAP_EN[key]

    df = df.rename(columns=col_map)
    print(f"   매핑 후: {df.columns.tolist()}")

    # 인구변동 계산
    if 'total_population' in df.columns and 'year' in df.columns and 'region' in df.columns:
        df = df.sort_values(['region', 'year'])
        df['population_change'] = df.groupby('region')['total_population'].diff()
        df['population_change_rate'] = df.groupby('region')['total_population'].pct_change() * 100

    df = df.where(pd.notnull(df), None)

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO korean_demographics
             (year, region, total_population, male_population, female_population,
              population_change, population_change_rate,
              birth_count, death_count, birth_rate, death_rate,
              natural_increase, economic_activity_rate, employment_rate, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            int(r['year']) if pd.notna(r.get('year')) else None,
            r.get('region'),
            int(r['total_population']) if pd.notna(r.get('total_population')) else None,
            int(r['male_population']) if pd.notna(r.get('male_population')) else None,
            int(r['female_population']) if pd.notna(r.get('female_population')) else None,
            int(r['population_change']) if pd.notna(r.get('population_change')) else None,
            float(r['population_change_rate']) if pd.notna(r.get('population_change_rate')) else None,
            int(r['birth_count']) if pd.notna(r.get('birth_count')) else None,
            int(r['death_count']) if pd.notna(r.get('death_count')) else None,
            float(r['birth_rate']) if pd.notna(r.get('birth_rate')) else None,
            float(r['death_rate']) if pd.notna(r.get('death_rate')) else None,
            int(r['natural_increase']) if pd.notna(r.get('natural_increase')) else None,
            float(r['economic_activity_rate']) if pd.notna(r.get('economic_activity_rate')) else None,
            float(r['employment_rate']) if pd.notna(r.get('employment_rate')) else None,
            'K2-1 Korean Demographics 2000-2022',
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   ✅ korean_demographics 적재: {len(rows)}행")

    # 대구 요약 생성
    build_daegu_summary()


def load_korean_income_welfare():
    """K2-2: Korea Income and Welfare 로딩"""

    candidates = [
        'korea_income_welfare.csv',
        'korea-income-and-welfare.csv',
        'korea_income_and_welfare.csv',
    ]

    csv_path = None
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        if os.path.isdir(KAGGLE_DIR):
            all_files = os.listdir(KAGGLE_DIR)
            inc_files = [f for f in all_files if 'income' in f.lower() or 'welfare' in f.lower()]
            if inc_files:
                csv_path = os.path.join(KAGGLE_DIR, inc_files[0])

    if csv_path is None:
        print("⚠️ K2-2 한국 소득·복지 파일 미발견 — 스킵")
        return

    enc = detect_encoding(csv_path)
    print(f"\n📥 K2-2 로딩: {csv_path} (encoding={enc})")

    df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
    print(f"   원본 열: {df.columns.tolist()}")

    # ⚠️ 이 데이터셋의 구조는 매우 다양할 수 있음
    # Claude Code에게: 열 이름을 출력한 뒤 아래 INSERT를 실제 열에 맞게 조정하세요
    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 범용 적재: 실제 열 구조에 맞춰 매핑
    # 최소한 year, region, household_income 정도는 있을 것으로 기대
    sql = """INSERT INTO korean_income_welfare
             (year, region, household_income, disposable_income,
              consumption_expenditure, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        # 열명 자동 매핑 시도
        year = r.get('year') or r.get('연도') or r.get('Year')
        region = r.get('region') or r.get('시도') or r.get('Region')
        income = r.get('household_income') or r.get('소득') or r.get('income')
        disp_income = r.get('disposable_income') or r.get('가처분소득')
        consumption = r.get('consumption_expenditure') or r.get('소비지출')

        rows.append((
            int(year) if pd.notna(year) else None,
            region,
            float(income) if pd.notna(income) else None,
            float(disp_income) if pd.notna(disp_income) else None,
            float(consumption) if pd.notna(consumption) else None,
            'K2-2 Korea Income Welfare',
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ korean_income_welfare 적재: {len(rows)}행")


def build_daegu_summary():
    """korean_demographics에서 대구만 추출 → daegu_population_summary"""
    print("\n📊 대구 인구 요약 생성")

    conn = get_connection(DB_NAME)

    df = pd.read_sql("""
        SELECT year, total_population, population_change, population_change_rate,
               natural_increase, economic_activity_rate
        FROM korean_demographics
        WHERE region LIKE '%대구%'
        ORDER BY year
    """, conn)

    if df.empty:
        print("   ⚠️ 대구 데이터 없음 — region 열 값 확인 필요")
        # 디버깅: 어떤 region 값이 있는지 확인
        df_regions = pd.read_sql("SELECT DISTINCT region FROM korean_demographics LIMIT 30", conn)
        print(f"   사용 가능 region 값: {df_regions['region'].tolist()}")
        conn.close()
        return

    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE daegu_population_summary")

    sql = """INSERT INTO daegu_population_summary
             (year, total_population, population_change, population_change_rate,
              natural_increase, economic_activity_rate)
             VALUES (%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            int(r['year']),
            int(r['total_population']) if pd.notna(r['total_population']) else None,
            int(r['population_change']) if pd.notna(r['population_change']) else None,
            float(r['population_change_rate']) if pd.notna(r['population_change_rate']) else None,
            int(r['natural_increase']) if pd.notna(r['natural_increase']) else None,
            float(r['economic_activity_rate']) if pd.notna(r['economic_activity_rate']) else None,
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ daegu_population_summary: {len(rows)}행")


if __name__ == '__main__':
    load_korean_demographics()
    load_korean_income_welfare()
    print("\n🎉 S2 STEP 4 완료")
```

---

## 🔨 STEP 5: 미국 인구통계 (Kaggle) 로딩

### 파일: `src/s2_step5_load_us_demographics.py`

```python
"""
STEP 5: Kaggle 미국 인구통계 → us_census_demographics + us_county_historical
실행: python src/s2_step5_load_us_demographics.py

핵심 데이터: U2-1 US Census Demographic Data (ACS 2015, 2017)
"""
import pandas as pd
import numpy as np
import pymysql
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

# 타겟 주 (US Census에서 state 열은 주 약어일 수 있음)
TARGET_STATES = {
    'Texas', 'TX', 'Georgia', 'GA', 'Arizona', 'AZ', 'North Carolina', 'NC',
}

# city_id 매핑 (county 기반 — Dallas County → Dallas 등)
COUNTY_CITY_MAP = {
    ('Dallas', 'Texas'): 2, ('Dallas', 'TX'): 2,
    ('Fulton', 'Georgia'): 3, ('Fulton', 'GA'): 3,         # Atlanta
    ('DeKalb', 'Georgia'): 3, ('DeKalb', 'GA'): 3,         # Atlanta
    ('Maricopa', 'Arizona'): 4, ('Maricopa', 'AZ'): 4,     # Phoenix
    ('Mecklenburg', 'North Carolina'): 5, ('Mecklenburg', 'NC'): 5,  # Charlotte
}


def load_us_census():
    """U2-1: US Census Demographic Data 로딩"""

    # 파일 자동 탐색 (폴더 또는 단일 파일)
    csv_files = []

    # 단일 파일 후보
    for fname in ['acs2015_county_data.csv', 'acs2017_county_data.csv',
                   'us_census_demographic.csv', 'acs2015_census_tract_data.csv']:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_files.append(path)

    # 하위 폴더 탐색
    subdir = os.path.join(KAGGLE_DIR, 'us_census_demographic')
    if os.path.isdir(subdir):
        for f in os.listdir(subdir):
            if f.endswith('.csv'):
                csv_files.append(os.path.join(subdir, f))

    if not csv_files:
        print("⚠️ U2-1 US Census 파일 미발견")
        if os.path.isdir(KAGGLE_DIR):
            print(f"   kaggle_data/ 내용: {os.listdir(KAGGLE_DIR)}")
        return

    for csv_path in csv_files:
        print(f"\n📥 U2-1 로딩: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"   열: {df.columns.tolist()[:15]}...")
        print(f"   크기: {df.shape}")

        # State 열 확인
        state_col = None
        for c in ['State', 'state', 'STATE', 'state_name']:
            if c in df.columns:
                state_col = c
                break

        if state_col is None:
            print("   ⚠️ State 열 없음 — 스킵")
            continue

        # 4개 주 필터
        df = df[df[state_col].isin(TARGET_STATES)]
        if df.empty:
            print(f"   ⚠️ 타겟 주 필터 결과 0행 (state 값: {df[state_col].unique()[:10]})")
            continue

        # census_year 추출 (파일명에서)
        if '2015' in csv_path:
            census_year = 2015
        elif '2017' in csv_path:
            census_year = 2017
        else:
            census_year = 2020

        # 열 매핑
        col_map = {
            'County': 'county', 'county': 'county', 'CountyName': 'county',
            'State': 'state', 'state': 'state',
            'TotalPop': 'total_population', 'total_population': 'total_population',
            'Men': 'men', 'Women': 'women',
            'Hispanic': 'hispanic', 'White': 'white', 'Black': 'black', 'Asian': 'asian',
            'Income': 'median_income', 'IncomePerCap': 'income_per_capita',
            'Poverty': 'poverty', 'Unemployment': 'unemployment',
            'Professional': 'professional', 'Service': 'service',
            'Construction': 'construction', 'Production': 'production',
            'Drive': 'drive', 'Transit': 'transit', 'Walk': 'walk',
            'MeanCommute': 'mean_commute',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        df = df.where(pd.notnull(df), None)

        conn = get_connection(DB_NAME)
        cursor = conn.cursor()

        sql = """INSERT INTO us_census_demographics
                 (census_year, county, state, total_population, men, women,
                  hispanic, white, black, asian,
                  median_income, income_per_capita, poverty, unemployment,
                  professional, service, construction, production,
                  drive, transit, walk, mean_commute,
                  city_id, source_dataset)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in df.iterrows():
            county = r.get('county', '')
            state = r.get('state', '')
            city_id = COUNTY_CITY_MAP.get((county, state))

            rows.append((
                census_year, county, state,
                int(r['total_population']) if pd.notna(r.get('total_population')) else None,
                int(r['men']) if pd.notna(r.get('men')) else None,
                int(r['women']) if pd.notna(r.get('women')) else None,
                r.get('hispanic'), r.get('white'), r.get('black'), r.get('asian'),
                r.get('median_income'), r.get('income_per_capita'),
                r.get('poverty'), r.get('unemployment'),
                r.get('professional'), r.get('service'),
                r.get('construction'), r.get('production'),
                r.get('drive'), r.get('transit'), r.get('walk'),
                r.get('mean_commute'),
                city_id,
                f'U2-1 ACS {census_year}',
            ))

        batch = 2000
        for i in range(0, len(rows), batch):
            cursor.executemany(sql, rows[i:i+batch])
            conn.commit()

        conn.close()
        print(f"   ✅ us_census_demographics 적재: {len(rows)}행 (ACS {census_year})")


def load_us_county_historical():
    """U2-3: US County Historical Demographics"""

    candidates = [
        'us_county_historical_demographics.csv',
        'us-county-historical-demographics.csv',
    ]
    csv_path = None
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        print("\n⚠️ U2-3 County Historical 미발견 — 스킵")
        return

    print(f"\n📥 U2-3 로딩: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   열: {df.columns.tolist()[:15]}...")

    # State 필터
    state_col = next((c for c in df.columns if c.lower() == 'state'), None)
    if state_col:
        df = df[df[state_col].isin(TARGET_STATES)]

    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # ⚠️ 이 데이터셋의 열 구조는 다양함 — 최소 스키마로 적재
    sql = """INSERT INTO us_county_historical
             (year, county_fips, county_name, state, total_population,
              median_household_income, unemployment_rate, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        year = r.get('year') or r.get('Year')
        county = r.get('county_name') or r.get('CountyName') or r.get('county')
        state = r.get('state') or r.get('State')
        fips = r.get('county_fips') or r.get('FIPS') or r.get('fips')
        pop = r.get('total_population') or r.get('TotalPop') or r.get('population')
        income = r.get('median_household_income') or r.get('MedianIncome') or r.get('Income')
        unemp = r.get('unemployment_rate') or r.get('Unemployment')

        rows.append((
            int(year) if pd.notna(year) else None,
            str(fips) if pd.notna(fips) else None,
            county, state,
            int(pop) if pd.notna(pop) else None,
            float(income) if pd.notna(income) else None,
            float(unemp) if pd.notna(unemp) else None,
            'U2-3 County Historical',
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   ✅ us_county_historical 적재: {len(rows)}행")


if __name__ == '__main__':
    load_us_census()
    load_us_county_historical()
    print("\n🎉 S2 STEP 5 완료")
```

---

## 🔨 STEP 6: 글로벌 인구 데이터 (Kaggle) 로딩

### 파일: `src/s2_step6_load_global_population.py`

```python
"""
STEP 6: G2-1 World Population Growth + G2-2 World Cities Database → world_city_population_growth
실행: python src/s2_step6_load_global_population.py
"""
import pandas as pd
import os
from step0_init_db import get_connection, DB_NAME

KAGGLE_DIR = 'kaggle_data/'

TARGET_CITIES = ['Daegu', 'Dallas', 'Atlanta', 'Phoenix', 'Charlotte',
                 '대구', 'daegu']


def load_world_population_growth():
    """G2-1: World Population Growth Rate by Cities 2024"""

    candidates = [
        'world_population_growth_2024.csv',
        'world-population-growth-rate-by-cities-2024.csv',
        'world_population_growth_rate_by_cities_2024.csv',
    ]
    csv_path = None
    for fname in candidates:
        path = os.path.join(KAGGLE_DIR, fname)
        if os.path.exists(path):
            csv_path = path
            break

    if csv_path is None:
        if os.path.isdir(KAGGLE_DIR):
            all_f = os.listdir(KAGGLE_DIR)
            pop_f = [f for f in all_f if 'population' in f.lower() and 'growth' in f.lower()]
            if pop_f:
                csv_path = os.path.join(KAGGLE_DIR, pop_f[0])

    if csv_path is None:
        print("⚠️ G2-1 파일 미발견 — 스킵")
        return

    print(f"\n📥 G2-1 로딩: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   열: {df.columns.tolist()}")
    print(f"   크기: {df.shape}")

    # 타겟 도시 필터 (부분 매칭)
    city_col = None
    for c in df.columns:
        if 'city' in c.lower() or 'name' in c.lower():
            city_col = c
            break

    if city_col:
        mask = df[city_col].str.lower().str.contains('|'.join([c.lower() for c in TARGET_CITIES]), na=False)
        df_target = df[mask].copy()
        print(f"   타겟 도시 필터: {len(df_target)}행")

        if df_target.empty:
            print("   ℹ️ 타겟 도시 미발견 — 전체 적재")
            df_target = df
    else:
        df_target = df

    df_target = df_target.where(pd.notnull(df_target), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO world_city_population_growth
             (city_name, country, population_2023, population_2024, growth_rate, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df_target.iterrows():
        city = r.get(city_col)
        country = None
        for c in df_target.columns:
            if 'country' in c.lower():
                country = r.get(c)
                break

        pop_2023, pop_2024, growth = None, None, None
        for c in df_target.columns:
            cl = c.lower()
            if '2023' in cl and 'pop' in cl:
                pop_2023 = r.get(c)
            elif '2024' in cl and 'pop' in cl:
                pop_2024 = r.get(c)
            elif 'growth' in cl or 'rate' in cl:
                growth = r.get(c)

        rows.append((
            city, country,
            int(pop_2023) if pd.notna(pop_2023) else None,
            int(pop_2024) if pd.notna(pop_2024) else None,
            float(growth) if pd.notna(growth) else None,
            'G2-1 World Pop Growth 2024',
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   ✅ world_city_population_growth: {len(rows)}행")


if __name__ == '__main__':
    load_world_population_growth()
    print("\n🎉 S2 STEP 6 완료")
```

---

## 🔨 STEP 7: 상관분석 데이터 구축

### 파일: `src/s2_step7_build_correlation.py`

```python
"""
STEP 7: 인구-부동산 상관분석용 통합 테이블 구축 → annual_pop_housing_merged
실행: python src/s2_step7_build_correlation.py
의존: 소주제1(us_metro_zhvi), S2 step2~6 모든 테이블
"""
import pandas as pd
import numpy as np
from scipy import stats
import pymysql
from step0_init_db import get_connection, DB_NAME


def build_us_annual_merged():
    """미국 4도시: 인구 + ZHVI + 수급지표 → 연도별 통합"""
    print("\n📊 미국 연도별 통합 데이터 구축")

    conn = get_connection(DB_NAME)

    # ── A. ZHVI 연평균 (소주제1 us_metro_zhvi 재사용) ──
    df_zhvi = pd.read_sql("""
        SELECT
            CASE
                WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
                WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
                WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
                WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
            END AS city_name,
            LEFT(year_month, 4) AS year,
            AVG(zhvi) AS zhvi
        FROM us_metro_zhvi
        WHERE region_name NOT LIKE '%United States%'
        GROUP BY city_name, year
        HAVING city_name IS NOT NULL
    """, conn)
    df_zhvi['year'] = df_zhvi['year'].astype(int)

    # ZHVI YoY 변동률
    df_zhvi = df_zhvi.sort_values(['city_name', 'year'])
    df_zhvi['zhvi_change_rate'] = df_zhvi.groupby('city_name')['zhvi'].pct_change() * 100

    # ── B. 수급 지표 연평균 (us_metro_demand) ──
    df_demand = pd.read_sql("""
        SELECT
            CASE
                WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
                WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
                WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
                WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
            END AS city_name,
            LEFT(year_month, 4) AS year,
            AVG(sales_count) AS avg_sales_count,
            AVG(inventory) AS avg_inventory,
            AVG(market_temp_index) AS avg_market_temp,
            AVG(mean_days_pending) AS avg_days_pending,
            AVG(income_needed) AS avg_income_needed
        FROM us_metro_demand
        WHERE region_name NOT LIKE '%United States%'
        GROUP BY city_name, year
        HAVING city_name IS NOT NULL
    """, conn)
    df_demand['year'] = df_demand['year'].astype(int)

    # ── C. 인구 데이터 (US Census — 포인트 데이터이므로 가용 연도만) ──
    df_pop = pd.read_sql("""
        SELECT
            c.city_name,
            d.census_year AS year,
            SUM(d.total_population) AS population,
            AVG(d.median_income) AS median_income,
            AVG(d.unemployment) AS unemployment
        FROM us_census_demographics d
        JOIN cities c ON d.city_id = c.city_id
        WHERE d.city_id IS NOT NULL
        GROUP BY c.city_name, d.census_year
    """, conn)

    conn.close()

    # ── MERGE ──
    merged = df_zhvi.merge(df_demand, on=['city_name', 'year'], how='outer')
    merged = merged.merge(df_pop, on=['city_name', 'year'], how='left')

    # 수급 비율 (재고 / 판매건수 = 몇 개월분 재고)
    merged['supply_demand_ratio'] = np.where(
        merged['avg_sales_count'] > 0,
        merged['avg_inventory'] / merged['avg_sales_count'],
        None
    )

    merged['country'] = 'USA'

    print(f"   미국 통합: {len(merged)}행")
    print(f"   도시: {merged['city_name'].unique()}")
    print(f"   연도: {merged['year'].min()} ~ {merged['year'].max()}")

    return merged


def build_kr_annual_merged():
    """대구: 인구 + 주택가격 + 거래건수 → 연도별 통합"""
    print("\n📊 대구 연도별 통합 데이터 구축")

    conn = get_connection(DB_NAME)

    # ── 인구 ──
    df_pop = pd.read_sql("""
        SELECT year, total_population AS population,
               population_change_rate AS pop_change_rate,
               economic_activity_rate
        FROM daegu_population_summary
        ORDER BY year
    """, conn)

    # ── 소득 ──
    df_income = pd.read_sql("""
        SELECT year, household_income AS median_income
        FROM korean_income_welfare
        WHERE region LIKE '%대구%'
    """, conn)

    # ── 주택가격+거래량 (소주제1 daegu_monthly_summary 재사용) ──
    df_housing = pd.read_sql("""
        SELECT
            LEFT(year_month, 4) AS year,
            AVG(avg_price) AS zhvi,
            SUM(transaction_count) AS total_transactions
        FROM daegu_monthly_summary
        WHERE district IS NOT NULL
        GROUP BY LEFT(year_month, 4)
    """, conn)

    conn.close()

    if df_pop.empty:
        print("   ⚠️ 대구 인구 데이터 없음")
        return pd.DataFrame()

    df_housing['year'] = df_housing['year'].astype(int) if not df_housing.empty else df_housing['year']

    merged = df_pop.merge(df_housing, on='year', how='left')
    merged = merged.merge(df_income, on='year', how='left')

    # ZHVI 변동률
    merged = merged.sort_values('year')
    merged['zhvi_change_rate'] = merged['zhvi'].pct_change() * 100

    # 대구는 월 평균 거래건수로 환산
    merged['avg_sales_count'] = merged['total_transactions'] / 12

    merged['city_name'] = '대구'
    merged['country'] = 'South Korea'

    print(f"   대구 통합: {len(merged)}행")

    return merged


def save_merged_to_db(df):
    """통합 데이터 → annual_pop_housing_merged 적재"""
    if df.empty:
        return

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE annual_pop_housing_merged")

    sql = """INSERT INTO annual_pop_housing_merged
             (city_name, country, year, population, pop_change_rate,
              median_income, zhvi, zhvi_change_rate,
              avg_sales_count, avg_inventory, avg_market_temp,
              avg_days_pending, avg_income_needed, supply_demand_ratio)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            r.get('city_name'), r.get('country'),
            int(r['year']),
            int(r['population']) if pd.notna(r.get('population')) else None,
            float(r['pop_change_rate']) if pd.notna(r.get('pop_change_rate')) else None,
            float(r['median_income']) if pd.notna(r.get('median_income')) else None,
            float(r['zhvi']) if pd.notna(r.get('zhvi')) else None,
            float(r['zhvi_change_rate']) if pd.notna(r.get('zhvi_change_rate')) else None,
            float(r['avg_sales_count']) if pd.notna(r.get('avg_sales_count')) else None,
            float(r['avg_inventory']) if pd.notna(r.get('avg_inventory')) else None,
            float(r['avg_market_temp']) if pd.notna(r.get('avg_market_temp')) else None,
            float(r['avg_days_pending']) if pd.notna(r.get('avg_days_pending')) else None,
            float(r['avg_income_needed']) if pd.notna(r.get('avg_income_needed')) else None,
            float(r['supply_demand_ratio']) if pd.notna(r.get('supply_demand_ratio')) else None,
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"\n✅ annual_pop_housing_merged 적재: {len(rows)}행")


def compute_correlations(df):
    """상관분석 수행 → population_housing_correlation"""
    print("\n📊 상관분석 수행")

    results = []

    pairs = [
        ('pop_change_rate', 'zhvi_change_rate', '인구변동률 vs ZHVI변동률'),
        ('pop_change_rate', 'avg_sales_count', '인구변동률 vs 판매건수'),
        ('pop_change_rate', 'avg_market_temp', '인구변동률 vs 시장온도'),
        ('pop_change_rate', 'avg_days_pending', '인구변동률 vs 대기일수'),
        ('pop_change_rate', 'supply_demand_ratio', '인구변동률 vs 수급비율'),
        ('population', 'zhvi', '총인구 vs ZHVI'),
        ('median_income', 'zhvi', '중위소득 vs ZHVI'),
        ('median_income', 'avg_income_needed', '중위소득 vs 필요소득'),
    ]

    for city in df['city_name'].unique():
        city_df = df[df['city_name'] == city].dropna()
        country = city_df['country'].iloc[0] if not city_df.empty else ''
        period = f"{city_df['year'].min()}-{city_df['year'].max()}" if not city_df.empty else ''

        for x_var, y_var, desc in pairs:
            sub = city_df[[x_var, y_var]].dropna()
            if len(sub) < 5:
                continue

            r, p = stats.pearsonr(sub[x_var], sub[y_var])

            sig = ''
            if p < 0.001:
                sig = '***'
            elif p < 0.01:
                sig = '**'
            elif p < 0.05:
                sig = '*'

            # 해석
            direction = '양의' if r > 0 else '음의'
            strength = '강한' if abs(r) > 0.7 else '보통' if abs(r) > 0.4 else '약한'

            results.append({
                'city_name': city, 'country': country,
                'analysis_period': period,
                'x_variable': x_var, 'y_variable': y_var,
                'pearson_r': round(r, 4), 'p_value': round(p, 8),
                'n_observations': len(sub), 'significance': sig,
                'interpretation': f'{desc}: {strength} {direction} 상관 (r={r:.3f})',
            })

    if not results:
        print("   ⚠️ 상관분석 결과 없음")
        return

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE population_housing_correlation")

    sql = """INSERT INTO population_housing_correlation
             (city_name, country, analysis_period,
              x_variable, y_variable, pearson_r, p_value,
              n_observations, significance, interpretation)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = [tuple(r.values()) for r in results]
    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()

    print(f"   ✅ 상관분석 결과: {len(results)}건")
    for res in results:
        print(f"      {res['city_name']:10s} | {res['x_variable']:25s} → {res['y_variable']:25s} | "
              f"r={res['pearson_r']:+.3f} {res['significance']}")


if __name__ == '__main__':
    df_us = build_us_annual_merged()
    df_kr = build_kr_annual_merged()

    df_all = pd.concat([df_us, df_kr], ignore_index=True)
    save_merged_to_db(df_all)
    compute_correlations(df_all)

    print("\n🎉 S2 STEP 7 완료")
```

---

## 🔨 STEP 8: 분석 쿼리

### 파일: `src/s2_step8_analysis_queries.py`

```python
"""
STEP 8: 소주제2 분석 SQL 쿼리 모음
실행: python src/s2_step8_analysis_queries.py
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
# Q1: 시장온도지수 추이 — 4도시 비교 (2018~2025)
# ============================================================
Q1_MARKET_TEMP = """
SELECT
    year_month,
    CASE
        WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
        WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
        WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
        WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
        WHEN region_name LIKE '%United States%' THEN 'US Average'
    END AS city,
    market_temp_index,
    inventory,
    sales_count,
    mean_days_pending,
    income_needed
FROM us_metro_demand
ORDER BY city, year_month
"""

# ============================================================
# Q2: 수급 균형 지표 (재고 / 판매건수 = 몇 개월분 재고)
# ============================================================
Q2_SUPPLY_DEMAND = """
SELECT
    year_month,
    CASE
        WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
        WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
        WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
        WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
    END AS city,
    inventory,
    sales_count,
    ROUND(inventory / NULLIF(sales_count, 0), 2) AS months_of_supply
FROM us_metro_demand
WHERE region_name NOT LIKE '%United States%'
  AND inventory IS NOT NULL
  AND sales_count IS NOT NULL
ORDER BY city, year_month
"""

# ============================================================
# Q3: 대구 인구 추이 + 인구변동률
# ============================================================
Q3_DAEGU_POP = """
SELECT
    year,
    total_population,
    population_change,
    population_change_rate,
    natural_increase,
    economic_activity_rate
FROM daegu_population_summary
ORDER BY year
"""

# ============================================================
# Q4: 인구-ZHVI 통합 비교 (연도별)
# ============================================================
Q4_POP_HOUSING = """
SELECT
    city_name,
    country,
    year,
    population,
    pop_change_rate,
    zhvi,
    zhvi_change_rate,
    avg_sales_count,
    avg_market_temp,
    supply_demand_ratio
FROM annual_pop_housing_merged
ORDER BY city_name, year
"""

# ============================================================
# Q5: 상관분석 결과 요약
# ============================================================
Q5_CORRELATION = """
SELECT
    city_name,
    x_variable,
    y_variable,
    pearson_r,
    p_value,
    significance,
    interpretation
FROM population_housing_correlation
ORDER BY city_name, ABS(pearson_r) DESC
"""

# ============================================================
# Q6: 주택구매 필요소득 추이 (구매력 진입장벽)
# ============================================================
Q6_INCOME_NEEDED = """
SELECT
    year_month,
    CASE
        WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
        WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
        WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
        WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
        WHEN region_name LIKE '%United States%' THEN 'US Average'
    END AS city,
    income_needed
FROM us_metro_demand
WHERE income_needed IS NOT NULL
ORDER BY city, year_month
"""

# ============================================================
# Q7: 미국 County별 인구·소득 비교 (4개 핵심 County)
# ============================================================
Q7_COUNTY_COMPARE = """
SELECT
    c.city_name,
    d.county,
    d.state,
    d.census_year,
    d.total_population,
    d.median_income,
    d.unemployment,
    d.professional,
    d.mean_commute
FROM us_census_demographics d
JOIN cities c ON d.city_id = c.city_id
WHERE d.city_id IS NOT NULL
ORDER BY c.city_name, d.census_year
"""

# ============================================================
# Q8: 글로벌 도시 인구성장률 비교 (대구 vs 미국 4도시)
# ============================================================
Q8_GLOBAL_POP = """
SELECT city_name, country, population_2024, growth_rate
FROM world_city_population_growth
WHERE city_name IN ('Daegu', 'Dallas', 'Atlanta', 'Phoenix', 'Charlotte')
   OR city_name LIKE '%대구%'
   OR city_name LIKE '%daegu%'
ORDER BY growth_rate DESC
"""

# ============================================================
# Q9: 판매건수 추이 — 수요 강도 (2008~2025)
# ============================================================
Q9_SALES_TREND = """
SELECT
    year_month,
    CASE
        WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
        WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
        WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
        WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
    END AS city,
    sales_count
FROM us_metro_demand
WHERE region_name NOT LIKE '%United States%'
  AND sales_count IS NOT NULL
ORDER BY city, year_month
"""

# ============================================================
# Q10: 대구 인구유출 vs 미국 인구유입 — 반대 방향 효과 대조표
# ============================================================
Q10_DIRECTION_CONTRAST = """
SELECT
    city_name,
    country,
    year,
    pop_change_rate,
    zhvi_change_rate,
    avg_market_temp,
    CASE
        WHEN pop_change_rate > 0 AND zhvi_change_rate > 0 THEN '인구유입+가격상승'
        WHEN pop_change_rate > 0 AND zhvi_change_rate <= 0 THEN '인구유입+가격하락'
        WHEN pop_change_rate <= 0 AND zhvi_change_rate > 0 THEN '인구유출+가격상승'
        WHEN pop_change_rate <= 0 AND zhvi_change_rate <= 0 THEN '인구유출+가격하락'
    END AS pattern
FROM annual_pop_housing_merged
WHERE pop_change_rate IS NOT NULL
  AND zhvi_change_rate IS NOT NULL
ORDER BY city_name, year
"""


if __name__ == '__main__':
    queries = {
        'S2_Q1_MARKET_TEMP': Q1_MARKET_TEMP,
        'S2_Q2_SUPPLY_DEMAND': Q2_SUPPLY_DEMAND,
        'S2_Q3_DAEGU_POP': Q3_DAEGU_POP,
        'S2_Q4_POP_HOUSING': Q4_POP_HOUSING,
        'S2_Q5_CORRELATION': Q5_CORRELATION,
        'S2_Q6_INCOME_NEEDED': Q6_INCOME_NEEDED,
        'S2_Q7_COUNTY_COMPARE': Q7_COUNTY_COMPARE,
        'S2_Q8_GLOBAL_POP': Q8_GLOBAL_POP,
        'S2_Q9_SALES_TREND': Q9_SALES_TREND,
        'S2_Q10_DIRECTION_CONTRAST': Q10_DIRECTION_CONTRAST,
    }

    os.makedirs('output', exist_ok=True)

    for name, sql in queries.items():
        print(f"\n{'='*60}")
        print(f"📊 {name}")
        print('='*60)
        try:
            df = query_to_df(sql)
            print(df.head(10).to_string(index=False))
            print(f"... 총 {len(df)}행")
            df.to_csv(f'output/{name}.csv', index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"   ❌ 에러: {e}")

    print("\n🎉 S2 STEP 8 완료")
```

---

## 🔨 STEP 9: 시각화

### 파일: `src/s2_step9_visualization.py`

```python
"""
STEP 9: 소주제2 시각화 (6개 차트)
실행: python src/s2_step9_visualization.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
from step0_init_db import get_connection, DB_NAME
from s2_step8_analysis_queries import query_to_df
from s2_step8_analysis_queries import (
    Q1_MARKET_TEMP, Q2_SUPPLY_DEMAND, Q3_DAEGU_POP,
    Q4_POP_HOUSING, Q5_CORRELATION, Q6_INCOME_NEEDED,
    Q9_SALES_TREND, Q10_DIRECTION_CONTRAST,
)

plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows; Mac: AppleGothic
plt.rcParams['axes.unicode_minus'] = False
os.makedirs('output', exist_ok=True)

COLORS = {
    'Dallas': '#E74C3C', 'Atlanta': '#3498DB',
    'Phoenix': '#E67E22', 'Charlotte': '#2ECC71',
    'US Average': '#95A5A6', '대구': '#9B59B6',
}


def viz1_market_temp_dashboard():
    """차트 1: 시장온도 + 재고 + 판매건수 복합 대시보드"""
    df = query_to_df(Q1_MARKET_TEMP)
    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    df['date'] = pd.to_datetime(df['year_month'])
    cities = [c for c in df['city'].unique() if c and c != 'US Average']

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    # 상: 시장온도지수
    for city in cities + ['US Average']:
        sub = df[df['city'] == city]
        ls = '--' if city == 'US Average' else '-'
        axes[0].plot(sub['date'], sub['market_temp_index'],
                     color=COLORS.get(city, 'gray'), label=city, linestyle=ls)
    axes[0].axhline(y=50, color='black', linewidth=0.8, linestyle=':')
    axes[0].set_ylabel('Market Temp Index')
    axes[0].set_title('시장온도지수 (50=균형, 80+=과열)', fontsize=13)
    axes[0].legend(ncol=5, fontsize=8)

    # 중: 매물 재고량
    for city in cities:
        sub = df[df['city'] == city]
        axes[1].plot(sub['date'], sub['inventory'],
                     color=COLORS.get(city, 'gray'), label=city)
    axes[1].set_ylabel('Inventory (건)')
    axes[1].set_title('매물 재고량')

    # 하: 판매 건수
    for city in cities:
        sub = df[df['city'] == city]
        axes[2].plot(sub['date'], sub['sales_count'],
                     color=COLORS.get(city, 'gray'), label=city)
    axes[2].set_ylabel('Sales Count')
    axes[2].set_title('월별 판매 건수')

    for ax in axes:
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/s2_viz1_market_dashboard.png', dpi=150)
    plt.close()
    print("✅ s2_viz1_market_dashboard.png")


def viz2_supply_demand_ratio():
    """차트 2: 수급비율 (Months of Supply)"""
    df = query_to_df(Q2_SUPPLY_DEMAND)
    if df.empty:
        print("⚠️ 데이터 없음 — 스킵"); return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for city in df['city'].dropna().unique():
        sub = df[df['city'] == city]
        ax.plot(sub['date'], sub['months_of_supply'],
                color=COLORS.get(city, 'gray'), label=city)

    ax.axhline(y=6, color='red', linewidth=1, linestyle='--', label='균형선 (6개월)')
    ax.axhspan(0, 4, alpha=0.05, color='red')      # 판매자 우위
    ax.axhspan(6, 10, alpha=0.05, color='blue')     # 구매자 우위

    ax.set_title('수급 균형 지표: Months of Supply (재고 ÷ 판매건수)', fontsize=13)
    ax.set_ylabel('개월')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/s2_viz2_supply_demand.png', dpi=150)
    plt.close()
    print("✅ s2_viz2_supply_demand.png")


def viz3_daegu_population():
    """차트 3: 대구 인구 추이 + 변동률 이중축"""
    df = query_to_df(Q3_DAEGU_POP)
    if df.empty:
        print("⚠️ 대구 인구 데이터 없음 — 스킵"); return

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    ax1.bar(df['year'], df['total_population'] / 10000, color='#9B59B6', alpha=0.6, label='총인구 (만명)')
    ax2.plot(df['year'], df['population_change_rate'], color='#E74C3C', marker='o',
             linewidth=2, label='인구변동률 (%)')
    ax2.axhline(y=0, color='black', linewidth=0.8, linestyle=':')

    ax1.set_xlabel('연도')
    ax1.set_ylabel('총인구 (만명)', color='#9B59B6')
    ax2.set_ylabel('인구변동률 (%)', color='#E74C3C')
    ax1.set_title('대구광역시 인구 추이 및 변동률', fontsize=13)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    plt.tight_layout()
    plt.savefig('output/s2_viz3_daegu_pop.png', dpi=150)
    plt.close()
    print("✅ s2_viz3_daegu_pop.png")


def viz4_pop_vs_zhvi_scatter():
    """차트 4: 인구변동률 vs ZHVI변동률 산점도 + 회귀선"""
    df = query_to_df(Q4_POP_HOUSING)
    df = df.dropna(subset=['pop_change_rate', 'zhvi_change_rate'])

    if df.empty:
        print("⚠️ 통합 데이터 부족 — 스킵"); return

    fig, ax = plt.subplots(figsize=(10, 8))

    for city in df['city_name'].unique():
        sub = df[df['city_name'] == city]
        ax.scatter(sub['pop_change_rate'], sub['zhvi_change_rate'],
                   color=COLORS.get(city, 'gray'), label=city, s=60, alpha=0.7)

    # 전체 회귀선
    from numpy.polynomial.polynomial import polyfit
    x = df['pop_change_rate'].values
    y = df['zhvi_change_rate'].values
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 2:
        b, m = polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(x_line, b + m * x_line, 'k--', linewidth=1, alpha=0.5, label=f'추세선 (기울기={m:.2f})')

    ax.axhline(y=0, color='gray', linewidth=0.5)
    ax.axvline(x=0, color='gray', linewidth=0.5)

    ax.set_xlabel('인구변동률 (%)')
    ax.set_ylabel('ZHVI 변동률 (%)')
    ax.set_title('인구변동률 vs 주택가치 변동률 — 도시별 산점도', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig('output/s2_viz4_pop_zhvi_scatter.png', dpi=150)
    plt.close()
    print("✅ s2_viz4_pop_zhvi_scatter.png")


def viz5_income_needed():
    """차트 5: 주택구매 필요소득 추이"""
    df = query_to_df(Q6_INCOME_NEEDED)
    if df.empty:
        print("⚠️ 필요소득 데이터 없음 — 스킵"); return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for city in df['city'].dropna().unique():
        sub = df[df['city'] == city]
        ls = '--' if city == 'US Average' else '-'
        ax.plot(sub['date'], sub['income_needed'],
                color=COLORS.get(city, 'gray'), label=city, linestyle=ls)

    ax.set_title('주택 구매 필요 연소득 추이 (계약금 20% 기준)', fontsize=13)
    ax.set_ylabel('필요 연소득 (USD)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('output/s2_viz5_income_needed.png', dpi=150)
    plt.close()
    print("✅ s2_viz5_income_needed.png")


def viz6_correlation_heatmap():
    """차트 6: 상관계수 히트맵"""
    df = query_to_df(Q5_CORRELATION)
    if df.empty:
        print("⚠️ 상관분석 결과 없음 — 스킵"); return

    # 피벗: 행=도시, 열=변수쌍, 값=pearson_r
    df['pair'] = df['x_variable'] + '\nvs\n' + df['y_variable']
    pivot = df.pivot_table(index='city_name', columns='pair', values='pearson_r')

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                vmin=-1, vmax=1, ax=ax, linewidths=0.5)
    ax.set_title('도시별 인구-부동산 상관계수 히트맵', fontsize=13)

    plt.tight_layout()
    plt.savefig('output/s2_viz6_correlation_heatmap.png', dpi=150)
    plt.close()
    print("✅ s2_viz6_correlation_heatmap.png")


if __name__ == '__main__':
    viz1_market_temp_dashboard()
    viz2_supply_demand_ratio()
    viz3_daegu_population()
    viz4_pop_vs_zhvi_scatter()
    viz5_income_needed()
    viz6_correlation_heatmap()
    print("\n🎉 S2 STEP 9 완료: 시각화 → output/")
```

---

## 🚀 실행 순서 요약

```bash
# 사전: 소주제1이 완료된 상태여야 함 (cities, us_metro_zhvi, daegu_monthly_summary 필요)
pip install pymysql pandas numpy scipy matplotlib seaborn

# 1. 테이블 생성
python src/s2_step1_create_tables.py

# 2. 미국 수급 지표 (data/ 폴더 — 5개 Wide 파일)
python src/s2_step2_load_zillow_demand.py

# 3. 미국 수급 시계열 (Zillow Economics Long)
python src/s2_step3_load_zillow_economics_demand.py

# 4. 한국 인구통계 (Kaggle)
python src/s2_step4_load_kr_demographics.py

# 5. 미국 인구통계 (Kaggle)
python src/s2_step5_load_us_demographics.py

# 6. 글로벌 인구 데이터 (Kaggle)
python src/s2_step6_load_global_population.py

# 7. 상관분석 통합 데이터 구축
python src/s2_step7_build_correlation.py

# 8. 분석 쿼리 → CSV
python src/s2_step8_analysis_queries.py

# 9. 시각화 → PNG
python src/s2_step9_visualization.py
```

---

## ⚠️ Claude Code 실행 시 체크리스트

| # | 확인 사항 | 확인 방법 |
|---|----------|----------|
| 1 | **소주제1 완료 여부** | `SELECT COUNT(*) FROM cities` → 5행 확인 |
| 2 | **소주제1 ZHVI 적재** | `SELECT COUNT(*) FROM us_metro_zhvi` → 0이면 소주제1 step2 먼저 |
| 3 | **zillow_Housing 5개 파일 존재** | `ls data/zillow_Housing/Metro_invt*`, `Metro_market*` 등 |
| 4 | **Kaggle 인구 파일명 확인** | `ls kaggle_data/` → 실제 파일명으로 step4, 5, 6 수정 |
| 5 | **Wide CSV RegionName 매칭** | `pd.read_csv(파일, nrows=5)['RegionName']` → TARGET_METROS 확인 |
| 6 | **Korean Demographics 인코딩** | `cp949` / `utf-8` / `euc-kr` 자동 감지 내장 |
| 7 | **Korean Demographics region 값** | `'대구광역시'` vs `'대구'` vs `'Daegu'` 확인 필요 |
| 8 | **US Census state 열 형식** | 약어(`TX`) vs 풀네임(`Texas`) 확인 |
| 9 | **scipy 설치** | `pip install scipy` (상관분석용) |

### 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| `Table 'us_metro_zhvi' doesn't exist` | 소주제1 미실행 | 소주제1 step1~2 먼저 실행 |
| `대구 데이터 없음 (0행)` | `region` 열 값 불일치 | `SELECT DISTINCT region FROM korean_demographics` 확인 후 LIKE 조건 수정 |
| `MERGE 결과 0행` | Wide 파일 RegionName 불일치 | `check_and_fix_metro_names()` (step2에서 자동 출력) |
| `scipy ImportError` | 미설치 | `pip install scipy` |
| `MemoryError` | Metro_time_series 56MB | `chunksize=5000`으로 줄이기 |

---

## 📊 최종 산출물

| 산출물 | 위치 | 설명 |
|--------|------|------|
| **DB 테이블 12개** | MySQL | korean_demographics, korean_income_welfare, daegu_population_summary, us_census_demographics, us_population_timeseries, us_county_historical, world_city_population_growth, us_metro_demand, zillow_demand_timeseries, population_housing_correlation, annual_pop_housing_merged |
| **분석 CSV 10개** | `output/S2_Q1~Q10_*.csv` | 각 쿼리 결과 |
| **시각화 6개** | `output/s2_viz1~6_*.png` | 시장온도 대시보드, 수급비율, 대구 인구, 산점도+회귀, 필요소득, 상관 히트맵 |

### 핵심 인사이트 기대값

| 도시 | 인구 방향 | 기대 패턴 |
|------|----------|----------|
| **대구** | 유출 (−) | 수요↓ → 시장 냉각 → 가격 정체/하락 |
| **Dallas** | 유입 (+) | 수요↑ → 재고↓ → 시장 과열 → 가격 급등 |
| **Atlanta** | 유입 (+) | 수요↑ + 산업허브 → 소득↑ + 가격↑ |
| **Phoenix** | 폭발 유입 | 극단적 과열 → 급등 후 조정 패턴 |
| **Charlotte** | 산업전환 유입 | 소득 구조 변화 → 필요소득 급상승 |
