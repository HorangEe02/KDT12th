"""
STEP 7: 기후 프로파일 구축 + 기후-가격 교차분석 + 상관분석
실행: python src/subtopic3/s3_step7_build_climate_price_merged.py
"""
import pandas as pd
import numpy as np
from scipy import stats
from s3_step0_config import (
    get_connection, DB_NAME, safe_val,
    CLIMATE_TYPE_MAP, CITY_ID_NAME_MAP,
)


def build_city_climate_profiles():
    """도시별 기후 프로파일 집계 → city_climate_profile"""
    print("\n[INFO] 도시별 기후 프로파일 구축")
    conn = get_connection(DB_NAME, for_pandas=True)

    # Berkeley Earth: 2000~2013 기준 집계
    df = pd.read_sql("""
        SELECT
            city, country,
            ROUND(AVG(avg_temp), 2) AS annual_avg_temp,
            ROUND(AVG(CASE WHEN month IN (6,7,8) THEN avg_temp END), 2) AS summer_avg_temp,
            ROUND(AVG(CASE WHEN month IN (12,1,2) THEN avg_temp END), 2) AS winter_avg_temp,
            ROUND(MAX(avg_temp), 2) AS summer_max_avg,
            ROUND(MAX(avg_temp) - MIN(avg_temp), 2) AS temp_range
        FROM climate_monthly_berkeley
        WHERE year >= 2000 AND avg_temp IS NOT NULL
        GROUP BY city, country
    """, conn)

    if df.empty:
        print("   [WARN] Berkeley 데이터 없음 - 일별 데이터에서 시도")

    # Daily: 폭염일수 집계 (서브쿼리 패턴 — ONLY_FULL_GROUP_BY 대응)
    df_heat = pd.read_sql("""
        SELECT
            city,
            ROUND(AVG(heat_days), 0) AS heatwave_days_avg,
            ROUND(AVG(extreme_days), 0) AS extreme_hot_days
        FROM (
            SELECT
                city,
                year,
                SUM(CASE WHEN avg_temp_celsius >= 35 THEN 1 ELSE 0 END) AS heat_days,
                SUM(CASE WHEN avg_temp_celsius >= 38 THEN 1 ELSE 0 END) AS extreme_days
            FROM climate_daily_cities
            WHERE avg_temp_celsius IS NOT NULL
            GROUP BY city, year
        ) sub
        GROUP BY city
    """, conn)

    if not df.empty and not df_heat.empty:
        merged = df.merge(df_heat, on='city', how='left')
    elif not df.empty:
        merged = df.copy()
        merged['heatwave_days_avg'] = None
        merged['extreme_hot_days'] = None
    else:
        print("   [WARN] 기후 데이터 부족")
        conn.close()
        return

    conn.close()

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE city_climate_profile")

    sql = """INSERT INTO city_climate_profile
             (city_name, country, period, annual_avg_temp, summer_avg_temp,
              winter_avg_temp, summer_max_avg, temp_range,
              heatwave_days_avg, extreme_hot_days, climate_type)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for _, r in merged.iterrows():
        cursor.execute(sql, (
            r['city'], r['country'], '2000-2013',
            safe_val(r.get('annual_avg_temp')),
            safe_val(r.get('summer_avg_temp')),
            safe_val(r.get('winter_avg_temp')),
            safe_val(r.get('summer_max_avg')),
            safe_val(r.get('temp_range')),
            int(r['heatwave_days_avg']) if pd.notna(r.get('heatwave_days_avg')) else None,
            int(r['extreme_hot_days']) if pd.notna(r.get('extreme_hot_days')) else None,
            CLIMATE_TYPE_MAP.get(r['city'], '기타'),
        ))

    conn.commit()
    conn.close()
    print(f"   [OK] city_climate_profile: {len(merged)}개 도시")


def build_us_zip_price_tiers():
    """미국 ZIP별 가격 등급 + 폭염 이벤트 수 → climate_price_merged"""
    print("\n[INFO] 미국 ZIP-가격-기후 교차 테이블 구축")
    conn = get_connection(DB_NAME, for_pandas=True)

    # ZIP 가격 (Realtor 기반)
    df_price = pd.read_sql("""
        SELECT z.zip_code, z.city_name, z.state, z.city_id,
               z.avg_price, z.avg_price_per_sqft, z.listing_count
        FROM us_zip_realtor_summary z
        WHERE z.avg_price > 0
    """, conn)

    if df_price.empty:
        print("   [WARN] ZIP 가격 데이터 없음")
        conn.close()
        return

    # ZIP별 극한 기상 이벤트 수 (Cold/Snow/Storm — Heat 이벤트 없음)
    df_heat = pd.read_sql("""
        SELECT zip_code, COUNT(*) AS heatwave_events
        FROM us_weather_events
        WHERE zip_code IS NOT NULL
        GROUP BY zip_code
    """, conn)

    merged = df_price.merge(df_heat, on='zip_code', how='left')
    merged['heatwave_events'] = merged['heatwave_events'].fillna(0).astype(int)

    # 가격 등급 (도시 내 3분위)
    for cid in merged['city_id'].unique():
        mask = merged['city_id'] == cid
        q33 = merged.loc[mask, 'avg_price'].quantile(0.33)
        q66 = merged.loc[mask, 'avg_price'].quantile(0.67)
        merged.loc[mask & (merged['avg_price'] <= q33), 'price_tier'] = 'low'
        merged.loc[mask & (merged['avg_price'] > q33) & (merged['avg_price'] <= q66), 'price_tier'] = 'mid'
        merged.loc[mask & (merged['avg_price'] > q66), 'price_tier'] = 'high'

    # 기온 등급 (폭염 이벤트 기반)
    merged['temp_tier'] = pd.cut(
        merged['heatwave_events'],
        bins=[-1, 0, 5, 999999],
        labels=['cool', 'mild', 'hot']
    )

    # 도시 기후 프로파일에서 여름 평균 기온
    df_climate = pd.read_sql("SELECT city_name, summer_avg_temp, annual_avg_temp FROM city_climate_profile", conn)
    merged['city_label'] = merged['city_id'].map(CITY_ID_NAME_MAP)
    merged = merged.merge(df_climate.rename(columns={'city_name': 'city_label'}),
                           on='city_label', how='left')

    conn.close()

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO climate_price_merged
             (city_name, country, sub_region, region_type,
              avg_price, price_per_unit, summer_avg_temp, annual_avg_temp,
              heatwave_events, price_tier, temp_tier)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in merged.iterrows():
        rows.append((
            safe_val(r.get('city_label')), 'USA', safe_val(r['zip_code']), 'zip',
            safe_val(r['avg_price']), safe_val(r.get('avg_price_per_sqft')),
            safe_val(r.get('summer_avg_temp')), safe_val(r.get('annual_avg_temp')),
            int(r['heatwave_events']),
            safe_val(r.get('price_tier')), str(r.get('temp_tier', '')),
        ))

    if rows:
        batch = 3000
        for i in range(0, len(rows), batch):
            cursor.executemany(sql, rows[i:i+batch])
            conn.commit()

    conn.close()
    print(f"   [OK] climate_price_merged (ZIP): {len(rows)}행")


def build_daegu_district_climate():
    """대구 구별 가격을 climate_price_merged에 추가"""
    print("\n[INFO] 대구 구별 기후-가격 교차 데이터 추가")
    conn = get_connection(DB_NAME, for_pandas=True)

    df = pd.read_sql("SELECT * FROM daegu_district_climate_prices", conn)
    # Berkeley Earth에 Daegu 없음 → Seoul을 한국 대표로 사용
    df_climate = pd.read_sql("""
        SELECT summer_avg_temp, annual_avg_temp
        FROM city_climate_profile
        WHERE city_name IN ('Daegu', 'Taegu', 'Seoul')
        LIMIT 1
    """, conn)
    conn.close()

    summer_temp = float(df_climate['summer_avg_temp'].iloc[0]) if not df_climate.empty else None
    annual_temp = float(df_climate['annual_avg_temp'].iloc[0]) if not df_climate.empty else None

    if df.empty:
        print("   [WARN] 대구 구별 데이터 없음")
        return

    # 가격 등급
    q33 = df['avg_price'].quantile(0.33)
    q66 = df['avg_price'].quantile(0.67)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO climate_price_merged
             (city_name, country, sub_region, region_type,
              avg_price, price_per_unit, summer_avg_temp, annual_avg_temp,
              heatwave_events, price_tier, temp_tier)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        tier = 'low' if r['avg_price'] <= q33 else ('mid' if r['avg_price'] <= q66 else 'high')
        rows.append((
            '대구', 'South Korea', r['district'], 'district',
            safe_val(r['avg_price']),
            safe_val(r.get('avg_price_per_m2')),
            summer_temp, annual_temp,
            None,  # 대구 폭염 이벤트 (Weather Events에 없음)
            tier, 'hot',  # 대구 분지 = hot
        ))

    if rows:
        cursor.executemany(sql, rows)
        conn.commit()

    conn.close()
    print(f"   [OK] climate_price_merged (대구 구): {len(rows)}행")


def compute_climate_price_correlations():
    """기후-가격 상관분석 → climate_price_correlation"""
    print("\n[INFO] 기후-가격 상관분석")
    conn = get_connection(DB_NAME, for_pandas=True)

    df = pd.read_sql("SELECT * FROM climate_price_merged WHERE avg_price IS NOT NULL", conn)

    results = []

    # 도시별: 폭염 이벤트 수 vs 가격
    for city in df[df['region_type'] == 'zip']['city_name'].dropna().unique():
        sub = df[(df['city_name'] == city) & (df['region_type'] == 'zip')].dropna(
            subset=['heatwave_events', 'avg_price']
        )
        if len(sub) < 10:
            continue

        r, p = stats.pearsonr(sub['heatwave_events'].astype(float), sub['avg_price'].astype(float))
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        direction = '양의' if r > 0 else '음의'
        strength = '강한' if abs(r) > 0.5 else '보통' if abs(r) > 0.3 else '약한'

        results.append({
            'city_name': city, 'analysis_type': 'cross-sectional',
            'x_variable': 'heatwave_events (ZIP)',
            'y_variable': 'avg_price',
            'pearson_r': round(r, 4), 'p_value': round(p, 8),
            'n_observations': len(sub), 'significance': sig,
            'interpretation': f'{city} ZIP 폭염이벤트-가격: {strength} {direction} 상관 (r={r:.3f})',
        })

    # 도시간 비교: 여름기온 vs 전체 가격수준
    df_city = pd.read_sql("""
        SELECT cp.city_name, cp.summer_avg_temp,
               AVG(cm.avg_price) AS avg_price_all_zips
        FROM city_climate_profile cp
        LEFT JOIN climate_price_merged cm ON cp.city_name = cm.city_name
        WHERE cm.region_type = 'zip'
        GROUP BY cp.city_name, cp.summer_avg_temp
    """, conn)
    conn.close()

    if len(df_city) >= 3:
        r, p = stats.pearsonr(
            df_city['summer_avg_temp'].astype(float),
            df_city['avg_price_all_zips'].astype(float)
        )
        results.append({
            'city_name': 'ALL', 'analysis_type': 'cross-city',
            'x_variable': 'summer_avg_temp',
            'y_variable': 'avg_zip_price',
            'pearson_r': round(r, 4), 'p_value': round(p, 8),
            'n_observations': len(df_city), 'significance': '*' if p < 0.05 else '',
            'interpretation': f'도시간 여름기온-평균가격 상관 (r={r:.3f})',
        })

    # DB 저장
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE climate_price_correlation")
    sql = """INSERT INTO climate_price_correlation
             (city_name, analysis_type, x_variable, y_variable,
              pearson_r, p_value, n_observations, significance, interpretation)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for res in results:
        cursor.execute(sql, tuple(res.values()))

    conn.commit()
    conn.close()
    print(f"   [OK] 상관분석 결과: {len(results)}건")
    for r in results:
        print(f"      {r['city_name']:10s} | {r['x_variable']:30s} -> r={r['pearson_r']:+.3f} {r['significance']}")


if __name__ == '__main__':
    build_city_climate_profiles()
    build_us_zip_price_tiers()
    build_daegu_district_climate()
    compute_climate_price_correlations()
    print("\n[DONE] S3 STEP 7 완료")
