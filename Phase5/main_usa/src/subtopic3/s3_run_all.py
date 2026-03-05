"""
소주제 3: 기후·입지와 지역별 가격 격차 — 전체 파이프라인 실행
실행: python src/subtopic3/s3_run_all.py

실행 순서:
  STEP 1: 테이블 생성 (9개)
  STEP 2: Berkeley Earth 월평균 기온 (1750~2013)
  STEP 3: Daily + Monthly 기온 (city_temperature + US_City_Temp_Data)
  STEP 4: 미국 기상 이벤트 (폭염·혹한)
  STEP 5: ZIP Code별 가격 (Zip_time_series + Realtor 집계)
  STEP 6: 대구 구별 가격 요약
  STEP 7: 기후-가격 교차분석 + 상관분석
  STEP 8: 분석 쿼리 → CSV (10개)
  STEP 9: 시각화 → PNG (7개)
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

    # STEP 1: 테이블 생성
    from s3_step1_create_tables import create_all_tables
    run_step("STEP 1: 소주제3 테이블 생성 (9개)", create_all_tables)

    # STEP 2: Berkeley Earth 월평균 기온
    from s3_step2_load_climate_berkeley import load_berkeley_earth
    run_step("STEP 2: Berkeley Earth 기온 적재", load_berkeley_earth)

    # STEP 3: Daily + Monthly 기온
    from s3_step3_load_climate_daily import load_daily_temperature, load_monthly_mean_temp
    def step3():
        load_daily_temperature()
        load_monthly_mean_temp()
    run_step("STEP 3: 일별/월별 기온 적재", step3)

    # STEP 4: 미국 기상 이벤트
    from s3_step4_load_us_weather_events import load_weather_events
    run_step("STEP 4: 미국 기상 이벤트 (폭염/혹한)", load_weather_events)

    # STEP 5: ZIP Code별 가격
    from s3_step5_load_zip_prices import load_zip_timeseries, build_zip_realtor_summary
    def step5():
        load_zip_timeseries()
        build_zip_realtor_summary()
    run_step("STEP 5: ZIP Code별 가격 적재", step5)

    # STEP 6: 대구 구별 가격
    from s3_step6_build_daegu_district_prices import build_daegu_district_prices
    run_step("STEP 6: 대구 구별 가격 요약", build_daegu_district_prices)

    # STEP 7: 기후-가격 교차분석
    def step7():
        from s3_step7_build_climate_price_merged import (
            build_city_climate_profiles, build_us_zip_price_tiers,
            build_daegu_district_climate, compute_climate_price_correlations,
        )
        build_city_climate_profiles()
        build_us_zip_price_tiers()
        build_daegu_district_climate()
        compute_climate_price_correlations()
    run_step("STEP 7: 기후-가격 교차분석 + 상관분석", step7)

    # STEP 8: 분석 쿼리 → CSV
    from s3_step8_analysis_queries import run_all_queries
    run_step("STEP 8: 분석 쿼리 -> CSV", run_all_queries)

    # STEP 9: 시각화 → PNG
    def step9():
        from s3_step9_visualization import (
            viz1_monthly_temp_radar, viz2_warming_trend,
            viz3_climate_profile_bar, viz4_zip_price_boxplot,
            viz5_daegu_district_bar, viz6_heat_price_heatmap,
            viz7_phoenix_heat_analysis,
        )
        viz1_monthly_temp_radar()
        viz2_warming_trend()
        viz3_climate_profile_bar()
        viz4_zip_price_boxplot()
        viz5_daegu_district_bar()
        viz6_heat_price_heatmap()
        viz7_phoenix_heat_analysis()
    run_step("STEP 9: 시각화 -> PNG", step9)

    total_elapsed = time.time() - total_start
    print(f"\n{'='*70}")
    print(f"[ALL DONE] 소주제3 전체 파이프라인 완료 (총 {total_elapsed:.1f}초)")
    print(f"  결과물: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
