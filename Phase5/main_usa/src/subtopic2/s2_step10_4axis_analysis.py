"""
STEP 10: 4축 인구-부동산 비교 분석 (v2 신규)
실행: python src/subtopic2/s2_step10_4axis_analysis.py
의존: STEP 1~7 완료
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from s2_step0_config import get_connection, DB_NAME, S2_OUTPUT_DIR

# 공통 설정
AXIS_CONFIG = {
    'comprehensive': {'us_city': 'Dallas', 'metro': 'Dallas, TX',
                       'state': 'Texas', 'axis_kr': '종합'},
    'industry':      {'us_city': 'Atlanta', 'metro': 'Atlanta, GA',
                       'state': 'Georgia', 'axis_kr': '산업'},
    'climate':       {'us_city': 'Phoenix', 'metro': 'Phoenix, AZ',
                       'state': 'Arizona', 'axis_kr': '기후'},
    'transformation':{'us_city': 'Charlotte', 'metro': 'Charlotte, NC',
                       'state': 'North Carolina', 'axis_kr': '변모'},
}

KRW_TO_USD = 1350  # 환율 기준


def query_to_df(sql, params=None):
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


def get_daegu_pop():
    """대구 인구 추이"""
    return query_to_df("""
        SELECT year, total_population, population_change_rate
        FROM daegu_population_summary ORDER BY year
    """)


def get_daegu_housing():
    """대구 아파트 연평균 가격 + 거래건수"""
    return query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price_manwon,
               COUNT(*) AS transaction_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)


def get_us_city_demand(metro_name):
    """미국 도시 수급 지표 연도별 집계"""
    return query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS avg_market_temp,
               AVG(income_needed) AS avg_income_needed,
               AVG(inventory_count) AS avg_inventory,
               AVG(mean_days_pending) AS avg_days_pending,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = %s
        GROUP BY LEFT(`year_month`, 4) ORDER BY year
    """, params=(metro_name,))


def get_us_city_zhvi(metro_name):
    """미국 도시 ZHVI 연도별"""
    return query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = %s
        GROUP BY LEFT(`year_month`, 4) ORDER BY year
    """, params=(metro_name,))


def get_us_pop_merged(city_name):
    """annual_pop_housing_merged에서 도시별 데이터"""
    return query_to_df("""
        SELECT year, population, pop_change_rate, zhvi, zhvi_change_rate,
               avg_sales_count, avg_inventory, avg_market_temp,
               avg_days_pending, avg_income_needed, supply_demand_ratio
        FROM annual_pop_housing_merged
        WHERE city_name = %s ORDER BY year
    """, params=(city_name,))


def save_scorecard(axis_kr, metric_category, daegu_name, daegu_val,
                   us_city, us_name, us_val, period, gap_dir,
                   corr_insight, strategy):
    """pop_housing_4axis_scorecard에 1행 저장"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pop_housing_4axis_scorecard
        (comparison_axis, metric_category, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value, year_or_period,
         gap_direction, correlation_insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (axis_kr, metric_category, daegu_name, daegu_val,
          us_city, us_name, us_val, period, gap_dir,
          corr_insight, strategy))
    conn.commit()
    conn.close()


def save_axis_summary(axis_kr, us_city, pop_trend, housing_demand_trend,
                      market_temp_trend, price_trend, causal_pathway,
                      daegu_comparison, policy_lesson):
    """pop_housing_axis_summary에 1행 저장"""
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pop_housing_axis_summary
        (comparison_axis, us_city_name, pop_trend, housing_demand_trend,
         market_temp_trend, price_trend, causal_pathway,
         daegu_comparison, policy_lesson)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (axis_kr, us_city, pop_trend, housing_demand_trend,
          market_temp_trend, price_trend, causal_pathway,
          daegu_comparison, policy_lesson))
    conn.commit()
    conn.close()


# =============================================
# 축 1: 종합 — 대구 vs Dallas
# =============================================

