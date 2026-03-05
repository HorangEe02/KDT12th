# -*- coding: utf-8 -*-
"""
Numpy 기반 통계 함수 모음
scipy 없이 numpy만으로 주요 통계 검정을 구현합니다.

구현 함수:
- 기술통계: descriptive_stats, frequency_table
- 카이제곱 검정: chi_square_test, chi_square_goodness_of_fit
- t-검정: independent_t_test
- 분산분석: one_way_anova
- 상관분석: pearson_correlation, correlation_matrix
- 회귀분석: linear_regression, multiple_linear_regression
- 로지스틱 회귀: logistic_regression_train, logistic_regression_predict
- 신뢰구간: confidence_interval, proportion_confidence_interval
- 효과크기: cohens_d, cramers_v
- 보조함수: norm_cdf, sigmoid, standardize_features, linear_trend, skewness, kurtosis
"""

import numpy as np


# ============================================================
# 표준정규분포 CDF 근사 (Abramowitz & Stegun 방법)
# ============================================================
def norm_cdf(z):
    """
    표준정규분포 누적분포함수(CDF) 근사
    Abramowitz & Stegun 26.2.17 근사법 사용 (정확도 ±1.5e-7)

    Parameters:
        z (float or ndarray): 표준화된 값
    Returns:
        float or ndarray: 누적 확률 P(Z ≤ z)
    """
    z = np.asarray(z, dtype=np.float64)

    # 상수
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = np.where(z < 0, -1.0, 1.0)
    z_abs = np.abs(z)

    t = 1.0 / (1.0 + p * z_abs)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-z_abs * z_abs / 2.0)

    result = 0.5 * (1.0 + sign * y)
    return float(result) if result.ndim == 0 else result


def norm_ppf(p):
    """
    표준정규분포 역함수 (percent point function) 근사
    Beasley-Springer-Moro 근사법 사용

    Parameters:
        p (float): 확률값 (0 < p < 1)
    Returns:
        float: z 값
    """
    if p <= 0 or p >= 1:
        raise ValueError("p는 0과 1 사이여야 합니다")

    # Rational approximation
    if p < 0.5:
        t = np.sqrt(-2.0 * np.log(p))
    else:
        t = np.sqrt(-2.0 * np.log(1.0 - p))

    # 계수
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    z = t - (c0 + c1 * t + c2 * t**2) / (1 + d1 * t + d2 * t**2 + d3 * t**3)

    if p < 0.5:
        return -z
    else:
        return z


# ============================================================
# 기술통계
# ============================================================
def descriptive_stats(arr):
    """
    기술통계량 계산

    Parameters:
        arr (ndarray): 1D 숫자 배열
    Returns:
        dict: 평균, 중앙값, 표준편차, 분산, 최소, 최대, Q1, Q3, IQR, 왜도, 첨도
    """
    arr = np.asarray(arr, dtype=np.float64)
    arr = arr[~np.isnan(arr)]  # NaN 제거

    n = len(arr)
    mean = np.mean(arr)
    median = np.median(arr)
    std = np.std(arr, ddof=1)
    var = np.var(arr, ddof=1)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)

    return {
        'n': n,
        '평균': mean,
        '중앙값': median,
        '표준편차': std,
        '분산': var,
        '최소': np.min(arr),
        '최대': np.max(arr),
        'Q1': q1,
        'Q3': q3,
        'IQR': q3 - q1,
        '왜도': skewness(arr),
        '첨도': kurtosis(arr),
    }


def frequency_table(arr):
    """
    범주형 변수의 빈도표 및 비율 계산

    Parameters:
        arr (ndarray): 1D 범주형 배열
    Returns:
        dict: {카테고리: {'빈도': n, '비율': pct}}
    """
    unique, counts = np.unique(arr, return_counts=True)
    total = len(arr)
    result = {}
    for u, c in zip(unique, counts):
        result[u] = {
            '빈도': int(c),
            '비율': c / total * 100
        }
    return result


def skewness(arr):
    """
    왜도(Skewness) 계산 — Fisher's 정의
    skew = (1/n) * Σ((xi - x̄) / s)^3
    """
    arr = np.asarray(arr, dtype=np.float64)
    n = len(arr)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return 0.0
    return (n / ((n - 1) * (n - 2))) * np.sum(((arr - mean) / std) ** 3)


def kurtosis(arr):
    """
    첨도(Kurtosis) 계산 — 초과 첨도 (정규분포 = 0)
    """
    arr = np.asarray(arr, dtype=np.float64)
    n = len(arr)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return 0.0
    m4 = np.mean((arr - mean) ** 4)
    return m4 / (std ** 4) - 3.0


