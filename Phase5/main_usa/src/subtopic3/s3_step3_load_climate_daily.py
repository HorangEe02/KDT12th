"""
STEP 3: C3-2 Daily Temperature + C3-4 Monthly Mean Temp → climate_daily_cities
실행: python src/subtopic3/s3_step3_load_climate_daily.py

C3-2 (city_temperature.csv): Region, Country, State, City, Month, Day, Year, AvgTemperature (℉)
C3-4 (US_City_Temp_Data.csv): Wide 형식 — time, dallas, atlanta, phoenix, charlotte, ... (℃)
"""
import pandas as pd
import numpy as np
from s3_step0_config import (
    get_connection, DB_NAME, safe_val,
    S3_DATA_FILES, TARGET_CITIES_DAILY, TARGET_CITY_COLS_WIDE,
    TARGET_COUNTRIES, TARGET_STATES_US,
)
import os


def load_daily_temperature():
    """C3-2: city_temperature.csv (화씨, 일별)"""
    csv_path = S3_DATA_FILES['CITY_TEMP_DAILY']
    if not os.path.exists(csv_path):
        print(f"[WARN] C3-2 Daily Temperature 파일 미발견: {csv_path}")
        return

    print(f"\n[INFO] C3-2 Daily Temperature 로딩: {csv_path}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO climate_daily_cities
             (date, year, month, city, country, state,
              avg_temp_celsius, avg_temp_fahrenheit, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    total = 0

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        chunk.columns = [c.strip() for c in chunk.columns]

        # 열 이름 탐색
        city_col = next((c for c in chunk.columns if c.lower() == 'city'), None)
        country_col = next((c for c in chunk.columns if c.lower() in ('country', 'region')), None)
        state_col = next((c for c in chunk.columns if c.lower() == 'state'), None)

        if city_col is None:
            print("   [WARN] City 열 없음")
            break

        # 타겟 도시 필터
        mask = chunk[city_col].str.lower().isin(TARGET_CITIES_DAILY)
        chunk = chunk[mask]

        if chunk.empty:
            continue

        year_col = next((c for c in chunk.columns if c.lower() == 'year'), None)
        month_col = next((c for c in chunk.columns if c.lower() == 'month'), None)
        day_col = next((c for c in chunk.columns if c.lower() == 'day'), None)
        temp_col = next((c for c in chunk.columns if 'avgtemp' in c.lower() or 'average' in c.lower()), None)

        rows = []
        for _, r in chunk.iterrows():
            year = int(r[year_col]) if year_col and pd.notna(r.get(year_col)) else None
            month = int(r[month_col]) if month_col and pd.notna(r.get(month_col)) else None
            day = int(r[day_col]) if day_col and pd.notna(r.get(day_col)) else None

            try:
                date_str = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}" if year and month and day else None
            except Exception:
                date_str = None

            temp_f = float(r[temp_col]) if temp_col and pd.notna(r.get(temp_col)) else None
            # 이상치 제거 (-99℉ 등)
            if temp_f is not None and (temp_f < -60 or temp_f > 150):
                temp_f = None

            temp_c = round((temp_f - 32) * 5 / 9, 2) if temp_f is not None else None

            rows.append((
                date_str, year, month,
                safe_val(r.get(city_col)), safe_val(r.get(country_col)), safe_val(r.get(state_col)),
                temp_c, temp_f,
                'C3-2 Daily Temperature',
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 50000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   [OK] climate_daily_cities (C3-2): {total}행")


def load_monthly_mean_temp():
    """C3-4: US_City_Temp_Data.csv — Wide 형식 (도시=열, time=행, 섭씨)
    Wide → Long 변환: melt()로 타겟 4도시 열만 추출, day=15
    """
    csv_path = S3_DATA_FILES['US_CITY_TEMP_MONTHLY']
    if not os.path.exists(csv_path):
        print(f"\n[WARN] C3-4 Monthly Mean Temp 미발견: {csv_path}")
        return

    print(f"\n[INFO] C3-4 Monthly Mean Temp 로딩: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   열: {df.columns.tolist()[:10]}... ({len(df.columns)}개)")
    print(f"   행수: {len(df)}")

    # Wide → Long 변환: 'time' 열 + 타겟 도시 열만 추출
    avail_cols = ['time'] + [c for c in TARGET_CITY_COLS_WIDE if c in df.columns]
    if len(avail_cols) <= 1:
        print(f"   [WARN] 타겟 도시 열 없음. 사용 가능 열: {df.columns.tolist()[:20]}")
        return

    df_sub = df[avail_cols].copy()

    # melt: Wide → Long
    df_long = df_sub.melt(id_vars=['time'], var_name='city', value_name='avg_temp_celsius')
    df_long = df_long.dropna(subset=['avg_temp_celsius'])

    # time 파싱 (예: "1948-01-01")
    df_long['time'] = pd.to_datetime(df_long['time'], errors='coerce')
    df_long = df_long.dropna(subset=['time'])
    df_long['year'] = df_long['time'].dt.year
    df_long['month'] = df_long['time'].dt.month

    # 도시 이름을 타이틀 케이스로
    city_name_map = {
        'dallas': 'Dallas', 'atlanta': 'Atlanta',
        'phoenix': 'Phoenix', 'charlotte': 'Charlotte',
    }
    df_long['city'] = df_long['city'].map(city_name_map)

    # 섭씨 → 화씨도 저장
    df_long['avg_temp_fahrenheit'] = (df_long['avg_temp_celsius'] * 9 / 5 + 32).round(2)

    # day=15 (월 중간)
    df_long['date'] = df_long['time'].apply(lambda t: t.replace(day=15))

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO climate_daily_cities
             (date, year, month, city, country, state,
              avg_temp_celsius, avg_temp_fahrenheit, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df_long.iterrows():
        rows.append((
            r['date'].strftime('%Y-%m-%d'),
            int(r['year']), int(r['month']),
            r['city'], 'United States', None,
            safe_val(round(r['avg_temp_celsius'], 2)),
            safe_val(round(r['avg_temp_fahrenheit'], 2)),
            'C3-4 Monthly Mean Temp',
        ))

    if rows:
        batch = 5000
        for i in range(0, len(rows), batch):
            cursor.executemany(sql, rows[i:i+batch])
            conn.commit()

    conn.close()
    print(f"   [OK] climate_daily_cities (C3-4): {len(rows)}행")


if __name__ == '__main__':
    load_daily_temperature()
    load_monthly_mean_temp()
    print("\n[DONE] S3 STEP 3 완료")
