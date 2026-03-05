"""
STEP 12: 4축 인구-부동산 비교 시각화 (v2 신규)
실행: python src/subtopic2/s2_step12_visualization_4axis.py
의존: STEP 10 완료
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns

from s2_step0_config import get_connection, DB_NAME, S2_OUTPUT_DIR
from s2_step10_4axis_analysis import (
    query_to_df, get_daegu_pop, get_daegu_housing,
    get_us_city_demand, get_us_city_zhvi, get_us_pop_merged,
    AXIS_CONFIG
)

# Mac 한글 폰트
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

COLORS = {
    'Dallas': '#E74C3C', 'Atlanta': '#3498DB',
    'Phoenix': '#E67E22', 'Charlotte': '#2ECC71',
    'US Average': '#95A5A6', 'Daegu': '#9B59B6', '대구': '#9B59B6',
}


# =============================================
# V7: 인구성장률 대조 — 대구 유출 vs 4도시 유입
# =============================================

def viz7_population_growth_contrast():
    """대구 자연증감률 vs 미국 4도시 ZHVI변동률 — 성장 대조 막대그래프"""
    print("\n[VIZ7] 인구성장률 대조 막대 그래프")

    # 대구: 자연증감률 (birth_rate - death_rate)
    df_daegu = query_to_df("""
        SELECT year,
               (birth_rate - death_rate) AS natural_rate
        FROM daegu_population_summary
        WHERE birth_rate IS NOT NULL AND death_rate IS NOT NULL
        ORDER BY year
    """)

    # 미국 4도시: ZHVI 연평균 변동률
    cities_cfg = {
        'Dallas': 'Dallas, TX', 'Atlanta': 'Atlanta, GA',
        'Phoenix': 'Phoenix, AZ', 'Charlotte': 'Charlotte, NC',
    }
    us_frames = {}
    for city, metro in cities_cfg.items():
        df_z = get_us_city_zhvi(metro)
        if not df_z.empty:
            df_z = df_z.copy()
            df_z['year'] = df_z['year'].astype(int)
            df_z['zhvi_pct'] = df_z['avg_zhvi'].pct_change() * 100
            us_frames[city] = df_z[['year', 'zhvi_pct']].dropna()

    # 공통 연도 범위 (최근 10년)
    target_years = list(range(2013, 2023))
    df_daegu_plot = df_daegu[df_daegu['year'].isin(target_years)].sort_values('year')

    if df_daegu_plot.empty:
        print("  [WARN] 대구 데이터 없음 - 스킵")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    years = df_daegu_plot['year'].values
    x = np.arange(len(years))

    # 상단: 대구 자연증감률 추이
    colors_dg = ['#2ECC71' if v >= 0 else '#E74C3C' for v in df_daegu_plot['natural_rate']]
    ax1.bar(x, df_daegu_plot['natural_rate'].astype(float), color=colors_dg, alpha=0.8, edgecolor='white')
    ax1.axhline(y=0, color='black', linewidth=1)
    ax1.set_ylabel('자연증감률 (출생률 - 사망률)', fontsize=12)
    ax1.set_title('대구: 자연증감률 추이 — 2019년부터 인구 자연감소 전환',
                  fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # 전환점 표시
    for i, (yr, val) in enumerate(zip(years, df_daegu_plot['natural_rate'])):
        if val is not None:
            v = float(val)
            ax1.text(i, v + (0.15 if v >= 0 else -0.25), f'{v:.1f}',
                    ha='center', fontsize=8, fontweight='bold',
                    color='#2ECC71' if v >= 0 else '#E74C3C')

    ax1.annotate('인구 자연감소 전환', xy=(6.5, -0.2), fontsize=10,
                color='red', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red'),
                xytext=(4, -2.5))

    # 하단: 미국 4도시 ZHVI 변동률 비교
    width = 0.2
    for i, (city, df_us) in enumerate(us_frames.items()):
        df_match = df_us[df_us['year'].isin(years)].sort_values('year')
        if not df_match.empty:
            matched_x = [np.where(years == yr)[0][0] for yr in df_match['year'] if yr in years]
            ax2.bar(np.array(matched_x) + (i - 1.5) * width,
                    df_match['zhvi_pct'].astype(float).values[:len(matched_x)],
                    width, label=city, color=COLORS[city], alpha=0.8)

    ax2.axhline(y=0, color='black', linewidth=1)
    ax2.set_ylabel('ZHVI 변동률 (%)', fontsize=12)
    ax2.set_title('미국 4도시: 주택가치(ZHVI) 연간 변동률 — 인구유입 도시의 가격 상승',
                  fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10, ncol=4)
    ax2.grid(axis='y', alpha=0.3)
    ax2.set_xticks(x)
    ax2.set_xticklabels(years)
    ax2.set_xlabel('Year', fontsize=12)

    # 대조 주석
    ax2.annotate('인구유입 도시 → 주택가격 상승\n대구는 인구감소 → 시장 정체',
                xy=(0.98, 0.95), xycoords='axes fraction',
                ha='right', va='top', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz7_pop_growth_contrast.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


# =============================================
# V8: 4축 인구→부동산 경로 대시보드 (2x2)
# =============================================

def viz8_4axis_pathway_dashboard():
    """축별 인구→수요→가격 경로를 2x2 패널로 표시"""
    print("\n[VIZ8] 4축 인구→부동산 경로 대시보드")

    fig = plt.figure(figsize=(18, 14))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    axis_list = [
        ('comprehensive', 'Axis 1 [종합]: Dallas\nPop Growth → Demand Surge → Price Rise'),
        ('industry', 'Axis 2 [산업]: Atlanta\nJob Diversity → Pop Inflow → Market Heat'),
        ('climate', 'Axis 3 [기후]: Phoenix\nAffordability → Pop Boom → Overheat Cycle'),
        ('transformation', 'Axis 4 [변모]: Charlotte\nIndustry Shift → Income Rise → Price Surge'),
    ]

    for idx, (axis_key, title) in enumerate(axis_list):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        cfg = AXIS_CONFIG[axis_key]
        df = get_us_city_demand(cfg['metro'])

        if not df.empty:
            ax2 = ax.twinx()
            ax.bar(df['year'], df['total_sales'], color=COLORS[cfg['us_city']], alpha=0.4,
                   label='Sales Count')
            ax2.plot(df['year'], df['avg_market_temp'], color='#E74C3C', marker='o',
                    linewidth=2, label='Market Temp')
            ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)

            ax.set_ylabel('Sales Count', color=COLORS[cfg['us_city']])
            ax2.set_ylabel('Market Temp Index', color='#E74C3C')
            ax.tick_params(axis='x', rotation=45)

        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.2)

    fig.suptitle('4-Axis Population → Housing Pathway Dashboard\n'
                 'How Population Movement Drives Housing Markets',
                 fontsize=15, fontweight='bold')

    path = os.path.join(S2_OUTPUT_DIR, 's2_viz8_4axis_pathway.png')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"  [OK] {path}")


# =============================================
# V9: 인구변동률 vs 시장온도 산점도
# =============================================

def viz9_pop_vs_market_temp():
    """4도시+대구 인구변동률 vs 시장온도 산점도"""
    print("\n[VIZ9] 인구변동률 vs 시장온도 산점도")

    # 미국 도시: ZHVI 변동률 vs 시장온도 (pop_change_rate 데이터가 부족하므로 대체)
    frames = []
    for axis_key, cfg in AXIS_CONFIG.items():
        city = cfg['us_city']
        df_zhvi = get_us_city_zhvi(cfg['metro'])
        df_dem = get_us_city_demand(cfg['metro'])
        if not df_zhvi.empty and not df_dem.empty:
            df_zhvi = df_zhvi.copy()
            df_zhvi['year'] = df_zhvi['year'].astype(int)
            df_zhvi['zhvi_change_rate'] = df_zhvi['avg_zhvi'].pct_change() * 100
            df_zhvi = df_zhvi[['year', 'zhvi_change_rate']].dropna()
            df_dem = df_dem[['year', 'avg_market_temp']].dropna()
            df_dem['year'] = df_dem['year'].astype(int)
            merged = df_zhvi.merge(df_dem, on='year', how='inner')
            merged['city_name'] = city
            frames.append(merged)

    if not frames:
        print("  [WARN] 데이터 부족 - 스킵")
        return

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=['zhvi_change_rate', 'avg_market_temp'])

    if df.empty:
        print("  [WARN] 조인 후 데이터 부족 - 스킵")
        return

    fig, ax = plt.subplots(figsize=(11, 8))

    for city in df['city_name'].unique():
        sub = df[df['city_name'] == city]
        ax.scatter(sub['zhvi_change_rate'], sub['avg_market_temp'],
                  color=COLORS.get(city, 'gray'), label=city, s=70, alpha=0.7)

    # 회귀선
    from numpy.polynomial.polynomial import polyfit
    x = df['zhvi_change_rate'].values.astype(float)
    y = df['avg_market_temp'].values.astype(float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 3:
        b, m = polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(x_line, b + m * x_line, 'k--', linewidth=1.5, alpha=0.5,
                label=f'Trend (slope={m:.1f})')

    ax.axhline(y=50, color='gray', linewidth=0.8, linestyle=':')
    ax.axvline(x=0, color='gray', linewidth=0.8, linestyle=':')

    # 사분면 라벨
    ax.text(0.98, 0.98, 'ZHVI Rise +\nMarket Hot', transform=ax.transAxes,
            ha='right', va='top', fontsize=9, color='red', alpha=0.6)
    ax.text(0.02, 0.02, 'ZHVI Decline +\nMarket Cold', transform=ax.transAxes,
            ha='left', va='bottom', fontsize=9, color='blue', alpha=0.6)

    ax.set_xlabel('ZHVI Change Rate (%)', fontsize=12)
    ax.set_ylabel('Market Temperature Index', fontsize=12)
    ax.set_title('ZHVI Change Rate vs Market Temperature\nPrice Movement and Market Heat Correlation',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.2)

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz9_pop_vs_market_temp.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


# =============================================
# V10: 대구 vs 미국 4도시 — 인구·주택가격 이중축
# =============================================

def viz10_daegu_vs_us_dual_axis():
    """상단: 미국 4도시 ZHVI 추이, 하단: 대구 인구+아파트가격"""
    print("\n[VIZ10] 대구 vs 미국 4도시 이중축")

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(16, 12))

    # 상단: 미국 4도시 ZHVI
    for axis_key, cfg in AXIS_CONFIG.items():
        df = get_us_city_zhvi(cfg['metro'])
        if not df.empty:
            label = cfg['us_city']
            ax_top.plot(df['year'], df['avg_zhvi'], marker='.', label=label,
                       color=COLORS[label], linewidth=2)
    ax_top.set_title('US Peer Cities: Home Value Index (ZHVI) — Population Inflow Effect',
                     fontsize=13, fontweight='bold')
    ax_top.set_ylabel('ZHVI (USD)')
    ax_top.legend(fontsize=10)
    ax_top.grid(alpha=0.3)
    ax_top.tick_params(axis='x', rotation=45)
    ax_top.annotate('Population Inflow → ZHVI 상승',
                   xy=(0.7, 0.85), xycoords='axes fraction',
                   fontsize=11, color='green', fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # 하단: 대구 자연증감 + 아파트 가격
    df_ni = query_to_df("""
        SELECT year, natural_increase
        FROM daegu_population_summary
        WHERE natural_increase IS NOT NULL
        ORDER BY year
    """)
    df_price = get_daegu_housing()

    ax_r = ax_bot.twinx()

    if not df_ni.empty:
        colors_ni = ['#2ECC71' if v >= 0 else '#E74C3C'
                     for v in df_ni['natural_increase'].astype(float)]
        ax_bot.bar(df_ni['year'].astype(int), df_ni['natural_increase'].astype(float),
                   color=colors_ni, alpha=0.6, label='자연증감 (출생-사망)')
        ax_bot.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
        ax_bot.set_ylabel('자연증감 (명)', color=COLORS['Daegu'], fontsize=12)

    if not df_price.empty:
        ax_r.plot(df_price['year'], df_price['avg_price_manwon'], color='#E67E22',
                  marker='s', linewidth=2.5, linestyle='-', label='대구 아파트 평균가')
        ax_r.set_ylabel('평균 아파트 가격 (만원)', color='#E67E22', fontsize=12)

    ax_bot.set_title('대구: 자연증감 감소 vs 주택가격 — 인구감소에도 가격은 상승 후 정체',
                     fontsize=13, fontweight='bold')
    ax_bot.set_xlabel('Year')
    ax_bot.grid(alpha=0.3)

    # 범례 합치기
    lines1, labels1 = ax_bot.get_legend_handles_labels()
    lines2, labels2 = ax_r.get_legend_handles_labels()
    ax_bot.legend(lines1 + lines2, labels1 + labels2, fontsize=10, loc='upper left')

    ax_bot.annotate('2019~ 자연감소 전환\n→ 주택시장 정체 우려',
                   xy=(0.6, 0.85), xycoords='axes fraction',
                   fontsize=11, color='red', fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='mistyrose', alpha=0.8))

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz10_daegu_vs_us_dual.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


# =============================================
# V11: Phoenix 과열 사이클 분석
# =============================================

def viz11_phoenix_overheat_cycle():
    """Phoenix 시장온도 + ZHVI 변동 사이클"""
    print("\n[VIZ11] Phoenix 과열 사이클 영역 차트")

    df_demand = get_us_city_demand('Phoenix, AZ')
    df_zhvi = get_us_city_zhvi('Phoenix, AZ')

    if df_demand.empty:
        print("  [WARN] Phoenix 데이터 없음 - 스킵")
        return

    # year를 int로 변환 + 정렬
    df_demand = df_demand.copy()
    df_demand['year'] = df_demand['year'].astype(int)
    df_demand = df_demand.sort_values('year')
    df_demand = df_demand.dropna(subset=['avg_market_temp'])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))

    # 상단: 시장온도 (영역 차트)
    years_d = df_demand['year'].values
    temps = df_demand['avg_market_temp'].astype(float).values

    ax1.fill_between(years_d, temps, 50,
                     where=temps >= 50,
                     color='#E74C3C', alpha=0.3, interpolate=True, label='과열 (>50)')
    ax1.fill_between(years_d, temps, 50,
                     where=temps < 50,
                     color='#3498DB', alpha=0.3, interpolate=True, label='냉각 (<50)')
    ax1.plot(years_d, temps,
             color='#E67E22', linewidth=2.5, marker='o', label='시장 온도')
    ax1.axhline(y=50, color='black', linewidth=1, linestyle='--')
    ax1.set_ylabel('Market Temp Index')
    ax1.set_title('Phoenix Overheat Cycle\n인구유입 → 수요급증 → 과열 → 조정',
                  fontsize=13, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)
    ax1.set_xticks(years_d)
    ax1.tick_params(axis='x', rotation=45)

    # 사이클 주석
    ax1.annotate('대구 교훈:\n점진적 인구유입이\n급격한 과열보다 안전',
                xy=(0.02, 0.15), xycoords='axes fraction', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    # 하단: ZHVI 변화율 (전체 기간, 시간순 정렬)
    if not df_zhvi.empty:
        df_zhvi = df_zhvi.copy()
        df_zhvi['year'] = df_zhvi['year'].astype(int)
        df_zhvi = df_zhvi.sort_values('year')
        df_zhvi['zhvi_pct'] = df_zhvi['avg_zhvi'].pct_change() * 100
        df_zhvi = df_zhvi.dropna(subset=['zhvi_pct'])

        years_z = df_zhvi['year'].values
        pcts = df_zhvi['zhvi_pct'].astype(float).values
        colors_bar = ['#E74C3C' if v > 0 else '#3498DB' for v in pcts]

        ax2.bar(years_z, pcts, color=colors_bar, alpha=0.7)
        ax2.axhline(y=0, color='black', linewidth=1)
        ax2.set_ylabel('ZHVI YoY Change (%)')
        ax2.set_title('Phoenix ZHVI 연간 변화율 — 버블(2005~07) → 폭락(08~11) → 회복 → 과열(20~21) → 조정',
                      fontsize=12)
        ax2.grid(alpha=0.3)
        ax2.set_xticks(years_z)
        ax2.tick_params(axis='x', rotation=45)

        # 주요 시점 주석
        ax2.annotate('2008 금융위기', xy=(2009, -25), fontsize=9, color='blue',
                    fontweight='bold', ha='center')
        ax2.annotate('2020~21 과열', xy=(2021, 25), fontsize=9, color='red',
                    fontweight='bold', ha='center')

    ax2.set_xlabel('Year')

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz11_phoenix_cycle.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


# =============================================
# V12: 대구 인구유지 전략 로드맵 인포그래픽
# =============================================

def viz12_strategy_roadmap():
    """대구 인구유지 전략 로드맵 시각화"""
    print("\n[VIZ12] 대구 인구유지 전략 로드맵 인포그래픽")

    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 타이틀
    ax.text(50, 97, '대구 인구유지 전략 로드맵', fontsize=18,
            fontweight='bold', ha='center', va='top')
    ax.text(50, 93, '인구이동 → 주택수요 | Dallas · Atlanta · Phoenix · Charlotte 벤치마크',
            fontsize=11, ha='center', va='top', color='gray')

    # 타임라인 화살표
    ax.annotate('', xy=(92, 50), xytext=(8, 50),
                arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=3))

    phases = [
        (15, '현재\n(0년차)', '#E74C3C'),
        (38, '3년차', '#F39C12'),
        (62, '7년차', '#2ECC71'),
        (85, '15년차', '#3498DB'),
    ]
    for x, label, color in phases:
        ax.text(x, 47, label, fontsize=10, fontweight='bold', color=color, ha='center')

    # 상단: 인구 전략 (파란 계열)
    ax.text(50, 87, '── 인구 전략 ──', fontsize=12, ha='center',
            fontweight='bold', color='#2980B9')

    pop_strats = [
        (15, 78, '주택가격\n경쟁력\n마케팅', 'Dallas', '#E74C3C'),
        (38, 78, '원격근무자\n유치\n프로그램', 'Phoenix', '#E67E22'),
        (62, 78, '앵커기업\n본사 유치\n→ 일자리창출', 'Charlotte', '#2ECC71'),
        (85, 78, '인구\n안정화\n& 순유입', 'All 4', '#3498DB'),
    ]
    for x, y, strat, model, color in pop_strats:
        rect = mpatches.FancyBboxPatch((x-11, y-7), 22, 14, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.12, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y+1, strat, fontsize=8.5, ha='center', va='center', fontweight='bold')
        ax.text(x, y-5, f'({model})', fontsize=7, ha='center', color=color, style='italic')

    # 하단: 부동산 효과 (주황 계열)
    ax.text(50, 38, '── 부동산 시장 효과 ──', fontsize=12, ha='center',
            fontweight='bold', color='#D35400')

    house_effects = [
        (15, 28, '거래량 증가\n시장 안정화', '#E74C3C'),
        (38, 28, '수요 증가\n재고 감소\n대기일 단축', '#F39C12'),
        (62, 28, '시장온도 상승\n신규건설 증가\n가격 상승', '#2ECC71'),
        (85, 28, '필요소득 상승\n지속가능\n성장 사이클', '#3498DB'),
    ]
    for x, y, effect, color in house_effects:
        rect = mpatches.FancyBboxPatch((x-11, y-7), 22, 14, boxstyle="round,pad=1",
                                        facecolor=color, alpha=0.08, edgecolor=color,
                                        linewidth=1.5, linestyle='--')
        ax.add_patch(rect)
        ax.text(x, y, effect, fontsize=8.5, ha='center', va='center')

    # 연결 화살표 (인구전략→부동산효과)
    for x in [15, 38, 62, 85]:
        ax.annotate('', xy=(x, 35), xytext=(x, 64),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1, alpha=0.5))

    # 범례 박스
    legend_data = [
        ('Dallas', '#E74C3C', '가격경쟁력 → 유입'),
        ('Atlanta', '#3498DB', '산업허브 → 일자리'),
        ('Phoenix', '#E67E22', '기후극복 → 붐'),
        ('Charlotte', '#2ECC71', '전환 → 고소득'),
    ]
    for i, (city, color, keyword) in enumerate(legend_data):
        x = 10 + i * 22
        ax.add_patch(mpatches.FancyBboxPatch((x-2, 6), 20, 8, boxstyle="round,pad=0.5",
                     facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5))
        ax.text(x+8, 12, city, fontsize=9, ha='center', fontweight='bold', color=color)
        ax.text(x+8, 8, keyword, fontsize=7.5, ha='center', color='gray')

    path = os.path.join(S2_OUTPUT_DIR, 's2_viz12_strategy_roadmap.png')
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  [OK] {path}")


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 12: 4축 인구-부동산 비교 시각화 (v2)")
    print("=" * 60)

    viz7_population_growth_contrast()
    viz8_4axis_pathway_dashboard()
    viz9_pop_vs_market_temp()
    viz10_daegu_vs_us_dual_axis()
    viz11_phoenix_overheat_cycle()
    viz12_strategy_roadmap()

    print(f"\n[DONE] S2 STEP 12 완료: 모든 v2 시각화 저장 → {S2_OUTPUT_DIR}")
