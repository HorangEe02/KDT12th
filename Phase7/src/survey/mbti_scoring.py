# -*- coding: utf-8 -*-
"""
MBTI 설문 채점 체계 (Scoring System)
=====================================
설문지 52문항 중 Q7~Q38 (32문항)을 이용하여
MBTI 4차원 점수를 산출하고 16가지 유형으로 분류

채점 원리:
    - 각 차원 8문항 × 7점 리커트 척도
    - 정방향 문항: 높은 점수 → E / S / T / J 성향
    - 역방향 문항: 높은 점수 → I / N / F / P 성향 → 역채점(8-원점수)
    - 차원 점수 = 8문항 평균 (범위: 1.0 ~ 7.0)
    - 중립점(midpoint) = 4.0
    - ≥ 4.0 → E / S / T / J
    - < 4.0 → I / N / F / P

KNU 12기 Phase7 Numpy 미니프로젝트
"""

import numpy as np

# ============================================================
#  1. 문항-차원 매핑 (Question → Dimension Mapping)
# ============================================================
# 설문 문항 번호(Q7~Q38)를 CSV 컬럼 인덱스로 변환
# CSV 구조: [타임스탬프(1)] + [기본정보 Q1-Q6(6)] + [리커트 Q7-Q38(32)] + ...
# → Q7 = cols[7], Q8 = cols[8], ..., Q38 = cols[38]

