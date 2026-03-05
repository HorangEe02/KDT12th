# -*- coding: utf-8 -*-
"""
데이터 로딩 모듈
CSV 파일을 pandas로 읽은 후 numpy 배열로 변환하여 반환합니다.
"""

import numpy as np
import pandas as pd
from .config import RAW_DIR


# ============================================================
# 1. 개인 성격 데이터 (data.csv - 43,745행)
# ============================================================
def load_personality_data():
    """
    data.csv 로딩 (Kaggle: Predict People Personality Types)

    컬럼: Age, Gender, Education, Introversion Score,
          Sensing Score, Thinking Score, Judging Score,
          Interest, Personality

    Returns:
        dict: numpy 배열 딕셔너리
            - age: float64 (나이)
            - gender: str (Male/Female)
            - education: int32 (0 또는 1)
            - introversion: float64 (내향-외향 점수)
            - sensing: float64 (감각-직관 점수)
            - thinking: float64 (사고-감정 점수)
            - judging: float64 (판단-인식 점수)
            - interest: str (관심사 분야)
            - personality: str (MBTI 유형)
    """
    df = pd.read_csv(RAW_DIR / 'data.csv')

    return {
        'age': df['Age'].to_numpy(dtype=np.float64),
        'gender': df['Gender'].to_numpy(),
        'education': df['Education'].to_numpy(dtype=np.int32),
        'introversion': df['Introversion Score'].to_numpy(dtype=np.float64),
        'sensing': df['Sensing Score'].to_numpy(dtype=np.float64),
        'thinking': df['Thinking Score'].to_numpy(dtype=np.float64),
        'judging': df['Judging Score'].to_numpy(dtype=np.float64),
        'interest': df['Interest'].to_numpy(),
        'personality': df['Personality'].to_numpy(),
    }


# ============================================================
# 2. 국가별 MBTI 분포 (countries.csv - 158국)
# ============================================================
def load_countries_mbti():
    """
    countries.csv 로딩 (Kaggle: MBTI-TYPES)

    32개 MBTI variant (16유형 × Assertive/Turbulent) 비율

    Returns:
        dict:
            - countries: ndarray (국가명)
            - mbti_32: ndarray (158 × 32, MBTI variant 비율)
            - mbti_16: ndarray (158 × 16, 기본 유형별 합산 비율)
            - mbti_dims: ndarray (158 × 8, E/I/S/N/T/F/J/P 비율)
            - col_names_32: list (32개 variant 컬럼명)
            - type_names_16: list (16개 기본 유형명)
    """
    df = pd.read_csv(RAW_DIR / 'countries.csv')

    countries = df['Country'].to_numpy()
    col_names_32 = [c for c in df.columns if c != 'Country']
    mbti_32 = df[col_names_32].to_numpy(dtype=np.float64)

    # 16 기본 유형으로 합산 (A + T)
    type_names_16 = ['ESTJ', 'ESFJ', 'INFP', 'ENFP', 'ISFJ',
                     'ENFJ', 'ESTP', 'ISTJ', 'INTP', 'INFJ',
                     'ISFP', 'ENTJ', 'ESFP', 'ENTP', 'INTJ',
                     'ISTP']
    mbti_16 = np.zeros((len(countries), 16), dtype=np.float64)

    for i, base_type in enumerate(type_names_16):
        a_col = f'{base_type}-A'
        t_col = f'{base_type}-T'
        a_idx = col_names_32.index(a_col) if a_col in col_names_32 else None
        t_idx = col_names_32.index(t_col) if t_col in col_names_32 else None

        if a_idx is not None:
            mbti_16[:, i] += mbti_32[:, a_idx]
        if t_idx is not None:
            mbti_16[:, i] += mbti_32[:, t_idx]

    # 8 차원 비율 (E/I/S/N/T/F/J/P)
    dim_map = {
        'E': ['ESTJ', 'ESFJ', 'ENFP', 'ENFJ', 'ESTP', 'ESFP', 'ENTP', 'ENTJ'],
        'I': ['INFP', 'ISFJ', 'ISTJ', 'INTP', 'INFJ', 'ISFP', 'INTJ', 'ISTP'],
        'S': ['ESTJ', 'ESFJ', 'ISFJ', 'ESTP', 'ISTJ', 'ESFP', 'ISFP', 'ISTP'],
        'N': ['INFP', 'ENFP', 'ENFJ', 'INTP', 'INFJ', 'ENTP', 'INTJ', 'ENTJ'],
        'T': ['ESTJ', 'ESTP', 'ISTJ', 'INTP', 'ENTJ', 'ENTP', 'INTJ', 'ISTP'],
        'F': ['ESFJ', 'INFP', 'ENFP', 'ISFJ', 'ENFJ', 'INFJ', 'ESFP', 'ISFP'],
        'J': ['ESTJ', 'ESFJ', 'ISFJ', 'ENFJ', 'ISTJ', 'INFJ', 'ENTJ', 'INTJ'],
        'P': ['INFP', 'ENFP', 'ESTP', 'INTP', 'ESFP', 'ENTP', 'ISFP', 'ISTP'],
    }

    dim_names = ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']
    mbti_dims = np.zeros((len(countries), 8), dtype=np.float64)

    for d, dim in enumerate(dim_names):
        for t in dim_map[dim]:
            idx = type_names_16.index(t)
            mbti_dims[:, d] += mbti_16[:, idx]

    return {
        'countries': countries,
        'mbti_32': mbti_32,
        'mbti_16': mbti_16,
        'mbti_dims': mbti_dims,
        'col_names_32': col_names_32,
        'type_names_16': type_names_16,
        'dim_names': dim_names,
    }


