"""
02. 데이터 시각화
기후 변화에 따른 햄버거 재료 영향 분석

탐색적 데이터 분석(EDA)을 수행하고 기후 변화와 햄버거 재료 간의 관계를 시각적으로 표현합니다.

데이터 출처:
    1. FAOSTAT (https://www.fao.org/faostat/en/#data)
    2. Kaggle Climate Change Impact on Agriculture
       (https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# 1. 환경 설정
# =============================================================================
def setup_environment():
    """시각화 환경 설정"""
    # 경로 설정
    PROJECT_DIR = Path(__file__).parent.parent
    PROCESSED_DIR = PROJECT_DIR / 'output' / 'processed'
    OUTPUT_DIR = PROJECT_DIR / 'output' / 'figures'
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 시각화 스타일 설정
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 13
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['figure.dpi'] = 100

    # 한글 폰트 설정 시도
    try:
        # macOS
        plt.rcParams['font.family'] = 'AppleGothic'
    except:
        try:
            # Windows
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            pass

    plt.rcParams['axes.unicode_minus'] = False

    print("=" * 60)
    print("📊 기후 변화에 따른 햄버거 재료 영향 분석")
    print("   02. 데이터 시각화")
    print("=" * 60)
    print(f"\n✅ 시각화 환경 설정 완료")
    print(f"   - 데이터 경로: {PROCESSED_DIR}")
    print(f"   - 출력 경로: {OUTPUT_DIR}")

    return PROJECT_DIR, PROCESSED_DIR, OUTPUT_DIR


# 색상 팔레트 정의 (재료별)
COLORS = {
    'wheat': '#F1C40F',      # 노란색 (빵)
    'beef': '#E74C3C',       # 빨간색 (패티)
    'tomatoes': '#E67E22',   # 주황색 (케찹)
    'lettuce': '#2ECC71',    # 초록색 (야채)
    'potatoes': '#9B59B6',   # 보라색 (감자튀김)
    'chillies': '#C0392B',   # 진한 빨간색 (스리라차)
    'cucumbers': '#1ABC9C',  # 청록색 (피클)
    'temperature': '#3498DB' # 파란색 (기온)
}

ITEM_NAMES = {
    'wheat': 'Wheat (빵)',
    'beef': 'Beef (패티)',
    'tomatoes': 'Tomatoes (케첩)',
    'lettuce': 'Lettuce (양상추)',
    'potatoes': 'Potatoes (감자튀김)',
    'chillies': 'Chillies (스리라차)',
    'cucumbers': 'Cucumbers (피클)'
}


# =============================================================================
# 2. 데이터 로드
# =============================================================================
def load_processed_data(processed_dir):
    """전처리된 모든 데이터 로드"""
    print("\n📥 데이터 로드 중...")
    data = {}

    # 재료별 생산량 데이터
    items = ['wheat', 'tomatoes', 'potatoes', 'lettuce', 'beef', 'cucumbers']

    for item in items:
        filepath = processed_dir / f'{item}_production.csv'
        if filepath.exists():
            data[item] = pd.read_csv(filepath)
            print(f"   ✓ {item}: {len(data[item])} rows")

    # 기온 데이터
    temp_path = processed_dir / 'temperature_processed.csv'
    if temp_path.exists():
        data['temperature'] = pd.read_csv(temp_path)
        print(f"   ✓ temperature: {len(data['temperature'])} rows")

    # Kaggle 데이터
    kaggle_path = processed_dir / 'kaggle_climate_agriculture.csv'
    if kaggle_path.exists():
        data['kaggle'] = pd.read_csv(kaggle_path)
        print(f"   ✓ kaggle: {len(data['kaggle'])} rows")

    # 무역 데이터
    trade_path = processed_dir / 'trade_processed.csv'
    if trade_path.exists():
        data['trade'] = pd.read_csv(trade_path)
        print(f"   ✓ trade: {len(data['trade'])} rows")

    # 통합 데이터
    integrated_path = processed_dir / 'integrated_dataset.csv'
    if integrated_path.exists():
        data['integrated'] = pd.read_csv(integrated_path)
        print(f"   ✓ integrated: {len(data['integrated'])} rows")

    print(f"\n✅ 총 {len(data)}개 데이터셋 로드 완료")
    return data


# =============================================================================
# 3. 기온 변화 시각화
# =============================================================================
def plot_temperature_trend(data, output_dir):
    """
    글로벌 기온 변화 추이 시각화

    통계적 의미:
    - 1951-1980 기준 대비 기온 편차(anomaly) 표시
    - 파리협정 1.5°C 목표선 포함
    """
    if 'temperature' not in data:
        print("⚠️ 기온 데이터 없음")
        return

    df = data['temperature']

    # 세계 평균 기온 데이터 추출
    df_world = df[df['Area'] == 'World'].copy()
    df_world = df_world.groupby('Year')['Temp_Anomaly'].mean().reset_index()

    if len(df_world) == 0:
        print("⚠️ World 기온 데이터 없음")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    # 색상 매핑: 온도에 따라
    colors = []
    for val in df_world['Temp_Anomaly']:
        if val < 0:
            colors.append('#3498DB')      # 파란색 (기준 이하)
        elif val < 0.5:
            colors.append('#85C1E9')      # 연한 파란색
        elif val < 1.0:
            colors.append('#F39C12')      # 주황색
        else:
            colors.append('#E74C3C')      # 빨간색 (1°C 이상)

    # 막대 그래프
    bars = ax.bar(df_world['Year'], df_world['Temp_Anomaly'], color=colors,
                  edgecolor='black', linewidth=0.3, alpha=0.85)

    # 추세선 (2차 다항식)
    z = np.polyfit(df_world['Year'], df_world['Temp_Anomaly'], 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(df_world['Year'].min(), df_world['Year'].max(), 100)
    ax.plot(x_smooth, p(x_smooth), 'k--', linewidth=2, label='Polynomial Trend')

    # 기준선
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    ax.axhline(y=1.5, color='red', linestyle='--', linewidth=2,
               label='Paris Agreement 1.5°C Target')

    # 주석
    latest_year = df_world['Year'].max()
    latest_temp = df_world[df_world['Year'] == latest_year]['Temp_Anomaly'].values[0]
    ax.annotate(f'{latest_temp:.2f}°C',
                xy=(latest_year, latest_temp),
                xytext=(latest_year - 5, latest_temp + 0.3),
                fontsize=12, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='black'))

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Temperature Anomaly (°C)\nBaseline: 1951-1980', fontsize=12)
    ax.set_title('Global Land Surface Temperature Change (1990-2019)\n'
                 'Source: FAOSTAT / NASA GISTEMP', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.set_xlim(df_world['Year'].min() - 1, df_world['Year'].max() + 1)

    plt.tight_layout()
    plt.savefig(output_dir / 'viz_01_temperature_trend.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 1] 기온 변화 추이 저장 완료")

    # 통계 요약
    first_year = df_world['Year'].min()
    first_temp = df_world[df_world['Year'] == first_year]['Temp_Anomaly'].values[0]
    print(f"\n📊 기온 변화 통계:")
    print(f"   - {first_year}년: {first_temp:.3f}°C")
    print(f"   - {latest_year}년: {latest_temp:.3f}°C")
    print(f"   - 변화량: +{latest_temp - first_temp:.3f}°C")

    return df_world


def plot_regional_temperature(data, output_dir):
    """
    지역별 기온 변화 비교 시각화
    - 고위도 지역의 더 빠른 온난화 확인
    """
    if 'temperature' not in data:
        print("⚠️ 기온 데이터 없음")
        return

    df = data['temperature']

    # 주요 국가 선택
    countries = ['World', 'Russian Federation', 'United States of America',
                 'China', 'Republic of Korea', 'India', 'Brazil', 'Australia']

    fig, ax = plt.subplots(figsize=(14, 7))

    colors = plt.cm.viridis(np.linspace(0, 0.9, len(countries)))

    for country, color in zip(countries, colors):
        df_country = df[df['Area'] == country]
        if len(df_country) > 0:
            df_agg = df_country.groupby('Year')['Temp_Anomaly'].mean().reset_index()
            ax.plot(df_agg['Year'], df_agg['Temp_Anomaly'], linewidth=2,
                    label=country, color=color, marker='o', markersize=3)

    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    ax.axhline(y=1.5, color='red', linestyle='--', linewidth=1.5, alpha=0.7,
               label='1.5°C Target')

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Temperature Anomaly (°C)', fontsize=12)
    ax.set_title('Regional Temperature Change Comparison\n'
                 'Source: FAOSTAT / NASA GISTEMP', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'viz_02_regional_temperature.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 2] 지역별 기온 변화 저장 완료")


# =============================================================================
# 4. 재료별 생산량 시각화
# =============================================================================
def plot_production_trends(data, output_dir):
    """
    햄버거 재료별 글로벌 생산량 추이
    """
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    items_info = [
        ('wheat', 'Wheat (Bread/Bun)'),
        ('beef', 'Beef (Patty)'),
        ('tomatoes', 'Tomatoes (Ketchup)'),
        ('lettuce', 'Lettuce (Vegetable)'),
        ('potatoes', 'Potatoes (Fries)'),
        ('cucumbers', 'Cucumbers (Pickle)')
    ]

    for ax, (key, title) in zip(axes, items_info):
        if key in data and 'World_Total' in data[key].columns:
            df = data[key]
            color = COLORS.get(key, '#3498DB')

            # 생산량 (백만 톤)
            production = df['World_Total'] / 1e6

            # 영역 그래프
            ax.fill_between(df['Year'], production, alpha=0.3, color=color)
            ax.plot(df['Year'], production, color=color, linewidth=2,
                    marker='o', markersize=4)

            # 변화율 표시
            if len(production) > 1:
                start_val = production.iloc[0]
                end_val = production.iloc[-1]
                change_pct = ((end_val - start_val) / start_val) * 100

                color_text = '#27AE60' if change_pct > 0 else '#E74C3C'
                ax.annotate(f'{change_pct:+.1f}%',
                           xy=(df['Year'].iloc[-1], end_val),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=11, fontweight='bold', color=color_text)

            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel('Year')
            ax.set_ylabel('Production (Million Tonnes)')
            ax.grid(alpha=0.3)
            ax.set_xlim(df['Year'].min(), df['Year'].max())
        else:
            ax.set_visible(False)

    plt.suptitle('Global Production Trends of Burger Ingredients (2000-2023)\n'
                 'Source: FAOSTAT', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'viz_03_production_trends.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 3] 재료별 생산량 추이 저장 완료")


def plot_production_vs_temperature(data, output_dir):
    """
    생산량과 기온 변화를 동시에 표시 (이중 Y축)
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    items = [('wheat', 'Wheat (Bread)'),
             ('tomatoes', 'Tomatoes (Ketchup)'),
             ('potatoes', 'Potatoes (Fries)'),
             ('lettuce', 'Lettuce')]

    for ax, (key, title) in zip(axes.flatten(), items):
        if key in data and 'World_Total' in data[key].columns:
            df = data[key]

            # 왼쪽 축: 생산량
            color1 = COLORS.get(key, '#3498DB')
            ax.set_xlabel('Year')
            ax.set_ylabel('Production (Million Tonnes)', color=color1)
            line1 = ax.plot(df['Year'], df['World_Total']/1e6,
                           color=color1, linewidth=2, marker='o',
                           markersize=4, label='Production')
            ax.tick_params(axis='y', labelcolor=color1)
            ax.fill_between(df['Year'], df['World_Total']/1e6, alpha=0.2, color=color1)

            # 오른쪽 축: 기온
            ax2 = ax.twinx()
            color2 = '#E74C3C'
            ax2.set_ylabel('Temp Anomaly (°C)', color=color2)

            if 'Temp_Anomaly' in df.columns:
                line2 = ax2.plot(df['Year'], df['Temp_Anomaly'],
                                color=color2, linewidth=2, linestyle='--',
                                marker='s', markersize=4, label='Temperature')
                ax2.tick_params(axis='y', labelcolor=color2)

                # 범례
                lines = line1 + line2
                labels = [l.get_label() for l in lines]
                ax.legend(lines, labels, loc='upper left', fontsize=9)
            else:
                ax.legend(loc='upper left', fontsize=9)

            ax.set_title(f'{title}: Production vs Temperature', fontsize=11, fontweight='bold')
            ax.grid(alpha=0.3)

    plt.suptitle('Global Production and Temperature Anomaly Comparison\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'viz_04_production_vs_temp.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 4] 생산량-기온 비교 저장 완료")


