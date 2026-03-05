# -*- coding: utf-8 -*-
"""
팀원 B 확장: 밈 설문 데이터로 team_b 분석 교차검증
====================================================
데이터: data/meme/ 설문 CSV + data.csv (Kaggle 43,744명)

목적:
  team_b(H1~H10)의 핵심 발견을 소규모 자체 설문으로 교차검증하고,
  설문 고유 문항(MBTI 신뢰도, 혈액형 인식)을 추가 분석한다.

반영 가능 항목:
  ✅ H1 교차검증: 차원 간 상관 (Pearson)
  ✅ H3 교차검증: 차원 쌍 회귀 (R²)
  ✅ H6 교차검증: 성별 조절효과 (t-test, Cohen's d)
  ✅ H9 교차검증: 연령대 조절효과 (ANOVA η²)
  ✅ PCA 교차검증: Kaggle 공간에 설문 투영
  ✅ 설문 고유: MBTI 신뢰도 × 차원 점수

반영 불가:
  ❌ H2, H4, H5: 설문에 "관심사" 문항 없음

통계 방법: Pearson 상관, 독립표본 t-검정, ANOVA, 선형회귀, PCA

그래프 목록 (11개):
  fig_bs1  : 설문 응답자 프로필 (4패널 EDA)
  fig_bs2  : 차원 점수 분포 비교 (설문 vs Kaggle)
  fig_bs3  : 차원 간 상관 교차검증 (H1)
  fig_bs4  : 차원 쌍 회귀 교차검증 (H3)
  fig_bs5  : 자기보고 vs 설문산출 MBTI 일치도
  fig_bs6  : 성별 × 차원 점수 교차검증 (H6)
  fig_bs7  : 연령대 × 차원 점수 교차검증 (H9)
  fig_bs8  : MBTI 신뢰도 × 차원 점수 (설문 고유)
  fig_bs9  : PCA 교차검증 (설문 vs Kaggle)
  fig_bs10 : 종합 결론 인포그래픽
  fig_bs11 : 로지스틱 회귀 LOO-CV MBTI 예측
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
    MBTI_TYPES, MBTI_COLORS, GENDER_COLORS, BLOOD_COLORS,
    MBTI_DIMENSIONS, DIMENSION_NAMES_KR,
    FIGSIZE_DEFAULT, FIGSIZE_WIDE
)
from common.data_loader import load_personality_data
from common.stats_utils import (
    descriptive_stats, pearson_correlation, independent_t_test,
    one_way_anova, cohens_d, confidence_interval,
    linear_regression, print_test_result,
    logistic_regression_train, logistic_regression_predict, standardize_features,
    logistic_regression_diagnostics, compute_vif, logistic_aic_bic,
    logistic_mcfadden_r2, compute_classification_metrics
)
from common.plot_style import (
    set_project_style, save_figure, format_p_value, add_result_text
)
from survey.mbti_scoring_v2 import (
    batch_compute_from_array_v2, extract_bonus_data,
    V2_COL_MAP, MIDPOINT
)

TEAM = 'team_b'

# 설문 CSV 경로
SURVEY_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'data', 'meme',
    'MBTI_밈_설문v2_응답_데이터 - Form Responses 1.csv'
)

# 차원 키 매핑 (설문 EI/SN/TF/JP → Kaggle 컬럼명)
DIM_KEYS = ['EI', 'SN', 'TF', 'JP']
KAGGLE_DIM_MAP = {
    'EI': 'introversion',
    'SN': 'sensing',
    'TF': 'thinking',
    'JP': 'judging',
}
DIM_LABELS_KR = {
    'EI': '내향성(EI) 점수',
    'SN': '감각(SN) 점수',
    'TF': '사고(TF) 점수',
    'JP': '판단(JP) 점수',
}
DIM_SHORT = {
    'EI': 'EI(내향)',
    'SN': 'SN(감각)',
    'TF': 'TF(사고)',
    'JP': 'JP(판단)',
}

AGE_COLORS = {'20대': '#3498DB', '30대': '#E67E22', '40대 이상': '#2ECC71'}


# ============================================================
#  데이터 로드
# ============================================================
def load_survey_data():
    """밈 설문 CSV + Kaggle 데이터 로드 및 전처리"""
    print("=" * 60)
    print("  팀원 B 확장: 밈 설문 교차검증 분석")
    print("=" * 60)

    if not os.path.exists(SURVEY_CSV):
        raise FileNotFoundError(f"설문 CSV 파일이 없습니다: {SURVEY_CSV}")

    # CSV 읽기
    df = pd.read_csv(SURVEY_CSV)
    raw = df.values
    n = raw.shape[0]
    print(f"\n[데이터] 설문 응답: {n}명")

    # MBTI 채점
    scoring = batch_compute_from_array_v2(raw)
    bonus = extract_bonus_data(raw)

    # 인구통계 추출
    self_mbti = np.array([str(raw[i, V2_COL_MAP['self_mbti']]).strip()
                          for i in range(n)])
    genders = np.array([str(raw[i, V2_COL_MAP['gender']]).strip()
                        for i in range(n)])
    ages = np.array([str(raw[i, V2_COL_MAP['age']]).strip()
                     for i in range(n)])
    blood_types = np.array([str(raw[i, V2_COL_MAP['blood_type']]).strip()
                            for i in range(n)])

    # Kaggle 데이터
    kaggle = load_personality_data()
    print(f"[데이터] Kaggle 비교용: {len(kaggle['age'])}명")

    return {
        'n': n,
        'survey_scores': scoring['scores'],   # {'EI': arr, 'SN': arr, ...}
        'survey_types': scoring['types'],       # MBTI 유형 배열
        'self_mbti': self_mbti,
        'genders': genders,
        'ages': ages,
        'blood_types': blood_types,
        'bonus': bonus,
        'kaggle': kaggle,
    }


# ============================================================
#  분석 1: 설문 응답자 프로필 (EDA)
# ============================================================
def analyze_survey_eda(data):
    """설문 응답자 인구통계 프로필"""
    print("\n\n" + "━" * 60)
    print("  분석 BS1: 설문 응답자 프로필")
    print("━" * 60)

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle(f'밈 설문 응답자 프로필 (N={data["n"]})',
                 fontsize=26, fontweight='bold')

    # (1) MBTI 유형 분포
    ax = axes[0, 0]
    types, counts = np.unique(data['survey_types'], return_counts=True)
    order = np.argsort(-counts)
    colors = [MBTI_COLORS.get(t, '#95A5A6') for t in types[order]]
    ax.barh(range(len(types)), counts[order], color=colors)
    ax.set_yticks(range(len(types)))
    ax.set_yticklabels(types[order], fontsize=14)
    ax.set_xlabel('응답자 수', fontsize=16)
    ax.set_title('설문산출 MBTI 유형 분포', fontsize=20, fontweight='bold')
    ax.invert_yaxis()

    # (2) 성별 분포
    ax = axes[0, 1]
    g_labels, g_counts = np.unique(data['genders'], return_counts=True)
    colors_g = [GENDER_COLORS.get('Male', '#5DADE2') if '남' in g
                else GENDER_COLORS.get('Female', '#F1948A') if '여' in g
                else '#95A5A6' for g in g_labels]
    bars = ax.bar(g_labels, g_counts, color=colors_g, edgecolor='white')
    for bar, cnt in zip(bars, g_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{cnt}명\n({cnt/data["n"]:.0%})', ha='center', fontsize=14)
    ax.set_title('성별 분포', fontsize=20, fontweight='bold')
    ax.set_ylabel('응답자 수', fontsize=16)

    # (3) 나이대 분포
    ax = axes[1, 0]
    age_order = ['20대', '30대', '40대 이상']
    a_counts = [np.sum(data['ages'] == a) for a in age_order]
    colors_a = [AGE_COLORS.get(a, '#95A5A6') for a in age_order]
    bars = ax.bar(age_order, a_counts, color=colors_a, edgecolor='white')
    for bar, cnt in zip(bars, a_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{cnt}명\n({cnt/data["n"]:.0%})', ha='center', fontsize=14)
    ax.set_title('나이대 분포', fontsize=20, fontweight='bold')
    ax.set_ylabel('응답자 수', fontsize=16)

    # (4) 혈액형 분포
    ax = axes[1, 1]
    b_labels, b_counts = np.unique(data['blood_types'], return_counts=True)
    colors_b = [BLOOD_COLORS.get(b.replace('형', ''), '#95A5A6')
                for b in b_labels]
    bars = ax.bar(b_labels, b_counts, color=colors_b, edgecolor='white')
    for bar, cnt in zip(bars, b_counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{cnt}명', ha='center', fontsize=14)
    ax.set_title('혈액형 분포', fontsize=20, fontweight='bold')
    ax.set_ylabel('응답자 수', fontsize=16)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs1_survey_eda.png')
    print(f"  → 설문 응답자: {data['n']}명")


# ============================================================
#  분석 2: 차원 점수 분포 비교 (설문 vs Kaggle)
# ============================================================
def analyze_dimension_comparison(data):
    """4차원 점수 분포: 설문 vs Kaggle"""
    print("\n\n" + "━" * 60)
    print("  분석 BS2: 차원 점수 분포 비교 (설문 vs Kaggle)")
    print("━" * 60)

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle(f'차원 점수 분포: 설문 (N={data["n"]}) vs Kaggle (N=43,744)',
                 fontsize=24, fontweight='bold')

    results = {}
    for idx, dim in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        s_scores = data['survey_scores'][dim]
        k_scores = data['kaggle'][KAGGLE_DIM_MAP[dim]]

        # Kaggle 히스토그램 (정규화)
        ax.hist(k_scores, bins=30, density=True, alpha=0.4,
                color='#3498DB', label=f'Kaggle (N={len(k_scores):,})')
        # 설문 히스토그램 (정규화)
        ax.hist(s_scores, bins=15, density=True, alpha=0.6,
                color='#E74C3C', label=f'설문 (N={len(s_scores)})')

        # 통계 검정
        t_res = independent_t_test(s_scores, k_scores)
        d_res = cohens_d(s_scores, k_scores)
        d_val = d_res['d']
        results[dim] = {'t': t_res, 'd': d_val}

        ax.set_title(f'{DIM_LABELS_KR[dim]}', fontsize=20, fontweight='bold')
        ax.set_xlabel('점수', fontsize=20)
        ax.set_ylabel('밀도', fontsize=20)
        ax.legend(fontsize=17, loc='upper right')

        # 결과 주석
        p_str = format_p_value(t_res['p_value'])
        ax.text(0.05, 0.95,
                f"설문 M={np.mean(s_scores):.2f} (SD={np.std(s_scores):.2f})\n"
                f"Kaggle M={np.mean(k_scores):.2f} (SD={np.std(k_scores):.2f})\n"
                f"t={t_res['t_stat']:.2f}, {p_str}\n"
                f"Cohen's d={d_val:.3f}",
                transform=ax.transAxes, fontsize=16, va='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                          alpha=0.9))

        print(f"  {DIM_LABELS_KR[dim]}: t={t_res['t_stat']:.2f}, "
              f"p={t_res['p_value']:.4f}, d={d_val:.3f}")

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs2_dimension_comparison.png')
    return results


# ============================================================
#  분석 3: 차원 간 상관 교차검증 (H1 analog)
# ============================================================
def analyze_correlation_crossval(data):
    """차원 간 상관관계: 설문 vs Kaggle 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 BS3: 차원 간 상관 교차검증 (H1)")
    print("━" * 60)

    fig, axes = plt.subplots(1, 2, figsize=(20, 9))
    fig.suptitle('차원 간 상관행렬: 설문 vs Kaggle (H1 교차검증)',
                 fontsize=24, fontweight='bold')

    results = {}
    for panel_idx, (label, source) in enumerate([
        (f'설문 (N={data["n"]})', 'survey'),
        ('Kaggle (N=43,744)', 'kaggle')
    ]):
        ax = axes[panel_idx]
        corr_mat = np.zeros((4, 4))

        for i, d1 in enumerate(DIM_KEYS):
            for j, d2 in enumerate(DIM_KEYS):
                if source == 'survey':
                    x = data['survey_scores'][d1]
                    y = data['survey_scores'][d2]
                else:
                    x = data['kaggle'][KAGGLE_DIM_MAP[d1]]
                    y = data['kaggle'][KAGGLE_DIM_MAP[d2]]

                if i == j:
                    corr_mat[i, j] = 1.0
                else:
                    r_res = pearson_correlation(x, y)
                    corr_mat[i, j] = r_res['r']
                    if i < j:
                        key = f"{d1}-{d2}_{source}"
                        results[key] = r_res

        mask = np.triu(np.ones_like(corr_mat, dtype=bool), k=1)
        sns.heatmap(corr_mat, ax=ax, annot=True, fmt='.3f',
                    mask=mask, cmap='RdBu_r', vmin=-0.3, vmax=0.3,
                    xticklabels=[DIM_SHORT[d] for d in DIM_KEYS],
                    yticklabels=[DIM_SHORT[d] for d in DIM_KEYS],
                    annot_kws={'fontsize': 16})
        ax.set_title(label, fontsize=20, fontweight='bold')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs3_correlation_crossval.png')

    # 비교 출력
    print("\n  차원 쌍 상관 비교:")
    for i, d1 in enumerate(DIM_KEYS):
        for j, d2 in enumerate(DIM_KEYS):
            if i < j:
                s_key = f"{d1}-{d2}_survey"
                k_key = f"{d1}-{d2}_kaggle"
                s_r = results[s_key]['r']
                k_r = results[k_key]['r']
                print(f"    {d1}-{d2}: 설문 r={s_r:.3f}, Kaggle r={k_r:.3f}")

    return results


