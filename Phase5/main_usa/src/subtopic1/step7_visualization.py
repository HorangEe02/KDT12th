"""
STEP 7: 소주제1 시각화
실행: python src/subtopic1/step7_visualization.py

차트 5개 -> PNG 저장
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import platform
from step0_init_db import get_connection, DB_NAME, OUTPUT_DIR
from step6_analysis_queries import (
    query_to_df, Q1_ZHVI_TREND, Q2_ZHVI_YOY, Q3_ZORI_TREND,
    Q5_DAEGU_DISTRICT, Q7_COVID_IMPACT, Q8_PRICE_REDUCTION
)

# ── 한글 폰트 설정 ──
system = platform.system()
if system == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
elif system == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 도시별 색상 (실제 RegionName 기준)
COLORS = {
    'Dallas, TX': '#E74C3C',
    'Atlanta, GA': '#3498DB',
    'Phoenix, AZ': '#E67E22',
    'Charlotte, NC': '#2ECC71',
    'United States': '#95A5A6',
}

SHORT_NAMES = {
    'Dallas, TX': 'Dallas',
    'Atlanta, GA': 'Atlanta',
    'Phoenix, AZ': 'Phoenix',
    'Charlotte, NC': 'Charlotte',
    'United States': 'US Average',
}


def viz1_zhvi_trend():
    """차트 1: ZHVI 장기 추이 (4도시 + 전국)"""
    df = query_to_df(Q1_ZHVI_TREND)
    if df.empty:
        print("  [SKIP] ZHVI 데이터 없음")
        return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 7))
    for name, group in df.groupby('region_name'):
        ax.plot(group['date'], group['zhvi'],
                color=COLORS.get(name, 'gray'),
                label=SHORT_NAMES.get(name, name),
                linewidth=2 if name != 'United States' else 1.5,
                linestyle='-' if name != 'United States' else '--')

    ax.set_title('ZHVI(Zillow Home Value Index) Long-term Trend\n'
                 'Dallas / Atlanta / Phoenix / Charlotte vs US Average', fontsize=14)
    ax.set_ylabel('ZHVI (USD)')
    ax.set_xlabel('')
    ax.legend(loc='upper left')
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.grid(alpha=0.3)

    # COVID / 금리인상 구간 표시
    ax.axvspan(pd.Timestamp('2020-03'), pd.Timestamp('2021-06'),
               alpha=0.1, color='red', label='COVID Surge')
    ax.axvspan(pd.Timestamp('2022-03'), pd.Timestamp('2023-12'),
               alpha=0.1, color='blue', label='Rate Hike')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'viz1_zhvi_trend.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def viz2_zhvi_yoy():
    """차트 2: ZHVI 전년동기 대비 변동률"""
    df = query_to_df(Q2_ZHVI_YOY)
    if df.empty:
        print("  [SKIP] YoY 데이터 없음")
        return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for name, group in df.groupby('region_name'):
        ax.plot(group['date'], group['yoy_pct'],
                color=COLORS.get(name, 'gray'),
                label=SHORT_NAMES.get(name, name))

    ax.axhline(y=0, color='black', linewidth=0.8)
    ax.set_title('ZHVI Year-over-Year Change Rate (%)', fontsize=14)
    ax.set_ylabel('YoY %')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'viz2_zhvi_yoy.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def viz3_zori_trend():
    """차트 3: 임대료(ZORI) 추이"""
    df = query_to_df(Q3_ZORI_TREND)
    if df.empty:
        print("  [SKIP] ZORI 데이터 없음")
        return

    df['date'] = pd.to_datetime(df['year_month'])

    fig, ax = plt.subplots(figsize=(14, 6))
    for name, group in df.groupby('region_name'):
        ax.plot(group['date'], group['zori'],
                color=COLORS.get(name, 'gray'),
                label=SHORT_NAMES.get(name, name))

    ax.set_title('ZORI(Zillow Observed Rent Index) Trend\n4 Cities vs US Average', fontsize=14)
    ax.set_ylabel('ZORI (USD/month)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'viz3_zori_trend.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def viz4_daegu_district():
    """차트 4: 대구 구별 평균가 추이"""
    df = query_to_df(Q5_DAEGU_DISTRICT)
    if df.empty:
        print("  [SKIP] 대구 데이터 없음")
        return

    df['date'] = pd.to_datetime(df['year_month'])

    top_districts = df.groupby('district')['transaction_count'].sum().nlargest(6).index

    fig, ax = plt.subplots(figsize=(14, 6))
    for dist in top_districts:
        sub = df[df['district'] == dist]
        ax.plot(sub['date'], sub['avg_price'], label=dist)

    ax.set_title('Daegu District Average Apartment Price Trend', fontsize=14)
    ax.set_ylabel('Average Price (10K KRW)')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'viz4_daegu_district.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def viz5_covid_bar():
    """차트 5: COVID 전후 가격 급등 비교 (막대 차트)"""
    df = query_to_df(Q7_COVID_IMPACT)
    if df.empty:
        print("  [SKIP] COVID 비교 데이터 없음")
        return

    df['label'] = df['region_name'].map(SHORT_NAMES)
    df = df.dropna(subset=['pre_covid', 'post_covid'])

    if df.empty:
        print("  [SKIP] COVID 비교 데이터 불완전")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 좌: 절대가격
    x_pos = range(len(df))
    w = 0.35
    axes[0].bar([p - w/2 for p in x_pos], df['pre_covid'], w,
                label='2019.12', color='#3498DB')
    axes[0].bar([p + w/2 for p in x_pos], df['post_covid'], w,
                label='2021.12', color='#E74C3C')
    axes[0].set_xticks(list(x_pos))
    axes[0].set_xticklabels(df['label'])
    axes[0].set_ylabel('ZHVI (USD)')
    axes[0].set_title('Pre vs Post COVID Home Value')
    axes[0].legend()

    # 우: 상승률
    colors = ['#E74C3C' if v > 30 else '#E67E22' if v > 20 else '#2ECC71'
              for v in df['covid_surge_pct']]
    axes[1].barh(df['label'], df['covid_surge_pct'], color=colors)
    axes[1].set_xlabel('Surge Rate (%)')
    axes[1].set_title('COVID Surge Rate (2019.12 -> 2021.12)')
    for i, v in enumerate(df['covid_surge_pct']):
        if pd.notna(v):
            axes[1].text(v + 0.5, i, f'{v}%', va='center')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'viz5_covid_impact.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


STATE_COLORS = {
    'Texas': '#E74C3C',
    'Georgia': '#3498DB',
    'Arizona': '#E67E22',
    'North Carolina': '#2ECC71',
}


def viz6_price_reduction():
    """차트 6: 가격 인하 매물 비율 추이 (State 레벨)"""
    df = query_to_df(Q8_PRICE_REDUCTION)
    if df.empty:
        print("  [SKIP] Price Reduction 데이터 없음")
        return

    df['date'] = pd.to_datetime(df['date'])

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # 상단: 가격 인하 매물 비율
    for name, group in df.groupby('region_name'):
        axes[0].plot(group['date'], group['pct_price_reduction'],
                     color=STATE_COLORS.get(name, 'gray'),
                     label=name, linewidth=1.5)
    axes[0].set_title('Percentage of Listings with Price Reductions by State', fontsize=14)
    axes[0].set_ylabel('% of Listings')
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # 하단: 중위 가격 인하 폭
    for name, group in df.groupby('region_name'):
        axes[1].plot(group['date'], group['median_pct_price_reduction'],
                     color=STATE_COLORS.get(name, 'gray'),
                     label=name, linewidth=1.5)
    axes[1].set_title('Median % of Price Reduction by State', fontsize=14)
    axes[1].set_ylabel('Median Reduction %')
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'viz6_price_reduction.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


if __name__ == '__main__':
    print(f"[VIZ] 시각화 시작 -> {OUTPUT_DIR}\n")
    viz1_zhvi_trend()
    viz2_zhvi_yoy()
    viz3_zori_trend()
    viz4_daegu_district()
    viz5_covid_bar()
    viz6_price_reduction()
    print(f"\n[DONE] STEP 7 완료: 시각화 저장 -> {OUTPUT_DIR}")
