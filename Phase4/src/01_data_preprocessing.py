"""
01. 데이터 전처리 및 통합 (소스류 분석)

프로젝트명: 기후 변화가 햄버거 소스류 원재료에 미치는 영향 분석
분석 대상: 토마토(케찹), 계란(마요네즈), 고추(스리라차)
핵심 메시지: "당신의 햄버거 소스 가격은 지구 반대편 기후에 달려있다"

데이터 출처:
- FAOSTAT Crops Production: https://www.fao.org/faostat/en/#data/QCL
- FAOSTAT Livestock Primary: https://www.fao.org/faostat/en/#data/QL
- FAOSTAT Temperature Change: https://www.fao.org/faostat/en/#data/ET
- Kaggle Climate Change Impact: https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 프로젝트 경로 설정
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'
RESULT_DIR = BASE_DIR / 'result_md'

# 디렉토리 생성
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("📊 소스류 원재료 데이터 전처리 및 통합")
print("=" * 60)
print(f"   - 분석 대상: 토마토(케찹), 계란(마요), 고추(스리라차)")
print(f"   - 데이터 경로: {DATA_DIR}")
print(f"   - 출력 경로: {OUTPUT_DIR}")
print()

# ============================================================
# 2. 분석 대상 소스류 정의
# ============================================================
SAUCE_ITEMS = {
    'tomatoes': {
        'name': '토마토 (케찹)',
        'item_code': 388,
        'item_name': 'Tomatoes',
        'top_producers': ['China', 'India', 'Turkey', 'United States of America', 'Egypt', 'Italy'],
        'climate_sensitivity': '중간 (관개 시설 의존)'
    },
    'eggs': {
        'name': '계란 (마요네즈)',
        'item_code': 1062,
        'item_name': 'Hen eggs in shell',
        'top_producers': ['China', 'United States of America', 'India', 'Mexico', 'Brazil', 'Japan'],
        'climate_sensitivity': '간접적 (사료 작물 영향)'
    },
    'chillies_dry': {
        'name': '건고추 (스리라차)',
        'item_code': 689,
        'item_name': 'Chillies and peppers, dry',
        'top_producers': ['India', 'China', 'Bangladesh', 'Thailand', 'Pakistan', 'Mexico'],
        'climate_sensitivity': '매우 높음 (가뭄, 폭염에 취약)'
    },
    'chillies_green': {
        'name': '풋고추',
        'item_code': 401,
        'item_name': 'Chillies and peppers, green',
        'top_producers': ['China', 'Mexico', 'Turkey', 'Indonesia', 'Spain'],
        'climate_sensitivity': '높음'
    }
}

print("[분석 대상 소스류]")
for key, info in SAUCE_ITEMS.items():
    print(f"   🍽️ {info['name']} - 기후 민감도: {info['climate_sensitivity']}")
print()

# ============================================================
# 3. 데이터 로드 함수
# ============================================================
def load_production_data(chunk_size=500000):
    """
    FAOSTAT 생산량 데이터 로드 (대용량 처리)

    데이터 출처: FAO. 2024. FAOSTAT: Crops and livestock products.
    https://www.fao.org/faostat/en/#data/QCL
    """
    production_path = DATA_DIR / 'Production_Crops_Livestock_E_All_Data_(Normalized)' / \
                      'Production_Crops_Livestock_E_All_Data_(Normalized).csv'

    if not production_path.exists():
        print(f"⚠️ 파일을 찾을 수 없습니다: {production_path}")
        return None

    print("📂 생산량 데이터 로드 중 (대용량 파일, 청크 처리)...")

    # 필요한 Item Code만 필터링
    target_item_codes = [info['item_code'] for info in SAUCE_ITEMS.values()]

    # 청크로 읽어서 필터링
    chunks = []
    for chunk in pd.read_csv(production_path, chunksize=chunk_size,
                             low_memory=False, encoding='utf-8'):
        filtered = chunk[chunk['Item Code'].isin(target_item_codes)]
        if len(filtered) > 0:
            chunks.append(filtered)

    if chunks:
        df = pd.concat(chunks, ignore_index=True)
        print(f"   ✓ 생산량 데이터 로드 완료: {len(df):,} rows")
        return df
    else:
        print("   ⚠️ 해당 품목 데이터가 없습니다.")
        return None


def load_temperature_data():
    """
    FAOSTAT 기온 변화 데이터 로드

    데이터 출처: FAO. 2024. FAOSTAT: Temperature change on land.
    https://www.fao.org/faostat/en/#data/ET
    원본: NASA Goddard Institute for Space Studies (GISTEMP)
    """
    temp_path = DATA_DIR / 'Environment_Temperature_change_E_All_Data_(Normalized)' / \
                'Environment_Temperature_change_E_All_Data_(Normalized).csv'

    if not temp_path.exists():
        print(f"⚠️ 파일을 찾을 수 없습니다: {temp_path}")
        return None

    print("📂 기온 변화 데이터 로드 중...")
    df = pd.read_csv(temp_path, low_memory=False, encoding='utf-8')
    print(f"   ✓ 기온 데이터 로드 완료: {len(df):,} rows")
    return df


def load_climate_agriculture_data():
    """
    Kaggle 기후 변화 농업 영향 데이터 로드

    데이터 출처: Kaggle - Climate Change Impact on Agriculture
    https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture
    """
    climate_path = DATA_DIR / 'climate_change_impact_on_agriculture_2024.csv'

    if not climate_path.exists():
        print(f"⚠️ 파일을 찾을 수 없습니다: {climate_path}")
        return None

    print("📂 기후-농업 데이터 로드 중...")
    df = pd.read_csv(climate_path, encoding='utf-8')
    print(f"   ✓ 기후-농업 데이터 로드 완료: {len(df):,} rows")
    return df


# ============================================================
# 4. 데이터 전처리 함수
# ============================================================
def preprocess_production_data(df, item_key):
    """
    생산량 데이터를 피벗 형태로 전처리

    Parameters:
    -----------
    df : DataFrame - 원본 FAOSTAT 생산량 데이터
    item_key : str - 품목 키 (tomatoes, eggs, chillies_dry, chillies_green)

    Returns:
    --------
    dict - 각 Element별 피벗 데이터프레임
    """
    item_info = SAUCE_ITEMS.get(item_key)
    if item_info is None:
        return None

    item_code = item_info['item_code']
    item_name = item_info['name']

    # 해당 품목 필터링
    df_item = df[df['Item Code'] == item_code].copy()

    if len(df_item) == 0:
        print(f"   ⚠️ {item_name}: 데이터 없음")
        return None

    print(f"\n   📊 {item_name} 전처리 중...")
    print(f"      - 원본 데이터: {len(df_item):,} rows")

    # 연도 필터링 (2000년 이후)
    df_item = df_item[df_item['Year'] >= 2000]

    # 주요 생산국 필터링
    top_producers = item_info['top_producers']

    results = {}

    for element in ['Production', 'Area harvested', 'Yield']:
        df_elem = df_item[df_item['Element'] == element].copy()

        if len(df_elem) == 0:
            continue

        # 피벗 테이블 생성
        df_pivot = df_elem.pivot_table(
            index='Year',
            columns='Area',
            values='Value',
            aggfunc='sum'
        ).reset_index()

        # 존재하는 주요 생산국만 선택
        existing_cols = ['Year'] + [c for c in top_producers if c in df_pivot.columns]
        df_pivot_filtered = df_pivot[existing_cols].copy()

        # 전체 합계 계산
        numeric_cols = [c for c in df_pivot_filtered.columns if c != 'Year']
        if numeric_cols:
            df_pivot_filtered['World_Total'] = df_pivot_filtered[numeric_cols].sum(axis=1)

        results[element] = df_pivot_filtered
        print(f"      - {element}: {df_pivot_filtered.shape}")

    return results


def preprocess_temperature_data(df, countries=None):
    """
    기온 데이터 전처리 (연간 평균)

    Parameters:
    -----------
    df : DataFrame - 원본 FAOSTAT 기온 데이터
    countries : list - 필터링할 국가 목록

    Returns:
    --------
    DataFrame - 연도별 국가별 기온 변화
    """
    print("\n   📊 기온 데이터 전처리 중...")

    # 연간 데이터만 필터링 (Meteorological year 또는 연간 평균 계산)
    df_annual = df[df['Months'].str.contains('Meteorological|Annual', case=False, na=False)].copy()

    # 연간 데이터가 없으면 월별 데이터 평균
    if len(df_annual) == 0:
        print("      - 월별 데이터를 연간 평균으로 변환 중...")
        df_annual = df.groupby(['Area', 'Year']).agg({
            'Value': 'mean'
        }).reset_index()

    # 피벗 테이블
    df_pivot = df_annual.pivot_table(
        index='Year',
        columns='Area',
        values='Value',
        aggfunc='mean'
    ).reset_index()

    # 국가 필터링
    if countries:
        existing_cols = ['Year'] + [c for c in countries if c in df_pivot.columns]
        df_pivot = df_pivot[existing_cols]

    # World 평균 계산
    numeric_cols = [c for c in df_pivot.columns if c != 'Year']
    if numeric_cols:
        df_pivot['World_Avg'] = df_pivot[numeric_cols].mean(axis=1)

    print(f"      - 기온 데이터 shape: {df_pivot.shape}")

    return df_pivot


def merge_production_temperature(df_prod, df_temp, year_col='Year'):
    """
    생산량 데이터와 기온 데이터 병합
    """
    if 'World_Avg' in df_temp.columns:
        df_temp_subset = df_temp[['Year', 'World_Avg']].rename(
            columns={'World_Avg': 'Temp_Anomaly_C'}
        )
    elif 'World' in df_temp.columns:
        df_temp_subset = df_temp[['Year', 'World']].rename(
            columns={'World': 'Temp_Anomaly_C'}
        )
    else:
        # 첫 번째 숫자 컬럼 사용
        numeric_cols = df_temp.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols and 'Year' in df_temp.columns:
            df_temp_subset = df_temp[['Year', numeric_cols[0]]].rename(
                columns={numeric_cols[0]: 'Temp_Anomaly_C'}
            )
        else:
            return df_prod

    df_merged = df_prod.merge(df_temp_subset, on='Year', how='left')
    return df_merged


def create_integrated_dataset(production_results, df_temp):
    """
    소스류 원료 통합 데이터셋 생성
    """
    print("\n   📊 통합 데이터셋 생성 중...")

    integrated_data = []

    for item_key, results in production_results.items():
        if results is None:
            continue

        item_info = SAUCE_ITEMS[item_key]

        # Production 데이터 사용
        if 'Production' in results:
            df_prod = results['Production']

            for _, row in df_prod.iterrows():
                integrated_data.append({
                    'Year': row['Year'],
                    'Item_Key': item_key,
                    'Item_Name': item_info['name'],
                    'World_Production_Tonnes': row.get('World_Total', np.nan),
                    'Climate_Sensitivity': item_info['climate_sensitivity']
                })

    df_integrated = pd.DataFrame(integrated_data)

    if len(df_integrated) > 0:
        # 기온 데이터 병합
        df_integrated = merge_production_temperature(df_integrated, df_temp)

        # 전년 대비 변화율 계산
        df_integrated['YoY_Change_Pct'] = df_integrated.groupby('Item_Key')['World_Production_Tonnes'].pct_change() * 100

        print(f"      - 통합 데이터: {df_integrated.shape}")

    return df_integrated


# ============================================================
# 5. 데이터 품질 검증
# ============================================================
def validate_data(df, name):
    """데이터 품질 검증"""
    print(f"\n   🔍 [{name}] 데이터 검증")
    print(f"      - 행 수: {len(df):,}")
    print(f"      - 컬럼 수: {len(df.columns)}")

    if 'Year' in df.columns:
        print(f"      - 기간: {df['Year'].min()} - {df['Year'].max()}")

    missing = df.isnull().sum().sum()
    missing_pct = (missing / (df.shape[0] * df.shape[1])) * 100
    print(f"      - 결측치: {missing:,}개 ({missing_pct:.2f}%)")

    return {
        'rows': len(df),
        'columns': len(df.columns),
        'missing': missing,
        'missing_pct': missing_pct
    }


# ============================================================
# 6. 메인 실행
# ============================================================
def main():
    """메인 전처리 파이프라인"""

    print("\n" + "=" * 60)
    print("🔧 데이터 로드 시작")
    print("=" * 60)

    # 1. 데이터 로드
    df_production = load_production_data()
    df_temperature = load_temperature_data()
    df_climate_agri = load_climate_agriculture_data()

    if df_production is None:
        print("\n⚠️ 생산량 데이터를 로드할 수 없습니다.")
        return

    print("\n" + "=" * 60)
    print("🔧 데이터 전처리 시작")
    print("=" * 60)

    # 2. 생산량 데이터 전처리
    production_results = {}
    for item_key in SAUCE_ITEMS.keys():
        results = preprocess_production_data(df_production, item_key)
        production_results[item_key] = results

    # 3. 기온 데이터 전처리
    df_temp_processed = None
    if df_temperature is not None:
        # 주요 생산국 목록
        all_producers = set()
        for info in SAUCE_ITEMS.values():
            all_producers.update(info['top_producers'])
        all_producers.add('World')

        df_temp_processed = preprocess_temperature_data(df_temperature, list(all_producers))

    # 4. 통합 데이터셋 생성
    df_integrated = None
    if df_temp_processed is not None:
        df_integrated = create_integrated_dataset(production_results, df_temp_processed)

    print("\n" + "=" * 60)
    print("💾 데이터 저장")
    print("=" * 60)

    # 5. 전처리된 데이터 저장
    saved_files = []

    # 생산량 데이터 저장
    for item_key, results in production_results.items():
        if results is None:
            continue

        for element, df in results.items():
            filename = f"{item_key}_{element.lower().replace(' ', '_')}.csv"
            filepath = OUTPUT_DIR / filename
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            saved_files.append(filename)
            print(f"   ✓ {filename}")

    # 기온 데이터 저장
    if df_temp_processed is not None:
        filepath = OUTPUT_DIR / 'temperature_processed.csv'
        df_temp_processed.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append('temperature_processed.csv')
        print(f"   ✓ temperature_processed.csv")

    # 통합 데이터 저장
    if df_integrated is not None and len(df_integrated) > 0:
        filepath = OUTPUT_DIR / 'sauce_ingredients_integrated.csv'
        df_integrated.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append('sauce_ingredients_integrated.csv')
        print(f"   ✓ sauce_ingredients_integrated.csv")

    # 기후-농업 데이터 저장 (필터링된 버전)
    if df_climate_agri is not None:
        filepath = OUTPUT_DIR / 'climate_agriculture_processed.csv'
        df_climate_agri.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append('climate_agriculture_processed.csv')
        print(f"   ✓ climate_agriculture_processed.csv")

    print("\n" + "=" * 60)
    print("📋 데이터 품질 검증")
    print("=" * 60)

    # 6. 데이터 검증
    for item_key, results in production_results.items():
        if results and 'Production' in results:
            validate_data(results['Production'], SAUCE_ITEMS[item_key]['name'])

    if df_temp_processed is not None:
        validate_data(df_temp_processed, '기온 변화')

    if df_integrated is not None:
        validate_data(df_integrated, '통합 데이터')

    print("\n" + "=" * 60)
    print("📊 전처리 결과 요약")
    print("=" * 60)

    print("\n[생성된 파일]")
    for f in saved_files:
        filepath = OUTPUT_DIR / f
        if filepath.exists():
            size = filepath.stat().st_size / 1024
            print(f"   📄 {f}: {size:.1f} KB")

    print("\n[분석 대상 소스류]")
    print("   🍅 토마토 → 케찹 (Ketchup)")
    print("   🥚 계란 → 마요네즈 (Mayonnaise)")
    print("   🌶️ 고추 → 스리라차 (Sriracha)")

    print("\n[데이터 출처]")
    print("   1. FAOSTAT Crops: https://www.fao.org/faostat/en/#data/QCL")
    print("   2. FAOSTAT Livestock: https://www.fao.org/faostat/en/#data/QL")
    print("   3. FAOSTAT Temperature: https://www.fao.org/faostat/en/#data/ET")
    print("   4. Kaggle Climate Change: https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture")

    print("\n" + "=" * 60)
    print("✅ 전처리 완료! 다음 단계: 02_데이터_시각화.md")
    print("=" * 60)

    return {
        'production': production_results,
        'temperature': df_temp_processed,
        'integrated': df_integrated,
        'climate_agri': df_climate_agri
    }


if __name__ == '__main__':
    results = main()