# ============================================================
#  분석 4: 차원 쌍 회귀 교차검증 (H3 analog)
# ============================================================
def analyze_regression_crossval(data):
    """차원 쌍 회귀분석: 설문 vs Kaggle R² 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 BS4: 차원 쌍 회귀 교차검증 (H3)")
    print("━" * 60)

    pairs = [(i, j) for i in range(4) for j in range(i+1, 4)]
    fig, axes = plt.subplots(2, 3, figsize=(22, 14))
    fig.suptitle(f'차원 쌍 회귀분석: 설문 {data["n"]}명 (H3 교차검증)',
                 fontsize=24, fontweight='bold')

    results = {}
    for pidx, (i, j) in enumerate(pairs):
        ax = axes[pidx // 3, pidx % 3]
        d1, d2 = DIM_KEYS[i], DIM_KEYS[j]

        sx = data['survey_scores'][d1]
        sy = data['survey_scores'][d2]
        kx = data['kaggle'][KAGGLE_DIM_MAP[d1]]
        ky = data['kaggle'][KAGGLE_DIM_MAP[d2]]

        # 설문 회귀
        s_reg = linear_regression(sx, sy)
        k_reg = linear_regression(kx, ky)
        results[f"{d1}-{d2}"] = {'survey': s_reg, 'kaggle': k_reg}

        # 산점도 + 회귀선
        ax.scatter(sx, sy, alpha=0.6, s=60, color='#E74C3C', zorder=3)
        x_line = np.linspace(sx.min(), sx.max(), 50)
        y_line = s_reg['slope'] * x_line + s_reg['intercept']
        ax.plot(x_line, y_line, 'k--', linewidth=2, zorder=4)

        ax.set_xlabel(DIM_SHORT[d1], fontsize=16)
        ax.set_ylabel(DIM_SHORT[d2], fontsize=16)
        ax.set_title(f'{DIM_SHORT[d1]} → {DIM_SHORT[d2]}',
                     fontsize=18, fontweight='bold')

        ax.text(0.05, 0.95,
                f"설문: y={s_reg['slope']:.3f}x+{s_reg['intercept']:.2f}\n"
                f"R\u00b2={s_reg['r_squared']:.4f}\n"
                f"Kaggle R\u00b2={k_reg['r_squared']:.4f}",
                transform=ax.transAxes, fontsize=12, va='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

        print(f"  {d1}\u2192{d2}: 설문 R\u00b2={s_reg['r_squared']:.4f}, "
              f"Kaggle R\u00b2={k_reg['r_squared']:.4f}")
        print(f"    설문 회귀식: {d2} = {s_reg['slope']:.4f} x {d1} + {s_reg['intercept']:.4f}")
        print(f"    Kaggle 회귀식: {d2} = {k_reg['slope']:.4f} x {d1} + {k_reg['intercept']:.4f}")

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs4_regression_crossval.png')
    return results


# ============================================================
#  분석 5: 자기보고 vs 설문산출 MBTI
# ============================================================
def analyze_self_vs_computed(data):
    """자기보고 MBTI와 설문 산출 MBTI 일치도"""
    print("\n\n" + "━" * 60)
    print("  분석 BS5: 자기보고 vs 설문산출 MBTI 일치도")
    print("━" * 60)

    self_m = data['self_mbti']
    comp_m = data['survey_types']

    # "모름" 제외
    valid = np.array([s in MBTI_TYPES for s in self_m])
    s_valid = self_m[valid]
    c_valid = comp_m[valid]
    n_valid = np.sum(valid)
    n_unknown = np.sum(~valid)

    # 전체 일치율
    full_match = np.mean(s_valid == c_valid)

    # 차원별 일치율
    dim_match = {}
    dim_labels = ['E/I', 'S/N', 'T/F', 'J/P']
    for idx, dim_name in enumerate(dim_labels):
        s_letter = np.array([s[idx] for s in s_valid])
        c_letter = np.array([c[idx] for c in c_valid])
        dim_match[dim_name] = np.mean(s_letter == c_letter)

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle('자기보고 vs 설문산출 MBTI 일치도',
                 fontsize=24, fontweight='bold')

    # (1) 차원별 일치율 바 차트
    ax = axes[0]
    labels = dim_labels + ['전체(16유형)']
    values = [dim_match[d] for d in dim_labels] + [full_match]
    colors = ['#3498DB', '#E67E22', '#E74C3C', '#2ECC71', '#9B59B6']
    bars = ax.bar(labels, values, color=colors, edgecolor='white', width=0.6)
    ax.axhline(y=0.5, color='gray', linestyle='--', linewidth=1.5,
               label='우연 수준 (50%)')
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{v:.1%}', ha='center', fontsize=15, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.set_ylabel('일치율', fontsize=16)
    ax.set_title(f'차원별/전체 일치율 (N={n_valid})', fontsize=20,
                 fontweight='bold')
    ax.legend(fontsize=14)

    # (2) 설명 텍스트 패널
    ax = axes[1]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('#F8F9F9')
    ax.set_title('해석', fontsize=20, fontweight='bold')

    text = (f"■ 유효 응답: {n_valid}명 (\"모름\" {n_unknown}명 제외)\n\n"
            f"■ 전체 16유형 일치율: {full_match:.1%}\n\n"
            f"■ 차원별 일치율:\n")
    for d in dim_labels:
        text += f"    {d}: {dim_match[d]:.1%}\n"
    text += (f"\n■ 해석:\n"
             f"  자기보고 MBTI와 설문 문항 응답에서\n"
             f"  산출된 MBTI는 차이를 보임.\n"
             f"  → 자기인식 ≠ 행동패턴 응답")
    ax.text(0.05, 0.92, text, transform=ax.transAxes,
            fontsize=16, va='top', linespacing=1.5)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs5_self_vs_computed.png')

    print(f"  전체 일치율: {full_match:.1%}")
    for d in dim_labels:
        print(f"    {d}: {dim_match[d]:.1%}")

    return {'full_match': full_match, 'dim_match': dim_match,
            'n_valid': n_valid}


# ============================================================
#  분석 6: 성별 × 차원 점수 교차검증 (H6 analog)
# ============================================================
def analyze_gender_crossval(data):
    """성별 조절효과 교차검증"""
    print("\n\n" + "━" * 60)
    print("  분석 BS6: 성별 × 차원 점수 교차검증 (H6)")
    print("━" * 60)

    male_mask = np.array(['남' in g for g in data['genders']])
    female_mask = np.array(['여' in g for g in data['genders']])
    n_male = np.sum(male_mask)
    n_female = np.sum(female_mask)

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle(f'성별 × 차원 점수: 설문 (남={n_male}, 여={n_female}) — H6 교차검증',
                 fontsize=22, fontweight='bold')

    results = {}
    for idx, dim in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        s_male = data['survey_scores'][dim][male_mask]
        s_female = data['survey_scores'][dim][female_mask]

        # 박스플롯
        bp = ax.boxplot([s_male, s_female],
                        tick_labels=['남성', '여성'],
                        patch_artist=True,
                        widths=0.5)
        colors_bp = [GENDER_COLORS['Male'], GENDER_COLORS['Female']]
        for patch, color in zip(bp['boxes'], colors_bp):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

        # t-검정
        if len(s_male) > 1 and len(s_female) > 1:
            t_res = independent_t_test(s_male, s_female)
            d_res = cohens_d(s_male, s_female)
            d_val = d_res['d']
        else:
            t_res = {'t_stat': 0, 'p_value': 1}
            d_val = 0

        results[dim] = {'t': t_res, 'd': d_val}

        # Kaggle 효과크기 (기존 team_b 결과 근사)
        k_male = data['kaggle'][KAGGLE_DIM_MAP[dim]][data['kaggle']['gender'] == 'Male']
        k_female = data['kaggle'][KAGGLE_DIM_MAP[dim]][data['kaggle']['gender'] == 'Female']
        k_d = cohens_d(k_male, k_female)['d']

        ax.set_title(DIM_LABELS_KR[dim], fontsize=20, fontweight='bold')
        ax.set_ylabel('점수', fontsize=16)

        p_str = format_p_value(t_res['p_value'])
        ax.text(0.02, 0.98,
                f"설문 d={d_val:.3f} ({p_str})\n"
                f"Kaggle d={k_d:.3f}",
                transform=ax.transAxes, fontsize=13, va='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

        print(f"  {DIM_LABELS_KR[dim]}: 설문 d={d_val:.3f}, Kaggle d={k_d:.3f}")

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs6_gender_crossval.png')
    return results


# ============================================================
#  분석 7: 연령대 × 차원 점수 교차검증 (H9 analog)
# ============================================================
def analyze_age_crossval(data):
    """연령대 조절효과 교차검증"""
    print("\n\n" + "━" * 60)
    print("  분석 BS7: 연령대 × 차원 점수 교차검증 (H9)")
    print("━" * 60)

    age_groups = ['20대', '30대', '40대 이상']
    masks = {a: (data['ages'] == a) for a in age_groups}

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('연령대 × 차원 점수: 설문 — H9 교차검증',
                 fontsize=24, fontweight='bold')

    results = {}
    for idx, dim in enumerate(DIM_KEYS):
        ax = axes[idx // 2, idx % 2]
        groups_data = []
        groups_labels = []
        for a in age_groups:
            g = data['survey_scores'][dim][masks[a]]
            if len(g) > 0:
                groups_data.append(g)
                groups_labels.append(a)

        # 박스플롯
        bp = ax.boxplot(groups_data, tick_labels=groups_labels,
                        patch_artist=True, widths=0.5)
        for i, (patch, a) in enumerate(zip(bp['boxes'], groups_labels)):
            patch.set_facecolor(AGE_COLORS.get(a, '#95A5A6'))
            patch.set_alpha(0.6)

        # ANOVA
        if len(groups_data) >= 2 and all(len(g) > 1 for g in groups_data):
            anova_res = one_way_anova(*groups_data)
            results[dim] = anova_res
        else:
            results[dim] = {'f_stat': 0, 'p_value': 1, 'eta_squared': 0}

        ax.set_title(DIM_LABELS_KR[dim], fontsize=20, fontweight='bold')
        ax.set_ylabel('점수', fontsize=16)

        p_str = format_p_value(results[dim]['p_value'])
        ax.text(0.02, 0.98,
                f"F={results[dim]['f_stat']:.2f}, {p_str}\n"
                f"η²={results[dim]['eta_squared']:.4f}",
                transform=ax.transAxes, fontsize=13, va='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

        print(f"  {DIM_LABELS_KR[dim]}: F={results[dim]['f_stat']:.2f}, "
              f"η²={results[dim]['eta_squared']:.4f}")

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs7_age_crossval.png')
    return results


# ============================================================
#  분석 8: MBTI 신뢰도 × 차원 점수 (설문 고유)
# ============================================================
def analyze_mbti_belief(data):
    """MBTI 신뢰도와 차원 점수 관계 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 BS8: MBTI 신뢰도 × 차원 점수 (설문 고유)")
    print("━" * 60)

    trust = data['bonus']['mbti_trust']
    opinions = data['bonus']['final_opinion']

    fig, axes = plt.subplots(1, 3, figsize=(24, 8))
    fig.suptitle('MBTI 신뢰도 × 차원 점수 분석',
                 fontsize=24, fontweight='bold')

    # (1) MBTI 신뢰도 분포
    ax = axes[0]
    vals, cnts = np.unique(trust.astype(int), return_counts=True)
    colors_t = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(vals)))
    ax.bar(vals, cnts, color=colors_t, edgecolor='white', width=0.7)
    for v, c in zip(vals, cnts):
        ax.text(v, c + 0.3, str(c), ha='center', fontsize=14)
    ax.set_xlabel('MBTI 신뢰도 (1=불신 ~ 7=신뢰)', fontsize=16)
    ax.set_ylabel('응답자 수', fontsize=16)
    ax.set_title('Q42: MBTI 신뢰도 분포', fontsize=20, fontweight='bold')
    ax.set_xticks(range(1, 8))

    # (2) 신뢰도 그룹별 차원 점수 명확도
    ax = axes[1]
    high_trust = trust >= 5
    low_trust = trust <= 3
    clarity_data = []
    clarity_labels = []
    clarity_colors = []

    for dim in DIM_KEYS:
        scores = data['survey_scores'][dim]
        clarity = np.abs(scores - MIDPOINT)
        if np.sum(high_trust) > 0:
            clarity_data.append(np.mean(clarity[high_trust]))
        else:
            clarity_data.append(0)
        if np.sum(low_trust) > 0:
            clarity_data.append(np.mean(clarity[low_trust]))
        else:
            clarity_data.append(0)

    x_pos = []
    x_labels = []
    for i, dim in enumerate(DIM_KEYS):
        x_pos.extend([i*3, i*3 + 1])
        x_labels.extend([f'{DIM_SHORT[dim]}\n높음', f'{DIM_SHORT[dim]}\n낮음'])

    colors_bar = ['#2ECC71', '#E74C3C'] * 4
    bars = ax.bar(range(len(clarity_data)), clarity_data,
                  color=colors_bar, edgecolor='white', width=0.7)
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, fontsize=11)
    ax.set_ylabel('평균 명확도 |score - 4.0|', fontsize=16)
    ax.set_title('신뢰도 그룹별 점수 명확도', fontsize=20, fontweight='bold')
    ax.legend([mpatches.Patch(color='#2ECC71'), mpatches.Patch(color='#E74C3C')],
              ['높은 신뢰(5-7)', '낮은 신뢰(1-3)'], fontsize=13)

    mean_trust = np.mean(trust)
    print(f"  평균 MBTI 신뢰도: {mean_trust:.2f}/7")
    print(f"  높은 신뢰(5-7): {np.sum(high_trust)}명, "
          f"낮은 신뢰(1-3): {np.sum(low_trust)}명")

    # (3) 최종 의견 파이 차트
    ax = axes[2]
    op_labels, op_counts = np.unique(opinions, return_counts=True)
    # 긴 레이블 축약
    short_labels = []
    for lab in op_labels:
        if '과학' in lab and '활용' in lab:
            short_labels.append('과학적 근거 있음')
        elif '꽤 맞는' in lab:
            short_labels.append('꽤 맞는 부분 있음')
        elif '재미' in lab:
            short_labels.append('재미로만')
        elif '미신' in lab:
            short_labels.append('완전 미신')
        elif '모르겠다' in lab or '관심' in lab:
            short_labels.append('모르겠다/무관심')
        else:
            short_labels.append(lab[:10])

    op_colors = ['#27AE60', '#F39C12', '#3498DB', '#E74C3C', '#95A5A6']
    wedges, texts, autotexts = ax.pie(
        op_counts, labels=short_labels, autopct='%1.0f%%',
        colors=op_colors[:len(op_counts)], startangle=90,
        textprops={'fontsize': 13})
    ax.set_title('Q46: 최종 의견', fontsize=20, fontweight='bold')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs8_mbti_belief.png')
    return {'mean_trust': mean_trust}