# ============================================================
# 3. 국가별 혈액형 분포 (blood_type_distribution.csv - 127국)
# ============================================================
def load_blood_type_distribution():
    """
    blood_type_distribution.csv 로딩

    Returns:
        dict:
            - countries: ndarray (국가명)
            - population: ndarray (인구수)
            - blood_8: ndarray (127 × 8, O+/A+/B+/AB+/O-/A-/B-/AB-)
            - blood_4: ndarray (127 × 4, A/B/O/AB 합산)
            - continent: ndarray (대륙 코드)
    """
    df = pd.read_csv(RAW_DIR / 'blood_type_distribution.csv')

    countries = df['Country'].to_numpy()
    population = df['Population'].to_numpy(dtype=np.float64)
    continent = df['Continent'].to_numpy()

    blood_cols_8 = ['O+', 'A+', 'B+', 'AB+', 'O-', 'A-', 'B-', 'AB-']
    blood_8 = df[blood_cols_8].to_numpy(dtype=np.float64)

    # 4대 혈액형 합산
    blood_4 = np.zeros((len(countries), 4), dtype=np.float64)
    blood_4[:, 0] = blood_8[:, 1] + blood_8[:, 5]  # A = A+ + A-
    blood_4[:, 1] = blood_8[:, 2] + blood_8[:, 6]  # B = B+ + B-
    blood_4[:, 2] = blood_8[:, 0] + blood_8[:, 4]  # O = O+ + O-
    blood_4[:, 3] = blood_8[:, 3] + blood_8[:, 7]  # AB = AB+ + AB-

    return {
        'countries': countries,
        'population': population,
        'blood_8': blood_8,
        'blood_4': blood_4,
        'continent': continent,
        'blood_cols_8': blood_cols_8,
        'blood_names_4': ['A', 'B', 'O', 'AB'],
    }


# ============================================================
# 4. MBTI 유형 설명 (types.csv)
# ============================================================
def load_types_reference():
    """
    types.csv 로딩 (MBTI 유형별 설명 정보)

    Returns:
        dict:
            - types: ndarray (유형명)
            - nicknames: ndarray (유형 별명)
            - descriptions: ndarray (유형 설명)
    """
    df = pd.read_csv(RAW_DIR / 'types.csv')

    return {
        'types': df['Type'].to_numpy(),
        'nicknames': df['Nickname'].to_numpy() if 'Nickname' in df.columns else None,
        'descriptions': df['Description'].to_numpy() if 'Description' in df.columns else None,
    }


# ============================================================
# 5. 한국 MBTI 분포 (korea_mbti_distribution.csv)
# ============================================================
def load_korea_mbti():
    """
    korea_mbti_distribution.csv 로딩 (TestMoa 2023, 표본 104,484명)

    Returns:
        dict:
            - types: ndarray (MBTI 유형명, 순위순)
            - percentages: ndarray (비율 %)
            - counts: ndarray (인원수)
            - sample_total: int (전체 표본 수)
    """
    df = pd.read_csv(RAW_DIR / 'korea_mbti_distribution.csv')

    return {
        'types': df['mbti_type'].to_numpy(),
        'percentages': df['percentage'].to_numpy(dtype=np.float64),
        'counts': df['count'].to_numpy(dtype=np.int64),
        'sample_total': int(df['sample_total'].iloc[0]),
    }


