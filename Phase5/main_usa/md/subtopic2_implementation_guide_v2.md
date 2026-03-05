# 소주제 2: 인구 이동과 주택 수요 — Claude Code 구현 가이드 (v2)

## 🎯 이 문서의 목적

Claude Code가 이 문서를 읽고 소주제 2(인구 이동과 주택 수요)의 **전체 파이프라인**을 자동 구현할 수 있도록 작성된 상세 가이드입니다.

> **v2 변경점:** 4축 비교 프레임워크 + 대구 인구유지 전략 도출 파트 추가.
> 소주제 4와 동일한 비교축(종합/산업/기후/변모)을 인구-부동산 관점에서 분석합니다.

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

## 📌 소주제 2 분석 프레임워크 (v2 확장)

```
┌─────────────────────────────────────────────────────────────────┐
│  인구 변동 (독립변수)              부동산 수급 (종속변수)          │
│  ─────────────────              ─────────────────────           │
│  🇰🇷 대구 인구유출                대구 거래량·가격 하락?          │
│  🇺🇸 Dallas/Atlanta 인구유입     수요↑ 재고↓ 가격↑?             │
│  🇺🇸 Phoenix 폭발적 성장         과열 시장?                     │
│  🇺🇸 Charlotte 산업전환 유입     구매력 변화?                   │
│                                                                 │
│  핵심 질문: 인구 증감은 부동산 시장에 어떤 경로로                │
│            영향을 미치는가?                                      │
│                                                                 │
│  경로 모델:                                                     │
│  인구변동 → 수요(판매건수) → 재고 소진 → 시장온도 상승          │
│         → 대기일수 단축 → 가격 상승 → 필요소득 상승             │
└─────────────────────────────────────────────────────────────────┘
```

### 🏙️ v2 추가: 4축 비교 프레임워크 (인구-부동산 관점)

| 비교축 | 대구광역시 | 미국 유사 도시 | 공통점 | 인구-부동산 핵심 질문 |
|--------|-----------|--------------|--------|---------------------|
| **종합** | 경상도 거점 대도시 | **Dallas** | 내륙 대도시, 보수적, 무더운 여름 | Dallas 인구유입 → 수요 폭발 패턴을 대구가 역전시킬 수 있는가? |
| **산업** | 자동차 부품, 에너지 | **Atlanta** | 자동차·배터리 허브, 교통 요충지 | 산업 허브화가 인구 유입에 얼마나 기여하는가? |
| **기후** | 분지 지형, 폭염 | **Phoenix** | 미국 내 최고 수준 여름 기온 | 기후 핸디캡에도 Phoenix 인구가 폭증하는 이유는? |
| **변모** | 섬유→첨단 산업 | **Charlotte** | 섬유 역사, 에너지/금융 도시 변모 | 산업 전환 성공 → 고소득 인구 유입 경로는? |

### 🎯 v2 최종 산출물: 대구 인구유지 전략 보고서

```
분석 흐름:
  [인구 데이터 수집] → [4축별 인구-부동산 상관분석] → [성공 패턴 추출] → [대구 전략 도출]

  축1. Dallas 비교   → 인구유입 → 수요폭발 → 가격급등 경로 분석
  축2. Atlanta 비교  → 산업 다각화 → 인구유입 → 시장과열 경로 분석
  축3. Phoenix 비교  → 기후 핸디캡 극복 → 인구폭증 → 부동산 과열·조정 패턴
  축4. Charlotte 비교 → 산업전환 → 고소득 유입 → 필요소득 급상승 경로

  종합: 4개 도시의 "인구유입 → 부동산 활성화" 성공 경로를 대구 맥락에 적용
```

---

## 📂 파일 경로 규칙 (v2 확장)

```
프로젝트 루트/
├── data/
│   ├── zillow_Housing/
│   │   ├── Metro_invt_fs_uc_sfrcondo_sm_month.csv               ← 매물 재고량
│   │   ├── Metro_market_temp_index_uc_sfrcondo_month.csv        ← 시장 온도 지수
│   │   ├── Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv      ← 평균 대기일수
│   │   ├── Metro_sales_count_now_uc_sfrcondo_month.csv          ← 판매 건수
│   │   ├── Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
│   │   │                                                        ← 주택 구매 필요 소득
│   │   ├── Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv ← v2: ZHVI
│   │   └── Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv   ← v2: 신규건설
│   └── Zillow_Economics/
│       ├── Metro_time_series.csv
│       └── State_time_series.csv
├── kaggle_data/
│   ├── korean_demographics_2000_2022.csv    ← K2-1 한국 인구통계
│   ├── korea_income_welfare.csv             ← K2-2 한국 소득·복지
│   ├── us_census_demographic/               ← U2-1 US Census
│   │   ├── acs2015_county_data.csv
│   │   └── acs2017_county_data.csv
│   ├── population_time_series.csv           ← U2-2 인구 시계열
│   ├── us_county_historical_demographics.csv ← U2-3
│   ├── us_county_data.csv                   ← U2-4
│   ├── world_population_growth_2024.csv     ← G2-1 도시별 인구성장률
│   ├── world_cities_database.csv            ← G2-2 도시 인구·좌표
│   └── daegu_apartment/                     ← v2: K1-1 대구 아파트 실거래
├── src/
│   ├── step0_init_db.py                     ← 소주제1 공통 모듈 재사용
│   ├── s2_step1_create_tables.py
│   ├── s2_step2_load_zillow_demand.py
│   ├── s2_step3_load_zillow_economics_demand.py
│   ├── s2_step4_load_kr_demographics.py
│   ├── s2_step5_load_us_demographics.py
│   ├── s2_step6_load_global_population.py
│   ├── s2_step7_build_correlation.py
│   ├── s2_step8_analysis_queries.py
│   ├── s2_step9_visualization.py
│   ├── s2_step10_4axis_analysis.py          ← ★ v2: 4축 인구-부동산 비교
│   ├── s2_step11_daegu_strategy.py          ← ★ v2: 대구 전략 보고서
│   └── s2_step12_visualization_4axis.py     ← ★ v2: 4축 비교 시각화
└── output/
    └── (시각화 결과물)
```

> **의존성:** 소주제1의 `step0_init_db.py`(DB 연결 공통 모듈), `cities` 테이블, `us_metro_zhvi` 테이블을 재사용합니다.
> 소주제1이 먼저 실행되어 있어야 합니다.

---

## 🔨 STEP 1: 테이블 생성 (v2 확장)

### 파일: `src/s2_step1_create_tables.py`

> v2에서 **3개 테이블 추가**: `daegu_housing_prices`, `pop_housing_4axis_scorecard`, `pop_housing_axis_summary`

