"""
STEP 8: 소주제2 분석 SQL 쿼리 모음 (10개) → CSV
실행: python src/subtopic2/s2_step8_analysis_queries.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from s2_step0_config import get_connection, DB_NAME, S2_OUTPUT_DIR


def query_to_df(sql):
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============================================================
# Q1: 시장온도지수 추이 — 4도시 비교
# ============================================================
Q1_MARKET_TEMP = """
SELECT
    `year_month`,
    CASE
        WHEN region_name LIKE '%%Dallas%%' THEN 'Dallas'
        WHEN region_name LIKE '%%Atlanta%%' THEN 'Atlanta'
        WHEN region_name LIKE '%%Phoenix%%' THEN 'Phoenix'
        WHEN region_name LIKE '%%Charlotte%%' THEN 'Charlotte'
        WHEN region_name LIKE '%%United States%%' THEN 'US Average'
    END AS city,
    market_temp_index,
    inventory,
    sales_count,
    mean_days_pending,
    income_needed
FROM us_metro_demand
ORDER BY city, `year_month`
"""

# ============================================================
# Q2: 수급 균형 지표 (재고 / 판매건수 = 몇 개월분 재고)
# ============================================================
Q2_SUPPLY_DEMAND = """
SELECT
    `year_month`,
    CASE
        WHEN region_name LIKE '%%Dallas%%' THEN 'Dallas'
        WHEN region_name LIKE '%%Atlanta%%' THEN 'Atlanta'
        WHEN region_name LIKE '%%Phoenix%%' THEN 'Phoenix'
        WHEN region_name LIKE '%%Charlotte%%' THEN 'Charlotte'
    END AS city,
    inventory,
    sales_count,
    ROUND(inventory / NULLIF(sales_count, 0), 2) AS months_of_supply
FROM us_metro_demand
WHERE region_name NOT LIKE '%%United States%%'
  AND inventory IS NOT NULL
  AND sales_count IS NOT NULL
ORDER BY city, `year_month`
"""

# ============================================================
# Q3: 대구 인구 추이 (출생/사망/자연증감)
# ============================================================
Q3_DAEGU_POP = """
SELECT
    year,
    birth_count,
    death_count,
    natural_increase,
    birth_rate,
    death_rate,
    avg_household_income
FROM daegu_population_summary
ORDER BY year
"""

# ============================================================
# Q4: 인구-ZHVI 통합 비교 (연도별)
# ============================================================
Q4_POP_HOUSING = """
SELECT
    city_name,
    country,
    year,
    population,
    pop_change_rate,
    zhvi,
    zhvi_change_rate,
    avg_sales_count,
    avg_market_temp,
    supply_demand_ratio
FROM annual_pop_housing_merged
ORDER BY city_name, year
"""

# ============================================================
# Q5: 상관분석 결과 요약
# ============================================================
Q5_CORRELATION = """
SELECT
    city_name,
    x_variable,
    y_variable,
    pearson_r,
    p_value,
    significance,
    interpretation
FROM population_housing_correlation
ORDER BY city_name, ABS(pearson_r) DESC
"""

# ============================================================
# Q6: 주택구매 필요소득 추이 (구매력 진입장벽)
# ============================================================
Q6_INCOME_NEEDED = """
SELECT
    `year_month`,
    CASE
        WHEN region_name LIKE '%%Dallas%%' THEN 'Dallas'
        WHEN region_name LIKE '%%Atlanta%%' THEN 'Atlanta'
        WHEN region_name LIKE '%%Phoenix%%' THEN 'Phoenix'
        WHEN region_name LIKE '%%Charlotte%%' THEN 'Charlotte'
        WHEN region_name LIKE '%%United States%%' THEN 'US Average'
    END AS city,
    income_needed
FROM us_metro_demand
WHERE income_needed IS NOT NULL
ORDER BY city, `year_month`
"""

# ============================================================
# Q7: 미국 County별 인구·소득 비교
# ============================================================
Q7_COUNTY_COMPARE = """
SELECT
    c.city_name,
    d.county,
    d.state,
    d.census_year,
    d.total_population,
    d.median_income,
    d.unemployment,
    d.professional,
    d.mean_commute
