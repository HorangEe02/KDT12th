# -*- coding: utf-8 -*-
"""
MBTI 밈 설문 v2 채점 체계 (Scoring System)
==========================================
create_mbti_meme_survey_v2.js 로 생성된 Google Form 응답(46문항)에서
MBTI 4차원 점수를 산출하고 16가지 유형으로 분류

설문 구조:
    Q1-Q5   : 기본 정보 (MBTI, 혈액형, 성별, 나이대, 검사방법)
    Q6-Q14  : E/I 차원 (9문항, 7점 리커트)
    Q15-Q23 : S/N 차원 (9문항, 7점 양극 척도)
    Q24-Q32 : T/F 차원 (9문항, 7점 양극 척도)
    Q33-Q41 : J/P 차원 (9문항, 7점 양극 척도)
    Q42-Q46 : 보너스 밈 인식 (5문항)

채점 원리:
    ■ E/I 차원 (단일 방향 — 전체 I방향)
      - 전체 9문항(Q6~Q14): 높은 점수 → 내향(I) 성향
      - 채점: 전체 역채점(8-원점수) → 높은 점수 = 외향(E) 성향
      - 결과: 높은 점수 = 외향(E) 성향 (v1과 동일 컨벤션)

    ■ S/N 차원 (단일 방향)
      - 원래 척도: 1=S(현실) ↔ 7=N(상상)
      - 채점: 전체 역채점(8-원점수) → 높은 점수 = 감각(S) 성향
      - 결과: v1과 동일 컨벤션 (≥4.0 → S)

    ■ T/F 차원 (단일 방향)
      - 원래 척도: 1=T(논리) ↔ 7=F(감정)
      - 채점: 전체 역채점(8-원점수) → 높은 점수 = 사고(T) 성향
      - 결과: v1과 동일 컨벤션 (≥4.0 → T)

    ■ J/P 차원 (단일 방향)
      - 원래 척도: 1=J(계획) ↔ 7=P(즉흥)
      - 채점: 전체 역채점(8-원점수) → 높은 점수 = 판단(J) 성향
      - 결과: v1과 동일 컨벤션 (≥4.0 → J)

    ■ 분류 기준
      - 차원 점수 ≥ 4.0 → E / S / T / J (첫 번째 글자)
      - 차원 점수 < 4.0 → I / N / F / P (두 번째 글자)

KNU 12기 Phase7 Numpy 미니프로젝트
"""

import numpy as np


# ============================================================
#  1. CSV 컬럼 매핑 (v2 설문지 구조)
# ============================================================
# Google Form → 스프레드시트 응답 CSV 컬럼 인덱스
# Col 0  : 타임스탬프
# Col 1  : Q1 MBTI (드롭다운)
# Col 2  : Q2 혈액형 (객관식)
# Col 3  : Q3 성별 (객관식)
# Col 4  : Q4 나이대 (객관식)
# Col 5  : Q5 MBTI 검사 방법 (객관식)
# Col 6-14 : Q6-Q14 E/I 리커트 (숫자 1-7)
# Col 15-23: Q15-Q23 S/N 양극 척도 (숫자 1-7)
# Col 24-32: Q24-Q32 T/F 양극 척도 (숫자 1-7)
# Col 33-41: Q33-Q41 J/P 양극 척도 (숫자 1-7)
# Col 42 : Q42 MBTI 신뢰도 (1-7)
# Col 43 : Q43 혈액형 신뢰도 (1-7)
# Col 44 : Q44 "너 T야?" 사용 여부 (객관식)
# Col 45 : Q45 MBTI 태도 변화 (객관식)
# Col 46 : Q46 최종 생각 (객관식)
# Col 47 : 자유의견 (텍스트)

