"""
STEP 8: 4축 비교 분석 (v2 신규)
- 축 1: 종합 (대구 vs Dallas) - 인구, 주택가격, 필요소득
- 축 2: 산업 (대구 vs Atlanta) - 산업구조, 신규건설
- 축 3: 기후 (대구 vs Phoenix) - 기온, 주택 경쟁력
- 축 4: 변모 (대구 vs Charlotte) - 산업전환, 부동산 변화
결과 → city_axis_scorecard 테이블
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def axis1_comprehensive_daegu_vs_dallas():
    """축 1: 종합 비교 - 대구 vs Dallas"""
    print("\n" + "=" * 70)
    print("축 1: 종합 비교 — 대구 vs Dallas")
    print("=" * 70)

    # 대구 인구 추이 (연도별 평균)
    df_daegu_pop = query_to_df("""
        SELECT year,
               AVG(birth_rate) AS avg_birth_rate,
               AVG(death_rate) AS avg_death_rate,
               AVG(natural_growth_rate) AS avg_growth_rate
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year ORDER BY year
    """)
    if not df_daegu_pop.empty:
        df_daegu_pop['year'] = df_daegu_pop['year'].astype(str)
        latest = df_daegu_pop.iloc[-1]
        print(f"  대구 최근 자연증가율: {latest.get('avg_growth_rate')}")

    # Dallas ZHVI
    df_dallas_zhvi = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = 'Dallas, TX'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_dallas_zhvi.empty:
        df_dallas_zhvi['year'] = df_dallas_zhvi['year'].astype(str)

    # Dallas 수급
    df_dallas = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Dallas, TX'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_dallas.empty:
        df_dallas['year'] = df_dallas['year'].astype(str)

    # 대구 아파트 평균가
    df_daegu_price = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price_manwon,
               COUNT(*) AS transaction_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL AND deal_amount IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    if not df_daegu_price.empty:
        df_daegu_price['year'] = df_daegu_price['year'].astype(str)

    # 인구성장률 비교
    df_pop_compare = query_to_df("""
        SELECT city_name, population_2024, population_2023, population_growth_rate
        FROM city_comparison_population
        WHERE city_name IN ('Daegu', 'Dallas')
    """)

    # --- 스코어카드 생성 ---
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    insert_sql = """INSERT INTO city_axis_scorecard
        (comparison_axis, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value,
         metric_category, year_or_period, gap_ratio, insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 1. 주택가격 비교
    if not df_dallas_zhvi.empty and not df_daegu_price.empty:
        dallas_price_usd = float(df_dallas_zhvi.iloc[-1]['avg_zhvi'])
        daegu_price_manwon = float(df_daegu_price.iloc[-1]['avg_price_manwon'])
        daegu_price_usd = daegu_price_manwon * 10000 / 1350

        cursor.execute(insert_sql, (
            '종합', '대구 아파트 평균가(USD 환산)', round(daegu_price_usd, 2),
            'Dallas', 'Dallas ZHVI 평균', round(dallas_price_usd, 2),
            '주택가격', str(df_dallas_zhvi.iloc[-1]['year']),
            round(daegu_price_usd / dallas_price_usd, 4) if dallas_price_usd else None,
            f'대구 아파트 평균가는 Dallas ZHVI의 약 {daegu_price_usd/dallas_price_usd*100:.0f}% 수준',
            'Dallas의 주택 가격 경쟁력이 기업 유치와 인구 유입의 핵심 동력. '
            '대구도 수도권 대비 주택 가격 경쟁력을 적극 마케팅해야 함'))

    # 2. 인구 트렌드
    daegu_pop_row = df_pop_compare[df_pop_compare['city_name'] == 'Daegu'] if not df_pop_compare.empty else pd.DataFrame()
    dallas_pop_row = df_pop_compare[df_pop_compare['city_name'] == 'Dallas'] if not df_pop_compare.empty else pd.DataFrame()

    daegu_growth = float(daegu_pop_row.iloc[0]['population_growth_rate']) if not daegu_pop_row.empty else -0.42
    dallas_growth = float(dallas_pop_row.iloc[0]['population_growth_rate']) if not dallas_pop_row.empty else None

    cursor.execute(insert_sql, (
        '종합', '대구 인구성장률(%)', round(daegu_growth * 100, 2) if daegu_growth else None,
        'Dallas', 'Dallas 인구성장률(%)', round(dallas_growth * 100, 2) if dallas_growth else None,
        '인구', '2023-2024',
        None,
        '대구는 인구 유출 추세, Dallas는 지속적 인구 유입',
        'Dallas 모델: (1)법인세 없는 TX주 세제 혜택 (2)풍부한 토지+저렴한 주택 '
        '(3)대기업 본사 유치(Toyota, AT&T) -> 대구 적용: 혁신도시 확장 + 기업 인센티브 강화'))

    # 3. 시장온도 비교
    if not df_dallas.empty:
        latest_temp = float(df_dallas.iloc[-1]['market_temp'])
        cursor.execute(insert_sql, (
            '종합', '대구 시장활성도(프록시)', None,
            'Dallas', 'Dallas 시장온도지수', round(latest_temp, 2),
            '시장활성도', str(df_dallas.iloc[-1]['year']),
            None,
            f'Dallas 시장온도 {latest_temp:.1f} (50=중립, 50초과=판매자 우위)',
            'Dallas는 지속적 인구 유입으로 안정적 판매자 시장 유지'))

    conn.commit()
    conn.close()
    print("  [OK] 축 1 스코어카드 저장 완료")
    return df_daegu_pop, df_dallas, df_dallas_zhvi, df_daegu_price


def axis2_industry_daegu_vs_atlanta():
    """축 2: 산업 비교 - 대구 vs Atlanta"""
    print("\n" + "=" * 70)
    print("축 2: 산업 비교 — 대구 vs Atlanta")
    print("=" * 70)

    # Atlanta 부동산 수급
    df_atlanta = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(new_construction_sales) AS total_new_construction,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Atlanta, GA'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_atlanta.empty:
        df_atlanta['year'] = df_atlanta['year'].astype(str)

    # 한국 vs 미국 제조업 비중
    df_mfg = query_to_df("""
        SELECT country, year, manufacturing_pct, services_pct, industry_pct
        FROM economic_indicators
        WHERE country IN ('South Korea', 'United States')
          AND year >= 2000
        ORDER BY country, year
    """)
    if not df_mfg.empty:
        df_mfg['year'] = df_mfg['year'].astype(str)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    insert_sql = """INSERT INTO city_axis_scorecard
        (comparison_axis, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value,
         metric_category, year_or_period, gap_ratio, insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 1. 제조업 비중 비교
    if not df_mfg.empty:
        kr_data = df_mfg[df_mfg['country'] == 'South Korea']
        us_data = df_mfg[df_mfg['country'] == 'United States']
        if not kr_data.empty and not us_data.empty:
            kr_latest = kr_data.iloc[-1]
            us_latest = us_data.iloc[-1]
            kr_mfg = float(kr_latest['manufacturing_pct']) if kr_latest['manufacturing_pct'] else None
            us_mfg = float(us_latest['manufacturing_pct']) if us_latest['manufacturing_pct'] else None

            cursor.execute(insert_sql, (
                '산업', '한국 제조업 비중(%)', round(kr_mfg, 2) if kr_mfg else None,
                'Atlanta', '미국 제조업 비중(%)', round(us_mfg, 2) if us_mfg else None,
                '산업구조', str(int(kr_latest['year'])),
                round(kr_mfg / us_mfg, 4) if kr_mfg and us_mfg else None,
                '한국은 미국 대비 제조업 비중이 여전히 높음. 대구 제조업 의존도는 더 높을 가능성',
                'Atlanta 모델: (1)세계 최대 공항(하츠필드) 활용한 물류 허브 '
                '(2)자동차(현대, 기아) + 영화/미디어 산업 유치 '
                '(3)Georgia Tech 산학협력 -> 대구 적용: 대구공항 확장 + 자동차부품 고도화 + 대학 연계'))

    # 2. Atlanta 신규건설 트렌드
    if not df_atlanta.empty:
        latest = df_atlanta.iloc[-1]
        cursor.execute(insert_sql, (
            '산업', '대구 신규건설(프록시)', None,
            'Atlanta', 'Atlanta 연간 신규건설 판매', safe_val(latest.get('total_new_construction')),
            '신규건설', str(latest['year']),
            None,
            'Atlanta는 산업 다각화 성공으로 지속적 신규건설 수요 유지',
            '산업 허브화 -> 인구 유입 -> 주택 수요 증가 -> 신규건설 활성화의 선순환'))

    conn.commit()
    conn.close()
    print("  [OK] 축 2 스코어카드 저장 완료")
    return df_atlanta, df_mfg


def axis3_climate_daegu_vs_phoenix():
    """축 3: 기후 비교 - 대구 vs Phoenix"""
    print("\n" + "=" * 70)
    print("축 3: 기후 비교 — 대구 vs Phoenix")
    print("=" * 70)

    # Phoenix 부동산
    df_phoenix = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               AVG(inventory_count) AS avg_inventory,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Phoenix, AZ'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_phoenix.empty:
        df_phoenix['year'] = df_phoenix['year'].astype(str)

    # Phoenix ZHVI
    df_phoenix_zhvi = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = 'Phoenix, AZ'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_phoenix_zhvi.empty:
        df_phoenix_zhvi['year'] = df_phoenix_zhvi['year'].astype(str)

    # 기온 데이터 로드 (메모리 분석)
    temp_path = S4_DATA_FILES.get('CITY_TEMP')
    df_temp_summary = pd.DataFrame()
    if temp_path and os.path.exists(temp_path):
        print("  기온 데이터 로드 중...")
        # 청크로 읽어서 대구/Phoenix만 필터
        temp_data = []
        for chunk in pd.read_csv(temp_path, chunksize=500000, low_memory=False):
            chunk.columns = chunk.columns.str.strip()
            mask = chunk['City'].astype(str).str.contains('Phoenix|Dallas|Atlanta|Charlotte', case=False, na=False)
            if mask.any():
                temp_data.append(chunk[mask])
        if temp_data:
            df_temp = pd.concat(temp_data, ignore_index=True)
            # 여름 (6-8월) 평균 기온 비교
            df_summer = df_temp[df_temp['Month'].isin([6, 7, 8])]
            df_temp_summary = df_summer.groupby('City').agg(
                avg_summer_temp=('AvgTemperature', 'mean'),
                max_temp=('AvgTemperature', 'max')
            ).reset_index()
            print(f"  기온 요약:\n{df_temp_summary.to_string(index=False)}")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    insert_sql = """INSERT INTO city_axis_scorecard
        (comparison_axis, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value,
         metric_category, year_or_period, gap_ratio, insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 1. 기온 비교
    phoenix_temp = None
    if not df_temp_summary.empty:
        phoenix_row = df_temp_summary[df_temp_summary['City'].str.contains('Phoenix', case=False)]
        if not phoenix_row.empty:
            phoenix_temp = float(phoenix_row.iloc[0]['avg_summer_temp'])

    # 대구 여름 평균기온 (참고값: 약 26-28도C = ~80F)
    daegu_summer_f = 80.0
    cursor.execute(insert_sql, (
        '기후', '대구 여름 평균기온(F)', daegu_summer_f,
        'Phoenix', 'Phoenix 여름 평균기온(F)', round(phoenix_temp, 1) if phoenix_temp else 95.0,
        '기후',
        '연평균 6-8월',
        None,
        '대구와 Phoenix 모두 분지 지형으로 여름 폭염이 극심. '
        'Phoenix는 연평균 40도C 이상 폭염에도 매년 인구 유입',
        'Phoenix 모델: (1)캘리포니아 대비 1/3 수준 주택 가격 (2)낮은 소득세(AZ) '
        '(3)반도체(TSMC, Intel) 대규모 공장 유치 (4)에어컨 인프라+실내 생활 문화 '
        '-> 대구 적용: 수도권 대비 주택 가격 경쟁력 강조 + 첨단산업단지 유치 + 도시 냉방 인프라'))

    # 2. 주택가격 경쟁력
    if not df_phoenix_zhvi.empty:
        latest_phoenix = float(df_phoenix_zhvi.iloc[-1]['avg_zhvi'])
        cursor.execute(insert_sql, (
            '기후', '대구 아파트 평균가(USD)', None,
            'Phoenix', 'Phoenix ZHVI', round(latest_phoenix, 2),
            '주택가격', str(df_phoenix_zhvi.iloc[-1]['year']),
            None,
            'Phoenix는 LA/SF 대비 저렴한 주택이 인구 유입의 핵심',
            '대구도 서울 대비 주택 가격 경쟁력(약 1/3~1/4 수준)을 적극 활용해야 함'))

    conn.commit()
    conn.close()
    print("  [OK] 축 3 스코어카드 저장 완료")
    return df_phoenix, df_phoenix_zhvi, df_temp_summary


def axis4_transformation_daegu_vs_charlotte():
    """축 4: 변모 비교 - 대구 vs Charlotte"""
    print("\n" + "=" * 70)
    print("축 4: 변모 비교 — 대구 vs Charlotte")
    print("=" * 70)

    # Charlotte 전환기 부동산
    df_charlotte = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year,
               AVG(market_temp_index) AS market_temp,
               AVG(income_needed) AS income_needed,
               SUM(new_construction_sales) AS total_new_construction,
               SUM(sales_count) AS total_sales
        FROM us_metro_demand
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_charlotte.empty:
        df_charlotte['year'] = df_charlotte['year'].astype(str)

    # Charlotte ZHVI
    df_charlotte_zhvi = query_to_df("""
        SELECT LEFT(`year_month`, 4) AS year, AVG(zhvi) AS avg_zhvi
        FROM us_metro_zhvi
        WHERE region_name = 'Charlotte, NC'
        GROUP BY LEFT(`year_month`, 4)
        ORDER BY year
    """)
    if not df_charlotte_zhvi.empty:
        df_charlotte_zhvi['year'] = df_charlotte_zhvi['year'].astype(str)

    # 대구 아파트
    df_daegu_price = query_to_df("""
        SELECT year, AVG(deal_amount) AS avg_price_manwon,
               COUNT(*) AS transaction_count
        FROM daegu_housing_prices
        WHERE year IS NOT NULL AND deal_amount IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    if not df_daegu_price.empty:
        df_daegu_price['year'] = df_daegu_price['year'].astype(str)

    # 대구 인구
    df_daegu_pop = query_to_df("""
        SELECT year, AVG(natural_growth_rate) AS avg_growth_rate
        FROM korean_demographics
        WHERE region = '대구'
        GROUP BY year ORDER BY year
    """)
    if not df_daegu_pop.empty:
        df_daegu_pop['year'] = df_daegu_pop['year'].astype(str)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    insert_sql = """INSERT INTO city_axis_scorecard
        (comparison_axis, daegu_metric_name, daegu_value,
         us_city_name, us_metric_name, us_value,
         metric_category, year_or_period, gap_ratio, insight, strategy_implication)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 1. 전환 타임라인 비교
    cursor.execute(insert_sql, (
        '변모', '대구 산업전환 단계', None,
        'Charlotte', 'Charlotte 산업전환 단계', None,
        '산업전환', '1980~2025',
        None,
        'Charlotte: 1980년대 섬유 쇠퇴 -> 1990년대 Bank of America 본사 유치 '
        '-> 2000년대 에너지(Duke Energy)+금융 확립 -> 2010년대 Tech 허브 확장. '
        '약 30년에 걸친 단계적 전환. '
        '대구: 1990년대 섬유 쇠퇴 -> 2000년대 자동차부품 성장 -> 2010년대 첨단산업단지 조성 -> 현재 진행 중',
        'Charlotte 성공의 3대 요인: '
        '(1)금융업 본사 유치로 고소득 일자리 창출 -> 대구: 대기업 지역본사 유치 전략 '
        '(2)대학(UNC Charlotte) 중심 인재 공급 -> 대구: 경북대+DGIST 산학 협력 강화 '
        '(3)공항 허브화(CLT)로 접근성 확보 -> 대구: KTX+공항 연계 광역 교통망 구축. '
        '핵심 교훈: 산업 전환은 20~30년 장기 프로젝트이며, "앵커 기업" 유치가 결정적'))

    # 2. Charlotte ZHVI 누적변화
    if not df_charlotte_zhvi.empty and len(df_charlotte_zhvi) >= 2:
        first = float(df_charlotte_zhvi.iloc[0]['avg_zhvi'])
        last = float(df_charlotte_zhvi.iloc[-1]['avg_zhvi'])
        change = (last - first) / first * 100 if first else 0

        cursor.execute(insert_sql, (
            '변모', '대구 전환기 아파트 가격변화율(%)', None,
            'Charlotte', 'Charlotte ZHVI 누적변화율(%)', round(change, 2),
            '주택가격변화',
            f"{df_charlotte_zhvi.iloc[0]['year']}~{df_charlotte_zhvi.iloc[-1]['year']}",
            None,
            f'Charlotte 주택가치 {df_charlotte_zhvi.iloc[0]["year"]}->{df_charlotte_zhvi.iloc[-1]["year"]}: '
            f'+{change:.1f}% 상승. 산업 전환 성공이 부동산 가치 상승으로 이어짐',
            '산업 전환 성공 -> 고소득 일자리 유입 -> 주택 수요 증가 -> 가격 상승의 선순환. '
            '대구가 산업 전환에 성공하면 유사한 부동산 상승 기대 가능'))

    # 3. 대구 아파트 가격 변화
    if not df_daegu_price.empty and len(df_daegu_price) >= 2:
        first_d = float(df_daegu_price.iloc[0]['avg_price_manwon'])
        last_d = float(df_daegu_price.iloc[-1]['avg_price_manwon'])
        change_d = (last_d - first_d) / first_d * 100 if first_d else 0

        cursor.execute(insert_sql, (
            '변모', '대구 아파트 평균가 변화율(%)', round(change_d, 2),
            'Charlotte', 'Charlotte ZHVI 변화율(%) 참고', None,
            '대구주택변화',
            f"{int(df_daegu_price.iloc[0]['year'])}~{int(df_daegu_price.iloc[-1]['year'])}",
            None,
            f'대구 아파트 {int(df_daegu_price.iloc[0]["year"])}->{int(df_daegu_price.iloc[-1]["year"])}: '
            f'+{change_d:.1f}% 변화',
            '대구의 산업 전환 진행 상황을 주택 가격 변화로 추적 가능'))

    conn.commit()
    conn.close()
    print("  [OK] 축 4 스코어카드 저장 완료")
    return df_charlotte, df_charlotte_zhvi, df_daegu_price, df_daegu_pop


def run():
    print("=" * 60)
    print("STEP 8: 4축 비교 분석")
    print("=" * 60)

    r1 = axis1_comprehensive_daegu_vs_dallas()
    r2 = axis2_industry_daegu_vs_atlanta()
    r3 = axis3_climate_daegu_vs_phoenix()
    r4 = axis4_transformation_daegu_vs_charlotte()

    print("\n  STEP 8 완료! city_axis_scorecard에 결과 저장됨")


if __name__ == '__main__':
    run()
