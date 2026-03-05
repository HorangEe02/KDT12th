"""
STEP 3: Zillow Economics Long Format 시계열 -> MySQL 적재
실행: python src/subtopic1/step3_load_us_zillow_economics.py

처리 파일:
  - Metro_time_series.csv  (56MB)  -> zillow_economics_ts (region_level='metro')
  - State_time_series.csv  (4.7MB) -> zillow_economics_ts (region_level='state')
  - City_time_series.csv   (689MB) -> zillow_economics_ts (region_level='city')
  + Crosswalk 테이블 2개
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import pymysql
from step0_init_db import get_connection, DB_NAME, DATA_FILES, safe_val

# ── 소주제1 핵심 지표 열 ──
SELECTED_COLS = [
    'Date', 'RegionName',
    'ZHVI_AllHomes', 'ZHVI_SingleFamilyResidence', 'ZHVI_CondoCoop',
    'ZHVIPerSqft_AllHomes',
    'ZRI_AllHomes', 'ZriPerSqft_AllHomes',
    'MedianListingPrice_AllHomes', 'MedianListingPricePerSqft_AllHomes',
    'MedianRentalPrice_AllHomes',
    'PriceToRentRatio_AllHomes',
    'PctOfListingsWithPriceReductions_AllHomes',
    'MedianPctOfPriceReduction_AllHomes',
    'PctOfHomesIncreasingInValues_AllHomes',
    'PctOfHomesDecreasingInValues_AllHomes',
    'Sale_Counts', 'Sale_Prices',
]

# ── 지역 필터 ──
TARGET_STATES = ['Texas', 'Georgia', 'Arizona', 'North Carolina']
TARGET_CITIES_APPROX = ['dallas', 'atlanta', 'phoenix', 'charlotte']


def _build_insert_row(r, region_level, source_file):
    """공통 행 생성 헬퍼"""
    return (
        safe_val(r.get('Date')), str(r['RegionName']), region_level,
        safe_val(r.get('ZHVI_AllHomes')), safe_val(r.get('ZHVI_SingleFamilyResidence')),
        safe_val(r.get('ZHVI_CondoCoop')), safe_val(r.get('ZHVIPerSqft_AllHomes')),
        safe_val(r.get('ZRI_AllHomes')), safe_val(r.get('ZriPerSqft_AllHomes')),
        safe_val(r.get('MedianListingPrice_AllHomes')),
        safe_val(r.get('MedianListingPricePerSqft_AllHomes')),
        safe_val(r.get('MedianRentalPrice_AllHomes')),
        safe_val(r.get('PriceToRentRatio_AllHomes')),
        safe_val(r.get('PctOfListingsWithPriceReductions_AllHomes')),
        safe_val(r.get('MedianPctOfPriceReduction_AllHomes')),
        safe_val(r.get('PctOfHomesIncreasingInValues_AllHomes')),
        safe_val(r.get('PctOfHomesDecreasingInValues_AllHomes')),
        safe_val(r.get('Sale_Counts')), safe_val(r.get('Sale_Prices')),
        source_file
    )


INSERT_SQL = """INSERT INTO zillow_economics_ts
    (date, region_name, region_level,
     zhvi_all, zhvi_sfr, zhvi_condo, zhvi_per_sqft,
     zri_all, zri_per_sqft,
     median_listing_price, median_listing_price_sqft,
     median_rental_price, price_to_rent_ratio,
     pct_price_reduction, median_pct_price_reduction,
     pct_homes_increasing, pct_homes_decreasing,
     sale_counts, sale_prices, source_file)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""


