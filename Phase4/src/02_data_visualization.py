"""
02. 데이터 시각화 (소스류 분석)

프로젝트명: 기후 변화가 햄버거 소스류 원재료에 미치는 영향 분석
분석 대상: 토마토(케찹), 계란(마요네즈), 고추(스리라차)
핵심 메시지: "당신의 햄버거 소스 가격은 지구 반대편 기후에 달려있다"

데이터 출처:
- FAOSTAT (https://www.fao.org/faostat/en/#data)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 환경 설정
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'output' / 'processed'  # 전처리된 데이터 경로
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 시각화 스타일 설정
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.unicode_minus'] = False

# 한글 폰트 설정 (macOS)
try:
    plt.rcParams['font.family'] = 'AppleGothic'
except:
    pass

# 소스류 색상 팔레트
SAUCE_COLORS = {
    'Tomatoes': '#E74C3C',       # 빨간색 (케찹)
    'Eggs': '#F1C40F',           # 노란색 (마요네즈)
    'Chillies_dry': '#C0392B',   # 진한 빨간색 (스리라차)
    'Chillies_green': '#27AE60', # 초록색 (풋고추)
    'Temperature': '#3498DB'     # 파란색 (기온)
}

print("=" * 60)
print("📊 소스류 데이터 시각화")
print("=" * 60)
print("   분석 대상:")
print("   🍅 케찹 색상: #E74C3C")
print("   🥚 마요 색상: #F1C40F")
print("   🌶️ 스리라차 색상: #C0392B")
print()

# ============================================================
# 2. 데이터 로드
# ============================================================
def load_sauce_data():
    """전처리된 소스류 데이터 로드"""
    data = {}

    files = {
        'Tomatoes': 'tomatoes_production.csv',
        'Eggs': 'eggs_production.csv',
        'Chillies_dry': 'chillies_dry_production.csv',
        'Chillies_green': 'chillies_green_production.csv',
        'Temperature': 'temperature_processed.csv',
        'Integrated': 'sauce_ingredients_integrated.csv',
        'Climate_Agri': 'climate_agriculture_processed.csv'
    }

    print("📂 데이터 로드 중...")
    for name, filename in files.items():
        filepath = DATA_DIR / filename
        if filepath.exists():
            data[name] = pd.read_csv(filepath)
            print(f"   ✓ {name}: {len(data[name])} rows")
        else:
            print(f"   ⚠️ {name}: 파일 없음 ({filename})")

    return data


# ============================================================
# 3. 기온 변화 시각화
# ============================================================
def plot_temperature_trend(data):
    """
    글로벌 기온 변화 추이 (소스 원료 생산국 포함)
    """
    if 'Temperature' not in data:
        print("   ⚠️ 기온 데이터 없음")
        return None

    df = data['Temperature']

    # World_Avg 또는 World 컬럼 찾기
    temp_col = None
    for col in ['World_Avg', 'World']:
        if col in df.columns:
            temp_col = col
            break

    if temp_col is None:
        # 숫자 컬럼의 평균 사용
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != 'Year']
        if numeric_cols:
            df['World_Avg'] = df[numeric_cols].mean(axis=1)
            temp_col = 'World_Avg'
        else:
            print("   ⚠️ 기온 데이터 컬럼 없음")
            return None

    fig, ax = plt.subplots(figsize=(14, 6))

    # 막대 색상 (기온에 따라)
    colors = ['#3498DB' if v < 0.5 else '#E74C3C' if v > 1.0 else '#F39C12'
              for v in df[temp_col]]

    bars = ax.bar(df['Year'], df[temp_col], color=colors,
                  edgecolor='black', linewidth=0.3, alpha=0.85)

    # 추세선 (2차 다항식)
    z = np.polyfit(df['Year'], df[temp_col], 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(df['Year'].min(), df['Year'].max(), 100)
    ax.plot(x_smooth, p(x_smooth), 'k--', linewidth=2, label='Trend')

    # 기준선
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    ax.axhline(y=1.5, color='red', linestyle='--', linewidth=2,
               label='Paris Agreement 1.5°C')

    # 주요 이벤트 표시
    events = {
        2012: 'US Drought',
        2019: 'EU Heatwave',
        2022: 'Sriracha Crisis'
    }

    for year, event in events.items():
        if year in df['Year'].values:
            idx = df[df['Year'] == year].index[0]
            val = df.loc[idx, temp_col]
            ax.annotate(event, xy=(year, val),
                       xytext=(year, val + 0.3),
                       fontsize=9, ha='center',
                       arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Temperature Anomaly (°C)', fontsize=12)
    ax.set_title('Global Temperature Change & Major Sauce Supply Events\n'
                 'Source: FAOSTAT / NASA GISTEMP', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_01_temperature.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 1] 기온 변화 추이 저장")

    return df


def plot_producer_temperature(data):
    """
    소스 원료 주요 생산국 기온 비교
    """
    if 'Temperature' not in data:
        return

    df = data['Temperature']

    # 주요 생산국 선택
    countries = {
        'World_Avg': ('Global', 'black'),
        'China': ('China (Tomato, Egg, Chilli)', '#E74C3C'),
        'India': ('India (Chilli)', '#C0392B'),
        'United States of America': ('USA (Tomato, Egg)', '#3498DB'),
        'Mexico': ('Mexico (Chilli/Sriracha)', '#27AE60'),
        'Turkey': ('Turkey (Tomato)', '#E67E22')
    }

    fig, ax = plt.subplots(figsize=(14, 7))

    plotted = False
    for col, (label, color) in countries.items():
        if col in df.columns:
            style = '-' if col == 'World_Avg' else '--'
            lw = 2.5 if col == 'World_Avg' else 1.5
            ax.plot(df['Year'], df[col], label=label,
                    color=color, linewidth=lw, linestyle=style)
            plotted = True

    if not plotted:
        print("   ⚠️ 생산국 기온 데이터 없음")
        plt.close()
        return

    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax.axhline(y=1.5, color='red', linestyle=':', linewidth=1.5, alpha=0.7)

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Temperature Anomaly (°C)', fontsize=12)
    ax.set_title('Temperature Change in Major Sauce Ingredient Producing Countries\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_02_producer_temp.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 2] 생산국 기온 비교 저장")


# ============================================================
# 4. 소스 원료별 생산량 시각화
# ============================================================
def plot_tomato_production(data):
    """
    토마토 생산량 추이 (케찹 원료)
    """
    if 'Tomatoes' not in data:
        print("   ⚠️ 토마토 데이터 없음")
        return

    df = data['Tomatoes']

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 1. 전체 생산량 추이
    ax1 = axes[0]

    if 'World_Total' in df.columns:
        production = df['World_Total'] / 1e6
    else:
        # World_Total 없으면 숫자 컬럼 합계
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != 'Year']
        df['World_Total'] = df[numeric_cols].sum(axis=1)
        production = df['World_Total'] / 1e6

    ax1.fill_between(df['Year'], production, alpha=0.3, color=SAUCE_COLORS['Tomatoes'])
    ax1.plot(df['Year'], production, color=SAUCE_COLORS['Tomatoes'],
             linewidth=2.5, marker='o', markersize=4)

    # 변화율
    if len(production) > 1:
        change = ((production.iloc[-1] - production.iloc[0]) / production.iloc[0]) * 100
        ax1.annotate(f'+{change:.1f}%', xy=(df['Year'].iloc[-1], production.iloc[-1]),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=12, fontweight='bold', color='#27AE60')

    ax1.set_xlabel('Year', fontsize=11)
    ax1.set_ylabel('Production (Million Tonnes)', fontsize=11)
    ax1.set_title('Global Tomato Production (Ketchup)\nSource: FAOSTAT',
                  fontsize=12, fontweight='bold')
    ax1.grid(alpha=0.3)

    # 2. 주요 생산국 비중
    ax2 = axes[1]

    latest_year = df['Year'].max()
    latest_row = df[df['Year'] == latest_year].iloc[0]

    exclude_cols = ['Year', 'World_Total', 'Temp_Anomaly', 'Item']
    countries_cols = [c for c in df.columns if c not in exclude_cols and
                      pd.notna(latest_row.get(c)) and isinstance(latest_row.get(c), (int, float))]

    if countries_cols:
        country_prod = {col: latest_row[col] for col in countries_cols}
        country_prod = dict(sorted(country_prod.items(), key=lambda x: x[1], reverse=True)[:6])

        colors = plt.cm.Reds(np.linspace(0.3, 0.8, len(country_prod)))
        bars = ax2.barh(list(country_prod.keys()),
                        [v/1e6 for v in country_prod.values()],
                        color=colors, edgecolor='black', linewidth=0.5)

        ax2.set_xlabel('Production (Million Tonnes)', fontsize=11)
        ax2.set_title(f'Top Tomato Producers ({int(latest_year)})', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)

        # 값 표시
        for bar, (country, val) in zip(bars, country_prod.items()):
            ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{val/1e6:.1f}M', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_03_tomato.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 3] 토마토(케찹) 생산량 저장")
    print(f"   - 최근 글로벌 생산량: {production.iloc[-1]:.1f} 백만톤")


def plot_eggs_production(data):
    """
    계란 생산량 추이 (마요네즈 원료)
    """
    if 'Eggs' not in data:
        print("   ⚠️ 계란 데이터 없음")
        return

    df = data['Eggs']

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 1. 전체 생산량 추이
    ax1 = axes[0]

    if 'World_Total' in df.columns:
        production = df['World_Total'] / 1e6
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != 'Year']
        df['World_Total'] = df[numeric_cols].sum(axis=1)
        production = df['World_Total'] / 1e6

    ax1.fill_between(df['Year'], production, alpha=0.3, color=SAUCE_COLORS['Eggs'])
    ax1.plot(df['Year'], production, color=SAUCE_COLORS['Eggs'],
             linewidth=2.5, marker='o', markersize=4)

    # AI 발생 연도 표시
    ai_events = {2015: 'AI Outbreak (USA)', 2022: 'AI Outbreak (Global)'}
    for year, label in ai_events.items():
        if year in df['Year'].values:
            ax1.axvline(x=year, color='red', linestyle='--', alpha=0.5)
            idx = df[df['Year'] == year].index[0]
            prod_val = production.iloc[list(df.index).index(idx)]
            ax1.annotate(label, xy=(year, prod_val),
                        xytext=(year+0.5, prod_val+2),
                        fontsize=9, color='red')

    if len(production) > 1:
        change = ((production.iloc[-1] - production.iloc[0]) / production.iloc[0]) * 100
        ax1.annotate(f'+{change:.1f}%', xy=(df['Year'].iloc[-1], production.iloc[-1]),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=12, fontweight='bold', color='#27AE60')

    ax1.set_xlabel('Year', fontsize=11)
    ax1.set_ylabel('Production (Million Tonnes)', fontsize=11)
    ax1.set_title('Global Egg Production (Mayonnaise)\nSource: FAOSTAT',
                  fontsize=12, fontweight='bold')
    ax1.grid(alpha=0.3)

    # 2. 주요 생산국 비중
    ax2 = axes[1]

    latest_year = df['Year'].max()
    latest_row = df[df['Year'] == latest_year].iloc[0]

    exclude_cols = ['Year', 'World_Total', 'Temp_Anomaly', 'Item']
    countries_cols = [c for c in df.columns if c not in exclude_cols and
                      pd.notna(latest_row.get(c)) and isinstance(latest_row.get(c), (int, float))]

    if countries_cols:
        country_prod = {col: latest_row[col] for col in countries_cols}
        country_prod = dict(sorted(country_prod.items(), key=lambda x: x[1], reverse=True)[:6])

        colors = plt.cm.YlOrBr(np.linspace(0.3, 0.8, len(country_prod)))
        bars = ax2.barh(list(country_prod.keys()),
                        [v/1e6 for v in country_prod.values()],
                        color=colors, edgecolor='black', linewidth=0.5)

        ax2.set_xlabel('Production (Million Tonnes)', fontsize=11)
        ax2.set_title(f'Top Egg Producers ({int(latest_year)})', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_04_eggs.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 4] 계란(마요네즈) 생산량 저장")
    print(f"   - 최근 글로벌 생산량: {production.iloc[-1]:.1f} 백만톤")


def plot_chillies_production(data):
    """
    고추 생산량 추이 (스리라차 원료)
    """
    if 'Chillies_dry' not in data:
        print("   ⚠️ 고추 데이터 없음")
        return

    df_dry = data['Chillies_dry']

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 1. 건고추 생산량 추이
    ax1 = axes[0]

    if 'World_Total' in df_dry.columns:
        production = df_dry['World_Total'] / 1e6
    else:
        numeric_cols = df_dry.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != 'Year']
        df_dry['World_Total'] = df_dry[numeric_cols].sum(axis=1)
        production = df_dry['World_Total'] / 1e6

    ax1.fill_between(df_dry['Year'], production, alpha=0.3, color=SAUCE_COLORS['Chillies_dry'])
    ax1.plot(df_dry['Year'], production, color=SAUCE_COLORS['Chillies_dry'],
             linewidth=2.5, marker='o', markersize=4)

    # 2022 스리라차 위기 표시
    if 2022 in df_dry['Year'].values:
        ax1.axvline(x=2022, color='darkred', linestyle='--', linewidth=2)
        idx_2022 = df_dry[df_dry['Year'] == 2022].index[0]
        prod_2022 = production.iloc[list(df_dry.index).index(idx_2022)]
        ax1.annotate('Sriracha Crisis\n(Mexico Drought)',
                    xy=(2022, prod_2022),
                    xytext=(2018, production.max() * 0.9),
                    fontsize=10, color='darkred', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='darkred'))

    if len(production) > 1:
        change = ((production.iloc[-1] - production.iloc[0]) / production.iloc[0]) * 100
        color_text = '#27AE60' if change > 0 else '#E74C3C'
        ax1.annotate(f'{change:+.1f}%', xy=(df_dry['Year'].iloc[-1], production.iloc[-1]),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=12, fontweight='bold', color=color_text)

    ax1.set_xlabel('Year', fontsize=11)
    ax1.set_ylabel('Production (Million Tonnes)', fontsize=11)
    ax1.set_title('Global Dry Chilli Production (Sriracha)\nSource: FAOSTAT',
                  fontsize=12, fontweight='bold')
    ax1.grid(alpha=0.3)

    # 2. 연간 변화율 (변동성 시각화)
    ax2 = axes[1]

    yoy_change = production.pct_change() * 100

    colors = ['#27AE60' if v > 0 else '#E74C3C' for v in yoy_change.fillna(0)]
    ax2.bar(df_dry['Year'][1:], yoy_change[1:], color=colors[1:],
            edgecolor='black', linewidth=0.3)
    ax2.axhline(y=0, color='black', linewidth=1)

    # 표준편차 표시
    std = yoy_change.std()
    ax2.axhline(y=std, color='gray', linestyle='--', alpha=0.7, label=f'+1σ ({std:.1f}%)')
    ax2.axhline(y=-std, color='gray', linestyle='--', alpha=0.7, label=f'-1σ ({-std:.1f}%)')

    ax2.set_xlabel('Year', fontsize=11)
    ax2.set_ylabel('Year-over-Year Change (%)', fontsize=11)
    ax2.set_title('Dry Chilli Production Volatility\n(High variability = Climate sensitivity)',
                  fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_05_chillies.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 5] 고추(스리라차) 생산량 저장")
    print(f"   - 건고추 생산량 변동성 (SD): {std:.2f}%")


# ============================================================
# 5. 생산량 vs 기온 관계 시각화
# ============================================================
def plot_sauce_production_vs_temp(data):
    """
    소스 원료 생산량과 기온 변화 동시 시각화
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    items = [
        ('Tomatoes', 'Tomato (Ketchup)', SAUCE_COLORS['Tomatoes']),
        ('Eggs', 'Eggs (Mayonnaise)', SAUCE_COLORS['Eggs']),
        ('Chillies_dry', 'Chilli (Sriracha)', SAUCE_COLORS['Chillies_dry'])
    ]

    # 기온 데이터 준비
    df_temp = data.get('Temperature')

    for ax, (key, title, color) in zip(axes, items):
        if key not in data:
            continue

        df = data[key].copy()

        # World_Total 확인/생성
        if 'World_Total' not in df.columns:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [c for c in numeric_cols if c != 'Year']
            df['World_Total'] = df[numeric_cols].sum(axis=1)

        # 왼쪽 축: 생산량
        ax.set_xlabel('Year')
        ax.set_ylabel('Production (Million Tonnes)', color=color)
        line1 = ax.plot(df['Year'], df['World_Total']/1e6,
                       color=color, linewidth=2.5, marker='o',
                       markersize=4, label='Production')
        ax.tick_params(axis='y', labelcolor=color)
        ax.fill_between(df['Year'], df['World_Total']/1e6, alpha=0.2, color=color)

        # 오른쪽 축: 기온
        ax2 = ax.twinx()
        if df_temp is not None:
            # 기온 컬럼 찾기
            temp_col = None
            for col in ['World_Avg', 'World']:
                if col in df_temp.columns:
                    temp_col = col
                    break

            if temp_col:
                # 연도 범위 맞추기
                df_temp_filtered = df_temp[df_temp['Year'].isin(df['Year'])]
                if len(df_temp_filtered) > 0:
                    line2 = ax2.plot(df_temp_filtered['Year'], df_temp_filtered[temp_col],
                                    color='#3498DB', linewidth=2, linestyle='--',
                                    marker='s', markersize=3, label='Temperature')
                    ax2.set_ylabel('Temp Anomaly (°C)', color='#3498DB')
                    ax2.tick_params(axis='y', labelcolor='#3498DB')

                    lines = line1 + line2
                    labels = [l.get_label() for l in lines]
                    ax.legend(lines, labels, loc='upper left', fontsize=9)

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(alpha=0.3)

    plt.suptitle('Sauce Ingredients: Production vs Temperature Anomaly\n'
                 'Source: FAOSTAT', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_06_prod_vs_temp.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 6] 생산량-기온 비교 저장")


