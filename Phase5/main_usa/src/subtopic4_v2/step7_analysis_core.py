"""
STEP 7: 기존 산업전환 분석 (v1 유지)
- Q1: 산업별 고용 vs 신규건설 상관분석
- Q2: Charlotte 시장 전환기 분석
- Q3: 4개 주 시장건전성 비교
- Q4: 대구 vs Charlotte 비교
- 산업-부동산 영향 분석 결과 저장
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *
from scipy import stats


def analysis_q1():
    """Q1: 산업별 고용 vs 신규건설 상관분석"""
    print("\n--- Q1: 산업별 고용 vs 신규건설 상관 ---")

    df_emp = query_to_df("""
        SELECT year, supersector_name, SUM(employee_count) AS total_emp
        FROM us_industry_employment
        WHERE data_type_code = '01'
        GROUP BY year, supersector_name
        ORDER BY year
    """)

    df_con = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               SUM(new_construction_sales) AS total_new_con
        FROM us_metro_demand
        WHERE region_name = 'United States'
          AND new_construction_sales IS NOT NULL
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)

    if df_emp.empty or df_con.empty:
        print("  [WARN] 데이터 부족")
        return df_emp, df_con

    df_emp['year'] = df_emp['year'].astype(str)
    df_con['year'] = df_con['year'].astype(str)

    # 상관분석
    correlations = []
    for sector in df_emp['supersector_name'].unique():
        sector_df = df_emp[df_emp['supersector_name'] == sector].copy()
        merged = pd.merge(sector_df, df_con, on='year', how='inner')
        if len(merged) >= 5:
            r, p = stats.pearsonr(merged['total_emp'], merged['total_new_con'])
            correlations.append({
                'supersector': sector,
                'correlation': round(r, 4),
                'p_value': round(p, 4),
                'n_years': len(merged)
            })

    df_corr = pd.DataFrame(correlations)
    if not df_corr.empty:
        df_corr = df_corr.sort_values('correlation', ascending=False)
        df_corr.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q1_EMPLOYMENT_VS_CONSTRUCTION.csv'), index=False)
        print(f"  상관분석 결과:\n{df_corr.to_string(index=False)}")
    df_emp.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q1_EMPLOYMENT_BY_SECTOR.csv'), index=False)
    return df_emp, df_con


def analysis_q2():
    """Q2: Charlotte 시장 전환기 분석"""
    print("\n--- Q2: Charlotte 전환기 분석 ---")

    df = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS avg_market_temp,
               AVG(income_needed) AS avg_income_needed,
               SUM(new_construction_sales) AS total_new_con,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)

    if not df.empty:
        df['year'] = df['year'].astype(str)
        df.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q2_CHARLOTTE_TRANSITION.csv'), index=False)
        print(f"  Charlotte 연도별 지표: {len(df)}행")
        print(df.to_string(index=False))
    return df


def analysis_q3():
    """Q3: 4개 주 시장건전성 비교"""
    print("\n--- Q3: 4개 주 시장건전성 ---")

    df = query_to_df("""
        SELECT region_name, YEAR(date) AS year,
               AVG(pct_homes_increasing) AS avg_pct_increasing,
               AVG(pct_homes_selling_for_loss) AS avg_pct_loss,
               AVG(pct_listings_price_reduction) AS avg_pct_reduction,
               AVG(zhvi_all) AS avg_zhvi,
               AVG(days_on_zillow) AS avg_days
        FROM zillow_timeseries
        WHERE region_level = 'state'
          AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
          AND YEAR(date) >= 2005
        GROUP BY region_name, YEAR(date)
        ORDER BY region_name, year
    """)

    if not df.empty:
        df['year'] = df['year'].astype(str)
        df.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q3_MARKET_HEALTH.csv'), index=False)
        print(f"  시장건전성: {len(df)}행")
        # 최근 연도 요약
        latest = df[df['year'] == df['year'].max()]
        if not latest.empty:
            print(f"\n  최근({latest.iloc[0]['year']}) 요약:")
            print(latest.to_string(index=False))
    return df


def analysis_q4():
    """Q4: 대구 vs Charlotte 비교"""
    print("\n--- Q4: 대구 vs Charlotte ---")

    # 대구 인구통계 (연도별 합산/평균)
    df_daegu = query_to_df("""
        SELECT year,
               SUM(birth_count) AS total_birth,
               AVG(birth_rate) AS avg_birth_rate,
               SUM(death_count) AS total_death,
               AVG(death_rate) AS avg_death_rate,
               AVG(natural_growth_rate) AS avg_natural_growth_rate,
               AVG(marriage_rate) AS avg_marriage_rate,
               AVG(divorce_rate) AS avg_divorce_rate
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year
        ORDER BY year
    """)
    if not df_daegu.empty:
        df_daegu['year'] = df_daegu['year'].astype(str)

    # Charlotte 수급
    df_charlotte = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS avg_market_temp,
               AVG(income_needed) AS avg_income_needed,
               SUM(new_construction_sales) AS total_new_con,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_charlotte.empty:
        df_charlotte['year'] = df_charlotte['year'].astype(str)

    # 거시경제 비교
    df_macro = query_to_df("""
        SELECT country, year, gdp_growth_rate, manufacturing_pct, services_pct
        FROM economic_indicators
        WHERE country IN ('South Korea', 'United States')
          AND year >= 2000
        ORDER BY country, year
    """)
    if not df_macro.empty:
        df_macro['year'] = df_macro['year'].astype(str)

    if not df_daegu.empty:
        df_daegu.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q4_DAEGU_DEMOGRAPHICS.csv'), index=False)
        print(f"  대구 인구통계: {len(df_daegu)}행")
    if not df_charlotte.empty:
        df_charlotte.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q4_CHARLOTTE_DEMAND.csv'), index=False)
        print(f"  Charlotte 수급: {len(df_charlotte)}행")
    if not df_macro.empty:
        df_macro.to_csv(os.path.join(OUTPUT_DIR, 'S4_Q4_MACRO_COMPARISON.csv'), index=False)
        print(f"  거시경제: {len(df_macro)}행")

    return df_daegu, df_charlotte, df_macro


def save_impact_analysis():
    """Charlotte 산업-부동산 영향 분석 저장"""
    print("\n--- 산업-부동산 영향 분석 저장 ---")

    df = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(new_construction_sales) AS new_con
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)

    if df.empty:
        print("  [WARN] Charlotte 데이터 없음")
        return

    df['year'] = df['year'].astype(str)
    df['market_temp_change'] = df['market_temp'].diff()
    df['income_change'] = df['income_needed'].pct_change() * 100
    df['construction_change'] = df['new_con'].pct_change() * 100

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO industry_housing_impact
             (city_id, city_name, country, year, dominant_industry,
              new_construction_sales, new_construction_sales_change,
              market_temp_index, market_temp_change,
              income_needed, income_needed_change, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    data = []
    for _, row in df.iterrows():
        data.append((
            5, 'Charlotte', 'United States', int(row['year']),
            'Finance/Tech Transition',
            safe_val(row.get('new_con')),
            safe_val(row.get('construction_change')),
            safe_val(row.get('market_temp')),
            safe_val(row.get('market_temp_change')),
            safe_val(row.get('income_needed')),
            safe_val(row.get('income_change')),
            'zillow/bls'
        ))

    total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] 산업-부동산 영향: {total}행 → industry_housing_impact")


def run():
    print("=" * 60)
    print("STEP 7: 기존 산업전환 분석")
    print("=" * 60)
    analysis_q1()
    analysis_q2()
    analysis_q3()
    analysis_q4()
    save_impact_analysis()
    print("\n  STEP 7 완료!")


if __name__ == '__main__':
    run()