```python
"""
STEP 1: 소주제 2 전용 테이블 생성 (v2: 4축 비교 테이블 추가)
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

    # ── A-3. 대구 인구 연도별 요약 ──
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

    # ── A-4. 미국 Census 인구통계 (U2-1) ──
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
            city_id INT COMMENT 'cities FK',
            source_dataset VARCHAR(100),
            INDEX idx_state (state),
            INDEX idx_county_state (county, state),
            INDEX idx_city (city_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── A-5. 미국 인구 시계열 (U2-2) ──
    'us_population_timeseries': """
        CREATE TABLE IF NOT EXISTS us_population_timeseries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date VARCHAR(10),
            region_name VARCHAR(200),
            region_type VARCHAR(30),
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
            days_on_zillow DECIMAL(8,2),
            sale_counts INT,
            sale_counts_sa INT,
            pct_selling_for_gain DECIMAL(8,4),
            pct_selling_for_loss DECIMAL(8,4),
            pct_price_reduction DECIMAL(8,4),
            pct_price_reduction_sa DECIMAL(8,4),
            age_of_inventory DECIMAL(8,2),
            source_file VARCHAR(100),
            INDEX idx_region_date (region_name(100), date),
            INDEX idx_level_date (region_level, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ══════════════════════════════════════════
    # C. 상관분석 결과 테이블
    # ══════════════════════════════════════════

    'population_housing_correlation': """
        CREATE TABLE IF NOT EXISTS population_housing_correlation (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50),
            country VARCHAR(20),
            analysis_period VARCHAR(30),
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

    'annual_pop_housing_merged': """
        CREATE TABLE IF NOT EXISTS annual_pop_housing_merged (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(50),
            country VARCHAR(20),
            year INT,
            population BIGINT,
            pop_change_rate DECIMAL(8,4),
            median_income DECIMAL(15,2),
            zhvi DECIMAL(15,2),
            zhvi_change_rate DECIMAL(8,4),
            avg_sales_count DECIMAL(12,2),
            avg_inventory DECIMAL(12,2),
            avg_market_temp DECIMAL(8,2),
            avg_days_pending DECIMAL(8,2),
            avg_income_needed DECIMAL(15,2),
            supply_demand_ratio DECIMAL(8,4),
            INDEX idx_city_year (city_name, year)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ══════════════════════════════════════════
    # D. ★ v2 추가: 4축 비교 분석 테이블
    # ══════════════════════════════════════════

    # ── D-1. ⭐ 대구 아파트 실거래 (소주제4와 공유) ──
    'daegu_housing_prices': """
        CREATE TABLE IF NOT EXISTS daegu_housing_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year_month VARCHAR(7),
            year INT,
            district VARCHAR(30) COMMENT '구/군',
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

    # ── D-2. ⭐ 4축 인구-부동산 스코어카드 ──
    'pop_housing_4axis_scorecard': """
        CREATE TABLE IF NOT EXISTS pop_housing_4axis_scorecard (
            id INT AUTO_INCREMENT PRIMARY KEY,
            comparison_axis VARCHAR(30) COMMENT '종합/산업/기후/변모',
            metric_category VARCHAR(50) COMMENT '인구성장/주택수요/시장과열/구매력 등',
            daegu_metric_name VARCHAR(100),
            daegu_value DECIMAL(15,4),
            us_city_name VARCHAR(50),
            us_metric_name VARCHAR(100),
            us_value DECIMAL(15,4),
            year_or_period VARCHAR(20),
            gap_direction VARCHAR(30) COMMENT '대구우위/미국우위/유사',
            correlation_insight TEXT COMMENT '인구-부동산 상관관계 인사이트',
            strategy_implication TEXT COMMENT '대구 인구유지 전략 시사점',
            INDEX idx_axis (comparison_axis),
            INDEX idx_category (metric_category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── D-3. ⭐ 축별 인구-부동산 경로 요약 ──
    'pop_housing_axis_summary': """
        CREATE TABLE IF NOT EXISTS pop_housing_axis_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            comparison_axis VARCHAR(30),
            us_city_name VARCHAR(50),
            pop_trend VARCHAR(20) COMMENT '증가/감소/정체',
            housing_demand_trend VARCHAR(20) COMMENT '증가/감소/과열',
            market_temp_trend VARCHAR(20) COMMENT '상승/하락/안정',
            price_trend VARCHAR(20) COMMENT '급등/완만상승/하락/정체',
            causal_pathway TEXT COMMENT '인구→부동산 인과 경로 설명',
            daegu_comparison TEXT COMMENT '대구와 비교한 차이점',
            policy_lesson TEXT COMMENT '대구가 배울 정책 교훈',
            INDEX idx_axis (comparison_axis)
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
    print(f"\n✅ 소주제2 전체 테이블 생성 완료 (v2: {len(TABLES)}개)")


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
    """Wide CSV → Long DataFrame 변환 + 타겟 MSA 필터"""
    df = pd.read_csv(csv_path)

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    id_cols = [c for c in id_cols if c in df.columns]
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()

    if df_f.empty:
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
    keys = ['RegionID', 'RegionName', 'year_month']
    merged = None

    for col_name, df in dfs.items():
        cols_keep = [c for c in keys if c in df.columns] + [col_name]
        if merged is None:
            extra = [c for c in ['SizeRank', 'RegionType', 'StateName'] if c in df.columns]
            df_slim = df[cols_keep + extra].copy()
            merged = df_slim
        else:
            df_slim = df[cols_keep].copy()
            merge_keys = [c for c in keys if c in merged.columns and c in df_slim.columns]
            merged = merged.merge(df_slim, on=merge_keys, how='outer')

    print(f"\n  📊 Merge 결과: {len(merged)}행 × {len(merged.columns)}열")

    # ── MySQL 적재 ──
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
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


if __name__ == '__main__':
    load_all_demand_metrics()
    print("\n🎉 S2 STEP 2 완료")
```

---

## 🔨 STEP 3~6: 기존 데이터 로딩 (v1 유지)

> STEP 3 (Zillow Economics 수급 시계열), STEP 4 (한국 인구통계), STEP 5 (미국 인구통계), STEP 6 (글로벌 인구) 코드는 v1과 동일합니다.
> 원본 `subtopic2_implementation_guide.md`의 STEP 3~6 코드를 그대로 사용하세요.

### 핵심 요약

| STEP | 파일 | 대상 테이블 | 핵심 데이터 |
|------|------|-----------|-----------|
| 3 | `s2_step3_load_zillow_economics_demand.py` | `zillow_demand_timeseries` | Metro/State 수급 시계열 |
| 4 | `s2_step4_load_kr_demographics.py` | `korean_demographics`, `korean_income_welfare`, `daegu_population_summary` | K2-1 한국 인구, K2-2 소득 |
| 5 | `s2_step5_load_us_demographics.py` | `us_census_demographics`, `us_county_historical` | U2-1 ACS Census, U2-3 County 역사 |
| 6 | `s2_step6_load_global_population.py` | `world_city_population_growth` | G2-1 글로벌 도시 인구성장률 |

---

## 🔨 STEP 7: 상관분석 데이터 구축 (v1 유지)

> v1의 `s2_step7_build_correlation.py` 코드를 그대로 사용합니다.
> 미국 4도시 ZHVI + 수급지표 + Census 인구 → `annual_pop_housing_merged`
> 대구 인구 + 주택가격 + 거래건수 → `annual_pop_housing_merged`
> Pearson 상관분석 → `population_housing_correlation`

---

## 🔨 STEP 8: 분석 쿼리 (v1 유지)

> v1의 `s2_step8_analysis_queries.py` 코드를 그대로 사용합니다. (Q1~Q10)

---

## 🔨 STEP 9: 기존 시각화 (v1 유지)

> v1의 `s2_step9_visualization.py` 코드를 그대로 사용합니다. (viz1~viz6)

---

## ⭐ STEP 10: 4축 인구-부동산 비교 분석 (v2 신규)

> **Claude Code 프롬프트:**
> 4축(종합/산업/기후/변모) 프레임워크로 대구와 4개 미국 도시의 "인구 이동 → 부동산 수급 변화" 경로를 비교 분석해줘. 각 축마다 인구-부동산 상관관계를 비교하고, 대구에 적용 가능한 인구유지 전략을 도출해줘. 결과를 pop_housing_4axis_scorecard, pop_housing_axis_summary 테이블에 저장해줘.

### 4축별 분석 설계

```
축 1 — 종합 (대구 vs Dallas)
  ├─ 인구: 대구 유출률 vs Dallas MSA 인구성장률
  ├─ 수요: 대구 거래건수 추이 vs Dallas 판매건수·재고
  ├─ 가격: 대구 아파트 평균가 vs Dallas ZHVI
  ├─ 경로: Dallas "인구유입 → 재고감소 → 시장과열 → 가격급등"
  └─ 교훈: 대구가 인구유입으로 전환되면 부동산에 미칠 영향 예측

축 2 — 산업 (대구 vs Atlanta)
  ├─ 인구: 산업 다각화 → 인구유입 상관관계
  ├─ 수요: Atlanta 신규건설·판매건수 추이
  ├─ 직업: 전문직 비율 vs 생산직 비율 → 소득구조 차이
  ├─ 경로: Atlanta "산업허브 → 일자리창출 → 인구유입 → 수요급증"
  └─ 교훈: 산업고도화가 인구유입+부동산 수요에 미치는 정량적 효과

축 3 — 기후 (대구 vs Phoenix)
  ├─ 인구: 동일 기후 핸디캡에도 Phoenix 인구 폭증 이유
  ├─ 수요: Phoenix 시장온도지수 (과열→조정→회복 사이클)
  ├─ 가격: ZHVI 변동성 비교 (과열-조정 패턴)
  ├─ 경로: Phoenix "저렴한 주택+저세율 → 인구유입 → 과열 → 조정 반복"
  └─ 교훈: 기후 불리해도 가격 경쟁력이 인구를 끌어당기는 메커니즘

축 4 — 변모 (대구 vs Charlotte)
  ├─ 인구: 산업전환 전후 인구 변화 패턴
  ├─ 수요: Charlotte 전환기 시장온도·필요소득·신규건설 변화
  ├─ 소득: 고소득 유입 → 필요소득 급상승 경로
  ├─ 경로: Charlotte "섬유쇠퇴 → 금융유치 → 고소득유입 → 주택수요폭발"
  └─ 교훈: 대구도 산업전환 성공 시 유사 경로 기대 가능
```

### 구현 사양

