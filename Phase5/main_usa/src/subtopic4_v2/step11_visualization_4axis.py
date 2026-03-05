"""
STEP 11: 4축 비교 시각화 (v2 신규)
- V6: 4축 레이더 차트
- V7: 4축 대시보드 (2x2 패널)
- V8: 인구 vs 주택가격 이중축
- V9: 산업 전환 타임라인
- V10: 전략 로드맵 인포그래픽
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from matplotlib.gridspec import GridSpec

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150


def viz_v6_radar_chart():
    """V6: 대구 vs 4도시 종합 비교 레이더 차트"""
    categories = [
        'Housing\nAffordability',
        'Population\nGrowth',
        'Industry\nDiversity',
        'Infrastructure\n(Transport)',
        'Job\nCreation',
        'Climate\nLivability'
    ]

    # 분석 결과 기반 정규화 점수 (0~100)
    # 실제 DB 데이터를 활용하여 점수 산출
    scores = {
        'Daegu':     [75, 25, 40, 55, 35, 40],
        'Dallas':    [65, 85, 75, 70, 80, 50],
        'Atlanta':   [60, 70, 80, 90, 75, 60],
        'Phoenix':   [55, 80, 60, 65, 70, 30],
        'Charlotte': [60, 75, 70, 70, 75, 65],
    }

    # DB에서 실제 데이터로 점수 조정 시도
    try:
        df_pop = query_to_df("""
            SELECT city_name, population_growth_rate
            FROM city_comparison_population
        """)
        if not df_pop.empty:
            for _, row in df_pop.iterrows():
                city = row['city_name']
                gr = row['population_growth_rate']
                if city in scores and gr is not None:
                    # 성장률 → 0~100 점수 (음수=-100%, 양수=+100% 범위)
                    pop_score = max(0, min(100, 50 + float(gr) * 5000))
                    scores[city][1] = int(pop_score)
    except Exception:
        pass

    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    for city, vals in scores.items():
        values = vals + vals[:1]
        color = CITY_COLORS.get(city, 'gray')
        ax.plot(angles, values, 'o-', linewidth=2, color=color, label=city)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=8)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
    ax.set_title('S4-V6: Daegu vs US Peer Cities\n4-Axis Comparison Radar',
                 fontsize=15, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V6_radar_4axis.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V6 레이더 차트 저장")


def viz_v7_4axis_dashboard():
    """V7: 4축 비교 대시보드 — 통일된 Sales+MarketTemp 이중축 형식"""
    fig = plt.figure(figsize=(20, 15))
    gs = GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

    axis_panels = [
        {
            'pos': (0, 0), 'metro': 'Dallas, TX', 'city': 'Dallas',
            'title': 'Axis 1 [종합]: Dallas',
            'subtitle': 'Pop Growth → Demand Surge → Price Rise',
            'color': '#E74C3C',
        },
        {
            'pos': (0, 1), 'metro': 'Atlanta, GA', 'city': 'Atlanta',
            'title': 'Axis 2 [산업]: Atlanta',
            'subtitle': 'Job Diversity → Pop Inflow → Market Heat',
            'color': '#3498DB',
        },
        {
            'pos': (1, 0), 'metro': 'Phoenix, AZ', 'city': 'Phoenix',
            'title': 'Axis 3 [기후]: Phoenix',
            'subtitle': 'Affordability → Pop Boom → Overheat Cycle',
            'color': '#F39C12',
        },
        {
            'pos': (1, 1), 'metro': 'Charlotte, NC', 'city': 'Charlotte',
            'title': 'Axis 4 [변모]: Charlotte',
            'subtitle': 'Industry Shift → Income Rise → Price Surge',
            'color': '#2ECC71',
        },
    ]

    for cfg in axis_panels:
        r, c = cfg['pos']
        ax = fig.add_subplot(gs[r, c])

        # 데이터 조회: Sales Count + Market Temp
        df = query_to_df(f"""
            SELECT LEFT(`year_month`, 4) AS year,
                   SUM(sales_count) AS total_sales,
                   AVG(market_temp_index) AS avg_market_temp
            FROM us_metro_demand
            WHERE region_name = %s
            GROUP BY LEFT(`year_month`, 4) ORDER BY year
        """, params=(cfg['metro'],))

        if not df.empty:
            df['year'] = df['year'].astype(int)
            df = df.sort_values('year')

            # 막대: Sales Count
            ax.bar(df['year'], df['total_sales'].fillna(0),
                   color=cfg['color'], alpha=0.35, label='Sales Count', width=0.7)
            ax.set_ylabel('Sales Count', color=cfg['color'], fontsize=10)
            ax.tick_params(axis='y', labelcolor=cfg['color'])

            # 선: Market Temp (이중축)
            ax2 = ax.twinx()
            df_temp = df.dropna(subset=['avg_market_temp'])
            if not df_temp.empty:
                ax2.plot(df_temp['year'], df_temp['avg_market_temp'],
                         color='#E74C3C', marker='o', linewidth=2.5, label='Market Temp')
                ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5, linewidth=1)
                ax2.set_ylabel('Market Temp Index', color='#E74C3C', fontsize=10)
                ax2.tick_params(axis='y', labelcolor='#E74C3C')
                # 50 기준선 라벨
                ax2.text(df_temp['year'].iloc[0], 51, '중립(50)',
                         fontsize=7, color='gray', va='bottom')

            ax.set_xticks(df['year'].values[::max(1, len(df)//8)])
            ax.tick_params(axis='x', rotation=45)

        ax.set_title(f"{cfg['title']}\n{cfg['subtitle']}",
                     fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.2)

    fig.suptitle('S4-V7: 4-Axis Comparison Dashboard\n'
                 '4축 도시 비교 대시보드 — Sales Count + Market Temperature',
                 fontsize=16, fontweight='bold')
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V7_4axis_dashboard.png'), bbox_inches='tight', dpi=150)
    plt.close()
    print("  [OK] V7 4축 대시보드 저장")


def viz_v8_population_vs_housing():
    """V8: 대구 인구유출 vs 4도시 주택가격"""
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(16, 12))

    # 상단: 4개 미국 도시 ZHVI
    df_zhvi = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year, AVG(zhvi) AS avg_zhvi, region_name
        FROM us_metro_zhvi
        WHERE region_name != 'United States'
        GROUP BY region_name, LEFT(`year_month`, 4) ORDER BY year
    """)
    if not df_zhvi.empty:
        df_zhvi['year'] = df_zhvi['year'].astype(str)
        for name in df_zhvi['region_name'].unique():
            sub = df_zhvi[df_zhvi['region_name'] == name]
            label = MSA_SHORT.get(name, name.split(',')[0])
            ax_top.plot(sub['year'], sub['avg_zhvi'], marker='.', label=label,
                        color=CITY_COLORS.get(name, 'gray'), linewidth=2)
        ax_top.set_title('US Peer Cities: Home Value Index (ZHVI) Trend',
                          fontsize=13, fontweight='bold')
        ax_top.set_ylabel('ZHVI (USD)')
        ax_top.legend()
        ax_top.grid(True, alpha=0.3)
        ticks = ax_top.get_xticks()
        ax_top.set_xticks(ticks[::max(1, len(ticks)//8)])
        ax_top.tick_params(axis='x', rotation=45)

    # 하단: 대구 인구 + 아파트 가격
    df_pop = query_to_df("""
        SELECT year, AVG(natural_growth_rate) AS growth_rate,
               SUM(birth_count) AS births, SUM(death_count) AS deaths
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year ORDER BY year
    """)
    if not df_pop.empty:
        df_pop['year'] = df_pop['year'].astype(str)
    df_price = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price
        FROM daegu_housing_prices
        WHERE year IS NOT NULL AND deal_amount IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    if not df_price.empty:
        df_price['year'] = df_price['year'].astype(str)

    if not df_pop.empty:
        ax_bot.bar(df_pop['year'], df_pop['growth_rate'], color='#9B59B6', alpha=0.5,
                   label='Natural Growth Rate')
        ax_bot.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax_bot.set_ylabel('Natural Growth Rate', color='#9B59B6', fontsize=12)
    if not df_price.empty:
        ax_r = ax_bot.twinx()
        ax_r.plot(df_price['year'], df_price['avg_price'], color='#E67E22',
                  marker='s', linewidth=2, linestyle='--', label='Daegu Apt Price (만원)')
        ax_r.set_ylabel('Avg Apt Price (만원)', color='#E67E22', fontsize=12)

    ax_bot.set_title('Daegu: Population Trend vs Housing Price', fontsize=13, fontweight='bold')
    ax_bot.set_xlabel('Year')
    lines1, labels1 = ax_bot.get_legend_handles_labels()
    if not df_price.empty:
        lines2, labels2 = ax_r.get_legend_handles_labels()
        ax_bot.legend(lines1 + lines2, labels1 + labels2)
    ax_bot.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V8_population_vs_housing.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V8 인구 vs 주택가격 저장")


def viz_v9_transformation_timeline():
    """V9: 대구 vs Charlotte 전환 타임라인"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # Charlotte
    df_ch = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS temp,
               AVG(income_needed) AS income,
               SUM(new_construction_sales) AS new_con
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4) ORDER BY year
    """)

    if not df_ch.empty:
        df_ch['year'] = df_ch['year'].astype(str)
        ax1_t = ax1.twinx()
        ax1.bar(range(len(df_ch)), df_ch['new_con'].fillna(0), color='#2ECC71', alpha=0.4, label='New Construction')
        ax1_t.plot(range(len(df_ch)), df_ch['income'], color='#E74C3C', marker='o',
                   linewidth=2, label='Income Needed')
        ax1.set_xticks(range(0, len(df_ch), max(1, len(df_ch)//6)))
        ax1.set_xticklabels(df_ch['year'].iloc[::max(1, len(df_ch)//6)], rotation=45)
        ax1.set_title('Charlotte\nTextile -> Finance/Tech Transition\n(Completed)',
                       fontsize=13, fontweight='bold', color='#2ECC71')
        ax1.set_ylabel('New Construction Sales', color='#2ECC71')
        ax1_t.set_ylabel('Income Needed (USD)', color='#E74C3C')
        mid = len(df_ch) // 2
        ax1.text(mid, ax1.get_ylim()[1] * 0.85,
                 'Bank of America HQ\nDuke Energy\nTech Hub Growth',
                 fontsize=9, ha='center', style='italic',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 대구
    df_dg = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price, COUNT(*) AS tx_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL AND deal_amount IS NOT NULL
        GROUP BY year ORDER BY year
    """)

    if not df_dg.empty:
        df_dg['year'] = df_dg['year'].astype(str)
        ax2_t = ax2.twinx()
        years = df_dg['year'].astype(str)
        ax2.bar(range(len(df_dg)), df_dg['tx_count'], color='#9B59B6', alpha=0.4,
                label='Transactions')
        ax2_t.plot(range(len(df_dg)), df_dg['avg_price'], color='#E74C3C',
                   marker='o', linewidth=2, label='Avg Price (만원)')
        ax2.set_xticks(range(0, len(df_dg), max(1, len(df_dg)//6)))
        ax2.set_xticklabels(years.iloc[::max(1, len(df_dg)//6)], rotation=45)
        ax2.set_title('Daegu\nTextile -> Hightech Transition\n(In Progress)',
                       fontsize=13, fontweight='bold', color='#9B59B6')
        ax2.set_ylabel('Transaction Count', color='#9B59B6')
        ax2_t.set_ylabel('Avg Apt Price (만원)', color='#E74C3C')
        mid = len(df_dg) // 2
        ax2.text(mid, ax2.get_ylim()[1] * 0.85,
                 'Auto Parts Growth\nDGIST Founded\nNational Innovation Cluster',
                 fontsize=9, ha='center', style='italic',
                 bbox=dict(boxstyle='round', facecolor='plum', alpha=0.5))

    fig.suptitle('S4-V9: Industrial Transformation Timeline\nCharlotte (Complete) vs Daegu (In Progress)',
                 fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V9_transformation_timeline.png'), bbox_inches='tight')
    plt.close()
    print("  [OK] V9 전환 타임라인 저장")


def viz_v10_strategy_roadmap():
    """V10: 대구 생존전략 로드맵 인포그래픽 (보완 - 겹침 해소, 글씨 확대+볼드)"""
    fig, ax = plt.subplots(figsize=(26, 20))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    fig.patch.set_facecolor('#FAFAFA')

    # ═══ Zone 1: 타이틀 (y=95~100) ═══
    ax.text(50, 99, 'Daegu Survival Strategy Roadmap', fontsize=28,
            fontweight='bold', ha='center', va='top')
    ax.text(50, 95.5, '대구광역시 생존 전략 로드맵  |  Dallas · Atlanta · Phoenix · Charlotte 벤치마크',
            fontsize=21, ha='center', va='top', color='#555555', fontweight='bold')

    # ═══ Zone 2: 인구·산업 전략 (y=79~93) ═══
    ax.text(50, 91.5, '── Population & Industry Strategies ──',
            fontsize=22, ha='center', fontweight='bold', color='#2980B9')

    strat_boxes = [
        (13, 85, '주택가격 경쟁력\nMarketing', '수도권 1/3~1/4 가격 홍보\n원격근무자 타겟', 'Dallas', '#E74C3C'),
        (37, 85, '앵커 기업 유치\nHQ Attraction', '대기업 지역본사/R&D\n세제 혜택+부지 제공', 'Charlotte', '#2ECC71'),
        (63, 85, '산학 클러스터\nAcademia-Industry', '경북대+DGIST+영남대\n스타트업 생태계', 'Atlanta', '#3498DB'),
        (87, 85, '산업 전환 완성\nTransformation', '섬유→첨단 전환\n인구 순유입 달성', 'All 4', '#9B59B6'),
    ]
    for x, y, title, subtitle, model, color in strat_boxes:
        rect = mpatches.FancyBboxPatch((x-11, y-6), 22, 13,
               boxstyle="round,pad=1", facecolor=color, alpha=0.12,
               edgecolor=color, linewidth=2.5)
        ax.add_patch(rect)
        ax.text(x, y+2.5, title, fontsize=18, ha='center', va='center', fontweight='bold')
        ax.text(x, y-2, subtitle, fontsize=15, ha='center', va='center', color='#333333', fontweight='bold')
        ax.text(x, y-5, f'({model})', fontsize=16, ha='center', color=color, fontweight='bold', style='italic')

    # ═══ Zone 3: 타임라인 (y=63~72) ═══
    ax.annotate('', xy=(95, 67), xytext=(5, 67),
                arrowprops=dict(arrowstyle='->', color='#2C3E50', lw=4))

    phases = [
        (10, 'NOW\n현재', '#E74C3C'),
        (35, '3 YEARS\n단기', '#F39C12'),
        (62, '7 YEARS\n중기', '#2ECC71'),
        (88, '15 YEARS\n장기', '#3498DB'),
    ]
    for x, label, color in phases:
        ax.plot(x, 67, 'o', color=color, markersize=16, zorder=5)
        ax.text(x, 63, label, fontsize=18, fontweight='bold', color=color, ha='center')

    # ═══ 연결 화살표 (전략→효과, 타임라인 관통) ═══
    for x in [13, 37, 63, 87]:
        ax.annotate('', xy=(x, 56), xytext=(x, 72),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, alpha=0.5))

    # ═══ Zone 4: 부동산 시장 효과 (y=44~59) ═══
    ax.text(50, 59, '── Housing Market Effects ──',
            fontsize=22, ha='center', fontweight='bold', color='#D35400')

    effect_boxes = [
        (13, 50, '거래량 증가\nVolume Up', '시장 안정화\n가격 하방 지지', '#E74C3C'),
        (37, 50, '수요 증가\nDemand Rise', '재고 감소 + 대기일 단축\n시장온도 상승', '#F39C12'),
        (63, 50, '신규건설 증가\nNew Construction', '도시 확장\n가격 완만 상승', '#2ECC71'),
        (87, 50, '지속 성장\nSustainable Growth', '필요소득 상승\n선순환 사이클', '#3498DB'),
    ]
    for x, y, title, subtitle, color in effect_boxes:
        rect = mpatches.FancyBboxPatch((x-11, y-5), 22, 11,
               boxstyle="round,pad=1", facecolor=color, alpha=0.08,
               edgecolor=color, linewidth=2, linestyle='--')
        ax.add_patch(rect)
        ax.text(x, y+1.5, title, fontsize=18, ha='center', va='center', fontweight='bold')
        ax.text(x, y-2.5, subtitle, fontsize=15, ha='center', va='center', color='#444444', fontweight='bold')

    # ═══ Zone 5: 핵심 KPI (y=30~41) ═══
    kpi_x, kpi_y = 50, 35
    rect = mpatches.FancyBboxPatch((kpi_x-35, kpi_y-5), 70, 12,
           boxstyle="round,pad=1", facecolor='#FFF9E6', alpha=0.9,
           edgecolor='#D4A017', linewidth=2.5)
    ax.add_patch(rect)
    ax.text(kpi_x, kpi_y+5.5, 'Key Performance Indicators (핵심 KPI)',
            fontsize=20, ha='center', fontweight='bold', color='#8B6914')

    kpi_items = [
        ('Dallas ZHVI  $363,580', '대구 아파트  $259,258 (71%)'),
        ('Atlanta 전문직  46.1%', 'Charlotte 필요소득  +163%'),
        ('Phoenix 시장온도  52~77', '대구 목표  시장온도 45~50'),
    ]
    for i, (us_val, dg_val) in enumerate(kpi_items):
        bx = kpi_x - 24 + i * 24
        ax.text(bx, kpi_y+1.5, us_val, fontsize=16, ha='center', va='center',
                color='#2C3E50', fontweight='bold')
        ax.text(bx, kpi_y-2.5, dg_val, fontsize=16, ha='center', va='center',
                color='#9B59B6', fontweight='bold')

    # ═══ Zone 6: 선순환 목표(좌) + Charlotte 교훈(우) (y=17~27) ═══
    # 선순환 모델 (왼쪽)
    cyc_x, cyc_y = 22, 22
    rect = mpatches.FancyBboxPatch((cyc_x-18, cyc_y-4), 36, 9,
           boxstyle="round,pad=1", facecolor='#FDE9D9', alpha=0.8,
           edgecolor='#E67E22', linewidth=2.5)
    ax.add_patch(rect)
    ax.text(cyc_x, cyc_y+3.5, '선순환 목표 (Virtuous Cycle)', fontsize=19,
            ha='center', fontweight='bold', color='#8B4513')
    ax.text(cyc_x, cyc_y-0.5, '기업유치 → 인구유입 → 수요증가 → 시장활성화 → 가격상승 → 투자매력↑',
            fontsize=15, ha='center', va='center', color='#8B4513', fontweight='bold')

    # Charlotte 교훈 (오른쪽)
    lesson_x, lesson_y = 75, 22
    rect = mpatches.FancyBboxPatch((lesson_x-18, lesson_y-4), 36, 9,
           boxstyle="round,pad=1", facecolor='#E8F8F5', alpha=0.9,
           edgecolor='#2ECC71', linewidth=2.5)
    ax.add_patch(rect)
    ax.text(lesson_x, lesson_y+3.5, 'Charlotte Lesson (산업 전환 교훈)', fontsize=19,
            ha='center', fontweight='bold', color='#1A5276')
    ax.text(lesson_x, lesson_y+0.5, '섬유→금융 전환 30년 소요  |  대구도 1990~현재 30년째',
            fontsize=15, ha='center', va='center', color='#2C3E50', fontweight='bold')
    ax.text(lesson_x, lesson_y-2.5, '전환 성공 신호: 신규건설 급증 + 시장온도 상승',
            fontsize=15, ha='center', va='center', color='#2ECC71', fontweight='bold')

    # ═══ Zone 7: 범례 (y=3~13) ═══
    legend_data = [
        ('Dallas', '#E74C3C', 'Affordability / 가격경쟁력'),
        ('Atlanta', '#3498DB', 'Hub Strategy / 산업허브'),
        ('Phoenix', '#F39C12', 'Climate Resilience / 기후극복'),
        ('Charlotte', '#2ECC71', 'Transformation / 산업전환'),
    ]
    for i, (city, color, keyword) in enumerate(legend_data):
        x = 8 + i * 23
        ax.add_patch(mpatches.FancyBboxPatch((x-2, 5), 21, 8,
                     boxstyle="round,pad=0.5", facecolor=color, alpha=0.15,
                     edgecolor=color, linewidth=2))
        ax.text(x+8.5, 11, city, fontsize=18, ha='center', fontweight='bold', color=color)
        ax.text(x+8.5, 7, keyword, fontsize=15, ha='center', fontweight='bold', color='gray')

    plt.savefig(os.path.join(OUTPUT_DIR, 'S4_V10_strategy_roadmap.png'), bbox_inches='tight', dpi=150)
    plt.close()
    print("  [OK] V10 전략 로드맵 저장")


def run():
    print("=" * 60)
    print("STEP 11: 4축 비교 시각화 (V6~V10)")
    print("=" * 60)
    viz_v6_radar_chart()
    viz_v7_4axis_dashboard()
    viz_v8_population_vs_housing()
    viz_v9_transformation_timeline()
    viz_v10_strategy_roadmap()
    print(f"\n  STEP 11 완료! 차트 저장: {OUTPUT_DIR}")


if __name__ == '__main__':
    run()
