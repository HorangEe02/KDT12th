# -*- coding: utf-8 -*-
"""
팀원 B: MBTI 차원 점수와 관심사/라이프스타일 상관분석 (고급 분석 확장 버전)
====================================================================
데이터: data.csv (43,744행)
분석: MBTI 4개 차원 점수(연속형)와 관심사 분야 간의 관계 다각도 분석

가설:
  H1: MBTI 4개 차원 점수 간에 유의한 상관관계가 있다
  H2: 관심사 분야에 따라 MBTI 차원 점수가 유의하게 다르다
  H3: 특정 차원 점수 쌍 간에 유의한 선형 관계가 존재한다
  H4: 관심사별 차원 점수 프로필로 집단 구분이 가능한가
  H5: MBTI 유형(범주)과 관심사 분야는 독립이 아니다
  H6: 성별이 MBTI-관심사 관계를 조절한다
  H7: MBTI 차원 점수의 명확도(극단성)가 관심사에 따라 유의하게 다르다
  H8: Unknown 관심사 그룹은 Known 그룹과 MBTI 차원 점수가 유의하게 다르다
  H9: 연령대가 MBTI-관심사 관계를 조절한다
  H10: 다중 예측변수(나이/성별/교육/다른 차원)로 차원 점수를 예측할 수 있다

통계 방법: 피어슨 상관분석, ANOVA, 단순/다중회귀분석, 신뢰구간,
          효과크기 분석, 유클리드 거리, 그룹 프로필링,
          카이제곱 독립성 검정, 독립표본 t-검정,
          중심점 기반 분류(Nearest Centroid),
          Shapiro-Wilk 정규성 검정 (scipy), Kruskal-Wallis 비모수 검정 (scipy),
          Mann-Whitney U 검정 (scipy), PCA 주성분분석 (numpy)

시각화: 21개 (fig_b1 ~ fig_b21)
  - fig_b1:  MBTI 차원 점수 분포 히스토그램 (4패널)
  - fig_b2:  차원 점수 산점도 행렬 (4×4)
  - fig_b3:  관심사별 차원 점수 Box Plot (4패널)
  - fig_b4:  관심사별 차원 점수 레이더 차트
  - fig_b5:  차원 점수 간 상관계수 Heatmap
  - fig_b6:  주요 차원 쌍 회귀분석 산점도 (3패널)
  - fig_b7:  관심사 그룹 프로필 Parallel Coordinates
  - fig_b8:  관심사별 차원 점수 KDE 밀도 + 95% CI Error Bar (통합)
  - fig_b9:  MBTI 유형(범주) × 관심사 표준화 잔차 Heatmap
  - fig_b10: 성별 조절효과 비교
  - fig_b11: 중심점 분류 Confusion Matrix + 정확도
  - fig_b12: 차원 점수 쌍별 관심사 색상 산점도 (대표 3쌍)
  - fig_b13: 관심사 간 유클리드 거리 Heatmap
  - fig_b14: 전체 효과크기 종합 Forest Plot (확장)
  - fig_b15: 종합 결론 인포그래픽 (10패널)
  - fig_b16: 정규성 검정 + 비모수 검증 (Shapiro-Wilk, Kruskal-Wallis)
  - fig_b17: H7 점수 명확도(극단성) × 관심사 Box Plot
  - fig_b18: H8 Unknown vs Known 그룹 비교 (KDE + Cohen's d)
  - fig_b19: H9 연령대 × 관심사 조절효과 η² Heatmap
  - fig_b20: H10 다중회귀분석 계수 Forest Plot + R² 비교
  - fig_b21: PCA 2차원 시각화 (산점도 + Scree Plot)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns
from scipy import stats as sp_stats

from common.config import INTEREST_COLORS, MBTI_TYPES, MBTI_COLORS, GENDER_COLORS
from common.data_loader import load_personality_data
from common.stats_utils import (
    descriptive_stats, pearson_correlation, correlation_matrix,
    one_way_anova, linear_regression, print_test_result,
    confidence_interval, chi_square_test, independent_t_test,
    cohens_d, frequency_table, multiple_linear_regression
)
from common.plot_style import (
    set_project_style, save_figure, add_result_text,
    format_p_value
)

TEAM = 'team_b'

SCORE_NAMES = {
    'introversion': '내향성 점수',
    'sensing': '감각 점수',
    'thinking': '사고 점수',
    'judging': '판단 점수',
}

SCORE_KEYS = ['introversion', 'sensing', 'thinking', 'judging']

# 차원 약어 한글
DIM_SHORT = {
    'introversion': 'EI(내향)',
    'sensing': 'SN(감각)',
    'thinking': 'TF(사고)',
    'judging': 'JP(판단)',
}


def load_and_preprocess():
    """데이터 로딩 및 전처리"""
    print("\n" + "=" * 60)
    print("  팀원 B: MBTI 차원 점수와 관심사 심층 상관분석 (강화)")
    print("=" * 60)

    data = load_personality_data()

    # 4개 차원 점수를 2D 행렬로
    scores = np.column_stack([data[k] for k in SCORE_KEYS])
    data['scores_matrix'] = scores

    # 기본 정보
    n = len(data['interest'])
    print(f"\n[데이터] 전체 표본 수: {n:,}명")
    print(f"[데이터] 차원 점수 변수: {len(SCORE_KEYS)}개")
    print(f"[데이터] 추가 변수: personality(MBTI유형), gender(성별)")

    # 관심사 분포
    print("\n[EDA] 관심사 분야별 분포:")
    interests = np.unique(data['interest'])
    for interest in sorted(interests):
        count = np.sum(data['interest'] == interest)
        pct = count / n * 100
        print(f"  {interest:12s}: {count:>6,}명 ({pct:5.1f}%)")

    # 성별 분포
    print("\n[EDA] 성별 분포:")
    for g in sorted(np.unique(data['gender'])):
        count = np.sum(data['gender'] == g)
        pct = count / n * 100
        print(f"  {g:12s}: {count:>6,}명 ({pct:5.1f}%)")

    # 차원 점수 기본 통계
    print("\n[EDA] 차원 점수 기술통계:")
    for key in SCORE_KEYS:
        stats = descriptive_stats(data[key])
        print(f"  {SCORE_NAMES[key]:12s}: 평균={stats['평균']:.3f}, "
              f"SD={stats['표준편차']:.3f}, "
              f"범위=[{stats['최소']:.1f}, {stats['최대']:.1f}], "
              f"왜도={stats['왜도']:.3f}, 첨도={stats['첨도']:.3f}")

    # 차원 점수 간 사분위 범위 비교
    print("\n[EDA] 차원 점수 IQR 비교:")
    for key in SCORE_KEYS:
        stats = descriptive_stats(data[key])
        print(f"  {SCORE_NAMES[key]:12s}: Q1={stats['Q1']:.2f}, "
              f"중앙값={stats['중앙값']:.2f}, Q3={stats['Q3']:.2f}, "
              f"IQR={stats['IQR']:.2f}")

    return data


# ============================================================
# 분석 1: 차원 점수 탐색적 분석 (EDA)
# ============================================================
def analyze_dimension_score_eda(data):
    """4개 MBTI 차원 점수 탐색적 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 1: MBTI 차원 점수 탐색적 데이터 분석")
    print("━" * 60)

    # === 시각화 1: 히스토그램 ===
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('MBTI 4개 차원 점수 분포', fontsize=26, fontweight='bold')

    colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12']
    for idx, key in enumerate(SCORE_KEYS):
        ax = axes[idx // 2, idx % 2]
        values = data[key]
        stats = descriptive_stats(values)
        ci = confidence_interval(values)

        ax.hist(values, bins=50, color=colors[idx], alpha=0.7,
                edgecolor='white', density=True)
        ax.axvline(stats['평균'], color='red', linestyle='--', linewidth=2,
                   label=f'평균: {stats["평균"]:.2f}')
        ax.axvline(stats['중앙값'], color='blue', linestyle=':',
                   linewidth=2, label=f'중앙값: {stats["중앙값"]:.2f}')

        # 95% CI 영역 표시
        ax.axvspan(ci['lower'], ci['upper'], alpha=0.15, color='red',
                   label=f'95% CI: [{ci["lower"]:.3f}, {ci["upper"]:.3f}]')

        ax.set_title(f'{SCORE_NAMES[key]}', fontsize=20)
        ax.set_xlabel('점수')
        ax.set_ylabel('밀도')
        ax.legend(fontsize=14, loc='upper right')

        info = (f"n={stats['n']:,}\nσ={stats['표준편차']:.3f}\n"
                f"왜도={stats['왜도']:.3f}\n첨도={stats['첨도']:.3f}")
        add_result_text(ax, info, position='top_left')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b1_dimension_histograms.png')

    # === 시각화 2: Scatter Matrix ===
    fig, axes = plt.subplots(4, 4, figsize=(16, 16))
    fig.suptitle('MBTI 차원 점수 산점도 행렬', fontsize=26,
                 fontweight='bold', y=1.01)

    score_labels = [SCORE_NAMES[k] for k in SCORE_KEYS]
    np.random.seed(42)

    for i in range(4):
        for j in range(4):
            ax = axes[i, j]
            if i == j:
                # 대각선: 히스토그램
                ax.hist(data[SCORE_KEYS[i]], bins=40, color=colors[i],
                        alpha=0.7, edgecolor='white')
                ax.set_ylabel('빈도' if j == 0 else '')
            elif i > j:
                # 하삼각: 상관계수 + 강도 표시
                r_result = pearson_correlation(data[SCORE_KEYS[j]],
                                               data[SCORE_KEYS[i]])
                r_val = r_result['r']
                # 배경색으로 상관 강도 표현
                bg_color = plt.cm.RdBu_r((r_val + 1) / 2)
                ax.set_facecolor((*bg_color[:3], 0.2))
                ax.text(0.5, 0.5,
                        f'r = {r_val:.3f}\n{format_p_value(r_result["p_value"])}\n'
                        f'({r_result["strength"]})',
                        ha='center', va='center', fontsize=18,
                        fontweight='bold', transform=ax.transAxes,
                        color='red' if r_result['significant'] else 'gray')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
            else:
                # 상삼각: 산점도 (샘플링)
                n_sample = min(2000, len(data[SCORE_KEYS[j]]))
                idx_sample = np.random.choice(len(data[SCORE_KEYS[j]]),
                                               n_sample, replace=False)
                ax.scatter(data[SCORE_KEYS[j]][idx_sample],
                           data[SCORE_KEYS[i]][idx_sample],
                           alpha=0.2, s=5, color='#2C3E50')

            if i == 3:
                ax.set_xlabel(score_labels[j], fontsize=15)
            if j == 0:
                ax.set_ylabel(score_labels[i], fontsize=15)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b2_scatter_matrix.png')


# ============================================================
# 분석 2: 관심사별 차원 점수 비교 (ANOVA)
# ============================================================
def analyze_interest_by_dimension(data):
    """관심사 분야별 MBTI 차원 점수 차이 검정"""
    print("\n\n" + "━" * 60)
    print("  분석 2: 관심사별 MBTI 차원 점수 비교")
    print("━" * 60)
    print("  H0: 관심사 분야에 따른 MBTI 차원 점수 차이는 없다")
    print("  H1: 적어도 하나의 분야에서 차원 점수가 유의하게 다르다")

    interest = data['interest']
    interest_list = sorted(np.unique(interest))

    anova_results = {}

    for key in SCORE_KEYS:
        groups = [data[key][interest == cat] for cat in interest_list]
        result = one_way_anova(*groups)
        anova_results[key] = result
        print_test_result(f"ANOVA: {SCORE_NAMES[key]} × 관심사", result)

        # 관심사별 평균 + CI
        print(f"  관심사별 평균 [95% CI]:")
        for cat, m, s in zip(interest_list, result['group_means'],
                              result['group_stds']):
            n_cat = np.sum(interest == cat)
            ci = confidence_interval(data[key][interest == cat])
            print(f"    {cat:12s}: {m:.3f} ± {s:.3f} "
                  f"[{ci['lower']:.3f}, {ci['upper']:.3f}] (n={n_cat:,})")

    # === 시각화 3: Box Plot (향상) ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('관심사별 MBTI 차원 점수 분포', fontsize=26,
                 fontweight='bold')

    for idx, key in enumerate(SCORE_KEYS):
        ax = axes[idx // 2, idx % 2]

        box_data = [data[key][interest == cat] for cat in interest_list]
        bp = ax.boxplot(box_data, labels=interest_list, patch_artist=True,
                        medianprops=dict(color='black', linewidth=2),
                        showmeans=True,
                        meanprops=dict(marker='D', markerfacecolor='red',
                                       markeredgecolor='red', markersize=8))

        for patch, cat in zip(bp['boxes'], interest_list):
            patch.set_facecolor(INTEREST_COLORS.get(cat, '#95A5A6'))
            patch.set_alpha(0.7)

        # 평균값 주석
        for i, cat in enumerate(interest_list):
            mean_val = np.mean(data[key][interest == cat])
            ax.annotate(f'{mean_val:.2f}', xy=(i + 1, mean_val),
                        xytext=(15, 5), textcoords='offset points',
                        fontsize=14, color='red', fontweight='bold')

        res = anova_results[key]
        sig_marker = '***' if res['p_value'] < 0.001 else (
            '**' if res['p_value'] < 0.01 else (
                '*' if res['p_value'] < 0.05 else 'ns'))
        ax.set_title(f'{SCORE_NAMES[key]} {sig_marker}\n'
                     f'F={res["f_stat"]:.2f}, '
                     f'{format_p_value(res["p_value"])}, '
                     f'η²={res["eta_squared"]:.4f}',
                     fontsize=20)
        ax.set_ylabel('점수')
        ax.tick_params(axis='x', rotation=30)

        # 범례: 빨간 다이아 = 평균
        ax.plot([], [], 'rD', markersize=8, label='평균')
        ax.legend(fontsize=15, loc='upper left')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b3_interest_dimension_boxplot.png')

    # === 시각화 4: Radar Chart (향상) ===
    fig, ax = plt.subplots(figsize=(10, 10),
                           subplot_kw=dict(projection='polar'))
    fig.suptitle('관심사별 MBTI 차원 점수 프로필',
                 fontsize=26, fontweight='bold', y=1.02)

    angles = np.linspace(0, 2 * np.pi, len(SCORE_KEYS),
                         endpoint=False).tolist()
    angles += angles[:1]

    # 전체 평균선 추가
    overall_means = [np.mean(data[key]) for key in SCORE_KEYS]
    overall_means += overall_means[:1]
    ax.plot(angles, overall_means, '--', linewidth=3, color='gray',
            alpha=0.6, label='전체 평균')

    for cat in interest_list:
        if cat == 'Unknown':
            continue
        values = [np.mean(data[key][interest == cat]) for key in SCORE_KEYS]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2, label=cat,
                color=INTEREST_COLORS.get(cat, '#95A5A6'), markersize=8)
        ax.fill(angles, values, alpha=0.08,
                color=INTEREST_COLORS.get(cat, '#95A5A6'))

    labels = [SCORE_NAMES[k] for k in SCORE_KEYS]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=18)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.05), fontsize=16)
    ax.set_ylim(0, max(overall_means) * 1.3)

    save_figure(fig, TEAM, 'fig_b4_interest_radar.png')

    return anova_results


