# -*- coding: utf-8 -*-
"""
시각화 스타일 공통 모듈
matplotlib/seaborn 한글 폰트 설정 및 공통 스타일링
"""

import os
import platform
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 비대화형 백엔드 (서버/스크립트 환경)
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from .config import FIGURES_DIR, DPI


def setup_korean_font():
    """
    한글 폰트 설정 (폰트 경로 직접 등록 방식)

    macOS: Apple SD Gothic Neo (시스템 기본 한글 폰트)
    Windows: Malgun Gothic
    Linux: NanumGothic
    """
    system = platform.system()
    font_name = None

    if system == 'Darwin':  # macOS
        # Apple SD Gothic Neo를 직접 등록 (가장 안정적)
        font_candidates = [
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
            '/Library/Fonts/AppleSDGothicNeo.ttc',
        ]
        for font_path in font_candidates:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                prop = fm.FontProperties(fname=font_path)
                font_name = prop.get_name()
                break

        if font_name is None:
            font_name = 'AppleGothic'

    elif system == 'Windows':
        font_candidates = [
            'C:/Windows/Fonts/malgun.ttf',
            'C:/Windows/Fonts/NanumGothic.ttf',
        ]
        for font_path in font_candidates:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                prop = fm.FontProperties(fname=font_path)
                font_name = prop.get_name()
                break

        if font_name is None:
            font_name = 'Malgun Gothic'

    else:  # Linux
        font_name = 'NanumGothic'

    # matplotlib 전역 설정
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False

    return font_name


def set_project_style():
    """
    프로젝트 전체 시각화 스타일 설정
    모든 분석 스크립트에서 이 함수를 먼저 호출합니다.

    PPT 삽입을 고려하여 글씨 크기를 크게 설정합니다.
    """
    # 한글 폰트 설정
    font_name = setup_korean_font()

    # seaborn 테마 설정 (PPT용 큰 글씨)
    sns.set_theme(
        style='whitegrid',
        palette='Set2',
        font=font_name,
        rc={
            'figure.figsize': (14, 9),
            'figure.dpi': 100,
            'savefig.dpi': DPI,
            # === PPT용 큰 글씨 크기 (확대) ===
            'font.size': 24,              # 기본 폰트 크기
            'axes.titlesize': 30,          # 차트 제목
            'axes.labelsize': 26,          # 축 라벨
            'xtick.labelsize': 20,         # X축 눈금
            'ytick.labelsize': 20,         # Y축 눈금
            'legend.fontsize': 22,         # 범례
            'legend.title_fontsize': 24,   # 범례 제목
            'figure.titlesize': 34,        # suptitle 크기
            # === 폰트 설정 ===
            'font.family': font_name,
            'axes.unicode_minus': False,
            # === 선 굵기 ===
            'axes.linewidth': 1.8,
            'grid.linewidth': 1.0,
            'lines.linewidth': 3.0,
            'lines.markersize': 10,
        }
    )

    # seaborn 이후에도 한글 폰트가 유지되도록 다시 강제 설정
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False

    print(f"[스타일] 한글 폰트 '{font_name}' 설정 완료")
    print(f"[스타일] PPT용 큰 글씨 크기 적용 완료")


def save_figure(fig, team_name, filename, tight=True):
    """
    그래프를 파일로 저장

    Parameters:
        fig: matplotlib Figure 객체
        team_name (str): 팀명 (예: 'team_a')
        filename (str): 파일명 (확장자 포함, 예: 'fig_a1_gender.png')
        tight (bool): tight_layout 적용 여부
    """
    save_dir = FIGURES_DIR / team_name
    os.makedirs(save_dir, exist_ok=True)

    filepath = save_dir / filename
    if tight:
        fig.tight_layout()
    fig.savefig(filepath, dpi=DPI, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)

    print(f"  [저장] {filepath}")


def add_significance_marker(ax, x, y, p_value, offset=0):
    """
    차트에 유의성 표시 추가

    * p < 0.05, ** p < 0.01, *** p < 0.001, ns 유의하지 않음
    """
    if p_value < 0.001:
        marker = '***'
    elif p_value < 0.01:
        marker = '**'
    elif p_value < 0.05:
        marker = '*'
    else:
        marker = 'ns'

    ax.annotate(marker, xy=(x, y + offset),
                ha='center', va='bottom',
                fontsize=22, fontweight='bold',
                color='red' if p_value < 0.05 else 'gray')


def add_result_text(ax, text, position='bottom_right'):
    """
    차트에 분석 결과 텍스트 박스 추가
    """
    positions = {
        'bottom_right': (0.98, 0.02),
        'top_right': (0.98, 0.98),
        'top_left': (0.02, 0.98),
        'bottom_left': (0.02, 0.02),
    }

    va_map = {
        'bottom_right': 'bottom',
        'top_right': 'top',
        'top_left': 'top',
        'bottom_left': 'bottom',
    }

    ha_map = {
        'bottom_right': 'right',
        'top_right': 'right',
        'top_left': 'left',
        'bottom_left': 'left',
    }

    x, y = positions.get(position, (0.98, 0.02))
    va = va_map.get(position, 'bottom')
    ha = ha_map.get(position, 'right')

    bbox_props = dict(
        boxstyle='round,pad=0.5',
        facecolor='lightyellow',
        edgecolor='gray',
        alpha=0.9
    )

    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=19, verticalalignment=va, horizontalalignment=ha,
            bbox=bbox_props)


def create_subtitle(fig, text, y=0.98):
    """
    그림 전체에 부제목(가설 등) 추가
    """
    fig.suptitle(text, fontsize=26, fontweight='bold',
                 y=y, color='#2C3E50')


def format_p_value(p):
    """p-value를 가독성 있게 포맷팅"""
    if p < 0.001:
        return "p < 0.001"
    elif p < 0.01:
        return f"p = {p:.3f}"
    elif p < 0.05:
        return f"p = {p:.3f}"
    else:
        return f"p = {p:.3f}"


def annotate_bars(ax, fmt='{:.1f}%', fontsize=18, offset=0):
    """
    바 차트에 값 라벨 추가
    """
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:
            ax.annotate(
                fmt.format(height),
                xy=(bar.get_x() + bar.get_width() / 2, height + offset),
                ha='center', va='bottom',
                fontsize=fontsize
            )
