"""
STEP 0: DB 연결 공통 모듈 + 데이터베이스 생성
실행: python src/subtopic1/step0_init_db.py
"""
import os
import sys
import math
import pymysql
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── 경로 설정 ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATA_KAGGLE_DIR = os.path.join(BASE_DIR, 'data_kaggle')
OUTPUT_DIR = os.path.join(BASE_DIR, 'src', 'subtopic1', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── DB 접속 정보 ──
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '***REMOVED***',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
DB_NAME = 'real_estate_comparison'

# ── 비교 대상 도시 (실제 ZHVI CSV의 RegionName 값 기준) ──
TARGET_METROS = [
    'Dallas, TX',
    'Atlanta, GA',
    'Phoenix, AZ',
    'Charlotte, NC',
    'United States',
]

# ── 환율 ──
EXCHANGE_RATE = 1300  # 1 USD = 1,300 KRW

# ── 분석 기간 ──
ANALYSIS_START = '2015-01'
ANALYSIS_END = '2024-12'

COVID_PERIODS = {
    'Pre-COVID':  ('2018-01', '2020-02'),
    'COVID-Peak': ('2020-03', '2021-12'),
    'Post-Peak':  ('2022-01', '2024-12'),
}

# ── 데이터 파일 경로 ──
DATA_FILES = {
    'ZHVI_WIDE': os.path.join(DATA_DIR, 'zillow_Housing Data',
                              'Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    'ZORI_WIDE': os.path.join(DATA_DIR, 'zillow_Housing Data',
                              'Metro_zori_uc_sfrcondomfr_sm_month.csv'),
    'ZHVF_GROWTH': os.path.join(DATA_DIR, 'zillow_Housing Data',
                                'Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    'ZORF_GROWTH': os.path.join(DATA_DIR, 'zillow_Housing Data',
                                'National_zorf_growth_uc_sfr_sm_month.csv'),
    'METRO_TS': os.path.join(DATA_DIR, 'Zillow Economics Data', 'Metro_time_series.csv'),
    'STATE_TS': os.path.join(DATA_DIR, 'Zillow Economics Data', 'State_time_series.csv'),
    'CITY_TS': os.path.join(DATA_DIR, 'Zillow Economics Data', 'City_time_series.csv'),
    'COUNTY_CROSSWALK': os.path.join(DATA_DIR, 'Zillow Economics Data', 'CountyCrossWalk_Zillow.csv'),
    'CITIES_CROSSWALK': os.path.join(DATA_DIR, 'Zillow Economics Data', 'cities_crosswalk.csv'),
    'REALTOR': os.path.join(DATA_DIR, 'realtor-data.zip.csv'),
    'DAEGU_APT': os.path.join(DATA_KAGGLE_DIR, 'daegu apartment actual transaction', 'Daegu_apt.csv'),
    'DAEGU_RE': os.path.join(DATA_KAGGLE_DIR, 'Daegu_Real_Estate_data.csv'),
    'APART_DEAL': os.path.join(DATA_KAGGLE_DIR, 'Apart Deal.csv'),
}


def safe_val(v):
    """Convert NaN/NaT/None-like values to None for MySQL"""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or np.isnan(v)):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def get_connection(db_name=None, for_pandas=False):
    """MySQL 연결 반환. for_pandas=True면 DictCursor 제외 (pd.read_sql 호환)"""
    config = DB_CONFIG.copy()
    if for_pandas:
        config.pop('cursorclass', None)
    if db_name:
        config['db'] = db_name
    return pymysql.connect(**config)


def execute_sql(sql, db_name=DB_NAME, fetch=False):
    """단일 SQL 실행 헬퍼"""
    conn = get_connection(db_name)
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return result


def create_database():
    """데이터베이스 생성"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                   f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    conn.close()
    print(f"[OK] DB '{DB_NAME}' 생성/확인 완료")


if __name__ == '__main__':
    create_database()
    print("[DONE] STEP 0 완료")