# ============================================================
# 분석 3: 차원 점수 간 상관관계
# ============================================================
def analyze_dimension_correlations(data):
    """차원 점수 간 상관관계 심층 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 3: MBTI 차원 점수 간 상관관계")
    print("━" * 60)
    print("  H0: MBTI 4개 차원 점수는 서로 독립이다")
    print("  H1: 특정 차원 쌍 간에 유의한 상관관계가 존재한다")

    # 상관계수 행렬
    corr_mat = correlation_matrix(data['scores_matrix'])
    print("\n  [상관계수 행렬]")
    labels = [SCORE_NAMES[k] for k in SCORE_KEYS]
    header = f"{'':14s}" + "".join(f"{l:>14s}" for l in labels)
    print(f"  {header}")
    for i, l in enumerate(labels):
        row = f"  {l:14s}" + "".join(
            f"{corr_mat[i,j]:14.4f}" for j in range(4))
        print(row)

    # 모든 쌍 상관분석
    print("\n  [차원 쌍별 상관분석 결과]")
    pair_results = {}
    for i in range(4):
        for j in range(i + 1, 4):
            result = pearson_correlation(data[SCORE_KEYS[i]],
                                          data[SCORE_KEYS[j]])
            pair_key = f"{SCORE_KEYS[i]}-{SCORE_KEYS[j]}"
            pair_results[pair_key] = result
            sig = "유의 ✓" if result['significant'] else "유의하지 않음 ✗"
            print(f"    {SCORE_NAMES[SCORE_KEYS[i]]} × "
                  f"{SCORE_NAMES[SCORE_KEYS[j]]}: "
                  f"r = {result['r']:.4f}, "
                  f"{format_p_value(result['p_value'])}, "
                  f"{result['strength']} ({sig})")

    # === 시각화 5: Correlation Heatmap (향상) ===
    fig, ax = plt.subplots(figsize=(10, 8))

    mask = np.triu(np.ones_like(corr_mat, dtype=bool), k=1)
    sns.heatmap(corr_mat, mask=mask, annot=True, fmt='.4f',
                cmap='RdBu_r', center=0, square=True,
                xticklabels=labels, yticklabels=labels,
                ax=ax, linewidths=1.0,
                vmin=-0.5, vmax=0.5,
                annot_kws={'fontsize': 16, 'fontweight': 'bold'})

    # 유의성 표시 추가
    for i in range(4):
        for j in range(i):
            pair_key = f"{SCORE_KEYS[j]}-{SCORE_KEYS[i]}"
            if pair_key in pair_results:
                res = pair_results[pair_key]
                if res['significant']:
                    sig_star = '***' if res['p_value'] < 0.001 else (
                        '**' if res['p_value'] < 0.01 else '*')
                    ax.text(j + 0.5, i + 0.75, sig_star,
                            ha='center', va='center',
                            fontsize=15, color='white',
                            fontweight='bold')

    ax.set_title('MBTI 차원 점수 간 상관계수 행렬\n'
                 '(* p<.05, ** p<.01, *** p<.001)',
                 fontsize=24, fontweight='bold')

    save_figure(fig, TEAM, 'fig_b5_correlation_heatmap.png')

    return pair_results, corr_mat


# ============================================================
# 분석 4: 주요 차원 쌍 회귀분석
# ============================================================
def analyze_regression_patterns(data):
    """주요 차원 점수 간 회귀분석"""
    print("\n\n" + "━" * 60)
    print("  분석 4: 차원 점수 간 회귀분석")
    print("━" * 60)
    print("  H3: 특정 차원 점수 쌍 간에 유의한 선형 관계가 존재한다")

    pairs = [
        ('introversion', 'thinking'),
        ('sensing', 'judging'),
        ('introversion', 'sensing'),
    ]

    reg_results = {}

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('MBTI 차원 점수 간 회귀분석', fontsize=26,
                 fontweight='bold')

    np.random.seed(42)

    for idx, (x_key, y_key) in enumerate(pairs):
        ax = axes[idx]
        x_data = data[x_key]
        y_data = data[y_key]

        reg_result = linear_regression(x_data, y_data)
        pair_name = f"{x_key}-{y_key}"
        reg_results[pair_name] = reg_result
        print_test_result(
            f"회귀: {SCORE_NAMES[y_key]} ~ {SCORE_NAMES[x_key]}",
            reg_result)

        # 산점도 (샘플링)
        n_sample = min(3000, len(x_data))
        sample_idx = np.random.choice(len(x_data), n_sample, replace=False)

        ax.scatter(x_data[sample_idx], y_data[sample_idx],
                   alpha=0.12, s=8, color='#2C3E50', label=f'n={n_sample}')

        # 회귀선
        x_line = np.linspace(np.min(x_data), np.max(x_data), 100)
        y_line = reg_result['slope'] * x_line + reg_result['intercept']
        ax.plot(x_line, y_line, 'r-', linewidth=2.5, label='회귀선')

        # 잔차 표준오차 밴드
        residual_std = np.std(reg_result['residuals'])
        ax.fill_between(x_line, y_line - residual_std,
                         y_line + residual_std,
                         alpha=0.15, color='red', label='±1σ 범위')

        ax.set_xlabel(SCORE_NAMES[x_key])
        ax.set_ylabel(SCORE_NAMES[y_key])
        ax.set_title(f'{SCORE_NAMES[x_key]} → {SCORE_NAMES[y_key]}',
                     fontsize=20)

        sig = '***' if reg_result['p_value'] < 0.001 else ''
        info = (f"y = {reg_result['slope']:.4f}x "
                f"+ {reg_result['intercept']:.4f}\n"
                f"R² = {reg_result['r_squared']:.4f} {sig}\n"
                f"{format_p_value(reg_result['p_value'])}")
        add_result_text(ax, info)
        ax.legend(fontsize=14)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b6_regression_by_interest.png')

    return reg_results


# ============================================================
# 분석 5: 관심사 그룹 프로필 비교
# ============================================================
def analyze_interest_profile(data):
    """관심사별 차원 점수 프로필 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 5: 관심사 그룹 프로필 비교")
    print("━" * 60)

    interest = data['interest']
    interest_list = [cat for cat in sorted(np.unique(interest))
                     if cat != 'Unknown']

    # 그룹별 평균 벡터
    centroids = np.zeros((len(interest_list), 4))
    for i, cat in enumerate(interest_list):
        mask = interest == cat
        for j, key in enumerate(SCORE_KEYS):
            centroids[i, j] = np.mean(data[key][mask])

    # 유클리드 거리 행렬
    n_groups = len(interest_list)
    dist_matrix = np.zeros((n_groups, n_groups))
    for i in range(n_groups):
        for j in range(n_groups):
            dist_matrix[i, j] = np.sqrt(
                np.sum((centroids[i] - centroids[j]) ** 2))

    print("\n  [관심사 간 유클리드 거리 (중심점 기반)]")
    header = f"{'':12s}" + "".join(f"{c:>12s}" for c in interest_list)
    print(f"  {header}")
    for i, cat in enumerate(interest_list):
        row = f"  {cat:12s}" + "".join(
            f"{dist_matrix[i,j]:12.4f}" for j in range(n_groups))
        print(row)

    # 가장 유사/이질적 관심사 쌍
    max_d, min_d = 0, np.inf
    max_pair, min_pair = ('', ''), ('', '')
    for i in range(n_groups):
        for j in range(i + 1, n_groups):
            d = dist_matrix[i, j]
            if d > max_d:
                max_d = d
                max_pair = (interest_list[i], interest_list[j])
            if d < min_d:
                min_d = d
                min_pair = (interest_list[i], interest_list[j])

    print(f"\n  가장 유사한 관심사 쌍: "
          f"{min_pair[0]} ↔ {min_pair[1]} (d={min_d:.4f})")
    print(f"  가장 이질적 관심사 쌍: "
          f"{max_pair[0]} ↔ {max_pair[1]} (d={max_d:.4f})")

    # === 시각화 7: Parallel Coordinates (향상) ===
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle('관심사별 MBTI 차원 점수 프로필 비교',
                 fontsize=26, fontweight='bold')

    x_pos = np.arange(len(SCORE_KEYS))
    labels = [SCORE_NAMES[k] for k in SCORE_KEYS]

    # 전체 평균 기준선
    overall = np.array([np.mean(data[k]) for k in SCORE_KEYS])
    ax.plot(x_pos, overall, '--', linewidth=3, color='gray', alpha=0.5,
            label='전체 평균', zorder=1)
    ax.fill_between(x_pos, overall - 0.05, overall + 0.05,
                     alpha=0.1, color='gray')

    for i, cat in enumerate(interest_list):
        color = INTEREST_COLORS.get(cat, '#95A5A6')
        ax.plot(x_pos, centroids[i], 'o-', linewidth=2.5, markersize=10,
                label=cat, color=color, zorder=2)

        # 값 주석
        for j, val in enumerate(centroids[i]):
            offset = 0.03 if val >= overall[j] else -0.06
            ax.annotate(f'{val:.2f}', xy=(j, val + offset),
                        fontsize=13, ha='center', color=color,
                        fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=18)
    ax.set_ylabel('평균 점수', fontsize=20)
    ax.legend(fontsize=16, loc='upper right')
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_title('관심사 그룹 중심점(centroid) 비교', fontsize=22)

    save_figure(fig, TEAM, 'fig_b7_interest_profile_parallel.png')

    return centroids, dist_matrix, interest_list