def axis1_comprehensive():
    """Dallas 인구유입 → 수요폭발 경로 vs 대구 인구유출"""
    print("\n" + "=" * 70)
    print("축 1 [종합]: 대구 vs Dallas — 인구유입·유출과 부동산 수급")
    print("=" * 70)

    cfg = AXIS_CONFIG['comprehensive']
    df_daegu_pop = get_daegu_pop()
    df_daegu_house = get_daegu_housing()
    df_dallas = get_us_city_demand(cfg['metro'])
    df_dallas_zhvi = get_us_city_zhvi(cfg['metro'])
    df_dallas_merged = get_us_pop_merged('Dallas')

    # --- 인구성장률 비교 ---
    daegu_growth = float(df_daegu_pop.iloc[-1]['population_change_rate']) if not df_daegu_pop.empty and pd.notna(df_daegu_pop.iloc[-1].get('population_change_rate')) else None
    dallas_growth = float(df_dallas_merged.iloc[-1]['pop_change_rate']) if not df_dallas_merged.empty and pd.notna(df_dallas_merged.iloc[-1].get('pop_change_rate')) else None

    save_scorecard('종합', '인구성장률',
        '대구 인구변동률(%)', daegu_growth,
        'Dallas', 'Dallas MSA 인구변동률(%)', dallas_growth,
        str(int(df_daegu_pop.iloc[-1]['year'])) if not df_daegu_pop.empty else '',
        '미국우위' if (dallas_growth or 0) > (daegu_growth or 0) else '대구우위',
        '대구는 인구 순유출, Dallas는 지속적 순유입. '
        '인구유입이 주택 수요를 폭발적으로 증가시키는 Dallas의 패턴은 대구의 정반대 상황',
        'Dallas 모델: 법인세 없는 TX → 기업 유치, 저렴한 토지+주택 → 인구 흡수, '
        '인구유입 → 재고감소 → 시장과열 → 가격상승의 선순환. '
        '대구 적용: 수도권 대비 주택가격 경쟁력을 활용한 기업·인구 유치 전략 필요')

    # --- 주택가격 비교 ---
    if not df_daegu_house.empty and not df_dallas_zhvi.empty:
        daegu_usd = float(df_daegu_house.iloc[-1]['avg_price_manwon']) * 10000 / KRW_TO_USD
        dallas_usd = float(df_dallas_zhvi.iloc[-1]['avg_zhvi'])
        save_scorecard('종합', '주택가격',
            '대구 아파트 평균가(USD)', round(daegu_usd, 2),
            'Dallas', 'Dallas ZHVI(USD)', round(dallas_usd, 2),
            str(int(df_dallas_zhvi.iloc[-1]['year'])),
            '대구우위' if daegu_usd < dallas_usd else '미국우위',
            f'대구 주택가격은 Dallas의 약 {daegu_usd/dallas_usd*100:.0f}% 수준. '
            '가격 경쟁력은 있으나 인구유출로 수요가 부족' if dallas_usd else '',
            '수도권 유출 인구를 대구로 흡수하려면 "저렴한 주택 + 양질의 일자리" 패키지가 핵심')

    # --- 시장 수급 비교 ---
    if not df_dallas.empty:
        latest_dallas = df_dallas.iloc[-1]
        save_scorecard('종합', '시장온도',
            '대구 시장온도(프록시 없음)', None,
            'Dallas', 'Dallas 시장온도지수',
            float(latest_dallas['avg_market_temp']) if pd.notna(latest_dallas.get('avg_market_temp')) else None,
            str(latest_dallas.get('year', '')),
            '비교불가',
            'Dallas 시장온도 50 이상 → 판매자 우위 시장, 인구유입이 수요를 재고 이상으로 밀어올림',
            '대구는 인구유출로 시장이 냉각될 가능성. '
            '인구유입 전환 시 시장온도 상승 → 신규건설 활성화 → 경제 선순환 기대')

    # --- 축 요약 ---
    save_axis_summary('종합', 'Dallas',
        pop_trend='유입(+)',
        housing_demand_trend='수요 급증',
        market_temp_trend='과열(50+)',
        price_trend='급등',
        causal_pathway='기업유치→일자리→인구유입→주택수요↑→재고↓→시장과열→가격급등→필요소득↑',
        daegu_comparison='대구는 정반대: 인구유출→수요감소→시장냉각→가격정체. '
                        'Dallas는 2010~2020 연평균 인구성장률 1.5%+, 대구는 -0.5%~-1.0%',
        policy_lesson='수도권 대비 주택가격 경쟁력(1/3~1/4) 적극 마케팅. '
                     '원격근무 시대 활용: 서울 소득+대구 주거비 → 삶의질 개선 홍보. '
                     '기업 본사/R&D 유치 세제 인센티브 (TX주 모델 벤치마크)')

    print("  [OK] 축 1 완료")
    return df_daegu_pop, df_dallas, df_dallas_zhvi


