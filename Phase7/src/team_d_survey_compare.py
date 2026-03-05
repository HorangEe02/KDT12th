# -*- coding: utf-8 -*-
"""
팀원 D: MBTI 밈 설문 v2 × 기존 데이터 비교분석 & MBTI 예측
============================================================
데이터: survey_responses_v2.csv (밈 설문) + data.csv (Kaggle 43,744명)
분석: v2 밈 설문 응답에서 산출한 MBTI와 기존 대규모 데이터 비교, MBTI 예측

가설:
  H1: 설문 산출 MBTI와 자기보고 MBTI는 높은 일치율을 보인다
  H2: 설문 데이터의 차원 점수 분포는 기존 데이터와 유사하다
  H3: 기존 데이터 기반 최근접 중심 분류기로 MBTI를 예측할 수 있다
  H4: 혈액형에 따른 MBTI 차원 점수 차이는 없다
  H5: MBTI 밈 인식(신뢰도)은 차원 점수와 관련이 있다

통계 방법: 카이제곱, 독립표본 t-검정, ANOVA, 유클리드 거리 분류, 상관분석

그래프 목록 (13개):
  fig_d1  : 설문 응답자 인구통계 (4패널)
  fig_d2  : MBTI 자기보고 vs 설문산출 분포
  fig_d3  : 자기보고 vs 설문산출 일치도 매트릭스
  fig_d4  : 차원 점수 분포 비교 (설문 vs Kaggle)
  fig_d5  : 차원 점수 평균 비교 + CI
  fig_d6  : MBTI 유형 분포 비교 (설문 vs Kaggle)
  fig_d7  : 유형별 중심점 + 설문 응답자 위치
  fig_d8  : 최근접 중심 예측 결과
  fig_d9  : 혈액형 × MBTI 차원 점수 boxplot
  fig_d10 : MBTI 밈 인식 분석 (보너스 문항)
  fig_d11 : 효과크기 Forest Plot
  fig_d12 : 종합 결론 인포그래픽
  fig_d13 : 로지스틱 회귀 MBTI 예측 (Kaggle 학습 → 설문 테스트)
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
    MBTI_TYPES, MBTI_COLORS, BLOOD_COLORS, FIGSIZE_DEFAULT,
    MBTI_DIMENSIONS, DIMENSION_NAMES_KR
)
from common.data_loader import load_personality_data
from common.stats_utils import (
    descriptive_stats, chi_square_test, chi_square_goodness_of_fit,
    independent_t_test, one_way_anova, cohens_d,
    confidence_interval, pearson_correlation,
    linear_regression, multiple_linear_regression, print_test_result,
    logistic_regression_train, logistic_regression_predict, standardize_features,
    logistic_regression_diagnostics, compute_vif, logistic_aic_bic,
    logistic_mcfadden_r2, compute_classification_metrics
)
from common.plot_style import (
    set_project_style, save_figure, format_p_value, add_result_text
)

from survey.mbti_scoring_v2 import (
    batch_compute_from_array_v2, compute_from_csv_row_v2,
    extract_bonus_data,
    SCORING_MAP_V2, MIDPOINT, MBTI_TYPE_CONDITIONS, V2_COL_MAP
)

TEAM = 'team_d'

# v2 설문 CSV 경로 (실제 Google Form 응답 데이터)
SURVEY_CSV_V2 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'data', 'meme',
    'MBTI_밈_설문v2_응답_데이터 - Form Responses 1.csv'
)

# v1 설문 CSV (호환 - 있으면 사용)
SURVEY_CSV_V1 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'data', 'raw', 'survey_responses.csv'
)

# Kaggle 데이터의 차원 점수 컬럼명
KAGGLE_DIM_COLS = {
    'EI': 'introversion',
    'SN': 'sensing',
    'TF': 'thinking',
    'JP': 'judging',
}

DIM_LABELS_KR = {
    'EI': '내향성(I) 점수',
    'SN': '감각(S) 점수',
    'TF': '사고(T) 점수',
    'JP': '판단(J) 점수',
}


# ============================================================
#  데모 데이터 생성 (v2 형식)
# ============================================================

def generate_demo_survey_data_v2(n=80, seed=42):
    """v2 밈 설문 응답 데모 데이터 생성

    실제 survey_responses_v2.csv가 없을 때 파이프라인 검증용.
    numpy 정규분포로 MBTI 성향이 포함된 리커트 응답을 생성.

    CSV 구조 (v2):
      Col 0: 타임스탬프
      Col 1: Q1 MBTI (문자)
      Col 2: Q2 혈액형 (문자)
      Col 3: Q3 성별 (문자)
      Col 4: Q4 나이대 (문자)
      Col 5: Q5 검사방법 (문자)
      Col 6-14: Q6-Q14 E/I 리커트 (1-7)
      Col 15-23: Q15-Q23 S/N 양극 (1-7)
      Col 24-32: Q24-Q32 T/F 양극 (1-7)
      Col 33-41: Q33-Q41 J/P 양극 (1-7)
      Col 42: Q42 MBTI 신뢰도 (1-7)
      Col 43: Q43 혈액형 신뢰도 (1-7)
      Col 44: Q44 "너 T야?" 사용 (문자)
      Col 45: Q45 MBTI 태도 변화 (문자)
      Col 46: Q46 최종 생각 (문자)
      Col 47: 자유의견 (문자)
    """
    rng = np.random.RandomState(seed)

    # 기본정보 생성
    genders = rng.choice(['남성', '여성', '기타/응답 안 함'],
                         size=n, p=[0.45, 0.50, 0.05])
    ages = rng.choice(['10대', '20대', '30대', '40대 이상'],
                      size=n, p=[0.08, 0.55, 0.25, 0.12])
    blood_types = rng.choice(['A형', 'B형', 'O형', 'AB형', '모름'],
                             size=n, p=[0.30, 0.24, 0.26, 0.10, 0.10])

    # 자기보고 MBTI
    mbti_options = MBTI_TYPES + ['모름/검사 안 해봄']
    mbti_probs = np.array([0.058] * 16 + [0.072])
    mbti_probs /= mbti_probs.sum()
    self_mbti = rng.choice(mbti_options, size=n, p=mbti_probs)

    test_methods = rng.choice([
        '16Personalities 같은 인터넷 무료 테스트',
        '공인 기관 정식 검사',
        '친구가 "너 이거야" 해서 그냥 받아들임',
        'MBTI 밈 보고 "아 나 이거다" 하고 자가진단',
        '모름/관심 없음'
    ], size=n, p=[0.40, 0.10, 0.15, 0.20, 0.15])

    # ── E/I 리커트 (Q6-Q14, 9문항) ──
    # 전체 I방향: Q6~Q14 → 내향적이면 높은 점수 (7=극I, 1=극E)
    ei_responses = np.zeros((n, 9), dtype=int)
    for i in range(n):
        # 숨은 EI 성향 (0=극E, 7=극I, 4=중립)
        ei_tend = rng.normal(4.0, 1.5)
        for j in range(9):
            # 전체 I방향: 내향적이면 높은 점수
            val = ei_tend + rng.normal(0, 0.8)
            ei_responses[i, j] = int(np.clip(round(val), 1, 7))

    # ── S/N 양극 (Q15-Q23, 9문항) ──
    # 1=S(현실), 7=N(상상)
    sn_responses = np.zeros((n, 9), dtype=int)
    for i in range(n):
        sn_tend = rng.normal(4.0, 1.5)  # 높을수록 N
        for j in range(9):
            val = sn_tend + rng.normal(0, 0.8)
            sn_responses[i, j] = int(np.clip(round(val), 1, 7))

    # ── T/F 양극 (Q24-Q32, 9문항) ──
    # 1=T(논리), 7=F(감정)
    tf_responses = np.zeros((n, 9), dtype=int)
    for i in range(n):
        tf_tend = rng.normal(4.0, 1.5)  # 높을수록 F
        for j in range(9):
            val = tf_tend + rng.normal(0, 0.8)
            tf_responses[i, j] = int(np.clip(round(val), 1, 7))

    # ── J/P 양극 (Q33-Q41, 9문항) ──
    # 1=J(계획), 7=P(즉흥)
    jp_responses = np.zeros((n, 9), dtype=int)
    for i in range(n):
        jp_tend = rng.normal(4.0, 1.5)  # 높을수록 P
        for j in range(9):
            val = jp_tend + rng.normal(0, 0.8)
            jp_responses[i, j] = int(np.clip(round(val), 1, 7))

    # ── 보너스 (Q42-Q46) ──
    mbti_trust = rng.randint(1, 8, size=n)     # Q42 (1-7)
    blood_trust = rng.randint(1, 8, size=n)     # Q43 (1-7)
    are_you_t = rng.choice([
        '자주 쓴다 (일상 밈)', '가끔 쓴다',
        '들어는 봤는데 안 써봄', '처음 들어봄'
    ], size=n, p=[0.20, 0.35, 0.30, 0.15])
    mbti_attitude = rng.choice([
        '많이 바뀜 (MBTI 참고해서 대화함)',
        '약간 바뀜 (아 이래서 그랬구나~ 정도)',
        '바뀌지 않음 (참고만 하고 크게 신경 안 씀)',
        'MBTI 자체에 관심 없음'
    ], size=n, p=[0.15, 0.35, 0.35, 0.15])
    final_opinion = rng.choice([
        '과학적 근거 있음! 진지하게 활용할 수 있다',
        '완전 과학은 아니지만 꽤 맞는 부분이 있다',
        '재미로는 좋지만 진지하게 믿진 않는다',
        '완전 미신이라고 생각한다',
        '잘 모르겠다 / 관심 없다'
    ], size=n, p=[0.08, 0.30, 0.40, 0.12, 0.10])

    # ── 자유의견 ──
    free_text = np.array(['' for _ in range(n)])

    # ── 타임스탬프 ──
    timestamps = np.array([f'2026/02/{rng.randint(1, 28)} {rng.randint(9, 22)}:00:00'
                           for _ in range(n)])

    # ── 전체 합치기 ──
    # Col: timestamp(1) + 기본(5) + EI(9) + SN(9) + TF(9) + JP(9)
    #      + bonus_scale(2) + bonus_text(3) + free(1) = 48
    data = np.column_stack([
        timestamps,                # col 0
        self_mbti,                 # col 1
        blood_types,               # col 2
        genders,                   # col 3
        ages,                      # col 4
        test_methods,              # col 5
        ei_responses,              # col 6-14
        sn_responses,              # col 15-23
        tf_responses,              # col 24-32
        jp_responses,              # col 33-41
        mbti_trust,                # col 42
        blood_trust,               # col 43
        are_you_t,                 # col 44
        mbti_attitude,             # col 45
        final_opinion,             # col 46
        free_text,                 # col 47
    ])

    return data


# ============================================================
#  데이터 로딩
# ============================================================

def load_and_preprocess():
    """v2 설문 데이터 + Kaggle 데이터 로딩 및 전처리"""
    print("\n" + "=" * 60)
    print("  팀원 D: MBTI 밈 설문 v2 × 기존 데이터 비교분석 & MBTI 예측")
    print("=" * 60)

    # 1. 설문 데이터 (v2 우선, 없으면 데모)
    is_demo = False
    if os.path.exists(SURVEY_CSV_V2):
        df = pd.read_csv(SURVEY_CSV_V2)
        survey_raw = df.values
        print(f"\n[데이터] v2 밈 설문 응답 파일 로딩: {len(df)}건")
    elif os.path.exists(SURVEY_CSV_V1):
        # v1이 있으면 안내 (v2 전용이므로 데모 사용)
        print(f"\n[데이터] v2 설문 CSV 미발견 (v1은 존재)")
        print(f"         → 데모 데이터 80명 생성 (v2 형식)")
        print(f"         (v2 설문 CSV: data/raw/survey_responses_v2.csv)")
        survey_raw = generate_demo_survey_data_v2(n=80)
        is_demo = True
    else:
        print(f"\n[데이터] 설문 CSV 미발견 → 데모 데이터 80명 생성 (v2 형식)")
        print(f"         (실제 설문 CSV를 data/raw/survey_responses_v2.csv 에 저장하면 자동 전환)")
        survey_raw = generate_demo_survey_data_v2(n=80)
        is_demo = True

    # 2. MBTI 채점 (v2: Q6~Q41 → 4차원 점수 + MBTI 유형)
    batch = batch_compute_from_array_v2(survey_raw)
    survey_types = batch['types']
    survey_scores = batch['scores']

    print(f"[채점] v2 설문 산출 MBTI: {len(survey_types)}명 분류 완료")
    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        s = survey_scores[dim_key]
        print(f"  [{dim_key}] 평균={np.mean(s):.2f}, SD={np.std(s):.2f}, "
              f"범위=[{np.min(s):.1f}, {np.max(s):.1f}]")

    # 3. 자기보고 MBTI (v2 col 1)
    self_mbti = survey_raw[:, V2_COL_MAP['self_mbti']].astype(str)

    # 4. 혈액형 (v2 col 2)
    blood_types = survey_raw[:, V2_COL_MAP['blood_type']].astype(str)

    # 5. 인구통계
    genders = survey_raw[:, V2_COL_MAP['gender']].astype(str)
    ages = survey_raw[:, V2_COL_MAP['age']].astype(str)
    test_methods = survey_raw[:, V2_COL_MAP['test_method']].astype(str)

    # 6. 보너스 문항 추출
    bonus = extract_bonus_data(survey_raw)

    # 7. Kaggle 데이터 로딩
    kaggle = load_personality_data()
    print(f"\n[데이터] Kaggle 데이터: {len(kaggle['personality'])}명")

    return {
        'survey_raw': survey_raw,
        'survey_types': survey_types,
        'survey_scores': survey_scores,
        'self_mbti': self_mbti,
        'blood_types': blood_types,
        'genders': genders,
        'ages': ages,
        'test_methods': test_methods,
        'bonus': bonus,
        'kaggle': kaggle,
        'is_demo': is_demo,
        'n_survey': len(survey_types),
    }


# ============================================================
#  분석 1: 설문 응답 EDA
# ============================================================

def analyze_survey_eda(data):
    """설문 응답자 기본 인구통계 + MBTI 분포"""
    print("\n\n" + "━" * 60)
    print("  분석 1: v2 밈 설문 응답 EDA")
    print("━" * 60)

    tag = ' [데모]' if data['is_demo'] else ''
    n = data['n_survey']

    # --- fig_d1: 인구통계 4-패널 ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'v2 밈 설문 응답자 인구통계 (n={n}){tag}',
                 fontsize=24, fontweight='bold')

    # 성별 (정렬: 남성, 여성, 기타)
    gvals, gcounts = np.unique(data['genders'], return_counts=True)
    gender_order = ['남성', '여성', '기타/응답 안 함']
    g_sorted_vals, g_sorted_counts = [], []
    for g in gender_order:
        idx = np.where(gvals == g)[0]
        if len(idx) > 0:
            g_sorted_vals.append(g)
            g_sorted_counts.append(gcounts[idx[0]])
    g_sorted_counts = np.array(g_sorted_counts)
    g_colors = ['#5DADE2', '#F1948A', '#95A5A6'][:len(g_sorted_vals)]
    axes[0, 0].barh(g_sorted_vals, g_sorted_counts, color=g_colors)
    axes[0, 0].set_title('성별 분포')
    for i, (v, c) in enumerate(zip(g_sorted_vals, g_sorted_counts)):
        axes[0, 0].text(c + 0.3, i, f'{c}명 ({c/n*100:.1f}%)', va='center', fontsize=14)

    # 나이대 (정렬: 10대 < 20대 < 30대 < 40대 이상)
    avals, acounts = np.unique(data['ages'], return_counts=True)
    age_order = ['10대', '20대', '30대', '40대 이상']
    a_sorted_vals, a_sorted_counts = [], []
    for a in age_order:
        idx = np.where(avals == a)[0]
        if len(idx) > 0:
            a_sorted_vals.append(a)
            a_sorted_counts.append(acounts[idx[0]])
    a_sorted_counts = np.array(a_sorted_counts)
    bars_age = axes[0, 1].bar(a_sorted_vals, a_sorted_counts, color='#3498DB', alpha=0.7)
    axes[0, 1].set_title('나이대 분포')
    axes[0, 1].tick_params(axis='x', rotation=30)
    for bar, c in zip(bars_age, a_sorted_counts):
        axes[0, 1].text(bar.get_x() + bar.get_width()/2, c + 0.3,
                        f'{c}명\n({c/n*100:.1f}%)', ha='center', fontsize=12)

    # 혈액형
    bvals, bcounts = np.unique(data['blood_types'], return_counts=True)
    blood_order = ['A형', 'B형', 'O형', 'AB형', '모름']
    b_sorted_vals, b_sorted_counts = [], []
    for b in blood_order:
        idx = np.where(bvals == b)[0]
        if len(idx) > 0:
            b_sorted_vals.append(b)
            b_sorted_counts.append(bcounts[idx[0]])
    b_sorted_counts = np.array(b_sorted_counts)
    colors_b = [BLOOD_COLORS.get(v.replace('형', ''), '#95A5A6') for v in b_sorted_vals]
    bars_blood = axes[1, 0].bar(b_sorted_vals, b_sorted_counts, color=colors_b)
    axes[1, 0].set_title('혈액형 분포')
    for bar, c in zip(bars_blood, b_sorted_counts):
        axes[1, 0].text(bar.get_x() + bar.get_width()/2, c + 0.3,
                        f'{c}명 ({c/n*100:.1f}%)', ha='center', fontsize=12)

    # MBTI 검사 방법 (v2 신규)
    tvals, tcounts = np.unique(data['test_methods'], return_counts=True)
    sort_idx = np.argsort(-tcounts)
    # 라벨 줄이기
    short_labels = []
    for t in tvals[sort_idx]:
        t_str = str(t)
        if '16Personalities' in t_str or '인터넷' in t_str:
            short_labels.append('인터넷 무료')
        elif '공인' in t_str or '정식' in t_str:
            short_labels.append('정식 검사')
        elif '친구' in t_str:
            short_labels.append('친구 판정')
        elif '밈' in t_str or '자가' in t_str:
            short_labels.append('밈 자가진단')
        else:
            short_labels.append('모름/기타')
    bars_method = axes[1, 1].barh(short_labels[::-1], tcounts[sort_idx][::-1],
                                   color='#9B59B6', alpha=0.7)
    axes[1, 1].set_title('MBTI 검사 방법')
    for bar, c in zip(bars_method, tcounts[sort_idx][::-1]):
        axes[1, 1].text(c + 0.3, bar.get_y() + bar.get_height()/2,
                        f'{c}명 ({c/n*100:.1f}%)', va='center', fontsize=12)

    # 응답 요약 텍스트
    print(f"\n  [응답 요약] 총 {n}명")
    print(f"  성별: {', '.join([f'{v}({c})' for v, c in zip(g_sorted_vals, g_sorted_counts)])}")
    print(f"  나이대: {', '.join([f'{v}({c})' for v, c in zip(a_sorted_vals, a_sorted_counts)])}")
    print(f"  혈액형: {', '.join([f'{v}({c})' for v, c in zip(b_sorted_vals, b_sorted_counts)])}")

    save_figure(fig, TEAM, 'fig_d1_survey_demographics.png')

    # --- fig_d2: 설문산출 MBTI vs 자기보고 MBTI 분포 비교 ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f'MBTI 유형 분포: 자기보고 vs v2 설문 산출{tag}',
                 fontsize=24, fontweight='bold')

    # 자기보고
    valid_self = data['self_mbti'][data['self_mbti'] != '모름/검사 안 해봄']
    if len(valid_self) > 0:
        self_types, self_counts = np.unique(valid_self, return_counts=True)
        sort_idx = np.argsort(-self_counts)
        colors_self = [MBTI_COLORS.get(t, '#95A5A6') for t in self_types[sort_idx]]
        axes[0].barh(self_types[sort_idx][::-1], self_counts[sort_idx][::-1],
                    color=colors_self[::-1])
        axes[0].set_title('자기보고 MBTI')
        axes[0].set_xlabel('인원수')
    else:
        axes[0].text(0.5, 0.5, '유효 자기보고 없음', ha='center', va='center',
                    transform=axes[0].transAxes, fontsize=18)
        axes[0].set_title('자기보고 MBTI')

    # 설문 산출
    calc_types, calc_counts = np.unique(data['survey_types'], return_counts=True)
    sort_idx = np.argsort(-calc_counts)
    colors_calc = [MBTI_COLORS.get(t, '#95A5A6') for t in calc_types[sort_idx]]
    axes[1].barh(calc_types[sort_idx][::-1], calc_counts[sort_idx][::-1],
                color=colors_calc[::-1])
    axes[1].set_title('v2 설문 산출 MBTI')
    axes[1].set_xlabel('인원수')

    save_figure(fig, TEAM, 'fig_d2_mbti_self_vs_calc_dist.png')


# ============================================================
#  분석 2: 자기보고 vs 설문산출 MBTI 일치도
# ============================================================

def _compute_cohens_kappa(labels_a, labels_b):
    """Cohen's kappa 계수 산출 (우연 일치 보정) — numpy 수동 구현"""
    all_labels = sorted(np.unique(np.concatenate([labels_a, labels_b])))
    n = len(labels_a)
    k = len(all_labels)
    label_to_idx = {l: i for i, l in enumerate(all_labels)}

    # 혼동행렬
    cm = np.zeros((k, k), dtype=float)
    for a, b in zip(labels_a, labels_b):
        if a in label_to_idx and b in label_to_idx:
            cm[label_to_idx[a], label_to_idx[b]] += 1

    # 관찰 일치율
    p_o = np.trace(cm) / n

    # 우연 일치율
    row_sums = cm.sum(axis=1) / n
    col_sums = cm.sum(axis=0) / n
    p_e = np.sum(row_sums * col_sums)

    # kappa
    if p_e == 1.0:
        kappa = 1.0
    else:
        kappa = (p_o - p_e) / (1 - p_e)

    # 해석
    if kappa >= 0.81:
        interp = '거의 완벽한 일치'
    elif kappa >= 0.61:
        interp = '상당한 일치'
    elif kappa >= 0.41:
        interp = '보통 일치'
    elif kappa >= 0.21:
        interp = '약한 일치'
    elif kappa >= 0.0:
        interp = '미미한 일치'
    else:
        interp = '불일치'

    return {'kappa': kappa, 'p_o': p_o, 'p_e': p_e, 'interpretation': interp}