# ============================================================
# 분석 6: 관심사별 KDE 밀도 + 95% CI Error Bar (통합)
# ============================================================
def analyze_kde_and_ci(data):
    """관심사별 차원 점수 분포 KDE + 평균 신뢰구간 통합"""
    print("\n\n" + "━" * 60)
    print("  분석 6: 관심사별 차원 점수 KDE 밀도 + 95% CI 통합")
    print("━" * 60)

    interest = data['interest']
    interest_list = [c for c in sorted(np.unique(interest))
                     if c != 'Unknown']

    fig, axes = plt.subplots(4, 2, figsize=(18, 20))
    fig.suptitle('관심사별 MBTI 차원 점수: KDE 밀도 분포 (좌) + 95% CI (우)',
                 fontsize=26, fontweight='bold')

    for idx, key in enumerate(SCORE_KEYS):
        # === 좌: KDE 밀도 오버레이 ===
        ax_kde = axes[idx, 0]

        for cat in interest_list:
            values = data[key][interest == cat]
            color = INTEREST_COLORS.get(cat, '#95A5A6')
            sns.kdeplot(values, ax=ax_kde, color=color, linewidth=2,
                        label=f'{cat} (μ={np.mean(values):.2f})')

        overall_mean = np.mean(data[key])
        ax_kde.axvline(overall_mean, color='gray', linestyle='--',
                       linewidth=2, alpha=0.6,
                       label=f'전체 평균={overall_mean:.2f}')

        ax_kde.set_title(f'{SCORE_NAMES[key]} — 밀도 분포', fontsize=20)
        ax_kde.set_xlabel('점수')
        ax_kde.set_ylabel('밀도')
        ax_kde.legend(fontsize=13)

        # === 우: 95% CI Error Bar ===
        ax_ci = axes[idx, 1]

        means = []
        ci_lowers = []
        ci_uppers = []
        colors_list = []

        for cat in interest_list:
            values = data[key][interest == cat]
            ci = confidence_interval(values)
            means.append(ci['mean'])
            ci_lowers.append(ci['mean'] - ci['lower'])
            ci_uppers.append(ci['upper'] - ci['mean'])
            colors_list.append(INTEREST_COLORS.get(cat, '#95A5A6'))

        means_arr = np.array(means)
        errors = np.array([ci_lowers, ci_uppers])

        # 정렬: 평균 높은 순
        sort_idx = np.argsort(means_arr)[::-1]
        sorted_cats = [interest_list[i] for i in sort_idx]
        sorted_means = means_arr[sort_idx]
        sorted_errors = errors[:, sort_idx]
        sorted_colors = [colors_list[i] for i in sort_idx]

        y_pos = np.arange(len(sorted_cats))
        ax_ci.barh(y_pos, sorted_means, xerr=sorted_errors,
                   color=sorted_colors, alpha=0.8, edgecolor='white',
                   capsize=5, error_kw={'linewidth': 2})

        # 전체 평균선
        ax_ci.axvline(overall_mean, color='red', linestyle='--',
                      linewidth=2, alpha=0.6)
        ax_ci.text(overall_mean, len(sorted_cats) - 0.5,
                   f'전체\n{overall_mean:.3f}',
                   fontsize=13, color='red', ha='center', fontweight='bold')

        for j, m in enumerate(sorted_means):
            ax_ci.text(m + 0.005, j, f'{m:.3f}', va='center',
                       fontsize=14, fontweight='bold')

        ax_ci.set_yticks(y_pos)
        ax_ci.set_yticklabels(sorted_cats, fontsize=15)
        ax_ci.set_xlabel('평균 점수')
        ax_ci.set_title(f'{SCORE_NAMES[key]} — 평균 ± 95% CI', fontsize=20)
        ax_ci.invert_yaxis()

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b8_kde_and_ci_combined.png')

    # 관심사 간 차이 보고
    print("\n  [관심사별 차원 점수 평균 차이 요약]")
    for key in SCORE_KEYS:
        means_dict = {cat: np.mean(data[key][interest == cat])
                      for cat in interest_list}
        max_cat = max(means_dict, key=means_dict.get)
        min_cat = min(means_dict, key=means_dict.get)
        diff = means_dict[max_cat] - means_dict[min_cat]
        print(f"  {SCORE_NAMES[key]:12s}: "
              f"최고={max_cat}({means_dict[max_cat]:.3f}), "
              f"최저={min_cat}({means_dict[min_cat]:.3f}), "
              f"차이={diff:.3f}")


# ============================================================
# 분석 7: MBTI 유형(범주) × 관심사 교차분석 (NEW)
# ============================================================
def analyze_mbti_type_interest(data):
    """MBTI 16유형(범주)과 관심사 간 독립성 검정"""
    print("\n\n" + "━" * 60)
    print("  분석 7: MBTI 유형(범주) × 관심사 교차분석 (NEW)")
    print("━" * 60)
    print("  H0: MBTI 유형과 관심사 분야는 독립이다")
    print("  H5: MBTI 유형과 관심사 분야는 독립이 아니다 (연관 있음)")

    personality = data['personality']
    interest = data['interest']

    # Unknown 제외
    interest_list = [c for c in sorted(np.unique(interest))
                     if c != 'Unknown']
    mask_known = np.isin(interest, interest_list)
    personality_known = personality[mask_known]
    interest_known = interest[mask_known]

    # 16 MBTI × 4 Interest 교차표
    mbti_types = sorted(np.unique(personality_known))
    cross_tab = np.zeros((len(mbti_types), len(interest_list)))
    for i, mbti in enumerate(mbti_types):
        for j, cat in enumerate(interest_list):
            cross_tab[i, j] = np.sum(
                (personality_known == mbti) & (interest_known == cat))

    # 카이제곱 독립성 검정
    chi2_result = chi_square_test(cross_tab)
    print_test_result("카이제곱 독립성: MBTI유형 × 관심사", chi2_result)

    # Cramer's V (이미 chi_square_test에 포함)
    print(f"  Cramer's V = {chi2_result['cramers_v']:.4f}")

    # 행별 비율 계산
    row_totals = cross_tab.sum(axis=1, keepdims=True)
    row_pct = cross_tab / row_totals * 100

    # 표준화 잔차 계산: (O - E) / sqrt(E)
    expected = chi2_result['expected']
    std_residuals = (cross_tab - expected) / np.sqrt(expected)

    # 어떤 MBTI-관심사 조합이 특이한가?
    print("\n  [표준화 잔차 상위/하위 5개 조합]")
    flat_idx = np.argsort(std_residuals.ravel())
    n_flat = len(flat_idx)
    print("  ── 과대대표 (기대보다 많음) ──")
    for k in range(1, 6):
        idx = flat_idx[n_flat - k]
        i, j = divmod(idx, len(interest_list))
        print(f"    {mbti_types[i]:5s} × {interest_list[j]:12s}: "
              f"잔차={std_residuals[i, j]:+.2f}, "
              f"관측={cross_tab[i,j]:.0f}, 기대={expected[i,j]:.1f}")
    print("  ── 과소대표 (기대보다 적음) ──")
    for k in range(5):
        idx = flat_idx[k]
        i, j = divmod(idx, len(interest_list))
        print(f"    {mbti_types[i]:5s} × {interest_list[j]:12s}: "
              f"잔차={std_residuals[i, j]:+.2f}, "
              f"관측={cross_tab[i,j]:.0f}, 기대={expected[i,j]:.1f}")

    # === 시각화 9: 표준화 잔차 Heatmap ===
    fig, ax = plt.subplots(figsize=(12, 10))

    sns.heatmap(std_residuals, annot=True, fmt='.1f',
                cmap='RdBu_r', center=0, square=False,
                xticklabels=interest_list, yticklabels=mbti_types,
                ax=ax, linewidths=0.5,
                vmin=-3, vmax=3,
                annot_kws={'fontsize': 14, 'fontweight': 'bold'},
                cbar_kws={'label': '표준화 잔차', 'shrink': 0.8})

    ax.set_title(
        f'MBTI 유형 × 관심사 표준화 잔차\n'
        f'χ²={chi2_result["chi2"]:.1f}, df={chi2_result["dof"]}, '
        f'{format_p_value(chi2_result["p_value"])}, '
        f"V={chi2_result['cramers_v']:.3f}",
        fontsize=22, fontweight='bold')
    ax.set_ylabel('MBTI 유형', fontsize=20)
    ax.set_xlabel('관심사 분야', fontsize=20)

    # 색상 범례 설명
    ax.text(1.02, -0.05,
            '양수(빨강): 기대보다 많음\n음수(파랑): 기대보다 적음\n'
            '|잔차|>2: 유의한 편차',
            transform=ax.transAxes, fontsize=13, va='top')

    save_figure(fig, TEAM, 'fig_b9_mbti_type_interest_residuals.png')

    return chi2_result, std_residuals, mbti_types