V2_COL_MAP = {
    'timestamp':    0,
    'self_mbti':    1,
    'blood_type':   2,
    'gender':       3,
    'age':          4,
    'test_method':  5,
    # 리커트 문항 시작/끝
    'ei_start':     6,   'ei_end':   14,    # Q6-Q14 (9문항)
    'sn_start':     15,  'sn_end':   23,    # Q15-Q23 (9문항)
    'tf_start':     24,  'tf_end':   32,    # Q24-Q32 (9문항)
    'jp_start':     33,  'jp_end':   41,    # Q33-Q41 (9문항)
    # 보너스
    'mbti_trust':   42,  # Q42 MBTI 신뢰도 (1-7)
    'blood_trust':  43,  # Q43 혈액형 신뢰도 (1-7)
    'are_you_t':    44,  # Q44 "너 T야?" 사용 빈도
    'mbti_attitude': 45, # Q45 MBTI 태도 변화
    'final_opinion': 46, # Q46 최종 생각
    'free_text':    47,  # 자유의견
}

# 리커트 문항 전체 범위 (채점 대상)
LIKERT_START_COL = 6    # Q6 = CSV col 6
LIKERT_END_COL = 41     # Q41 = CSV col 41
N_LIKERT_ITEMS = 36     # 9문항 × 4차원


# ============================================================
#  2. 문항-차원 매핑 (v2 전용)
# ============================================================

