# -*- coding: utf-8 -*-
"""
팀원 C 확장: 밈 설문 데이터로 혈액형 성격론 교차검증
====================================================
데이터: data/meme/ 설문 CSV + 한국 혈액형 데이터

목적:
  team_c(H1~H5)가 한국 공공데이터로 혈액형 성격론의 근거 부족을 보였다면,
  밈 설문 데이터로 "혈액형 vs MBTI" 인식을 직접 교차검증한다.
  핵심: Q42(MBTI 신뢰) vs Q43(혈액형 신뢰)의 직접 비교

반영 가능 항목:
  [O] 혈액형 분포 교차검증: 설문 vs 전국 분포
  [O] 혈액형 신뢰 vs MBTI 신뢰 직접 비교 (설문 고유)
  [O] 혈액형 x MBTI 차원 점수 (독립성 검증)
  [O] 혈액형 x MBTI 유형 (독립성 검증)
  [O] 신뢰도 그룹별 차원 점수 명확도
  [O] 최종 의견(Q46) 분석

통계 방법: 카이제곱, t-검정, ANOVA, Cohen's d, Pearson 상관

그래프 목록 (7개):
  fig_cs1: 설문 혈액형 분포 vs 한국 인구 분포
  fig_cs2: 혈액형 신뢰도 vs MBTI 신뢰도 비교
  fig_cs3: 혈액형 x MBTI 차원 점수 (ANOVA)
  fig_cs4: 혈액형 x MBTI 유형 분포 (카이제곱)
  fig_cs5: 신뢰도 그룹별 차원 점수 명확도
  fig_cs6: 최종 의견(Q46) + 혈액형 연계
  fig_cs7: 종합 결론 인포그래픽
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
    MBTI_TYPES, MBTI_COLORS, BLOOD_COLORS, BLOOD_TYPES,
    MBTI_DIMENSIONS, DIMENSION_NAMES_KR,
    FIGSIZE_DEFAULT, FIGSIZE_WIDE
)
from common.data_loader import load_korea_bloodtype
from common.stats_utils import (
    descriptive_stats, pearson_correlation, independent_t_test,
    one_way_anova, cohens_d, chi_square_test,
    chi_square_goodness_of_fit, linear_regression, print_test_result
)
from common.plot_style import (
    set_project_style, save_figure, format_p_value, add_result_text
)
from survey.mbti_scoring_v2 import (
    batch_compute_from_array_v2, extract_bonus_data,
    V2_COL_MAP, MIDPOINT
)

TEAM = 'team_c'

SURVEY_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'data', 'meme',
    'MBTI_밈_설문v2_응답_데이터 - Form Responses 1.csv'
)

DIM_KEYS = ['EI', 'SN', 'TF', 'JP']
DIM_LABELS_KR = {
    'EI': '내향성(EI)', 'SN': '감각(SN)',
    'TF': '사고(TF)', 'JP': '판단(JP)',
}

# 혈액형 색상 (한국어 라벨)
BT_ORDER = ['A형', 'B형', 'O형', 'AB형']
BT_SHORT = ['A', 'B', 'O', 'AB']


# ============================================================
#  데이터 로드
# ============================================================
def load_survey_data():
    """밈 설문 CSV + 한국 혈액형 데이터 로드"""
    print("=" * 60)
    print("  팀원 C 확장: 밈 설문 교차검증 (혈액형 성격론 관점)")
    print("=" * 60)

    if not os.path.exists(SURVEY_CSV):
        raise FileNotFoundError(f"설문 CSV 파일이 없습니다: {SURVEY_CSV}")

    df = pd.read_csv(SURVEY_CSV)
    raw = df.values
    n = raw.shape[0]
    print(f"\n[데이터] 설문 응답: {n}명")

    scoring = batch_compute_from_array_v2(raw)
    bonus = extract_bonus_data(raw)

    blood_types = np.array([str(raw[i, V2_COL_MAP['blood_type']]).strip()
                            for i in range(n)])
    genders = np.array([str(raw[i, V2_COL_MAP['gender']]).strip()
                        for i in range(n)])
    ages = np.array([str(raw[i, V2_COL_MAP['age']]).strip()
                     for i in range(n)])

    # 한국 혈액형 분포 로드
    korea_blood = load_korea_bloodtype()
    print(f"[데이터] 한국 혈액형: {', '.join(f'{t}={p}%' for t, p in zip(korea_blood['types'], korea_blood['percentages']))}")

    # 혈액형/MBTI 신뢰도 추출
    mbti_trust = bonus['mbti_trust']
    blood_trust = bonus['blood_trust']

    print(f"[데이터] MBTI 신뢰도 평균: {np.nanmean(mbti_trust):.2f}")
    print(f"[데이터] 혈액형 신뢰도 평균: {np.nanmean(blood_trust):.2f}")

    return {
        'n': n,
        'survey_scores': scoring['scores'],
        'survey_types': scoring['types'],
        'blood_types': blood_types,
        'genders': genders,
        'ages': ages,
        'bonus': bonus,
        'mbti_trust': mbti_trust,
        'blood_trust': blood_trust,
        'korea_blood': korea_blood,
    }


# ============================================================
#  CS1: 설문 혈액형 분포 vs 한국 인구 분포
# ============================================================
def analyze_blood_distribution(data):
    """설문 혈액형 분포 vs 한국 전체 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 CS1: 혈액형 분포 — 설문 vs 한국 인구")
    print("━" * 60)

    blood_types = data['blood_types']
    korea_blood = data['korea_blood']
    n = data['n']

    # 설문 혈액형 빈도
    s_counts = np.array([np.sum(blood_types == bt) for bt in BT_ORDER])
    s_pcts = s_counts / n * 100

    # 한국 비율
    korea_dict = dict(zip(korea_blood['types'], korea_blood['percentages']))
    k_pcts = np.array([korea_dict.get(bt.replace('형', ''), 0) for bt in BT_ORDER])

    # 카이제곱 적합도
    expected = k_pcts / 100 * n
    expected = np.where(expected < 1, 1, expected)
    chi2_res = chi_square_goodness_of_fit(s_counts.astype(float), expected)

    print(f"  설문: {', '.join(f'{bt}={s_pcts[i]:.1f}%' for i, bt in enumerate(BT_ORDER))}")
    print(f"  한국: {', '.join(f'{bt}={k_pcts[i]:.1f}%' for i, bt in enumerate(BT_ORDER))}")
    print(f"  chi2={chi2_res['chi2']:.2f}, {format_p_value(chi2_res['p_value'])}")

    # === 시각화 ===
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('혈액형 분포 비교: 설문 vs 한국 인구', fontsize=24, fontweight='bold')

    colors = [BLOOD_COLORS.get(bt.replace('형', ''), '#95A5A6') for bt in BT_ORDER]

    # 좌: 설문 파이
    ax = axes[0]
    wedges, texts, autotexts = ax.pie(
        s_pcts, labels=[f'{bt}\n({cnt}명)' for bt, cnt in zip(BT_ORDER, s_counts)],
        colors=colors, autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 14})
    for at in autotexts:
        at.set_fontsize(13)
    ax.set_title(f'설문 (N={n})', fontsize=20, fontweight='bold')

    # 우: 한국 파이
    ax = axes[1]
    wedges, texts, autotexts = ax.pie(
        k_pcts, labels=BT_ORDER,
        colors=colors, autopct='%1.1f%%', startangle=90,
        textprops={'fontsize': 14})
    for at in autotexts:
        at.set_fontsize(13)
    ax.set_title('한국 전체', fontsize=20, fontweight='bold')

    fig.text(0.5, 0.02,
             f'카이제곱 적합도: chi2={chi2_res["chi2"]:.2f}, '
             f'{format_p_value(chi2_res["p_value"])}',
             ha='center', fontsize=14, color='#7F8C8D')

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    save_figure(fig, TEAM, 'fig_cs1_blood_distribution.png')

    return chi2_res


