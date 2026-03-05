"""
소주제 2: 인구 이동과 주택 수요 — 전체 파이프라인 실행
실행: python src/subtopic2/s2_run_all.py

실행 순서:
  STEP 1: 테이블 생성 (11개)
  STEP 2: Zillow Housing 수급 지표 (5개 Wide → Long)
  STEP 3: Zillow Economics 수급 시계열
  STEP 4: 한국 인구통계 (K2-1 Demographics + K2-2 Income)
  STEP 5: 미국 인구통계 (Census + County Historical + Pop Timeseries)
  STEP 6: 글로벌 인구 데이터
  STEP 7: 상관분석 통합 데이터 구축
  STEP 8: 분석 쿼리 → CSV (10개)
  STEP 9: 시각화 → PNG (6개)
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
    from s2_step1_create_tables import create_all_tables
    run_step("STEP 1: 소주제2 테이블 생성", create_all_tables)

    # STEP 2: Zillow Housing 수급 지표
    from s2_step2_load_zillow_demand import load_all_demand_metrics
    run_step("STEP 2: Zillow Housing 수급 지표", load_all_demand_metrics)

    # STEP 3: Zillow Economics 수급 시계열
    from s2_step3_load_zillow_economics_demand import load_all
    run_step("STEP 3: Zillow Economics 수급 시계열", load_all)

    # STEP 4: 한국 인구통계
    from s2_step4_load_kr_demographics import (
        load_korean_demographics, load_korean_income_welfare, build_daegu_summary
    )
    def step4():
        load_korean_demographics()
        load_korean_income_welfare()
        build_daegu_summary()
    run_step("STEP 4: 한국 인구통계 적재", step4)

    # STEP 5: 미국 인구통계
    from s2_step5_load_us_demographics import (
        load_us_census, load_us_county_historical, load_us_population_timeseries
    )
    def step5():
        load_us_census()
        load_us_county_historical()
        load_us_population_timeseries()
    run_step("STEP 5: 미국 인구통계 적재", step5)

    # STEP 6: 글로벌 인구 데이터
    from s2_step6_load_global_population import load_world_population_growth
    run_step("STEP 6: 글로벌 인구 데이터 적재", load_world_population_growth)

    # STEP 7: 상관분석 통합 데이터 구축
    def step7():
        from s2_step7_build_correlation import (
            build_us_annual_merged, build_kr_annual_merged,
            save_merged_to_db, compute_correlations
        )
        import pandas as pd_local
        df_us = build_us_annual_merged()
        df_kr = build_kr_annual_merged()
        dfs = [d for d in [df_us, df_kr] if not d.empty]
        if dfs:
            df_all = pd_local.concat(dfs, ignore_index=True)
            save_merged_to_db(df_all)
            compute_correlations(df_all)
        else:
            print("[WARN] 통합 데이터 없음")
    run_step("STEP 7: 상관분석 통합 데이터", step7)

    # STEP 8: 분석 쿼리 → CSV
    from s2_step8_analysis_queries import run_all_queries
    run_step("STEP 8: 분석 쿼리 -> CSV", run_all_queries)

    # STEP 9: 시각화 → PNG
    def step9():
        from s2_step9_visualization import (
            viz1_market_temp_dashboard, viz2_supply_demand_ratio,
            viz3_daegu_population, viz4_pop_vs_zhvi_scatter,
            viz5_income_needed, viz6_correlation_heatmap,
        )
        viz1_market_temp_dashboard()
        viz2_supply_demand_ratio()
        viz3_daegu_population()
        viz4_pop_vs_zhvi_scatter()
        viz5_income_needed()
        viz6_correlation_heatmap()
    run_step("STEP 9: 시각화 -> PNG", step9)

    total_elapsed = time.time() - total_start
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    print(f"\n{'='*70}")
    print(f"[ALL DONE] 소주제2 전체 파이프라인 완료 (총 {total_elapsed:.1f}초)")
    print(f"  결과물: {output_dir}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