# ============================================================
# 카이제곱 검정
# ============================================================
def chi_square_test(observed):
    """
    카이제곱 독립성 검정

    관측 빈도 행렬(2D)에서 기대빈도를 계산하고
    카이제곱 통계량, 자유도, p-value를 반환합니다.

    Parameters:
        observed (ndarray): 2D 관측 빈도 행렬 (행 × 열)
    Returns:
        dict: chi2(통계량), dof(자유도), p_value, expected(기대빈도),
              significant(유의 여부), cramers_v(효과크기)
    """
    observed = np.asarray(observed, dtype=np.float64)

    row_totals = observed.sum(axis=1, keepdims=True)
    col_totals = observed.sum(axis=0, keepdims=True)
    grand_total = observed.sum()

    # 기대빈도: E_ij = (행합_i × 열합_j) / 전체합
    expected = (row_totals * col_totals) / grand_total

    # 카이제곱 통계량: χ² = Σ (O - E)² / E
    chi2 = np.sum((observed - expected) ** 2 / expected)

    # 자유도
    r, c = observed.shape
    dof = (r - 1) * (c - 1)

    # p-value 근사 (Wilson-Hilferty 정규 근사법)
    p_value = _chi2_p_value(chi2, dof)

    # Cramer's V 효과크기
    min_dim = min(r, c) - 1
    v = np.sqrt(chi2 / (grand_total * min_dim)) if min_dim > 0 else 0.0

    return {
        'chi2': chi2,
        'dof': dof,
        'p_value': p_value,
        'expected': expected,
        'significant': p_value < 0.05,
        'cramers_v': v,
    }


def chi_square_goodness_of_fit(observed, expected):
    """
    카이제곱 적합도 검정

    관측값이 기대분포를 따르는지 검정합니다.

    Parameters:
        observed (ndarray): 1D 관측 빈도 배열
        expected (ndarray): 1D 기대 빈도 배열
    Returns:
        dict: chi2, dof, p_value, significant
    """
    observed = np.asarray(observed, dtype=np.float64)
    expected = np.asarray(expected, dtype=np.float64)

    chi2 = np.sum((observed - expected) ** 2 / expected)
    dof = len(observed) - 1
    p_value = _chi2_p_value(chi2, dof)

    return {
        'chi2': chi2,
        'dof': dof,
        'p_value': p_value,
        'significant': p_value < 0.05,
    }


def _chi2_p_value(chi2, dof):
    """
    카이제곱 분포 p-value 근사 (Wilson-Hilferty 정규 근사법)

    z = ((χ²/df)^(1/3) - (1 - 2/(9*df))) / sqrt(2/(9*df))
    p = 1 - Φ(z)
    """
    if dof <= 0:
        return 1.0
    if chi2 <= 0:
        return 1.0

    # Wilson-Hilferty 근사
    z = ((chi2 / dof) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * dof))) / np.sqrt(2.0 / (9.0 * dof))

    p_value = 1.0 - norm_cdf(z)
    return max(0.0, min(1.0, p_value))


