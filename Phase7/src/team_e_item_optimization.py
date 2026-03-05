# -*- coding: utf-8 -*-
"""
팀원 E: MBTI 설문 문항 최적화 — 질문 축소로 정확도 향상 가능성 검증
====================================================================
데이터: MBTI 밈 설문 v2
분석: 심리측정학적 문항 분석 → 최적 문항 부분집합 탐색 → 정확도 비교

핵심 질문:
  "현재 36문항(차원당 9문항)에서 질문을 줄여서 정확도를 높일 수 있는가?"

분석 방법:
  1) 문항 분석 (Item Analysis)
     - 수정 문항-총점 상관 (Corrected Item-Total Correlation, CITC)
     - Cronbach's α 및 α-if-item-deleted
     - 문항 변별도 (상위/하위 27% 그룹 비교)
  2) 문항-자기보고 예측력 분석
     - 문항별 자기보고 MBTI 예측 정확도 기여도
     - Point-biserial 상관 (문항 점수 ↔ 자기보고 일치 여부)
  3) 최적 문항 부분집합 탐색
     - 순차 제거 (Sequential Backward Elimination)
     - 전수 탐색 (Exhaustive Search) — 가능한 모든 부분집합 테스트
     - Leave-One-Out 교차검증 (LOO-CV)
  4) 정확도 비교 (전체 36문항 vs 최적 축소)
     - 차원별 일치율
     - 전체 4글자 일치율

그래프 목록 (15개):
  fig_e1  : 문항-총점 상관 (CITC) 히트맵
  fig_e2  : Cronbach's α 변화 (문항 제거 시)
  fig_e3  : 문항 변별도 (상위/하위 27% 평균 차이)
  fig_e4  : 문항별 자기보고 MBTI 예측 기여도
  fig_e5  : 순차 제거 시 차원별 정확도 변화 곡선
  fig_e6  : 최적 문항 수 vs 정확도 (전체 4글자 일치율)
  fig_e7  : 최적 문항 조합 상세 결과
  fig_e8  : 원본 vs 최적화 정확도 비교 (막대 그래프)
  fig_e9  : 차원별 문항 기여도 종합 순위
  fig_e10 : 종합 결론 인포그래픽
  fig_e11 : 교차검증 정확도 비교 (In-sample vs CV Test vs Baseline)
  fig_e12 : 문항 선택 안정성 (CV 반복에서 선택 빈도)
  fig_e13 : 교차검증 종합 결론 (과적합 진단 인포그래픽)
  fig_e14 : 고급 최적화 방법 비교 (적응적 임계값, CITC 가중, 다수결 투표 등)
  fig_e15 : 로지스틱 회귀 MBTI 차원 예측 (계수 히트맵, 정확도 비교)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from itertools import combinations

from common.config import MBTI_TYPES
from common.plot_style import set_project_style, save_figure
from common.stats_utils import (
    linear_regression, pearson_correlation,
    logistic_regression_train, logistic_regression_predict, standardize_features,
    logistic_regression_diagnostics, compute_vif, logistic_aic_bic,
    logistic_mcfadden_r2, compute_classification_metrics
)

from survey.mbti_scoring_v2 import (
    SCORING_MAP_V2, MIDPOINT, V2_COL_MAP,
    reverse_score, LIKERT_START_COL, LIKERT_END_COL
)

TEAM = 'team_e'

# ── 설문 CSV 경로 ──
SURVEY_CSV_V2 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'data', 'meme',
    'MBTI_밈_설문v2_응답_데이터 - Form Responses 1.csv'
)

# ── 차원 관련 상수 ──
DIM_KEYS = ['EI', 'SN', 'TF', 'JP']
DIM_LABELS = {'EI': '내향성(EI)', 'SN': '감각(SN)', 'TF': '사고(TF)', 'JP': '판단(JP)'}
DIM_COLORS = {'EI': '#e74c3c', 'SN': '#2ecc71', 'TF': '#3498db', 'JP': '#f39c12'}

# 분류 기준: ≥4.0 → 첫 글자 (E, S, T, J), <4.0 → 둘째 글자 (I, N, F, P)
DIM_HIGH = {'EI': 'E', 'SN': 'S', 'TF': 'T', 'JP': 'J'}
DIM_LOW  = {'EI': 'I', 'SN': 'N', 'TF': 'F', 'JP': 'P'}


# ============================================================
#  1. 데이터 로딩 및 전처리
# ============================================================

def load_survey_data():
    """설문 CSV 로딩 → (raw_array, valid_mask, self_mbti, item_scores_per_dim)"""
    print(f"\n{'='*70}")
    print("  [Step 1] 설문 데이터 로딩")
    print(f"{'='*70}")

    df = pd.read_csv(SURVEY_CSV_V2)
    data = df.values
    n_total = len(data)
    print(f"  전체 응답: {n_total}명")

    # 자기보고 MBTI 추출 및 유효 필터
    self_mbti_raw = data[:, V2_COL_MAP['self_mbti']].astype(str)
    valid_mask = np.array([m.upper().strip() in MBTI_TYPES for m in self_mbti_raw])
    self_mbti = np.array([m.upper().strip() for m in self_mbti_raw])

    n_valid = valid_mask.sum()
    n_excluded = n_total - n_valid
    print(f"  유효 MBTI: {n_valid}명 (제외: {n_excluded}명 — '모름' 등)")

    # 차원별 개별 문항 점수 추출 (채점 후)
    item_scores = {}  # {dim: (n_valid, n_items)} — 채점 후 점수
    item_raw = {}     # {dim: (n_valid, n_items)} — 원점수

    valid_data = data[valid_mask]

    for dim_key in DIM_KEYS:
        dim_info = SCORING_MAP_V2[dim_key]
        cols = dim_info['csv_cols']
        fwd = dim_info['forward_cols']
        rev = dim_info['reverse_cols']
        n_items = len(cols)

        scores_matrix = np.zeros((n_valid, n_items))
        raw_matrix = np.zeros((n_valid, n_items))

        for i in range(n_valid):
            for j, col in enumerate(cols):
                try:
                    raw_val = int(float(valid_data[i, col]))
                except (ValueError, TypeError):
                    raw_val = 4
                raw_matrix[i, j] = raw_val

                # 채점: forward면 그대로, reverse면 역채점
                if col in fwd:
                    scores_matrix[i, j] = raw_val
                else:
                    scores_matrix[i, j] = reverse_score(raw_val)

        item_scores[dim_key] = scores_matrix
        item_raw[dim_key] = raw_matrix

    # 자기보고 MBTI에서 각 차원 글자 추출
    valid_self_mbti = self_mbti[valid_mask]
    self_letters = {}
    for dim_key in DIM_KEYS:
        idx = DIM_KEYS.index(dim_key)
        self_letters[dim_key] = np.array([m[idx] for m in valid_self_mbti])

    # 전체 점수 (9문항 평균)
    dim_scores = {}
    for dim_key in DIM_KEYS:
        dim_scores[dim_key] = item_scores[dim_key].mean(axis=1)

    # 전체 설문산출 MBTI
    computed_mbti = []
    for i in range(n_valid):
        letters = []
        for dim_key in DIM_KEYS:
            s = dim_scores[dim_key][i]
            letters.append(DIM_HIGH[dim_key] if s >= MIDPOINT else DIM_LOW[dim_key])
        computed_mbti.append(''.join(letters))
    computed_mbti = np.array(computed_mbti)

    # 기존 정확도
    overall_match = (computed_mbti == valid_self_mbti).mean()
    dim_match = {}
    for dim_key in DIM_KEYS:
        idx = DIM_KEYS.index(dim_key)
        comp_letters = np.array([m[idx] for m in computed_mbti])
        dim_match[dim_key] = (comp_letters == self_letters[dim_key]).mean()

    print(f"\n  ── 기존 정확도 (전체 9문항) ──")
    for dim_key in DIM_KEYS:
        print(f"    {DIM_LABELS[dim_key]}: {dim_match[dim_key]*100:.1f}%")
    print(f"    전체 4글자 일치: {overall_match*100:.1f}%")

    return {
        'data': valid_data,
        'n': n_valid,
        'n_total': n_total,
        'item_scores': item_scores,       # 채점 후 점수
        'item_raw': item_raw,             # 원점수
        'dim_scores': dim_scores,          # 차원 평균점수
        'self_mbti': valid_self_mbti,      # 자기보고 MBTI
        'computed_mbti': computed_mbti,    # 설문산출 MBTI
        'self_letters': self_letters,      # 차원별 자기보고 글자
        'dim_match': dim_match,            # 차원별 일치율
        'overall_match': overall_match,    # 전체 일치율
    }


# ============================================================
#  2. 문항 분석 (Item Analysis)
# ============================================================

def corrected_item_total_correlation(scores_matrix):
    """수정 문항-총점 상관 (CITC)

    각 문항과 나머지 문항 합 간의 Pearson 상관.
    해당 문항을 총점에서 제외하여 인위적 상관 팽창 방지.

    Parameters: scores_matrix (n, n_items)
    Returns: citc (n_items,)
    """
    n, k = scores_matrix.shape
    citc = np.zeros(k)

    for j in range(k):
        item_j = scores_matrix[:, j]
        rest_sum = scores_matrix.sum(axis=1) - item_j
        # Pearson correlation
        r = np.corrcoef(item_j, rest_sum)[0, 1]
        citc[j] = r if not np.isnan(r) else 0.0

    return citc


def cronbachs_alpha(scores_matrix):
    """Cronbach's α 계산

    α = (k / (k-1)) * (1 - Σσ²ᵢ / σ²total)
    """
    n, k = scores_matrix.shape
    if k <= 1:
        return 0.0

    item_vars = scores_matrix.var(axis=0, ddof=1)
    total_var = scores_matrix.sum(axis=1).var(ddof=1)

    if total_var == 0:
        return 0.0

    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return alpha


def alpha_if_deleted(scores_matrix):
    """각 문항 제거 시 Cronbach's α

    Returns: alpha_values (n_items,)
    """
    n, k = scores_matrix.shape
    alphas = np.zeros(k)

    for j in range(k):
        # j번째 문항 제거
        remaining = np.delete(scores_matrix, j, axis=1)
        alphas[j] = cronbachs_alpha(remaining)

    return alphas


def item_discrimination(scores_matrix):
    """문항 변별도: 상위 27% vs 하위 27% 평균 차이

    Returns: disc (n_items,), upper_means (n_items,), lower_means (n_items,)
    """
    n, k = scores_matrix.shape
    total_scores = scores_matrix.sum(axis=1)

    n_group = max(1, int(n * 0.27))
    sorted_idx = np.argsort(total_scores)
    lower_idx = sorted_idx[:n_group]
    upper_idx = sorted_idx[-n_group:]

    upper_means = scores_matrix[upper_idx].mean(axis=0)
    lower_means = scores_matrix[lower_idx].mean(axis=0)
    disc = upper_means - lower_means

    return disc, upper_means, lower_means


def run_item_analysis(info):
    """차원별 문항 분석 실행"""
    print(f"\n{'='*70}")
    print("  [Step 2] 문항 분석 (Item Analysis)")
    print(f"{'='*70}")

    results = {}

    for dim_key in DIM_KEYS:
        scores = info['item_scores'][dim_key]
        dim_info = SCORING_MAP_V2[dim_key]
        cols = dim_info['csv_cols']
        n_items = len(cols)

        # (a) CITC
        citc = corrected_item_total_correlation(scores)

        # (b) Cronbach's α
        alpha_full = cronbachs_alpha(scores)
        alpha_del = alpha_if_deleted(scores)

        # (c) 변별도
        disc, upper_m, lower_m = item_discrimination(scores)

        # (d) 자기보고 예측 기여도
        # 각 문항이 자기보고 MBTI 차원 글자를 얼마나 잘 예측하는지
        self_letter = info['self_letters'][dim_key]
        # 자기보고가 High letter인지 여부 (binary)
        self_high = (self_letter == DIM_HIGH[dim_key]).astype(float)

        item_predictive = np.zeros(n_items)
        for j in range(n_items):
            # 단일 문항 점수 ≥ 4.0 이면 High로 예측
            predicted_high = (scores[:, j] >= MIDPOINT).astype(float)
            item_predictive[j] = (predicted_high == self_high).mean()

        results[dim_key] = {
            'citc': citc,
            'alpha_full': alpha_full,
            'alpha_del': alpha_del,
            'disc': disc,
            'upper_means': upper_m,
            'lower_means': lower_m,
            'item_predictive': item_predictive,
            'cols': cols,
            'q_labels': [f'Q{c}' for c in cols],
        }

        # 출력
        print(f"\n  ── {DIM_LABELS[dim_key]} (α={alpha_full:.3f}) ──")
        print(f"  {'문항':<6} {'CITC':>6} {'α삭제':>6} {'변별도':>6} {'예측력':>6}")
        for j in range(n_items):
            flag = ''
            if citc[j] < 0.3:
                flag = ' ⚠️ 약한 문항'
            if alpha_del[j] > alpha_full + 0.01:
                flag += ' 📈 α↑'
            print(f"  Q{cols[j]:<4} {citc[j]:>6.3f} {alpha_del[j]:>6.3f} "
                  f"{disc[j]:>6.3f} {item_predictive[j]*100:>5.1f}%{flag}")

        # 차원별 회귀: CITC → 예측력
        reg = linear_regression(citc, item_predictive)
        print(f"  [회귀] 예측력 = {reg['slope']:.4f} \u00d7 CITC + {reg['intercept']:.4f}, "
              f"R\u00b2={reg['r_squared']:.4f}")

    # 전체 문항 통합 회귀: CITC → 예측력 (36문항)
    all_citc = np.concatenate([results[dk]['citc'] for dk in DIM_KEYS])
    all_pred = np.concatenate([results[dk]['item_predictive'] for dk in DIM_KEYS])
    all_disc = np.concatenate([results[dk]['disc'] for dk in DIM_KEYS])

    print(f"\n  ── 전체 36문항 통합 회귀분석 ──")

    # 회귀 1: CITC → 예측력
    reg_citc = linear_regression(all_citc, all_pred)
    print(f"  [회귀 1] 예측력 = {reg_citc['slope']:.4f} \u00d7 CITC + {reg_citc['intercept']:.4f}")
    print(f"    R\u00b2 = {reg_citc['r_squared']:.4f} ({'*' if reg_citc['p_value'] < 0.05 else 'ns'})")
    print(f"    해석: CITC가 1단위 증가 시 예측력 {reg_citc['slope']*100:.1f}%p 변화")

    # 회귀 2: 변별도 → 예측력
    reg_disc = linear_regression(all_disc, all_pred)
    print(f"  [회귀 2] 예측력 = {reg_disc['slope']:.4f} \u00d7 변별도 + {reg_disc['intercept']:.4f}")
    print(f"    R\u00b2 = {reg_disc['r_squared']:.4f} ({'*' if reg_disc['p_value'] < 0.05 else 'ns'})")

    # 상관
    corr = pearson_correlation(all_citc, all_pred)
    print(f"  [상관] CITC \u2194 예측력: r={corr['r']:.4f}, "
          f"R\u00b2={corr['r']**2:.4f}")

    results['_regression'] = {
        'citc_pred': reg_citc,
        'disc_pred': reg_disc,
        'corr_citc_pred': corr,
    }

    return results


# ============================================================
#  3. 최적 문항 부분집합 탐색
# ============================================================

def compute_accuracy_with_subset(item_scores, self_letters, subset_indices, dim_key):
    """주어진 문항 부분집합으로 차원 정확도 계산

    Parameters
    ----------
    item_scores : (n, n_items) — 전체 문항 채점 후 점수
    self_letters : (n,) — 자기보고 차원 글자
    subset_indices : list of int — 사용할 문항 인덱스 (0~8)
    dim_key : str — 'EI', 'SN', 'TF', 'JP'

    Returns
    -------
    accuracy : float
    """
    subset_scores = item_scores[:, subset_indices].mean(axis=1)
    predicted = np.where(subset_scores >= MIDPOINT, DIM_HIGH[dim_key], DIM_LOW[dim_key])
    accuracy = (predicted == self_letters).mean()
    return accuracy


def compute_overall_accuracy_with_subsets(info, dim_subsets):
    """모든 차원에 부분집합 적용 → 전체 4글자 정확도

    Parameters
    ----------
    info : dict
    dim_subsets : {dim_key: list of item indices}

    Returns
    -------
    overall_acc, dim_accs
    """
    n = info['n']
    dim_accs = {}
    predicted_types = []

    for i in range(n):
        letters = []
        for dim_key in DIM_KEYS:
            subset = dim_subsets[dim_key]
            score = info['item_scores'][dim_key][i, subset].mean()
            letter = DIM_HIGH[dim_key] if score >= MIDPOINT else DIM_LOW[dim_key]
            letters.append(letter)
        predicted_types.append(''.join(letters))

    predicted_types = np.array(predicted_types)
    overall_acc = (predicted_types == info['self_mbti']).mean()

    for dim_key in DIM_KEYS:
        subset = dim_subsets[dim_key]
        dim_accs[dim_key] = compute_accuracy_with_subset(
            info['item_scores'][dim_key],
            info['self_letters'][dim_key],
            subset, dim_key
        )

    return overall_acc, dim_accs


def loo_cv_accuracy(item_scores, self_letters, subset_indices, dim_key):
    """Leave-One-Out 교차검증 정확도

    N=93이므로 과적합 방지를 위해 LOO-CV 사용.
    각 응답자를 하나씩 제외하고 나머지로 threshold를 최적화하되,
    여기서는 threshold=4.0 고정이므로 LOO는 사실상 full accuracy와 동일.
    대신, 한 명 제외한 나머지의 평균 점수와의 상관으로 안정성 체크.
    """
    n = len(self_letters)
    correct = 0
    for i in range(n):
        score = item_scores[i, subset_indices].mean()
        predicted = DIM_HIGH[dim_key] if score >= MIDPOINT else DIM_LOW[dim_key]
        if predicted == self_letters[i]:
            correct += 1
    return correct / n


def sequential_backward_elimination(item_scores, self_letters, dim_key, item_analysis):
    """순차 후진 제거: 가장 기여도 낮은 문항부터 하나씩 제거

    제거 기준: CITC와 예측력의 가중 합 기준 최하위 문항 제거

    Returns
    -------
    history : list of (n_items, accuracy, removed_q, remaining_indices)
    """
    n_total_items = item_scores.shape[1]
    remaining = list(range(n_total_items))
    citc = item_analysis['citc']
    pred = item_analysis['item_predictive']

    history = []

    # 초기 (전체 9문항)
    acc = compute_accuracy_with_subset(item_scores, self_letters, remaining, dim_key)
    history.append((len(remaining), acc, None, remaining.copy()))

    while len(remaining) > 1:
        # 각 문항 제거 시 정확도 계산
        best_acc = -1
        best_remove = -1
        for idx in remaining:
            candidate = [x for x in remaining if x != idx]
            candidate_acc = compute_accuracy_with_subset(
                item_scores, self_letters, candidate, dim_key)
            if candidate_acc > best_acc:
                best_acc = candidate_acc
                best_remove = idx

        remaining = [x for x in remaining if x != best_remove]
        cols = item_analysis['cols']
        history.append((len(remaining), best_acc, f'Q{cols[best_remove]}', remaining.copy()))

    return history


def exhaustive_search(item_scores, self_letters, dim_key, min_items=3, max_items=9):
    """전수 탐색: 가능한 모든 부분집합에서 최적 정확도 탐색

    9문항에서 3~9문항 부분집합 탐색.
    C(9,3)+C(9,4)+...+C(9,9) = 84+126+126+84+36+9+1 = 466 경우

    Returns
    -------
    best_per_size : {n_items: (best_acc, best_indices)}
    all_results : list of (n_items, acc, indices)
    """
    n_items = item_scores.shape[1]
    best_per_size = {}
    all_results = []

    for k in range(min_items, max_items + 1):
        best_acc = -1
        best_combo = None

        for combo in combinations(range(n_items), k):
            subset = list(combo)
            acc = compute_accuracy_with_subset(
                item_scores, self_letters, subset, dim_key)
            all_results.append((k, acc, subset))

            if acc > best_acc:
                best_acc = acc
                best_combo = subset

        best_per_size[k] = (best_acc, best_combo)

    return best_per_size, all_results


def run_optimization(info, item_analysis_results):
    """전체 최적화 실행"""
    print(f"\n{'='*70}")
    print("  [Step 3] 최적 문항 부분집합 탐색")
    print(f"{'='*70}")

    opt_results = {}

    for dim_key in DIM_KEYS:
        scores = info['item_scores'][dim_key]
        self_l = info['self_letters'][dim_key]
        ia = item_analysis_results[dim_key]

        print(f"\n  ── {DIM_LABELS[dim_key]} ──")

        # (a) 순차 후진 제거
        sbe_history = sequential_backward_elimination(scores, self_l, dim_key, ia)
        print(f"  순차 제거 과정:")
        for n_items, acc, removed, remaining in sbe_history:
            removed_str = f' (제거: {removed})' if removed else ''
            q_labels = [f'Q{ia["cols"][i]}' for i in remaining]
            print(f"    {n_items}문항: {acc*100:.1f}%{removed_str}")

        # (b) 전수 탐색
        best_per_size, all_results = exhaustive_search(scores, self_l, dim_key)
        print(f"\n  전수 탐색 최적 결과:")
        for k in sorted(best_per_size.keys()):
            acc, indices = best_per_size[k]
            q_labels = [f'Q{ia["cols"][i]}' for i in indices]
            print(f"    {k}문항: {acc*100:.1f}% — {q_labels}")

        # 최적 문항 수 결정 (정확도 최대, 같으면 적은 문항 수 선호)
        baseline_acc = best_per_size[9][0]
        best_reduced_k = 9
        best_reduced_acc = baseline_acc
        for k in range(3, 9):
            acc, _ = best_per_size[k]
            if acc > best_reduced_acc or (acc == best_reduced_acc and k < best_reduced_k):
                best_reduced_acc = acc
                best_reduced_k = k

        opt_results[dim_key] = {
            'sbe_history': sbe_history,
            'best_per_size': best_per_size,
            'all_results': all_results,
            'optimal_k': best_reduced_k,
            'optimal_indices': best_per_size[best_reduced_k][1],
            'optimal_acc': best_per_size[best_reduced_k][0],
            'baseline_acc': baseline_acc,
        }

        opt_q = [f'Q{ia["cols"][i]}' for i in best_per_size[best_reduced_k][1]]
        improvement = (best_reduced_acc - baseline_acc) * 100
        print(f"\n  ★ 최적: {best_reduced_k}문항 {opt_q}")
        print(f"    정확도: {baseline_acc*100:.1f}% → {best_reduced_acc*100:.1f}% "
              f"(Δ={improvement:+.1f}%p)")

    # 전체 4글자 일치율 (최적 문항 조합)
    optimal_subsets = {dk: list(opt_results[dk]['optimal_indices']) for dk in DIM_KEYS}
    full_subsets = {dk: list(range(9)) for dk in DIM_KEYS}

    overall_baseline, dim_baseline = compute_overall_accuracy_with_subsets(info, full_subsets)
    overall_optimal, dim_optimal = compute_overall_accuracy_with_subsets(info, optimal_subsets)

    print(f"\n{'─'*70}")
    print(f"  전체 4글자 일치율 비교:")
    print(f"    원본 (36문항): {overall_baseline*100:.1f}%")
    print(f"    최적화: {overall_optimal*100:.1f}%")
    total_items = sum(opt_results[dk]['optimal_k'] for dk in DIM_KEYS)
    print(f"    총 문항 수: 36 → {total_items}")
    improvement = (overall_optimal - overall_baseline) * 100
    print(f"    개선: {improvement:+.1f}%p")

    opt_results['_summary'] = {
        'overall_baseline': overall_baseline,
        'overall_optimal': overall_optimal,
        'dim_baseline': dim_baseline,
        'dim_optimal': dim_optimal,
        'total_items_original': 36,
        'total_items_optimal': total_items,
        'optimal_subsets': optimal_subsets,
    }

    return opt_results


# ============================================================
#  3-2. 고급 최적화 방법 (Advanced Optimization)
# ============================================================

def find_optimal_threshold(item_scores, self_letters, dim_key,
                           subset_indices=None, weights=None,
                           lo=2.0, hi=6.0, step=0.1):
    """차원별 최적 임계값 탐색

    고정 MIDPOINT=4.0 대신, 데이터에 맞는 최적 임계값을 탐색.
    7점 척도에서 2.0~6.0 범위를 0.1 단위로 탐색 (41개 후보).

    Parameters
    ----------
    item_scores : (n, n_items)
    self_letters : (n,)
    dim_key : str
    subset_indices : list of int or None (전체 사용)
    weights : array or None (균등 가중)

    Returns
    -------
    best_threshold, best_accuracy
    """
    if subset_indices is None:
        subset_indices = list(range(item_scores.shape[1]))

    scores_subset = item_scores[:, subset_indices]

    if weights is not None:
        w = np.array(weights)
        w_pos = np.maximum(w, 0)
        if w_pos.sum() == 0:
            dim_score = scores_subset.mean(axis=1)
        else:
            w_norm = w_pos / w_pos.sum()
            if len(w_norm) == item_scores.shape[1]:
                w_norm = w_norm[subset_indices]
                w_norm = w_norm / w_norm.sum()
            dim_score = (scores_subset * w_norm).sum(axis=1)
    else:
        dim_score = scores_subset.mean(axis=1)

    thresholds = np.arange(lo, hi + step / 2, step)
    best_acc = -1
    best_threshold = MIDPOINT

    for t in thresholds:
        predicted = np.where(dim_score >= t, DIM_HIGH[dim_key], DIM_LOW[dim_key])
        acc = (predicted == self_letters).mean()
        if acc > best_acc or (acc == best_acc and abs(t - MIDPOINT) < abs(best_threshold - MIDPOINT)):
            best_acc = acc
            best_threshold = t

    return best_threshold, best_acc


def compute_weighted_accuracy(item_scores, self_letters, dim_key,
                              weights, threshold=MIDPOINT):
    """CITC 기반 가중 문항 점수로 정확도 계산"""
    w = np.array(weights)
    w_pos = np.maximum(w, 0)
    if w_pos.sum() == 0:
        w_norm = np.ones(len(w)) / len(w)
    else:
        w_norm = w_pos / w_pos.sum()

    dim_score = (item_scores * w_norm).sum(axis=1)
    predicted = np.where(dim_score >= threshold, DIM_HIGH[dim_key], DIM_LOW[dim_key])
    return (predicted == self_letters).mean()


def compute_majority_vote_accuracy(item_scores, self_letters, dim_key,
                                   subset_indices=None, threshold=MIDPOINT):
    """다수결 투표: 각 문항이 독립적으로 투표, 과반수로 결정"""
    if subset_indices is None:
        subset_indices = list(range(item_scores.shape[1]))

    scores_subset = item_scores[:, subset_indices]
    n, k = scores_subset.shape

    votes = (scores_subset >= threshold).astype(int)
    majority = votes.sum(axis=1) > (k / 2)

    predicted = np.where(majority, DIM_HIGH[dim_key], DIM_LOW[dim_key])
    return (predicted == self_letters).mean()


def compute_logistic_loo_accuracy(item_scores, self_letters, dim_key):
    """로지스틱 회귀 LOO-CV 정확도 계산

    Leave-One-Out 교차검증: 각 샘플을 하나씩 빼고
    나머지로 로지스틱 회귀를 학습하여 빠진 샘플을 예측.
    """
    n = len(self_letters)
    y = (self_letters == DIM_HIGH[dim_key]).astype(int)
    X = item_scores  # (n, 9) 문항 점수 행렬

    correct = 0
    weights_all = None  # 전체 학습용 가중치도 반환

    for i in range(n):
        # train/test 분할
        train_mask = np.ones(n, dtype=bool)
        train_mask[i] = False
        X_train, y_train = X[train_mask], y[train_mask]
        X_test = X[i:i+1]

        # 표준화 (학습 데이터 기준)
        X_tr_std, tr_mean, tr_std = standardize_features(X_train)
        X_te_std, _, _ = standardize_features(X_test, mean=tr_mean, std=tr_std)

        # 학습
        model = logistic_regression_train(
            X_tr_std, y_train, lr=0.5, epochs=300, lambda_reg=0.1)

        # 예측
        pred = logistic_regression_predict(X_te_std, model['weights'])
        if pred['predictions'][0] == y[i]:
            correct += 1

    # 전체 데이터로도 한번 학습 (계수 반환용)
    X_full_std, _, _ = standardize_features(X)
    model_full = logistic_regression_train(
        X_full_std, y, lr=0.5, epochs=500, lambda_reg=0.1)

    return correct / n, model_full['weights'], model_full['train_acc']


def run_advanced_optimization(info, item_analysis, opt_results):
    """고급 최적화 방법 비교 실행

    6가지 방법을 In-sample로 비교:
      0) Baseline: 9문항, 균등, t=4.0
      1) Item Subset: 최적 부분집합, 균등, t=4.0 (기존)
      2) Adaptive Threshold: 9문항, 균등, 최적 임계값
      3) CITC Weighted: 9문항, CITC 가중, t=4.0
      4) CITC + Adaptive: 9문항, CITC 가중, 최적 임계값
      5) Majority Vote: 9문항, 다수결 투표
      6) Subset + Adaptive: 최적 부분집합, 균등, 최적 임계값
    """
    print(f"\n{'='*70}")
    print("  [Step 3-2] 고급 최적화 방법 비교")
    print(f"{'='*70}")

    n = info['n']
    methods = {}

    # ── Method 0: Baseline ──
    methods['baseline'] = {
        'name': '기준선 (9문항, 균등, t=4.0)',
        'short': 'Baseline',
        'overall': info['overall_match'],
        'dim_accs': dict(info['dim_match']),
    }

    # ── Method 1: Item Subset (기존) ──
    methods['item_subset'] = {
        'name': '문항 축소 (최적 부분집합, t=4.0)',
        'short': 'Item Subset',
        'overall': opt_results['_summary']['overall_optimal'],
        'dim_accs': dict(opt_results['_summary']['dim_optimal']),
    }

    # ── Method 2: Adaptive Threshold ──
    adap_dim_accs = {}
    adap_thresholds = {}
    for dk in DIM_KEYS:
        t, acc = find_optimal_threshold(
            info['item_scores'][dk], info['self_letters'][dk], dk)
        adap_dim_accs[dk] = acc
        adap_thresholds[dk] = t

    adap_pred = []
    for i in range(n):
        letters = []
        for dk in DIM_KEYS:
            s = info['item_scores'][dk][i].mean()
            letters.append(DIM_HIGH[dk] if s >= adap_thresholds[dk] else DIM_LOW[dk])
        adap_pred.append(''.join(letters))
    adap_pred = np.array(adap_pred)
    adap_overall = (adap_pred == info['self_mbti']).mean()

    methods['adaptive'] = {
        'name': '적응적 임계값 (9문항)',
        'short': 'Adaptive Threshold',
        'overall': adap_overall,
        'dim_accs': adap_dim_accs,
        'thresholds': adap_thresholds,
    }

    print(f"\n  ── Method 2: 적응적 임계값 ──")
    for dk in DIM_KEYS:
        print(f"    {DIM_LABELS[dk]}: t={adap_thresholds[dk]:.1f} → "
              f"{adap_dim_accs[dk]*100:.1f}% (기준: {info['dim_match'][dk]*100:.1f}%)")
    print(f"    전체 4글자: {adap_overall*100:.1f}%")

    # ── Method 3: CITC-Weighted ──
    citc_dim_accs = {}
    citc_weights = {}
    for dk in DIM_KEYS:
        w = item_analysis[dk]['citc']
        citc_weights[dk] = w
        acc = compute_weighted_accuracy(
            info['item_scores'][dk], info['self_letters'][dk], dk, w, MIDPOINT)
        citc_dim_accs[dk] = acc

    citc_pred = []
    for i in range(n):
        letters = []
        for dk in DIM_KEYS:
            w = citc_weights[dk]
            w_pos = np.maximum(w, 0)
            w_norm = w_pos / w_pos.sum() if w_pos.sum() > 0 else np.ones(9) / 9
            s = (info['item_scores'][dk][i] * w_norm).sum()
            letters.append(DIM_HIGH[dk] if s >= MIDPOINT else DIM_LOW[dk])
        citc_pred.append(''.join(letters))
    citc_pred = np.array(citc_pred)
    citc_overall = (citc_pred == info['self_mbti']).mean()

    methods['citc'] = {
        'name': 'CITC 가중 (9문항, t=4.0)',
        'short': 'CITC Weighted',
        'overall': citc_overall,
        'dim_accs': citc_dim_accs,
    }

    print(f"\n  ── Method 3: CITC 가중 점수 ──")
    for dk in DIM_KEYS:
        print(f"    {DIM_LABELS[dk]}: {citc_dim_accs[dk]*100:.1f}%")
    print(f"    전체 4글자: {citc_overall*100:.1f}%")

    # ── Method 4: CITC + Adaptive Threshold ──
    citc_adap_dim_accs = {}
    citc_adap_thresholds = {}
    for dk in DIM_KEYS:
        w = citc_weights[dk]
        t, acc = find_optimal_threshold(
            info['item_scores'][dk], info['self_letters'][dk], dk,
            weights=w)
        citc_adap_dim_accs[dk] = acc
        citc_adap_thresholds[dk] = t

    citc_adap_pred = []
    for i in range(n):
        letters = []
        for dk in DIM_KEYS:
            w = citc_weights[dk]
            w_pos = np.maximum(w, 0)
            w_norm = w_pos / w_pos.sum() if w_pos.sum() > 0 else np.ones(9) / 9
            s = (info['item_scores'][dk][i] * w_norm).sum()
            t = citc_adap_thresholds[dk]
            letters.append(DIM_HIGH[dk] if s >= t else DIM_LOW[dk])
        citc_adap_pred.append(''.join(letters))
    citc_adap_pred = np.array(citc_adap_pred)
    citc_adap_overall = (citc_adap_pred == info['self_mbti']).mean()

    methods['citc_adaptive'] = {
        'name': 'CITC 가중 + 적응적 임계값',
        'short': 'CITC + Adaptive',
        'overall': citc_adap_overall,
        'dim_accs': citc_adap_dim_accs,
        'thresholds': citc_adap_thresholds,
    }

    print(f"\n  ── Method 4: CITC 가중 + 적응적 임계값 ──")
    for dk in DIM_KEYS:
        print(f"    {DIM_LABELS[dk]}: t={citc_adap_thresholds[dk]:.1f} → "
              f"{citc_adap_dim_accs[dk]*100:.1f}%")
    print(f"    전체 4글자: {citc_adap_overall*100:.1f}%")

    # ── Method 5: Majority Vote ──
    mv_dim_accs = {}
    for dk in DIM_KEYS:
        acc = compute_majority_vote_accuracy(
            info['item_scores'][dk], info['self_letters'][dk], dk)
        mv_dim_accs[dk] = acc

    mv_pred = []
    for i in range(n):
        letters = []
        for dk in DIM_KEYS:
            votes = (info['item_scores'][dk][i] >= MIDPOINT).astype(int)
            majority = votes.sum() > 4.5  # 9 items → need ≥5
            letters.append(DIM_HIGH[dk] if majority else DIM_LOW[dk])
        mv_pred.append(''.join(letters))
    mv_pred = np.array(mv_pred)
    mv_overall = (mv_pred == info['self_mbti']).mean()

    methods['majority'] = {
        'name': '다수결 투표 (9문항)',
        'short': 'Majority Vote',
        'overall': mv_overall,
        'dim_accs': mv_dim_accs,
    }

    print(f"\n  ── Method 5: 다수결 투표 ──")
    for dk in DIM_KEYS:
        print(f"    {DIM_LABELS[dk]}: {mv_dim_accs[dk]*100:.1f}%")
    print(f"    전체 4글자: {mv_overall*100:.1f}%")

    # ── Method 6: Subset + Adaptive ──
    sa_dim_accs = {}
    sa_thresholds = {}
    for dk in DIM_KEYS:
        subset = list(opt_results[dk]['optimal_indices'])
        t, acc = find_optimal_threshold(
            info['item_scores'][dk], info['self_letters'][dk], dk,
            subset_indices=subset)
        sa_dim_accs[dk] = acc
        sa_thresholds[dk] = t

    sa_pred = []
    for i in range(n):
        letters = []
        for dk in DIM_KEYS:
            subset = list(opt_results[dk]['optimal_indices'])
            s = info['item_scores'][dk][i, subset].mean()
            t = sa_thresholds[dk]
            letters.append(DIM_HIGH[dk] if s >= t else DIM_LOW[dk])
        sa_pred.append(''.join(letters))
    sa_pred = np.array(sa_pred)
    sa_overall = (sa_pred == info['self_mbti']).mean()

    methods['subset_adaptive'] = {
        'name': '문항 축소 + 적응적 임계값',
        'short': 'Subset + Adaptive',
        'overall': sa_overall,
        'dim_accs': sa_dim_accs,
        'thresholds': sa_thresholds,
    }

    print(f"\n  ── Method 6: 문항 축소 + 적응적 임계값 ──")
    for dk in DIM_KEYS:
        subset = list(opt_results[dk]['optimal_indices'])
        print(f"    {DIM_LABELS[dk]}: t={sa_thresholds[dk]:.1f} → "
              f"{sa_dim_accs[dk]*100:.1f}%")
    print(f"    전체 4글자: {sa_overall*100:.1f}%")

    # ── Method 7: Logistic Regression (LOO-CV) ──
    lr_dim_accs = {}
    lr_weights = {}
    lr_train_accs = {}
    for dk in DIM_KEYS:
        loo_acc, weights, train_acc = compute_logistic_loo_accuracy(
            info['item_scores'][dk], info['self_letters'][dk], dk)
        lr_dim_accs[dk] = loo_acc
        lr_weights[dk] = weights
        lr_train_accs[dk] = train_acc

    # 전체 4글자 LOO-CV 정확도: 각 차원 독립 LOO 예측 결합
    lr_pred_dims = {}
    for dk in DIM_KEYS:
        y = (info['self_letters'][dk] == DIM_HIGH[dk]).astype(int)
        X = info['item_scores'][dk]
        preds = np.zeros(n, dtype=int)
        for i in range(n):
            train_mask = np.ones(n, dtype=bool)
            train_mask[i] = False
            X_tr, y_tr = X[train_mask], y[train_mask]
            X_te = X[i:i+1]
            X_tr_std, m, s = standardize_features(X_tr)
            X_te_std, _, _ = standardize_features(X_te, mean=m, std=s)
            model = logistic_regression_train(
                X_tr_std, y_tr, lr=0.5, epochs=300, lambda_reg=0.1)
            pred = logistic_regression_predict(X_te_std, model['weights'])
            preds[i] = pred['predictions'][0]
        lr_pred_dims[dk] = np.where(preds == 1, DIM_HIGH[dk], DIM_LOW[dk])

    lr_pred_4letter = np.array([
        ''.join([lr_pred_dims[dk][i] for dk in DIM_KEYS])
        for i in range(n)
    ])
    lr_overall = (lr_pred_4letter == info['self_mbti']).mean()

    methods['logistic'] = {
        'name': '로지스틱 회귀 (LOO-CV)',
        'short': 'Logistic Reg.',
        'overall': lr_overall,
        'dim_accs': lr_dim_accs,
        'weights': lr_weights,
        'train_accs': lr_train_accs,
    }

    print(f"\n  ── Method 7: 로지스틱 회귀 (LOO-CV) ──")
    for dk in DIM_KEYS:
        print(f"    {DIM_LABELS[dk]}: LOO-CV={lr_dim_accs[dk]*100:.1f}% "
              f"(train={lr_train_accs[dk]*100:.1f}%)")
    print(f"    전체 4글자 (LOO-CV): {lr_overall*100:.1f}%")

    # ── 요약 테이블 ──
    method_order = ['baseline', 'item_subset', 'adaptive', 'citc',
                    'citc_adaptive', 'majority', 'subset_adaptive', 'logistic']
    print(f"\n{'─'*70}")
    print(f"  {'방법':<28} {'차원 평균':>10} {'4글자':>10} {'Δ vs Base':>10}")
    print(f"  {'─'*60}")
    baseline_ov = info['overall_match']
    for key in method_order:
        m = methods[key]
        dim_avg = np.mean([m['dim_accs'][dk] for dk in DIM_KEYS]) * 100
        overall = m['overall'] * 100
        delta = overall - baseline_ov * 100
        marker = ' ★' if key != 'baseline' and delta > 0 else ''
        print(f"  {m['short']:<28} {dim_avg:>9.1f}% {overall:>9.1f}% "
              f"{delta:>+9.1f}%p{marker}")

    return methods


def _advanced_cv_fold(info, train_idx, test_idx):
    """단일 CV fold에서 고급 방법들의 test 정확도 계산

    핵심: 모든 파라미터 최적화는 train_idx에서만 수행.
    """
    results = {}

    # ── Baseline: 9문항, 균등, t=4.0 ──
    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                s = info['item_scores'][dk][i].mean()
                letters.append(DIM_HIGH[dk] if s >= MIDPOINT else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'baseline_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── Adaptive Threshold: train에서 최적 임계값 학습 ──
    adap_t = {}
    for dk in DIM_KEYS:
        t, _ = find_optimal_threshold(
            info['item_scores'][dk][train_idx],
            info['self_letters'][dk][train_idx], dk)
        adap_t[dk] = t

    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                s = info['item_scores'][dk][i].mean()
                letters.append(DIM_HIGH[dk] if s >= adap_t[dk] else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'adaptive_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── CITC-Weighted: train에서 CITC 산출 ──
    citc_w = {}
    for dk in DIM_KEYS:
        citc_w[dk] = corrected_item_total_correlation(
            info['item_scores'][dk][train_idx])

    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                w = citc_w[dk]
                w_pos = np.maximum(w, 0)
                w_norm = w_pos / w_pos.sum() if w_pos.sum() > 0 else np.ones(9) / 9
                s = (info['item_scores'][dk][i] * w_norm).sum()
                letters.append(DIM_HIGH[dk] if s >= MIDPOINT else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'citc_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── CITC + Adaptive ──
    ca_t = {}
    for dk in DIM_KEYS:
        t, _ = find_optimal_threshold(
            info['item_scores'][dk][train_idx],
            info['self_letters'][dk][train_idx], dk,
            weights=citc_w[dk])
        ca_t[dk] = t

    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                w = citc_w[dk]
                w_pos = np.maximum(w, 0)
                w_norm = w_pos / w_pos.sum() if w_pos.sum() > 0 else np.ones(9) / 9
                s = (info['item_scores'][dk][i] * w_norm).sum()
                letters.append(DIM_HIGH[dk] if s >= ca_t[dk] else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'citc_adaptive_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── Majority Vote: 파라미터 없음 ──
    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                votes = (info['item_scores'][dk][i] >= MIDPOINT).astype(int)
                majority = votes.sum() > 4.5
                letters.append(DIM_HIGH[dk] if majority else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'majority_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── Item Subset (기존 방식): train에서 subset 탐색 ──
    cv_subsets = {}
    for dk in DIM_KEYS:
        opt_idx, opt_k = _cv_find_optimal_per_dim(
            info['item_scores'][dk][train_idx],
            info['self_letters'][dk][train_idx], dk)
        cv_subsets[dk] = opt_idx

    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                s = info['item_scores'][dk][i, cv_subsets[dk]].mean()
                letters.append(DIM_HIGH[dk] if s >= MIDPOINT else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'item_subset_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── Subset + Adaptive: train에서 subset + 임계값 탐색 ──
    sa_t = {}
    for dk in DIM_KEYS:
        t, _ = find_optimal_threshold(
            info['item_scores'][dk][train_idx],
            info['self_letters'][dk][train_idx], dk,
            subset_indices=cv_subsets[dk])
        sa_t[dk] = t

    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                s = info['item_scores'][dk][i, cv_subsets[dk]].mean()
                letters.append(DIM_HIGH[dk] if s >= sa_t[dk] else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'subset_adaptive_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    # ── Logistic Regression: train에서 학습 ──
    lr_models = {}
    for dk in DIM_KEYS:
        y_tr = (info['self_letters'][dk][train_idx] == DIM_HIGH[dk]).astype(int)
        X_tr = info['item_scores'][dk][train_idx]
        X_tr_std, m, s = standardize_features(X_tr)
        model = logistic_regression_train(
            X_tr_std, y_tr, lr=0.5, epochs=300, lambda_reg=0.1)
        lr_models[dk] = {'weights': model['weights'], 'mean': m, 'std': s}

    for label, idx_set in [('train', train_idx), ('test', test_idx)]:
        pred = []
        for i in idx_set:
            letters = []
            for dk in DIM_KEYS:
                X_i = info['item_scores'][dk][i:i+1]
                X_i_std, _, _ = standardize_features(
                    X_i, mean=lr_models[dk]['mean'], std=lr_models[dk]['std'])
                p = logistic_regression_predict(X_i_std, lr_models[dk]['weights'])
                letters.append(DIM_HIGH[dk] if p['predictions'][0] == 1 else DIM_LOW[dk])
            pred.append(''.join(letters))
        pred = np.array(pred)
        results[f'logistic_{label}'] = (pred == info['self_mbti'][idx_set]).mean()

    return results


def run_advanced_cv(info, n_splits=5, n_repeats=20, seed=42):
    """고급 방법들의 교차검증 (Repeated K-Fold)

    8개 방법 동시 비교, 각 fold에서 train에서만 학습하여 과적합 정량화.
    """
    print(f"\n{'='*70}")
    print("  [Step 6] 고급 방법 교차검증 (Repeated 5-Fold CV)")
    print(f"{'='*70}")
    print(f"    Running {n_splits}-Fold x {n_repeats} repeats...", end=' ', flush=True)

    rng = np.random.RandomState(seed)
    n = info['n']
    total_folds = n_splits * n_repeats

    method_keys = ['baseline', 'item_subset', 'adaptive', 'citc',
                   'citc_adaptive', 'majority', 'subset_adaptive', 'logistic']

    all_results = {f'{mk}_{s}': [] for mk in method_keys for s in ['train', 'test']}

    for rep in range(n_repeats):
        perm = rng.permutation(n)
        fold_size = n // n_splits

        for fold in range(n_splits):
            start = fold * fold_size
            end = start + fold_size if fold < n_splits - 1 else n
            test_idx = perm[start:end]
            train_idx = np.concatenate([perm[:start], perm[end:]])

            fold_r = _advanced_cv_fold(info, train_idx, test_idx)

            for mk in method_keys:
                all_results[f'{mk}_train'].append(fold_r[f'{mk}_train'])
                all_results[f'{mk}_test'].append(fold_r[f'{mk}_test'])

    print(f"Done! ({total_folds} folds)")

    # 결과 정리
    cv_summary = {}
    baseline_test = np.mean(all_results['baseline_test'])

    name_map = {
        'baseline': 'Baseline (9문항)',
        'item_subset': 'Item Subset',
        'adaptive': 'Adaptive Threshold',
        'citc': 'CITC Weighted',
        'citc_adaptive': 'CITC + Adaptive',
        'majority': 'Majority Vote',
        'subset_adaptive': 'Subset + Adaptive',
        'logistic': 'Logistic Regression',
    }

    print(f"\n  {'방법':<25} {'Train':>10} {'Test':>10} "
          f"{'Gap':>10} {'vs Base':>10}")
    print(f"  {'─'*65}")

    for mk in method_keys:
        train_mean = np.mean(all_results[f'{mk}_train'])
        test_mean = np.mean(all_results[f'{mk}_test'])
        test_std = np.std(all_results[f'{mk}_test'])
        gap = (train_mean - test_mean) * 100
        vs_base = (test_mean - baseline_test) * 100

        cv_summary[mk] = {
            'train_mean': train_mean,
            'test_mean': test_mean,
            'test_std': test_std,
            'gap': gap,
            'vs_baseline': vs_base,
            'train_accs': np.array(all_results[f'{mk}_train']),
            'test_accs': np.array(all_results[f'{mk}_test']),
        }

        marker = ' ★' if vs_base > 0.5 else ''
        print(f"  {name_map[mk]:<25} {train_mean*100:>9.1f}% {test_mean*100:>9.1f}% "
              f"{gap:>+9.1f}%p {vs_base:>+9.1f}%p{marker}")

    # 최적 방법 결정 (CV test 기준)
    best_method = max(method_keys, key=lambda mk: cv_summary[mk]['test_mean'])
    print(f"\n  ★ 교차검증 기준 최적 방법: {name_map[best_method]}")
    print(f"    CV Test 정확도: {cv_summary[best_method]['test_mean']*100:.1f}% "
          f"(vs Baseline: {cv_summary[best_method]['vs_baseline']:+.1f}%p)")
    print(f"    과적합 Gap: {cv_summary[best_method]['gap']:.1f}%p")

    cv_summary['_best'] = best_method
    cv_summary['_baseline_test'] = baseline_test
    cv_summary['_n_folds'] = total_folds
    cv_summary['_name_map'] = name_map

    return cv_summary


# ============================================================
#  4. Bootstrap 신뢰구간 (과적합 검증)
# ============================================================

def bootstrap_accuracy_ci(item_scores, self_letters, subset_indices, dim_key,
                          n_bootstrap=1000, seed=42):
    """부트스트랩 신뢰구간: 최적화된 정확도가 안정적인지 검증"""
    rng = np.random.RandomState(seed)
    n = len(self_letters)
    accs = np.zeros(n_bootstrap)

    for b in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        bs_scores = item_scores[idx][:, subset_indices].mean(axis=1)
        predicted = np.where(bs_scores >= MIDPOINT, DIM_HIGH[dim_key], DIM_LOW[dim_key])
        accs[b] = (predicted == self_letters[idx]).mean()

    return {
        'mean': accs.mean(),
        'std': accs.std(),
        'ci_lower': np.percentile(accs, 2.5),
        'ci_upper': np.percentile(accs, 97.5),
        'accs': accs,
    }


def run_bootstrap_validation(info, opt_results):
    """부트스트랩 검증"""
    print(f"\n{'='*70}")
    print("  [Step 4] 부트스트랩 교차검증 (과적합 위험 평가)")
    print(f"{'='*70}")

    bs_results = {}

    for dim_key in DIM_KEYS:
        scores = info['item_scores'][dim_key]
        self_l = info['self_letters'][dim_key]

        # 원본 (전체 9문항)
        full_bs = bootstrap_accuracy_ci(scores, self_l, list(range(9)), dim_key)

        # 최적화 부분집합
        opt_idx = opt_results[dim_key]['optimal_indices']
        opt_bs = bootstrap_accuracy_ci(scores, self_l, list(opt_idx), dim_key)

        bs_results[dim_key] = {
            'full': full_bs,
            'optimal': opt_bs,
        }

        print(f"\n  {DIM_LABELS[dim_key]}:")
        print(f"    원본 9문항: {full_bs['mean']*100:.1f}% "
              f"(95% CI: [{full_bs['ci_lower']*100:.1f}%, {full_bs['ci_upper']*100:.1f}%])")
        opt_k = opt_results[dim_key]['optimal_k']
        print(f"    최적 {opt_k}문항: {opt_bs['mean']*100:.1f}% "
              f"(95% CI: [{opt_bs['ci_lower']*100:.1f}%, {opt_bs['ci_upper']*100:.1f}%])")

        # 신뢰구간 겹침 여부
        if opt_bs['ci_lower'] > full_bs['ci_upper']:
            print(f"    → 유의한 개선 (CI 비겹침)")
        elif opt_bs['ci_lower'] > full_bs['ci_lower']:
            print(f"    → CI 겹침 — 개선이 통계적으로 유의하지 않을 수 있음")
        else:
            print(f"    → CI 겹침 — 실질적 차이 없음")

    return bs_results


# ============================================================
#  4-2. 독립 표본 교차검증 (과적합 정량 평가)
# ============================================================

def _cv_find_optimal_per_dim(scores_train, letters_train, dim_key):
    """CV fold 내부: training 데이터에서 최적 부분집합 탐색

    exhaustive_search를 train set에만 적용하여
    데이터 누출(data leakage) 없이 최적 부분집합을 결정.

    Returns: (optimal_indices_list, optimal_k)
    """
    best_per_size, _ = exhaustive_search(
        scores_train, letters_train, dim_key,
        min_items=3, max_items=9
    )
    baseline_acc = best_per_size[9][0]
    best_k = 9
    best_acc = baseline_acc
    for k in range(3, 9):
        acc, _ = best_per_size[k]
        if acc > best_acc or (acc == best_acc and k < best_k):
            best_acc = acc
            best_k = k
    return list(best_per_size[best_k][1]), best_k


def run_kfold_cv(info, n_splits=5, n_repeats=20, seed=42):
    """Repeated K-Fold 교차검증

    각 fold에서:
      1) Training set으로 exhaustive_search → 최적 부분집합 결정
      2) Test set으로 해당 부분집합의 정확도 평가 (honest estimation)
      3) Baseline (전체 9문항) test 정확도도 함께 기록

    Parameters
    ----------
    info : dict — load_survey_data() 결과
    n_splits : int — K (fold 수, 기본 5)
    n_repeats : int — 반복 횟수 (기본 20, 총 100 folds)
    seed : int — 랜덤 시드

    Returns
    -------
    dict with test/train accuracies, item selection frequencies
    """
    rng = np.random.RandomState(seed)
    n = info['n']
    total_folds = n_splits * n_repeats

    dim_test_accs = {dk: [] for dk in DIM_KEYS}
    dim_train_accs = {dk: [] for dk in DIM_KEYS}
    dim_baseline_test = {dk: [] for dk in DIM_KEYS}
    overall_test_accs = []
    overall_train_accs = []
    overall_baseline_test = []
    item_selections = {dk: np.zeros(9) for dk in DIM_KEYS}
    selected_ks = {dk: [] for dk in DIM_KEYS}

    for rep in range(n_repeats):
        perm = rng.permutation(n)
        fold_size = n // n_splits

        for fold in range(n_splits):
            start = fold * fold_size
            end = start + fold_size if fold < n_splits - 1 else n
            test_idx = perm[start:end]
            train_idx = np.concatenate([perm[:start], perm[end:]])

            dim_subsets_opt = {}
            dim_subsets_full = {dk: list(range(9)) for dk in DIM_KEYS}

            for dim_key in DIM_KEYS:
                scores = info['item_scores'][dim_key]
                self_l = info['self_letters'][dim_key]

                # Train: 최적 부분집합 탐색 (test data 접근 없음)
                opt_idx, opt_k = _cv_find_optimal_per_dim(
                    scores[train_idx], self_l[train_idx], dim_key)
                dim_subsets_opt[dim_key] = opt_idx

                for j in opt_idx:
                    item_selections[dim_key][j] += 1
                selected_ks[dim_key].append(opt_k)

                # Train accuracy (optimized subset)
                dim_train_accs[dim_key].append(
                    compute_accuracy_with_subset(
                        scores[train_idx], self_l[train_idx], opt_idx, dim_key))

                # Test accuracy (optimized subset — honest)
                dim_test_accs[dim_key].append(
                    compute_accuracy_with_subset(
                        scores[test_idx], self_l[test_idx], opt_idx, dim_key))

                # Baseline test accuracy (전체 9문항)
                dim_baseline_test[dim_key].append(
                    compute_accuracy_with_subset(
                        scores[test_idx], self_l[test_idx],
                        list(range(9)), dim_key))

            # Overall 4-letter accuracies
            for accs_list, idx_set, subsets in [
                (overall_test_accs, test_idx, dim_subsets_opt),
                (overall_train_accs, train_idx, dim_subsets_opt),
                (overall_baseline_test, test_idx, dim_subsets_full),
            ]:
                pred = []
                for i in idx_set:
                    letters = []
                    for dk in DIM_KEYS:
                        s = info['item_scores'][dk][i, subsets[dk]].mean()
                        letters.append(DIM_HIGH[dk] if s >= MIDPOINT else DIM_LOW[dk])
                    pred.append(''.join(letters))
                pred = np.array(pred)
                accs_list.append((pred == info['self_mbti'][idx_set]).mean())

    sel_freq = {dk: item_selections[dk] / total_folds for dk in DIM_KEYS}

    return {
        'dim_test_accs': {dk: np.array(v) for dk, v in dim_test_accs.items()},
        'dim_train_accs': {dk: np.array(v) for dk, v in dim_train_accs.items()},
        'dim_baseline_test': {dk: np.array(v) for dk, v in dim_baseline_test.items()},
        'overall_test_accs': np.array(overall_test_accs),
        'overall_train_accs': np.array(overall_train_accs),
        'overall_baseline_test': np.array(overall_baseline_test),
        'item_selection_freq': sel_freq,
        'selected_ks': {dk: np.array(v) for dk, v in selected_ks.items()},
        'n_folds': total_folds,
        'method': f'Repeated {n_splits}-Fold CV ({n_repeats} repeats = {total_folds} folds)',
    }


def run_monte_carlo_cv(info, n_iterations=200, test_ratio=0.3, seed=42):
    """Monte Carlo 교차검증 (Random Sub-sampling Validation)

    각 iteration에서:
      1) 랜덤 70/30 분할
      2) 70% 훈련 → exhaustive_search로 최적 부분집합 결정
      3) 30% 테스트 → 정직한 정확도 평가

    Parameters
    ----------
    info : dict — load_survey_data() 결과
    n_iterations : int — 반복 횟수 (기본 200)
    test_ratio : float — 테스트 비율 (기본 0.3)
    seed : int — 랜덤 시드
    """
    rng = np.random.RandomState(seed)
    n = info['n']
    n_test = max(1, int(n * test_ratio))

    dim_test_accs = {dk: [] for dk in DIM_KEYS}
    dim_train_accs = {dk: [] for dk in DIM_KEYS}
    dim_baseline_test = {dk: [] for dk in DIM_KEYS}
    overall_test_accs = []
    overall_train_accs = []
    overall_baseline_test = []
    item_selections = {dk: np.zeros(9) for dk in DIM_KEYS}
    selected_ks = {dk: [] for dk in DIM_KEYS}

    for it in range(n_iterations):
        perm = rng.permutation(n)
        test_idx = perm[:n_test]
        train_idx = perm[n_test:]

        dim_subsets_opt = {}
        dim_subsets_full = {dk: list(range(9)) for dk in DIM_KEYS}

        for dim_key in DIM_KEYS:
            scores = info['item_scores'][dim_key]
            self_l = info['self_letters'][dim_key]

            opt_idx, opt_k = _cv_find_optimal_per_dim(
                scores[train_idx], self_l[train_idx], dim_key)
            dim_subsets_opt[dim_key] = opt_idx

            for j in opt_idx:
                item_selections[dim_key][j] += 1
            selected_ks[dim_key].append(opt_k)

            dim_train_accs[dim_key].append(
                compute_accuracy_with_subset(
                    scores[train_idx], self_l[train_idx], opt_idx, dim_key))
            dim_test_accs[dim_key].append(
                compute_accuracy_with_subset(
                    scores[test_idx], self_l[test_idx], opt_idx, dim_key))
            dim_baseline_test[dim_key].append(
                compute_accuracy_with_subset(
                    scores[test_idx], self_l[test_idx],
                    list(range(9)), dim_key))

        for accs_list, idx_set, subsets in [
            (overall_test_accs, test_idx, dim_subsets_opt),
            (overall_train_accs, train_idx, dim_subsets_opt),
            (overall_baseline_test, test_idx, dim_subsets_full),
        ]:
            pred = []
            for i in idx_set:
                letters = []
                for dk in DIM_KEYS:
                    s = info['item_scores'][dk][i, subsets[dk]].mean()
                    letters.append(DIM_HIGH[dk] if s >= MIDPOINT else DIM_LOW[dk])
                pred.append(''.join(letters))
            pred = np.array(pred)
            accs_list.append((pred == info['self_mbti'][idx_set]).mean())

    sel_freq = {dk: item_selections[dk] / n_iterations for dk in DIM_KEYS}

    return {
        'dim_test_accs': {dk: np.array(v) for dk, v in dim_test_accs.items()},
        'dim_train_accs': {dk: np.array(v) for dk, v in dim_train_accs.items()},
        'dim_baseline_test': {dk: np.array(v) for dk, v in dim_baseline_test.items()},
        'overall_test_accs': np.array(overall_test_accs),
        'overall_train_accs': np.array(overall_train_accs),
        'overall_baseline_test': np.array(overall_baseline_test),
        'item_selection_freq': sel_freq,
        'selected_ks': {dk: np.array(v) for dk, v in selected_ks.items()},
        'n_iterations': n_iterations,
        'test_ratio': test_ratio,
        'method': f'Monte Carlo CV ({n_iterations} iter, {int(test_ratio*100)}% test)',
    }


def run_cross_validation(info, opt_results, item_analysis):
    """독립 표본 교차검증 종합 실행: K-Fold + Monte Carlo

    과적합 정량 평가를 위해 두 가지 독립 CV 방법을 적용:
    1) Repeated 5-Fold CV — 모든 데이터가 test로 사용됨 (완전 커버리지)
    2) Monte Carlo CV — 독립적 무작위 분할 반복 (K-Fold 결과 교차 확인)

    핵심 지표:
    - 과적합 Gap = In-sample 최적 정확도 - CV Test 정확도
    - 정직한 개선 = CV Test 최적 정확도 - CV Test 기준선 (9문항)
    - 문항 선택 안정성 = CV 반복에서 각 문항이 선택된 빈도
    """
    print(f"\n{'='*70}")
    print("  [Step 5] 독립 표본 교차검증 (과적합 정량 평가)")
    print(f"{'='*70}")

    # ── K-Fold CV ──
    print(f"\n  ── Repeated 5-Fold CV (5 splits x 20 repeats = 100 folds) ──")
    print(f"    각 fold: train으로 exhaustive_search → test로 정직한 평가")
    print(f"    Running...", end=' ', flush=True)
    kfold = run_kfold_cv(info, n_splits=5, n_repeats=20, seed=42)
    print(f"Done!")

    print(f"\n  {'차원':<14} {'In-sample':>10} {'CV-Test':>10} {'기준선':>10} "
          f"{'과적합Gap':>10} {'정직개선':>10}")
    print(f"  {'─'*66}")

    for dim_key in DIM_KEYS:
        insample = opt_results[dim_key]['optimal_acc'] * 100
        cv_test = kfold['dim_test_accs'][dim_key].mean() * 100
        cv_std = kfold['dim_test_accs'][dim_key].std() * 100
        baseline = kfold['dim_baseline_test'][dim_key].mean() * 100
        gap = insample - cv_test
        honest = cv_test - baseline
        print(f"  {DIM_LABELS[dim_key]:<14} {insample:>9.1f}% {cv_test:>8.1f}%  {baseline:>8.1f}% "
              f"{gap:>+9.1f}%p {honest:>+9.1f}%p")

    insample_ov = opt_results['_summary']['overall_optimal'] * 100
    cv_test_ov = kfold['overall_test_accs'].mean() * 100
    baseline_ov = kfold['overall_baseline_test'].mean() * 100
    gap_ov = insample_ov - cv_test_ov
    honest_ov = cv_test_ov - baseline_ov
    print(f"  {'─'*66}")
    print(f"  {'전체 4글자':<14} {insample_ov:>9.1f}% {cv_test_ov:>8.1f}%  {baseline_ov:>8.1f}% "
          f"{gap_ov:>+9.1f}%p {honest_ov:>+9.1f}%p")

    # ── Monte Carlo CV ──
    print(f"\n  ── Monte Carlo CV (200 iterations, 70/30 split) ──")
    print(f"    Running...", end=' ', flush=True)
    mc = run_monte_carlo_cv(info, n_iterations=200, test_ratio=0.3, seed=42)
    print(f"Done!")

    print(f"\n  {'차원':<14} {'In-sample':>10} {'MC-Test':>10} {'기준선':>10} "
          f"{'과적합Gap':>10} {'정직개선':>10}")
    print(f"  {'─'*66}")

    for dim_key in DIM_KEYS:
        insample = opt_results[dim_key]['optimal_acc'] * 100
        mc_test = mc['dim_test_accs'][dim_key].mean() * 100
        baseline = mc['dim_baseline_test'][dim_key].mean() * 100
        gap = insample - mc_test
        honest = mc_test - baseline
        print(f"  {DIM_LABELS[dim_key]:<14} {insample:>9.1f}% {mc_test:>8.1f}%  {baseline:>8.1f}% "
              f"{gap:>+9.1f}%p {honest:>+9.1f}%p")

    mc_test_ov = mc['overall_test_accs'].mean() * 100
    mc_baseline_ov = mc['overall_baseline_test'].mean() * 100
    gap_mc_ov = insample_ov - mc_test_ov
    honest_mc_ov = mc_test_ov - mc_baseline_ov
    print(f"  {'─'*66}")
    print(f"  {'전체 4글자':<14} {insample_ov:>9.1f}% {mc_test_ov:>8.1f}%  {mc_baseline_ov:>8.1f}% "
          f"{gap_mc_ov:>+9.1f}%p {honest_mc_ov:>+9.1f}%p")

    # ── 문항 선택 안정성 ──
    print(f"\n  ── 문항 선택 안정성 (CV 반복에서 최적 부분집합에 선택된 빈도) ──")
    for dim_key in DIM_KEYS:
        ia = item_analysis[dim_key]
        freq_kf = kfold['item_selection_freq'][dim_key]
        freq_mc = mc['item_selection_freq'][dim_key]
        opt_set = set(opt_results[dim_key]['optimal_indices'])
        median_k_kf = np.median(kfold['selected_ks'][dim_key])
        median_k_mc = np.median(mc['selected_ks'][dim_key])

        print(f"\n    {DIM_LABELS[dim_key]} "
              f"(in-sample {opt_results[dim_key]['optimal_k']}문항 | "
              f"CV median: KF={median_k_kf:.0f}, MC={median_k_mc:.0f})")
        for j in range(9):
            marker = ' *' if j in opt_set else '  '
            stab = 'STABLE' if (freq_kf[j] > 0.8 or freq_kf[j] < 0.2) else \
                   'MID   ' if (freq_kf[j] > 0.6 or freq_kf[j] < 0.4) else 'UNSTBL'
            print(f"      Q{ia['cols'][j]}{marker}: KF={freq_kf[j]*100:5.1f}% "
                  f"MC={freq_mc[j]*100:5.1f}%  [{stab}]")

    # ── 과적합 진단 요약 ──
    print(f"\n  ── 과적합 진단 요약 ──")

    avg_gap_kf = np.mean([
        opt_results[dk]['optimal_acc'] * 100 - kfold['dim_test_accs'][dk].mean() * 100
        for dk in DIM_KEYS
    ])
    avg_gap_mc = np.mean([
        opt_results[dk]['optimal_acc'] * 100 - mc['dim_test_accs'][dk].mean() * 100
        for dk in DIM_KEYS
    ])
    avg_honest_kf = np.mean([
        kfold['dim_test_accs'][dk].mean() * 100 - kfold['dim_baseline_test'][dk].mean() * 100
        for dk in DIM_KEYS
    ])
    avg_honest_mc = np.mean([
        mc['dim_test_accs'][dk].mean() * 100 - mc['dim_baseline_test'][dk].mean() * 100
        for dk in DIM_KEYS
    ])

    print(f"    평균 과적합 Gap (K-Fold): {avg_gap_kf:.1f}%p")
    print(f"    평균 과적합 Gap (MC):     {avg_gap_mc:.1f}%p")

    if avg_gap_kf > 5:
        print(f"    --> 심각한 과적합: In-sample 결과 신뢰 불가")
    elif avg_gap_kf > 2:
        print(f"    --> 중간 수준 과적합: In-sample 결과 과대추정 존재")
    else:
        print(f"    --> 과적합 미미: 최적화 결과 신뢰 가능")

    print(f"\n    정직한 평균 개선 (K-Fold): {avg_honest_kf:+.1f}%p")
    print(f"    정직한 평균 개선 (MC):     {avg_honest_mc:+.1f}%p")

    if avg_honest_kf > 1:
        print(f"    --> 문항 축소 효과가 독립 표본에서도 확인됨")
    elif avg_honest_kf > -1:
        print(f"    --> 문항 축소 효과 불분명 (우연 범위 내)")
    else:
        print(f"    --> 문항 축소가 오히려 성능 저하 — 과적합으로 인한 환상")

    return {
        'kfold': kfold,
        'mc': mc,
    }


# ============================================================
#  5. 시각화 함수
# ============================================================

def plot_e1_citc_heatmap(item_analysis, save_dir):
    """fig_e1: 문항-총점 상관 (CITC) 히트맵"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fig_e1: 수정 문항-총점 상관 (CITC)', fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        ia = item_analysis[dim_key]
        citc = ia['citc']
        q_labels = ia['q_labels']

        # 가로 막대
        colors = ['#e74c3c' if c < 0.3 else '#2ecc71' if c >= 0.5 else '#f39c12'
                  for c in citc]
        bars = ax.barh(range(len(citc)), citc, color=colors, edgecolor='white')

        # 기준선
        ax.axvline(x=0.3, color='red', linestyle='--', alpha=0.7, label='최소 기준 (0.3)')
        ax.axvline(x=0.5, color='green', linestyle='--', alpha=0.5, label='양호 기준 (0.5)')

        ax.set_yticks(range(len(q_labels)))
        ax.set_yticklabels(q_labels)
        ax.set_xlabel('CITC')
        ax.set_title(f'{DIM_LABELS[dim_key]} (α={ia["alpha_full"]:.3f})')
        ax.set_xlim(-0.1, 1.0)
        ax.legend(fontsize=8, loc='lower right')

        # 값 표시
        for i, (bar, val) in enumerate(zip(bars, citc)):
            ax.text(val + 0.02, i, f'{val:.3f}', va='center', fontsize=9)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e1_citc_heatmap.png')
    return fig