SCORING_MAP = {
    # ─────────────────────────────────────────────────────
    #  E/I 차원 (에너지 방향): Q7 ~ Q14
    # ─────────────────────────────────────────────────────
    #  높은 점수(7) = 외향(E) 성향 강함
    #  낮은 점수(1) = 내향(I) 성향 강함
    'EI': {
        'name': '외향(E) — 내향(I)',
        'description': '에너지 방향: 외부 세계 vs 내면 세계',
        'high_label': 'E (외향)',
        'low_label': 'I (내향)',
        'questions': {
            # Q번호: (CSV인덱스, 방향, 문항내용)
            'Q7':  (7,  'E', '새로운 사람들을 만나면 에너지가 충전되는 느낌이다'),
            'Q8':  (8,  'I', '혼자만의 시간을 보내는 것이 휴식이 된다'),
            'Q9':  (9,  'E', '모임이나 파티에서 먼저 다가가서 대화를 시작하는 편이다'),
            'Q10': (10, 'I', '여러 명과 함께하는 것보다 소수의 친한 친구와 있는 것이 편하다'),
            'Q11': (11, 'E', '생각을 말로 표현하면서 정리하는 편이다'),
            'Q12': (12, 'I', '중요한 결정을 내리기 전에 혼자 깊이 생각하는 시간이 필요하다'),
            'Q13': (13, 'E', '조용한 환경보다 사람이 많은 활기찬 환경에서 더 잘 집중된다'),
            'Q14': (14, 'I', '처음 보는 사람에게 자신의 이야기를 쉽게 하는 편이다'),
        },
        'forward_items': [7, 9, 11, 13],    # E 방향 (그대로 사용)
        'reverse_items': [8, 10, 12, 14],    # I 방향 (역채점: 8 - 원점수)
    },

    # ─────────────────────────────────────────────────────
    #  S/N 차원 (인식 방식): Q15 ~ Q22
    # ─────────────────────────────────────────────────────
    #  높은 점수(7) = 감각(S) 성향 강함
    #  낮은 점수(1) = 직관(N) 성향 강함
    'SN': {
        'name': '감각(S) — 직관(N)',
        'description': '인식 방식: 구체적 사실 vs 전체적 패턴',
        'high_label': 'S (감각)',
        'low_label': 'N (직관)',
        'questions': {
            'Q15': (15, 'S', '현실적이고 실용적인 정보에 더 관심이 있다'),
            'Q16': (16, 'N', '미래의 가능성과 상상의 세계에 대해 자주 생각한다'),
            'Q17': (17, 'S', '세부 사항과 구체적인 사실에 주의를 기울이는 편이다'),
            'Q18': (18, 'N', '전체적인 큰 그림이나 패턴을 먼저 파악하려 한다'),
            'Q19': (19, 'S', '경험해보지 않은 새로운 방법보다는 검증된 방법을 선호한다'),
            'Q20': (20, 'N', '비유나 은유적 표현을 자주 사용하거나 이해하는 것이 쉽다'),
            'Q21': (21, 'S', '"지금 여기"에 집중하는 편이다'),
            'Q22': (22, 'N', '앞으로 일어날 일에 대한 예감이나 직감이 잘 맞는 편이다'),
        },
        'forward_items': [15, 17, 19, 21],
        'reverse_items': [16, 18, 20, 22],
    },

    # ─────────────────────────────────────────────────────
    #  T/F 차원 (판단 기준): Q23 ~ Q30
    # ─────────────────────────────────────────────────────
    #  높은 점수(7) = 사고(T) 성향 강함
    #  낮은 점수(1) = 감정(F) 성향 강함
    'TF': {
        'name': '사고(T) — 감정(F)',
        'description': '판단 기준: 논리/공정성 vs 감정/배려',
        'high_label': 'T (사고)',
        'low_label': 'F (감정)',
        'questions': {
            'Q23': (23, 'T', '결정을 내릴 때 논리와 객관적 사실을 가장 중요하게 생각한다'),
            'Q24': (24, 'F', '다른 사람의 감정이나 상황을 고려해서 결정하는 편이다'),
            'Q25': (25, 'T', '공정함과 일관성이 배려보다 더 중요하다고 생각한다'),
            'Q26': (26, 'F', '주변 사람의 기분을 잘 알아차리고 공감하는 편이다'),
            'Q27': (27, 'T', '비판적 피드백을 솔직하게 전달하는 것이 도움이 된다고 생각한다'),
            'Q28': (28, 'F', '갈등 상황에서 상대방의 입장을 먼저 이해하려고 노력한다'),
            'Q29': (29, 'T', '감정보다는 이성적 분석을 통해 문제를 해결하는 편이다'),
            'Q30': (30, 'F', '다른 사람을 돕거나 화합을 이루는 것에서 보람을 느낀다'),
        },
        'forward_items': [23, 25, 27, 29],
        'reverse_items': [24, 26, 28, 30],
    },

    # ─────────────────────────────────────────────────────
    #  J/P 차원 (생활 방식): Q31 ~ Q38
    # ─────────────────────────────────────────────────────
    #  높은 점수(7) = 판단(J) 성향 강함
    #  낮은 점수(1) = 인식(P) 성향 강함
    'JP': {
        'name': '판단(J) — 인식(P)',
        'description': '생활 방식: 계획/체계 vs 유연/즉흥',
        'high_label': 'J (판단)',
        'low_label': 'P (인식)',
        'questions': {
            'Q31': (31, 'J', '미리 계획을 세우고 그에 따라 행동하는 것을 좋아한다'),
            'Q32': (32, 'P', '상황에 따라 유연하게 대처하는 것을 선호한다'),
            'Q33': (33, 'J', '마감 기한은 반드시 지켜야 한다고 생각한다'),
            'Q34': (34, 'P', '여행할 때 즉흥적으로 일정을 정하는 것이 더 재미있다'),
            'Q35': (35, 'J', '할 일 목록(To-Do List)을 작성하고 체크하는 습관이 있다'),
            'Q36': (36, 'P', '여러 가지 선택지를 열어두고 마지막까지 결정을 미루는 편이다'),
            'Q37': (37, 'J', '정리정돈이 잘 된 깔끔한 환경에서 효율이 높아진다'),
            'Q38': (38, 'P', '규칙이나 절차보다는 상황에 맞게 유연하게 행동하는 것이 낫다'),
        },
        'forward_items': [31, 33, 35, 37],
        'reverse_items': [32, 34, 36, 38],
    },
}


# ============================================================
#  2. 채점 기준 (Threshold)
# ============================================================
# 7점 리커트 척도의 이론적 중앙값 = 4.0
# 이 값을 기준으로 MBTI 차원을 분류함

MIDPOINT = 4.0  # 7점 척도 중앙값

# 선호 강도 (Preference Clarity Index) 기준
PREFERENCE_STRENGTH = {
    'slight':   (4.0, 4.75),   # 약간의 선호 (0.0 ~ 0.75 차이)
    'moderate': (4.75, 5.5),   # 보통의 선호 (0.75 ~ 1.5 차이)
    'clear':    (5.5, 6.25),   # 명확한 선호 (1.5 ~ 2.25 차이)
    'very_clear': (6.25, 7.0), # 매우 명확한 선호 (2.25 ~ 3.0 차이)
}


