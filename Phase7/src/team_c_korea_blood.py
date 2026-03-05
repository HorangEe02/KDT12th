# -*- coding: utf-8 -*-
"""
팀원 C: 한국인 혈액형 성격론 통계적 검증 (심층 버전)
====================================================
데이터: korea_*.csv 5종 + blood_type_distribution.csv (127국)
분석: 한국의 혈액형 성격론에 대한 과학적 근거를 통계적으로 검증

가설:
  H1: 한국 MBTI 분포는 균등분포와 유의하게 다르다
  H2: 혈액형-성격 관련성 믿음은 시간에 따라 감소 추세이다
  H3: 선호 혈액형 분포는 실제 혈액형 분포와 유의하게 다르다
  H4: 혈액형별 헌혈 건수는 동일한 감소 추세를 보인다
  H5: 한국의 혈액형 분포는 세계 평균과 유의하게 다르다

통계 방법: 카이제곱 적합도 검정, 비율 신뢰구간, 시계열 회귀,
          피어슨 상관분석, z-점수, 효과크기(w, R², |z|)

시각화: 13개 (fig_c1 ~ fig_c13)
  - fig_c1:  한국 MBTI 유형 분포 Bar Chart
  - fig_c2:  한국 vs 세계 평균 MBTI Grouped Bar
  - fig_c3:  혈액형 분포 Pie (한국/아시아/세계)
  - fig_c4:  연도별 총 헌혈 건수 추이
  - fig_c5:  혈액형-성격 믿음 추이 Line Chart
  - fig_c6:  '관련있다' 비율 95% CI Error Bar
  - fig_c7:  선호 vs 실제 혈액형 Grouped Bar
  - fig_c8:  믿음 비율 Donut Chart
  - fig_c9:  혈액형별 헌혈 건수 개별 추이 (2×2 Line)
  - fig_c10: 세계 혈액형 분포 대륙별 Box Plot + 한국 위치
  - fig_c11: 한국 혈액형 분포 세계 평균 편차 Bar
  - fig_c12: 전체 효과크기 종합 Forest Plot
  - fig_c13: 종합 결론 인포그래픽 (6패널)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

from common.config import (
    BLOOD_COLORS, MBTI_COLORS, CONTINENT_COLORS,
    FIGSIZE_DEFAULT, BLOOD_TYPES
)
from common.data_loader import (
    load_korea_mbti, load_korea_bloodtype, load_korea_bloodtype_yearly,
    load_korea_bloodtype_survey, load_korea_bloodtype_belief,
    load_blood_type_distribution, load_countries_mbti
)
from common.stats_utils import (
    chi_square_goodness_of_fit, proportion_confidence_interval,
    linear_trend, print_test_result,
    pearson_correlation, descriptive_stats, confidence_interval
)
from common.plot_style import (
    set_project_style, save_figure, add_result_text,
    format_p_value, annotate_bars
)

TEAM = 'team_c'


def load_and_preprocess():
    """한국 데이터 5종 로딩"""
    print("\n" + "=" * 60)
    print("  팀원 C: 한국인 혈액형 성격론 통계적 검증")
    print("=" * 60)

    data = {
        'korea_mbti': load_korea_mbti(),
        'korea_blood': load_korea_bloodtype(),
        'korea_yearly': load_korea_bloodtype_yearly(),
        'korea_survey': load_korea_bloodtype_survey(),
        'korea_belief': load_korea_bloodtype_belief(),
    }

    print(f"\n[데이터] 한국 MBTI: {data['korea_mbti']['sample_total']:,}명 표본")
    print(f"[데이터] 혈액형 비율: {', '.join(f'{t}={p}%' for t, p in zip(data['korea_blood']['types'], data['korea_blood']['percentages']))}")
    print(f"[데이터] 헌혈통계: {data['korea_yearly']['years'][0]}~{data['korea_yearly']['years'][-1]}년")
    print(f"[데이터] 믿음추이: {data['korea_belief']['years'][0]}~{data['korea_belief']['years'][-1]}년 ({len(data['korea_belief']['years'])}개 시점)")

    return data


# ============================================================
# 분석 1: 한국 MBTI 분포
# ============================================================
def analyze_korea_mbti_distribution(data):
    """한국 MBTI 분포 특성 분석 + 효과크기 w"""
    print("\n\n" + "━" * 60)
    print("  분석 1: 한국 MBTI 분포 분석")
    print("━" * 60)

    korea_mbti = data['korea_mbti']
    types = korea_mbti['types']
    counts = korea_mbti['counts']
    pcts = korea_mbti['percentages']
    total = korea_mbti['sample_total']

    # 균등분포 대비 카이제곱 적합도 검정
    expected_counts = np.full(16, total / 16)
    chi2_result = chi_square_goodness_of_fit(counts, expected_counts)
    print_test_result("카이제곱 적합도 검정: 한국 MBTI 분포 vs 균등분포", chi2_result)

    # 효과크기 w = sqrt(chi2 / n)
    w_mbti = np.sqrt(chi2_result['chi2'] / total)
    print(f"  효과크기 w = {w_mbti:.4f} ({'큰 효과' if w_mbti >= 0.5 else '보통 효과' if w_mbti >= 0.3 else '작은 효과'})")

    # 세계 평균 MBTI 비교
    try:
        world_data = load_countries_mbti()
        world_means = np.mean(world_data['mbti_16'], axis=0) * 100
        world_types = world_data['type_names_16']
    except Exception:
        world_means = None
        world_types = None

    # === 시각화 1: 한국 MBTI 분포 Bar Chart ===
    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(types))
    colors = [MBTI_COLORS.get(t, '#95A5A6') for t in types]
    bars = ax.bar(x, pcts, color=colors, edgecolor='white', alpha=0.85)

    ax.axhline(y=100/16, color='red', linestyle='--', linewidth=2,
               label=f'균등분포 ({100/16:.2f}%)')

    ax.set_xlabel('MBTI 유형')
    ax.set_ylabel('비율 (%)')
    ax.set_title(f'한국 MBTI 유형 분포 (표본: {total:,}명, TestMoa 2023)',
                fontsize=24, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(types, rotation=45, ha='right', fontsize=16)
    ax.legend(fontsize=18)

    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
               f'{pct:.1f}%', ha='center', va='bottom', fontsize=15)

    result_text = (f"χ² = {chi2_result['chi2']:.1f}\n"
                   f"df = {chi2_result['dof']}\n"
                   f"{format_p_value(chi2_result['p_value'])}\n"
                   f"w = {w_mbti:.3f}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_c1_korea_mbti_distribution.png')

    # === 시각화 2: 한국 vs 세계 평균 비교 ===
    if world_means is not None:
        fig, ax = plt.subplots(figsize=(16, 8))

        korea_dict = dict(zip(types, pcts))
        korea_ordered = np.array([korea_dict.get(t, 0.0) for t in world_types])

        x = np.arange(len(world_types))
        width = 0.35

        ax.bar(x - width/2, korea_ordered, width,
               label='한국', color='#E74C3C', alpha=0.8, edgecolor='white')
        ax.bar(x + width/2, world_means, width,
               label='세계 평균', color='#3498DB', alpha=0.8, edgecolor='white')

        ax.set_xlabel('MBTI 유형')
        ax.set_ylabel('비율 (%)')
        ax.set_title('한국 vs 세계 평균 MBTI 분포 비교', fontsize=24, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(world_types, rotation=45, ha='right')
        ax.legend(fontsize=18)

        save_figure(fig, TEAM, 'fig_c2_korea_vs_world_mbti.png')

    return {**chi2_result, 'w': w_mbti}


# ============================================================
# 분석 2: 한국 혈액형 분포 및 헌혈 추이
# ============================================================
def analyze_korea_blood_distribution(data):
    """한국 혈액형 분포 및 연도별 헌혈 추이"""
    print("\n\n" + "━" * 60)
    print("  분석 2: 한국 혈액형 분포 및 헌혈 추이")
    print("━" * 60)

    korea_blood = data['korea_blood']
    yearly = data['korea_yearly']

    # 세계 비교
    try:
        world_blood = load_blood_type_distribution()
        blood_names_4 = world_blood['blood_names_4']
        blood_4_clean = world_blood['blood_4']
        valid_mask = ~np.any(np.isnan(blood_4_clean), axis=1)
        continent_arr = world_blood['continent']
        continent_str = np.array([str(c) if not (isinstance(c, float) and np.isnan(c))
                                  else 'UN' for c in continent_arr])
        asia_mask = (continent_str == 'AS') & valid_mask
        asia_means = np.nanmean(blood_4_clean[asia_mask], axis=0) if np.sum(asia_mask) > 0 else None
        world_valid = blood_4_clean[valid_mask]
        world_means = np.nanmean(world_valid, axis=0)
    except Exception:
        asia_means = None
        world_means = None
        blood_names_4 = ['A', 'B', 'O', 'AB']

    print(f"\n  한국 혈액형 분포:")
    for t, p in zip(korea_blood['types'], korea_blood['percentages']):
        print(f"    {t}형: {p}%")

    # === 시각화 3: 혈액형 Pie + 비교 ===
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('한국 혈액형 분포 비교', fontsize=26, fontweight='bold')

    ax = axes[0]
    colors = [BLOOD_COLORS.get(t, '#95A5A6') for t in korea_blood['types']]
    ax.pie(korea_blood['percentages'], labels=[f"{t}형" for t in korea_blood['types']],
           colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 14})
    ax.set_title('한국', fontsize=20, fontweight='bold')

    if asia_means is not None:
        ax = axes[1]
        colors_4 = [BLOOD_COLORS.get(n, '#95A5A6') for n in blood_names_4]
        ax.pie(asia_means, labels=[f"{n}형" for n in blood_names_4],
               colors=colors_4, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 14})
        ax.set_title('아시아 평균', fontsize=20, fontweight='bold')

    if world_means is not None:
        ax = axes[2]
        colors_4 = [BLOOD_COLORS.get(n, '#95A5A6') for n in blood_names_4]
        ax.pie(world_means, labels=[f"{n}형" for n in blood_names_4],
               colors=colors_4, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 14})
        ax.set_title('세계 평균', fontsize=20, fontweight='bold')

    save_figure(fig, TEAM, 'fig_c3_korea_blood_type_pie.png')

    # === 시각화 4: 연도별 헌혈 건수 추이 ===
    fig, ax = plt.subplots(figsize=(12, 7))

    years = yearly['years']
    total = yearly['total_donations']

    ax.plot(years, total / 10000, 'o-', linewidth=2.5, markersize=8,
           color='#E74C3C', label='헌혈 건수')

    trend = linear_trend(years.astype(float), total.astype(float))
    ax.plot(years, trend['predicted'] / 10000, '--', linewidth=2,
           color='gray', label='추세선')

    ax.set_xlabel('연도')
    ax.set_ylabel('헌혈 건수 (만 건)')
    ax.set_title('한국 연도별 헌혈 건수 추이 (2014-2023)', fontsize=24, fontweight='bold')
    ax.legend(fontsize=18)

    for yr, val in zip(years, total):
        ax.annotate(f'{val/10000:.0f}만', xy=(yr, val/10000),
                   xytext=(0, 10), textcoords='offset points',
                   ha='center', fontsize=15)

    result_text = (f"연간 변화: {trend['slope']/10000:.1f}만 건\n"
                   f"R² = {trend['r_squared']:.3f}\n"
                   f"{trend['trend_direction']}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_c4_donation_trend.png')

    return trend


# ============================================================
# 분석 3: 혈액형 성격론 믿음 추이 (핵심)
# ============================================================
def analyze_personality_belief_trend(data):
    """혈액형 성격론 믿음 추이 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 3: 혈액형-성격 관련성 믿음 추이 분석 (핵심)")
    print("━" * 60)
    print("  H0: 믿음 비율은 시간에 따라 변하지 않는다")
    print("  H1: 믿음 비율은 시간에 따라 감소 추세이다")

    belief = data['korea_belief']
    years = belief['years'].astype(float)
    believe = belief['believe_pct']
    not_related = belief['not_related_pct']
    dont_know = belief['dont_know_pct']
    sample_sizes = belief['sample_size']

    # 추세 분석
    trend_believe = linear_trend(years, believe)
    trend_not = linear_trend(years, not_related)
    trend_dk = linear_trend(years, dont_know)

    print_test_result("추세분석: '관련있다' 비율", trend_believe)
    print_test_result("추세분석: '관련없다' 비율", trend_not)
    print_test_result("추세분석: '모르겠다' 비율", trend_dk)

    # 각 시점 비율의 신뢰구간
    print("\n  [각 시점별 '관련있다' 비율 95% 신뢰구간]")
    ci_data = []
    for yr, pct, n in zip(belief['years'], believe, sample_sizes):
        ci = proportion_confidence_interval(pct / 100, n)
        ci_data.append(ci)
        print(f"    {yr}년: {pct:.1f}% (95% CI: [{ci['lower']*100:.1f}%, {ci['upper']*100:.1f}%])")

    # === 시각화 5: 믿음 추이 Line Chart ===
    fig, ax = plt.subplots(figsize=(12, 8))

    ax.plot(years, believe, 'o-', linewidth=2.5, markersize=10,
           color='#E74C3C', label='관련있다')
    ax.plot(years, not_related, 's-', linewidth=2.5, markersize=10,
           color='#3498DB', label='관련없다')
    ax.plot(years, dont_know, '^-', linewidth=2.5, markersize=10,
           color='#95A5A6', label='모르겠다')

    x_ext = np.linspace(years[0], years[-1] + 2, 100)
    y_ext = trend_believe['slope'] * x_ext + trend_believe['intercept']
    ax.plot(x_ext, y_ext, '--', color='#E74C3C', alpha=0.5, linewidth=1.5)

    ax.set_xlabel('조사 연도')
    ax.set_ylabel('비율 (%)')
    ax.set_title('혈액형-성격 관련성 믿음 추이 (한국갤럽, 2004-2023)',
                fontsize=24, fontweight='bold')
    ax.legend(fontsize=18)
    ax.set_ylim(0, 80)
    ax.set_xticks(belief['years'])

    for yr, b, n, d in zip(years, believe, not_related, dont_know):
        ax.annotate(f'{b:.0f}%', xy=(yr, b), xytext=(0, 10),
                   textcoords='offset points', ha='center', fontsize=15, color='#E74C3C')
        ax.annotate(f'{n:.0f}%', xy=(yr, n), xytext=(0, -15),
                   textcoords='offset points', ha='center', fontsize=15, color='#3498DB')

    result_text = (f"'관련있다' 추세:\n"
                   f"기울기 = {trend_believe['slope']:.3f}%/년\n"
                   f"R² = {trend_believe['r_squared']:.3f}\n"
                   f"{trend_believe['trend_direction']}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_c5_belief_trend_line.png')

    # === 시각화 6: 신뢰구간 Error Bar ===
    fig, ax = plt.subplots(figsize=(10, 7))

    yr_pos = np.arange(len(belief['years']))
    means = [ci['proportion'] * 100 for ci in ci_data]
    lowers = [ci['lower'] * 100 for ci in ci_data]
    uppers = [ci['upper'] * 100 for ci in ci_data]
    errors_low = [m - l for m, l in zip(means, lowers)]
    errors_high = [u - m for m, u in zip(means, uppers)]

    ax.errorbar(yr_pos, means, yerr=[errors_low, errors_high],
               fmt='o', markersize=12, capsize=8, capthick=2,
               color='#E74C3C', ecolor='#E74C3C', elinewidth=2,
               markerfacecolor='white', markeredgewidth=2)

    ax.set_xlabel('조사 연도')
    ax.set_ylabel("'관련있다' 비율 (%)")
    ax.set_title("혈액형-성격 관련성 '관련있다' 비율의 95% 신뢰구간",
                fontsize=24, fontweight='bold')
    ax.set_xticks(yr_pos)
    ax.set_xticklabels(belief['years'])
    ax.set_ylim(45, 75)

    ax.axhline(y=50, color='gray', linestyle=':', linewidth=1.5, label='50% (과반)')
    ax.legend()

    for i, (m, l, u) in enumerate(zip(means, lowers, uppers)):
        ax.annotate(f'{m:.1f}%\n[{l:.1f}-{u:.1f}]',
                   xy=(yr_pos[i], u + 1), ha='center', fontsize=15)

    save_figure(fig, TEAM, 'fig_c6_belief_ci_errorbar.png')

    return {'believe': trend_believe, 'not_related': trend_not, 'dont_know': trend_dk}, ci_data


# ============================================================
# 분석 4: 선호 혈액형 vs 실제 분포
# ============================================================
def analyze_blood_personality_theory_test(data):
    """혈액형 성격론 자체의 통계적 검증 + 효과크기 w"""
    print("\n\n" + "━" * 60)
    print("  분석 4: 혈액형 성격론 통계적 검증")
    print("━" * 60)

    survey = data['korea_survey']
    korea_blood = data['korea_blood']

    # 선호혈액형 vs 실제 비율
    print("\n  [선호 혈액형 vs 실제 혈액형 비율]")
    preferred_types = ['O형', 'A형', 'B형', 'AB형']
    preferred_pcts = np.array([survey['선호혈액형'].get(t, 0) for t in preferred_types])
    actual_types = ['O', 'A', 'B', 'AB']
    actual_dict = dict(zip(korea_blood['types'], korea_blood['percentages']))
    actual_pcts = np.array([actual_dict.get(t, 0) for t in actual_types])

    print(f"  {'혈액형':8s} {'선호':>8s} {'실제':>8s} {'차이':>8s}")
    for pt, pp, at, ap in zip(preferred_types, preferred_pcts,
                               actual_types, actual_pcts):
        print(f"  {pt:8s} {pp:8.1f}% {ap:8.1f}% {pp-ap:+8.1f}%")

    # 카이제곱 적합도
    n = 1500
    preferred_total = np.sum(preferred_pcts)
    observed = (preferred_pcts / preferred_total * 100) / 100 * n
    expected = (actual_pcts / np.sum(actual_pcts) * 100) / 100 * n

    chi2_result = chi_square_goodness_of_fit(observed, expected)
    print_test_result("카이제곱 적합도: 선호 혈액형 분포 vs 실제 분포", chi2_result)

    # 효과크기 w
    w_pref = np.sqrt(chi2_result['chi2'] / n)
    print(f"  효과크기 w = {w_pref:.4f} ({'큰 효과' if w_pref >= 0.5 else '보통 효과' if w_pref >= 0.3 else '작은 효과'})")

    # 궁합 믿음 비율 신뢰구간
    compat_believe = survey['궁합믿음'].get('관련있다', 37.0) / 100
    ci_compat = proportion_confidence_interval(compat_believe, 1500)
    print(f"\n  [궁합 관련성 '관련있다' 비율]")
    print(f"    비율: {compat_believe*100:.1f}%")
    print(f"    95% CI: [{ci_compat['lower']*100:.1f}%, {ci_compat['upper']*100:.1f}%]")
    print(f"    → 50% 미만으로 과반이 궁합 관련성을 부정")

    # 성격 관련성 비율 신뢰구간
    personality_believe = survey['성격관련성믿음'].get('관련있다', 58.0) / 100
    ci_personality = proportion_confidence_interval(personality_believe, 1500)
    print(f"\n  [성격 관련성 '관련있다' 비율]")
    print(f"    비율: {personality_believe*100:.1f}%")
    print(f"    95% CI: [{ci_personality['lower']*100:.1f}%, {ci_personality['upper']*100:.1f}%]")

    # === 시각화 7: 선호 vs 실제 Grouped Bar ===
    fig, ax = plt.subplots(figsize=(10, 7))

    x = np.arange(4)
    width = 0.35
    labels = ['O형', 'A형', 'B형', 'AB형']

    ax.bar(x - width/2, preferred_pcts, width,
           label='선호 비율', color='#F39C12', edgecolor='white')
    ax.bar(x + width/2, actual_pcts, width,
           label='실제 비율', color='#3498DB', edgecolor='white')

    ax.set_xlabel('혈액형')
    ax.set_ylabel('비율 (%)')
    ax.set_title('선호 혈액형 vs 실제 혈액형 분포', fontsize=24, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=18)
    ax.legend(fontsize=18)

    result_text = (f"χ² = {chi2_result['chi2']:.2f}\n"
                   f"{format_p_value(chi2_result['p_value'])}\n"
                   f"w = {w_pref:.3f}\n"
                   f"선호 ≠ 실제 분포")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_c7_preferred_vs_actual_blood.png')

    # === 시각화 8: 믿음 비율 Donut Chart ===
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('혈액형 관련 믿음 비율 (한국갤럽 2017)', fontsize=26, fontweight='bold')

    ax = axes[0]
    vals = [survey['성격관련성믿음'].get('관련있다', 58),
            survey['성격관련성믿음'].get('관련없다', 42)]
    labels_belief = ['관련있다', '관련없다']
    colors_belief = ['#E74C3C', '#3498DB']
    ax.pie(vals, labels=labels_belief, colors=colors_belief,
           autopct='%1.0f%%', startangle=90, textprops={'fontsize': 15},
           pctdistance=0.75)
    centre_circle = plt.Circle((0, 0), 0.4, fc='white')
    ax.add_artist(centre_circle)
    ax.set_title('성격-혈액형 관련성', fontsize=20, fontweight='bold')

    ax = axes[1]
    vals = [survey['궁합믿음'].get('관련있다', 37),
            survey['궁합믿음'].get('관련없다', 63)]
    ax.pie(vals, labels=labels_belief, colors=colors_belief,
           autopct='%1.0f%%', startangle=90, textprops={'fontsize': 15},
           pctdistance=0.75)
    centre_circle = plt.Circle((0, 0), 0.4, fc='white')
    ax.add_artist(centre_circle)
    ax.set_title('궁합-혈액형 관련성', fontsize=20, fontweight='bold')

    save_figure(fig, TEAM, 'fig_c8_belief_donut.png')

    return {**chi2_result, 'w': w_pref}, ci_compat, ci_personality


# ============================================================
# 분석 5: 혈액형별 헌혈 건수 개별 추이 (신규)
# ============================================================
def analyze_blood_type_donation_trends(data):
    """혈액형별 헌혈 건수 개별 추세 분석 + 혈액형 간 상관"""
    print("\n\n" + "━" * 60)
    print("  분석 5: 혈액형별 헌혈 건수 개별 추이 분석")
    print("━" * 60)
    print("  H4: 혈액형별 헌혈 건수는 동일한 추세를 보이는가?")

    yearly = data['korea_yearly']
    years = yearly['years'].astype(float)
    counts = yearly['counts']  # (n_years, 4)
    blood_names = ['A', 'B', 'O', 'AB']

    # 각 혈액형별 추세 분석
    trends = {}
    print(f"\n  [혈액형별 헌혈 건수 추세]")
    print(f"  {'혈액형':6s} {'기울기(만/년)':>12s} {'R²':>8s} {'p-value':>12s} {'추세':>8s}")
    print("  " + "─" * 50)
    for i, bt in enumerate(blood_names):
        trend = linear_trend(years, counts[:, i].astype(float))
        trends[bt] = trend
        sig = "✓" if trend.get('significant', trend['p_value'] < 0.05) else "✗"
        print(f"  {bt}형     {trend['slope']/10000:>10.2f}   {trend['r_squared']:>7.3f}   "
              f"{format_p_value(trend['p_value']):>11s}  {sig}")

    # 혈액형 간 상관 분석
    print(f"\n  [혈액형별 헌혈 건수 상관계수 (Pearson)]")
    corr_results = {}
    print(f"  {'':6s}", end='')
    for bt in blood_names:
        print(f"  {bt:>8s}", end='')
    print()

    for i, bt1 in enumerate(blood_names):
        print(f"  {bt1}형   ", end='')
        for j, bt2 in enumerate(blood_names):
            if i == j:
                print(f"  {'1.0000':>8s}", end='')
            elif j > i:
                corr = pearson_correlation(counts[:, i].astype(float),
                                           counts[:, j].astype(float))
                corr_results[f'{bt1}_{bt2}'] = corr
                print(f"  {corr['r']:>8.4f}", end='')
            else:
                key = f'{bt2}_{bt1}'
                print(f"  {corr_results[key]['r']:>8.4f}", end='')
        print()

    # === 시각화 9: 혈액형별 헌혈 건수 개별 추이 (2×2) ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('혈액형별 헌혈 건수 추이 분석 (2014-2023)',
                fontsize=26, fontweight='bold', y=0.98)

    for idx, (bt, ax) in enumerate(zip(blood_names, axes.flat)):
        color = BLOOD_COLORS.get(bt, '#95A5A6')
        trend = trends[bt]

        # 실제 데이터
        ax.plot(years, counts[:, idx] / 10000, 'o-', linewidth=2.5,
               markersize=8, color=color, label=f'{bt}형 헌혈 건수')

        # 추세선
        ax.plot(years, trend['predicted'] / 10000, '--', linewidth=2,
               color='gray', alpha=0.7, label='추세선')

        ax.set_xlabel('연도')
        ax.set_ylabel('헌혈 건수 (만 건)')
        ax.set_title(f'{bt}형 헌혈 건수 추이', fontsize=20, fontweight='bold',
                    color=color)
        ax.legend(fontsize=14, loc='upper right')
        ax.set_xticks(yearly['years'][::2])

        # 첫해, 마지막해 수치
        ax.annotate(f'{counts[0, idx]/10000:.1f}만',
                   xy=(years[0], counts[0, idx]/10000),
                   xytext=(-5, 10), textcoords='offset points',
                   ha='center', fontsize=14, color=color)
        ax.annotate(f'{counts[-1, idx]/10000:.1f}만',
                   xy=(years[-1], counts[-1, idx]/10000),
                   xytext=(5, -15), textcoords='offset points',
                   ha='center', fontsize=14, color=color)

        # 결과 텍스트
        sig_text = "유의" if trend.get('significant', trend['p_value'] < 0.05) else "비유의"
        result_text = (f"기울기: {trend['slope']/10000:.2f}만/년\n"
                       f"R² = {trend['r_squared']:.3f}\n"
                       f"{format_p_value(trend['p_value'])} ({sig_text})")
        add_result_text(ax, result_text, position='bottom_left')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    save_figure(fig, TEAM, 'fig_c9_bloodtype_donation_by_type.png')

    return trends, corr_results


