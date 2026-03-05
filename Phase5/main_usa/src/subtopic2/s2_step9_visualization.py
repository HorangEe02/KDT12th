"""
STEP 9: 소주제2 시각화 (6개 차트) → PNG
실행: python src/subtopic2/s2_step9_visualization.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from s2_step0_config import get_connection, DB_NAME, S2_OUTPUT_DIR
from s2_step8_analysis_queries import query_to_df
from s2_step8_analysis_queries import (
    Q1_MARKET_TEMP, Q2_SUPPLY_DEMAND, Q3_DAEGU_POP,
    Q4_POP_HOUSING, Q5_CORRELATION, Q6_INCOME_NEEDED,
    Q9_SALES_TREND,
)

# Mac 한글 폰트
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

COLORS = {
    'Dallas': '#E74C3C', 'Atlanta': '#3498DB',
    'Phoenix': '#E67E22', 'Charlotte': '#2ECC71',
    'US Average': '#95A5A6', '대구': '#9B59B6',
}


def viz1_market_temp_dashboard():
    """차트 1: 시장온도 + 재고 + 판매건수 복합 대시보드"""
    df = query_to_df(Q1_MARKET_TEMP)
    if df.empty:
        print("[WARN] viz1 데이터 없음 - 스킵"); return

    df['date'] = pd.to_datetime(df['year_month'])
    cities = [c for c in df['city'].unique() if c and c != 'US Average']

    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    # 상: 시장온도지수
    for city in cities + ['US Average']:
        sub = df[df['city'] == city].dropna(subset=['market_temp_index'])
        if sub.empty:
            continue
        ls = '--' if city == 'US Average' else '-'
        axes[0].plot(sub['date'], sub['market_temp_index'],
                     color=COLORS.get(city, 'gray'), label=city, linestyle=ls)
    axes[0].axhline(y=50, color='black', linewidth=0.8, linestyle=':')
    axes[0].set_ylabel('Market Temp Index')
    axes[0].set_title('시장온도지수 (50=균형, 80+=과열)', fontsize=13)
    axes[0].legend(ncol=5, fontsize=8)

    # 중: 매물 재고량
    for city in cities:
        sub = df[df['city'] == city].dropna(subset=['inventory'])
        if sub.empty:
            continue
        axes[1].plot(sub['date'], sub['inventory'],
                     color=COLORS.get(city, 'gray'), label=city)
    axes[1].set_ylabel('Inventory')
    axes[1].set_title('매물 재고량')

    # 하: 판매 건수
    for city in cities:
        sub = df[df['city'] == city].dropna(subset=['sales_count'])
        if sub.empty:
            continue
        axes[2].plot(sub['date'], sub['sales_count'],
                     color=COLORS.get(city, 'gray'), label=city)
    axes[2].set_ylabel('Sales Count')
    axes[2].set_title('월별 판매 건수')

    for ax in axes:
        ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz1_market_dashboard.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz2_supply_demand_ratio():
    """차트 2: 수급비율 (Months of Supply)"""
    df = query_to_df(Q2_SUPPLY_DEMAND)
    if df.empty:
        print("[WARN] viz2 데이터 없음 - 스킵"); return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for city in df['city'].dropna().unique():
        sub = df[df['city'] == city]
        ax.plot(sub['date'], sub['months_of_supply'],
                color=COLORS.get(city, 'gray'), label=city)

    ax.axhline(y=6, color='red', linewidth=1, linestyle='--', label='균형선 (6개월)')
    ax.axhspan(0, 4, alpha=0.05, color='red')
    ax.axhspan(6, 10, alpha=0.05, color='blue')

    ax.set_title('수급 균형 지표: Months of Supply (재고 / 판매건수)', fontsize=13)
    ax.set_ylabel('개월')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz2_supply_demand.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz3_daegu_population():
    """차트 3: 대구 인구 추이 (출생/사망/자연증감) 이중축"""
    df = query_to_df(Q3_DAEGU_POP)
    if df.empty:
        print("[WARN] viz3 대구 인구 데이터 없음 - 스킵"); return

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    # 출생/사망 막대
    width = 0.35
    x = df['year']
    if 'birth_count' in df.columns and df['birth_count'].notna().any():
        ax1.bar(x - width/2, df['birth_count'], width, color='#3498DB', alpha=0.7, label='출생')
    if 'death_count' in df.columns and df['death_count'].notna().any():
        ax1.bar(x + width/2, df['death_count'], width, color='#E74C3C', alpha=0.7, label='사망')

    # 자연증감 라인
    if 'natural_increase' in df.columns and df['natural_increase'].notna().any():
        ax2.plot(x, df['natural_increase'], color='#2ECC71', marker='o',
                 linewidth=2, label='자연증감')
        ax2.axhline(y=0, color='black', linewidth=0.8, linestyle=':')

    ax1.set_xlabel('연도')
    ax1.set_ylabel('출생/사망 수', color='#3498DB')
    ax2.set_ylabel('자연증감', color='#2ECC71')
    ax1.set_title('대구광역시 인구 동태: 출생 vs 사망 및 자연증감', fontsize=13)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz3_daegu_pop.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz4_pop_vs_zhvi_scatter():
    """차트 4: 인구변동률 vs ZHVI변동률 산점도 + 회귀선"""
    df = query_to_df(Q4_POP_HOUSING)
    df = df.dropna(subset=['pop_change_rate', 'zhvi_change_rate'])

    if df.empty:
        print("[WARN] viz4 통합 데이터 부족 - 스킵"); return

    fig, ax = plt.subplots(figsize=(10, 8))

    for city in df['city_name'].unique():
        sub = df[df['city_name'] == city]
        ax.scatter(sub['pop_change_rate'], sub['zhvi_change_rate'],
                   color=COLORS.get(city, 'gray'), label=city, s=60, alpha=0.7)

    # 전체 회귀선
    from numpy.polynomial.polynomial import polyfit
    x = df['pop_change_rate'].values.astype(float)
    y = df['zhvi_change_rate'].values.astype(float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 2:
        b, m = polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(x_line, b + m * x_line, 'k--', linewidth=1, alpha=0.5,
                label=f'추세선 (기울기={m:.2f})')

    ax.axhline(y=0, color='gray', linewidth=0.5)
    ax.axvline(x=0, color='gray', linewidth=0.5)

    ax.set_xlabel('인구변동률 (%)')
    ax.set_ylabel('ZHVI 변동률 (%)')
    ax.set_title('인구변동률 vs 주택가치 변동률 - 도시별 산점도', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.2)

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz4_pop_zhvi_scatter.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz5_income_needed():
    """차트 5: 주택구매 필요소득 추이"""
    df = query_to_df(Q6_INCOME_NEEDED)
    if df.empty:
        print("[WARN] viz5 필요소득 데이터 없음 - 스킵"); return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for city in df['city'].dropna().unique():
        sub = df[df['city'] == city]
        ls = '--' if city == 'US Average' else '-'
        ax.plot(sub['date'], sub['income_needed'],
                color=COLORS.get(city, 'gray'), label=city, linestyle=ls)

    ax.set_title('주택 구매 필요 연소득 추이 (계약금 20% 기준)', fontsize=13)
    ax.set_ylabel('필요 연소득 (USD)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz5_income_needed.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz6_correlation_heatmap():
    """차트 6: 상관계수 히트맵"""
    df = query_to_df(Q5_CORRELATION)
    if df.empty:
        print("[WARN] viz6 상관분석 결과 없음 - 스킵"); return

    df['pair'] = df['x_variable'] + '\nvs\n' + df['y_variable']
    pivot = df.pivot_table(index='city_name', columns='pair', values='pearson_r')

    if pivot.empty:
        print("[WARN] viz6 피벗 결과 없음 - 스킵"); return

    fig, ax = plt.subplots(figsize=(max(14, len(pivot.columns) * 2), max(6, len(pivot) * 1.5)))
    sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                vmin=-1, vmax=1, ax=ax, linewidths=0.5)
    ax.set_title('도시별 인구-부동산 상관계수 히트맵', fontsize=13)

    plt.tight_layout()
    path = os.path.join(S2_OUTPUT_DIR, 's2_viz6_correlation_heatmap.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


if __name__ == '__main__':
    viz1_market_temp_dashboard()
    viz2_supply_demand_ratio()
    viz3_daegu_population()
    viz4_pop_vs_zhvi_scatter()
    viz5_income_needed()
    viz6_correlation_heatmap()
    print("\n[DONE] S2 STEP 9 완료: 시각화 -> output/")