def plot_temp_yield_scatter(data):
    """
    기온과 생산량 간의 산점도
    """
    if 'Integrated' not in data:
        print("   ⚠️ 통합 데이터 없음")
        return

    df_integrated = data['Integrated']

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    items = [
        ('tomatoes', 'Tomato', SAUCE_COLORS['Tomatoes']),
        ('eggs', 'Eggs', SAUCE_COLORS['Eggs']),
        ('chillies_dry', 'Chilli', SAUCE_COLORS['Chillies_dry'])
    ]

    for ax, (key, title, color) in zip(axes, items):
        df_item = df_integrated[df_integrated['Item_Key'] == key].dropna(
            subset=['World_Production_Tonnes', 'Temp_Anomaly_C']
        )

        if len(df_item) < 3:
            ax.set_title(f'{title}\n(Insufficient data)')
            continue

        x = df_item['Temp_Anomaly_C'].values
        y = df_item['World_Production_Tonnes'].values / 1e6

        # 산점도
        ax.scatter(x, y, c=color, s=60, alpha=0.7, edgecolors='black', linewidth=0.5)

        # 선형 회귀선
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, p(x_line), 'k--', linewidth=2, label='Linear Trend')

        # 상관계수 표시
        corr, pval = pearsonr(x, y)
        sig = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''
        ax.text(0.05, 0.95, f'r = {corr:.3f}{sig}\np = {pval:.4f}',
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel('Temperature Anomaly (°C)', fontsize=11)
        ax.set_ylabel('Production (Million Tonnes)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(alpha=0.3)

    plt.suptitle('Temperature vs Production: Scatter Analysis\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_07_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 7] 산점도 분석 저장")


# ============================================================
# 6. 통합 비교 시각화
# ============================================================
def plot_all_sauce_comparison(data):
    """
    모든 소스 원료 생산량 비교
    """
    fig, ax = plt.subplots(figsize=(14, 7))

    items = [
        ('Tomatoes', 'Tomato (Ketchup)', SAUCE_COLORS['Tomatoes']),
        ('Eggs', 'Eggs (Mayonnaise)', SAUCE_COLORS['Eggs']),
        ('Chillies_dry', 'Dry Chilli (Sriracha)', SAUCE_COLORS['Chillies_dry']),
        ('Chillies_green', 'Green Chilli', SAUCE_COLORS['Chillies_green'])
    ]

    for key, label, color in items:
        if key not in data:
            continue

        df = data[key].copy()

        if 'World_Total' not in df.columns:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [c for c in numeric_cols if c != 'Year']
            df['World_Total'] = df[numeric_cols].sum(axis=1)

        # 정규화 (첫 해 기준 100)
        production_norm = (df['World_Total'] / df['World_Total'].iloc[0]) * 100

        ax.plot(df['Year'], production_norm, label=label, color=color,
                linewidth=2.5, marker='o', markersize=4)

    ax.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Production Index (Base Year = 100)', fontsize=12)
    ax.set_title('Sauce Ingredient Production Trends (Normalized)\n'
                 'Source: FAOSTAT', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_08_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 8] 소스 원료 비교 저장")


# ============================================================
# 7. 종합 대시보드
# ============================================================
def create_sauce_dashboard(data):
    """
    소스류 분석 종합 대시보드
    """
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    # ===== 1행: 기온 변화 (전체 너비) =====
    ax1 = fig.add_subplot(gs[0, :])

    if 'Temperature' in data:
        df_temp = data['Temperature']
        temp_col = 'World_Avg' if 'World_Avg' in df_temp.columns else 'World'

        if temp_col in df_temp.columns:
            colors = ['#3498DB' if v < 0.5 else '#E74C3C' if v > 1.0 else '#F39C12'
                      for v in df_temp[temp_col]]
            ax1.bar(df_temp['Year'], df_temp[temp_col], color=colors,
                    edgecolor='black', linewidth=0.2, alpha=0.85)
            ax1.axhline(y=1.5, color='red', linestyle='--', linewidth=2)

            if 2022 in df_temp['Year'].values:
                ax1.axvline(x=2022, color='darkred', linestyle=':', linewidth=2, alpha=0.7)
                ax1.text(2022, 1.4, 'Sriracha\nCrisis', fontsize=9, color='darkred', ha='center')

    ax1.set_title('Global Temperature Anomaly | Source: FAOSTAT/NASA',
                  fontweight='bold', fontsize=12)
    ax1.set_ylabel('Temp Anomaly (°C)')
    ax1.grid(axis='y', alpha=0.3)

    # ===== 2행: 소스 원료별 생산량 =====
    items = [
        ('Tomatoes', gs[1, 0], SAUCE_COLORS['Tomatoes'], 'Tomato\n(Ketchup)'),
        ('Eggs', gs[1, 1], SAUCE_COLORS['Eggs'], 'Eggs\n(Mayonnaise)'),
        ('Chillies_dry', gs[1, 2], SAUCE_COLORS['Chillies_dry'], 'Chilli\n(Sriracha)')
    ]

    for key, grid_pos, color, title in items:
        ax = fig.add_subplot(grid_pos)
        if key in data:
            df = data[key].copy()

            if 'World_Total' not in df.columns:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                numeric_cols = [c for c in numeric_cols if c != 'Year']
                df['World_Total'] = df[numeric_cols].sum(axis=1)

            production = df['World_Total'] / 1e6
            ax.plot(df['Year'], production, color=color, linewidth=2,
                    marker='o', markersize=3)
            ax.fill_between(df['Year'], production, alpha=0.3, color=color)

        ax.set_title(title, fontweight='bold', fontsize=11)
        ax.set_ylabel('Million Tonnes')
        ax.grid(alpha=0.3)

    # ===== 3행: 연간 변화율 비교 =====
    items_row3 = [
        ('Tomatoes', gs[2, 0], SAUCE_COLORS['Tomatoes'], 'Tomato YoY %'),
        ('Eggs', gs[2, 1], SAUCE_COLORS['Eggs'], 'Eggs YoY %'),
        ('Chillies_dry', gs[2, 2], SAUCE_COLORS['Chillies_dry'], 'Chilli YoY %')
    ]

    for key, grid_pos, color, title in items_row3:
        ax = fig.add_subplot(grid_pos)
        if key in data:
            df = data[key].copy()

            if 'World_Total' not in df.columns:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                numeric_cols = [c for c in numeric_cols if c != 'Year']
                df['World_Total'] = df[numeric_cols].sum(axis=1)

            yoy = df['World_Total'].pct_change() * 100
            bar_colors = ['#27AE60' if v > 0 else '#E74C3C' for v in yoy.fillna(0)]
            ax.bar(df['Year'][1:], yoy[1:], color=bar_colors[1:],
                   edgecolor='black', linewidth=0.3)
            ax.axhline(y=0, color='black', linewidth=1)

        ax.set_title(title, fontweight='bold', fontsize=11)
        ax.set_ylabel('Change (%)')
        ax.grid(axis='y', alpha=0.3)

    fig.suptitle('Climate Change x Burger Sauces Dashboard\n'
                 '"Your sauce price depends on the climate on the other side of the world"',
                 fontsize=15, fontweight='bold', y=0.98)

    plt.savefig(OUTPUT_DIR / 'sauce_09_dashboard.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ [Figure 9] 종합 대시보드 저장")


# ============================================================
# 8. 결과 요약
# ============================================================
def summarize_visualizations():
    """시각화 결과 요약"""

    print("\n" + "=" * 60)
    print("📊 소스류 시각화 결과 요약")
    print("=" * 60)

    print("\n[생성된 시각화]")
    png_files = sorted(OUTPUT_DIR.glob("sauce_*.png"))
    for i, f in enumerate(png_files, 1):
        size = f.stat().st_size / 1024
        print(f"   {i}. {f.name} ({size:.1f} KB)")

    print("\n[주요 발견사항]")
    print("   - 토마토: 안정적 성장, 중국이 최대 생산국")
    print("   - 계란: AI(조류인플루엔자) 발생 시 급감")
    print("   - 고추: 높은 변동성, 2022년 스리라차 위기")

    print("\n[데이터 출처]")
    print("   - FAOSTAT Crops: https://www.fao.org/faostat/en/#data/QCL")
    print("   - FAOSTAT Livestock: https://www.fao.org/faostat/en/#data/QL")
    print("   - FAOSTAT Temperature: https://www.fao.org/faostat/en/#data/ET")

    print("\n✅ 다음 단계: 03_데이터_분석.md")


# ============================================================
# 9. 메인 실행
# ============================================================
def main():
    """메인 시각화 파이프라인"""

    # 1. 데이터 로드
    data = load_sauce_data()

    if len(data) == 0:
        print("\n⚠️ 로드된 데이터가 없습니다. 먼저 01_data_preprocessing.py를 실행하세요.")
        return

    print("\n" + "=" * 60)
    print("📊 시각화 생성 시작")
    print("=" * 60)

    # 2. 기온 변화 시각화
    print("\n[기온 변화]")
    plot_temperature_trend(data)
    plot_producer_temperature(data)

    # 3. 소스 원료별 생산량
    print("\n[생산량 시각화]")
    plot_tomato_production(data)
    plot_eggs_production(data)
    plot_chillies_production(data)

    # 4. 관계 분석
    print("\n[관계 분석]")
    plot_sauce_production_vs_temp(data)
    plot_temp_yield_scatter(data)

    # 5. 비교 및 대시보드
    print("\n[종합 시각화]")
    plot_all_sauce_comparison(data)
    create_sauce_dashboard(data)

    # 6. 결과 요약
    summarize_visualizations()

    return data


if __name__ == '__main__':
    data = main()