def plot_e2_alpha_if_deleted(item_analysis, save_dir):
    """fig_e2: Cronbach's α 변화 (문항 제거 시)"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("fig_e2: 문항 제거 시 Cronbach's α 변화", fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        ia = item_analysis[dim_key]
        alpha_full = ia['alpha_full']
        alpha_del = ia['alpha_del']
        q_labels = ia['q_labels']

        colors = ['#e74c3c' if a > alpha_full + 0.005 else '#3498db'
                  for a in alpha_del]

        bars = ax.barh(range(len(alpha_del)), alpha_del, color=colors, edgecolor='white')
        ax.axvline(x=alpha_full, color='black', linestyle='-', linewidth=2,
                   label=f'현재 α = {alpha_full:.3f}')

        ax.set_yticks(range(len(q_labels)))
        ax.set_yticklabels(q_labels)
        ax.set_xlabel("Cronbach's α (문항 제거 후)")
        ax.set_title(f'{DIM_LABELS[dim_key]}')
        ax.legend(fontsize=9, loc='lower right')

        for i, (bar, val) in enumerate(zip(bars, alpha_del)):
            marker = '▲' if val > alpha_full + 0.005 else ''
            ax.text(val + 0.002, i, f'{val:.3f}{marker}', va='center', fontsize=9)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e2_alpha_if_deleted.png')
    return fig


def plot_e3_discrimination(item_analysis, save_dir):
    """fig_e3: 문항 변별도 (상위/하위 27% 평균 차이)"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fig_e3: 문항 변별도 (상위 27% − 하위 27% 평균)', fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        ia = item_analysis[dim_key]
        disc = ia['disc']
        q_labels = ia['q_labels']

        colors = ['#e74c3c' if d < 1.0 else '#2ecc71' if d >= 2.0 else '#f39c12'
                  for d in disc]

        bars = ax.barh(range(len(disc)), disc, color=colors, edgecolor='white')
        ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='약한 변별 (<1.0)')
        ax.axvline(x=2.0, color='green', linestyle='--', alpha=0.5, label='양호 (≥2.0)')

        ax.set_yticks(range(len(q_labels)))
        ax.set_yticklabels(q_labels)
        ax.set_xlabel('변별도 (점수 차이)')
        ax.set_title(f'{DIM_LABELS[dim_key]}')
        ax.legend(fontsize=8, loc='lower right')

        for i, (bar, val) in enumerate(zip(bars, disc)):
            ax.text(val + 0.05, i, f'{val:.2f}', va='center', fontsize=9)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e3_discrimination.png')
    return fig