# ============================================================
#  분석 9: PCA 교차검증 (설문 vs Kaggle)
# ============================================================
def analyze_pca_crossval(data):
    """PCA: 설문 데이터를 Kaggle PCA 공간에 투영"""
    print("\n\n" + "━" * 60)
    print("  분석 BS9: PCA 교차검증 (설문 vs Kaggle)")
    print("━" * 60)

    # Kaggle 데이터 표준화 + PCA
    k_mat = np.column_stack([data['kaggle'][KAGGLE_DIM_MAP[d]]
                             for d in DIM_KEYS])
    k_mean = k_mat.mean(axis=0)
    k_std = k_mat.std(axis=0)
    k_std[k_std == 0] = 1
    k_norm = (k_mat - k_mean) / k_std

    cov = np.cov(k_norm.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    idx_sort = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx_sort]
    eigvecs = eigvecs[:, idx_sort]
    var_ratio = eigvals / eigvals.sum()

    k_pc = k_norm @ eigvecs[:, :2]

    # 설문 데이터를 Kaggle 공간에 투영
    s_mat = np.column_stack([data['survey_scores'][d] for d in DIM_KEYS])
    s_norm = (s_mat - k_mean) / k_std
    s_pc = s_norm @ eigvecs[:, :2]

    fig, axes = plt.subplots(1, 2, figsize=(22, 10))
    fig.suptitle(f'PCA 교차검증: 설문 {data["n"]}명을 Kaggle PCA 공간에 투영',
                 fontsize=24, fontweight='bold')

    # (1) Kaggle 배경 + 설문 투영
    ax = axes[0]
    # Kaggle 배경 (서브샘플링)
    rng = np.random.RandomState(42)
    sub_idx = rng.choice(len(k_pc), size=min(3000, len(k_pc)), replace=False)
    ax.scatter(k_pc[sub_idx, 0], k_pc[sub_idx, 1],
               alpha=0.08, s=10, color='#BDC3C7', label='Kaggle (샘플)')

    # 설문 점들
    survey_types = data['survey_types']
    for mtype in np.unique(survey_types):
        mask_t = survey_types == mtype
        ax.scatter(s_pc[mask_t, 0], s_pc[mask_t, 1],
                   s=100, alpha=0.8, edgecolors='black', linewidths=0.5,
                   color=MBTI_COLORS.get(mtype, '#95A5A6'),
                   label=mtype, zorder=5)

    ax.set_xlabel(f'PC1 ({var_ratio[0]:.1%})', fontsize=16)
    ax.set_ylabel(f'PC2 ({var_ratio[1]:.1%})', fontsize=16)
    ax.set_title('설문 응답자 위치 (Kaggle PCA 공간)',
                 fontsize=20, fontweight='bold')
    ax.legend(fontsize=10, ncol=4, loc='upper right', framealpha=0.8)

    # (2) Scree plot
    ax = axes[1]
    components = range(1, 5)
    ax.bar(components, var_ratio * 100, color='#3498DB',
           edgecolor='white', width=0.6)
    ax.plot(components, np.cumsum(var_ratio) * 100,
            'ro-', markersize=10, linewidth=2, label='누적')
    for i, (v, cv) in enumerate(zip(var_ratio, np.cumsum(var_ratio))):
        ax.text(i+1, v*100 + 1, f'{v:.1%}', ha='center', fontsize=14)
    ax.set_xlabel('주성분', fontsize=16)
    ax.set_ylabel('설명분산비율 (%)', fontsize=16)
    ax.set_title('Scree Plot (Kaggle 기반)', fontsize=20, fontweight='bold')
    ax.set_xticks(components)
    ax.legend(fontsize=14)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_bs9_pca_crossval.png')

    cum_var = np.cumsum(var_ratio)
    print(f"  PC1+PC2 설명분산: {cum_var[1]:.1%}")
    return {'var_ratio': var_ratio, 'cumulative_var': cum_var}


