"""
STEP 4: BLS 고용 데이터 → us_industry_employment
  - 15.8M행 all.data.combined.csv에서 핵심 산업 필터링
  - series_id = CES + supersector(2) + industry(8) + datatype(2)
  - datatype '01' = ALL EMPLOYEES (천명 단위)
실행: python src/subtopic4/s4_step4_load_bls_employment.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *

# ── 로딩 대상 산업 (supersector 레벨 총계) ──
TARGET_SUPERSECTORS = {
    '00': 'Total nonfarm',
    '05': 'Total private',
    '20': 'Construction',
    '30': 'Manufacturing',
    '40': 'Trade, transportation, and utilities',
    '50': 'Information',
    '55': 'Financial activities',
    '60': 'Professional and business services',
    '65': 'Education and health services',
    '70': 'Leisure and hospitality',
    '80': 'Other services',
    '90': 'Government',
}


def build_target_series():
    """ce.series.csv에서 로딩 대상 series_id 목록 구축"""
    series_path = S4_DATA_FILES['BLS_SERIES']
    df_series = pd.read_csv(series_path, dtype=str)
    df_series.columns = df_series.columns.str.strip()

    # supersector 총계: industry_code = SS + '000000' (예: 30000000)
    # SS=00 총계는 industry_code = '00000000'
    target_ic_set = set()
    for ss in TARGET_SUPERSECTORS.keys():
        target_ic_set.add(f'{ss}000000')

    mask = (
        (df_series['supersector_code'].str.strip().isin(TARGET_SUPERSECTORS.keys())) &
        (df_series['industry_code'].str.strip().isin(target_ic_set)) &
        (df_series['data_type_code'].str.strip() == '01') &
        (df_series['seasonal'].str.strip() == 'S')
    )
    df_target = df_series[mask].copy()
    print(f"  대상 series: {len(df_target)}개")

    # series_id → (supersector_code, supersector_name, industry_code, industry_name) 매핑
    industry_path = S4_DATA_FILES['BLS_INDUSTRY']
    df_ind = pd.read_csv(industry_path, dtype=str)
    df_ind.columns = df_ind.columns.str.strip()
    ind_map = dict(zip(df_ind['industry_code'].str.strip(), df_ind['industry_name'].str.strip()))

    series_map = {}
    for _, row in df_target.iterrows():
        sid = row['series_id'].strip()
        ss_code = row['supersector_code'].strip()
        ind_code = row['industry_code'].strip()
        series_map[sid] = {
            'supersector_code': ss_code,
            'supersector_name': TARGET_SUPERSECTORS.get(ss_code, 'Unknown'),
            'industry_code': ind_code,
            'industry_name': ind_map.get(ind_code, TARGET_SUPERSECTORS.get(ss_code, 'Unknown')),
            'data_type_code': row['data_type_code'].strip(),
        }

    for sid, info in series_map.items():
        print(f"    {sid} → {info['supersector_name']}")

    return series_map


def load_bls_data(series_map):
    """15.8M행 데이터에서 대상 series만 필터링하여 적재"""
    data_path = S4_DATA_FILES['BLS_DATA']
    if not os.path.exists(data_path):
        print(f"  [SKIP] BLS 데이터 파일 없음")
        return 0

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO us_industry_employment
             (year, month, series_id, supersector_code, supersector_name,
              industry_code, industry_name, data_type_code, employee_count)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    target_ids = set(series_map.keys())
    total = 0
    batch_data = []
    chunk_n = 0

    for chunk in pd.read_csv(data_path, chunksize=100000, dtype=str):
        chunk.columns = chunk.columns.str.strip()
        chunk['series_id'] = chunk['series_id'].str.strip()

        # 타겟 series 필터링
        df_f = chunk[chunk['series_id'].isin(target_ids)].copy()

        if df_f.empty:
            chunk_n += 1
            if chunk_n % 50 == 0:
                print(f"    ... {chunk_n * 100000}행 스캔 중")
            continue

        for _, row in df_f.iterrows():
            sid = row['series_id']
            info = series_map[sid]

            period = row.get('period', '').strip()
            if not period.startswith('M') or period == 'M13':
                continue
            month = int(period[1:])

            try:
                val = float(row['value'].strip()) if row['value'].strip() else None
            except (ValueError, AttributeError):
                val = None

            batch_data.append((
                int(row['year'].strip()),
                month,
                sid,
                info['supersector_code'],
                info['supersector_name'],
                info['industry_code'],
                info['industry_name'],
                info['data_type_code'],
                val,
            ))

        if len(batch_data) >= 5000:
            cursor.executemany(sql, batch_data)
            conn.commit()
            total += len(batch_data)
            batch_data = []

        chunk_n += 1
        if chunk_n % 50 == 0:
            print(f"    ... {chunk_n * 100000}행 스캔, 적재: {total}행")

    if batch_data:
        cursor.executemany(sql, batch_data)
        conn.commit()
        total += len(batch_data)

    conn.close()
    print(f"  [OK] BLS 고용: {total}행 → us_industry_employment")
    return total


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 4: BLS 산업별 고용 데이터 로딩")
    print("=" * 60)
    series_map = build_target_series()
    load_bls_data(series_map)
    print("\n[DONE] STEP 4 완료")
