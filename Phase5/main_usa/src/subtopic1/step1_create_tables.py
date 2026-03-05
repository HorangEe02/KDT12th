"""
STEP 1: 소주제 1 관련 테이블 생성 + 도시 마스터 데이터 삽입
실행: python src/subtopic1/step1_create_tables.py
의존: step0_init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from step0_init_db import get_connection, DB_NAME, create_database


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

    # ── 1-A. 대구 아파트 실거래가 ──
    'daegu_housing_prices': """
        CREATE TABLE IF NOT EXISTS daegu_housing_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `year_month` VARCHAR(7) COMMENT 'YYYY-MM',
            district VARCHAR(30) COMMENT '구/군',
            dong VARCHAR(50) COMMENT '동',
            apt_name VARCHAR(100) COMMENT '아파트명',
            exclusive_area DECIMAL(10,2) COMMENT '전용면적 m2',
            deal_amount BIGINT COMMENT '거래금액 (만원)',
            floor INT COMMENT '층',
            build_year INT COMMENT '건축년도',
            deal_date DATE COMMENT '거래일자',
            deal_type VARCHAR(20) COMMENT '거래유형',
            source_dataset VARCHAR(100) COMMENT '원본 데이터셋명',
            INDEX idx_ym (`year_month`),
            INDEX idx_district (district),
            INDEX idx_date (deal_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-B. 대구 월별 집계 ──
    'daegu_monthly_summary': """
        CREATE TABLE IF NOT EXISTS daegu_monthly_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `year_month` VARCHAR(7),
            district VARCHAR(30),
            avg_price BIGINT COMMENT '평균 거래금액 (만원)',
            median_price BIGINT COMMENT '중위 거래금액 (만원)',
            min_price BIGINT,
            max_price BIGINT,
            transaction_count INT COMMENT '거래 건수',
            avg_area DECIMAL(10,2) COMMENT '평균 전용면적 m2',
            avg_price_per_m2 DECIMAL(12,2) COMMENT 'm2당 평균가 (만원)',
            yoy_change_rate DECIMAL(8,4) COMMENT '전년동기 대비 변동률',
            INDEX idx_ym_district (`year_month`, district)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-C. 미국 Realtor.com 개별 매물 ──
    'us_realtor_listings': """
        CREATE TABLE IF NOT EXISTS us_realtor_listings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_id INT COMMENT 'cities 테이블 FK',
            brokered_by DOUBLE,
            status VARCHAR(30) COMMENT '매물상태',
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

    # ── 1-D. 미국 MSA ZHVI (Wide -> Long) ──
    'us_metro_zhvi': """
        CREATE TABLE IF NOT EXISTS us_metro_zhvi (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT COMMENT 'Zillow RegionID',
            size_rank INT COMMENT '지역크기 순위',
            region_name VARCHAR(200) COMMENT 'MSA명',
            region_type VARCHAR(30) COMMENT 'country 또는 msa',
            state_name VARCHAR(10) COMMENT '주 약어',
            `year_month` VARCHAR(7) COMMENT 'YYYY-MM',
            zhvi DECIMAL(15,2) COMMENT '주택가치지수 USD',
            INDEX idx_region_ym (region_name(100), `year_month`),
            INDEX idx_ym (`year_month`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-E. 미국 MSA ZORI ──
    'us_metro_zori': """
        CREATE TABLE IF NOT EXISTS us_metro_zori (
            id INT AUTO_INCREMENT PRIMARY KEY,
            region_id INT,
            size_rank INT,
            region_name VARCHAR(200),
            region_type VARCHAR(30),
            state_name VARCHAR(10),
            `year_month` VARCHAR(7),
            zori DECIMAL(12,2) COMMENT '임대관측지수 USD/월',
            INDEX idx_region_ym (region_name(100), `year_month`),
            INDEX idx_ym (`year_month`)
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

    # ── 1-H. Zillow Economics 시계열 ──
    'zillow_economics_ts': """
        CREATE TABLE IF NOT EXISTS zillow_economics_ts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE COMMENT '관측일',
            region_name VARCHAR(200) COMMENT '지역명',
            region_level ENUM('metro','state','city') COMMENT '지역 레벨',
            zhvi_all DECIMAL(15,2) COMMENT 'ZHVI_AllHomes',
            zhvi_sfr DECIMAL(15,2) COMMENT 'ZHVI_SingleFamilyResidence',
            zhvi_condo DECIMAL(15,2) COMMENT 'ZHVI_CondoCoop',
            zhvi_per_sqft DECIMAL(10,2) COMMENT 'ZHVIPerSqft_AllHomes',
            zri_all DECIMAL(12,2) COMMENT 'ZRI_AllHomes',
            zri_per_sqft DECIMAL(10,2) COMMENT 'ZriPerSqft_AllHomes',
            median_listing_price DECIMAL(15,2),
            median_listing_price_sqft DECIMAL(10,2),
            median_rental_price DECIMAL(12,2),
            price_to_rent_ratio DECIMAL(8,4),
            pct_price_reduction DECIMAL(8,4),
            median_pct_price_reduction DECIMAL(8,4),
            pct_homes_increasing DECIMAL(8,4),
            pct_homes_decreasing DECIMAL(8,4),
            sale_counts INT,
            sale_prices DECIMAL(15,2),
            source_file VARCHAR(100),
            INDEX idx_region_date (region_name(100), date),
            INDEX idx_level_date (region_level, date),
            INDEX idx_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,

    # ── 1-I. 미국 월별 집계 ──
    'us_monthly_summary': """
        CREATE TABLE IF NOT EXISTS us_monthly_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city_id INT,
            city_name VARCHAR(50),
            state VARCHAR(50),
            `year_month` VARCHAR(7),
            avg_price DECIMAL(15,2) COMMENT '평균 매물가 USD',
            median_price DECIMAL(15,2) COMMENT '중위 매물가 USD',
            listing_count INT COMMENT '매물 건수',
            avg_house_size DECIMAL(12,2) COMMENT '평균 면적 sqft',
            avg_price_per_sqft DECIMAL(10,2) COMMENT 'sqft당 평균가 USD',
            avg_bed DECIMAL(4,1),
            avg_bath DECIMAL(4,1),
            FOREIGN KEY (city_id) REFERENCES cities(city_id),
            INDEX idx_city_ym (city_name, `year_month`)
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


def insert_cities():
    """비교 대상 5개 도시 마스터 데이터 삽입"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS cnt FROM cities")
    if cursor.fetchone()['cnt'] > 0:
        print("  [INFO] cities 테이블에 이미 데이터 존재 - 스킵")
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
    print("  [OK] 5개 도시 마스터 삽입 완료")


def create_all_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for table_name, ddl in TABLES.items():
        cursor.execute(ddl)
        print(f"  [OK] {table_name}")
    conn.commit()
    conn.close()
    print("[OK] 소주제1 전체 테이블 생성 완료")


if __name__ == '__main__':
    create_database()
    create_all_tables()
    insert_cities()
    print("[DONE] STEP 1 완료")
