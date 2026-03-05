"""
STEP 2: zillow_Housing 수급 지표 5개 파일 → us_metro_demand 통합 적재
실행: python src/subtopic2/s2_step2_load_zillow_demand.py

파일 → 컬럼 매핑:
  Metro_invt_fs_...csv              → inventory        (2018~2025)
  Metro_market_temp_index_...csv    → market_temp_index (2018~2025)
  Metro_mean_doz_pending_...csv     → mean_days_pending (2018~2025)
  Metro_sales_count_now_...csv      → sales_count       (2008~2025)
  Metro_new_homeowner_income_...csv → income_needed     (2012~2025)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from s2_step0_config import (
    get_connection, DB_NAME, safe_val,
    S2_DATA_FILES, S2_TARGET_METROS,
)

FILES = {
    'inventory': {
        'key': 'INVENTORY',
        'desc': '매물 재고량 (건)',
    },
    'market_temp_index': {
        'key': 'MARKET_TEMP',
        'desc': '시장온도지수 (0~100)',
    },
    'mean_days_pending': {
        'key': 'DAYS_PENDING',
        'desc': '평균 대기일수',
    },
    'sales_count': {
        'key': 'SALES_COUNT',
        'desc': '월별 판매 건수',
    },
    'income_needed': {
        'key': 'INCOME_NEEDED',
        'desc': '주택구매 필요 연소득 (USD)',
    },
}


def wide_to_long(csv_path, value_col_name):
    """Wide CSV → Long DataFrame 변환 + 타겟 MSA 필터"""
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    id_cols = [c for c in id_cols if c in df.columns]
    date_cols = [c for c in df.columns if c not in id_cols]

    # 타겟 필터
    df_f = df[df['RegionName'].isin(S2_TARGET_METROS)].copy()

    if df_f.empty:
        # 부분 매칭 시도
        all_names = df['RegionName'].unique()
        for target in S2_TARGET_METROS:
            keyword = target.split(',')[0].strip().lower()
            matches = [n for n in all_names if keyword in str(n).lower()]
            if matches:
                print(f"   [INFO] '{target}' 미매칭 -> 후보: {matches[:3]}")
        return pd.DataFrame()

    df_long = df_f.melt(
        id_vars=id_cols, value_vars=date_cols,
        var_name='date_raw', value_name=value_col_name
    )
    df_long = df_long.dropna(subset=[value_col_name])
    df_long['year_month'] = df_long['date_raw'].str[:7]
    df_long.drop(columns=['date_raw'], inplace=True)

    return df_long


def load_all_demand_metrics():
    """5개 파일을 각각 Long 변환 → year_month + region_name 기준 MERGE → MySQL"""

    print("[S2 STEP2] Zillow Housing 수급 지표 5개 파일 로딩 시작\n")

    dfs = {}
    for col_name, info in FILES.items():
        csv_path = S2_DATA_FILES[info['key']]
        print(f"  [{info['desc']}]: {os.path.basename(csv_path)}")

        df = wide_to_long(csv_path, col_name)
        if df.empty:
            print(f"     [WARN] 필터 결과 0행 - 스킵")
            continue

        print(f"     [OK] {len(df)}행 변환 완료")
        dfs[col_name] = df

    if not dfs:
        print("[ERROR] 로딩된 파일 없음")
        return

    # MERGE: year_month + RegionName 기준
    keys = ['RegionID', 'RegionName', 'year_month']
    merged = None

    for col_name, df in dfs.items():
        cols_keep = [c for c in keys if c in df.columns] + [col_name]
        if merged is None:
            extra = [c for c in ['SizeRank', 'RegionType', 'StateName'] if c in df.columns]
            df_slim = df[cols_keep + extra].copy()
            merged = df_slim
        else:
            df_slim = df[cols_keep].copy()
            merge_keys = [c for c in keys if c in merged.columns and c in df_slim.columns]
            merged = merged.merge(df_slim, on=merge_keys, how='outer')

    print(f"\n  [MERGE] {len(merged)}행 x {len(merged.columns)}열")

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE us_metro_demand")
    conn.commit()

    sql = """INSERT INTO us_metro_demand
             (region_id, size_rank, region_name, region_type, state_name, `year_month`,
              inventory, market_temp_index, mean_days_pending, sales_count, income_needed)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in merged.iterrows():
        rows.append((
            safe_val(int(r['RegionID'])) if pd.notna(r.get('RegionID')) else None,
            safe_val(int(r['SizeRank'])) if pd.notna(r.get('SizeRank')) else None,
            r['RegionName'],
            safe_val(r.get('RegionType')),
            safe_val(r.get('StateName')),
            r['year_month'],
            safe_val(float(r['inventory'])) if pd.notna(r.get('inventory')) else None,
            safe_val(float(r['market_temp_index'])) if pd.notna(r.get('market_temp_index')) else None,
            safe_val(float(r['mean_days_pending'])) if pd.notna(r.get('mean_days_pending')) else None,
            safe_val(int(r['sales_count'])) if pd.notna(r.get('sales_count')) else None,
            safe_val(float(r['income_needed'])) if pd.notna(r.get('income_needed')) else None,
        ))

    batch = 5000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
        print(f"   ... {min(i+batch, len(rows))}/{len(rows)} 삽입")

    conn.close()
    print(f"\n[OK] us_metro_demand 적재 완료: {len(rows)}행")

    # 적재 확인
    conn = get_connection(DB_NAME, for_pandas=True)
    df_check = pd.read_sql("""
        SELECT region_name,
               COUNT(*) as months,
               MIN(`year_month`) as from_ym,
               MAX(`year_month`) as to_ym,
               SUM(CASE WHEN inventory IS NOT NULL THEN 1 ELSE 0 END) as inv_cnt,
               SUM(CASE WHEN market_temp_index IS NOT NULL THEN 1 ELSE 0 END) as mti_cnt,
               SUM(CASE WHEN sales_count IS NOT NULL THEN 1 ELSE 0 END) as sales_cnt,
               SUM(CASE WHEN income_needed IS NOT NULL THEN 1 ELSE 0 END) as income_cnt
        FROM us_metro_demand
        GROUP BY region_name
    """, conn)
    conn.close()
    print("\n[CHECK] 적재 현황:")
    print(df_check.to_string(index=False))


if __name__ == '__main__':
    load_all_demand_metrics()
    print("\n[DONE] S2 STEP 2 완료")
