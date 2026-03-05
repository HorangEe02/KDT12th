"""
STEP 8: 소주제3 분석 SQL 쿼리 모음 (10개 → CSV)
실행: python src/subtopic3/s3_step8_analysis_queries.py
"""
import pandas as pd
import os
from s3_step0_config import get_connection, DB_NAME, S3_OUTPUT_DIR


def query_to_df(sql):
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============================================================
# Q1: 도시별 기후 프로파일 비교
# ============================================================
Q1_CLIMATE_PROFILE = """
SELECT city_name, country, climate_type,
       annual_avg_temp, summer_avg_temp, winter_avg_temp,
       temp_range, heatwave_days_avg, extreme_hot_days
FROM city_climate_profile
ORDER BY summer_avg_temp DESC
"""

# ============================================================
# Q2: 월별 기온 패턴 비교 (5도시 1~12월)
# ============================================================
Q2_MONTHLY_PATTERN = """
SELECT city, month,
       ROUND(AVG(avg_temp), 2) AS avg_temp,
       ROUND(MIN(avg_temp), 2) AS min_temp,
       ROUND(MAX(avg_temp), 2) AS max_temp
FROM climate_monthly_berkeley
WHERE year >= 2000 AND avg_temp IS NOT NULL
GROUP BY city, month
ORDER BY city, month
"""

# ============================================================
# Q3: 기온 장기 트렌드 (온난화 확인)
# ============================================================
Q3_WARMING_TREND = """
SELECT city,
       FLOOR(year / 10) * 10 AS decade,
       ROUND(AVG(avg_temp), 2) AS decade_avg_temp,
       ROUND(AVG(CASE WHEN month IN (6,7,8) THEN avg_temp END), 2) AS decade_summer
FROM climate_monthly_berkeley
WHERE year >= 1900 AND avg_temp IS NOT NULL
GROUP BY city, FLOOR(year / 10) * 10
ORDER BY city, decade
"""

# ============================================================
# Q4: 대구 구별 가격 순위 + 프리미엄
# ============================================================
Q4_DAEGU_DISTRICT_RANK = """
SELECT district, avg_price, median_price, avg_price_per_m2,
       transaction_count, price_rank, premium_vs_avg
FROM daegu_district_climate_prices
ORDER BY price_rank
"""

# ============================================================
# Q5: 미국 도시별 ZIP 가격 분포 통계
# ============================================================
Q5_ZIP_PRICE_DISTRIBUTION = """
SELECT
    c.city_name,
    COUNT(z.zip_code) AS zip_count,
    ROUND(AVG(z.avg_price), 0) AS city_avg,
    ROUND(MIN(z.avg_price), 0) AS cheapest_zip,
    ROUND(MAX(z.avg_price), 0) AS priciest_zip,
    ROUND(MAX(z.avg_price) / NULLIF(MIN(z.avg_price), 0), 1) AS price_gap_ratio,
    ROUND(STDDEV(z.avg_price), 0) AS price_stddev
FROM us_zip_realtor_summary z
JOIN cities c ON z.city_id = c.city_id
GROUP BY c.city_name
ORDER BY price_gap_ratio DESC
"""

# ============================================================
# Q6: 가격 등급별 평균 — 기후 교차
# ============================================================
Q6_TIER_COMPARISON = """
SELECT
    city_name, region_type,
    price_tier,
    COUNT(*) AS zone_count,
    ROUND(AVG(avg_price), 0) AS tier_avg_price,
    ROUND(AVG(price_per_unit), 2) AS tier_avg_per_unit,
    ROUND(AVG(heatwave_events), 1) AS avg_heatwave_events
FROM climate_price_merged
WHERE avg_price IS NOT NULL
GROUP BY city_name, region_type, price_tier
ORDER BY city_name, price_tier DESC
"""