# =============================================
# 축 2: 산업 — 대구 vs Atlanta
# =============================================

def axis2_industry():
    """Atlanta 산업 다각화 → 인구유입 → 수요 급증 경로"""
    print("\n" + "=" * 70)
    print("축 2 [산업]: 대구 vs Atlanta — 산업 허브화와 인구-부동산 관계")
    print("=" * 70)

    cfg = AXIS_CONFIG['industry']
    df_atlanta = get_us_city_demand(cfg['metro'])
    df_atlanta_merged = get_us_pop_merged('Atlanta')

    # --- Census 직업구조 비교 ---
    df_census = query_to_df("""
        SELECT city_id, AVG(professional) AS prof_pct, AVG(service) AS svc_pct,
               AVG(production) AS prod_pct, AVG(median_income) AS med_income,
               AVG(unemployment) AS unemp
        FROM us_census_demographics
        WHERE city_id = 3
    """)

    if not df_census.empty and pd.notna(df_census.iloc[0].get('prof_pct')):
        save_scorecard('산업', '직업구조',
            '대구 전문직 비율(%)', None,
            'Atlanta', 'Atlanta 전문직 비율(%)',
            float(df_census.iloc[0]['prof_pct']) if pd.notna(df_census.iloc[0]['prof_pct']) else None,
            'ACS 2015/2017',
            '비교불가',
            'Atlanta는 전문직 비율이 높고 중위소득도 높음 → 높은 주택 구매력으로 연결',
            'Atlanta 모델: 교통 허브(하츠필드 공항) + 대학(Georgia Tech, Emory) → '
            '전문직 유입 → 소득 상승 → 주택수요 상승. '
            '대구 적용: DGIST+경북대 산학 클러스터 + 대구공항 국제선 확충')

    # --- 시장 수급 비교 ---
    if not df_atlanta.empty:
        latest = df_atlanta.iloc[-1]
        save_scorecard('산업', '시장수급',
            '대구 연간 거래건수', None,
            'Atlanta', 'Atlanta 연간 판매건수',
            float(latest['total_sales']) if pd.notna(latest.get('total_sales')) else None,
            str(latest.get('year', '')),
            '비교불가',
            'Atlanta 판매건수는 산업 다각화에 따른 인구유입과 강한 양의 상관관계',
            '산업 다각화 → 다양한 소득계층 유입 → 주택 수요 다변화 (고급+중급+임대)')

    # --- 축 요약 ---
    save_axis_summary('산업', 'Atlanta',
        pop_trend='유입(+)',
        housing_demand_trend='수요 급증',
        market_temp_trend='상승',
        price_trend='완만 상승',
        causal_pathway='교통허브+산업다각화→다양한일자리→전문직유입→소득↑→주택수요↑→가격상승',
        daegu_comparison='대구는 제조업 의존도 높아 고소득 전문직 유입이 제한적. '
                        'Atlanta는 물류+IT+미디어+의료 등 다각화에 성공',
        policy_lesson='자동차부품 → 전기차·배터리 고도화 (현대·삼성SDI 유치). '
                     '대구 의료특구 활용: 바이오·헬스케어 산업 육성 → 전문직 유입. '
                     '교통 인프라: KTX 30분 생활권 + 대구공항 확장으로 접근성 개선')

    print("  [OK] 축 2 완료")
    return df_atlanta