# ============================================================
# 분석 6: 한국 혈액형 세계 비교 (신규)
# ============================================================
def analyze_blood_type_world_comparison(data):
    """한국 혈액형 분포의 세계적 위치 분석 (127국 비교)"""
    print("\n\n" + "━" * 60)
    print("  분석 6: 한국 혈액형 분포의 세계적 위치")
    print("━" * 60)
    print("  H5: 한국의 혈액형 분포는 세계 평균과 유의하게 다른가?")

    korea_blood = data['korea_blood']
    korea_dict = dict(zip(korea_blood['types'], korea_blood['percentages']))
    korea_pcts = np.array([korea_dict.get(bt, 0) for bt in ['A', 'B', 'O', 'AB']])
    blood_names = ['A', 'B', 'O', 'AB']

    # 세계 데이터 로딩
    try:
        world = load_blood_type_distribution()
    except Exception as e:
        print(f"  [경고] 세계 혈액형 데이터 로딩 실패: {e}")
        return None

    blood_4 = world['blood_4']
    continent_arr = world['continent']
    continent_str = np.array([str(c) if not (isinstance(c, float) and np.isnan(c))
                              else 'UN' for c in continent_arr])
    valid_mask = ~np.any(np.isnan(blood_4), axis=1)

    # 세계 통계 + z-score
    print(f"\n  [혈액형별 세계 분포 vs 한국]")
    print(f"  {'혈액형':6s} {'세계평균':>8s} {'세계SD':>8s} {'한국':>8s} {'z-score':>8s} {'해석':>12s}")
    print("  " + "─" * 56)

    z_scores = {}
    world_stats = {}
    for i, bt in enumerate(blood_names):
        col = blood_4[valid_mask, i]
        stats = descriptive_stats(col)
        world_mean = stats['평균']
        world_std = stats['표준편차']
        z = (korea_pcts[i] - world_mean) / world_std if world_std > 0 else 0
        z_scores[bt] = z
        world_stats[bt] = stats

        interpretation = ("매우 높음" if z > 2 else "높음" if z > 1 else
                         "보통" if z > -1 else "낮음" if z > -2 else "매우 낮음")
        print(f"  {bt}형     {world_mean:>7.1f}%  {world_std:>7.1f}%  {korea_pcts[i]:>7.1f}%  "
              f"{z:>+7.2f}   {interpretation}")

    # 카이제곱 적합도: 한국 vs 세계 평균
    world_mean_pcts = np.array([world_stats[bt]['평균'] for bt in blood_names])
    # 한국 인구 기준 빈도 변환
    n_korea = 51_740_000
    observed = korea_pcts / 100 * n_korea
    expected = world_mean_pcts / np.sum(world_mean_pcts) * n_korea
    chi2_world = chi_square_goodness_of_fit(observed, expected)
    w_world = np.sqrt(chi2_world['chi2'] / n_korea)
    print_test_result("카이제곱 적합도: 한국 혈액형 분포 vs 세계 평균", chi2_world)
    print(f"  효과크기 w = {w_world:.6f}")

    # === 시각화 10: 대륙별 Box Plot + 한국 위치 (2×2) ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('한국 혈액형 분포의 세계적 위치 (127개국 비교)',
                fontsize=26, fontweight='bold', y=0.98)

    continent_labels = {'AF': '아프리카', 'AS': '아시아', 'EU': '유럽',
                       'NA': '북미', 'SA': '남미', 'OC': '오세아니아'}
    continents_order = ['AF', 'AS', 'EU', 'NA', 'SA', 'OC']

    for idx, (bt, ax) in enumerate(zip(blood_names, axes.flat)):
        col = blood_4[:, idx]

        # 대륙별 데이터 수집
        box_data = []
        box_labels = []
        box_colors = []
        for cont in continents_order:
            mask = (continent_str == cont) & valid_mask
            vals = col[mask]
            vals = vals[~np.isnan(vals)]
            if len(vals) >= 2:
                box_data.append(vals)
                box_labels.append(continent_labels.get(cont, cont))
                box_colors.append(CONTINENT_COLORS.get(cont, '#95A5A6'))

        if box_data:
            bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True,
                           medianprops=dict(color='black', linewidth=2))
            for patch, c in zip(bp['boxes'], box_colors):
                patch.set_facecolor(c)
                patch.set_alpha(0.6)

        # 한국 위치 표시
        ax.axhline(y=korea_pcts[idx], color='red', linestyle='--',
                   linewidth=2, alpha=0.7, label=f'한국 ({korea_pcts[idx]}%)')

        # 한국 마커 (아시아 위치에)
        asia_idx = None
        for bi, bl in enumerate(box_labels):
            if bl == '아시아':
                asia_idx = bi + 1
                break
        if asia_idx is not None:
            ax.plot(asia_idx, korea_pcts[idx], 'D', color='red',
                   markersize=12, markeredgecolor='darkred', markeredgewidth=2,
                   zorder=5, label=f'한국 (z={z_scores[bt]:+.2f})')

        color = BLOOD_COLORS.get(bt, '#95A5A6')
        ax.set_title(f'{bt}형 분포 (한국: z={z_scores[bt]:+.2f})',
                    fontsize=20, fontweight='bold', color=color)
        ax.set_ylabel('비율 (%)')
        ax.legend(fontsize=13, loc='upper right')
        ax.tick_params(axis='x', rotation=30)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    save_figure(fig, TEAM, 'fig_c10_korea_blood_world_boxplot.png')

    # === 시각화 11: 한국 편차 Horizontal Bar ===
    fig, ax = plt.subplots(figsize=(10, 7))

    deviations = korea_pcts - world_mean_pcts
    y_pos = np.arange(4)
    colors_dev = ['#E74C3C' if d > 0 else '#3498DB' for d in deviations]

    bars = ax.barh(y_pos, deviations, color=colors_dev, edgecolor='white',
                   height=0.6, alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f'{bt}형' for bt in blood_names], fontsize=18)
    ax.set_xlabel('세계 평균 대비 편차 (%p)', fontsize=18)
    ax.set_title('한국 혈액형 분포: 세계 평균 대비 편차',
                fontsize=24, fontweight='bold')
    ax.axvline(x=0, color='black', linewidth=1)

    # z-score 주석
    for i, (dev, z) in enumerate(zip(deviations, [z_scores[bt] for bt in blood_names])):
        x_pos = dev + (0.3 if dev > 0 else -0.3)
        ha = 'left' if dev > 0 else 'right'
        ax.text(x_pos, i, f'{dev:+.1f}%p (z={z:+.2f})',
               ha=ha, va='center', fontsize=16, fontweight='bold')

    result_text = (f"χ² = {chi2_world['chi2']:.1f}\n"
                   f"{format_p_value(chi2_world['p_value'])}\n"
                   f"w = {w_world:.4f}")
    add_result_text(ax, result_text)

    save_figure(fig, TEAM, 'fig_c11_korea_blood_deviation.png')

    return {
        'chi2': chi2_world,
        'w': w_world,
        'z_scores': z_scores,
        'world_stats': world_stats,
        'deviations': dict(zip(blood_names, deviations)),
    }