# ============================================================
#  3. 16가지 MBTI 유형별 분류 조건
# ============================================================
MBTI_TYPE_CONDITIONS = {
    # ── 분석가 그룹 (NT) ──
    'INTJ': {'EI': '<4.0', 'SN': '<4.0', 'TF': '>=4.0', 'JP': '>=4.0',
             'name': '용의주도한 전략가', 'group': '분석가(NT)'},
    'INTP': {'EI': '<4.0', 'SN': '<4.0', 'TF': '>=4.0', 'JP': '<4.0',
             'name': '논리적인 사색가', 'group': '분석가(NT)'},
    'ENTJ': {'EI': '>=4.0', 'SN': '<4.0', 'TF': '>=4.0', 'JP': '>=4.0',
             'name': '대담한 통솔자', 'group': '분석가(NT)'},
    'ENTP': {'EI': '>=4.0', 'SN': '<4.0', 'TF': '>=4.0', 'JP': '<4.0',
             'name': '뜨거운 논쟁가', 'group': '분석가(NT)'},

    # ── 외교관 그룹 (NF) ──
    'INFJ': {'EI': '<4.0', 'SN': '<4.0', 'TF': '<4.0', 'JP': '>=4.0',
             'name': '선의의 옹호자', 'group': '외교관(NF)'},
    'INFP': {'EI': '<4.0', 'SN': '<4.0', 'TF': '<4.0', 'JP': '<4.0',
             'name': '열정적인 중재자', 'group': '외교관(NF)'},
    'ENFJ': {'EI': '>=4.0', 'SN': '<4.0', 'TF': '<4.0', 'JP': '>=4.0',
             'name': '정의로운 사회운동가', 'group': '외교관(NF)'},
    'ENFP': {'EI': '>=4.0', 'SN': '<4.0', 'TF': '<4.0', 'JP': '<4.0',
             'name': '재기발랄한 활동가', 'group': '외교관(NF)'},

    # ── 관리자 그룹 (SJ) ──
    'ISTJ': {'EI': '<4.0', 'SN': '>=4.0', 'TF': '>=4.0', 'JP': '>=4.0',
             'name': '청렴결백한 논리주의자', 'group': '관리자(SJ)'},
    'ISFJ': {'EI': '<4.0', 'SN': '>=4.0', 'TF': '<4.0', 'JP': '>=4.0',
             'name': '용감한 수호자', 'group': '관리자(SJ)'},
    'ESTJ': {'EI': '>=4.0', 'SN': '>=4.0', 'TF': '>=4.0', 'JP': '>=4.0',
             'name': '엄격한 관리자', 'group': '관리자(SJ)'},
    'ESFJ': {'EI': '>=4.0', 'SN': '>=4.0', 'TF': '<4.0', 'JP': '>=4.0',
             'name': '사교적인 외교관', 'group': '관리자(SJ)'},

    # ── 탐험가 그룹 (SP) ──
    'ISTP': {'EI': '<4.0', 'SN': '>=4.0', 'TF': '>=4.0', 'JP': '<4.0',
             'name': '만능 재주꾼', 'group': '탐험가(SP)'},
    'ISFP': {'EI': '<4.0', 'SN': '>=4.0', 'TF': '<4.0', 'JP': '<4.0',
             'name': '호기심 많은 예술가', 'group': '탐험가(SP)'},
    'ESTP': {'EI': '>=4.0', 'SN': '>=4.0', 'TF': '>=4.0', 'JP': '<4.0',
             'name': '모험을 즐기는 사업가', 'group': '탐험가(SP)'},
    'ESFP': {'EI': '>=4.0', 'SN': '>=4.0', 'TF': '<4.0', 'JP': '<4.0',
             'name': '자유로운 연예인', 'group': '탐험가(SP)'},
}


# ============================================================
#  4. 채점 함수
# ============================================================

def reverse_score(value, scale_max=7):
    """역채점: (척도최대값+1) - 원점수

    7점 척도: 8 - 원점수
    예) 원점수 1 → 7, 원점수 7 → 1
    """
    return (scale_max + 1) - value