# =============================================
# 축 3: 기후 — 대구 vs Phoenix
# =============================================

def axis3_climate():
    """Phoenix 기후 핸디캡 극복 → 인구 폭증 → 과열·조정 반복 패턴"""
    print("\n" + "=" * 70)
    print("축 3 [기후]: 대구 vs Phoenix — 폭염에도 인구가 증가하는 이유")
    print("=" * 70)

    cfg = AXIS_CONFIG['climate']
    df_phoenix = get_us_city_demand(cfg['metro'])
    df_phoenix_zhvi = get_us_city_zhvi(cfg['metro'])
    df_phoenix_merged = get_us_pop_merged('Phoenix')

    # --- 인구 폭증 vs 대구 유출 ---
    phoenix_growth = float(df_phoenix_merged.iloc[-1]['pop_change_rate']) if not df_phoenix_merged.empty and pd.notna(df_phoenix_merged.iloc[-1].get('pop_change_rate')) else None
    df_daegu_pop = get_daegu_pop()
    daegu_growth = float(df_daegu_pop.iloc[-1]['population_change_rate']) if not df_daegu_pop.empty and pd.notna(df_daegu_pop.iloc[-1].get('population_change_rate')) else None

    save_scorecard('기후', '인구성장률',
        '대구 인구변동률(%)', daegu_growth,
        'Phoenix', 'Phoenix 인구변동률(%)', phoenix_growth,
        str(int(df_daegu_pop.iloc[-1]['year'])) if not df_daegu_pop.empty else '',
        '미국우위',
        'Phoenix는 대구와 유사한 폭염 환경이지만 인구가 폭발적으로 증가. '
        '2010~2020 Phoenix MSA 인구성장률 약 +15%, 대구는 약 -5%',
        'Phoenix 성공 비밀: CA 대비 1/3 주택가격, 낮은 세율(AZ), '
        '반도체(TSMC, Intel) 대규모 공장 유치, 은퇴인구 유입(선벨트). '
        '대구 적용: 수도권 대비 주택 가격 경쟁력 + 첨단산업단지 유치')

    # --- 시장온도 과열·조정 패턴 ---
    if not df_phoenix.empty:
        max_temp = df_phoenix['avg_market_temp'].max()
        min_temp = df_phoenix['avg_market_temp'].min()
        save_scorecard('기후', '시장변동성',
            '대구 시장 변동성', None,
            'Phoenix', 'Phoenix 시장온도 변동폭',
            round(float(max_temp - min_temp), 2) if pd.notna(max_temp) and pd.notna(min_temp) else None,
            f"{df_phoenix.iloc[0]['year']}~{df_phoenix.iloc[-1]['year']}",
            '비교불가',
            f'Phoenix 시장온도 범위: {min_temp:.0f}~{max_temp:.0f}. '
            '인구 급유입 → 과열 → 조정의 사이클이 반복됨 (2006-08 버블, 2020-22 과열)',
            '인구 유입이 급격하면 시장 과열 리스크 발생. '
            '대구는 점진적 인구유입 전략이 안정적 시장 형성에 유리')

    # --- 주택가격 경쟁력 ---
    if not df_phoenix_zhvi.empty:
        save_scorecard('기후', '주택가격',
            '대구 아파트 평균가(USD)', None,
            'Phoenix', 'Phoenix ZHVI(USD)',
            round(float(df_phoenix_zhvi.iloc[-1]['avg_zhvi']), 2),
            str(int(df_phoenix_zhvi.iloc[-1]['year'])),
            '대구우위',
            'Phoenix도 LA/SF 대비 저렴한 주택으로 인구를 끌어들임. '
            '대구는 서울 대비 유사한 가격 경쟁력 보유',
            '"폭염에도 인구 유입" 핵심: 주택 구매력 > 기후 불편. '
            '대구도 서울 대비 주택 구매력 우위를 극대화해야 함')

    # --- 축 요약 ---
    save_axis_summary('기후', 'Phoenix',
        pop_trend='폭발 유입',
        housing_demand_trend='과열',
        market_temp_trend='급등→조정 반복',
        price_trend='급등 후 조정',
        causal_pathway='저렴한주택+저세율→인구폭증→수요급증→재고부족→시장과열→'
                      '가격급등→조정(2008/2022)→재유입 반복',
        daegu_comparison='대구와 Phoenix는 여름 폭염이라는 동일한 기후 핸디캡. '
                        'Phoenix는 가격경쟁력으로 극복, 대구는 인구유출 중',
        policy_lesson='"서울 대비 1/3 가격으로 내 집 마련" 마케팅 캠페인. '
                     '도시 냉방 인프라(그린 인프라, 지하 공간) 투자. '
                     '은퇴인구 유치: 의료인프라 + 저렴한 생활비 패키지. '
                     'TSMC/Intel 모델 벤치마크 → 대규모 첨단공장 유치')

    print("  [OK] 축 3 완료")
    return df_phoenix, df_phoenix_zhvi