SCORING_MAP_V2 = {
    # ─────────────────────────────────────────────────────
    #  E/I 차원: Q6~Q14 (9문항, 단일 방향 — 전체 I방향)
    # ─────────────────────────────────────────────────────
    #  채점 후 높은 점수 = E (외향) 성향
    #  전체 I방향 문항 → 전체 역채점
    'EI': {
        'name': '외향(E) — 내향(I)',
        'description': '에너지 방향: 인싸 vs 아싸 (집순이/집돌이 감별기)',
        'high_label': 'E (외향)',
        'low_label': 'I (내향)',
        'n_items': 9,
        'csv_cols': list(range(6, 15)),  # col 6~14
        'questions': {
            'Q6':  (6,  'I', '주말을 침대에서 보내고 싶다'),
            'Q7':  (7,  'I', '약속 취소됐다는 연락 → 은근히 좋다'),
            'Q8':  (8,  'I', '주중에는 회사(실외)였으니 주말엔 집에 있어야 한다'),
            'Q9':  (9,  'I', '놀고 난 후 → 집에서 혼자 충전해야지'),
            'Q10': (10, 'I', '몇 개월 집 밖 안 나가도 잘 살 수 있다'),
            'Q11': (11, 'I', '당일 갑자기 잡히는 약속이 힘들다'),
            'Q12': (12, 'I', '볼일 많으면 하루에 몰아서 끝낸다'),
            'Q13': (13, 'I', '새로운 모임 → 집에 빨리 가고 싶다'),
            'Q14': (14, 'I', '빈 강의실에 벽 근처에 앉는다'),
        },
        # 전체 I방향 → 전체 역채점 (역채점 후 높으면 E)
        'forward_cols': [],
        'reverse_cols': [6, 7, 8, 9, 10, 11, 12, 13, 14],  # Q6~Q14 전체 (I방향)
    },

    # ─────────────────────────────────────────────────────
    #  S/N 차원: Q15~Q23 (9문항, 단일 방향)
    # ─────────────────────────────────────────────────────
    #  원래 척도: 1=S(현실적), 7=N(상상적)
    #  채점: 전체 역채점 → 높은 점수 = S (감각)
    'SN': {
        'name': '감각(S) — 직관(N)',
        'description': '인식 방식: 현실주의자 vs 몽상가 (사과 하면? 밈)',
        'high_label': 'S (감각)',
        'low_label': 'N (직관)',
        'n_items': 9,
        'csv_cols': list(range(15, 24)),  # col 15~23
        'questions': {
            'Q15': (15, 'N', '과제 깜빡 → ①현실적 반응 ↔ ⑦극단적 상상'),
            'Q16': (16, 'N', '축제 구경 → ①눈앞 무대 ↔ ⑦내가 참가하는 상상'),
            'Q17': (17, 'N', '망상 스타일 → ①현실 기반 ↔ ⑦판타지급'),
            'Q18': (18, 'N', '드라마·영화 → ①고증 체크 ↔ ⑦2차 창작'),
            'Q19': (19, 'N', '성과 부진 → ①원인 분석 ↔ ⑦파국적 상상'),
            'Q20': (20, 'N', '버스 창밖 → ①현실적 관찰 ↔ ⑦타인 상상'),
            'Q21': (21, 'N', '사과 하면? → ①감각적 묘사 ↔ ⑦연상·상징'),
            'Q22': (22, 'N', '시험 공부 → ①실전 해결책 ↔ ⑦이상 세계 상상'),
            'Q23': (23, 'N', '소풍 전날 → ①준비 체크리스트 ↔ ⑦만약의 시나리오'),
        },
        # 전체 역채점 (원래 high=N → 역채점 후 high=S)
        'forward_cols': [],
        'reverse_cols': list(range(15, 24)),
    },

    # ─────────────────────────────────────────────────────
    #  T/F 차원: Q24~Q32 (9문항, 단일 방향)
    # ─────────────────────────────────────────────────────
    #  원래 척도: 1=T(논리), 7=F(감정)
    #  채점: 전체 역채점 → 높은 점수 = T (사고)
    'TF': {
        'name': '사고(T) — 감정(F)',
        'description': '판단 기준: "너 T야?" 밸런스 게임',
        'high_label': 'T (사고)',
        'low_label': 'F (감정)',
        'n_items': 9,
        'csv_cols': list(range(24, 33)),  # col 24~32
        'questions': {
            'Q24': (24, 'F', '친구 고민 → ①해결책 제시 ↔ ⑦공감 먼저'),
            'Q25': (25, 'F', '"아무도 안 좋아해" → ①담담 ↔ ⑦속상'),
            'Q26': (26, 'F', '"아는 척 하지마" → ①논리 반박 ↔ ⑦감정 상처'),
            'Q27': (27, 'F', '친구 차 사고 → ①보험사 불렀어? ↔ ⑦괜찮아?'),
            'Q28': (28, 'F', '"재능 있다!" → ①팩트 집중 ↔ ⑦뉘앙스 집중'),
            'Q29': (29, 'F', '칭찬 스타일 → ①객관적 ↔ ⑦공감형'),
            'Q30': (30, 'F', '"나 살 쪘지?" → ①솔직 팩트 ↔ ⑦감성 케어'),
            'Q31': (31, 'F', '"죽을 수 있어" → ①팩트 폭격 ↔ ⑦감정 보호'),
            'Q32': (32, 'F', '설문 부탁 → ①귀찮음 솔직 ↔ ⑦의리 챙김'),
        },
        # 전체 역채점 (원래 high=F → 역채점 후 high=T)
        'forward_cols': [],
        'reverse_cols': list(range(24, 33)),
    },

    # ─────────────────────────────────────────────────────
    #  J/P 차원: Q33~Q41 (9문항, 단일 방향)
    # ─────────────────────────────────────────────────────
    #  원래 척도: 1=J(계획), 7=P(즉흥)
    #  채점: 전체 역채점 → 높은 점수 = J (판단)
    'JP': {
        'name': '판단(J) — 인식(P)',
        'description': '생활 방식: 계획충 vs 즉흥충 (여행 엑셀 밈)',
        'high_label': 'J (판단)',
        'low_label': 'P (인식)',
        'n_items': 9,
        'csv_cols': list(range(33, 42)),  # col 33~41
        'questions': {
            'Q33': (33, 'P', '여행 준비 → ①엑셀 완벽 계획 ↔ ⑦발길 닿는 대로'),
            'Q34': (34, 'P', '스마트폰 → ①0개 알림 ↔ ⑦999+ 기본'),
            'Q35': (35, 'P', '식당 휴업 → ①플랜 B ↔ ⑦즉석 발견'),
            'Q36': (36, 'P', '마감 과제 → ①미리미리 ↔ ⑦전날 벼락치기'),
            'Q37': (37, 'P', '여행 짐 → ①체크리스트 ↔ ⑦대충 쑤셔넣기'),
            'Q38': (38, 'P', '마트 → ①리스트대로 ↔ ⑦충동 장바구니'),
            'Q39': (39, 'P', '방/책상 → ①각 잡힌 정리 ↔ ⑦나만의 카오스'),
            'Q40': (40, 'P', '요리 → ①정량 정순서 ↔ ⑦감으로 대충'),
            'Q41': (41, 'P', '금요일 밤 → ①타임라인 완성 ↔ ⑦알람 OFF 늦잠'),
        },
        # 전체 역채점 (원래 high=P → 역채점 후 high=J)
        'forward_cols': [],
        'reverse_cols': list(range(33, 42)),
    },
}


