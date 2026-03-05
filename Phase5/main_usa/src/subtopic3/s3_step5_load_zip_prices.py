"""
STEP 5: Zillow Zip_time_series.csv → us_zip_prices + Realtor ZIP 집계 → us_zip_realtor_summary
실행: python src/subtopic3/s3_step5_load_zip_prices.py

Zip_time_series.csv (746MB, 76열) — 반드시 타겟 ZIP 목록으로 필터!
타겟 ZIP: 소주제1 us_realtor_listings에서 city_id별 zip_code 추출
"""
import pandas as pd
import numpy as np
import os
from s3_step0_config import (
    get_connection, DB_NAME, safe_val,
    S3_DATA_FILES, CITY_ID_NAME_MAP,
)

# Zip_time_series.csv에서 사용할 핵심 열
ZIP_PRICE_COLS = [
    'Date', 'RegionName',
    'ZHVI_AllHomes', 'ZHVIPerSqft_AllHomes',
    'MedianListingPrice_AllHomes',
    'MedianRentalPrice_AllHomes',
    'InventorySeasonallyAdjusted_AllHomes',
]


def get_target_zips_from_realtor():
    """소주제1 us_realtor_listings에서 city_id별 상위 ZIP 코드 추출"""
    print("[INFO] Realtor 데이터에서 타겟 ZIP 추출")
    conn = get_connection(DB_NAME, for_pandas=True)

    try:
        df = pd.read_sql("""
            SELECT city_id, zip_code, COUNT(*) AS cnt
            FROM us_realtor_listings
            WHERE city_id IS NOT NULL AND zip_code IS NOT NULL
            GROUP BY city_id, zip_code
            HAVING cnt >= 5
            ORDER BY city_id, cnt DESC
        """, conn)
    except Exception as e:
        print(f"   [WARN] Realtor 테이블 조회 실패: {e}")
        conn.close()
        return get_fallback_zips()

    conn.close()

    if df.empty:
        print("   [WARN] Realtor ZIP 없음 - 대표 ZIP 범위 사용")
        return get_fallback_zips()

    zips = df['zip_code'].astype(str).str.zfill(5).unique().tolist()
    print(f"   [OK] {len(zips)}개 ZIP 추출")
    return zips


def get_fallback_zips():
    """Realtor 미적재 시 대표 ZIP 범위"""
    zips = []
    zips += [str(z) for z in range(75001, 75399)]   # Dallas
    zips += [str(z) for z in range(30301, 31299)]   # Atlanta
    zips += [str(z) for z in range(85001, 85399)]   # Phoenix
    zips += [str(z) for z in range(28001, 28299)]   # Charlotte
    return zips