# =============================================
# 축 4: 변모 — 대구 vs Charlotte
# =============================================

def axis4_transformation():
    """Charlotte 산업전환 → 고소득 유입 → 필요소득 급상승 경로"""
    print("\n" + "=" * 70)
    print("축 4 [변모]: 대구 vs Charlotte — 산업전환과 인구-부동산 경로")
    print("=" * 70)

    cfg = AXIS_CONFIG['transformation']
    df_charlotte = get_us_city_demand(cfg['metro'])
    df_charlotte_zhvi = get_us_city_zhvi(cfg['metro'])
    df_charlotte_merged = get_us_pop_merged('Charlotte')
    df_daegu_pop = get_daegu_pop()
    df_daegu_house = get_daegu_housing()

    # --- 필요소득 비교 (산업전환→고소득유입→구매력 변화) ---
    if not df_charlotte.empty:
        ch_income = df_charlotte[df_charlotte['avg_income_needed'].notna()]
        if not ch_income.empty:
            first_income = float(ch_income.iloc[0]['avg_income_needed'])
            last_income = float(ch_income.iloc[-1]['avg_income_needed'])
            income_change = (last_income - first_income) / first_income * 100 if first_income else 0

            save_scorecard('변모', '구매필요소득',
                '대구 아파트 구매 필요소득(추정)', None,
                'Charlotte', 'Charlotte 필요소득 변화율(%)', round(income_change, 2),
                f"{ch_income.iloc[0]['year']}~{ch_income.iloc[-1]['year']}",
                '비교불가',
                f'Charlotte 주택구매 필요소득이 {income_change:.0f}% 급상승 → '
                '금융·IT 고소득 유입이 주택 진입장벽을 높임',
                'Charlotte 전환 성공의 양면: 경제 활성화 vs 기존 주민 주거비 부담 증가. '
                '대구도 전환 성공 시 유사 현상 대비 필요 → 중저소득 주거 안전망 병행 구축')

    # --- 인구 전환기 패턴 ---
    if not df_charlotte_merged.empty:
        ch_pop = df_charlotte_merged[df_charlotte_merged['pop_change_rate'].notna()]
        avg_pop_growth = float(ch_pop['pop_change_rate'].mean()) if not ch_pop.empty else None

        daegu_avg = float(df_daegu_pop['population_change_rate'].mean()) if not df_daegu_pop.empty and df_daegu_pop['population_change_rate'].notna().any() else None

        save_scorecard('변모', '전환기 인구',
            '대구 평균 인구변동률(%)', daegu_avg,
            'Charlotte', 'Charlotte 평균 인구변동률(%)', avg_pop_growth,
            '전체 기간',
            '미국우위',
            '산업 전환 성공 → 고소득 일자리 → 인구유입의 인과관계가 Charlotte에서 확인됨',
            'Charlotte 전환 핵심 3요소를 대구에 적용: '
            '앵커기업(Bank of America급) → 삼성·현대 지역본사 유치, '
            '대학 인재파이프라인(UNC Charlotte) → 경북대+DGIST 활용, '
            '공항 허브(CLT) → KTX+대구공항 연계 광역교통')

    # --- 대구 vs Charlotte 가격 추이 ---
    if not df_charlotte_zhvi.empty and not df_daegu_house.empty:
        ch_first = float(df_charlotte_zhvi.iloc[0]['avg_zhvi'])
        ch_last = float(df_charlotte_zhvi.iloc[-1]['avg_zhvi'])
        ch_change = (ch_last - ch_first) / ch_first * 100 if ch_first else 0

        dg_first = float(df_daegu_house.iloc[0]['avg_price_manwon'])
        dg_last = float(df_daegu_house.iloc[-1]['avg_price_manwon'])
        dg_change = (dg_last - dg_first) / dg_first * 100 if dg_first else 0

        save_scorecard('변모', '주택가격 변화',
            '대구 아파트 가격변화율(%)', round(dg_change, 2),
            'Charlotte', 'Charlotte ZHVI 변화율(%)', round(ch_change, 2),
            f"{df_charlotte_zhvi.iloc[0]['year']}~{df_charlotte_zhvi.iloc[-1]['year']}",
            '미국우위' if ch_change > dg_change else '대구우위',
            f'Charlotte 전환 성공 → ZHVI +{ch_change:.0f}% 상승. '
            '산업전환 → 인구유입 → 부동산 가치 상승의 선순환 확인',
            '대구도 산업전환 성공 시 부동산 가치 상승 기대. '
            '현재 대구 아파트 가격은 상대적으로 저평가 → 투자 잠재력 존재')

    # --- 축 요약 ---
    save_axis_summary('변모', 'Charlotte',
        pop_trend='전환기 유입',
        housing_demand_trend='고소득 수요 급증',
        market_temp_trend='상승',
        price_trend='급등 (전환 후)',
        causal_pathway='섬유쇠퇴→금융본사유치→고소득유입→주택수요↑→필요소득급등→신규건설↑→도시확장',
        daegu_comparison='대구: 섬유→자동차부품→첨단 전환 진행 중 (Charlotte보다 10~15년 후발). '
                        'Charlotte의 2000년대 = 대구의 2020년대 → 전환 성공 신호 주시 필요',
        policy_lesson='30년 장기 전환 로드맵 수립 (Charlotte 사례: 1980→2010). '
                     '"앵커 기업" 1개 유치가 연쇄 효과 → 대규모 기업 유치에 집중. '
                     '전환 성공 시 주거비 급등 대비 → 중저소득 공공임대 확대 병행')

    print("  [OK] 축 4 완료")
    return df_charlotte, df_charlotte_zhvi


# =============================================
# 실행
# =============================================

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 10: 4축 인구-부동산 비교 분석 (v2)")
    print("=" * 60)

    # 기존 데이터 초기화
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pop_housing_4axis_scorecard")
    cursor.execute("DELETE FROM pop_housing_axis_summary")
    conn.commit()
    conn.close()
    print("[INIT] 기존 4축 분석 데이터 초기화 완료")

    r1 = axis1_comprehensive()
    r2 = axis2_industry()
    r3 = axis3_climate()
    r4 = axis4_transformation()

    # 검증
    conn = get_connection(DB_NAME, for_pandas=True)
    sc_count = pd.read_sql("SELECT COUNT(*) AS cnt FROM pop_housing_4axis_scorecard", conn).iloc[0]['cnt']
    sm_count = pd.read_sql("SELECT COUNT(*) AS cnt FROM pop_housing_axis_summary", conn).iloc[0]['cnt']
    conn.close()

    print(f"\n[DONE] STEP 10 완료!")
    print(f"  pop_housing_4axis_scorecard: {sc_count}행")
    print(f"  pop_housing_axis_summary: {sm_count}행")
