"""
STEP 5: Kaggle 미국 인구통계 → us_census_demographics + us_county_historical
실행: python src/subtopic2/s2_step5_load_us_demographics.py

데이터:
  U2-1: acs2015_county_data.csv, acs2017_county_data.csv
        컬럼: State, County, TotalPop, Men, Women, Hispanic, White, Black,
              Asian, Income, IncomePerCap, Poverty, Unemployment, Professional,
              Service, Construction, Production, Drive, Transit, Walk, MeanCommute

  U2-3: us_county_demographics.csv (zipcode 단위, 5901 컬럼)
        → county + state 기준 인구 집계
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from s2_step0_config import (
    get_connection, DB_NAME, safe_val,
    S2_DATA_FILES, TARGET_STATES_ALL, COUNTY_CITY_MAP,
)


def load_us_census():
    """U2-1: US Census Demographic Data (ACS 2015, 2017)"""

    files = [
        (S2_DATA_FILES['ACS2015'], 2015),
        (S2_DATA_FILES['ACS2017'], 2017),
    ]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE us_census_demographics")
    conn.commit()
    conn.close()

    for csv_path, census_year in files:
        if not os.path.exists(csv_path):
            print(f"  [WARN] 파일 없음: {csv_path}")
            continue

        print(f"\n[LOAD] U2-1: {os.path.basename(csv_path)} (year={census_year})")
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"   컬럼: {df.columns.tolist()[:15]}...")
        print(f"   크기: {df.shape}")

        # State 열 확인
        state_col = None
        for c in ['State', 'state', 'STATE']:
            if c in df.columns:
                state_col = c
                break

        if state_col is None:
            print("   [WARN] State 열 없음 - 스킵")
            continue

        # 4개 주 필터
        df = df[df[state_col].isin(TARGET_STATES_ALL)]
        if df.empty:
            print(f"   [WARN] 타겟 주 필터 결과 0행")
            continue

        print(f"   필터 후: {len(df)}행")

        # 열 매핑
        col_map = {
            'County': 'county', 'county': 'county', 'CountyName': 'county',
            'State': 'state', 'state': 'state',
            'TotalPop': 'total_population',
            'Men': 'men', 'Women': 'women',
            'Hispanic': 'hispanic', 'White': 'white', 'Black': 'black', 'Asian': 'asian',
            'Income': 'median_income', 'IncomePerCap': 'income_per_capita',
            'Poverty': 'poverty', 'Unemployment': 'unemployment',
            'Professional': 'professional', 'Service': 'service',
            'Construction': 'construction', 'Production': 'production',
            'Drive': 'drive', 'Transit': 'transit', 'Walk': 'walk',
            'MeanCommute': 'mean_commute',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        conn = get_connection(DB_NAME)
        cursor = conn.cursor()

        sql = """INSERT INTO us_census_demographics
                 (census_year, county, state, total_population, men, women,
                  hispanic, white, black, asian,
                  median_income, income_per_capita, poverty, unemployment,
                  professional, service, construction, production,
                  drive, transit, walk, mean_commute,
                  city_id, source_dataset)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in df.iterrows():
            county = str(r.get('county', ''))
            state = str(r.get('state', ''))
            city_id = COUNTY_CITY_MAP.get((county, state))

            rows.append((
                census_year, county, state,
                safe_val(int(r['total_population'])) if pd.notna(r.get('total_population')) else None,
                safe_val(int(r['men'])) if pd.notna(r.get('men')) else None,
                safe_val(int(r['women'])) if pd.notna(r.get('women')) else None,
                safe_val(r.get('hispanic')), safe_val(r.get('white')),
                safe_val(r.get('black')), safe_val(r.get('asian')),
                safe_val(r.get('median_income')), safe_val(r.get('income_per_capita')),
                safe_val(r.get('poverty')), safe_val(r.get('unemployment')),
                safe_val(r.get('professional')), safe_val(r.get('service')),
                safe_val(r.get('construction')), safe_val(r.get('production')),
                safe_val(r.get('drive')), safe_val(r.get('transit')),
                safe_val(r.get('walk')), safe_val(r.get('mean_commute')),
                city_id,
                f'U2-1 ACS {census_year}',
            ))

        batch = 2000
        for i in range(0, len(rows), batch):
            cursor.executemany(sql, rows[i:i+batch])
            conn.commit()

        conn.close()
        print(f"   [OK] us_census_demographics 적재: {len(rows)}행 (ACS {census_year})")