# ============================================================
# t-검정
# ============================================================
def independent_t_test(group1, group2):
    """
    독립표본 t-검정 (Welch's t-test)

    두 집단의 평균 차이가 통계적으로 유의한지 검정합니다.
    등분산을 가정하지 않는 Welch 방법을 사용합니다.

    Parameters:
        group1 (ndarray): 첫 번째 집단 데이터
        group2 (ndarray): 두 번째 집단 데이터
    Returns:
        dict: t_stat, dof, p_value, mean_diff, ci_95, cohens_d, significant
    """
    g1 = np.asarray(group1, dtype=np.float64)
    g2 = np.asarray(group2, dtype=np.float64)
    g1 = g1[~np.isnan(g1)]
    g2 = g2[~np.isnan(g2)]

    n1, n2 = len(g1), len(g2)
    mean1, mean2 = np.mean(g1), np.mean(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)

    # t-통계량
    se = np.sqrt(var1 / n1 + var2 / n2)
    t_stat = (mean1 - mean2) / se if se > 0 else 0.0

    # Welch-Satterthwaite 자유도 근사
    num = (var1 / n1 + var2 / n2) ** 2
    den = (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
    dof = num / den if den > 0 else 1.0

    # p-value (양측 검정, 대표본에서 t → z 근사)
    p_value = 2.0 * (1.0 - norm_cdf(abs(t_stat)))

    # 95% 신뢰구간
    z_crit = 1.96
    mean_diff = mean1 - mean2
    ci_lower = mean_diff - z_crit * se
    ci_upper = mean_diff + z_crit * se

    # Cohen's d 효과크기
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0.0

    return {
        't_stat': t_stat,
        'dof': dof,
        'p_value': p_value,
        'mean_diff': mean_diff,
        'ci_95': (ci_lower, ci_upper),
        'cohens_d': d,
        'significant': p_value < 0.05,
        'mean1': mean1,
        'mean2': mean2,
        'std1': np.sqrt(var1),
        'std2': np.sqrt(var2),
        'n1': n1,
        'n2': n2,
    }


# ============================================================
# 분산분석 (ANOVA)
# ============================================================
def one_way_anova(*groups):
    """
    일원분산분석 (One-Way ANOVA)

    3개 이상 집단의 평균이 모두 같은지 검정합니다.

    Parameters:
        *groups: 가변 인자로 각 집단의 데이터 배열
    Returns:
        dict: f_stat, dof_between, dof_within, p_value,
              group_means, group_stds, group_ns,
              eta_squared(효과크기), significant
    """
    k = len(groups)  # 집단 수
    groups_clean = [np.asarray(g, dtype=np.float64)[~np.isnan(np.asarray(g, dtype=np.float64))] for g in groups]

    ns = np.array([len(g) for g in groups_clean])
    N = np.sum(ns)
    means = np.array([np.mean(g) for g in groups_clean])
    stds = np.array([np.std(g, ddof=1) for g in groups_clean])
    grand_mean = np.sum([np.sum(g) for g in groups_clean]) / N

    # SSB (집단 간 변동): Σ n_i * (x̄_i - x̄)²
    ssb = np.sum(ns * (means - grand_mean) ** 2)

    # SSW (집단 내 변동): ΣΣ (x_ij - x̄_i)²
    ssw = np.sum([np.sum((g - np.mean(g)) ** 2) for g in groups_clean])

    # SST (전체 변동)
    sst = ssb + ssw

    # 자유도
    df_between = k - 1
    df_within = N - k

    # F-통계량
    msb = ssb / df_between
    msw = ssw / df_within if df_within > 0 else 1.0
    f_stat = msb / msw if msw > 0 else 0.0

    # p-value (F분포 근사)
    p_value = _f_p_value(f_stat, df_between, df_within)

    # η² (Eta-squared) 효과크기
    eta_sq = ssb / sst if sst > 0 else 0.0

    return {
        'f_stat': f_stat,
        'dof_between': df_between,
        'dof_within': df_within,
        'p_value': p_value,
        'group_means': means,
        'group_stds': stds,
        'group_ns': ns,
        'ssb': ssb,
        'ssw': ssw,
        'sst': sst,
        'eta_squared': eta_sq,
        'significant': p_value < 0.05,
    }


def _f_p_value(f_stat, df1, df2):
    """
    F분포 p-value 근사 (정규 근사법)

    대표본에서의 근사: z ≈ ((f * df1 / df2)^(1/3) - ...) / ...
    """
    if f_stat <= 0 or df1 <= 0 or df2 <= 0:
        return 1.0

    # Approximation using Wilson-Hilferty for F-distribution
    # Convert F to chi-square approximation
    x = f_stat * df1
    v = df1

    # For the numerator chi-square
    z1 = ((x / v) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * v))) / np.sqrt(2.0 / (9.0 * v))

    # Simple normal approximation
    # More accurate for large df2
    a = 2.0 / (9.0 * df1)
    b = 2.0 / (9.0 * df2)
    z = ((1.0 - b) * (f_stat ** (1.0 / 3.0)) - (1.0 - a)) / np.sqrt(b * f_stat ** (2.0 / 3.0) + a)

    p_value = 1.0 - norm_cdf(z)
    return max(0.0, min(1.0, p_value))


# ============================================================
# 상관분석
# ============================================================
def pearson_correlation(x, y):
    """
    피어슨 상관계수 및 유의성 검정

    r = Σ((xi - x̄)(yi - ȳ)) / √(Σ(xi - x̄)² × Σ(yi - ȳ)²)
    t = r × √(n-2) / √(1-r²)

    Parameters:
        x (ndarray): 1D 배열
        y (ndarray): 1D 배열
    Returns:
        dict: r(상관계수), p_value, t_stat, n, significant,
              strength(상관강도 해석)
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # NaN 제거 (pairwise)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)

    if n < 3:
        return {'r': 0.0, 'p_value': 1.0, 't_stat': 0.0, 'n': n,
                'significant': False, 'strength': '데이터 부족'}

    # 상관계수 계산
    x_mean, y_mean = np.mean(x), np.mean(y)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sqrt(np.sum((x - x_mean) ** 2) * np.sum((y - y_mean) ** 2))

    r = numerator / denominator if denominator > 0 else 0.0

    # t-통계량 및 p-value
    if abs(r) >= 1.0:
        t_stat = np.inf
        p_value = 0.0
    else:
        t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r ** 2)
        p_value = 2.0 * (1.0 - norm_cdf(abs(t_stat)))

    # 상관 강도 해석
    abs_r = abs(r)
    if abs_r < 0.1:
        strength = '무시할 수준'
    elif abs_r < 0.3:
        strength = '약한 상관'
    elif abs_r < 0.5:
        strength = '보통 상관'
    elif abs_r < 0.7:
        strength = '강한 상관'
    else:
        strength = '매우 강한 상관'

    return {
        'r': r,
        'p_value': p_value,
        't_stat': t_stat,
        'n': n,
        'significant': p_value < 0.05,
        'strength': strength,
    }


def correlation_matrix(data):
    """
    다변량 데이터의 상관계수 행렬 계산

    Parameters:
        data (ndarray): 2D 배열 (n_samples × n_features)
    Returns:
        ndarray: 상관계수 행렬 (n_features × n_features)
    """
    data = np.asarray(data, dtype=np.float64)
    return np.corrcoef(data, rowvar=False)


# ============================================================
# 회귀분석
# ============================================================
def linear_regression(x, y):
    """
    단순선형회귀분석

    y = slope * x + intercept

    최소자승법(OLS)으로 기울기와 절편을 계산합니다.
    slope = Σ((xi - x̄)(yi - ȳ)) / Σ(xi - x̄)²
    intercept = ȳ - slope × x̄

    Parameters:
        x (ndarray): 독립변수
        y (ndarray): 종속변수
    Returns:
        dict: slope, intercept, r_squared, p_value, std_error,
              y_pred(예측값), residuals(잔차)
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # NaN 제거
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)

    x_mean, y_mean = np.mean(x), np.mean(y)

    # 기울기와 절편
    ss_xy = np.sum((x - x_mean) * (y - y_mean))
    ss_xx = np.sum((x - x_mean) ** 2)

    slope = ss_xy / ss_xx if ss_xx > 0 else 0.0
    intercept = y_mean - slope * x_mean

    # 예측값과 잔차
    y_pred = slope * x + intercept
    residuals = y - y_pred

    # R²
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # 표준오차
    se = np.sqrt(ss_res / (n - 2)) if n > 2 else 0.0
    se_slope = se / np.sqrt(ss_xx) if ss_xx > 0 else 0.0

    # t-통계량 및 p-value (기울기)
    t_stat = slope / se_slope if se_slope > 0 else 0.0
    p_value = 2.0 * (1.0 - norm_cdf(abs(t_stat)))

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'p_value': p_value,
        'std_error': se_slope,
        't_stat': t_stat,
        'y_pred': y_pred,
        'residuals': residuals,
        'n': n,
        'significant': p_value < 0.05,
    }


