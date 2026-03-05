"""
STEP 7: 인구-부동산 상관분석용 통합 테이블 구축 → annual_pop_housing_merged + 피어슨 상관분석
실행: python src/subtopic2/s2_step7_build_correlation.py
의존: 소주제1(us_metro_zhvi, daegu_monthly_summary), S2 step2~6 모든 테이블
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from scipy import stats

from s2_step0_config import get_connection, DB_NAME, safe_val


def build_us_annual_merged():
    """미국 4도시: 인구 + ZHVI + 수급지표 → 연도별 통합"""
    print("\n[BUILD] 미국 연도별 통합 데이터 구축")

    conn = get_connection(DB_NAME, for_pandas=True)

    # A. ZHVI 연평균 (소주제1 us_metro_zhvi 재사용)
    df_zhvi = pd.read_sql("""
        SELECT
            CASE
                WHEN region_name LIKE '%%Dallas%%' THEN 'Dallas'
                WHEN region_name LIKE '%%Atlanta%%' THEN 'Atlanta'
                WHEN region_name LIKE '%%Phoenix%%' THEN 'Phoenix'
                WHEN region_name LIKE '%%Charlotte%%' THEN 'Charlotte'
            END AS city_name,
            LEFT(`year_month`, 4) AS year,
            AVG(zhvi) AS zhvi
        FROM us_metro_zhvi
        WHERE region_name NOT LIKE '%%United States%%'
        GROUP BY city_name, year
        HAVING city_name IS NOT NULL
    """, conn)

    if not df_zhvi.empty:
        df_zhvi['year'] = df_zhvi['year'].astype(int)
        df_zhvi = df_zhvi.sort_values(['city_name', 'year'])
        df_zhvi['zhvi_change_rate'] = df_zhvi.groupby('city_name')['zhvi'].pct_change() * 100
        print(f"   ZHVI: {len(df_zhvi)}행, 도시: {df_zhvi['city_name'].unique()}")
    else:
        print("   [WARN] ZHVI 데이터 없음")

    # B. 수급 지표 연평균 (us_metro_demand)
    df_demand = pd.read_sql("""
        SELECT
            CASE
                WHEN region_name LIKE '%%Dallas%%' THEN 'Dallas'
                WHEN region_name LIKE '%%Atlanta%%' THEN 'Atlanta'
                WHEN region_name LIKE '%%Phoenix%%' THEN 'Phoenix'
                WHEN region_name LIKE '%%Charlotte%%' THEN 'Charlotte'
            END AS city_name,
            LEFT(`year_month`, 4) AS year,
            AVG(sales_count) AS avg_sales_count,
            AVG(inventory) AS avg_inventory,
            AVG(market_temp_index) AS avg_market_temp,
            AVG(mean_days_pending) AS avg_days_pending,
            AVG(income_needed) AS avg_income_needed
        FROM us_metro_demand
        WHERE region_name NOT LIKE '%%United States%%'
        GROUP BY city_name, year
        HAVING city_name IS NOT NULL
    """, conn)

    if not df_demand.empty:
        df_demand['year'] = df_demand['year'].astype(int)
        print(f"   수급: {len(df_demand)}행")
    else:
        print("   [WARN] 수급 데이터 없음")

    # C. 인구 데이터 (US Census)
    df_pop = pd.read_sql("""
        SELECT
            c.city_name,
            d.census_year AS year,
            SUM(d.total_population) AS population,
            AVG(d.median_income) AS median_income,
            AVG(d.unemployment) AS unemployment
        FROM us_census_demographics d
        JOIN cities c ON d.city_id = c.city_id
        WHERE d.city_id IS NOT NULL
        GROUP BY c.city_name, d.census_year
    """, conn)

    if not df_pop.empty:
        print(f"   인구: {len(df_pop)}행")
    else:
        print("   [WARN] Census 인구 데이터 없음")

    conn.close()

    # MERGE
    if df_zhvi.empty:
        return pd.DataFrame()

    merged = df_zhvi.copy()
    if not df_demand.empty:
        merged = merged.merge(df_demand, on=['city_name', 'year'], how='outer')
    if not df_pop.empty:
        merged = merged.merge(df_pop, on=['city_name', 'year'], how='left')

    # 수급 비율
    if 'avg_inventory' in merged.columns and 'avg_sales_count' in merged.columns:
        merged['supply_demand_ratio'] = np.where(
            merged['avg_sales_count'] > 0,
            merged['avg_inventory'] / merged['avg_sales_count'],
            None
        )

    merged['country'] = 'USA'

    print(f"   미국 통합: {len(merged)}행")
    print(f"   도시: {merged['city_name'].unique()}")
    print(f"   연도: {merged['year'].min()} ~ {merged['year'].max()}")

    return merged


def build_kr_annual_merged():
    """대구: 인구 + 주택가격 + 거래건수 → 연도별 통합"""
    print("\n[BUILD] 대구 연도별 통합 데이터 구축")

    conn = get_connection(DB_NAME, for_pandas=True)

    # 인구 (birth/death/natural_increase 기반)
    df_pop = pd.read_sql("""
        SELECT year, birth_count, death_count, natural_increase,
               birth_rate, death_rate, avg_household_income AS median_income
        FROM daegu_population_summary
        ORDER BY year
    """, conn)

    # 주택가격+거래량 (소주제1 daegu_monthly_summary 재사용)
    df_housing = pd.read_sql("""
        SELECT
            t.yr AS year,
            AVG(t.avg_price) AS zhvi,
            SUM(t.transaction_count) AS total_transactions
        FROM (
            SELECT LEFT(`year_month`, 4) AS yr, avg_price, transaction_count
            FROM daegu_monthly_summary
            WHERE district IS NOT NULL
        ) t
        GROUP BY t.yr
    """, conn)

    conn.close()

    if df_pop.empty:
        print("   [WARN] 대구 인구 데이터 없음")
        return pd.DataFrame()

    if not df_housing.empty:
        df_housing['year'] = df_housing['year'].astype(int)

    merged = df_pop.merge(df_housing, on='year', how='left')

    # ZHVI 변동률
    merged = merged.sort_values('year')
    if 'zhvi' in merged.columns:
        merged['zhvi_change_rate'] = merged['zhvi'].pct_change() * 100

    # 월평균 거래건수
    if 'total_transactions' in merged.columns:
        merged['avg_sales_count'] = merged['total_transactions'] / 12

    # natural_increase를 pop_change_rate 대용으로 사용
    if 'natural_increase' in merged.columns and 'birth_count' in merged.columns:
        # 자연증감률 = natural_increase / (birth_count + death_count) * 100 (근사치)
        total = merged['birth_count'].fillna(0) + merged['death_count'].fillna(0)
        merged['pop_change_rate'] = np.where(
            total > 0,
            merged['natural_increase'] / total * 100,
            None
        )

    merged['city_name'] = '대구'
    merged['country'] = 'South Korea'
    merged['population'] = None  # total_population 없음

    print(f"   대구 통합: {len(merged)}행")

    return merged


def save_merged_to_db(df):
    """통합 데이터 → annual_pop_housing_merged 적재"""
    if df.empty:
        return

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE annual_pop_housing_merged")
    conn.commit()

    sql = """INSERT INTO annual_pop_housing_merged
             (city_name, country, year, population, pop_change_rate,
              median_income, zhvi, zhvi_change_rate,
              avg_sales_count, avg_inventory, avg_market_temp,
              avg_days_pending, avg_income_needed, supply_demand_ratio)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_val(r.get('city_name')),
            safe_val(r.get('country')),
            safe_val(int(r['year'])),
            safe_val(int(r['population'])) if pd.notna(r.get('population')) else None,
            safe_val(float(r['pop_change_rate'])) if pd.notna(r.get('pop_change_rate')) else None,
            safe_val(float(r['median_income'])) if pd.notna(r.get('median_income')) else None,
            safe_val(float(r['zhvi'])) if pd.notna(r.get('zhvi')) else None,
            safe_val(float(r['zhvi_change_rate'])) if pd.notna(r.get('zhvi_change_rate')) else None,
            safe_val(float(r['avg_sales_count'])) if pd.notna(r.get('avg_sales_count')) else None,
            safe_val(float(r['avg_inventory'])) if pd.notna(r.get('avg_inventory')) else None,
            safe_val(float(r['avg_market_temp'])) if pd.notna(r.get('avg_market_temp')) else None,
            safe_val(float(r['avg_days_pending'])) if pd.notna(r.get('avg_days_pending')) else None,
            safe_val(float(r['avg_income_needed'])) if pd.notna(r.get('avg_income_needed')) else None,
            safe_val(float(r['supply_demand_ratio'])) if pd.notna(r.get('supply_demand_ratio')) else None,
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"\n[OK] annual_pop_housing_merged 적재: {len(rows)}행")