def load_us_county_historical():
    """U2-3: US County & Zipcode Historical Demographics
    실제 데이터: zipcode 단위, 5901 컬럼 → county+state 기준 인구 집계
    """
    csv_path = S2_DATA_FILES['US_COUNTY_DEMO']

    if not os.path.exists(csv_path):
        print(f"\n  [WARN] U2-3 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] U2-3: {os.path.basename(csv_path)}")

    # 메모리 절약: 필요한 컬럼만 로드
    # 실제 컬럼: zipcode_type, major_city, county, state, population_census_2010,
    #           population_estimate_2010~2019, lat, lng, county_fips, state_name ...
    df_sample = pd.read_csv(csv_path, nrows=2)
    all_cols = df_sample.columns.tolist()

    # 인구 관련 컬럼 찾기 (실제 인구 수치만, 코드/유형 제외)
    pop_cols = [c for c in all_cols
                if ('population_census' in c.lower()
                    or 'population_estimate' in c.lower())
                and 'code' not in c.lower()
                and 'typology' not in c.lower()]
    base_cols = ['county', 'state', 'state_name', 'county_fips', 'major_city']
    use_cols = [c for c in base_cols + pop_cols if c in all_cols]

    print(f"   전체 컬럼: {len(all_cols)}, 사용 컬럼: {len(use_cols)}")
    print(f"   인구 컬럼: {pop_cols[:10]}")

    if not pop_cols:
        print("   [WARN] 인구 컬럼 없음 - 스킵")
        return

    df = pd.read_csv(csv_path, usecols=use_cols, low_memory=False)
    print(f"   로드 크기: {df.shape}")

    # state 필터
    state_col = 'state_name' if 'state_name' in df.columns else 'state'
    df = df[df[state_col].isin(TARGET_STATES_ALL)]
    print(f"   필터 후: {len(df)}행")

    if df.empty:
        return

    # county + state 기준 인구 집계 (연도별 인구 컬럼을 Long 변환)
    id_cols = [c for c in ['county', state_col, 'county_fips'] if c in df.columns]

    # census_2010, estimate_2010~2019 패턴 파악
    year_pop_map = {}
    for c in pop_cols:
        cl = c.lower()
        for yr in range(2000, 2025):
            if str(yr) in cl:
                year_pop_map[c] = yr
                break

    if not year_pop_map:
        print("   [WARN] 연도별 인구 매핑 실패")
        return

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE us_county_historical")
    conn.commit()

    sql = """INSERT INTO us_county_historical
             (year, county_fips, county_name, state, total_population, city_id, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s)"""

    total_rows = 0
    for pop_col, year in sorted(year_pop_map.items(), key=lambda x: x[1]):
        grp = df.groupby(id_cols).agg({pop_col: 'sum'}).reset_index()
        grp = grp[grp[pop_col] > 0]

        rows = []
        for _, r in grp.iterrows():
            county_name = str(r.get('county', ''))
            state_val = str(r.get(state_col, ''))
            fips = safe_val(r.get('county_fips'))
            city_id = COUNTY_CITY_MAP.get((county_name, state_val))

            rows.append((
                year,
                str(fips) if fips else None,
                county_name,
                state_val,
                safe_val(int(r[pop_col])) if pd.notna(r[pop_col]) else None,
                city_id,
                'U2-3 County Historical',
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total_rows += len(rows)

    conn.close()
    print(f"   [OK] us_county_historical 적재: {total_rows}행")


def load_us_population_timeseries():
    """U2-2: Population Time Series Data (전국 인구)"""
    csv_path = S2_DATA_FILES['POP_TIMESERIES']

    if not os.path.exists(csv_path):
        print(f"\n  [WARN] U2-2 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] U2-2: {os.path.basename(csv_path)}")

    df = pd.read_csv(csv_path)
    print(f"   컬럼: {df.columns.tolist()}")
    print(f"   크기: {df.shape}")

    # 컬럼: realtime_start, value, date, realtime_end
    # 전국 인구 시계열 (thousands)
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE us_population_timeseries")
    conn.commit()

    sql = """INSERT INTO us_population_timeseries
             (date, region_name, region_type, population, source_dataset)
             VALUES (%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        date_val = r.get('date')
        pop_val = r.get('value')
        if pd.notna(pop_val) and str(pop_val) != '.':
            try:
                pop = int(float(pop_val) * 1000)  # thousands → actual
            except (ValueError, TypeError):
                continue
            rows.append((
                str(date_val),
                'United States',
                'national',
                pop,
                'U2-2 Population Time Series',
            ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   [OK] us_population_timeseries 적재: {len(rows)}행")


if __name__ == '__main__':
    load_us_census()
    load_us_county_historical()
    load_us_population_timeseries()
    print("\n[DONE] S2 STEP 5 완료")
