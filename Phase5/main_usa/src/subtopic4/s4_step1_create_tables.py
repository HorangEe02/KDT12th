"""
STEP 1: 소주제4 전용 MySQL 테이블 생성 (7개)
실행: python src/subtopic4/s4_step1_create_tables.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import get_connection, DB_NAME

TABLES_SQL = [
    # 1. 미국 산업별 고용
    """
    CREATE TABLE IF NOT EXISTS us_industry_employment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT,
        month INT,
        series_id VARCHAR(30),
        supersector_code VARCHAR(10),
        supersector_name VARCHAR(100),
        industry_code VARCHAR(20),
        industry_name VARCHAR(200),
        data_type_code VARCHAR(10),
        employee_count DECIMAL(15,1),
        source_dataset VARCHAR(100) DEFAULT 'bls/employment',
        INDEX idx_ss_year (supersector_code, year),
        INDEX idx_industry (industry_code, year)
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
        state_name VARCHAR(30),
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

    # 4. 주택가치 예측 성장률
    """
    CREATE TABLE IF NOT EXISTS us_metro_zhvf_growth (
        id INT AUTO_INCREMENT PRIMARY KEY,
        region_id INT,
        region_name VARCHAR(200),
        state_name VARCHAR(30),
        base_date DATE,
        forecast_date DATE,
        growth_rate DECIMAL(8,4),
        INDEX idx_region (region_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # 5. 산업-부동산 영향 분석 결과
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

    # 6. Zillow Economics 종합 시계열
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

    # 7. 한국 인구통계 (대구 산업 프록시)
    """
    CREATE TABLE IF NOT EXISTS korean_demographics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT,
        month INT,
        region VARCHAR(50),
        total_population BIGINT,
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
        source_dataset VARCHAR(100),
        INDEX idx_region_year (region, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


ALTER_SQL = [
    # us_metro_demand: 기존 subtopic2 테이블에 new_construction_sales 추가
    "ALTER TABLE us_metro_demand ADD COLUMN new_construction_sales INT AFTER sales_count",
    # korean_demographics: 기존 테이블에 S4 전용 컬럼 추가
    "ALTER TABLE korean_demographics ADD COLUMN month INT AFTER year",
    "ALTER TABLE korean_demographics ADD COLUMN natural_growth INT AFTER death_rate",
    "ALTER TABLE korean_demographics ADD COLUMN natural_growth_rate DECIMAL(8,4) AFTER natural_growth",
    "ALTER TABLE korean_demographics ADD COLUMN marriage_count INT AFTER natural_growth_rate",
    "ALTER TABLE korean_demographics ADD COLUMN marriage_rate DECIMAL(8,4) AFTER marriage_count",
    "ALTER TABLE korean_demographics ADD COLUMN divorce_count INT AFTER marriage_rate",
    "ALTER TABLE korean_demographics ADD COLUMN divorce_rate DECIMAL(8,4) AFTER divorce_count",
]


def create_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # CREATE TABLE IF NOT EXISTS (새 테이블만 생성)
    for i, sql in enumerate(TABLES_SQL):
        try:
            tbl = sql.split('EXISTS')[1].split('(')[0].strip().strip('`')
            cursor.execute(sql)
            print(f"  [OK] {tbl}")
        except Exception as e:
            print(f"  [ERR] table_{i}: {e}")
    conn.commit()

    # ALTER TABLE (기존 테이블에 누락 컬럼 추가)
    for alter in ALTER_SQL:
        try:
            cursor.execute(alter)
            conn.commit()
            print(f"  [ALTER OK] {alter[:60]}...")
        except Exception as e:
            if 'Duplicate column' in str(e):
                pass
            else:
                print(f"  [ALTER SKIP] {str(e)[:60]}")

    # S4 전용 테이블 TRUNCATE (재실행 시 중복 방지)
    for tbl in ['us_industry_employment', 'us_metro_zhvf_growth', 'industry_housing_impact']:
        try:
            cursor.execute(f'TRUNCATE TABLE {tbl}')
            conn.commit()
            print(f"  [TRUNCATE] {tbl}")
        except Exception as e:
            print(f"  [TRUNCATE SKIP] {tbl}: {e}")

    # 공유 테이블에서 S4 데이터만 삭제 (재실행 안전)
    cleanup = [
        ("zillow_timeseries", "source_file = 'State_time_series.csv'"),
        ("economic_indicators", "source_dataset = 'Global Economy Indicators'"),
        ("korean_demographics", "source_dataset = 'Korean_demographics_2000-2022'"),
    ]
    for tbl, where in cleanup:
        try:
            cursor.execute(f"DELETE FROM {tbl} WHERE {where}")
            cnt = cursor.rowcount
            conn.commit()
            if cnt > 0:
                print(f"  [CLEAN] {tbl}: {cnt}행 삭제")
        except Exception as e:
            print(f"  [CLEAN SKIP] {tbl}: {e}")

    conn.close()
    print("\n[DONE] 소주제4 테이블 생성/수정 완료")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 1: 소주제4 테이블 생성")
    print("=" * 60)
    create_tables()