def compute_dimension_score(responses, dimension_key):
    """단일 차원 점수 계산

    Parameters
    ----------
    responses : dict
        {Q번호(int): 응답값(int)} 형태. 예: {7: 5, 8: 3, 9: 6, ...}
    dimension_key : str
        'EI', 'SN', 'TF', 'JP' 중 하나

    Returns
    -------
    dict
        score: 차원 점수 (1.0~7.0)
        letter: 분류된 알파벳 (E/I, S/N, T/F, J/P)
        strength: 선호 강도 텍스트
        distance: 중립점(4.0)으로부터의 거리
        item_scores: 각 문항별 (역채점 후) 점수
    """
    dim_info = SCORING_MAP[dimension_key]
    forward = dim_info['forward_items']
    reverse = dim_info['reverse_items']

    item_scores = []

    for q_num in forward:
        raw = responses.get(q_num, 4)  # 미응답 시 중립값
        item_scores.append(raw)

    for q_num in reverse:
        raw = responses.get(q_num, 4)
        item_scores.append(reverse_score(raw))

    # 차원 점수 = 8문항 평균
    score = np.mean(item_scores)

    # 분류
    high_letter = dimension_key[0]  # E, S, T, J
    low_letter = dimension_key[1]   # I, N, F, P

    if score >= MIDPOINT:
        letter = high_letter
        distance = score - MIDPOINT
    else:
        letter = low_letter
        distance = MIDPOINT - score

    # 선호 강도 판정
    abs_score = max(score, 8 - score)  # 중립에서의 편향 정도
    strength = get_preference_strength(distance)

    return {
        'score': round(score, 2),
        'letter': letter,
        'strength': strength,
        'distance': round(distance, 2),
        'item_scores': item_scores,
        'raw_items': {
            'forward': {q: responses.get(q, 4) for q in forward},
            'reverse': {q: responses.get(q, 4) for q in reverse},
        }
    }


def get_preference_strength(distance):
    """중립점으로부터의 거리 → 선호 강도 텍스트"""
    if distance < 0.75:
        return '약간 (Slight)'
    elif distance < 1.5:
        return '보통 (Moderate)'
    elif distance < 2.25:
        return '명확 (Clear)'
    else:
        return '매우 명확 (Very Clear)'


def compute_all_dimensions(responses):
    """4개 차원 모두 계산

    Parameters
    ----------
    responses : dict
        {Q번호(int): 응답값(int)}. Q7~Q38까지 32개 키.

    Returns
    -------
    dict
        dimensions: 각 차원별 결과
        mbti_type: 4글자 MBTI 유형
        type_info: 유형 설명
        profile: 차원별 점수 프로필
    """
    dimensions = {}
    mbti_letters = []

    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        result = compute_dimension_score(responses, dim_key)
        dimensions[dim_key] = result
        mbti_letters.append(result['letter'])

    mbti_type = ''.join(mbti_letters)
    type_info = MBTI_TYPE_CONDITIONS.get(mbti_type, {})

    return {
        'dimensions': dimensions,
        'mbti_type': mbti_type,
        'type_name': type_info.get('name', '알 수 없음'),
        'type_group': type_info.get('group', '알 수 없음'),
        'profile': {
            'EI': dimensions['EI']['score'],
            'SN': dimensions['SN']['score'],
            'TF': dimensions['TF']['score'],
            'JP': dimensions['JP']['score'],
        }
    }


def compute_from_csv_row(row_values, start_col=7):
    """CSV 한 행 → MBTI 결과 계산

    Parameters
    ----------
    row_values : array-like
        CSV 한 행의 전체 값 (타임스탬프 포함)
    start_col : int
        리커트 문항 시작 컬럼 인덱스 (기본: 7 = Q7)

    Returns
    -------
    dict
        compute_all_dimensions()의 결과
    """
    responses = {}
    for q_num in range(7, 39):  # Q7 ~ Q38
        col_idx = start_col + (q_num - 7)
        if col_idx < len(row_values):
            try:
                responses[q_num] = int(float(row_values[col_idx]))
            except (ValueError, TypeError):
                responses[q_num] = 4  # 결측치 → 중립
        else:
            responses[q_num] = 4

    return compute_all_dimensions(responses)