# ============================================================
# 신뢰구간
# ============================================================
def confidence_interval(arr, confidence=0.95):
    """
    평균의 신뢰구간 계산

    CI = x̄ ± z × (s / √n)

    Parameters:
        arr (ndarray): 1D 숫자 배열
        confidence (float): 신뢰수준 (기본 0.95)
    Returns:
        dict: mean, lower, upper, margin_of_error, n, std
    """
    arr = np.asarray(arr, dtype=np.float64)
    arr = arr[~np.isnan(arr)]

    n = len(arr)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)

    # z 임계값
    alpha = 1 - confidence
    z = norm_ppf(1 - alpha / 2)

    margin = z * std / np.sqrt(n)

    return {
        'mean': mean,
        'lower': mean - margin,
        'upper': mean + margin,
        'margin_of_error': margin,
        'n': n,
        'std': std,
    }


def proportion_confidence_interval(p_hat, n, confidence=0.95):
    """
    비율의 신뢰구간 계산

    CI = p̂ ± z × √(p̂(1-p̂)/n)

    Parameters:
        p_hat (float): 표본 비율 (0~1)
        n (int): 표본 크기
        confidence (float): 신뢰수준
    Returns:
        dict: proportion, lower, upper, margin_of_error
    """
    alpha = 1 - confidence
    z = norm_ppf(1 - alpha / 2)

    se = np.sqrt(p_hat * (1 - p_hat) / n)
    margin = z * se

    return {
        'proportion': p_hat,
        'lower': max(0.0, p_hat - margin),
        'upper': min(1.0, p_hat + margin),
        'margin_of_error': margin,
        'n': n,
    }


# ============================================================
# 효과크기
# ============================================================
def cohens_d(group1, group2):
    """
    Cohen's d 효과크기

    d = (mean1 - mean2) / pooled_std

    해석: |d| < 0.2 작음, 0.2~0.5 보통, 0.5~0.8 큼, > 0.8 매우 큼
    """
    g1 = np.asarray(group1, dtype=np.float64)
    g2 = np.asarray(group2, dtype=np.float64)

    n1, n2 = len(g1), len(g2)
    var1 = np.var(g1, ddof=1)
    var2 = np.var(g2, ddof=1)

    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    d = (np.mean(g1) - np.mean(g2)) / pooled_std if pooled_std > 0 else 0.0

    # 해석
    abs_d = abs(d)
    if abs_d < 0.2:
        interpretation = '작은 효과'
    elif abs_d < 0.5:
        interpretation = '보통 효과'
    elif abs_d < 0.8:
        interpretation = '큰 효과'
    else:
        interpretation = '매우 큰 효과'

    return {'d': d, 'interpretation': interpretation}


def cramers_v(chi2_stat, n, min_dim):
    """
    Cramer's V 효과크기

    V = √(χ² / (n × (min(r,c) - 1)))

    해석: V < 0.1 무시, 0.1~0.3 약, 0.3~0.5 보통, > 0.5 강
    """
    if min_dim <= 1 or n <= 0:
        return {'v': 0.0, 'interpretation': '계산 불가'}

    v = np.sqrt(chi2_stat / (n * (min_dim - 1)))

    if v < 0.1:
        interpretation = '무시할 수준'
    elif v < 0.3:
        interpretation = '약한 연관'
    elif v < 0.5:
        interpretation = '보통 연관'
    else:
        interpretation = '강한 연관'

    return {'v': v, 'interpretation': interpretation}