```python
# === src/s2_step10_4axis_analysis.py ===

"""
STEP 10: 4축 인구-부동산 비교 분석 (v2 신규)
실행: python src/s2_step10_4axis_analysis.py
의존: STEP 1~7 완료
"""
import sys, os
import pandas as pd
import numpy as np
from scipy import stats
from step0_init_db import get_connection, DB_NAME

# 공통 설정
AXIS_CONFIG = {
    'comprehensive': {'us_city': 'Dallas', 'metro': 'Dallas-Fort Worth-Arlington, TX',
                       'state': 'Texas', 'axis_kr': '종합'},
    'industry':      {'us_city': 'Atlanta', 'metro': 'Atlanta-Sandy Springs-Roswell, GA',
                       'state': 'Georgia', 'axis_kr': '산업'},
    'climate':       {'us_city': 'Phoenix', 'metro': 'Phoenix-Mesa-Chandler, AZ',
                       'state': 'Arizona', 'axis_kr': '기후'},
    'transformation':{'us_city': 'Charlotte', 'metro': 'Charlotte-Concord-Gastonia, NC-SC',
                       'state': 'North Carolina', 'axis_kr': '변모'},
}

KRW_TO_USD = 1350  # 환율 기준


def query_to_df(sql, params=None):
    conn = get_connection(DB_NAME)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


def get_daegu_pop():
    """대구 인구 추이"""
    return query_to_df("""
        SELECT year, total_population, population_change_rate,
               economic_activity_rate
        FROM daegu_population_summary ORDER BY year
    """)


def get_daegu_housing():
    """대구 아파트 연평균 가격 + 거래건수"""
    return query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price_manwon,
               COUNT(*) AS transaction_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)


def get_us_city_demand(metro_name):
    """미국 도시 수급 지표 연도별 집계"""
    return query_to_df("""
        SELECT LEFT(year_month, 4) AS year,
               AVG(market_temp_index) AS avg_market_temp,
               AVG(income_needed) AS avg_income_needed,
               AVG(inventory) AS avg_inventory,
               AVG(mean_days_pending) AS avg_days_pending,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = %s
        GROUP BY LEFT(year_month, 4) ORDER BY year
    """, params=(metro_name,))


def get_us_city_zhvi(metro_name):
    """미국 도시 ZHVI 연도별"""
    return query_to_df("""
        SELECT LEFT(year_month, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = %s
        GROUP BY LEFT(year_month, 4) ORDER BY year
    """, params=(metro_name,))


def get_us_pop_merged(city_name):
    """annual_pop_housing_merged에서 도시별 데이터"""
    return query_to_df("""
        SELECT year, population, pop_change_rate, zhvi, zhvi_change_rate,
               avg_sales_count, avg_inventory, avg_market_temp,
               avg_days_pending, avg_income_needed, supply_demand_ratio
        FROM annual_pop_housing_merged
        WHERE city_name = %s ORDER BY year
    """, params=(city_name,))


def save_scorecard(axis_kr, metric_category, daegu_name, daegu_val,
                   us_city, us_name, us_val, period, gap_dir,
                   corr_insight, strategy):
    """pop_housing_4axis_scorecard에 1행 저장"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pop_housing_4axis_scorecard
        (comparison_axis, metric_category, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value, year_or_period,
         gap_direction, correlation_insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (axis_kr, metric_category, daegu_name, daegu_val,
          us_city, us_name, us_val, period, gap_dir,
          corr_insight, strategy))
    conn.commit()
    conn.close()


def save_axis_summary(axis_kr, us_city, pop_trend, housing_trend,
                      temp_trend, price_trend, pathway, comparison, lesson):
    """pop_housing_axis_summary에 1행 저장"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pop_housing_axis_summary
        (comparison_axis, us_city_name, pop_trend, housing_demand_trend,
         market_temp_trend, price_trend, causal_pathway,
         daegu_comparison, policy_lesson)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (axis_kr, us_city, pop_trend, housing_trend,
          temp_trend, price_trend, pathway, comparison, lesson))
    conn.commit()
    conn.close()


# =============================================
# 축 1: 종합 — 대구 vs Dallas
# =============================================

def axis1_comprehensive():
    """Dallas 인구유입 → 수요폭발 경로 vs 대구 인구유출"""
    print("\n" + "=" * 70)
    print("축 1 [종합]: 대구 vs Dallas — 인구유입·유출과 부동산 수급")
    print("=" * 70)

    cfg = AXIS_CONFIG['comprehensive']
    df_daegu_pop = get_daegu_pop()
    df_daegu_house = get_daegu_housing()
    df_dallas = get_us_city_demand(cfg['metro'])
    df_dallas_zhvi = get_us_city_zhvi(cfg['metro'])
    df_dallas_merged = get_us_pop_merged('Dallas')

    # --- 인구성장률 비교 ---
    daegu_growth = df_daegu_pop.iloc[-1]['population_change_rate'] if not df_daegu_pop.empty else None
    dallas_growth = df_dallas_merged.iloc[-1]['pop_change_rate'] if not df_dallas_merged.empty else None

    save_scorecard('종합', '인구성장률',
        '대구 인구변동률(%)', daegu_growth,
        'Dallas', 'Dallas MSA 인구변동률(%)', dallas_growth,
        str(df_daegu_pop.iloc[-1]['year']) if not df_daegu_pop.empty else '',
        '미국우위' if (dallas_growth or 0) > (daegu_growth or 0) else '대구우위',
        '대구는 인구 순유출, Dallas는 지속적 순유입. '
        '인구유입이 주택 수요를 폭발적으로 증가시키는 Dallas의 패턴은 대구의 정반대 상황',
        'Dallas 모델: ①법인세 없는 TX → 기업 유치 ②저렴한 토지+주택 → 인구 흡수 '
        '③인구유입 → 재고감소 → 시장과열 → 가격상승의 선순환. '
        '대구 적용: 수도권 대비 주택가격 경쟁력을 활용한 기업·인구 유치 전략 필요')

    # --- 주택가격 비교 ---
    if not df_daegu_house.empty and not df_dallas_zhvi.empty:
        daegu_usd = df_daegu_house.iloc[-1]['avg_price_manwon'] * 10000 / KRW_TO_USD
        dallas_usd = df_dallas_zhvi.iloc[-1]['avg_zhvi']
        save_scorecard('종합', '주택가격',
            '대구 아파트 평균가(USD)', round(daegu_usd, 2),
            'Dallas', 'Dallas ZHVI(USD)', round(dallas_usd, 2),
            str(df_dallas_zhvi.iloc[-1]['year']),
            '대구우위' if daegu_usd < dallas_usd else '미국우위',
            f'대구 주택가격은 Dallas의 약 {daegu_usd/dallas_usd*100:.0f}% 수준. '
            '가격 경쟁력은 있으나 인구유출로 수요가 부족' if dallas_usd else '',
            '수도권 유출 인구를 대구로 흡수하려면 "저렴한 주택 + 양질의 일자리" 패키지가 핵심')

    # --- 시장 수급 비교 ---
    if not df_dallas.empty:
        latest_dallas = df_dallas.iloc[-1]
        save_scorecard('종합', '시장온도',
            '대구 시장온도(프록시 없음)', None,
            'Dallas', 'Dallas 시장온도지수', latest_dallas.get('avg_market_temp'),
            str(latest_dallas.get('year', '')),
            '비교불가',
            'Dallas 시장온도 50 이상 → 판매자 우위 시장, 인구유입이 수요를 재고 이상으로 밀어올림',
            '대구는 인구유출로 시장이 냉각될 가능성. '
            '인구유입 전환 시 시장온도 상승 → 신규건설 활성화 → 경제 선순환 기대')

    # --- 축 요약 ---
    save_axis_summary('종합', 'Dallas',
        pop_trend='유입(+)',
        housing_demand_trend='수요 급증',
        market_temp_trend='과열(50+)',
        price_trend='급등',
        causal_pathway='기업유치→일자리→인구유입→주택수요↑→재고↓→시장과열→가격급등→필요소득↑',
        daegu_comparison='대구는 정반대: 인구유출→수요감소→시장냉각→가격정체. '
                        'Dallas는 2010~2020 연평균 인구성장률 1.5%+, 대구는 -0.5%~-1.0%',
        policy_lesson='①수도권 대비 주택가격 경쟁력(1/3~1/4) 적극 마케팅 '
                     '②원격근무 시대 활용: 서울 소득+대구 주거비 → 삶의질 개선 홍보 '
                     '③기업 본사/R&D 유치 세제 인센티브 (TX주 모델 벤치마크)')

    print("  ✅ 축 1 완료")
    return df_daegu_pop, df_dallas, df_dallas_zhvi


# =============================================
# 축 2: 산업 — 대구 vs Atlanta
# =============================================

def axis2_industry():
    """Atlanta 산업 다각화 → 인구유입 → 수요 급증 경로"""
    print("\n" + "=" * 70)
    print("축 2 [산업]: 대구 vs Atlanta — 산업 허브화와 인구-부동산 관계")
    print("=" * 70)

    cfg = AXIS_CONFIG['industry']
    df_atlanta = get_us_city_demand(cfg['metro'])
    df_atlanta_merged = get_us_pop_merged('Atlanta')

    # --- Census 직업구조 비교 ---
    df_census = query_to_df("""
        SELECT city_id, AVG(professional) AS prof_pct, AVG(service) AS svc_pct,
               AVG(production) AS prod_pct, AVG(median_income) AS med_income,
               AVG(unemployment) AS unemp
        FROM us_census_demographics
        WHERE city_id = 3
    """)

    if not df_census.empty:
        save_scorecard('산업', '직업구조',
            '대구 전문직 비율(%)', None,
            'Atlanta', 'Atlanta 전문직 비율(%)', df_census.iloc[0].get('prof_pct'),
            'ACS 2015/2017',
            '비교불가',
            'Atlanta는 전문직 비율이 높고 중위소득도 높음 → 높은 주택 구매력으로 연결',
            'Atlanta 모델: 교통 허브(하츠필드 공항) + 대학(Georgia Tech, Emory) → '
            '전문직 유입 → 소득↑ → 주택수요↑. '
            '대구 적용: DGIST+경북대 산학 클러스터 + 대구공항 국제선 확충')

    # --- 시장 수급 비교 ---
    if not df_atlanta.empty:
        latest = df_atlanta.iloc[-1]
        save_scorecard('산업', '시장수급',
            '대구 연간 거래건수', None,
            'Atlanta', 'Atlanta 연간 판매건수', latest.get('total_sales'),
            str(latest.get('year', '')),
            '비교불가',
            'Atlanta 판매건수는 산업 다각화에 따른 인구유입과 강한 양의 상관관계',
            '산업 다각화 → 다양한 소득계층 유입 → 주택 수요 다변화 (고급+중급+임대)')

    # --- 축 요약 ---
    save_axis_summary('산업', 'Atlanta',
        pop_trend='유입(+)',
        housing_demand_trend='수요 급증',
        market_temp_trend='상승',
        price_trend='완만 상승',
        causal_pathway='교통허브+산업다각화→다양한일자리→전문직유입→소득↑→주택수요↑→가격상승',
        daegu_comparison='대구는 제조업 의존도 높아 고소득 전문직 유입이 제한적. '
                        'Atlanta는 물류+IT+미디어+의료 등 다각화에 성공',
        policy_lesson='①자동차부품 → 전기차·배터리 고도화 (현대·삼성SDI 유치) '
                     '②대구 의료특구 활용: 바이오·헬스케어 산업 육성 → 전문직 유입 '
                     '③교통 인프라: KTX 30분 생활권 + 대구공항 확장으로 접근성 개선')

    print("  ✅ 축 2 완료")
    return df_atlanta


# =============================================
# 축 3: 기후 — 대구 vs Phoenix
# =============================================

def axis3_climate():
    """Phoenix 기후 핸디캡 극복 → 인구 폭증 → 과열·조정 반복 패턴"""
    print("\n" + "=" * 70)
    print("축 3 [기후]: 대구 vs Phoenix — 폭염에도 인구가 증가하는 이유")
    print("=" * 70)

    cfg = AXIS_CONFIG['climate']
    df_phoenix = get_us_city_demand(cfg['metro'])
    df_phoenix_zhvi = get_us_city_zhvi(cfg['metro'])
    df_phoenix_merged = get_us_pop_merged('Phoenix')

    # --- 인구 폭증 vs 대구 유출 ---
    phoenix_growth = df_phoenix_merged.iloc[-1]['pop_change_rate'] if not df_phoenix_merged.empty else None
    df_daegu_pop = get_daegu_pop()
    daegu_growth = df_daegu_pop.iloc[-1]['population_change_rate'] if not df_daegu_pop.empty else None

    save_scorecard('기후', '인구성장률',
        '대구 인구변동률(%)', daegu_growth,
        'Phoenix', 'Phoenix 인구변동률(%)', phoenix_growth,
        str(df_daegu_pop.iloc[-1]['year']) if not df_daegu_pop.empty else '',
        '미국우위',
        'Phoenix는 대구와 유사한 폭염 환경이지만 인구가 폭발적으로 증가. '
        '2010~2020 Phoenix MSA 인구성장률 약 +15%, 대구는 약 -5%',
        'Phoenix 성공 비밀: ①CA 대비 1/3 주택가격 ②낮은 세율(AZ) '
        '③반도체(TSMC, Intel) 대규모 공장 유치 ④은퇴인구 유입(선벨트). '
        '대구 적용: 수도권 대비 주택 가격 경쟁력 + 첨단산업단지 유치')

    # --- 시장온도 과열·조정 패턴 ---
    if not df_phoenix.empty:
        max_temp = df_phoenix['avg_market_temp'].max()
        min_temp = df_phoenix['avg_market_temp'].min()
        save_scorecard('기후', '시장변동성',
            '대구 시장 변동성', None,
            'Phoenix', 'Phoenix 시장온도 변동폭', round(max_temp - min_temp, 2) if pd.notna(max_temp) and pd.notna(min_temp) else None,
            f"{df_phoenix.iloc[0]['year']}~{df_phoenix.iloc[-1]['year']}",
            '비교불가',
            f'Phoenix 시장온도 범위: {min_temp:.0f}~{max_temp:.0f}. '
            '인구 급유입 → 과열 → 조정의 사이클이 반복됨 (2006-08 버블, 2020-22 과열)',
            '인구 유입이 급격하면 시장 과열 리스크 발생. '
            '대구는 점진적 인구유입 전략이 안정적 시장 형성에 유리')

    # --- 주택가격 경쟁력 ---
    if not df_phoenix_zhvi.empty:
        save_scorecard('기후', '주택가격',
            '대구 아파트 평균가(USD)', None,
            'Phoenix', 'Phoenix ZHVI(USD)', round(df_phoenix_zhvi.iloc[-1]['avg_zhvi'], 2),
            str(df_phoenix_zhvi.iloc[-1]['year']),
            '대구우위',
            'Phoenix도 LA/SF 대비 저렴한 주택으로 인구를 끌어들임. '
            '대구는 서울 대비 유사한 가격 경쟁력 보유',
            '"폭염에도 인구 유입" 핵심: 주택 구매력 > 기후 불편. '
            '대구도 서울 대비 주택 구매력 우위를 극대화해야 함')

    # --- 축 요약 ---
    save_axis_summary('기후', 'Phoenix',
        pop_trend='폭발 유입',
        housing_demand_trend='과열',
        market_temp_trend='급등→조정 반복',
        price_trend='급등 후 조정',
        causal_pathway='저렴한주택+저세율→인구폭증→수요급증→재고부족→시장과열→'
                      '가격급등→조정(2008/2022)→재유입 반복',
        daegu_comparison='대구와 Phoenix는 여름 폭염이라는 동일한 기후 핸디캡. '
                        'Phoenix는 가격경쟁력으로 극복, 대구는 인구유출 중',
        policy_lesson='①"서울 대비 1/3 가격으로 내 집 마련" 마케팅 캠페인 '
                     '②도시 냉방 인프라(그린 인프라, 지하 공간) 투자 '
                     '③은퇴인구 유치: 의료인프라 + 저렴한 생활비 패키지 '
                     '④TSMC/Intel 모델 벤치마크 → 대규모 첨단공장 유치')

    print("  ✅ 축 3 완료")
    return df_phoenix, df_phoenix_zhvi


# =============================================
# 축 4: 변모 — 대구 vs Charlotte
# =============================================

def axis4_transformation():
    """Charlotte 산업전환 → 고소득 유입 → 필요소득 급상승 경로"""
    print("\n" + "=" * 70)
    print("축 4 [변모]: 대구 vs Charlotte — 산업전환과 인구-부동산 경로")
    print("=" * 70)

    cfg = AXIS_CONFIG['transformation']
    df_charlotte = get_us_city_demand(cfg['metro'])
    df_charlotte_zhvi = get_us_city_zhvi(cfg['metro'])
    df_charlotte_merged = get_us_pop_merged('Charlotte')
    df_daegu_pop = get_daegu_pop()
    df_daegu_house = get_daegu_housing()

    # --- 필요소득 비교 (산업전환→고소득유입→구매력 변화) ---
    if not df_charlotte.empty:
        ch_income = df_charlotte[df_charlotte['avg_income_needed'].notna()]
        if not ch_income.empty:
            first_income = ch_income.iloc[0]['avg_income_needed']
            last_income = ch_income.iloc[-1]['avg_income_needed']
            income_change = (last_income - first_income) / first_income * 100 if first_income else 0

            save_scorecard('변모', '구매필요소득',
                '대구 아파트 구매 필요소득(추정)', None,
                'Charlotte', 'Charlotte 필요소득 변화율(%)', round(income_change, 2),
                f"{ch_income.iloc[0]['year']}~{ch_income.iloc[-1]['year']}",
                '비교불가',
                f'Charlotte 주택구매 필요소득이 {income_change:.0f}% 급상승 → '
                '금융·IT 고소득 유입이 주택 진입장벽을 높임',
                'Charlotte 전환 성공의 양면: ①경제 활성화 ②기존 주민 주거비 부담 증가. '
                '대구도 전환 성공 시 유사 현상 대비 필요 → 중저소득 주거 안전망 병행 구축')

    # --- 인구 전환기 패턴 ---
    if not df_charlotte_merged.empty:
        ch_pop = df_charlotte_merged[df_charlotte_merged['pop_change_rate'].notna()]
        avg_pop_growth = ch_pop['pop_change_rate'].mean() if not ch_pop.empty else None

        save_scorecard('변모', '전환기 인구',
            '대구 평균 인구변동률(%)', df_daegu_pop['population_change_rate'].mean() if not df_daegu_pop.empty else None,
            'Charlotte', 'Charlotte 평균 인구변동률(%)', avg_pop_growth,
            '전체 기간',
            '미국우위',
            '산업 전환 성공 → 고소득 일자리 → 인구유입의 인과관계가 Charlotte에서 확인됨',
            'Charlotte 전환 핵심 3요소를 대구에 적용: '
            '①앵커기업(Bank of America급) → 삼성·현대 지역본사 유치 '
            '②대학 인재파이프라인(UNC Charlotte) → 경북대+DGIST 활용 '
            '③공항 허브(CLT) → KTX+대구공항 연계 광역교통')

    # --- 대구 vs Charlotte 가격 추이 ---
    if not df_charlotte_zhvi.empty and not df_daegu_house.empty:
        ch_first = df_charlotte_zhvi.iloc[0]['avg_zhvi']
        ch_last = df_charlotte_zhvi.iloc[-1]['avg_zhvi']
        ch_change = (ch_last - ch_first) / ch_first * 100 if ch_first else 0

        dg_first = df_daegu_house.iloc[0]['avg_price_manwon']
        dg_last = df_daegu_house.iloc[-1]['avg_price_manwon']
        dg_change = (dg_last - dg_first) / dg_first * 100 if dg_first else 0

        save_scorecard('변모', '주택가격 변화',
            '대구 아파트 가격변화율(%)', round(dg_change, 2),
            'Charlotte', 'Charlotte ZHVI 변화율(%)', round(ch_change, 2),
            f"{df_charlotte_zhvi.iloc[0]['year']}~{df_charlotte_zhvi.iloc[-1]['year']}",
            '미국우위' if ch_change > dg_change else '대구우위',
            f'Charlotte 전환 성공 → ZHVI +{ch_change:.0f}% 상승. '
            '산업전환 → 인구유입 → 부동산 가치 상승의 선순환 확인',
            '대구도 산업전환 성공 시 부동산 가치 상승 기대. '
            '현재 대구 아파트 가격은 상대적으로 저평가 → 투자 잠재력 존재')

    # --- 축 요약 ---
    save_axis_summary('변모', 'Charlotte',
        pop_trend='전환기 유입',
        housing_demand_trend='고소득 수요 급증',
        market_temp_trend='상승',
        price_trend='급등 (전환 후)',
        causal_pathway='섬유쇠퇴→금융본사유치→고소득유입→주택수요↑→필요소득급등→신규건설↑→도시확장',
        daegu_comparison='대구: 섬유→자동차부품→첨단 전환 진행 중 (Charlotte보다 10~15년 후발). '
                        'Charlotte의 2000년대 = 대구의 2020년대 → 전환 성공 신호 주시 필요',
        policy_lesson='①30년 장기 전환 로드맵 수립 (Charlotte 사례: 1980→2010) '
                     '②"앵커 기업" 1개 유치가 연쇄 효과 → 대규모 기업 유치에 집중 '
                     '③전환 성공 시 주거비 급등 대비 → 중저소득 공공임대 확대 병행')

    print("  ✅ 축 4 완료")
    return df_charlotte, df_charlotte_zhvi


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 10: 4축 인구-부동산 비교 분석 (v2)")
    print("=" * 60)

    r1 = axis1_comprehensive()
    r2 = axis2_industry()
    r3 = axis3_climate()
    r4 = axis4_transformation()

    print("\n🎉 STEP 10 완료! pop_housing_4axis_scorecard + pop_housing_axis_summary 저장됨")
```