def batch_compute_from_array(data_array, start_col=7):
    """numpy 2D 배열 전체 → MBTI 유형 일괄 분류

    Parameters
    ----------
    data_array : np.ndarray
        (n_respondents, n_columns) 형태
    start_col : int
        리커트 문항 시작 컬럼

    Returns
    -------
    dict
        types: np.array of MBTI types (str)
        scores: dict of {dim_key: np.array of scores}
        results: list of individual results
    """
    n = data_array.shape[0]
    types = []
    scores = {'EI': [], 'SN': [], 'TF': [], 'JP': []}
    results = []

    for i in range(n):
        result = compute_from_csv_row(data_array[i], start_col)
        types.append(result['mbti_type'])
        for dim_key in ['EI', 'SN', 'TF', 'JP']:
            scores[dim_key].append(result['dimensions'][dim_key]['score'])
        results.append(result)

    return {
        'types': np.array(types),
        'scores': {k: np.array(v) for k, v in scores.items()},
        'results': results,
    }


# ============================================================
#  5. 출력/리포트 함수
# ============================================================

def print_scoring_guide():
    """채점 체계 전체 출력"""
    print("=" * 70)
    print("  MBTI 설문 채점 체계 (Scoring System)")
    print("=" * 70)

    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│  ■ 채점 원리                                            │")
    print("│    · 각 차원: 8문항 × 7점 리커트 척도                   │")
    print("│    · 정방향 문항(4개): 점수 그대로 사용                  │")
    print("│    · 역방향 문항(4개): 역채점 (8 - 원점수)              │")
    print("│    · 차원 점수 = 8문항 평균 (범위: 1.0 ~ 7.0)          │")
    print("│    · 기준점 = 4.0 (7점 척도 이론적 중앙값)              │")
    print("└─────────────────────────────────────────────────────────┘")

    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│  ■ 분류 기준                                            │")
    print("│                                                         │")
    print("│    차원점수 ≥ 4.0  →  E / S / T / J                    │")
    print("│    차원점수 < 4.0  →  I / N / F / P                    │")
    print("│                                                         │")
    print("│  ■ 선호 강도 (중립점 4.0으로부터의 거리)                │")
    print("│    |d| < 0.75   : 약간의 선호 (Slight)                  │")
    print("│    0.75 ≤ |d| < 1.50 : 보통의 선호 (Moderate)          │")
    print("│    1.50 ≤ |d| < 2.25 : 명확한 선호 (Clear)             │")
    print("│    2.25 ≤ |d|  : 매우 명확한 선호 (Very Clear)         │")
    print("└─────────────────────────────────────────────────────────┘")

    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        dim = SCORING_MAP[dim_key]
        print(f"\n{'━' * 70}")
        print(f"  {dim['name']} — {dim['description']}")
        print(f"{'━' * 70}")
        print(f"  점수 높음(→7) = {dim['high_label']}  |  점수 낮음(→1) = {dim['low_label']}")
        print()

        print(f"  ▷ 정방향 문항 (점수 그대로 사용):")
        for q_num in dim['forward_items']:
            q_key = f'Q{q_num}'
            _, direction, text = dim['questions'][q_key]
            print(f"    Q{q_num}. [{direction}] {text}")

        print(f"\n  ▷ 역방향 문항 (역채점: 8 - 원점수):")
        for q_num in dim['reverse_items']:
            q_key = f'Q{q_num}'
            _, direction, text = dim['questions'][q_key]
            print(f"    Q{q_num}. [{direction}] {text}  → 역채점")

    print(f"\n{'=' * 70}")
    print(f"  16가지 MBTI 유형 분류 조건")
    print(f"{'=' * 70}")
    print(f"\n  {'유형':<6} {'EI점수':<12} {'SN점수':<12} {'TF점수':<12} {'JP점수':<12} {'별명'}")
    print(f"  {'─'*6} {'─'*10}   {'─'*10}   {'─'*10}   {'─'*10}   {'─'*20}")

    for mbti_type in ['ISTJ','ISFJ','INFJ','INTJ',
                       'ISTP','ISFP','INFP','INTP',
                       'ESTP','ESFP','ENFP','ENTP',
                       'ESTJ','ESFJ','ENFJ','ENTJ']:
        info = MBTI_TYPE_CONDITIONS[mbti_type]
        ei = '< 4.0 (I)' if info['EI'] == '<4.0' else '≥ 4.0 (E)'
        sn = '< 4.0 (N)' if info['SN'] == '<4.0' else '≥ 4.0 (S)'
        tf = '< 4.0 (F)' if info['TF'] == '<4.0' else '≥ 4.0 (T)'
        jp = '< 4.0 (P)' if info['JP'] == '<4.0' else '≥ 4.0 (J)'
        print(f"  {mbti_type:<6} {ei:<12} {sn:<12} {tf:<12} {jp:<12} {info['name']}")


