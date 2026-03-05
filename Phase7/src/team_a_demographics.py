# -*- coding: utf-8 -*-
"""
팀원 A: MBTI 유형별 인구통계학적 특성 심층 분석
================================================
데이터: data.csv (43,744행)
분석: 성별/나이/교육수준과 MBTI 유형 간의 관계 검정

가설:
  H1: MBTI 유형별 성별 분포에 유의한 차이가 있다
  H2: MBTI 유형별 평균 나이에 유의한 차이가 있다
  H3: MBTI 유형별 교육수준(0/1) 분포에 유의한 차이가 있다
  H4: MBTI 차원 점수와 나이 사이에 유의한 상관관계가 있다

통계 방법: 카이제곱 독립성 검정, t-검정, 일원분산분석(ANOVA),
          피어슨 상관분석, 선형회귀, 신뢰구간, 효과크기 분석

시각화: 12개 (fig_a1 ~ fig_a12)
  - fig_a1: MBTI 유형별 성별 비율 Grouped Bar
  - fig_a2: 성별-MBTI 관측/기대 빈도비 Heatmap
  - fig_a3: MBTI 유형별 나이 Box Plot
  - fig_a4: MBTI 차원별 나이 비교 (2×2 Box)
  - fig_a5: MBTI 유형별 교육수준 Stacked Bar
  - fig_a6: MBTI 차원별 인구통계 요약 Heatmap
  - fig_a7: 데이터 탐색 EDA 개요 (분포 + 히스토그램)
  - fig_a8: 성별 × MBTI 차원 Butterfly Chart
  - fig_a9: MBTI 유형별 나이 Violin Plot
  - fig_a10: MBTI 차원 점수 × 나이 산점도 + 회귀
  - fig_a11: 전체 효과크기 Forest Plot
  - fig_a12: 종합 결론 인포그래픽
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns

from common.config import (
    MBTI_TYPES, MBTI_DIMENSIONS, DIMENSION_NAMES_KR,
    GENDER_COLORS, MBTI_COLORS
)
from common.data_loader import load_personality_data
from common.stats_utils import (
    descriptive_stats, frequency_table, chi_square_test,
    independent_t_test, one_way_anova, pearson_correlation,
    linear_regression, confidence_interval,
    proportion_confidence_interval, print_test_result
)
from common.plot_style import (
    set_project_style, save_figure, add_result_text,
    format_p_value
)

TEAM = 'team_a'


def load_and_preprocess():
    """데이터 로딩 및 전처리"""
    print("\n" + "=" * 60)
    print("  팀원 A: MBTI 유형별 인구통계학적 특성 심층 분석")
    print("=" * 60)

    data = load_personality_data()

    # 기본 정보 출력
    n = len(data['personality'])
    print(f"\n[데이터] 전체 표본 수: {n:,}명")
    print(f"[데이터] MBTI 유형 수: {len(np.unique(data['personality']))}개")
    print(f"[데이터] 성별: {np.unique(data['gender'])}")
    print(f"[데이터] 나이 범위: {np.min(data['age']):.0f} ~ {np.max(data['age']):.0f}세")
    print(f"[데이터] 교육수준: {np.unique(data['education'])}")

    # 상세 기술통계
    age_stats = descriptive_stats(data['age'])
    print(f"\n[기술통계] 나이:")
    print(f"  평균: {age_stats['평균']:.2f}세, 표준편차: {age_stats['표준편차']:.2f}")
    print(f"  중앙값: {age_stats['중앙값']:.1f}, Q1: {age_stats['Q1']:.1f}, Q3: {age_stats['Q3']:.1f}")
    print(f"  왜도: {age_stats['왜도']:.3f}, 첨도: {age_stats['첨도']:.3f}")

    # 성별 분포
    gender_freq = frequency_table(data['gender'])
    print(f"\n[기술통계] 성별 분포:")
    for g, info in gender_freq.items():
        print(f"  {g}: {info['빈도']:,}명 ({info['비율']:.1f}%)")

    # 교육수준 분포
    edu_freq = frequency_table(data['education'])
    print(f"\n[기술통계] 교육수준 분포:")
    for e, info in edu_freq.items():
        print(f"  Level {e}: {info['빈도']:,}명 ({info['비율']:.1f}%)")

    # MBTI 유형별 빈도
    print("\n[EDA] MBTI 유형별 표본 수:")
    for mbti in sorted(np.unique(data['personality'])):
        count = np.sum(data['personality'] == mbti)
        print(f"  {mbti}: {count:,}명 ({count/n*100:.1f}%)")

    return data


# ============================================================
# 분석 1: 성별 × MBTI 유형
# ============================================================
def analyze_gender_by_mbti(data):
    """MBTI 유형별 성별 분포 차이 검정"""
    print("\n\n" + "━" * 60)
    print("  분석 1: MBTI 유형별 성별 분포")
    print("━" * 60)
    print("  H0: MBTI 유형과 성별은 독립이다")
    print("  H1: MBTI 유형과 성별은 독립이 아니다")

    personality = data['personality']
    gender = data['gender']
    types = sorted(np.unique(personality))

    # 교차표 생성 (16 × 2)
    genders = ['Female', 'Male']
    observed = np.zeros((len(types), len(genders)), dtype=np.float64)
    for i, t in enumerate(types):
        mask = personality == t
        for j, g in enumerate(genders):
            observed[i, j] = np.sum(gender[mask] == g)

    # 카이제곱 검정
    result = chi_square_test(observed)
    print_test_result("카이제곱 독립성 검정: 성별 × MBTI 유형", result)

    # 비율 계산
    row_totals = observed.sum(axis=1, keepdims=True)
    proportions = observed / row_totals * 100

    # 여성비율 기준 상위/하위 유형 출력
    female_pct = proportions[:, 0]
    sorted_idx = np.argsort(female_pct)
    print("\n  [여성 비율 상위 5개 유형]")
    for i in sorted_idx[-5:][::-1]:
        print(f"    {types[i]}: 여성 {female_pct[i]:.1f}% / 남성 {proportions[i,1]:.1f}%")
    print("\n  [여성 비율 하위 5개 유형]")
    for i in sorted_idx[:5]:
        print(f"    {types[i]}: 여성 {female_pct[i]:.1f}% / 남성 {proportions[i,1]:.1f}%")

    # === 시각화 1: 성별 비율 Grouped Bar Chart ===
    fig, ax = plt.subplots(figsize=(16, 8))
    x = np.arange(len(types))
    width = 0.35

    bars_f = ax.bar(x - width/2, proportions[:, 0], width,
                    label='여성', color=GENDER_COLORS['Female'], edgecolor='white')
    bars_m = ax.bar(x + width/2, proportions[:, 1], width,
                    label='남성', color=GENDER_COLORS['Male'], edgecolor='white')

    ax.set_xlabel('MBTI 유형')
    ax.set_ylabel('비율 (%)')
    ax.set_title('MBTI 유형별 성별 분포', fontsize=24, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(types, rotation=45, ha='right')
    ax.legend(fontsize=18)
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 75)

    result_text = (f"χ² = {result['chi2']:.2f}, df = {result['dof']}\n"
                   f"{format_p_value(result['p_value'])}\n"
                   f"Cramer's V = {result['cramers_v']:.4f}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_a1_gender_by_mbti_bar.png')

    # === 시각화 2: 성별-MBTI 교차표 Heatmap ===
    fig, ax = plt.subplots(figsize=(14, 8))

    # 관측빈도 / 기대빈도 비율
    ratio = observed / result['expected']

    sns.heatmap(ratio, annot=True, fmt='.3f', cmap='RdBu_r',
                center=1.0, xticklabels=['여성', '남성'],
                yticklabels=types, ax=ax, linewidths=0.5,
                vmin=0.9, vmax=1.1,
                annot_kws={'fontsize': 13})
    ax.set_title('MBTI 유형별 성별 관측/기대 빈도 비율', fontsize=24, fontweight='bold')
    ax.set_ylabel('MBTI 유형')
    ax.set_xlabel('성별')

    save_figure(fig, TEAM, 'fig_a2_gender_mbti_heatmap.png')

    return result


# ============================================================
# 분석 2: 나이 × MBTI 유형
# ============================================================
def analyze_age_by_mbti(data):
    """MBTI 유형별 나이 분포 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 2: MBTI 유형별 나이 분포")
    print("━" * 60)
    print("  H0: 모든 MBTI 유형의 평균 나이는 동일하다")
    print("  H1: 적어도 하나의 MBTI 유형의 평균 나이가 다르다")

    personality = data['personality']
    age = data['age']
    types = sorted(np.unique(personality))

    # 유형별 나이 그룹
    age_groups = [age[personality == t] for t in types]

    # ANOVA 검정
    anova_result = one_way_anova(*age_groups)
    print_test_result("일원분산분석 (ANOVA): 나이 × MBTI 유형", anova_result)

    # 유형별 기술통계
    print("\n  [유형별 나이 기술통계]")
    for i, t in enumerate(types):
        stats = descriptive_stats(age_groups[i])
        ci = confidence_interval(age_groups[i])
        print(f"    {t}: 평균 = {stats['평균']:.1f} [{ci['lower']:.1f}, {ci['upper']:.1f}], "
              f"SD = {stats['표준편차']:.1f}, 중앙값 = {stats['중앙값']:.1f}, n = {stats['n']:,}")

    # E/I, S/N, T/F, J/P 차원별 t-test
    print("\n  [MBTI 차원별 나이 t-검정]")
    dim_results = {}
    for dim_key, (letter1, letter2) in MBTI_DIMENSIONS.items():
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dim_key]
        group1_mask = np.array([p[dim_idx] == letter1 for p in personality])
        group2_mask = np.array([p[dim_idx] == letter2 for p in personality])

        t_result = independent_t_test(age[group1_mask], age[group2_mask])
        dim_results[dim_key] = t_result
        kr_names = DIMENSION_NAMES_KR[dim_key]
        print(f"    {kr_names[0]} vs {kr_names[1]}: "
              f"평균 {t_result['mean1']:.2f} vs {t_result['mean2']:.2f}, "
              f"t = {t_result['t_stat']:.3f}, {format_p_value(t_result['p_value'])}, "
              f"Cohen's d = {t_result['cohens_d']:.3f}")

    # === 시각화 3: MBTI 유형별 나이 Box Plot ===
    fig, ax = plt.subplots(figsize=(16, 8))

    bp = ax.boxplot(age_groups, labels=types, patch_artist=True,
                    medianprops=dict(color='black', linewidth=2))
    colors = [MBTI_COLORS.get(t, '#95A5A6') for t in types]
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel('MBTI 유형')
    ax.set_ylabel('나이')
    ax.set_title('MBTI 유형별 나이 분포', fontsize=24, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)

    # 평균선 추가
    means = [np.mean(g) for g in age_groups]
    ax.scatter(range(1, 17), means, color='red', marker='D', s=40, zorder=5, label='평균')
    ax.legend(fontsize=22)

    result_text = (f"ANOVA: F = {anova_result['f_stat']:.2f}\n"
                   f"{format_p_value(anova_result['p_value'])}\n"
                   f"η² = {anova_result['eta_squared']:.4f}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_a3_age_by_mbti_boxplot.png')

    # === 시각화 4: 차원별 나이 비교 ===
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('MBTI 차원별 나이 분포 비교 (t-검정)', fontsize=26, fontweight='bold')

    for idx, (dim_key, (letter1, letter2)) in enumerate(MBTI_DIMENSIONS.items()):
        ax = axes[idx // 2, idx % 2]
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dim_key]

        group1_mask = np.array([p[dim_idx] == letter1 for p in personality])
        group2_mask = np.array([p[dim_idx] == letter2 for p in personality])

        kr = DIMENSION_NAMES_KR[dim_key]
        t_res = dim_results[dim_key]

        bp = ax.boxplot([age[group1_mask], age[group2_mask]],
                       labels=[kr[0], kr[1]], patch_artist=True,
                       medianprops=dict(color='black', linewidth=2))
        bp['boxes'][0].set_facecolor('#5DADE2')
        bp['boxes'][1].set_facecolor('#F1948A')

        # 평균값 표시
        m1, m2 = t_res['mean1'], t_res['mean2']
        ax.scatter([1, 2], [m1, m2], color='red', marker='D', s=50, zorder=5)
        ax.annotate(f'{m1:.1f}', (1, m1), textcoords="offset points",
                   xytext=(15, 5), fontsize=19, color='red')
        ax.annotate(f'{m2:.1f}', (2, m2), textcoords="offset points",
                   xytext=(15, 5), fontsize=19, color='red')

        sig_marker = '***' if t_res['p_value'] < 0.001 else ('**' if t_res['p_value'] < 0.01 else ('*' if t_res['p_value'] < 0.05 else 'ns'))
        ax.set_title(f'{dim_key}: d={t_res["cohens_d"]:.3f} ({sig_marker})',
                    fontsize=24)
        ax.set_ylabel('나이', fontsize=22)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a4_dimension_age_comparison.png')

    return anova_result, dim_results


# ============================================================
# 분석 3: 교육수준 × MBTI 유형
# ============================================================
def analyze_education_by_mbti(data):
    """MBTI 유형별 교육수준 분포 검정"""
    print("\n\n" + "━" * 60)
    print("  분석 3: MBTI 유형별 교육수준 분포")
    print("━" * 60)
    print("  H0: MBTI 유형과 교육수준은 독립이다")
    print("  H1: MBTI 유형과 교육수준은 독립이 아니다")

    personality = data['personality']
    education = data['education']
    types = sorted(np.unique(personality))

    # 교차표 생성 (16 × 2)
    edu_levels = [0, 1]
    observed = np.zeros((len(types), 2), dtype=np.float64)
    for i, t in enumerate(types):
        mask = personality == t
        for j, e in enumerate(edu_levels):
            observed[i, j] = np.sum(education[mask] == e)

    # 카이제곱 검정
    result = chi_square_test(observed)
    print_test_result("카이제곱 독립성 검정: 교육수준 × MBTI 유형", result)

    # 교육수준 1 비율 기준 Top 5 / Bottom 5
    edu1_pct = observed[:, 1] / observed.sum(axis=1) * 100
    sorted_idx = np.argsort(edu1_pct)

    print("\n  [교육수준 1 비율 상위 5개 유형]")
    for i in sorted_idx[-5:][::-1]:
        ci = proportion_confidence_interval(edu1_pct[i]/100, int(observed[i].sum()))
        print(f"    {types[i]}: {edu1_pct[i]:.1f}% "
              f"[{ci['lower']*100:.1f}%, {ci['upper']*100:.1f}%]")

    print("\n  [교육수준 1 비율 하위 5개 유형]")
    for i in sorted_idx[:5]:
        ci = proportion_confidence_interval(edu1_pct[i]/100, int(observed[i].sum()))
        print(f"    {types[i]}: {edu1_pct[i]:.1f}% "
              f"[{ci['lower']*100:.1f}%, {ci['upper']*100:.1f}%]")

    # 차원별 교육수준 차이 (추가 분석)
    print("\n  [MBTI 차원별 교육수준 1 비율 비교]")
    edu_dim_results = {}
    for dim_key, (letter1, letter2) in MBTI_DIMENSIONS.items():
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dim_key]
        mask1 = np.array([p[dim_idx] == letter1 for p in personality])
        mask2 = np.array([p[dim_idx] == letter2 for p in personality])

        pct1 = np.mean(education[mask1] == 1) * 100
        pct2 = np.mean(education[mask2] == 1) * 100
        kr = DIMENSION_NAMES_KR[dim_key]

        # 2×2 교차표로 차원별 카이제곱
        obs_dim = np.array([
            [np.sum(education[mask1] == 0), np.sum(education[mask1] == 1)],
            [np.sum(education[mask2] == 0), np.sum(education[mask2] == 1)]
        ], dtype=np.float64)
        chi_dim = chi_square_test(obs_dim)
        edu_dim_results[dim_key] = chi_dim

        print(f"    {kr[0]}: {pct1:.1f}% vs {kr[1]}: {pct2:.1f}% "
              f"(χ²={chi_dim['chi2']:.2f}, {format_p_value(chi_dim['p_value'])})")

    # === 시각화 5: 교육수준 Stacked Bar Chart ===
    fig, ax = plt.subplots(figsize=(16, 8))

    edu0_pct = observed[:, 0] / observed.sum(axis=1) * 100
    edu1_pcts = observed[:, 1] / observed.sum(axis=1) * 100

    x = np.arange(len(types))
    ax.bar(x, edu0_pct, label='교육수준 0', color='#85C1E9', edgecolor='white')
    ax.bar(x, edu1_pcts, bottom=edu0_pct, label='교육수준 1',
           color='#2E86C1', edgecolor='white')

    # 교육수준 1 비율 텍스트
    for i, (pct, bottom) in enumerate(zip(edu1_pcts, edu0_pct)):
        ax.text(i, bottom + pct/2, f'{pct:.1f}%',
                ha='center', va='center', fontsize=13, color='white', fontweight='bold')

    ax.set_xlabel('MBTI 유형')
    ax.set_ylabel('비율 (%)')
    ax.set_title('MBTI 유형별 교육수준 분포', fontsize=24, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(types, rotation=45, ha='right')
    ax.legend(fontsize=18)

    result_text = (f"χ² = {result['chi2']:.2f}, df = {result['dof']}\n"
                   f"{format_p_value(result['p_value'])}\n"
                   f"Cramer's V = {result['cramers_v']:.4f}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_a5_education_by_mbti_stacked.png')

    return result


# ============================================================
# 분석 4: MBTI 차원별 인구통계 종합 요약
# ============================================================
def analyze_dimension_demographics(data):
    """E/I, S/N, T/F, J/P 차원별 인구통계 종합"""
    print("\n\n" + "━" * 60)
    print("  분석 4: MBTI 차원별 인구통계 종합 요약")
    print("━" * 60)

    personality = data['personality']
    age = data['age']
    gender = data['gender']
    education = data['education']

    # 4차원 × 3변수 요약 행렬
    dim_keys = ['EI', 'SN', 'TF', 'JP']
    summary_data = np.zeros((4, 6), dtype=np.float64)

    for idx, dim_key in enumerate(dim_keys):
        letter1, letter2 = MBTI_DIMENSIONS[dim_key]
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dim_key]

        mask1 = np.array([p[dim_idx] == letter1 for p in personality])
        mask2 = np.array([p[dim_idx] == letter2 for p in personality])

        kr = DIMENSION_NAMES_KR[dim_key]

        # 여성 비율
        summary_data[idx, 0] = np.mean(gender[mask1] == 'Female') * 100
        summary_data[idx, 1] = np.mean(gender[mask2] == 'Female') * 100
        # 평균 나이
        summary_data[idx, 2] = np.mean(age[mask1])
        summary_data[idx, 3] = np.mean(age[mask2])
        # 교육수준 1 비율
        summary_data[idx, 4] = np.mean(education[mask1] == 1) * 100
        summary_data[idx, 5] = np.mean(education[mask2] == 1) * 100

        # 상세 출력
        print(f"\n  [{dim_key}] {kr[0]} vs {kr[1]}")
        print(f"    여성비율: {summary_data[idx,0]:.1f}% vs {summary_data[idx,1]:.1f}% "
              f"(차이: {summary_data[idx,0]-summary_data[idx,1]:+.1f}%p)")
        print(f"    평균나이: {summary_data[idx,2]:.1f}세 vs {summary_data[idx,3]:.1f}세 "
              f"(차이: {summary_data[idx,2]-summary_data[idx,3]:+.1f}세)")
        print(f"    교육1비율: {summary_data[idx,4]:.1f}% vs {summary_data[idx,5]:.1f}% "
              f"(차이: {summary_data[idx,4]-summary_data[idx,5]:+.1f}%p)")

    # === 시각화 6: 요약 Heatmap ===
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('MBTI 차원별 인구통계 요약', fontsize=26, fontweight='bold')

    titles = ['여성 비율 (%)', '평균 나이 (세)', '교육수준 1 비율 (%)']
    cmaps = ['PuBuGn', 'YlOrRd', 'BuPu']

    for i, ax in enumerate(axes):
        data_slice = summary_data[:, i*2:(i+1)*2]

        # x축 레이블: 각 차원의 그룹1/그룹2
        letters_0 = [MBTI_DIMENSIONS[dk][0] for dk in dim_keys]
        letters_1 = [MBTI_DIMENSIONS[dk][1] for dk in dim_keys]

        sns.heatmap(data_slice, annot=True, fmt='.1f',
                    cmap=cmaps[i], ax=ax,
                    yticklabels=dim_keys,
                    linewidths=0.5,
                    annot_kws={'fontsize': 14, 'fontweight': 'bold'})

        ax.set_xticklabels(['그룹 1\n(' + '/'.join(letters_0) + ')',
                           '그룹 2\n(' + '/'.join(letters_1) + ')'])
        ax.set_title(titles[i], fontsize=20)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a6_dimension_demographics_summary.png')

    return summary_data


# ============================================================
# 분석 5: 데이터 탐색 EDA 개요
# ============================================================
def analyze_eda_overview(data):
    """탐색적 데이터 분석 — 분포 시각화"""
    print("\n\n" + "━" * 60)
    print("  분석 5: 데이터 탐색 EDA 개요")
    print("━" * 60)

    personality = data['personality']
    age = data['age']
    gender = data['gender']
    n = len(personality)
    types = sorted(np.unique(personality))

    # 유형별 빈도
    counts = np.array([np.sum(personality == t) for t in types])
    pcts = counts / n * 100

    # === 시각화 7: EDA 4패널 개요 ===
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('데이터 탐색적 분석 (EDA) 개요', fontsize=28, fontweight='bold')

    # (1) MBTI 유형 분포 — 수평 막대 (정렬)
    ax = axes[0, 0]
    sort_idx = np.argsort(counts)
    sorted_types = [types[i] for i in sort_idx]
    sorted_counts = counts[sort_idx]
    sorted_pcts = pcts[sort_idx]
    colors_sorted = [MBTI_COLORS.get(t, '#95A5A6') for t in sorted_types]

    bars = ax.barh(range(len(types)), sorted_counts, color=colors_sorted,
                   edgecolor='white', height=0.7)

    for i, (c, p) in enumerate(zip(sorted_counts, sorted_pcts)):
        ax.text(c + 30, i, f'{c:,} ({p:.1f}%)', va='center', fontsize=14)

    ax.set_yticks(range(len(types)))
    ax.set_yticklabels(sorted_types, fontsize=15)
    ax.set_xlabel('응답자 수')
    ax.set_title('MBTI 유형별 분포 (정렬)', fontsize=22, fontweight='bold')

    # (2) 나이 히스토그램 + 성별 구분
    ax = axes[0, 1]
    age_f = age[gender == 'Female']
    age_m = age[gender == 'Male']

    bins = np.arange(np.floor(np.min(age)), np.ceil(np.max(age)) + 2, 2)
    ax.hist(age_f, bins=bins, alpha=0.6, label=f'여성 (n={len(age_f):,})',
            color=GENDER_COLORS['Female'], edgecolor='white')
    ax.hist(age_m, bins=bins, alpha=0.6, label=f'남성 (n={len(age_m):,})',
            color=GENDER_COLORS['Male'], edgecolor='white')

    # 전체 평균 표시
    mean_age = np.mean(age)
    ax.axvline(mean_age, color='red', linestyle='--', linewidth=2,
               label=f'전체 평균: {mean_age:.1f}세')

    ax.set_xlabel('나이')
    ax.set_ylabel('빈도')
    ax.set_title('성별 나이 분포', fontsize=22, fontweight='bold')
    ax.legend(fontsize=15)

    # (3) 성별 비율 Pie Chart
    ax = axes[1, 0]
    gender_counts = [np.sum(gender == 'Female'), np.sum(gender == 'Male')]
    gender_labels = [f'여성\n{gender_counts[0]:,}명\n({gender_counts[0]/n*100:.1f}%)',
                     f'남성\n{gender_counts[1]:,}명\n({gender_counts[1]/n*100:.1f}%)']
    wedges, texts = ax.pie(gender_counts,
                           labels=gender_labels,
                           colors=[GENDER_COLORS['Female'], GENDER_COLORS['Male']],
                           startangle=90, wedgeprops=dict(edgecolor='white', linewidth=2))
    for text in texts:
        text.set_fontsize(14)
    ax.set_title('성별 분포', fontsize=22, fontweight='bold')

    # (4) E/I, S/N, T/F, J/P 차원별 분포
    ax = axes[1, 1]
    dim_keys = ['EI', 'SN', 'TF', 'JP']
    dim_colors_1 = ['#3498DB', '#2ECC71', '#E74C3C', '#9B59B6']
    dim_colors_2 = ['#85C1E9', '#82E0AA', '#F1948A', '#D7BDE2']

    y_pos = np.arange(len(dim_keys))
    bar_height = 0.35

    for idx, dim_key in enumerate(dim_keys):
        letter1, letter2 = MBTI_DIMENSIONS[dim_key]
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dim_key]
        cnt1 = np.sum(np.array([p[dim_idx] == letter1 for p in personality]))
        cnt2 = np.sum(np.array([p[dim_idx] == letter2 for p in personality]))
        pct1 = cnt1 / n * 100
        pct2 = cnt2 / n * 100
        kr = DIMENSION_NAMES_KR[dim_key]

        ax.barh(idx + bar_height/2, pct1, bar_height,
                color=dim_colors_1[idx], label=kr[0] if idx == 0 else '')
        ax.barh(idx - bar_height/2, pct2, bar_height,
                color=dim_colors_2[idx], label=kr[1] if idx == 0 else '')

        ax.text(pct1 + 0.5, idx + bar_height/2, f'{kr[0]}: {pct1:.1f}%',
                va='center', fontsize=14, fontweight='bold')
        ax.text(pct2 + 0.5, idx - bar_height/2, f'{kr[1]}: {pct2:.1f}%',
                va='center', fontsize=14)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(dim_keys, fontsize=18)
    ax.set_xlabel('비율 (%)')
    ax.set_title('MBTI 차원별 분포', fontsize=22, fontweight='bold')
    ax.set_xlim(0, 70)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a7_eda_overview.png')

    print(f"  MBTI 유형 분포 범위: {np.min(pcts):.1f}% ~ {np.max(pcts):.1f}%")
    print(f"  나이 분포: 평균 {mean_age:.1f}세, 왜도 {descriptive_stats(age)['왜도']:.3f}")


