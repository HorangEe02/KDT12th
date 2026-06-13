"""
01. 데이터 전처리 및 통합
기후 변화에 따른 햄버거 재료 영향 분석

프로젝트 목적: 기후 변화가 일상 식품(햄버거)에 미치는 영향을 통계적으로 검증
핵심 메시지: "기후변화는 먼 미래의 이야기가 아니라, 오늘 점심 메뉴에 영향을 미치는 현실이다"

데이터 출처:
    1. FAOSTAT (UN 식량농업기구) - https://www.fao.org/faostat/en/#data
    2. Kaggle Climate Change Impact on Agriculture
       - https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# 1. 환경 설정
# =============================================================================
def setup_directories():
    """프로젝트 디렉토리 설정"""
    # 프로젝트 경로 설정
    PROJECT_DIR = Path(__file__).parent.parent
    DATA_DIR = PROJECT_DIR / 'data'
    OUTPUT_DIR = PROJECT_DIR / 'output'

    # 처리된 데이터 저장 디렉토리
    PROCESSED_DIR = OUTPUT_DIR / 'processed'
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("📊 기후 변화에 따른 햄버거 재료 영향 분석")
    print("   01. 데이터 전처리 및 통합")
    print("=" * 60)
    print(f"\n✅ 환경 설정 완료")
    print(f"   - 데이터 경로: {DATA_DIR}")
    print(f"   - 처리된 데이터: {PROCESSED_DIR}")
    print(f"   - 결과물 경로: {OUTPUT_DIR}")

    return PROJECT_DIR, DATA_DIR, OUTPUT_DIR, PROCESSED_DIR


# =============================================================================
# 2. 데이터 로드 함수
# =============================================================================
def load_kaggle_climate_data(data_dir):
    """
    Kaggle Climate Change Impact on Agriculture 데이터 로드

    출처: https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture
    """
    filepath = data_dir / 'climate_change_impact_on_agriculture_2024.csv'

    if not filepath.exists():
        print(f"⚠️ 파일 없음: {filepath}")
        return None

    df = pd.read_csv(filepath)
    print(f"\n📥 Kaggle 기후-농업 데이터 로드")
    print(f"   - 크기: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   - 기간: {df['Year'].min()} ~ {df['Year'].max()}")
    print(f"   - 국가 수: {df['Country'].nunique()}")
    print(f"   - 작물 종류: {df['Crop_Type'].unique().tolist()}")

    return df


def load_faostat_production(data_dir, chunksize=500000):
    """
    FAOSTAT 작물/축산 생산량 데이터 로드 (대용량 파일 처리)

    출처: FAO. 2024. FAOSTAT: Crops and livestock products.
          https://www.fao.org/faostat/en/#data/QCL
    """
    filepath = data_dir / 'Production_Crops_Livestock_E_All_Data_(Normalized)' / \
               'Production_Crops_Livestock_E_All_Data_(Normalized).csv'

    if not filepath.exists():
        print(f"⚠️ 파일 없음: {filepath}")
        return None

    # 분석 대상 품목 (햄버거 재료)
    target_items = [
        'Wheat',                                          # 빵 원료
        'Meat of cattle with the bone, fresh or chilled', # 소고기 (패티)
        'Meat of cattle, boneless (beef & veal)',         # 소고기 (뼈없음)
        'Tomatoes',                                        # 토마토 (케첩)
        'Lettuce and chicory',                            # 양상추
        'Potatoes',                                        # 감자 (감자튀김)
        'Chillies and peppers, dry',                      # 고추 (스리라차)
        'Chillies and peppers, green',                    # 고추 (신선)
        'Onions, dry',                                    # 양파
        'Cucumbers and gherkins',                         # 피클
        'Cheese, whole cow milk',                         # 치즈
        'Sugar beet',                                     # 설탕 원료
        'Sugar cane'                                      # 설탕 원료
    ]

    print(f"\n📥 FAOSTAT 생산량 데이터 로드 중... (대용량 파일)")

    # 청크 단위로 읽으면서 필요한 데이터만 필터링
    chunks = []
    total_rows = 0

    for chunk in pd.read_csv(filepath, chunksize=chunksize, encoding='latin-1'):
        total_rows += len(chunk)
        # 분석 대상 품목만 필터링
        filtered = chunk[chunk['Item'].isin(target_items)]
        if len(filtered) > 0:
            chunks.append(filtered)

        if total_rows % 2000000 == 0:
            print(f"   처리 중... {total_rows:,} rows")

    if not chunks:
        print(f"⚠️ 대상 품목 데이터 없음")
        return None

    df = pd.concat(chunks, ignore_index=True)

    print(f"   - 전체 데이터: {total_rows:,} rows")
    print(f"   - 필터링 후: {len(df):,} rows")
    print(f"   - 품목 수: {df['Item'].nunique()}")
    print(f"   - 기간: {df['Year'].min()} ~ {df['Year'].max()}")

    return df


def load_faostat_temperature(data_dir):
    """
    FAOSTAT 기온 변화 데이터 로드

    출처: FAO. 2024. FAOSTAT: Temperature change on land.
          https://www.fao.org/faostat/en/#data/ET
    원본: NASA Goddard Institute for Space Studies (GISTEMP)
    """
    filepath = data_dir / 'Temperature change' / 'Environment_Temperature_change_E_All_Data_NOFLAG.csv'

    if not filepath.exists():
        print(f"⚠️ 파일 없음: {filepath}")
        return None

    df = pd.read_csv(filepath, encoding='latin-1')

    print(f"\n📥 FAOSTAT 기온 변화 데이터 로드")
    print(f"   - 크기: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"   - 국가 수: {df['Area'].nunique()}")

    return df


def load_faostat_trade(data_dir, chunksize=1000000):
    """
    FAOSTAT 무역 데이터 로드 (대용량 파일 처리)
    한국 수입 데이터 중심

    출처: FAO. 2024. FAOSTAT: Crops and livestock products (Trade).
          https://www.fao.org/faostat/en/#data/TCL
    """
    filepath = data_dir / 'Trade_CropsLivestock_E_All_Data_(Normalized)' / \
               'Trade_CropsLivestock_E_All_Data_(Normalized).csv'

    if not filepath.exists():
        print(f"⚠️ 파일 없음: {filepath}")
        return None

    # 분석 대상 품목
    target_items = [
        'Wheat', 'Potatoes', 'Tomatoes',
        'Meat of cattle, boneless (beef & veal)',
        'Meat of cattle with the bone, fresh or chilled',
        'Lettuce and chicory', 'Onions, dry',
        'Cheese, whole cow milk'
    ]

    # 대상 국가 (한국 및 주요 수출국)
    target_countries = [
        'Republic of Korea', 'Korea, Republic of',
        'China', 'United States of America', 'Australia',
        'Brazil', 'Canada', 'New Zealand'
    ]

    print(f"\n📥 FAOSTAT 무역 데이터 로드 중... (대용량 파일)")

    chunks = []
    total_rows = 0

    for chunk in pd.read_csv(filepath, chunksize=chunksize, encoding='latin-1'):
        total_rows += len(chunk)
        # 필터링
        filtered = chunk[
            (chunk['Item'].isin(target_items)) &
            (chunk['Area'].isin(target_countries))
        ]
        if len(filtered) > 0:
            chunks.append(filtered)

        if total_rows % 5000000 == 0:
            print(f"   처리 중... {total_rows:,} rows")

    if not chunks:
        print(f"⚠️ 대상 품목/국가 데이터 없음")
        return None

    df = pd.concat(chunks, ignore_index=True)

    print(f"   - 전체 데이터: {total_rows:,} rows")
    print(f"   - 필터링 후: {len(df):,} rows")

    return df


# =============================================================================
# 3. 데이터 전처리 함수
# =============================================================================
def preprocess_production_data(df):
    """
    생산량 데이터 전처리
    - Wide format 변환
    - 연도별 생산량 집계
    """
    if df is None:
        return None

    print("\n🔧 생산량 데이터 전처리...")

    # 필요한 컬럼만 선택
    df_clean = df[['Area', 'Item', 'Element', 'Year', 'Unit', 'Value']].copy()

    # 결측치 처리
    df_clean['Value'] = pd.to_numeric(df_clean['Value'], errors='coerce')
    df_clean = df_clean.dropna(subset=['Value'])

    # 분석 기간 필터링 (2000-2023)
    df_clean = df_clean[(df_clean['Year'] >= 2000) & (df_clean['Year'] <= 2023)]

    print(f"   - 전처리 후 크기: {len(df_clean):,} rows")
    print(f"   - 기간: {df_clean['Year'].min()} ~ {df_clean['Year'].max()}")

    return df_clean


def preprocess_temperature_data(df):
    """
    기온 데이터 전처리
    - Wide format에서 Long format으로 변환
    - 연간 평균 기온 편차 계산
    """
    if df is None:
        return None

    print("\n🔧 기온 데이터 전처리...")

    # Meteorological year 데이터만 추출 (연간 평균)
    df_annual = df[df['Months'] == 'Meteorological year'].copy()

    # Temperature change 데이터만 추출
    df_temp = df_annual[df_annual['Element'] == 'Temperature change'].copy()

    # Wide to Long format 변환
    year_cols = [col for col in df_temp.columns if col.startswith('Y')]

    df_long = df_temp.melt(
        id_vars=['Area Code', 'Area', 'Months', 'Element', 'Unit'],
        value_vars=year_cols,
        var_name='Year_Col',
        value_name='Temp_Anomaly'
    )

    # 연도 추출
    df_long['Year'] = df_long['Year_Col'].str.replace('Y', '').astype(int)
    df_long = df_long.drop('Year_Col', axis=1)

    # 결측치 제거
    df_long['Temp_Anomaly'] = pd.to_numeric(df_long['Temp_Anomaly'], errors='coerce')
    df_long = df_long.dropna(subset=['Temp_Anomaly'])

    # 분석 기간 필터링
    df_long = df_long[(df_long['Year'] >= 1990) & (df_long['Year'] <= 2023)]

    print(f"   - 전처리 후 크기: {len(df_long):,} rows")
    print(f"   - 국가 수: {df_long['Area'].nunique()}")
    print(f"   - 기간: {df_long['Year'].min()} ~ {df_long['Year'].max()}")

    return df_long


def preprocess_trade_data(df):
    """
    무역 데이터 전처리
    """
    if df is None:
        return None

    print("\n🔧 무역 데이터 전처리...")

    # 필요한 컬럼만 선택
    df_clean = df[['Area', 'Item', 'Element', 'Year', 'Unit', 'Value']].copy()

    # 결측치 처리
    df_clean['Value'] = pd.to_numeric(df_clean['Value'], errors='coerce')
    df_clean = df_clean.dropna(subset=['Value'])

    # 분석 기간 필터링
    df_clean = df_clean[(df_clean['Year'] >= 2000) & (df_clean['Year'] <= 2023)]

    print(f"   - 전처리 후 크기: {len(df_clean):,} rows")

    return df_clean


def preprocess_kaggle_data(df):
    """
    Kaggle 기후-농업 데이터 전처리
    """
    if df is None:
        return None

    print("\n🔧 Kaggle 데이터 전처리...")

    # 햄버거 관련 작물만 필터링
    burger_crops = ['Wheat', 'Corn', 'Potatoes', 'Soybeans']
    df_filtered = df[df['Crop_Type'].isin(burger_crops)].copy()

    # 주요 국가만 필터링
    major_countries = [
        'United States', 'China', 'India', 'Brazil', 'Australia',
        'Canada', 'France', 'Germany', 'Argentina', 'Russia'
    ]
    df_filtered = df_filtered[df_filtered['Country'].isin(major_countries)]

    print(f"   - 전처리 후 크기: {len(df_filtered):,} rows")
    print(f"   - 작물: {df_filtered['Crop_Type'].unique().tolist()}")

    return df_filtered


# =============================================================================
# 4. 품목별 데이터 추출 및 피벗
# =============================================================================
def create_item_production_pivot(df, item_name, element='Production'):
    """
    특정 품목의 생산량 데이터를 Wide format으로 변환

    Parameters:
    -----------
    df : DataFrame - 전처리된 생산량 데이터
    item_name : str - 품목명
    element : str - 요소 (Production, Area harvested, Yield)

    Returns:
    --------
    DataFrame - 연도 × 국가 피벗 테이블
    """
    if df is None:
        return None

    # 필터링
    mask = (df['Item'] == item_name) & (df['Element'] == element)
    df_filtered = df[mask].copy()

    if len(df_filtered) == 0:
        print(f"   ⚠️ '{item_name}' - '{element}' 데이터 없음")
        return None

    # 피벗
    df_pivot = df_filtered.pivot_table(
        index='Year',
        columns='Area',
        values='Value',
        aggfunc='sum'
    ).reset_index()

    # 전체 합계 컬럼 추가
    numeric_cols = [c for c in df_pivot.columns if c != 'Year']
    df_pivot['World_Total'] = df_pivot[numeric_cols].sum(axis=1)

    return df_pivot


def extract_burger_ingredients(df_production, df_temperature):
    """
    햄버거 재료별 생산량 데이터 추출 및 기온 데이터 병합
    """
    if df_production is None:
        return {}

    print("\n📊 햄버거 재료별 데이터 추출...")

    # 세계 평균 기온 데이터 준비
    df_world_temp = None
    if df_temperature is not None:
        df_world_temp = df_temperature[df_temperature['Area'] == 'World'][['Year', 'Temp_Anomaly']].copy()
        df_world_temp = df_world_temp.groupby('Year')['Temp_Anomaly'].mean().reset_index()

    # 분석 대상 품목
    ingredients = {
        'wheat': 'Wheat',
        'tomatoes': 'Tomatoes',
        'lettuce': 'Lettuce and chicory',
        'potatoes': 'Potatoes',
        'beef': 'Meat of cattle with the bone, fresh or chilled',
        'beef_boneless': 'Meat of cattle, boneless (beef & veal)',
        'chillies': 'Chillies and peppers, dry',
        'onions': 'Onions, dry',
        'cucumbers': 'Cucumbers and gherkins'
    }

    results = {}

    for key, item_name in ingredients.items():
        df_item = create_item_production_pivot(df_production, item_name, 'Production')

        if df_item is not None:
            # 기온 데이터 병합
            if df_world_temp is not None:
                df_item = df_item.merge(df_world_temp, on='Year', how='left')

            results[key] = df_item
            print(f"   ✓ {item_name}: {df_item.shape}")

    return results


# =============================================================================
# 5. 통합 데이터셋 생성
# =============================================================================
def create_integrated_dataset(ingredient_data, df_temperature):
    """
    모든 재료의 생산량과 기온 데이터를 통합한 분석용 데이터셋 생성
    """
    print("\n📊 통합 데이터셋 생성...")

    integrated_data = []

    # 세계 평균 기온 데이터 준비
    df_world_temp = None
    if df_temperature is not None:
        df_world_temp = df_temperature[df_temperature['Area'] == 'World'][['Year', 'Temp_Anomaly']].copy()
        df_world_temp = df_world_temp.groupby('Year')['Temp_Anomaly'].mean().reset_index()

    item_names = {
        'wheat': '밀 (Wheat)',
        'tomatoes': '토마토 (Tomatoes)',
        'lettuce': '양상추 (Lettuce)',
        'potatoes': '감자 (Potatoes)',
        'beef': '소고기 (Beef)',
        'beef_boneless': '소고기-뼈없음 (Beef Boneless)',
        'chillies': '고추 (Chillies)',
        'onions': '양파 (Onions)',
        'cucumbers': '오이 (Cucumbers)'
    }

    for key, df in ingredient_data.items():
        if df is None or 'World_Total' not in df.columns:
            continue

        for _, row in df.iterrows():
            record = {
                'Year': row['Year'],
                'Item_Key': key,
                'Item_Name': item_names.get(key, key),
                'World_Production_Tonnes': row['World_Total']
            }

            # 기온 데이터 추가
            if df_world_temp is not None:
                temp_row = df_world_temp[df_world_temp['Year'] == row['Year']]
                if len(temp_row) > 0:
                    record['Temp_Anomaly_C'] = temp_row['Temp_Anomaly'].values[0]
                else:
                    record['Temp_Anomaly_C'] = np.nan
            else:
                record['Temp_Anomaly_C'] = row.get('Temp_Anomaly', np.nan)

            integrated_data.append(record)

    df_integrated = pd.DataFrame(integrated_data)

    # 연간 변화율 계산
    df_integrated = df_integrated.sort_values(['Item_Key', 'Year'])
    df_integrated['YoY_Change_Pct'] = df_integrated.groupby('Item_Key')['World_Production_Tonnes'].pct_change() * 100

    print(f"   - 통합 데이터셋 크기: {df_integrated.shape}")

    return df_integrated


# =============================================================================
# 6. 데이터 품질 검증
# =============================================================================
def validate_data_quality(df, name):
    """
    데이터 품질 검증
    """
    print(f"\n📋 {name} 데이터 품질 검증")
    print("-" * 50)

    if df is None:
        print("   ⚠️ 데이터 없음")
        return False

    # 기본 정보
    print(f"   행 수: {len(df):,}")
    print(f"   열 수: {len(df.columns)}")

    # 결측치
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(f"\n   결측치:")
        for col, count in missing[missing > 0].items():
            print(f"      - {col}: {count} ({count/len(df)*100:.1f}%)")
    else:
        print("   결측치: 없음")

    # 수치형 컬럼 통계
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print(f"\n   수치형 변수 요약:")
        summary = df[numeric_cols].describe().round(2)
        print(summary.to_string())

    return True


# =============================================================================
# 7. 데이터 저장
# =============================================================================
def save_processed_data(processed_dir, ingredient_data, df_integrated,
                        df_temp_processed, df_kaggle_processed, df_trade_processed):
    """
    전처리된 데이터 저장
    """
    print("\n💾 전처리 데이터 저장...")

    saved_files = []

    # 1. 재료별 데이터 저장
    for key, df in ingredient_data.items():
        if df is not None:
            filepath = processed_dir / f'{key}_production.csv'
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            saved_files.append(filepath.name)

    # 2. 통합 데이터셋 저장
    if df_integrated is not None:
        filepath = processed_dir / 'integrated_dataset.csv'
        df_integrated.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append(filepath.name)

    # 3. 기온 데이터 저장
    if df_temp_processed is not None:
        filepath = processed_dir / 'temperature_processed.csv'
        df_temp_processed.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append(filepath.name)

    # 4. Kaggle 데이터 저장
    if df_kaggle_processed is not None:
        filepath = processed_dir / 'kaggle_climate_agriculture.csv'
        df_kaggle_processed.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append(filepath.name)

    # 5. 무역 데이터 저장
    if df_trade_processed is not None:
        filepath = processed_dir / 'trade_processed.csv'
        df_trade_processed.to_csv(filepath, index=False, encoding='utf-8-sig')
        saved_files.append(filepath.name)

    print(f"   ✅ 저장 완료: {len(saved_files)} 파일")
    for f in saved_files:
        print(f"      - {f}")

    return saved_files


# =============================================================================
# 8. 메인 실행
# =============================================================================
def main():
    """메인 실행 함수"""

    # 1. 환경 설정
    PROJECT_DIR, DATA_DIR, OUTPUT_DIR, PROCESSED_DIR = setup_directories()

    # 2. 데이터 로드
    print("\n" + "=" * 60)
    print("📥 데이터 로드")
    print("=" * 60)

    df_kaggle = load_kaggle_climate_data(DATA_DIR)
    df_temperature = load_faostat_temperature(DATA_DIR)
    df_production = load_faostat_production(DATA_DIR)
    df_trade = load_faostat_trade(DATA_DIR)

    # 3. 데이터 전처리
    print("\n" + "=" * 60)
    print("🔧 데이터 전처리")
    print("=" * 60)

    df_production_processed = preprocess_production_data(df_production)
    df_temp_processed = preprocess_temperature_data(df_temperature)
    df_kaggle_processed = preprocess_kaggle_data(df_kaggle)
    df_trade_processed = preprocess_trade_data(df_trade)

    # 4. 재료별 데이터 추출
    ingredient_data = extract_burger_ingredients(df_production_processed, df_temp_processed)

    # 5. 통합 데이터셋 생성
    df_integrated = create_integrated_dataset(ingredient_data, df_temp_processed)

    # 6. 데이터 품질 검증
    print("\n" + "=" * 60)
    print("📋 데이터 품질 검증")
    print("=" * 60)

    validate_data_quality(df_integrated, "통합 데이터셋")
    validate_data_quality(df_temp_processed, "기온 데이터")
    validate_data_quality(df_kaggle_processed, "Kaggle 기후-농업 데이터")

    # 7. 데이터 저장
    print("\n" + "=" * 60)
    print("💾 데이터 저장")
    print("=" * 60)

    save_processed_data(
        PROCESSED_DIR,
        ingredient_data,
        df_integrated,
        df_temp_processed,
        df_kaggle_processed,
        df_trade_processed
    )

    # 8. 결과 요약
    print("\n" + "=" * 60)
    print("📊 데이터 전처리 결과 요약")
    print("=" * 60)

    print("\n[분석 대상 품목 - 햄버거 재료]")
    print("   - 빵 원료: Wheat (밀)")
    print("   - 패티 원료: Beef (소고기)")
    print("   - 야채: Lettuce and chicory (양상추)")
    print("   - 케찹 원료: Tomatoes (토마토)")
    print("   - 감자튀김 원료: Potatoes (감자)")
    print("   - 스리라차 원료: Chillies and peppers (고추)")
    print("   - 기타: Onions (양파), Cucumbers (오이/피클)")

    print("\n[분석 기간]")
    if df_integrated is not None:
        print(f"   - 생산량 데이터: {df_integrated['Year'].min()} ~ {df_integrated['Year'].max()}")
    if df_temp_processed is not None:
        print(f"   - 기온 데이터: {df_temp_processed['Year'].min()} ~ {df_temp_processed['Year'].max()}")

    print("\n[데이터 출처]")
    print("   1. FAOSTAT - Crops and livestock products (https://www.fao.org/faostat/en/#data/QCL)")
    print("   2. FAOSTAT - Temperature change on land (https://www.fao.org/faostat/en/#data/ET)")
    print("   3. FAOSTAT - Trade data (https://www.fao.org/faostat/en/#data/TCL)")
    print("   4. Kaggle - Climate Change Impact on Agriculture")
    print("      (https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture)")

    print("\n[생성된 파일 목록]")
    for f in sorted(PROCESSED_DIR.glob("*.csv")):
        size = f.stat().st_size / 1024
        print(f"   - {f.name}: {size:.1f} KB")

    print("\n" + "=" * 60)
    print("✅ 데이터 전처리 완료!")
    print("   다음 단계: 02_데이터_시각화.py")
    print("=" * 60)

    return {
        'integrated': df_integrated,
        'temperature': df_temp_processed,
        'kaggle': df_kaggle_processed,
        'trade': df_trade_processed,
        'ingredients': ingredient_data
    }


if __name__ == "__main__":
    results = main()