# ============================================================
# 시계열 추세분석
# ============================================================
def linear_trend(years, values):
    """
    시계열 선형 추세 분석

    최소자승법으로 시간에 따른 선형 추세를 분석합니다.

    Parameters:
        years (ndarray): 연도 배열
        values (ndarray): 관측값 배열
    Returns:
        dict: slope(연간 변화율), intercept, r_squared, p_value,
              trend_direction(추세 방향), predicted(추세선 값)
    """
    result = linear_regression(np.asarray(years, dtype=np.float64),
                                np.asarray(values, dtype=np.float64))

    if result['slope'] > 0:
        direction = '증가 추세'
    elif result['slope'] < 0:
        direction = '감소 추세'
    else:
        direction = '변화 없음'

    result['trend_direction'] = direction
    result['predicted'] = result['y_pred']
    return result


# ============================================================
# 다중선형회귀분석
# ============================================================
def multiple_linear_regression(X, y):
    """
    다중선형회귀분석 (numpy np.linalg.lstsq 기반)

    여러 독립변수를 사용하여 종속변수를 예측하는 다중회귀모형을 적합합니다.

    Parameters:
        X (ndarray): 2D 독립변수 행렬 (n_samples × n_features, 절편 미포함)
        y (ndarray): 1D 종속변수 배열

    Returns:
        dict: betas (절편 포함 계수), r_squared, adj_r_squared,
              f_stat, p_value, se_betas (표준오차), t_stats (t통계량),
              p_values_betas (개별 계수 p-value), y_pred, n, k,
              residuals, mse
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    n = len(y)
    k = X.shape[1]  # 독립변수 수

    # 절편 열 추가
    X_aug = np.column_stack([np.ones(n), X])

    # 최소자승법
    betas, _, _, _ = np.linalg.lstsq(X_aug, y, rcond=None)

    # 예측값 및 잔차
    y_pred = X_aug @ betas
    residuals = y - y_pred

    # R² 및 수정 R²
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    adj_r_squared = 1.0 - (1.0 - r_squared) * (n - 1) / (n - k - 1)

    # F-통계량
    if k > 0 and (n - k - 1) > 0:
        ms_reg = (ss_tot - ss_res) / k
        ms_res = ss_res / (n - k - 1)
        f_stat = ms_reg / ms_res if ms_res > 0 else 0.0
    else:
        f_stat = 0.0

    # F p-value (Wilson-Hilferty 근사)
    df1, df2 = k, n - k - 1
    if f_stat > 0 and df1 > 0 and df2 > 0:
        x_wh = ((f_stat * df1 / df2) ** (1/3) - (1 - 2/(9*df2))) / \
               np.sqrt(2/(9*df2))
        f_p_value = 1.0 - norm_cdf(x_wh)
    else:
        f_p_value = 1.0

    # 개별 계수 표준오차 및 t-검정
    mse = ss_res / (n - k - 1) if (n - k - 1) > 0 else 0.0
    try:
        cov_matrix = np.linalg.inv(X_aug.T @ X_aug) * mse
        se_betas = np.sqrt(np.diag(cov_matrix))
    except np.linalg.LinAlgError:
        se_betas = np.full(k + 1, np.nan)

    t_stats = np.where(se_betas > 0, betas / se_betas, 0.0)

    # 개별 계수 p-value (양측검정, 정규 근사)
    p_values_betas = np.array([2.0 * (1.0 - norm_cdf(abs(t))) for t in t_stats])

    return {
        'betas': betas,
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        'f_stat': f_stat,
        'p_value': f_p_value,
        'se_betas': se_betas,
        't_stats': t_stats,
        'p_values_betas': p_values_betas,
        'y_pred': y_pred,
        'residuals': residuals,
        'mse': mse,
        'n': n,
        'k': k,
        'significant': f_p_value < 0.05,
    }


# ============================================================
# 유틸리티 함수
# ============================================================
def print_test_result(test_name, result, alpha=0.05):
    """
    통계 검정 결과를 한글로 출력하는 유틸리티 함수
    """
    print(f"\n{'='*60}")
    print(f"  {test_name}")
    print(f"{'='*60}")

    if 'chi2' in result:
        print(f"  카이제곱 통계량 (χ²) = {result['chi2']:.4f}")
        print(f"  자유도 (df)          = {result['dof']}")
    if 't_stat' in result and 'chi2' not in result:
        print(f"  t-통계량              = {result['t_stat']:.4f}")
        if 'dof' in result:
            print(f"  자유도 (df)          = {result['dof']:.1f}")
    if 'f_stat' in result:
        print(f"  F-통계량              = {result['f_stat']:.4f}")
        print(f"  집단 간 자유도 (dfB)  = {result['dof_between']}")
        print(f"  집단 내 자유도 (dfW)  = {result['dof_within']}")
    if 'r' in result:
        print(f"  상관계수 (r)          = {result['r']:.4f}")
        print(f"  상관 강도             = {result['strength']}")
    if 'slope' in result:
        print(f"  기울기 (slope)        = {result['slope']:.6f}")
        print(f"  절편 (intercept)      = {result['intercept']:.4f}")
        print(f"  R²                    = {result['r_squared']:.4f}")

    if 'p_value' in result:
        print(f"  p-value               = {result['p_value']:.6f}")
        print(f"  유의수준 (α)          = {alpha}")

        if result['p_value'] < alpha:
            print(f"  ▶ 결론: 귀무가설 기각 (p < {alpha}) — 통계적으로 유의함")
        else:
            print(f"  ▶ 결론: 귀무가설 채택 (p ≥ {alpha}) — 통계적으로 유의하지 않음")

    if 'cramers_v' in result:
        print(f"  Cramer's V            = {result['cramers_v']:.4f}")
    if 'cohens_d' in result:
        print(f"  Cohen's d             = {result['cohens_d']:.4f}")
    if 'eta_squared' in result:
        print(f"  η² (효과크기)         = {result['eta_squared']:.4f}")

    print(f"{'='*60}")


# ============================================================
# 로지스틱 회귀 (Logistic Regression)
# ============================================================
def sigmoid(z):
    """
    시그모이드 함수: sigma(z) = 1 / (1 + exp(-z))

    Parameters:
        z (float or ndarray): 입력값
    Returns:
        float or ndarray: 0~1 사이의 확률값
    """
    z = np.asarray(z, dtype=np.float64)
    z = np.clip(z, -500, 500)  # overflow 방지
    return 1.0 / (1.0 + np.exp(-z))


def standardize_features(X, mean=None, std=None):
    """
    특성 표준화 (Z-score normalization)

    학습 시에는 mean/std를 계산하여 반환하고,
    테스트 시에는 학습 데이터의 mean/std를 재사용합니다.

    Parameters:
        X (ndarray): 2D 특성 행렬 (n_samples x n_features)
        mean (ndarray, optional): 사전 계산된 평균 (테스트 시 사용)
        std (ndarray, optional): 사전 계산된 표준편차 (테스트 시 사용)
    Returns:
        tuple: (X_standardized, mean, std)
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if mean is None:
        mean = np.mean(X, axis=0)
    if std is None:
        std = np.std(X, axis=0, ddof=0)

    # 표준편차가 0인 특성은 1로 대체 (상수 특성 처리)
    std_safe = np.where(std == 0, 1.0, std)
    X_std = (X - mean) / std_safe

    return X_std, mean, std


