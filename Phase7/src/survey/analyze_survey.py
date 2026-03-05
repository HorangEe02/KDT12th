# -*- coding: utf-8 -*-
"""
자체 설문 응답 분석 스크립트
============================
Google Forms 응답 CSV를 다운로드하여 분석

사용법:
    1. Google Sheets에서 응답 데이터를 CSV로 다운로드
    2. mini/data/raw/survey_responses.csv 로 저장
    3. python src/survey/analyze_survey.py 실행

설문 구조:
    - Q1-Q6:   기본 정보 (성별, 나이대, 교육수준, 혈액형, MBTI, 검사경험)
    - Q7-Q14:  E/I 차원 (7점 리커트, 8문항)
    - Q15-Q22: S/N 차원 (7점 리커트, 8문항)
    - Q23-Q30: T/F 차원 (7점 리커트, 8문항)
    - Q31-Q38: J/P 차원 (7점 리커트, 8문항)
    - Q39-Q48: 혈액형 성격론 인식 (10문항)
    - Q49-Q52: 관심사 & 라이프스타일 (4문항)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common.config import FIGURES_DIR, BLOOD_COLORS, MBTI_COLORS
from common.stats_utils import (
    descriptive_stats, chi_square_test, independent_t_test,
    one_way_anova, pearson_correlation, print_test_result
)
from common.plot_style import (
    set_project_style, save_figure, add_result_text,
    format_p_value, annotate_bars
)
from survey.mbti_scoring import (
    compute_from_csv_row, batch_compute_from_array,
    print_scoring_guide, print_individual_result,
    SCORING_MAP, MIDPOINT, MBTI_TYPE_CONDITIONS
)

TEAM = 'survey'
SURVEY_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'data', 'raw', 'survey_responses.csv'
)

# ============================================================
#  리커트 점수 → MBTI 차원 점수 변환 규칙
# ============================================================
# E/I 차원: 홀수번 문항은 E(정방향), 짝수번 문항은 I(역방향 → E 점수로 변환)
# S/N 차원: 홀수번 문항은 S(정방향), 짝수번 문항은 N(역방향 → S 점수로 변환)
# T/F 차원: 홀수번 문항은 T(정방향), 짝수번 문항은 F(역방향 → T 점수로 변환)
# J/P 차원: 홀수번 문항은 J(정방향), 짝수번 문항은 P(역방향 → J 점수로 변환)

# 역채점: 8 - 원점수 (7점 척도)
REVERSE_SCORED = {
    'EI': [1, 3, 5, 7],  # Q8, Q10, Q12, Q14 (짝수번 = 내향 문항, 0-indexed within dim)
    'SN': [1, 3, 5, 7],  # Q16, Q18, Q20, Q22
    'TF': [1, 3, 5, 7],  # Q24, Q26, Q28, Q30
    'JP': [1, 3, 5, 7],  # Q32, Q34, Q36, Q38
}


def load_survey_data():
    """설문 CSV 로딩 및 전처리"""
    if not os.path.exists(SURVEY_CSV):
        print(f"[오류] 설문 응답 파일을 찾을 수 없습니다: {SURVEY_CSV}")
        print(f"       Google Sheets에서 CSV를 다운로드하여 위 경로에 저장해 주세요.")
        return None

    df = pd.read_csv(SURVEY_CSV)
    print(f"[데이터] 설문 응답 수: {len(df)}건")
    print(f"[데이터] 컬럼 수: {len(df.columns)}개")

    return df


def compute_dimension_scores(df):
    """리커트 응답 → MBTI 4차원 점수 계산 (mbti_scoring 모듈 활용)

    각 차원 점수 범위: 1.0 ~ 7.0
    높을수록 E / S / T / J 성향이 강함
    """
    cols = df.columns.tolist()
    start_idx = 1 + 6  # 타임스탬프(1) + 기본정보(6) 이후

    # mbti_scoring 모듈의 일괄 채점 사용
    batch = batch_compute_from_array(df.values, start_col=start_idx)

    scores = batch['scores']
    dim_labels = {
        'EI': ('외향(E)', '내향(I)'),
        'SN': ('감각(S)', '직관(N)'),
        'TF': ('사고(T)', '감정(F)'),
        'JP': ('판단(J)', '인식(P)')
    }

    for dim in ['EI', 'SN', 'TF', 'JP']:
        label = dim_labels[dim]
        print(f"  [{dim}] {label[0]}-{label[1]} 점수: "
              f"평균={np.mean(scores[dim]):.2f}, 표준편차={np.std(scores[dim]):.2f}")

    return scores


def classify_mbti(scores):
    """차원 점수 → MBTI 4글자 유형 분류

    기준: 차원 점수 ≥ 4.0 → E/S/T/J, < 4.0 → I/N/F/P
    """
    n = len(scores['EI'])
    types = []
    for i in range(n):
        e_or_i = 'E' if scores['EI'][i] >= MIDPOINT else 'I'
        s_or_n = 'S' if scores['SN'][i] >= MIDPOINT else 'N'
        t_or_f = 'T' if scores['TF'][i] >= MIDPOINT else 'F'
        j_or_p = 'J' if scores['JP'][i] >= MIDPOINT else 'P'
        types.append(e_or_i + s_or_n + t_or_f + j_or_p)
    return np.array(types)


def analyze_mbti_vs_blood(df, scores, mbti_types):
    """혈액형 × MBTI 교차 분석"""
    print("\n" + "━" * 60)
    print("  분석: 혈액형 × MBTI 차원 점수 관계")
    print("━" * 60)

    # 혈액형 컬럼 (4번째 문항 = cols[4])
    blood_col = df.iloc[:, 4].values  # Q4: 혈액형
    blood_types = ['A형', 'B형', 'O형', 'AB형']

    for dim_key, dim_score in scores.items():
        groups = []
        labels = []
        for bt in blood_types:
            mask = blood_col == bt
            if np.sum(mask) > 0:
                groups.append(dim_score[mask])
                labels.append(bt)

        if len(groups) >= 2:
            result = one_way_anova(*groups)
            print_test_result(f"ANOVA: {dim_key} × 혈액형", result)


def analyze_belief_by_demographics(df):
    """혈액형 성격론 믿음 × 인구통계"""
    print("\n" + "━" * 60)
    print("  분석: 혈액형 성격론 믿음 × 인구통계")
    print("━" * 60)

    # Q39: 혈액형-성격 관련성 믿음 (1-5점)
    # 실제 컬럼 인덱스는 CSV 구조에 따라 조정 필요
    belief_idx = 1 + 6 + 32  # 타임스탬프(1) + 기본정보(6) + 리커트32문항 이후
    if belief_idx < len(df.columns):
        belief = df.iloc[:, belief_idx].values.astype(float)
        stats = descriptive_stats(belief)
        print(f"\n  혈액형-성격 관련성 믿음 (1-5점):")
        print(f"    평균: {stats['평균']:.2f}")
        print(f"    표준편차: {stats['표준편차']:.2f}")
        print(f"    중앙값: {stats['중앙값']:.1f}")


def main():
    """설문 분석 메인"""
    print("\n" + "=" * 60)
    print("  자체 설문 응답 분석")
    print("=" * 60)

    set_project_style()

    df = load_survey_data()
    if df is None:
        return

    # 응답 기본 통계
    print(f"\n[기본 통계]")
    print(f"  총 응답 수: {len(df)}")

    # 차원 점수 계산
    print(f"\n[MBTI 차원 점수 계산]")
    scores = compute_dimension_scores(df)

    if scores:
        # MBTI 유형 분류
        mbti_types = classify_mbti(scores)
        print(f"\n[설문 기반 MBTI 분류 결과]")
        for t in sorted(np.unique(mbti_types)):
            n = np.sum(mbti_types == t)
            pct = n / len(mbti_types) * 100
            print(f"  {t}: {n}명 ({pct:.1f}%)")

        # 자기보고 MBTI vs 설문 기반 MBTI 일치도
        self_mbti = df.iloc[:, 5].values  # Q5: 본인 MBTI
        valid = self_mbti != '모름/검사 안 해봄'
        if np.sum(valid) > 0:
            match = np.sum(mbti_types[valid] == self_mbti[valid])
            total_valid = np.sum(valid)
            print(f"\n[자기보고 vs 설문 기반 MBTI 일치율]")
            print(f"  일치: {match}/{total_valid} ({match/total_valid*100:.1f}%)")

        # 혈액형 × MBTI 분석
        analyze_mbti_vs_blood(df, scores, mbti_types)

    # 혈액형 믿음 분석
    analyze_belief_by_demographics(df)

    print("\n[완료] 설문 분석 완료!")


if __name__ == '__main__':
    main()