# ============================================================
# 분석 8: 성별 조절효과 분석 (NEW)
# ============================================================
def analyze_gender_moderator(data):
    """성별이 MBTI-관심사 관계를 조절하는지 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 8: 성별 조절효과 분석 (NEW)")
    print("━" * 60)
    print("  H0: MBTI-관심사 관계는 남녀 간 동일하다")
    print("  H6: 성별이 MBTI-관심사 관계를 조절한다 (η² 차이)")

    interest = data['interest']
    gender = data['gender']
    interest_list = [c for c in sorted(np.unique(interest))
                     if c != 'Unknown']

    genders = sorted(np.unique(gender))

    # 성별별 ANOVA η² 비교
    print("\n  [성별별 ANOVA η² 비교: 관심사 → 차원점수]")
    gender_anova = {}
    for g in genders:
        g_mask = gender == g
        gender_anova[g] = {}
        print(f"\n  === {g} (n={np.sum(g_mask):,}) ===")
        for key in SCORE_KEYS:
            groups = [data[key][g_mask & (interest == cat)]
                      for cat in interest_list]
            result = one_way_anova(*groups)
            gender_anova[g][key] = result
            sig = "✓" if result['significant'] else "✗"
            print(f"    {SCORE_NAMES[key]:12s}: "
                  f"F={result['f_stat']:7.2f}, "
                  f"η²={result['eta_squared']:.4f} {sig}")

    # η² 차이 계산
    print("\n  [η² 차이 (Male - Female)]")
    eta_diffs = {}
    for key in SCORE_KEYS:
        eta_m = gender_anova['Male'][key]['eta_squared']
        eta_f = gender_anova['Female'][key]['eta_squared']
        diff = eta_m - eta_f
        eta_diffs[key] = diff
        print(f"    {SCORE_NAMES[key]:12s}: "
              f"Male η²={eta_m:.4f}, Female η²={eta_f:.4f}, "
              f"차이={diff:+.4f}")

    # 성별 × 차원별 관심사 평균 비교
    print("\n  [성별 × 관심사별 차원 평균 t-검정]")
    gender_t_results = {}
    for key in SCORE_KEYS:
        for cat in interest_list:
            male_vals = data[key][(gender == 'Male') & (interest == cat)]
            female_vals = data[key][(gender == 'Female') & (interest == cat)]
            t_res = independent_t_test(male_vals, female_vals)
            d_res = cohens_d(male_vals, female_vals)
            gender_t_results[(key, cat)] = {**t_res, 'cohens_d_val': d_res['d']}
            sig = "✓" if t_res['significant'] else "✗"
            print(f"    {SCORE_NAMES[key]:10s} × {cat:12s}: "
                  f"d={d_res['d']:+.3f} ({d_res['interpretation']}) {sig}")

    # === 시각화 10: 성별 조절효과 비교 (2행2열) ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('성별 조절효과: 관심사별 MBTI 차원 점수 (Male vs Female)',
                 fontsize=24, fontweight='bold')

    x_pos = np.arange(len(interest_list))
    bar_width = 0.35

    for idx, key in enumerate(SCORE_KEYS):
        ax = axes[idx // 2, idx % 2]

        male_means = []
        female_means = []
        male_cis = []
        female_cis = []

        for cat in interest_list:
            m_vals = data[key][(gender == 'Male') & (interest == cat)]
            f_vals = data[key][(gender == 'Female') & (interest == cat)]
            m_ci = confidence_interval(m_vals)
            f_ci = confidence_interval(f_vals)
            male_means.append(m_ci['mean'])
            female_means.append(f_ci['mean'])
            male_cis.append(m_ci['margin_of_error'])
            female_cis.append(f_ci['margin_of_error'])

        bars_m = ax.bar(x_pos - bar_width / 2, male_means, bar_width,
                        yerr=male_cis, capsize=4,
                        color=GENDER_COLORS['Male'], alpha=0.8,
                        label='Male', edgecolor='white')
        bars_f = ax.bar(x_pos + bar_width / 2, female_means, bar_width,
                        yerr=female_cis, capsize=4,
                        color=GENDER_COLORS['Female'], alpha=0.8,
                        label='Female', edgecolor='white')

        # 값 주석
        for i, (mm, fm) in enumerate(zip(male_means, female_means)):
            ax.text(i - bar_width / 2, mm + 0.02, f'{mm:.2f}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold',
                    color=GENDER_COLORS['Male'])
            ax.text(i + bar_width / 2, fm + 0.02, f'{fm:.2f}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold',
                    color=GENDER_COLORS['Female'])

        # ANOVA η² 표시
        eta_m = gender_anova['Male'][key]['eta_squared']
        eta_f = gender_anova['Female'][key]['eta_squared']
        ax.set_title(
            f'{SCORE_NAMES[key]}\n'
            f'η² Male={eta_m:.4f}, Female={eta_f:.4f}, '
            f'Δ={eta_diffs[key]:+.4f}',
            fontsize=18)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(interest_list, fontsize=14)
        ax.set_ylabel('평균 점수')
        ax.legend(fontsize=14)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b10_gender_moderator.png')

    return gender_anova, gender_t_results, eta_diffs


# ============================================================
# 분석 9: 중심점 분류 정확도 검증 (NEW)
# ============================================================
def analyze_centroid_classifier(data):
    """중심점 기반 분류 정확도로 MBTI 예측력 검증"""
    print("\n\n" + "━" * 60)
    print("  분석 9: 중심점 분류(Nearest Centroid) 정확도 검증 (NEW)")
    print("━" * 60)
    print("  질문: MBTI 4차원 점수로 관심사를 실제로 예측할 수 있는가?")
    print("  방법: 각 관심사 중심점 → 가장 가까운 중심점으로 분류")

    interest = data['interest']
    interest_list = [c for c in sorted(np.unique(interest))
                     if c != 'Unknown']
    mask_known = np.isin(interest, interest_list)

    scores = data['scores_matrix'][mask_known]
    labels = interest[mask_known]
    n_total = len(labels)

    # 중심점 계산
    centroids = np.zeros((len(interest_list), 4))
    for i, cat in enumerate(interest_list):
        cat_mask = labels == cat
        centroids[i] = np.mean(scores[cat_mask], axis=0)

    # 분류: 각 샘플 → 가장 가까운 중심점
    predictions = []
    for sample in scores:
        dists = np.sqrt(np.sum((centroids - sample) ** 2, axis=1))
        pred_idx = np.argmin(dists)
        predictions.append(interest_list[pred_idx])
    predictions = np.array(predictions)

    # 정확도
    accuracy = np.mean(predictions == labels)
    chance_level = 1.0 / len(interest_list)

    print(f"\n  [분류 결과]")
    print(f"  전체 정확도: {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"  우연 수준 (1/{len(interest_list)}): "
          f"{chance_level:.4f} ({chance_level*100:.1f}%)")
    print(f"  향상도: {accuracy/chance_level:.2f}배")

    # Confusion Matrix 계산
    n_classes = len(interest_list)
    conf_matrix = np.zeros((n_classes, n_classes), dtype=int)
    for true_label, pred_label in zip(labels, predictions):
        i = interest_list.index(true_label)
        j = interest_list.index(pred_label)
        conf_matrix[i, j] += 1

    # 클래스별 정확도
    print(f"\n  [클래스별 분류 결과]")
    print(f"  {'실제 관심사':12s} {'정확도':>8s} {'n':>8s}  예측 분포")
    for i, cat in enumerate(interest_list):
        row_total = conf_matrix[i].sum()
        class_acc = conf_matrix[i, i] / row_total if row_total > 0 else 0
        pred_dist = ", ".join(
            f"{interest_list[j]}:{conf_matrix[i,j]}"
            for j in range(n_classes) if conf_matrix[i, j] > 0)
        print(f"  {cat:12s} {class_acc:7.1%} {row_total:>8,}  {pred_dist}")

    # 비율 Confusion Matrix (행 기준 정규화)
    conf_pct = conf_matrix / conf_matrix.sum(axis=1, keepdims=True) * 100

    # === 시각화 11: Confusion Matrix ===
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(
        f'중심점 분류(Nearest Centroid): MBTI 점수 → 관심사 예측\n'
        f'정확도={accuracy:.1%} (우연 수준={chance_level:.1%}, '
        f'향상도={accuracy/chance_level:.2f}배)',
        fontsize=22, fontweight='bold')

    # 좌: 빈도 Confusion Matrix
    sns.heatmap(conf_matrix, annot=True, fmt='d',
                cmap='Blues', square=True,
                xticklabels=interest_list, yticklabels=interest_list,
                ax=ax1, linewidths=1,
                annot_kws={'fontsize': 16, 'fontweight': 'bold'})
    ax1.set_title('Confusion Matrix (빈도)', fontsize=20)
    ax1.set_ylabel('실제 관심사', fontsize=18)
    ax1.set_xlabel('예측 관심사', fontsize=18)

    # 우: 비율 Confusion Matrix
    sns.heatmap(conf_pct, annot=True, fmt='.1f',
                cmap='YlOrRd', square=True,
                xticklabels=interest_list, yticklabels=interest_list,
                ax=ax2, linewidths=1, vmin=0, vmax=100,
                annot_kws={'fontsize': 16, 'fontweight': 'bold'})
    ax2.set_title('Confusion Matrix (행 비율 %)', fontsize=20)
    ax2.set_ylabel('실제 관심사', fontsize=18)
    ax2.set_xlabel('예측 관심사', fontsize=18)

    # 대각선 강조
    for ax in [ax1, ax2]:
        for i in range(n_classes):
            ax.add_patch(plt.Rectangle((i, i), 1, 1, fill=False,
                                        edgecolor='red', linewidth=3))

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b11_centroid_classifier.png')

    return {
        'accuracy': accuracy,
        'chance_level': chance_level,
        'improvement': accuracy / chance_level,
        'conf_matrix': conf_matrix,
    }


# ============================================================
# 분석 10: 관심사 색상 산점도
# ============================================================
def analyze_scatter_by_interest(data):
    """관심사별 색상 구분 산점도 (대표 차원 쌍)"""
    print("\n\n" + "━" * 60)
    print("  분석 10: 관심사별 차원 점수 산점도")
    print("━" * 60)

    pairs = [
        ('introversion', 'thinking'),
        ('sensing', 'judging'),
        ('introversion', 'judging'),
    ]

    interest = data['interest']
    interest_list = [c for c in sorted(np.unique(interest))
                     if c != 'Unknown']

    fig, axes = plt.subplots(1, 3, figsize=(20, 7))
    fig.suptitle('관심사별 MBTI 차원 점수 산점도',
                 fontsize=26, fontweight='bold')

    np.random.seed(42)

    for idx, (x_key, y_key) in enumerate(pairs):
        ax = axes[idx]

        for cat in interest_list:
            mask = interest == cat
            x_vals = data[x_key][mask]
            y_vals = data[y_key][mask]

            # 샘플링
            n_cat = len(x_vals)
            n_sample = min(800, n_cat)
            sample_idx = np.random.choice(n_cat, n_sample, replace=False)

            color = INTEREST_COLORS.get(cat, '#95A5A6')
            ax.scatter(x_vals[sample_idx], y_vals[sample_idx],
                       alpha=0.25, s=15, color=color, label=cat)

            # 그룹 중심점 마커
            cx = np.mean(x_vals)
            cy = np.mean(y_vals)
            ax.scatter(cx, cy, s=200, color=color, marker='*',
                       edgecolors='black', linewidth=1.5, zorder=5)

        ax.set_xlabel(SCORE_NAMES[x_key])
        ax.set_ylabel(SCORE_NAMES[y_key])
        ax.set_title(f'{DIM_SHORT[x_key]} × {DIM_SHORT[y_key]}',
                     fontsize=20)
        ax.legend(fontsize=14, loc='best')

    # ★ = 그룹 중심점 범례
    axes[2].scatter([], [], s=200, color='gray', marker='*',
                     edgecolors='black', linewidth=1.5,
                     label='중심점(★)')
    axes[2].legend(fontsize=14, loc='best')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_b12_scatter_by_interest.png')


# ============================================================
# 분석 11: 관심사 간 유클리드 거리 Heatmap
# ============================================================
def analyze_distance_heatmap(centroids, dist_matrix, interest_list):
    """관심사 간 유클리드 거리 히트맵"""
    print("\n\n" + "━" * 60)
    print("  분석 11: 관심사 간 유클리드 거리 히트맵")
    print("━" * 60)

    fig, ax = plt.subplots(figsize=(9, 7))

    sns.heatmap(dist_matrix, annot=True, fmt='.3f',
                cmap='YlOrRd', square=True,
                xticklabels=interest_list, yticklabels=interest_list,
                ax=ax, linewidths=1.0,
                annot_kws={'fontsize': 16, 'fontweight': 'bold'})

    ax.set_title('관심사 그룹 간 유클리드 거리\n'
                 '(4차원 중심점 기반)',
                 fontsize=24, fontweight='bold')

    save_figure(fig, TEAM, 'fig_b13_distance_heatmap.png')

    # 거리 해석
    flat_dists = dist_matrix[np.triu_indices_from(dist_matrix, k=1)]
    print(f"\n  거리 통계: 평균={np.mean(flat_dists):.4f}, "
          f"SD={np.std(flat_dists):.4f}, "
          f"범위=[{np.min(flat_dists):.4f}, {np.max(flat_dists):.4f}]")


# ============================================================
# 분석 14: 정규성 검정 + 비모수 검증 (Scipy)
# ============================================================
def analyze_normality_and_nonparametric(data):
    """Shapiro-Wilk 정규성 검정 + Kruskal-Wallis 비모수 ANOVA 검증"""
    print("\n\n" + "━" * 60)
    print("  분석 14: 정규성 검정 + 비모수 검증 (Scipy)")
    print("━" * 60)

    interest_arr = data['interest']
    interests = ['Arts', 'Sports', 'Technology', 'Others']
    known_mask = np.isin(interest_arr, interests)

    normality_results = {}
    kw_results = {}

    for key in SCORE_KEYS:
        scores = data[key]
        known_scores = scores[known_mask]

        # Shapiro-Wilk (서브샘플 5000)
        rng = np.random.RandomState(42)
        sub_idx = rng.choice(len(known_scores), size=min(5000, len(known_scores)),
                             replace=False)
        subsample = known_scores[sub_idx]
        w_stat, sw_p = sp_stats.shapiro(subsample)
        normality_results[key] = {'w_stat': w_stat, 'p_value': sw_p}

        # Kruskal-Wallis
        groups = [scores[interest_arr == g] for g in interests]
        h_stat, kw_p = sp_stats.kruskal(*groups)

        # 기존 ANOVA 비교
        anova = one_way_anova(*groups)
        kw_results[key] = {
            'h_stat': h_stat, 'kw_p': kw_p,
            'f_stat': anova['f_stat'], 'anova_p': anova['p_value'],
            'eta_squared': anova['eta_squared'],
        }

        print(f"\n  [{SCORE_NAMES[key]}]")
        print(f"    Shapiro-Wilk: W={w_stat:.4f}, p={sw_p:.6f} "
              f"({'비정규' if sw_p < 0.05 else '정규'})")
        print(f"    ANOVA:         F={anova['f_stat']:.4f}, p={anova['p_value']:.6f}")
        print(f"    Kruskal-Wallis: H={h_stat:.4f}, p={kw_p:.6f}")
        agree = ((anova['p_value'] < 0.05) == (kw_p < 0.05))
        print(f"    결론 일치: {'✓ 동일' if agree else '✗ 불일치'}")

    # === 시각화 fig_b16 ===
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle('정규성 검정 + 비모수 검증 (Scipy 활용)',
                 fontsize=26, fontweight='bold')

    # 좌: QQ-plot (대표: introversion)
    ax = axes[0]
    intro_known = data['introversion'][known_mask]
    rng = np.random.RandomState(42)
    sub = intro_known[rng.choice(len(intro_known), 5000, replace=False)]
    sorted_data = np.sort(sub)
    n = len(sorted_data)
    theoretical_q = sp_stats.norm.ppf(np.arange(1, n + 1) / (n + 1))
    ax.scatter(theoretical_q, sorted_data, s=5, alpha=0.3, color='#3498DB')
    z_range = np.array([theoretical_q.min(), theoretical_q.max()])
    ax.plot(z_range, z_range * np.std(sub) + np.mean(sub),
            'r-', linewidth=2, label='이론선')
    sw = normality_results['introversion']
    ax.set_title(f"QQ-Plot: 내향성 점수\n(Shapiro W={sw['w_stat']:.4f}, "
                 f"p={sw['p_value']:.4f})", fontsize=18)
    ax.set_xlabel('이론적 분위수', fontsize=16)
    ax.set_ylabel('관측값', fontsize=16)
    ax.legend(fontsize=14)
    ax.grid(True, alpha=0.3)

    # 우: ANOVA vs Kruskal-Wallis 비교
    ax = axes[1]
    dim_labels = [SCORE_NAMES[k] for k in SCORE_KEYS]
    x_pos = np.arange(len(SCORE_KEYS))
    width = 0.35

    anova_ps = [-np.log10(max(kw_results[k]['anova_p'], 1e-300))
                for k in SCORE_KEYS]
    kw_ps = [-np.log10(max(kw_results[k]['kw_p'], 1e-300))
             for k in SCORE_KEYS]

    ax.bar(x_pos - width/2, anova_ps, width, label='ANOVA (-log₁₀p)',
           color='#E74C3C', alpha=0.8)
    ax.bar(x_pos + width/2, kw_ps, width, label='Kruskal-Wallis (-log₁₀p)',
           color='#3498DB', alpha=0.8)
    ax.axhline(-np.log10(0.05), color='gray', linestyle='--', linewidth=1.5,
               label='α=0.05 기준')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(dim_labels, fontsize=14)
    ax.set_ylabel('-log₁₀(p-value)', fontsize=16)
    ax.set_title('모수 vs 비모수 검정 결과 비교\n(높을수록 유의)', fontsize=18)
    ax.legend(fontsize=13, loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')

    save_figure(fig, TEAM, 'fig_b16_normality_nonparametric.png')

    return {'normality': normality_results, 'kruskal_wallis': kw_results}


# ============================================================
# 분석 15: H7 점수 명확도(극단성) × 관심사 (방안4)
# ============================================================
def analyze_score_clarity(data):
    """H7: 차원 점수 명확도(|score - 5.0|)가 관심사에 따라 다른가"""
    print("\n\n" + "━" * 60)
    print("  분석 15: H7 점수 명확도(극단성) × 관심사")
    print("━" * 60)

    interest_arr = data['interest']
    interests = ['Arts', 'Sports', 'Technology', 'Others']
    known_mask = np.isin(interest_arr, interests)

    clarity_results = {}

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('H7: MBTI 차원 점수 명확도 × 관심사\n'
                 '(명확도 = |점수 - 5.0|, 중간점에서의 거리)',
                 fontsize=24, fontweight='bold')

    for idx, key in enumerate(SCORE_KEYS):
        ax = axes[idx // 2, idx % 2]

        # 명확도 계산
        clarity = np.abs(data[key] - 5.0)

        # 관심사별 ANOVA
        groups = [clarity[(interest_arr == g) & known_mask]
                  for g in interests]
        anova = one_way_anova(*groups)

        clarity_results[key] = {
            'eta_squared': anova['eta_squared'],
            'f_stat': anova['f_stat'],
            'p_value': anova['p_value'],
            'significant': anova['significant'],
        }

        sig = "유의 ✓" if anova['significant'] else "비유의 ✗"
        print(f"\n  [{SCORE_NAMES[key]}]")
        print(f"    ANOVA: F={anova['f_stat']:.4f}, "
              f"p={anova['p_value']:.6f}, η²={anova['eta_squared']:.4f} [{sig}]")

        # Box Plot
        bp_data = [g for g in groups]
        bp = ax.boxplot(bp_data, labels=interests, patch_artist=True,
                        widths=0.6, showmeans=True,
                        meanprops=dict(marker='D', markerfacecolor='red',
                                       markersize=8))
        for j, patch in enumerate(bp['boxes']):
            patch.set_facecolor(INTEREST_COLORS.get(interests[j], '#95A5A6'))
            patch.set_alpha(0.7)

        # 평균값 주석
        for j, g in enumerate(groups):
            ax.text(j + 1, np.mean(g) + 0.02, f'{np.mean(g):.3f}',
                    ha='center', va='bottom', fontsize=13, fontweight='bold',
                    color='red')

        eta_str = f"η²={anova['eta_squared']:.4f}"
        p_str = format_p_value(anova['p_value'])
        ax.set_title(f'{SCORE_NAMES[key]} 명확도\n'
                     f'F={anova["f_stat"]:.2f}, {p_str}, {eta_str}',
                     fontsize=16)
        ax.set_ylabel('명확도 (|score - 5.0|)', fontsize=14)
        ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    save_figure(fig, TEAM, 'fig_b17_score_clarity_by_interest.png')

    return clarity_results


# ============================================================
# 분석 16: H8 Unknown vs Known 그룹 비교 (방안5)
# ============================================================
def analyze_unknown_vs_known(data):
    """H8: Unknown 관심사 그룹과 Known 그룹의 MBTI 차원 점수 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 16: H8 Unknown vs Known 그룹 비교")
    print("━" * 60)

    interest_arr = data['interest']
    unknown_mask = (interest_arr == 'Unknown')
    known_mask = np.isin(interest_arr, ['Arts', 'Sports', 'Technology', 'Others'])

    n_unknown = np.sum(unknown_mask)
    n_known = np.sum(known_mask)
    print(f"\n  Unknown: N={n_unknown:,}, Known: N={n_known:,}")

    unknown_results = {}

    fig, axes = plt.subplots(4, 2, figsize=(16, 20))
    fig.suptitle('H8: Unknown vs Known 관심사 그룹 MBTI 차원 점수 비교\n'
                 '(t-검정 + Mann-Whitney U 비모수 검증)',
                 fontsize=24, fontweight='bold')

    for idx, key in enumerate(SCORE_KEYS):
        unknown_scores = data[key][unknown_mask]
        known_scores = data[key][known_mask]

        # t-검정
        t_result = independent_t_test(unknown_scores, known_scores)

        # Cohen's d
        d_result = cohens_d(unknown_scores, known_scores)

        # Mann-Whitney U (scipy)
        u_stat, mw_p = sp_stats.mannwhitneyu(unknown_scores, known_scores,
                                              alternative='two-sided')

        unknown_results[key] = {
            't_stat': t_result['t_stat'],
            't_p': t_result['p_value'],
            'cohens_d': d_result['d'],
            'd_interpretation': d_result['interpretation'],
            'u_stat': u_stat,
            'mw_p': mw_p,
            'significant': t_result['significant'],
            'mean_unknown': np.mean(unknown_scores),
            'mean_known': np.mean(known_scores),
        }

        print(f"\n  [{SCORE_NAMES[key]}]")
        print(f"    Unknown 평균={np.mean(unknown_scores):.4f}, "
              f"Known 평균={np.mean(known_scores):.4f}")
        print(f"    t-검정: t={t_result['t_stat']:.4f}, p={t_result['p_value']:.6f}")
        print(f"    Cohen's d = {d_result['d']:.4f} ({d_result['interpretation']})")
        print(f"    Mann-Whitney U: U={u_stat:.0f}, p={mw_p:.6f}")

        # 좌: KDE 오버레이
        ax_kde = axes[idx, 0]
        x_range = np.linspace(
            min(np.min(unknown_scores), np.min(known_scores)) - 0.5,
            max(np.max(unknown_scores), np.max(known_scores)) + 0.5,
            300)
        # KDE (numpy 기반 가우시안 커널)
        bw = 0.3
        for arr, label, color, ls in [(known_scores, 'Known', '#3498DB', '-'),
                                       (unknown_scores, 'Unknown', '#95A5A6', '--')]:
            density = np.zeros_like(x_range)
            for val in arr[::50]:  # 서브샘플링 (속도)
                density += np.exp(-0.5 * ((x_range - val) / bw) ** 2)
            density = density / (len(arr[::50]) * bw * np.sqrt(2 * np.pi))
            ax_kde.plot(x_range, density, color=color, linestyle=ls,
                        linewidth=2.5, label=label)
            ax_kde.fill_between(x_range, density, alpha=0.2, color=color)

        ax_kde.set_title(f'{SCORE_NAMES[key]} 밀도 분포', fontsize=15)
        ax_kde.set_xlabel('점수', fontsize=13)
        ax_kde.set_ylabel('밀도', fontsize=13)
        ax_kde.legend(fontsize=12)
        ax_kde.grid(True, alpha=0.3)

        # 우: Cohen's d + p-values 바 차트
        ax_d = axes[idx, 1]
        d_val = abs(d_result['d'])
        bar_color = '#E74C3C' if t_result['significant'] else '#95A5A6'
        ax_d.barh([0], [d_val], color=bar_color, alpha=0.8, height=0.5)
        ax_d.axvline(0.2, color='orange', linestyle=':', linewidth=1.5,
                     alpha=0.6, label='d=0.2 (작은 효과)')
        ax_d.axvline(0.5, color='red', linestyle=':', linewidth=1.5,
                     alpha=0.6, label='d=0.5 (보통 효과)')
        ax_d.text(d_val + 0.01, 0, f"|d|={d_val:.4f}\n({d_result['interpretation']})",
                  va='center', fontsize=14, fontweight='bold')

        t_p_str = format_p_value(t_result['p_value'])
        mw_p_str = format_p_value(mw_p)
        ax_d.set_title(f"{SCORE_NAMES[key]}: t={t_result['t_stat']:.2f} ({t_p_str})\n"
                       f"Mann-Whitney ({mw_p_str})", fontsize=14)
        ax_d.set_yticks([])
        ax_d.set_xlabel("|Cohen's d|", fontsize=13)
        ax_d.legend(fontsize=10, loc='lower right')
        ax_d.set_xlim(0, max(d_val * 2, 0.6))
        ax_d.grid(True, alpha=0.3, axis='x')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    save_figure(fig, TEAM, 'fig_b18_unknown_vs_known.png')

    return unknown_results