def load_crosswalk_county():
    """CountyCrossWalk_Zillow.csv -> zillow_county_crosswalk"""
    csv_path = DATA_FILES['COUNTY_CROSSWALK']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] County Crosswalk: {csv_path}")
    df = pd.read_csv(csv_path)
    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO zillow_county_crosswalk
             (CountyName, StateName, StateFIPS, CountyFIPS, FIPS,
              MetroName_Zillow, CBSAName, CBSACode,
              CountyRegionID_Zillow, MetroRegionID_Zillow)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    target_cols = ['CountyName', 'StateName', 'StateFIPS', 'CountyFIPS',
                   'FIPS', 'MetroName_Zillow', 'CBSAName', 'CBSACode',
                   'CountyRegionID_Zillow', 'MetroRegionID_Zillow']
    rows = [tuple(safe_val(v) for v in r) for r in df[target_cols].values]

    batch = 1000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
    conn.close()
    print(f"  [OK] zillow_county_crosswalk 적재: {len(rows)}행")

    # 타겟 MSA 매핑 확인
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT MetroName_Zillow, MetroRegionID_Zillow, CBSACode
        FROM zillow_county_crosswalk
        WHERE MetroName_Zillow LIKE '%Dallas%'
           OR MetroName_Zillow LIKE '%Atlanta%'
           OR MetroName_Zillow LIKE '%Phoenix%'
           OR MetroName_Zillow LIKE '%Charlotte%'
    """)
    results = cursor.fetchall()
    print("\n  [INFO] 타겟 MSA 매핑 확인:")
    for row in results:
        print(f"    {row}")
    conn.close()


def load_crosswalk_cities():
    """cities_crosswalk.csv -> zillow_cities_crosswalk"""
    csv_path = DATA_FILES['CITIES_CROSSWALK']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] Cities Crosswalk: {csv_path}")
    df = pd.read_csv(csv_path)
    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO zillow_cities_crosswalk
             (Unique_City_ID, City, County, State)
             VALUES (%s,%s,%s,%s)"""

    rows = [tuple(safe_val(v) for v in r) for r in df[['Unique_City_ID', 'City', 'County', 'State']].values]
    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
    conn.close()
    print(f"  [OK] zillow_cities_crosswalk 적재: {len(rows)}행")

    # 타겟 도시 ID 확인
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    for city in TARGET_CITIES_APPROX:
        cursor.execute("SELECT Unique_City_ID, City, State FROM zillow_cities_crosswalk "
                       "WHERE City LIKE %s LIMIT 5", (f'%{city}%',))
        print(f"  [INFO] '{city}' 매칭: {cursor.fetchall()}")
    conn.close()


def load_state_timeseries():
    """State_time_series.csv -> zillow_economics_ts (region_level='state')"""
    csv_path = DATA_FILES['STATE_TS']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] State 시계열: {csv_path}")

    df_sample = pd.read_csv(csv_path, nrows=5)
    available_cols = [c for c in SELECTED_COLS if c in df_sample.columns]
    print(f"  사용 가능 열: {len(available_cols)}/{len(SELECTED_COLS)}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in available_cols,
                              chunksize=10000):
        chunk = chunk[chunk['RegionName'].isin(TARGET_STATES)]
        if chunk.empty:
            continue
        chunk = chunk.where(pd.notnull(chunk), None)

        rows = [_build_insert_row(r, 'state', 'State_time_series.csv')
                for _, r in chunk.iterrows()]

        cursor.executemany(INSERT_SQL, rows)
        conn.commit()
        total += len(rows)
        print(f"    ... {total}행")

    conn.close()
    print(f"  [OK] State 시계열 적재 완료: {total}행")


