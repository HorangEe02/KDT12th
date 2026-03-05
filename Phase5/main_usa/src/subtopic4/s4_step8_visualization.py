"""
STEP 8: 소주제4 시각화 5개
  V1: 산업전환 타임라인 (고용변화 + 신규건설 + 필요소득)
  V2: Charlotte 전환기 대시보드
  V3: 4개 주 시장건전성 히트맵
  V4: 대구 vs Charlotte 비교
  V5: 예측 성장률 (ZHVF)
실행: python src/subtopic4/s4_step8_visualization.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s4_step0_config import *
from s4_step7_analysis_queries import query_to_df

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['figure.dpi'] = 150

OUTPUT = S4_OUTPUT_DIR


# ── V1: 산업전환 타임라인 ──
def viz_v1():
    sql = """
        SELECT region_name,
               LEFT(`year_month`, 4) AS year,
               AVG(new_construction_sales) AS avg_new_con,
               AVG(income_needed) AS avg_income,
               AVG(market_temp_index) AS avg_market_temp
        FROM us_metro_demand
        WHERE region_name IN (
            'Dallas, TX',
            'Atlanta, GA',
            'Phoenix, AZ',
            'Charlotte, NC'
        )
        GROUP BY region_name, LEFT(`year_month`, 4)
        HAVING avg_new_con IS NOT NULL OR avg_income IS NOT NULL
        ORDER BY region_name, year
    """
    df = query_to_df(sql)
    if df.empty:
        print("  [WARN] V1 데이터 없음")
        return

    df['year'] = df['year'].astype(int)

    fig, axes = plt.subplots(3, 1, figsize=(14, 14), sharex=True)

    for metro in df['region_name'].unique():
        sub = df[df['region_name'] == metro]
        color = CITY_COLORS.get(metro, 'gray')
        label = metro.split(',')[0]

        mask_con = sub['avg_new_con'].notna()
        if mask_con.any():
            axes[0].plot(sub.loc[mask_con, 'year'], sub.loc[mask_con, 'avg_new_con'],
                         marker='o', color=color, label=label, linewidth=2)

        mask_inc = sub['avg_income'].notna()
        if mask_inc.any():
            axes[1].plot(sub.loc[mask_inc, 'year'], sub.loc[mask_inc, 'avg_income'],
                         marker='s', color=color, label=label, linewidth=2)

        mask_temp = sub['avg_market_temp'].notna()
        if mask_temp.any():
            axes[2].plot(sub.loc[mask_temp, 'year'], sub.loc[mask_temp, 'avg_market_temp'],
                         marker='^', color=color, label=label, linewidth=2)

    axes[0].set_title('New Construction Sales (Monthly Avg)', fontsize=13)
    axes[0].set_ylabel('Sales Count')
    axes[0].legend(loc='upper left')
    axes[0].grid(True, alpha=0.3)

    axes[1].set_title('Income Needed to Buy Home (Annual, USD)', fontsize=13)
    axes[1].set_ylabel('USD / Year')
    axes[1].legend(loc='upper left')
    axes[1].grid(True, alpha=0.3)

    axes[2].set_title('Market Temperature Index', fontsize=13)
    axes[2].set_ylabel('Index (50=Balanced)')
    axes[2].axhline(y=50, color='black', linestyle='--', alpha=0.5, label='Balanced')
    axes[2].legend(loc='upper left')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_xlabel('Year')

    fig.suptitle('Sub-topic 4: Industrial Transformation & Real Estate Impact\n'
                 '4 Metro Areas Comparison', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT, 'S4_V1_industry_timeline.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V1 저장")


# ── V2: Charlotte 전환기 대시보드 ──
def viz_v2():
    sql = """
        SELECT `year_month`,
               MAX(market_temp_index) AS market_temp_index,
               MAX(income_needed) AS income_needed,
               MAX(new_construction_sales) AS new_construction_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY `year_month`
        ORDER BY `year_month`
    """
    df = query_to_df(sql)
    if df.empty:
        print("  [WARN] V2 데이터 없음")
        return

    df = df.reset_index(drop=True)
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # 데이터프레임 인덱스를 x 위치로 사용하여 시간축 정렬
    mask_temp = df['market_temp_index'].notna()
    if mask_temp.any():
        idx_temp = df.index[mask_temp]
        y = df.loc[mask_temp, 'market_temp_index'].values
        ax1.fill_between(idx_temp, 50, y, alpha=0.3, color='#2ECC71')
        ax1.plot(idx_temp, y, color='#2ECC71', linewidth=2, label='Market Temp Index')
        ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Market Temp Index', color='#2ECC71', fontsize=12)

    ax2 = ax1.twinx()
    mask_inc = df['income_needed'].notna()
    if mask_inc.any():
        idx_inc = df.index[mask_inc]
        y_inc = df.loc[mask_inc, 'income_needed'].values
        ax2.plot(idx_inc, y_inc, color='#E74C3C', linewidth=2, linestyle='--',
                 label='Income Needed')
    ax2.set_ylabel('Income Needed (USD/Year)', color='#E74C3C', fontsize=12)

    # X축 레이블 (전체 데이터프레임 기준, 연도-월)
    tick_step = max(1, len(df) // 12)
    ax1.set_xticks(range(0, len(df), tick_step))
    ax1.set_xticklabels([df['year_month'].iloc[i] for i in range(0, len(df), tick_step)], rotation=45)

    ax1.set_title('Charlotte: Textile → Finance/Tech Transition Period\n'
                   'Market Temperature & Income Required',
                   fontsize=14, fontweight='bold')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT, 'S4_V2_charlotte_dashboard.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V2 저장")


# ── V3: 시장건전성 히트맵 ──
def viz_v3():
    sql = """
        SELECT region_name,
               YEAR(date) AS year,
               AVG(pct_homes_increasing) AS pct_increasing,
               AVG(pct_homes_selling_for_loss) AS pct_loss,
               AVG(pct_listings_price_reduction) AS pct_reduction
        FROM zillow_timeseries
        WHERE region_level = 'state'
          AND region_name IN ('Texas', 'Georgia', 'Arizona', 'North Carolina')
          AND date >= '2005-01-01'
        GROUP BY region_name, YEAR(date)
        ORDER BY region_name, year
    """
    df = query_to_df(sql)
    if df.empty:
        print("  [WARN] V3 데이터 없음")
        return

    fig, axes = plt.subplots(1, 3, figsize=(20, 8))

    metrics = [
        ('pct_increasing', 'Homes Increasing in Value (%)', 'Greens'),
        ('pct_loss', 'Homes Selling for Loss (%)', 'Reds'),
        ('pct_reduction', 'Listings with Price Reduction (%)', 'Oranges'),
    ]

    for ax, (col, title, cmap) in zip(axes, metrics):
        pivot = df.pivot_table(index='year', columns='region_name',
                               values=col, aggfunc='mean')
        if not pivot.empty:
            sns.heatmap(pivot, ax=ax, cmap=cmap, annot=True, fmt='.1f',
                        linewidths=0.5, cbar_kws={'shrink': 0.8})
            ax.set_title(title, fontsize=11)
            ax.set_xlabel('')

    fig.suptitle('Market Health Indicators: TX vs GA vs AZ vs NC',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT, 'S4_V3_market_health_heatmap.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V3 저장")


# ── V4: 대구 vs Charlotte 비교 ──
def viz_v4():
    # 대구 인구추이
    sql_daegu = """
        SELECT year,
               AVG(birth_rate) AS avg_birth_rate,
               AVG(death_rate) AS avg_death_rate,
               AVG(natural_growth_rate) AS avg_growth_rate,
               AVG(marriage_rate) AS avg_marriage_rate
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year
        ORDER BY year
    """
    # Charlotte 시장온도
    sql_charlotte = """
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """

    df_daegu = query_to_df(sql_daegu)
    df_charlotte = query_to_df(sql_charlotte)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # 대구: 출생률/사망률/자연증감률
    if not df_daegu.empty:
        ax1.plot(df_daegu['year'], df_daegu['avg_birth_rate'],
                 color='#E74C3C', marker='o', linewidth=2, label='Birth Rate')
        ax1.plot(df_daegu['year'], df_daegu['avg_death_rate'],
                 color='#3498DB', marker='s', linewidth=2, label='Death Rate')
        ax1.plot(df_daegu['year'], df_daegu['avg_growth_rate'],
                 color='#9B59B6', marker='^', linewidth=2, label='Natural Growth Rate')
        ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax1.set_title('Daegu: Demographic Indicators (2000-2022)\n'
                       'Textile → Hi-tech Transition in Progress',
                       fontsize=13)
        ax1.set_ylabel('Rate (per 1,000)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

    # Charlotte: 시장온도 + 필요소득
    if not df_charlotte.empty:
        ax2_twin = ax2.twinx()
        ax2.plot(df_charlotte['year'], df_charlotte['market_temp'],
                 color='#2ECC71', marker='s', linewidth=2, label='Market Temp')
        ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)

        mask_inc = df_charlotte['income_needed'].notna()
        if mask_inc.any():
            ax2_twin.plot(df_charlotte.loc[mask_inc, 'year'],
                          df_charlotte.loc[mask_inc, 'income_needed'],
                          color='#E74C3C', marker='^', linewidth=2, linestyle='--',
                          label='Income Needed')
            ax2_twin.set_ylabel('Income Needed (USD)', color='#E74C3C')

        ax2.set_title('Charlotte: Market Temperature & Income Needed\n'
                       'Textile → Finance Transition Complete',
                       fontsize=13)
        ax2.set_ylabel('Market Temp Index', color='#2ECC71')
        ax2.set_xlabel('Year')

        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        ax2.grid(True, alpha=0.3)

    fig.suptitle('Daegu vs Charlotte: Industrial Transformation Comparison',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT, 'S4_V4_daegu_vs_charlotte.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V4 저장")


# ── V5: 예측 성장률 (ZHVF) ──
def viz_v5():
    sql = """
        SELECT region_name, forecast_date, growth_rate
        FROM us_metro_zhvf_growth
        WHERE region_name != 'United States'
        ORDER BY region_name, forecast_date
    """
    df = query_to_df(sql)
    if df.empty:
        print("  [WARN] V5 데이터 없음")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    for metro in df['region_name'].unique():
        sub = df[df['region_name'] == metro]
        color = CITY_COLORS.get(metro, 'gray')
        label = metro.split(',')[0]
        ax.plot(sub['forecast_date'].astype(str), sub['growth_rate'],
                marker='o', color=color, label=label, linewidth=2)

    # US 전국도 추가
    sql_us = """
        SELECT forecast_date, growth_rate
        FROM us_metro_zhvf_growth
        WHERE region_name = 'United States'
        ORDER BY forecast_date
    """
    df_us = query_to_df(sql_us)
    if not df_us.empty:
        ax.plot(df_us['forecast_date'].astype(str), df_us['growth_rate'],
                marker='D', color='#95A5A6', label='US Average',
                linewidth=2, linestyle='--')

    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_title('ZHVF: Forecasted Home Value Growth Rate (%)\n'
                 '4 Metro Areas + US Average', fontsize=14, fontweight='bold')
    ax.set_ylabel('Growth Rate (%)')
    ax.set_xlabel('Forecast Date')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT, 'S4_V5_forecast_growth.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V5 저장")


if __name__ == '__main__':
    print("=" * 60)
    print("STEP 8: 소주제4 시각화")
    print("=" * 60)
    viz_v1()
    viz_v2()
    viz_v3()
    viz_v4()
    viz_v5()
    print(f"\n[DONE] 모든 차트 → {OUTPUT}")