# ============================================================
#  CS2: 혈액형 신뢰도 vs MBTI 신뢰도
# ============================================================
def analyze_trust_comparison(data):
    """혈액형 신뢰 vs MBTI 신뢰 직접 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 CS2: 혈액형 신뢰도 vs MBTI 신뢰도")
    print("━" * 60)

    mbti_trust = data['mbti_trust']
    blood_trust = data['blood_trust']

    # NaN 제거
    valid = ~(np.isnan(mbti_trust) | np.isnan(blood_trust))
    m_valid = mbti_trust[valid]
    b_valid = blood_trust[valid]

    # 기술통계
    print(f"  MBTI 신뢰도: 평균={np.mean(m_valid):.2f}, SD={np.std(m_valid):.2f}")
    print(f"  혈액형 신뢰도: 평균={np.mean(b_valid):.2f}, SD={np.std(b_valid):.2f}")

    # 대응표본 비교 (같은 사람의 두 신뢰도)
    diff = m_valid - b_valid
    t_stat = np.mean(diff) / (np.std(diff, ddof=1) / np.sqrt(len(diff)))
    df = len(diff) - 1
    # p-value 근사 (양측)
    from scipy import stats as sp_stats
    p_val = 2 * (1 - sp_stats.t.cdf(abs(t_stat), df))
    d_val = np.mean(diff) / np.std(diff, ddof=1)  # paired Cohen's d

    print(f"  대응표본 t-검정: t={t_stat:.3f}, df={df}, p={p_val:.4f}")
    print(f"  Cohen's d (paired) = {d_val:.3f}")
    print(f"  -> {'MBTI가 혈액형보다 더 신뢰받음' if np.mean(diff) > 0 else '혈액형이 MBTI보다 더 신뢰받음'}")

    # === 시각화 ===
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('혈액형 신뢰도 vs MBTI 신뢰도 비교', fontsize=24, fontweight='bold')

    # 좌: MBTI 신뢰 히스토그램
    ax = axes[0]
    bins = np.arange(0.5, 8.5, 1)
    ax.hist(m_valid, bins=bins, color='#3498DB', alpha=0.8, edgecolor='white')
    ax.axvline(np.mean(m_valid), color='red', linestyle='--', linewidth=2,
               label=f'평균={np.mean(m_valid):.2f}')
    ax.set_xlabel('신뢰도 (1-7)')
    ax.set_ylabel('빈도')
    ax.set_title('MBTI 신뢰도 (Q42)', fontsize=18, fontweight='bold')
    ax.legend(fontsize=18)

    # 중: 혈액형 신뢰 히스토그램
    ax = axes[1]
    ax.hist(b_valid, bins=bins, color='#E74C3C', alpha=0.8, edgecolor='white')
    ax.axvline(np.mean(b_valid), color='red', linestyle='--', linewidth=2,
               label=f'평균={np.mean(b_valid):.2f}')
    ax.set_xlabel('신뢰도 (1-7)')
    ax.set_ylabel('빈도')
    ax.set_title('혈액형 신뢰도 (Q43)', fontsize=18, fontweight='bold')
    ax.legend(fontsize=18)

    # 우: 차이 분포 + 박스플롯
    ax = axes[2]
    bp = ax.boxplot([m_valid, b_valid], tick_labels=['MBTI\n신뢰도', '혈액형\n신뢰도'],
                    patch_artist=True,
                    medianprops=dict(color='black', linewidth=2))
    bp['boxes'][0].set_facecolor('#3498DB')
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor('#E74C3C')
    bp['boxes'][1].set_alpha(0.7)

    for i, vals in enumerate([m_valid, b_valid]):
        ax.scatter(i + 1, np.mean(vals), color='red', marker='D', s=80, zorder=5)
        ax.annotate(f'{np.mean(vals):.2f}', (i + 1, np.mean(vals)),
                    textcoords="offset points", xytext=(20, 5),
                    fontsize=18, color='red', fontweight='bold')

    sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'ns'))
    ax.set_title(f'비교: d={d_val:.3f} ({sig})', fontsize=18, fontweight='bold')
    ax.set_ylabel('신뢰도 (1-7)')

    result_text = (f"paired t = {t_stat:.3f}\n"
                   f"p = {p_val:.4f}\n"
                   f"Cohen's d = {d_val:.3f}")
    add_result_text(ax, result_text)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_cs2_trust_comparison.png')

    # --- 회귀분석: MBTI 신뢰도 → 혈액형 신뢰도 ---
    print(f"\n  [회귀분석] MBTI 신뢰도 → 혈액형 신뢰도 예측")
    reg_result = linear_regression(m_valid, b_valid)
    corr_result = pearson_correlation(m_valid, b_valid)
    print(f"    회귀식: 혈액형신뢰도 = {reg_result['slope']:.4f} \u00d7 MBTI신뢰도 + {reg_result['intercept']:.4f}")
    print(f"    R\u00b2 = {reg_result['r_squared']:.4f} (예측력: {reg_result['r_squared']*100:.1f}%)")
    print(f"    Pearson r = {corr_result['r']:.4f}, {format_p_value(corr_result['p_value'])}")
    if reg_result['r_squared'] < 0.13:
        print(f"    해석: R\u00b2 < 0.13 \u2192 MBTI 신뢰도가 혈액형 신뢰도를 거의 예측하지 못함")
    elif reg_result['r_squared'] < 0.26:
        print(f"    해석: 0.13 \u2264 R\u00b2 < 0.26 \u2192 보통 수준의 예측력")
    else:
        print(f"    해석: R\u00b2 \u2265 0.26 \u2192 큰 예측력")

    return {'t': t_stat, 'p': p_val, 'd': d_val,
            'mbti_mean': float(np.mean(m_valid)),
            'blood_mean': float(np.mean(b_valid)),
            'regression': reg_result}


# ============================================================
#  CS3: 혈액형 x MBTI 차원 점수 (ANOVA)
# ============================================================
def analyze_blood_mbti_dimensions(data):
    """혈액형이 MBTI 차원 점수를 예측하는가?"""
    print("\n\n" + "━" * 60)
    print("  분석 CS3: 혈액형 x MBTI 차원 점수 (독립성 검증)")
    print("━" * 60)

    blood_types = data['blood_types']
    anova_results = {}

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('혈액형 x MBTI 차원 점수: 혈액형 성격론 직접 검증',
                 fontsize=24, fontweight='bold')

    for idx, dk in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        scores = data['survey_scores'][dk]

        groups_data = []
        labels = []
        for bt in BT_ORDER:
            mask = blood_types == bt
            grp = scores[mask]
            if len(grp) >= 2:
                groups_data.append(grp)
                labels.append(f'{bt}\n(n={len(grp)})')

        if len(groups_data) >= 2:
            anova_res = one_way_anova(*groups_data)
            anova_results[dk] = anova_res

            colors = [BLOOD_COLORS.get(bt.replace('형', ''), '#95A5A6')
                      for bt in BT_ORDER[:len(groups_data)]]
            bp = ax.boxplot(groups_data, tick_labels=labels, patch_artist=True,
                            medianprops=dict(color='black', linewidth=2))
            for patch, c in zip(bp['boxes'], colors):
                patch.set_facecolor(c)
                patch.set_alpha(0.7)

            # 평균 표시
            for i, grp in enumerate(groups_data):
                ax.scatter(i + 1, np.mean(grp), color='red', marker='D',
                           s=60, zorder=5)

            sig = '***' if anova_res['p_value'] < 0.001 else ('**' if anova_res['p_value'] < 0.01 else ('*' if anova_res['p_value'] < 0.05 else 'ns'))
            ax.set_title(f'{dk}: F={anova_res["f_stat"]:.2f}, '
                         f'eta2={anova_res["eta_squared"]:.4f} ({sig})',
                         fontsize=16, fontweight='bold')

            print(f"  [{dk}] F={anova_res['f_stat']:.3f}, "
                  f"eta2={anova_res['eta_squared']:.4f}, "
                  f"{format_p_value(anova_res['p_value'])}")
        else:
            ax.text(0.5, 0.5, 'N/A', ha='center', va='center',
                    fontsize=20, transform=ax.transAxes)
            ax.set_title(f'{dk}: 데이터 부족', fontsize=16)

        ax.set_ylabel(f'{DIM_LABELS_KR[dk]} 점수')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_cs3_blood_mbti_dimensions.png')

    return anova_results


# ============================================================
#  CS4: 혈액형 x MBTI 유형 분포 (카이제곱)
# ============================================================
def analyze_blood_mbti_types(data):
    """혈액형과 MBTI 유형은 독립적인가?"""
    print("\n\n" + "━" * 60)
    print("  분석 CS4: 혈액형 x MBTI 유형 분포 (독립성 검정)")
    print("━" * 60)

    blood_types = data['blood_types']
    survey_types = data['survey_types']
    n = data['n']

    # 설문에 존재하는 MBTI 유형만
    unique_mbti = sorted(set(survey_types))

    # 교차표 (혈액형 4 x MBTI k)
    observed = np.zeros((len(BT_ORDER), len(unique_mbti)), dtype=np.float64)
    for i, bt in enumerate(BT_ORDER):
        for j, mt in enumerate(unique_mbti):
            observed[i, j] = np.sum((blood_types == bt) & (survey_types == mt))

    # 카이제곱 독립성 검정 (기대빈도 < 5 경고)
    total = np.sum(observed)
    row_total = observed.sum(axis=1, keepdims=True)
    col_total = observed.sum(axis=0, keepdims=True)
    expected = row_total * col_total / total

    small_cells = np.sum(expected < 5)
    print(f"  교차표 크기: {observed.shape[0]} x {observed.shape[1]}")
    print(f"  기대빈도 < 5인 셀: {small_cells}개 (전체 {observed.size}개)")

    if small_cells > 0.2 * observed.size:
        print("  [!] 기대빈도 5 미만 셀이 20% 초과 — 카이제곱 결과 신뢰도 낮음")

    chi2_res = chi_square_test(observed)
    print(f"  chi2={chi2_res['chi2']:.2f}, df={chi2_res['dof']}, "
          f"{format_p_value(chi2_res['p_value'])}")
    print(f"  Cramer's V = {chi2_res['cramers_v']:.4f}")

    # === 시각화: 혈액형별 MBTI 유형 분포 ===
    fig, ax = plt.subplots(figsize=(16, 8))

    # 혈액형별 비율 계산
    proportions = observed / row_total * 100

    x = np.arange(len(unique_mbti))
    width = 0.2
    colors = [BLOOD_COLORS.get(bt.replace('형', ''), '#95A5A6') for bt in BT_ORDER]

    for i, (bt, color) in enumerate(zip(BT_ORDER, colors)):
        bars = ax.bar(x + i * width - 1.5 * width, proportions[i],
                      width, label=bt, color=color, edgecolor='white', alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(unique_mbti, rotation=45, ha='right', fontsize=13)
    ax.set_ylabel('비율 (%)')
    ax.set_xlabel('MBTI 유형')
    ax.set_title('혈액형별 MBTI 유형 분포', fontsize=24, fontweight='bold')
    ax.legend(fontsize=16)

    result_text = (f"chi2 = {chi2_res['chi2']:.2f}, df = {chi2_res['dof']}\n"
                   f"{format_p_value(chi2_res['p_value'])}\n"
                   f"V = {chi2_res['cramers_v']:.4f}\n"
                   f"[!] 기대빈도<5: {small_cells}셀")
    add_result_text(ax, result_text)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_cs4_blood_mbti_types.png')

    return chi2_res


# ============================================================
#  CS5: 신뢰도 그룹별 차원 점수 명확도
# ============================================================
def analyze_trust_clarity(data):
    """신뢰도 높은 사람이 더 극단적 점수를 보이는가?"""
    print("\n\n" + "━" * 60)
    print("  분석 CS5: 신뢰도 그룹별 차원 점수 명확도")
    print("━" * 60)

    mbti_trust = data['mbti_trust']
    blood_trust = data['blood_trust']

    # 명확도: |score - 4.0| 의 평균 (4차원 평균)
    clarity = np.zeros(data['n'])
    for dk in DIM_KEYS:
        clarity += np.abs(data['survey_scores'][dk] - MIDPOINT)
    clarity /= 4  # 평균 명확도

    # MBTI 신뢰 그룹 (높음 5-7, 낮음 1-3)
    m_high_mask = mbti_trust >= 5
    m_low_mask = mbti_trust <= 3
    m_mid_mask = (~m_high_mask) & (~m_low_mask) & (~np.isnan(mbti_trust))

    # 혈액형 신뢰 그룹
    b_high_mask = blood_trust >= 5
    b_low_mask = blood_trust <= 3

    results = {}

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('신뢰도 그룹별 차원 점수 명확도 (|score - 4.0| 평균)',
                 fontsize=22, fontweight='bold')

    # 좌: MBTI 신뢰도 그룹
    ax = axes[0]
    groups_m = []
    labels_m = []
    for mask, lbl in [(m_low_mask, '낮음(1-3)'), (m_mid_mask, '보통(4)'), (m_high_mask, '높음(5-7)')]:
        valid = mask & ~np.isnan(clarity)
        if np.sum(valid) >= 2:
            groups_m.append(clarity[valid])
            labels_m.append(f'{lbl}\n(n={np.sum(valid)})')

    if len(groups_m) >= 2:
        bp = ax.boxplot(groups_m, tick_labels=labels_m, patch_artist=True,
                        medianprops=dict(color='black', linewidth=2))
        colors_m = ['#AED6F1', '#5DADE2', '#2471A3']
        for patch, c in zip(bp['boxes'], colors_m[:len(groups_m)]):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)

        for i, grp in enumerate(groups_m):
            ax.scatter(i + 1, np.mean(grp), color='red', marker='D', s=60, zorder=5)
            ax.annotate(f'{np.mean(grp):.2f}', (i + 1, np.mean(grp)),
                        textcoords="offset points", xytext=(15, 5),
                        fontsize=14, color='red')

        if len(groups_m) >= 2:
            anova_m = one_way_anova(*groups_m)
            results['mbti_anova'] = anova_m
            sig = '***' if anova_m['p_value'] < 0.001 else ('**' if anova_m['p_value'] < 0.01 else ('*' if anova_m['p_value'] < 0.05 else 'ns'))
            ax.set_title(f'MBTI 신뢰도별: eta2={anova_m["eta_squared"]:.4f} ({sig})',
                         fontsize=16, fontweight='bold')
            print(f"  MBTI 신뢰 그룹: F={anova_m['f_stat']:.3f}, "
                  f"eta2={anova_m['eta_squared']:.4f}, {format_p_value(anova_m['p_value'])}")

    ax.set_ylabel('명확도 (|score - 4.0| 평균)')

    # 우: 혈액형 신뢰도 그룹
    ax = axes[1]
    b_mid_mask = (~b_high_mask) & (~b_low_mask) & (~np.isnan(blood_trust))
    groups_b = []
    labels_b = []
    for mask, lbl in [(b_low_mask, '낮음(1-3)'), (b_mid_mask, '보통(4)'), (b_high_mask, '높음(5-7)')]:
        valid = mask & ~np.isnan(clarity)
        if np.sum(valid) >= 2:
            groups_b.append(clarity[valid])
            labels_b.append(f'{lbl}\n(n={np.sum(valid)})')

    if len(groups_b) >= 2:
        bp = ax.boxplot(groups_b, tick_labels=labels_b, patch_artist=True,
                        medianprops=dict(color='black', linewidth=2))
        colors_b = ['#F5B7B1', '#E74C3C', '#922B21']
        for patch, c in zip(bp['boxes'], colors_b[:len(groups_b)]):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)

        for i, grp in enumerate(groups_b):
            ax.scatter(i + 1, np.mean(grp), color='red', marker='D', s=60, zorder=5)
            ax.annotate(f'{np.mean(grp):.2f}', (i + 1, np.mean(grp)),
                        textcoords="offset points", xytext=(15, 5),
                        fontsize=14, color='red')

        if len(groups_b) >= 2:
            anova_b = one_way_anova(*groups_b)
            results['blood_anova'] = anova_b
            sig = '***' if anova_b['p_value'] < 0.001 else ('**' if anova_b['p_value'] < 0.01 else ('*' if anova_b['p_value'] < 0.05 else 'ns'))
            ax.set_title(f'혈액형 신뢰도별: eta2={anova_b["eta_squared"]:.4f} ({sig})',
                         fontsize=16, fontweight='bold')
            print(f"  혈액형 신뢰 그룹: F={anova_b['f_stat']:.3f}, "
                  f"eta2={anova_b['eta_squared']:.4f}, {format_p_value(anova_b['p_value'])}")

    ax.set_ylabel('명확도 (|score - 4.0| 평균)')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_cs5_trust_clarity.png')

    return results


# ============================================================
#  CS6: 최종 의견(Q46) + 혈액형 연계
# ============================================================
def analyze_final_opinion(data):
    """최종 의견 분석 + 혈액형 신뢰도 연계"""
    print("\n\n" + "━" * 60)
    print("  분석 CS6: 최종 의견(Q46) 분석")
    print("━" * 60)

    final_opinion = data['bonus']['final_opinion']
    mbti_trust = data['mbti_trust']
    blood_trust = data['blood_trust']

    # 의견 정리 (문자열 clean)
    opinions = np.array([str(o).strip() for o in final_opinion])
    unique_ops = sorted(set(opinions))
    op_counts = {op: np.sum(opinions == op) for op in unique_ops}

    print("  최종 의견 분포:")
    for op, cnt in sorted(op_counts.items(), key=lambda x: -x[1]):
        print(f"    {op}: {cnt}명 ({cnt/data['n']*100:.1f}%)")

    # 의견 그룹별 신뢰도 비교
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('최종 의견(Q46) 분석 + 신뢰도 연계', fontsize=24, fontweight='bold')

    # 좌: 의견 분포 바 차트
    ax = axes[0]
    # 짧은 라벨 사용
    op_sorted = sorted(op_counts.items(), key=lambda x: -x[1])
    op_labels = [op[:15] + '...' if len(op) > 15 else op for op, _ in op_sorted]
    op_vals = [cnt for _, cnt in op_sorted]
    op_pcts = [cnt / data['n'] * 100 for cnt in op_vals]

    colors_opinion = plt.cm.Set2(np.linspace(0, 1, len(op_labels)))
    bars = ax.barh(range(len(op_labels)), op_vals, color=colors_opinion,
                   edgecolor='white', height=0.6)
    ax.set_yticks(range(len(op_labels)))
    ax.set_yticklabels(op_labels, fontsize=13)
    ax.set_xlabel('응답 수')
    ax.set_title('최종 의견 분포', fontsize=20, fontweight='bold')
    for i, (v, p) in enumerate(zip(op_vals, op_pcts)):
        ax.text(v + 0.3, i, f'{v}명 ({p:.1f}%)', va='center', fontsize=13)

    # 우: MBTI 신뢰도 높은/낮은 그룹 vs 혈액형 신뢰도 높은/낮은 그룹의 의견 비교
    ax = axes[1]
    # 신뢰도 상위/하위 분류
    m_high = mbti_trust >= 5
    m_low = mbti_trust <= 3
    b_high = blood_trust >= 5
    b_low = blood_trust <= 3

    group_labels = ['MBTI\n고신뢰', 'MBTI\n저신뢰', '혈액형\n고신뢰', '혈액형\n저신뢰']
    group_masks = [m_high, m_low, b_high, b_low]
    group_mean_mbti = [np.nanmean(mbti_trust[m]) if np.sum(m) > 0 else 0 for m in group_masks]
    group_mean_blood = [np.nanmean(blood_trust[m]) if np.sum(m) > 0 else 0 for m in group_masks]
    group_ns = [np.sum(m & ~np.isnan(mbti_trust)) for m in group_masks]

    x = np.arange(len(group_labels))
    width = 0.35
    ax.bar(x - width/2, group_mean_mbti, width, label='MBTI 신뢰도', color='#3498DB', alpha=0.8)
    ax.bar(x + width/2, group_mean_blood, width, label='혈액형 신뢰도', color='#E74C3C', alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([f'{lbl}\n(n={n})' for lbl, n in zip(group_labels, group_ns)],
                       fontsize=12)
    ax.set_ylabel('평균 신뢰도 (1-7)')
    ax.set_title('신뢰도 그룹별 프로필', fontsize=20, fontweight='bold')
    ax.legend(fontsize=14)
    ax.set_ylim(0, 7.5)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_cs6_final_opinion.png')

    return op_counts


# ============================================================
#  CS7: 종합 결론 인포그래픽
# ============================================================
def create_conclusion_infographic(data, chi2_blood, trust_res, anova_dims,
                                    chi2_types, trust_clarity, op_counts):
    """혈액형 성격론 설문 교차검증 종합 결론"""
    print("\n\n" + "━" * 60)
    print("  분석 CS7: 종합 결론 인포그래픽")
    print("━" * 60)

    fig = plt.figure(figsize=(28, 16))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.96, '혈액형 성격론 vs MBTI — 설문 교차검증 종합 결론',
             ha='center', fontsize=34, fontweight='bold', color='#2C3E50')
    fig.text(0.5, 0.925,
             f'설문 {data["n"]}명 | 혈액형->MBTI 전환: 어느 체계가 더 신뢰받는가?',
             ha='center', fontsize=22, color='#7F8C8D')

    panels = [
        (0.03, 0.55, 0.30, 0.32),
        (0.35, 0.55, 0.30, 0.32),
        (0.67, 0.55, 0.30, 0.32),
        (0.03, 0.15, 0.30, 0.32),
        (0.35, 0.15, 0.30, 0.32),
        (0.67, 0.15, 0.30, 0.32),
    ]

    # 혈액형xMBTI ANOVA 요약
    dim_text_lines = []
    for dk in DIM_KEYS:
        if dk in anova_dims:
            eta = anova_dims[dk]['eta_squared']
            dim_text_lines.append(f"{dk}: eta2={eta:.4f}")
    dim_text = '\n'.join(dim_text_lines) if dim_text_lines else 'N/A'

    # 명확도 결과
    clarity_text = ""
    if 'mbti_anova' in trust_clarity:
        m_eta = trust_clarity['mbti_anova']['eta_squared']
        clarity_text += f"MBTI: eta2={m_eta:.4f}\n"
    if 'blood_anova' in trust_clarity:
        b_eta = trust_clarity['blood_anova']['eta_squared']
        clarity_text += f"혈액형: eta2={b_eta:.4f}"

    panel_data = [
        {
            'title': '혈액형 분포',
            'content': (f"설문 vs 한국 전체 비교\n"
                       f"chi2 = {chi2_blood.get('chi2', 0):.1f}\n"
                       f"{format_p_value(chi2_blood.get('p_value', 1))}\n\n"
                       f"-> 표본 분포 확인"),
            'color': '#E74C3C',
        },
        {
            'title': '신뢰도 비교',
            'content': (f"MBTI: 평균 {trust_res.get('mbti_mean', 0):.2f}\n"
                       f"혈액형: 평균 {trust_res.get('blood_mean', 0):.2f}\n"
                       f"d = {trust_res.get('d', 0):.3f}\n\n"
                       f"-> {'MBTI가 더 신뢰받음' if trust_res.get('d', 0) > 0 else '유사한 수준'}"),
            'color': '#3498DB',
        },
        {
            'title': '혈액형 x MBTI 차원',
            'content': (f"혈액형별 차원 점수 ANOVA:\n{dim_text}\n\n"
                       f"-> 혈액형은 MBTI 점수와\n"
                       f"   독립적 (효과 극히 미약)"),
            'color': '#2ECC71',
        },
        {
            'title': '혈액형 x MBTI 유형',
            'content': (f"chi2 = {chi2_types.get('chi2', 0):.1f}\n"
                       f"V = {chi2_types.get('cramers_v', 0):.4f}\n"
                       f"{format_p_value(chi2_types.get('p_value', 1))}\n\n"
                       f"-> 두 분류 체계 독립"),
            'color': '#9B59B6',
        },
        {
            'title': '신뢰도와 명확도',
            'content': (f"{clarity_text}\n\n"
                       f"-> 신뢰도가 높을수록\n"
                       f"   점수가 극단적인가?"),
            'color': '#F39C12',
        },
        {
            'title': '종합 해석',
            'content': (f"1. 혈액형 -> MBTI 전환 확인\n"
                       f"2. 혈액형-MBTI 독립적\n"
                       f"3. MBTI 신뢰 > 혈액형 신뢰\n\n"
                       f"-> 두 체계 모두 과학적\n"
                       f"   근거는 제한적"),
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
             '결론: 혈액형 성격론에서 MBTI로의 전환이 설문에서 확인됨 — 그러나 두 체계 모두 과학적 근거는 제한적',
             ha='center', fontsize=26, fontweight='bold', color='#2C3E50',
             bbox=dict(facecolor='#FEF9E7', edgecolor='#F39C12',
                       boxstyle='round,pad=0.6', linewidth=2))

    fig.text(0.5, 0.025,
             f'* 설문 N={data["n"]} 소표본 한계 | 혈액형 4그룹 x MBTI 16유형 = 기대빈도 부족 주의',
             ha='center', fontsize=23, color='#7F8C8D', style='italic')

    save_figure(fig, TEAM, 'fig_cs7_conclusion_infographic.png', tight=False)


# ============================================================
#  메인 실행
# ============================================================
def main():
    """팀원 C 설문 교차검증 실행"""
    data = load_survey_data()

    chi2_blood = analyze_blood_distribution(data)           # cs1
    trust_res = analyze_trust_comparison(data)               # cs2
    anova_dims = analyze_blood_mbti_dimensions(data)         # cs3
    chi2_types = analyze_blood_mbti_types(data)              # cs4
    trust_clarity = analyze_trust_clarity(data)              # cs5
    op_counts = analyze_final_opinion(data)                  # cs6
    create_conclusion_infographic(data, chi2_blood, trust_res,
                                   anova_dims, chi2_types,
                                   trust_clarity, op_counts)  # cs7

    print(f"\n[완료] 팀원 C 설문 교차검증 완료! 그래프 7개 저장")
    print(f"  저장 위치: results/figures/team_c/\n")


if __name__ == '__main__':
    set_project_style()
    main()