# ============================================================
# 6. 한국 혈액형 분포 (korea_bloodtype_distribution.csv)
# ============================================================
def load_korea_bloodtype():
    """
    korea_bloodtype_distribution.csv 로딩

    Returns:
        dict:
            - types: ndarray (혈액형)
            - percentages: ndarray (비율 %)
    """
    df = pd.read_csv(RAW_DIR / 'korea_bloodtype_distribution.csv')

    return {
        'types': df['blood_type'].to_numpy(),
        'percentages': df['korea_pct'].to_numpy(dtype=np.float64),
    }


# ============================================================
# 7. 한국 연도별 헌혈 통계 (korea_bloodtype_by_year.csv)
# ============================================================
def load_korea_bloodtype_yearly():
    """
    korea_bloodtype_by_year.csv 로딩 (2014-2023)

    Returns:
        dict:
            - years: ndarray (연도)
            - total_donations: ndarray (연간 헌혈 건수)
            - counts: ndarray (10 × 4, A/B/O/AB별 건수)
            - percentages: ndarray (10 × 4, A/B/O/AB별 비율)
    """
    df = pd.read_csv(RAW_DIR / 'korea_bloodtype_by_year.csv')

    counts = np.column_stack([
        df['A_count'].to_numpy(dtype=np.float64),
        df['B_count'].to_numpy(dtype=np.float64),
        df['O_count'].to_numpy(dtype=np.float64),
        df['AB_count'].to_numpy(dtype=np.float64),
    ])

    percentages = np.column_stack([
        df['A_pct'].to_numpy(dtype=np.float64),
        df['B_pct'].to_numpy(dtype=np.float64),
        df['O_pct'].to_numpy(dtype=np.float64),
        df['AB_pct'].to_numpy(dtype=np.float64),
    ])

    return {
        'years': df['year'].to_numpy(dtype=np.int32),
        'total_donations': df['total_donations'].to_numpy(dtype=np.int64),
        'counts': counts,
        'percentages': percentages,
    }


# ============================================================
# 8. 한국 혈액형 성격 관련 설문 (korea_bloodtype_personality_survey.csv)
# ============================================================
def load_korea_bloodtype_survey():
    """
    korea_bloodtype_personality_survey.csv 로딩 (한국갤럽 설문)

    Returns:
        dict: 카테고리별 딕셔너리
            - blood_dist: {혈액형: 비율}
            - personality_belief: {항목: 비율}
            - belief_yearly: {연도: 비율}
            - preferred_blood: {혈액형: 비율}
            - compatibility_belief: {항목: 비율}
    """
    df = pd.read_csv(RAW_DIR / 'korea_bloodtype_personality_survey.csv')

    result = {}

    # 카테고리별 분리
    for category in df['category'].unique():
        sub = df[df['category'] == category]
        items = sub['item'].to_numpy()
        values = sub['value'].to_numpy(dtype=np.float64)
        result[category] = dict(zip(items, values))

    return result


# ============================================================
# 9. 한국 혈액형 성격론 믿음 추이 (korea_bloodtype_belief.csv)
# ============================================================
def load_korea_bloodtype_belief():
    """
    korea_bloodtype_belief.csv 로딩 (2004-2023 4개 시점)

    Returns:
        dict:
            - years: ndarray (조사 연도)
            - believe_pct: ndarray (관련있다 비율)
            - not_related_pct: ndarray (관련없다 비율)
            - dont_know_pct: ndarray (모르겠다 비율)
            - sample_size: ndarray (표본크기)
    """
    df = pd.read_csv(RAW_DIR / 'korea_bloodtype_belief.csv')

    return {
        'years': df['year'].to_numpy(dtype=np.int32),
        'believe_pct': df['believe_related_pct'].to_numpy(dtype=np.float64),
        'not_related_pct': df['not_related_pct'].to_numpy(dtype=np.float64),
        'dont_know_pct': df['dont_know_pct'].to_numpy(dtype=np.float64),
        'sample_size': df['sample_size'].to_numpy(dtype=np.int32),
    }
