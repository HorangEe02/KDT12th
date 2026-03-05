"""
STEP 6: G2-1 World Population Growth Rate by Cities 2024 → world_city_population_growth
실행: python src/subtopic2/s2_step6_load_global_population.py

실제 파일명: Wprld population growth rate by cities 2024.csv
실제 컬럼: City, Country, Continent, Population (2024), Population (2023), Growth Rate
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from s2_step0_config import (
    get_connection, DB_NAME, safe_val,
    S2_DATA_FILES, TARGET_GLOBAL_CITIES,
)


def load_world_population_growth():
    """G2-1: World Population Growth Rate by Cities 2024"""
    csv_path = S2_DATA_FILES['WORLD_POP_GROWTH']

    if not os.path.exists(csv_path):
        print(f"  [WARN] G2-1 파일 없음: {csv_path}")
        return

    print(f"\n[LOAD] G2-1: {os.path.basename(csv_path)}")

    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   컬럼: {df.columns.tolist()}")
    print(f"   크기: {df.shape}")

    # 컬럼 매핑
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl == 'city':
            col_map[c] = 'city_name'
        elif cl == 'country':
            col_map[c] = 'country'
        elif cl == 'continent':
            col_map[c] = 'continent'
        elif '2024' in cl and 'pop' in cl:
            col_map[c] = 'population_2024'
        elif '2023' in cl and 'pop' in cl:
            col_map[c] = 'population_2023'
        elif 'growth' in cl or 'rate' in cl:
            col_map[c] = 'growth_rate'

    df = df.rename(columns=col_map)
    print(f"   매핑 후 컬럼: {df.columns.tolist()}")

    # 타겟 도시 필터 (부분 매칭)
    if 'city_name' in df.columns:
        keywords = [c.lower() for c in TARGET_GLOBAL_CITIES]
        mask = df['city_name'].str.lower().str.contains('|'.join(keywords), na=False)
        df_target = df[mask].copy()
        print(f"   타겟 도시 필터: {len(df_target)}행")
        print(f"   매칭된 도시: {df_target['city_name'].tolist()}")

        # 타겟이 적으면 전체 적재 (비교용)
        if len(df_target) < 3:
            print("   [INFO] 타겟 도시 부족 - 전체 적재")
            df_target = df
    else:
        df_target = df

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE world_city_population_growth")
    conn.commit()

    sql = """INSERT INTO world_city_population_growth
             (city_name, country, continent, population_2023, population_2024,
              growth_rate, rank_global, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for idx, (_, r) in enumerate(df_target.iterrows()):
        # population 값 클리닝 (콤마, 문자 제거)
        def clean_pop(v):
            if pd.isna(v):
                return None
            try:
                s = str(v).replace(',', '').replace(' ', '')
                return int(float(s))
            except (ValueError, TypeError):
                return None

        def clean_rate(v):
            if pd.isna(v):
                return None
            try:
                s = str(v).replace('%', '').replace(',', '').strip()
                return float(s)
            except (ValueError, TypeError):
                return None

        rows.append((
            safe_val(r.get('city_name')),
            safe_val(r.get('country')),
            safe_val(r.get('continent')),
            clean_pop(r.get('population_2023')),
            clean_pop(r.get('population_2024')),
            clean_rate(r.get('growth_rate')),
            idx + 1,  # rank
            'G2-1 World Pop Growth 2024',
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   [OK] world_city_population_growth: {len(rows)}행")


if __name__ == '__main__':
    load_world_population_growth()
    print("\n[DONE] S2 STEP 6 완료")