def logistic_regression_train(X, y, lr=0.1, epochs=1000, lambda_reg=0.01):
    """
    로지스틱 회귀 학습 (경사하강법 + L2 정규화)

    이진 분류를 위한 로지스틱 회귀 모형을 경사하강법으로 학습합니다.
    L2 정규화(Ridge)를 적용하여 소표본에서의 과적합을 방지합니다.

    비용함수: J(w) = -1/n * [y*log(h) + (1-y)*log(1-h)] + lambda/2n * ||w||^2
    경사: dJ/dw = 1/n * X^T * (h - y) + lambda/n * w  (절편 제외)

    Parameters:
        X (ndarray): 2D 특성 행렬 (n_samples x n_features), 표준화 권장
        y (ndarray): 1D 이진 레이블 (0 또는 1)
        lr (float): 학습률 (기본 0.1)
        epochs (int): 반복 횟수 (기본 1000)
        lambda_reg (float): L2 정규화 강도 (기본 0.01)
    Returns:
        dict: weights(절편 포함), train_acc, loss_history, n_epochs
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n, k = X.shape

    # 절편 열 추가 (첫 번째 열에 1)
    X_aug = np.column_stack([np.ones(n), X])

    # 가중치 초기화 (0으로)
    weights = np.zeros(k + 1)

    loss_history = []
    eps = 1e-15  # log(0) 방지

    for epoch in range(epochs):
        # 순전파: h = sigmoid(X_aug @ w)
        z = X_aug @ weights
        h = sigmoid(z)

        # 비용 계산 (Binary Cross-Entropy + L2)
        bce = -np.mean(y * np.log(h + eps) + (1 - y) * np.log(1 - h + eps))
        l2_penalty = (lambda_reg / (2 * n)) * np.sum(weights[1:] ** 2)
        loss = bce + l2_penalty
        loss_history.append(loss)

        # 경사 계산
        gradient = (1 / n) * (X_aug.T @ (h - y))

        # L2 정규화 경사 (절편 제외)
        reg_gradient = np.zeros_like(weights)
        reg_gradient[1:] = (lambda_reg / n) * weights[1:]

        # 가중치 업데이트
        weights -= lr * (gradient + reg_gradient)

    # 학습 정확도
    h_final = sigmoid(X_aug @ weights)
    predictions = (h_final >= 0.5).astype(int)
    train_acc = np.mean(predictions == y)

    return {
        'weights': weights,       # [bias, w1, w2, ..., wk]
        'bias_included': True,
        'train_acc': train_acc,
        'loss_history': loss_history,
        'n_epochs': epochs,
        'n_features': k,
        'n_samples': n,
    }


def logistic_regression_predict(X, weights, threshold=0.5):
    """
    로지스틱 회귀 예측

    학습된 가중치를 사용하여 새로운 데이터에 대한 확률 및 클래스를 예측합니다.

    Parameters:
        X (ndarray): 2D 특성 행렬 (n_samples x n_features)
        weights (ndarray): 학습된 가중치 (절편 포함, [bias, w1, ..., wk])
        threshold (float): 분류 임계값 (기본 0.5)
    Returns:
        dict: probabilities(확률), predictions(0/1), threshold
    """
    X = np.asarray(X, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n = X.shape[0]

    # 절편 열 추가
    X_aug = np.column_stack([np.ones(n), X])

    # 확률 계산
    probabilities = sigmoid(X_aug @ weights)

    # 클래스 예측
    predictions = (probabilities >= threshold).astype(int)

    return {
        'probabilities': probabilities,
        'predictions': predictions,
        'threshold': threshold,
    }


# ============================================================
# 로지스틱 회귀 진단 (Logistic Regression Diagnostics)
# ============================================================

def compute_vif(X):
    """
    분산팽창인자(VIF) 계산 — 다중공선성 진단

    각 특성을 종속변수로 놓고 나머지 특성으로 OLS 회귀 시 R²를 구한 후
    VIF = 1 / (1 - R²)로 계산합니다.

    VIF 해석:
      - VIF < 5: 다중공선성 없음
      - 5 ≤ VIF < 10: 보통 (주의)
      - VIF ≥ 10: 심각한 다중공선성

    Parameters:
        X (ndarray): 2D 특성 행렬 (n_samples x n_features), 표준화 전 원본 권장
    Returns:
        ndarray: 각 특성의 VIF 값 (n_features,)
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n, k = X.shape
    vif_values = np.zeros(k)

    for j in range(k):
        y_j = X[:, j]
        X_others = np.delete(X, j, axis=1)

        if X_others.shape[1] == 0:
            vif_values[j] = 1.0
            continue

        # 절편 추가
        X_ols = np.column_stack([np.ones(n), X_others])

        # OLS: beta = (X'X)^{-1} X'y
        try:
            beta = np.linalg.lstsq(X_ols, y_j, rcond=None)[0]
            y_hat = X_ols @ beta
            ss_res = np.sum((y_j - y_hat) ** 2)
            ss_tot = np.sum((y_j - np.mean(y_j)) ** 2)

            if ss_tot == 0:
                vif_values[j] = float('inf')
            else:
                r2 = 1.0 - ss_res / ss_tot
                r2 = min(r2, 1.0 - 1e-15)  # 1.0 방지
                vif_values[j] = 1.0 / (1.0 - r2)
        except np.linalg.LinAlgError:
            vif_values[j] = float('inf')

    return vif_values


