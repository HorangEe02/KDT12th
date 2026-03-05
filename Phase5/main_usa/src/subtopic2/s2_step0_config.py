"""
STEP 0: 소주제2 공통 설정 — subtopic1의 step0_init_db.py 재사용 + S2 전용 상수
실행: import만 하면 됨 (직접 실행 불필요)
"""
import sys
import os

# ── 경로 설정 ──
S2_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(S2_DIR)
BASE_DIR = os.path.dirname(SRC_DIR)

# subtopic1 모듈 임포트 경로
S1_DIR = os.path.join(SRC_DIR, 'subtopic1')
sys.path.insert(0, S1_DIR)

from step0_init_db import (
    get_connection, DB_NAME, DB_CONFIG, safe_val,
    create_database, execute_sql,
    DATA_DIR, DATA_KAGGLE_DIR,
    TARGET_METROS, EXCHANGE_RATE,
)

# ── S2 전용 출력 경로 ──
S2_OUTPUT_DIR = os.path.join(S2_DIR, 'output')
os.makedirs(S2_OUTPUT_DIR, exist_ok=True)

# ── S2 전용 데이터 파일 경로 ──
ZILLOW_HOUSING_DIR = os.path.join(DATA_DIR, 'zillow_Housing Data')
ZILLOW_ECONOMICS_DIR = os.path.join(DATA_DIR, 'Zillow Economics Data')

S2_DATA_FILES = {
    # Zillow Housing — 수급 지표 5개
    'INVENTORY': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_invt_fs_uc_sfrcondo_sm_month.csv'),
    'MARKET_TEMP': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_market_temp_index_uc_sfrcondo_month.csv'),
    'DAYS_PENDING': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_mean_doz_pending_uc_sfrcondo_sm_month.csv'),
    'SALES_COUNT': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_sales_count_now_uc_sfrcondo_month.csv'),
    'INCOME_NEEDED': os.path.join(ZILLOW_HOUSING_DIR,
                                   'Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    # Zillow Economics
    'METRO_TS': os.path.join(ZILLOW_ECONOMICS_DIR, 'Metro_time_series.csv'),
    'STATE_TS': os.path.join(ZILLOW_ECONOMICS_DIR, 'State_time_series.csv'),
    # Kaggle — 한국
    'KR_DEMOGRAPHICS': os.path.join(DATA_KAGGLE_DIR, 'Korean_demographics_2000-2022.csv'),
    'KR_INCOME': os.path.join(DATA_KAGGLE_DIR, 'Korea Income and Welfare', 'Korea Income and Welfare.csv'),
    # Kaggle — US
    'ACS2015': os.path.join(DATA_KAGGLE_DIR, 'US Census Demographic Data', 'acs2015_county_data.csv'),
    'ACS2017': os.path.join(DATA_KAGGLE_DIR, 'US Census Demographic Data', 'acs2017_county_data.csv'),
    'US_COUNTY_DEMO': os.path.join(DATA_KAGGLE_DIR, 'US County & Zipcode Historical Demographics',
                                    'us_county_demographics.csv'),
    'POP_TIMESERIES': os.path.join(DATA_KAGGLE_DIR, 'Population Time Series Data', 'POP.csv'),
    # Kaggle — Global
    'WORLD_POP_GROWTH': os.path.join(DATA_KAGGLE_DIR, 'Wprld population growth rate by cities 2024.csv'),
}

# ── 타겟 도시 (짧은 형식 — 실제 Zillow CSV의 RegionName) ──
S2_TARGET_METROS = [
    'Dallas, TX',
    'Atlanta, GA',
    'Phoenix, AZ',
    'Charlotte, NC',
    'United States',
]

TARGET_STATES_FULL = ['Texas', 'Georgia', 'Arizona', 'North Carolina']
TARGET_STATES_ABBR = ['TX', 'GA', 'AZ', 'NC']
TARGET_STATES_ALL = set(TARGET_STATES_FULL + TARGET_STATES_ABBR)

# County → city_id 매핑 (subtopic1 cities 테이블 기준)
# city_id: 1=대구, 2=Dallas, 3=Atlanta, 4=Phoenix, 5=Charlotte
COUNTY_CITY_MAP = {
    ('Dallas', 'Texas'): 2, ('Dallas', 'TX'): 2,
    ('Fulton', 'Georgia'): 3, ('Fulton', 'GA'): 3,
    ('DeKalb', 'Georgia'): 3, ('DeKalb', 'GA'): 3,
    ('Maricopa', 'Arizona'): 4, ('Maricopa', 'AZ'): 4,
    ('Mecklenburg', 'North Carolina'): 5, ('Mecklenburg', 'NC'): 5,
}

TARGET_GLOBAL_CITIES = ['Daegu', 'Dallas', 'Atlanta', 'Phoenix', 'Charlotte']

if __name__ == '__main__':
    print(f"[S2 CONFIG] BASE_DIR: {BASE_DIR}")
    print(f"[S2 CONFIG] S2_OUTPUT_DIR: {S2_OUTPUT_DIR}")
    for k, v in S2_DATA_FILES.items():
        exists = os.path.exists(v)
        print(f"  {'OK' if exists else 'MISSING'} {k}: {v}")
