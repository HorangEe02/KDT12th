"""
STEP 3: Zillow Economics State_time_series.csv → zillow_timeseries
4개 주(Texas, Georgia, Arizona, North Carolina)의 주택 시계열 데이터 로딩
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *

# CSV 컬럼 → DB 컬럼 매핑
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

TARGET_STATES = ['Texas', 'Georgia', 'Arizona', 'North Carolina']


def load_state_timeseries():
    csv_path = S4_DATA_FILES['STATE_TS']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] State_time_series.csv 없음")
        return 0

    use_cols = ['Date', 'RegionName'] + list(COL_MAP.keys())
    df = pd.read_csv(csv_path, usecols=lambda c: c in use_cols, low_memory=False)
    df = df[df['RegionName'].isin(TARGET_STATES)].copy()
    df = df.where(pd.notnull(df), None)

    print(f"  State 시계열 데이터: {len(df):,}행 (4개 주)")

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO zillow_timeseries
             (date, region_name, region_level,
              zhvi_all, zhvi_per_sqft, zri_all, median_listing_price,
              median_rental_price, inventory_seasonally_adj, days_on_zillow,
              sale_counts, sale_counts_seas_adj, price_to_rent_ratio,
              pct_homes_increasing, pct_homes_decreasing,
              pct_homes_selling_for_loss, pct_listings_price_reduction,
              median_pct_price_reduction, source_file)
             VALUES (%s,%s,'state',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    data = []
    for _, row in df.iterrows():
        data.append((
            safe_val(row.get('Date')), row['RegionName'],
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
        ))

    total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] State 시계열: {total:,}행 → zillow_timeseries")
    return total


def run():
    print("=" * 60)
    print("STEP 3: Zillow State 시계열 로딩")
    print("=" * 60)
    load_state_timeseries()
    print("\n  STEP 3 완료!")


if __name__ == '__main__':
    run()