def logistic_log_likelihood(X, y, weights):
    """
    로지스틱 회귀 로그 우도(Log-Likelihood) 계산

    LL = Σ [y_i * log(p_i) + (1 - y_i) * log(1 - p_i)]

    Parameters:
        X (ndarray): 특성 행렬 (n_samples x n_features), 절편 미포함
        y (ndarray): 이진 레이블 (0/1)
        weights (ndarray): 학습된 가중치 (절편 포함)
    Returns:
        float: 로그 우도 값
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n = X.shape[0]
    X_aug = np.column_stack([np.ones(n), X])
    p = sigmoid(X_aug @ weights)

    eps = 1e-15
    p = np.clip(p, eps, 1 - eps)

    ll = np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    return ll


def logistic_null_log_likelihood(y):
    """
    널 모형(절편만) 로그 우도 계산

    Parameters:
        y (ndarray): 이진 레이블 (0/1)
    Returns:
        float: 널 모형 로그 우도
    """
    y = np.asarray(y, dtype=np.float64)
    p0 = np.mean(y)
    eps = 1e-15
    p0 = np.clip(p0, eps, 1 - eps)
    n = len(y)
    ll_null = n * (p0 * np.log(p0) + (1 - p0) * np.log(1 - p0))
    return ll_null


def logistic_aic_bic(X, y, weights):
    """
    로지스틱 회귀 AIC / BIC 계산

    AIC = -2 * LL + 2 * k
    BIC = -2 * LL + k * ln(n)

    여기서 k = 추정 파라미터 수 (가중치 개수 = 특성 수 + 절편)

    Parameters:
        X (ndarray): 특성 행렬 (절편 미포함)
        y (ndarray): 이진 레이블
        weights (ndarray): 학습된 가중치 (절편 포함)
    Returns:
        dict: aic, bic, log_likelihood, n_params, n_samples
    """
    ll = logistic_log_likelihood(X, y, weights)
    k = len(weights)  # 절편 + 특성 수
    n = len(y)

    aic = -2.0 * ll + 2.0 * k
    bic = -2.0 * ll + k * np.log(n)

    return {
        'aic': aic,
        'bic': bic,
        'log_likelihood': ll,
        'n_params': k,
        'n_samples': n,
    }


def logistic_mcfadden_r2(X, y, weights):
    """
    McFadden의 Pseudo R² 계산

    McFadden R² = 1 - (LL_model / LL_null)

    해석:
      - 0.2 ~ 0.4: 매우 좋은 적합 (OLS R²의 0.7~0.9에 해당)
      - > 0.4: 우수한 적합

    Parameters:
        X (ndarray): 특성 행렬 (절편 미포함)
        y (ndarray): 이진 레이블
        weights (ndarray): 학습된 가중치 (절편 포함)
    Returns:
        dict: mcfadden_r2, adjusted_mcfadden_r2, ll_model, ll_null
    """
    ll_model = logistic_log_likelihood(X, y, weights)
    ll_null = logistic_null_log_likelihood(y)

    if ll_null == 0:
        r2 = 0.0
        adj_r2 = 0.0
    else:
        r2 = 1.0 - (ll_model / ll_null)
        k = len(weights)
        adj_r2 = 1.0 - ((ll_model - k) / ll_null)

    return {
        'mcfadden_r2': r2,
        'adjusted_mcfadden_r2': adj_r2,
        'll_model': ll_model,
        'll_null': ll_null,
    }


def compute_classification_metrics(y_true, y_pred):
    """
    이진 분류 평가 지표 계산 (Precision, Recall, F1-score, Specificity)

    Parameters:
        y_true (ndarray): 실제 레이블 (0/1)
        y_pred (ndarray): 예측 레이블 (0/1)
    Returns:
        dict: accuracy, precision, recall, f1, specificity, tp, fp, tn, fn
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))

    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'specificity': specificity,
        'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn),
    }