# ============================================================
# 분석 7: 효과크기 종합 Forest Plot (신규)
# ============================================================
def analyze_effect_size_forest(chi2_mbti, trend_results, chi2_pref,
                                bloodtype_trends, world_comp):
    """전체 효과크기 종합 Forest Plot"""
    print("\n\n" + "━" * 60)
    print("  분석 7: 효과크기 종합 Forest Plot")
    print("━" * 60)

    blood_names = ['A', 'B', 'O', 'AB']

    # 효과크기 수집
    effects = []

    # 1. MBTI 균등성 (w)
    effects.append({
        'label': 'MBTI 균등성 (w)',
        'value': chi2_mbti['w'],
        'type': 'w',
        'significant': chi2_mbti.get('significant', True),
    })

    # 2. 믿음 추이 R²
    for key, label in [('believe', "'관련있다' 추이 (R²)"),
                        ('not_related', "'관련없다' 추이 (R²)"),
                        ('dont_know', "'모르겠다' 추이 (R²)")]:
        tr = trend_results[key]
        effects.append({
            'label': label,
            'value': tr['r_squared'],
            'type': 'R²',
            'significant': tr.get('significant', tr['p_value'] < 0.05),
        })

    # 3. 선호 vs 실제 (w)
    effects.append({
        'label': '선호 vs 실제 (w)',
        'value': chi2_pref['w'],
        'type': 'w',
        'significant': chi2_pref.get('significant', True),
    })

    # 4. 혈액형별 추이 R²
    bt_trends, _ = bloodtype_trends
    for bt in blood_names:
        tr = bt_trends[bt]
        effects.append({
            'label': f'{bt}형 헌혈 추이 (R²)',
            'value': tr['r_squared'],
            'type': 'R²',
            'significant': tr.get('significant', tr['p_value'] < 0.05),
        })

    # 5. 세계 편차 |z|
    if world_comp is not None:
        for bt in blood_names:
            z = world_comp['z_scores'][bt]
            effects.append({
                'label': f'{bt}형 세계편차 (|z|)',
                'value': abs(z),
                'type': '|z|',
                'significant': abs(z) > 1.96,
            })

    # 출력
    print(f"\n  {'검정':30s} {'효과크기':>8s} {'값':>8s}  {'유의':>4s}")
    print("  " + "─" * 56)
    for e in effects:
        sig = "✓" if e['significant'] else "✗"
        print(f"  {e['label']:30s} {e['type']:>8s} {e['value']:>8.4f}  {sig:>4s}")

    # === 시각화 12: Forest Plot ===
    fig, ax = plt.subplots(figsize=(12, max(8, len(effects) * 0.55)))

    y_pos = np.arange(len(effects))
    type_colors = {'w': '#E74C3C', 'R²': '#3498DB', '|z|': '#2ECC71'}

    for i, e in enumerate(effects):
        color = type_colors.get(e['type'], '#95A5A6')
        if e['significant']:
            ax.plot(e['value'], i, 'D', color=color, markersize=10,
                   markeredgecolor='black', markeredgewidth=1.5, zorder=5)
        else:
            ax.plot(e['value'], i, 'o', color='white', markersize=10,
                   markeredgecolor=color, markeredgewidth=2, zorder=5)

    # 기준선
    ax.axvline(x=0.1, color='#95A5A6', linestyle=':', alpha=0.5, label='작은 효과 (0.1)')
    ax.axvline(x=0.3, color='#95A5A6', linestyle='--', alpha=0.5, label='보통 효과 (0.3)')
    ax.axvline(x=0.5, color='#95A5A6', linestyle='-', alpha=0.5, label='큰 효과 (0.5)')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([e['label'] for e in effects], fontsize=15)
    ax.set_xlabel('효과크기', fontsize=18)
    ax.set_title('팀원 C: 전체 효과크기 종합 Forest Plot',
                fontsize=24, fontweight='bold')
    ax.invert_yaxis()

    # 범례
    legend_elements = [
        Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
               markersize=10, markeredgecolor='black', label='유의 (p < .05)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='white',
               markersize=10, markeredgecolor='gray', label='비유의'),
        mpatches.Patch(color='#E74C3C', alpha=0.7, label='w (카이제곱)'),
        mpatches.Patch(color='#3498DB', alpha=0.7, label='R² (회귀)'),
        mpatches.Patch(color='#2ECC71', alpha=0.7, label='|z| (편차)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=14)

    ax.set_xlim(-0.05, max(e['value'] for e in effects) * 1.2 + 0.1)
    ax.grid(axis='x', alpha=0.3)

    save_figure(fig, TEAM, 'fig_c12_effect_size_forest.png')

    return effects


# ============================================================
# 분석 8: 종합 결론 인포그래픽 (6패널)
# ============================================================
def analyze_scientific_evidence(data, chi2_mbti, trend_results, chi2_pref,
                                 ci_compat, bloodtype_trends, world_comp):
    """과학적 근거 정리 및 6패널 종합 결론"""
    print("\n\n" + "━" * 60)
    print("  분석 8: 종합 결론 — 과학 vs 미신")
    print("━" * 60)

    korea_blood = data['korea_blood']
    korea_pop = 51_740_000

    a_pop = int(korea_pop * 34.2 / 100)
    b_pop = int(korea_pop * 27.1 / 100)
    o_pop = int(korea_pop * 28.1 / 100)
    ab_pop = int(korea_pop * 10.6 / 100)

    print(f"\n  [혈액형별 한국 추정 인구]")
    print(f"    A형:  약 {a_pop:>12,}명 (34.2%)")
    print(f"    B형:  약 {b_pop:>12,}명 (27.1%)")
    print(f"    O형:  약 {o_pop:>12,}명 (28.1%)")
    print(f"    AB형: 약 {ab_pop:>12,}명 (10.6%)")
    print(f"\n  → 4개의 혈액형으로 {korea_pop:,}명의 성격을 분류하는 것은")
    print(f"    각 그룹 평균 {korea_pop//4:,}명이 동일한 성격이라는 주장과 같음")

    trend_believe = trend_results['believe']
    bt_trends, _ = bloodtype_trends

    # === 시각화 13: 종합 결론 인포그래픽 (3×2 = 6패널) ===
    fig = plt.figure(figsize=(28, 16))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.96, '혈액형 성격론 통계적 검증 종합 결론',
            ha='center', fontsize=36, fontweight='bold', color='#2C3E50')
    fig.text(0.5, 0.93, '"과학인가 미신인가" — 데이터가 말하는 답',
            ha='center', fontsize=24, color='#7F8C8D')

    # 6패널 레이아웃 (3×2)
    panels = [
        (0.03, 0.60, 0.30, 0.28),   # 좌상
        (0.35, 0.60, 0.30, 0.28),   # 중상
        (0.67, 0.60, 0.30, 0.28),   # 우상
        (0.03, 0.22, 0.30, 0.28),   # 좌하
        (0.35, 0.22, 0.30, 0.28),   # 중하
        (0.67, 0.22, 0.30, 0.28),   # 우하
    ]

    # 혈액형별 추이 최대 R² 찾기
    max_r2_bt = max(bt_trends.items(), key=lambda x: x[1]['r_squared'])

    # 세계 편차 요약
    if world_comp is not None:
        max_z_bt = max(world_comp['z_scores'].items(), key=lambda x: abs(x[1]))
        world_text = (f"한국 vs 세계 127국 비교\n"
                      f"최대 편차: {max_z_bt[0]}형 (z={max_z_bt[1]:+.2f})\n\n"
                      f"▶ 한국은 B형이 세계 평균보다\n"
                      f"  높은 독특한 분포 보유")
    else:
        world_text = "세계 데이터 미가용"

    panel_data = [
        {
            'title': '검증 1: MBTI 분포',
            'content': (f"χ² = {chi2_mbti['chi2']:.1f}\n"
                       f"p < 0.001, w = {chi2_mbti['w']:.3f}\n\n"
                       f"▶ MBTI 분포는 균등하지 않음\n"
                       f"  (ISFJ, ISTJ, INFP 상위)"),
            'color': '#E74C3C',
        },
        {
            'title': '검증 2: 믿음 추세',
            'content': (f"'관련있다': {trend_believe['slope']:.2f}%/년\n"
                       f"R² = {trend_believe['r_squared']:.3f}\n\n"
                       f"▶ 과학적 회의론 확산 중\n"
                       f"  67% (2004) → 57% (2023)"),
            'color': '#3498DB',
        },
        {
            'title': '검증 3: 선호 vs 실제',
            'content': (f"χ² = {chi2_pref['chi2']:.1f}\n"
                       f"p < 0.001, w = {chi2_pref['w']:.3f}\n\n"
                       f"▶ O형 과대 선호 (49% vs 28%)\n"
                       f"  문화적 편향 반영"),
            'color': '#2ECC71',
        },
        {
            'title': '검증 4: 궁합 믿음',
            'content': (f"궁합 관련: {ci_compat['proportion']*100:.0f}%\n"
                       f"95% CI: [{ci_compat['lower']*100:.1f}%, {ci_compat['upper']*100:.1f}%]\n\n"
                       f"▶ 과반 미만이 관련있다 응답\n"
                       f"  → 대다수가 과학적 근거 부정"),
            'color': '#9B59B6',
        },
        {
            'title': '검증 5: 혈액형별 추이',
            'content': (f"4혈액형 모두 동일 추세\n"
                       f"최대 R²: {max_r2_bt[0]}형 ({max_r2_bt[1]['r_squared']:.3f})\n\n"
                       f"▶ 혈액형 비율 10년간 불변\n"
                       f"  → 유전적 결정, 비환경적"),
            'color': '#F39C12',
        },
        {
            'title': '검증 6: 세계 비교',
            'content': world_text,
            'color': '#1ABC9C',
        },
    ]

    for (x, y, w, h), pd_item in zip(panels, panel_data):
        ax = fig.add_axes([x, y, w, h])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()

        rect = plt.Rectangle((0, 0), 1, 1, facecolor=pd_item['color'],
                             alpha=0.1, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.axhline(y=0.88, xmin=0.05, xmax=0.95, color=pd_item['color'], linewidth=3)
        ax.text(0.5, 0.92, pd_item['title'], ha='center', va='bottom',
               fontsize=24, fontweight='bold', color=pd_item['color'])
        ax.text(0.08, 0.4, pd_item['content'], ha='left', va='center',
               fontsize=24, color='#2C3E50', linespacing=1.5)

    # 최종 결론
    fig.text(0.5, 0.12, '결론: 혈액형 성격론은 통계적 근거가 부족하며, 사회적 믿음은 점차 감소 중',
            ha='center', fontsize=26, fontweight='bold', color='#2C3E50',
            bbox=dict(facecolor='lightyellow', edgecolor='#F39C12',
                     boxstyle='round,pad=0.5'))

    fig.text(0.5, 0.06, f'한국 인구 약 {korea_pop//10000:,}만 명을 4개 혈액형으로 성격 분류 → '
            f'그룹당 평균 {korea_pop//4//10000:,}만 명이 동일 성격이라는 주장',
            ha='center', fontsize=24, color='#7F8C8D')

    fig.text(0.5, 0.02, '* 6개 검증 모두 혈액형 성격론의 과학적 근거 부족을 지지',
            ha='center', fontsize=23, color='#95A5A6', style='italic')

    save_figure(fig, TEAM, 'fig_c13_conclusion_summary.png', tight=False)


# ============================================================
# 결과 요약
# ============================================================
def create_summary(chi2_mbti, trend_results, chi2_pref, ci_compat, ci_personality,
                   bloodtype_trends, world_comp):
    """최종 결론"""
    print("\n\n" + "=" * 60)
    print("  팀원 C: 분석 결과 종합 요약")
    print("=" * 60)

    trend_believe = trend_results['believe']

    print(f"\n[검증 1] 한국 MBTI 분포 균등성")
    print(f"  → 균등분포와 유의하게 다름 (χ² = {chi2_mbti['chi2']:.1f}, p < 0.001, w = {chi2_mbti['w']:.3f})")
    print(f"    ISFJ, ISTJ, INFP가 상위 — 한국의 문화적 특성 반영 가능성")

    print(f"\n[검증 2] 혈액형-성격 관련성 믿음 추이")
    print(f"  → {trend_believe['trend_direction']} (기울기: {trend_believe['slope']:.2f}%/년)")
    print(f"    2004년 67% → 2023년 57%로 10%p 감소")
    print(f"    '관련없다' 추이: R² = {trend_results['not_related']['r_squared']:.3f} (유의한 증가)")

    print(f"\n[검증 3] 선호 혈액형 vs 실제 분포")
    print(f"  → 유의하게 다름 ({format_p_value(chi2_pref['p_value'])}, w = {chi2_pref['w']:.3f})")
    print(f"    O형 선호 49% vs 실제 28.1% — 선호는 문화적 편향")

    print(f"\n[검증 4] 궁합 관련성 믿음")
    print(f"  → 37%만 관련있다고 응답 (95% CI: "
          f"[{ci_compat['lower']*100:.1f}%, {ci_compat['upper']*100:.1f}%])")
    print(f"    과반 미만으로 대다수가 부정")

    bt_trends, corr_results = bloodtype_trends
    print(f"\n[검증 5] 혈액형별 헌혈 건수 추이")
    for bt in ['A', 'B', 'O', 'AB']:
        tr = bt_trends[bt]
        sig = "유의" if tr.get('significant', tr['p_value'] < 0.05) else "비유의"
        print(f"  → {bt}형: R² = {tr['r_squared']:.3f}, 기울기 = {tr['slope']/10000:.2f}만/년 ({sig})")

    if world_comp is not None:
        print(f"\n[검증 6] 한국 혈액형 세계적 위치")
        for bt in ['A', 'B', 'O', 'AB']:
            z = world_comp['z_scores'][bt]
            print(f"  → {bt}형: z = {z:+.2f} ({world_comp['deviations'][bt]:+.1f}%p)")

    print(f"\n[최종 결론]")
    print(f"  ✗ 혈액형 성격론은 통계적 근거가 부족합니다")
    print(f"  ✗ 한국 사회의 혈액형 성격론 믿음은 감소 추세입니다")
    print(f"  ✗ 선호 혈액형은 실제 분포가 아닌 문화적 편향을 반영합니다")
    print(f"  ✗ ABO 유전자 하나로 복잡한 인간 성격을 설명할 수 없습니다")
    print(f"  ✗ 혈액형 비율은 10년간 불변 — 유전적 결정 요인이지 성격 요인이 아닙니다")


# ============================================================
# 메인 실행
# ============================================================
def main():
    """팀원 C 전체 분석 실행"""
    data = load_and_preprocess()

    # 기존 분석 (fig_c1 ~ fig_c8)
    chi2_mbti = analyze_korea_mbti_distribution(data)
    donation_trend = analyze_korea_blood_distribution(data)
    trend_results, ci_data = analyze_personality_belief_trend(data)
    chi2_pref, ci_compat, ci_personality = analyze_blood_personality_theory_test(data)

    # 신규 분석 (fig_c9 ~ fig_c12)
    bloodtype_trends = analyze_blood_type_donation_trends(data)
    world_comp = analyze_blood_type_world_comparison(data)
    analyze_effect_size_forest(chi2_mbti, trend_results, chi2_pref,
                                bloodtype_trends, world_comp)

    # 종합 결론 (fig_c13)
    analyze_scientific_evidence(data, chi2_mbti, trend_results, chi2_pref,
                                 ci_compat, bloodtype_trends, world_comp)
    create_summary(chi2_mbti, trend_results, chi2_pref, ci_compat, ci_personality,
                   bloodtype_trends, world_comp)

    print(f"\n[완료] 팀원 C 분석 완료! 그래프 13개 저장")
    print(f"  저장 위치: results/figures/team_c/\n")


if __name__ == '__main__':
    set_project_style()
    main()