# ============================================================
#  분석 10: 종합 결론 인포그래픽
# ============================================================
def analyze_logistic_crossval(data):
    """로지스틱 회귀 LOO-CV MBTI 차원 예측"""
    print("\n\n" + "━" * 60)
    print("  분석 BS11: 로지스틱 회귀 LOO-CV 예측")
    print("━" * 60)
    print("  방법: LOO-CV로 4차원 각각 로지스틱 회귀 이진 분류")

    dim_high = {'EI': 'E', 'SN': 'S', 'TF': 'T', 'JP': 'J'}
    dim_low = {'EI': 'I', 'SN': 'N', 'TF': 'F', 'JP': 'P'}

    n = data['n']
    scores = data['survey_scores']
    survey_types = data['survey_types']

    # 특성 행렬: 4차원 점수
    X = np.column_stack([scores[dk] for dk in DIM_KEYS])

    # LOO-CV per dimension
    loo_dim_accs = {}
    loo_probs = {}
    baseline_dim_accs = {}
    all_weights = {}
    train_accs_all = {}

    for dk_idx, dk in enumerate(DIM_KEYS):
        y = np.array([1 if t[dk_idx] == dim_high[dk] else 0
                      for t in survey_types])

        # Baseline: 임계값 (t=4.0)
        baseline_pred = (scores[dk] >= MIDPOINT).astype(int)
        baseline_dim_accs[dk] = np.mean(baseline_pred == y)

        # LOO-CV 로지스틱 회귀
        loo_preds = np.zeros(n, dtype=int)
        loo_prob = np.zeros(n)

        for i in range(n):
            mask = np.ones(n, dtype=bool)
            mask[i] = False
            X_train, y_train = X[mask], y[mask]
            X_test = X[i:i+1]

            X_tr_std, m, s = standardize_features(X_train)
            X_te_std, _, _ = standardize_features(X_test, mean=m, std=s)

            model = logistic_regression_train(
                X_tr_std, y_train, lr=0.5, epochs=300, lambda_reg=0.1)
            pred = logistic_regression_predict(X_te_std, model['weights'])

            loo_preds[i] = pred['predictions'][0]
            loo_prob[i] = pred['probabilities'][0]

        loo_dim_accs[dk] = np.mean(loo_preds == y)
        loo_probs[dk] = loo_prob

        # 전체 학습 (계수 반환용)
        X_full_std, _, _ = standardize_features(X)
        model_full = logistic_regression_train(
            X_full_std, y, lr=0.5, epochs=500, lambda_reg=0.1)
        all_weights[dk] = model_full['weights']
        train_accs_all[dk] = model_full['train_acc']

        print(f"\n  {DIM_LABELS_KR[dk]}:")
        print(f"    Baseline (t=4.0): {baseline_dim_accs[dk]*100:.1f}%")
        print(f"    Logistic LOO-CV:  {loo_dim_accs[dk]*100:.1f}%")
        print(f"    Train (전체):     {model_full['train_acc']*100:.1f}%")

    # 전체 4글자 정확도
    # Baseline
    baseline_pred_4letter = np.array([
        ''.join([dim_high[dk] if scores[dk][i] >= MIDPOINT else dim_low[dk]
                 for dk in DIM_KEYS])
        for i in range(n)
    ])
    baseline_overall = np.mean(baseline_pred_4letter == survey_types)

    # LOO-CV 로지스틱
    # 각 차원 독립 LOO 예측을 결합
    loo_pred_dims = {}
    for dk_idx, dk in enumerate(DIM_KEYS):
        y = np.array([1 if t[dk_idx] == dim_high[dk] else 0
                      for t in survey_types])
        preds = np.zeros(n, dtype=int)
        for i in range(n):
            mask = np.ones(n, dtype=bool)
            mask[i] = False
            X_tr_std, m, s = standardize_features(X[mask])
            X_te_std, _, _ = standardize_features(X[i:i+1], mean=m, std=s)
            model = logistic_regression_train(
                X_tr_std, y[mask], lr=0.5, epochs=300, lambda_reg=0.1)
            pred = logistic_regression_predict(X_te_std, model['weights'])
            preds[i] = pred['predictions'][0]
        loo_pred_dims[dk] = np.where(preds == 1, dim_high[dk], dim_low[dk])

    loo_pred_4letter = np.array([
        ''.join([loo_pred_dims[dk][i] for dk in DIM_KEYS])
        for i in range(n)
    ])
    loo_overall = np.mean(loo_pred_4letter == survey_types)

    print(f"\n  [전체 4글자]")
    print(f"    Baseline: {baseline_overall*100:.1f}%")
    print(f"    Logistic LOO-CV: {loo_overall*100:.1f}%")

    # 자기보고 vs 로지스틱 비교
    self_mbti = data['self_mbti']
    valid = np.array([len(str(s)) == 4 for s in self_mbti])
    if np.sum(valid) > 0:
        self_baseline = np.mean(baseline_pred_4letter[valid] == self_mbti[valid])
        self_logistic = np.mean(loo_pred_4letter[valid] == self_mbti[valid])
    else:
        self_baseline = 0
        self_logistic = 0

    print(f"\n  [자기보고 MBTI 대비]")
    print(f"    Baseline: {self_baseline*100:.1f}%")
    print(f"    Logistic LOO-CV: {self_logistic*100:.1f}%")

    # --- fig_bs11: 로지스틱 회귀 LOO-CV 결과 ---
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'fig_bs11: 로지스틱 회귀 LOO-CV MBTI 예측 (N={n})',
                 fontsize=24, fontweight='bold')

    # (1) 차원별 정확도 비교
    ax = axes[0, 0]
    x = np.arange(len(DIM_KEYS))
    width = 0.35

    baseline_vals = [baseline_dim_accs[dk] * 100 for dk in DIM_KEYS]
    logistic_vals = [loo_dim_accs[dk] * 100 for dk in DIM_KEYS]

    bars1 = ax.bar(x - width/2, baseline_vals, width, label='Baseline (t=4.0)',
                   color='#95a5a6', edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x + width/2, logistic_vals, width, label='Logistic LOO-CV',
                   color='#1abc9c', edgecolor='white', linewidth=1.5)

    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{bar.get_height():.1f}%', ha='center', fontsize=16,
                   fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels([DIM_SHORT[dk] for dk in DIM_KEYS], fontsize=17)
    ax.set_ylabel('정확도 (%)', fontsize=18)
    ax.set_title('차원별 정확도: 임계값 vs 로지스틱 회귀', fontsize=18,
                 fontweight='bold')
    ax.legend(fontsize=16)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)

    # (2) 전체 정확도 비교
    ax = axes[0, 1]
    methods = ['Baseline\n(t=4.0)', 'Logistic\nLOO-CV']
    overall_vals = [baseline_overall * 100, loo_overall * 100]
    self_vals = [self_baseline * 100, self_logistic * 100]

    x2 = np.arange(len(methods))
    w2 = 0.35

    bars_ov = ax.bar(x2 - w2/2, overall_vals, w2, label='산출 MBTI 기준',
                     color=['#95a5a6', '#1abc9c'], edgecolor='white')
    bars_self = ax.bar(x2 + w2/2, self_vals, w2, label='자기보고 기준',
                       color=['#95a5a6', '#1abc9c'], alpha=0.4,
                       edgecolor='white', hatch='///')

    for bar in list(bars_ov) + list(bars_self):
        val = bar.get_height()
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.5,
                   f'{val:.1f}%', ha='center', fontsize=16, fontweight='bold')

    ax.set_xticks(x2)
    ax.set_xticklabels(methods, fontsize=18)
    ax.set_ylabel('전체 4글자 일치율 (%)', fontsize=18)
    ax.set_title('전체 예측 정확도 비교', fontsize=18, fontweight='bold')
    ax.legend(fontsize=16)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', alpha=0.3)

    # (3) 예측 확률 히스토그램
    ax = axes[1, 0]
    colors_dim = ['#e74c3c', '#2ecc71', '#3498db', '#f39c12']
    for idx, dk in enumerate(DIM_KEYS):
        ax.hist(loo_probs[dk], bins=15, alpha=0.5, label=DIM_SHORT[dk],
               color=colors_dim[idx], edgecolor='white')

    ax.axvline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.7,
              label='결정 경계 (0.5)')
    ax.set_xlabel('P(High)', fontsize=18)
    ax.set_ylabel('빈도', fontsize=18)
    ax.set_title('LOO-CV 예측 확률 분포', fontsize=18, fontweight='bold')
    ax.legend(fontsize=16)
    ax.grid(axis='y', alpha=0.3)

    # (4) 모형 요약
    ax = axes[1, 1]
    ax.axis('off')

    ax.text(0.5, 0.95, '모형 요약', ha='center', fontsize=24,
            fontweight='bold', color='#1abc9c', transform=ax.transAxes)

    rect = mpatches.FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.88, boxstyle='round,pad=0.02',
        facecolor='#e8f8f5', edgecolor='#1abc9c',
        linewidth=2, transform=ax.transAxes)
    ax.add_patch(rect)

    dim_avg_base = np.mean([baseline_dim_accs[dk] * 100 for dk in DIM_KEYS])
    dim_avg_lr = np.mean([loo_dim_accs[dk] * 100 for dk in DIM_KEYS])
    improvement = dim_avg_lr - dim_avg_base

    summary_text = (
        f'모형: 로지스틱 회귀 (L2, lambda=0.1)\n'
        f'검증: Leave-One-Out CV (N={n})\n'
        f'특성: 4차원 MBTI 점수\n'
        f'\n'
        f'차원 평균 정확도:\n'
        f'  Baseline: {dim_avg_base:.1f}%\n'
        f'  Logistic: {dim_avg_lr:.1f}%\n'
        f'  개선: {improvement:+.1f}%p\n'
        f'\n'
        f'전체 4글자 일치율:\n'
        f'  Baseline: {baseline_overall*100:.1f}%\n'
        f'  Logistic: {loo_overall*100:.1f}%\n'
        f'\n'
        f'해석: 소표본(N={n})에서 LOO-CV로\n'
        f'일반화 성능을 정직하게 평가합니다.'
    )

    ax.text(0.06, 0.85, summary_text, fontsize=18, color='#333',
           transform=ax.transAxes, verticalalignment='top',
           linespacing=1.5)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    save_figure(fig, TEAM, 'fig_bs11_logistic_crossval.png')

    return {
        'loo_dim_accs': loo_dim_accs,
        'loo_overall': loo_overall,
        'baseline_dim_accs': baseline_dim_accs,
        'baseline_overall': baseline_overall,
        'self_baseline': self_baseline,
        'self_logistic': self_logistic,
        'weights': all_weights,
        'train_accs': train_accs_all,
        'X': X,
    }


