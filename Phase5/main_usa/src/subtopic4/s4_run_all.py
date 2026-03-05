"""
소주제4 전체 파이프라인 오케스트레이터
실행: python src/subtopic4/s4_run_all.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    ('s4_step1_create_tables', 'STEP 1: 테이블 생성'),
    ('s4_step2_load_zillow_demand', 'STEP 2: Zillow 수급지표 로딩'),
    ('s4_step3_load_zillow_timeseries', 'STEP 3: Zillow State 시계열 로딩'),
    ('s4_step4_load_bls_employment', 'STEP 4: BLS 고용 데이터 로딩'),
    ('s4_step5_load_global_economy', 'STEP 5: 글로벌 경제지표 로딩'),
    ('s4_step6_load_korean_proxy', 'STEP 6: 한국(대구) 프록시 데이터'),
    ('s4_step7_analysis_queries', 'STEP 7: 분석 쿼리'),
    ('s4_step8_visualization', 'STEP 8: 시각화'),
]

def main():
    print("=" * 60)
    print("  소주제4: 산업 전환과 부동산")
    print("  전체 파이프라인 실행")
    print("=" * 60)

    t0 = time.time()
    errors = []

    for module_name, desc in STEPS:
        print(f"\n{'─' * 60}")
        print(f"  {desc}")
        print(f"{'─' * 60}")
        t1 = time.time()
        try:
            mod = __import__(module_name)
            # 각 모듈의 main 함수 또는 __main__ 블록 호출
            if hasattr(mod, 'run'):
                mod.run()
            elif hasattr(mod, 'create_tables'):
                mod.create_tables()
            elif hasattr(mod, 'load_state_timeseries'):
                mod.load_state_timeseries()
            elif module_name == 's4_step4_load_bls_employment':
                series_map = mod.build_target_series()
                mod.load_bls_data(series_map)
            elif module_name == 's4_step5_load_global_economy':
                mod.load_global_economy()
            elif module_name == 's4_step6_load_korean_proxy':
                mod.load_korean_demographics()
                mod.load_korea_income_summary()
            elif module_name == 's4_step7_analysis_queries':
                mod.analysis_q1()
                mod.analysis_q2()
                mod.analysis_q3()
                mod.analysis_q4()
                mod.save_impact_analysis()
            elif module_name == 's4_step8_visualization':
                mod.viz_v1()
                mod.viz_v2()
                mod.viz_v3()
                mod.viz_v4()
                mod.viz_v5()
            dt = time.time() - t1
            print(f"  [{desc}] 완료 ({dt:.1f}초)")
        except Exception as e:
            dt = time.time() - t1
            errors.append((desc, str(e)))
            print(f"  [ERROR] {desc}: {e} ({dt:.1f}초)")
            import traceback
            traceback.print_exc()

    total_time = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  전체 파이프라인 완료: {total_time:.1f}초")
    print(f"  에러: {len(errors)}건")
    if errors:
        for desc, err in errors:
            print(f"    - {desc}: {err}")
    print(f"{'=' * 60}")

    # 산출물 확인
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    if os.path.exists(output_dir):
        files = sorted(os.listdir(output_dir))
        print(f"\n  output/ 파일 ({len(files)}개):")
        for f in files:
            size = os.path.getsize(os.path.join(output_dir, f))
            print(f"    {f} ({size:,} bytes)")


if __name__ == '__main__':
    main()