# ============================================================
#  3. 채점 기준 (v1과 동일)
# ============================================================
MIDPOINT = 4.0  # 7점 척도 중앙값

PREFERENCE_STRENGTH = {
    'slight':     (0.0,  0.75),   # 약간의 선호
    'moderate':   (0.75, 1.50),   # 보통의 선호
    'clear':      (1.50, 2.25),   # 명확한 선호
    'very_clear': (2.25, 3.00),   # 매우 명확한 선호
}


# ============================================================
#  4. 16가지 MBTI 유형 (v1과 동일)
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
#  5. 채점 함수
# ============================================================

def reverse_score(value, scale_max=7):
    """역채점: (척도최대값+1) - 원점수

    7점 척도: 8 - 원점수
    예) 원점수 1 -> 7, 원점수 7 -> 1
    """
    return (scale_max + 1) - value


def compute_dimension_score_v2(responses, dimension_key):
    """v2 설문 단일 차원 점수 계산

    Parameters
    ----------
    responses : dict
        {Q번호(int): 응답값(int)} 형태. 예: {6: 5, 7: 3, ..., 14: 6}
        Q번호는 CSV 컬럼 인덱스와 동일 (Q6=6, Q7=7, ...)
    dimension_key : str
        'EI', 'SN', 'TF', 'JP' 중 하나

    Returns
    -------
    dict
        score: 차원 점수 (1.0~7.0, 높을수록 E/S/T/J)
        letter: 분류된 알파벳
        strength: 선호 강도 텍스트
        distance: 중립점(4.0)으로부터의 거리
        item_scores: 각 문항별 (채점 후) 점수
        raw_scores: 각 문항별 원점수
    """
    dim_info = SCORING_MAP_V2[dimension_key]
    forward_cols = dim_info['forward_cols']
    reverse_cols = dim_info['reverse_cols']

    item_scores = []
    raw_scores = []

    # forward 문항: 그대로 사용
    for col in forward_cols:
        raw = responses.get(col, 4)  # 미응답 시 중립값
        item_scores.append(raw)
        raw_scores.append(raw)

    # reverse 문항: 역채점
    for col in reverse_cols:
        raw = responses.get(col, 4)
        item_scores.append(reverse_score(raw))
        raw_scores.append(raw)

    # 차원 점수 = N문항 평균
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
    strength = get_preference_strength(distance)

    return {
        'score': round(float(score), 2),
        'letter': letter,
        'strength': strength,
        'distance': round(float(distance), 2),
        'item_scores': item_scores,
        'raw_scores': raw_scores,
        'raw_items': {
            'forward': {col: responses.get(col, 4) for col in forward_cols},
            'reverse': {col: responses.get(col, 4) for col in reverse_cols},
        }
    }


def get_preference_strength(distance):
    """중립점으로부터의 거리 -> 선호 강도 텍스트"""
    if distance < 0.75:
        return '약간 (Slight)'
    elif distance < 1.5:
        return '보통 (Moderate)'
    elif distance < 2.25:
        return '명확 (Clear)'
    else:
        return '매우 명확 (Very Clear)'


def compute_all_dimensions_v2(responses):
    """v2 설문 4개 차원 모두 계산

    Parameters
    ----------
    responses : dict
        {Q번호(int): 응답값(int)}. Q6~Q41까지 36개 키.
        Q번호 = CSV 컬럼 인덱스

    Returns
    -------
    dict
        dimensions: 각 차원별 결과
        mbti_type: 4글자 MBTI 유형
        type_name: 유형 별명
        type_group: 유형 그룹
        profile: 차원별 점수 프로필
    """
    dimensions = {}
    mbti_letters = []

    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        result = compute_dimension_score_v2(responses, dim_key)
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