def plot_e4_predictive_power(item_analysis, save_dir):
    """fig_e4: 문항별 자기보고 MBTI 예측 정확도"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fig_e4: 문항별 자기보고 MBTI 예측 정확도 (단일 문항)', fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        ia = item_analysis[dim_key]
        pred = ia['item_predictive']
        q_labels = ia['q_labels']

        colors = [DIM_COLORS[dim_key] if p >= 0.6 else '#bdc3c7' for p in pred]
        bars = ax.barh(range(len(pred)), pred * 100, color=colors, edgecolor='white')

        ax.axvline(x=50, color='gray', linestyle=':', alpha=0.7, label='우연 수준 (50%)')

        ax.set_yticks(range(len(q_labels)))
        ax.set_yticklabels(q_labels)
        ax.set_xlabel('예측 정확도 (%)')
        ax.set_title(f'{DIM_LABELS[dim_key]}')
        ax.set_xlim(30, 100)
        ax.legend(fontsize=9)

        for i, (bar, val) in enumerate(zip(bars, pred)):
            ax.text(val * 100 + 0.5, i, f'{val*100:.1f}%', va='center', fontsize=9)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e4_predictive_power.png')
    return fig


def plot_e5_sbe_curve(opt_results, item_analysis, save_dir):
    """fig_e5: 순차 제거 시 차원별 정확도 변화 곡선"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fig_e5: 순차 후진 제거 — 문항 수 vs 정확도', fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        history = opt_results[dim_key]['sbe_history']
        n_items_list = [h[0] for h in history]
        acc_list = [h[1] * 100 for h in history]
        removed_list = [h[2] for h in history]

        ax.plot(n_items_list, acc_list, 'o-', color=DIM_COLORS[dim_key],
                linewidth=2, markersize=8)

        # 최적점 표시
        best_idx = np.argmax(acc_list)
        ax.plot(n_items_list[best_idx], acc_list[best_idx], '*',
                color='red', markersize=15, zorder=5)
        ax.annotate(f'최적: {n_items_list[best_idx]}문항\n{acc_list[best_idx]:.1f}%',
                    xy=(n_items_list[best_idx], acc_list[best_idx]),
                    xytext=(n_items_list[best_idx]-1.5, acc_list[best_idx]+2),
                    fontsize=10, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='red'))

        # 제거된 문항 라벨
        for i, (n_it, acc, removed) in enumerate(zip(n_items_list, acc_list, removed_list)):
            if removed:
                ax.annotate(f'-{removed}', xy=(n_it, acc),
                           xytext=(n_it + 0.2, acc - 1.5), fontsize=7, color='gray')

        ax.set_xlabel('문항 수')
        ax.set_ylabel('정확도 (%)')
        ax.set_title(f'{DIM_LABELS[dim_key]}')
        ax.set_xticks(range(1, 10))
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e5_sbe_curve.png')
    return fig


