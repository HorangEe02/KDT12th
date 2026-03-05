"""
STEP 4: Kaggle 한국 인구통계 → korean_demographics + korean_income_welfare + daegu_population_summary
실행: python src/subtopic2/s2_step4_load_kr_demographics.py

데이터:
  K2-1: Korean_demographics_2000-2022.csv
        실제 컬럼: Date, Region, Birth, Birth_rate, Death, Death_rate,
                   Divorce, Divorce_rate, Marriage, Marriage_rate,
                   Natural_growth, Natural_growth_rate
        ** total_population 컬럼 없음 **

  K2-2: Korea Income and Welfare.csv
        실제 컬럼: id, year, wave, region, income, family_member, gender,
                   year_born, education_level, marriage, religion,
                   occupation, company_size, reason_none_worker
        ** 개인 단위 → region+year 그룹핑 필요 **
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from s2_step0_config import (
    get_connection, DB_NAME, safe_val,
    S2_DATA_FILES,
)


def detect_encoding(csv_path):
    for enc in ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr']:
        try:
            pd.read_csv(csv_path, nrows=2, encoding=enc)
            return enc
        except Exception:
            continue
    return 'utf-8'


def load_korean_demographics():
    """K2-1: Korean Demographics 2000-2022"""
    csv_path = S2_DATA_FILES['KR_DEMOGRAPHICS']

    if not os.path.exists(csv_path):
        print(f"  [WARN] K2-1 파일 없음: {csv_path}")
        return

    enc = detect_encoding(csv_path)
    print(f"\n[LOAD] K2-1: {csv_path} (encoding={enc})")

    df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
    print(f"   원본 컬럼: {df.columns.tolist()}")
    print(f"   크기: {df.shape}")

    # Date 컬럼에서 year 추출
    if 'Date' in df.columns:
        df['year'] = pd.to_datetime(df['Date'], errors='coerce').dt.year
    elif 'date' in df.columns:
        df['year'] = pd.to_datetime(df['date'], errors='coerce').dt.year

    # Region 매핑
    region_col = 'Region' if 'Region' in df.columns else 'region'

    # 연도별 Region별 집계 (월별 데이터이므로 연 합산/평균)
    agg_cols = {}
    for c in ['Birth', 'Death', 'Natural_growth', 'Divorce', 'Marriage']:
        if c in df.columns:
            agg_cols[c] = 'sum'
    for c in ['Birth_rate', 'Death_rate', 'Natural_growth_rate',
              'Divorce_rate', 'Marriage_rate']:
        if c in df.columns:
            agg_cols[c] = 'mean'

    if not agg_cols:
        print("  [WARN] 집계할 컬럼 없음")
        return

    df_agg = df.groupby(['year', region_col]).agg(agg_cols).reset_index()
    df_agg = df_agg.rename(columns={region_col: 'region'})
    print(f"   연도별 집계: {df_agg.shape}")
    print(f"   Region 값: {df_agg['region'].unique()[:10]}")

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE korean_demographics")
    conn.commit()

    sql = """INSERT INTO korean_demographics
             (year, region, birth_count, death_count, birth_rate, death_rate,
              natural_increase, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df_agg.iterrows():
        rows.append((
            safe_val(int(r['year'])) if pd.notna(r.get('year')) else None,
            safe_val(r.get('region')),
            safe_val(int(r['Birth'])) if pd.notna(r.get('Birth')) else None,
            safe_val(int(r['Death'])) if pd.notna(r.get('Death')) else None,
            safe_val(float(r['Birth_rate'])) if pd.notna(r.get('Birth_rate')) else None,
            safe_val(float(r['Death_rate'])) if pd.notna(r.get('Death_rate')) else None,
            safe_val(int(r['Natural_growth'])) if pd.notna(r.get('Natural_growth')) else None,
            'K2-1 Korean Demographics 2000-2022',
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   [OK] korean_demographics 적재: {len(rows)}행")


def load_korean_income_welfare():
    """K2-2: Korea Income and Welfare (개인 데이터 → region+year 그룹핑)"""
    csv_path = S2_DATA_FILES['KR_INCOME']

    if not os.path.exists(csv_path):
        print(f"  [WARN] K2-2 파일 없음: {csv_path}")
        return

    enc = detect_encoding(csv_path)
    print(f"\n[LOAD] K2-2: {csv_path} (encoding={enc})")

    df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
    print(f"   원본 컬럼: {df.columns.tolist()}")
    print(f"   크기: {df.shape}")

    # region + year 기준 평균소득 집계
    if 'year' not in df.columns or 'region' not in df.columns or 'income' not in df.columns:
        print("  [WARN] 필수 컬럼(year, region, income) 없음")
        print(f"   사용 가능: {df.columns.tolist()}")
        return

    df_agg = df.groupby(['year', 'region']).agg(
        household_income=('income', 'mean'),
        sample_count=('income', 'count'),
        avg_family_member=('family_member', 'mean'),
    ).reset_index()

    print(f"   집계 결과: {df_agg.shape}")
    print(f"   Region 값: {df_agg['region'].unique()[:10]}")

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE korean_income_welfare")
    conn.commit()

    sql = """INSERT INTO korean_income_welfare
             (year, region, household_income, sample_count, avg_family_member, source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df_agg.iterrows():
        rows.append((
            safe_val(int(r['year'])) if pd.notna(r.get('year')) else None,
            safe_val(r.get('region')),
            safe_val(float(r['household_income'])) if pd.notna(r.get('household_income')) else None,
            safe_val(int(r['sample_count'])) if pd.notna(r.get('sample_count')) else None,
            safe_val(float(r['avg_family_member'])) if pd.notna(r.get('avg_family_member')) else None,
            'K2-2 Korea Income Welfare',
        ))

    batch = 2000
    for i in range(0, len(rows), batch):
        cursor.executemany(sql, rows[i:i+batch])
        conn.commit()

    conn.close()
    print(f"   [OK] korean_income_welfare 적재: {len(rows)}행")


def build_daegu_summary():
    """korean_demographics에서 대구만 추출 → daegu_population_summary"""
    print("\n[BUILD] 대구 인구 요약 생성")

    conn = get_connection(DB_NAME, for_pandas=True)

    # 대구 region 값 확인 (Daegu, 대구, 대구광역시 등)
    df_regions = pd.read_sql("SELECT DISTINCT region FROM korean_demographics LIMIT 50", conn)
    print(f"   사용 가능 region 값: {df_regions['region'].tolist()}")

    # 대구 필터 (다양한 이름 시도)
    df = pd.read_sql("""
        SELECT year, birth_count, death_count, birth_rate, death_rate,
               natural_increase
        FROM korean_demographics
        WHERE region LIKE '%%Daegu%%'
           OR region LIKE '%%대구%%'
           OR region LIKE '%%daegu%%'
        ORDER BY year
    """, conn)

    if df.empty:
        print("   [WARN] 대구 데이터 없음 - region 값 확인 필요")
        conn.close()
        return

    print(f"   대구 데이터: {len(df)}행")

    # 소득 데이터 조인 시도
    df_income = pd.read_sql("""
        SELECT year, household_income
        FROM korean_income_welfare
        WHERE region LIKE '%%Daegu%%'
           OR region LIKE '%%대구%%'
           OR region LIKE '%%daegu%%'
           OR region = 4
           OR region = '4'
    """, conn)

    conn.close()

    # 소득 merge
    if not df_income.empty:
        df = df.merge(df_income, on='year', how='left')
    else:
        df['household_income'] = None

    # MySQL 적재
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE daegu_population_summary")
    conn.commit()

    sql = """INSERT INTO daegu_population_summary
             (year, birth_count, death_count, birth_rate, death_rate,
              natural_increase, avg_household_income)
             VALUES (%s,%s,%s,%s,%s,%s,%s)"""

    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_val(int(r['year'])),
            safe_val(int(r['birth_count'])) if pd.notna(r.get('birth_count')) else None,
            safe_val(int(r['death_count'])) if pd.notna(r.get('death_count')) else None,
            safe_val(float(r['birth_rate'])) if pd.notna(r.get('birth_rate')) else None,
            safe_val(float(r['death_rate'])) if pd.notna(r.get('death_rate')) else None,
            safe_val(int(r['natural_increase'])) if pd.notna(r.get('natural_increase')) else None,
            safe_val(float(r['household_income'])) if pd.notna(r.get('household_income')) else None,
        ))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    print(f"   [OK] daegu_population_summary: {len(rows)}행")


if __name__ == '__main__':
    load_korean_demographics()
    load_korean_income_welfare()
    build_daegu_summary()
    print("\n[DONE] S2 STEP 4 완료")