def load_zip_timeseries():
    """Zip_time_series.csv → us_zip_prices (타겟 ZIP 필터)"""
    csv_path = S3_DATA_FILES['ZIP_TIME_SERIES']
    if not os.path.exists(csv_path):
        print(f"[WARN] 파일 없음: {csv_path}")
        return

    print(f"\n[INFO] Zip_time_series 로딩: {csv_path}")

    target_zips = get_target_zips_from_realtor()
    target_zips_set = set(target_zips)
    print(f"   타겟 ZIP 수: {len(target_zips_set)}")

    # 사용 가능 열 확인
    df_sample = pd.read_csv(csv_path, nrows=5)
    avail = [c for c in ZIP_PRICE_COLS if c in df_sample.columns]
    # InventorySeasonallyAdjusted 대체 이름 확인
    if 'InventorySeasonallyAdjusted_AllHomes' not in avail:
        for c in df_sample.columns:
            if 'inventory' in c.lower() and 'seasonal' in c.lower():
                avail.append(c)
                break
    # DaysOnZillow 찾기
    for c in df_sample.columns:
        if 'daysonzillow' in c.lower():
            avail.append(c)
            break
    avail = list(set(avail))
    print(f"   사용 열: {avail}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO us_zip_prices
             (zip_code, date, `year_month`, zhvi, zhvi_per_sqft,
              median_listing_price, median_rental_price,
              inventory, days_on_zillow)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for chunk in pd.read_csv(csv_path, usecols=lambda c: c in avail,
                              chunksize=30000, low_memory=False):
        # RegionName = ZIP 코드
        if 'RegionName' not in chunk.columns:
            continue
        chunk['RegionName'] = chunk['RegionName'].astype(str).str.zfill(5)
        chunk = chunk[chunk['RegionName'].isin(target_zips_set)]

        if chunk.empty:
            continue

        rows = []
        for _, r in chunk.iterrows():
            date = r.get('Date')
            ym = str(date)[:7] if pd.notna(date) else None

            # 동적 열 이름 매핑
            inv_col = next((c for c in chunk.columns if 'inventory' in c.lower() and 'seasonal' in c.lower()), None)
            doz_col = next((c for c in chunk.columns if 'daysonzillow' in c.lower()), None)

            rows.append((
                r['RegionName'], safe_val(date), ym,
                safe_val(r.get('ZHVI_AllHomes')),
                safe_val(r.get('ZHVIPerSqft_AllHomes')),
                safe_val(r.get('MedianListingPrice_AllHomes')),
                safe_val(r.get('MedianRentalPrice_AllHomes')),
                safe_val(r.get(inv_col)) if inv_col else None,
                safe_val(r.get(doz_col)) if doz_col else None,
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 30000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   [OK] us_zip_prices 적재: {total}행")


def build_zip_realtor_summary():
    """소주제1 us_realtor_listings → us_zip_realtor_summary (ZIP별 매물 집계)"""
    print("\n[INFO] ZIP별 Realtor 매물 집계")

    conn = get_connection(DB_NAME, for_pandas=True)

    try:
        df = pd.read_sql("""
            SELECT
                zip_code,
                city AS city_name,
                state,
                city_id,
                COUNT(*) AS listing_count,
                AVG(price) AS avg_price,
                AVG(house_size) AS avg_house_size,
                AVG(CASE WHEN house_size > 0 THEN price / house_size END) AS avg_price_per_sqft,
                AVG(bed) AS avg_bed,
                AVG(bath) AS avg_bath,
                MIN(price) AS min_price,
                MAX(price) AS max_price
            FROM us_realtor_listings
            WHERE zip_code IS NOT NULL AND price > 0 AND city_id IS NOT NULL
            GROUP BY zip_code, city, state, city_id
            HAVING listing_count >= 3
        """, conn)
    except Exception as e:
        print(f"   [WARN] 조회 실패: {e}")
        conn.close()
        return

    if df.empty:
        print("   [WARN] 집계 결과 0행")
        conn.close()
        return

    # 중위가격 별도 계산
    try:
        df_median = pd.read_sql("""
            SELECT zip_code, price
            FROM us_realtor_listings
            WHERE zip_code IS NOT NULL AND price > 0 AND city_id IS NOT NULL
        """, conn)
        median_by_zip = df_median.groupby('zip_code')['price'].median().reset_index()
        median_by_zip.columns = ['zip_code', 'median_price']
        df = df.merge(median_by_zip, on='zip_code', how='left')
    except Exception:
        df['median_price'] = None

    conn.close()

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE us_zip_realtor_summary")

    sql = """INSERT INTO us_zip_realtor_summary
             (zip_code, city_name, state, city_id, listing_count,
              avg_price, median_price, avg_house_size, avg_price_per_sqft,
              avg_bed, avg_bath, min_price, max_price)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_val(r['zip_code']),
            safe_val(r['city_name']),
            safe_val(r['state']),
            int(r['city_id']),
            int(r['listing_count']),
            round(float(r['avg_price']), 2) if pd.notna(r['avg_price']) else None,
            round(float(r['median_price']), 2) if pd.notna(r.get('median_price')) else None,
            round(float(r['avg_house_size']), 2) if pd.notna(r['avg_house_size']) else None,
            round(float(r['avg_price_per_sqft']), 2) if pd.notna(r['avg_price_per_sqft']) else None,
            round(float(r['avg_bed']), 1) if pd.notna(r['avg_bed']) else None,
            round(float(r['avg_bath']), 1) if pd.notna(r['avg_bath']) else None,
            round(float(r['min_price']), 2) if pd.notna(r['min_price']) else None,
            round(float(r['max_price']), 2) if pd.notna(r['max_price']) else None,
        ))

    batch = 3000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   [OK] us_zip_realtor_summary: {len(rows)}행 ({len(df['city_id'].unique())}개 도시)")


if __name__ == '__main__':
    load_zip_timeseries()
    build_zip_realtor_summary()
    print("\n[DONE] S3 STEP 5 완료")