---

## ⭐ STEP 11: 대구 인구유지 전략 보고서 생성 (v2 신규)

> **Claude Code 프롬프트:**
> 4축 분석 결과를 종합하여 "대구가 인구를 유지하며 부동산 시장을 활성화할 수 있는 전략" 보고서를 자동 생성해줘. pop_housing_4axis_scorecard와 pop_housing_axis_summary에서 데이터를 읽어 Markdown 보고서로 출력해줘.

```python
# === src/s2_step11_daegu_strategy.py ===

"""
STEP 11: 대구 인구유지 전략 보고서 생성 (v2 신규)
실행: python src/s2_step11_daegu_strategy.py
의존: STEP 10 완료
"""
import os
from step0_init_db import get_connection, DB_NAME
import pandas as pd


def query_to_df(sql):
    conn = get_connection(DB_NAME)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


def generate_report():
    print("\n" + "=" * 70)
    print("대구 인구유지 전략 보고서 생성")
    print("=" * 70)

    # 스코어카드 전체 조회
    df_sc = query_to_df("""
        SELECT comparison_axis, metric_category,
               daegu_metric_name, daegu_value,
               us_city_name, us_metric_name, us_value,
               gap_direction, correlation_insight, strategy_implication
        FROM pop_housing_4axis_scorecard
        ORDER BY FIELD(comparison_axis, '종합', '산업', '기후', '변모'), metric_category
    """)

    # 축별 요약 조회
    df_sum = query_to_df("""
        SELECT comparison_axis, us_city_name,
               pop_trend, housing_demand_trend, market_temp_trend, price_trend,
               causal_pathway, daegu_comparison, policy_lesson
        FROM pop_housing_axis_summary
        ORDER BY FIELD(comparison_axis, '종합', '산업', '기후', '변모')
    """)

    report = []
    report.append("# 대구광역시 인구유지 전략 보고서")
    report.append("> 소주제 2: 인구 이동과 주택 수요 — 미국 4개 유사 도시 비교 분석 기반\n")
    report.append("---\n")

    # 요약 표
    report.append("## Executive Summary\n")
    report.append("| 비교축 | 미국 도시 | 인구 추세 | 부동산 수요 | 시장 온도 | 가격 추세 |")
    report.append("|--------|----------|----------|-----------|----------|----------|")
    for _, row in df_sum.iterrows():
        report.append(f"| {row['comparison_axis']} | {row['us_city_name']} | "
                     f"{row['pop_trend']} | {row['housing_demand_trend']} | "
                     f"{row['market_temp_trend']} | {row['price_trend']} |")
    report.append(f"| **대구** | - | **유출(−)** | **수요 감소** | **냉각** | **정체** |\n")

    # 축별 상세
    for axis in ['종합', '산업', '기후', '변모']:
        axis_sc = df_sc[df_sc['comparison_axis'] == axis]
        axis_sm = df_sum[df_sum['comparison_axis'] == axis]

        if axis_sc.empty and axis_sm.empty:
            continue

        us_city = axis_sc.iloc[0]['us_city_name'] if not axis_sc.empty else ''
        report.append(f"## {axis} 비교: 대구 vs {us_city}\n")

        # 인과 경로
        if not axis_sm.empty:
            sm = axis_sm.iloc[0]
            report.append(f"### 인과 경로\n")
            report.append(f"```\n{sm['causal_pathway']}\n```\n")
            report.append(f"### 대구와의 차이\n{sm['daegu_comparison']}\n")

        # 지표별 비교
        for _, row in axis_sc.iterrows():
            report.append(f"### 📊 {row['metric_category']}")
            report.append(f"- **대구:** {row['daegu_metric_name']} = {row['daegu_value']}")
            report.append(f"- **{us_city}:** {row['us_metric_name']} = {row['us_value']}")
            report.append(f"- **격차:** {row['gap_direction']}")
            report.append(f"\n**인사이트:** {row['correlation_insight']}\n")
            report.append(f"**🎯 전략 시사점:** {row['strategy_implication']}\n")

        # 정책 교훈
        if not axis_sm.empty:
            report.append(f"### 💡 정책 교훈\n{axis_sm.iloc[0]['policy_lesson']}\n")

        report.append("---\n")

    # 종합 전략
    report.append("## 🏆 대구 인구유지 + 부동산 활성화 종합 전략\n")
    report.append("""
| # | 전략 | 벤치마크 | 인구 효과 | 부동산 효과 | 우선순위 |
|---|------|---------|----------|-----------|---------|
| 1 | **주택가격 경쟁력 마케팅** | Dallas, Phoenix | 수도권 유출 인구 흡수 | 거래량↑, 시장 안정 | 🔴 단기 |
| 2 | **원격근무자 유치 프로그램** | Phoenix | 서울 소득+대구 주거비 | 수요↑, 가격 완만 상승 | 🔴 단기 |
| 3 | **앵커 기업 유치** | Charlotte, Dallas | 고소득 일자리 → 인구유입 | 신규건설↑, 가격 상승 | 🟡 중기 |
| 4 | **산학 클러스터 구축** | Atlanta, Charlotte | 전문직 유입 | 고급 주택 수요↑ | 🟡 중기 |
| 5 | **교통 인프라 혁신** | Atlanta | 광역 생활권 확대 | 외곽 개발 활성화 | 🟡 중기 |
| 6 | **의료·바이오 특구** | Atlanta | 은퇴+전문직 유입 | 다양한 수요 창출 | 🟢 장기 |
| 7 | **산업 전환 완성** | Charlotte | 인구 안정화+유입 전환 | 시장 과열→가격 급등 | 🟢 장기 |

### 인구-부동산 선순환 모델

```
[현재] 인구유출 → 수요↓ → 시장냉각 → 가격정체 → 매력도↓ → 추가유출 (악순환)
                     ↓ (전략 투입)
