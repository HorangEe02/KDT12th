"""
STEP 0: 소주제3 공통 설정 — subtopic1의 step0_init_db.py 재사용 + S3 전용 상수
실행: import만 하면 됨 (직접 실행 불필요)
"""
import sys
import os

# ── 경로 설정 ──
S3_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(S3_DIR)
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

# ── S3 전용 출력 경로 ──
S3_OUTPUT_DIR = os.path.join(S3_DIR, 'output')
os.makedirs(S3_OUTPUT_DIR, exist_ok=True)

# ── S3 전용 데이터 파일 경로 ──
ZILLOW_ECONOMICS_DIR = os.path.join(DATA_DIR, 'Zillow Economics Data')

S3_DATA_FILES = {
    # 기후 데이터 (Kaggle)
    'BERKELEY_EARTH': os.path.join(DATA_KAGGLE_DIR,
                                   'Climate Change_Earth Surface Temperature Data',
                                   'GlobalLandTemperaturesByCity.csv'),
    'CITY_TEMP_DAILY': os.path.join(DATA_KAGGLE_DIR, 'city_temperature.csv'),
    'US_CITY_TEMP_MONTHLY': os.path.join(DATA_KAGGLE_DIR, 'US_City_Temp_Data.csv'),
    'WEATHER_EVENTS': os.path.join(DATA_KAGGLE_DIR, 'WeatherEvents_Jan2016-Dec2022.csv'),
    # Zillow ZIP 시계열
    'ZIP_TIME_SERIES': os.path.join(ZILLOW_ECONOMICS_DIR, 'Zip_time_series.csv'),
    'CITIES_CROSSWALK': os.path.join(ZILLOW_ECONOMICS_DIR, 'cities_crosswalk.csv'),
}

# ── 타겟 도시 ──
# Berkeley Earth에 Daegu/Taegu 없음 → Seoul을 한국 대표로 사용
TARGET_CITIES_BERKELEY = [
    'Daegu', 'Taegu', 'Seoul',
    'Dallas', 'Atlanta', 'Phoenix', 'Charlotte',
]

TARGET_CITIES_DAILY = {
    'dallas', 'atlanta', 'phoenix', 'charlotte',
    'daegu', 'taegu',
}

# C3-4 Wide 형식에서 추출할 열 (US_City_Temp_Data.csv)
TARGET_CITY_COLS_WIDE = ['dallas', 'atlanta', 'phoenix', 'charlotte']

TARGET_STATES = {'Texas', 'TX', 'Georgia', 'GA', 'Arizona', 'AZ', 'North Carolina', 'NC'}
TARGET_COUNTRIES = {'US', 'United States', 'South Korea', 'Korea'}
TARGET_STATES_US = {'Texas', 'TX', 'Georgia', 'GA', 'Arizona', 'AZ', 'North Carolina', 'NC'}

# 기후 유형 매핑
CLIMATE_TYPE_MAP = {
    'Dallas': '아열대 습윤 (내륙)',
    'Atlanta': '아열대 습윤',
    'Phoenix': '고온 사막 (분지)',
    'Charlotte': '아열대 습윤 (피드몬트)',
    'Daegu': '대륙성 (분지)',
    'Taegu': '대륙성 (분지)',
    'Seoul': '대륙성 습윤 (한국 대표)',
}

# city_id 매핑
CITY_ID_NAME_MAP = {2: 'Dallas', 3: 'Atlanta', 4: 'Phoenix', 5: 'Charlotte'}

# ── 시각화 색상 ──
CITY_COLORS = {
    'Dallas': '#E74C3C', 'Atlanta': '#3498DB',
    'Phoenix': '#E67E22', 'Charlotte': '#2ECC71',
    '대구': '#9B59B6', 'Daegu': '#9B59B6', 'Taegu': '#9B59B6',
    'Seoul': '#9B59B6',
}

if __name__ == '__main__':
    print(f"[S3 CONFIG] BASE_DIR: {BASE_DIR}")
    print(f"[S3 CONFIG] S3_OUTPUT_DIR: {S3_OUTPUT_DIR}")
    for k, v in S3_DATA_FILES.items():
        exists = os.path.exists(v)
        print(f"  {'OK' if exists else 'MISSING'} {k}: {v}")
