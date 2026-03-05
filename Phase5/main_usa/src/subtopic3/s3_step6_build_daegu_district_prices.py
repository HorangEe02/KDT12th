"""
STEP 6: 소주제1 daegu_housing_prices → daegu_district_climate_prices (구별 가격 요약)
실행: python src/subtopic3/s3_step6_build_daegu_district_prices.py
"""
import pandas as pd
import numpy as np
from s3_step0_config import get_connection, DB_NAME, safe_val


def build_daegu_district_prices():
    print("\n[INFO] 대구 구별 가격 요약 생성")
    conn = get_connection(DB_NAME, for_pandas=True)

    df = pd.read_sql("""
        SELECT district, deal_amount, exclusive_area
        FROM daegu_housing_prices
        WHERE district IS NOT NULL AND deal_amount > 0
    """, conn)
    conn.close()

    if df.empty:
        print("   [WARN] 대구 데이터 없음")
        return

    df['price_per_m2'] = np.where(
        df['exclusive_area'] > 0,
        df['deal_amount'] / df['exclusive_area'],
        np.nan
    )

    grouped = df.groupby('district').agg(
        avg_price=('deal_amount', 'mean'),
        median_price=('deal_amount', 'median'),
        avg_price_per_m2=('price_per_m2', 'mean'),
        transaction_count=('deal_amount', 'count'),
        avg_exclusive_area=('exclusive_area', 'mean'),
    ).reset_index()

    # 순위 + 프리미엄
    grouped = grouped.sort_values('avg_price', ascending=False).reset_index(drop=True)
    grouped['price_rank'] = range(1, len(grouped) + 1)
    city_avg = grouped['avg_price'].mean()
    grouped['premium_vs_avg'] = ((grouped['avg_price'] - city_avg) / city_avg * 100).round(4)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE daegu_district_climate_prices")

    sql = """INSERT INTO daegu_district_climate_prices
             (district, period, avg_price, median_price, avg_price_per_m2,
              transaction_count, avg_exclusive_area, price_rank, premium_vs_avg)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in grouped.iterrows():
        rows.append((
            r['district'], '전체기간',
            int(r['avg_price']), int(r['median_price']),
            round(float(r['avg_price_per_m2']), 2) if pd.notna(r['avg_price_per_m2']) else None,
            int(r['transaction_count']),
            round(float(r['avg_exclusive_area']), 2) if pd.notna(r['avg_exclusive_area']) else None,
            int(r['price_rank']),
            float(r['premium_vs_avg']),
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   [OK] daegu_district_climate_prices: {len(rows)}개 구")
    if len(grouped) > 0:
        print(f"   [INFO] 최고가 구: {grouped.iloc[0]['district']} (프리미엄: +{grouped.iloc[0]['premium_vs_avg']:.1f}%)")


if __name__ == '__main__':
    build_daegu_district_prices()
    print("\n[DONE] S3 STEP 6 완료")