# ============================================================
# 분석 17: H9 연령대 조절효과 (방안6)
# ============================================================
def analyze_age_interest_interaction(data):
    """H9: 연령대가 MBTI-관심사 관계를 조절하는가"""
    print("\n\n" + "━" * 60)
    print("  분석 17: H9 연령대 × 관심사 조절효과")
    print("━" * 60)

    age = data['age']
    interest_arr = data['interest']
    interests = ['Arts', 'Sports', 'Technology', 'Others']
    known_mask = np.isin(interest_arr, interests)

    # 연령 그룹 분류
    age_bins = [('Young (18-29)', (age >= 18) & (age <= 29)),
                ('Middle (30-39)', (age >= 30) & (age <= 39)),
                ('Older (40-52)', (age >= 40) & (age <= 52))]

    age_labels = [ab[0] for ab in age_bins]
    eta_matrix = np.zeros((len(age_bins) + 1, len(SCORE_KEYS)))  # +1 for overall
    sig_matrix = np.zeros((len(age_bins) + 1, len(SCORE_KEYS)), dtype=bool)

    age_mod_results = {}

    # 연령 그룹별 ANOVA
    for i, (label, age_mask) in enumerate(age_bins):
        combined_mask = age_mask & known_mask
        n_group = np.sum(combined_mask)
        print(f"\n  [{label}] N={n_group:,}")

        for j, key in enumerate(SCORE_KEYS):
            groups = [data[key][(interest_arr == g) & combined_mask]
                      for g in interests]
            # 최소 그룹 크기 확인
            min_size = min(len(g) for g in groups)
            if min_size < 5:
                eta_matrix[i, j] = 0.0
                sig_matrix[i, j] = False
                continue

            anova = one_way_anova(*groups)
            eta_matrix[i, j] = anova['eta_squared']
            sig_matrix[i, j] = anova['significant']

            print(f"    {SCORE_NAMES[key]}: F={anova['f_stat']:.2f}, "
                  f"η²={anova['eta_squared']:.4f} "
                  f"({'유의' if anova['significant'] else '비유의'})")

    # 전체 (Overall)
    print(f"\n  [Overall] N={np.sum(known_mask):,}")
    for j, key in enumerate(SCORE_KEYS):
        groups = [data[key][(interest_arr == g) & known_mask]
                  for g in interests]
        anova = one_way_anova(*groups)
        eta_matrix[-1, j] = anova['eta_squared']
        sig_matrix[-1, j] = anova['significant']

    age_mod_results['eta_matrix'] = eta_matrix
    age_mod_results['sig_matrix'] = sig_matrix
    age_mod_results['age_labels'] = age_labels + ['Overall']

    # η² 범위 요약
    max_eta = np.max(eta_matrix)
    print(f"\n  η² 최대값: {max_eta:.4f}")
    print(f"  결론: 연령대별 η² 차이 미미 → 연령은 유의미한 조절변수 아님")

    # === 시각화 fig_b19 ===
    fig, ax = plt.subplots(figsize=(12, 7))

    row_labels = age_labels + ['전체 (Overall)']
    col_labels = [SCORE_NAMES[k] for k in SCORE_KEYS]

    im = ax.imshow(eta_matrix, cmap='YlOrRd', aspect='auto',
                   vmin=0, vmax=max(0.01, eta_matrix.max() * 1.2))
    plt.colorbar(im, ax=ax, label='η² (효과크기)', shrink=0.8)

    # 셀 주석
    for i in range(eta_matrix.shape[0]):
        for j in range(eta_matrix.shape[1]):
            val = eta_matrix[i, j]
            sig_mark = '*' if sig_matrix[i, j] else ''
            ax.text(j, i, f'{val:.4f}{sig_mark}',
                    ha='center', va='center',
                    fontsize=16, fontweight='bold',
                    color='white' if val > eta_matrix.max() * 0.6 else 'black')

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, fontsize=15)
    ax.set_yticklabels(row_labels, fontsize=15)

    ax.set_title('H9: 연령대별 관심사 효과크기 (η²) 비교\n'
                 '(* = 통계적 유의, p < .05)',
                 fontsize=22, fontweight='bold')

    # 하단 해석
    fig.text(0.5, 0.01,
             '해석: 모든 연령대에서 η² < 0.01 → 연령은 MBTI-관심사 관계의 '
             '유의미한 조절변수가 아님',
             ha='center', fontsize=16, style='italic',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                       alpha=0.8))

    save_figure(fig, TEAM, 'fig_b19_age_interest_interaction.png')

    return age_mod_results