FROM us_census_demographics d
JOIN cities c ON d.city_id = c.city_id
WHERE d.city_id IS NOT NULL
ORDER BY c.city_name, d.census_year
"""

# ============================================================
# Q8: 글로벌 도시 인구성장률 비교
# ============================================================
Q8_GLOBAL_POP = """
SELECT city_name, country, continent, population_2024, growth_rate
FROM world_city_population_growth
WHERE city_name IN ('Daegu', 'Dallas', 'Atlanta', 'Phoenix', 'Charlotte')
   OR city_name LIKE '%%대구%%'
   OR city_name LIKE '%%daegu%%'
ORDER BY growth_rate DESC
"""

# ============================================================
# Q9: 판매건수 추이 — 수요 강도
# ============================================================
Q9_SALES_TREND = """
SELECT
    `year_month`,
    CASE
        WHEN region_name LIKE '%%Dallas%%' THEN 'Dallas'
        WHEN region_name LIKE '%%Atlanta%%' THEN 'Atlanta'
        WHEN region_name LIKE '%%Phoenix%%' THEN 'Phoenix'
        WHEN region_name LIKE '%%Charlotte%%' THEN 'Charlotte'
    END AS city,
    sales_count
FROM us_metro_demand
WHERE region_name NOT LIKE '%%United States%%'
  AND sales_count IS NOT NULL
ORDER BY city, `year_month`
"""

# ============================================================
# Q10: 대구 인구유출 vs 미국 인구유입 — 방향 효과 대조표
# ============================================================
Q10_DIRECTION_CONTRAST = """
SELECT
    city_name,
    country,
    year,
    pop_change_rate,
    zhvi_change_rate,
    avg_market_temp,
    CASE
        WHEN pop_change_rate > 0 AND zhvi_change_rate > 0 THEN '인구유입+가격상승'
        WHEN pop_change_rate > 0 AND zhvi_change_rate <= 0 THEN '인구유입+가격하락'
        WHEN pop_change_rate <= 0 AND zhvi_change_rate > 0 THEN '인구유출+가격상승'
        WHEN pop_change_rate <= 0 AND zhvi_change_rate <= 0 THEN '인구유출+가격하락'
    END AS pattern
FROM annual_pop_housing_merged
WHERE pop_change_rate IS NOT NULL
  AND zhvi_change_rate IS NOT NULL
ORDER BY city_name, year
"""


def run_all_queries():
    queries = {
        'S2_Q1_MARKET_TEMP': Q1_MARKET_TEMP,
        'S2_Q2_SUPPLY_DEMAND': Q2_SUPPLY_DEMAND,
        'S2_Q3_DAEGU_POP': Q3_DAEGU_POP,
        'S2_Q4_POP_HOUSING': Q4_POP_HOUSING,
        'S2_Q5_CORRELATION': Q5_CORRELATION,
        'S2_Q6_INCOME_NEEDED': Q6_INCOME_NEEDED,
        'S2_Q7_COUNTY_COMPARE': Q7_COUNTY_COMPARE,
        'S2_Q8_GLOBAL_POP': Q8_GLOBAL_POP,
        'S2_Q9_SALES_TREND': Q9_SALES_TREND,
        'S2_Q10_DIRECTION_CONTRAST': Q10_DIRECTION_CONTRAST,
    }

    for name, sql in queries.items():
        print(f"\n{'='*60}")
        print(f"[QUERY] {name}")
        print('='*60)
        try:
            df = query_to_df(sql)
            print(df.head(10).to_string(index=False))
            print(f"... 총 {len(df)}행")
            csv_path = os.path.join(S2_OUTPUT_DIR, f'{name}.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"   -> {csv_path}")
        except Exception as e:
            print(f"   [ERROR] {e}")


if __name__ == '__main__':
    run_all_queries()
    print("\n[DONE] S2 STEP 8 완료")
