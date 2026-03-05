"""
STEP 1: 테이블 생성 (v2 확장 - 10개 테이블)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import get_connection, DB_NAME

TABLES_SQL = [
    # ==================== 기존 (v1) ====================

    # 1. 미국 산업별 고용
    """
    CREATE TABLE IF NOT EXISTS us_industry_employment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_id INT,
        city_name VARCHAR(50),
        state VARCHAR(10),
        year INT,
        month INT,
        series_id VARCHAR(30),
        supersector_code VARCHAR(10),
        supersector_name VARCHAR(100),
        industry_code VARCHAR(20),
        industry_name VARCHAR(200),
        data_type_code VARCHAR(10),
        employee_count DECIMAL(15,1),
        avg_weekly_hours DECIMAL(8,2),
        avg_hourly_earnings DECIMAL(10,2),
        source_dataset VARCHAR(100) DEFAULT 'bls/employment',
        INDEX idx_city_year (city_name, year),
        INDEX idx_industry (industry_code, year),
        INDEX idx_supersector (supersector_code, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 2. 글로벌 경제지표
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
        construction_pct DECIMAL(8,4),
        unemployment_rate DECIMAL(8,4),
        inflation_rate DECIMAL(8,4),
        population BIGINT,
        source_dataset VARCHAR(100),
        INDEX idx_country_year (country, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 3. MSA 수급지표
    """
    CREATE TABLE IF NOT EXISTS us_metro_demand (
        id INT AUTO_INCREMENT PRIMARY KEY,
        region_id INT,
        region_name VARCHAR(200),
        state_name VARCHAR(50),
        `year_month` VARCHAR(7),
        inventory_count INT,
        market_temp_index DECIMAL(8,2),
        mean_days_pending DECIMAL(8,2),
        sales_count INT,
        new_construction_sales INT,
        income_needed DECIMAL(15,2),
        INDEX idx_region_date (region_name, `year_month`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 4. ZHVI (v2 추가 테이블)
    """
    CREATE TABLE IF NOT EXISTS us_metro_zhvi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        region_id INT,
        region_name VARCHAR(200),
        state_name VARCHAR(50),
        `year_month` VARCHAR(7),
        zhvi DECIMAL(15,2),
        INDEX idx_region_date (region_name, `year_month`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 5. ZORI (v2 추가 테이블)
    """
    CREATE TABLE IF NOT EXISTS us_metro_zori (
        id INT AUTO_INCREMENT PRIMARY KEY,
        region_id INT,
        region_name VARCHAR(200),
        state_name VARCHAR(50),
        `year_month` VARCHAR(7),
        zori DECIMAL(15,2),
        INDEX idx_region_date (region_name, `year_month`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 6. 주택가치 예측 성장률
    """
    CREATE TABLE IF NOT EXISTS us_metro_zhvf_growth (
        id INT AUTO_INCREMENT PRIMARY KEY,
        region_id INT,
        region_name VARCHAR(200),
        state_name VARCHAR(50),
        base_date DATE,
        forecast_date DATE,
        growth_rate DECIMAL(8,4),
        INDEX idx_region (region_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 7. 산업-부동산 영향 분석 결과
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

    # 8. Zillow 종합 시계열
    """
    CREATE TABLE IF NOT EXISTS zillow_timeseries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE,
        region_name VARCHAR(200),
        region_level VARCHAR(20),
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

    # 9. 한국 인구통계
    """
    CREATE TABLE IF NOT EXISTS korean_demographics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT,
        month INT,
        region VARCHAR(50),
        total_population BIGINT,
        population_change BIGINT,
        population_change_rate DECIMAL(8,4),
        birth_count INT,
        birth_rate DECIMAL(8,4),
        death_count INT,
        death_rate DECIMAL(8,4),
        natural_growth INT,
        natural_growth_rate DECIMAL(8,4),
        marriage_count INT,
        marriage_rate DECIMAL(8,4),
        divorce_count INT,
        divorce_rate DECIMAL(8,4),
        economic_activity_rate DECIMAL(8,4),
        employment_rate DECIMAL(8,4),
        unemployment_rate DECIMAL(8,4),
        source_dataset VARCHAR(100),
        INDEX idx_region_year (region, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ==================== v2 추가 ====================

    # 10. 도시별 인구성장률 비교
    """
    CREATE TABLE IF NOT EXISTS city_comparison_population (
        id INT AUTO_INCREMENT PRIMARY KEY,
        city_name VARCHAR(100),
        country VARCHAR(50),
        continent VARCHAR(50),
        comparison_axis VARCHAR(30) COMMENT '종합/산업/기후/변모',
        population_2024 BIGINT,
        population_2023 BIGINT,
        population_growth_rate DECIMAL(8,4),
        source_dataset VARCHAR(100),
        INDEX idx_city (city_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 11. 대구 아파트 실거래
    """
    CREATE TABLE IF NOT EXISTS daegu_housing_prices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        `year_month` VARCHAR(7),
        year INT,
        month INT,
        district VARCHAR(30) COMMENT '구/군',
        apt_name VARCHAR(200),
        exclusive_area DECIMAL(10,2) COMMENT '전용면적 (m2)',
        deal_amount BIGINT COMMENT '거래금액 (만원)',
        floor INT,
        build_year INT,
        housing_type VARCHAR(30),
        source_dataset VARCHAR(100),
        INDEX idx_district_year (district, year),
        INDEX idx_year_month (`year_month`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 12. 4축 비교 종합 스코어카드
    """
    CREATE TABLE IF NOT EXISTS city_axis_scorecard (
        id INT AUTO_INCREMENT PRIMARY KEY,
        comparison_axis VARCHAR(30) COMMENT '종합/산업/기후/변모',
        daegu_metric_name VARCHAR(100),
        daegu_value DECIMAL(15,4),
        us_city_name VARCHAR(50),
        us_metric_name VARCHAR(100),
        us_value DECIMAL(15,4),
        metric_category VARCHAR(50) COMMENT '인구/주택가격/고용/기후/소득',
        year_or_period VARCHAR(20),
        gap_ratio DECIMAL(8,4) COMMENT '대구/미국 비율',
        insight TEXT,
        strategy_implication TEXT,
        INDEX idx_axis (comparison_axis),
        INDEX idx_category (metric_category)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def create_database():
    """DB 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    conn.close()
    print(f"  DB '{DB_NAME}' 확인/생성 완료")


def create_subtopic4_tables():
    """소주제4 테이블 생성 (v2: 12개)"""
    create_database()
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    created = 0
    for sql in TABLES_SQL:
        try:
            cursor.execute(sql)
            tbl = sql.split('EXISTS')[1].split('(')[0].strip()
            print(f"  [OK] {tbl}")
            created += 1
        except Exception as e:
            print(f"  [ERR] {e}")
    conn.commit()
    conn.close()
    print(f"\n  소주제 4 테이블 생성 완료 ({created}개)")


def truncate_s4_tables():
    """S4 전용 테이블 초기화"""
    s4_tables = [
        'us_industry_employment', 'economic_indicators',
        'us_metro_demand', 'us_metro_zhvi', 'us_metro_zori',
        'us_metro_zhvf_growth', 'industry_housing_impact',
        'zillow_timeseries', 'korean_demographics',
        'city_comparison_population', 'daegu_housing_prices',
        'city_axis_scorecard',
    ]
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for tbl in s4_tables:
        try:
            cursor.execute(f"TRUNCATE TABLE `{tbl}`")
            print(f"  [TRUNCATE] {tbl}")
        except Exception as e:
            print(f"  [SKIP] {tbl}: {e}")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 1: 테이블 생성 (v2)")
    print("=" * 60)
    create_subtopic4_tables()
    truncate_s4_tables()
