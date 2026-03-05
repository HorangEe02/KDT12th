"""
STEP 9: 소주제3 시각화 (7개 차트)
실행: python src/subtopic3/s3_step9_visualization.py
"""
import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

from s3_step0_config import (
    get_connection, DB_NAME, S3_OUTPUT_DIR, CITY_COLORS,
)
from s3_step8_analysis_queries import (
    query_to_df,
    Q1_CLIMATE_PROFILE, Q2_MONTHLY_PATTERN, Q3_WARMING_TREND,
    Q4_DAEGU_DISTRICT_RANK, Q5_ZIP_PRICE_DISTRIBUTION,
    Q6_TIER_COMPARISON, Q7_PHOENIX_HEAT_PRICE,
)

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


def viz1_monthly_temp_radar():
    """차트 1: 5도시 월별 기온 패턴"""
    df = query_to_df(Q2_MONTHLY_PATTERN)
    if df.empty:
        print("[WARN] viz1 데이터 없음"); return

    fig, ax = plt.subplots(figsize=(12, 6))
    for city in df['city'].unique():
        sub = df[df['city'] == city].sort_values('month')
        ax.plot(sub['month'], sub['avg_temp'],
                color=CITY_COLORS.get(city, 'gray'), label=city,
                marker='o', linewidth=2)
        ax.fill_between(sub['month'], sub['min_temp'], sub['max_temp'],
                         color=CITY_COLORS.get(city, 'gray'), alpha=0.1)

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['1월','2월','3월','4월','5월','6월',
                         '7월','8월','9월','10월','11월','12월'])
    ax.axhline(y=35, color='red', linewidth=0.8, linestyle=':', label='폭염 기준 (35℃)')
    ax.set_ylabel('월평균 기온 (℃)')
    ax.set_title('5개 비교 도시 월별 기온 패턴 (2000~2013 평균)', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz1_monthly_temp.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz2_warming_trend():
    """차트 2: 10년 단위 온난화 트렌드"""
    df = query_to_df(Q3_WARMING_TREND)
    if df.empty:
        print("[WARN] viz2 데이터 없음"); return

    fig, ax = plt.subplots(figsize=(14, 6))
    for city in df['city'].unique():
        sub = df[df['city'] == city]
        ax.plot(sub['decade'], sub['decade_summer'],
                color=CITY_COLORS.get(city, 'gray'), label=f'{city} (여름)',
                marker='s', linewidth=2)

    ax.set_xlabel('연대')
    ax.set_ylabel('여름 평균 기온 (℃)')
    ax.set_title('10년 단위 여름 기온 변화 추이 (온난화 확인)', fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz2_warming_trend.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz3_climate_profile_bar():
    """차트 3: 도시별 기후 프로파일 비교 (막대)"""
    df = query_to_df(Q1_CLIMATE_PROFILE)
    if df.empty:
        print("[WARN] viz3 데이터 없음"); return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    colors_list = [CITY_COLORS.get(c, 'gray') for c in df['city_name']]

    # 여름 기온
    axes[0].barh(df['city_name'], df['summer_avg_temp'], color=colors_list)
    axes[0].set_title('여름 평균 기온 (℃)')
    axes[0].set_xlabel('℃')

    # 연교차
    axes[1].barh(df['city_name'], df['temp_range'], color=colors_list)
    axes[1].set_title('연교차 (℃)')
    axes[1].set_xlabel('℃')

    # 폭염일수
    heat_data = df['heatwave_days_avg'].fillna(0)
    axes[2].barh(df['city_name'], heat_data, color=colors_list)
    axes[2].set_title('연평균 폭염일수 (35℃+)')
    axes[2].set_xlabel('일')

    plt.suptitle('내륙 거점 도시 기후 프로파일 비교', fontsize=14, y=1.02)
    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz3_climate_profile.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] {path}")


def viz4_zip_price_boxplot():
    """차트 4: 도시별 ZIP 가격 분포 (박스플롯)"""
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql("""
        SELECT c.city_name, z.avg_price
        FROM us_zip_realtor_summary z
        JOIN cities c ON z.city_id = c.city_id
        WHERE z.avg_price > 0 AND z.avg_price < 5000000
    """, conn)
    conn.close()

    if df.empty:
        print("[WARN] viz4 데이터 없음"); return

    fig, ax = plt.subplots(figsize=(12, 6))
    order = df.groupby('city_name')['avg_price'].median().sort_values(ascending=False).index
    palette = {c: CITY_COLORS.get(c, 'gray') for c in order}
    sns.boxplot(data=df, x='city_name', y='avg_price', order=order,
                palette=palette, ax=ax, showfliers=False)

    ax.set_ylabel('ZIP별 평균 매물가 (USD)')
    ax.set_xlabel('')
    ax.set_title('도시 내부 ZIP Code별 가격 분포 (격차 비교)', fontsize=13)
    ax.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz4_zip_boxplot.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz5_daegu_district_bar():
    """차트 5: 대구 구별 가격 순위 + 프리미엄"""
    df = query_to_df(Q4_DAEGU_DISTRICT_RANK)
    if df.empty:
        print("[WARN] viz5 대구 구별 데이터 없음"); return

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ['#9B59B6' if p > 0 else '#95A5A6' for p in df['premium_vs_avg']]
    # 수성구 강조
    for i, d in enumerate(df['district']):
        if d == '수성구':
            colors[i] = '#E74C3C'

    bars = ax.barh(df['district'], df['avg_price'] / 10000, color=colors)

    # 프리미엄 % 표시
    for bar, prem in zip(bars, df['premium_vs_avg']):
        sign = '+' if prem > 0 else ''
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f'{sign}{prem:.1f}%', va='center', fontsize=9)

    ax.set_xlabel('평균 거래가 (억원)')
    ax.set_title('대구 구별 평균 아파트 거래가 순위 (도시 평균 대비 프리미엄)', fontsize=13)
    ax.grid(alpha=0.3, axis='x')

    patches = [
        mpatches.Patch(color='#E74C3C', label='수성구 (쾌적 프리미엄)'),
        mpatches.Patch(color='#9B59B6', label='평균 이상'),
        mpatches.Patch(color='#95A5A6', label='평균 이하'),
    ]
    ax.legend(handles=patches, loc='lower right')

    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz5_daegu_district.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