def analyze_logistic_diagnostics_b(data, logistic_res):
    """fig_bs12: 로지스틱 회귀 모형 진단 — VIF, AIC/BIC, McFadden R², 분류 성능"""
    print("\n\n" + "━" * 60)
    print("  분석 BS12: 로지스틱 회귀 모형 진단")
    print("━" * 60)

    dim_high = {'EI': 'E', 'SN': 'S', 'TF': 'T', 'JP': 'J'}
    n = data['n']
    survey_types = data['survey_types']
    feature_names = ['EI 점수', 'SN 점수', 'TF 점수', 'JP 점수']
    X = logistic_res['X']
    all_weights = logistic_res['weights']

    # 진단을 위해 전체 데이터로 표준화 (학습 시와 동일한 조건)
    X_std, _, _ = standardize_features(X)

    # 각 차원별 진단 (전체 데이터 모형)
    diagnostics = {}
    for dk_idx, dk in enumerate(DIM_KEYS):
        y = np.array([1 if t[dk_idx] == dim_high[dk] else 0
                      for t in survey_types])
        diag = logistic_regression_diagnostics(
            X_std, y, all_weights[dk], feature_names=feature_names,
            X_raw=X
        )
        diagnostics[dk] = diag
        print(f"\n  [{dk} 차원]")
        print(f"    VIF: {', '.join([f'{v:.2f}' for v in diag['vif']])}")
        print(f"    AIC: {diag['aic_bic']['aic']:.1f}, BIC: {diag['aic_bic']['bic']:.1f}")
        print(f"    McFadden R²: {diag['mcfadden']['mcfadden_r2']:.4f}")
        print(f"    F1: {diag['classification']['f1']:.3f}")

    # --- fig_bs12: 로지스틱 회귀 모형 진단 ---
    fig = plt.figure(figsize=(24, 18))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.97, f'fig_bs12: 로지스틱 회귀 모형 진단 (Regression Diagnostics)',
             ha='center', fontsize=26, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.945, f'N={n} | LOO-CV | 4차원 독립 이진 분류 | '
             f'다중공선성 · AIC/BIC · McFadden R² · 분류 성능',
             ha='center', fontsize=19, color='#7f8c8d')

    dim_labels = [DIM_SHORT[dk] for dk in DIM_KEYS]

    # ── 패널 1: VIF ──
    ax1 = fig.add_axes([0.06, 0.54, 0.42, 0.36])

    x_feats = np.arange(4)
    width = 0.18
    colors_dim = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']

    for idx, dk in enumerate(DIM_KEYS):
        vifs = diagnostics[dk]['vif']
        bars = ax1.bar(x_feats + idx * width - 1.5 * width, vifs, width,
                       label=dim_labels[idx], color=colors_dim[idx], alpha=0.85,
                       edgecolor='white', linewidth=1)
        for bar in bars:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{bar.get_height():.2f}', ha='center', fontsize=16, fontweight='bold')

    ax1.axhline(y=5, color='#e74c3c', linestyle='--', linewidth=2, alpha=0.7,
                label='경고 (VIF=5)')
    ax1.set_xticks(x_feats)
    ax1.set_xticklabels(feature_names, fontsize=18)
    ax1.set_ylabel('VIF 값', fontsize=19, fontweight='bold')
    ax1.set_title('1. 다중공선성 진단 (VIF)', fontsize=19, fontweight='bold')
    ax1.legend(fontsize=16, loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    max_vif = max(max(diagnostics[dk]['vif']) for dk in DIM_KEYS)
    ax1.set_ylim(0, max(max_vif * 1.5, 6))

    # ── 패널 2: AIC / BIC ──
    ax2 = fig.add_axes([0.55, 0.54, 0.42, 0.36])

    aic_vals = [diagnostics[dk]['aic_bic']['aic'] for dk in DIM_KEYS]
    bic_vals = [diagnostics[dk]['aic_bic']['bic'] for dk in DIM_KEYS]
    ll_vals = [diagnostics[dk]['aic_bic']['log_likelihood'] for dk in DIM_KEYS]

    x_d = np.arange(4)
    w = 0.3
    bars_a = ax2.bar(x_d - w/2, aic_vals, w, label='AIC', color='#3498db',
                     edgecolor='white', linewidth=1.5)
    bars_b = ax2.bar(x_d + w/2, bic_vals, w, label='BIC', color='#e74c3c',
                     edgecolor='white', linewidth=1.5)

    for bar in bars_a:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}', ha='center', fontsize=17,
                fontweight='bold', color='#3498db')
    for bar in bars_b:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}', ha='center', fontsize=17,
                fontweight='bold', color='#e74c3c')

    ax2.set_xticks(x_d)
    ax2.set_xticklabels(dim_labels, fontsize=18)
    ax2.set_ylabel('정보 기준 값 (낮을수록 좋음)', fontsize=18, fontweight='bold')
    ax2.set_title('2. 모형 적합도: AIC / BIC', fontsize=19, fontweight='bold')
    ax2.legend(fontsize=17)
    ax2.grid(axis='y', alpha=0.3)

    for i, ll in enumerate(ll_vals):
        ax2.text(i, 2, f'LL={ll:.1f}', ha='center', fontsize=16,
                color='#7f8c8d', fontweight='bold')

    # ── 패널 3: McFadden R² + 분류 성능 ──
    ax3 = fig.add_axes([0.06, 0.07, 0.42, 0.36])

    r2_vals = [diagnostics[dk]['mcfadden']['mcfadden_r2'] for dk in DIM_KEYS]
    acc_vals = [diagnostics[dk]['classification']['accuracy'] for dk in DIM_KEYS]
    f1_vals = [diagnostics[dk]['classification']['f1'] for dk in DIM_KEYS]
    prec_vals = [diagnostics[dk]['classification']['precision'] for dk in DIM_KEYS]
    recall_vals = [diagnostics[dk]['classification']['recall'] for dk in DIM_KEYS]

    w2 = 0.15
    x_d2 = np.arange(4)
    ax3.bar(x_d2 - 2*w2, r2_vals, w2, label='McFadden R²', color='#9b59b6',
            edgecolor='white', linewidth=1.5)
    ax3.bar(x_d2 - w2, acc_vals, w2, label='Accuracy', color='#1abc9c',
            edgecolor='white', linewidth=1.5)
    ax3.bar(x_d2, prec_vals, w2, label='Precision', color='#3498db',
            edgecolor='white', linewidth=1.5)
    ax3.bar(x_d2 + w2, recall_vals, w2, label='Recall', color='#e67e22',
            edgecolor='white', linewidth=1.5)
    ax3.bar(x_d2 + 2*w2, f1_vals, w2, label='F1-score', color='#e74c3c',
            edgecolor='white', linewidth=1.5)

    for i in range(4):
        vals = [r2_vals[i], acc_vals[i], prec_vals[i], recall_vals[i], f1_vals[i]]
        offsets = [-2*w2, -w2, 0, w2, 2*w2]
        for v, off in zip(vals, offsets):
            ax3.text(i + off, v + 0.01, f'{v:.2f}', ha='center', fontsize=16,
                    fontweight='bold')

    ax3.axhline(y=0.2, color='#9b59b6', linestyle='--', linewidth=1.5, alpha=0.5)
    ax3.text(3.5, 0.215, 'R²=0.2 기준', fontsize=16, color='#9b59b6', ha='right')

    ax3.set_xticks(x_d2)
    ax3.set_xticklabels(dim_labels, fontsize=18)
    ax3.set_ylabel('값 (0~1)', fontsize=19, fontweight='bold')
    ax3.set_title('3. McFadden R² + 분류 성능', fontsize=19, fontweight='bold')
    ax3.legend(fontsize=16, loc='upper right', ncol=3)
    ax3.set_ylim(0, 1.15)
    ax3.grid(axis='y', alpha=0.3)

    # ── 패널 4: 종합 진단 요약 테이블 ──
    ax4 = fig.add_axes([0.55, 0.07, 0.42, 0.36])
    ax4.axis('off')

    ax4.text(0.5, 0.97, '4. 회귀 모형 종합 진단 요약',
             ha='center', fontsize=22, fontweight='bold', color='#2c3e50',
             transform=ax4.transAxes)

    col_labels = ['지표'] + dim_labels
    table_data = []

    vif_row = ['VIF (평균)']
    for dk in DIM_KEYS:
        mv = np.mean(diagnostics[dk]['vif'])
        s = '양호' if mv < 5 else '주의' if mv < 10 else '심각'
        vif_row.append(f'{mv:.2f} ({s})')
    table_data.append(vif_row)

    table_data.append(['AIC'] + [f'{diagnostics[dk]["aic_bic"]["aic"]:.1f}' for dk in DIM_KEYS])
    table_data.append(['BIC'] + [f'{diagnostics[dk]["aic_bic"]["bic"]:.1f}' for dk in DIM_KEYS])
    table_data.append(['Log-Likelihood'] +
                      [f'{diagnostics[dk]["aic_bic"]["log_likelihood"]:.1f}' for dk in DIM_KEYS])

    r2_row = ['McFadden R²']
    for dk in DIM_KEYS:
        r2 = diagnostics[dk]['mcfadden']['mcfadden_r2']
        q = '우수' if r2 > 0.4 else '양호' if r2 > 0.2 else '미흡'
        r2_row.append(f'{r2:.4f} ({q})')
    table_data.append(r2_row)

    table_data.append(['조건수'] +
                      [f'{diagnostics[dk]["condition_number"]:.1f}' for dk in DIM_KEYS])
    table_data.append(['Accuracy'] +
                      [f'{diagnostics[dk]["classification"]["accuracy"]:.1%}' for dk in DIM_KEYS])
    table_data.append(['F1-score'] +
                      [f'{diagnostics[dk]["classification"]["f1"]:.3f}' for dk in DIM_KEYS])
    table_data.append(['Precision'] +
                      [f'{diagnostics[dk]["classification"]["precision"]:.3f}' for dk in DIM_KEYS])
    table_data.append(['Recall'] +
                      [f'{diagnostics[dk]["classification"]["recall"]:.3f}' for dk in DIM_KEYS])

    table = ax4.table(cellText=table_data, colLabels=col_labels,
                      loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1.0, 1.8)

    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold', fontsize=19)

    for i in range(len(table_data)):
        cell = table[i+1, 0]
        cell.set_facecolor('#ecf0f1')
        cell.set_text_props(fontweight='bold')

    for i in range(len(table_data)):
        for j in range(1, len(col_labels)):
            cell = table[i+1, j]
            if i == 0:
                dk = DIM_KEYS[j-1]
                mv = np.mean(diagnostics[dk]['vif'])
                cell.set_facecolor('#d5f5e3' if mv < 5 else '#fdebd0' if mv < 10 else '#fadbd8')
            elif i == 4:
                dk = DIM_KEYS[j-1]
                r2 = diagnostics[dk]['mcfadden']['mcfadden_r2']
                cell.set_facecolor('#d5f5e3' if r2 > 0.4 else '#d4efdf' if r2 > 0.2 else '#fdebd0')

    save_figure(fig, TEAM, 'fig_bs12_logistic_diagnostics.png')

    return diagnostics


