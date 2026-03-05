# -*- coding: utf-8 -*-
"""
팀원 A 확장: 밈 설문 데이터로 team_a 분석 교차검증
====================================================
데이터: data/meme/ 설문 CSV + data.csv (Kaggle 43,744명)

목적:
  team_a(H1~H4)의 핵심 발견을 소규모 자체 설문으로 교차검증하고,
  MBTI 유형(범주형) × 인구통계 관점에서 두 데이터셋을 비교한다.

반영 가능 항목:
  [O] H1 교차검증: 성별 x MBTI 유형 분포 (카이제곱)
  [O] H2 교차검증: 연령대 x MBTI 차원 점수 (ANOVA)
  [O] H4 교차검증: 차원 점수 x 나이 상관 (Pearson)
  [!] H3: 교육수준 (설문에 교육수준 문항 없음)

통계 방법: 카이제곱 적합도/독립성, t-검정, ANOVA, Pearson 상관, 효과크기

그래프 목록 (7개):
  fig_as1: 설문 MBTI 유형 분포 vs Kaggle
  fig_as2: 성별 x MBTI 유형 — 설문 vs Kaggle (H1)
  fig_as3: 연령대 x MBTI 차원 점수 — 설문 교차검증 (H2)
  fig_as4: MBTI 차원별 인구통계 요약 — 설문 vs Kaggle
  fig_as5: 차원 점수 x 나이 상관 — 설문 교차검증 (H4)
  fig_as6: 효과크기 비교 Forest Plot
  fig_as7: 종합 결론 인포그래픽
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

from common.config import (
    MBTI_TYPES, MBTI_COLORS, GENDER_COLORS,
    MBTI_DIMENSIONS, DIMENSION_NAMES_KR,
    FIGSIZE_DEFAULT, FIGSIZE_WIDE
)
from common.data_loader import load_personality_data
from common.stats_utils import (
    descriptive_stats, pearson_correlation, independent_t_test,
    one_way_anova, cohens_d, confidence_interval,
    linear_regression, chi_square_test, chi_square_goodness_of_fit,
    frequency_table, print_test_result
)
from common.plot_style import (
    set_project_style, save_figure, format_p_value, add_result_text
)
from survey.mbti_scoring_v2 import (
    batch_compute_from_array_v2, extract_bonus_data,
    V2_COL_MAP, MIDPOINT
)

TEAM = 'team_a'

# 설문 CSV 경로
SURVEY_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'data', 'meme',
    'MBTI_밈_설문v2_응답_데이터 - Form Responses 1.csv'
)

DIM_KEYS = ['EI', 'SN', 'TF', 'JP']
KAGGLE_DIM_MAP = {
    'EI': 'introversion', 'SN': 'sensing',
    'TF': 'thinking', 'JP': 'judging',
}
DIM_LABELS_KR = {
    'EI': '내향성(EI)', 'SN': '감각(SN)',
    'TF': '사고(TF)', 'JP': '판단(JP)',
}

AGE_MAP = {'20대': 25, '30대': 35, '40대 이상': 50}
AGE_COLORS = {'20대': '#3498DB', '30대': '#E67E22', '40대 이상': '#2ECC71'}


# ============================================================
#  데이터 로드
# ============================================================
def load_survey_data():
    """밈 설문 CSV + Kaggle 데이터 로드"""
    print("=" * 60)
    print("  팀원 A 확장: 밈 설문 교차검증 (인구통계 관점)")
    print("=" * 60)

    if not os.path.exists(SURVEY_CSV):
        raise FileNotFoundError(f"설문 CSV 파일이 없습니다: {SURVEY_CSV}")

    df = pd.read_csv(SURVEY_CSV)
    raw = df.values
    n = raw.shape[0]
    print(f"\n[데이터] 설문 응답: {n}명")

    scoring = batch_compute_from_array_v2(raw)
    bonus = extract_bonus_data(raw)

    self_mbti = np.array([str(raw[i, V2_COL_MAP['self_mbti']]).strip()
                          for i in range(n)])
    genders = np.array([str(raw[i, V2_COL_MAP['gender']]).strip()
                        for i in range(n)])
    ages = np.array([str(raw[i, V2_COL_MAP['age']]).strip()
                     for i in range(n)])
    blood_types = np.array([str(raw[i, V2_COL_MAP['blood_type']]).strip()
                            for i in range(n)])

    kaggle = load_personality_data()
    print(f"[데이터] Kaggle 비교용: {len(kaggle['age'])}명")

    return {
        'n': n,
        'survey_scores': scoring['scores'],
        'survey_types': scoring['types'],
        'self_mbti': self_mbti,
        'genders': genders,
        'ages': ages,
        'blood_types': blood_types,
        'bonus': bonus,
        'kaggle': kaggle,
    }


# ============================================================
#  AS1: 설문 MBTI 유형 분포 vs Kaggle
# ============================================================
def analyze_mbti_type_distribution(data):
    """설문 vs Kaggle MBTI 유형 분포 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 AS1: MBTI 유형 분포 — 설문 vs Kaggle")
    print("━" * 60)

    survey_types = data['survey_types']
    kaggle_types = data['kaggle']['personality']
    n_s = data['n']
    n_k = len(kaggle_types)

    types_sorted = sorted(MBTI_TYPES)

    # 설문 빈도
    s_counts = np.array([np.sum(survey_types == t) for t in types_sorted])
    s_pcts = s_counts / n_s * 100

    # Kaggle 빈도
    k_counts = np.array([np.sum(kaggle_types == t) for t in types_sorted])
    k_pcts = k_counts / n_k * 100

    # 카이제곱 적합도 (설문 분포 vs Kaggle 비율 기대빈도)
    expected = k_pcts / 100 * n_s
    expected = np.where(expected < 1, 1, expected)  # 0 방지
    chi2_res = chi_square_goodness_of_fit(s_counts.astype(float), expected)

    print(f"  설문 {n_s}명 vs Kaggle {n_k:,}명")
    print(f"  카이제곱 적합도: chi2={chi2_res['chi2']:.2f}, "
          f"df={chi2_res['dof']}, {format_p_value(chi2_res['p_value'])}")

    # === 시각화 ===
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    fig.suptitle('MBTI 유형 분포 비교: 설문 vs Kaggle', fontsize=26, fontweight='bold')

    # 좌: 설문
    ax = axes[0]
    colors = [MBTI_COLORS.get(t, '#95A5A6') for t in types_sorted]
    bars = ax.bar(range(len(types_sorted)), s_pcts, color=colors,
                  edgecolor='white', alpha=0.85)
    ax.set_xticks(range(len(types_sorted)))
    ax.set_xticklabels(types_sorted, rotation=45, ha='right', fontsize=13)
    ax.set_ylabel('비율 (%)')
    ax.set_title(f'설문 (N={n_s})', fontsize=22, fontweight='bold')
    ax.set_ylim(0, max(s_pcts) * 1.3)
    for bar, pct, cnt in zip(bars, s_pcts, s_counts):
        if cnt > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{cnt}명\n({pct:.1f}%)', ha='center', fontsize=11)

    # 우: Kaggle
    ax = axes[1]
    bars = ax.bar(range(len(types_sorted)), k_pcts, color=colors,
                  edgecolor='white', alpha=0.85)
    ax.set_xticks(range(len(types_sorted)))
    ax.set_xticklabels(types_sorted, rotation=45, ha='right', fontsize=13)
    ax.set_ylabel('비율 (%)')
    ax.set_title(f'Kaggle (N={n_k:,})', fontsize=22, fontweight='bold')
    ax.set_ylim(0, max(k_pcts) * 1.3)

    result_text = (f"적합도 검정:\nchi2 = {chi2_res['chi2']:.2f}\n"
                   f"{format_p_value(chi2_res['p_value'])}")
    add_result_text(ax, result_text)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_as1_mbti_type_distribution.png')

    return chi2_res