def analyze_agreement(data):
    """자기보고 MBTI와 v2 설문 산출 MBTI 일치율 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 2: 자기보고 vs v2 설문산출 MBTI 일치도")
    print("━" * 60)

    self_mbti = data['self_mbti']
    calc_mbti = data['survey_types']
    tag = ' [데모]' if data['is_demo'] else ''

    # '모름' 제외
    valid_mask = (self_mbti != '모름/검사 안 해봄') & (self_mbti != 'nan')
    # 실제 MBTI 형식인지 체크 (4글자)
    valid_mask = valid_mask & np.array([len(str(s)) == 4 for s in self_mbti])
    n_valid = np.sum(valid_mask)
    n_unknown = np.sum(~valid_mask)

    if n_valid == 0:
        print("  [경고] 유효한 자기보고 MBTI가 없어 일치도 분석을 건너뜁니다.")
        return {}

    self_v = self_mbti[valid_mask]
    calc_v = calc_mbti[valid_mask]

    # 전체 일치율
    exact_match = np.sum(self_v == calc_v)
    match_rate = exact_match / n_valid * 100
    print(f"\n  [전체 일치율] {exact_match}/{n_valid} ({match_rate:.1f}%)")
    print(f"  ['모름/미응답' 제외] {n_unknown}명 제외됨")

    # Cohen's kappa
    kappa_result = _compute_cohens_kappa(self_v, calc_v)
    print(f"  [Cohen's kappa] k={kappa_result['kappa']:.3f} ({kappa_result['interpretation']})")
    print(f"    관찰 일치율(p_o)={kappa_result['p_o']:.3f}, 우연 일치율(p_e)={kappa_result['p_e']:.3f}")

    # 차원별 일치율 + kappa
    dim_matches = {}
    dim_kappas = {}
    for dim_idx, dim_key in enumerate(['EI', 'SN', 'TF', 'JP']):
        self_dim = np.array([s[dim_idx] for s in self_v])
        calc_dim = np.array([c[dim_idx] for c in calc_v])
        match_n = np.sum(self_dim == calc_dim)
        dim_rate = match_n / n_valid * 100
        dim_matches[dim_key] = dim_rate

        dim_kappa = _compute_cohens_kappa(self_dim, calc_dim)
        dim_kappas[dim_key] = dim_kappa['kappa']

        print(f"  [{dim_key}] {match_n}/{n_valid} ({dim_rate:.1f}%), "
              f"kappa={dim_kappa['kappa']:.3f} ({dim_kappa['interpretation']})")

    # --- fig_d3: Confusion Matrix + 차원별 일치 막대 차트 ---
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    fig.suptitle(f'자기보고 vs v2 설문산출 MBTI 일치도 분석{tag}',
                 fontsize=22, fontweight='bold')

    # 왼쪽: 혼동행렬
    ax = axes[0]
    all_types = sorted(np.unique(np.concatenate([self_v, calc_v])))
    n_types = len(all_types)
    type_to_idx = {t: i for i, t in enumerate(all_types)}

    conf_matrix = np.zeros((n_types, n_types), dtype=int)
    for s, c in zip(self_v, calc_v):
        if s in type_to_idx and c in type_to_idx:
            conf_matrix[type_to_idx[s], type_to_idx[c]] += 1

    im = ax.imshow(conf_matrix, cmap='Blues', aspect='auto')
    ax.set_xticks(range(n_types))
    ax.set_yticks(range(n_types))
    ax.set_xticklabels(all_types, rotation=45, ha='right', fontsize=11)
    ax.set_yticklabels(all_types, fontsize=11)
    ax.set_xlabel('v2 설문 산출 MBTI')
    ax.set_ylabel('자기보고 MBTI')
    ax.set_title(f'일치율: {match_rate:.1f}%  |  '
                 f"Cohen's kappa: {kappa_result['kappa']:.3f}\n"
                 f"(유효: {n_valid}명, 모름/미응답: {n_unknown}명)",
                 fontsize=16)

    for i in range(n_types):
        for j in range(n_types):
            val = conf_matrix[i, j]
            if val > 0:
                color = 'white' if val > conf_matrix.max() * 0.5 else 'black'
                ax.text(j, i, str(val), ha='center', va='center',
                       fontsize=11, color=color, fontweight='bold')

    plt.colorbar(im, ax=ax, shrink=0.8, label='인원수')

    # 오른쪽: 차원별 일치율 + kappa 막대 차트
    ax2 = axes[1]
    dims = ['EI', 'SN', 'TF', 'JP']
    x = np.arange(len(dims))
    width = 0.35

    match_rates = [dim_matches[d] for d in dims]
    kappa_vals = [dim_kappas[d] * 100 for d in dims]  # 백분율로 변환

    bars1 = ax2.bar(x - width/2, match_rates, width,
                    label='일치율 (%)', color='#3498DB', alpha=0.8)
    bars2 = ax2.bar(x + width/2, kappa_vals, width,
                    label='kappa x 100', color='#E74C3C', alpha=0.8)

    ax2.set_xticks(x)
    ax2.set_xticklabels(dims, fontsize=16)
    ax2.set_ylabel('(%)', fontsize=14)
    ax2.set_title('차원별 일치율 vs Cohen\'s kappa', fontsize=16)
    ax2.legend(fontsize=14)
    ax2.set_ylim(0, 105)
    ax2.axhline(y=50, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    for bar, val in zip(bars1, match_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}%', ha='center', fontsize=13, fontweight='bold')
    for bar, val in zip(bars2, kappa_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}', ha='center', fontsize=13, fontweight='bold', color='#E74C3C')

    save_figure(fig, TEAM, 'fig_d3_agreement_confusion_matrix.png')

    return {
        'match_rate': match_rate,
        'dim_matches': dim_matches,
        'dim_kappas': dim_kappas,
        'kappa': kappa_result['kappa'],
        'kappa_interp': kappa_result['interpretation'],
        'n_valid': n_valid,
        'n_unknown': n_unknown,
    }


# ============================================================
#  분석 3: 설문 vs Kaggle 차원 점수 비교
# ============================================================

def analyze_score_comparison(data):
    """v2 설문 데이터와 Kaggle 데이터의 MBTI 차원 점수 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 3: v2 설문 vs Kaggle 차원 점수 비교")
    print("━" * 60)
    print("  H0: v2 설문과 Kaggle의 차원 점수 평균은 동일하다")
    print("  H2: 두 데이터셋 간 유의한 차이가 존재한다")

    kaggle = data['kaggle']
    tag = ' [데모]' if data['is_demo'] else ''
    comparison_results = {}

    # Kaggle의 차원 점수 매핑
    kaggle_scores = {
        'EI': kaggle['introversion'],
        'SN': kaggle['sensing'],
        'TF': kaggle['thinking'],
        'JP': kaggle['judging'],
    }

    # --- fig_d4: 히스토그램 오버레이 ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'MBTI 차원 점수 분포 비교: v2 설문 vs Kaggle{tag}',
                 fontsize=24, fontweight='bold')

    for idx, dim_key in enumerate(['EI', 'SN', 'TF', 'JP']):
        ax = axes[idx // 2, idx % 2]
        survey_s = data['survey_scores'][dim_key]
        kaggle_s = kaggle_scores[dim_key]

        # 히스토그램 오버레이
        ax.hist(kaggle_s, bins=30, density=True, alpha=0.5,
                color='#3498DB', label=f'Kaggle (n={len(kaggle_s):,})')
        ax.hist(survey_s, bins=15, density=True, alpha=0.6,
                color='#E74C3C', label=f'v2 설문 (n={len(survey_s)})')

        # t-검정
        result = independent_t_test(survey_s, kaggle_s)
        d = cohens_d(survey_s, kaggle_s)
        comparison_results[dim_key] = {
            't': result['t_stat'],
            'p': result['p_value'],
            'd': d['d'],
            'survey_mean': np.mean(survey_s),
            'kaggle_mean': np.mean(kaggle_s),
        }

        sig = '*' if result['p_value'] < 0.05 else 'ns'
        ax.set_title(f'{DIM_LABELS_KR[dim_key]} [{sig}]')
        ax.legend(fontsize=17)
        ax.set_xlabel('점수')
        ax.set_ylabel('밀도')

        # 평균선
        ax.axvline(np.mean(survey_s), color='#E74C3C', linestyle='--', linewidth=1.5)
        ax.axvline(np.mean(kaggle_s), color='#3498DB', linestyle='--', linewidth=1.5)

        print_test_result(f"t-검정: {dim_key} (v2 설문 vs Kaggle)", result)
        print(f"  Cohen's d = {d['d']:.4f} ({d['interpretation']})")

    save_figure(fig, TEAM, 'fig_d4_score_distribution_compare.png')

    # --- fig_d5: 평균 비교 막대그래프 + CI + 효과크기 해석 ---
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.suptitle(f'MBTI 차원 점수 평균 비교 (95% CI){tag}',
                 fontsize=22, fontweight='bold')

    # 왼쪽: 막대 비교
    ax = axes[0]
    dims = ['EI', 'SN', 'TF', 'JP']
    x = np.arange(len(dims))
    width = 0.35

    survey_means = [np.mean(data['survey_scores'][d]) for d in dims]
    kaggle_means = [np.mean(kaggle_scores[d]) for d in dims]
    survey_ci = [confidence_interval(data['survey_scores'][d]) for d in dims]
    kaggle_ci = [confidence_interval(kaggle_scores[d]) for d in dims]

    survey_errs = [(m - ci['lower'], ci['upper'] - m)
                   for m, ci in zip(survey_means, survey_ci)]
    kaggle_errs = [(m - ci['lower'], ci['upper'] - m)
                   for m, ci in zip(kaggle_means, kaggle_ci)]

    bars1 = ax.bar(x - width/2, survey_means, width,
                   yerr=np.array(survey_errs).T, capsize=5,
                   label=f'v2 설문 (n={data["n_survey"]})', color='#E74C3C', alpha=0.7)
    bars2 = ax.bar(x + width/2, kaggle_means, width,
                   yerr=np.array(kaggle_errs).T, capsize=5,
                   label=f'Kaggle (n={len(kaggle["personality"]):,})', color='#3498DB', alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels([DIM_LABELS_KR[d] for d in dims])
    ax.set_ylabel('평균 점수')
    ax.set_title('차원 점수 평균 + 95% CI', fontsize=18)
    ax.legend(fontsize=18)
    ax.axhline(y=MIDPOINT, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.text(len(dims)-0.1, MIDPOINT+0.1, f'중립점({MIDPOINT})', fontsize=16, color='gray')

    # p-value + Cohen's d 표시
    for i, dim_key in enumerate(dims):
        cr = comparison_results[dim_key]
        sig_mark = '***' if cr['p'] < 0.001 else ('**' if cr['p'] < 0.01 else
                   ('*' if cr['p'] < 0.05 else 'ns'))
        y_max = max(survey_means[i], kaggle_means[i]) + 0.7
        ax.text(i, y_max, f'{sig_mark}\nd={cr["d"]:.2f}', ha='center', fontsize=17,
                fontweight='bold', color='red' if cr['p'] < 0.05 else 'gray')

    # 오른쪽: 기술통계 요약 테이블
    ax2 = axes[1]
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.set_axis_off()
    ax2.set_title('기술통계 비교 요약', fontsize=18)

    # 테이블 데이터
    table_data = [['차원', '설문 M(SD)', 'Kaggle M(SD)', "Cohen's d", '해석']]
    for dk in dims:
        s_scores = data['survey_scores'][dk]
        k_scores = kaggle_scores[dk]
        cr = comparison_results[dk]
        d_abs = abs(cr['d'])
        if d_abs >= 0.8:
            d_interp = '큰 효과'
        elif d_abs >= 0.5:
            d_interp = '보통'
        elif d_abs >= 0.2:
            d_interp = '작은 효과'
        else:
            d_interp = '무시'
        table_data.append([
            dk,
            f'{np.mean(s_scores):.2f}({np.std(s_scores):.2f})',
            f'{np.mean(k_scores):.2f}({np.std(k_scores):.2f})',
            f'{cr["d"]:.3f}',
            d_interp,
        ])
    # 소표본 경고 추가
    table_data.append(['', '', '', '', ''])
    table_data.append(['[주의]', f'설문 n={data["n_survey"]}',
                       f'Kaggle n={len(kaggle["personality"]):,}', 'SE 차이', '큼'])

    table = ax2.table(cellText=table_data, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1.0, 1.8)

    # 헤더 색상
    for j in range(5):
        table[0, j].set_facecolor('#3498DB')
        table[0, j].set_text_props(color='white', fontweight='bold')
    # 마지막 행 (주의) 색상
    for j in range(5):
        table[len(table_data)-1, j].set_facecolor('#FEF9E7')
        table[len(table_data)-2, j].set_facecolor('#FEF9E7')

    save_figure(fig, TEAM, 'fig_d5_score_mean_comparison.png')

    # --- 회귀분석: 차원 점수 명확도 → 자기보고 일치도 ---
    print(f"\n  [회귀분석] 차원 점수 명확도와 자기보고 일치 관계")
    print(f"  가설: 점수가 극단적(명확)할수록 자기보고 MBTI와 일치할 확률이 높은가?")

    # 1) 차원별 단순 회귀: |score - 4.0| → agreement (0/1)
    self_mbti = data['self_mbti']
    valid_self = np.array([len(str(s)) == 4 for s in self_mbti])

    if np.sum(valid_self) >= 10:
        for dim_idx, dk in enumerate(dims):
            scores = data['survey_scores'][dk][valid_self]
            clarity = np.abs(scores - MIDPOINT)
            # 차원별 일치 여부
            calc_letters = np.array([t[dim_idx] for t in data['survey_types'][valid_self]])
            self_letters = np.array([str(s)[dim_idx] for s in self_mbti[valid_self]])
            agreement_binary = (calc_letters == self_letters).astype(float)

            reg = linear_regression(clarity, agreement_binary)
            print(f"    [{dk}] 일치확률 = {reg['slope']:.4f} \u00d7 |점수-4.0| + {reg['intercept']:.4f}, "
                  f"R\u00b2={reg['r_squared']:.4f}, "
                  f"{'*' if reg['p_value'] < 0.05 else 'ns'}")

        # 2) 다중회귀: 4차원 명확도 → 전체 일치 차원 수 (0~4)
        clarity_matrix = np.column_stack([
            np.abs(data['survey_scores'][dk][valid_self] - MIDPOINT)
            for dk in dims
        ])
        # 전체 일치 차원 수
        match_count = np.zeros(np.sum(valid_self))
        for dim_idx, dk in enumerate(dims):
            calc_letters = np.array([t[dim_idx] for t in data['survey_types'][valid_self]])
            self_letters = np.array([str(s)[dim_idx] for s in self_mbti[valid_self]])
            match_count += (calc_letters == self_letters).astype(float)

        mreg = multiple_linear_regression(clarity_matrix, match_count)
        print(f"\n  [다중회귀] 4차원 명확도 → 전체 일치 차원 수")
        print(f"    회귀식: 일치수 = ", end='')
        coef_strs = []
        for i, dk in enumerate(dims):
            coef_strs.append(f"{mreg['betas'][i+1]:.4f}\u00d7|{dk}-4.0|")
        print(' + '.join(coef_strs) + f" + {mreg['betas'][0]:.4f}")
        print(f"    R\u00b2 = {mreg['r_squared']:.4f}, adj_R\u00b2 = {mreg['adj_r_squared']:.4f}")
        print(f"    F = {mreg['f_stat']:.3f}, {format_p_value(mreg['p_value'])}")
        if mreg['r_squared'] < 0.13:
            print(f"    해석: R\u00b2 < 0.13 \u2192 예측력 작음 (점수 명확도가 일치도를 잘 설명하지 못함)")
        elif mreg['r_squared'] < 0.26:
            print(f"    해석: 0.13 \u2264 R\u00b2 < 0.26 \u2192 보통 수준의 예측력")
        else:
            print(f"    해석: R\u00b2 \u2265 0.26 \u2192 큰 예측력")

        comparison_results['regression'] = {
            'multiple_r_squared': mreg['r_squared'],
            'adj_r_squared': mreg['adj_r_squared'],
            'betas': mreg['betas'],
            'f_stat': mreg['f_stat'],
            'p_value': mreg['p_value'],
        }

    return comparison_results


# ============================================================
#  분석 4: MBTI 유형 분포 비교
# ============================================================

def analyze_type_distribution(data):
    """v2 설문 MBTI 유형 분포 vs Kaggle 분포 비교"""
    print("\n\n" + "━" * 60)
    print("  분석 4: v2 설문 MBTI 유형 분포 vs Kaggle 분포 비교")
    print("━" * 60)

    kaggle = data['kaggle']
    tag = ' [데모]' if data['is_demo'] else ''

    # 설문 산출 유형 빈도
    survey_types, survey_counts = np.unique(data['survey_types'], return_counts=True)
    survey_freq = dict(zip(survey_types, survey_counts))

    # Kaggle 유형 빈도
    kaggle_types, kaggle_counts = np.unique(kaggle['personality'], return_counts=True)
    kaggle_freq = dict(zip(kaggle_types, kaggle_counts))

    # 공통 유형으로 정렬
    all_types = sorted(set(list(survey_freq.keys()) + list(kaggle_freq.keys())))

    survey_arr = np.array([survey_freq.get(t, 0) for t in all_types])
    kaggle_arr = np.array([kaggle_freq.get(t, 0) for t in all_types])

    survey_pct = survey_arr / survey_arr.sum() * 100
    kaggle_pct = kaggle_arr / kaggle_arr.sum() * 100

    # 카이제곱 적합도 검정
    kaggle_ratios = kaggle_arr / kaggle_arr.sum()
    nonzero_mask = survey_arr > 0
    if np.sum(nonzero_mask) >= 2:
        expected = kaggle_ratios[nonzero_mask] * survey_arr.sum()
        expected = np.maximum(expected, 0.5)
        chi2_result = chi_square_goodness_of_fit(
            survey_arr[nonzero_mask], expected
        )
        print_test_result("카이제곱 적합도: v2 설문 MBTI 분포 vs Kaggle 비율", chi2_result)
    else:
        chi2_result = None
        print("  [경고] 유효 유형 부족으로 적합도 검정 생략")

    # --- fig_d6: 유형 분포 그룹 막대 차트 ---
    fig, ax = plt.subplots(figsize=(16, 8))

    x = np.arange(len(all_types))
    width = 0.35

    bars1 = ax.bar(x - width/2, survey_pct, width, label=f'v2 설문 (n={data["n_survey"]})',
                   color='#E74C3C', alpha=0.7)
    bars2 = ax.bar(x + width/2, kaggle_pct, width, label=f'Kaggle (n={len(kaggle["personality"]):,})',
                   color='#3498DB', alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(all_types, rotation=45, ha='right')
    ax.set_ylabel('비율 (%)')

    # 카이제곱 결과를 제목에 표시
    if chi2_result:
        chi2_str = (f'chi2={chi2_result.get("chi2_stat", 0):.2f}, '
                    f'p={format_p_value(chi2_result.get("p_value", 1))}')
    else:
        chi2_str = '검정 불가'
    ax.set_title(f'MBTI 유형 분포 비교: v2 설문 vs Kaggle{tag}\n({chi2_str})',
                 fontsize=20)
    ax.legend(fontsize=16)

    # 설문 실제 인원수 표시 (소표본이므로 N이 중요)
    for i, (pct, cnt) in enumerate(zip(survey_pct, survey_arr)):
        if cnt > 0:
            ax.text(x[i] - width/2, pct + 0.3, f'n={cnt}',
                    ha='center', fontsize=10, color='#E74C3C', fontweight='bold')

    # 차이가 큰 유형 강조
    diff = np.abs(survey_pct - kaggle_pct)
    top3_idx = np.argsort(-diff)[:3]
    for idx in top3_idx:
        y_pos = max(survey_pct[idx], kaggle_pct[idx]) + 1.5
        ax.annotate(f'{diff[idx]:+.1f}%p',
                   xy=(x[idx], y_pos),
                   ha='center', fontsize=13, color='red', fontweight='bold')

    save_figure(fig, TEAM, 'fig_d6_type_distribution_compare.png')

    return chi2_result


# ============================================================
#  분석 5: MBTI 예측 — 최근접 중심 분류
# ============================================================

def analyze_mbti_prediction(data):
    """Kaggle 데이터 기반 최근접 중심(centroid) 분류로 MBTI 예측"""
    print("\n\n" + "━" * 60)
    print("  분석 5: MBTI 예측 — 최근접 중심 분류기")
    print("━" * 60)
    print("  방법: Kaggle 43,744명의 16유형별 중심점 계산 → v2 설문 응답자 분류")

    kaggle = data['kaggle']
    tag = ' [데모]' if data['is_demo'] else ''

    # 1. Kaggle 데이터로 유형별 중심(centroid) 계산
    kaggle_dims = np.column_stack([
        kaggle['introversion'],
        kaggle['sensing'],
        kaggle['thinking'],
        kaggle['judging'],
    ])
    kaggle_labels = kaggle['personality']

    centroids = {}
    centroid_matrix = []
    type_order = sorted(np.unique(kaggle_labels))

    for mbti_type in type_order:
        mask = kaggle_labels == mbti_type
        centroid = np.mean(kaggle_dims[mask], axis=0)
        centroids[mbti_type] = centroid
        centroid_matrix.append(centroid)

    centroid_matrix = np.array(centroid_matrix)
    print(f"\n  [중심점] {len(centroids)}개 유형별 centroid 계산 완료")

    for t in type_order:
        c = centroids[t]
        print(f"    {t}: EI={c[0]:.2f}, SN={c[1]:.2f}, TF={c[2]:.2f}, JP={c[3]:.2f}")

    # 2. v2 설문 응답자에 대해 예측
    survey_dims = np.column_stack([
        data['survey_scores']['EI'],
        data['survey_scores']['SN'],
        data['survey_scores']['TF'],
        data['survey_scores']['JP'],
    ])

    predicted_types = []
    predicted_distances = []

    for i in range(len(survey_dims)):
        point = survey_dims[i]
        distances = np.sqrt(np.sum((centroid_matrix - point) ** 2, axis=1))
        nearest_idx = np.argmin(distances)
        predicted_types.append(type_order[nearest_idx])
        predicted_distances.append(distances[nearest_idx])

    predicted_types = np.array(predicted_types)
    predicted_distances = np.array(predicted_distances)

    # 3. 예측 정확도 (설문 산출 MBTI 대비)
    calc_types = data['survey_types']
    accuracy = np.mean(predicted_types == calc_types) * 100

    # 차원별 일치율
    dim_accuracy = {}
    for dim_idx, dim_key in enumerate(['EI', 'SN', 'TF', 'JP']):
        pred_dim = np.array([t[dim_idx] for t in predicted_types])
        calc_dim = np.array([t[dim_idx] for t in calc_types])
        dim_accuracy[dim_key] = np.mean(pred_dim == calc_dim) * 100

    print(f"\n  [예측 결과]")
    print(f"    전체 일치율: {accuracy:.1f}%")
    for dk, da in dim_accuracy.items():
        print(f"    {dk} 차원: {da:.1f}%")
    print(f"    평균 거리: {np.mean(predicted_distances):.3f}")

    # 4. 예측 확신도 (1등 거리 / 2등 거리)
    confidences = []
    for i in range(len(survey_dims)):
        point = survey_dims[i]
        distances = np.sqrt(np.sum((centroid_matrix - point) ** 2, axis=1))
        sorted_dists = np.sort(distances)
        if sorted_dists[0] > 0:
            confidence = 1 - (sorted_dists[0] / sorted_dists[1])
        else:
            confidence = 1.0
        confidences.append(confidence)
    confidences = np.array(confidences)

    # 5. 자기보고 vs 중심분류기 일치율
    self_mbti = data['self_mbti']
    valid_mask = np.array([len(str(s)) == 4 for s in self_mbti])
    if np.sum(valid_mask) > 0:
        self_pred_match = np.mean(predicted_types[valid_mask] == self_mbti[valid_mask]) * 100
    else:
        self_pred_match = 0.0

    print(f"    자기보고 vs 중심분류기: {self_pred_match:.1f}%")
    print(f"    평균 확신도: {np.mean(confidences):.3f}")

    # --- fig_d7: 중심점 시각화 + 설문 데이터 오버레이 ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f'MBTI 유형별 중심점 + v2 설문 응답자 위치{tag}',
                 fontsize=22, fontweight='bold')

    dim_pairs = [('EI', 'SN'), ('EI', 'TF'), ('SN', 'JP')]
    dim_idx_map = {'EI': 0, 'SN': 1, 'TF': 2, 'JP': 3}

    for ax_idx, (dx, dy) in enumerate(dim_pairs):
        ax = axes[ax_idx]
        xi, yi = dim_idx_map[dx], dim_idx_map[dy]

        # 결정 경계 (MIDPOINT=4.0)
        ax.axhline(y=MIDPOINT, color='#E74C3C', linestyle='--', linewidth=1.2, alpha=0.4)
        ax.axvline(x=MIDPOINT, color='#E74C3C', linestyle='--', linewidth=1.2, alpha=0.4)

        # 중심점
        for t_idx, t in enumerate(type_order):
            c = centroids[t]
            color = MBTI_COLORS.get(t, '#95A5A6')
            ax.scatter(c[xi], c[yi], s=120, c=color, marker='D',
                      edgecolors='black', linewidths=1.2, zorder=5)
            ax.annotate(t, (c[xi], c[yi]), fontsize=9, ha='center', va='bottom',
                       xytext=(0, 6), textcoords='offset points')

        # 설문 응답자 (확신도로 크기/투명도 조절)
        sizes = 15 + confidences * 50
        ax.scatter(survey_dims[:, xi], survey_dims[:, yi],
                  s=sizes, c='red', alpha=0.4, zorder=3, label='v2 설문 응답자')

        ax.set_xlabel(DIM_LABELS_KR[dx])
        ax.set_ylabel(DIM_LABELS_KR[dy])
        ax.set_title(f'{dx} vs {dy}')

    save_figure(fig, TEAM, 'fig_d7_centroid_prediction_scatter.png')

    # --- fig_d8: 예측 결과 요약 (3패널) ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f'최근접 중심 MBTI 예측 결과{tag}',
                 fontsize=22, fontweight='bold')

    # 왼쪽: 차원별 일치율 + 자기보고 대비
    ax = axes[0]
    dim_keys = ['EI', 'SN', 'TF', 'JP']
    dim_accs = [dim_accuracy[k] for k in dim_keys]
    # 자기보고 vs 설문산출 차원별 일치율 (참고용)
    self_dim_accs = []
    for dim_idx, dk in enumerate(dim_keys):
        if np.sum(valid_mask) > 0:
            self_dim = np.array([str(s)[dim_idx] for s in self_mbti[valid_mask]])
            pred_dim = np.array([t[dim_idx] for t in predicted_types[valid_mask]])
            self_dim_accs.append(np.mean(self_dim == pred_dim) * 100)
        else:
            self_dim_accs.append(0)

    x = np.arange(len(dim_keys))
    width = 0.35
    bars1 = ax.bar(x - width/2, dim_accs, width, label='산출 vs 중심분류', color='#3498DB', alpha=0.8)
    bars2 = ax.bar(x + width/2, self_dim_accs, width, label='자기보고 vs 중심분류', color='#F39C12', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(dim_keys, fontsize=14)
    ax.set_ylabel('일치율 (%)')
    ax.set_title(f'차원별 예측 일치율\n(전체: {accuracy:.1f}%)', fontsize=14)
    ax.set_ylim(0, 110)
    ax.legend(fontsize=11, loc='lower right')
    for bar, val in zip(bars1, dim_accs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
               f'{val:.0f}%', ha='center', fontsize=12, fontweight='bold')

    # 중앙: 예측 거리 히스토그램
    ax = axes[1]
    ax.hist(predicted_distances, bins=15, color='#3498DB', alpha=0.7, edgecolor='white')
    ax.axvline(np.mean(predicted_distances), color='red', linestyle='--',
               linewidth=2, label=f'평균: {np.mean(predicted_distances):.3f}')
    ax.set_xlabel('유클리드 거리')
    ax.set_ylabel('빈도')
    ax.set_title('중심점까지 거리 분포', fontsize=14)
    ax.legend(fontsize=13)

    # 오른쪽: 확신도 히스토그램
    ax = axes[2]
    ax.hist(confidences, bins=15, color='#2ECC71', alpha=0.7, edgecolor='white')
    ax.axvline(np.mean(confidences), color='red', linestyle='--',
               linewidth=2, label=f'평균: {np.mean(confidences):.3f}')
    ax.set_xlabel('확신도 (1 - d1/d2)')
    ax.set_ylabel('빈도')
    ax.set_title('예측 확신도 분포', fontsize=14)
    ax.legend(fontsize=13)

    save_figure(fig, TEAM, 'fig_d8_prediction_summary.png')

    return {
        'accuracy': accuracy,
        'dim_accuracy': dim_accuracy,
        'mean_distance': np.mean(predicted_distances),
        'centroids': centroids,
        'predicted_types': predicted_types,
    }


def analyze_logistic_prediction(data, prediction_result):
    """로지스틱 회귀 MBTI 예측 — Kaggle로 학습, 설문으로 테스트"""
    print("\n\n" + "━" * 60)
    print("  분석 5-2: 로지스틱 회귀 MBTI 예측")
    print("━" * 60)
    print("  방법: Kaggle 43,744명으로 차원별 로지스틱 회귀 학습 → 설문 응답자 예측")

    kaggle = data['kaggle']
    tag = ' [데모]' if data['is_demo'] else ''

    # 1. Kaggle 학습 데이터 준비
    X_train = np.column_stack([
        kaggle['introversion'],
        kaggle['sensing'],
        kaggle['thinking'],
        kaggle['judging'],
    ])

    # 2. 설문 테스트 데이터 준비
    X_test = np.column_stack([
        data['survey_scores']['EI'],
        data['survey_scores']['SN'],
        data['survey_scores']['TF'],
        data['survey_scores']['JP'],
    ])

    dim_keys = ['EI', 'SN', 'TF', 'JP']
    dim_high = {'EI': 'E', 'SN': 'S', 'TF': 'T', 'JP': 'J'}
    dim_low = {'EI': 'I', 'SN': 'N', 'TF': 'F', 'JP': 'P'}
    kaggle_types = kaggle['personality']

    # 3. 차원별 독립 이진 분류
    models = {}
    lr_dim_accs = {}
    lr_dim_preds = {}
    train_accs = {}
    all_weights = {}

    # 표준화 (학습 데이터 기준)
    X_train_std, tr_mean, tr_std = standardize_features(X_train)
    X_test_std, _, _ = standardize_features(X_test, mean=tr_mean, std=tr_std)

    for dk_idx, dk in enumerate(dim_keys):
        # 학습 레이블: Kaggle의 해당 차원 문자
        y_train = np.array([1 if t[dk_idx] == dim_high[dk] else 0
                           for t in kaggle_types])

        # 학습 (대규모 데이터이므로 epochs 줄이고 lr 낮춤)
        model = logistic_regression_train(
            X_train_std, y_train, lr=0.1, epochs=500, lambda_reg=0.001)

        # 예측
        pred = logistic_regression_predict(X_test_std, model['weights'])

        models[dk] = model
        all_weights[dk] = model['weights']
        train_accs[dk] = model['train_acc']

        # 예측된 문자
        pred_letters = np.where(pred['predictions'] == 1, dim_high[dk], dim_low[dk])
        lr_dim_preds[dk] = pred_letters

        print(f"\n  {DIM_LABELS_KR[dk]}:")
        print(f"    학습 정확도: {model['train_acc']*100:.1f}%")
        print(f"    학습 데이터 비율: {dk}={dim_high[dk]} {y_train.mean()*100:.1f}%")

    # 4. 전체 4글자 예측
    n_test = len(X_test)
    lr_predicted_types = np.array([
        ''.join([lr_dim_preds[dk][i] for dk in dim_keys])
        for i in range(n_test)
    ])

    # 5. 정확도 평가 (설문 산출 MBTI 대비)
    calc_types = data['survey_types']
    lr_accuracy = np.mean(lr_predicted_types == calc_types) * 100

    for dk_idx, dk in enumerate(dim_keys):
        pred_d = np.array([t[dk_idx] for t in lr_predicted_types])
        calc_d = np.array([t[dk_idx] for t in calc_types])
        lr_dim_accs[dk] = np.mean(pred_d == calc_d) * 100

    print(f"\n  [로지스틱 회귀 예측 결과 — 설문 산출 대비]")
    print(f"    전체 일치율: {lr_accuracy:.1f}%")
    for dk, da in lr_dim_accs.items():
        print(f"    {dk} 차원: {da:.1f}%")

    # 6. 자기보고 MBTI 대비 정확도
    self_mbti = data['self_mbti']
    valid_mask = np.array([len(str(s)) == 4 for s in self_mbti])

    if np.sum(valid_mask) > 0:
        lr_self_match = np.mean(lr_predicted_types[valid_mask] == self_mbti[valid_mask]) * 100
        self_dim_accs_lr = {}
        for dk_idx, dk in enumerate(dim_keys):
            self_d = np.array([str(s)[dk_idx] for s in self_mbti[valid_mask]])
            pred_d = np.array([t[dk_idx] for t in lr_predicted_types[valid_mask]])
            self_dim_accs_lr[dk] = np.mean(self_d == pred_d) * 100
    else:
        lr_self_match = 0.0
        self_dim_accs_lr = {dk: 0.0 for dk in dim_keys}

    print(f"    자기보고 vs 로지스틱 회귀: {lr_self_match:.1f}%")

    # 7. 기존 최근접 중심 결과 비교
    centroid_acc = prediction_result['accuracy']
    centroid_dim_accs = prediction_result['dim_accuracy']

    print(f"\n  [방법 비교]")
    print(f"    {'방법':<25} {'전체':>8} {'EI':>8} {'SN':>8} {'TF':>8} {'JP':>8}")
    print(f"    {'─'*65}")
    print(f"    {'임계값 (t=4.0)':<25} {'100.0':>7}% {'100.0':>7}% {'100.0':>7}% {'100.0':>7}% {'100.0':>7}%")
    print(f"    {'최근접 중심':<25} {centroid_acc:>7.1f}% {centroid_dim_accs['EI']:>7.1f}% "
          f"{centroid_dim_accs['SN']:>7.1f}% {centroid_dim_accs['TF']:>7.1f}% {centroid_dim_accs['JP']:>7.1f}%")
    print(f"    {'로지스틱 회귀':<25} {lr_accuracy:>7.1f}% {lr_dim_accs['EI']:>7.1f}% "
          f"{lr_dim_accs['SN']:>7.1f}% {lr_dim_accs['TF']:>7.1f}% {lr_dim_accs['JP']:>7.1f}%")

    # --- fig_d13: 로지스틱 회귀 vs 기존 방법 비교 ---
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'fig_d13: 로지스틱 회귀 MBTI 예측 (Kaggle→설문){tag}',
                 fontsize=24, fontweight='bold')

    # (1) 차원별 정확도 비교 (3가지 방법)
    ax = axes[0, 0]
    x = np.arange(len(dim_keys))
    width = 0.25

    # 임계값 기준 (산출 = 산출이므로 항상 100%)
    threshold_accs = [100.0] * 4
    centroid_accs = [centroid_dim_accs[dk] for dk in dim_keys]
    logistic_accs = [lr_dim_accs[dk] for dk in dim_keys]

    bars1 = ax.bar(x - width, threshold_accs, width, label='임계값 (t=4.0)',
                   color='#95a5a6', alpha=0.8, edgecolor='white')
    bars2 = ax.bar(x, centroid_accs, width, label='최근접 중심',
                   color='#3498DB', alpha=0.8, edgecolor='white')
    bars3 = ax.bar(x + width, logistic_accs, width, label='로지스틱 회귀',
                   color='#1abc9c', alpha=0.8, edgecolor='white')

    for bars in [bars2, bars3]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{bar.get_height():.1f}%', ha='center', fontsize=16,
                   fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(dim_keys, fontsize=18)
    ax.set_ylabel('정확도 (%)', fontsize=18)
    ax.set_title('차원별 정확도 (설문 산출 MBTI 기준)', fontsize=18, fontweight='bold')
    ax.legend(fontsize=16)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', alpha=0.3)

    # (2) 전체 4글자 비교 + 자기보고 대비
    ax = axes[0, 1]
    methods = ['임계값\n(t=4.0)', '최근접\n중심', '로지스틱\n회귀']
    calc_accs = [100.0, centroid_acc, lr_accuracy]
    self_accs = [0, prediction_result.get('self_pred_match', 0), lr_self_match]

    # 자기보고 일치율도 함께 표시
    x2 = np.arange(len(methods))
    w2 = 0.35

    bars_calc = ax.bar(x2 - w2/2, calc_accs, w2, label='산출 MBTI 대비',
                       color=['#95a5a6', '#3498DB', '#1abc9c'], edgecolor='white')
    bars_self = ax.bar(x2 + w2/2, self_accs, w2, label='자기보고 대비',
                       color=['#95a5a6', '#3498DB', '#1abc9c'], alpha=0.4,
                       edgecolor='white', hatch='///')

    for bar in list(bars_calc) + list(bars_self):
        val = bar.get_height()
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 0.5,
                   f'{val:.1f}%', ha='center', fontsize=16, fontweight='bold')

    ax.set_xticks(x2)
    ax.set_xticklabels(methods, fontsize=17)
    ax.set_ylabel('전체 4글자 일치율 (%)', fontsize=18)
    ax.set_title('전체 예측 정확도 비교', fontsize=18, fontweight='bold')
    ax.legend(fontsize=16)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', alpha=0.3)

    # (3) 로지스틱 회귀 계수 시각화
    ax = axes[1, 0]
    weight_matrix = np.zeros((4, 4))
    for row, dk in enumerate(dim_keys):
        w = all_weights[dk]
        weight_matrix[row] = w[1:]  # bias 제외, 4개 특성만

    im = ax.imshow(weight_matrix, cmap='RdBu_r', aspect='auto',
                   vmin=-np.abs(weight_matrix).max(),
                   vmax=np.abs(weight_matrix).max())

    ax.set_yticks(range(4))
    ax.set_yticklabels([f'{dk} 분류' for dk in dim_keys], fontsize=17)
    ax.set_xticks(range(4))
    ax.set_xticklabels(['EI 점수', 'SN 점수', 'TF 점수', 'JP 점수'], fontsize=16)
    ax.set_title('로지스틱 회귀 계수 (4차원 x 4특성)', fontsize=18, fontweight='bold')

    for i in range(4):
        for j in range(4):
            val = weight_matrix[i, j]
            color = 'white' if abs(val) > np.abs(weight_matrix).max() * 0.5 else 'black'
            ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                   fontsize=18, color=color, fontweight='bold')

    plt.colorbar(im, ax=ax, shrink=0.8, label='계수 값')

    # (4) 모형 요약 텍스트
    ax = axes[1, 1]
    ax.axis('off')

    ax.text(0.5, 0.95, '모형 요약 및 해석', ha='center', fontsize=24,
            fontweight='bold', color='#1abc9c', transform=ax.transAxes)

    rect = mpatches.FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.88, boxstyle='round,pad=0.02',
        facecolor='#e8f8f5', edgecolor='#1abc9c',
        linewidth=2, transform=ax.transAxes)
    ax.add_patch(rect)

    improvement_vs_centroid = lr_accuracy - centroid_acc

    summary_lines = [
        f'학습 데이터: Kaggle N=43,744',
        f'테스트 데이터: 설문 N={n_test}',
        f'모형: 로지스틱 회귀 (L2, lambda=0.001)',
        f'',
        f'최근접 중심 전체: {centroid_acc:.1f}%',
        f'로지스틱 회귀 전체: {lr_accuracy:.1f}%',
        f'차이: {improvement_vs_centroid:+.1f}%p',
        f'',
        f'자기보고 vs 로지스틱: {lr_self_match:.1f}%',
        f'',
        f'해석: 로지스틱 회귀는 차원 간 교차정보를',
        f'활용하여 더 정교한 분류 경계를 형성합니다.',
        f'대각선 계수가 크면 해당 차원 점수가',
        f'그 차원 분류에 가장 중요합니다.',
    ]

    y = 0.84
    for line in summary_lines:
        if line == '':
            y -= 0.02
            continue
        ax.text(0.06, y, line, fontsize=18, color='#333',
               transform=ax.transAxes)
        y -= 0.055

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    save_figure(fig, TEAM, 'fig_d13_logistic_prediction.png')

    return {
        'accuracy': lr_accuracy,
        'dim_accuracy': lr_dim_accs,
        'self_match': lr_self_match,
        'self_dim_accs': self_dim_accs_lr,
        'weights': all_weights,
        'train_accs': train_accs,
        'X_train': X_train,
        'X_train_std': X_train_std,
        'X_test': X_test,
        'X_test_std': X_test_std,
        'models': models,
        'tr_mean': tr_mean,
        'tr_std': tr_std,
    }


