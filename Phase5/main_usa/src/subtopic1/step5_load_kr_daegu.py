"""
STEP 5: Kaggle 대구 주택 데이터 -> daegu_housing_prices + daegu_monthly_summary
실행: python src/subtopic1/step5_load_kr_daegu.py

처리 파일:
  - K1-1: Daegu_apt.csv (대구 아파트 실거래가)
    열: county_or_gu, sub_locality, building_name, exclusive_area_m2,
        transaction_price_krw_10k, construction_year, contract_year_month, contract_day, floor
  - K1-3: Apart Deal.csv (전국 아파트 거래 - 대구 필터)
    열: 지역코드, 법정동, 거래일, 아파트, 지번, 전용면적, 층, 건축년도, 거래금액
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import pymysql
from step0_init_db import get_connection, DB_NAME, DATA_FILES, safe_val

# 대구 지역코드 앞 2자리 (행정구역코드)
DAEGU_REGION_CODES = [27]  # 대구광역시 = 27xxx


def load_daegu_apt():
    """K1-1: Daegu_apt.csv -> daegu_housing_prices"""
    csv_path = DATA_FILES['DAEGU_APT']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] 대구 아파트 실거래가: {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  원본: {len(df)}행")
    print(f"  열: {df.columns.tolist()}")

    # year_month 생성: contract_year_month -> YYYY-MM
    df['contract_year_month'] = df['contract_year_month'].astype(str)
    df['year_month'] = df['contract_year_month'].str[:4] + '-' + df['contract_year_month'].str[4:6]

    # deal_date 생성
    df['deal_date'] = pd.to_datetime(
        df['contract_year_month'].str[:4] + '-' +
        df['contract_year_month'].str[4:6] + '-' +
        df['contract_day'].astype(str).str.zfill(2),
        errors='coerce'
    )

    df = df.where(pd.notnull(df), None)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO daegu_housing_prices
             (`year_month`, district, dong, apt_name, exclusive_area,
              deal_amount, floor, build_year, deal_date, deal_type, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_val(r.get('year_month')),
            safe_val(r.get('county_or_gu')),
            safe_val(r.get('sub_locality')),
            safe_val(r.get('building_name')),
            safe_val(r.get('exclusive_area_m2')),
            int(r['transaction_price_krw_10k']) if pd.notna(r.get('transaction_price_krw_10k')) else None,
            int(r['floor']) if pd.notna(r.get('floor')) else None,
            int(r['construction_year']) if pd.notna(r.get('construction_year')) else None,
            str(r['deal_date'])[:10] if pd.notna(r.get('deal_date')) else None,
            safe_val(r.get('transaction_type')),
            'K1-1 Daegu Apt Transaction',
        ))

    batch = 5000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()
        print(f"    ... {min(i+batch, len(rows))}/{len(rows)}")

    conn.close()
    print(f"  [OK] daegu_housing_prices 적재: {len(rows)}행 (K1-1)")


def load_apart_deal_daegu():
    """K1-3: Apart Deal.csv -> daegu_housing_prices (대구 필터)
    열: 지역코드, 법정동, 거래일, 아파트, 지번, 전용면적, 층, 건축년도, 거래금액"""
    csv_path = DATA_FILES['APART_DEAL']
    if not os.path.exists(csv_path):
        print(f"  [WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] 전국 아파트 거래 (대구 필터): {csv_path}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO daegu_housing_prices
             (`year_month`, district, dong, apt_name, exclusive_area,
              deal_amount, floor, build_year, deal_date, deal_type, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        # 대구 필터: 지역코드 앞 2자리 = 27 (대구광역시)
        chunk['지역코드'] = pd.to_numeric(chunk['지역코드'], errors='coerce')
        chunk = chunk[chunk['지역코드'].notna()]
        chunk = chunk[chunk['지역코드'].astype(int).astype(str).str[:2].astype(int).isin(DAEGU_REGION_CODES)]
        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        # 거래일 파싱 (형식: 'M/DD/YYYY 0:00' 또는 다양)
        chunk['parsed_date'] = pd.to_datetime(chunk['거래일'], errors='coerce')
        chunk['year_month'] = chunk['parsed_date'].dt.strftime('%Y-%m')

        # 거래금액 정리
        chunk['거래금액_clean'] = pd.to_numeric(
            chunk['거래금액'].astype(str).str.replace(',', '').str.strip(),
            errors='coerce'
        )

        rows = []
        for _, r in chunk.iterrows():
            rows.append((
                safe_val(r.get('year_month')),
                None,  # district - 지역코드에서 구 정보 추출이 복잡하여 None
                safe_val(r.get('법정동')),
                safe_val(r.get('아파트')),
                safe_val(r.get('전용면적')),
                int(r['거래금액_clean']) if pd.notna(r.get('거래금액_clean')) else None,
                int(r['층']) if pd.notna(r.get('층')) else None,
                int(r['건축년도']) if pd.notna(r.get('건축년도')) else None,
                str(r['parsed_date'])[:10] if pd.notna(r.get('parsed_date')) else None,
                None,
                'K1-3 Korean Apt Deal (대구 필터)',
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        print(f"    ... 대구 {total}행 적재")

    conn.close()
    print(f"  [OK] daegu_housing_prices 적재: {total}행 (K1-3 대구)")


def build_daegu_monthly_summary():
    """daegu_housing_prices -> daegu_monthly_summary 집계"""
    print("\n[ANALYSIS] 대구 월별 요약 집계")

    conn_pd = get_connection(DB_NAME, for_pandas=True)

    df = pd.read_sql("""
        SELECT `year_month`, district, deal_amount, exclusive_area
        FROM daegu_housing_prices
        WHERE deal_amount IS NOT NULL AND deal_amount > 0
          AND `year_month` IS NOT NULL
    """, conn_pd)
    conn_pd.close()

    if df.empty:
        print("  [WARN] 집계 대상 0행")
        return

    df['deal_amount'] = pd.to_numeric(df['deal_amount'], errors='coerce')
    df['exclusive_area'] = pd.to_numeric(df['exclusive_area'], errors='coerce')

    df['price_per_m2'] = np.where(
        df['exclusive_area'].notna() & (df['exclusive_area'] > 0),
        df['deal_amount'] / df['exclusive_area'],
        None
    )

    grouped = df.groupby(['year_month', 'district']).agg(
        avg_price=('deal_amount', 'mean'),
        median_price=('deal_amount', 'median'),
        min_price=('deal_amount', 'min'),
        max_price=('deal_amount', 'max'),
        transaction_count=('deal_amount', 'count'),
        avg_area=('exclusive_area', 'mean'),
        avg_price_per_m2=('price_per_m2', 'mean'),
    ).reset_index()

    # YoY 변동률
    grouped['year'] = grouped['year_month'].str[:4].astype(int)
    grouped['month'] = grouped['year_month'].str[5:7].astype(int)
    grouped = grouped.sort_values(['district', 'year_month'])

    grouped['prev_ym'] = (grouped['year'] - 1).astype(str) + '-' + grouped['month'].astype(str).str.zfill(2)
    prev_map = grouped.set_index(['district', 'year_month'])['avg_price'].to_dict()
    grouped['prev_price'] = grouped.apply(
        lambda r: prev_map.get((r['district'], r['prev_ym'])), axis=1
    )
    grouped['yoy_change_rate'] = np.where(
        grouped['prev_price'].notna() & (grouped['prev_price'] > 0),
        (grouped['avg_price'] - grouped['prev_price']) / grouped['prev_price'],
        None
    )

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    sql = """INSERT INTO daegu_monthly_summary
             (`year_month`, district, avg_price, median_price, min_price, max_price,
              transaction_count, avg_area, avg_price_per_m2, yoy_change_rate)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in grouped.iterrows():
        rows.append((
            safe_val(r['year_month']), safe_val(r['district']),
            int(r['avg_price']), int(r['median_price']),
            int(r['min_price']), int(r['max_price']),
            int(r['transaction_count']),
            round(r['avg_area'], 2) if pd.notna(r['avg_area']) else None,
            round(float(r['avg_price_per_m2']), 2) if pd.notna(r['avg_price_per_m2']) else None,
            round(float(r['yoy_change_rate']), 4) if pd.notna(r['yoy_change_rate']) else None,
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"  [OK] daegu_monthly_summary 집계 완료: {len(rows)}행")


if __name__ == '__main__':
    load_daegu_apt()
    load_apart_deal_daegu()
    build_daegu_monthly_summary()
    print("\n[DONE] STEP 5 완료: 대구 데이터 적재 + 월별 요약")