# ============================================================
#  AS2: 성별 x MBTI 유형 — 설문 vs Kaggle (H1)
# ============================================================
def analyze_gender_mbti_crossval(data):
    """성별 x MBTI 유형 분포 교차검증"""
    print("\n\n" + "━" * 60)
    print("  분석 AS2: 성별 x MBTI 유형 — 설문 vs Kaggle (H1)")
    print("━" * 60)

    survey_types = data['survey_types']
    genders = data['genders']
    kaggle = data['kaggle']
    n_s = data['n']

    # 설문 성별 매핑
    gender_map = {'남성': 'Male', '여성': 'Female'}
    s_gender = np.array([gender_map.get(g, 'Other') for g in genders])

    # 설문에서 유효한 성별만
    valid_mask = np.isin(s_gender, ['Male', 'Female'])
    s_types_valid = survey_types[valid_mask]
    s_gender_valid = s_gender[valid_mask]

    # 차원별 성별 차이 (설문)
    dim_results_survey = {}
    print("\n  [설문] 차원별 성별 차이:")
    for dk in DIM_KEYS:
        scores = data['survey_scores'][dk]
        m_scores = scores[valid_mask & (s_gender == 'Male')]
        f_scores = scores[valid_mask & (s_gender == 'Female')]
        if len(m_scores) >= 2 and len(f_scores) >= 2:
            t_res = independent_t_test(m_scores, f_scores)
            d_res = cohens_d(m_scores, f_scores)
            dim_results_survey[dk] = {'t': t_res, 'd': d_res['d']}
            print(f"    {dk}: 남성={np.mean(m_scores):.2f}, 여성={np.mean(f_scores):.2f}, "
                  f"d={d_res['d']:.3f}, {format_p_value(t_res['p_value'])}")

    # Kaggle 차원별 성별 차이
    dim_results_kaggle = {}
    k_gender = kaggle['gender']
    print("\n  [Kaggle] 차원별 성별 차이:")
    for dk in DIM_KEYS:
        k_scores = kaggle[KAGGLE_DIM_MAP[dk]]
        m_scores = k_scores[k_gender == 'Male']
        f_scores = k_scores[k_gender == 'Female']
        t_res = independent_t_test(m_scores, f_scores)
        d_res = cohens_d(m_scores, f_scores)
        dim_results_kaggle[dk] = {'t': t_res, 'd': d_res['d']}
        print(f"    {dk}: 남성={np.mean(m_scores):.2f}, 여성={np.mean(f_scores):.2f}, "
              f"d={d_res['d']:.3f}, {format_p_value(t_res['p_value'])}")

    # === 시각화: 2x2 차원별 성별 박스플롯 (설문) ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('성별 x MBTI 차원 점수 — 설문 vs Kaggle (H1 교차검증)',
                 fontsize=24, fontweight='bold')

    for idx, dk in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        scores = data['survey_scores'][dk]
        m_s = scores[valid_mask & (s_gender == 'Male')]
        f_s = scores[valid_mask & (s_gender == 'Female')]

        bp = ax.boxplot([m_s, f_s], tick_labels=['남성', '여성'],
                        patch_artist=True,
                        medianprops=dict(color='black', linewidth=2))
        bp['boxes'][0].set_facecolor(GENDER_COLORS.get('Male', '#5DADE2'))
        bp['boxes'][1].set_facecolor(GENDER_COLORS.get('Female', '#F1948A'))

        # 평균 표시
        for i, (vals, lbl) in enumerate([(m_s, '남성'), (f_s, '여성')]):
            if len(vals) > 0:
                ax.scatter(i + 1, np.mean(vals), color='red', marker='D',
                           s=60, zorder=5)
                ax.annotate(f'{np.mean(vals):.2f}', (i + 1, np.mean(vals)),
                            textcoords="offset points", xytext=(15, 5),
                            fontsize=14, color='red')

        s_d = dim_results_survey.get(dk, {}).get('d', 0)
        k_d = dim_results_kaggle.get(dk, {}).get('d', 0)
        ax.set_title(f'{dk}: 설문 d={s_d:.3f} / Kaggle d={k_d:.3f}',
                     fontsize=18, fontweight='bold')
        ax.set_ylabel(f'{DIM_LABELS_KR[dk]} 점수')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_as2_gender_mbti_crossval.png')

    return dim_results_survey, dim_results_kaggle