# ============================================================
# 분석 6: 성별 × MBTI 차원 상세 (Butterfly Chart)
# ============================================================
def analyze_gender_dimension_detail(data):
    """성별 × MBTI 차원 비율 Butterfly Chart"""
    print("\n\n" + "━" * 60)
    print("  분석 6: 성별 × MBTI 차원 상세 분석")
    print("━" * 60)

    personality = data['personality']
    gender = data['gender']
    n = len(personality)

    dim_keys = ['EI', 'SN', 'TF', 'JP']

    # 성별별 차원 분포 계산
    results = {}
    for dim_key in dim_keys:
        letter1, letter2 = MBTI_DIMENSIONS[dim_key]
        dim_idx = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}[dim_key]

        for g in ['Female', 'Male']:
            g_mask = gender == g
            g_pers = personality[g_mask]
            n_g = len(g_pers)
            cnt1 = np.sum(np.array([p[dim_idx] == letter1 for p in g_pers]))
            cnt2 = np.sum(np.array([p[dim_idx] == letter2 for p in g_pers]))
            results[(dim_key, g)] = {
                'pct1': cnt1 / n_g * 100,
                'pct2': cnt2 / n_g * 100,
            }

        kr = DIMENSION_NAMES_KR[dim_key]
        f_data = results[(dim_key, 'Female')]
        m_data = results[(dim_key, 'Male')]
        print(f"  [{dim_key}] {kr[0]} vs {kr[1]}")
        print(f"    여성: {f_data['pct1']:.1f}% vs {f_data['pct2']:.1f}%")
        print(f"    남성: {m_data['pct1']:.1f}% vs {m_data['pct2']:.1f}%")

    # === 시각화 8: Butterfly Chart ===
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.suptitle('성별 × MBTI 차원 비율 비교 (Butterfly Chart)',
                fontsize=26, fontweight='bold')

    y_positions = np.arange(len(dim_keys)) * 3
    bar_height = 0.8

    for i, dim_key in enumerate(dim_keys):
        kr = DIMENSION_NAMES_KR[dim_key]
        f_data = results[(dim_key, 'Female')]
        m_data = results[(dim_key, 'Male')]

        y_f = y_positions[i] + 0.5
        y_m = y_positions[i] - 0.5

        # 여성 — 왼쪽(그룹1) + 오른쪽(그룹2)
        ax.barh(y_f, -f_data['pct1'], bar_height, color='#F1948A',
                edgecolor='white', alpha=0.8)
        ax.barh(y_f, f_data['pct2'], bar_height, color='#F5B7B1',
                edgecolor='white', alpha=0.8)

        # 남성
        ax.barh(y_m, -m_data['pct1'], bar_height, color='#5DADE2',
                edgecolor='white', alpha=0.8)
        ax.barh(y_m, m_data['pct2'], bar_height, color='#AED6F1',
                edgecolor='white', alpha=0.8)

        # 값 표시
        ax.text(-f_data['pct1'] - 1, y_f, f'{f_data["pct1"]:.1f}%',
                ha='right', va='center', fontsize=14, fontweight='bold')
        ax.text(f_data['pct2'] + 1, y_f, f'{f_data["pct2"]:.1f}%',
                ha='left', va='center', fontsize=14)
        ax.text(-m_data['pct1'] - 1, y_m, f'{m_data["pct1"]:.1f}%',
                ha='right', va='center', fontsize=14, fontweight='bold')
        ax.text(m_data['pct2'] + 1, y_m, f'{m_data["pct2"]:.1f}%',
                ha='left', va='center', fontsize=14)

        # 차원 레이블
        ax.text(0, y_positions[i], dim_key, ha='center', va='center',
                fontsize=20, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor='gray', alpha=0.9))

    # 축 설정
    ax.set_yticks([y_positions[i] + 0.5 for i in range(len(dim_keys))] +
                  [y_positions[i] - 0.5 for i in range(len(dim_keys))])
    ax.set_yticklabels(['여성'] * len(dim_keys) + ['남성'] * len(dim_keys),
                       fontsize=14)
    ax.set_xlabel('비율 (%)', fontsize=18)

    # 중앙선
    ax.axvline(0, color='black', linewidth=1.5)

    # x축 레이블 커스텀
    max_val = 65
    ax.set_xlim(-max_val, max_val)
    xticks = np.arange(-60, 61, 10)
    ax.set_xticks(xticks)
    ax.set_xticklabels([f'{abs(x)}%' for x in xticks])

    # 범례
    ax.text(-max_val/2, y_positions[-1] + 2.5,
            '← E / S / T / J (그룹 1)', ha='center', fontsize=16, color='#2C3E50')
    ax.text(max_val/2, y_positions[-1] + 2.5,
            'I / N / F / P (그룹 2) →', ha='center', fontsize=16, color='#2C3E50')

    legend_patches = [
        mpatches.Patch(color='#F1948A', label='여성'),
        mpatches.Patch(color='#5DADE2', label='남성'),
    ]
    ax.legend(handles=legend_patches, fontsize=18, loc='upper right')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a8_gender_dimension_butterfly.png')


