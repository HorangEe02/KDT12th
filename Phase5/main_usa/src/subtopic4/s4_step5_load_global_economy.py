"""
STEP 5: 글로벌 경제지표 → economic_indicators
  - Global Economy Indicators.csv (한국/미국)
  - World GDP 데이터로 성장률 보완
실행: python src/subtopic4/s4_step5_load_global_economy.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *


def load_global_economy():
    """Global Economy Indicators.csv에서 한국/미국 추출"""
    csv_path = S4_DATA_FILES['GLOBAL_ECONOMY']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] 파일 없음: {csv_path}")
        return 0

    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()

    # 한국(Republic of Korea) + 미국(United States) 필터
    target_countries = ['Republic of Korea', 'United States']
    df_f = df[df['Country'].str.strip().isin(target_countries)].copy()
    print(f"  필터(한국+미국): {len(df_f)}행")

    if df_f.empty:
        return 0

    # 국가명 정규화
    df_f['Country'] = df_f['Country'].str.strip()
    df_f.loc[df_f['Country'] == 'Republic of Korea', 'Country'] = 'South Korea'

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO economic_indicators
             (country, year, gdp, gdp_per_capita,
              manufacturing_pct, construction_pct,
              services_pct, agriculture_pct,
              population, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = 0
    for _, row in df_f.iterrows():
        year = safe_val(row.get('Year'))
        gdp = safe_val(row.get('Gross Domestic Product (GDP)'))
        total_va = safe_val(row.get('Total Value Added'))
        manufacturing = safe_val(row.get('Manufacturing (ISIC D)'))
        construction = safe_val(row.get('Construction (ISIC F)'))
        services = safe_val(row.get('Other Activities (ISIC J-P)'))
        agriculture = safe_val(row.get('Agriculture, hunting, forestry, fishing (ISIC A-B)'))
        population = safe_val(row.get('Population'))
        per_capita = safe_val(row.get('Per capita GNI'))

        # 산업 비중 계산 (Total Value Added 대비 %)
        mfg_pct = None
        con_pct = None
        svc_pct = None
        agr_pct = None
        if total_va and total_va > 0:
            if manufacturing:
                mfg_pct = round(float(manufacturing) / float(total_va) * 100, 2)
            if construction:
                con_pct = round(float(construction) / float(total_va) * 100, 2)
            if services:
                svc_pct = round(float(services) / float(total_va) * 100, 2)
            if agriculture:
                agr_pct = round(float(agriculture) / float(total_va) * 100, 2)

        cursor.execute(sql, (
            row['Country'], year, gdp, per_capita,
            mfg_pct, con_pct, svc_pct, agr_pct,
            population, 'Global Economy Indicators',
        ))
        rows += 1

    conn.commit()

    # GDP 성장률 계산 (전년 대비)
    cursor = conn.cursor()
    for country in ['South Korea', 'United States']:
        cursor.execute("""
            SELECT id, year, gdp FROM economic_indicators
            WHERE country = %s AND gdp IS NOT NULL
            ORDER BY year
        """, (country,))
        all_rows = cursor.fetchall()
        prev_gdp = None
        for r in all_rows:
            rid = r['id']
            cur_gdp = float(r['gdp']) if r['gdp'] else None
            if prev_gdp and cur_gdp and prev_gdp > 0:
                growth = round((cur_gdp - prev_gdp) / prev_gdp * 100, 4)
                cursor.execute(
                    "UPDATE economic_indicators SET gdp_growth_rate = %s WHERE id = %s",
                    (growth, rid)
                )
            prev_gdp = cur_gdp
    conn.commit()
    conn.close()

    print(f"  [OK] 글로벌 경제지표: {rows}행 → economic_indicators")
    return rows


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 5: 글로벌 경제지표 로딩")
    print("=" * 60)
    load_global_economy()
    print("\n[DONE] STEP 5 완료")