def analyze_logistic_diagnostics(data, logistic_pred):
    """fig_d14: 로지스틱 회귀 모형 진단 — VIF, AIC/BIC, McFadden R², 분류 성능"""
    print("\n\n" + "━" * 60)
    print("  분석 5-3: 로지스틱 회귀 모형 진단")
    print("━" * 60)

    tag = ' [데모]' if data['is_demo'] else ''
    kaggle = data['kaggle']
    dim_keys = ['EI', 'SN', 'TF', 'JP']
    dim_high = {'EI': 'E', 'SN': 'S', 'TF': 'T', 'JP': 'J'}
    kaggle_types = kaggle['personality']
    feature_names = ['EI 점수', 'SN 점수', 'TF 점수', 'JP 점수']

    X_train = logistic_pred['X_train']
    X_train_std = logistic_pred['X_train_std']
    models = logistic_pred['models']

    # 각 차원별 진단 수행
    diagnostics = {}
    for dk_idx, dk in enumerate(dim_keys):
        y_train = np.array([1 if t[dk_idx] == dim_high[dk] else 0
                           for t in kaggle_types])
        diag = logistic_regression_diagnostics(
            X_train_std, y_train, models[dk]['weights'],
            feature_names=feature_names,
            X_raw=X_train
        )
        diagnostics[dk] = diag
        print(f"\n  [{dk} 차원]")
        print(f"    VIF: {', '.join([f'{v:.2f}' for v in diag['vif']])}")
        print(f"    AIC: {diag['aic_bic']['aic']:.1f}, BIC: {diag['aic_bic']['bic']:.1f}")
        print(f"    McFadden R²: {diag['mcfadden']['mcfadden_r2']:.4f}")
        print(f"    F1: {diag['classification']['f1']:.3f}")

    # --- fig_d14: 로지스틱 회귀 모형 진단 ---
    fig = plt.figure(figsize=(24, 18))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.97, f'fig_d14: 로지스틱 회귀 모형 진단 (Regression Diagnostics){tag}',
             ha='center', fontsize=26, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.945, f'Kaggle N=43,744 학습 | 4차원 독립 이진 분류 | '
             f'다중공선성 · AIC/BIC · McFadden R² · 분류 성능',
             ha='center', fontsize=19, color='#7f8c8d')

    dim_labels = [DIM_LABELS_KR[dk] for dk in dim_keys]

    # ── 패널 1: VIF (다중공선성) ──
    ax1 = fig.add_axes([0.06, 0.54, 0.42, 0.36])

    x_feats = np.arange(4)
    width = 0.18
    colors_dim = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']

    for idx, dk in enumerate(dim_keys):
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
    ax1.set_title('1. 다중공선성 진단 (VIF) — 모든 차원 동일', fontsize=19, fontweight='bold')
    ax1.legend(fontsize=16, loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    max_vif = max(max(diagnostics[dk]['vif']) for dk in dim_keys)
    ax1.set_ylim(0, max(max_vif * 1.5, 6))

    # ── 패널 2: AIC / BIC 비교 ──
    ax2 = fig.add_axes([0.55, 0.54, 0.42, 0.36])

    aic_vals = [diagnostics[dk]['aic_bic']['aic'] for dk in dim_keys]
    bic_vals = [diagnostics[dk]['aic_bic']['bic'] for dk in dim_keys]
    ll_vals = [diagnostics[dk]['aic_bic']['log_likelihood'] for dk in dim_keys]

    x_d = np.arange(4)
    w = 0.3
    bars_a = ax2.bar(x_d - w/2, aic_vals, w, label='AIC', color='#3498db',
                     edgecolor='white', linewidth=1.5)
    bars_b = ax2.bar(x_d + w/2, bic_vals, w, label='BIC', color='#e74c3c',
                     edgecolor='white', linewidth=1.5)

    for bar in bars_a:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{bar.get_height():.0f}', ha='center', fontsize=17,
                fontweight='bold', color='#3498db')
    for bar in bars_b:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{bar.get_height():.0f}', ha='center', fontsize=17,
                fontweight='bold', color='#e74c3c')

    ax2.set_xticks(x_d)
    ax2.set_xticklabels(dim_labels, fontsize=18)
    ax2.set_ylabel('정보 기준 값', fontsize=18, fontweight='bold')
    ax2.set_title('2. 모형 적합도: AIC / BIC', fontsize=19, fontweight='bold')
    ax2.legend(fontsize=17)
    ax2.grid(axis='y', alpha=0.3)

    # ── 패널 3: McFadden R² + 분류 성능 ──
    ax3 = fig.add_axes([0.06, 0.07, 0.42, 0.36])

    r2_vals = [diagnostics[dk]['mcfadden']['mcfadden_r2'] for dk in dim_keys]
    acc_vals = [diagnostics[dk]['classification']['accuracy'] for dk in dim_keys]
    f1_vals = [diagnostics[dk]['classification']['f1'] for dk in dim_keys]
    prec_vals = [diagnostics[dk]['classification']['precision'] for dk in dim_keys]
    recall_vals = [diagnostics[dk]['classification']['recall'] for dk in dim_keys]

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
    for dk in dim_keys:
        mv = np.mean(diagnostics[dk]['vif'])
        s = '양호' if mv < 5 else '주의' if mv < 10 else '심각'
        vif_row.append(f'{mv:.2f} ({s})')
    table_data.append(vif_row)

    table_data.append(['AIC'] + [f'{diagnostics[dk]["aic_bic"]["aic"]:.0f}' for dk in dim_keys])
    table_data.append(['BIC'] + [f'{diagnostics[dk]["aic_bic"]["bic"]:.0f}' for dk in dim_keys])
    table_data.append(['Log-Likelihood'] +
                      [f'{diagnostics[dk]["aic_bic"]["log_likelihood"]:.0f}' for dk in dim_keys])

    r2_row = ['McFadden R²']
    for dk in dim_keys:
        r2 = diagnostics[dk]['mcfadden']['mcfadden_r2']
        q = '우수' if r2 > 0.4 else '양호' if r2 > 0.2 else '미흡'
        r2_row.append(f'{r2:.4f} ({q})')
    table_data.append(r2_row)

    table_data.append(['조건수'] +
                      [f'{diagnostics[dk]["condition_number"]:.1f}' for dk in dim_keys])
    table_data.append(['Accuracy'] +
                      [f'{diagnostics[dk]["classification"]["accuracy"]:.1%}' for dk in dim_keys])
    table_data.append(['F1-score'] +
                      [f'{diagnostics[dk]["classification"]["f1"]:.3f}' for dk in dim_keys])
    table_data.append(['Precision'] +
                      [f'{diagnostics[dk]["classification"]["precision"]:.3f}' for dk in dim_keys])
    table_data.append(['Recall'] +
                      [f'{diagnostics[dk]["classification"]["recall"]:.3f}' for dk in dim_keys])

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
                dk = dim_keys[j-1]
                mv = np.mean(diagnostics[dk]['vif'])
                cell.set_facecolor('#d5f5e3' if mv < 5 else '#fdebd0' if mv < 10 else '#fadbd8')
            elif i == 4:
                dk = dim_keys[j-1]
                r2 = diagnostics[dk]['mcfadden']['mcfadden_r2']
                cell.set_facecolor('#d5f5e3' if r2 > 0.4 else '#d4efdf' if r2 > 0.2 else '#fdebd0')

    save_figure(fig, TEAM, 'fig_d14_logistic_diagnostics.png')

    return diagnostics