def print_individual_result(result):
    """개인 결과 상세 출력"""
    print(f"\n{'─' * 60}")
    print(f"  📊 MBTI 분류 결과: {result['mbti_type']}  — {result['type_name']}")
    print(f"     그룹: {result['type_group']}")
    print(f"{'─' * 60}")

    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        dim = result['dimensions'][dim_key]
        dim_info = SCORING_MAP[dim_key]

        # 점수 바 시각화
        score = dim['score']
        bar_len = 30
        pos = int((score - 1) / 6 * bar_len)
        bar = '░' * pos + '█' + '░' * (bar_len - pos - 1)

        print(f"\n  [{dim_key}] {dim_info['name']}")
        print(f"       점수: {score:.2f} / 7.00")
        print(f"       분류: {dim['letter']} ({dim['strength']})")
        print(f"       거리: {dim['distance']:.2f} (중립점 4.0 기준)")
        print(f"       {dim_info['low_label']} |{bar}| {dim_info['high_label']}")
        print(f"                    1.0        4.0        7.0")


def print_scoring_example():
    """채점 예시 출력"""
    print("\n" + "=" * 70)
    print("  채점 예시: 응답자 A")
    print("=" * 70)

    # 예시 응답 (ISTJ 성향)
    example_responses = {
        # E/I: 내향 성향 (I)
        7: 2, 8: 6, 9: 3, 10: 7, 11: 2, 12: 6, 13: 1, 14: 3,
        # S/N: 감각 성향 (S)
        15: 6, 16: 2, 17: 7, 18: 3, 19: 6, 20: 2, 21: 5, 22: 3,
        # T/F: 사고 성향 (T)
        23: 6, 24: 3, 25: 5, 26: 2, 27: 6, 28: 3, 29: 7, 30: 2,
        # J/P: 판단 성향 (J)
        31: 7, 32: 2, 33: 6, 34: 1, 35: 7, 36: 2, 37: 6, 38: 2,
    }

    print("\n  [E/I 차원 채점 과정]")
    print("  ─────────────────────────────────────────────")
    ei_info = SCORING_MAP['EI']

    print("  정방향 문항 (E):")
    forward_sum = 0
    for q in ei_info['forward_items']:
        raw = example_responses[q]
        forward_sum += raw
        print(f"    Q{q}: 원점수 {raw} → 그대로 {raw}")

    print("  역방향 문항 (I → E로 역채점):")
    reverse_sum = 0
    for q in ei_info['reverse_items']:
        raw = example_responses[q]
        rev = 8 - raw
        reverse_sum += rev
        print(f"    Q{q}: 원점수 {raw} → 역채점 (8-{raw}) = {rev}")

    total = forward_sum + reverse_sum
    avg = total / 8
    print(f"\n  합계: {forward_sum} + {reverse_sum} = {total}")
    print(f"  평균: {total} ÷ 8 = {avg:.2f}")
    print(f"  판정: {avg:.2f} {'≥' if avg >= 4.0 else '<'} 4.0 → {'E (외향)' if avg >= 4.0 else 'I (내향)'}")

    # 전체 결과
    result = compute_all_dimensions(example_responses)
    print_individual_result(result)


# ============================================================
#  6. 메인 실행
# ============================================================

if __name__ == '__main__':
    # 1) 채점 가이드 출력
    print_scoring_guide()

    # 2) 채점 예시 출력
    print_scoring_example()

    print("\n" + "=" * 70)
    print("  사용법 안내")
    print("=" * 70)
    print("""
  ■ 개별 응답 채점:
    from mbti_scoring import compute_all_dimensions

    responses = {7: 5, 8: 3, 9: 6, 10: 2, ..., 38: 4}
    result = compute_all_dimensions(responses)
    print(result['mbti_type'])  # 예: 'ENFP'

  ■ CSV 일괄 채점:
    from mbti_scoring import batch_compute_from_array
    import pandas as pd

    df = pd.read_csv('survey_responses.csv')
    batch = batch_compute_from_array(df.values, start_col=7)
    print(batch['types'])    # 전체 MBTI 유형 배열
    print(batch['scores'])   # 차원별 점수 배열

  ■ analyze_survey.py에서 활용:
    scores = compute_dimension_scores(df)  → 기존 함수 대체 가능
    mbti_types = classify_mbti(scores)     → 기존 함수 대체 가능
""")
