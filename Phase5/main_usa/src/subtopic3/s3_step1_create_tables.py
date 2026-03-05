"""
STEP 1: 소주제 3 전용 테이블 생성 (9개)
실행: python src/subtopic3/s3_step1_create_tables.py
의존: subtopic1/step0_init_db.py
"""
from s3_step0_config import get_connection, DB_NAME

TABLES = {

    # ══════════════════════════════════════════
    # A. 기후 데이터
    # ══════════════════════════════════════════

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

    'us_zip_prices': """
        CREATE TABLE IF NOT EXISTS us_zip_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            zip_code VARCHAR(10),
            city_name VARCHAR(100),
            state VARCHAR(30),
            city_id INT COMMENT 'cities FK',
            date DATE,
            `year_month` VARCHAR(7),
            zhvi DECIMAL(15,2) COMMENT 'ZHVI_AllHomes',
            zhvi_per_sqft DECIMAL(10,2) COMMENT 'ZHVIPerSqft_AllHomes',
            median_listing_price DECIMAL(15,2),
            median_rental_price DECIMAL(12,2),
            inventory INT COMMENT 'InventorySeasonallyAdjusted',
            days_on_zillow DECIMAL(8,2),
            source_file VARCHAR(100) DEFAULT 'Zip_time_series.csv',
            INDEX idx_zip_date (zip_code, date),
            INDEX idx_city_date (city_id, date),
            INDEX idx_ym (`year_month`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    'us_zip_realtor_summary': """
        CREATE TABLE IF NOT EXISTS us_zip_realtor_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            zip_code VARCHAR(10),
            city_name VARCHAR(100),
            state VARCHAR(30),
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
        cursor.execute(f"DROP TABLE IF EXISTS `{name}`")
        cursor.execute(ddl)
        print(f"  [OK] {name}")
    conn.commit()
    conn.close()
    print("[OK] 소주제3 전체 테이블 생성 완료 (9개)")


if __name__ == '__main__':
    create_all_tables()
    print("[DONE] S3 STEP 1 완료")