# ============================================================
# 분석 18: H10 다중회귀분석 (방안7)
# ============================================================
def analyze_multiple_regression(data):
    """H10: 다중 예측변수로 차원 점수를 예측할 수 있는가"""
    print("\n\n" + "━" * 60)
    print("  분석 18: H10 다중회귀분석")
    print("━" * 60)

    # 예측변수 준비
    age = data['age']
    gender_bin = (data['gender'] == 'Male').astype(np.float64)
    education = data['education'].astype(np.float64)

    mlr_results = {}
    simple_r2 = {}

    for key in SCORE_KEYS:
        y = data[key]

        # 다른 3개 차원 점수를 예측변수에 포함
        other_keys = [k for k in SCORE_KEYS if k != key]
        X = np.column_stack([
            age, gender_bin, education,
            *[data[k] for k in other_keys]
        ])

        predictor_names = ['나이', '성별(M)', '교육', ] + \
                          [SCORE_NAMES[k] for k in other_keys]

        # 다중회귀
        result = multiple_linear_regression(X, y)
        mlr_results[key] = {
            'r_squared': result['r_squared'],
            'adj_r_squared': result['adj_r_squared'],
            'f_stat': result['f_stat'],
            'p_value': result['p_value'],
            'betas': result['betas'],
            'se_betas': result['se_betas'],
            't_stats': result['t_stats'],
            'p_values_betas': result['p_values_betas'],
            'predictor_names': predictor_names,
            'significant': result['significant'],
        }

        # 단순회귀 R² (최고값)
        best_simple_r2 = 0
        for other_key in other_keys:
            reg = linear_regression(data[other_key], y)
            best_simple_r2 = max(best_simple_r2, reg['r_squared'])
        simple_r2[key] = best_simple_r2

        print(f"\n  [{SCORE_NAMES[key]}] 다중회귀 (6개 예측변수)")
        print(f"    R² = {result['r_squared']:.4f}, "
              f"adj_R² = {result['adj_r_squared']:.4f}")
        print(f"    F = {result['f_stat']:.2f}, p = {result['p_value']:.6f}")
        print(f"    단순회귀 최고 R² = {best_simple_r2:.4f}")
        print(f"    {'예측변수':<12s} {'β':>8s} {'SE':>8s} {'t':>8s} {'p':>10s}")
        print(f"    {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*10}")
        for i, name in enumerate(predictor_names):
            b = result['betas'][i + 1]  # +1 for intercept
            se = result['se_betas'][i + 1]
            t = result['t_stats'][i + 1]
            p = result['p_values_betas'][i + 1]
            sig_mark = '*' if p < 0.05 else ''
            print(f"    {name:<12s} {b:8.4f} {se:8.4f} {t:8.2f} {p:10.6f} {sig_mark}")

    mlr_results['simple_r2'] = simple_r2

    # === 시각화 fig_b20 (2패널) ===
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    fig.suptitle('H10: 다중회귀분석 — 예측변수별 계수 + R² 비교',
                 fontsize=24, fontweight='bold')

    # 좌: 대표 모델(introversion) 표준화 계수 Forest Plot
    ax = axes[0]
    key = 'introversion'
    res = mlr_results[key]
    pred_names = res['predictor_names']
    betas = res['betas'][1:]  # 절편 제외
    ses = res['se_betas'][1:]
    p_vals = res['p_values_betas'][1:]

    y_pos = np.arange(len(pred_names))
    colors = ['#E74C3C' if p < 0.05 else '#95A5A6' for p in p_vals]

    ax.barh(y_pos, betas, xerr=1.96 * ses, color=colors, alpha=0.8,
            height=0.6, capsize=5, ecolor='black')
    ax.axvline(0, color='black', linewidth=1.5)

    for j, (b, p) in enumerate(zip(betas, p_vals)):
        sig = '*' if p < 0.05 else ''
        ax.text(b + (0.01 if b >= 0 else -0.01), j,
                f'{b:.4f}{sig}', va='center',
                ha='left' if b >= 0 else 'right',
                fontsize=13, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(pred_names, fontsize=14)
    ax.set_xlabel('회귀계수 (β) ± 95% CI', fontsize=16)
    ax.set_title(f'내향성 점수 예측 모델\n'
                 f'R²={res["r_squared"]:.4f}, adj_R²={res["adj_r_squared"]:.4f}',
                 fontsize=17)
    ax.grid(True, alpha=0.3, axis='x')
    ax.invert_yaxis()

    # 우: 4개 모델 R² 비교 (단순 vs 다중)
    ax = axes[1]
    dim_labels = [SCORE_NAMES[k] for k in SCORE_KEYS]
    x_pos = np.arange(len(SCORE_KEYS))
    width = 0.35

    simple_vals = [simple_r2[k] for k in SCORE_KEYS]
    multi_vals = [mlr_results[k]['r_squared'] for k in SCORE_KEYS]

    bars1 = ax.bar(x_pos - width/2, simple_vals, width,
                    label='단순회귀 (최고 R²)', color='#3498DB', alpha=0.8)
    bars2 = ax.bar(x_pos + width/2, multi_vals, width,
                    label='다중회귀 (R²)', color='#E74C3C', alpha=0.8)

    # 값 주석
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.001,
                f'{h:.4f}', ha='center', va='bottom', fontsize=12)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.001,
                f'{h:.4f}', ha='center', va='bottom', fontsize=12)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(dim_labels, fontsize=14)
    ax.set_ylabel('R² (결정계수)', fontsize=16)
    ax.set_title('단순회귀 vs 다중회귀 R² 비교\n'
                 '(예측변수 추가 효과)', fontsize=17)
    ax.legend(fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')

    save_figure(fig, TEAM, 'fig_b20_multiple_regression.png')

    return mlr_results


# ============================================================
# 분석 19: PCA 2차원 시각화
# ============================================================
def analyze_pca_visualization(data):
    """PCA로 4차원 MBTI 점수를 2D로 축소하여 관심사 분리 가능성 시각화"""
    print("\n\n" + "━" * 60)
    print("  분석 19: PCA 주성분분석 2D 시각화")
    print("━" * 60)

    interest_arr = data['interest']
    interests = ['Arts', 'Sports', 'Technology', 'Others']
    known_mask = np.isin(interest_arr, interests)

    # 4차원 점수 행렬 구성
    X = np.column_stack([data[k] for k in SCORE_KEYS])
    X_known = X[known_mask]
    interest_known = interest_arr[known_mask]

    # 표준화
    means = np.mean(X_known, axis=0)
    stds = np.std(X_known, axis=0)
    X_std = (X_known - means) / stds

    # PCA: 공분산 → 고유값 분해
    cov_mat = np.cov(X_std.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov_mat)

    # 내림차순 정렬
    sort_idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sort_idx]
    eigenvectors = eigenvectors[:, sort_idx]

    # 설명분산비율
    explained_var = eigenvalues / np.sum(eigenvalues)
    cumulative_var = np.cumsum(explained_var)

    # 2D 투영
    pc_scores = X_std @ eigenvectors[:, :2]

    print(f"\n  고유값: {eigenvalues}")
    print(f"  설명분산비율: {explained_var}")
    print(f"  누적분산비율: {cumulative_var}")
    print(f"  PC1+PC2 설명력: {cumulative_var[1]:.1%}")

    # 중심점 계산
    centroids_pc = {}
    for g in interests:
        mask = interest_known == g
        centroids_pc[g] = np.mean(pc_scores[mask], axis=0)

    pca_results = {
        'explained_var': explained_var,
        'cumulative_var': cumulative_var,
        'eigenvectors': eigenvectors,
        'pc_scores': pc_scores,
        'centroids_pc': centroids_pc,
    }

    # === 시각화 fig_b21 (2패널) ===
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'PCA 주성분분석: 4차원 → 2차원 축소\n'
                 f'(PC1+PC2 설명력: {cumulative_var[1]:.1%})',
                 fontsize=24, fontweight='bold')

    # 좌: PC1-PC2 산점도
    ax = axes[0]
    for g in interests:
        mask = interest_known == g
        ax.scatter(pc_scores[mask, 0], pc_scores[mask, 1],
                   c=INTEREST_COLORS.get(g, '#95A5A6'),
                   label=g, alpha=0.15, s=8, rasterized=True)

    # 중심점
    for g in interests:
        c = centroids_pc[g]
        ax.scatter(c[0], c[1], marker='*', s=400,
                   c=INTEREST_COLORS.get(g, '#95A5A6'),
                   edgecolors='black', linewidth=2, zorder=10)

    ax.set_xlabel(f'PC1 ({explained_var[0]:.1%})', fontsize=16)
    ax.set_ylabel(f'PC2 ({explained_var[1]:.1%})', fontsize=16)
    ax.set_title('관심사별 PCA 산점도\n(★ = 그룹 중심점)', fontsize=18)
    ax.legend(fontsize=13, loc='best', markerscale=5)
    ax.grid(True, alpha=0.3)

    # 우: Scree Plot (설명분산비율)
    ax = axes[1]
    pc_labels = [f'PC{i+1}' for i in range(4)]
    bars = ax.bar(pc_labels, explained_var * 100, color='#3498DB', alpha=0.8,
                  edgecolor='black', linewidth=1.5)
    ax.plot(pc_labels, cumulative_var * 100, 'ro-', linewidth=2.5,
            markersize=10, label='누적 설명력 (%)')

    for j, (ev, cv) in enumerate(zip(explained_var, cumulative_var)):
        ax.text(j, ev * 100 + 1, f'{ev:.1%}', ha='center', fontsize=14,
                fontweight='bold')
        ax.text(j, cv * 100 + 1.5, f'{cv:.1%}', ha='center', fontsize=12,
                color='red', fontweight='bold')

    ax.set_ylabel('설명분산비율 (%)', fontsize=16)
    ax.set_title('Scree Plot: 주성분별 설명력', fontsize=18)
    ax.legend(fontsize=14)
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3, axis='y')

    # PCA 로딩 텍스트
    loading_text = 'PCA 로딩 (PC1):\n'
    for j, key in enumerate(SCORE_KEYS):
        loading_text += f'  {SCORE_NAMES[key]}: {eigenvectors[j, 0]:.3f}\n'
    ax.text(0.98, 0.02, loading_text, transform=ax.transAxes,
            fontsize=12, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow',
                      alpha=0.9))

    save_figure(fig, TEAM, 'fig_b21_pca_visualization.png')

    return pca_results