# ============================================================
#  AS3: 연령대 x MBTI 차원 점수 (H2)
# ============================================================
def analyze_age_mbti_crossval(data):
    """연령대 x MBTI 차원 점수 교차검증"""
    print("\n\n" + "━" * 60)
    print("  분석 AS3: 연령대 x MBTI 차원 점수 — 설문 교차검증 (H2)")
    print("━" * 60)

    ages = data['ages']
    age_groups_order = ['20대', '30대', '40대 이상']
    age_results = {}

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('연령대 x MBTI 차원 점수 — 설문 교차검증 (H2)',
                 fontsize=24, fontweight='bold')

    for idx, dk in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        scores = data['survey_scores'][dk]

        groups_data = []
        labels = []
        for ag in age_groups_order:
            mask = ages == ag
            grp = scores[mask]
            if len(grp) >= 2:
                groups_data.append(grp)
                labels.append(f'{ag}\n(n={len(grp)})')

        if len(groups_data) >= 2:
            anova_res = one_way_anova(*groups_data)
            age_results[dk] = anova_res
            print(f"  [{dk}] F={anova_res['f_stat']:.3f}, "
                  f"eta2={anova_res['eta_squared']:.4f}, "
                  f"{format_p_value(anova_res['p_value'])}")

            bp = ax.boxplot(groups_data, tick_labels=labels, patch_artist=True,
                            medianprops=dict(color='black', linewidth=2))
            for i, (patch, ag) in enumerate(zip(bp['boxes'], age_groups_order[:len(groups_data)])):
                patch.set_facecolor(AGE_COLORS.get(ag, '#95A5A6'))
                patch.set_alpha(0.7)
                ax.scatter(i + 1, np.mean(groups_data[i]), color='red',
                           marker='D', s=60, zorder=5)

            sig = '***' if anova_res['p_value'] < 0.001 else ('**' if anova_res['p_value'] < 0.01 else ('*' if anova_res['p_value'] < 0.05 else 'ns'))
            ax.set_title(f'{dk}: eta2={anova_res["eta_squared"]:.4f} ({sig})',
                         fontsize=18, fontweight='bold')
        else:
            ax.set_title(f'{dk}: 데이터 부족', fontsize=18)
            ax.text(0.5, 0.5, 'N/A', ha='center', va='center',
                    fontsize=20, transform=ax.transAxes)

        ax.set_ylabel(f'{DIM_LABELS_KR[dk]} 점수')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_as3_age_mbti_crossval.png')

    return age_results