# ============================================================
#  분석 6: 혈액형 × 설문 MBTI 교차분석
# ============================================================

def analyze_blood_mbti(data):
    """v2 설문 데이터의 혈액형별 MBTI 차원 점수 ANOVA"""
    print("\n\n" + "━" * 60)
    print("  분석 6: 혈액형 × v2 설문 MBTI 차원 점수")
    print("━" * 60)
    print("  H0: 혈액형에 따른 MBTI 차원 점수 차이는 없다")

    tag = ' [데모]' if data['is_demo'] else ''
    blood = data['blood_types']
    # '모름' 제외
    valid_blood_mask = blood != '모름'
    blood_labels_all = np.unique(blood[valid_blood_mask])
    # 정렬: A형, B형, O형, AB형
    blood_order = ['A형', 'B형', 'O형', 'AB형']
    blood_labels = [b for b in blood_order if b in blood_labels_all]

    anova_results = {}

    # --- fig_d9: 혈액형별 차원 점수 boxplot + jitter ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'혈액형별 MBTI 차원 점수 비교 (v2 설문){tag}',
                 fontsize=24, fontweight='bold')

    rng = np.random.RandomState(42)  # jitter 재현성

    for idx, dim_key in enumerate(['EI', 'SN', 'TF', 'JP']):
        ax = axes[idx // 2, idx % 2]
        scores = data['survey_scores'][dim_key]

        groups = []
        group_labels = []
        group_ns = []
        for bt in blood_labels:
            mask = blood == bt
            n_bt = np.sum(mask)
            if n_bt >= 2:
                groups.append(scores[mask])
                group_labels.append(bt)
                group_ns.append(n_bt)
            else:
                print(f"    [경고] {bt}: n={n_bt} (<2) → ANOVA에서 제외")

        if len(groups) >= 2:
            result = one_way_anova(*groups)
            anova_results[dim_key] = result
            print_test_result(f"ANOVA: {DIM_LABELS_KR[dim_key]} x 혈액형", result)

            eta2 = result.get('eta_squared', 0)
            sig = '*' if result['p_value'] < 0.05 else 'ns'
            eta_str = f'eta2={eta2:.4f}'
        else:
            sig = '-'
            eta_str = ''

        # boxplot
        positions = list(range(len(group_labels)))
        bp = ax.boxplot([g for g in groups], positions=positions,
                       widths=0.5, patch_artist=True, zorder=2)
        for patch, bl in zip(bp['boxes'], group_labels):
            color = BLOOD_COLORS.get(bl.replace('형', ''), '#95A5A6')
            patch.set_facecolor(color)
            patch.set_alpha(0.5)

        # jitter scatter overlay (개별 데이터 포인트)
        for i, g in enumerate(groups):
            jitter = rng.normal(0, 0.08, size=len(g))
            ax.scatter(i + jitter, g, s=25, alpha=0.6,
                      color=BLOOD_COLORS.get(group_labels[i].replace('형', ''), '#95A5A6'),
                      edgecolors='gray', linewidths=0.3, zorder=3)

        # x축 라벨에 N 포함
        ax.set_xticks(positions)
        ax.set_xticklabels([f'{bl}\n(n={n})' for bl, n in zip(group_labels, group_ns)],
                           fontsize=13)
        ax.set_ylabel('점수')
        ax.set_title(f'{DIM_LABELS_KR[dim_key]} [{sig}] {eta_str}', fontsize=14)
        ax.axhline(y=MIDPOINT, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)

        # 평균 다이아몬드
        for i, g in enumerate(groups):
            ax.scatter(i, np.mean(g), marker='D', color='black', s=50, zorder=5)

    save_figure(fig, TEAM, 'fig_d9_blood_mbti_boxplot.png')

    return anova_results


# ============================================================
#  분석 7: MBTI 밈 인식 (v2 보너스 문항 분석)
# ============================================================

def analyze_meme_perception(data):
    """v2 보너스 문항(Q42-Q46) 밈 인식 분석"""
    print("\n\n" + "━" * 60)
    print("  분석 7: MBTI 밈 인식 분석 (보너스 문항)")
    print("━" * 60)
    print("  H5: MBTI 밈 인식(신뢰도)은 차원 점수와 관련이 있다")

    bonus = data['bonus']
    tag = ' [데모]' if data['is_demo'] else ''

    # --- fig_d10: 밈 인식 분석 (2×2) ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'MBTI & 혈액형 밈 인식 분석{tag}',
                 fontsize=24, fontweight='bold')

    # (1) MBTI 신뢰도 분포
    ax = axes[0, 0]
    trust_vals = bonus['mbti_trust']
    trust_vals_valid = trust_vals[(trust_vals >= 1) & (trust_vals <= 7)]
    ax.hist(trust_vals_valid, bins=np.arange(0.5, 8.5, 1), color='#3498DB',
            alpha=0.7, edgecolor='white', rwidth=0.8)
    ax.axvline(np.mean(trust_vals_valid), color='red', linestyle='--', linewidth=2,
               label=f'평균: {np.mean(trust_vals_valid):.2f}')
    ax.set_xlabel('신뢰도 (1=밈 / 7=정확)')
    ax.set_ylabel('빈도')
    ax.set_title('Q42: MBTI 신뢰도')
    ax.legend(fontsize=13)
    ax.set_xticks(range(1, 8))

    # (2) 혈액형 신뢰도 분포
    ax = axes[0, 1]
    blood_trust = bonus['blood_trust']
    blood_trust_valid = blood_trust[(blood_trust >= 1) & (blood_trust <= 7)]
    ax.hist(blood_trust_valid, bins=np.arange(0.5, 8.5, 1), color='#E74C3C',
            alpha=0.7, edgecolor='white', rwidth=0.8)
    ax.axvline(np.mean(blood_trust_valid), color='red', linestyle='--', linewidth=2,
               label=f'평균: {np.mean(blood_trust_valid):.2f}')
    ax.set_xlabel('신뢰도 (1=근거없음 / 7=맞다고봄)')
    ax.set_ylabel('빈도')
    ax.set_title('Q43: 혈액형 성격론 신뢰도')
    ax.legend(fontsize=13)
    ax.set_xticks(range(1, 8))

    # (3) "너 T야?" 사용 빈도
    ax = axes[1, 0]
    t_vals, t_counts = np.unique(bonus['are_you_t'], return_counts=True)
    sort_idx = np.argsort(-t_counts)
    # 라벨 축약
    short_t = []
    for v in t_vals[sort_idx]:
        if '자주' in v:
            short_t.append('자주 쓴다')
        elif '가끔' in v:
            short_t.append('가끔 쓴다')
        elif '안 써봄' in v:
            short_t.append('들어만 봄')
        else:
            short_t.append('처음 들어봄')
    ax.barh(short_t[::-1], t_counts[sort_idx][::-1],
            color='#F39C12', alpha=0.7)
    ax.set_title('Q44: "너 T야?" 사용 빈도')
    ax.set_xlabel('인원수')

    # (4) 최종 생각
    ax = axes[1, 1]
    op_vals, op_counts = np.unique(bonus['final_opinion'], return_counts=True)
    sort_idx = np.argsort(-op_counts)
    # 라벨 축약
    short_op = []
    for v in op_vals[sort_idx]:
        if '과학적 근거' in v:
            short_op.append('과학적')
        elif '꽤 맞는' in v:
            short_op.append('꽤 맞음')
        elif '재미로' in v:
            short_op.append('재미로만')
        elif '미신' in v:
            short_op.append('미신')
        else:
            short_op.append('모르겠다')
    ax.barh(short_op[::-1], op_counts[sort_idx][::-1],
            color='#2ECC71', alpha=0.7)
    ax.set_title('Q46: MBTI/혈액형 최종 생각')
    ax.set_xlabel('인원수')

    save_figure(fig, TEAM, 'fig_d10_meme_perception.png')

    # 상관분석: MBTI 신뢰도 × 차원 점수
    meme_corr = {}
    print(f"\n  [상관분석] MBTI 신뢰도(Q42) × 차원 점수")
    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        scores = data['survey_scores'][dim_key]
        n_min = min(len(trust_vals_valid), len(scores))
        corr = pearson_correlation(trust_vals_valid[:n_min], scores[:n_min])
        meme_corr[dim_key] = corr
        sig = '*' if corr['p_value'] < 0.05 else 'ns'
        print(f"    {dim_key}: r={corr['r']:.3f}, p={corr['p_value']:.4f} [{sig}]")

    # 대응표본 비교: MBTI 신뢰도 vs 혈액형 신뢰도
    n_paired = min(len(trust_vals_valid), len(blood_trust_valid))
    paired_diff = trust_vals_valid[:n_paired] - blood_trust_valid[:n_paired]
    paired_mean = np.mean(paired_diff)
    paired_sd = np.std(paired_diff, ddof=1)
    if paired_sd > 0 and n_paired > 1:
        paired_t = paired_mean / (paired_sd / np.sqrt(n_paired))
        # p-value 근사 (양측)
        from common.stats_utils import norm_cdf
        paired_p = 2 * (1 - norm_cdf(abs(paired_t)))
        paired_d = paired_mean / paired_sd
    else:
        paired_t, paired_p, paired_d = 0, 1, 0

    print(f"\n  [대응표본 비교] MBTI 신뢰도 vs 혈액형 신뢰도")
    print(f"    MBTI 평균: {np.mean(trust_vals_valid):.2f} (SD={np.std(trust_vals_valid):.2f})")
    print(f"    혈액형 평균: {np.mean(blood_trust_valid):.2f} (SD={np.std(blood_trust_valid):.2f})")
    print(f"    차이: {paired_mean:.2f}, t={paired_t:.3f}, p={paired_p:.4f}, d={paired_d:.3f}")

    # 신뢰도 간 상관
    trust_corr = pearson_correlation(trust_vals_valid[:n_paired], blood_trust_valid[:n_paired])
    print(f"    MBTI-혈액형 신뢰도 상관: r={trust_corr['r']:.3f}, p={trust_corr['p_value']:.4f}")

    return {
        'mbti_trust_mean': float(np.mean(trust_vals_valid)),
        'blood_trust_mean': float(np.mean(blood_trust_valid)),
        'meme_corr': meme_corr,
        'paired_t': paired_t,
        'paired_p': paired_p,
        'paired_d': paired_d,
        'trust_corr': trust_corr,
    }