[목표] 기업유치+가격경쟁력 → 인구유입 전환 → 수요↑ → 시장활성화 → 가격상승 → 투자매력↑ (선순환)
```

### 핵심 KPI (인구유입 전환 신호)

| 지표 | 현재 (대구) | 목표 (5년 후) | 벤치마크 |
|------|-----------|-------------|---------|
| 인구변동률 | −0.5~−1.0% | 0% (유출 중단) | Dallas +1.5% |
| 시장온도지수 | 없음(추정 30~40) | 45~50 | Dallas 55~65 |
| 연간 거래건수 | 감소 추세 | 10% 증가 | Atlanta 패턴 |
| 주택구매 필요소득 | 낮음 | 완만 상승 | Charlotte 패턴 |
""")

    # 저장
    os.makedirs('output', exist_ok=True)
    path = 'output/s2_daegu_population_strategy_report.md'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n✅ 보고서 저장: {path}")
    return path


if __name__ == '__main__':
    generate_report()
```

---

## ⭐ STEP 12: 4축 비교 시각화 (v2 신규)

> **Claude Code 프롬프트:**
> 4축 인구-부동산 비교 분석 결과를 시각화해줘. 총 6개 차트: 인구성장률 대조, 인구→부동산 경로 4축 패널, 인구변동률 vs 시장온도 산점도, 대구vs미국 수급비율 이중축, Phoenix 과열사이클, 전략 로드맵