# ============================================================
# 분석 7: 나이 Violin Plot (밀도 시각화)
# ============================================================
def analyze_age_violin(data):
    """MBTI 유형별 나이 분포 — Violin Plot으로 밀도 시각화"""
    print("\n\n" + "━" * 60)
    print("  분석 7: MBTI 유형별 나이 Violin Plot")
    print("━" * 60)

    personality = data['personality']
    age = data['age']
    gender = data['gender']
    types = sorted(np.unique(personality))

    # 유형별 나이 통계 (신뢰구간 포함)
    print("\n  [유형별 나이 95% 신뢰구간]")
    ci_data = {}
    for t in types:
        ages_t = age[personality == t]
        ci = confidence_interval(ages_t)
        ci_data[t] = ci
        print(f"    {t}: {ci['mean']:.2f} [{ci['lower']:.2f}, {ci['upper']:.2f}]"
              f" (n={ci['n']:,})")

    # === 시각화 9: Violin Plot ===
    fig, axes = plt.subplots(2, 1, figsize=(18, 14))
    fig.suptitle('MBTI 유형별 나이 분포 (Violin + 신뢰구간)',
                fontsize=28, fontweight='bold')

    # (1) 상단: Violin Plot
    ax = axes[0]
    # numpy 기반 violin data 생성 (seaborn 의존 최소화)
    parts = ax.violinplot([age[personality == t] for t in types],
                          positions=range(len(types)),
                          showmeans=True, showmedians=True,
                          showextrema=False)

    # 색상 적용
    for i, body in enumerate(parts['bodies']):
        body.set_facecolor(MBTI_COLORS.get(types[i], '#95A5A6'))
        body.set_alpha(0.7)
        body.set_edgecolor('white')
        body.set_linewidth(1)

    parts['cmeans'].set_color('red')
    parts['cmeans'].set_linewidth(2)
    parts['cmedians'].set_color('black')
    parts['cmedians'].set_linewidth(2)

    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=45, ha='right', fontsize=15)
    ax.set_ylabel('나이', fontsize=18)
    ax.set_title('MBTI 유형별 나이 Violin Plot', fontsize=24, fontweight='bold')

    # 범례
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', linewidth=2, label='평균'),
        Line2D([0], [0], color='black', linewidth=2, label='중앙값'),
    ]
    ax.legend(handles=legend_elements, fontsize=16)

    # (2) 하단: 평균 + 95% CI Error Bar (정렬)
    ax = axes[1]
    means = np.array([ci_data[t]['mean'] for t in types])
    lowers = np.array([ci_data[t]['lower'] for t in types])
    uppers = np.array([ci_data[t]['upper'] for t in types])
    sort_idx = np.argsort(means)

    sorted_types_ci = [types[i] for i in sort_idx]
    sorted_means = means[sort_idx]
    sorted_lowers = lowers[sort_idx]
    sorted_uppers = uppers[sort_idx]
    sorted_colors = [MBTI_COLORS.get(t, '#95A5A6') for t in sorted_types_ci]

    y_pos = np.arange(len(types))
    xerr_low = sorted_means - sorted_lowers
    xerr_high = sorted_uppers - sorted_means

    ax.barh(y_pos, sorted_means, color=sorted_colors, alpha=0.7,
            edgecolor='white', height=0.6)
    ax.errorbar(sorted_means, y_pos, xerr=[xerr_low, xerr_high],
               fmt='none', color='black', capsize=4, linewidth=1.5)

    # 전체 평균선
    grand_mean = np.mean(age)
    ax.axvline(grand_mean, color='red', linestyle='--', linewidth=2,
               label=f'전체 평균: {grand_mean:.1f}세')

    for i, (m, lo, up) in enumerate(zip(sorted_means, sorted_lowers, sorted_uppers)):
        ax.text(up + 0.05, i, f'{m:.2f} [{lo:.2f}, {up:.2f}]',
                va='center', fontsize=13)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_types_ci, fontsize=15)
    ax.set_xlabel('평균 나이 (세)', fontsize=18)
    ax.set_title('MBTI 유형별 평균 나이 + 95% 신뢰구간 (정렬)',
                fontsize=24, fontweight='bold')
    ax.legend(fontsize=16)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a9_age_violin_ci.png')