def get_target_metro_codes():
    """Crosswalk에서 타겟 MSA 코드 반환"""
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT CAST(MetroRegionID_Zillow AS CHAR) AS code
            FROM zillow_county_crosswalk
            WHERE MetroName_Zillow LIKE '%Dallas%'
               OR MetroName_Zillow LIKE '%Atlanta%'
               OR MetroName_Zillow LIKE '%Phoenix%'
               OR MetroName_Zillow LIKE '%Charlotte%'
        """)
        codes = [r['code'] for r in cursor.fetchall() if r['code']]

        cursor.execute("""
            SELECT DISTINCT CBSACode
            FROM zillow_county_crosswalk
            WHERE MetroName_Zillow LIKE '%Dallas%'
               OR MetroName_Zillow LIKE '%Atlanta%'
               OR MetroName_Zillow LIKE '%Phoenix%'
               OR MetroName_Zillow LIKE '%Charlotte%'
        """)
        cbsa = [r['CBSACode'] for r in cursor.fetchall() if r['CBSACode']]
        conn.close()
        return list(set(codes + cbsa))
    except Exception:
        return []


def get_target_city_ids():
    """Crosswalk에서 타겟 도시 Unique_City_ID 반환"""
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Unique_City_ID
            FROM zillow_cities_crosswalk
            WHERE City IN ('Dallas', 'Atlanta', 'Phoenix', 'Charlotte')
        """)
        ids = [r['Unique_City_ID'] for r in cursor.fetchall() if r['Unique_City_ID']]
        conn.close()
        return ids
    except Exception:
        return []


def load_metro_timeseries():
    """Metro_time_series.csv -> zillow_economics_ts (region_level='metro')"""
    csv_path = DATA_FILES['METRO_TS']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] Metro 시계열: {csv_path}")

    target_codes = get_target_metro_codes()
    if target_codes:
        print(f"  타겟 MSA 코드: {target_codes}")
    else:
        print("  [INFO] Crosswalk 미적재 -> 전체 로딩 (시간 소요)")

    df_sample = pd.read_csv(csv_path, nrows=5)
    available_cols = [c for c in SELECTED_COLS if c in df_sample.columns]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in available_cols,
                              chunksize=10000):
        if target_codes:
            chunk = chunk[chunk['RegionName'].astype(str).isin(target_codes)]
        if chunk.empty:
            continue
        chunk = chunk.where(pd.notnull(chunk), None)

        rows = [_build_insert_row(r, 'metro', 'Metro_time_series.csv')
                for _, r in chunk.iterrows()]

        cursor.executemany(INSERT_SQL, rows)
        conn.commit()
        total += len(rows)
        if total % 50000 == 0:
            print(f"    ... {total}행")

    conn.close()
    print(f"  [OK] Metro 시계열 적재 완료: {total}행")


def load_city_timeseries():
    """City_time_series.csv -> zillow_economics_ts (region_level='city')
    689MB 대용량 - 타겟 도시 필터 적용"""
    csv_path = DATA_FILES['CITY_TS']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] City 시계열: {csv_path}")
    print("  [INFO] 689MB 대용량 - 타겟 도시 필터 적용")

    target_city_ids = get_target_city_ids()
    if not target_city_ids:
        print("  [SKIP] Crosswalk 미적재 또는 타겟 도시 없음")
        print("  -> 먼저 load_crosswalk_cities()를 실행하세요")
        return

    print(f"  필터 대상: {target_city_ids}")

    df_sample = pd.read_csv(csv_path, nrows=5)
    available_cols = [c for c in SELECTED_COLS if c in df_sample.columns]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in available_cols,
                              chunksize=20000):
        chunk = chunk[chunk['RegionName'].isin(target_city_ids)]
        if chunk.empty:
            continue
        chunk = chunk.where(pd.notnull(chunk), None)

        rows = [_build_insert_row(r, 'city', 'City_time_series.csv')
                for _, r in chunk.iterrows()]

        cursor.executemany(INSERT_SQL, rows)
        conn.commit()
        total += len(rows)
        if total % 10000 == 0:
            print(f"    ... {total}행")

    conn.close()
    print(f"  [OK] City 시계열 적재 완료: {total}행")


if __name__ == '__main__':
    # 순서 중요: Crosswalk 먼저 -> 시계열 로딩 시 필터에 활용
    load_crosswalk_county()
    load_crosswalk_cities()
    load_state_timeseries()
    load_metro_timeseries()
    load_city_timeseries()
    print("\n[DONE] STEP 3 완료: Zillow Economics 시계열 적재")
