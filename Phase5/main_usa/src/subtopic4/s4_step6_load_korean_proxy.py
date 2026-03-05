"""
STEP 6: 한국(대구) 인구통계 + 소득 프록시 데이터 로딩
  - Korean_demographics_2000-2022.csv → korean_demographics (Daegu 필터)
  - Korea Income and Welfare.csv → 대구 소득 집계 (참고용)
실행: python src/subtopic4/s4_step6_load_korean_proxy.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *


def load_korean_demographics():
    """Korean demographics (대구) → korean_demographics 테이블"""
    csv_path = S4_DATA_FILES['KR_DEMOGRAPHICS']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] 파일 없음: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)
    print(f"  전체: {len(df)}행")

    # 대구 + 전국 필터
    df_f = df[df['Region'].isin(['Daegu', 'Whole country'])].copy()
    print(f"  필터(대구+전국): {len(df_f)}행")

    if df_f.empty:
        return 0

    # Date 파싱 (M/D/YYYY → year, month)
    df_f['Date_parsed'] = pd.to_datetime(df_f['Date'], format='%m/%d/%Y', errors='coerce')
    df_f['year'] = df_f['Date_parsed'].dt.year
    df_f['month'] = df_f['Date_parsed'].dt.month

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    sql = """INSERT INTO korean_demographics
             (year, month, region, birth_count, birth_rate,
              death_count, death_rate, natural_growth, natural_growth_rate,
              marriage_count, marriage_rate, divorce_count, divorce_rate,
              source_dataset)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    rows = 0
    for _, row in df_f.iterrows():
        region = '대구' if row['Region'] == 'Daegu' else '전국'
        cursor.execute(sql, (
            safe_val(row['year']),
            safe_val(row['month']),
            region,
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
            'Korean_demographics_2000-2022',
        ))
        rows += 1

    conn.commit()
    conn.close()
    print(f"  [OK] 한국 인구통계: {rows}행 → korean_demographics")
    return rows


def load_korea_income_summary():
    """Korea Income and Welfare → 대구 소득 연도별 요약 (참고용 출력)"""
    csv_path = S4_DATA_FILES['KR_INCOME']
    if not os.path.exists(csv_path):
        print(f"  [SKIP] 파일 없음: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"\n  Korea Income 전체: {len(df)}행")
    print(f"  지역 코드: {sorted(df['region'].unique())}")
    print(f"  연도 범위: {df['year'].min()}-{df['year'].max()}")

    # 지역별 연도별 평균 소득 (지역코드별)
    summary = df.groupby(['region', 'year']).agg(
        avg_income=('income', 'mean'),
        count=('income', 'count'),
    ).reset_index()

    print(f"\n  지역별 2018년 평균 소득:")
    yr_2018 = summary[summary['year'] == 2018].sort_values('avg_income', ascending=False)
    print(yr_2018.to_string(index=False))


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 6: 한국(대구) 프록시 데이터 로딩")
    print("=" * 60)
    load_korean_demographics()
    load_korea_income_summary()
    print("\n[DONE] STEP 6 완료")