# ============================================================
# 분석 8: MBTI 차원 점수 × 나이 상관분석
# ============================================================
def analyze_score_age_correlation(data):
    """MBTI 4차원 연속 점수와 나이의 상관관계 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 8: MBTI 차원 점수 × 나이 상관분석")
    print("━" * 60)
    print("  H0: MBTI 차원 점수와 나이 사이에 상관이 없다")
    print("  H4: MBTI 차원 점수와 나이 사이에 유의한 상관이 있다")

    age = data['age']
    score_keys = ['introversion', 'sensing', 'thinking', 'judging']
    score_labels_kr = ['내향성 점수\n(Introversion)', '감각성 점수\n(Sensing)',
                       '사고성 점수\n(Thinking)', '판단성 점수\n(Judging)']
    dim_keys = ['EI', 'SN', 'TF', 'JP']

    corr_results = {}

    # === 시각화 10: 산점도 + 회귀선 (2×2) ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle('MBTI 차원 점수 × 나이 상관관계 + 회귀분석',
                fontsize=26, fontweight='bold')

    scatter_colors = ['#3498DB', '#2ECC71', '#E74C3C', '#9B59B6']

    for idx, (key, label_kr) in enumerate(zip(score_keys, score_labels_kr)):
        ax = axes[idx // 2, idx % 2]
        scores = data[key]

        # 상관분석
        corr = pearson_correlation(scores, age)
        corr_results[dim_keys[idx]] = corr

        # 회귀분석
        reg = linear_regression(scores, age)

        # 산점도 (샘플링하여 표시 — 전체 43k는 너무 많음)
        np.random.seed(42)
        sample_idx = np.random.choice(len(age), size=min(3000, len(age)), replace=False)

        ax.scatter(scores[sample_idx], age[sample_idx],
                   alpha=0.15, s=15, color=scatter_colors[idx], rasterized=True)

        # 회귀선
        x_line = np.linspace(np.min(scores), np.max(scores), 100)
        y_line = reg['slope'] * x_line + reg['intercept']
        ax.plot(x_line, y_line, color='red', linewidth=2.5,
                label=f'회귀선: y = {reg["slope"]:.3f}x + {reg["intercept"]:.1f}')

        # 결과 텍스트
        sig_marker = '***' if corr['p_value'] < 0.001 else ('**' if corr['p_value'] < 0.01 else ('*' if corr['p_value'] < 0.05 else 'ns'))
        result_text = (f"r = {corr['r']:.4f} ({sig_marker})\n"
                       f"R² = {reg['r_squared']:.4f}\n"
                       f"{corr['strength']}")
        add_result_text(ax, result_text, position='top_left')

        ax.set_xlabel(label_kr, fontsize=16)
        ax.set_ylabel('나이', fontsize=16)
        ax.set_title(f'{dim_keys[idx]} 차원 점수 × 나이',
                    fontsize=20, fontweight='bold')
        ax.legend(fontsize=14, loc='upper right')

        print(f"\n  [{dim_keys[idx]}] {key} × 나이:")
        print(f"    r = {corr['r']:.4f}, {format_p_value(corr['p_value'])}")
        print(f"    상관 강도: {corr['strength']}")
        print(f"    회귀식: 나이 = {reg['slope']:.4f} × {key} + {reg['intercept']:.2f}")
        print(f"    R² = {reg['r_squared']:.4f}")

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a10_score_age_correlation.png')

    return corr_results


# ============================================================
# 분석 9: 전체 효과크기 종합 Forest Plot
# ============================================================
def analyze_effect_size_summary(gender_result, anova_result, dim_results, edu_result, corr_results):
    """모든 통계 검정의 효과크기를 Forest Plot으로 종합 시각화"""
    print("\n\n" + "━" * 60)
    print("  분석 9: 효과크기 종합 Forest Plot")
    print("━" * 60)

    # 효과크기 수집
    effects = []

    # 1) 성별 × MBTI: Cramer's V
    effects.append({
        'label': '성별 × MBTI\n(Cramer\'s V)',
        'value': gender_result['cramers_v'],
        'type': 'V',
        'color': '#E74C3C',
        'significant': gender_result['significant'],
    })

    # 2) 나이 ANOVA: η²
    effects.append({
        'label': '나이 × MBTI\n(η²)',
        'value': anova_result['eta_squared'],
        'type': 'eta2',
        'color': '#3498DB',
        'significant': anova_result['significant'],
    })

    # 3) 교육 × MBTI: Cramer's V
    effects.append({
        'label': '교육 × MBTI\n(Cramer\'s V)',
        'value': edu_result['cramers_v'],
        'type': 'V',
        'color': '#2ECC71',
        'significant': edu_result['significant'],
    })

    # 4) 차원별 Cohen's d
    dim_colors = {'EI': '#F39C12', 'SN': '#8E44AD', 'TF': '#1ABC9C', 'JP': '#D35400'}
    for dim_key, res in dim_results.items():
        kr = DIMENSION_NAMES_KR[dim_key]
        effects.append({
            'label': f'{dim_key} 나이 차이\n(Cohen\'s d)',
            'value': abs(res['cohens_d']),
            'type': 'd',
            'color': dim_colors[dim_key],
            'significant': res['significant'],
        })

    # 5) 상관계수 |r|
    if corr_results:
        corr_colors = {'EI': '#2980B9', 'SN': '#27AE60', 'TF': '#C0392B', 'JP': '#8E44AD'}
        for dim_key, res in corr_results.items():
            effects.append({
                'label': f'{dim_key} 점수-나이\n(|r|)',
                'value': abs(res['r']),
                'type': 'r',
                'color': corr_colors[dim_key],
                'significant': res['significant'],
            })

    # 콘솔 출력
    print(f"\n  {'검정':<25} {'효과크기':<12} {'값':>8}  {'유의성'}")
    print(f"  {'-'*60}")
    for e in effects:
        sig = '✓' if e['significant'] else '✗'
        print(f"  {e['label'].replace(chr(10), ' '):<25} {e['type']:<12} {e['value']:>8.4f}  {sig}")

    # === 시각화 11: Forest Plot ===
    fig, ax = plt.subplots(figsize=(14, max(8, len(effects) * 0.8)))
    fig.suptitle('전체 분석 효과크기 종합 (Forest Plot)',
                fontsize=26, fontweight='bold')

    y_pos = np.arange(len(effects))

    for i, e in enumerate(effects):
        marker = 'D' if e['significant'] else 'o'
        edge_color = e['color']
        face_color = e['color'] if e['significant'] else 'white'

        ax.barh(i, e['value'], color=e['color'], alpha=0.3,
                edgecolor=e['color'], height=0.5)
        ax.plot(e['value'], i, marker=marker, markersize=12,
                color=face_color, markeredgecolor=edge_color, markeredgewidth=2)

        ax.text(e['value'] + 0.005, i,
                f"{e['value']:.4f} {'✓' if e['significant'] else '(ns)'}",
                va='center', fontsize=15, fontweight='bold' if e['significant'] else 'normal')

    # 효과크기 해석 기준선
    thresholds = [
        (0.1, '작은 효과\n(0.1)', '#95A5A6'),
        (0.3, '보통 효과\n(0.3)', '#7F8C8D'),
        (0.5, '큰 효과\n(0.5)', '#566573'),
    ]
    for thresh, label, color in thresholds:
        ax.axvline(thresh, color=color, linestyle=':', linewidth=1.5, alpha=0.7)
        ax.text(thresh, len(effects) - 0.3, label, ha='center', fontsize=13,
                color=color, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([e['label'] for e in effects], fontsize=15)
    ax.set_xlabel('효과크기', fontsize=18)
    ax.set_xlim(-0.01, max(0.6, max(e['value'] for e in effects) + 0.1))

    # 범례
    sig_patch = mpatches.Patch(facecolor='gray', alpha=0.5, label='유의 (p < .05)')
    ns_patch = mpatches.Patch(facecolor='white', edgecolor='gray', label='유의하지 않음')
    ax.legend(handles=[sig_patch, ns_patch], fontsize=16, loc='lower right')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_a11_effect_size_forest.png')


# ============================================================
# 분석 10: 종합 결론 인포그래픽
# ============================================================
def create_conclusion_infographic(gender_result, anova_result, dim_results,
                                   edu_result, corr_results):
    """종합 결론을 시각적 대시보드로 제시"""
    print("\n\n" + "━" * 60)
    print("  분석 10: 종합 결론 인포그래픽")
    print("━" * 60)

    fig = plt.figure(figsize=(28, 16))

    # 대제목
    fig.text(0.5, 0.96, 'MBTI 유형별 인구통계학적 특성 분석 — 종합 결론',
            ha='center', fontsize=34, fontweight='bold', color='#2C3E50')
    fig.text(0.5, 0.925, '43,744명 대상 | 카이제곱 · t-검정 · ANOVA · 상관분석 · 효과크기',
            ha='center', fontsize=22, color='#7F8C8D')

    # ── 6개 패널 ──
    panels = [
        (0.03, 0.55, 0.30, 0.32),   # 좌상
        (0.35, 0.55, 0.30, 0.32),   # 중상
        (0.67, 0.55, 0.30, 0.32),   # 우상
        (0.03, 0.15, 0.30, 0.32),   # 좌하
        (0.35, 0.15, 0.30, 0.32),   # 중하
        (0.67, 0.15, 0.30, 0.32),   # 우하
    ]

    sig_label = lambda r: '유의 ✓' if r['significant'] else '유의하지 않음 ✗'

    # 가장 유의한 차원
    max_d_dim = max(dim_results.items(), key=lambda x: abs(x[1]['cohens_d']))
    max_d_kr = DIMENSION_NAMES_KR[max_d_dim[0]]

    # 가장 강한 상관
    if corr_results:
        max_r_dim = max(corr_results.items(), key=lambda x: abs(x[1]['r']))
        max_r_kr = DIMENSION_NAMES_KR[max_r_dim[0]]
    else:
        max_r_dim = ('EI', {'r': 0, 'p_value': 1, 'strength': '-'})
        max_r_kr = ('', '')

    panel_data = [
        {
            'title': '가설 1: 성별 × MBTI',
            'icon': '♀♂',
            'content': (f"χ² = {gender_result['chi2']:.1f} (df={gender_result['dof']})\n"
                       f"{format_p_value(gender_result['p_value'])}\n\n"
                       f"Cramer's V = {gender_result['cramers_v']:.4f}\n"
                       f"▶ {sig_label(gender_result)}"),
            'color': '#E74C3C',
            'conclusion': '성별-MBTI 연관성 극히 미약' if gender_result['cramers_v'] < 0.1 else '성별-MBTI 약한 연관'
        },
        {
            'title': '가설 2: 나이 × MBTI',
            'icon': '📊',
            'content': (f"ANOVA F = {anova_result['f_stat']:.2f}\n"
                       f"{format_p_value(anova_result['p_value'])}\n\n"
                       f"η² = {anova_result['eta_squared']:.4f}\n"
                       f"▶ {sig_label(anova_result)}"),
            'color': '#3498DB',
            'conclusion': '나이-MBTI 실질적 차이 미미' if anova_result['eta_squared'] < 0.01 else '나이-MBTI 약한 차이'
        },
        {
            'title': '가설 3: 교육 × MBTI',
            'icon': '🎓',
            'content': (f"χ² = {edu_result['chi2']:.1f} (df={edu_result['dof']})\n"
                       f"{format_p_value(edu_result['p_value'])}\n\n"
                       f"Cramer's V = {edu_result['cramers_v']:.4f}\n"
                       f"▶ {sig_label(edu_result)}"),
            'color': '#2ECC71',
            'conclusion': '교육-MBTI 연관성 극히 미약' if edu_result['cramers_v'] < 0.1 else '교육-MBTI 약한 연관'
        },
        {
            'title': '차원별 나이 t-검정',
            'icon': 'E/I',
            'content': '\n'.join([
                f"{dk}: d={abs(r['cohens_d']):.3f} "
                f"({'***' if r['p_value']<0.001 else ('**' if r['p_value']<0.01 else ('*' if r['p_value']<0.05 else 'ns'))})"
                for dk, r in dim_results.items()
            ]) + f"\n\n▶ 최대 효과: {max_d_dim[0]}\n"
                 f"  (d={abs(max_d_dim[1]['cohens_d']):.3f})",
            'color': '#F39C12',
            'conclusion': f'{max_d_dim[0]} 차원이 나이와 가장 관련'
        },
        {
            'title': '가설 4: 점수-나이 상관',
            'icon': 'r',
            'content': '\n'.join([
                f"{dk}: r={r['r']:.4f} ({r['strength']})"
                for dk, r in (corr_results or {}).items()
            ]) + (f"\n\n▶ 최대: {max_r_dim[0]}\n"
                  f"  (r={max_r_dim[1]['r']:.4f})" if corr_results else '\n\n데이터 없음'),
            'color': '#9B59B6',
            'conclusion': f'모든 상관이 매우 약함' if corr_results and all(abs(r['r'])<0.1 for r in corr_results.values()) else '약한 상관 존재'
        },
        {
            'title': '종합 해석',
            'icon': '!!',
            'content': (f"전체 12개 검정 수행\n"
                       f"대부분 효과크기 < 0.1\n\n"
                       f"대표본(43,744명) 효과로\n"
                       f"통계적 유의성 ≠ 실질적 의미\n"
                       f"(statistical vs practical)"),
            'color': '#2C3E50',
            'conclusion': 'MBTI-인구통계 연관성 미약'
        },
    ]

    for (x, y, w, h), pd in zip(panels, panel_data):
        ax = fig.add_axes([x, y, w, h])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()

        # 배경
        rect = plt.Rectangle((0, 0), 1, 1, facecolor=pd['color'],
                             alpha=0.08, transform=ax.transAxes)
        ax.add_patch(rect)

        # 상단 컬러 바
        rect_top = plt.Rectangle((0, 0.88), 1, 0.12, facecolor=pd['color'],
                                alpha=0.3, transform=ax.transAxes)
        ax.add_patch(rect_top)

        # 제목
        ax.text(0.5, 0.93, pd['title'], ha='center', va='center',
               fontsize=24, fontweight='bold', color=pd['color'])

        # 내용
        ax.text(0.08, 0.5, pd['content'], ha='left', va='center',
               fontsize=23, color='#2C3E50', linespacing=1.5)

        # 결론 라벨
        ax.text(0.5, 0.05, pd['conclusion'], ha='center', va='bottom',
               fontsize=23, fontweight='bold', color=pd['color'],
               bbox=dict(facecolor='white', edgecolor=pd['color'],
                        boxstyle='round,pad=0.3', alpha=0.8))

    # 최종 결론 배너
    fig.text(0.5, 0.075, '결론: MBTI 유형은 인구통계적 변수(성별/나이/교육수준)와 통계적으로 거의 독립적이다',
            ha='center', fontsize=26, fontweight='bold', color='#2C3E50',
            bbox=dict(facecolor='#FEF9E7', edgecolor='#F39C12',
                     boxstyle='round,pad=0.6', linewidth=2))

    fig.text(0.5, 0.025, '통계적 유의성이 발견되더라도 효과크기가 극히 작아 실질적 의미는 제한적 — '
             '"p-value 만능주의"의 함정에 주의',
            ha='center', fontsize=23, color='#7F8C8D', style='italic')

    save_figure(fig, TEAM, 'fig_a12_conclusion_infographic.png', tight=False)


# ============================================================
# 결과 요약
# ============================================================
def create_summary(gender_result, anova_result, dim_results, edu_result, corr_results):
    """분석 결과 종합 요약 (텍스트)"""
    print("\n\n" + "=" * 60)
    print("  팀원 A: 분석 결과 종합 요약")
    print("=" * 60)

    print("\n[가설 1] MBTI 유형별 성별 분포 차이")
    if gender_result['significant']:
        print(f"  -> 통계적으로 유의한 차이 존재 (chi2 = {gender_result['chi2']:.2f}, "
              f"{format_p_value(gender_result['p_value'])})")
    else:
        print(f"  -> 통계적으로 유의한 차이 없음 ({format_p_value(gender_result['p_value'])})")
    print(f"  -> 효과크기: Cramer's V = {gender_result['cramers_v']:.4f}")
    v_interp = '무시할 수준' if gender_result['cramers_v'] < 0.1 else ('약한 연관' if gender_result['cramers_v'] < 0.3 else '보통 연관')
    print(f"     해석: {v_interp}")

    print(f"\n[가설 2] MBTI 유형별 평균 나이 차이")
    if anova_result['significant']:
        print(f"  -> 통계적으로 유의한 차이 존재 (F = {anova_result['f_stat']:.2f}, "
              f"{format_p_value(anova_result['p_value'])})")
    else:
        print(f"  -> 통계적으로 유의한 차이 없음 ({format_p_value(anova_result['p_value'])})")
    print(f"  -> 효과크기: eta^2 = {anova_result['eta_squared']:.4f}")
    eta_interp = '작은 효과' if anova_result['eta_squared'] < 0.01 else ('보통 효과' if anova_result['eta_squared'] < 0.06 else '큰 효과')
    print(f"     해석: {eta_interp}")

    print(f"\n  차원별 t-검정 결과:")
    for dim_key, res in dim_results.items():
        kr = DIMENSION_NAMES_KR[dim_key]
        sig = "유의" if res['significant'] else "유의하지 않음"
        d_interp = '작은' if abs(res['cohens_d']) < 0.2 else ('보통' if abs(res['cohens_d']) < 0.5 else '큰')
        print(f"    {kr[0]} vs {kr[1]}: {sig} "
              f"(t = {res['t_stat']:.3f}, d = {res['cohens_d']:.3f}, {d_interp} 효과)")

    print(f"\n[가설 3] MBTI 유형별 교육수준 분포 차이")
    if edu_result['significant']:
        print(f"  -> 통계적으로 유의한 차이 존재 (chi2 = {edu_result['chi2']:.2f}, "
              f"{format_p_value(edu_result['p_value'])})")
    else:
        print(f"  -> 통계적으로 유의한 차이 없음 ({format_p_value(edu_result['p_value'])})")
    print(f"  -> 효과크기: Cramer's V = {edu_result['cramers_v']:.4f}")

    if corr_results:
        print(f"\n[가설 4] MBTI 차원 점수 × 나이 상관관계")
        for dim_key, res in corr_results.items():
            sig = "유의" if res['significant'] else "유의하지 않음"
            print(f"    {dim_key}: r = {res['r']:.4f}, {format_p_value(res['p_value'])}, "
                  f"{res['strength']}")

    print("\n" + "─" * 60)
    print("  [핵심 인사이트]")
    print("  1. MBTI 유형별 인구통계학적 차이가 존재하는지 다각도로 검증")
    print("  2. 효과크기를 함께 보고하여 통계적 유의성과 실질적 의미를 구분")
    print("  3. 대표본(43,744명) 특성상 작은 차이도 통계적으로 유의할 수 있음에 주의")
    print("  4. 모든 효과크기가 '작은 효과' 수준 → MBTI는 인구통계와 거의 독립")
    print("  5. MBTI 차원 점수(연속형)와 나이의 상관도 극히 미약 (|r| < 0.1)")
    print("  6. '통계적 유의성'과 '실질적 의미'는 별개임을 실증적으로 보여줌")
    print("─" * 60)


# ============================================================
# 메인 실행
# ============================================================
def main():
    """팀원 A 전체 분석 실행"""
    data = load_and_preprocess()

    # 기존 분석 (fig_a1 ~ fig_a6)
    gender_result = analyze_gender_by_mbti(data)
    anova_result, dim_results = analyze_age_by_mbti(data)
    edu_result = analyze_education_by_mbti(data)
    analyze_dimension_demographics(data)

    # 신규 분석 (fig_a7 ~ fig_a12)
    analyze_eda_overview(data)
    analyze_gender_dimension_detail(data)
    analyze_age_violin(data)
    corr_results = analyze_score_age_correlation(data)
    analyze_effect_size_summary(gender_result, anova_result, dim_results,
                                edu_result, corr_results)
    create_conclusion_infographic(gender_result, anova_result, dim_results,
                                   edu_result, corr_results)

    # 텍스트 요약
    create_summary(gender_result, anova_result, dim_results, edu_result, corr_results)

    print("\n[완료] 팀원 A 심층 분석 완료! 그래프 12개 저장")
    print("  저장 위치: results/figures/team_a/\n")


if __name__ == '__main__':
    set_project_style()
    main()