def viz6_heat_price_heatmap():
    """차트 6: 기온등급 x 가격등급 교차 — 도시별 파셋"""
    df = query_to_df(Q6_TIER_COMPARISON)
    if df.empty:
        print("[WARN] viz6 데이터 없음"); return

    cities = df['city_name'].dropna().unique()
    n = len(cities)
    if n == 0:
        return

    fig, axes = plt.subplots(1, min(n, 4), figsize=(5*min(n,4), 5))
    if min(n, 4) == 1:
        axes = [axes]

    for i, city in enumerate(cities[:4]):
        sub = df[df['city_name'] == city]
        ax = axes[i]
        tier_order = ['high', 'mid', 'low']
        sub_sorted = sub.set_index('price_tier').reindex(tier_order).dropna(subset=['tier_avg_price'])
        colors = ['#E74C3C', '#F39C12', '#3498DB'][:len(sub_sorted)]
        ax.barh(sub_sorted.index, sub_sorted['tier_avg_price'], color=colors)
        ax.set_title(f'{city}', fontsize=11)
        ax.set_xlabel('평균가')

    plt.suptitle('도시별 가격등급 평균 비교', fontsize=13, y=1.02)
    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz6_tier_heatmap.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] {path}")


def viz7_phoenix_heat_analysis():
    """차트 7: Phoenix 폭염 지역 vs 비폭염 지역 가격 비교"""
    df = query_to_df(Q7_PHOENIX_HEAT_PRICE)
    if df.empty:
        print("[WARN] viz7 Phoenix 데이터 없음"); return

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#E74C3C', '#F39C12', '#3498DB'][:len(df)]
    bars = ax.bar(df['heat_group'], df['avg_price'], color=colors)

    for bar, cnt, per_sqft in zip(bars, df['zip_count'], df['avg_per_sqft']):
        label_text = f'{cnt} ZIPs'
        if pd.notna(per_sqft):
            label_text += f'\n${per_sqft:.0f}/sqft'
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000,
                label_text, ha='center', fontsize=9)

    ax.set_ylabel('ZIP 평균 매물가 (USD)')
    ax.set_title('Phoenix: 극한 기상 빈도별 ZIP 가격 비교', fontsize=13)
    ax.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    path = os.path.join(S3_OUTPUT_DIR, 's3_viz7_phoenix_heat.png')
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[OK] {path}")


if __name__ == '__main__':
    viz1_monthly_temp_radar()
    viz2_warming_trend()
    viz3_climate_profile_bar()
    viz4_zip_price_boxplot()
    viz5_daegu_district_bar()
    viz6_heat_price_heatmap()
    viz7_phoenix_heat_analysis()
    print(f"\n[DONE] S3 STEP 9 완료: 시각화 -> {S3_OUTPUT_DIR}")
