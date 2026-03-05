"""
STEP 3: Zillow Economics Long Format에서 수급 관련 지표 추출 → zillow_demand_timeseries
실행: python src/subtopic2/s2_step3_load_zillow_economics_demand.py

대상: Metro_time_series.csv (RegionName = numeric ID), State_time_series.csv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from s2_step0_config import (
    get_connection, DB_NAME, safe_val,
    S2_DATA_FILES, TARGET_STATES_FULL,
)

# 수급 관련 열
DEMAND_COLS_PATTERNS = [
    'InventorySeasonallyAdjusted', 'InventoryRaw',
    'DaysOnZillow_AllHomes',
    'Sale_Counts', 'Sale_Counts_Seas_Adj',
    'PctOfHomesSellingForGain_AllHomes',
    'PctOfHomesSellingForLoss_AllHomes',
    'PctOfListingsWithPriceReductions_AllHomes',
    'PctOfListingsWithPriceReductionsSeasAdj_AllHomes',
    'AgeOfInventory',
]


def get_target_metro_ids():
    """소주제1 zillow_county_crosswalk에서 타겟 MSA의 CBSACode 조회
    Metro_time_series.csv의 RegionName은 CBSA Code (예: 19100, 12060)"""
    try:
        conn = get_connection(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT CBSACode AS code
            FROM zillow_county_crosswalk
            WHERE MetroName_Zillow LIKE '%Dallas%'
               OR MetroName_Zillow LIKE '%Atlanta%'
               OR MetroName_Zillow LIKE '%Phoenix%'
               OR MetroName_Zillow LIKE '%Charlotte%'
        """)
        codes = [r['code'] for r in cursor.fetchall() if r['code']]
        conn.close()
        return codes
    except Exception as e:
        print(f"  [WARN] Crosswalk 조회 실패: {e}")
        return []


def load_demand_timeseries(csv_path, region_level, target_regions=None):
    """Long Format 시계열에서 수급 지표만 추출 적재"""

    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] 수급 시계열: {os.path.basename(csv_path)} (level={region_level})")

    # 사용 가능한 열 확인
    df_sample = pd.read_csv(csv_path, nrows=5)
    base_cols = ['Date', 'RegionName']
    avail_demand = [c for c in df_sample.columns
                    if any(p in c for p in DEMAND_COLS_PATTERNS)]
    usecols = [c for c in base_cols + avail_demand if c in df_sample.columns]
    print(f"   사용 열: {len(avail_demand)}개 수급 지표")

    if not avail_demand:
        print("   [WARN] 수급 관련 열 없음 - 스킵")
        return

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(csv_path, usecols=usecols, chunksize=10000):
        if target_regions:
            chunk = chunk[chunk['RegionName'].astype(str).isin([str(x) for x in target_regions])]
        if chunk.empty:
            continue

        sql = """INSERT INTO zillow_demand_timeseries
                 (date, region_name, region_level,
                  inventory_sa, inventory_raw, days_on_zillow,
                  sale_counts, sale_counts_sa,
                  pct_selling_for_gain, pct_selling_for_loss,
                  pct_price_reduction, pct_price_reduction_sa,
                  age_of_inventory, source_file)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            def get_col(patterns):
                for p in (patterns if isinstance(patterns, list) else [patterns]):
                    for c in chunk.columns:
                        if p in c:
                            v = r.get(c)
                            return safe_val(v) if pd.notna(v) else None
                return None

            rows.append((
                safe_val(r.get('Date')),
                str(r['RegionName']),
                region_level,
                get_col(['InventorySeasonallyAdjusted']),
                get_col(['InventoryRaw']),
                get_col(['DaysOnZillow_AllHomes']),
                get_col(['Sale_Counts_Seas_Adj']),  # SA first
                get_col(['Sale_Counts']),
                get_col(['PctOfHomesSellingForGain']),
                get_col(['PctOfHomesSellingForLoss']),
                get_col(['PctOfListingsWithPriceReductions_AllHomes']),
                get_col(['PctOfListingsWithPriceReductionsSeasAdj']),
                get_col(['AgeOfInventory']),
                os.path.basename(csv_path),
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        if total % 30000 == 0:
            print(f"   ... {total}행")

    conn.close()
    print(f"   [OK] {region_level} 수급 시계열 적재: {total}행")


def load_all():
    # TRUNCATE
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE zillow_demand_timeseries")
    conn.commit()
    conn.close()

    # State (4개 주)
    load_demand_timeseries(
        S2_DATA_FILES['STATE_TS'],
        region_level='state',
        target_regions=TARGET_STATES_FULL
    )

    # Metro (MSA ID 기반)
    metro_ids = get_target_metro_ids()
    print(f"\n  [INFO] 타겟 Metro IDs: {metro_ids[:10]}")
    load_demand_timeseries(
        S2_DATA_FILES['METRO_TS'],
        region_level='metro',
        target_regions=metro_ids if metro_ids else None
    )


if __name__ == '__main__':
    load_all()
    print("\n[DONE] S2 STEP 3 완료")