# ============================================================
# 분석 12: 효과크기 종합 Forest Plot (확장)
# ============================================================
def analyze_effect_size_summary(anova_results, pair_results, reg_results,
                                 chi2_result, gender_anova, classifier_result,
                                 clarity_results=None, unknown_results=None,
                                 age_mod_results=None, mlr_results=None,
                                 pca_results=None):
    """전체 효과크기 종합 Forest Plot (확장)"""
    print("\n\n" + "━" * 60)
    print("  분석 12: 효과크기 종합 Forest Plot (확장)")
    print("━" * 60)

    # 효과크기 수집
    effects = []

    # ANOVA η²
    for key in SCORE_KEYS:
        res = anova_results[key]
        effects.append({
            'name': f'{SCORE_NAMES[key]} × 관심사\n(ANOVA η²)',
            'value': res['eta_squared'],
            'type': 'eta2',
            'significant': res['significant'],
        })

    # 상관계수 |r|
    for pair_key, res in pair_results.items():
        k1, k2 = pair_key.split('-')
        effects.append({
            'name': f'{DIM_SHORT[k1]} × {DIM_SHORT[k2]}\n(|r|)',
            'value': abs(res['r']),
            'type': 'r',
            'significant': res['significant'],
        })

    # 회귀 R²
    for pair_key, res in reg_results.items():
        k1, k2 = pair_key.split('-')
        effects.append({
            'name': f'{DIM_SHORT[k1]} → {DIM_SHORT[k2]}\n(R²)',
            'value': res['r_squared'],
            'type': 'r2',
            'significant': res['significant'],
        })

    # Cramer's V (MBTI유형 × 관심사)
    effects.append({
        'name': 'MBTI유형 × 관심사\n(Cramer\'s V)',
        'value': chi2_result['cramers_v'],
        'type': 'v',
        'significant': chi2_result['significant'],
    })

    # 성별 조절 η² (Male/Female 중 큰 값)
    for key in SCORE_KEYS:
        eta_m = gender_anova['Male'][key]['eta_squared']
        eta_f = gender_anova['Female'][key]['eta_squared']
        max_eta = max(eta_m, eta_f)
        gender_label = 'M' if eta_m >= eta_f else 'F'
        effects.append({
            'name': f'{SCORE_NAMES[key]} 성별조절\n(max η², {gender_label})',
            'value': max_eta,
            'type': 'eta2_g',
            'significant': (gender_anova['Male'][key]['significant'] or
                            gender_anova['Female'][key]['significant']),
        })

    # H7: Clarity ANOVA η² (최대값)
    if clarity_results:
        max_clarity_key = max(clarity_results, key=lambda k: clarity_results[k]['eta_squared'])
        effects.append({
            'name': f'H7 명확도 최대\n({SCORE_NAMES[max_clarity_key]} η²)',
            'value': clarity_results[max_clarity_key]['eta_squared'],
            'type': 'eta2_c',
            'significant': clarity_results[max_clarity_key]['significant'],
        })

    # H8: Unknown vs Known Cohen's d (최대)
    if unknown_results:
        max_d_key = max(unknown_results, key=lambda k: abs(unknown_results[k]['cohens_d']))
        effects.append({
            'name': f'H8 Unknown vs Known\n({SCORE_NAMES[max_d_key]} |d|)',
            'value': abs(unknown_results[max_d_key]['cohens_d']),
            'type': 'd',
            'significant': unknown_results[max_d_key]['significant'],
        })

    # H9: Age moderator (최대 η²)
    if age_mod_results:
        eta_mat = age_mod_results['eta_matrix']
        max_age_eta = np.max(eta_mat[:-1])  # Overall 제외
        effects.append({
            'name': 'H9 연령대 조절\n(max η²)',
            'value': max_age_eta,
            'type': 'eta2_a',
            'significant': bool(np.any(age_mod_results['sig_matrix'][:-1])),
        })

    # H10: 다중회귀 R² (최대)
    if mlr_results:
        mlr_keys = [k for k in SCORE_KEYS if k in mlr_results]
        if mlr_keys:
            max_mlr_key = max(mlr_keys, key=lambda k: mlr_results[k]['r_squared'])
            effects.append({
                'name': f'H10 다중회귀\n({SCORE_NAMES[max_mlr_key]} R²)',
                'value': mlr_results[max_mlr_key]['r_squared'],
                'type': 'r2_m',
                'significant': mlr_results[max_mlr_key]['significant'],
            })

    # PCA: PC1+PC2 설명분산비율
    if pca_results:
        effects.append({
            'name': 'PCA PC1+PC2\n(설명분산비율)',
            'value': pca_results['cumulative_var'][1],
            'type': 'pca',
            'significant': True,  # 항상 의미 있음
        })

    # 출력
    print(f"\n  {'검정':<40s} {'효과크기':<8s} {'값':>8s}  유의성")
    print(f"  {'─'*40} {'─'*8} {'─'*8}  {'─'*6}")
    for e in effects:
        sig = "✓" if e['significant'] else "✗"
        name_flat = e['name'].replace('\n', ' ')
        print(f"  {name_flat:40s} "
              f"{e['type']:<8s} {e['value']:8.4f}  {sig}")

    # === 시각화 14: Forest Plot (확장) ===
    fig, ax = plt.subplots(figsize=(16, max(12, len(effects) * 0.55)))
    fig.suptitle('전체 효과크기 종합 Forest Plot (H1~H10 + PCA)',
                 fontsize=26, fontweight='bold')

    y_pos = np.arange(len(effects))
    names = [e['name'] for e in effects]
    values = [e['value'] for e in effects]
    significant = [e['significant'] for e in effects]
    types = [e['type'] for e in effects]

    # 색상 지정
    type_colors = {
        'eta2': '#E74C3C', 'r': '#3498DB', 'r2': '#2ECC71',
        'v': '#9B59B6', 'eta2_g': '#F39C12',
        'eta2_c': '#E67E22', 'd': '#1ABC9C', 'eta2_a': '#D4AC0D',
        'r2_m': '#2980B9', 'pca': '#8E44AD',
    }
    bar_colors = [type_colors.get(t, '#95A5A6') for t in types]
    edge_colors = ['black' if s else 'lightgray' for s in significant]

    bars = ax.barh(y_pos, values, color=bar_colors, alpha=0.8,
                    edgecolor=edge_colors, linewidth=2, height=0.7)

    # 값 주석
    for j, (v, s) in enumerate(zip(values, significant)):
        marker = '***' if s else ''
        ax.text(v + 0.002, j, f'{v:.4f} {marker}',
                va='center', fontsize=14, fontweight='bold')

    # 기준선
    ax.axvline(0.01, color='red', linestyle=':', linewidth=1.5,
               alpha=0.6, label='η²/R²=0.01 (작은 효과)')
    ax.axvline(0.06, color='orange', linestyle=':', linewidth=1.5,
               alpha=0.6, label='η²/R²=0.06 (보통 효과)')
    ax.axvline(0.14, color='green', linestyle=':', linewidth=1.5,
               alpha=0.6, label='η²/R²=0.14 (큰 효과)')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=13)
    ax.set_xlabel('효과크기', fontsize=20)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.3)

    # 범례
    legend_elements = [
        mpatches.Patch(facecolor='#E74C3C', label='ANOVA η²'),
        mpatches.Patch(facecolor='#3498DB', label='상관계수 |r|'),
        mpatches.Patch(facecolor='#2ECC71', label='회귀 R²'),
        mpatches.Patch(facecolor='#9B59B6', label="Cramer's V"),
        mpatches.Patch(facecolor='#F39C12', label='성별조절 η²'),
        mpatches.Patch(facecolor='#E67E22', label='명확도 η²'),
        mpatches.Patch(facecolor='#1ABC9C', label="Cohen's d"),
        mpatches.Patch(facecolor='#2980B9', label='다중회귀 R²'),
        mpatches.Patch(facecolor='#8E44AD', label='PCA 설명분산'),
        Line2D([0], [0], color='red', linestyle=':', label='작은 효과 기준'),
        Line2D([0], [0], color='orange', linestyle=':',
               label='보통 효과 기준'),
    ]
    ax.legend(handles=legend_elements, fontsize=12, loc='lower right',
              ncol=2)

    ax.set_title('(*** = 통계적으로 유의, p < .05)', fontsize=18)

    save_figure(fig, TEAM, 'fig_b14_effect_size_forest.png')