# ============================================================
#  분석 8: 효과크기 Forest Plot
# ============================================================

def analyze_effect_size_forest(comparison, anova_blood, prediction, meme_result, agreement=None):
    """모든 검정의 효과크기를 Forest Plot으로 종합"""
    print("\n\n" + "━" * 60)
    print("  분석 8: 효과크기 종합 Forest Plot")
    print("━" * 60)

    # 효과크기 수집
    effects = []

    # 0. 일치도 kappa (H1)
    if agreement and 'kappa' in agreement:
        effects.append({
            'label': 'H1: 자기보고 일치도 (kappa)',
            'value': abs(agreement['kappa']),
            'type': 'kappa',
            'sig': agreement['kappa'] > 0.40,  # "보통" 이상이면 유의미
            'category': 'H1',
        })

    # 1. 설문 vs Kaggle 차원 비교 (Cohen's d)
    if comparison:
        for dk, cr in comparison.items():
            if dk == 'regression':
                continue
            effects.append({
                'label': f'H2: {dk} 설문 vs Kaggle',
                'value': abs(cr.get('d', 0)),
                'type': "Cohen's d",
                'sig': cr.get('p', 1) < 0.05,
                'category': 'H2',
            })

    # 2. 예측 정확도 (H3) — 차원별 정확도를 비율로 표현
    if prediction and 'dim_accuracy' in prediction:
        pred_acc = prediction.get('accuracy', 0) / 100
        effects.append({
            'label': f'H3: 중심분류 정확도',
            'value': pred_acc,
            'type': 'accuracy',
            'sig': pred_acc > 0.5,  # 50% 이상이면 의미
            'category': 'H3',
        })

    # 3. 혈액형 ANOVA (eta²)
    if anova_blood:
        for dk, r in anova_blood.items():
            effects.append({
                'label': f'H4: {dk} 혈액형 ANOVA',
                'value': r.get('eta_squared', 0),
                'type': 'eta2',
                'sig': r.get('p_value', 1) < 0.05,
                'category': 'H4',
            })

    # 4. 밈 인식 상관 (|r|)
    if meme_result and 'meme_corr' in meme_result:
        for dk, corr in meme_result['meme_corr'].items():
            effects.append({
                'label': f'H5: {dk} 밈 신뢰도 상관',
                'value': abs(corr.get('r', 0)),
                'type': '|r|',
                'sig': corr.get('p_value', 1) < 0.05,
                'category': 'H5',
            })

    # 5. MBTI vs 혈액형 신뢰도 차이 (paired d)
    if meme_result and 'paired_d' in meme_result:
        effects.append({
            'label': 'H5: MBTI-혈액형 신뢰도 차이',
            'value': abs(meme_result['paired_d']),
            'type': "Cohen's d",
            'sig': meme_result.get('paired_p', 1) < 0.05,
            'category': 'H5',
        })

    if not effects:
        print("  [경고] 수집된 효과크기 없음")
        return

    # --- fig_d11: Forest Plot ---
    fig, ax = plt.subplots(figsize=(14, max(7, len(effects) * 0.5 + 2)))

    labels = [e['label'] for e in effects]
    values = [e['value'] for e in effects]
    sigs = [e['sig'] for e in effects]
    types = [e['type'] for e in effects]
    categories = [e.get('category', '') for e in effects]

    y_pos = np.arange(len(effects))

    # 카테고리별 배경색
    cat_colors = {'H1': '#E8F8F5', 'H2': '#EBF5FB', 'H3': '#F4ECF7',
                  'H4': '#FEF9E7', 'H5': '#FDEDEC'}
    for i, cat in enumerate(categories):
        bg_color = cat_colors.get(cat, '#FFFFFF')
        ax.axhspan(i - 0.4, i + 0.4, color=bg_color, alpha=0.5, zorder=0)

    for i, (val, sig, etype) in enumerate(zip(values, sigs, types)):
        color = '#E74C3C' if sig else '#95A5A6'
        ax.scatter(val, i, s=120, c=color, marker='D' if sig else 'o',
                  zorder=5, edgecolors='black', linewidths=0.5)
        ax.text(val + 0.02, i, f'{val:.3f} ({etype})', va='center', fontsize=12)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=13)
    ax.set_xlabel('효과크기', fontsize=16)
    ax.set_title('효과크기 종합 Forest Plot (가설별)', fontsize=22, fontweight='bold')

    # 기준선 (Cohen's d 기준)
    max_val = max(values) if values else 1
    ax.axvline(x=0.2, color='green', linestyle=':', alpha=0.5, linewidth=1.5)
    ax.axvline(x=0.5, color='orange', linestyle=':', alpha=0.5, linewidth=1.5)
    if max_val > 0.7:
        ax.axvline(x=0.8, color='red', linestyle=':', alpha=0.5, linewidth=1.5)

    ax.text(0.2, -0.8, '작은', fontsize=11, color='green', ha='center')
    ax.text(0.5, -0.8, '보통', fontsize=11, color='orange', ha='center')
    if max_val > 0.7:
        ax.text(0.8, -0.8, '큰', fontsize=11, color='red', ha='center')

    # 범례
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='D', color='#E74C3C', label='유의/의미있음',
               markersize=10, linestyle='None'),
        Line2D([0], [0], marker='o', color='#95A5A6', label='비유의/미미함',
               markersize=10, linestyle='None'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=13)

    ax.set_xlim(-0.05, max_val + 0.3)
    ax.invert_yaxis()

    save_figure(fig, TEAM, 'fig_d11_effect_size_forest.png')

    # 출력
    for e in effects:
        sig_str = '[O]' if e['sig'] else '[X]'
        print(f"  {e['label']}: {e['value']:.4f} ({e['type']}) {sig_str}")