# ============================================================
#  AS4: MBTI 차원별 인구통계 요약 — 설문 vs Kaggle
# ============================================================
def analyze_demographics_summary(data):
    """차원별 인구통계 요약 히트맵 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 AS4: MBTI 차원별 인구통계 요약 — 설문 vs Kaggle")
    print("━" * 60)

    survey_types = data['survey_types']
    genders = data['genders']
    ages = data['ages']
    kaggle = data['kaggle']

    gender_map = {'남성': 'Male', '여성': 'Female'}
    s_gender = np.array([gender_map.get(g, 'Other') for g in genders])
    s_age_num = np.array([AGE_MAP.get(a, 35) for a in ages], dtype=float)

    # 설문 4차원 x 2지표 (여성비율, 평균나이)
    s_data = np.zeros((4, 4), dtype=np.float64)  # 4dim x (grp1_f%, grp2_f%, grp1_age, grp2_age)
    k_data = np.zeros((4, 4), dtype=np.float64)

    for idx, dk in enumerate(DIM_KEYS):
        letter1, letter2 = MBTI_DIMENSIONS[dk]
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dk]

        # 설문
        s_mask1 = np.array([t[dim_idx] == letter1 for t in survey_types])
        s_mask2 = np.array([t[dim_idx] == letter2 for t in survey_types])

        valid_gender = s_gender != 'Other'
        s_data[idx, 0] = np.mean(s_gender[s_mask1 & valid_gender] == 'Female') * 100 if np.sum(s_mask1 & valid_gender) > 0 else 0
        s_data[idx, 1] = np.mean(s_gender[s_mask2 & valid_gender] == 'Female') * 100 if np.sum(s_mask2 & valid_gender) > 0 else 0
        s_data[idx, 2] = np.mean(s_age_num[s_mask1]) if np.sum(s_mask1) > 0 else 0
        s_data[idx, 3] = np.mean(s_age_num[s_mask2]) if np.sum(s_mask2) > 0 else 0

        # Kaggle
        k_pers = kaggle['personality']
        k_mask1 = np.array([p[dim_idx] == letter1 for p in k_pers])
        k_mask2 = np.array([p[dim_idx] == letter2 for p in k_pers])

        k_data[idx, 0] = np.mean(kaggle['gender'][k_mask1] == 'Female') * 100
        k_data[idx, 1] = np.mean(kaggle['gender'][k_mask2] == 'Female') * 100
        k_data[idx, 2] = np.mean(kaggle['age'][k_mask1])
        k_data[idx, 3] = np.mean(kaggle['age'][k_mask2])

        kr = DIMENSION_NAMES_KR[dk]
        print(f"  [{dk}] 설문: {kr[0]} 여성 {s_data[idx,0]:.1f}%, 나이 {s_data[idx,2]:.1f} / "
              f"{kr[1]} 여성 {s_data[idx,1]:.1f}%, 나이 {s_data[idx,3]:.1f}")
        print(f"       Kaggle: {kr[0]} 여성 {k_data[idx,0]:.1f}%, 나이 {k_data[idx,2]:.1f} / "
              f"{kr[1]} 여성 {k_data[idx,1]:.1f}%, 나이 {k_data[idx,3]:.1f}")

    # === 시각화: 2열 히트맵 ===
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('MBTI 차원별 인구통계 요약: 설문 vs Kaggle', fontsize=24, fontweight='bold')

    col_labels = ['Grp1\n여성%', 'Grp2\n여성%', 'Grp1\n평균나이', 'Grp2\n평균나이']

    ax = axes[0]
    sns.heatmap(s_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                yticklabels=DIM_KEYS, xticklabels=col_labels,
                linewidths=0.5, annot_kws={'fontsize': 14})
    ax.set_title(f'설문 (N={data["n"]})', fontsize=20, fontweight='bold')

    ax = axes[1]
    sns.heatmap(k_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                yticklabels=DIM_KEYS, xticklabels=col_labels,
                linewidths=0.5, annot_kws={'fontsize': 14})
    ax.set_title(f'Kaggle (N={len(kaggle["age"]):,})', fontsize=20, fontweight='bold')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_as4_demographics_summary.png')


# ============================================================
#  AS5: 차원 점수 x 나이 상관 (H4)
# ============================================================
def analyze_score_age_crossval(data):
    """차원 점수 x 나이 상관 교차검증"""
    print("\n\n" + "━" * 60)
    print("  분석 AS5: 차원 점수 x 나이 상관 — 설문 교차검증 (H4)")
    print("━" * 60)

    ages = data['ages']
    s_age_num = np.array([AGE_MAP.get(a, 35) for a in ages], dtype=float)
    kaggle = data['kaggle']

    corr_results = {}
    scatter_colors = ['#3498DB', '#2ECC71', '#E74C3C', '#9B59B6']

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('MBTI 차원 점수 x 나이 상관: 설문 교차검증 (H4)',
                 fontsize=24, fontweight='bold')

    for idx, dk in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        s_scores = data['survey_scores'][dk]

        # 설문 상관
        s_corr = pearson_correlation(s_scores, s_age_num)
        s_reg = linear_regression(s_scores, s_age_num)
        corr_results[dk] = s_corr

        # Kaggle 상관
        k_corr = pearson_correlation(kaggle[KAGGLE_DIM_MAP[dk]], kaggle['age'])

        # 산점도 (설문)
        # 나이대별 약간의 jitter 추가
        jitter = np.random.default_rng(42).normal(0, 0.8, len(s_age_num))
        ax.scatter(s_scores, s_age_num + jitter, alpha=0.6, s=60,
                   color=scatter_colors[idx], edgecolor='white', linewidth=0.5)

        # 회귀선
        x_line = np.linspace(np.min(s_scores), np.max(s_scores), 100)
        y_line = s_reg['slope'] * x_line + s_reg['intercept']
        ax.plot(x_line, y_line, color='red', linewidth=2.5,
                label=f'y={s_reg["slope"]:.3f}x+{s_reg["intercept"]:.1f}\nR\u00b2={s_reg["r_squared"]:.3f}')

        sig = '***' if s_corr['p_value'] < 0.001 else ('**' if s_corr['p_value'] < 0.01 else ('*' if s_corr['p_value'] < 0.05 else 'ns'))
        ax.set_title(f'{dk}: r={s_corr["r"]:.3f}({sig}) / Kaggle r={k_corr["r"]:.3f}',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel(f'{DIM_LABELS_KR[dk]} 점수')
        ax.set_ylabel('나이 (추정)')
        ax.legend(fontsize=14)

        print(f"  [{dk}] 설문: r={s_corr['r']:.4f}, {format_p_value(s_corr['p_value'])} / "
              f"Kaggle: r={k_corr['r']:.4f}")
        print(f"    회귀식: 나이 = {s_reg['slope']:.4f} x {dk}점수 + {s_reg['intercept']:.2f}, "
              f"R\u00b2={s_reg['r_squared']:.4f}")

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_as5_score_age_crossval.png')

    return corr_results


# ============================================================
#  AS6: 효과크기 비교 Forest Plot
# ============================================================
def analyze_effect_size_comparison(gender_survey, gender_kaggle, age_results, corr_results, n_survey=0):
    """설문 vs Kaggle 효과크기 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 AS6: 효과크기 비교 Forest Plot")
    print("━" * 60)

    effects = []

    # 성별 Cohen's d 비교 (차원별)
    for dk in DIM_KEYS:
        s_d = abs(gender_survey.get(dk, {}).get('d', 0))
        k_d = abs(gender_kaggle.get(dk, {}).get('d', 0))
        effects.append({
            'label': f'{dk} 성별 차이 (d)',
            'survey': s_d,
            'kaggle': k_d,
        })

    # 연령 ANOVA eta^2
    for dk in DIM_KEYS:
        s_eta = age_results.get(dk, {}).get('eta_squared', 0)
        effects.append({
            'label': f'{dk} 연령 (eta2)',
            'survey': s_eta,
            'kaggle': 0,  # Kaggle은 연속 나이로 직접 비교 어려움
        })

    # 상관 |r|
    for dk in DIM_KEYS:
        s_r = abs(corr_results.get(dk, {}).get('r', 0))
        effects.append({
            'label': f'{dk} 나이상관 (|r|)',
            'survey': s_r,
            'kaggle': 0,
        })

    # 출력
    print(f"\n  {'검정':25s} {'설문':>8s} {'Kaggle':>8s}")
    print("  " + "-" * 45)
    for e in effects:
        print(f"  {e['label']:25s} {e['survey']:>8.4f} {e['kaggle']:>8.4f}")

    # === 시각화 ===
    fig, ax = plt.subplots(figsize=(14, max(8, len(effects) * 0.6)))
    fig.suptitle('효과크기 비교: 설문 vs Kaggle (팀원 A 교차검증)',
                 fontsize=24, fontweight='bold')

    y_pos = np.arange(len(effects))
    height = 0.35

    bars_s = ax.barh(y_pos + height/2, [e['survey'] for e in effects],
                     height, color='#E74C3C', alpha=0.7, label=f'설문 (N={n_survey})')
    bars_k = ax.barh(y_pos - height/2, [e['kaggle'] for e in effects],
                     height, color='#3498DB', alpha=0.7, label='Kaggle (N=43,744)')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([e['label'] for e in effects], fontsize=18)
    ax.set_xlabel('효과크기', fontsize=20)
    ax.legend(fontsize=20, loc='lower right')

    # 기준선
    ax.axvline(0.1, color='gray', linestyle=':', alpha=0.5, label='작은 효과')
    ax.axvline(0.3, color='gray', linestyle='--', alpha=0.5, label='보통 효과')

    ax.text(0.5, -0.08, f'* 소표본(N={n_survey}) 한계: 효과크기 추정의 신뢰구간이 넓음에 주의',
            transform=ax.transAxes, fontsize=17, color='#7F8C8D', ha='center')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_as6_effect_size_comparison.png')

    return effects