def compute_from_csv_row_v2(row_values):
    """v2 CSV 한 행 -> MBTI 결과 계산

    Parameters
    ----------
    row_values : array-like
        CSV 한 행의 전체 값 (타임스탬프 포함)

    Returns
    -------
    dict
        compute_all_dimensions_v2()의 결과
    """
    responses = {}
    for col in range(LIKERT_START_COL, LIKERT_END_COL + 1):
        if col < len(row_values):
            try:
                responses[col] = int(float(row_values[col]))
            except (ValueError, TypeError):
                responses[col] = 4  # 결측치 -> 중립
        else:
            responses[col] = 4

    return compute_all_dimensions_v2(responses)


def batch_compute_from_array_v2(data_array):
    """v2 numpy 2D 배열 전체 -> MBTI 유형 일괄 분류

    Parameters
    ----------
    data_array : np.ndarray
        (n_respondents, n_columns) 형태

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
        result = compute_from_csv_row_v2(data_array[i])
        types.append(result['mbti_type'])
        for dim_key in ['EI', 'SN', 'TF', 'JP']:
            scores[dim_key].append(result['dimensions'][dim_key]['score'])
        results.append(result)

    return {
        'types': np.array(types),
        'scores': {k: np.array(v) for k, v in scores.items()},
        'results': results,
    }


def compute_raw_dimension_scores_v2(data_array):
    """원점수 기반 차원 점수 (역채점 하지 않은 자연 방향)

    원점수 그대로의 의미를 분석할 때 사용 (예: E/I 원점수 높으면 I 성향)

    Parameters
    ----------
    data_array : np.ndarray

    Returns
    -------
    dict
        raw_scores: {dim_key: np.array} - 원점수 평균 (역채점 안 함)
    """
    n = data_array.shape[0]
    raw_scores = {'EI': [], 'SN': [], 'TF': [], 'JP': []}

    for i in range(n):
        for dim_key in ['EI', 'SN', 'TF', 'JP']:
            dim_info = SCORING_MAP_V2[dim_key]
            cols = dim_info['csv_cols']
            values = []
            for col in cols:
                if col < data_array.shape[1]:
                    try:
                        values.append(int(float(data_array[i, col])))
                    except (ValueError, TypeError):
                        values.append(4)
                else:
                    values.append(4)
            raw_scores[dim_key].append(np.mean(values))

    return {k: np.array(v) for k, v in raw_scores.items()}


# ============================================================
#  6. 보너스 문항 추출
# ============================================================

def extract_bonus_data(data_array):
    """v2 보너스 문항(Q42-Q46) 데이터 추출

    Returns
    -------
    dict
        mbti_trust: Q42 MBTI 신뢰도 (1-7 리커트)
        blood_trust: Q43 혈액형 신뢰도 (1-7 리커트)
        are_you_t: Q44 "너 T야?" 사용 (문자열)
        mbti_attitude: Q45 MBTI 태도 변화 (문자열)
        final_opinion: Q46 최종 생각 (문자열)
    """
    n = data_array.shape[0]
    result = {
        'mbti_trust': np.zeros(n),
        'blood_trust': np.zeros(n),
        'are_you_t': [],
        'mbti_attitude': [],
        'final_opinion': [],
    }

    for i in range(n):
        # Q42, Q43: 리커트 (숫자)
        try:
            result['mbti_trust'][i] = float(data_array[i, V2_COL_MAP['mbti_trust']])
        except (ValueError, TypeError, IndexError):
            result['mbti_trust'][i] = 4

        try:
            result['blood_trust'][i] = float(data_array[i, V2_COL_MAP['blood_trust']])
        except (ValueError, TypeError, IndexError):
            result['blood_trust'][i] = 4

        # Q44~Q46: 문자열
        try:
            result['are_you_t'].append(str(data_array[i, V2_COL_MAP['are_you_t']]))
        except (IndexError,):
            result['are_you_t'].append('')

        try:
            result['mbti_attitude'].append(str(data_array[i, V2_COL_MAP['mbti_attitude']]))
        except (IndexError,):
            result['mbti_attitude'].append('')

        try:
            result['final_opinion'].append(str(data_array[i, V2_COL_MAP['final_opinion']]))
        except (IndexError,):
            result['final_opinion'].append('')

    result['are_you_t'] = np.array(result['are_you_t'])
    result['mbti_attitude'] = np.array(result['mbti_attitude'])
    result['final_opinion'] = np.array(result['final_opinion'])

    return result


# ============================================================
#  7. 출력/리포트 함수
# ============================================================

def print_scoring_guide_v2():
    """v2 채점 체계 전체 출력"""
    print("=" * 70)
    print("  MBTI 밈 설문 v2 채점 체계 (Scoring System)")
    print("=" * 70)

    print("\n  설문 구조: 총 46문항 + 자유의견 1개")
    print("  ─────────────────────────────────────────")
    print("    Q1-Q5    기본 정보 (MBTI, 혈액형, 성별, 나이대, 검사방법)")
    print("    Q6-Q14   E/I 인싸/아싸 (9문항, 7점 리커트)")
    print("    Q15-Q23  S/N 현실/몽상 (9문항, 7점 양극 척도)")
    print("    Q24-Q32  T/F 너T야? (9문항, 7점 양극 척도)")
    print("    Q33-Q41  J/P 계획/즉흥 (9문항, 7점 양극 척도)")
    print("    Q42-Q46  보너스 밈 인식 (5문항)")

    print("\n┌──────────────────────────────────────────────────────┐")
    print("│  ■ 채점 원리 (v1과의 차이점)                          │")
    print("│    * v1: 각 차원 8문항, 정방향/역방향 4:4              │")
    print("│    * v2: 각 차원 9문항, 전체 단일 방향 (전부 역채점)   │")
    print("│    * 최종 컨벤션은 v1과 동일: 높은 점수 = E/S/T/J     │")
    print("│    * 분류 기준: ≥ 4.0 → E/S/T/J, < 4.0 → I/N/F/P   │")
    print("└──────────────────────────────────────────────────────┘")

    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        dim = SCORING_MAP_V2[dim_key]
        print(f"\n{'━' * 70}")
        print(f"  {dim['name']} — {dim['description']}")
        print(f"{'━' * 70}")
        print(f"  채점 후: 높은 점수(→7) = {dim['high_label']}  |  낮은 점수(→1) = {dim['low_label']}")
        print(f"  문항 수: {dim['n_items']}개")

        if dim['forward_cols']:
            print(f"\n  ▷ 정방향 문항 (점수 그대로 사용):")
            for col in dim['forward_cols']:
                q_key = f'Q{col}'
                _, direction, text = dim['questions'][q_key]
                print(f"    Q{col}. [{direction}] {text}")

        if dim['reverse_cols']:
            print(f"\n  ▷ 역방향 문항 (역채점: 8 - 원점수):")
            for col in dim['reverse_cols']:
                q_key = f'Q{col}'
                _, direction, text = dim['questions'][q_key]
                print(f"    Q{col}. [{direction}] {text}  -> 역채점")


def print_individual_result_v2(result):
    """개인 결과 상세 출력"""
    print(f"\n{'─' * 60}")
    print(f"  MBTI 분류 결과: {result['mbti_type']}  — {result['type_name']}")
    print(f"     그룹: {result['type_group']}")
    print(f"{'─' * 60}")

    for dim_key in ['EI', 'SN', 'TF', 'JP']:
        dim = result['dimensions'][dim_key]
        dim_info = SCORING_MAP_V2[dim_key]

        score = dim['score']
        bar_len = 30
        pos = int((score - 1) / 6 * bar_len)
        pos = max(0, min(bar_len - 1, pos))
        bar = '░' * pos + '█' + '░' * (bar_len - pos - 1)

        print(f"\n  [{dim_key}] {dim_info['name']}")
        print(f"       점수: {score:.2f} / 7.00")
        print(f"       분류: {dim['letter']} ({dim['strength']})")
        print(f"       거리: {dim['distance']:.2f} (중립점 4.0 기준)")
        print(f"       {dim_info['low_label']} |{bar}| {dim_info['high_label']}")


def print_scoring_example_v2():
    """v2 채점 예시 출력"""
    print("\n" + "=" * 70)
    print("  v2 채점 예시")
    print("=" * 70)

    # 예시 응답 (ENFP 성향 — 외향, 직관, 감정, 인식)
    example = {}
    # E/I: E 성향 (전체 I방향 → 낮은 점수 = 외향 성향)
    example.update({6: 2, 7: 2, 8: 2, 9: 3, 10: 1, 11: 2, 12: 3, 13: 2, 14: 2})
    # S/N: N 성향 (높은 점수 = N)
    example.update({15: 6, 16: 6, 17: 7, 18: 5, 19: 6, 20: 5, 21: 7, 22: 5, 23: 6})
    # T/F: F 성향 (높은 점수 = F)
    example.update({24: 6, 25: 6, 26: 5, 27: 7, 28: 5, 29: 6, 30: 7, 31: 6, 32: 6})
    # J/P: P 성향 (높은 점수 = P)
    example.update({33: 6, 34: 7, 35: 6, 36: 7, 37: 6, 38: 5, 39: 6, 40: 7, 41: 6})

    print("\n  [E/I 차원 채점 과정]")
    print("  ─────────────────────────────────────────────")
    ei_info = SCORING_MAP_V2['EI']

    print("  전체 I방향 문항 (역채점: 8 - 원점수 -> 높으면 E):")
    for col in ei_info['reverse_cols']:
        raw = example[col]
        rev = 8 - raw
        print(f"    Q{col}: 원점수 {raw} -> 역채점 (8-{raw}) = {rev}")

    all_scored = []
    for col in ei_info['forward_cols']:
        all_scored.append(example[col])
    for col in ei_info['reverse_cols']:
        all_scored.append(8 - example[col])

    avg = np.mean(all_scored)
    print(f"\n  9문항 평균: {avg:.2f}")
    print(f"  판정: {avg:.2f} {'≥' if avg >= 4.0 else '<'} 4.0"
          f" -> {'E (외향)' if avg >= 4.0 else 'I (내향)'}")

    # 전체 결과
    result = compute_all_dimensions_v2(example)
    print_individual_result_v2(result)


# ============================================================
#  8. 메인 실행
# ============================================================

if __name__ == '__main__':
    # 1) 채점 가이드 출력
    print_scoring_guide_v2()

    # 2) 채점 예시 출력
    print_scoring_example_v2()

    print("\n" + "=" * 70)
    print("  v2 사용법 안내")
    print("=" * 70)
    print("""
  ■ 개별 응답 채점:
    from survey.mbti_scoring_v2 import compute_all_dimensions_v2

    # Q번호 = CSV 컬럼 인덱스 (Q6=6, Q7=7, ..., Q41=41)
    responses = {6: 5, 7: 3, 8: 6, ..., 41: 4}
    result = compute_all_dimensions_v2(responses)
    print(result['mbti_type'])  # 예: 'ENFP'

  ■ CSV 일괄 채점:
    from survey.mbti_scoring_v2 import batch_compute_from_array_v2

    df = pd.read_csv('survey_responses_v2.csv')
    batch = batch_compute_from_array_v2(df.values)
    print(batch['types'])    # 전체 MBTI 유형 배열
    print(batch['scores'])   # 차원별 점수 배열

  ■ 보너스 문항 추출:
    from survey.mbti_scoring_v2 import extract_bonus_data

    bonus = extract_bonus_data(df.values)
    print(bonus['mbti_trust'])     # MBTI 신뢰도 (1-7)
    print(bonus['are_you_t'])      # "너 T야?" 사용 빈도
""")
