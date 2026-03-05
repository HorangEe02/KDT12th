"""
STEP 2: C3-1 Berkeley Earth → climate_monthly_berkeley (대구+미국4도시 필터)
실행: python src/subtopic3/s3_step2_load_climate_berkeley.py

원본 열: dt, AverageTemperature, AverageTemperatureUncertainty, City, Country, Latitude, Longitude
"""
import pandas as pd
from s3_step0_config import (
    get_connection, DB_NAME, safe_val,
    S3_DATA_FILES, TARGET_CITIES_BERKELEY,
)


def load_berkeley_earth():
    csv_path = S3_DATA_FILES['BERKELEY_EARTH']
    import os
    if not os.path.exists(csv_path):
        print(f"[WARN] C3-1 Berkeley Earth 파일 미발견: {csv_path}")
        return

    print(f"\n[INFO] C3-1 Berkeley Earth 로딩: {csv_path}")

    target_lower = set(c.lower() for c in TARGET_CITIES_BERKELEY)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO climate_monthly_berkeley
             (dt, year, month, city, country, avg_temp, avg_temp_uncertainty, latitude, longitude)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        mask = chunk['City'].str.lower().isin(target_lower)
        chunk = chunk[mask]

        if chunk.empty:
            continue

        rows = []
        for _, r in chunk.iterrows():
            dt = r.get('dt')
            year = int(str(dt)[:4]) if pd.notna(dt) and len(str(dt)) >= 4 else None
            month = int(str(dt)[5:7]) if pd.notna(dt) and len(str(dt)) >= 7 else None

            rows.append((
                safe_val(dt), year, month,
                safe_val(r.get('City')), safe_val(r.get('Country')),
                float(r['AverageTemperature']) if pd.notna(r.get('AverageTemperature')) else None,
                float(r['AverageTemperatureUncertainty']) if pd.notna(r.get('AverageTemperatureUncertainty')) else None,
                safe_val(r.get('Latitude')), safe_val(r.get('Longitude')),
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 10000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   [OK] climate_monthly_berkeley 적재: {total}행")

    # 적재 확인
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql("""
        SELECT city, country, COUNT(*) AS months,
               MIN(dt) AS from_dt, MAX(dt) AS to_dt,
               ROUND(AVG(avg_temp),1) AS mean_temp
        FROM climate_monthly_berkeley
        GROUP BY city, country
    """, conn)
    conn.close()
    print("\n[INFO] 적재 현황:")
    print(df.to_string(index=False))


if __name__ == '__main__':
    load_berkeley_earth()
    print("\n[DONE] S3 STEP 2 완료")
