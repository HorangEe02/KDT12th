"""
STEP 2: Zillow 부동산 수급 데이터 로딩
- 5개 수급 지표 → us_metro_demand
- ZHVI → us_metro_zhvi
- ZORI → us_metro_zori
- ZHVF Growth → us_metro_zhvf_growth
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def load_demand_indicator(csv_path, col_name):
    """Wide CSV → 4개 MSA 필터 → Long → us_metro_demand 적재"""
    if not os.path.exists(csv_path):
        print(f"  [SKIP] 파일 없음: {csv_path}")
        return 0
    df_long = load_zillow_wide_to_long(csv_path)
    if df_long.empty:
        return 0

    conn = get_connection(DB_NAME)
    sql = f"""INSERT INTO us_metro_demand
              (region_id, region_name, state_name, `year_month`, `{col_name}`)
              VALUES (%s, %s, %s, %s, %s)"""
    data = [
        (safe_val(row.get('RegionID')), row['RegionName'],
         safe_val(row.get('StateName')), row['year_month'], safe_val(row['value']))
        for _, row in df_long.iterrows()
    ]
    total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] {col_name}: {total:,}행 → us_metro_demand")
    return total


def load_zhvi():
    """ZHVI → us_metro_zhvi"""
    csv_path = S4_DATA_FILES['ZHVI']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] ZHVI 파일 없음")
        return 0
    df_long = load_zillow_wide_to_long(csv_path)
    if df_long.empty:
        return 0

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO us_metro_zhvi
             (region_id, region_name, state_name, `year_month`, zhvi)
             VALUES (%s, %s, %s, %s, %s)"""
    data = [
        (safe_val(row.get('RegionID')), row['RegionName'],
         safe_val(row.get('StateName')), row['year_month'], safe_val(row['value']))
        for _, row in df_long.iterrows()
    ]
    total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] ZHVI: {total:,}행 → us_metro_zhvi")
    return total


def load_zori():
    """ZORI → us_metro_zori"""
    csv_path = S4_DATA_FILES['ZORI']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] ZORI 파일 없음")
        return 0
    df_long = load_zillow_wide_to_long(csv_path)
    if df_long.empty:
        return 0

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO us_metro_zori
             (region_id, region_name, state_name, `year_month`, zori)
             VALUES (%s, %s, %s, %s, %s)"""
    data = [
        (safe_val(row.get('RegionID')), row['RegionName'],
         safe_val(row.get('StateName')), row['year_month'], safe_val(row['value']))
        for _, row in df_long.iterrows()
    ]
    total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] ZORI: {total:,}행 → us_metro_zori")
    return total


def load_zhvf_growth():
    """ZHVF 성장률 → us_metro_zhvf_growth"""
    csv_path = S4_DATA_FILES['ZHVF_GROWTH']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] ZHVF Growth 파일 없음")
        return 0
    df = pd.read_csv(csv_path)
    filter_names = TARGET_METROS + ['United States']
    df_f = df[df['RegionName'].isin(filter_names)].copy()
    if df_f.empty:
        print("  [WARN] ZHVF 타겟 MSA 없음")
        return 0

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    date_cols = [c for c in df_f.columns if c not in id_cols]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    rows = 0
    data = []
    for _, rr in df_f.iterrows():
        for dc in date_cols:
            val = rr[dc]
            if pd.notna(val):
                data.append((
                    safe_val(rr.get('RegionID')), rr['RegionName'],
                    safe_val(rr.get('StateName')),
                    safe_val(rr.get('BaseDate')), dc, float(val)
                ))
    sql = """INSERT INTO us_metro_zhvf_growth
             (region_id, region_name, state_name, base_date, forecast_date, growth_rate)
             VALUES (%s,%s,%s,%s,%s,%s)"""
    rows = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] ZHVF Growth: {rows:,}행")
    return rows


def run():
    print("=" * 60)
    print("STEP 2: Zillow 부동산 데이터 로딩")
    print("=" * 60)

    # 수급 지표
    demand_files = [
        ('NEW_CON_SALES', 'new_construction_sales'),
        ('INCOME_NEEDED', 'income_needed'),
        ('MARKET_TEMP', 'market_temp_index'),
        ('SALES_COUNT', 'sales_count'),
        ('INVENTORY', 'inventory_count'),
    ]
    for key, col in demand_files:
        load_demand_indicator(S4_DATA_FILES[key], col)

    # ZHVI / ZORI (v2)
    load_zhvi()
    load_zori()

    # ZHVF Growth
    load_zhvf_growth()

    print("\n  STEP 2 완료!")


if __name__ == '__main__':
    run()