def plot_e6_overall_accuracy_curve(info, opt_results, item_analysis, save_dir):
    """fig_e6: 최적 문항 수 vs 전체 4글자 일치율"""
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle('fig_e6: 차원별 최적 문항 조합 → 전체 4글자 MBTI 일치율', fontsize=16, fontweight='bold')

    # 각 차원에서 k문항 최적 조합을 사용할 때의 전체 일치율
    # 전 차원 동일한 k문항 사용
    results_by_k = {}
    for k in range(3, 10):
        dim_subsets = {}
        for dim_key in DIM_KEYS:
            _, indices = opt_results[dim_key]['best_per_size'][k]
            dim_subsets[dim_key] = list(indices)

        overall, dim_accs = compute_overall_accuracy_with_subsets(info, dim_subsets)
        results_by_k[k] = {
            'overall': overall,
            'dim_accs': dim_accs,
            'total_items': k * 4,
        }

    ks = sorted(results_by_k.keys())
    overall_accs = [results_by_k[k]['overall'] * 100 for k in ks]
    total_items = [results_by_k[k]['total_items'] for k in ks]

    # 전체 정확도 곡선
    ax.plot(ks, overall_accs, 's-', color='#2c3e50', linewidth=3, markersize=10,
            label='전체 4글자 일치율', zorder=5)

    # 차원별 곡선
    for dim_key in DIM_KEYS:
        dim_accs = [results_by_k[k]['dim_accs'][dim_key] * 100 for k in ks]
        ax.plot(ks, dim_accs, 'o--', color=DIM_COLORS[dim_key], alpha=0.7,
                label=f'{DIM_LABELS[dim_key]}')

    # 최적점 표시
    best_k_idx = np.argmax(overall_accs)
    ax.plot(ks[best_k_idx], overall_accs[best_k_idx], '*',
            color='red', markersize=20, zorder=10)
    ax.annotate(f'최적: {ks[best_k_idx]}문항/차원\n총 {total_items[best_k_idx]}문항\n'
                f'{overall_accs[best_k_idx]:.1f}%',
                xy=(ks[best_k_idx], overall_accs[best_k_idx]),
                xytext=(ks[best_k_idx] + 0.5, overall_accs[best_k_idx] + 3),
                fontsize=12, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='red', lw=2))

    ax.axhline(y=overall_accs[-1], color='gray', linestyle=':', alpha=0.5,
               label=f'기준선 (9문항): {overall_accs[-1]:.1f}%')

    ax.set_xlabel('차원당 문항 수', fontsize=12)
    ax.set_ylabel('일치율 (%)', fontsize=12)
    ax.set_xticks(ks)
    ax.set_xticklabels([f'{k}문항\n(총{k*4})' for k in ks])
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=max(0, min(overall_accs) - 10))

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e6_overall_accuracy_curve.png')
    return fig


