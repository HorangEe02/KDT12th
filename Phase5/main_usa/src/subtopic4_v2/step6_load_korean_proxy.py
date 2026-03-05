"""
STEP 6: 한국 프록시 데이터 로딩
- Korean_demographics_2000-2022.csv → korean_demographics
- 대구 + 전국 필터
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def load_korean_demographics():
    csv_path = S4_DATA_FILES['KR_DEMOGRAPHICS']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] Korean_demographics 파일 없음")
        return 0

    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    print(f"  전체 행수: {len(df):,}, 열: {list(df.columns)}")

    # 대구 + 전국 필터
    # Region 열에서 Daegu, Whole country 찾기
    target_regions = df[
        df['Region'].astype(str).str.contains('Daegu|Whole country|Seoul|Busan', case=False, na=False)
    ]
    # 대구와 전국만 추출 (추가로 서울, 부산은 비교용)
    target_regions = df[
        df['Region'].astype(str).str.strip().isin([
            'Daegu', 'Whole country', 'Seoul', 'Busan'
        ])
    ].copy()
    print(f"  필터 후 행수: {len(target_regions):,}")

    # 지역명 매핑
    region_map = {
        'Daegu': '대구',
        'Whole country': '전국',
        'Seoul': '서울',
        'Busan': '부산',
    }

    conn = get_connection(DB_NAME)
    sql = """INSERT INTO korean_demographics
             (year, month, region, birth_count, birth_rate,
              death_count, death_rate, natural_growth, natural_growth_rate,
              marriage_count, marriage_rate, divorce_count, divorce_rate,
              source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    data = []
    for _, row in target_regions.iterrows():
        # Date: M/D/YYYY
        date_str = str(row.get('Date', ''))
        try:
            parts = date_str.split('/')
            month = int(parts[0])
            year = int(parts[2]) if len(parts) >= 3 else int(parts[0])
        except (ValueError, IndexError):
            continue

        region_en = str(row.get('Region', '')).strip()
        region_kr = region_map.get(region_en, region_en)

        data.append((
            year, month, region_kr,
            safe_val(row.get('Birth')),
            safe_val(row.get('Birth_rate')),
            safe_val(row.get('Death')),
            safe_val(row.get('Death_rate')),
            safe_val(row.get('Natural_growth')),
            safe_val(row.get('Natural_growth_rate')),
            safe_val(row.get('Marriage')),
            safe_val(row.get('Marriage_rate')),
            safe_val(row.get('Divorce')),
            safe_val(row.get('Divorce_rate')),
            'korean-demographics-20002022'
        ))

    total = batch_insert(conn, sql, data)
    conn.close()
    print(f"  [OK] 한국 인구통계: {total:,}행 → korean_demographics")
    return total


def run():
    print("=" * 60)
    print("STEP 6: 한국 프록시 데이터 로딩")
    print("=" * 60)
    load_korean_demographics()
    print("\n  STEP 6 완료!")


if __name__ == '__main__':
    run()