# ============================================================
#  분석 9: 종합 결론 인포그래픽
# ============================================================

def create_conclusion_infographic(data, agreement, comparison, prediction,
                                  anova_blood, meme_result):
    """종합 결론 대시보드"""
    print("\n\n" + "━" * 60)
    print("  분석 9: 종합 결론 인포그래픽")
    print("━" * 60)

    tag = ' [데모]' if data['is_demo'] else ''

    # 가설별 판정
    h1_judge = '[O]' if agreement.get('match_rate', 0) > 50 else '[X]'
    h1_kappa = agreement.get('kappa', 0)
    h1_kappa_judge = '[O]' if h1_kappa > 0.40 else '[X]'

    h2_sigs = sum(1 for dk, cr in comparison.items() if dk != 'regression' and cr.get('p', 1) < 0.05) if comparison else 0
    h2_total = sum(1 for dk in comparison if dk != 'regression') if comparison else 0
    h2_judge = '[O]' if h2_sigs > 0 else '[X]'

    h3_acc = prediction.get('accuracy', 0)
    h3_judge = '[O]' if h3_acc > 50 else '[X]'

    h4_sigs = sum(1 for r in anova_blood.values() if r.get('p_value', 1) < 0.05) if anova_blood else 0
    h4_judge = '[O]' if h4_sigs == 0 else '[X]'  # H4는 "차이 없음"이 기대

    h5_mbti = meme_result.get('mbti_trust_mean', 0) if meme_result else 0
    h5_blood = meme_result.get('blood_trust_mean', 0) if meme_result else 0
    h5_judge = '[O]' if h5_mbti > h5_blood else '[X]'

    fig = plt.figure(figsize=(42, 18))
    fig.suptitle(f'팀원 D 분석 종합: MBTI 밈 설문 v2 비교분석{tag}',
                 fontsize=34, fontweight='bold', y=0.97)

    # 6-패널 레이아웃 (2×3, 가로 배치)
    panels = [
        (0.02, 0.52, 0.30, 0.35),
        (0.35, 0.52, 0.30, 0.35),
        (0.68, 0.52, 0.30, 0.35),
        (0.02, 0.12, 0.30, 0.35),
        (0.35, 0.12, 0.30, 0.35),
        (0.68, 0.12, 0.30, 0.35),
    ]

    panel_data = [
        {
            'title': f'1. v2 밈 설문 개요',
            'content': (f"총 응답자: {data['n_survey']}명\n"
                       f"데이터: {'데모' if data['is_demo'] else '실제 설문'}\n"
                       f"도구: 밈 기반 36문항 리커트\n"
                       f"분석: 5개 가설 검증"),
            'color': '#3498DB',
        },
        {
            'title': f'2. H1 자기보고 일치율 {h1_judge}',
            'content': (f"전체: {agreement.get('match_rate', 0):.1f}%\n"
                       f"kappa: {h1_kappa:.3f} {h1_kappa_judge}\n"
                       f"EI: {agreement.get('dim_matches', {}).get('EI', 0):.0f}%  "
                       f"SN: {agreement.get('dim_matches', {}).get('SN', 0):.0f}%\n"
                       f"TF: {agreement.get('dim_matches', {}).get('TF', 0):.0f}%  "
                       f"JP: {agreement.get('dim_matches', {}).get('JP', 0):.0f}%"),
            'color': '#2ECC71',
        },
        {
            'title': f'3. H2 Kaggle 비교 {h2_judge}',
            'content': ('\n'.join([
                f"{dk}: d={cr.get('d', 0):.3f} "
                f"({'유의' if cr.get('p', 1) < 0.05 else 'ns'})"
                for dk, cr in comparison.items() if dk != 'regression'
            ]) + f'\n유의차원: {h2_sigs}/{h2_total}') if comparison else 'N/A',
            'color': '#E74C3C',
        },
        {
            'title': f'4. H3 MBTI 예측 {h3_judge}',
            'content': (f"전체 정확도: {h3_acc:.1f}%\n"
                       f"평균 거리: {prediction.get('mean_distance', 0):.3f}\n"
                       f"방법: 최근접 중심 분류기"),
            'color': '#9B59B6',
        },
        {
            'title': f'5. H4 혈액형 x MBTI {h4_judge}',
            'content': ('\n'.join([
                f"{dk}: F={r.get('f_stat', 0):.2f}, "
                f"eta2={r.get('eta_squared', 0):.4f} "
                f"({'유의' if r.get('p_value', 1) < 0.05 else 'ns'})"
                for dk, r in anova_blood.items()
            ]) + f'\n유의차원: {h4_sigs}/{len(anova_blood)}') if anova_blood else '분석 데이터 부족',
            'color': '#F39C12',
        },
        {
            'title': f'6. H5 밈 인식 {h5_judge}',
            'content': (f"MBTI 신뢰도: {h5_mbti:.1f}/7\n"
                       f"혈액형 신뢰도: {h5_blood:.1f}/7\n"
                       f"차이: d={meme_result.get('paired_d', 0):.3f}\n"
                       f"MBTI > 혈액형: {'예' if h5_mbti > h5_blood else '아니오'}"),
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
        ax.axhline(y=0.85, xmin=0.05, xmax=0.95, color=pd_item['color'], linewidth=3)
        ax.text(0.5, 0.9, pd_item['title'], ha='center', va='bottom',
               fontsize=24, fontweight='bold', color=pd_item['color'])
        ax.text(0.08, 0.4, pd_item['content'], ha='left', va='center',
               fontsize=24, color='#2C3E50', linespacing=1.5)

    # 하단 요약 테이블
    ax_summary = fig.add_axes([0.05, 0.01, 0.90, 0.09])
    ax_summary.set_xlim(0, 1)
    ax_summary.set_ylim(0, 1)
    ax_summary.set_axis_off()

    summary_text = (
        f"[가설 검정 요약]  "
        f"H1 일치율:{h1_judge}  "
        f"H2 Kaggle비교:{h2_judge}  "
        f"H3 예측:{h3_judge}  "
        f"H4 혈액형무관:{h4_judge}  "
        f"H5 밈인식:{h5_judge}"
    )
    ax_summary.text(0.5, 0.5, summary_text, ha='center', va='center',
                    fontsize=24, fontweight='bold', color='#2C3E50',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#F8F9F9',
                             edgecolor='#2C3E50', linewidth=2))

    save_figure(fig, TEAM, 'fig_d12_conclusion_infographic.png', tight=False)


# ============================================================
#  결과 요약
# ============================================================

def create_summary(data, agreement, comparison, prediction, anova_blood, meme_result):
    """최종 결론 출력"""
    print("\n\n" + "=" * 60)
    print("  팀원 D: 분석 결과 종합 요약")
    print("=" * 60)

    tag = ' [데모 데이터]' if data['is_demo'] else ' [실제 설문 데이터]'
    print(f"\n  데이터: v2 밈 설문 {data['n_survey']}명{tag}")

    print(f"\n[가설 1] 자기보고 vs v2 설문산출 MBTI 일치도")
    if agreement:
        print(f"  -> 전체 일치율: {agreement.get('match_rate', 0):.1f}%")
        print(f"  -> Cohen's kappa: {agreement.get('kappa', 0):.3f} "
              f"({agreement.get('kappa_interp', 'N/A')})")
        for dk, dv in agreement.get('dim_matches', {}).items():
            kv = agreement.get('dim_kappas', {}).get(dk, 0)
            print(f"    {dk}: 일치율={dv:.1f}%, kappa={kv:.3f}")
        print(f"  -> 유효 응답: {agreement.get('n_valid', 0)}명 "
              f"(모름/미응답 {agreement.get('n_unknown', 0)}명 제외)")
    else:
        print("  -> 유효한 자기보고 부족")

    print(f"\n[가설 2] v2 설문 vs Kaggle 차원 점수 비교")
    if comparison:
        for dk, cr in comparison.items():
            if dk == 'regression':
                continue
            sig = 'sig' if cr.get('p', 1) < 0.05 else 'ns'
            d_abs = abs(cr.get('d', 0))
            d_interp = ('큰' if d_abs >= 0.8 else '보통' if d_abs >= 0.5
                       else '작은' if d_abs >= 0.2 else '무시')
            print(f"  -> {dk}: 설문 {cr.get('survey_mean', 0):.2f} vs "
                  f"Kaggle {cr.get('kaggle_mean', 0):.2f}, "
                  f"d={cr.get('d', 0):.3f} ({d_interp}) [{sig}]")
        # 회귀분석 요약
        if 'regression' in comparison:
            reg = comparison['regression']
            print(f"  -> [회귀] 4차원 명확도→일치 예측: R²={reg['multiple_r_squared']:.4f}, "
                  f"adj_R²={reg['adj_r_squared']:.4f}")

    print(f"\n[가설 3] MBTI 예측 (최근접 중심 분류기)")
    if prediction:
        print(f"  -> 전체 정확도: {prediction['accuracy']:.1f}%")
        for dk, da in prediction.get('dim_accuracy', {}).items():
            print(f"    {dk} 차원: {da:.1f}%")
        print(f"  -> 평균 거리: {prediction.get('mean_distance', 0):.3f}")

    print(f"\n[가설 4] 혈액형 x MBTI 차원 점수")
    if anova_blood:
        all_ns = True
        for dk, r in anova_blood.items():
            sig = 'sig' if r.get('p_value', 1) < 0.05 else 'ns'
            if sig == 'sig':
                all_ns = False
            print(f"  -> {dk}: F={r.get('f_stat', 0):.2f}, "
                  f"eta2={r.get('eta_squared', 0):.4f} [{sig}]")
        if all_ns:
            print("  -> [결론] 모든 차원에서 혈액형 효과 유의하지 않음 (H4 지지)")

    print(f"\n[가설 5] MBTI 밈 인식")
    if meme_result:
        print(f"  -> MBTI 신뢰도: {meme_result.get('mbti_trust_mean', 0):.2f}/7")
        print(f"  -> 혈액형 신뢰도: {meme_result.get('blood_trust_mean', 0):.2f}/7")
        print(f"  -> 대응표본 비교: t={meme_result.get('paired_t', 0):.3f}, "
              f"d={meme_result.get('paired_d', 0):.3f}")
        if 'meme_corr' in meme_result:
            for dk, corr in meme_result['meme_corr'].items():
                sig = 'sig' if corr.get('p_value', 1) < 0.05 else 'ns'
                print(f"    {dk} x 신뢰도: r={corr.get('r', 0):.3f} [{sig}]")

    print("\n" + "─" * 60)
    print("  [핵심 인사이트]")
    print("  1. v2 밈 설문 36문항 리커트 -> MBTI 4차원 점수 산출 및 분류")
    print("  2. 자기보고 MBTI와의 일치도 + Cohen's kappa로 밈 설문 타당성 검증")
    print("  3. Kaggle 43,744명 대규모 데이터와 차원 점수 비교 (Cohen's d)")
    print("  4. 최근접 중심 분류기: 차원 점수로 MBTI 유형 예측 + 확신도")
    print("  5. 혈액형-MBTI 무관성: ANOVA eta2로 재확인")
    print("  6. MBTI vs 혈액형 신뢰도 직접 비교 (대응표본)")
    print("─" * 60)

    print(f"\n[완료] 팀원 D 분석 완료! 그래프 저장 위치: results/figures/team_d/\n")


# ============================================================
#  메인 실행
# ============================================================

def main():
    """팀원 D 전체 분석 실행"""

    # 데이터 로딩
    data = load_and_preprocess()

    # 분석 1: 설문 응답 EDA
    analyze_survey_eda(data)

    # 분석 2: 자기보고 vs 설문산출 일치도
    agreement = analyze_agreement(data)

    # 분석 3: 설문 vs Kaggle 차원 점수 비교
    comparison = analyze_score_comparison(data)

    # 분석 4: MBTI 유형 분포 비교
    chi2_dist = analyze_type_distribution(data)

    # 분석 5: MBTI 예측 (최근접 중심 분류기)
    prediction = analyze_mbti_prediction(data)

    # 분석 5-2: 로지스틱 회귀 MBTI 예측
    logistic_pred = analyze_logistic_prediction(data, prediction)

    # 분석 5-3: 로지스틱 회귀 모형 진단
    logistic_diag = analyze_logistic_diagnostics(data, logistic_pred)

    # 분석 6: 혈액형 × MBTI
    anova_blood = analyze_blood_mbti(data)

    # 분석 7: MBTI 밈 인식 (v2 보너스 문항)
    meme_result = analyze_meme_perception(data)

    # 분석 8: 효과크기 Forest Plot
    analyze_effect_size_forest(comparison, anova_blood, prediction, meme_result, agreement)

    # 분석 9: 종합 결론 인포그래픽
    create_conclusion_infographic(data, agreement, comparison, prediction,
                                  anova_blood, meme_result)

    # 최종 요약
    create_summary(data, agreement, comparison, prediction, anova_blood, meme_result)


if __name__ == '__main__':
    set_project_style()
    main()
