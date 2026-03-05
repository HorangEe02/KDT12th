"""
STEP 4: C3-5 US Weather Events 2016-2022 → us_weather_events (폭염·혹한 중심)
실행: python src/subtopic3/s3_step4_load_us_weather_events.py

원본 열: EventId, Type, Severity, StartTime(UTC), EndTime(UTC), Precipitation(in),
         TimeZone, AirportCode, LocationLat, LocationLng, City, County, State, ZipCode
1.08GB, 8.6M행 → 4개 주(TX/GA/AZ/NC) + Heat/Cold 이벤트만 필터
"""
import pandas as pd
import os
from s3_step0_config import (
    get_connection, DB_NAME, safe_val,
    S3_DATA_FILES, TARGET_STATES,
)

TARGET_EVENT_TYPES = {'Heat', 'Cold', 'Severe-Cold', 'Extreme-Cold',
                      'heat', 'cold', 'Heatwave', 'Extreme Heat'}

# 열 이름 매핑 후보
COL_CANDIDATES = {
    'event_id': ['EventId', 'event_id', 'EventID'],
    'event_type': ['Type', 'EventType', 'event_type', 'type'],
    'severity': ['Severity', 'severity'],
    'start_time': ['StartTime(UTC)', 'StartTime', 'start_time'],
    'end_time': ['EndTime(UTC)', 'EndTime', 'end_time'],
    'city': ['City', 'city'],
    'county': ['County', 'county'],
    'state': ['State', 'state'],
    'zip_code': ['ZipCode', 'zip_code', 'Zipcode'],
    'latitude': ['LocationLat', 'Latitude', 'latitude'],
    'longitude': ['LocationLng', 'Longitude', 'longitude'],
    'airport_code': ['AirportCode', 'airport_code'],
}


def resolve_col(cols, target_key):
    for c in COL_CANDIDATES.get(target_key, []):
        if c in cols:
            return c
    return None


def load_weather_events():
    csv_path = S3_DATA_FILES['WEATHER_EVENTS']
    if not os.path.exists(csv_path):
        print(f"[WARN] C3-5 US Weather Events 미발견: {csv_path}")
        return

    print(f"\n[INFO] C3-5 US Weather Events 로딩: {csv_path}")
    print("   [INFO] 대용량 (1.08GB) — 4개 주 + Heat/Cold 필터 적용")

    df_sample = pd.read_csv(csv_path, nrows=5)
    print(f"   열: {df_sample.columns.tolist()}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    total = 0

    sql = """INSERT INTO us_weather_events
             (event_id, event_type, severity, start_time, end_time,
              city, county, state, zip_code, latitude, longitude, airport_code)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    for chunk in pd.read_csv(csv_path, chunksize=50000, low_memory=False):
        cols = chunk.columns.tolist()

        # 주 필터
        state_c = resolve_col(cols, 'state')
        if state_c:
            chunk = chunk[chunk[state_c].isin(TARGET_STATES)]

        # 이벤트 타입 필터 (Cold/Snow/Storm — 극한 기상)
        # 참고: 이 데이터셋에는 Heat 타입 없음, Cold가 극한 기상 대표 지표
        type_c = resolve_col(cols, 'event_type')
        if type_c:
            chunk = chunk[chunk[type_c].str.lower().str.contains('cold|snow|storm|hail', na=False)]

        if chunk.empty:
            continue

        rows = []
        for _, r in chunk.iterrows():
            zc = r.get(resolve_col(cols, 'zip_code'))
            zip_str = str(int(zc))[:10] if pd.notna(zc) else None

            rows.append((
                safe_val(r.get(resolve_col(cols, 'event_id'))),
                safe_val(r.get(resolve_col(cols, 'event_type'))),
                safe_val(r.get(resolve_col(cols, 'severity'))),
                safe_val(r.get(resolve_col(cols, 'start_time'))),
                safe_val(r.get(resolve_col(cols, 'end_time'))),
                safe_val(r.get(resolve_col(cols, 'city'))),
                safe_val(r.get(resolve_col(cols, 'county'))),
                safe_val(r.get(resolve_col(cols, 'state'))),
                zip_str,
                safe_val(r.get(resolve_col(cols, 'latitude'))),
                safe_val(r.get(resolve_col(cols, 'longitude'))),
                safe_val(r.get(resolve_col(cols, 'airport_code'))),
            ))

        if rows:
            cursor.executemany(sql, rows)
            conn.commit()
            total += len(rows)
            if total % 20000 == 0:
                print(f"   ... {total}행")

    conn.close()
    print(f"   [OK] us_weather_events 적재: {total}행")

    # 확인
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql("""
        SELECT state, event_type, COUNT(*) AS cnt
        FROM us_weather_events
        GROUP BY state, event_type
        ORDER BY state, cnt DESC
    """, conn)
    conn.close()
    print("\n[INFO] 이벤트 현황:")
    print(df.to_string(index=False))


if __name__ == '__main__':
    load_weather_events()
    print("\n[DONE] S3 STEP 4 완료")