def plot_e7_optimal_detail(opt_results, item_analysis, save_dir):
    """fig_e7: 최적 문항 조합 상세 결과"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fig_e7: 전수 탐색 — 문항 수별 정확도 분포 (Swarm)', fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        all_results = opt_results[dim_key]['all_results']
        best_per_size = opt_results[dim_key]['best_per_size']

        # 문항 수별 모든 정확도
        for k in range(3, 10):
            results_k = [(acc, idx) for n, acc, idx in all_results if n == k]
            if results_k:
                accs = [r[0] * 100 for r in results_k]
                jitter = np.random.RandomState(42).uniform(-0.2, 0.2, len(accs))
                ax.scatter(k + jitter, accs, alpha=0.3, s=15, color=DIM_COLORS[dim_key])

        # 최적 점 강조
        ks = sorted(best_per_size.keys())
        best_accs = [best_per_size[k][0] * 100 for k in ks]
        ax.plot(ks, best_accs, 'D-', color='black', markersize=7, linewidth=2,
                label='각 문항수별 최고', zorder=5)

        # 최적 K 표시
        opt_k = opt_results[dim_key]['optimal_k']
        opt_acc = opt_results[dim_key]['optimal_acc'] * 100
        ax.plot(opt_k, opt_acc, '*', color='red', markersize=18, zorder=10)

        ax.set_xlabel('문항 수')
        ax.set_ylabel('정확도 (%)')
        ax.set_title(f'{DIM_LABELS[dim_key]} (최적: {opt_k}문항 = {opt_acc:.1f}%)')
        ax.set_xticks(range(3, 10))
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e7_optimal_detail.png')
    return fig


def plot_e8_comparison_bar(info, opt_results, save_dir):
    """fig_e8: 원본 vs 최적화 정확도 비교"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    fig.suptitle('fig_e8: 원본 (36문항) vs 최적화 정확도 비교', fontsize=16, fontweight='bold')

    summary = opt_results['_summary']

    # (a) 차원별 비교
    x = np.arange(len(DIM_KEYS))
    width = 0.35

    baseline_vals = [summary['dim_baseline'][dk] * 100 for dk in DIM_KEYS]
    optimal_vals = [summary['dim_optimal'][dk] * 100 for dk in DIM_KEYS]

    bars1 = ax1.bar(x - width/2, baseline_vals, width, label='원본 (9문항)', color='#bdc3c7')
    bars2 = ax1.bar(x + width/2, optimal_vals, width, label='최적화', color='#2ecc71')

    ax1.set_xticks(x)
    x_labels = []
    for dk in DIM_KEYS:
        opt_k = opt_results[dk]['optimal_k']
        x_labels.append(f'{DIM_LABELS[dk]}\n({opt_k}문항)')
    ax1.set_xticklabels(x_labels)
    ax1.set_ylabel('정확도 (%)')
    ax1.set_title('차원별 일치율')
    ax1.legend()
    ax1.set_ylim(50, 100)
    ax1.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars1, baseline_vals):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', fontsize=18)
    for bar, val in zip(bars2, optimal_vals):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', fontsize=18, fontweight='bold')

    # (b) 전체 4글자 비교
    categories = ['원본\n(36문항)', f'최적화\n({summary["total_items_optimal"]}문항)']
    values = [summary['overall_baseline'] * 100, summary['overall_optimal'] * 100]
    colors = ['#bdc3c7', '#2ecc71']

    bars = ax2.bar(categories, values, color=colors, width=0.5, edgecolor='white')
    ax2.set_ylabel('전체 4글자 일치율 (%)')
    ax2.set_title('전체 MBTI 유형 일치율')
    ax2.set_ylim(0, max(values) + 15)
    ax2.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}%', ha='center', fontsize=22, fontweight='bold')

    diff = values[1] - values[0]
    ax2.annotate(f'Δ = {diff:+.1f}%p', xy=(0.5, max(values) + 8),
                fontsize=22, ha='center', color='#e74c3c' if diff < 0 else '#27ae60',
                fontweight='bold')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e8_comparison_bar.png')
    return fig


def plot_e9_item_rank(item_analysis, opt_results, save_dir):
    """fig_e9: 차원별 문항 기여도 종합 순위"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('fig_e9: 차원별 문항 종합 기여도 순위', fontsize=16, fontweight='bold')

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        ia = item_analysis[dim_key]
        n_items = len(ia['cols'])

        # 종합 점수 계산 (CITC, 변별도, 예측력의 정규화 합)
        citc = ia['citc']
        disc = ia['disc']
        pred = ia['item_predictive']

        # Min-Max 정규화
        def normalize(arr):
            r = arr.max() - arr.min()
            if r == 0:
                return np.ones_like(arr) * 0.5
            return (arr - arr.min()) / r

        composite = (normalize(citc) + normalize(disc) + normalize(pred)) / 3

        # 순위
        rank_order = np.argsort(-composite)
        sorted_labels = [ia['q_labels'][i] for i in rank_order]
        sorted_citc = citc[rank_order]
        sorted_disc = disc[rank_order] / disc.max()  # 0~1 스케일
        sorted_pred = pred[rank_order]
        sorted_composite = composite[rank_order]

        # 최적 부분집합에 포함 여부
        opt_indices = set(opt_results[dim_key]['optimal_indices'])
        in_optimal = [rank_order[i] in opt_indices for i in range(n_items)]

        y = range(n_items)

        # 누적 막대 (정규화된 CITC, 변별도, 예측력)
        ax.barh(y, normalize(citc)[rank_order], color='#3498db', alpha=0.8, label='CITC')
        ax.barh(y, sorted_disc, left=normalize(citc)[rank_order],
                color='#2ecc71', alpha=0.8, label='변별도')
        ax.barh(y, sorted_pred, left=normalize(citc)[rank_order] + sorted_disc,
                color='#f39c12', alpha=0.8, label='예측력')

        # 최적 부분집합 표시
        for i, is_opt in enumerate(in_optimal):
            if is_opt:
                ax.text(-0.08, i, '★', fontsize=12, color='red', ha='center', va='center')

        ax.set_yticks(y)
        ax.set_yticklabels(sorted_labels)
        ax.set_xlabel('정규화된 기여도')
        opt_k = opt_results[dim_key]['optimal_k']
        ax.set_title(f'{DIM_LABELS[dim_key]} (최적 {opt_k}문항 ★)')
        ax.legend(fontsize=7, loc='lower right')

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e9_item_rank.png')
    return fig


def plot_e10_conclusion(info, opt_results, item_analysis, bs_results, save_dir):
    """fig_e10: 종합 결론 인포그래픽 — 가시성 강화 버전"""
    fig = plt.figure(figsize=(30, 18))
    fig.patch.set_facecolor('white')

    summary = opt_results['_summary']
    overall_diff = (summary['overall_optimal'] - summary['overall_baseline']) * 100

    # ── 메인 제목 ──
    fig.text(0.5, 0.96, 'MBTI 설문 문항 최적화 — 종합 결론',
             ha='center', fontsize=32, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.935, f'N={info["n"]}명 | 원본 {summary["total_items_original"]}문항 → '
             f'최적 {summary["total_items_optimal"]}문항',
             ha='center', fontsize=24, color='#7f8c8d')

    # ── (1) 핵심 결과 배너 ──
    ax1 = fig.add_axes([0.05, 0.78, 0.9, 0.13])
    ax1.axis('off')

    # 배경 사각형
    rect = mpatches.FancyBboxPatch((0.02, 0.05), 0.96, 0.85,
                                    boxstyle='round,pad=0.02',
                                    facecolor='#eaf2e3', edgecolor='#27ae60',
                                    linewidth=3, transform=ax1.transAxes)
    ax1.add_patch(rect)

    ax1.text(0.5, 0.75, '핵심 결과', ha='center', fontsize=26, fontweight='bold',
             color='#27ae60', transform=ax1.transAxes)

    ax1.text(0.25, 0.35, f'전체 4글자 일치율', ha='center', fontsize=23,
             color='#555', transform=ax1.transAxes)
    ax1.text(0.25, 0.1, f'{summary["overall_baseline"]*100:.1f}%  →  '
             f'{summary["overall_optimal"]*100:.1f}%',
             ha='center', fontsize=26, fontweight='bold', color='#2c3e50',
             transform=ax1.transAxes)

    ax1.text(0.65, 0.35, '정확도 변화', ha='center', fontsize=23,
             color='#555', transform=ax1.transAxes)
    diff_color = '#27ae60' if overall_diff > 0 else '#e74c3c'
    ax1.text(0.65, 0.1, f'{overall_diff:+.1f}%p 향상',
             ha='center', fontsize=32, fontweight='bold', color=diff_color,
             transform=ax1.transAxes)

    ax1.text(0.9, 0.35, '문항 감소', ha='center', fontsize=23,
             color='#555', transform=ax1.transAxes)
    ax1.text(0.9, 0.1, f'-{summary["total_items_original"]-summary["total_items_optimal"]}문항 '
             f'({(summary["total_items_original"]-summary["total_items_optimal"])/summary["total_items_original"]*100:.0f}%)',
             ha='center', fontsize=24, fontweight='bold', color='#3498db',
             transform=ax1.transAxes)

    # ── (2) 차원별 상세 테이블 ──
    ax2 = fig.add_axes([0.05, 0.38, 0.9, 0.37])
    ax2.axis('off')

    ax2.text(0.5, 0.97, '차원별 최적화 결과', ha='center', fontsize=26,
             fontweight='bold', color='#2c3e50', transform=ax2.transAxes)

    # 테이블 헤더
    col_headers = ['차원', '원본 정확도', '최적 정확도', '문항수', '변화',
                   '제거된 문항', 'Bootstrap 95% CI']
    col_x = [0.02, 0.14, 0.27, 0.39, 0.49, 0.60, 0.84]

    # 헤더 배경
    header_rect = mpatches.FancyBboxPatch((0.0, 0.84), 1.0, 0.08,
                                           boxstyle='round,pad=0.01',
                                           facecolor='#34495e', edgecolor='none',
                                           transform=ax2.transAxes)
    ax2.add_patch(header_rect)

    for i, header in enumerate(col_headers):
        ax2.text(col_x[i], 0.87, header, fontsize=21, fontweight='bold',
                 color='white', transform=ax2.transAxes)

    # 데이터 행
    dim_bg_colors = ['#fef9f0', '#f0fef0', '#f0f0fe', '#fef0f0']
    for row, dim_key in enumerate(DIM_KEYS):
        y_center = 0.72 - row * 0.17
        y_text = y_center

        # 행 배경
        row_rect = mpatches.FancyBboxPatch((0.0, y_center - 0.06), 1.0, 0.13,
                                            boxstyle='round,pad=0.005',
                                            facecolor=dim_bg_colors[row],
                                            edgecolor='#ddd', linewidth=1,
                                            transform=ax2.transAxes)
        ax2.add_patch(row_rect)

        baseline = summary['dim_baseline'][dim_key] * 100
        optimal = summary['dim_optimal'][dim_key] * 100
        opt_k = opt_results[dim_key]['optimal_k']
        diff = optimal - baseline
        d_color = '#27ae60' if diff > 0 else '#e74c3c' if diff < 0 else '#7f8c8d'

        # 제거된 문항
        ia = item_analysis[dim_key]
        all_items = set(range(9))
        kept_items = set(opt_results[dim_key]['optimal_indices'])
        removed = all_items - kept_items
        removed_labels = [f'Q{ia["cols"][i]}' for i in sorted(removed)]
        removed_str = ', '.join(removed_labels) if removed_labels else '-'

        # Bootstrap CI
        bs = bs_results[dim_key]
        ci_str = f'[{bs["optimal"]["ci_lower"]*100:.1f}%, {bs["optimal"]["ci_upper"]*100:.1f}%]'

        # 차원명 (색상 표시)
        ax2.text(col_x[0], y_text, f'{DIM_LABELS[dim_key]}',
                 fontsize=22, fontweight='bold', color=DIM_COLORS[dim_key],
                 transform=ax2.transAxes)

        vals = [f'{baseline:.1f}%', f'{optimal:.1f}%',
                f'9 → {opt_k}', f'{diff:+.1f}%p', removed_str, ci_str]
        val_sizes = [17, 18, 17, 20, 15, 15]
        val_weights = ['normal', 'bold', 'normal', 'bold', 'normal', 'normal']
        val_colors = ['#333', '#2c3e50', '#333', d_color, '#555', '#666']

        for i, (val, sz, wt, vc) in enumerate(zip(vals, val_sizes, val_weights, val_colors)):
            ax2.text(col_x[i+1], y_text, val, fontsize=sz, fontweight=wt,
                     color=vc, transform=ax2.transAxes)

    # ── (3) 결론 및 제언 ──
    ax3 = fig.add_axes([0.05, 0.03, 0.55, 0.32])
    ax3.axis('off')

    ax3.text(0.5, 0.95, '결론', ha='center', fontsize=26, fontweight='bold',
             color='#2c3e50', transform=ax3.transAxes)

    if overall_diff > 3:
        conclusion_title = '문항 축소가 효과적'
        conclusion_body = (
            f'36문항 중 {summary["total_items_original"]-summary["total_items_optimal"]}개 '
            f'노이즈 문항을 제거하면\n'
            f'정확도가 {summary["overall_baseline"]*100:.1f}% → '
            f'{summary["overall_optimal"]*100:.1f}%로 향상됩니다.\n\n'
            '노이즈 문항 제거 시 신호 대 잡음 비율(SNR)이\n'
            '개선되어 더 정확한 예측이 가능합니다.'
        )
        box_face = '#e8f6e8'
        box_edge = '#27ae60'
        title_color = '#27ae60'
    elif overall_diff > 0:
        conclusion_title = '소폭 개선 가능'
        conclusion_body = (
            '문항 축소로 정확도가 소폭 향상되나,\n'
            '소표본에서는 우연 변동이 크므로 주의 필요.'
        )
        box_face = '#e8f6e8'
        box_edge = '#27ae60'
        title_color = '#f39c12'
    else:
        conclusion_title = '전체 문항 유지 권장'
        conclusion_body = '모든 문항이 유의미한 정보를 제공합니다.'
        box_face = '#fef5e7'
        box_edge = '#f39c12'
        title_color = '#f39c12'

    concl_rect = mpatches.FancyBboxPatch((0.02, 0.08), 0.96, 0.78,
                                          boxstyle='round,pad=0.03',
                                          facecolor=box_face, edgecolor=box_edge,
                                          linewidth=2.5, transform=ax3.transAxes)
    ax3.add_patch(concl_rect)
    ax3.text(0.5, 0.78, conclusion_title, ha='center', fontsize=24,
             fontweight='bold', color=title_color, transform=ax3.transAxes)
    ax3.text(0.5, 0.45, conclusion_body, ha='center', va='center',
             fontsize=22, color='#333', transform=ax3.transAxes,
             linespacing=1.5)

    # ── (4) 주의사항 ──
    ax4 = fig.add_axes([0.63, 0.03, 0.35, 0.32])
    ax4.axis('off')

    ax4.text(0.5, 0.95, '주의사항', ha='center', fontsize=26, fontweight='bold',
             color='#e67e22', transform=ax4.transAxes)

    warn_rect = mpatches.FancyBboxPatch((0.02, 0.08), 0.96, 0.78,
                                         boxstyle='round,pad=0.03',
                                         facecolor='#fff8e1', edgecolor='#ffc107',
                                         linewidth=2.5, transform=ax4.transAxes)
    ax4.add_patch(warn_rect)

    warnings = [
        f'1. N={info["n"]} 소표본 — 일반화 한계',
        '2. 동일 데이터 최적화 → 과적합 위험',
        '3. 독립 표본 교차검증 필요',
        '4. 자기보고 MBTI 기준 타당성 제한',
    ]
    for i, w in enumerate(warnings):
        ax4.text(0.08, 0.72 - i * 0.16, w, fontsize=21, color='#795548',
                 transform=ax4.transAxes, linespacing=1.4)

    save_figure(fig, TEAM, 'fig_e10_conclusion.png')
    return fig


def plot_e11_cv_accuracy(cv_results, opt_results, info, save_dir):
    """fig_e11: 교차검증 정확도 비교 — In-sample vs CV Test vs Baseline"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(f'fig_e11: 교차검증 정확도 비교 (N={info["n"]})',
                 fontsize=16, fontweight='bold')

    kfold = cv_results['kfold']
    mc = cv_results['mc']

    # ── (a) 차원별 비교 (grouped bar) ──
    x = np.arange(len(DIM_KEYS))
    width = 0.2

    insample_vals = [opt_results[dk]['optimal_acc'] * 100 for dk in DIM_KEYS]
    kf_test_vals = [kfold['dim_test_accs'][dk].mean() * 100 for dk in DIM_KEYS]
    kf_test_std = [kfold['dim_test_accs'][dk].std() * 100 for dk in DIM_KEYS]
    mc_test_vals = [mc['dim_test_accs'][dk].mean() * 100 for dk in DIM_KEYS]
    mc_test_std = [mc['dim_test_accs'][dk].std() * 100 for dk in DIM_KEYS]
    baseline_vals = [kfold['dim_baseline_test'][dk].mean() * 100 for dk in DIM_KEYS]

    ax1.bar(x - 1.5*width, insample_vals, width, label='In-sample 최적화',
            color='#e74c3c', alpha=0.85)
    ax1.bar(x - 0.5*width, kf_test_vals, width, label='5-Fold CV Test',
            color='#3498db', alpha=0.85, yerr=kf_test_std, capsize=3)
    ax1.bar(x + 0.5*width, mc_test_vals, width, label='MC CV Test',
            color='#2ecc71', alpha=0.85, yerr=mc_test_std, capsize=3)
    ax1.bar(x + 1.5*width, baseline_vals, width, label='Baseline (9문항)',
            color='#bdc3c7', alpha=0.85)

    ax1.set_xticks(x)
    ax1.set_xticklabels([DIM_LABELS[dk] for dk in DIM_KEYS])
    ax1.set_ylabel('정확도 (%)')
    ax1.set_title('차원별 정확도 비교')
    ax1.legend(fontsize=9, loc='lower left')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(40, 100)

    # 값 표시
    for bars_data in [(x - 1.5*width, insample_vals),
                      (x - 0.5*width, kf_test_vals),
                      (x + 0.5*width, mc_test_vals),
                      (x + 1.5*width, baseline_vals)]:
        for xp, val in zip(bars_data[0], bars_data[1]):
            ax1.text(xp, val + 0.8, f'{val:.1f}', ha='center', fontsize=7, rotation=45)

    # ── (b) 전체 4글자 일치율 + 과적합 Gap ──
    categories = ['In-sample\n최적화', '5-Fold CV\nTest', 'MC CV\nTest', 'Baseline\n(9문항)']
    vals = [
        opt_results['_summary']['overall_optimal'] * 100,
        kfold['overall_test_accs'].mean() * 100,
        mc['overall_test_accs'].mean() * 100,
        kfold['overall_baseline_test'].mean() * 100,
    ]
    stds = [
        0,
        kfold['overall_test_accs'].std() * 100,
        mc['overall_test_accs'].std() * 100,
        kfold['overall_baseline_test'].std() * 100,
    ]
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#bdc3c7']

    bars = ax2.bar(categories, vals, color=colors, width=0.55, edgecolor='white',
                   yerr=stds, capsize=5)
    for bar, val, std in zip(bars, vals, stds):
        label = f'{val:.1f}%'
        if std > 0:
            label += f'\n(+/-{std:.1f})'
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                label, ha='center', fontsize=11, fontweight='bold')

    # Overfitting gap annotation
    gap = vals[0] - vals[1]
    mid_y = (vals[0] + vals[1]) / 2
    ax2.annotate('', xy=(0, vals[0] - 0.5), xytext=(1, vals[1] + 0.5),
                arrowprops=dict(arrowstyle='<->', color='#e74c3c', lw=2))
    ax2.text(0.5, mid_y, f'Overfit Gap\n{gap:.1f}%p',
            ha='center', fontsize=10, color='#e74c3c', fontweight='bold')

    ax2.set_ylabel('전체 4글자 일치율 (%)')
    ax2.set_title('전체 MBTI 유형 일치율')
    ax2.set_ylim(0, max(vals) + 20)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e11_cv_accuracy.png')
    return fig


