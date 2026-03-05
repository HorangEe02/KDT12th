"""
소주제 1: 주택 가격 추이 비교 - 전체 파이프라인 실행
실행: python src/subtopic1/run_all.py

실행 순서:
  STEP 0: DB 생성
  STEP 1: 테이블 생성 + 도시 마스터 삽입
  STEP 2: Zillow Housing Wide -> Long (ZHVI, ZORI, 예측)
  STEP 3: Zillow Economics (Crosswalk + State/Metro/City 시계열)
  STEP 4: Realtor.com 매물 + 월별 요약
  STEP 5: 대구 실거래가 + 월별 요약
  STEP 6: 분석 쿼리 실행 -> CSV
  STEP 7: 시각화 -> PNG
"""
import sys
import os
import time

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_step(step_name, func):
    print(f"\n{'#'*70}")
    print(f"# {step_name}")
    print(f"{'#'*70}")
    start = time.time()
    try:
        func()
        elapsed = time.time() - start
        print(f"\n  -> {step_name} 완료 ({elapsed:.1f}초)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n  -> {step_name} 실패 ({elapsed:.1f}초): {e}")
        import traceback
        traceback.print_exc()


def main():
    total_start = time.time()

    # ── STEP 0 ──
    from step0_init_db import create_database
    run_step("STEP 0: DB 생성", create_database)

    # ── STEP 1 ──
    from step1_create_tables import create_all_tables, insert_cities
    def step1():
        create_all_tables()
        insert_cities()
    run_step("STEP 1: 테이블 생성 + 도시 마스터", step1)

    # ── STEP 2 ──
    from step2_load_us_zillow_wide import load_zhvi, load_zori, load_zhvf_growth, load_zorf_growth
    def step2():
        load_zhvi()
        load_zori()
        load_zhvf_growth()
        load_zorf_growth()
    run_step("STEP 2: Zillow Housing Wide -> Long", step2)

    # ── STEP 3 ──
    from step3_load_us_zillow_economics import (
        load_crosswalk_county, load_crosswalk_cities,
        load_state_timeseries, load_metro_timeseries, load_city_timeseries
    )
    def step3():
        load_crosswalk_county()
        load_crosswalk_cities()
        load_state_timeseries()
        load_metro_timeseries()
        load_city_timeseries()
    run_step("STEP 3: Zillow Economics 시계열", step3)

    # ── STEP 4 ──
    from step4_load_us_realtor import load_realtor_listings, build_us_monthly_summary
    def step4():
        load_realtor_listings()
        build_us_monthly_summary()
    run_step("STEP 4: Realtor.com 매물 적재", step4)

    # ── STEP 5 ──
    from step5_load_kr_daegu import load_daegu_apt, load_apart_deal_daegu, build_daegu_monthly_summary
    def step5():
        load_daegu_apt()
        load_apart_deal_daegu()
        build_daegu_monthly_summary()
    run_step("STEP 5: 대구 데이터 적재", step5)

    # ── STEP 6 ──
    def step6():
        import step6_analysis_queries
        # step6의 __main__ 블록 로직을 직접 실행
        queries = {
            'Q1_ZHVI_TREND': step6_analysis_queries.Q1_ZHVI_TREND,
            'Q2_ZHVI_YOY': step6_analysis_queries.Q2_ZHVI_YOY,
            'Q3_ZORI_TREND': step6_analysis_queries.Q3_ZORI_TREND,
            'Q4_PRICE_TO_RENT': step6_analysis_queries.Q4_PRICE_TO_RENT,
            'Q5_DAEGU_DISTRICT': step6_analysis_queries.Q5_DAEGU_DISTRICT,
            'Q6_CROSS_COMPARISON': step6_analysis_queries.Q6_CROSS_COMPARISON,
            'Q7_COVID_IMPACT': step6_analysis_queries.Q7_COVID_IMPACT,
            'Q8_PRICE_REDUCTION': step6_analysis_queries.Q8_PRICE_REDUCTION,
            'Q9_REALTOR_STATS': step6_analysis_queries.Q9_REALTOR_STATS,
            'Q10_FORECAST': step6_analysis_queries.Q10_FORECAST,
        }
        from step0_init_db import OUTPUT_DIR
        for name, sql in queries.items():
            try:
                df = step6_analysis_queries.query_to_df(sql)
                csv_path = os.path.join(OUTPUT_DIR, f'{name}.csv')
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"  [OK] {name}: {len(df)}행 -> {csv_path}")
            except Exception as e:
                print(f"  [ERROR] {name}: {e}")
    run_step("STEP 6: 분석 쿼리 -> CSV", step6)

    # ── STEP 7 ──
    from step7_visualization import viz1_zhvi_trend, viz2_zhvi_yoy, viz3_zori_trend, viz4_daegu_district, viz5_covid_bar
    def step7():
        viz1_zhvi_trend()
        viz2_zhvi_yoy()
        viz3_zori_trend()
        viz4_daegu_district()
        viz5_covid_bar()
    run_step("STEP 7: 시각화 -> PNG", step7)

    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"[ALL DONE] 소주제1 전체 파이프라인 완료 (총 {total_elapsed:.1f}초)")
    print(f"  결과물: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
