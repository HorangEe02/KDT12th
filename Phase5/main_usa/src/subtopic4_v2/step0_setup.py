"""
STEP 0: 공통 유틸리티 모듈
- DB 연결, CSV→MySQL 로딩, Zillow Wide→Long 변환
- 4축 비교 프레임워크 설정 (v2)
"""

import pymysql
import pandas as pd
import numpy as np
import os
import glob

# ===== 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, 'src', 'subtopic4_v2')
OUTPUT_DIR = os.path.join(SRC_DIR, 'output')
DATA_DIR = os.path.join(BASE_DIR, 'data')
KAGGLE_DIR = os.path.join(BASE_DIR, 'data_kaggle')
ZILLOW_HOUSING_DIR = os.path.join(DATA_DIR, 'zillow_Housing Data')
ZILLOW_ECONOMICS_DIR = os.path.join(DATA_DIR, 'Zillow Economics Data')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== DB 설정 =====
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '***REMOVED***',
    'charset': 'utf8mb4'
}
DB_NAME = 'real_estate_comparison'

# ===== 4개 MSA 명칭 (Zillow CSV 기준) =====
TARGET_METROS = [
    'Dallas, TX',
    'Atlanta, GA',
    'Phoenix, AZ',
    'Charlotte, NC',
]

# ===== 4축 비교 매핑 (v2) =====
AXIS_MAP = {
    'comprehensive': {
        'daegu': '대구', 'us_city': 'Dallas',
        'metro': 'Dallas, TX', 'state': 'Texas', 'state_abbr': 'TX',
        'label_kr': '종합 비교', 'label_en': 'Comprehensive',
        'common': '내륙 대도시, 보수적 성향, 무더운 여름',
    },
    'industry': {
        'daegu': '대구', 'us_city': 'Atlanta',
        'metro': 'Atlanta, GA', 'state': 'Georgia', 'state_abbr': 'GA',
        'label_kr': '산업 비교', 'label_en': 'Industry',
        'common': '자동차·배터리 허브, 교통 요충지',
    },
    'climate': {
        'daegu': '대구', 'us_city': 'Phoenix',
        'metro': 'Phoenix, AZ', 'state': 'Arizona', 'state_abbr': 'AZ',
        'label_kr': '기후 비교', 'label_en': 'Climate',
        'common': '미국 내 최고 수준 여름 기온, 분지 지형',
    },
    'transformation': {
        'daegu': '대구', 'us_city': 'Charlotte',
        'metro': 'Charlotte, NC', 'state': 'North Carolina', 'state_abbr': 'NC',
        'label_kr': '산업 변모 비교', 'label_en': 'Transformation',
        'common': '섬유 산업 역사, 에너지/금융/첨단 도시로 변모',
    },
}

CITY_ID_MAP = {'Dallas': 2, 'Atlanta': 3, 'Phoenix': 4, 'Charlotte': 5}
STATE_MAP = {'Dallas': 'TX', 'Atlanta': 'GA', 'Phoenix': 'AZ', 'Charlotte': 'NC'}
MSA_SHORT = {
    'Dallas, TX': 'Dallas',
    'Atlanta, GA': 'Atlanta',
    'Phoenix, AZ': 'Phoenix',
    'Charlotte, NC': 'Charlotte',
    'United States': 'US Average',
}

# BLS 산업 분류 (supersector codes)
BLS_SUPERSECTORS = {
    '00': 'Total nonfarm',
    '05': 'Total private',
    '06': 'Goods-producing',
    '07': 'Service-providing',
    '08': 'Private service-providing',
    '10': 'Mining and logging',
    '20': 'Construction',
    '30': 'Manufacturing',
    '40': 'Trade, transportation, and utilities',
    '50': 'Information',
    '55': 'Financial activities',
    '60': 'Professional and business services',
    '65': 'Education and health services',
    '70': 'Leisure and hospitality',
    '80': 'Other services',
    '90': 'Government',
}

# 도시별 시각화 색상
CITY_COLORS = {
    'Dallas': '#E74C3C',       'Texas': '#E74C3C',
    'Atlanta': '#3498DB',      'Georgia': '#3498DB',
    'Phoenix': '#F39C12',      'Arizona': '#F39C12',
    'Charlotte': '#2ECC71',    'North Carolina': '#2ECC71',
    '대구': '#9B59B6',         'Daegu': '#9B59B6',
    'United States': '#95A5A6', 'US Average': '#95A5A6',
    'Dallas, TX': '#E74C3C',
    'Atlanta, GA': '#3498DB',
    'Phoenix, AZ': '#F39C12',
    'Charlotte, NC': '#2ECC71',
}

