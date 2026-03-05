"""
STEP 6: 소주제1 분석 SQL 쿼리 모음
실행: python src/subtopic1/step6_analysis_queries.py

10개 분석 쿼리 실행 -> CSV 저장
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from step0_init_db import get_connection, DB_NAME, OUTPUT_DIR


def query_to_df(sql):
    """SQL -> DataFrame"""
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============================================================
# Q1: ZHVI 장기 추이 (2000~2025) - 4개 MSA + 전국
# ============================================================
Q1_ZHVI_TREND = """
SELECT
    `year_month`,
    region_name,
    zhvi
FROM us_metro_zhvi
WHERE region_name IN (
    'Dallas, TX',
    'Atlanta, GA',
    'Phoenix, AZ',
    'Charlotte, NC',
    'United States'
)
ORDER BY region_name, `year_month`
"""

# ============================================================
# Q2: ZHVI 전년동기 대비 변동률 (YoY%)
# ============================================================
Q2_ZHVI_YOY = """
SELECT
    a.`year_month`,
    a.region_name,
    a.zhvi AS current_zhvi,
    b.zhvi AS prev_year_zhvi,
    ROUND((a.zhvi - b.zhvi) / b.zhvi * 100, 2) AS yoy_pct
FROM us_metro_zhvi a
LEFT JOIN us_metro_zhvi b
    ON a.region_name = b.region_name
    AND CONCAT(CAST(SUBSTRING(a.`year_month`, 1, 4) AS UNSIGNED) - 1,
               SUBSTRING(a.`year_month`, 5)) = b.`year_month`
WHERE a.region_name != 'United States'
  AND b.zhvi IS NOT NULL
ORDER BY a.region_name, a.`year_month`
"""

# ============================================================
# Q3: ZORI 임대료 추이 (2015~2025)
# ============================================================
Q3_ZORI_TREND = """
SELECT
    `year_month`,
    region_name,
    zori
FROM us_metro_zori
WHERE region_name IN (
    'Dallas, TX',
    'Atlanta, GA',
    'Phoenix, AZ',
    'Charlotte, NC',
    'United States'
)
ORDER BY region_name, `year_month`
"""

# ============================================================
# Q4: PriceToRentRatio 비교 (Zillow Economics)
# ============================================================
Q4_PRICE_TO_RENT = """
SELECT
    date,
    region_name,
    region_level,
    price_to_rent_ratio,
    zhvi_all,
    zri_all
FROM zillow_economics_ts
WHERE region_level = 'state'
  AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
  AND price_to_rent_ratio IS NOT NULL
ORDER BY region_name, date
"""

# ============================================================
# Q5: 대구 구별 평균가 추이
# ============================================================
Q5_DAEGU_DISTRICT = """
SELECT
    `year_month`,
    district,
    avg_price,
    median_price,
    transaction_count,
    avg_price_per_m2,
    yoy_change_rate
FROM daegu_monthly_summary
ORDER BY district, `year_month`
"""

# ============================================================
# Q6: 대구 vs 미국 4도시 - 가격 변동률 비교 (정규화)
# ============================================================
Q6_CROSS_COMPARISON = """
SELECT
    LEFT(`year_month`, 4) AS year,
    '대구' AS city,
    ROUND(AVG(median_price)) AS annual_median_price,
    'KRW_10K' AS currency
FROM daegu_monthly_summary
WHERE district IS NOT NULL
GROUP BY LEFT(`year_month`, 4)

UNION ALL

SELECT
    LEFT(`year_month`, 4) AS year,
    CASE
        WHEN region_name LIKE '%Dallas%' THEN 'Dallas'
        WHEN region_name LIKE '%Atlanta%' THEN 'Atlanta'
        WHEN region_name LIKE '%Phoenix%' THEN 'Phoenix'
        WHEN region_name LIKE '%Charlotte%' THEN 'Charlotte'
    END AS city,
    ROUND(AVG(zhvi)) AS annual_median_price,
    'USD' AS currency