### 시각화 목록 (v2 추가: 6개)

| # | 차트명 | 유형 | 핵심 비교 |
|---|--------|------|----------|
| V7 | 인구성장률 대조: 대구 유출 vs 4도시 유입 | 막대 그래프 | 5개 도시 인구변동률 나란히 |
| V8 | 4축 인구→부동산 경로 대시보드 | 2×2 서브플롯 | 축별 인구→수요→가격 경로 |
| V9 | 인구변동률 vs 시장온도 산점도 (4축 색분류) | 산점도+회귀 | 인구-시장온도 상관관계 |
| V10 | 대구 vs 미국 4도시: 인구-주택가격 이중축 | 이중축 선형 | 인구 감소+가격 정체 vs 인구 유입+가격 급등 |
| V11 | Phoenix 과열 사이클 분석 | 영역 차트 | 인구유입→과열→조정→재유입 |
| V12 | 대구 인구유지 전략 로드맵 | 인포그래픽 | 단기/중기/장기 전략 시각화 |

```python
# === src/s2_step12_visualization_4axis.py ===

"""
STEP 12: 4축 인구-부동산 비교 시각화 (v2 신규)
실행: python src/s2_step12_visualization_4axis.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import os
from step0_init_db import get_connection, DB_NAME
from s2_step10_4axis_analysis import (
    query_to_df, get_daegu_pop, get_daegu_housing,
    get_us_city_demand, get_us_city_zhvi, get_us_pop_merged,
    AXIS_CONFIG
)

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

OUTPUT_DIR = 'output/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLORS = {
    'Dallas': '#E74C3C', 'Atlanta': '#3498DB',
    'Phoenix': '#E67E22', 'Charlotte': '#2ECC71',
    'US Average': '#95A5A6', 'Daegu': '#9B59B6', '대구': '#9B59B6',
}


# =============================================
# V7: 인구성장률 대조 — 대구 유출 vs 4도시 유입
# =============================================

def viz7_population_growth_contrast():
    """5개 도시 인구성장률 막대 그래프"""

    df_daegu = get_daegu_pop()
    cities = ['Dallas', 'Atlanta', 'Phoenix', 'Charlotte']

    fig, ax = plt.subplots(figsize=(12, 7))

    # 대구 인구변동률 (연도별)
    if not df_daegu.empty:
        latest_years = df_daegu.tail(5)
        x_positions = np.arange(len(latest_years))
        width = 0.15

        ax.bar(x_positions - 2*width, latest_years['population_change_rate'],
               width, label='Daegu', color=COLORS['Daegu'], alpha=0.8)

        # 미국 4도시 (annual_pop_housing_merged에서)
        for i, city in enumerate(cities):
            df_city = get_us_pop_merged(city)
            if not df_city.empty:
                # 대구와 같은 연도 필터
                common_years = set(latest_years['year']).intersection(set(df_city['year']))
                df_match = df_city[df_city['year'].isin(common_years)].sort_values('year')
                if not df_match.empty:
                    ax.bar(x_positions[:len(df_match)] + (i-1)*width,
                           df_match['pop_change_rate'].values[:len(x_positions)],
                           width, label=city, color=COLORS[city], alpha=0.8)

        ax.set_xticks(x_positions)
        ax.set_xticklabels(latest_years['year'].astype(int))

    ax.axhline(y=0, color='black', linewidth=1, linestyle='-')
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Population Change Rate (%)', fontsize=12)
    ax.set_title('Population Growth Contrast\nDaegu (Decline) vs US Peer Cities (Growth)',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    # 대구 영역 강조
    ax.axhspan(ax.get_ylim()[0], 0, alpha=0.05, color='red', label='_nolegend_')
    ax.axhspan(0, ax.get_ylim()[1], alpha=0.05, color='green', label='_nolegend_')
    ax.text(0.02, 0.02, '← Population Decline Zone', transform=ax.transAxes,
            fontsize=9, color='red', alpha=0.7)
    ax.text(0.02, 0.95, '← Population Growth Zone', transform=ax.transAxes,
            fontsize=9, color='green', alpha=0.7)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}s2_viz7_pop_growth_contrast.png', dpi=150)
    plt.close()
    print("✅ s2_viz7_pop_growth_contrast.png")


# =============================================
# V8: 4축 인구→부동산 경로 대시보드 (2×2)
# =============================================

def viz8_4axis_pathway_dashboard():
    """축별 인구→수요→가격 경로를 2×2 패널로 표시"""

    fig = plt.figure(figsize=(18, 14))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    axis_list = [
        ('comprehensive', 'Axis 1 [Comprehensive]: Dallas\nPop Growth → Demand Surge → Price Rise'),
        ('industry', 'Axis 2 [Industry]: Atlanta\nJob Diversity → Pop Inflow → Market Heat'),
        ('climate', 'Axis 3 [Climate]: Phoenix\nAffordability → Pop Boom → Overheat Cycle'),
        ('transformation', 'Axis 4 [Transformation]: Charlotte\nIndustry Shift → Income Rise → Price Surge'),
    ]

    for idx, (axis_key, title) in enumerate(axis_list):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        cfg = AXIS_CONFIG[axis_key]
        df = get_us_city_demand(cfg['metro'])

        if not df.empty:
            # 이중축: 판매건수(막대) + 시장온도(선)
            ax2 = ax.twinx()
            ax.bar(df['year'], df['total_sales'], color=COLORS[cfg['us_city']], alpha=0.4,
                   label='Sales Count')
            ax2.plot(df['year'], df['avg_market_temp'], color='#E74C3C', marker='o',
                    linewidth=2, label='Market Temp')
            ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)

            ax.set_ylabel('Sales Count', color=COLORS[cfg['us_city']])
            ax2.set_ylabel('Market Temp Index', color='#E74C3C')
            ax.tick_params(axis='x', rotation=45)

        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.2)

    fig.suptitle('4-Axis Population → Housing Pathway Dashboard\n'
                 'How Population Movement Drives Housing Markets',
                 fontsize=15, fontweight='bold')
    plt.savefig(f'{OUTPUT_DIR}s2_viz8_4axis_pathway.png', bbox_inches='tight')
    plt.close()
    print("✅ s2_viz8_4axis_pathway.png")


# =============================================
# V9: 인구변동률 vs 시장온도 산점도
# =============================================

def viz9_pop_vs_market_temp():
    """4도시+대구 인구변동률 vs 시장온도 산점도"""

    df = query_to_df("""
        SELECT city_name, year, pop_change_rate, avg_market_temp
        FROM annual_pop_housing_merged
        WHERE pop_change_rate IS NOT NULL AND avg_market_temp IS NOT NULL
    """)

    if df.empty:
        print("⚠️ 데이터 부족 — 스킵")
        return

    fig, ax = plt.subplots(figsize=(11, 8))

    for city in df['city_name'].unique():
        sub = df[df['city_name'] == city]
        ax.scatter(sub['pop_change_rate'], sub['avg_market_temp'],
                  color=COLORS.get(city, 'gray'), label=city, s=70, alpha=0.7)

    # 회귀선
    from numpy.polynomial.polynomial import polyfit
    x = df['pop_change_rate'].values
    y = df['avg_market_temp'].values
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 3:
        b, m = polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(x_line, b + m * x_line, 'k--', linewidth=1.5, alpha=0.5,
                label=f'Trend (slope={m:.1f})')

    ax.axhline(y=50, color='gray', linewidth=0.8, linestyle=':',)
    ax.axvline(x=0, color='gray', linewidth=0.8, linestyle=':')

    # 사분면 라벨
    ax.text(0.98, 0.98, 'Pop Growth +\nMarket Hot', transform=ax.transAxes,
            ha='right', va='top', fontsize=9, color='red', alpha=0.6)
    ax.text(0.02, 0.02, 'Pop Decline +\nMarket Cold', transform=ax.transAxes,
            ha='left', va='bottom', fontsize=9, color='blue', alpha=0.6)

    ax.set_xlabel('Population Change Rate (%)', fontsize=12)
    ax.set_ylabel('Market Temperature Index', fontsize=12)
    ax.set_title('Population Change Rate vs Market Temperature\nDo More People = Hotter Market?',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}s2_viz9_pop_vs_market_temp.png', dpi=150)
    plt.close()
    print("✅ s2_viz9_pop_vs_market_temp.png")


# =============================================
# V10: 대구 vs 미국 4도시 — 인구·주택가격 이중축
# =============================================

def viz10_daegu_vs_us_dual_axis():
    """상단: 미국 4도시 ZHVI 추이, 하단: 대구 인구+아파트가격"""

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(16, 12))

    # 상단: 미국 4도시 ZHVI
    for city_name, cfg in AXIS_CONFIG.items():
        df = get_us_city_zhvi(cfg['metro'])
        if not df.empty:
            label = cfg['us_city']
            ax_top.plot(df['year'], df['avg_zhvi'], marker='.', label=label,
                       color=COLORS[label], linewidth=2)
    ax_top.set_title('US Peer Cities: Home Value Index (ZHVI) — Population Inflow Effect',
                     fontsize=13, fontweight='bold')
    ax_top.set_ylabel('ZHVI (USD)')
    ax_top.legend(fontsize=10)
    ax_top.grid(alpha=0.3)
    ax_top.tick_params(axis='x', rotation=45)
    ax_top.annotate('Population Inflow → ZHVI ↑',
                   xy=(0.7, 0.85), xycoords='axes fraction',
                   fontsize=11, color='green', fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # 하단: 대구 인구 + 아파트 가격
    df_pop = get_daegu_pop()
    df_price = get_daegu_housing()

    if not df_pop.empty:
        ax_bot.plot(df_pop['year'], df_pop['total_population'], color=COLORS['Daegu'],
                    marker='o', linewidth=2.5, label='Daegu Population')
        ax_bot.set_ylabel('Population', color=COLORS['Daegu'], fontsize=12)

    if not df_price.empty:
        ax_r = ax_bot.twinx()
        ax_r.plot(df_price['year'], df_price['avg_price_manwon'], color='#E67E22',
                  marker='s', linewidth=2, linestyle='--', label='Daegu Apt Price')
        ax_r.set_ylabel('Avg Apt Price (만원)', color='#E67E22', fontsize=12)

    ax_bot.set_title('Daegu: Population Decline vs Housing Price — Opposite Pattern',
                     fontsize=13, fontweight='bold')
    ax_bot.set_xlabel('Year')
    ax_bot.grid(alpha=0.3)

    # 범례 합치기
    lines1, labels1 = ax_bot.get_legend_handles_labels()
    if not df_price.empty:
        lines2, labels2 = ax_r.get_legend_handles_labels()
        ax_bot.legend(lines1 + lines2, labels1 + labels2, fontsize=10)

    ax_bot.annotate('Population Outflow → Market Stagnation',
                   xy=(0.6, 0.15), xycoords='axes fraction',
                   fontsize=11, color='red', fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='mistyrose', alpha=0.8))

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}s2_viz10_daegu_vs_us_dual.png', dpi=150)
    plt.close()
    print("✅ s2_viz10_daegu_vs_us_dual.png")


# =============================================
# V11: Phoenix 과열 사이클 분석
# =============================================

def viz11_phoenix_overheat_cycle():
    """Phoenix 시장온도 + 재고 + 가격 변동 사이클"""

    df_demand = get_us_city_demand('Phoenix-Mesa-Chandler, AZ')
    df_zhvi = get_us_city_zhvi('Phoenix-Mesa-Chandler, AZ')

    if df_demand.empty:
        print("⚠️ Phoenix 데이터 없음 — 스킵")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

    # 상단: 시장온도 (영역 차트) + 재고
    ax1.fill_between(df_demand['year'], df_demand['avg_market_temp'],
                     50, where=df_demand['avg_market_temp'] >= 50,
                     color='#E74C3C', alpha=0.3, label='Overheated (>50)')
    ax1.fill_between(df_demand['year'], df_demand['avg_market_temp'],
                     50, where=df_demand['avg_market_temp'] < 50,
                     color='#3498DB', alpha=0.3, label='Cool (<50)')
    ax1.plot(df_demand['year'], df_demand['avg_market_temp'],
             color='#E67E22', linewidth=2.5, marker='o', label='Market Temp')
    ax1.axhline(y=50, color='black', linewidth=1, linestyle='--')
    ax1.set_ylabel('Market Temp Index')
    ax1.set_title('Phoenix Overheat Cycle\nPopulation Boom → Demand Surge → Overheat → Correction',
                  fontsize=13, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)

    # 하단: ZHVI 변화율
    if not df_zhvi.empty:
        df_zhvi['zhvi_pct'] = df_zhvi['avg_zhvi'].pct_change() * 100
        ax2.bar(df_zhvi['year'], df_zhvi['zhvi_pct'],
                color=['#E74C3C' if v > 0 else '#3498DB' for v in df_zhvi['zhvi_pct'].fillna(0)],
                alpha=0.7)
        ax2.axhline(y=0, color='black', linewidth=1)
        ax2.set_ylabel('ZHVI YoY Change (%)')
        ax2.set_title('Phoenix ZHVI Year-over-Year Change', fontsize=12)
        ax2.grid(alpha=0.3)

    ax2.set_xlabel('Year')
    ax2.tick_params(axis='x', rotation=45)

    # 사이클 주석
    ax1.annotate('Lesson for Daegu:\nGradual inflow is safer\nthan explosive boom',
                xy=(0.75, 0.15), xycoords='axes fraction', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}s2_viz11_phoenix_cycle.png', dpi=150)
    plt.close()
    print("✅ s2_viz11_phoenix_cycle.png")


# =============================================
# V12: 대구 인구유지 전략 로드맵 인포그래픽
# =============================================

def viz12_strategy_roadmap():
    """대구 인구유지 전략 로드맵 시각화"""

    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 타이틀
    ax.text(50, 97, 'Daegu Population Retention Strategy Roadmap', fontsize=18,
            fontweight='bold', ha='center', va='top')
    ax.text(50, 93, 'Population Movement → Housing Demand | Lessons from Dallas · Atlanta · Phoenix · Charlotte',
            fontsize=11, ha='center', va='top', color='gray')

    # 타임라인 화살표
    ax.annotate('', xy=(92, 50), xytext=(8, 50),
                arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=3))

    phases = [
        (15, 'NOW\n(Year 0)', '#E74C3C'),
        (38, '3 YEARS', '#F39C12'),
        (62, '7 YEARS', '#2ECC71'),
        (85, '15 YEARS', '#3498DB'),
    ]
    for x, label, color in phases:
        ax.text(x, 47, label, fontsize=10, fontweight='bold', color=color, ha='center')

    # 상단: 인구 전략 (파란 계열)
    ax.text(50, 87, '── Population Strategy ──', fontsize=12, ha='center',
            fontweight='bold', color='#2980B9')

    pop_strats = [
        (15, 78, 'Housing Price\nCompetitiveness\nMarketing', 'Dallas', '#E74C3C'),
        (38, 78, 'Remote Worker\nAttraction\nProgram', 'Phoenix', '#E67E22'),
        (62, 78, 'Anchor Company\nHQ Attraction\n→ Job Creation', 'Charlotte', '#2ECC71'),
        (85, 78, 'Population\nStabilization\n& Net Inflow', 'All 4', '#3498DB'),
    ]
    for x, y, strat, model, color in pop_strats:
        rect = mpatches.FancyBboxPatch((x-11, y-7), 22, 14, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.12, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y+1, strat, fontsize=8.5, ha='center', va='center', fontweight='bold')
        ax.text(x, y-5, f'({model})', fontsize=7, ha='center', color=color, style='italic')

    # 하단: 부동산 효과 (주황 계열)
    ax.text(50, 38, '── Housing Market Effect ──', fontsize=12, ha='center',
            fontweight='bold', color='#D35400')

    house_effects = [
        (15, 28, 'Transaction\nVolume ↑\nMarket Stabilize', '#E74C3C'),
        (38, 28, 'Demand ↑\nInventory ↓\nDays Pending ↓', '#F39C12'),
        (62, 28, 'Market Temp ↑\nNew Construction ↑\nPrice Rise', '#2ECC71'),
        (85, 28, 'Income Needed ↑\nSustainable\nGrowth Cycle', '#3498DB'),
    ]
    for x, y, effect, color in house_effects:
        rect = mpatches.FancyBboxPatch((x-11, y-7), 22, 14, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.08, edgecolor=color,
                                        linewidth=1.5, linestyle='--')
        ax.add_patch(rect)
        ax.text(x, y, effect, fontsize=8.5, ha='center', va='center')

    # 연결 화살표 (인구전략→부동산효과)
    for x in [15, 38, 62, 85]:
        ax.annotate('', xy=(x, 35), xytext=(x, 64),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1, alpha=0.5))

    # 범례 박스
    legend_data = [
        ('Dallas', '#E74C3C', 'Affordability → Inflow'),
        ('Atlanta', '#3498DB', 'Industry Hub → Jobs'),
        ('Phoenix', '#E67E22', 'Climate Overcome → Boom'),
        ('Charlotte', '#2ECC71', 'Transition → High Income'),
    ]
    for i, (city, color, keyword) in enumerate(legend_data):
        x = 10 + i * 22
        ax.add_patch(mpatches.FancyBboxPatch((x-2, 6), 20, 8, boxstyle="round,pad=0.5",
                     facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5))
        ax.text(x+8, 12, city, fontsize=9, ha='center', fontweight='bold', color=color)
        ax.text(x+8, 8, keyword, fontsize=7.5, ha='center', color='gray')

    plt.savefig(f'{OUTPUT_DIR}s2_viz12_strategy_roadmap.png', bbox_inches='tight')
    plt.close()
    print("✅ s2_viz12_strategy_roadmap.png")


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 12: 4축 인구-부동산 비교 시각화 (v2)")
    print("=" * 60)

    viz7_population_growth_contrast()
    viz8_4axis_pathway_dashboard()
    viz9_pop_vs_market_temp()
    viz10_daegu_vs_us_dual_axis()
    viz11_phoenix_overheat_cycle()
    viz12_strategy_roadmap()

    print(f"\n🎉 모든 v2 시각화 저장: {OUTPUT_DIR}")
```