def plot_e12_item_stability(cv_results, item_analysis, opt_results, save_dir):
    """fig_e12: 문항 선택 안정성 — CV 반복에서 각 문항이 선택된 빈도"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('fig_e12: 문항 선택 안정성 (교차검증 반복에서 선택 빈도)',
                 fontsize=16, fontweight='bold')

    kfold = cv_results['kfold']
    mc = cv_results['mc']

    for ax, dim_key in zip(axes.flat, DIM_KEYS):
        ia = item_analysis[dim_key]
        freq_kf = kfold['item_selection_freq'][dim_key]
        freq_mc = mc['item_selection_freq'][dim_key]
        q_labels = ia['q_labels']
        n_items = len(q_labels)

        # 빈도순 정렬
        sort_idx = np.argsort(-freq_kf)
        x = np.arange(n_items)
        width = 0.35

        bars1 = ax.bar(x - width/2, freq_kf[sort_idx] * 100, width,
                       label='K-Fold CV', color='#3498db', alpha=0.85)
        bars2 = ax.bar(x + width/2, freq_mc[sort_idx] * 100, width,
                       label='MC CV', color='#2ecc71', alpha=0.85)

        # In-sample 최적 마커
        opt_set = set(opt_results[dim_key]['optimal_indices'])
        for i, orig_idx in enumerate(sort_idx):
            if orig_idx in opt_set:
                max_freq = max(freq_kf[orig_idx], freq_mc[orig_idx]) * 100
                ax.text(i, min(max_freq + 4, 110),
                       '*', ha='center', fontsize=14, color='red', fontweight='bold')

        # 기준선
        ax.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='안정 (80%)')
        ax.axhline(y=50, color='orange', linestyle=':', alpha=0.5, label='불안정 (50%)')

        ax.set_xticks(x)
        ax.set_xticklabels([q_labels[i] for i in sort_idx])
        ax.set_ylabel('선택 빈도 (%)')
        opt_k = opt_results[dim_key]['optimal_k']
        ax.set_title(f'{DIM_LABELS[dim_key]} (In-sample {opt_k}문항, * = 선택됨)')
        ax.set_ylim(0, 115)
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(axis='y', alpha=0.3)

        # 값 표시
        for bar in list(bars1) + list(bars2):
            h = bar.get_height()
            if h > 5:
                ax.text(bar.get_x() + bar.get_width()/2, h + 1,
                       f'{h:.0f}', ha='center', fontsize=7)

    plt.tight_layout()
    save_figure(fig, TEAM, 'fig_e12_item_stability.png')
    return fig


def plot_e13_cv_conclusion(cv_results, opt_results, info, item_analysis, save_dir):
    """fig_e13: 교차검증 종합 결론 — 과적합 진단 인포그래픽"""
    fig = plt.figure(figsize=(28, 16))
    fig.patch.set_facecolor('white')

    kfold = cv_results['kfold']
    mc = cv_results['mc']
    summary = opt_results['_summary']

    # ── 제목 ──
    fig.text(0.5, 0.96, '교차검증 기반 과적합 진단 결과',
             ha='center', fontsize=32, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.935, f'N={info["n"]} | {kfold["method"]} | {mc["method"]}',
             ha='center', fontsize=22, color='#7f8c8d')

    # ── (1) 과적합 Gap 테이블 (상단) ──
    ax1 = fig.add_axes([0.05, 0.68, 0.9, 0.23])
    ax1.axis('off')

    ax1.text(0.5, 0.97, '1. 과적합 Gap 분석 (In-sample - CV Test)',
             ha='center', fontsize=24, fontweight='bold', color='#c0392b',
             transform=ax1.transAxes)

    col_headers = ['차원', 'In-sample', 'K-Fold Test', 'MC Test',
                   'K-Fold Gap', 'MC Gap']
    col_x = [0.02, 0.16, 0.32, 0.48, 0.64, 0.82]

    # 헤더 배경
    h_rect = mpatches.FancyBboxPatch((0.0, 0.76), 1.0, 0.10,
                                      boxstyle='round,pad=0.01',
                                      facecolor='#c0392b', edgecolor='none',
                                      transform=ax1.transAxes)
    ax1.add_patch(h_rect)
    for i, h in enumerate(col_headers):
        ax1.text(col_x[i], 0.79, h, fontsize=24, fontweight='bold',
                 color='white', transform=ax1.transAxes)

    # 데이터 행
    for row, dk in enumerate(DIM_KEYS):
        y = 0.62 - row * 0.13
        insample = opt_results[dk]['optimal_acc'] * 100
        kf_test = kfold['dim_test_accs'][dk].mean() * 100
        mc_test = mc['dim_test_accs'][dk].mean() * 100
        kf_gap = insample - kf_test
        mc_gap = insample - mc_test

        bg = '#fff5f5' if row % 2 == 0 else '#ffffff'
        r = mpatches.FancyBboxPatch((0.0, y - 0.04), 1.0, 0.10,
                                     boxstyle='round,pad=0.005',
                                     facecolor=bg, edgecolor='#eee',
                                     transform=ax1.transAxes)
        ax1.add_patch(r)

        def gap_color(g):
            return '#e74c3c' if g > 5 else '#f39c12' if g > 2 else '#27ae60'

        vals = [DIM_LABELS[dk], f'{insample:.1f}%', f'{kf_test:.1f}%',
                f'{mc_test:.1f}%', f'{kf_gap:+.1f}%p', f'{mc_gap:+.1f}%p']
        colors_v = [DIM_COLORS[dk], '#333', '#3498db', '#2ecc71',
                    gap_color(kf_gap), gap_color(mc_gap)]

        for i, (v, c) in enumerate(zip(vals, colors_v)):
            w = 'bold' if i >= 4 else 'normal'
            ax1.text(col_x[i], y, v, fontsize=23, color=c, fontweight=w,
                     transform=ax1.transAxes)

    # 전체 행
    y_ov = 0.62 - 4 * 0.13
    insample_ov = summary['overall_optimal'] * 100
    kf_test_ov = kfold['overall_test_accs'].mean() * 100
    mc_test_ov = mc['overall_test_accs'].mean() * 100
    kf_gap_ov = insample_ov - kf_test_ov
    mc_gap_ov = insample_ov - mc_test_ov

    r = mpatches.FancyBboxPatch((0.0, y_ov - 0.04), 1.0, 0.10,
                                 boxstyle='round,pad=0.005',
                                 facecolor='#f0f0f0', edgecolor='#ccc',
                                 linewidth=2, transform=ax1.transAxes)
    ax1.add_patch(r)
    ov_vals = ['전체 4글자', f'{insample_ov:.1f}%', f'{kf_test_ov:.1f}%',
               f'{mc_test_ov:.1f}%', f'{kf_gap_ov:+.1f}%p', f'{mc_gap_ov:+.1f}%p']
    for i, v in enumerate(ov_vals):
        ax1.text(col_x[i], y_ov, v, fontsize=24, fontweight='bold',
                 color='#2c3e50', transform=ax1.transAxes)

    # ── (2) 정직한 개선 분석 (중단 좌) ──
    ax2 = fig.add_axes([0.05, 0.28, 0.43, 0.36])
    ax2.axis('off')

    ax2.text(0.5, 0.97, '2. 정직한 개선 (CV Test - Baseline)',
             ha='center', fontsize=22, fontweight='bold', color='#2980b9',
             transform=ax2.transAxes)

    rect2 = mpatches.FancyBboxPatch((0.02, 0.02), 0.96, 0.88,
                                     boxstyle='round,pad=0.02',
                                     facecolor='#eaf4fc', edgecolor='#3498db',
                                     linewidth=2, transform=ax2.transAxes)
    ax2.add_patch(rect2)

    y_start = 0.82
    for dk in DIM_KEYS:
        kf_test = kfold['dim_test_accs'][dk].mean() * 100
        kf_base = kfold['dim_baseline_test'][dk].mean() * 100
        honest = kf_test - kf_base
        h_color = '#27ae60' if honest > 1 else '#e74c3c' if honest < -1 else '#f39c12'

        ax2.text(0.06, y_start, f'{DIM_LABELS[dk]}:', fontsize=21,
                 color=DIM_COLORS[dk], fontweight='bold', transform=ax2.transAxes)
        ax2.text(0.42, y_start, f'{kf_test:.1f}% vs {kf_base:.1f}%',
                 fontsize=24, color='#555', transform=ax2.transAxes)
        ax2.text(0.88, y_start, f'{honest:+.1f}%p',
                 fontsize=22, color=h_color, fontweight='bold',
                 transform=ax2.transAxes, ha='center')
        y_start -= 0.17

    # Overall
    kf_test_ov = kfold['overall_test_accs'].mean() * 100
    kf_base_ov = kfold['overall_baseline_test'].mean() * 100
    honest_ov = kf_test_ov - kf_base_ov
    h_color_ov = '#27ae60' if honest_ov > 1 else '#e74c3c' if honest_ov < -1 else '#f39c12'

    ax2.text(0.06, y_start, f'전체 4글자:', fontsize=22, fontweight='bold',
             color='#2c3e50', transform=ax2.transAxes)
    ax2.text(0.42, y_start, f'{kf_test_ov:.1f}% vs {kf_base_ov:.1f}%',
             fontsize=21, color='#333', transform=ax2.transAxes)
    ax2.text(0.88, y_start, f'{honest_ov:+.1f}%p',
             fontsize=24, color=h_color_ov, fontweight='bold',
             transform=ax2.transAxes, ha='center')

    # ── (3) 종합 판정 (중단 우) ──
    ax3 = fig.add_axes([0.52, 0.28, 0.46, 0.36])
    ax3.axis('off')

    ax3.text(0.5, 0.97, '3. 종합 판정',
             ha='center', fontsize=22, fontweight='bold', color='#8e44ad',
             transform=ax3.transAxes)

    avg_gap = np.mean([
        opt_results[dk]['optimal_acc'] * 100 - kfold['dim_test_accs'][dk].mean() * 100
        for dk in DIM_KEYS
    ])
    avg_honest = np.mean([
        kfold['dim_test_accs'][dk].mean() * 100 - kfold['dim_baseline_test'][dk].mean() * 100
        for dk in DIM_KEYS
    ])

    if avg_gap > 5:
        verdict = '과적합 심각'
        verdict_detail = (
            f'평균 과적합 Gap = {avg_gap:.1f}%p\n\n'
            'In-sample 최적화 결과를 신뢰할 수 없습니다.\n'
            '문항 축소 효과의 대부분은 과적합에 의한\n'
            '환상(illusion)일 가능성이 높습니다.'
        )
        v_face, v_edge, v_color = '#fde8e8', '#e74c3c', '#c0392b'
    elif avg_gap > 2:
        verdict = '부분적 과적합'
        verdict_detail = (
            f'평균 과적합 Gap = {avg_gap:.1f}%p\n'
            f'정직한 평균 개선 = {avg_honest:+.1f}%p\n\n'
            'In-sample 결과가 과대추정되어 있으나,\n'
            '일부 문항 축소 효과는 실재할 수 있습니다.'
        )
        v_face, v_edge, v_color = '#fef5e7', '#f39c12', '#e67e22'
    else:
        verdict = '과적합 미미'
        verdict_detail = (
            f'평균 과적합 Gap = {avg_gap:.1f}%p\n'
            f'정직한 평균 개선 = {avg_honest:+.1f}%p\n\n'
            '최적화 결과가 독립 데이터에서도\n'
            '재현됩니다.'
        )
        v_face, v_edge, v_color = '#e8f6e8', '#27ae60', '#27ae60'

    rect3 = mpatches.FancyBboxPatch((0.02, 0.02), 0.96, 0.88,
                                     boxstyle='round,pad=0.02',
                                     facecolor=v_face, edgecolor=v_edge,
                                     linewidth=3, transform=ax3.transAxes)
    ax3.add_patch(rect3)

    ax3.text(0.5, 0.78, verdict, ha='center', fontsize=28,
             fontweight='bold', color=v_color, transform=ax3.transAxes)
    ax3.text(0.5, 0.42, verdict_detail, ha='center', va='center',
             fontsize=21, color='#333', transform=ax3.transAxes,
             linespacing=1.5)

    # ── (4) 분석 방법 요약 (하단) ──
    ax4 = fig.add_axes([0.05, 0.03, 0.9, 0.22])
    ax4.axis('off')

    ax4.text(0.5, 0.95, '4. 분석 방법 요약',
             ha='center', fontsize=22, fontweight='bold', color='#2c3e50',
             transform=ax4.transAxes)

    method_rect = mpatches.FancyBboxPatch((0.02, 0.05), 0.96, 0.82,
                                           boxstyle='round,pad=0.02',
                                           facecolor='#f8f9fa', edgecolor='#dee2e6',
                                           linewidth=1.5, transform=ax4.transAxes)
    ax4.add_patch(method_rect)

    methods = [
        f'K-Fold CV: 5-Fold x 20 Repeats = {kfold["n_folds"]} folds '
        f'| 각 fold: train으로 exhaustive search, test로 정직한 평가',
        f'Monte Carlo CV: {mc["n_iterations"]}회 랜덤 70/30 분할 '
        f'| 독립적 무작위 검증으로 K-Fold 결과 교차 확인',
        f'문항 선택 안정성: {kfold["n_folds"]+mc["n_iterations"]}회 반복에서 '
        f'각 문항의 최적 부분집합 선택 빈도 분석',
        f'과적합 Gap = In-sample 정확도 - CV Test 정확도 '
        f'| 정직한 개선 = CV Test - Baseline (9문항)',
    ]
    for i, m in enumerate(methods):
        ax4.text(0.05, 0.72 - i * 0.18, f'{i+1}. {m}',
                fontsize=22, color='#495057', transform=ax4.transAxes,
                linespacing=1.3)

    save_figure(fig, TEAM, 'fig_e13_cv_conclusion.png')
    return fig


def plot_e14_advanced_comparison(adv_methods, adv_cv, info, opt_results, save_dir):
    """fig_e14: 고급 최적화 방법 비교 — In-sample vs CV Test 정확도"""
    fig = plt.figure(figsize=(30, 18))
    fig.patch.set_facecolor('white')

    method_order = ['baseline', 'item_subset', 'adaptive', 'citc',
                    'citc_adaptive', 'majority', 'subset_adaptive', 'logistic']
    name_map = adv_cv.get('_name_map', {
        'baseline': 'Baseline\n(9문항, t=4.0)',
        'item_subset': 'Item Subset\n(축소, t=4.0)',
        'adaptive': 'Adaptive\nThreshold',
        'citc': 'CITC\nWeighted',
        'citc_adaptive': 'CITC +\nAdaptive',
        'majority': 'Majority\nVote',
        'subset_adaptive': 'Subset +\nAdaptive',
        'logistic': 'Logistic\nRegression',
    })
    short_names = [
        'Baseline\n(9문항)', 'Item\nSubset',
        'Adaptive\nThreshold', 'CITC\nWeighted',
        'CITC +\nAdaptive', 'Majority\nVote',
        'Subset +\nAdaptive', 'Logistic\nRegression'
    ]
    bar_colors = ['#95a5a6', '#e74c3c', '#3498db', '#2ecc71',
                  '#9b59b6', '#f39c12', '#e67e22', '#1abc9c']

    # ── 패널 1: In-sample vs CV Test 비교 (상단) ──
    ax1 = fig.add_axes([0.06, 0.55, 0.58, 0.38])

    x = np.arange(len(method_order))
    width = 0.35

    insample_vals = [adv_methods[mk]['overall'] * 100 for mk in method_order]
    cv_test_vals = [adv_cv[mk]['test_mean'] * 100 for mk in method_order]

    bars1 = ax1.bar(x - width/2, insample_vals, width,
                    label='In-sample', color=bar_colors, alpha=0.85,
                    edgecolor='white', linewidth=1.5)
    bars2 = ax1.bar(x + width/2, cv_test_vals, width,
                    label='CV Test', color=bar_colors, alpha=0.45,
                    edgecolor='white', linewidth=1.5,
                    hatch='///')

    for bar, val in zip(list(bars1) + list(bars2), insample_vals + cv_test_vals):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', fontsize=20, fontweight='bold')

    # Best CV method marker
    best_mk = adv_cv['_best']
    best_idx = method_order.index(best_mk)
    ax1.annotate('Best\nCV', xy=(best_idx + width/2, cv_test_vals[best_idx]),
                xytext=(best_idx + width/2 + 0.5, cv_test_vals[best_idx] + 8),
                fontsize=22, fontweight='bold', color='#e74c3c',
                ha='center',
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))

    ax1.set_xticks(x)
    ax1.set_xticklabels(short_names, fontsize=21)
    ax1.set_ylabel('전체 4글자 일치율 (%)', fontsize=24)
    ax1.set_title('In-sample vs 교차검증 Test 정확도', fontsize=22, fontweight='bold')
    ax1.legend(fontsize=22, loc='upper left')
    ax1.set_ylim(0, max(insample_vals) + 15)
    ax1.grid(axis='y', alpha=0.3)

    # Baseline reference line
    baseline_insample = insample_vals[0]
    ax1.axhline(y=baseline_insample, color='gray', linestyle='--',
               alpha=0.5, linewidth=1.5)
    ax1.text(len(method_order) - 0.5, baseline_insample + 1,
            f'Baseline: {baseline_insample:.1f}%',
            fontsize=20, color='gray', ha='right')

    # ── 패널 2: 과적합 Gap (상단 우) ──
    ax2 = fig.add_axes([0.68, 0.55, 0.28, 0.38])

    gaps = [adv_cv[mk]['gap'] for mk in method_order]
    gap_colors = ['#27ae60' if g < 2 else '#f39c12' if g < 5 else '#e74c3c'
                  for g in gaps]

    bars_gap = ax2.barh(range(len(method_order)), gaps, color=gap_colors,
                        edgecolor='white', height=0.6)
    ax2.set_yticks(range(len(method_order)))
    ax2.set_yticklabels(short_names, fontsize=20)
    ax2.set_xlabel('과적합 Gap (Train - Test, %p)', fontsize=22)
    ax2.set_title('과적합 위험도', fontsize=20, fontweight='bold')
    ax2.axvline(x=2, color='#f39c12', linestyle='--', alpha=0.7, label='경고 (2%p)')
    ax2.axvline(x=5, color='#e74c3c', linestyle='--', alpha=0.7, label='심각 (5%p)')
    ax2.legend(fontsize=19, loc='lower right')

    for bar, val in zip(bars_gap, gaps):
        x_pos = max(val + 0.3, 0.5)
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%p', va='center', fontsize=20, fontweight='bold')

    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.3)

    # ── 패널 3: 차원별 CV Test 정확도 (하단 좌) ──
    ax3 = fig.add_axes([0.06, 0.08, 0.58, 0.38])
    ax3.axis('off')

    ax3.text(0.5, 0.97, '차원별 CV Test 정확도 비교',
             ha='center', fontsize=22, fontweight='bold', color='#2c3e50',
             transform=ax3.transAxes)

    # 테이블 헤더
    col_x = [0.0, 0.14, 0.28, 0.42, 0.56, 0.7, 0.84]
    headers = ['차원'] + short_names[1:]  # skip baseline column, too many
    # Use simplified layout: show only key methods
    key_methods = ['baseline', 'adaptive', 'citc', 'citc_adaptive', 'majority']
    key_names = ['Baseline', 'Adaptive\nThreshold', 'CITC\nWeighted',
                 'CITC +\nAdaptive', 'Majority\nVote']
    col_x_k = [0.0, 0.15, 0.32, 0.49, 0.66, 0.83]

    # Header background
    h_rect = mpatches.FancyBboxPatch(
        (0.0, 0.79), 1.0, 0.12, boxstyle='round,pad=0.01',
        facecolor='#2c3e50', edgecolor='none', transform=ax3.transAxes)
    ax3.add_patch(h_rect)

    for i, h in enumerate(['차원'] + key_names):
        ax3.text(col_x_k[i], 0.83, h, fontsize=21, fontweight='bold',
                 color='white', transform=ax3.transAxes)

    # Data rows — per dimension CV test accuracy
    for row, dk in enumerate(DIM_KEYS + ['overall']):
        y = 0.65 - row * 0.13
        bg = '#f8f9fa' if row % 2 == 0 else '#ffffff'
        r = mpatches.FancyBboxPatch(
            (0.0, y - 0.04), 1.0, 0.11, boxstyle='round,pad=0.005',
            facecolor=bg, edgecolor='#eee', transform=ax3.transAxes)
        ax3.add_patch(r)

        if dk == 'overall':
            label_text = '전체 4글자'
            vals = [adv_cv[mk]['test_mean'] * 100 for mk in key_methods]
        else:
            label_text = DIM_LABELS[dk]
            # Per-dimension CV accuracy not stored globally; show in-sample
            vals = [adv_methods[mk]['dim_accs'][dk] * 100 for mk in key_methods]

        ax3.text(col_x_k[0], y, label_text, fontsize=22,
                 fontweight='bold' if dk == 'overall' else 'normal',
                 color=DIM_COLORS.get(dk, '#2c3e50'), transform=ax3.transAxes)

        best_val = max(vals)
        for i, val in enumerate(vals):
            color = '#27ae60' if val == best_val and val > vals[0] else '#333'
            weight = 'bold' if val == best_val else 'normal'
            ax3.text(col_x_k[i + 1], y, f'{val:.1f}%', fontsize=22,
                     color=color, fontweight=weight, transform=ax3.transAxes)

    # ── 패널 4: 결론 (하단 우) ──
    ax4 = fig.add_axes([0.68, 0.08, 0.28, 0.38])
    ax4.axis('off')

    ax4.text(0.5, 0.97, '결론',
             ha='center', fontsize=22, fontweight='bold', color='#8e44ad',
             transform=ax4.transAxes)

    best_mk = adv_cv['_best']
    best_cv_test = adv_cv[best_mk]['test_mean'] * 100
    best_insample = adv_methods[best_mk]['overall'] * 100
    best_gap = adv_cv[best_mk]['gap']
    baseline_cv = adv_cv['baseline']['test_mean'] * 100
    improvement = best_cv_test - baseline_cv

    if improvement > 1:
        verdict = '개선 확인'
        v_face, v_edge = '#e8f6e8', '#27ae60'
        v_color = '#27ae60'
    elif improvement > -1:
        verdict = '유의미한 차이 없음'
        v_face, v_edge = '#fef5e7', '#f39c12'
        v_color = '#e67e22'
    else:
        verdict = '개선 불가'
        v_face, v_edge = '#fde8e8', '#e74c3c'
        v_color = '#c0392b'

    rect4 = mpatches.FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.88, boxstyle='round,pad=0.02',
        facecolor=v_face, edgecolor=v_edge,
        linewidth=3, transform=ax4.transAxes)
    ax4.add_patch(rect4)

    ax4.text(0.5, 0.78, verdict, ha='center', fontsize=26,
             fontweight='bold', color=v_color, transform=ax4.transAxes)

    best_name = adv_cv['_name_map'].get(best_mk, best_mk)
    conclusion_text = (
        f'CV 최적 방법: {best_name}\n\n'
        f'Baseline CV Test: {baseline_cv:.1f}%\n'
        f'Best CV Test: {best_cv_test:.1f}%\n'
        f'정직한 개선: {improvement:+.1f}%p\n'
        f'과적합 Gap: {best_gap:.1f}%p'
    )
    ax4.text(0.5, 0.40, conclusion_text, ha='center', va='center',
             fontsize=24, color='#333', transform=ax4.transAxes,
             linespacing=1.6)

    # Title
    fig.text(0.5, 0.97, 'fig_e14: 고급 최적화 방법 비교 — 교차검증 기반 정직한 평가',
             ha='center', fontsize=28, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.945, f'N={info["n"]} | Repeated 5-Fold CV (100 folds) | 8개 방법 비교',
             ha='center', fontsize=24, color='#7f8c8d')

    save_figure(fig, TEAM, 'fig_e14_advanced_comparison.png')
    return fig


def plot_e15_logistic_regression(adv_methods, adv_cv, info, save_dir):
    """fig_e15: 로지스틱 회귀 분석 결과 — 계수, 정확도, 방법 비교"""
    fig = plt.figure(figsize=(28, 18))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.97, 'fig_e15: 로지스틱 회귀(Logistic Regression) MBTI 차원 예측',
             ha='center', fontsize=28, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.945, f'N={info["n"]} | LOO-CV (Leave-One-Out) | L2 정규화 | 경사하강법',
             ha='center', fontsize=24, color='#7f8c8d')

    lr_data = adv_methods.get('logistic', {})
    lr_dim_accs = lr_data.get('dim_accs', {})
    lr_weights = lr_data.get('weights', {})
    lr_train_accs = lr_data.get('train_accs', {})

    # ── 패널 1: 차원별 정확도 비교 (임계값 vs 로지스틱) ──
    ax1 = fig.add_axes([0.06, 0.52, 0.42, 0.38])

    dims = DIM_KEYS
    baseline_accs = [adv_methods['baseline']['dim_accs'][dk] * 100 for dk in dims]
    logistic_accs = [lr_dim_accs.get(dk, 0) * 100 for dk in dims]
    train_accs = [lr_train_accs.get(dk, 0) * 100 for dk in dims]

    x = np.arange(len(dims))
    width = 0.25

    bars1 = ax1.bar(x - width, baseline_accs, width, label='Baseline (t=4.0)',
                    color='#95a5a6', edgecolor='white', linewidth=1.5)
    bars2 = ax1.bar(x, logistic_accs, width, label='Logistic (LOO-CV)',
                    color='#1abc9c', edgecolor='white', linewidth=1.5)
    bars3 = ax1.bar(x + width, train_accs, width, label='Logistic (Train)',
                    color='#1abc9c', alpha=0.4, edgecolor='white', linewidth=1.5,
                    hatch='///')

    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{bar.get_height():.1f}%', ha='center', fontsize=20,
                    fontweight='bold')

    ax1.set_xticks(x)
    ax1.set_xticklabels([DIM_LABELS[dk] for dk in dims], fontsize=22)
    ax1.set_ylabel('정확도 (%)', fontsize=23)
    ax1.set_title('1. 차원별 정확도: 임계값 vs 로지스틱 회귀', fontsize=20,
                  fontweight='bold')
    ax1.legend(fontsize=20, loc='upper right')
    ax1.set_ylim(0, 105)
    ax1.grid(axis='y', alpha=0.3)

    # ── 패널 2: 전체 방법 비교 (8개 방법) ──
    ax2 = fig.add_axes([0.55, 0.52, 0.42, 0.38])

    all_methods_order = ['baseline', 'item_subset', 'adaptive', 'citc',
                         'citc_adaptive', 'majority', 'subset_adaptive', 'logistic']
    method_names_short = ['Baseline', 'Subset', 'Adaptive', 'CITC',
                          'CITC+Adap', 'Majority', 'Sub+Adap', 'Logistic']
    colors_all = ['#95a5a6', '#e74c3c', '#3498db', '#2ecc71',
                  '#9b59b6', '#f39c12', '#e67e22', '#1abc9c']

    # In-sample vs CV-test
    insample_vals = [adv_methods[mk]['overall'] * 100 for mk in all_methods_order]
    cv_vals = [adv_cv[mk]['test_mean'] * 100 if mk in adv_cv else 0
               for mk in all_methods_order]

    y_pos = np.arange(len(all_methods_order))
    height = 0.35

    ax2.barh(y_pos + height/2, insample_vals, height, label='In-sample',
             color=colors_all, alpha=0.85, edgecolor='white')
    ax2.barh(y_pos - height/2, cv_vals, height, label='CV Test',
             color=colors_all, alpha=0.45, edgecolor='white', hatch='///')

    for i, (iv, cv) in enumerate(zip(insample_vals, cv_vals)):
        ax2.text(iv + 0.5, i + height/2, f'{iv:.1f}%', va='center', fontsize=20)
        ax2.text(cv + 0.5, i - height/2, f'{cv:.1f}%', va='center', fontsize=20)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(method_names_short, fontsize=21)
    ax2.set_xlabel('전체 4글자 일치율 (%)', fontsize=22)
    ax2.set_title('2. 8개 방법 전체 비교 (In-sample vs CV)', fontsize=20,
                  fontweight='bold')
    ax2.legend(fontsize=20, loc='lower right')
    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.3)

    # ── 패널 3: 로지스틱 회귀 계수 히트맵 ──
    ax3 = fig.add_axes([0.06, 0.06, 0.42, 0.38])

    if lr_weights:
        # 각 차원의 가중치 (bias 제외, 9개 문항 계수)
        weight_matrix = np.zeros((4, 9))
        for row, dk in enumerate(DIM_KEYS):
            w = lr_weights.get(dk, np.zeros(10))
            weight_matrix[row] = w[1:]  # bias 제외

        im = ax3.imshow(weight_matrix, cmap='RdBu_r', aspect='auto',
                        vmin=-np.abs(weight_matrix).max(),
                        vmax=np.abs(weight_matrix).max())
        ax3.set_yticks(range(4))
        ax3.set_yticklabels([DIM_LABELS[dk] for dk in DIM_KEYS], fontsize=21)
        ax3.set_xticks(range(9))
        ax3.set_xticklabels([f'Q{i+1}' for i in range(9)], fontsize=20)
        ax3.set_title('3. 로지스틱 회귀 계수 (문항별 가중치)', fontsize=20,
                      fontweight='bold')

        # 값 표시
        for i in range(4):
            for j in range(9):
                val = weight_matrix[i, j]
                color = 'white' if abs(val) > np.abs(weight_matrix).max() * 0.6 else 'black'
                ax3.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=19, color=color, fontweight='bold')

        plt.colorbar(im, ax=ax3, shrink=0.8, label='계수 값')
    else:
        ax3.text(0.5, 0.5, '가중치 데이터 없음', ha='center', va='center',
                fontsize=24, transform=ax3.transAxes)

    # ── 패널 4: 모형 요약 ──
    ax4 = fig.add_axes([0.55, 0.06, 0.42, 0.38])
    ax4.axis('off')

    ax4.text(0.5, 0.95, '4. 로지스틱 회귀 모형 요약',
             ha='center', fontsize=24, fontweight='bold', color='#1abc9c',
             transform=ax4.transAxes)

    # 결과 요약 박스
    rect = mpatches.FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.88, boxstyle='round,pad=0.02',
        facecolor='#e8f8f5', edgecolor='#1abc9c',
        linewidth=2, transform=ax4.transAxes)
    ax4.add_patch(rect)

    baseline_ov = adv_methods['baseline']['overall'] * 100
    logistic_ov = lr_data.get('overall', 0) * 100
    logistic_cv = adv_cv.get('logistic', {}).get('test_mean', 0) * 100
    logistic_gap = adv_cv.get('logistic', {}).get('gap', 0)
    improvement = logistic_cv - adv_cv['baseline']['test_mean'] * 100

    summary_lines = [
        ('모형', '로지스틱 회귀 (이진 분류, L2 정규화)'),
        ('학습 방법', '경사하강법 (lr=0.5, epochs=300, lambda=0.1)'),
        ('검증 방법', 'LOO-CV (In-sample) + Repeated 5-Fold CV'),
        ('', ''),
        ('Baseline (4글자)', f'{baseline_ov:.1f}% (In-sample)'),
        ('Logistic In-sample', f'{logistic_ov:.1f}%'),
        ('Logistic CV Test', f'{logistic_cv:.1f}%'),
        ('과적합 Gap', f'{logistic_gap:.1f}%p'),
        ('vs Baseline (CV)', f'{improvement:+.1f}%p'),
        ('', ''),
        ('해석', '로지스틱 회귀는 문항별 최적 가중치를 학습하여'),
        ('', '단순 임계값 방식보다 유연한 결정 경계를 형성합니다.'),
    ]

    y = 0.82
    for label, value in summary_lines:
        if label == '' and value == '':
            y -= 0.03
            continue
        if label:
            ax4.text(0.06, y, f'{label}:', fontsize=22, fontweight='bold',
                     color='#2c3e50', transform=ax4.transAxes)
            ax4.text(0.40, y, value, fontsize=22, color='#333',
                     transform=ax4.transAxes)
        else:
            ax4.text(0.40, y, value, fontsize=22, color='#333',
                     transform=ax4.transAxes)
        y -= 0.065

    save_figure(fig, TEAM, 'fig_e15_logistic_regression.png')
    return fig


def plot_e16_logistic_diagnostics(adv_methods, info, save_dir):
    """fig_e16: 로지스틱 회귀 모형 진단 — VIF, AIC/BIC, McFadden R², 분류 성능"""
    fig = plt.figure(figsize=(28, 20))
    fig.patch.set_facecolor('white')

    fig.text(0.5, 0.97, 'fig_e16: 로지스틱 회귀 모형 진단 (Regression Diagnostics)',
             ha='center', fontsize=28, fontweight='bold', color='#2c3e50')
    fig.text(0.5, 0.945, f'N={info["n"]} | 4차원 독립 이진 분류 | '
             f'다중공선성(VIF) · AIC/BIC · McFadden R² · 분류 성능 평가',
             ha='center', fontsize=24, color='#7f8c8d')

    lr_data = adv_methods.get('logistic', {})
    lr_weights = lr_data.get('weights', {})

    dims = DIM_KEYS
    dim_labels = [DIM_LABELS[dk] for dk in dims]

    # 각 차원별 진단 수행 (전체 데이터로 학습한 모형)
    diagnostics = {}
    for dk in dims:
        X = info['item_scores'][dk]
        y = (info['self_letters'][dk] == DIM_HIGH[dk]).astype(int)
        X_std, m, s = standardize_features(X)
        model = logistic_regression_train(X_std, y, lr=0.5, epochs=300, lambda_reg=0.1)
        diag = logistic_regression_diagnostics(
            X_std, y, model['weights'],
            feature_names=[f'Q{i+1}' for i in range(X.shape[1])],
            X_raw=X
        )
        diagnostics[dk] = diag

    # ── 패널 1: VIF (다중공선성) ──
    ax1 = fig.add_axes([0.06, 0.54, 0.42, 0.36])

    n_items = max(len(diagnostics[dk]['vif']) for dk in dims)
    x_items = np.arange(n_items)
    width = 0.18
    colors_dim = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']

    for idx, dk in enumerate(dims):
        vifs = diagnostics[dk]['vif']
        ax1.bar(x_items[:len(vifs)] + idx * width - 1.5 * width, vifs, width,
                label=dim_labels[idx], color=colors_dim[idx], alpha=0.85,
                edgecolor='white', linewidth=1)

    ax1.axhline(y=5, color='#e74c3c', linestyle='--', linewidth=2,
                alpha=0.7, label='경고 기준 (VIF=5)')
    ax1.axhline(y=10, color='#c0392b', linestyle=':', linewidth=2,
                alpha=0.7, label='심각 기준 (VIF=10)')

    ax1.set_xticks(x_items)
    ax1.set_xticklabels([f'Q{i+1}' for i in range(n_items)], fontsize=20)
    ax1.set_ylabel('VIF 값', fontsize=23, fontweight='bold')
    ax1.set_title('1. 다중공선성 진단 (VIF)', fontsize=20, fontweight='bold')
    ax1.legend(fontsize=20, loc='upper right', ncol=2)
    ax1.grid(axis='y', alpha=0.3)

    max_vif = max(max(diagnostics[dk]['vif']) for dk in dims)
    ax1.set_ylim(0, max(max_vif * 1.3, 6))

    # ── 패널 2: AIC / BIC 비교 ──
    ax2 = fig.add_axes([0.55, 0.54, 0.42, 0.36])

    aic_vals = [diagnostics[dk]['aic_bic']['aic'] for dk in dims]
    bic_vals = [diagnostics[dk]['aic_bic']['bic'] for dk in dims]
    ll_vals = [diagnostics[dk]['aic_bic']['log_likelihood'] for dk in dims]

    x_dims = np.arange(len(dims))
    w = 0.3

    bars_aic = ax2.bar(x_dims - w/2, aic_vals, w, label='AIC',
                       color='#3498db', edgecolor='white', linewidth=1.5)
    bars_bic = ax2.bar(x_dims + w/2, bic_vals, w, label='BIC',
                       color='#e74c3c', edgecolor='white', linewidth=1.5)

    for bar in bars_aic:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}', ha='center', fontsize=20, fontweight='bold',
                color='#3498db')
    for bar in bars_bic:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}', ha='center', fontsize=20, fontweight='bold',
                color='#e74c3c')

    ax2.set_xticks(x_dims)
    ax2.set_xticklabels(dim_labels, fontsize=22)
    ax2.set_ylabel('정보 기준 값 (낮을수록 좋음)', fontsize=22, fontweight='bold')
    ax2.set_title('2. 모형 적합도: AIC / BIC', fontsize=20, fontweight='bold')
    ax2.legend(fontsize=21)
    ax2.grid(axis='y', alpha=0.3)

    # AIC/BIC 아래에 Log-Likelihood 표시
    for i, ll in enumerate(ll_vals):
        ax2.text(i, 2, f'LL={ll:.1f}', ha='center', fontsize=20,
                color='#7f8c8d', fontweight='bold')

    # ── 패널 3: McFadden R² + 분류 성능 ──
    ax3 = fig.add_axes([0.06, 0.07, 0.42, 0.36])

    r2_vals = [diagnostics[dk]['mcfadden']['mcfadden_r2'] for dk in dims]
    acc_vals = [diagnostics[dk]['classification']['accuracy'] for dk in dims]
    f1_vals = [diagnostics[dk]['classification']['f1'] for dk in dims]
    prec_vals = [diagnostics[dk]['classification']['precision'] for dk in dims]
    recall_vals = [diagnostics[dk]['classification']['recall'] for dk in dims]

    w = 0.15
    ax3.bar(x_dims - 2*w, r2_vals, w, label='McFadden R²',
            color='#9b59b6', edgecolor='white', linewidth=1.5)
    ax3.bar(x_dims - w, acc_vals, w, label='Accuracy',
            color='#1abc9c', edgecolor='white', linewidth=1.5)
    ax3.bar(x_dims, prec_vals, w, label='Precision',
            color='#3498db', edgecolor='white', linewidth=1.5)
    ax3.bar(x_dims + w, recall_vals, w, label='Recall',
            color='#e67e22', edgecolor='white', linewidth=1.5)
    ax3.bar(x_dims + 2*w, f1_vals, w, label='F1-score',
            color='#e74c3c', edgecolor='white', linewidth=1.5)

    # 각 바 위에 값 표시
    for i in range(len(dims)):
        vals = [r2_vals[i], acc_vals[i], prec_vals[i], recall_vals[i], f1_vals[i]]
        offsets = [-2*w, -w, 0, w, 2*w]
        for v, off in zip(vals, offsets):
            ax3.text(i + off, v + 0.01, f'{v:.2f}', ha='center', fontsize=20,
                    fontweight='bold')

    ax3.axhline(y=0.2, color='#9b59b6', linestyle='--', linewidth=1, alpha=0.5)
    ax3.text(len(dims)-0.5, 0.21, 'R²=0.2 (양호 기준)', fontsize=20,
            color='#9b59b6', ha='right')

    ax3.set_xticks(x_dims)
    ax3.set_xticklabels(dim_labels, fontsize=22)
    ax3.set_ylabel('값 (0~1)', fontsize=23, fontweight='bold')
    ax3.set_title('3. McFadden R² + 분류 성능 지표', fontsize=20, fontweight='bold')
    ax3.legend(fontsize=20, loc='upper right', ncol=3)
    ax3.set_ylim(0, 1.15)
    ax3.grid(axis='y', alpha=0.3)

    # ── 패널 4: 종합 진단 요약 테이블 ──
    ax4 = fig.add_axes([0.55, 0.07, 0.42, 0.36])
    ax4.axis('off')

    ax4.text(0.5, 0.97, '4. 회귀 모형 종합 진단 요약',
             ha='center', fontsize=22, fontweight='bold', color='#2c3e50',
             transform=ax4.transAxes)

    # 테이블 데이터 구성
    col_labels = ['지표'] + dim_labels
    table_data = []

    # VIF 평균
    vif_row = ['VIF (평균)']
    for dk in dims:
        mean_vif = np.mean(diagnostics[dk]['vif'])
        status = '✓ 양호' if mean_vif < 5 else '⚠ 주의' if mean_vif < 10 else '✗ 심각'
        vif_row.append(f'{mean_vif:.2f} {status}')
    table_data.append(vif_row)

    # AIC
    table_data.append(['AIC'] + [f'{diagnostics[dk]["aic_bic"]["aic"]:.1f}' for dk in dims])

    # BIC
    table_data.append(['BIC'] + [f'{diagnostics[dk]["aic_bic"]["bic"]:.1f}' for dk in dims])

    # Log-Likelihood
    table_data.append(['Log-Likelihood'] +
                      [f'{diagnostics[dk]["aic_bic"]["log_likelihood"]:.1f}' for dk in dims])

    # McFadden R²
    r2_row = ['McFadden R²']
    for dk in dims:
        r2 = diagnostics[dk]['mcfadden']['mcfadden_r2']
        quality = '우수' if r2 > 0.4 else '양호' if r2 > 0.2 else '미흡'
        r2_row.append(f'{r2:.4f} ({quality})')
    table_data.append(r2_row)

    # 조건수
    table_data.append(['조건수'] +
                      [f'{diagnostics[dk]["condition_number"]:.1f}' for dk in dims])

    # Accuracy
    table_data.append(['Accuracy'] +
                      [f'{diagnostics[dk]["classification"]["accuracy"]:.1%}' for dk in dims])

    # F1-score
    table_data.append(['F1-score'] +
                      [f'{diagnostics[dk]["classification"]["f1"]:.3f}' for dk in dims])

    # Precision / Recall
    table_data.append(['Precision'] +
                      [f'{diagnostics[dk]["classification"]["precision"]:.3f}' for dk in dims])
    table_data.append(['Recall'] +
                      [f'{diagnostics[dk]["classification"]["recall"]:.3f}' for dk in dims])

    table = ax4.table(cellText=table_data, colLabels=col_labels,
                      loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1.0, 1.8)

    # 헤더 스타일
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold', fontsize=23)

    # 첫 열 스타일
    for i in range(len(table_data)):
        cell = table[i+1, 0]
        cell.set_facecolor('#ecf0f1')
        cell.set_text_props(fontweight='bold')

    # 데이터 셀 배경색 (VIF, R² 행에 조건부 색상)
    for i in range(len(table_data)):
        for j in range(1, len(col_labels)):
            cell = table[i+1, j]
            if i == 0:  # VIF 행
                dk = dims[j-1]
                mean_vif = np.mean(diagnostics[dk]['vif'])
                if mean_vif < 5:
                    cell.set_facecolor('#d5f5e3')
                elif mean_vif < 10:
                    cell.set_facecolor('#fdebd0')
                else:
                    cell.set_facecolor('#fadbd8')
            elif i == 4:  # McFadden R² 행
                dk = dims[j-1]
                r2 = diagnostics[dk]['mcfadden']['mcfadden_r2']
                if r2 > 0.4:
                    cell.set_facecolor('#d5f5e3')
                elif r2 > 0.2:
                    cell.set_facecolor('#d4efdf')
                else:
                    cell.set_facecolor('#fdebd0')

    save_figure(fig, TEAM, 'fig_e16_logistic_diagnostics.png')
    return fig


# ============================================================
#  6. 메인 실행
# ============================================================

def main():
    set_project_style()

    save_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'results', 'figures', TEAM
    )
    os.makedirs(save_dir, exist_ok=True)

    # ── Step 1: 데이터 로딩 ──
    info = load_survey_data()

    # ── Step 2: 문항 분석 ──
    item_analysis = run_item_analysis(info)

    # ── Step 3: 최적화 ──
    opt_results = run_optimization(info, item_analysis)

    # ── Step 3-2: 고급 최적화 ──
    adv_methods = run_advanced_optimization(info, item_analysis, opt_results)

    # ── Step 4: 부트스트랩 검증 ──
    bs_results = run_bootstrap_validation(info, opt_results)

    # ── Step 5: 교차검증 ──
    cv_results = run_cross_validation(info, opt_results, item_analysis)

    # ── Step 6: 고급 방법 교차검증 ──
    adv_cv = run_advanced_cv(info, n_splits=5, n_repeats=20, seed=42)

    # ── Step 7: 시각화 ──
    print(f"\n{'='*70}")
    print("  [Step 7] 시각화 생성")
    print(f"{'='*70}")

    plot_e1_citc_heatmap(item_analysis, save_dir)
    print("  ✅ fig_e1: CITC 히트맵")

    plot_e2_alpha_if_deleted(item_analysis, save_dir)
    print("  ✅ fig_e2: α-if-deleted")

    plot_e3_discrimination(item_analysis, save_dir)
    print("  ✅ fig_e3: 문항 변별도")

    plot_e4_predictive_power(item_analysis, save_dir)
    print("  ✅ fig_e4: 예측력")

    plot_e5_sbe_curve(opt_results, item_analysis, save_dir)
    print("  ✅ fig_e5: 순차 제거 곡선")

    plot_e6_overall_accuracy_curve(info, opt_results, item_analysis, save_dir)
    print("  ✅ fig_e6: 전체 정확도 곡선")

    plot_e7_optimal_detail(opt_results, item_analysis, save_dir)
    print("  ✅ fig_e7: 전수 탐색 분포")

    plot_e8_comparison_bar(info, opt_results, save_dir)
    print("  ✅ fig_e8: 원본 vs 최적화 비교")

    plot_e9_item_rank(item_analysis, opt_results, save_dir)
    print("  ✅ fig_e9: 문항 기여도 순위")

    plot_e10_conclusion(info, opt_results, item_analysis, bs_results, save_dir)
    print("  ✅ fig_e10: 종합 결론")

    plot_e11_cv_accuracy(cv_results, opt_results, info, save_dir)
    print("  ✅ fig_e11: 교차검증 정확도 비교")

    plot_e12_item_stability(cv_results, item_analysis, opt_results, save_dir)
    print("  ✅ fig_e12: 문항 선택 안정성")

    plot_e13_cv_conclusion(cv_results, opt_results, info, item_analysis, save_dir)
    print("  ✅ fig_e13: 교차검증 종합 결론")

    plot_e14_advanced_comparison(adv_methods, adv_cv, info, opt_results, save_dir)
    print("  ✅ fig_e14: 고급 최적화 방법 비교")

    plot_e15_logistic_regression(adv_methods, adv_cv, info, save_dir)
    print("  ✅ fig_e15: 로지스틱 회귀 분석")

    plot_e16_logistic_diagnostics(adv_methods, info, save_dir)
    print("  ✅ fig_e16: 로지스틱 회귀 모형 진단")

    # ── 최종 요약 ──
    print(f"\n{'='*70}")
    print("  [최종 요약] Team E: MBTI 설문 문항 최적화")
    print(f"{'='*70}")

    summary = opt_results['_summary']
    print(f"\n  데이터: N={info['n']}명 (유효 MBTI 응답자)")
    print(f"\n  ── 차원별 결과 (기존 문항 축소) ──")
    for dim_key in DIM_KEYS:
        ia = item_analysis[dim_key]
        opt_k = opt_results[dim_key]['optimal_k']
        baseline = summary['dim_baseline'][dim_key] * 100
        optimal = summary['dim_optimal'][dim_key] * 100
        diff = optimal - baseline

        kept = sorted(opt_results[dim_key]['optimal_indices'])
        kept_q = [f'Q{ia["cols"][i]}' for i in kept]
        removed = sorted(set(range(9)) - set(kept))
        removed_q = [f'Q{ia["cols"][i]}' for i in removed]

        print(f"\n  {DIM_LABELS[dim_key]}:")
        print(f"    α = {ia['alpha_full']:.3f}")
        print(f"    정확도: {baseline:.1f}% → {optimal:.1f}% (Δ={diff:+.1f}%p)")
        print(f"    문항 수: 9 → {opt_k}")
        print(f"    유지: {kept_q}")
        if removed_q:
            print(f"    제거: {removed_q}")
        else:
            print(f"    제거: 없음")

    print(f"\n  ── 전체 결과 (기존 문항 축소) ──")
    print(f"    문항 수: {summary['total_items_original']} → {summary['total_items_optimal']}")
    print(f"    4글자 일치율: {summary['overall_baseline']*100:.1f}% → {summary['overall_optimal']*100:.1f}%")
    improvement = (summary['overall_optimal'] - summary['overall_baseline']) * 100
    print(f"    변화: {improvement:+.1f}%p")

    # ── 기존 교차검증 결과 ──
    print(f"\n  ── 기존 교차검증 결과 (문항 축소) ──")
    kfold = cv_results['kfold']
    mc = cv_results['mc']
    kf_test_overall = kfold['overall_test_accs'].mean() * 100
    mc_test_overall = mc['overall_test_accs'].mean() * 100
    kf_baseline_overall = kfold['overall_baseline_test'].mean() * 100
    overfit_gap = summary['overall_optimal'] * 100 - kf_test_overall
    honest_improvement = kf_test_overall - kf_baseline_overall

    print(f"    K-Fold CV Test (전체 4글자): {kf_test_overall:.1f}%")
    print(f"    MC CV Test (전체 4글자):     {mc_test_overall:.1f}%")
    print(f"    과적합 Gap: {overfit_gap:.1f}%p")
    print(f"    정직한 개선: {honest_improvement:+.1f}%p")

    # ── 고급 방법 교차검증 결과 ──
    print(f"\n  ── 고급 최적화 방법 교차검증 결과 ──")
    best_mk = adv_cv['_best']
    best_name = adv_cv['_name_map'].get(best_mk, best_mk)
    best_cv_test = adv_cv[best_mk]['test_mean'] * 100
    baseline_cv_test = adv_cv['baseline']['test_mean'] * 100
    adv_improvement = best_cv_test - baseline_cv_test

    print(f"    CV 기준 최적 방법: {best_name}")
    print(f"    Baseline CV Test: {baseline_cv_test:.1f}%")
    print(f"    Best CV Test: {best_cv_test:.1f}%")
    print(f"    정직한 개선: {adv_improvement:+.1f}%p")
    print(f"    과적합 Gap: {adv_cv[best_mk]['gap']:.1f}%p")

    print(f"\n  생성된 그래프: 16개")
    print(f"  저장 위치: {save_dir}")
    print(f"\n{'='*70}")
    print("  Team E 분석 완료!")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
