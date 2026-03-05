"""
소주제 4 전체 파이프라인 실행 (v2)
순서: 테이블 생성 → 데이터 로딩 → 분석 → 시각화
"""

import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    ('Step 1: 테이블 생성', 'step1_create_tables'),
    ('Step 2: Zillow 수급 데이터', 'step2_load_zillow_demand'),
    ('Step 3: Zillow State 시계열', 'step3_load_zillow_timeseries'),
    ('Step 4: BLS 고용 데이터', 'step4_load_bls_employment'),
    ('Step 5: 글로벌 경제지표', 'step5_load_global_economy'),
    ('Step 6: 한국 프록시 데이터', 'step6_load_korean_proxy'),
    ('Step 6b: v2 추가 데이터', 'step6b_load_v2_data'),
    ('Step 7: 기존 산업전환 분석', 'step7_analysis_core'),
    ('Step 8: 4축 비교 분석', 'step8_analysis_4axis'),
    ('Step 9: 대구 발전전략 보고서', 'step9_daegu_strategy'),
    ('Step 10: 기존 시각화 (V1~V5)', 'step10_visualization_core'),
    ('Step 11: 4축 비교 시각화 (V6~V10)', 'step11_visualization_4axis'),
]


def main():
    print("=" * 70)
    print("  소주제 4: 산업 전환과 부동산 - 전체 파이프라인 (v2)")
    print("=" * 70)

    errors = []
    timings = []

    for step_name, module_name in STEPS:
        print(f"\n{'='*60}")
        print(f"  >>> {step_name}")
        print(f"{'='*60}")

        start = time.time()
        try:
            mod = __import__(module_name)
            if hasattr(mod, 'run'):
                mod.run()
            elif hasattr(mod, 'create_subtopic4_tables'):
                mod.create_subtopic4_tables()
                mod.truncate_s4_tables()
            elapsed = time.time() - start
            timings.append((step_name, elapsed))
            print(f"  >>> {step_name} 완료 ({elapsed:.1f}초)")
        except Exception as e:
            elapsed = time.time() - start
            timings.append((step_name, elapsed))
            errors.append((step_name, str(e)))
            print(f"  >>> [ERROR] {step_name}: {e}")
            traceback.print_exc()

    # 실행 요약
    print("\n" + "=" * 70)
    print("  실행 요약")
    print("=" * 70)
    total_time = sum(t for _, t in timings)
    for name, t in timings:
        status = "ERROR" if any(name == en for en, _ in errors) else "OK"
        print(f"  [{status:5s}] {name:40s} {t:8.1f}초")
    print(f"\n  총 소요시간: {total_time:.1f}초")

    if errors:
        print(f"\n  [WARN] {len(errors)}개 스텝에서 오류 발생:")
        for name, err in errors:
            print(f"    - {name}: {err}")
    else:
        print("\n  모든 스텝 성공!")

    # output 디렉토리 확인
    from step0_setup import OUTPUT_DIR
    print(f"\n  출력 디렉토리: {OUTPUT_DIR}")
    if os.path.exists(OUTPUT_DIR):
        files = os.listdir(OUTPUT_DIR)
        print(f"  생성된 파일 ({len(files)}개):")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"    {f:50s} {size/1024:8.1f} KB")


if __name__ == '__main__':
    main()