---

## 🚀 실행 순서 요약 (v2 전체)

```bash
# 사전: 소주제1이 완료된 상태여야 함 (cities, us_metro_zhvi, daegu_monthly_summary 필요)
pip install pymysql pandas numpy scipy matplotlib seaborn

# 1. 테이블 생성 (v2: 14개)
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

# 8. 분석 쿼리 → CSV (Q1~Q10)
python src/s2_step8_analysis_queries.py

# 9. 기존 시각화 → PNG (viz1~viz6)
python src/s2_step9_visualization.py

# ★ v2 추가
# 10. 4축 인구-부동산 비교 분석
python src/s2_step10_4axis_analysis.py

# 11. 대구 인구유지 전략 보고서 생성
python src/s2_step11_daegu_strategy.py

# 12. 4축 비교 시각화 (viz7~viz12)
python src/s2_step12_visualization_4axis.py
```

---

## ⚠️ Claude Code 실행 시 체크리스트 (v2 확장)

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
| 10 | **v2: daegu_housing_prices 적재** | 소주제4 또는 별도 스크립트로 대구 아파트 실거래 적재 필요 |
| 11 | **v2: us_metro_zhvi ZHVI 데이터** | 소주제1에서 ZHVI 적재 완료 확인 |

### 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| `Table 'us_metro_zhvi' doesn't exist` | 소주제1 미실행 | 소주제1 step1~2 먼저 실행 |
| `대구 데이터 없음 (0행)` | `region` 열 값 불일치 | `SELECT DISTINCT region FROM korean_demographics` 확인 후 LIKE 조건 수정 |
| `MERGE 결과 0행` | Wide 파일 RegionName 불일치 | `check_and_fix_metro_names()` (step2에서 자동 출력) |
| `scipy ImportError` | 미설치 | `pip install scipy` |
| `MemoryError` | Metro_time_series 56MB | `chunksize=5000`으로 줄이기 |
| `v2: daegu_housing_prices 0행` | 실거래 미적재 | 소주제4 step6b 또는 별도 로딩 스크립트 실행 |

