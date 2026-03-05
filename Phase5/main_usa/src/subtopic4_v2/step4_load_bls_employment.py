"""
STEP 4: BLS 고용 데이터 로딩
- ce.series.csv에서 타겟 시리즈 식별
- all.data.combined.csv에서 고용 데이터 추출
- us_industry_employment 테이블에 적재
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def build_target_series():
    """BLS 시리즈 메타데이터에서 타겟 시리즈 추출"""
    series_path = S4_DATA_FILES['BLS_SERIES']
    if not os.path.exists(series_path):
        print(f"  [SKIP] ce.series.csv 없음")
        return {}

    df = pd.read_csv(series_path, low_memory=False)
    df.columns = df.columns.str.strip()

    # 타겟 supersectors + data_type 01(ALL EMPLOYEES) + seasonal S
    target_supersectors = set(BLS_SUPERSECTORS.keys())
    series_map = {}

    for _, row in df.iterrows():
        sid = str(row.get('series_id', '')).strip()
        sc = str(int(row.get('supersector_code', 0))).zfill(2)
        ic = str(int(row.get('industry_code', 0))).zfill(8)
        dt = str(int(row.get('data_type_code', 0))).zfill(2)
        seasonal = str(row.get('seasonal', '')).strip()

        if sc in target_supersectors and dt == '01' and seasonal == 'S':
            # industry_code가 supersector + '000000' (총합 레벨, 8자리)
            expected_ic = sc + '000000'
            if ic == expected_ic:
                series_map[sid] = {
                    'supersector_code': sc,
                    'supersector_name': BLS_SUPERSECTORS.get(sc, ''),
                    'industry_code': ic,
                    'industry_name': str(row.get('series_title', '')).strip(),
                    'data_type_code': dt,
                }

    print(f"  타겟 시리즈: {len(series_map)}개")
    return series_map


def load_bls_data(series_map):
    """BLS 데이터 파일 → us_industry_employment"""
    data_path = S4_DATA_FILES['BLS_DATA']
    if not os.path.exists(data_path):
        print(f"  [SKIP] all.data.combined.csv 없음")
        return 0
    if not series_map:
        print("  [SKIP] 타겟 시리즈 없음")
        return 0

    target_ids = set(series_map.keys())
    conn = get_connection(DB_NAME)
    sql = """INSERT INTO us_industry_employment
             (year, month, series_id, supersector_code, supersector_name,
              industry_code, industry_name, data_type_code, employee_count,
              source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    total = 0
    chunk_count = 0

    for chunk in pd.read_csv(data_path, chunksize=100000, low_memory=False):
        chunk.columns = chunk.columns.str.strip()
        chunk['series_id'] = chunk['series_id'].astype(str).str.strip()

        matched = chunk[chunk['series_id'].isin(target_ids)]

        if matched.empty:
            chunk_count += 1
            if chunk_count % 50 == 0:
                print(f"    ... {chunk_count} chunks 처리 ({total:,}행)")
            continue

        data = []
        for _, row in matched.iterrows():
            sid = row['series_id'].strip()
            period = str(row.get('period', '')).strip()
            if not period.startswith('M') or period == 'M13':
                continue
            month = int(period[1:])
            year = int(row['year'])
            value = row.get('value', '')
            try:
                emp = float(str(value).strip().replace(',', ''))
            except (ValueError, TypeError):
                continue

            info = series_map[sid]
            data.append((
                year, month, sid,
                info['supersector_code'], info['supersector_name'],
                info['industry_code'], info['industry_name'],
                info['data_type_code'], emp,
                'bls/employment'
            ))

        if data:
            total += batch_insert(conn, sql, data)

        chunk_count += 1
        if chunk_count % 50 == 0:
            print(f"    ... {chunk_count} chunks 처리 ({total:,}행)")

    conn.close()
    print(f"  [OK] BLS 고용: {total:,}행 → us_industry_employment")
    return total


def run():
    print("=" * 60)
    print("STEP 4: BLS 고용 데이터 로딩")
    print("=" * 60)
    series_map = build_target_series()
    load_bls_data(series_map)
    print("\n  STEP 4 완료!")


if __name__ == '__main__':
    run()