def logistic_regression_diagnostics(X, y, weights, feature_names=None, X_raw=None):
    """
    로지스틱 회귀 종합 진단 — 모형 적합도, 다중공선성, 분류 성능 일괄 평가

    Parameters:
        X (ndarray): 특성 행렬 (절편 미포함) — 모형 평가용 (학습 시 사용한 것과 동일해야 함)
                     표준화된 X를 사용했다면 표준화된 X를 전달
        y (ndarray): 이진 레이블 (0/1)
        weights (ndarray): 학습된 가중치 (절편 포함)
        feature_names (list, optional): 특성 이름 리스트
        X_raw (ndarray, optional): VIF 계산용 원본(비표준화) 특성 행렬.
                                    None이면 X를 사용
    Returns:
        dict: vif, aic_bic, mcfadden, classification, correlation_matrix,
              condition_number, feature_names, summary_text
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    n, k = X.shape

    if feature_names is None:
        feature_names = [f'X{i+1}' for i in range(k)]

    # 1. VIF (다중공선성) — 원본 X로 계산
    X_vif = np.asarray(X_raw, dtype=np.float64) if X_raw is not None else X
    if X_vif.ndim == 1:
        X_vif = X_vif.reshape(-1, 1)
    vif = compute_vif(X_vif)

    # 2. AIC / BIC
    aic_bic = logistic_aic_bic(X, y, weights)

    # 3. McFadden R²
    mcfadden = logistic_mcfadden_r2(X, y, weights)

    # 4. 분류 성능
    pred_result = logistic_regression_predict(X, weights)
    clf_metrics = compute_classification_metrics(y, pred_result['predictions'])

    # 5. 특성 간 상관 행렬 (원본 X 기준)
    if k > 1:
        corr_matrix = np.corrcoef(X_vif.T)
    else:
        corr_matrix = np.array([[1.0]])

    # 6. 조건수 (Condition Number) — 수치 안정성
    X_aug = np.column_stack([np.ones(n), X])
    cond_number = np.linalg.cond(X_aug)

    # 7. VIF 판정
    vif_status = []
    for i, v in enumerate(vif):
        if v < 5:
            vif_status.append('양호')
        elif v < 10:
            vif_status.append('주의')
        else:
            vif_status.append('심각')

    # 8. 종합 요약 텍스트
    summary_lines = [
        f"[모형 적합도]",
        f"  Log-Likelihood: {aic_bic['log_likelihood']:.2f}",
        f"  AIC: {aic_bic['aic']:.2f}",
        f"  BIC: {aic_bic['bic']:.2f}",
        f"  McFadden R²: {mcfadden['mcfadden_r2']:.4f}",
        f"  Adjusted McFadden R²: {mcfadden['adjusted_mcfadden_r2']:.4f}",
        f"",
        f"[다중공선성 (VIF)]",
    ]
    for i, (name, v, s) in enumerate(zip(feature_names, vif, vif_status)):
        summary_lines.append(f"  {name}: VIF={v:.2f} ({s})")

    summary_lines.extend([
        f"",
        f"[분류 성능]",
        f"  Accuracy: {clf_metrics['accuracy']:.4f}",
        f"  Precision: {clf_metrics['precision']:.4f}",
        f"  Recall: {clf_metrics['recall']:.4f}",
        f"  F1-score: {clf_metrics['f1']:.4f}",
        f"  Specificity: {clf_metrics['specificity']:.4f}",
        f"",
        f"[수치 안정성]",
        f"  조건수(Condition Number): {cond_number:.1f}",
    ])

    return {
        'vif': vif,
        'vif_status': vif_status,
        'aic_bic': aic_bic,
        'mcfadden': mcfadden,
        'classification': clf_metrics,
        'correlation_matrix': corr_matrix,
        'condition_number': cond_number,
        'feature_names': feature_names,
        'summary_text': '\n'.join(summary_lines),
    }