FROM us_metro_zhvi
WHERE region_name != 'United States'
GROUP BY LEFT(`year_month`, 4), city

ORDER BY city, year
"""

# ============================================================
# Q7: COVID 전후 급등 분석 (2019 vs 2021 비교)
# ============================================================
Q7_COVID_IMPACT = """
SELECT
    region_name,
    MAX(CASE WHEN `year_month` = '2019-12' THEN zhvi END) AS pre_covid,
    MAX(CASE WHEN `year_month` = '2021-12' THEN zhvi END) AS post_covid,
    ROUND(
        (MAX(CASE WHEN `year_month` = '2021-12' THEN zhvi END)
       - MAX(CASE WHEN `year_month` = '2019-12' THEN zhvi END))
       / MAX(CASE WHEN `year_month` = '2019-12' THEN zhvi END) * 100, 2
    ) AS covid_surge_pct
FROM us_metro_zhvi
WHERE region_name != 'United States'
  AND `year_month` IN ('2019-12', '2021-12')
GROUP BY region_name
"""

# ============================================================
# Q8: 가격 인하 매물 비율 추이 (2020~)
# ============================================================
Q8_PRICE_REDUCTION = """
SELECT
    date,
    region_name,
    region_level,
    pct_price_reduction,
    median_pct_price_reduction
FROM zillow_economics_ts
WHERE region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
  AND pct_price_reduction IS NOT NULL
ORDER BY region_name, date
"""

# ============================================================
# Q9: Realtor.com 매물 기본 통계 (4개 도시)
# ============================================================
Q9_REALTOR_STATS = """
SELECT
    c.city_name,
    COUNT(*) AS total_listings,
    ROUND(AVG(r.price), 0) AS avg_price,
    ROUND(AVG(r.house_size), 0) AS avg_sqft,
    ROUND(AVG(r.bed), 1) AS avg_bed,
    ROUND(AVG(r.bath), 1) AS avg_bath,
    ROUND(AVG(CASE WHEN r.house_size > 0 THEN r.price / r.house_size END), 2) AS avg_price_per_sqft
FROM us_realtor_listings r
JOIN cities c ON r.city_id = c.city_id
WHERE r.price > 0
GROUP BY c.city_name
"""

# ============================================================
# Q10: 예측 성장률 (ZHVF)
# ============================================================
Q10_FORECAST = """
SELECT
    region_name,
    base_date,
    forecast_date,
    growth_rate
FROM us_metro_zhvf_growth
ORDER BY region_name, forecast_date
"""


# ── 실행 ──
if __name__ == '__main__':
    queries = {
        'Q1_ZHVI_TREND': Q1_ZHVI_TREND,
        'Q2_ZHVI_YOY': Q2_ZHVI_YOY,
        'Q3_ZORI_TREND': Q3_ZORI_TREND,
        'Q4_PRICE_TO_RENT': Q4_PRICE_TO_RENT,
        'Q5_DAEGU_DISTRICT': Q5_DAEGU_DISTRICT,
        'Q6_CROSS_COMPARISON': Q6_CROSS_COMPARISON,
        'Q7_COVID_IMPACT': Q7_COVID_IMPACT,
        'Q8_PRICE_REDUCTION': Q8_PRICE_REDUCTION,
        'Q9_REALTOR_STATS': Q9_REALTOR_STATS,
        'Q10_FORECAST': Q10_FORECAST,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for name, sql in queries.items():
        print(f"\n{'='*60}")
        print(f"[QUERY] {name}")
        print(f"{'='*60}")
        try:
            df = query_to_df(sql)
            print(df.head(10).to_string(index=False))
            print(f"... 총 {len(df)}행")

            csv_path = os.path.join(OUTPUT_DIR, f'{name}.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  -> {csv_path}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    print(f"\n[DONE] STEP 6 완료: 분석 쿼리 실행 + CSV 저장 -> {OUTPUT_DIR}")
