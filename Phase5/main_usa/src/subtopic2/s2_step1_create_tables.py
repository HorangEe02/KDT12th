"""
STEP 1: 소주제 2 전용 테이블 생성 (11개)
실행: python src/subtopic2/s2_step1_create_tables.py
의존: s2_step0_config.py → step0_init_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from s2_step0_config import get_connection, DB_NAME

TABLES = {

    # ══════════════════════════════════════════
    # A. 인구 데이터 (독립변수 측)
    # ══════════════════════════════════════════

    'korean_demographics': """
        CREATE TABLE IF NOT EXISTS korean_demographics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT COMMENT '연도',
            region VARCHAR(50) COMMENT '시도명',
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

    'korean_income_welfare': """
        CREATE TABLE IF NOT EXISTS korean_income_welfare (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT,
            region VARCHAR(50),
            household_income DECIMAL(15,2) COMMENT '가구 평균 소득 (만원)',
            sample_count INT COMMENT '표본 수',
            avg_family_member DECIMAL(4,2) COMMENT '평균 가구원 수',
            source_dataset VARCHAR(100) DEFAULT 'K2-2 Korea Income Welfare',
            INDEX idx_yr (year, region)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    'daegu_population_summary': """
        CREATE TABLE IF NOT EXISTS daegu_population_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT,
            total_population BIGINT,
            population_change BIGINT,
            population_change_rate DECIMAL(8,4),
            natural_increase INT,
            birth_count INT,
            death_count INT,
            birth_rate DECIMAL(8,4),
            death_rate DECIMAL(8,4),
            avg_household_income DECIMAL(15,2) COMMENT '평균 가구소득 (만원, K2-2 조인)',
            INDEX idx_year (year)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    'us_census_demographics': """
        CREATE TABLE IF NOT EXISTS us_census_demographics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            census_year INT COMMENT 'ACS 조사 연도',
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
            professional DECIMAL(8,4),
            service DECIMAL(8,4),
            construction DECIMAL(8,4),
            production DECIMAL(8,4),
            drive DECIMAL(8,4),
            transit DECIMAL(8,4),
            walk DECIMAL(8,4),
            mean_commute DECIMAL(8,2),
            city_id INT COMMENT 'cities FK',
            source_dataset VARCHAR(100),
            INDEX idx_state (state),
            INDEX idx_county_state (county, state),
            INDEX idx_city (city_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    'us_population_timeseries': """
        CREATE TABLE IF NOT EXISTS us_population_timeseries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date VARCHAR(10) COMMENT '날짜',
            region_name VARCHAR(200) COMMENT '지역명',
            region_type VARCHAR(30) COMMENT '지역 유형',
            population BIGINT,
            population_change BIGINT,
            population_change_rate DECIMAL(8,4),
            source_dataset VARCHAR(100) DEFAULT 'U2-2 Population Time Series',
            INDEX idx_region_date (region_name(100), date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

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

    'world_city_population_growth': """
        CREATE TABLE IF NOT EXISTS world_city_population_growth (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_name VARCHAR(100),
            country VARCHAR(50),
            continent VARCHAR(50),
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

    'us_metro_demand': """
        CREATE TABLE IF NOT EXISTS us_metro_demand (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT COMMENT 'Zillow RegionID',
            size_rank INT,
            region_name VARCHAR(200) COMMENT 'MSA명',
            region_type VARCHAR(30),
            state_name VARCHAR(10),
            `year_month` VARCHAR(7),
            inventory DECIMAL(15,2) COMMENT '매물 재고량',
            market_temp_index DECIMAL(8,2) COMMENT '시장온도지수',
            mean_days_pending DECIMAL(8,2) COMMENT '평균 대기일수',
            sales_count INT COMMENT '월별 판매 건수',
            income_needed DECIMAL(15,2) COMMENT '주택구매 필요소득 USD/년',
            INDEX idx_region_ym (region_name(100), `year_month`),
            INDEX idx_ym (`year_month`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

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
    # D. v2: 4축 비교 분석 테이블
    # ══════════════════════════════════════════

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
        print(f"  [OK] {name}")
    conn.commit()
    conn.close()
    print("[OK] 소주제2 전체 테이블 생성 완료")


if __name__ == '__main__':
    create_all_tables()
    print("[DONE] S2 STEP 1 완료")