def compute_correlations(df):
    """상관분석 수행 → population_housing_correlation"""
    print("\n[CORR] 상관분석 수행")

    results = []

    pairs = [
        ('pop_change_rate', 'zhvi_change_rate', '인구변동률 vs ZHVI변동률'),
        ('pop_change_rate', 'avg_sales_count', '인구변동률 vs 판매건수'),
        ('pop_change_rate', 'avg_market_temp', '인구변동률 vs 시장온도'),
        ('pop_change_rate', 'avg_days_pending', '인구변동률 vs 대기일수'),
        ('pop_change_rate', 'supply_demand_ratio', '인구변동률 vs 수급비율'),
        ('population', 'zhvi', '총인구 vs ZHVI'),
        ('median_income', 'zhvi', '중위소득 vs ZHVI'),
        ('median_income', 'avg_income_needed', '중위소득 vs 필요소득'),
    ]

    for city in df['city_name'].unique():
        city_df = df[df['city_name'] == city]
        country = city_df['country'].iloc[0] if not city_df.empty else ''
        period = f"{int(city_df['year'].min())}-{int(city_df['year'].max())}" if not city_df.empty else ''

        for x_var, y_var, desc in pairs:
            if x_var not in city_df.columns or y_var not in city_df.columns:
                continue

            sub = city_df[[x_var, y_var]].dropna()
            # float 변환
            try:
                sub = sub.astype(float)
            except (ValueError, TypeError):
                continue

            if len(sub) < 3:
                continue

            try:
                r, p = stats.pearsonr(sub[x_var], sub[y_var])
            except Exception:
                continue

            sig = ''
            if p < 0.001:
                sig = '***'
            elif p < 0.01:
                sig = '**'
            elif p < 0.05:
                sig = '*'

            direction = '양의' if r > 0 else '음의'
            strength = '강한' if abs(r) > 0.7 else '보통' if abs(r) > 0.4 else '약한'

            results.append({
                'city_name': city, 'country': country,
                'analysis_period': period,
                'x_variable': x_var, 'y_variable': y_var,
                'pearson_r': round(r, 4), 'p_value': round(p, 8),
                'n_observations': len(sub), 'significance': sig,
                'interpretation': f'{desc}: {strength} {direction} 상관 (r={r:.3f})',
            })

    if not results:
        print("   [WARN] 상관분석 결과 없음")
        return

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE population_housing_correlation")
    conn.commit()

    sql = """INSERT INTO population_housing_correlation
             (city_name, country, analysis_period,
              x_variable, y_variable, pearson_r, p_value,
              n_observations, significance, interpretation)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = [tuple(r.values()) for r in results]
    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()

    print(f"   [OK] 상관분석 결과: {len(results)}건")
    for res in results:
        print(f"      {res['city_name']:10s} | {res['x_variable']:25s} -> {res['y_variable']:25s} | "
              f"r={res['pearson_r']:+.3f} {res['significance']}")


if __name__ == '__main__':
    df_us = build_us_annual_merged()
    df_kr = build_kr_annual_merged()

    dfs = [d for d in [df_us, df_kr] if not d.empty]
    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)
        save_merged_to_db(df_all)
        compute_correlations(df_all)
    else:
        print("[WARN] 통합 데이터 없음")

    print("\n[DONE] S2 STEP 7 완료")
