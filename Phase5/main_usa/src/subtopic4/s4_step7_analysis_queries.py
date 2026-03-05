"""
STEP 7: 소주제4 분석 쿼리 4개 + industry_housing_impact 적재
  Q1: 산업별 고용 변동 vs 신규건설
  Q2: Charlotte 전환기 시장 분석
  Q3: 4개 주 시장 건전성 비교
  Q4: 대구 vs Charlotte 비교
실행: python src/subtopic4/s4_step7_analysis_queries.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *
from scipy import stats


def query_to_df(sql, params=None):
    """SQL → DataFrame"""
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ── Q1: 산업별 고용 변동 vs 신규건설 상관분석 ──
def analysis_q1():
    print("\n" + "=" * 60)
    print("Q1: 산업별 고용 변동 vs 신규건설 판매건수")
    print("=" * 60)

    # 산업별 고용 (연도별, supersector 레벨)
    sql_emp = """
        SELECT year, supersector_name,
               AVG(employee_count) AS avg_employees
        FROM us_industry_employment
        WHERE supersector_code IN ('30','50','55','60')
          AND year >= 2000
        GROUP BY year, supersector_name
        ORDER BY year, supersector_name
    """
    df_emp = query_to_df(sql_emp)
    print(f"  고용 데이터: {len(df_emp)}행")

    # 신규건설 (MSA별 연도별)
    sql_con = """
        SELECT region_name,
               LEFT(`year_month`, 4) AS year,
               AVG(new_construction_sales) AS avg_new_con,
               SUM(new_construction_sales) AS total_new_con
        FROM us_metro_demand
        WHERE new_construction_sales IS NOT NULL
        GROUP BY region_name, LEFT(`year_month`, 4)
        ORDER BY region_name, year
    """
    df_con = query_to_df(sql_con)
    print(f"  신규건설 데이터: {len(df_con)}행")

    # 전국 합산
    df_con_total = df_con.groupby('year').agg(
        total_new_con=('total_new_con', 'sum')
    ).reset_index()
    df_con_total['year'] = df_con_total['year'].astype(int)

    # 상관분석
    if not df_emp.empty and not df_con_total.empty:
        for ind in df_emp['supersector_name'].unique():
            subset = df_emp[df_emp['supersector_name'] == ind].copy()
            subset['year'] = subset['year'].astype(int)
            merged = subset.merge(df_con_total, on='year')
            if len(merged) >= 3:
                corr, pval = stats.pearsonr(merged['avg_employees'], merged['total_new_con'])
                print(f"  {ind} vs 신규건설: r={corr:.3f}, p={pval:.4f}")

    # CSV 저장
    df_con.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q1_EMPLOYMENT_VS_CONSTRUCTION.csv'),
                  index=False, encoding='utf-8-sig')
    df_emp.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q1_EMPLOYMENT_BY_SECTOR.csv'),
                  index=False, encoding='utf-8-sig')

    return df_emp, df_con


# ── Q2: Charlotte 전환기 분석 ──
def analysis_q2():
    print("\n" + "=" * 60)
    print("Q2: Charlotte 산업전환기 시장 분석")
    print("=" * 60)

    sql = """
        SELECT `year_month`,
               MAX(market_temp_index) AS market_temp_index,
               MAX(income_needed) AS income_needed,
               MAX(new_construction_sales) AS new_construction_sales,
               MAX(sales_count) AS sales_count
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY `year_month`
        ORDER BY `year_month`
    """
    df = query_to_df(sql)
    print(f"  Charlotte 수급: {len(df)}행")

    if not df.empty:
        df['year'] = df['year_month'].str[:4].astype(int)
        summary = df.groupby('year').agg({
            'market_temp_index': 'mean',
            'income_needed': 'mean',
            'new_construction_sales': 'sum',
            'sales_count': 'sum',
        }).round(2)
        print(f"\n  연도별 요약:\n{summary}")

    df.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q2_CHARLOTTE_TRANSITION.csv'),
              index=False, encoding='utf-8-sig')
    return df


# ── Q3: 4개 주 시장 건전성 비교 ──
def analysis_q3():
    print("\n" + "=" * 60)
    print("Q3: 4개 주(State) 시장 건전성 비교")
    print("=" * 60)

    sql = """
        SELECT region_name,
               YEAR(date) AS year,
               AVG(pct_homes_increasing) AS avg_pct_increasing,
               AVG(pct_homes_selling_for_loss) AS avg_pct_loss,
               AVG(pct_listings_price_reduction) AS avg_pct_reduction,
               AVG(zhvi_all) AS avg_zhvi,
               AVG(days_on_zillow) AS avg_days_on_zillow
        FROM zillow_timeseries
        WHERE region_level = 'state'
          AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
          AND date >= '2000-01-01'
        GROUP BY region_name, YEAR(date)
        ORDER BY region_name, year
    """
    df = query_to_df(sql)
    print(f"  시장 건전성: {len(df)}행")

    if not df.empty:
        recent = df[df['year'] >= 2020]
        if not recent.empty:
            pivot = recent.pivot_table(
                index='year', columns='region_name',
                values='avg_zhvi', aggfunc='mean'
            ).round(0)
            print(f"\n  2020~최근 ZHVI:\n{pivot}")

    df.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q3_MARKET_HEALTH.csv'),
              index=False, encoding='utf-8-sig')
    return df


# ── Q4: 대구 vs Charlotte 비교 ──
def analysis_q4():
    print("\n" + "=" * 60)
    print("Q4: 대구 vs Charlotte 산업전환 비교")
    print("=" * 60)

    # 대구 인구통계 (연도별 집계)
    sql_daegu = """
        SELECT year,
               SUM(birth_count) AS total_birth,
               AVG(birth_rate) AS avg_birth_rate,
               SUM(death_count) AS total_death,
               AVG(death_rate) AS avg_death_rate,
               SUM(natural_growth) AS total_natural_growth,
               AVG(natural_growth_rate) AS avg_natural_growth_rate,
               SUM(marriage_count) AS total_marriage,
               AVG(marriage_rate) AS avg_marriage_rate
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year
        ORDER BY year
    """
    df_daegu = query_to_df(sql_daegu)
    print(f"  대구 인구통계: {len(df_daegu)}행")

    # Charlotte 수급 (연도별)
    sql_charlotte = """
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS avg_market_temp,
               AVG(income_needed) AS avg_income_needed,
               SUM(new_construction_sales) AS total_new_con
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """
    df_charlotte = query_to_df(sql_charlotte)
    print(f"  Charlotte 수급: {len(df_charlotte)}행")

    # 한국 vs 미국 거시경제 (제조업→서비스업 전환)
    sql_macro = """
        SELECT country, year,
               manufacturing_pct, services_pct, construction_pct,
               gdp_growth_rate
        FROM economic_indicators
        WHERE country IN ('South Korea', 'United States')
          AND year >= 2000
        ORDER BY country, year
    """
    df_macro = query_to_df(sql_macro)
    print(f"  거시경제 비교: {len(df_macro)}행")

    # CSV 저장
    df_daegu.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q4_DAEGU_DEMOGRAPHICS.csv'),
                    index=False, encoding='utf-8-sig')
    df_charlotte.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q4_CHARLOTTE_DEMAND.csv'),
                        index=False, encoding='utf-8-sig')
    df_macro.to_csv(os.path.join(S4_OUTPUT_DIR, 'S4_Q4_MACRO_COMPARISON.csv'),
                    index=False, encoding='utf-8-sig')

    return df_daegu, df_charlotte, df_macro


# ── industry_housing_impact 적재 ──
def save_impact_analysis():
    """Charlotte 연도별 수급 변화율 → industry_housing_impact"""
    sql = """
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(new_construction_sales) AS new_con_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
          AND new_construction_sales IS NOT NULL
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """
    df = query_to_df(sql)

    if df.empty:
        print("  [WARN] Charlotte 데이터 없음")
        return

    df['year'] = df['year'].astype(int)
    df['market_temp'] = pd.to_numeric(df['market_temp'], errors='coerce')
    df['income_needed'] = pd.to_numeric(df['income_needed'], errors='coerce')
    df['new_con_sales'] = pd.to_numeric(df['new_con_sales'], errors='coerce')
    df['market_temp_change'] = df['market_temp'].diff()
    df['income_change'] = df['income_needed'].pct_change()
    df['construction_change'] = df['new_con_sales'].pct_change()

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        if pd.isna(row.get('market_temp_change')):
            continue
        cursor.execute(
            """INSERT INTO industry_housing_impact
               (city_id, city_name, country, year,
                dominant_industry, new_construction_sales,
                new_construction_sales_change, market_temp_index,
                market_temp_change, income_needed, income_needed_change,
                source_dataset)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                5, 'Charlotte', 'USA', row['year'],
                'Finance/Tech Transition',
                safe_val(row.get('new_con_sales')),
                safe_val(row.get('construction_change')),
                safe_val(row.get('market_temp')),
                safe_val(row.get('market_temp_change')),
                safe_val(row.get('income_needed')),
                safe_val(row.get('income_change')),
                'zillow_housing_analysis',
            )
        )

    conn.commit()
    conn.close()
    print("  [OK] Charlotte 영향 분석 → industry_housing_impact")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 7: 소주제4 분석 쿼리")
    print("=" * 60)
    analysis_q1()
    analysis_q2()
    analysis_q3()
    analysis_q4()
    save_impact_analysis()
    print("\n[DONE] STEP 7 완료")
