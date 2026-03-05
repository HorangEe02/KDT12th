"""
STEP 3: Zillow Economics State_time_series.csv → zillow_timeseries 테이블
  TX, GA, AZ, NC 4개 주 필터링
실행: python src/subtopic4/s4_step3_load_zillow_timeseries.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *

# State_time_series.csv 컬럼 → DB 컬럼 매핑
COL_MAP = {
    'ZHVI_AllHomes': 'zhvi_all',
    'ZHVIPerSqft_AllHomes': 'zhvi_per_sqft',
    'ZRI_AllHomes': 'zri_all',
    'MedianListingPrice_AllHomes': 'median_listing_price',
    'MedianRentalPrice_AllHomes': 'median_rental_price',
    'InventorySeasonallyAdjusted_AllHomes': 'inventory_seasonally_adj',
    'DaysOnZillow_AllHomes': 'days_on_zillow',
    'Sale_Counts': 'sale_counts',
    'Sale_Counts_Seas_Adj': 'sale_counts_seas_adj',
    'PriceToRentRatio_AllHomes': 'price_to_rent_ratio',
    'PctOfHomesIncreasingInValues_AllHomes': 'pct_homes_increasing',
    'PctOfHomesDecreasingInValues_AllHomes': 'pct_homes_decreasing',
    'PctOfHomesSellingForLoss_AllHomes': 'pct_homes_selling_for_loss',
    'PctOfListingsWithPriceReductions_AllHomes': 'pct_listings_price_reduction',
    'MedianPctOfPriceReduction_AllHomes': 'median_pct_price_reduction',
}


def load_state_timeseries():
    csv_path = S4_DATA_FILES['STATE_TS']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] 파일 없음: {csv_path}")
        return 0

    print(f"  파일 로딩: {os.path.basename(csv_path)}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  전체: {len(df)}행, {len(df.columns)}열")

    # 타겟 주 필터
    df_f = df[df['RegionName'].isin(TARGET_STATES)].copy()
    print(f"  필터(4개 주): {len(df_f)}행")

    if df_f.empty:
        print("  [WARN] 타겟 주 없음")
        return 0

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO zillow_timeseries
             (date, region_name, region_level,
              zhvi_all, zhvi_per_sqft, zri_all,
              median_listing_price, median_rental_price,
              inventory_seasonally_adj, days_on_zillow,
              sale_counts, sale_counts_seas_adj,
              price_to_rent_ratio,
              pct_homes_increasing, pct_homes_decreasing,
              pct_homes_selling_for_loss,
              pct_listings_price_reduction,
              median_pct_price_reduction,
              source_file)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = 0
    batch_data = []

    for _, row in df_f.iterrows():
        date_val = safe_val(row.get('Date'))
        if not date_val:
            continue

        vals = (
            date_val,
            row['RegionName'],
            'state',
            safe_val(row.get('ZHVI_AllHomes')),
            safe_val(row.get('ZHVIPerSqft_AllHomes')),
            safe_val(row.get('ZRI_AllHomes')),
            safe_val(row.get('MedianListingPrice_AllHomes')),
            safe_val(row.get('MedianRentalPrice_AllHomes')),
            safe_val(row.get('InventorySeasonallyAdjusted_AllHomes')),
            safe_val(row.get('DaysOnZillow_AllHomes')),
            safe_val(row.get('Sale_Counts')),
            safe_val(row.get('Sale_Counts_Seas_Adj')),
            safe_val(row.get('PriceToRentRatio_AllHomes')),
            safe_val(row.get('PctOfHomesIncreasingInValues_AllHomes')),
            safe_val(row.get('PctOfHomesDecreasingInValues_AllHomes')),
            safe_val(row.get('PctOfHomesSellingForLoss_AllHomes')),
            safe_val(row.get('PctOfListingsWithPriceReductions_AllHomes')),
            safe_val(row.get('MedianPctOfPriceReduction_AllHomes')),
            'State_time_series.csv',
        )
        batch_data.append(vals)

        if len(batch_data) >= 5000:
            cursor.executemany(sql, batch_data)
            conn.commit()
            rows += len(batch_data)
            batch_data = []

    if batch_data:
        cursor.executemany(sql, batch_data)
        conn.commit()
        rows += len(batch_data)

    conn.close()
    print(f"  [OK] State 시계열: {rows}행 → zillow_timeseries")
    return rows


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 3: Zillow Economics State 시계열 로딩")
    print("=" * 60)
    load_state_timeseries()
    print("\n[DONE] STEP 3 완료")
