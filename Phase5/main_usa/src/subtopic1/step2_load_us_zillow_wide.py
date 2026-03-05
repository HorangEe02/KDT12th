"""
STEP 2: zillow_Housing Wide Format CSV -> Long 변환 -> MySQL 적재
실행: python src/subtopic1/step2_load_us_zillow_wide.py

처리 파일:
  - Metro_zhvi_...csv  -> us_metro_zhvi
  - Metro_zori_...csv  -> us_metro_zori
  - Metro_zhvf_growth_...csv -> us_metro_zhvf_growth
  - National_zorf_growth_...csv -> us_national_zorf_growth
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import pymysql
from step0_init_db import get_connection, DB_NAME, DATA_FILES, TARGET_METROS


def check_and_fix_metro_names(csv_path):
    """CSV에서 실제 RegionName을 읽어 TARGET_METROS와 매칭 확인"""
    df_full = pd.read_csv(csv_path, usecols=['RegionName'])
    all_names = df_full['RegionName'].unique().tolist()

    matched = [m for m in TARGET_METROS if m in all_names]
    unmatched = [m for m in TARGET_METROS if m not in all_names]

    if unmatched:
        print(f"  [WARN] 매칭 실패: {unmatched}")
        for um in unmatched:
            keyword = um.split(',')[0].split('-')[0].strip()
            candidates = [n for n in all_names if keyword.lower() in str(n).lower()]
            print(f"    '{um}' 후보: {candidates[:5]}")
    else:
        print(f"  [OK] 전체 매칭 성공: {matched}")

    return matched, unmatched


def load_zhvi():
    """ZHVI Wide -> us_metro_zhvi Long"""
    csv_path = DATA_FILES['ZHVI_WIDE']
    print(f"\n[LOAD] ZHVI: {csv_path}")

    df = pd.read_csv(csv_path)

    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()
    print(f"  필터 결과: {len(df_f)}개 MSA")

    if df_f.empty:
        print("  [WARN] 필터 결과 0행 - TARGET_METROS 이름 확인 필요")
        check_and_fix_metro_names(csv_path)
        return

    df_long = df_f.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name='date_raw',
        value_name='zhvi'
    )
    df_long = df_long.dropna(subset=['zhvi'])
    df_long['year_month'] = df_long['date_raw'].str[:7]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO us_metro_zhvi
             (region_id, size_rank, region_name, region_type, state_name, `year_month`, zhvi)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r['RegionID']) else None,
            int(r['SizeRank']) if pd.notna(r['SizeRank']) else None,
            r['RegionName'],
            r.get('RegionType'),
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r['year_month'],
            float(r['zhvi'])
        ))

    batch_size = 5000
    for i in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[i:i+batch_size])
        conn.commit()
        print(f"    ... {min(i+batch_size, len(rows))}/{len(rows)} 삽입")

    conn.close()
    print(f"  [OK] us_metro_zhvi 적재 완료: {len(rows)}행")


def load_zori():
    """ZORI Wide -> us_metro_zori Long"""
    csv_path = DATA_FILES['ZORI_WIDE']
    print(f"\n[LOAD] ZORI: {csv_path}")

    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName']
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()
    print(f"  필터 결과: {len(df_f)}개 MSA")

    if df_f.empty:
        check_and_fix_metro_names(csv_path)
        return

    df_long = df_f.melt(id_vars=id_cols, value_vars=date_cols,
                         var_name='date_raw', value_name='zori')
    df_long = df_long.dropna(subset=['zori'])
    df_long['year_month'] = df_long['date_raw'].str[:7]

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO us_metro_zori
             (region_id, size_rank, region_name, region_type, state_name, `year_month`, zori)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r['RegionID']) else None,
            int(r['SizeRank']) if pd.notna(r['SizeRank']) else None,
            r['RegionName'], r.get('RegionType'),
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r['year_month'], float(r['zori'])
        ))

    batch_size = 5000
    for i in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[i:i+batch_size])
        conn.commit()
    conn.close()
    print(f"  [OK] us_metro_zori 적재 완료: {len(rows)}행")


def load_zhvf_growth():
    """ZHVF Growth Wide -> us_metro_zhvf_growth Long"""
    csv_path = DATA_FILES['ZHVF_GROWTH']
    print(f"\n[LOAD] ZHVF Growth: {csv_path}")

    df = pd.read_csv(csv_path)
    id_cols = ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
    date_cols = [c for c in df.columns if c not in id_cols]

    df_f = df[df['RegionName'].isin(TARGET_METROS)].copy()

    if df_f.empty:
        print("  [WARN] 필터 결과 0행")
        return

    df_long = df_f.melt(id_vars=id_cols, value_vars=date_cols,
                         var_name='forecast_date', value_name='growth_rate')
    df_long = df_long.dropna(subset=['growth_rate'])

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO us_metro_zhvf_growth
             (region_id, region_name, region_type, state_name, base_date, forecast_date, growth_rate)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r['RegionID']) else None,
            r['RegionName'], r.get('RegionType'),
            r.get('StateName') if pd.notna(r.get('StateName')) else None,
            r.get('BaseDate'), r['forecast_date'], float(r['growth_rate'])
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"  [OK] us_metro_zhvf_growth 적재 완료: {len(rows)}행")


def load_zorf_growth():
    """National ZORF Growth -> us_national_zorf_growth"""
    csv_path = DATA_FILES['ZORF_GROWTH']
    print(f"\n[LOAD] National ZORF Growth: {csv_path}")

    df = pd.read_csv(csv_path)
    id_cols = [c for c in ['RegionID', 'SizeRank', 'RegionName', 'RegionType', 'StateName', 'BaseDate']
               if c in df.columns]
    date_cols = [c for c in df.columns if c not in id_cols]

    df_long = df.melt(id_vars=id_cols, value_vars=date_cols,
                       var_name='forecast_date', value_name='growth_rate')
    df_long = df_long.dropna(subset=['growth_rate'])

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO us_national_zorf_growth
             (region_id, region_name, base_date, forecast_date, growth_rate)
             VALUES (%s, %s, %s, %s, %s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            int(r['RegionID']) if pd.notna(r.get('RegionID')) else None,
            r.get('RegionName', 'United States'),
            r.get('BaseDate'), r['forecast_date'], float(r['growth_rate'])
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"  [OK] us_national_zorf_growth 적재 완료: {len(rows)}행")


if __name__ == '__main__':
    load_zhvi()
    load_zori()
    load_zhvf_growth()
    load_zorf_growth()
    print("\n[DONE] STEP 2 완료: Zillow Housing Wide -> Long 적재")
