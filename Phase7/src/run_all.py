# -*- coding: utf-8 -*-
"""
MBTI & 혈액형: 과학인가 미신인가 — 데이터로 검증하는 성격 유형론
================================================================
KNU 12기 Phase7 Numpy 미니프로젝트
전체 분석 실행 스크립트

사용법:
    cd mini/src
    python run_all.py           # 전체 실행
    python run_all.py --team ac # 특정 팀만 실행
"""

import sys
import os
import time
import argparse

# src 디렉토리를 기준으로 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.config import FIGURES_DIR
from common.plot_style import set_project_style


def ensure_directories():
    """결과 저장 디렉토리 생성"""
    for team in ['team_a', 'team_b', 'team_c', 'team_d', 'team_e']:
        path = FIGURES_DIR / team
        os.makedirs(path, exist_ok=True)
    print("[준비] 결과 저장 디렉토리 확인 완료\n")


def run_team_ac():
    """팀 A+C 통합 실행: 혈액형→MBTI 전환 — 성격 유형론 데이터 검증

    Part A: MBTI × 인구통계 (Kaggle 43,744명)
    Part A-S: MBTI × 인구통계 설문 교차검증
    Part C: 한국 혈액형 성격론 검증
    Part C-S: 혈액형→MBTI 전환 설문 교차검증
    """
    # ── Part A: MBTI × 인구통계 (Kaggle) ──
    print("\n" + "─" * 50)
    print("  [A+C 통합] Part A: MBTI × 인구통계 (Kaggle 43,744명)")
    print("─" * 50)
    from team_a_demographics import main as a_main
    a_main()

    # ── Part A 설문 교차검증 ──
    try:
        from team_a_survey import main as a_survey_main
        a_survey_main()
    except FileNotFoundError:
        print("  ⚠️ 밈 설문 CSV 미발견 → A 설문 교차검증 생략")
    except Exception as e:
        print(f"  ⚠️ A 설문 교차검증 오류: {e}")

    # ── Part C: 한국 혈액형 성격론 검증 ──
    print("\n" + "─" * 50)
    print("  [A+C 통합] Part C: 한국 혈액형 성격론 검증")
    print("─" * 50)
    from team_c_korea_blood import main as c_main
    c_main()

    # ── Part C 설문 교차검증 ──
    try:
        from team_c_survey import main as c_survey_main
        c_survey_main()
    except FileNotFoundError:
        print("  ⚠️ 밈 설문 CSV 미발견 → C 설문 교차검증 생략")
    except Exception as e:
        print(f"  ⚠️ C 설문 교차검증 오류: {e}")


def run_team_b():
    """팀원 B 실행 (본 분석 + 설문 교차검증)"""
    from team_b_interest import main
    main()
    # 설문 교차검증 (CSV 존재 시에만)
    try:
        from team_b_survey import main as survey_main
        survey_main()
    except FileNotFoundError:
        print("  ⚠️ 밈 설문 CSV 미발견 → 설문 교차검증 생략")
    except Exception as e:
        print(f"  ⚠️ 설문 교차검증 오류: {e}")


def run_team_d():
    """팀원 D 실행"""
    from team_d_survey_compare import main
    main()


def run_team_e():
    """팀원 E 실행: 설문 문항 최적화 — 질문 축소로 정확도 향상 검증"""
    from team_e_item_optimization import main
    main()


def print_final_summary():
    """전체 실행 요약"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█  MBTI & 혈액형: 과학인가 미신인가                    █")
    print("█  — 데이터로 검증하는 성격 유형론                      █")
    print("█" + " " * 58 + "█")
    print("█" * 60)

    print("\n[전체 분석 결과 요약]")
    print("─" * 50)
    print("팀 A+C (통합): 혈액형→MBTI 전환 — 성격 유형론 검증")
    print("  → MBTI × 인구통계 + 혈액형 성격론 + 설문 교차검증")
    print("")
    print("팀원 B: MBTI 점수 × 관심사")
    print("  → 차원 점수 상관관계 및 관심사별 차이 분석")
    print("")
    print("팀원 D: 설문 비교분석 & MBTI 예측")
    print("  → 자체 설문 데이터 × 기존 데이터 비교, MBTI 예측 검증")
    print("")
    print("팀원 E: 설문 문항 최적화")
    print("  → 문항 분석으로 질문 축소 & 정확도 향상 가능성 검증")
    print("─" * 50)

    # 생성된 그래프 수 확인
    total_figs = 0

    # 팀 A+C 통합
    ac_figs = 0
    for team in ['team_a', 'team_c']:
        team_dir = FIGURES_DIR / team
        if team_dir.exists():
            figs = list(team_dir.glob('*.png'))
            ac_figs += len(figs)
    print(f"  팀 A+C (통합): {ac_figs}개 그래프 생성")
    total_figs += ac_figs

    # 팀 B, D, E
    for team in ['team_b', 'team_d', 'team_e']:
        team_dir = FIGURES_DIR / team
        if team_dir.exists():
            figs = list(team_dir.glob('*.png'))
            total_figs += len(figs)
            print(f"  {team}: {len(figs)}개 그래프 생성")

    print(f"\n  총 {total_figs}개 그래프 → results/figures/ 에 저장")
    print("\n✅ 전체 분석 완료!")


def main():
    parser = argparse.ArgumentParser(description='MBTI & 혈액형 미니프로젝트 분석 실행')
    parser.add_argument('--team', type=str, default='all',
                       choices=['all', 'ac', 'b', 'd', 'e'],
                       help='실행할 팀 선택 (기본: all)')
    args = parser.parse_args()

    print("╔" + "═" * 58 + "╗")
    print("║  MBTI & 혈액형: 과학인가 미신인가                    ║")
    print("║  — 데이터로 검증하는 성격 유형론                      ║")
    print("║  KNU 12기 Phase7 Numpy 미니프로젝트                  ║")
    print("╚" + "═" * 58 + "╝")

    # 환경 설정
    set_project_style()
    ensure_directories()

    start_time = time.time()

    teams = {
        'ac': ('팀 A+C: 혈액형→MBTI 통합 검증', run_team_ac),
        'b': ('팀원 B: MBTI 점수 × 관심사', run_team_b),
        'd': ('팀원 D: 설문 비교분석 & MBTI 예측', run_team_d),
        'e': ('팀원 E: 설문 문항 최적화 & 정확도 향상', run_team_e),
    }

    if args.team == 'all':
        for key, (name, func) in teams.items():
            team_start = time.time()
            try:
                func()
                elapsed = time.time() - team_start
                print(f"  ⏱️ {name} 소요시간: {elapsed:.1f}초")
            except Exception as e:
                print(f"\n  ❌ {name} 실행 오류: {e}")
                import traceback
                traceback.print_exc()
    else:
        key = args.team
        name, func = teams[key]
        try:
            func()
        except Exception as e:
            print(f"\n  ❌ {name} 실행 오류: {e}")
            import traceback
            traceback.print_exc()

    total_time = time.time() - start_time
    print(f"\n  ⏱️ 전체 소요시간: {total_time:.1f}초")

    if args.team == 'all':
        print_final_summary()


if __name__ == '__main__':
    main()