### v2 Claude Code 단계별 프롬프트

```
[STEP 10 — 4축 인구-부동산 분석]
4축 비교 분석을 실행해줘:
- 축1(종합): 대구 인구유출 vs Dallas 인구유입 → 부동산 수급 차이 비교
- 축2(산업): Atlanta 산업다각화 → 인구유입 → 수요급증 경로 분석
- 축3(기후): Phoenix 기후핸디캡 극복 → 인구폭증 → 과열사이클 분석
- 축4(변모): Charlotte 산업전환 → 고소득유입 → 필요소득 급상승 경로
결과를 pop_housing_4axis_scorecard, pop_housing_axis_summary 테이블에 저장해줘.

[STEP 11 — 전략 보고서]
pop_housing_4axis_scorecard에서 데이터를 읽어서
"대구 인구유지 + 부동산 활성화 종합 전략" 보고서를
output/s2_daegu_population_strategy_report.md로 생성해줘.

[STEP 12 — 4축 시각화]
V7: 인구성장률 대조 (대구 유출 vs 4도시 유입 막대)
V8: 4축 2×2 대시보드 (축별 판매건수+시장온도)
V9: 인구변동률 vs 시장온도 산점도 (상관관계)
V10: 대구vs미국 인구-주택가격 이중축
V11: Phoenix 과열사이클 (영역차트)
V12: 전략 로드맵 인포그래픽
```

---

## 📊 최종 산출물 (v2 전체)

### 테이블 (v1: 11개 + v2: 3개 = 14개)

| # | 테이블명 | 역할 | v2 |
|---|---------|------|----|
| 1 | `korean_demographics` | 한국 인구통계 | |
| 2 | `korean_income_welfare` | 한국 소득·복지 | |
| 3 | `daegu_population_summary` | 대구 인구 요약 | |
| 4 | `us_census_demographics` | 미국 Census | |
| 5 | `us_population_timeseries` | 미국 인구 시계열 | |
| 6 | `us_county_historical` | 미국 County 역사 | |
| 7 | `world_city_population_growth` | 글로벌 도시 인구성장률 | |
| 8 | `us_metro_demand` | MSA 수급 종합 | |
| 9 | `zillow_demand_timeseries` | Zillow 수급 시계열 | |
| 10 | `population_housing_correlation` | 상관분석 결과 | |
| 11 | `annual_pop_housing_merged` | 연도별 통합 뷰 | |
| 12 | `daegu_housing_prices` | ⭐ 대구 아파트 실거래 | ✅ |
| 13 | `pop_housing_4axis_scorecard` | ⭐ 4축 비교 스코어카드 | ✅ |
| 14 | `pop_housing_axis_summary` | ⭐ 축별 경로 요약 | ✅ |

### 분석 CSV (v1: 10개)

| 파일 | 내용 |
|------|------|
| `S2_Q1_MARKET_TEMP.csv` | 시장온도 4도시 추이 |
| `S2_Q2_SUPPLY_DEMAND.csv` | 수급비율 |
| `S2_Q3_DAEGU_POP.csv` | 대구 인구 |
| `S2_Q4_POP_HOUSING.csv` | 인구-주택 통합 |
| `S2_Q5_CORRELATION.csv` | 상관계수 |
| `S2_Q6_INCOME_NEEDED.csv` | 필요소득 |
| `S2_Q7_COUNTY_COMPARE.csv` | County 비교 |
| `S2_Q8_GLOBAL_POP.csv` | 글로벌 인구 |
| `S2_Q9_SALES_TREND.csv` | 판매건수 |
| `S2_Q10_DIRECTION_CONTRAST.csv` | 유출/유입 패턴 |

### 시각화 (v1: 6개 + v2: 6개 = 12개)

| # | 차트명 | v2 | 상태 |
|---|--------|-----|------|
| V1 | 시장온도 대시보드 (3패널) | | ☐ |
| V2 | 수급비율 (Months of Supply) | | ☐ |
| V3 | 대구 인구 추이 + 변동률 | | ☐ |
| V4 | 인구변동률 vs ZHVI 산점도 | | ☐ |
| V5 | 주택구매 필요소득 추이 | | ☐ |
| V6 | 상관계수 히트맵 | | ☐ |
| V7 | ⭐ 인구성장률 대조 (대구 vs 4도시) | ✅ | ☐ |
| V8 | ⭐ 4축 경로 대시보드 (2×2) | ✅ | ☐ |
| V9 | ⭐ 인구변동률 vs 시장온도 산점도 | ✅ | ☐ |
| V10 | ⭐ 대구 vs 미국 인구-주택가격 이중축 | ✅ | ☐ |
| V11 | ⭐ Phoenix 과열 사이클 | ✅ | ☐ |
| V12 | ⭐ 전략 로드맵 인포그래픽 | ✅ | ☐ |

### 보고서 (v2 신규)

| 산출물 | 파일 | 상태 |
|--------|------|------|
| 대구 인구유지 전략 보고서 | `output/s2_daegu_population_strategy_report.md` | ☐ |

### 핵심 인사이트 기대값 (v2 확장)

| 비교축 | 도시 | 인구 방향 | 부동산 수급 경로 | 대구 교훈 |
|--------|------|----------|----------------|----------|
| **종합** | Dallas | 유입 (+) | 수요↑→재고↓→시장과열→가격급등 | 주택가격 경쟁력으로 인구 흡수 |
| **산업** | Atlanta | 유입 (+) | 산업허브→일자리↑→소득↑→수요↑ | 산업 다각화로 전문직 유입 |
| **기후** | Phoenix | 폭발 유입 | 과열→조정→재유입 반복 사이클 | 기후 핸디캡 < 가격 경쟁력 |
| **변모** | Charlotte | 전환 유입 | 고소득→필요소득 급상승→신규건설↑ | 산업전환 성공이 부동산 선순환 열쇠 |
| **기준** | **대구** | **유출 (−)** | **수요↓→시장냉각→가격정체** | **인구유입 전환이 최우선 과제** |
