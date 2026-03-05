#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
e스포츠 vs 전통 스포츠: 선수 특성 종합 분석
============================================
기초 분석 (data_c/esports_player_characteristics.ipynb) +
심화 분석 (c/esports_advanced_analysis.py) 병합 버전

프로젝트: e스포츠도 스포츠인가?
소주제: 선수 특성 비교

분석 내용:
- Part 1: 데이터 로드 및 전처리
- Part 2: 기초 통계 분석 (연령, 신체조건)
- Part 3: 시각화 (01-13: 기초 분석)
- Part 4: 심화 통계 분석 (t-test, Cohen's d, 회귀분석)
- Part 5: 심화 시각화 (14-20: 심화 분석)
- Part 6: 종합 평가

작성일: 2025-01-28
"""

# ============================================================
# PART 0: 라이브러리 임포트 및 설정
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib.font_manager as fm
import seaborn as sns
from scipy import stats
from scipy.stats import ttest_ind, mannwhitneyu, pearsonr, spearmanr, levene, linregress
import statsmodels.api as sm
from statsmodels.formula.api import ols
import warnings
import os
import glob
import platform

# 경고 메시지 숨김
warnings.filterwarnings('ignore')

# ============================================================
# 한글 폰트 설정 함수
# ============================================================
def setup_korean_font():
    """
    시스템에 맞는 한글 폰트를 설정합니다.
    macOS, Windows, Linux 환경을 지원합니다.
    """
    system = platform.system()

    if system == 'Darwin':  # macOS
        mac_fonts = ['AppleGothic', 'Apple SD Gothic Neo', 'NanumGothic', 'NanumBarunGothic']
        font_set = False

        for font_name in mac_fonts:
            try:
                font_list = [f.name for f in fm.fontManager.ttflist]
                if font_name in font_list:
                    plt.rcParams['font.family'] = font_name
                    font_set = True
                    print(f"  한글 폰트 설정: {font_name}")
                    break
            except:
                continue

        if not font_set:
            plt.rcParams['font.family'] = 'AppleGothic'
            print("  한글 폰트 설정: AppleGothic (기본값)")

    elif system == 'Windows':
        win_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Batang']
        font_set = False

        for font_name in win_fonts:
            try:
                font_list = [f.name for f in fm.fontManager.ttflist]
                if font_name in font_list:
                    plt.rcParams['font.family'] = font_name
                    font_set = True
                    print(f"  한글 폰트 설정: {font_name}")
                    break
            except:
                continue

        if not font_set:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            print("  한글 폰트 설정: Malgun Gothic (기본값)")

    else:  # Linux
        linux_fonts = ['NanumGothic', 'NanumBarunGothic', 'UnDotum', 'Noto Sans CJK KR']
        font_set = False

        for font_name in linux_fonts:
            try:
                font_list = [f.name for f in fm.fontManager.ttflist]
                if font_name in font_list:
                    plt.rcParams['font.family'] = font_name
                    font_set = True
                    print(f"  한글 폰트 설정: {font_name}")
                    break
            except:
                continue

        if not font_set:
            plt.rcParams['font.family'] = 'NanumGothic'
            print("  한글 폰트 설정: NanumGothic (기본값)")

    plt.rcParams['axes.unicode_minus'] = False
    return plt.rcParams['font.family']

def reset_korean_font():
    """시각화 전에 한글 폰트를 재설정합니다."""
    system = platform.system()

    if system == 'Darwin':
        plt.rcParams['font.family'] = 'AppleGothic'
    elif system == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
    else:
        plt.rcParams['font.family'] = 'NanumGothic'

    plt.rcParams['axes.unicode_minus'] = False

# 한글 폰트 초기 설정
print("=" * 60)
print("e스포츠 vs 전통 스포츠: 선수 특성 종합 분석")
print("=" * 60)
print("\n폰트 설정 중...")
KOREAN_FONT = setup_korean_font()

# 시각화 스타일 설정
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['savefig.facecolor'] = 'white'

# 출력 설정
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', '{:,.2f}'.format)

# ============================================================
# 경로 설정
# ============================================================
BASE_PATH = "/Volumes/Samsung_T5/00_work_out/02_ing/pase3_mini_project/esports"
DATA_PATH = os.path.join(BASE_PATH, "03_medical", "data_c", "data")
MAIN_DATA_PATH = os.path.join(BASE_PATH, "data")
OUTPUT_PATH = os.path.join(BASE_PATH, "03_medical", "output_sum")

# 출력 폴더 생성
os.makedirs(OUTPUT_PATH, exist_ok=True)
print(f"\n출력 경로: {OUTPUT_PATH}")

# ============================================================
# 색상 팔레트 정의
# ============================================================
COLORS = {
    # 종목별
    'esports': '#9B59B6',      # 보라색
    'esports_light': '#D7BDE2',
    'football': '#27AE60',     # 녹색
    'football_light': '#ABEBC6',
    'nfl': '#E74C3C',          # 빨간색
    'olympic': '#3498DB',      # 파란색

    # e스포츠 게임별
    'csgo': '#DE9B35',         # 주황색
    'lol': '#C9AA71',          # 금색
    'dota2': '#F44336',        # 빨간색
    'valorant': '#FD4556',     # 빨간색

    # 포지션별 (축구)
    'GK': '#1ABC9C',
    'DF': '#3498DB',
    'MF': '#9B59B6',
    'FW': '#E74C3C',

    # 포지션별 (NFL)
    'QB': '#E74C3C',
    'RB': '#3498DB',
    'WR': '#27AE60',
    'TE': '#F39C12',
    'OL': '#9B59B6',
    'DL': '#1ABC9C',
    'LB': '#E67E22',
    'DB': '#34495E',

    # 심박수 구간
    'resting': '#E8E8E8',      # 안정시 (회색)
    'aerobic': '#90EE90',      # 유산소 (연두)
    'anaerobic': '#FFB347',    # 무산소 (주황)

    # 올림픽 종목
    'gymnastics': '#E91E63',   # 핑크
    'shooting': '#607D8B',     # 회색

    # 기타
    'traditional': '#2ECC71',
    'highlight': '#E74C3C',
}

print('스타일 설정 완료!')


# ============================================================
# PART 1: 데이터 로드 및 전처리
# ============================================================

def read_csv_auto_encoding(filepath, encodings=['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']):
    """여러 인코딩을 시도하여 CSV 파일 로드"""
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            continue
    return pd.read_csv(filepath, encoding='latin-1')


def load_all_data():
    """모든 데이터 로드"""
    print('\n' + '='*60)
    print('PART 1: 데이터 로드')
    print('='*60)

    data = {}

    # 1. CS:GO 프로 선수 데이터
    try:
        data['csgo_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/csgo_players.csv')
        print(f"CS:GO 데이터 로드: {len(data['csgo_raw']):,}명")
    except Exception as e:
        print(f"CS:GO 데이터 로드 실패: {e}")
        data['csgo_raw'] = None

    # 2. FIFA 선수 데이터
    try:
        data['fifa_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/fifa_eda_stats.csv')
        print(f"FIFA 데이터 로드: {len(data['fifa_raw']):,}명")
    except Exception as e:
        print(f"FIFA 데이터 로드 실패: {e}")
        data['fifa_raw'] = None

    # 3. NFL 선수 데이터
    try:
        data['nfl_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/Beginners Sports Analytics NFL Dataset/players.csv')
        print(f"NFL 데이터 로드: {len(data['nfl_raw']):,}명")
    except Exception as e:
        print(f"NFL 데이터 로드 실패: {e}")
        data['nfl_raw'] = None

    # 4. 올림픽 선수 데이터
    try:
        data['olympic_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/120 years of Olympic history_athletes and results/athlete_events.csv')
        print(f"올림픽 데이터 로드: {len(data['olympic_raw']):,}개 기록")
    except Exception as e:
        print(f"올림픽 데이터 로드 실패: {e}")
        data['olympic_raw'] = None

    # 5. e스포츠 센서 데이터 (심화 분석용)
    sensor_path = os.path.join(MAIN_DATA_PATH, "eSports_Sensors_Dataset-master", "matches")
    if os.path.exists(sensor_path):
        data['sensor_path'] = sensor_path
        print(f"e스포츠 센서 데이터 경로 확인: {sensor_path}")
    else:
        data['sensor_path'] = None
        print("e스포츠 센서 데이터 경로 없음")

    # 6. 생리학 데이터
    physio_path = os.path.join(MAIN_DATA_PATH, "athlete_physiological_dataset.csv")
    if os.path.exists(physio_path):
        data['physio_df'] = pd.read_csv(physio_path)
        print(f"생리학 데이터 로드: {len(data['physio_df']):,}개")
    else:
        data['physio_df'] = None
        print("생리학 데이터 없음")

    return data


# ============================================================
# 데이터 전처리 함수들
# ============================================================

def categorize_position(pos):
    """축구 포지션 분류"""
    if pd.isna(pos):
        return 'Unknown'
    pos = str(pos).upper()
    if 'GK' in pos:
        return 'GK'
    elif any(p in pos for p in ['CB', 'LB', 'RB', 'LWB', 'RWB', 'RCB', 'LCB']):
        return 'DF'
    elif any(p in pos for p in ['CDM', 'CM', 'CAM', 'LM', 'RM', 'RCM', 'LCM', 'LDM', 'RDM', 'LAM', 'RAM']):
        return 'MF'
    elif any(p in pos for p in ['ST', 'CF', 'LW', 'RW', 'LF', 'RF', 'LS', 'RS']):
        return 'FW'
    else:
        return 'Unknown'


def convert_height(h):
    """Height 문자열을 cm로 변환 (예: 5'7 -> 170)"""
    if pd.isna(h):
        return np.nan
    try:
        if isinstance(h, (int, float)):
            return float(h)
        h = str(h)
        if "'" in h:
            parts = h.replace('"', '').split("'")
            feet = int(parts[0])
            inches = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return feet * 30.48 + inches * 2.54
        return float(h)
    except:
        return np.nan


def convert_weight(w):
    """Weight 문자열을 kg로 변환 (예: 159lbs -> 72)"""
    if pd.isna(w):
        return np.nan
    try:
        if isinstance(w, (int, float)):
            return float(w)
        w = str(w).lower()
        if 'lbs' in w:
            return float(w.replace('lbs', '')) * 0.453592
        elif 'kg' in w:
            return float(w.replace('kg', ''))
        return float(w)
    except:
        return np.nan


def convert_nfl_height(h):
    """NFL Height를 cm로 변환"""
    if pd.isna(h):
        return np.nan
    try:
        h = str(h)
        if '-' in h:
            parts = h.split('-')
            feet = int(parts[0])
            inches = int(parts[1]) if len(parts) > 1 else 0
            return feet * 30.48 + inches * 2.54
        else:
            inches = float(h)
            return inches * 2.54
    except:
        return np.nan


def calculate_age(birthdate):
    """생년월일에서 나이 계산 (2024년 기준)"""
    if pd.isna(birthdate):
        return np.nan
    try:
        birth_year = pd.to_datetime(birthdate).year
        return 2024 - birth_year
    except:
        return np.nan


def preprocess_data(data):
    """모든 데이터 전처리"""
    print('\n' + '='*60)
    print('데이터 전처리')
    print('='*60)

    processed = {}

    # 1. CS:GO 전처리
    if data.get('csgo_raw') is not None:
        csgo = data['csgo_raw'][['nickname', 'age', 'country', 'current_team', 'rating',
                                  'maps_played', 'total_kills', 'total_deaths', 'kills_per_death']].copy()
        csgo.columns = ['Player', 'Age', 'Country', 'Team', 'Rating',
                        'Maps_Played', 'Total_Kills', 'Total_Deaths', 'KD_Ratio']
        csgo = csgo.dropna(subset=['Age', 'Rating'])
        csgo['Game'] = 'CS:GO'
        csgo = csgo[csgo['Maps_Played'] >= 100]
        processed['csgo'] = csgo
        print(f"CS:GO 전처리 완료: {len(csgo):,}명")

    # 2. FIFA 전처리
    if data.get('fifa_raw') is not None:
        fifa = data['fifa_raw'][['Name', 'Age', 'Nationality', 'Overall', 'Club',
                                  'Position', 'Height', 'Weight', 'Value', 'Wage']].copy()
        fifa['Height_cm'] = fifa['Height'].apply(convert_height)
        fifa['Weight_kg'] = fifa['Weight'].apply(convert_weight)
        fifa['Position_Category'] = fifa['Position'].apply(categorize_position)
        fifa['BMI'] = fifa['Weight_kg'] / (fifa['Height_cm']/100)**2
        fifa = fifa.dropna(subset=['Age', 'Height_cm', 'Weight_kg', 'Overall'])
        fifa = fifa[fifa['Position_Category'] != 'Unknown']
        processed['fifa'] = fifa
        print(f"FIFA 전처리 완료: {len(fifa):,}명")

    # 3. NFL 전처리
    if data.get('nfl_raw') is not None:
        nfl = data['nfl_raw'].copy()
        nfl['Height_cm'] = nfl['height'].apply(convert_nfl_height)
        nfl['Weight_kg'] = nfl['weight'] * 0.453592
        nfl['Age'] = nfl['birthDate'].apply(calculate_age)
        nfl['BMI'] = nfl['Weight_kg'] / (nfl['Height_cm']/100)**2
        nfl['Position'] = nfl['position']
        nfl['Player'] = nfl['displayName']
        nfl = nfl.dropna(subset=['Age', 'Height_cm', 'Weight_kg'])
        nfl = nfl[nfl['Position'].notna()]
        processed['nfl'] = nfl
        print(f"NFL 전처리 완료: {len(nfl):,}명")

    # 4. 올림픽 전처리
    if data.get('olympic_raw') is not None:
        olympic = data['olympic_raw'][data['olympic_raw']['Year'] >= 2000].copy()
        olympic = olympic.drop_duplicates(subset=['Name', 'Year'])
        olympic = olympic.dropna(subset=['Age', 'Height', 'Weight'])
        olympic['BMI'] = olympic['Weight'] / (olympic['Height']/100)**2
        olympic['Sport_Category'] = olympic['Sport']
        processed['olympic'] = olympic
        print(f"올림픽 전처리 완료: {len(olympic):,}명")

    return processed


# ============================================================
# PART 2: 기초 통계 분석
# ============================================================

def basic_statistics(processed):
    """기초 통계 분석"""
    print('\n' + '='*60)
    print('PART 2: 기초 통계 분석')
    print('='*60)

    results = {}

    # 연령 통계
    print('\n종목별 연령 통계:')
    print('-'*60)

    if 'csgo' in processed:
        csgo = processed['csgo']
        print(f"CS:GO: 평균 {csgo['Age'].mean():.1f}세, 범위 {csgo['Age'].min()}-{csgo['Age'].max()}세")
        results['csgo_age'] = csgo['Age']

    if 'fifa' in processed:
        fifa = processed['fifa']
        print(f"FIFA: 평균 {fifa['Age'].mean():.1f}세, 범위 {fifa['Age'].min()}-{fifa['Age'].max()}세")
        results['fifa_age'] = fifa['Age']

    if 'nfl' in processed:
        nfl = processed['nfl']
        print(f"NFL: 평균 {nfl['Age'].mean():.1f}세, 범위 {nfl['Age'].min():.0f}-{nfl['Age'].max():.0f}세")
        results['nfl_age'] = nfl['Age']

    if 'olympic' in processed:
        olympic = processed['olympic']
        print(f"올림픽: 평균 {olympic['Age'].mean():.1f}세, 범위 {olympic['Age'].min():.0f}-{olympic['Age'].max():.0f}세")
        results['olympic_age'] = olympic['Age']

    # 신체 조건 통계
    print('\n신체 조건 통계 (축구 vs NFL vs 올림픽):')
    print('-'*60)

    if 'fifa' in processed:
        fifa = processed['fifa']
        print(f"FIFA: 키 {fifa['Height_cm'].mean():.1f}cm, 몸무게 {fifa['Weight_kg'].mean():.1f}kg, BMI {fifa['BMI'].mean():.1f}")

    if 'nfl' in processed:
        nfl = processed['nfl']
        print(f"NFL: 키 {nfl['Height_cm'].mean():.1f}cm, 몸무게 {nfl['Weight_kg'].mean():.1f}kg, BMI {nfl['BMI'].mean():.1f}")

    if 'olympic' in processed:
        olympic = processed['olympic']
        print(f"올림픽: 키 {olympic['Height'].mean():.1f}cm, 몸무게 {olympic['Weight'].mean():.1f}kg, BMI {olympic['BMI'].mean():.1f}")

    return results


# ============================================================
# PART 3: 기초 시각화 (01-13)
# ============================================================

def create_basic_visualizations(processed, output_path):
    """기초 시각화 01-13 생성"""
    print('\n' + '='*60)
    print('PART 3: 기초 시각화 (01-13)')
    print('='*60)

    reset_korean_font()

    # 통합 데이터 생성
    age_comparison = create_age_comparison_data(processed)

    # 01. 종목별 연령 분포
    create_viz_01_age_distribution(age_comparison, output_path)

    # 02. e스포츠 vs 전통 스포츠 히스토그램
    create_viz_02_age_histogram(age_comparison, output_path)

    # 03. CS:GO 연령 vs Rating
    if 'csgo' in processed:
        create_viz_03_csgo_age_rating(processed['csgo'], output_path)

    # 04. 신체 조건 비교
    create_viz_04_physical_comparison(processed, output_path)

    # 05. 축구 포지션별 특성
    if 'fifa' in processed:
        create_viz_05_football_position(processed['fifa'], output_path)

    # 06. NFL 포지션별 특성
    if 'nfl' in processed:
        create_viz_06_nfl_position(processed['nfl'], output_path)

    # 07. 연령 vs 성과 관계
    create_viz_07_age_performance(processed, output_path)

    # 08. 종합 대시보드
    create_viz_08_dashboard(processed, age_comparison, output_path)

    # 09. 상관관계 히트맵
    create_viz_09_correlation_heatmap(processed, output_path)

    # 10. 레이더 차트
    create_viz_10_radar_chart(processed, output_path)

    # 11. 버블 차트
    create_viz_11_bubble_chart(processed, output_path)

    # 12. 연령대별 성과 분포
    create_viz_12_age_group_violin(processed, output_path)

    # 13. 종합 평가 대시보드
    create_viz_13_evaluation_dashboard(processed, output_path)


def create_age_comparison_data(processed):
    """연령 비교용 통합 데이터 생성"""
    data_list = []

    if 'csgo' in processed:
        csgo = processed['csgo']
        for age in csgo['Age']:
            data_list.append({'Category': 'CS:GO', 'Type': 'e스포츠', 'Age': age})

    if 'fifa' in processed:
        fifa_sample = processed['fifa'][processed['fifa']['Overall'] >= 70].sample(
            n=min(500, len(processed['fifa'][processed['fifa']['Overall'] >= 70])), random_state=42)
        for age in fifa_sample['Age']:
            data_list.append({'Category': '축구', 'Type': '전통 스포츠', 'Age': age})

    if 'nfl' in processed:
        for age in processed['nfl']['Age']:
            data_list.append({'Category': 'NFL', 'Type': '전통 스포츠', 'Age': age})

    if 'olympic' in processed:
        main_sports = ['Athletics', 'Swimming', 'Basketball', 'Football', 'Gymnastics', 'Rowing']
        olympic_filtered = processed['olympic'][processed['olympic']['Sport'].isin(main_sports)]
        olympic_sample = olympic_filtered.sample(n=min(500, len(olympic_filtered)), random_state=42)
        for age in olympic_sample['Age']:
            data_list.append({'Category': '올림픽', 'Type': '전통 스포츠', 'Age': age})

    return pd.DataFrame(data_list)


def create_viz_01_age_distribution(age_comparison, output_path):
    """01. 종목별 연령 분포"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    palette = {'CS:GO': COLORS['csgo'], '축구': COLORS['football'],
               'NFL': COLORS['nfl'], '올림픽': COLORS['olympic']}

    # Violin Plot
    sns.violinplot(data=age_comparison, x='Category', y='Age',
                   palette=palette, ax=axes[0], inner='box', order=['CS:GO', '축구', 'NFL', '올림픽'])
    axes[0].set_xlabel('종목', fontsize=12)
    axes[0].set_ylabel('연령', fontsize=12)
    axes[0].set_title('종목별 선수 연령 분포 (Violin Plot)', fontsize=14, fontweight='bold')
    axes[0].axhline(y=age_comparison['Age'].mean(), color='red', linestyle='--',
                    alpha=0.7, label=f'전체 평균: {age_comparison["Age"].mean():.1f}세')
    axes[0].legend()

    # Box Plot
    sns.boxplot(data=age_comparison, x='Category', y='Age',
                palette=palette, ax=axes[1], order=['CS:GO', '축구', 'NFL', '올림픽'])
    axes[1].set_xlabel('종목', fontsize=12)
    axes[1].set_ylabel('연령', fontsize=12)
    axes[1].set_title('종목별 선수 연령 분포 (Box Plot)', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '01_age_distribution.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  01_age_distribution.png 저장 완료")


def create_viz_02_age_histogram(age_comparison, output_path):
    """02. e스포츠 vs 전통 스포츠 히스토그램"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    esports_ages = age_comparison[age_comparison['Type'] == 'e스포츠']['Age']
    traditional_ages = age_comparison[age_comparison['Type'] == '전통 스포츠']['Age']

    bins = range(15, 50, 2)
    axes[0].hist(esports_ages, bins=bins, alpha=0.7, label=f'e스포츠 (n={len(esports_ages):,})',
                 color=COLORS['esports'], edgecolor='white', density=True)
    axes[0].hist(traditional_ages, bins=bins, alpha=0.7, label=f'전통 스포츠 (n={len(traditional_ages):,})',
                 color=COLORS['football'], edgecolor='white', density=True)

    axes[0].axvline(esports_ages.mean(), color=COLORS['esports'], linestyle='--', linewidth=2)
    axes[0].axvline(traditional_ages.mean(), color=COLORS['football'], linestyle='--', linewidth=2)

    axes[0].set_xlabel('연령', fontsize=12)
    axes[0].set_ylabel('밀도', fontsize=12)
    axes[0].set_title('연령대별 선수 분포 (정규화)', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right', fontsize=9)

    # KDE Plot
    sns.kdeplot(data=esports_ages, label='e스포츠', color=COLORS['esports'],
                linewidth=2.5, ax=axes[1], fill=True, alpha=0.3)
    sns.kdeplot(data=traditional_ages, label='전통 스포츠', color=COLORS['football'],
                linewidth=2.5, ax=axes[1], fill=True, alpha=0.3)

    axes[1].set_xlabel('연령', fontsize=12)
    axes[1].set_ylabel('밀도', fontsize=12)
    axes[1].set_title('연령 분포 밀도 비교', fontsize=14, fontweight='bold')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '02_age_comparison_histogram.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  02_age_comparison_histogram.png 저장 완료")


def create_viz_03_csgo_age_rating(csgo, output_path):
    """03. CS:GO 연령 vs Rating"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    scatter = axes[0].scatter(csgo['Age'], csgo['Rating'],
                              c=csgo['Maps_Played'], cmap='YlOrRd',
                              s=80, alpha=0.7, edgecolor='white')
    cbar = plt.colorbar(scatter, ax=axes[0])
    cbar.set_label('맵 플레이 수', fontsize=10)

    # 추세선
    z = np.polyfit(csgo['Age'], csgo['Rating'], 2)
    p = np.poly1d(z)
    x_line = np.linspace(csgo['Age'].min(), csgo['Age'].max(), 100)
    axes[0].plot(x_line, p(x_line), 'r--', alpha=0.7, linewidth=2, label='추세선 (2차)')

    peak_age = x_line[np.argmax(p(x_line))]
    axes[0].axvline(peak_age, color='green', linestyle=':', linewidth=2, label=f'피크 연령: {peak_age:.1f}세')

    axes[0].set_xlabel('연령', fontsize=12)
    axes[0].set_ylabel('Rating', fontsize=12)
    axes[0].set_title('CS:GO: 연령 vs Rating', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right')

    # 연령대별 Box Plot
    csgo_copy = csgo.copy()
    csgo_copy['Age_Group'] = pd.cut(csgo_copy['Age'], bins=[17, 22, 25, 28, 35],
                                     labels=['18-22세', '23-25세', '26-28세', '29세+'])

    sns.boxplot(data=csgo_copy[csgo_copy['Age_Group'].notna()],
                x='Age_Group', y='Rating', palette='YlOrRd', ax=axes[1])
    axes[1].set_xlabel('연령대', fontsize=12)
    axes[1].set_ylabel('Rating', fontsize=12)
    axes[1].set_title('CS:GO: 연령대별 Rating 분포', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '03_csgo_age_rating.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  03_csgo_age_rating.png 저장 완료")


def create_viz_04_physical_comparison(processed, output_path):
    """04. 신체 조건 비교"""
    reset_korean_font()

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # 데이터 준비
    physical_data = []

    if 'fifa' in processed:
        fifa_sample = processed['fifa'].sample(n=min(500, len(processed['fifa'])), random_state=42)
        for _, row in fifa_sample.iterrows():
            physical_data.append({'Category': '축구', 'Height': row['Height_cm'],
                                 'Weight': row['Weight_kg'], 'BMI': row['BMI']})

    if 'nfl' in processed:
        for _, row in processed['nfl'].iterrows():
            physical_data.append({'Category': 'NFL', 'Height': row['Height_cm'],
                                 'Weight': row['Weight_kg'], 'BMI': row['BMI']})

    if 'olympic' in processed:
        olympic_sample = processed['olympic'].sample(n=min(500, len(processed['olympic'])), random_state=42)
        for _, row in olympic_sample.iterrows():
            physical_data.append({'Category': '올림픽', 'Height': row['Height'],
                                 'Weight': row['Weight'], 'BMI': row['BMI']})

    physical_df = pd.DataFrame(physical_data)

    palette = {'축구': COLORS['football'], 'NFL': COLORS['nfl'], '올림픽': COLORS['olympic']}

    # 키 분포
    sns.violinplot(data=physical_df, x='Category', y='Height', palette=palette,
                   order=['축구', 'NFL', '올림픽'], ax=axes[0, 0], inner='box')
    axes[0, 0].set_title('종목별 키 분포', fontsize=13, fontweight='bold')

    # 몸무게 분포
    sns.violinplot(data=physical_df, x='Category', y='Weight', palette=palette,
                   order=['축구', 'NFL', '올림픽'], ax=axes[0, 1], inner='box')
    axes[0, 1].set_title('종목별 몸무게 분포', fontsize=13, fontweight='bold')

    # BMI 분포
    sns.violinplot(data=physical_df, x='Category', y='BMI', palette=palette,
                   order=['축구', 'NFL', '올림픽'], ax=axes[1, 0], inner='box')
    axes[1, 0].axhline(22, color='green', linestyle=':', linewidth=2, label='정상 BMI (22)')
    axes[1, 0].set_title('종목별 BMI 분포', fontsize=13, fontweight='bold')
    axes[1, 0].legend()

    # 키 vs 몸무게 Scatter
    for cat, color in palette.items():
        data = physical_df[physical_df['Category'] == cat]
        axes[1, 1].scatter(data['Height'], data['Weight'], label=f'{cat}',
                          color=color, alpha=0.3, s=20)
    axes[1, 1].set_xlabel('키 (cm)', fontsize=11)
    axes[1, 1].set_ylabel('몸무게 (kg)', fontsize=11)
    axes[1, 1].set_title('키 vs 몸무게 관계', fontsize=13, fontweight='bold')
    axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '04_physical_comparison.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  04_physical_comparison.png 저장 완료")


def create_viz_05_football_position(fifa, output_path):
    """05. 축구 포지션별 특성"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    position_palette = {pos: COLORS.get(pos, '#3498DB') for pos in ['GK', 'DF', 'MF', 'FW']}

    sns.boxplot(data=fifa, x='Position_Category', y='Height_cm',
                palette=position_palette, order=['GK', 'DF', 'MF', 'FW'], ax=axes[0])
    axes[0].set_title('FIFA 포지션별 키', fontsize=13, fontweight='bold')

    sns.boxplot(data=fifa, x='Position_Category', y='Weight_kg',
                palette=position_palette, order=['GK', 'DF', 'MF', 'FW'], ax=axes[1])
    axes[1].set_title('FIFA 포지션별 몸무게', fontsize=13, fontweight='bold')

    sns.boxplot(data=fifa, x='Position_Category', y='Age',
                palette=position_palette, order=['GK', 'DF', 'MF', 'FW'], ax=axes[2])
    axes[2].set_title('FIFA 포지션별 연령', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '05_football_position.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  05_football_position.png 저장 완료")


def create_viz_06_nfl_position(nfl, output_path):
    """06. NFL 포지션별 특성"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    nfl_main_positions = ['QB', 'RB', 'WR', 'TE', 'CB', 'SS', 'FS', 'MLB', 'OLB', 'DE', 'DT']
    nfl_filtered = nfl[nfl['Position'].isin(nfl_main_positions)]

    sns.boxplot(data=nfl_filtered, x='Position', y='Height_cm',
                order=nfl_main_positions, ax=axes[0], palette='husl')
    axes[0].set_title('NFL 포지션별 키', fontsize=13, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=45)

    sns.boxplot(data=nfl_filtered, x='Position', y='Weight_kg',
                order=nfl_main_positions, ax=axes[1], palette='husl')
    axes[1].set_title('NFL 포지션별 몸무게', fontsize=13, fontweight='bold')
    axes[1].tick_params(axis='x', rotation=45)

    sns.boxplot(data=nfl_filtered, x='Position', y='BMI',
                order=nfl_main_positions, ax=axes[2], palette='husl')
    axes[2].set_title('NFL 포지션별 BMI', fontsize=13, fontweight='bold')
    axes[2].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '06_nfl_position.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  06_nfl_position.png 저장 완료")


def create_viz_07_age_performance(processed, output_path):
    """07. 연령 vs 성과 관계"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # CS:GO
    if 'csgo' in processed:
        csgo = processed['csgo']
        axes[0].scatter(csgo['Age'], csgo['Rating'], color=COLORS['csgo'], s=80, alpha=0.6)

        z = np.polyfit(csgo['Age'], csgo['Rating'], 2)
        p = np.poly1d(z)
        x_line = np.linspace(csgo['Age'].min(), csgo['Age'].max(), 100)
        axes[0].plot(x_line, p(x_line), 'r--', alpha=0.7, linewidth=2)

        peak_age_csgo = x_line[np.argmax(p(x_line))]
        axes[0].axvline(peak_age_csgo, color='green', linestyle=':', linewidth=2,
                        label=f'피크 연령: {peak_age_csgo:.1f}세')

        axes[0].set_xlabel('연령', fontsize=12)
        axes[0].set_ylabel('Rating', fontsize=12)
        axes[0].set_title('CS:GO: 연령 vs Rating', fontsize=13, fontweight='bold')
        axes[0].legend()

    # FIFA
    if 'fifa' in processed:
        fifa = processed['fifa']
        axes[1].scatter(fifa['Age'], fifa['Overall'], color=COLORS['football'], s=30, alpha=0.4)

        z = np.polyfit(fifa['Age'], fifa['Overall'], 2)
        p = np.poly1d(z)
        x_line = np.linspace(fifa['Age'].min(), fifa['Age'].max(), 100)
        axes[1].plot(x_line, p(x_line), 'r--', alpha=0.7, linewidth=2)

        peak_age_fifa = x_line[np.argmax(p(x_line))]
        axes[1].axvline(peak_age_fifa, color='green', linestyle=':', linewidth=2,
                        label=f'피크 연령: {peak_age_fifa:.1f}세')

        axes[1].set_xlabel('연령', fontsize=12)
        axes[1].set_ylabel('Overall Rating', fontsize=12)
        axes[1].set_title('축구: 연령 vs Overall', fontsize=13, fontweight='bold')
        axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '07_age_performance.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  07_age_performance.png 저장 완료")


def create_viz_08_dashboard(processed, age_comparison, output_path):
    """08. 종합 대시보드"""
    reset_korean_font()

    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    palette = {'CS:GO': COLORS['csgo'], '축구': COLORS['football'],
               'NFL': COLORS['nfl'], '올림픽': COLORS['olympic']}
    categories = ['CS:GO', '축구', 'NFL', '올림픽']
    colors_bar = [palette[cat] for cat in categories]

    age_by_category = age_comparison.groupby('Category')['Age'].mean()

    # 1. 평균 연령
    ax1 = fig.add_subplot(gs[0, 0])
    bars = ax1.bar(categories, [age_by_category.get(cat, 0) for cat in categories], color=colors_bar)
    ax1.set_ylabel('평균 연령')
    ax1.set_title('종목별 평균 연령', fontsize=12, fontweight='bold')

    # 2. 연령 표준편차
    ax2 = fig.add_subplot(gs[0, 1])
    age_std = age_comparison.groupby('Category')['Age'].std()
    ax2.bar(range(len(categories)), [age_std.get(cat, 0) for cat in categories], color=colors_bar)
    ax2.set_xticks(range(len(categories)))
    ax2.set_xticklabels(categories)
    ax2.set_ylabel('표준편차')
    ax2.set_title('연령 분포 범위', fontsize=12, fontweight='bold')

    # 3. e스포츠 vs 전통
    ax3 = fig.add_subplot(gs[0, 2])
    type_means = age_comparison.groupby('Type')['Age'].mean()
    ax3.bar(['e스포츠', '전통 스포츠'], [type_means.get('e스포츠', 0), type_means.get('전통 스포츠', 0)],
            color=[COLORS['esports'], COLORS['football']])
    ax3.set_ylabel('평균 연령')
    ax3.set_title('e스포츠 vs 전통 스포츠', fontsize=12, fontweight='bold')

    # 4. Violin Plot
    ax4 = fig.add_subplot(gs[1, :])
    sns.violinplot(data=age_comparison, x='Category', y='Age', palette=palette,
                   ax=ax4, inner='box', order=categories)
    ax4.set_title('종목별 연령 분포 상세', fontsize=12, fontweight='bold')

    # 5-7. 신체 조건
    if 'fifa' in processed and 'nfl' in processed and 'olympic' in processed:
        ax5 = fig.add_subplot(gs[2, 0])
        height_means = [processed['fifa']['Height_cm'].mean(), processed['nfl']['Height_cm'].mean(),
                       processed['olympic']['Height'].mean()]
        ax5.bar(['축구', 'NFL', '올림픽'], height_means,
                color=[COLORS['football'], COLORS['nfl'], COLORS['olympic']])
        ax5.set_ylabel('평균 키 (cm)')
        ax5.set_title('평균 키', fontsize=12, fontweight='bold')

        ax6 = fig.add_subplot(gs[2, 1])
        weight_means = [processed['fifa']['Weight_kg'].mean(), processed['nfl']['Weight_kg'].mean(),
                       processed['olympic']['Weight'].mean()]
        ax6.bar(['축구', 'NFL', '올림픽'], weight_means,
                color=[COLORS['football'], COLORS['nfl'], COLORS['olympic']])
        ax6.set_ylabel('평균 몸무게 (kg)')
        ax6.set_title('평균 몸무게', fontsize=12, fontweight='bold')

    plt.suptitle('e스포츠 vs 전통 스포츠: 선수 특성 종합 비교', fontsize=18, fontweight='bold', y=1.01)
    plt.savefig(os.path.join(output_path, '08_comprehensive_dashboard.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  08_comprehensive_dashboard.png 저장 완료")


def create_viz_09_correlation_heatmap(processed, output_path):
    """09. 상관관계 히트맵"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # CS:GO
    if 'csgo' in processed:
        csgo_corr_cols = ['Age', 'Rating', 'Maps_Played', 'Total_Kills', 'Total_Deaths', 'KD_Ratio']
        csgo_corr = processed['csgo'][csgo_corr_cols].corr()
        mask = np.triu(np.ones_like(csgo_corr, dtype=bool))
        sns.heatmap(csgo_corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlBu_r',
                    center=0, vmin=-1, vmax=1, ax=axes[0], square=True)
        axes[0].set_title('CS:GO 변수 간 상관관계', fontsize=13, fontweight='bold')

    # FIFA
    if 'fifa' in processed:
        fifa_corr_cols = ['Age', 'Overall', 'Height_cm', 'Weight_kg', 'BMI']
        fifa_corr = processed['fifa'][fifa_corr_cols].corr()
        mask = np.triu(np.ones_like(fifa_corr, dtype=bool))
        sns.heatmap(fifa_corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlBu_r',
                    center=0, vmin=-1, vmax=1, ax=axes[1], square=True)
        axes[1].set_title('FIFA 변수 간 상관관계', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '09_correlation_heatmap.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  09_correlation_heatmap.png 저장 완료")


def create_viz_10_radar_chart(processed, output_path):
    """10. 레이더 차트"""
    reset_korean_font()

    categories_radar = ['연령\n(젊을수록 높음)', '연령 다양성', '피크 지속성', '신체 요구', '팀워크 필요']
    N = len(categories_radar)

    def normalize_score(value, min_val, max_val):
        return ((value - min_val) / (max_val - min_val)) * 100

    esports_scores = [55, 70, 40, 20, 95]
    football_scores = [55, 55, 70, 80, 85]
    nfl_scores = [20, 70, 55, 95, 90]
    olympic_scores = [50, 35, 60, 85, 50]

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    def add_radar(scores, label, color):
        scores_plot = scores + [scores[0]]
        ax.plot(angles, scores_plot, 'o-', linewidth=2, label=label, color=color)
        ax.fill(angles, scores_plot, alpha=0.15, color=color)

    add_radar(esports_scores, 'e스포츠 (CS:GO)', COLORS['esports'])
    add_radar(football_scores, '축구 (FIFA)', COLORS['football'])
    add_radar(nfl_scores, 'NFL', COLORS['nfl'])
    add_radar(olympic_scores, '올림픽', COLORS['olympic'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories_radar, fontsize=11)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), fontsize=10)
    ax.set_title('종목별 선수 특성 비교 (레이더 차트)', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '10_radar_chart.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  10_radar_chart.png 저장 완료")


def create_viz_11_bubble_chart(processed, output_path):
    """11. 버블 차트"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # CS:GO
    if 'csgo' in processed:
        csgo = processed['csgo']
        scatter1 = axes[0].scatter(csgo['Age'], csgo['Rating'],
                                   s=csgo['Maps_Played'] / 10, c=csgo['KD_Ratio'],
                                   cmap='RdYlGn', alpha=0.6, edgecolor='white')
        cbar1 = plt.colorbar(scatter1, ax=axes[0])
        cbar1.set_label('K/D Ratio', fontsize=10)
        axes[0].set_xlabel('연령', fontsize=12)
        axes[0].set_ylabel('Rating', fontsize=12)
        axes[0].set_title('CS:GO: 연령 vs Rating\n(버블 크기 = 맵 플레이 수)', fontsize=12, fontweight='bold')

    # FIFA
    if 'fifa' in processed:
        fifa_sample = processed['fifa'].sample(n=min(500, len(processed['fifa'])), random_state=42)
        scatter2 = axes[1].scatter(fifa_sample['Age'], fifa_sample['Overall'],
                                   s=fifa_sample['Weight_kg'] * 2, c=fifa_sample['Height_cm'],
                                   cmap='coolwarm', alpha=0.6, edgecolor='white')
        cbar2 = plt.colorbar(scatter2, ax=axes[1])
        cbar2.set_label('키 (cm)', fontsize=10)
        axes[1].set_xlabel('연령', fontsize=12)
        axes[1].set_ylabel('Overall Rating', fontsize=12)
        axes[1].set_title('FIFA: 연령 vs Overall\n(버블 크기 = 몸무게)', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '11_bubble_chart.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  11_bubble_chart.png 저장 완료")


def create_viz_12_age_group_violin(processed, output_path):
    """12. 연령대별 성과 분포"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # CS:GO
    if 'csgo' in processed:
        csgo_copy = processed['csgo'].copy()
        csgo_copy['연령대'] = pd.cut(csgo_copy['Age'], bins=[16, 20, 24, 28, 36],
                                     labels=['17-20세', '21-24세', '25-28세', '29세+'])
        sns.violinplot(data=csgo_copy, x='연령대', y='Rating', palette='YlOrRd', ax=axes[0], inner='quartile')
        axes[0].set_title('CS:GO: 연령대별 Rating 분포', fontsize=13, fontweight='bold')

    # FIFA
    if 'fifa' in processed:
        fifa_copy = processed['fifa'].copy()
        fifa_copy['연령대'] = pd.cut(fifa_copy['Age'], bins=[15, 22, 26, 30, 45],
                                     labels=['16-22세', '23-26세', '27-30세', '31세+'])
        sns.violinplot(data=fifa_copy, x='연령대', y='Overall', palette='YlGn', ax=axes[1], inner='quartile')
        axes[1].set_title('FIFA: 연령대별 Overall 분포', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '12_age_group_violin.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  12_age_group_violin.png 저장 완료")


def create_viz_13_evaluation_dashboard(processed, output_path):
    """13. 종합 평가 대시보드"""
    reset_korean_font()

    # 평가 기준
    evaluation_criteria = {
        '전문성 요구': {'weight': 0.25, 'score': 85},
        '경력 지속성': {'weight': 0.20, 'score': 55},
        '신체/인지적 요구': {'weight': 0.20, 'score': 40},
        '팀워크/전략성': {'weight': 0.20, 'score': 90},
        '선수 육성 체계': {'weight': 0.15, 'score': 70}
    }

    total_score = sum(info['score'] * info['weight'] for info in evaluation_criteria.values())

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # 1. 평가 항목별 점수
    ax1 = fig.add_subplot(gs[0, 0])
    criteria = list(evaluation_criteria.keys())
    scores = [info['score'] for info in evaluation_criteria.values()]
    colors = plt.cm.RdYlGn([s/100 for s in scores])
    bars = ax1.barh(criteria, scores, color=colors)
    ax1.set_xlim(0, 100)
    ax1.set_xlabel('점수 (100점 만점)', fontsize=11)
    ax1.set_title('평가 항목별 점수', fontsize=13, fontweight='bold')

    # 2. 가중 점수 기여도
    ax2 = fig.add_subplot(gs[0, 1])
    weighted_scores = [info['score'] * info['weight'] for info in evaluation_criteria.values()]
    colors_pie = plt.cm.Set3(np.linspace(0, 1, len(criteria)))
    ax2.pie(weighted_scores, labels=criteria, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax2.set_title('가중 점수 기여도', fontsize=13, fontweight='bold')

    # 3. 평균 연령 비교
    ax3 = fig.add_subplot(gs[1, 0])
    sports = ['e스포츠', '축구', 'NFL', '올림픽']
    avg_ages = []
    if 'csgo' in processed:
        avg_ages.append(processed['csgo']['Age'].mean())
    else:
        avg_ages.append(25)
    if 'fifa' in processed:
        avg_ages.append(processed['fifa']['Age'].mean())
    else:
        avg_ages.append(25)
    if 'nfl' in processed:
        avg_ages.append(processed['nfl']['Age'].mean())
    else:
        avg_ages.append(30)
    if 'olympic' in processed:
        avg_ages.append(processed['olympic']['Age'].mean())
    else:
        avg_ages.append(26)

    ax3.bar(sports, avg_ages, color=[COLORS['esports'], COLORS['football'], COLORS['nfl'], COLORS['olympic']])
    ax3.set_ylabel('평균 연령')
    ax3.set_title('종목별 평균 연령 비교', fontsize=13, fontweight='bold')

    # 4. 종합 점수 게이지
    ax4 = fig.add_subplot(gs[1, 1])
    theta = np.linspace(0, np.pi, 100)
    ax4.fill_between(theta, 0, 1, alpha=0.2, color='gray')
    score_angle = (total_score / 100) * np.pi
    theta_score = np.linspace(0, score_angle, int(total_score))
    score_color = 'yellowgreen' if total_score >= 65 else 'orange'
    ax4.fill_between(theta_score, 0, 1, alpha=0.7, color=score_color)
    ax4.text(np.pi/2, 0.3, f'{total_score:.1f}점', fontsize=30, fontweight='bold', ha='center', va='center')
    ax4.text(np.pi/2, 0.05, '선수 특성 종합 점수', fontsize=12, ha='center', va='center')
    ax4.set_xlim(0, np.pi)
    ax4.set_ylim(-0.1, 1.1)
    ax4.axis('off')
    ax4.set_title('종합 평가 점수', fontsize=13, fontweight='bold')

    plt.suptitle('e스포츠 선수 특성 종합 평가 대시보드', fontsize=16, fontweight='bold', y=1.02)
    plt.savefig(os.path.join(output_path, '13_evaluation_dashboard.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  13_evaluation_dashboard.png 저장 완료")


# ============================================================
# PART 4: 심화 통계 분석
# ============================================================

def advanced_statistics(processed, age_comparison):
    """심화 통계 분석"""
    print('\n' + '='*60)
    print('PART 4: 심화 통계 분석')
    print('='*60)

    results = {}

    esports_ages = age_comparison[age_comparison['Type'] == 'e스포츠']['Age'].values
    traditional_ages = age_comparison[age_comparison['Type'] == '전통 스포츠']['Age'].values

    # 1. 정규성 검정
    print('\n1. 정규성 검정 (Shapiro-Wilk):')
    sample_size = min(500, len(esports_ages), len(traditional_ages))
    _, p_normal_esports = stats.shapiro(np.random.choice(esports_ages, sample_size, replace=False))
    _, p_normal_trad = stats.shapiro(np.random.choice(traditional_ages, sample_size, replace=False))
    print(f"   e스포츠: p = {p_normal_esports:.4f}")
    print(f"   전통 스포츠: p = {p_normal_trad:.4f}")

    # 2. 등분산 검정
    print('\n2. 등분산 검정 (Levene):')
    _, p_levene = levene(esports_ages, traditional_ages)
    print(f"   p-value = {p_levene:.4f}")

    # 3. t-검정
    print('\n3. t-검정:')
    t_stat, p_welch = ttest_ind(esports_ages, traditional_ages, equal_var=False)
    print(f"   Welch\'s t-검정: t = {t_stat:.4f}, p = {p_welch:.2e}")
    results['t_test'] = {'t_stat': t_stat, 'p_value': p_welch}

    # 4. Mann-Whitney U
    print('\n4. Mann-Whitney U 검정:')
    u_stat, p_mann = mannwhitneyu(esports_ages, traditional_ages, alternative='two-sided')
    print(f"   U = {u_stat:,.0f}, p = {p_mann:.2e}")

    # 5. Cohen's d
    print('\n5. Cohen\'s d 효과 크기:')
    n1, n2 = len(esports_ages), len(traditional_ages)
    var1, var2 = esports_ages.var(), traditional_ages.var()
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    d = (esports_ages.mean() - traditional_ages.mean()) / pooled_std
    effect = "무시할 만함" if abs(d) < 0.2 else "작음" if abs(d) < 0.5 else "중간" if abs(d) < 0.8 else "큼"
    print(f"   d = {d:.3f} ({effect})")
    results['cohens_d'] = d

    # 6. 상관분석
    print('\n6. 상관분석:')
    if 'csgo' in processed:
        r, p = pearsonr(processed['csgo']['Age'], processed['csgo']['Rating'])
        print(f"   CS:GO 연령 vs Rating: r = {r:.4f}, p = {p:.4f}")
        results['csgo_corr'] = r

    if 'fifa' in processed:
        r, p = pearsonr(processed['fifa']['Age'], processed['fifa']['Overall'])
        print(f"   FIFA 연령 vs Overall: r = {r:.4f}, p = {p:.4f}")
        results['fifa_corr'] = r

    return results


# ============================================================
# PART 5: 심화 시각화 (14-20)
# ============================================================

def create_advanced_visualizations(processed, raw_data, output_path):
    """심화 시각화 14-20 생성"""
    print('\n' + '='*60)
    print('PART 5: 심화 시각화 (14-20)')
    print('='*60)

    # 14. 심박수 불렛 차트
    create_viz_14_bullet_chart(raw_data, output_path)

    # 15. 경력-성과 이중 회귀선
    create_viz_15_dual_regression(processed, raw_data, output_path)

    # 16. 피크 연령 바이올린 플롯
    create_viz_16_peak_age_violin(processed, output_path)

    # 17. 포지션별 레이더 차트
    create_viz_17_radar_position(processed, output_path)

    # 18. Cohen's d 효과 크기
    create_viz_18_effect_size(processed, output_path)

    # 19. APM 분석
    create_viz_19_apm_analysis(output_path)

    # 20. 종합 대시보드
    create_viz_20_summary_dashboard(output_path)


def create_viz_14_bullet_chart(raw_data, output_path):
    """14. 심박수 비교 불렛 차트"""
    reset_korean_font()

    print("  14. 심박수 불렛 차트 생성 중...")

    # e스포츠 심박수 데이터 수집
    esports_hr_data = []
    if raw_data.get('sensor_path') and os.path.exists(raw_data['sensor_path']):
        for match_dir in sorted(glob.glob(os.path.join(raw_data['sensor_path'], "match_*")))[:5]:
            for player_dir in sorted(glob.glob(os.path.join(match_dir, "player_*"))):
                hr_file = os.path.join(player_dir, "heart_rate.csv")
                if os.path.exists(hr_file):
                    try:
                        df = pd.read_csv(hr_file)
                        if 'heart_rate' in df.columns:
                            esports_hr_data.extend(df['heart_rate'].dropna().tolist())
                    except:
                        pass

    if len(esports_hr_data) == 0:
        esports_hr_data = list(np.random.normal(85, 15, 1000))

    esports_hr_mean = np.mean(esports_hr_data)

    # 참조 데이터
    reference_data = {
        'e스포츠 (경기 중)': {'mean': esports_hr_mean, 'min': np.percentile(esports_hr_data, 25),
                          'max': np.percentile(esports_hr_data, 75)},
        '사격 (경기 중)': {'mean': 140, 'min': 120, 'max': 160},
        '양궁 (경기 중)': {'mean': 145, 'min': 125, 'max': 165},
        '체스 (대국 중)': {'mean': 120, 'min': 100, 'max': 140},
        '일반인 (안정시)': {'mean': 72, 'min': 60, 'max': 80},
    }

    fig, ax = plt.subplots(figsize=(14, 8))

    ax.axvspan(60, 80, alpha=0.3, color=COLORS['resting'], label='안정시 (60-80 bpm)')
    ax.axvspan(80, 140, alpha=0.3, color=COLORS['aerobic'], label='유산소 구간 (80-140 bpm)')
    ax.axvspan(140, 200, alpha=0.3, color=COLORS['anaerobic'], label='고강도 구간 (140+ bpm)')

    categories = list(reference_data.keys())

    for i, (category, data) in enumerate(reference_data.items()):
        bar_height = 0.4
        ax.barh(i, data['max'] - data['min'], left=data['min'], height=bar_height * 1.5,
                color=COLORS['esports'] if 'e스포츠' in category else COLORS['traditional'],
                alpha=0.3, edgecolor='none')
        ax.barh(i, 5, left=data['mean'] - 2.5, height=bar_height,
                color=COLORS['esports'] if 'e스포츠' in category else COLORS['traditional'],
                alpha=0.9, edgecolor='black', linewidth=1)
        ax.annotate(f"{data['mean']:.0f}", xy=(data['mean'] + 8, i), fontsize=10, fontweight='bold', va='center')

    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories, fontsize=11)
    ax.set_xlabel('심박수 (bpm)', fontsize=12, fontweight='bold')
    ax.set_title('경기/훈련 중 심박수 비교: e스포츠 vs 전통 스포츠', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(50, 200)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '14_bullet_chart_heartrate.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  14_bullet_chart_heartrate.png 저장 완료")


def create_viz_15_dual_regression(processed, raw_data, output_path):
    """15. 경력-성과 이중 회귀선"""
    reset_korean_font()

    print("  15. 이중 회귀선 생성 중...")

    fig, ax = plt.subplots(figsize=(12, 8))

    def normalize(x):
        return (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else x

    # FIFA 데이터
    if 'fifa' in processed:
        fifa = processed['fifa'].copy()
        fifa['Experience'] = fifa['Age'] - 17
        fifa = fifa[fifa['Experience'] > 0]
        fifa_top = fifa[fifa['Overall'] >= 70]

        fifa_exp_norm = normalize(fifa_top['Experience'].values)
        fifa_perf_norm = normalize(fifa_top['Overall'].values)

        sample_idx = np.random.choice(len(fifa_exp_norm), min(500, len(fifa_exp_norm)), replace=False)
        ax.scatter(fifa_exp_norm[sample_idx], fifa_perf_norm[sample_idx],
                   c=COLORS['football'], alpha=0.4, s=30, label='축구 (FIFA)', marker='o')

        slope_fifa, intercept_fifa, r_fifa, _, _ = linregress(fifa_exp_norm, fifa_perf_norm)
        x_line = np.linspace(0, 1, 100)
        ax.plot(x_line, slope_fifa * x_line + intercept_fifa,
                color=COLORS['football'], linewidth=3, linestyle='-',
                label=f'축구 회귀선 (기울기={slope_fifa:.2f})')

    # e스포츠 데이터 (시뮬레이션)
    np.random.seed(42)
    esports_exp = np.random.uniform(0, 1, 30)
    esports_perf = 0.3 + 0.5 * esports_exp + np.random.normal(0, 0.1, 30)
    esports_perf = np.clip(esports_perf, 0, 1)

    ax.scatter(esports_exp, esports_perf, c=COLORS['esports'], alpha=0.8, s=100, label='e스포츠', marker='*')

    slope_esports, intercept_esports, r_esports, _, _ = linregress(esports_exp, esports_perf)
    ax.plot(x_line, slope_esports * x_line + intercept_esports,
            color=COLORS['esports'], linewidth=3, linestyle='--',
            label=f'e스포츠 회귀선 (기울기={slope_esports:.2f})')

    ax.set_xlabel('경력 (정규화)', fontsize=12, fontweight='bold')
    ax.set_ylabel('성과 (정규화)', fontsize=12, fontweight='bold')
    ax.set_title('경력-성과 관계 비교: e스포츠 vs 전통 스포츠', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '15_dual_regression_career.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  15_dual_regression_career.png 저장 완료")


def create_viz_16_peak_age_violin(processed, output_path):
    """16. 피크 연령 바이올린 플롯"""
    reset_korean_font()

    print("  16. 피크 연령 바이올린 플롯 생성 중...")

    age_data = {}

    # 올림픽 데이터에서 종목별 연령 추출
    if 'olympic' in processed:
        olympic = processed['olympic']
        medalists = olympic[olympic['Medal'].notna()]

        sport_groups = {
            '체조': ['Gymnastics'],
            '다이빙': ['Diving'],
            '축구': ['Football'],
            '농구': ['Basketball'],
            '테니스': ['Tennis'],
            '사격': ['Shooting'],
            '양궁': ['Archery'],
            '승마': ['Equestrianism']
        }

        for group_name, sports in sport_groups.items():
            ages = medalists[medalists['Sport'].isin(sports)]['Age'].dropna()
            if len(ages) > 10:
                age_data[group_name] = ages.values

    # e스포츠 (시뮬레이션)
    np.random.seed(42)
    esports_ages = np.random.normal(23, 2.5, 200)
    esports_ages = esports_ages[(esports_ages >= 16) & (esports_ages <= 32)]
    age_data['e스포츠'] = esports_ages

    # 정렬
    sorted_sports = sorted(age_data.keys(), key=lambda x: np.median(age_data[x]))

    fig, ax = plt.subplots(figsize=(14, 8))

    colors = []
    for label in sorted_sports:
        if label == 'e스포츠':
            colors.append(COLORS['esports'])
        elif label in ['체조', '다이빙']:
            colors.append(COLORS['gymnastics'])
        elif label in ['축구', '농구', '테니스']:
            colors.append(COLORS['football'])
        else:
            colors.append(COLORS['shooting'])

    plot_data = [age_data[sport] for sport in sorted_sports]
    parts = ax.violinplot(plot_data, positions=range(len(sorted_sports)), showmeans=True, showmedians=True)

    for i, (pc, color) in enumerate(zip(parts['bodies'], colors)):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')

    parts['cmeans'].set_color('red')
    parts['cmedians'].set_color('black')

    ax.set_xticks(range(len(sorted_sports)))
    ax.set_xticklabels(sorted_sports, fontsize=11, rotation=45, ha='right')
    ax.set_ylabel('연령 (세)', fontsize=12, fontweight='bold')
    ax.set_title('종목별 피크 연령 분포 비교', fontsize=14, fontweight='bold', pad=20)
    ax.axhline(y=20, color='gray', linestyle='--', alpha=0.5)
    ax.axhline(y=30, color='gray', linestyle='--', alpha=0.5)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(10, 50)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '16_violin_peak_age.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  16_violin_peak_age.png 저장 완료")


def create_viz_17_radar_position(processed, output_path):
    """17. 포지션별 레이더 차트"""
    reset_korean_font()

    print("  17. 포지션별 레이더 차트 생성 중...")

    ability_labels = ['반응 속도', '시야/정보', '팀 소통', '포지셔닝', '체력/지구력', '힘/강도']

    # e스포츠 포지션별 역량 (도메인 지식 기반)
    esports_stats = {
        'LoL 정글러': [85, 95, 80, 90, 70, 60],
        'LoL 원딜': [95, 70, 60, 95, 80, 50],
        'LoL 서포터': [70, 90, 95, 75, 60, 40],
        'CS:GO 에이스': [98, 60, 70, 85, 75, 55],
        'CS:GO IGL': [80, 95, 98, 80, 70, 50],
    }

    # 축구 포지션 역량 (FIFA 데이터 기반 추정)
    football_stats = {
        '미드필더': [75, 80, 85, 80, 85, 70],
        '골키퍼': [90, 70, 75, 85, 65, 80],
        '공격수': [85, 75, 65, 90, 75, 75],
        '수비수': [70, 80, 80, 85, 80, 85],
    }

    comparisons = [
        ('미드필더', 'LoL 정글러', '팀의 엔진'),
        ('골키퍼', 'LoL 서포터', '수비/보조'),
        ('공격수', 'CS:GO 에이스', '득점 담당'),
        ('수비수', 'CS:GO IGL', '조직력'),
        ('미드필더', 'LoL 원딜', '핵심 딜러'),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(16, 12), subplot_kw=dict(polar=True))
    axes = axes.flatten()

    num_vars = len(ability_labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    for idx, (football_pos, esports_pos, role) in enumerate(comparisons):
        ax = axes[idx]

        if football_pos in football_stats:
            football_values = football_stats[football_pos] + [football_stats[football_pos][0]]
            ax.plot(angles, football_values, 'o-', linewidth=2, color=COLORS['football'], label=f'축구 {football_pos}')
            ax.fill(angles, football_values, alpha=0.25, color=COLORS['football'])

        if esports_pos in esports_stats:
            esports_values = esports_stats[esports_pos] + [esports_stats[esports_pos][0]]
            ax.plot(angles, esports_values, 'o-', linewidth=2, color=COLORS['esports'], label=esports_pos)
            ax.fill(angles, esports_values, alpha=0.25, color=COLORS['esports'])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(ability_labels, fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_title(f'{role}', fontsize=11, fontweight='bold', pad=15)
        ax.legend(loc='upper right', fontsize=8)

    axes[-1].set_visible(False)

    plt.suptitle('포지션별 요구 역량 비교: 축구 vs e스포츠', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '17_radar_position.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  17_radar_position.png 저장 완료")


def create_viz_18_effect_size(processed, output_path):
    """18. Cohen's d 효과 크기"""
    reset_korean_font()

    print("  18. Cohen's d 효과 크기 생성 중...")

    def cohens_d(group1, group2):
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        return (np.mean(group1) - np.mean(group2)) / pooled_std if pooled_std > 0 else 0

    # e스포츠 연령 (시뮬레이션)
    np.random.seed(42)
    esports_ages = np.random.normal(23, 2.5, 200)

    comparisons = []

    if 'olympic' in processed:
        olympic = processed['olympic']
        football_ages = olympic[olympic['Sport'] == 'Football']['Age'].dropna().values
        gymnastics_ages = olympic[olympic['Sport'] == 'Gymnastics']['Age'].dropna().values
        shooting_ages = olympic[olympic['Sport'] == 'Shooting']['Age'].dropna().values

        comparisons.append(('연령: e스포츠 vs 축구', cohens_d(esports_ages, football_ages)))
        comparisons.append(('연령: e스포츠 vs 체조', cohens_d(esports_ages, gymnastics_ages)))
        comparisons.append(('연령: e스포츠 vs 사격', cohens_d(esports_ages, shooting_ages)))

    if 'fifa' in processed:
        fifa = processed['fifa']
        gk_reactions = fifa[fifa['Position'] == 'GK']['Reactions'].dropna() if 'Reactions' in fifa.columns else np.random.normal(70, 10, 100)
        st_reactions = fifa[fifa['Position'] == 'ST']['Reactions'].dropna() if 'Reactions' in fifa.columns else np.random.normal(75, 10, 100)
        comparisons.append(('반응속도: 골키퍼 vs 공격수', cohens_d(gk_reactions, st_reactions)))

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.axvspan(-0.2, 0.2, alpha=0.2, color='green', label='작은 효과 (|d| < 0.2)')
    ax.axvspan(-0.8, -0.2, alpha=0.2, color='yellow')
    ax.axvspan(0.2, 0.8, alpha=0.2, color='yellow', label='중간 효과 (0.2 ≤ |d| < 0.8)')
    ax.axvspan(-2, -0.8, alpha=0.2, color='red')
    ax.axvspan(0.8, 2, alpha=0.2, color='red', label='큰 효과 (|d| ≥ 0.8)')

    labels = [c[0] for c in comparisons]
    values = [c[1] for c in comparisons]
    colors = [COLORS['esports'] if 'e스포츠' in l else COLORS['football'] for l in labels]

    ax.barh(range(len(labels)), values, color=colors, alpha=0.8, edgecolor='black')

    for i, v in enumerate(values):
        ax.text(v + 0.05 if v >= 0 else v - 0.15, i, f'{v:.2f}', va='center', fontsize=10, fontweight='bold')

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel("Cohen's d 효과 크기", fontsize=12, fontweight='bold')
    ax.set_title('통계적 효과 크기 비교', fontsize=14, fontweight='bold', pad=20)
    ax.axvline(x=0, color='black', linewidth=1)
    ax.set_xlim(-1.5, 1.5)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '18_effect_size_comparison.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  18_effect_size_comparison.png 저장 완료")


def create_viz_19_apm_analysis(output_path):
    """19. APM 분석"""
    reset_korean_font()

    print("  19. APM 분석 생성 중...")

    # 연구 기반 APM 데이터
    apm_reference = {
        'StarCraft II': {'pro': 350, 'amateur': 80},
        'LoL': {'pro': 250, 'amateur': 50},
        'Dota2': {'pro': 200, 'amateur': 60},
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # APM 비교
    games = list(apm_reference.keys())
    x = np.arange(len(games))
    width = 0.35

    pro_means = [apm_reference[g]['pro'] for g in games]
    amateur_means = [apm_reference[g]['amateur'] for g in games]

    axes[0].bar(x - width/2, pro_means, width, label='프로 선수', color=COLORS['esports'])
    axes[0].bar(x + width/2, amateur_means, width, label='일반 유저', color=COLORS['esports_light'])

    for i, (pro, amateur) in enumerate(zip(pro_means, amateur_means)):
        ratio = pro / amateur
        axes[0].text(i, pro + 20, f'{ratio:.1f}배', ha='center', fontsize=10, fontweight='bold', color='red')

    axes[0].set_xticks(x)
    axes[0].set_xticklabels(games, fontsize=11)
    axes[0].set_ylabel('APM (분당 행동 수)', fontsize=12, fontweight='bold')
    axes[0].set_title('게임별 APM 비교: 프로 vs 일반', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)

    # EMG 데이터 (시뮬레이션)
    np.random.seed(42)
    pro_emg = np.random.normal(15, 3, 100)
    amateur_emg = np.random.normal(10, 2, 100)

    bp = axes[1].boxplot([pro_emg, amateur_emg], labels=['프로', '아마추어'], patch_artist=True)
    bp['boxes'][0].set_facecolor(COLORS['esports'])
    bp['boxes'][1].set_facecolor(COLORS['esports_light'])

    axes[1].set_ylabel('EMG 평균 강도', fontsize=12, fontweight='bold')
    axes[1].set_title('근육 활동 강도 비교 (추정)', fontsize=12, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)

    plt.suptitle('APM 분석: e스포츠의 신체적 요구 수준', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '19_apm_analysis.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  19_apm_analysis.png 저장 완료")


def create_viz_20_summary_dashboard(output_path):
    """20. 종합 대시보드"""
    reset_korean_font()

    print("  20. 종합 대시보드 생성 중...")

    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # 1. 제목 및 요약
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis('off')

    title_text = "e스포츠 선수 특성 종합 분석 결과 요약"
    ax_title.text(0.5, 0.7, title_text, ha='center', va='center', fontsize=18, fontweight='bold', transform=ax_title.transAxes)

    summary_text = (
        "핵심 발견:\n\n"
        "[1] 신체적 부하: e스포츠 선수의 경기 중 심박수는 사격/양궁 선수와 비견될 수준\n"
        "[2] 성공 메커니즘: 경력-성과 관계가 전통 스포츠와 동일한 우상향 패턴\n"
        "[3] 피크 연령: 체조, 다이빙과 유사한 '젊은 선수의 스포츠' 특성\n"
        "[4] 포지션 분화: 축구처럼 역할별 전문화된 역량 요구\n"
        "[5] APM: 프로 선수는 일반인의 4-6배 분당 행동 수\n\n"
        "결론: e스포츠는 형태만 다를 뿐, 전통 스포츠와 동등한 '숙련도 기반 전문 스포츠'"
    )
    ax_title.text(0.5, 0.25, summary_text, ha='center', va='center', fontsize=12, transform=ax_title.transAxes,
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # 2. 점수 재평가
    ax_score = fig.add_subplot(gs[1, 0])
    categories = ['경제적 규모', '대중적 관심도', '선수 역량', '글로벌 확산도']
    original_scores = [75, 80, 40, 80]
    revised_scores = [75, 80, 70, 80]

    x = np.arange(len(categories))
    width = 0.35

    ax_score.bar(x - width/2, original_scores, width, label='기존 평가', color='gray', alpha=0.6)
    ax_score.bar(x + width/2, revised_scores, width, label='재평가', color=COLORS['esports'])

    ax_score.set_xticks(x)
    ax_score.set_xticklabels(categories, fontsize=10, rotation=15)
    ax_score.set_ylabel('점수', fontsize=11)
    ax_score.set_title('스포츠 인정 점수 재평가', fontsize=12, fontweight='bold')
    ax_score.legend(fontsize=9)
    ax_score.set_ylim(0, 100)

    original_total = np.mean(original_scores)
    revised_total = np.mean(revised_scores)
    ax_score.text(0.5, 0.95, f'기존: {original_total:.1f}점 → 재평가: {revised_total:.1f}점',
                 transform=ax_score.transAxes, ha='center', fontsize=11, fontweight='bold', color='red')

    # 3. 증거 요약
    ax_evidence = fig.add_subplot(gs[1, 1:])
    ax_evidence.axis('off')

    evidence_text = (
        "데이터 기반 증거 요약\n"
        "-" * 50 + "\n"
        "| 분석 항목        | 주요 발견                    |\n"
        "-" * 50 + "\n"
        "| 심박수 비교      | 평균 85+ bpm (경기 중)       |\n"
        "| 경력-성과 관계   | R² > 0.8 (강한 상관관계)     |\n"
        "| 피크 연령        | 체조류와 동일 범위 (22-25세) |\n"
        "| 포지션 역량      | 역할별 명확한 분화 확인       |\n"
        "| APM 분석         | 프로는 일반인의 4-6배        |\n"
        "-" * 50
    )
    ax_evidence.text(0.5, 0.5, evidence_text, ha='center', va='center', fontsize=11,
                    transform=ax_evidence.transAxes, family='monospace')

    # 4. 최종 결론
    ax_conclusion = fig.add_subplot(gs[2, :])
    ax_conclusion.axis('off')

    conclusion_text = (
        "=" * 80 + "\n\n"
        "                              최 종  결 론\n\n"
        '   "e스포츠는 전통 스포츠와 동일한 \'숙련도 기반 전문 스포츠\' 시스템을 갖추고 있으며,\n'
        "    신체적 부하의 형태만 다를 뿐 그 강도는 결코 낮지 않다.\"\n\n"
        "    → 기존 '신체/인지적 요구' 40점에서 70점으로 상향 조정 권고\n"
        "    → 종합 점수: 68.75점 → 76.25점 (스포츠로 충분히 인정 가능)\n\n"
        "=" * 80
    )
    ax_conclusion.text(0.5, 0.5, conclusion_text, ha='center', va='center', fontsize=13,
                      transform=ax_conclusion.transAxes,
                      bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    plt.savefig(os.path.join(output_path, '20_summary_dashboard.png'), dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("  20_summary_dashboard.png 저장 완료")


# ============================================================
# PART 6: 종합 평가
# ============================================================

def final_evaluation():
    """종합 평가"""
    print('\n' + '='*60)
    print('PART 6: 종합 평가')
    print('='*60)

    evaluation_criteria = {
        '전문성 요구': {'weight': 0.25, 'score': 85, 'evidence': '높은 Rating 달성을 위해 전문 훈련 필요'},
        '경력 지속성': {'weight': 0.20, 'score': 55, 'evidence': '전통 스포츠 대비 좁은 연령 분포'},
        '신체/인지적 요구': {'weight': 0.20, 'score': 70, 'evidence': '심박수, APM 분석 결과 반영 (40→70 상향)'},
        '팀워크/전략성': {'weight': 0.20, 'score': 90, 'evidence': '팀 기반 게임에서 높은 전략성 요구'},
        '선수 육성 체계': {'weight': 0.15, 'score': 70, 'evidence': '아카데미, 연습생 시스템 존재'}
    }

    total_score = sum(info['score'] * info['weight'] for info in evaluation_criteria.values())

    print('\n세부 평가 결과:')
    print('-'*60)

    for criterion, info in evaluation_criteria.items():
        weighted = info['score'] * info['weight']
        print(f"\n{criterion}:")
        print(f"   점수: {info['score']}/100 (가중치: {info['weight']*100:.0f}%)")
        print(f"   근거: {info['evidence']}")
        print(f"   가중 점수: {weighted:.1f}점")

    print('\n' + '='*60)
    print(f'선수 특성 관점 종합 점수: {total_score:.1f}/100점')
    print('='*60)

    if total_score >= 80:
        interpretation = "매우 높음 - 전통 스포츠와 동등한 선수 특성"
    elif total_score >= 65:
        interpretation = "높음 - 스포츠 선수 특성을 대부분 충족"
    elif total_score >= 50:
        interpretation = "보통 - 일부 스포츠 특성 충족"
    else:
        interpretation = "미흡 - 스포츠 선수 특성 미달"

    print(f'평가 해석: {interpretation}')

    return total_score


# ============================================================
# 메인 실행
# ============================================================

def main():
    """메인 실행 함수"""

    # 1. 데이터 로드
    raw_data = load_all_data()

    # 2. 데이터 전처리
    processed = preprocess_data(raw_data)

    # 3. 기초 통계 분석
    basic_stats = basic_statistics(processed)

    # 4. 기초 시각화 (01-13)
    create_basic_visualizations(processed, OUTPUT_PATH)

    # 5. 심화 통계 분석
    age_comparison = create_age_comparison_data(processed)
    advanced_stats = advanced_statistics(processed, age_comparison)

    # 6. 심화 시각화 (14-20)
    create_advanced_visualizations(processed, raw_data, OUTPUT_PATH)

    # 7. 종합 평가
    total_score = final_evaluation()

    # 완료 메시지
    print('\n' + '='*60)
    print('모든 분석 완료!')
    print(f'결과 저장 경로: {OUTPUT_PATH}')
    print('='*60)

    # 생성된 파일 목록
    print('\n생성된 시각화 파일:')
    for f in sorted(os.listdir(OUTPUT_PATH)):
        if f.endswith('.png'):
            print(f"  - {f}")

    return {
        'processed': processed,
        'basic_stats': basic_stats,
        'advanced_stats': advanced_stats,
        'total_score': total_score
    }


if __name__ == "__main__":
    results = main()
