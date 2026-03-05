"""
STEP 5: 글로벌 경제지표 로딩
- Global Economy Indicators.csv → economic_indicators
- 한국(South Korea) + 미국(United States) 필터
- GDP 성장률 계산
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def load_global_economy():
    csv_path = S4_DATA_FILES['GLOBAL_ECONOMY']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] Global Economy Indicators.csv 없음")
        return 0

    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()

    # 한국, 미국 필터
    target_countries = ['Republic of Korea', 'United States']
    df = df[df['Country'].str.strip().isin(target_countries)].copy()
    print(f"  필터링 후 행수: {len(df):,}")

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO economic_indicators
             (country, country_code, year, gdp, gdp_per_capita,
              manufacturing_pct, services_pct, industry_pct,
              agriculture_pct, construction_pct, population, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    data = []
    for _, row in df.iterrows():
        country_raw = str(row.get('Country', '')).strip()
        country = 'South Korea' if 'Korea' in country_raw else country_raw
        year = safe_val(row.get('Year'))

        # GDP
        gdp = safe_val(row.get('Gross Domestic Product (GDP)'))

        # Per capita GNI
        gdp_pc = safe_val(row.get('Per capita GNI'))

        # 총부가가치 (분모)
        total_va = safe_val(row.get('Total Value Added'))

        # 산업 비중 계산
        manufacturing = safe_val(row.get('Manufacturing (ISIC D)'))
        construction = safe_val(row.get('Construction (ISIC F)'))
        agriculture = safe_val(row.get('Agriculture hunting forestry fishing (ISIC A-B)'))
        services = safe_val(row.get('Other Activities (ISIC J-P)'))
        mining_mfg = safe_val(row.get('Mining Manufacturing Utilities (ISIC C-E)'))

        mfg_pct = (float(manufacturing) / float(total_va) * 100) if manufacturing and total_va and float(total_va) != 0 else None
        con_pct = (float(construction) / float(total_va) * 100) if construction and total_va and float(total_va) != 0 else None
        agr_pct = (float(agriculture) / float(total_va) * 100) if agriculture and total_va and float(total_va) != 0 else None
        svc_pct = (float(services) / float(total_va) * 100) if services and total_va and float(total_va) != 0 else None
        ind_pct = (float(mining_mfg) / float(total_va) * 100) if mining_mfg and total_va and float(total_va) != 0 else None

        population = safe_val(row.get('Population'))

        data.append((
            country, None, year, gdp, gdp_pc,
            safe_val(mfg_pct), safe_val(svc_pct), safe_val(ind_pct),
            safe_val(agr_pct), safe_val(con_pct),
            int(float(population)) if population else None,
            'global-economy-indicators'
        ))

    total = batch_insert(conn, sql, data)

    # GDP 성장률 계산 (INSERT 후 UPDATE)
    cursor = conn.cursor()
    for country in ['South Korea', 'United States']:
        cursor.execute("""
            SELECT id, year, gdp FROM economic_indicators
            WHERE country = %s ORDER BY year
        """, (country,))
        rows = cursor.fetchall()
        for i in range(1, len(rows)):
            prev_gdp = rows[i-1][2]
            curr_gdp = rows[i][2]
            if prev_gdp and curr_gdp and float(prev_gdp) != 0:
                growth = (float(curr_gdp) - float(prev_gdp)) / float(prev_gdp) * 100
                cursor.execute(
                    "UPDATE economic_indicators SET gdp_growth_rate = %s WHERE id = %s",
                    (round(growth, 4), rows[i][0])
                )
        conn.commit()

    conn.close()
    print(f"  [OK] 글로벌 경제지표: {total:,}행 → economic_indicators")
    return total


def run():
    print("=" * 60)
    print("STEP 5: 글로벌 경제지표 로딩")
    print("=" * 60)
    load_global_economy()
    print("\n  STEP 5 완료!")


if __name__ == '__main__':
    run()
