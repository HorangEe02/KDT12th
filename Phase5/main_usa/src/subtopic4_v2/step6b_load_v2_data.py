"""
STEP 6b: v2 추가 데이터 로딩
1) 대구 아파트 실거래 → daegu_housing_prices
2) 도시별 인구성장률 → city_comparison_population
3) 도시별 기온 (메모리에서 분석용)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def load_daegu_apartment():
    """대구 아파트 실거래 → daegu_housing_prices"""
    csv_path = S4_DATA_FILES['DAEGU_APT']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] Daegu_apt.csv 없음")
        return 0

    # 대용량 파일이므로 청크 단위 처리
    conn = get_connection(DB_NAME)
    sql = """INSERT INTO daegu_housing_prices
             (`year_month`, year, month, district, apt_name, exclusive_area,
              deal_amount, floor, build_year, housing_type, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    total = 0
    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        chunk.columns = chunk.columns.str.strip()

        data = []
        for _, row in chunk.iterrows():
            # contract_year_month: "200508" → "2005-08"
            ym_raw = str(row.get('contract_year_month', ''))
            if len(ym_raw) >= 6:
                year = int(ym_raw[:4])
                month = int(ym_raw[4:6])
                ym = f"{year}-{month:02d}"
            else:
                continue

            # county_or_gu: "서구" 등
            district = safe_val(row.get('county_or_gu'))

            # floor
            floor_val = safe_val(row.get('floor'))
            try:
                floor_val = int(float(floor_val)) if floor_val is not None else None
            except (ValueError, TypeError):
                floor_val = None

            # construction_year
            build_year = safe_val(row.get('construction_year'))
            try:
                build_year = int(float(build_year)) if build_year is not None else None
            except (ValueError, TypeError):
                build_year = None

            # exclusive_area_m2
            area = safe_val(row.get('exclusive_area_m2'))
            try:
                area = float(area) if area is not None else None
            except (ValueError, TypeError):
                area = None

            # transaction_price_krw_10k (만원)
            price = safe_val(row.get('transaction_price_krw_10k'))
            try:
                price = int(float(str(price).replace(',', ''))) if price is not None else None
            except (ValueError, TypeError):
                price = None

            data.append((
                ym, year, month, district,
                safe_val(row.get('building_name')),
                area, price, floor_val, build_year,
                safe_val(row.get('housing_type')),
                'daegu-apartment'
            ))

        if data:
            total += batch_insert(conn, sql, data)
            print(f"    ... {total:,}행 삽입됨")

    conn.close()
    print(f"  [OK] 대구 아파트 실거래: {total:,}행 → daegu_housing_prices")
    return total


def load_world_population_growth():
    """도시별 인구성장률 → city_comparison_population"""
    csv_path = S4_DATA_FILES['WORLD_POP_GROWTH']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] World population growth 파일 없음")
        return 0

    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    print(f"  인구성장률 데이터: {len(df):,}행, 열: {list(df.columns)}")

    # 5개 도시 검색
    target_keywords = {
        'Daegu': ('Daegu', 'comprehensive', 'South Korea'),
        'Dallas': ('Dallas', 'comprehensive', 'United States'),
        'Atlanta': ('Atlanta', 'industry', 'United States'),
        'Phoenix': ('Phoenix', 'climate', 'United States'),
        'Charlotte': ('Charlotte', 'transformation', 'United States'),
    }

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO city_comparison_population
             (city_name, country, continent, comparison_axis,
              population_2024, population_2023, population_growth_rate, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

    total = 0
    data = []

    city_col = 'City'
    for city_key, (search_term, axis, default_country) in target_keywords.items():
        mask = df[city_col].astype(str).str.contains(search_term, case=False, na=False)
        city_rows = df[mask]
        if not city_rows.empty:
            row = city_rows.iloc[0]
            pop_2024 = safe_val(row.get('Population (2024)'))
            pop_2023 = safe_val(row.get('Population (2023)'))
            growth = safe_val(row.get('Growth Rate'))

            try:
                pop_2024 = int(float(pop_2024)) if pop_2024 else None
            except (ValueError, TypeError):
                pop_2024 = None
            try:
                pop_2023 = int(float(pop_2023)) if pop_2023 else None
            except (ValueError, TypeError):
                pop_2023 = None
            try:
                growth = float(growth) if growth else None
            except (ValueError, TypeError):
                growth = None

            data.append((
                city_key,
                safe_val(row.get('Country', default_country)),
                safe_val(row.get('Continent')),
                axis,
                pop_2024, pop_2023, growth,
                'world-population-growth-2024'
            ))
            print(f"  [OK] {city_key}: pop={pop_2024}, growth={growth}")
        else:
            print(f"  [WARN] {city_key} 없음 - 수동 입력")
            # 대구가 없을 경우 수동 데이터
            if city_key == 'Daegu':
                data.append((
                    'Daegu', 'South Korea', 'Asia', 'comprehensive',
                    2380000, 2390000, -0.0042,
                    'manual-estimate'
                ))

    if data:
        total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] 도시 인구성장률: {total}행 → city_comparison_population")
    return total


def run():
    print("=" * 60)
    print("STEP 6b: v2 추가 데이터 로딩")
    print("=" * 60)
    load_daegu_apartment()
    load_world_population_growth()
    print("\n  STEP 6b 완료!")


if __name__ == '__main__':
    run()