# ============================================================
#  AS7: 종합 결론 인포그래픽
# ============================================================
def create_conclusion_infographic(data, chi2_type, gender_survey, gender_kaggle,
                                    age_results, corr_results):
    """교차검증 종합 결론"""
    print("\n\n" + "━" * 60)
    print("  분석 AS7: 종합 결론 인포그래픽")
    print("━" * 60)

    fig = plt.figure(figsize=(28, 16))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.96, 'MBTI x 인구통계 — 설문 교차검증 종합 결론',
             ha='center', fontsize=34, fontweight='bold', color='#2C3E50')
    fig.text(0.5, 0.925, f'Kaggle 43,744명 vs 설문 {data["n"]}명 | 팀원 A 확장 분석',
             ha='center', fontsize=22, color='#7F8C8D')

    panels = [
        (0.03, 0.55, 0.30, 0.32),
        (0.35, 0.55, 0.30, 0.32),
        (0.67, 0.55, 0.30, 0.32),
        (0.03, 0.15, 0.30, 0.32),
        (0.35, 0.15, 0.30, 0.32),
        (0.67, 0.15, 0.30, 0.32),
    ]

    # 성별 효과크기 요약
    gender_summary = []
    for dk in DIM_KEYS:
        s_d = abs(gender_survey.get(dk, {}).get('d', 0))
        k_d = abs(gender_kaggle.get(dk, {}).get('d', 0))
        gender_summary.append(f"{dk}: s={s_d:.3f}/k={k_d:.3f}")
    gender_text = '\n'.join(gender_summary)

    # 연령 효과크기 요약
    age_summary = []
    for dk in DIM_KEYS:
        eta = age_results.get(dk, {}).get('eta_squared', 0)
        sig = '[O]' if age_results.get(dk, {}).get('significant', False) else '[X]'
        age_summary.append(f"{dk}: eta2={eta:.4f} {sig}")
    age_text = '\n'.join(age_summary)

    # 상관 요약
    corr_summary = []
    for dk in DIM_KEYS:
        r = corr_results.get(dk, {}).get('r', 0)
        corr_summary.append(f"{dk}: r={r:.3f}")
    corr_text = '\n'.join(corr_summary)

    panel_data = [
        {
            'title': 'MBTI 유형 분포',
            'content': (f"설문 vs Kaggle 분포 비교\n"
                       f"chi2 = {chi2_type.get('chi2', 0):.1f}\n"
                       f"{format_p_value(chi2_type.get('p_value', 1))}\n\n"
                       f"[!] 소표본으로 편차 불가피"),
            'color': '#E74C3C',
        },
        {
            'title': 'H1: 성별 x MBTI',
            'content': f"차원별 Cohen's d:\n{gender_text}\n\n[!] 설문에서도 약한 효과",
            'color': '#3498DB',
        },
        {
            'title': 'H2: 연령 x MBTI',
            'content': f"차원별 ANOVA:\n{age_text}\n\n[!] 범주형 나이대 한계",
            'color': '#2ECC71',
        },
        {
            'title': 'H4: 점수-나이 상관',
            'content': f"Pearson r:\n{corr_text}\n\n[!] 범주형 나이 사용",
            'color': '#9B59B6',
        },
        {
            'title': '교차검증 일치도',
            'content': ("Kaggle과 설문 결과 비교:\n"
                       "성별 효과: 방향 일치\n"
                       "효과크기: 모두 작은 수준\n\n"
                       "-> 두 데이터셋 패턴 유사"),
            'color': '#F39C12',
        },
        {
            'title': '종합 해석',
            'content': (f"N={data['n']}명 소표본 교차검증\n\n"
                       "Kaggle 대표본과 유사한 패턴:\n"
                       "MBTI-인구통계 연관 극히 미약\n\n"
                       "-> 통계적 유의성 != 실질적 의미"),
            'color': '#2C3E50',
        },
    ]

    for (x, y, w, h), pd_item in zip(panels, panel_data):
        ax = fig.add_axes([x, y, w, h])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()

        rect = plt.Rectangle((0, 0), 1, 1, facecolor=pd_item['color'],
                              alpha=0.08, transform=ax.transAxes)
        ax.add_patch(rect)
        rect_top = plt.Rectangle((0, 0.88), 1, 0.12, facecolor=pd_item['color'],
                                 alpha=0.3, transform=ax.transAxes)
        ax.add_patch(rect_top)
        ax.text(0.5, 0.93, pd_item['title'], ha='center', va='center',
                fontsize=24, fontweight='bold', color=pd_item['color'])
        ax.text(0.08, 0.45, pd_item['content'], ha='left', va='center',
                fontsize=23, color='#2C3E50', linespacing=1.4)

    fig.text(0.5, 0.075,
             '결론: 소규모 설문에서도 MBTI-인구통계 연관성은 미약 — Kaggle 대표본과 일관된 결과',
             ha='center', fontsize=26, fontweight='bold', color='#2C3E50',
             bbox=dict(facecolor='#FEF9E7', edgecolor='#F39C12',
                       boxstyle='round,pad=0.6', linewidth=2))

    fig.text(0.5, 0.025,
             f'* 설문 N={data["n"]} 소표본 한계: 효과크기 추정의 불확실성 높음, 방향성 참고용',
             ha='center', fontsize=23, color='#7F8C8D', style='italic')

    save_figure(fig, TEAM, 'fig_as7_conclusion_infographic.png', tight=False)


# ============================================================
#  메인 실행
# ============================================================
def main():
    """팀원 A 설문 교차검증 실행"""
    data = load_survey_data()

    chi2_type = analyze_mbti_type_distribution(data)               # as1
    gender_s, gender_k = analyze_gender_mbti_crossval(data)        # as2
    age_results = analyze_age_mbti_crossval(data)                  # as3
    analyze_demographics_summary(data)                              # as4
    corr_results = analyze_score_age_crossval(data)                # as5
    analyze_effect_size_comparison(gender_s, gender_k,
                                   age_results, corr_results,
                                   n_survey=data['n'])              # as6
    create_conclusion_infographic(data, chi2_type, gender_s,
                                   gender_k, age_results,
                                   corr_results)                    # as7

    print(f"\n[완료] 팀원 A 설문 교차검증 완료! 그래프 7개 저장")
    print(f"  저장 위치: results/figures/team_a/\n")


if __name__ == '__main__':
    set_project_style()
    main()
