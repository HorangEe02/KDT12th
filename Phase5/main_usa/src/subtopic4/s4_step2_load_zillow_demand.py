"""
STEP 2: Zillow Housing 수급지표 4개 + ZHVF 성장률 로딩
  - us_metro_demand: new_construction_sales, market_temp_index, income_needed, sales_count
  - us_metro_zhvf_growth: 예측 성장률
실행: python src/subtopic4/s4_step2_load_zillow_demand.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *

# ── 수급지표 파일 매핑 ──
DEMAND_FILES = [
    ('NEW_CON_SALES', 'new_construction_sales'),
    ('MARKET_TEMP', 'market_temp_index'),
    ('INCOME_NEEDED', 'income_needed'),
    ('SALES_COUNT', 'sales_count'),
]


def load_demand_indicator(csv_path, col_name):
    """Wide CSV → 타겟 MSA 필터 → Long → us_metro_demand INSERT"""
    df_long = load_zillow_wide_to_long(csv_path, col_name)
    if df_long.empty:
        return 0

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    # 기존 S4 데이터 삭제 (MSA 풀네임 기준)
    msa_names = TARGET_MSA_NAMES + ['United States']
    placeholders = ','.join(['%s'] * len(msa_names))
    cursor.execute(
        f"DELETE FROM us_metro_demand WHERE region_name IN ({placeholders}) AND `{col_name}` IS NOT NULL",
        tuple(msa_names)
    )
    conn.commit()

    sql = f"""INSERT INTO us_metro_demand
              (region_id, region_name, state_name, `year_month`, `{col_name}`)
              VALUES (%s, %s, %s, %s, %s)"""

    data = []
    for _, row in df_long.iterrows():
        data.append((
            safe_val(row.get('RegionID')),
            row['RegionName'],
            safe_val(row.get('StateName')),
            row['year_month'],
            safe_val(row[col_name]),
        ))

    batch = 5000
    for i in range(0, len(data), batch):
        cursor.executemany(sql, data[i:i + batch])
        conn.commit()

    conn.close()
    print(f"  [OK] {col_name}: {len(data)}행 → us_metro_demand")
    return len(data)


def load_zhvf_growth():
    """ZHVF 예측 성장률 → us_metro_zhvf_growth"""
    csv_path = S4_DATA_FILES['ZHVF_GROWTH']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] ZHVF 파일 없음: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)
    target_names = TARGET_MSA_NAMES + ['United States']
    df_f = df[df['RegionName'].isin(target_names)].copy()

    if df_f.empty:
        print("  [WARN] ZHVF 타겟 MSA 없음")
        return 0

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    date_cols = [c for c in df_f.columns if c not in id_cols]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    rows = 0

    for _, region_row in df_f.iterrows():
        base_date = safe_val(region_row.get('BaseDate'))
        for dc in date_cols:
            val = region_row[dc]
            if pd.notna(val):
                cursor.execute(
                    """INSERT INTO us_metro_zhvf_growth
                       (region_id, region_name, state_name, base_date, forecast_date, growth_rate)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        safe_val(region_row.get('RegionID')),
                        region_row['RegionName'],
                        safe_val(region_row.get('StateName')),
                        base_date, dc, val,
                    )
                )
                rows += 1

    conn.commit()
    conn.close()
    print(f"  [OK] ZHVF 성장률: {rows}행 → us_metro_zhvf_growth")
    return rows


def run():
    total = 0

    # 수급지표 4개
    for file_key, col_name in DEMAND_FILES:
        csv_path = S4_DATA_FILES[file_key]
        if not os.path.exists(csv_path):
            print(f"  [SKIP] {file_key} 파일 없음")
            continue
        cnt = load_demand_indicator(csv_path, col_name)
        total += cnt

    # ZHVF 성장률
    total += load_zhvf_growth()

    print(f"\n  총 적재: {total}행")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 2: Zillow Housing 수급지표 로딩")
    print("=" * 60)
    run()
    print("\n[DONE] STEP 2 완료")