# ===== 데이터 파일 매핑 =====
S4_DATA_FILES = {
    # Zillow Housing
    'NEW_CON_SALES': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv'),
    'MARKET_TEMP': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_market_temp_index_uc_sfrcondo_month.csv'),
    'INCOME_NEEDED': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    'SALES_COUNT': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_sales_count_now_uc_sfrcondo_month.csv'),
    'INVENTORY': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_invt_fs_uc_sfrcondo_sm_month.csv'),
    'ZHVI': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    'ZORI': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_zori_uc_sfrcondomfr_sm_month.csv'),
    'ZHVF_GROWTH': os.path.join(ZILLOW_HOUSING_DIR, 'Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    # Zillow Economics
    'STATE_TS': os.path.join(ZILLOW_ECONOMICS_DIR, 'State_time_series.csv'),
    # BLS
    'BLS_DATA': os.path.join(KAGGLE_DIR, 'National Employment, Hours, and Earnings', 'all.data.combined.csv'),
    'BLS_SERIES': os.path.join(KAGGLE_DIR, 'National Employment, Hours, and Earnings', 'ce.series.csv'),
    'BLS_INDUSTRY': os.path.join(KAGGLE_DIR, 'National Employment, Hours, and Earnings', 'ce.industry.csv'),
    'BLS_SUPERSECTOR': os.path.join(KAGGLE_DIR, 'National Employment, Hours, and Earnings', 'ce.supersector.csv'),
    # Global Economy
    'GLOBAL_ECONOMY': os.path.join(KAGGLE_DIR, 'Global Economy Indicators.csv'),
    # Korean
    'KR_DEMOGRAPHICS': os.path.join(KAGGLE_DIR, 'Korean_demographics_2000-2022.csv'),
    'KR_INCOME': os.path.join(KAGGLE_DIR, 'Korea Income and Welfare', 'Korea Income and Welfare.csv'),
    # v2 추가
    'DAEGU_APT': os.path.join(KAGGLE_DIR, 'daegu apartment actual transaction', 'Daegu_apt.csv'),
    'WORLD_POP_GROWTH': os.path.join(KAGGLE_DIR, 'Wprld population growth rate by cities 2024.csv'),
    'CITY_TEMP': os.path.join(KAGGLE_DIR, 'city_temperature.csv'),
}


# ===== 유틸리티 함수 =====

def get_connection(db_name=None):
    """MySQL 연결 반환"""
    config = DB_CONFIG.copy()
    if db_name:
        config['db'] = db_name
    return pymysql.connect(**config)


def query_to_df(sql, params=None):
    """SQL 쿼리 → pandas DataFrame"""
    conn = get_connection(DB_NAME)
    try:
        df = pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
    return df


def safe_val(val):
    """안전한 값 변환 (NaN → None)"""
    if val is None:
        return None
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    return val


def load_zillow_wide_to_long(csv_path, target_metros=None):
    """Zillow Wide 형식 CSV → Long 형식 DataFrame 변환"""
    if target_metros is None:
        target_metros = TARGET_METROS
    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    if 'BaseDate' in df.columns:
        id_cols.append('BaseDate')
    date_cols = [c for c in df.columns if c not in id_cols]
    filter_names = target_metros + ['United States']
    df_f = df[df['RegionName'].isin(filter_names)].copy()
    if df_f.empty:
        print(f"  [WARN] 타겟 MSA 없음: {os.path.basename(csv_path)}")
        return pd.DataFrame()
    df_long = df_f.melt(
        id_vars=[c for c in id_cols if c in df_f.columns],
        value_vars=date_cols, var_name='year_month', value_name='value'
    ).dropna(subset=['value'])
    df_long['year_month'] = df_long['year_month'].astype(str).str[:7]
    return df_long


def batch_insert(conn, sql, data, batch_size=5000):
    """배치 INSERT"""
    cursor = conn.cursor()
    total = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany(sql, batch)
        conn.commit()
        total += len(batch)
    return total


if __name__ == '__main__':
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"\n데이터 파일 존재 확인:")
    for key, path in S4_DATA_FILES.items():
        exists = os.path.exists(path)
        size = os.path.getsize(path) / 1024 / 1024 if exists else 0
        status = f"OK ({size:.1f}MB)" if exists else "MISSING"
        print(f"  {key:20s}: {status}")
    print(f"\nMySQL 연결 테스트:")
    try:
        conn = get_connection(DB_NAME)
        conn.close()
        print("  OK - real_estate_comparison DB 연결 성공")
    except Exception as e:
        print(f"  FAIL: {e}")