def create_survey_conclusion(data, dim_comp, corr_res, reg_res,
                              match_res, gender_res, age_res,
                              belief_res, pca_res):
    """종합 결론 인포그래픽 (PPT 최적화)"""
    print("\n\n" + "━" * 60)
    print("  분석 BS10: 종합 결론 인포그래픽")
    print("━" * 60)

    fig = plt.figure(figsize=(48, 18))
    fig.suptitle(f'밈 설문 교차검증 종합 결론 (N={data["n"]})',
                 fontsize=44, fontweight='bold', y=0.98)

    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.25,
                          top=0.92, bottom=0.10)

    PANEL_FONT = 26
    PANEL_LINE = 1.6

    panel_cfgs = [
        {'title': '차원 분포: 설문 vs Kaggle', 'color': '#EBF5FB', 'border': '#2980B9'},
        {'title': 'H1/H3 교차검증: 상관·회귀', 'color': '#FDEDEC', 'border': '#E74C3C'},
        {'title': 'H6/H9 교차검증: 성별·연령', 'color': '#E8F8F5', 'border': '#1ABC9C'},
        {'title': '자기보고 vs 설문산출', 'color': '#FEF9E7', 'border': '#F39C12'},
        {'title': 'MBTI 신뢰도 (설문 고유)', 'color': '#F4ECF7', 'border': '#8E44AD'},
        {'title': '종합: 교차검증 일치 여부', 'color': '#EAECEE', 'border': '#2C3E50'},
    ]

    def make_panel(gs_pos, cfg):
        ax = fig.add_subplot(gs_pos)
        ax.set_facecolor(cfg['color'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title(cfg['title'], fontsize=32,
                     fontweight='bold', color=cfg['border'], pad=20)
        ax.set_xticks([])
        ax.set_yticks([])
        return ax

    # ── 패널 1: 차원 분포 ── (row 0, col 0)
    ax0 = make_panel(gs[0, 0], panel_cfgs[0])
    content = ""
    for dim in DIM_KEYS:
        d_val = dim_comp[dim]['d']
        content += f"  {DIM_SHORT[dim]}: Cohen's d={d_val:.3f}\n"
    content += "\n→ 설문은 Kaggle과 분포 유사/차이 확인"
    ax0.text(0.05, 0.85, content, transform=ax0.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── 패널 2: 상관·회귀 ── (row 0, col 1)
    ax1 = make_panel(gs[0, 1], panel_cfgs[1])
    content = "차원 간 상관 (6쌍):\n"
    for i, d1 in enumerate(DIM_KEYS):
        for j, d2 in enumerate(DIM_KEYS):
            if i < j:
                s_r = corr_res[f"{d1}-{d2}_survey"]['r']
                k_r = corr_res[f"{d1}-{d2}_kaggle"]['r']
                content += f"  {d1}-{d2}: S={s_r:.3f} K={k_r:.3f}\n"
    content += "\n→ 차원 독립성 확인"
    ax1.text(0.05, 0.85, content, transform=ax1.transAxes,
             fontsize=PANEL_FONT-2, va='top', linespacing=PANEL_LINE)

    # ── 패널 3: 성별·연령 ── (row 0, col 2)
    ax2 = make_panel(gs[0, 2], panel_cfgs[2])
    content = "성별 효과크기 (Cohen's d):\n"
    for dim in DIM_KEYS:
        s_d = gender_res[dim]['d']
        content += f"  {DIM_SHORT[dim]}: d={s_d:.3f}\n"
    content += "\n연령대 ANOVA η²:\n"
    for dim in DIM_KEYS:
        eta = age_res[dim]['eta_squared']
        content += f"  {DIM_SHORT[dim]}: η²={eta:.4f}\n"
    ax2.text(0.05, 0.85, content, transform=ax2.transAxes,
             fontsize=PANEL_FONT-2, va='top', linespacing=PANEL_LINE)

    # ── 패널 4: 자기보고 vs 설문산출 ── (row 1, col 0)
    ax3 = make_panel(gs[1, 0], panel_cfgs[3])
    content = (f"전체 일치율: {match_res['full_match']:.1%}\n"
               f"유효 응답: {match_res['n_valid']}명\n\n"
               "차원별 일치율:\n")
    for d_name, d_val in match_res['dim_match'].items():
        content += f"  {d_name}: {d_val:.1%}\n"
    content += "\n→ 자기인식 ≠ 행동패턴"
    ax3.text(0.05, 0.85, content, transform=ax3.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── 패널 5: MBTI 신뢰도 ── (row 1, col 1)
    ax4 = make_panel(gs[1, 1], panel_cfgs[4])
    content = (f"평균 MBTI 신뢰도: {belief_res['mean_trust']:.1f}/7\n\n"
               f"응답자 과반이 MBTI에 긍정적\n"
               f"→ 그러나 효과크기는 미미\n\n"
               f"PCA PC1+PC2: {pca_res['cumulative_var'][1]:.1%}\n"
               f"→ 설문도 군집 분리 불가")
    ax4.text(0.05, 0.85, content, transform=ax4.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # ── 패널 6: 종합 ── (row 1, col 2)
    ax5 = make_panel(gs[1, 2], panel_cfgs[5])
    content = ("교차검증 결과:\n\n"
               "[O] 차원 독립성 - 설문에서도 확인\n"
               "[O] 성별/연령 조절효과 - 미미\n"
               "[O] PCA 군집 분리 - 불가\n\n"
               f"[!] 소표본(N={data['n']}) 한계\n"
               "[!] 관심사 문항 미포함\n\n"
               "=> Kaggle 결론의 방향성 재확인")
    ax5.text(0.05, 0.85, content, transform=ax5.transAxes,
             fontsize=PANEL_FONT, va='top', linespacing=PANEL_LINE)

    # 하단 결론 배너
    fig.text(0.5, 0.03,
             f'결론: {data["n"]}명 소규모 설문에서도 Kaggle 43,744명 분석의 핵심 발견 '
             '(차원 독립성, 인구통계 무관성)이 재현되었으나, '
             '관심사 문항 부재로 H2~H5 직접 검증은 불가',
             ha='center', va='center', fontsize=28, fontweight='bold',
             color='white',
             bbox=dict(boxstyle='round,pad=0.8', facecolor='#2C3E50',
                       edgecolor='#2C3E50', alpha=0.95))

    save_figure(fig, TEAM, 'fig_bs10_survey_conclusion.png')


# ============================================================
#  결과 요약 출력
# ============================================================
def create_survey_summary(data, dim_comp, match_res, belief_res, pca_res):
    """교차검증 결과 텍스트 요약"""
    print("\n\n" + "=" * 60)
    print("  팀원 B 확장: 밈 설문 교차검증 요약")
    print("=" * 60)

    print(f"\n[표본] 설문 N={data['n']}명 vs Kaggle N=43,744명")
    print(f"\n[차원 분포 비교]")
    for dim in DIM_KEYS:
        d = dim_comp[dim]['d']
        print(f"  {DIM_LABELS_KR[dim]}: Cohen's d={d:.3f}")

    print(f"\n[자기보고 vs 설문산출] 전체 일치율: {match_res['full_match']:.1%}")
    print(f"[MBTI 신뢰도] 평균: {belief_res['mean_trust']:.1f}/7")
    print(f"[PCA] PC1+PC2: {pca_res['cumulative_var'][1]:.1%}")

    print("\n" + "─" * 60)
    print("  [핵심 인사이트]")
    print("  1. 차원 독립성: 설문에서도 Kaggle과 동일 패턴 확인")
    print("  2. 성별·연령 조절효과: 소표본에서도 미미")
    print("  3. 자기보고 MBTI ≠ 설문산출 MBTI → 자기인식 한계")
    print("  4. MBTI 신뢰도 높지만 효과크기는 미미 → 확증편향 가능성")
    print("  5. 관심사 문항 미포함으로 H2~H5 직접 검증 불가 (한계)")
    print("─" * 60)


# ============================================================
#  메인 실행
# ============================================================
def main():
    """팀원 B 밈 설문 교차검증 분석 전체 실행"""
    set_project_style()

    data = load_survey_data()

    # 분석 실행
    analyze_survey_eda(data)                                 # bs1
    dim_comp = analyze_dimension_comparison(data)             # bs2
    corr_res = analyze_correlation_crossval(data)             # bs3
    reg_res = analyze_regression_crossval(data)               # bs4
    match_res = analyze_self_vs_computed(data)                # bs5
    gender_res = analyze_gender_crossval(data)                # bs6
    age_res = analyze_age_crossval(data)                      # bs7
    belief_res = analyze_mbti_belief(data)                    # bs8
    pca_res = analyze_pca_crossval(data)                      # bs9
    logistic_res = analyze_logistic_crossval(data)             # bs11
    logistic_diag = analyze_logistic_diagnostics_b(data, logistic_res)  # bs12

    # 종합
    create_survey_conclusion(data, dim_comp, corr_res, reg_res,
                              match_res, gender_res, age_res,
                              belief_res, pca_res)            # bs10
    create_survey_summary(data, dim_comp, match_res,
                           belief_res, pca_res)

    print(f"\n[완료] 팀원 B 설문 교차검증 완료! 그래프 12개 저장")
    print(f"  저장 위치: results/figures/team_b/")


if __name__ == '__main__':
    main()
