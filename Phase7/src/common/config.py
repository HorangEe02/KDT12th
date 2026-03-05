# -*- coding: utf-8 -*-
"""
프로젝트 전역 설정 및 상수 정의
"""

import os
from pathlib import Path

# ============================================================
# 경로 설정
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # mini/
SRC_DIR = BASE_DIR / 'src'
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
RESULTS_DIR = BASE_DIR / 'results'
FIGURES_DIR = RESULTS_DIR / 'figures'

# ============================================================
# MBTI 관련 상수
# ============================================================
MBTI_TYPES = [
    'ISTJ', 'ISFJ', 'INFJ', 'INTJ',
    'ISTP', 'ISFP', 'INFP', 'INTP',
    'ESTP', 'ESFP', 'ENFP', 'ENTP',
    'ESTJ', 'ESFJ', 'ENFJ', 'ENTJ'
]

MBTI_DIMENSIONS = {
    'EI': ('E', 'I'),   # 외향(E) vs 내향(I)
    'SN': ('S', 'N'),   # 감각(S) vs 직관(N)
    'TF': ('T', 'F'),   # 사고(T) vs 감정(F)
    'JP': ('J', 'P'),   # 판단(J) vs 인식(P)
}

DIMENSION_NAMES_KR = {
    'EI': ('외향(E)', '내향(I)'),
    'SN': ('감각(S)', '직관(N)'),
    'TF': ('사고(T)', '감정(F)'),
    'JP': ('판단(J)', '인식(P)'),
}

DIMENSION_SCORE_COLS = {
    'EI': 'Introversion Score',
    'SN': 'Sensing Score',
    'TF': 'Thinking Score',
    'JP': 'Judging Score',
}

# ============================================================
# 혈액형 관련 상수
# ============================================================
BLOOD_TYPES = ['A', 'B', 'O', 'AB']

# ============================================================
# 통계 설정
# ============================================================
SIGNIFICANCE_LEVEL = 0.05

# ============================================================
# 시각화 컬러 팔레트
# ============================================================
MBTI_COLORS = {
    'ISTJ': '#1A5276', 'ISFJ': '#2E86C1', 'INFJ': '#5DADE2', 'INTJ': '#85C1E9',
    'ISTP': '#117A65', 'ISFP': '#1ABC9C', 'INFP': '#76D7C4', 'INTP': '#A3E4D7',
    'ESTP': '#B7950B', 'ESFP': '#F1C40F', 'ENFP': '#F9E79F', 'ENTP': '#F4D03F',
    'ESTJ': '#A93226', 'ESFJ': '#E74C3C', 'ENFJ': '#F1948A', 'ENTJ': '#CB4335',
}

BLOOD_COLORS = {
    'A': '#E74C3C',
    'B': '#3498DB',
    'O': '#2ECC71',
    'AB': '#9B59B6',
}

GENDER_COLORS = {
    'Male': '#5DADE2',
    'Female': '#F1948A',
}

INTEREST_COLORS = {
    'Arts': '#E74C3C',
    'Sports': '#3498DB',
    'Technology': '#2ECC71',
    'Others': '#F39C12',
    'Unknown': '#95A5A6',
}

CONTINENT_COLORS = {
    'AF': '#E74C3C',  # 아프리카
    'AS': '#F39C12',  # 아시아
    'EU': '#3498DB',  # 유럽
    'NA': '#2ECC71',  # 북미
    'SA': '#9B59B6',  # 남미
    'OC': '#1ABC9C',  # 오세아니아
}

# ============================================================
# 차트 기본 설정
# ============================================================
FIGSIZE_DEFAULT = (12, 8)
FIGSIZE_WIDE = (16, 8)
FIGSIZE_TALL = (12, 12)
FIGSIZE_SMALL = (8, 6)
DPI = 150