# ============================================================
# 분석 13: 종합 결론 인포그래픽 (8패널 강화)
# ============================================================
def create_conclusion_infographic(anova_results, pair_results, reg_results,
                                   chi2_result, gender_anova,
                                   classifier_result,
                                   clarity_results=None, unknown_results=None,
                                   age_mod_results=None, mlr_results=None,
                                   pca_results=None):
    """종합 결론 인포그래픽 대시보드 (10패널)"""
    print("\n\n" + "━" * 60)
    print("  분석 13: 종합 결론 인포그래픽 (10패널)")
    print("━" * 60)

    fig = plt.figure(figsize=(56, 24))
    fig.suptitle('MBTI 차원 점수 × 관심사 분석: 종합 결론 (H1~H10)',
                 fontsize=52, fontweight='bold', y=0.98)

    # 10패널 레이아웃 (2행 × 5열, 가로 배치)
    gs = fig.add_gridspec(2, 5, hspace=0.35, wspace=0.25,
                          top=0.92, bottom=0.08)

    panel_configs = [
        {'title': 'H1: 차원 점수 간 상관관계',
         'color': '#EBF5FB', 'border': '#2980B9'},
        {'title': 'H2: 관심사별 차원 점수 차이',
         'color': '#FDEDEC', 'border': '#E74C3C'},
        {'title': 'H3: 차원 쌍 회귀분석',
         'color': '#E8F8F5', 'border': '#1ABC9C'},
        {'title': 'H4: 관심사 그룹 프로필 차이',
         'color': '#FEF9E7', 'border': '#F39C12'},
        {'title': 'H5: MBTI 유형 × 관심사 (범주형)',
         'color': '#F4ECF7', 'border': '#8E44AD'},
        {'title': 'H6: 성별 조절효과',
         'color': '#FDEBD0', 'border': '#E67E22'},
        {'title': 'H7-H8: 명확도 + Unknown 분석',
         'color': '#D6EAF8', 'border': '#2471A3'},
        {'title': 'H9-H10: 연령 조절 + 다중회귀',
         'color': '#D5F5E3', 'border': '#27AE60'},
        {'title': '분류/PCA + 핵심 수치',
         'color': '#FADBD8', 'border': '#C0392B'},
        {'title': '연구 의의 & 한계',
         'color': '#EAECEE', 'border': '#2C3E50'},
    ]

    def make_panel(gs_pos, cfg):
        ax = fig.add_subplot(gs_pos)
        ax.set_facecolor(cfg['color'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title(cfg['title'], fontsize=36,
                     fontweight='bold', color=cfg['border'], pad=22)
        ax.set_xticks([])
        ax.set_yticks([])
        return ax

    # ── H1: 차원 상관 ── (row 0, col 0)
    ax0 = make_panel(gs[0, 0], panel_configs[0])
    sig_pairs = [(k, v) for k, v in pair_results.items() if v['significant']]
    content = f"6개 차원 쌍 중 {len(sig_pairs)}개 유의\n\n"
    for k, v in sig_pairs[:4]:
        k1, k2 = k.split('-')
        content += f"• {DIM_SHORT[k1]}×{DIM_SHORT[k2]}: r={v['r']:.3f}\n"
    if len(sig_pairs) > 4:
        content += f"  ... 외 {len(sig_pairs)-4}개"
    PANEL_FONT = 30
    PANEL_LINE = 1.7

    ax0.text(0.05, 0.85, content, transform=ax0.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H2: 관심사별 ANOVA ── (row 0, col 1)
    ax1 = make_panel(gs[0, 1], panel_configs[1])
    content = ""
    for key in SCORE_KEYS:
        res = anova_results[key]
        sig = "[Y]" if res['significant'] else "[N]"
        content += (f"  {SCORE_NAMES[key]}: η²={res['eta_squared']:.4f} {sig}\n")
    max_eta = max(anova_results[k]['eta_squared'] for k in SCORE_KEYS)
    content += f"\n최대 η²={max_eta:.4f} (작은 효과 미만)"
    ax1.text(0.05, 0.85, content, transform=ax1.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H3: 회귀분석 ── (row 0, col 2)
    ax2 = make_panel(gs[0, 2], panel_configs[2])
    content = ""
    for pair_key, res in reg_results.items():
        k1, k2 = pair_key.split('-')
        content += (f"  {DIM_SHORT[k1]}→{DIM_SHORT[k2]}: "
                    f"R²={res['r_squared']:.4f}\n")
    max_r2 = max(r['r_squared'] for r in reg_results.values())
    content += f"\n최대 R²={max_r2:.4f} — 설명력 극히 낮음"
    ax2.text(0.05, 0.85, content, transform=ax2.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H4: 그룹 프로필 ── (row 0, col 3)
    ax3 = make_panel(gs[0, 3], panel_configs[3])
    content = ("- 관심사별 차원 점수 프로필 유사\n"
               "- 유클리드 거리 매우 작음\n"
               "- 차원 점수만으로 구분 어려움\n\n"
               "=> 관심사 예측 불가")
    ax3.text(0.05, 0.85, content, transform=ax3.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H5: MBTI 유형 × 관심사 ── (row 0, col 4)
    ax4 = make_panel(gs[0, 4], panel_configs[4])
    chi2_sig = "유의" if chi2_result['significant'] else "비유의"
    content = (f"χ²={chi2_result['chi2']:.1f}, "
               f"df={chi2_result['dof']} [{chi2_sig}]\n"
               f"Cramer's V = {chi2_result['cramers_v']:.4f}\n\n"
               f"→ 범주형도 효과크기 극히 작음")
    ax4.text(0.05, 0.85, content, transform=ax4.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H6: 성별 조절효과 ── (row 1, col 0)
    ax5 = make_panel(gs[1, 0], panel_configs[5])
    eta_m_vals = [gender_anova['Male'][k]['eta_squared'] for k in SCORE_KEYS]
    eta_f_vals = [gender_anova['Female'][k]['eta_squared'] for k in SCORE_KEYS]
    max_diff = max(abs(m - f) for m, f in zip(eta_m_vals, eta_f_vals))
    content = (f"Male η² 범위: {min(eta_m_vals):.4f}~{max(eta_m_vals):.4f}\n"
               f"Female η² 범위: {min(eta_f_vals):.4f}~{max(eta_f_vals):.4f}\n"
               f"최대 |Δη²| = {max_diff:.4f}\n\n"
               f"→ 성별은 조절변수 아님")
    ax5.text(0.05, 0.85, content, transform=ax5.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H7-H8: 명확도 + Unknown ── (row 1, col 1)
    ax6 = make_panel(gs[1, 1], panel_configs[6])
    content = ""
    if clarity_results:
        max_c_key = max(clarity_results, key=lambda k: clarity_results[k]['eta_squared'])
        content += (f"H7 명확도(|score-5|) × 관심사:\n"
                    f"  최대 η²={clarity_results[max_c_key]['eta_squared']:.4f}\n"
                    f"  → 극단적 선호도도 관심사 무관\n\n")
    if unknown_results:
        max_d_key = max(unknown_results, key=lambda k: abs(unknown_results[k]['cohens_d']))
        content += (f"H8 Unknown vs Known:\n"
                    f"  최대 |d|={abs(unknown_results[max_d_key]['cohens_d']):.4f}\n"
                    f"  → Unknown은 무작위/미분류 그룹")
    ax6.text(0.05, 0.85, content, transform=ax6.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── H9-H10: 연령 조절 + 다중회귀 ── (row 1, col 2)
    ax7 = make_panel(gs[1, 2], panel_configs[7])
    content = ""
    if age_mod_results:
        max_age_eta = np.max(age_mod_results['eta_matrix'][:-1])
        content += (f"H9 연령대 조절효과:\n"
                    f"  최대 η²={max_age_eta:.4f}\n"
                    f"  → 연령도 조절변수 아님\n\n")
    if mlr_results:
        max_mlr_key = max(SCORE_KEYS, key=lambda k: mlr_results[k]['r_squared'])
        content += (f"H10 다중회귀 (6변수):\n"
                    f"  최대 R²={mlr_results[max_mlr_key]['r_squared']:.4f}\n"
                    f"  → 변수 추가해도 설명력 미미")
    ax7.text(0.05, 0.85, content, transform=ax7.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── 분류/PCA + 핵심 수치 ── (row 1, col 3)
    ax8 = make_panel(gs[1, 3], panel_configs[8])
    acc = classifier_result['accuracy']
    chance = classifier_result['chance_level']
    content = (f"분류 정확도: {acc:.1%} (우연 {chance:.1%})\n")
    if pca_results:
        content += (f"PCA PC1+PC2: {pca_results['cumulative_var'][1]:.1%}\n\n")
    content += (f"표본: N = 43,744\n"
                f"V={chi2_result['cramers_v']:.4f}")
    ax8.text(0.05, 0.85, content, transform=ax8.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── 연구 의의 ── (row 1, col 4)
    ax9 = make_panel(gs[1, 4], panel_configs[9])
    content = ("[+] 10개 가설 다각도 검증\n"
               "[+] 모수+비모수 이중 검증 (scipy)\n"
               "[+] PCA+다중회귀 고급 분석\n"
               "[+] 효과크기 체계적 보고\n\n"
               "[-] 자기보고 설문 한계\n"
               "[-] 관심사 4분류의 거칠기")
    ax9.text(0.05, 0.85, content, transform=ax9.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # 하단 결론 배너
    fig.text(0.5, 0.015,
             '결론: 10개 가설 × 12종 통계검정 결과, MBTI 차원 점수와 관심사 간 '
             '통계적 유의성은 있으나 효과크기가 모두 극히 작아 실질적 예측력은 미약함',
             ha='center', va='center', fontsize=34, fontweight='bold',
             color='white',
             bbox=dict(boxstyle='round,pad=0.8', facecolor='#2C3E50',
                       edgecolor='#2C3E50', alpha=0.95))

    save_figure(fig, TEAM, 'fig_b15_conclusion_infographic.png')


# ============================================================
# 결과 요약
# ============================================================
def create_summary(anova_results, pair_results, reg_results,
                    chi2_result, gender_anova, classifier_result,
                    clarity_results=None, unknown_results=None,
                    age_mod_results=None, mlr_results=None,
                    pca_results=None):
    """분석 결과 종합"""
    print("\n\n" + "=" * 60)
    print("  팀원 B: 분석 결과 종합 요약 (H1~H10)")
    print("=" * 60)

    print("\n[가설 1] MBTI 차원 점수 간 상관관계")
    sig_count = sum(1 for r in pair_results.values() if r['significant'])
    print(f"  → 6개 차원 쌍 중 {sig_count}개에서 유의한 상관관계 발견")
    for key, res in pair_results.items():
        k1, k2 = key.split('-')
        sig = "유의 ✓" if res['significant'] else "유의하지 않음 ✗"
        print(f"    {SCORE_NAMES[k1]} × {SCORE_NAMES[k2]}: "
              f"r = {res['r']:.4f} ({res['strength']}) [{sig}]")

    print(f"\n[가설 2] 관심사별 MBTI 차원 점수 차이")
    for key, res in anova_results.items():
        sig = "유의 ✓" if res['significant'] else "유의하지 않음 ✗"
        eta_interp = ('작은 효과' if res['eta_squared'] < 0.06
                      else '보통 효과' if res['eta_squared'] < 0.14
                      else '큰 효과')
        print(f"  → {SCORE_NAMES[key]}: F = {res['f_stat']:.2f}, "
              f"η² = {res['eta_squared']:.4f} ({eta_interp}) [{sig}]")

    print(f"\n[가설 3] 차원 점수 쌍 간 회귀분석")
    for pair_key, res in reg_results.items():
        k1, k2 = pair_key.split('-')
        sig = "유의 ✓" if res['significant'] else "유의하지 않음 ✗"
        print(f"  → {SCORE_NAMES[k1]} → {SCORE_NAMES[k2]}: "
              f"R² = {res['r_squared']:.4f}, β = {res['slope']:.4f} [{sig}]")

    print(f"\n[가설 5] MBTI 유형(범주) × 관심사 독립성")
    chi2_sig = "유의 ✓" if chi2_result['significant'] else "유의하지 않음 ✗"
    print(f"  → χ² = {chi2_result['chi2']:.1f}, "
          f"Cramer's V = {chi2_result['cramers_v']:.4f} [{chi2_sig}]")

    print(f"\n[가설 6] 성별 조절효과")
    for key in SCORE_KEYS:
        eta_m = gender_anova['Male'][key]['eta_squared']
        eta_f = gender_anova['Female'][key]['eta_squared']
        print(f"  → {SCORE_NAMES[key]}: "
              f"Male η²={eta_m:.4f}, Female η²={eta_f:.4f}, "
              f"Δ={eta_m - eta_f:+.4f}")
    print(f"    성별은 유의미한 조절변수가 아님")

    if clarity_results:
        print(f"\n[가설 7] 점수 명확도(극단성) × 관심사")
        for key in SCORE_KEYS:
            res = clarity_results[key]
            sig = "유의 ✓" if res['significant'] else "비유의 ✗"
            print(f"  → {SCORE_NAMES[key]} 명확도: "
                  f"η²={res['eta_squared']:.4f} [{sig}]")
        print(f"    극단적 MBTI 선호도도 관심사와 무관")

    if unknown_results:
        print(f"\n[가설 8] Unknown vs Known 그룹 비교")
        for key in SCORE_KEYS:
            res = unknown_results[key]
            sig = "유의 ✓" if res['significant'] else "비유의 ✗"
            print(f"  → {SCORE_NAMES[key]}: "
                  f"|d|={abs(res['cohens_d']):.4f} ({res['d_interpretation']}) [{sig}]")
        print(f"    Unknown은 무작위/미분류 그룹으로 판단")

    if age_mod_results:
        print(f"\n[가설 9] 연령대 조절효과")
        for i, label in enumerate(age_mod_results['age_labels']):
            etas = age_mod_results['eta_matrix'][i]
            print(f"  → {label}: η² = {etas}")
        print(f"    연령대도 유의미한 조절변수 아님")

    if mlr_results:
        print(f"\n[가설 10] 다중회귀분석")
        for key in SCORE_KEYS:
            if key in mlr_results:
                res = mlr_results[key]
                print(f"  → {SCORE_NAMES[key]}: "
                      f"R²={res['r_squared']:.4f}, "
                      f"adj_R²={res['adj_r_squared']:.4f}")
        print(f"    6개 예측변수 투입해도 설명력 미미")

    print(f"\n[분류 검증] 중심점 분류 정확도")
    acc = classifier_result['accuracy']
    chance = classifier_result['chance_level']
    print(f"  → 정확도: {acc:.1%} (우연 수준: {chance:.1%})")

    if pca_results:
        print(f"\n[PCA] 주성분분석")
        print(f"  → PC1+PC2 설명분산: {pca_results['cumulative_var'][1]:.1%}")
        print(f"    2D 공간에서도 관심사 그룹 분리 불가")

    print("\n" + "─" * 60)
    print("  [핵심 인사이트]")
    print("  1. 10개 가설 × 12종 통계검정 → 모두 일관된 결론")
    print("  2. 연속형/범주형/분류/비모수/다중회귀/PCA 전방위 검증")
    print("  3. 모든 효과크기가 '작은 효과' 미만 (η²<0.01, |d|<0.2)")
    print("  4. 성별/연령대 조절효과도 무의미")
    print("  5. 결론: MBTI 차원 점수는 관심사를 예측하지 못함")
    print("  6. 대표본(N=43,744)으로 p<.05 달성은 쉬우나 효과크기가 본질")
    print("─" * 60)


# ============================================================
# 메인 실행
# ============================================================
def main():
    """팀원 B 전체 분석 실행 (H1~H10 + PCA)"""
    data = load_and_preprocess()

    # 기존 분석 (1-5) → fig_b1~b7
    analyze_dimension_score_eda(data)                                  # b1, b2
    anova_results = analyze_interest_by_dimension(data)                # b3, b4
    pair_results, corr_mat = analyze_dimension_correlations(data)      # b5
    reg_results = analyze_regression_patterns(data)                    # b6
    centroids, dist_matrix, interest_list = analyze_interest_profile(data)  # b7

    # 통합 분석 (6) → fig_b8
    analyze_kde_and_ci(data)                                           # b8

    # 범주형+조절 분석 (7-9) → fig_b9~b11
    chi2_result, std_res, mbti_list = analyze_mbti_type_interest(data)   # b9
    gender_anova, gender_t, eta_diffs = analyze_gender_moderator(data)   # b10
    classifier_result = analyze_centroid_classifier(data)                 # b11

    # 시각화 보조 → fig_b12~b13
    analyze_scatter_by_interest(data)                                    # b12
    analyze_distance_heatmap(centroids, dist_matrix, interest_list)      # b13

    # === 고급 분석 (Scipy + 방안4~7 + PCA) → fig_b16~b21 ===
    normality_results = analyze_normality_and_nonparametric(data)        # b16
    clarity_results = analyze_score_clarity(data)                        # b17
    unknown_results = analyze_unknown_vs_known(data)                     # b18
    age_mod_results = analyze_age_interest_interaction(data)             # b19
    mlr_results = analyze_multiple_regression(data)                      # b20
    pca_results = analyze_pca_visualization(data)                        # b21

    # === 종합 분석 (확장) → fig_b14~b15 ===
    analyze_effect_size_summary(anova_results, pair_results, reg_results,
                                 chi2_result, gender_anova,
                                 classifier_result,
                                 clarity_results, unknown_results,
                                 age_mod_results, mlr_results,
                                 pca_results)                           # b14
    create_conclusion_infographic(anova_results, pair_results, reg_results,
                                   chi2_result, gender_anova,
                                   classifier_result,
                                   clarity_results, unknown_results,
                                   age_mod_results, mlr_results,
                                   pca_results)                         # b15

    # 종합 요약
    create_summary(anova_results, pair_results, reg_results,
                    chi2_result, gender_anova, classifier_result,
                    clarity_results, unknown_results,
                    age_mod_results, mlr_results, pca_results)

    print(f"\n[완료] 팀원 B 고급 분석 완료! "
          f"그래프 21개 저장")
    print(f"  저장 위치: results/figures/team_b/\n")


if __name__ == '__main__':
    set_project_style()
    main()
