"""
STEP 10: 기존 시각화 (V1~V5)
- V1: 산업 타임라인 (4도시 신규건설/필요소득/시장온도)
- V2: Charlotte 전환 대시보드
- V3: 시장건전성 히트맵
- V4: 대구 vs Charlotte 비교
- V5: ZHVF 예측 성장률
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150


def viz_v1_industry_timeline():
    """V1: 4도시 신규건설/필요소득/시장온도 타임라인"""
    df = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year, region_name,
               SUM(new_construction_sales) AS new_con,
               AVG(income_needed) AS income,
               AVG(market_temp_index) AS temp
        FROM us_metro_demand
        WHERE region_name IN (
            'Dallas, TX',
            'Atlanta, GA',
            'Phoenix, AZ',
            'Charlotte, NC'
        )
        GROUP BY region_name, LEFT(`year_month`, 4)
        ORDER BY year
    """)

    if df.empty:
        print("  [SKIP] V1 데이터 없음")
        return

    df['year'] = df['year'].astype(str)
    fig, axes = plt.subplots(3, 1, figsize=(14, 14), sharex=True)
    metrics = [
        ('new_con', 'New Construction Sales', axes[0]),
        ('income', 'Income Needed (USD)', axes[1]),
        ('temp', 'Market Temperature Index', axes[2]),
    ]

    for col, title, ax in metrics:
        for name in df['region_name'].unique():
            sub = df[df['region_name'] == name]
            label = MSA_SHORT.get(name, name.split(',')[0])
            ax.plot(sub['year'], sub[col], marker='.', label=label,
                    color=CITY_COLORS.get(name, 'gray'), linewidth=2)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        if col == 'temp':
            ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Neutral (50)')

    fig.suptitle('S4-V1: Industry Timeline - 4 Metro Areas', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V1_industry_timeline.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V1 산업 타임라인 저장")


def viz_v2_charlotte_dashboard():
    """V2: Charlotte 전환 대시보드"""
    df = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS temp,
               AVG(income_needed) AS income,
               SUM(new_construction_sales) AS new_con
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)

    if df.empty:
        print("  [SKIP] V2 데이터 없음")
        return

    df['year'] = df['year'].astype(str)
    fig, ax1 = plt.subplots(figsize=(14, 8))
    ax2 = ax1.twinx()

    ax1.fill_between(df['year'], df['temp'], alpha=0.3, color='#2ECC71')
    ax1.plot(df['year'], df['temp'], color='#2ECC71', linewidth=2, marker='o', label='Market Temp')
    ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Market Temperature Index', color='#2ECC71', fontsize=12)

    ax2.plot(df['year'], df['income'], color='#E74C3C', linewidth=2,
             linestyle='--', marker='s', label='Income Needed')
    ax2.set_ylabel('Income Needed (USD)', color='#E74C3C', fontsize=12)

    ax1.set_title('S4-V2: Charlotte Transition Dashboard\nMarket Temp & Income Needed',
                   fontsize=14, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V2_charlotte_dashboard.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V2 Charlotte 대시보드 저장")


def viz_v3_market_health_heatmap():
    """V3: 4개 주 시장건전성 히트맵"""
    df = query_to_df("""
        SELECT region_name, YEAR(date) AS year,
               AVG(pct_homes_increasing) AS pct_inc,
               AVG(pct_homes_selling_for_loss) AS pct_loss,
               AVG(pct_listings_price_reduction) AS pct_red
        FROM zillow_timeseries
        WHERE region_level = 'state'
          AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
          AND YEAR(date) >= 2005
        GROUP BY region_name, YEAR(date)
        ORDER BY region_name, year
    """)

    if df.empty:
        print("  [SKIP] V3 데이터 없음")
        return

    df['year'] = df['year'].astype(str)
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    metrics = [
        ('pct_inc', '% Homes Increasing', 'Greens', axes[0]),
        ('pct_loss', '% Homes Selling for Loss', 'Reds', axes[1]),
        ('pct_red', '% Listings Price Reduction', 'Oranges', axes[2]),
    ]

    for col, title, cmap, ax in metrics:
        pivot = df.pivot_table(index='year', columns='region_name', values=col)
        if not pivot.empty:
            sns.heatmap(pivot, cmap=cmap, annot=True, fmt='.1f', ax=ax,
                        linewidths=0.5, cbar_kws={'shrink': 0.8})
            ax.set_title(title, fontsize=11, fontweight='bold')
            ax.set_xlabel('')
            ax.set_ylabel('Year')

    fig.suptitle('S4-V3: Market Health Heatmap (4 States)', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V3_market_health_heatmap.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V3 시장건전성 히트맵 저장")


def viz_v4_daegu_vs_charlotte():
    """V4: 대구 인구통계 vs Charlotte 시장지표"""
    df_daegu = query_to_df("""
        SELECT year,
               AVG(birth_rate) AS birth_rate,
               AVG(death_rate) AS death_rate,
               AVG(natural_growth_rate) AS growth_rate,
               AVG(marriage_rate) AS marriage_rate
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year ORDER BY year
    """)

    df_ch = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS temp,
               AVG(income_needed) AS income
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4) ORDER BY year
    """)
    if not df_daegu.empty:
        df_daegu['year'] = df_daegu['year'].astype(str)
    if not df_ch.empty:
        df_ch['year'] = df_ch['year'].astype(str)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

    # 상단: 대구 인구통계
    if not df_daegu.empty:
        for col, label, color in [
            ('birth_rate', 'Birth Rate', '#3498DB'),
            ('death_rate', 'Death Rate', '#E74C3C'),
            ('growth_rate', 'Natural Growth Rate', '#2ECC71'),
            ('marriage_rate', 'Marriage Rate', '#F39C12'),
        ]:
            if col in df_daegu.columns:
                ax1.plot(df_daegu['year'], df_daegu[col], marker='.', label=label,
                         color=color, linewidth=2)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.set_title('대구 인구통계 (연도별)', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Rate')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)

    # 하단: Charlotte 시장
    if not df_ch.empty:
        ax2_twin = ax2.twinx()
        ax2.plot(df_ch['year'], df_ch['temp'], color='#2ECC71', marker='o',
                 linewidth=2, label='Market Temp')
        ax2_twin.plot(df_ch['year'], df_ch['income'], color='#E74C3C',
                      marker='s', linewidth=2, linestyle='--', label='Income Needed')
        ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        ax2.set_title('Charlotte Market Metrics', fontsize=13, fontweight='bold')
        ax2.set_ylabel('Market Temp', color='#2ECC71')
        ax2_twin.set_ylabel('Income Needed (USD)', color='#E74C3C')
        ax2.tick_params(axis='x', rotation=45)
        lines1, l1 = ax2.get_legend_handles_labels()
        lines2, l2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, l1 + l2)

    fig.suptitle('S4-V4: Daegu vs Charlotte Comparison', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V4_daegu_vs_charlotte.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V4 대구 vs Charlotte 저장")


def viz_v5_forecast_growth():
    """V5: ZHVF 예측 성장률"""
    df = query_to_df("""
        SELECT region_name, forecast_date, growth_rate
        FROM us_metro_zhvf_growth
        ORDER BY region_name, forecast_date
    """)

    if df.empty:
        print("  [SKIP] V5 데이터 없음")
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    for name in df['region_name'].unique():
        sub = df[df['region_name'] == name]
        label = MSA_SHORT.get(name, name.split(',')[0])
        ax.plot(sub['forecast_date'], sub['growth_rate'], marker='.', label=label,
                color=CITY_COLORS.get(name, 'gray'), linewidth=2)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_title('S4-V5: Home Value Forecast Growth Rate', fontsize=14, fontweight='bold')
    ax.set_ylabel('Growth Rate (%)')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V5_forecast_growth.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V5 예측 성장률 저장")


def run():
    print("=" * 60)
    print("STEP 10: 기존 시각화 (V1~V5)")
    print("=" * 60)
    viz_v1_industry_timeline()
    viz_v2_charlotte_dashboard()
    viz_v3_market_health_heatmap()
    viz_v4_daegu_vs_charlotte()
    viz_v5_forecast_growth()
    print(f"\n  STEP 10 완료! 차트 저장: {OUTPUT_DIR}")


if __name__ == '__main__':
    run()
