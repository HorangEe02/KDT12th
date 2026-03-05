"""
STEP 4: realtor-data.zip.csv -> us_realtor_listings + us_monthly_summary
실행: python src/subtopic1/step4_load_us_realtor.py

원본: 178MB / 220만행 - 4개 주(Texas, Georgia, Arizona, North Carolina) 필터 적용
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import pymysql
from step0_init_db import get_connection, DB_NAME, DATA_FILES, safe_val

REALTOR_PATH = DATA_FILES['REALTOR']

# state 열은 풀네임 형식 ('Texas', 'Georgia' 등)
TARGET_STATES = {'Texas', 'Georgia', 'Arizona', 'North Carolina'}

# city_id 매핑 (cities 테이블 기준 - step1에서 삽입 순서)
# 1=대구, 2=Dallas, 3=Atlanta, 4=Phoenix, 5=Charlotte
CITY_ID_MAP = {
    ('Texas', 'dallas'): 2,
    ('Georgia', 'atlanta'): 3,
    ('Arizona', 'phoenix'): 4,
    ('North Carolina', 'charlotte'): 5,
}


def resolve_city_id(state, city):
    """state + city로 city_id 매핑"""
    if not city or not state:
        return None
    city_lower = str(city).lower().strip()
    state_str = str(state).strip()
    for (st, kw), cid in CITY_ID_MAP.items():
        if state_str == st and kw in city_lower:
            return cid
    return None


def load_realtor_listings():
    """개별 매물 적재 (4개 주 필터)"""
    print(f"\n[LOAD] Realtor.com 매물: {REALTOR_PATH}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    for chunk in pd.read_csv(REALTOR_PATH, chunksize=10000, low_memory=False):
        chunk = chunk[chunk['state'].isin(TARGET_STATES)]
        if chunk.empty:
            continue

        chunk = chunk.where(pd.notnull(chunk), None)

        sql = """INSERT INTO us_realtor_listings
                 (city_id, brokered_by, status, price, bed, bath,
                  acre_lot, street, city, state, zip_code, house_size, prev_sold_date)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        rows = []
        for _, r in chunk.iterrows():
            cid = resolve_city_id(r.get('state'), r.get('city'))
            rows.append((
                cid,
                safe_val(r.get('brokered_by')),
                safe_val(r.get('status')),
                safe_val(r.get('price')),
                int(r['bed']) if pd.notna(r.get('bed')) else None,
                int(r['bath']) if pd.notna(r.get('bath')) else None,
                safe_val(r.get('acre_lot')),
                safe_val(r.get('street')),
                safe_val(r.get('city')),
                safe_val(r.get('state')),
                str(int(r['zip_code'])) if pd.notna(r.get('zip_code')) else None,
                safe_val(r.get('house_size')),
                safe_val(r.get('prev_sold_date')),
            ))

        cursor.executemany(sql, rows)
        conn.commit()
        total += len(rows)
        if total % 50000 == 0:
            print(f"    ... {total}행 삽입")

    conn.close()
    print(f"  [OK] us_realtor_listings 적재 완료: {total}행")


def build_us_monthly_summary():
    """us_realtor_listings -> us_monthly_summary (Python pandas 기반 집계)"""
    print("\n[ANALYSIS] US 월별 요약 집계 생성")

    conn = get_connection(DB_NAME)

    # prev_sold_date 샘플 확인
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prev_sold_date
        FROM us_realtor_listings
        WHERE prev_sold_date IS NOT NULL
        LIMIT 5
    """)
    samples = cursor.fetchall()
    print(f"  prev_sold_date 샘플: {samples}")
    conn.close()

    conn_pd = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql("""
        SELECT city_id, city, state, prev_sold_date, price, house_size, bed, bath
        FROM us_realtor_listings
        WHERE city_id IS NOT NULL AND price IS NOT NULL AND price > 0
          AND prev_sold_date IS NOT NULL
    """, conn_pd)
    conn_pd.close()

    if df.empty:
        print("  [WARN] 집계 대상 0행 - prev_sold_date 미존재 가능")
        return

    df['year_month'] = df['prev_sold_date'].str[:7]

    grouped = df.groupby(['city_id', 'city', 'state', 'year_month']).agg(
        avg_price=('price', 'mean'),
        median_price=('price', 'median'),
        listing_count=('price', 'count'),
        avg_house_size=('house_size', 'mean'),
        avg_bed=('bed', 'mean'),
        avg_bath=('bath', 'mean'),
    ).reset_index()

    grouped['avg_price_per_sqft'] = np.where(
        grouped['avg_house_size'] > 0,
        grouped['avg_price'] / grouped['avg_house_size'],
        None
    )

    conn = get_connection(DB_NAME)
    cursor2 = conn.cursor()
    sql = """INSERT INTO us_monthly_summary
             (city_id, city_name, state, `year_month`,
              avg_price, median_price, listing_count,
              avg_house_size, avg_price_per_sqft, avg_bed, avg_bath)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in grouped.iterrows():
        rows.append((
            int(r['city_id']), safe_val(r['city']), safe_val(r['state']), safe_val(r['year_month']),
            round(r['avg_price'], 2) if pd.notna(r['avg_price']) else None,
            round(r['median_price'], 2) if pd.notna(r['median_price']) else None,
            int(r['listing_count']),
            round(r['avg_house_size'], 2) if pd.notna(r['avg_house_size']) else None,
            round(float(r['avg_price_per_sqft']), 2) if pd.notna(r['avg_price_per_sqft']) else None,
            round(r['avg_bed'], 1) if pd.notna(r['avg_bed']) else None,
            round(r['avg_bath'], 1) if pd.notna(r['avg_bath']) else None,
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor2.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"  [OK] us_monthly_summary 집계 완료: {len(rows)}행")


if __name__ == '__main__':
    load_realtor_listings()
    build_us_monthly_summary()
    print("\n[DONE] STEP 4 완료: Realtor.com 적재 + 월별 요약")