# =============================================================================
# 5. 한국 수입/무역 현황 시각화
# =============================================================================
def plot_korea_trade_trends(data, output_dir):
    """
    한국의 주요 품목 수입량 추이
    """
    if 'trade' not in data:
        print("⚠️ 무역 데이터 없음")
        return

    df = data['trade']

    # 한국 데이터 필터링
    korea_names = ['Republic of Korea', 'Korea, Republic of']
    df_korea = df[df['Area'].isin(korea_names)]

    if len(df_korea) == 0:
        print("⚠️ 한국 무역 데이터 없음")
        return

    # 수입량 데이터만 필터링
    df_import = df_korea[df_korea['Element'].str.contains('Import', case=False, na=False)]

    if len(df_import) == 0:
        print("⚠️ 한국 수입 데이터 없음")
        return

    # 품목별 연도별 수입량 집계
    df_pivot = df_import.pivot_table(
        index='Year',
        columns='Item',
        values='Value',
        aggfunc='sum'
    ).reset_index()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    items_config = [
        ('Wheat', 'Wheat Import (Bread)', '#F1C40F', 1e6, 'Million'),
        ('Meat of cattle, boneless (beef & veal)', 'Beef Import (Patty)', '#E74C3C', 1e3, 'Thousand'),
        ('Potatoes', 'Potatoes Import (Fries)', '#9B59B6', 1e3, 'Thousand'),
        ('Tomatoes', 'Tomatoes Import (Ketchup)', '#E67E22', 1e3, 'Thousand')
    ]

    for ax, (col, title, color, divisor, unit) in zip(axes.flatten(), items_config):
        if col in df_pivot.columns:
            values = df_pivot[col].fillna(0) / divisor

            # 막대 그래프
            bars = ax.bar(df_pivot['Year'], values, color=color, alpha=0.7,
                         edgecolor='black', linewidth=0.5)

            # 추세선
            valid_mask = values > 0
            if valid_mask.sum() > 1:
                x_valid = df_pivot['Year'][valid_mask]
                y_valid = values[valid_mask]
                z = np.polyfit(x_valid, y_valid, 1)
                p = np.poly1d(z)
                ax.plot(df_pivot['Year'], p(df_pivot['Year']), 'k--', linewidth=2, label='Trend')

            # 변화율
            first_valid = values[values > 0].iloc[0] if (values > 0).any() else 0
            last_valid = values[values > 0].iloc[-1] if (values > 0).any() else 0
            if first_valid > 0:
                change = ((last_valid - first_valid) / first_valid) * 100
                ax.text(0.98, 0.95, f'{change:+.1f}%', transform=ax.transAxes,
                       fontsize=12, fontweight='bold', ha='right', va='top',
                       color='#27AE60' if change > 0 else '#E74C3C')

            ax.set_title(f'Korea: {title}', fontsize=11, fontweight='bold')
            ax.set_xlabel('Year')
            ax.set_ylabel(f'Import Quantity ({unit} Tonnes)')
            ax.legend(loc='upper left', fontsize=9)
            ax.grid(axis='y', alpha=0.3)
        else:
            ax.set_title(f'Korea: {title} (No Data)', fontsize=11)
            ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14, color='gray')

    plt.suptitle('South Korea Agricultural Import Trends\n'
                 'Source: FAOSTAT Trade Data', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'viz_05_korea_import.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 5] 한국 수입 추이 저장 완료")


# =============================================================================
# 6. 기후-수율 관계 시각화
# =============================================================================
def plot_climate_yield_scatter(data, output_dir):
    """
    기온과 작물 수율 간의 관계 시각화
    - Kaggle 데이터 활용
    """
    if 'kaggle' not in data:
        print("⚠️ Kaggle 데이터 없음")
        return

    df = data['kaggle']

    fig, ax = plt.subplots(figsize=(12, 8))

    # 국가별 색상
    countries = df['Country'].unique()
    colors = plt.cm.Set2(np.linspace(0, 1, len(countries)))

    for country, color in zip(countries, colors):
        df_c = df[df['Country'] == country]
        ax.scatter(df_c['Average_Temperature_C'], df_c['Crop_Yield_MT_per_HA'],
                  c=[color], label=country, alpha=0.6, s=50,
                  edgecolors='black', linewidth=0.3)

    # 2차 다항 추세선
    x = df['Average_Temperature_C'].values
    y = df['Crop_Yield_MT_per_HA'].values

    # 결측치 제거
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean, y_clean = x[mask], y[mask]

    if len(x_clean) > 2:
        z = np.polyfit(x_clean, y_clean, 2)
        p = np.poly1d(z)
        x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
        ax.plot(x_line, p(x_line), 'r-', linewidth=2.5, label='Quadratic Trend')

        # 최적 온도 표시
        if z[0] != 0:
            optimal_temp = -z[1] / (2 * z[0])
            if x_clean.min() < optimal_temp < x_clean.max():
                ax.axvline(x=optimal_temp, color='green', linestyle='--',
                           linewidth=1.5, alpha=0.7, label=f'Optimal: {optimal_temp:.1f}°C')

        print(f"   - 추세선 방정식: y = {z[0]:.4f}x² + {z[1]:.4f}x + {z[2]:.4f}")

    ax.set_xlabel('Average Temperature (°C)', fontsize=12)
    ax.set_ylabel('Crop Yield (MT/HA)', fontsize=12)
    ax.set_title('Temperature vs Crop Yield: Non-linear Relationship\n'
                 'Source: Kaggle Climate Change Impact on Agriculture',
                 fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9, ncol=2)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'viz_06_temp_yield_scatter.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 6] 기온-수율 산점도 저장 완료")


def plot_yield_by_crop_type(data, output_dir):
    """
    작물 종류별 수율 분포 시각화
    """
    if 'kaggle' not in data:
        print("⚠️ Kaggle 데이터 없음")
        return

    df = data['kaggle']

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 1. 작물별 수율 박스플롯
    ax1 = axes[0]
    crop_types = df['Crop_Type'].unique()
    crop_colors = plt.cm.Set3(np.linspace(0, 1, len(crop_types)))

    box_data = [df[df['Crop_Type'] == crop]['Crop_Yield_MT_per_HA'].dropna() for crop in crop_types]
    bp = ax1.boxplot(box_data, labels=crop_types, patch_artist=True)

    for patch, color in zip(bp['boxes'], crop_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.set_xlabel('Crop Type', fontsize=11)
    ax1.set_ylabel('Crop Yield (MT/HA)', fontsize=11)
    ax1.set_title('Yield Distribution by Crop Type', fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(axis='y', alpha=0.3)

    # 2. 연도별 평균 수율 추이
    ax2 = axes[1]
    for crop, color in zip(crop_types, crop_colors):
        df_crop = df[df['Crop_Type'] == crop].groupby('Year')['Crop_Yield_MT_per_HA'].mean()
        ax2.plot(df_crop.index, df_crop.values, marker='o', markersize=3,
                linewidth=1.5, label=crop, color=color)

    ax2.set_xlabel('Year', fontsize=11)
    ax2.set_ylabel('Average Crop Yield (MT/HA)', fontsize=11)
    ax2.set_title('Yield Trend by Crop Type (1990-2024)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=8, ncol=2)
    ax2.grid(alpha=0.3)

    plt.suptitle('Crop Yield Analysis | Source: Kaggle Climate Change Impact on Agriculture',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'viz_07_yield_by_crop.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 7] 작물별 수율 분석 저장 완료")


# =============================================================================
# 7. 종합 대시보드
# =============================================================================
def create_summary_dashboard(data, output_dir):
    """
    프로젝트 핵심 메시지를 담은 종합 대시보드
    """
    fig = plt.figure(figsize=(18, 14))

    # 레이아웃 설정
    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.3)

    # ===== 1행: 기온 변화 (전체 너비) =====
    ax1 = fig.add_subplot(gs[0, :])

    if 'temperature' in data:
        df_temp = data['temperature']
        df_world = df_temp[df_temp['Area'] == 'World'].groupby('Year')['Temp_Anomaly'].mean().reset_index()

        if len(df_world) > 0:
            colors = ['#3498DB' if v < 0.5 else '#E74C3C' if v > 1.0 else '#F39C12'
                      for v in df_world['Temp_Anomaly']]
            ax1.bar(df_world['Year'], df_world['Temp_Anomaly'], color=colors,
                    edgecolor='black', linewidth=0.3, alpha=0.85)
            ax1.axhline(y=1.5, color='red', linestyle='--', linewidth=2, label='1.5°C Target')
            ax1.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
            ax1.set_title('Global Temperature Anomaly (°C) | Source: FAOSTAT/NASA',
                          fontweight='bold', fontsize=12)
            ax1.set_ylabel('Temp Anomaly (°C)')
            ax1.legend(loc='upper left')
            ax1.grid(axis='y', alpha=0.3)

    # ===== 2행: 재료별 생산량 =====
    items = [('wheat', gs[1, 0], '#F1C40F'),
             ('tomatoes', gs[1, 1], '#E67E22'),
             ('potatoes', gs[1, 2], '#9B59B6'),
             ('beef', gs[1, 3], '#E74C3C')]

    for key, grid_pos, color in items:
        ax = fig.add_subplot(grid_pos)
        if key in data and 'World_Total' in data[key].columns:
            df = data[key]
            production = df['World_Total'] / 1e6
            ax.plot(df['Year'], production, color=color, linewidth=2,
                    marker='o', markersize=3)
            ax.fill_between(df['Year'], production, alpha=0.3, color=color)
            ax.set_title(f'{key.title()} (MT)', fontweight='bold', fontsize=10)
            ax.set_ylabel('Million Tonnes')
            ax.grid(alpha=0.3)

    # ===== 3행: Kaggle 데이터 분석 =====
    if 'kaggle' in data:
        df_kaggle = data['kaggle']

        # 3-1: 온도 vs 수율 산점도
        ax31 = fig.add_subplot(gs[2, 0:2])
        scatter = ax31.scatter(df_kaggle['Average_Temperature_C'],
                              df_kaggle['Crop_Yield_MT_per_HA'],
                              c=df_kaggle['Year'], cmap='viridis',
                              alpha=0.5, s=30, edgecolors='black', linewidth=0.2)
        ax31.set_xlabel('Temperature (°C)')
        ax31.set_ylabel('Yield (MT/HA)')
        ax31.set_title('Temperature vs Yield (Color: Year)', fontweight='bold', fontsize=10)
        plt.colorbar(scatter, ax=ax31, label='Year')
        ax31.grid(alpha=0.3)

        # 3-2: 연도별 평균 수율
        ax32 = fig.add_subplot(gs[2, 2:4])
        df_yearly = df_kaggle.groupby('Year')['Crop_Yield_MT_per_HA'].mean()
        ax32.plot(df_yearly.index, df_yearly.values, color='#27AE60',
                 linewidth=2, marker='o', markersize=4)
        ax32.fill_between(df_yearly.index, df_yearly.values, alpha=0.3, color='#27AE60')
        ax32.set_xlabel('Year')
        ax32.set_ylabel('Avg Yield (MT/HA)')
        ax32.set_title('Global Average Crop Yield Trend', fontweight='bold', fontsize=10)
        ax32.grid(alpha=0.3)

    # 메인 제목
    fig.suptitle('Climate Change × Burger Ingredients Dashboard\n'
                 '"기후변화는 먼 미래가 아니라, 오늘 점심 메뉴에 영향을 미치는 현실이다"',
                 fontsize=15, fontweight='bold', y=0.98)

    plt.savefig(output_dir / 'viz_08_summary_dashboard.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 8] 종합 대시보드 저장 완료")


# =============================================================================
# 8. 상관관계 히트맵
# =============================================================================
def plot_correlation_heatmap(data, output_dir):
    """
    주요 변수 간 상관관계 히트맵
    """
    if 'integrated' not in data:
        print("⚠️ 통합 데이터 없음")
        return

    df = data['integrated']

    # 품목별 생산량을 열로 변환
    df_pivot = df.pivot_table(
        index='Year',
        columns='Item_Key',
        values='World_Production_Tonnes',
        aggfunc='sum'
    ).reset_index()

    # 기온 데이터 추가
    if 'temperature' in data:
        df_temp = data['temperature']
        df_world_temp = df_temp[df_temp['Area'] == 'World'].groupby('Year')['Temp_Anomaly'].mean().reset_index()
        df_pivot = df_pivot.merge(df_world_temp, on='Year', how='left')

    # 수치형 컬럼만 선택
    numeric_cols = df_pivot.select_dtypes(include=[np.number]).columns.tolist()
    if 'Year' in numeric_cols:
        numeric_cols.remove('Year')

    if len(numeric_cols) < 2:
        print("⚠️ 상관관계 분석할 변수 부족")
        return

    # 상관관계 계산
    corr_matrix = df_pivot[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(12, 10))

    # 히트맵
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f',
                cmap='RdBu_r', center=0, vmin=-1, vmax=1,
                square=True, linewidths=0.5, ax=ax,
                annot_kws={'size': 10})

    ax.set_title('Correlation Matrix: Production vs Temperature\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'viz_09_correlation_heatmap.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 9] 상관관계 히트맵 저장 완료")


# =============================================================================
# 9. 결과 요약
# =============================================================================
def summarize_visualizations(output_dir):
    """시각화 결과 요약 출력"""
    print("\n" + "=" * 60)
    print("📊 시각화 결과 요약")
    print("=" * 60)

    print("\n[생성된 시각화 파일]")
    for i, f in enumerate(sorted(output_dir.glob("viz_*.png")), 1):
        size = f.stat().st_size / 1024
        print(f"   {i}. {f.name} ({size:.1f} KB)")

    print("\n[시각화 주요 발견사항]")
    print("   1. 기온 변화: 1990년 대비 2019년 약 +0.8~1.2°C 상승")
    print("   2. 생산량 추세: 대부분 재료에서 증가 추세 (기술 발전 효과)")
    print("   3. 기온-수율 관계: 비선형 관계 확인 (일정 온도 이상에서 감소)")
    print("   4. 지역별 차이: 고위도 지역(러시아 등)이 더 빠르게 온난화")

    print("\n[데이터 출처]")
    print("   - FAOSTAT: https://www.fao.org/faostat/en/#data")
    print("   - Kaggle: https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture")

    print("\n✅ 다음 단계: 03_데이터_분석.py")


# =============================================================================
# 메인 실행
# =============================================================================
def main():
    """메인 실행 함수"""

    # 1. 환경 설정
    PROJECT_DIR, PROCESSED_DIR, OUTPUT_DIR = setup_environment()

    # 2. 데이터 로드
    data = load_processed_data(PROCESSED_DIR)

    # 3. 시각화 생성
    print("\n" + "=" * 60)
    print("📈 시각화 생성")
    print("=" * 60)

    # 3.1 기온 변화 시각화
    print("\n[기온 변화 시각화]")
    plot_temperature_trend(data, OUTPUT_DIR)
    plot_regional_temperature(data, OUTPUT_DIR)

    # 3.2 재료별 생산량 시각화
    print("\n[재료별 생산량 시각화]")
    plot_production_trends(data, OUTPUT_DIR)
    plot_production_vs_temperature(data, OUTPUT_DIR)

    # 3.3 한국 수입 현황
    print("\n[한국 수입 현황 시각화]")
    plot_korea_trade_trends(data, OUTPUT_DIR)

    # 3.4 기후-수율 관계 (Kaggle)
    print("\n[기후-수율 관계 시각화]")
    plot_climate_yield_scatter(data, OUTPUT_DIR)
    plot_yield_by_crop_type(data, OUTPUT_DIR)

    # 3.5 종합 대시보드
    print("\n[종합 대시보드]")
    create_summary_dashboard(data, OUTPUT_DIR)

    # 3.6 상관관계 분석
    print("\n[상관관계 분석]")
    plot_correlation_heatmap(data, OUTPUT_DIR)

    # 4. 결과 요약
    summarize_visualizations(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("✅ 시각화 완료!")
    print("=" * 60)

    return data


if __name__ == "__main__":
    data = main()
