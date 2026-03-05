"""
STEP 0: 소주제4 공통 설정 — subtopic1의 step0_init_db.py 재사용 + S4 전용 상수
실행: import만 하면 됨 (직접 실행 불필요)
"""
import sys
import os
import math
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── 경로 설정 ──
S4_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(S4_DIR)
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

# ── S4 전용 출력 경로 ──
S4_OUTPUT_DIR = os.path.join(S4_DIR, 'output')
os.makedirs(S4_OUTPUT_DIR, exist_ok=True)

# ── 데이터 디렉토리 ──
ZILLOW_HOUSING_DIR = os.path.join(DATA_DIR, 'zillow_Housing Data')
ZILLOW_ECONOMICS_DIR = os.path.join(DATA_DIR, 'Zillow Economics Data')

# ── S4 전용 데이터 파일 경로 ──
S4_DATA_FILES = {
    # Zillow Housing (수급지표)
    'NEW_CON_SALES': os.path.join(ZILLOW_HOUSING_DIR,
                                   'Metro_new_con_sales_count_raw_uc_sfrcondo_month.csv'),
    'MARKET_TEMP': os.path.join(ZILLOW_HOUSING_DIR,
                                 'Metro_market_temp_index_uc_sfrcondo_month.csv'),
    'INCOME_NEEDED': os.path.join(ZILLOW_HOUSING_DIR,
                                   'Metro_new_homeowner_income_needed_downpayment_0.20_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    'SALES_COUNT': os.path.join(ZILLOW_HOUSING_DIR,
                                 'Metro_sales_count_now_uc_sfrcondo_month.csv'),
    'ZHVF_GROWTH': os.path.join(ZILLOW_HOUSING_DIR,
                                 'Metro_zhvf_growth_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
    # Zillow Economics
    'STATE_TS': os.path.join(ZILLOW_ECONOMICS_DIR, 'State_time_series.csv'),
    # BLS Employment
    'BLS_DATA': os.path.join(DATA_KAGGLE_DIR, 'National Employment, Hours, and Earnings',
                              'all.data.combined.csv'),
    'BLS_SERIES': os.path.join(DATA_KAGGLE_DIR, 'National Employment, Hours, and Earnings',
                                'ce.series.csv'),
    'BLS_INDUSTRY': os.path.join(DATA_KAGGLE_DIR, 'National Employment, Hours, and Earnings',
                                  'ce.industry.csv'),
    'BLS_SUPERSECTOR': os.path.join(DATA_KAGGLE_DIR, 'National Employment, Hours, and Earnings',
                                     'ce.supersector.csv'),
    # Global Economy
    'GLOBAL_ECONOMY': os.path.join(DATA_KAGGLE_DIR, 'Global Economy Indicators.csv'),
    'MACRO_GDP_PC': os.path.join(DATA_KAGGLE_DIR,
                                  'Macro-Economic Indicators Dataset (Country-Level)',
                                  'GDP_per_capita.csv'),
    'WORLD_GDP': os.path.join(DATA_KAGGLE_DIR,
                               'World GDP by Country, Region, and Income Group',
                               'gdp_data.csv'),
    # Korean data
    'KR_DEMOGRAPHICS': os.path.join(DATA_KAGGLE_DIR, 'Korean_demographics_2000-2022.csv'),
    'KR_INCOME': os.path.join(DATA_KAGGLE_DIR, 'Korea Income and Welfare',
                               'Korea Income and Welfare.csv'),
}

# ── 타겟 MSA (Zillow Housing 파일의 실제 RegionName) ──
TARGET_MSA_NAMES = [
    'Dallas, TX',
    'Atlanta, GA',
    'Phoenix, AZ',
    'Charlotte, NC',
]

# MSA 약칭 매핑
MSA_SHORT = {
    'Dallas, TX': 'Dallas',
    'Atlanta, GA': 'Atlanta',
    'Phoenix, AZ': 'Phoenix',
    'Charlotte, NC': 'Charlotte',
    'United States': 'US',
}

# 도시별 city_id 매핑
CITY_ID_MAP = {
    'Dallas': 2, 'Atlanta': 3, 'Phoenix': 4, 'Charlotte': 5,
}

# 주(State) 매핑
STATE_MAP = {
    'Dallas': 'TX', 'Atlanta': 'GA', 'Phoenix': 'AZ', 'Charlotte': 'NC',
}

# 타겟 주 (State_time_series)
TARGET_STATES = ['Texas', 'Georgia', 'Arizona', 'North Carolina']

# BLS supersector 코드 (산업별 고용)
BLS_SUPERSECTORS = {
    '05': 'Total private',
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

# ── 시각화 색상 ──
CITY_COLORS = {
    'Dallas, TX': '#E74C3C',
    'Atlanta, GA': '#3498DB',
    'Phoenix, AZ': '#F39C12',
    'Charlotte, NC': '#2ECC71',
    'United States': '#95A5A6',
    'Dallas': '#E74C3C',
    'Atlanta': '#3498DB',
    'Phoenix': '#F39C12',
    'Charlotte': '#2ECC71',
    'Texas': '#E74C3C',
    'Georgia': '#3498DB',
    'Arizona': '#F39C12',
    'North Carolina': '#2ECC71',
    '대구': '#9B59B6',
}


def load_zillow_wide_to_long(csv_path, value_col_name, target_names=None):
    """
    Zillow Wide Format CSV → Long Format DataFrame 변환
    Wide: 행=지역, 열=날짜 → Long: (RegionName, year_month, value)
    """
    if target_names is None:
        target_names = TARGET_MSA_NAMES + ['United States']

    df = pd.read_csv(csv_path)

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    if 'BaseDate' in df.columns:
        id_cols.append('BaseDate')
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(target_names)].copy()
    if df_f.empty:
        print(f"  [WARN] 타겟 MSA 없음: {os.path.basename(csv_path)}")
        return pd.DataFrame()

    df_long = df_f.melt(
        id_vars=[c for c in id_cols if c in df_f.columns],
        value_vars=date_cols,
        var_name='date_raw',
        value_name=value_col_name,
    ).dropna(subset=[value_col_name])
    df_long['year_month'] = df_long['date_raw'].astype(str).str[:7]

    return df_long


if __name__ == '__main__':
    print(f"[S4 CONFIG] BASE_DIR: {BASE_DIR}")
    print(f"[S4 CONFIG] S4_OUTPUT_DIR: {S4_OUTPUT_DIR}")
    for k, v in S4_DATA_FILES.items():
        exists = os.path.exists(v)
        print(f"  {'OK' if exists else 'MISSING'} {k}: {os.path.basename(v)}")
