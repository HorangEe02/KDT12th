"""
02_1. 추가 데이터 시각화
기후 변화에 따른 햄버거 재료 영향 분석 - 보완 시각화

추가 시각화:
    1. 글로벌 기온 변화 추이 - 선 그래프 버전
    2. 주요 국가별 기온 변화 비교 - 가시성 향상 버전

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
    print("   02_1. 추가 데이터 시각화")
    print("=" * 60)
    print(f"\n✅ 시각화 환경 설정 완료")
    print(f"   - 데이터 경로: {PROCESSED_DIR}")
    print(f"   - 출력 경로: {OUTPUT_DIR}")

    return PROJECT_DIR, PROCESSED_DIR, OUTPUT_DIR


# =============================================================================
# 2. 데이터 로드
# =============================================================================
def load_processed_data(processed_dir):
    """전처리된 모든 데이터 로드"""
    print("\n📥 데이터 로드 중...")
    data = {}

    # 기온 데이터
    temp_path = processed_dir / 'temperature_processed.csv'
    if temp_path.exists():
        data['temperature'] = pd.read_csv(temp_path)
        print(f"   ✓ temperature: {len(data['temperature'])} rows")

    print(f"\n✅ 총 {len(data)}개 데이터셋 로드 완료")
    return data


# =============================================================================
# 3. 글로벌 기온 변화 추이 - 선 그래프 버전
# =============================================================================
def plot_temperature_trend_line(data, output_dir):
    """
    글로벌 기온 변화 추이 시각화 - 선 그래프 버전

    통계적 의미:
    - 1951-1980 기준 대비 기온 편차(anomaly) 표시
    - 파리협정 1.5°C 목표선 포함
    - 이동평균선으로 장기 추세 강조
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

    fig, ax = plt.subplots(figsize=(14, 7))

    # 선 그래프 - 기온 편차
    ax.plot(df_world['Year'], df_world['Temp_Anomaly'],
            color='#3498DB', linewidth=2.5, marker='o', markersize=6,
            markerfacecolor='white', markeredgewidth=2, markeredgecolor='#3498DB',
            label='Annual Temperature Anomaly', zorder=3)

    # 영역 채우기 (0 기준)
    ax.fill_between(df_world['Year'], 0, df_world['Temp_Anomaly'],
                    where=(df_world['Temp_Anomaly'] >= 0),
                    interpolate=True, alpha=0.3, color='#E74C3C', label='Above Baseline')
    ax.fill_between(df_world['Year'], 0, df_world['Temp_Anomaly'],
                    where=(df_world['Temp_Anomaly'] < 0),
                    interpolate=True, alpha=0.3, color='#3498DB', label='Below Baseline')

    # 5년 이동평균선
    if len(df_world) >= 5:
        df_world['MA_5'] = df_world['Temp_Anomaly'].rolling(window=5, center=True).mean()
        ax.plot(df_world['Year'], df_world['MA_5'],
                color='#E74C3C', linewidth=3, linestyle='-',
                label='5-Year Moving Average', zorder=4)

    # 추세선 (선형 회귀)
    z = np.polyfit(df_world['Year'], df_world['Temp_Anomaly'], 1)
    p = np.poly1d(z)
    ax.plot(df_world['Year'], p(df_world['Year']),
            'k--', linewidth=2, alpha=0.7, label=f'Linear Trend (slope: {z[0]:.4f}°C/year)')

    # 기준선
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1.5, alpha=0.7)
    ax.axhline(y=1.5, color='#C0392B', linestyle='--', linewidth=2.5,
               label='Paris Agreement 1.5°C Target')

    # 최신 연도 데이터 강조
    latest_year = df_world['Year'].max()
    latest_temp = df_world[df_world['Year'] == latest_year]['Temp_Anomaly'].values[0]
    ax.scatter([latest_year], [latest_temp], s=150, color='#E74C3C',
               edgecolors='black', linewidth=2, zorder=5)
    ax.annotate(f'{latest_year}\n{latest_temp:.2f}°C',
                xy=(latest_year, latest_temp),
                xytext=(latest_year - 3, latest_temp + 0.25),
                fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

    # 첫 연도 데이터 표시
    first_year = df_world['Year'].min()
    first_temp = df_world[df_world['Year'] == first_year]['Temp_Anomaly'].values[0]
    ax.annotate(f'{first_year}\n{first_temp:.2f}°C',
                xy=(first_year, first_temp),
                xytext=(first_year + 2, first_temp - 0.25),
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

    ax.set_xlabel('Year', fontsize=13, fontweight='bold')
    ax.set_ylabel('Temperature Anomaly (°C)\nBaseline: 1951-1980', fontsize=13, fontweight='bold')
    ax.set_title('Global Land Surface Temperature Change (1990-2019)\n'
                 'Line Graph Version | Source: FAOSTAT / NASA GISTEMP',
                 fontsize=15, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax.grid(axis='both', alpha=0.3, linestyle='--')
    ax.set_xlim(df_world['Year'].min() - 1, df_world['Year'].max() + 1)

    # Y축 범위 설정
    y_min = min(df_world['Temp_Anomaly'].min() - 0.3, -0.5)
    y_max = max(df_world['Temp_Anomaly'].max() + 0.5, 1.7)
    ax.set_ylim(y_min, y_max)

    plt.tight_layout()
    plt.savefig(output_dir / 'viz_01_1_temperature_trend_line.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 1-1] 기온 변화 추이 (선 그래프) 저장 완료")

    # 통계 요약
    print(f"\n📊 기온 변화 통계:")
    print(f"   - {first_year}년: {first_temp:.3f}°C")
    print(f"   - {latest_year}년: {latest_temp:.3f}°C")
    print(f"   - 변화량: +{latest_temp - first_temp:.3f}°C")
    print(f"   - 연평균 상승률: {z[0]:.4f}°C/year")

    return df_world


# =============================================================================
# 4. 주요 국가별 기온 변화 비교 - 가시성 향상 버전
# =============================================================================
def plot_regional_temperature_selected(data, output_dir):
    """
    주요 국가별 기온 변화 비교 시각화 - 가시성 향상 버전

    선별 국가: World, 미국, 중국, 한국 (4개 국가만 선별하여 가시성 향상)
    """
    if 'temperature' not in data:
        print("⚠️ 기온 데이터 없음")
        return

    df = data['temperature']

    # 주요 국가 선택 (가시성을 위해 4개만 선별)
    selected_countries = {
        'World': {'color': '#2C3E50', 'marker': 's', 'name': 'World (Global Average)'},
        'United States of America': {'color': '#3498DB', 'marker': '^', 'name': 'United States'},
        'China': {'color': '#E74C3C', 'marker': 'o', 'name': 'China'},
        'Republic of Korea': {'color': '#27AE60', 'marker': 'D', 'name': 'South Korea'}
    }

    fig, ax = plt.subplots(figsize=(14, 8))

    for country, config in selected_countries.items():
        df_country = df[df['Area'] == country]
        if len(df_country) > 0:
            df_agg = df_country.groupby('Year')['Temp_Anomaly'].mean().reset_index()

            # 선 그래프
            ax.plot(df_agg['Year'], df_agg['Temp_Anomaly'],
                    linewidth=3, label=config['name'], color=config['color'],
                    marker=config['marker'], markersize=8, markerfacecolor='white',
                    markeredgewidth=2, markeredgecolor=config['color'])

            # 최신 값 표시
            latest_year = df_agg['Year'].max()
            latest_temp = df_agg[df_agg['Year'] == latest_year]['Temp_Anomaly'].values[0]

            # 국가별 최종 값 레이블
            ax.annotate(f'{latest_temp:.2f}°C',
                       xy=(latest_year, latest_temp),
                       xytext=(5, 0), textcoords='offset points',
                       fontsize=11, fontweight='bold', color=config['color'],
                       va='center')

    # 기준선
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1.5, alpha=0.7, label='Baseline (0°C)')
    ax.axhline(y=1.5, color='#C0392B', linestyle='--', linewidth=2.5, alpha=0.8,
               label='Paris Agreement 1.5°C Target')

    ax.set_xlabel('Year', fontsize=13, fontweight='bold')
    ax.set_ylabel('Temperature Anomaly (°C)', fontsize=13, fontweight='bold')
    ax.set_title('Temperature Change Comparison: Key Countries\n'
                 'Selected for Better Visibility | Source: FAOSTAT / NASA GISTEMP',
                 fontsize=15, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11, framealpha=0.95,
              fancybox=True, shadow=True)
    ax.grid(alpha=0.3, linestyle='--')

    # Y축 범위 조정
    ax.set_ylim(-0.6, 2.0)

    plt.tight_layout()
    plt.savefig(output_dir / 'viz_02_1_regional_temperature_selected.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 2-1] 주요 국가별 기온 변화 (가시성 향상) 저장 완료")

    # 국가별 변화량 요약
    print(f"\n📊 주요 국가별 기온 변화 요약:")
    for country, config in selected_countries.items():
        df_country = df[df['Area'] == country]
        if len(df_country) > 0:
            df_agg = df_country.groupby('Year')['Temp_Anomaly'].mean().reset_index()
            first_temp = df_agg['Temp_Anomaly'].iloc[0]
            last_temp = df_agg['Temp_Anomaly'].iloc[-1]
            change = last_temp - first_temp
            print(f"   - {config['name']}: {first_temp:.2f}°C → {last_temp:.2f}°C (변화: +{change:.2f}°C)")


def plot_regional_temperature_subplot(data, output_dir):
    """
    주요 국가별 기온 변화 - 개별 서브플롯 버전
    각 국가를 개별 그래프로 표시하여 세부 정보 강조
    """
    if 'temperature' not in data:
        print("⚠️ 기온 데이터 없음")
        return

    df = data['temperature']

    # 주요 국가 선택
    selected_countries = {
        'World': {'color': '#2C3E50', 'name': 'World (Global)'},
        'United States of America': {'color': '#3498DB', 'name': 'United States'},
        'China': {'color': '#E74C3C', 'name': 'China'},
        'Republic of Korea': {'color': '#27AE60', 'name': 'South Korea'}
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for ax, (country, config) in zip(axes, selected_countries.items()):
        df_country = df[df['Area'] == country]
        if len(df_country) > 0:
            df_agg = df_country.groupby('Year')['Temp_Anomaly'].mean().reset_index()

            # 영역 그래프 배경
            ax.fill_between(df_agg['Year'], 0, df_agg['Temp_Anomaly'],
                           where=(df_agg['Temp_Anomaly'] >= 0),
                           interpolate=True, alpha=0.3, color='#E74C3C')
            ax.fill_between(df_agg['Year'], 0, df_agg['Temp_Anomaly'],
                           where=(df_agg['Temp_Anomaly'] < 0),
                           interpolate=True, alpha=0.3, color='#3498DB')

            # 선 그래프
            ax.plot(df_agg['Year'], df_agg['Temp_Anomaly'],
                    linewidth=3, color=config['color'],
                    marker='o', markersize=6, markerfacecolor='white',
                    markeredgewidth=2, markeredgecolor=config['color'])

            # 추세선
            z = np.polyfit(df_agg['Year'], df_agg['Temp_Anomaly'], 1)
            p = np.poly1d(z)
            ax.plot(df_agg['Year'], p(df_agg['Year']),
                    'k--', linewidth=2, alpha=0.6)

            # 기준선
            ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
            ax.axhline(y=1.5, color='red', linestyle='--', linewidth=2, alpha=0.7)

            # 통계 정보 표시
            first_temp = df_agg['Temp_Anomaly'].iloc[0]
            last_temp = df_agg['Temp_Anomaly'].iloc[-1]
            change = last_temp - first_temp

            stats_text = (f"Start: {first_temp:.2f}°C\n"
                         f"End: {last_temp:.2f}°C\n"
                         f"Change: +{change:.2f}°C\n"
                         f"Trend: {z[0]*10:.3f}°C/decade")

            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=10, fontweight='bold', verticalalignment='top',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

            ax.set_title(config['name'], fontsize=14, fontweight='bold', color=config['color'])
            ax.set_xlabel('Year', fontsize=11)
            ax.set_ylabel('Temperature Anomaly (°C)', fontsize=11)
            ax.grid(alpha=0.3, linestyle='--')
            ax.set_ylim(-0.6, 2.0)

    plt.suptitle('Temperature Change by Country: Detailed View\n'
                 'Source: FAOSTAT / NASA GISTEMP',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'viz_02_2_regional_temperature_subplot.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("✅ [Figure 2-2] 주요 국가별 기온 변화 (서브플롯) 저장 완료")


# =============================================================================
# 5. 결과 요약
# =============================================================================
def summarize_visualizations(output_dir):
    """시각화 결과 요약 출력"""
    print("\n" + "=" * 60)
    print("📊 추가 시각화 결과 요약")
    print("=" * 60)

    print("\n[생성된 추가 시각화 파일]")
    new_files = ['viz_01_1_temperature_trend_line.png',
                 'viz_02_1_regional_temperature_selected.png',
                 'viz_02_2_regional_temperature_subplot.png']

    for i, fname in enumerate(new_files, 1):
        f = output_dir / fname
        if f.exists():
            size = f.stat().st_size / 1024
            print(f"   {i}. {fname} ({size:.1f} KB)")

    print("\n[추가 시각화 설명]")
    print("   1. viz_01_1: 글로벌 기온 변화 선 그래프")
    print("      - 연간 기온 편차를 선 그래프로 표현")
    print("      - 5년 이동평균선으로 장기 추세 강조")
    print("      - 선형 추세선 및 기울기 표시")
    print()
    print("   2. viz_02_1: 주요 국가별 기온 변화 (단일 그래프)")
    print("      - World, 미국, 중국, 한국 4개국만 선별")
    print("      - 가시성을 높이기 위해 국가 수 제한")
    print("      - 각 국가별 마커 스타일 차별화")
    print()
    print("   3. viz_02_2: 주요 국가별 기온 변화 (서브플롯)")
    print("      - 4개 국가를 개별 그래프로 상세 표시")
    print("      - 각 국가별 통계 정보 포함")


# =============================================================================
# 메인 실행
# =============================================================================
def main():
    """메인 실행 함수"""

    # 1. 환경 설정
    PROJECT_DIR, PROCESSED_DIR, OUTPUT_DIR = setup_environment()

    # 2. 데이터 로드
    data = load_processed_data(PROCESSED_DIR)

    # 3. 추가 시각화 생성
    print("\n" + "=" * 60)
    print("📈 추가 시각화 생성")
    print("=" * 60)

    # 3.1 글로벌 기온 변화 - 선 그래프
    print("\n[Figure 1-1: 글로벌 기온 변화 선 그래프]")
    plot_temperature_trend_line(data, OUTPUT_DIR)

    # 3.2 주요 국가별 기온 변화 - 가시성 향상 버전
    print("\n[Figure 2-1: 주요 국가별 기온 변화 (단일 그래프)]")
    plot_regional_temperature_selected(data, OUTPUT_DIR)

    # 3.3 주요 국가별 기온 변화 - 서브플롯 버전
    print("\n[Figure 2-2: 주요 국가별 기온 변화 (서브플롯)]")
    plot_regional_temperature_subplot(data, OUTPUT_DIR)

    # 4. 결과 요약
    summarize_visualizations(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("✅ 추가 시각화 완료!")
    print("=" * 60)

    return data


if __name__ == "__main__":
    data = main()