# ============================================================
# Q7: Phoenix ZIP 폭염이벤트 상위 vs 하위 가격 비교
# ============================================================
Q7_PHOENIX_HEAT_PRICE = """
SELECT
    CASE
        WHEN heatwave_events >= 10 THEN '다발 ZIP (10+ events)'
        WHEN heatwave_events >= 3 THEN '중간 ZIP (3~9 events)'
        ELSE '소수 ZIP (0~2 events)'
    END AS heat_group,
    COUNT(*) AS zip_count,
    ROUND(AVG(avg_price), 0) AS avg_price,
    ROUND(AVG(price_per_unit), 2) AS avg_per_sqft,
    ROUND(AVG(heatwave_events), 1) AS avg_events
FROM climate_price_merged
WHERE city_name = 'Phoenix' AND region_type = 'zip'
GROUP BY heat_group
ORDER BY avg_events DESC
"""

# ============================================================
# Q8: 대구 수성구 vs 나머지 구 프리미엄 비교
# ============================================================
Q8_SUSEONG_PREMIUM = """
SELECT
    CASE WHEN sub_region = '수성구' THEN '수성구 (쾌적 프리미엄)'
         ELSE '기타 구 평균'
    END AS category,
    ROUND(AVG(avg_price), 0) AS avg_price,
    ROUND(AVG(price_per_unit), 2) AS avg_per_m2,
    COUNT(*) AS district_count
FROM climate_price_merged
WHERE city_name = '대구' AND region_type = 'district'
GROUP BY CASE WHEN sub_region = '수성구' THEN '수성구 (쾌적 프리미엄)' ELSE '기타 구 평균' END
"""

# ============================================================
# Q9: 미국 4개 주 폭염 이벤트 통계 (연도별)
# ============================================================
Q9_HEATWAVE_STATS = """
SELECT
    state,
    event_type,
    YEAR(start_time) AS `year`,
    COUNT(*) AS events,
    COUNT(DISTINCT zip_code) AS affected_zips
FROM us_weather_events
WHERE start_time IS NOT NULL
GROUP BY state, event_type, YEAR(start_time)
ORDER BY state, event_type, `year`
"""

# ============================================================
# Q10: 기후-가격 상관분석 결과
# ============================================================
Q10_CORRELATION = """
SELECT city_name, analysis_type, x_variable, y_variable,
       pearson_r, p_value, significance, interpretation
FROM climate_price_correlation
ORDER BY ABS(pearson_r) DESC
"""


def run_all_queries():
    queries = {
        'S3_Q1_CLIMATE_PROFILE': Q1_CLIMATE_PROFILE,
        'S3_Q2_MONTHLY_PATTERN': Q2_MONTHLY_PATTERN,
        'S3_Q3_WARMING_TREND': Q3_WARMING_TREND,
        'S3_Q4_DAEGU_DISTRICT_RANK': Q4_DAEGU_DISTRICT_RANK,
        'S3_Q5_ZIP_PRICE_DISTRIBUTION': Q5_ZIP_PRICE_DISTRIBUTION,
        'S3_Q6_TIER_COMPARISON': Q6_TIER_COMPARISON,
        'S3_Q7_PHOENIX_HEAT_PRICE': Q7_PHOENIX_HEAT_PRICE,
        'S3_Q8_SUSEONG_PREMIUM': Q8_SUSEONG_PREMIUM,
        'S3_Q9_HEATWAVE_STATS': Q9_HEATWAVE_STATS,
        'S3_Q10_CORRELATION': Q10_CORRELATION,
    }

    for name, sql in queries.items():
        print(f"\n{'='*60}\n[QUERY] {name}\n{'='*60}")
        try:
            df = query_to_df(sql)
            print(df.head(15).to_string(index=False))
            print(f"... 총 {len(df)}행")
            df.to_csv(os.path.join(S3_OUTPUT_DIR, f'{name}.csv'),
                      index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"   [ERROR] {e}")


if __name__ == '__main__':
    run_all_queries()
    print(f"\n[DONE] S3 STEP 8 완료 -> {S3_OUTPUT_DIR}")
