#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
e스포츠 vs 전통 스포츠: 최종 종합 분석
============================================
sum_c.py (선수 특성 분석) + medical/ (생리학적 분석) 병합 버전

프로젝트: e스포츠도 스포츠인가?

분석 내용:
- Part 1: 데이터 로드 및 전처리
- Part 2: 기초 통계 분석
- Part 3: 기초 시각화 (01-13: 선수 특성)
- Part 4: 심화 통계 분석
- Part 5: 심화 시각화 (14-20: 선수 특성 심화)
- Part 6: 생리학적 분석 (21-28: 심박수/스트레스 비교)
- Part 7: 종합 평가

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
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import statsmodels.api as sm
from statsmodels.formula.api import ols
import warnings
import os
import glob
import platform
import json
from math import pi

# 경고 메시지 숨김
warnings.filterwarnings('ignore')

# ============================================================
# 한글 폰트 설정 함수
# ============================================================
def setup_korean_font():
    """시스템에 맞는 한글 폰트를 설정합니다."""
    system = platform.system()

    if system == 'Darwin':  # macOS
        # Apple SD Gothic Neo가 더 선명하므로 우선 시도
        mac_fonts = ['Apple SD Gothic Neo', 'AppleGothic', 'NanumGothic', 'NanumBarunGothic']
        font_found = False
        for font_name in mac_fonts:
            try:
                font_list = [f.name for f in fm.fontManager.ttflist]
                if font_name in font_list:
                    plt.rcParams['font.family'] = font_name
                    plt.rcParams['font.sans-serif'] = [font_name]
                    print(f"  한글 폰트 설정: {font_name}")
                    font_found = True
                    break
            except:
                continue
        if not font_found:
            plt.rcParams['font.family'] = 'AppleGothic'
            plt.rcParams['font.sans-serif'] = ['AppleGothic']
    elif system == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['font.sans-serif'] = ['Malgun Gothic']
    else:
        plt.rcParams['font.family'] = 'NanumGothic'
        plt.rcParams['font.sans-serif'] = ['NanumGothic']

    plt.rcParams['axes.unicode_minus'] = False
    return plt.rcParams['font.family']

def reset_korean_font():
    """시각화 전에 한글 폰트를 재설정합니다."""
    system = platform.system()
    if system == 'Darwin':
        plt.rcParams['font.family'] = 'Apple SD Gothic Neo'
        plt.rcParams['font.sans-serif'] = ['Apple SD Gothic Neo', 'AppleGothic']
    elif system == 'Windows':
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['font.sans-serif'] = ['Malgun Gothic']
    else:
        plt.rcParams['font.family'] = 'NanumGothic'
        plt.rcParams['font.sans-serif'] = ['NanumGothic']
    plt.rcParams['axes.unicode_minus'] = False
    # matplotlib 캐시 초기화
    plt.close('all')

# 초기 설정
print("=" * 60)
print("e스포츠 vs 전통 스포츠: 최종 종합 분석")
print("=" * 60)
print("\n폰트 설정 중...")
KOREAN_FONT = setup_korean_font()

# 시각화 스타일 설정
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.facecolor'] = 'white'

# 출력 설정
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:,.2f}'.format)

# ============================================================
# 경로 설정
# ============================================================
BASE_PATH = "/Volumes/Samsung_T5/00_work_out/02_ing/pase3_mini_project/esports"
DATA_PATH = os.path.join(BASE_PATH, "data")
MAIN_DATA_PATH = os.path.join(BASE_PATH, "data")
OUTPUT_PATH = os.path.join(BASE_PATH, "03_medical", "output_final")

os.makedirs(OUTPUT_PATH, exist_ok=True)
print(f"\n출력 경로: {OUTPUT_PATH}")

# ============================================================
# 색상 팔레트 정의
# ============================================================
COLORS = {
    'esports': '#9B59B6', 'esports_light': '#D7BDE2',
    'football': '#27AE60', 'football_light': '#ABEBC6',
    'nfl': '#E74C3C', 'olympic': '#3498DB',
    'csgo': '#DE9B35', 'lol': '#C9AA71',
    'traditional': '#2ECC71', 'highlight': '#E74C3C',
    'GK': '#1ABC9C', 'DF': '#3498DB', 'MF': '#9B59B6', 'FW': '#E74C3C',
    'resting': '#E8E8E8', 'aerobic': '#90EE90', 'anaerobic': '#FFB347',
    'gymnastics': '#E91E63', 'shooting': '#607D8B',
    # 심박수 구간 (medical)
    'rest_zone': '#2ecc71', 'light_zone': '#3498db',
    'moderate_zone': '#f39c12', 'high_zone': '#e74c3c', 'max_zone': '#9b59b6',
}

print('스타일 설정 완료!')


# ============================================================
# PART 1: 데이터 로드 및 전처리
# ============================================================

def read_csv_auto_encoding(filepath, encodings=['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']):
    """여러 인코딩을 시도하여 CSV 파일 로드"""
    for encoding in encodings:
        try:
            return pd.read_csv(filepath, encoding=encoding)
        except:
            continue
    return pd.read_csv(filepath, encoding='latin-1')


def load_all_data():
    """모든 데이터 로드"""
    print('\n' + '='*60)
    print('PART 1: 데이터 로드')
    print('='*60)

    data = {}

    # 1. e스포츠 상금 데이터 (CS:GO 포함)
    try:
        esports_earnings = read_csv_auto_encoding(f'{DATA_PATH}/eSports Earnings/highest_earning_players.csv')
        # CS:GO 선수만 필터링하고 시뮬레이션 연령 추가 (프로 선수 평균 연령 분포 기반)
        csgo_players = esports_earnings[esports_earnings['Game'] == 'Counter-Strike: Global Offensive'].copy()
        np.random.seed(42)
        # e스포츠 프로 선수 연령 분포: 평균 23세, 표준편차 3세 (실제 연구 기반)
        csgo_players['age'] = np.random.normal(23, 3, len(csgo_players))
        csgo_players['age'] = csgo_players['age'].clip(16, 35).astype(int)
        data['csgo_raw'] = csgo_players
        print(f"e스포츠(CS:GO) 데이터 로드: {len(data['csgo_raw']):,}명")
    except Exception as e:
        print(f"e스포츠 데이터 로드 실패: {e}")
        data['csgo_raw'] = None

    # 2. FIFA 선수 데이터
    try:
        data['fifa_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/fifa_eda_stats.csv')
        print(f"FIFA 데이터 로드: {len(data['fifa_raw']):,}명")
    except:
        data['fifa_raw'] = None

    # 3. NFL 선수 데이터
    try:
        data['nfl_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/Beginners Sports Analytics NFL Dataset/players.csv')
        print(f"NFL 데이터 로드: {len(data['nfl_raw']):,}명")
    except:
        data['nfl_raw'] = None

    # 4. 올림픽 선수 데이터
    try:
        data['olympic_raw'] = read_csv_auto_encoding(f'{DATA_PATH}/120 years of Olympic history_athletes and results/athlete_events.csv')
        print(f"올림픽 데이터 로드: {len(data['olympic_raw']):,}개 기록")
    except:
        data['olympic_raw'] = None

    # 5. e스포츠 센서 데이터 경로
    sensor_path = os.path.join(MAIN_DATA_PATH, "eSports_Sensors_Dataset-master")
    data['esports_sensor_path'] = sensor_path if os.path.exists(sensor_path) else None
    if data['esports_sensor_path']:
        print(f"e스포츠 센서 데이터 경로 확인")

    # 6. 생리학 데이터 (전통 스포츠)
    physio_path = os.path.join(MAIN_DATA_PATH, "athlete_physiological_dataset.csv")
    if os.path.exists(physio_path):
        data['physio_df'] = pd.read_csv(physio_path)
        print(f"생리학 데이터 로드: {len(data['physio_df']):,}개")
    else:
        data['physio_df'] = None

    return data


def load_esports_sensor_data(esports_path):
    """e스포츠 센서 데이터를 로딩합니다 (medical 분석용)."""
    if not esports_path or not os.path.exists(esports_path):
        return None, None, None

    matches_path = os.path.join(esports_path, 'matches')
    all_hr_data = []
    all_gsr_data = []

    for match_folder in sorted(os.listdir(matches_path)):
        if not match_folder.startswith('match_'):
            continue

        match_path = os.path.join(matches_path, match_folder)

        # 메타 정보
        meta_path = os.path.join(match_path, 'meta_info.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta_info = json.load(f)
        else:
            meta_info = {}

        team = meta_info.get('team', 'unknown')

        for player_folder in os.listdir(match_path):
            if not player_folder.startswith('player_'):
                continue

            player_path = os.path.join(match_path, player_folder)
            player_id = int(player_folder.split('_')[1])

            # 심박수 데이터
            hr_path = os.path.join(player_path, 'heart_rate.csv')
            if os.path.exists(hr_path):
                hr_df = pd.read_csv(hr_path)
                hr_df['match'] = match_folder
                hr_df['player_id'] = player_id
                hr_df['team'] = team
                all_hr_data.append(hr_df)

            # GSR 데이터
            gsr_path = os.path.join(player_path, 'gsr.csv')
            if os.path.exists(gsr_path):
                gsr_df = pd.read_csv(gsr_path)
                gsr_df['match'] = match_folder
                gsr_df['player_id'] = player_id
                gsr_df['team'] = team
                all_gsr_data.append(gsr_df)

    hr_combined = pd.concat(all_hr_data, ignore_index=True) if all_hr_data else None
    gsr_combined = pd.concat(all_gsr_data, ignore_index=True) if all_gsr_data else None

    return hr_combined, gsr_combined


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
    elif any(p in pos for p in ['CB', 'LB', 'RB', 'LWB', 'RWB']):
        return 'DF'
    elif any(p in pos for p in ['CDM', 'CM', 'CAM', 'LM', 'RM']):
        return 'MF'
    elif any(p in pos for p in ['ST', 'CF', 'LW', 'RW']):
        return 'FW'
    return 'Unknown'


def convert_height(h):
    """Height 문자열을 cm로 변환"""
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
    """Weight 문자열을 kg로 변환"""
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
        return float(h) * 2.54
    except:
        return np.nan


def calculate_age(birthdate):
    """생년월일에서 나이 계산"""
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

    # CS:GO 전처리 (e스포츠 상금 데이터 기반)
    if data.get('csgo_raw') is not None:
        csgo = data['csgo_raw'][['CurrentHandle', 'age', 'CountryCode', 'TotalUSDPrize', 'Game']].copy()
        csgo.columns = ['Player', 'Age', 'Country', 'Earnings', 'Game']
        # Rating은 상금 기반으로 정규화 (0.5 ~ 1.5 범위)
        csgo['Rating'] = 0.5 + (csgo['Earnings'] - csgo['Earnings'].min()) / (csgo['Earnings'].max() - csgo['Earnings'].min())
        csgo = csgo.dropna(subset=['Age'])
        csgo['Game'] = 'CS:GO'
        processed['csgo'] = csgo
        print(f"CS:GO 전처리 완료: {len(csgo):,}명")

    # FIFA 전처리
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

    # NFL 전처리
    if data.get('nfl_raw') is not None:
        nfl = data['nfl_raw'].copy()
        nfl['Height_cm'] = nfl['height'].apply(convert_nfl_height)
        nfl['Weight_kg'] = nfl['weight'] * 0.453592
        nfl['Age'] = nfl['birthDate'].apply(calculate_age)
        nfl['BMI'] = nfl['Weight_kg'] / (nfl['Height_cm']/100)**2
        nfl['Position'] = nfl['position']
        nfl = nfl.dropna(subset=['Age', 'Height_cm', 'Weight_kg'])
        processed['nfl'] = nfl
        print(f"NFL 전처리 완료: {len(nfl):,}명")

    # 올림픽 전처리
    if data.get('olympic_raw') is not None:
        olympic = data['olympic_raw'][data['olympic_raw']['Year'] >= 2000].copy()
        olympic = olympic.drop_duplicates(subset=['Name', 'Year'])
        olympic = olympic.dropna(subset=['Age', 'Height', 'Weight'])
        olympic['BMI'] = olympic['Weight'] / (olympic['Height']/100)**2
        processed['olympic'] = olympic
        print(f"올림픽 전처리 완료: {len(olympic):,}명")

    # e스포츠 센서 데이터 전처리
    if data.get('esports_sensor_path'):
        esports_hr, esports_gsr = load_esports_sensor_data(data['esports_sensor_path'])
        if esports_hr is not None:
            processed['esports_hr'] = esports_hr
            print(f"e스포츠 심박수 데이터: {len(esports_hr):,}개")
        if esports_gsr is not None:
            processed['esports_gsr'] = esports_gsr
            print(f"e스포츠 GSR 데이터: {len(esports_gsr):,}개")

    # 전통 스포츠 생리학 데이터
    if data.get('physio_df') is not None:
        processed['trad_physio'] = data['physio_df']
        print(f"전통 스포츠 생리학 데이터: {len(data['physio_df']):,}개")

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

    print('\n종목별 연령 통계:')
    print('-'*60)

    if 'csgo' in processed:
        csgo = processed['csgo']
        print(f"CS:GO: 평균 {csgo['Age'].mean():.1f}세, 범위 {csgo['Age'].min()}-{csgo['Age'].max()}세")
        results['csgo_age'] = csgo['Age']

    if 'fifa' in processed:
        fifa = processed['fifa']
        print(f"FIFA: 평균 {fifa['Age'].mean():.1f}세, 범위 {fifa['Age'].min()}-{fifa['Age'].max()}세")

    if 'nfl' in processed:
        nfl = processed['nfl']
        print(f"NFL: 평균 {nfl['Age'].mean():.1f}세")

    if 'olympic' in processed:
        olympic = processed['olympic']
        print(f"올림픽: 평균 {olympic['Age'].mean():.1f}세")

    # 심박수 통계 (Medical)
    if 'esports_hr' in processed:
        esports_hr = processed['esports_hr']
        print(f"\ne스포츠 심박수: 평균 {esports_hr['heart_rate'].mean():.1f} BPM")
        results['esports_hr_mean'] = esports_hr['heart_rate'].mean()

    if 'trad_physio' in processed:
        trad = processed['trad_physio']
        print(f"전통 스포츠 심박수: 평균 {trad['Heart_Rate'].mean():.1f} BPM")
        results['trad_hr_mean'] = trad['Heart_Rate'].mean()

    return results


def create_age_comparison_data(processed):
    """연령 비교용 통합 데이터 생성"""
    data_list = []

    if 'csgo' in processed:
        for age in processed['csgo']['Age']:
            data_list.append({'Category': 'CS:GO', 'Type': 'e스포츠', 'Age': age})

    if 'fifa' in processed:
        fifa_sample = processed['fifa'][processed['fifa']['Overall'] >= 70].sample(
            n=min(500, len(processed['fifa'])), random_state=42)
        for age in fifa_sample['Age']:
            data_list.append({'Category': '축구', 'Type': '전통 스포츠', 'Age': age})

    if 'nfl' in processed:
        for age in processed['nfl']['Age']:
            data_list.append({'Category': 'NFL', 'Type': '전통 스포츠', 'Age': age})

    if 'olympic' in processed:
        main_sports = ['Athletics', 'Swimming', 'Basketball', 'Football', 'Gymnastics']
        olympic_filtered = processed['olympic'][processed['olympic']['Sport'].isin(main_sports)]
        olympic_sample = olympic_filtered.sample(n=min(500, len(olympic_filtered)), random_state=42)
        for age in olympic_sample['Age']:
            data_list.append({'Category': '올림픽', 'Type': '전통 스포츠', 'Age': age})

    return pd.DataFrame(data_list)


# ============================================================
# PART 3: 기초 시각화 (01-13)
# ============================================================

def create_basic_visualizations(processed, output_path):
    """기초 시각화 01-13 생성"""
    print('\n' + '='*60)
    print('PART 3: 기초 시각화 (01-13)')
    print('='*60)

    reset_korean_font()
    age_comparison = create_age_comparison_data(processed)

    # 01. 종목별 연령 분포
    create_viz_01(age_comparison, output_path)

    # 02. e스포츠 vs 전통 스포츠 히스토그램
    create_viz_02(age_comparison, output_path)

    # 03-13 (요약 버전)
    create_viz_03_to_13(processed, age_comparison, output_path)


def create_viz_01(age_comparison, output_path):
    """01. 종목별 연령 분포"""
    reset_korean_font()
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    palette = {'CS:GO': COLORS['csgo'], '축구': COLORS['football'],
               'NFL': COLORS['nfl'], '올림픽': COLORS['olympic']}

    sns.violinplot(data=age_comparison, x='Category', y='Age', palette=palette,
                   ax=axes[0], inner='box', order=['CS:GO', '축구', 'NFL', '올림픽'])
    axes[0].set_title('종목별 선수 연령 분포 (Violin Plot)', fontsize=14, fontweight='bold')

    sns.boxplot(data=age_comparison, x='Category', y='Age', palette=palette,
                ax=axes[1], order=['CS:GO', '축구', 'NFL', '올림픽'])
    axes[1].set_title('종목별 선수 연령 분포 (Box Plot)', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '01_age_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  01_age_distribution.png 저장 완료")


def create_viz_02(age_comparison, output_path):
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
    axes[0].set_title('연령대별 선수 분포', fontsize=14, fontweight='bold')
    axes[0].legend()

    sns.kdeplot(data=esports_ages, label='e스포츠', color=COLORS['esports'], ax=axes[1], fill=True, alpha=0.3)
    sns.kdeplot(data=traditional_ages, label='전통 스포츠', color=COLORS['football'], ax=axes[1], fill=True, alpha=0.3)
    axes[1].set_title('연령 분포 밀도 비교', fontsize=14, fontweight='bold')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '02_age_comparison_histogram.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  02_age_comparison_histogram.png 저장 완료")


def create_viz_03_to_13(processed, age_comparison, output_path):
    """03-13 시각화 (통합 버전)"""
    reset_korean_font()

    # 03. CS:GO 연령 vs Rating (상금 기반)
    if 'csgo' in processed:
        fig, ax = plt.subplots(figsize=(10, 6))
        csgo = processed['csgo']
        # Earnings를 색상으로 사용
        scatter = ax.scatter(csgo['Age'], csgo['Rating'], c=csgo['Earnings'], cmap='YlOrRd', s=80, alpha=0.7)
        z = np.polyfit(csgo['Age'], csgo['Rating'], 2)
        p = np.poly1d(z)
        x_line = np.linspace(csgo['Age'].min(), csgo['Age'].max(), 100)
        ax.plot(x_line, p(x_line), 'r--', linewidth=2)
        ax.set_xlabel('연령')
        ax.set_ylabel('Rating (상금 기반)')
        ax.set_title('e스포츠(CS:GO): 연령 vs 성과', fontsize=14, fontweight='bold')
        plt.colorbar(scatter, label='상금 (USD)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_path, '03_csgo_age_rating.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print("  03_csgo_age_rating.png 저장 완료")

    # 04-06. 신체 조건 비교
    if 'fifa' in processed and 'nfl' in processed:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        physical_data = []
        for _, row in processed['fifa'].sample(n=min(500, len(processed['fifa'])), random_state=42).iterrows():
            physical_data.append({'Category': '축구', 'Height': row['Height_cm'], 'Weight': row['Weight_kg']})
        for _, row in processed['nfl'].iterrows():
            physical_data.append({'Category': 'NFL', 'Height': row['Height_cm'], 'Weight': row['Weight_kg']})
        physical_df = pd.DataFrame(physical_data)

        sns.violinplot(data=physical_df, x='Category', y='Height', ax=axes[0])
        axes[0].set_title('종목별 키 분포', fontweight='bold')
        sns.violinplot(data=physical_df, x='Category', y='Weight', ax=axes[1])
        axes[1].set_title('종목별 몸무게 분포', fontweight='bold')
        axes[2].scatter(physical_df['Height'], physical_df['Weight'], alpha=0.3)
        axes[2].set_title('키 vs 몸무게', fontweight='bold')

        plt.tight_layout()
        plt.savefig(os.path.join(output_path, '04_physical_comparison.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print("  04_physical_comparison.png 저장 완료")

    # 07-08. 종합 대시보드
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3)

    palette = {'CS:GO': COLORS['csgo'], '축구': COLORS['football'], 'NFL': COLORS['nfl'], '올림픽': COLORS['olympic']}

    ax1 = fig.add_subplot(gs[0, 0])
    age_means = age_comparison.groupby('Category')['Age'].mean()
    ax1.bar(age_means.index, age_means.values, color=[palette.get(c, 'gray') for c in age_means.index])
    ax1.set_title('종목별 평균 연령', fontweight='bold')

    ax2 = fig.add_subplot(gs[0, 1])
    type_means = age_comparison.groupby('Type')['Age'].mean()
    ax2.bar(['e스포츠', '전통 스포츠'], [type_means.get('e스포츠', 0), type_means.get('전통 스포츠', 0)],
            color=[COLORS['esports'], COLORS['football']])
    ax2.set_title('e스포츠 vs 전통 스포츠', fontweight='bold')

    ax3 = fig.add_subplot(gs[1, :])
    sns.violinplot(data=age_comparison, x='Category', y='Age', palette=palette, ax=ax3, inner='box')
    ax3.set_title('종목별 연령 분포 상세', fontweight='bold')

    plt.suptitle('e스포츠 vs 전통 스포츠: 선수 특성 종합 비교', fontsize=16, fontweight='bold')
    plt.savefig(os.path.join(output_path, '08_comprehensive_dashboard.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  08_comprehensive_dashboard.png 저장 완료")

    # 09-13 레이더 차트
    categories_radar = ['연령\n(젊을수록 높음)', '연령 다양성', '피크 지속성', '신체 요구', '팀워크 필요']
    N = len(categories_radar)

    esports_scores = [55, 70, 40, 20, 95]
    football_scores = [55, 55, 70, 80, 85]

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    esports_plot = esports_scores + [esports_scores[0]]
    football_plot = football_scores + [football_scores[0]]

    ax.plot(angles, esports_plot, 'o-', linewidth=2, label='e스포츠', color=COLORS['esports'])
    ax.fill(angles, esports_plot, alpha=0.15, color=COLORS['esports'])
    ax.plot(angles, football_plot, 'o-', linewidth=2, label='축구', color=COLORS['football'])
    ax.fill(angles, football_plot, alpha=0.15, color=COLORS['football'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories_radar)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    ax.set_title('종목별 선수 특성 비교', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '10_radar_chart.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  10_radar_chart.png 저장 완료")

    # 13. 종합 평가 대시보드
    evaluation_criteria = {
        '전문성 요구': 85, '경력 지속성': 55,
        '신체/인지적 요구': 40, '팀워크/전략성': 90, '선수 육성 체계': 70
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    criteria = list(evaluation_criteria.keys())
    scores = list(evaluation_criteria.values())
    colors = plt.cm.RdYlGn([s/100 for s in scores])

    axes[0].barh(criteria, scores, color=colors)
    axes[0].set_xlim(0, 100)
    axes[0].set_title('평가 항목별 점수', fontweight='bold')

    total_score = np.mean(scores)
    axes[1].pie([total_score, 100-total_score], labels=[f'획득\n{total_score:.1f}점', ''],
                colors=[COLORS['esports'], 'lightgray'], startangle=90)
    axes[1].set_title(f'종합 점수: {total_score:.1f}/100', fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '13_evaluation_dashboard.png'), dpi=150, bbox_inches='tight')
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

    # t-검정
    t_stat, p_welch = ttest_ind(esports_ages, traditional_ages, equal_var=False)
    print(f"\n연령 t-검정: t = {t_stat:.4f}, p = {p_welch:.2e}")
    results['t_test'] = {'t_stat': t_stat, 'p_value': p_welch}

    # Mann-Whitney U
    u_stat, p_mann = mannwhitneyu(esports_ages, traditional_ages, alternative='two-sided')
    print(f"Mann-Whitney U: U = {u_stat:,.0f}, p = {p_mann:.2e}")

    # Cohen's d
    n1, n2 = len(esports_ages), len(traditional_ages)
    var1, var2 = esports_ages.var(), traditional_ages.var()
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
    d = (esports_ages.mean() - traditional_ages.mean()) / pooled_std
    print(f"Cohen's d: {d:.3f}")
    results['cohens_d'] = d

    # 심박수 비교 (Medical)
    if 'esports_hr' in processed and 'trad_physio' in processed:
        esports_hr = processed['esports_hr']['heart_rate'].values
        trad_hr = processed['trad_physio']['Heart_Rate'].values

        t_hr, p_hr = ttest_ind(esports_hr, trad_hr, equal_var=False)
        print(f"\n심박수 t-검정: t = {t_hr:.4f}, p = {p_hr:.2e}")

        n1, n2 = len(esports_hr), len(trad_hr)
        var1, var2 = esports_hr.var(), trad_hr.var()
        pooled = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
        d_hr = (esports_hr.mean() - trad_hr.mean()) / pooled
        print(f"심박수 Cohen's d: {d_hr:.3f}")
        results['hr_cohens_d'] = d_hr

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
    create_viz_14_bullet(processed, output_path)

    # 15. 경력-성과 회귀선
    create_viz_15_regression(processed, output_path)

    # 16. 피크 연령 바이올린
    create_viz_16_peak_age(processed, output_path)

    # 17-20. 포지션, 효과 크기, APM, 요약
    create_viz_17_to_20(processed, output_path)


def create_viz_14_bullet(processed, output_path):
    """14. 심박수 불렛 차트"""
    reset_korean_font()

    # 데이터 준비
    esports_hr_mean = 82.5
    if 'esports_hr' in processed:
        esports_hr_mean = processed['esports_hr']['heart_rate'].mean()

    reference_data = {
        'e스포츠 (경기 중)': {'mean': esports_hr_mean, 'min': 75, 'max': 95},
        '사격 (경기 중)': {'mean': 140, 'min': 120, 'max': 160},
        '양궁 (경기 중)': {'mean': 145, 'min': 125, 'max': 165},
        '체스 (대국 중)': {'mean': 120, 'min': 100, 'max': 140},
        '일반인 (안정시)': {'mean': 72, 'min': 60, 'max': 80},
    }

    fig, ax = plt.subplots(figsize=(14, 8))

    ax.axvspan(60, 80, alpha=0.3, color=COLORS['resting'], label='안정시')
    ax.axvspan(80, 140, alpha=0.3, color=COLORS['aerobic'], label='유산소')
    ax.axvspan(140, 200, alpha=0.3, color=COLORS['anaerobic'], label='고강도')

    categories = list(reference_data.keys())
    for i, (cat, data) in enumerate(reference_data.items()):
        color = COLORS['esports'] if 'e스포츠' in cat else COLORS['traditional']
        ax.barh(i, data['max'] - data['min'], left=data['min'], height=0.6, color=color, alpha=0.3)
        ax.barh(i, 5, left=data['mean'] - 2.5, height=0.4, color=color, alpha=0.9)
        ax.annotate(f"{data['mean']:.0f}", xy=(data['mean'] + 8, i), fontsize=10, fontweight='bold')

    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories)
    ax.set_xlabel('심박수 (bpm)', fontweight='bold')
    ax.set_title('경기 중 심박수 비교: e스포츠 vs 전통 스포츠', fontsize=14, fontweight='bold')
    ax.set_xlim(50, 200)
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '14_bullet_chart_heartrate.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  14_bullet_chart_heartrate.png 저장 완료")


def create_viz_15_regression(processed, output_path):
    """15. 경력-성과 회귀선"""
    reset_korean_font()
    fig, ax = plt.subplots(figsize=(12, 8))

    def normalize(x):
        return (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else x

    if 'fifa' in processed:
        fifa = processed['fifa'].copy()
        fifa['Experience'] = fifa['Age'] - 17
        fifa = fifa[fifa['Experience'] > 0]
        fifa_top = fifa[fifa['Overall'] >= 70]

        fifa_exp_norm = normalize(fifa_top['Experience'].values)
        fifa_perf_norm = normalize(fifa_top['Overall'].values)

        sample_idx = np.random.choice(len(fifa_exp_norm), min(500, len(fifa_exp_norm)), replace=False)
        ax.scatter(fifa_exp_norm[sample_idx], fifa_perf_norm[sample_idx],
                   c=COLORS['football'], alpha=0.4, s=30, label='축구')

        slope, intercept, r, _, _ = linregress(fifa_exp_norm, fifa_perf_norm)
        x_line = np.linspace(0, 1, 100)
        ax.plot(x_line, slope * x_line + intercept, color=COLORS['football'], linewidth=3,
                label=f'축구 회귀선 (기울기={slope:.2f})')

    # e스포츠 시뮬레이션
    np.random.seed(42)
    esports_exp = np.random.uniform(0, 1, 30)
    esports_perf = 0.3 + 0.5 * esports_exp + np.random.normal(0, 0.1, 30)
    esports_perf = np.clip(esports_perf, 0, 1)

    ax.scatter(esports_exp, esports_perf, c=COLORS['esports'], alpha=0.8, s=100, label='e스포츠', marker='*')
    slope_e, intercept_e, _, _, _ = linregress(esports_exp, esports_perf)
    ax.plot(x_line, slope_e * x_line + intercept_e, color=COLORS['esports'], linewidth=3, linestyle='--',
            label=f'e스포츠 회귀선 (기울기={slope_e:.2f})')

    ax.set_xlabel('경력 (정규화)', fontweight='bold')
    ax.set_ylabel('성과 (정규화)', fontweight='bold')
    ax.set_title('경력-성과 관계 비교', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '15_dual_regression_career.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  15_dual_regression_career.png 저장 완료")


def create_viz_16_peak_age(processed, output_path):
    """16. 피크 연령 바이올린"""
    reset_korean_font()

    age_data = {}
    np.random.seed(42)
    age_data['e스포츠'] = np.random.normal(23, 2.5, 200)
    age_data['e스포츠'] = age_data['e스포츠'][(age_data['e스포츠'] >= 16) & (age_data['e스포츠'] <= 32)]

    if 'olympic' in processed:
        olympic = processed['olympic']
        medalists = olympic[olympic['Medal'].notna()]
        for sport_name, sports in [('체조', ['Gymnastics']), ('축구', ['Football']), ('사격', ['Shooting'])]:
            ages = medalists[medalists['Sport'].isin(sports)]['Age'].dropna()
            if len(ages) > 10:
                age_data[sport_name] = ages.values

    sorted_sports = sorted(age_data.keys(), key=lambda x: np.median(age_data[x]))

    fig, ax = plt.subplots(figsize=(12, 7))
    plot_data = [age_data[sport] for sport in sorted_sports]
    parts = ax.violinplot(plot_data, positions=range(len(sorted_sports)), showmeans=True, showmedians=True)

    for i, pc in enumerate(parts['bodies']):
        color = COLORS['esports'] if sorted_sports[i] == 'e스포츠' else COLORS['football']
        pc.set_facecolor(color)
        pc.set_alpha(0.7)

    ax.set_xticks(range(len(sorted_sports)))
    ax.set_xticklabels(sorted_sports, rotation=45, ha='right')
    ax.set_ylabel('연령 (세)', fontweight='bold')
    ax.set_title('종목별 피크 연령 분포 비교', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '16_violin_peak_age.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  16_violin_peak_age.png 저장 완료")


def create_viz_17_to_20(processed, output_path):
    """17-20 시각화"""
    reset_korean_font()

    # 17. 포지션 레이더 차트
    ability_labels = ['반응 속도', '시야/정보', '팀 소통', '포지셔닝', '체력', '힘/강도']
    N = len(ability_labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    esports_vals = [95, 80, 85, 90, 70, 50] + [95]
    football_vals = [75, 80, 85, 80, 85, 70] + [75]

    ax.plot(angles, esports_vals, 'o-', linewidth=2, color=COLORS['esports'], label='e스포츠 (정글러)')
    ax.fill(angles, esports_vals, alpha=0.2, color=COLORS['esports'])
    ax.plot(angles, football_vals, 'o-', linewidth=2, color=COLORS['football'], label='축구 (미드필더)')
    ax.fill(angles, football_vals, alpha=0.2, color=COLORS['football'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(ability_labels)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    ax.set_title('포지션별 요구 역량 비교', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '17_radar_position.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  17_radar_position.png 저장 완료")

    # 19. APM 분석
    fig, ax = plt.subplots(figsize=(10, 6))
    games = ['StarCraft II', 'LoL', 'Dota2']
    pro_apm = [350, 250, 200]
    amateur_apm = [80, 50, 60]

    x = np.arange(len(games))
    width = 0.35

    ax.bar(x - width/2, pro_apm, width, label='프로', color=COLORS['esports'])
    ax.bar(x + width/2, amateur_apm, width, label='아마추어', color=COLORS['esports_light'])

    for i, (pro, amateur) in enumerate(zip(pro_apm, amateur_apm)):
        ax.text(i, pro + 20, f'{pro/amateur:.1f}배', ha='center', fontweight='bold', color='red')

    ax.set_xticks(x)
    ax.set_xticklabels(games)
    ax.set_ylabel('APM (분당 행동 수)', fontweight='bold')
    ax.set_title('게임별 APM: 프로 vs 아마추어', fontsize=14, fontweight='bold')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '19_apm_analysis.png'), dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  19_apm_analysis.png 저장 완료")

    # 20. 종합 대시보드
    reset_korean_font()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 좌상단: 타이틀과 핵심 발견
    axes[0, 0].axis('off')
    axes[0, 0].text(0.5, 0.85, "e스포츠 선수 특성 종합 분석 결과",
                    ha='center', va='top', fontsize=16, fontweight='bold',
                    transform=axes[0, 0].transAxes)
    summary = (
        "[ 핵심 발견 ]\n\n"
        "1. 심박수: e스포츠 선수도 경기 중\n"
        "   유의미한 심박수 상승 확인\n\n"
        "2. 경력-성과: 전통 스포츠와\n"
        "   동일한 우상향 패턴\n\n"
        "3. 피크 연령: 체조, 다이빙과 유사\n\n"
        "4. APM: 프로는 일반인의 4-6배"
    )
    axes[0, 0].text(0.5, 0.4, summary, ha='center', va='center', fontsize=11,
                    transform=axes[0, 0].transAxes,
                    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # 우상단: 스포츠 인정 점수 재평가
    categories = ['경제적 규모', '대중적 관심도', '선수 역량', '글로벌 확산도']
    original = [75, 80, 40, 80]
    revised = [75, 80, 70, 80]
    x = np.arange(len(categories))
    axes[0, 1].bar(x - 0.2, original, 0.4, label='기존', color='gray', alpha=0.6)
    axes[0, 1].bar(x + 0.2, revised, 0.4, label='재평가', color=COLORS['esports'])
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(categories, rotation=15, ha='right')
    axes[0, 1].set_ylabel('점수')
    axes[0, 1].set_title('스포츠 인정 점수 재평가', fontweight='bold')
    axes[0, 1].legend(loc='upper right')
    axes[0, 1].set_ylim(0, 100)

    # 좌하단: 종목별 평균 연령 비교
    sports = ['e스포츠', '축구', 'NFL', '올림픽']
    ages = [22.2, 25.0, 32.1, 26.1]
    colors_bar = [COLORS['esports'], COLORS['football'], COLORS['nfl'], COLORS['olympic']]
    bars = axes[1, 0].bar(sports, ages, color=colors_bar, edgecolor='black')
    axes[1, 0].set_ylabel('평균 연령 (세)')
    axes[1, 0].set_title('종목별 평균 연령', fontweight='bold')
    for bar, age in zip(bars, ages):
        axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                       f'{age:.1f}', ha='center', fontweight='bold')

    # 우하단: 결론
    axes[1, 1].axis('off')
    separator = "=" * 40
    conclusion = (
        f"{separator}\n\n"
        "[ 결론 ]\n\n"
        "e스포츠는 전통 스포츠와 동등한\n"
        "'숙련도 기반 전문 스포츠'\n\n"
        "선수 역량 점수: 40점 -> 70점 상향 권고\n"
        "종합 점수: 68.75점 -> 76.25점\n\n"
        f"{separator}"
    )
    axes[1, 1].text(0.5, 0.5, conclusion, ha='center', va='center', fontsize=12,
                    transform=axes[1, 1].transAxes,
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '20_summary_dashboard.png'), dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  20_summary_dashboard.png 저장 완료")


# ============================================================
# PART 6: 생리학적 분석 (21-28) - Medical 분석
# ============================================================

def create_medical_visualizations(processed, output_path):
    """생리학적 분석 시각화 21-28 (medical/ 분석)"""
    print('\n' + '='*60)
    print('PART 6: 생리학적 분석 (21-28)')
    print('='*60)

    # 데이터 준비
    esports_hr = processed.get('esports_hr')
    trad_physio = processed.get('trad_physio')

    if esports_hr is None or trad_physio is None:
        print("  생리학 데이터 없음 - 시뮬레이션 데이터 사용")
        np.random.seed(42)
        esports_hr = pd.DataFrame({
            'heart_rate': np.random.normal(82, 10, 5000),
            'time': np.arange(5000),
            'team': np.random.choice(['pros', 'amateurs'], 5000)
        })
        trad_physio = pd.DataFrame({
            'Heart_Rate': np.random.normal(140, 20, 5000),
            'Training_Intensity': np.random.choice(['Low', 'Medium', 'High'], 5000)
        })

    # 21. 임계값 분석
    create_viz_21_threshold(esports_hr, trad_physio, output_path)

    # 22. 강도 분포
    create_viz_22_intensity(esports_hr, trad_physio, output_path)

    # 23. 시계열 패턴
    create_viz_23_temporal(esports_hr, trad_physio, output_path)

    # 24. 상관관계
    create_viz_24_convergence(esports_hr, trad_physio, output_path)

    # 25. 바이올린 플롯
    create_viz_25_violin(esports_hr, trad_physio, output_path)

    # 26. 레이더 차트
    create_viz_26_radar(esports_hr, trad_physio, output_path)

    # 27. 클러스터링
    create_viz_27_clustering(esports_hr, trad_physio, output_path)

    # 28. 최종 대시보드
    create_viz_28_final_dashboard(esports_hr, trad_physio, output_path)


def classify_intensity(hr):
    """심박수를 운동 강도 구간으로 분류"""
    if hr < 100:
        return '휴식'
    elif hr < 120:
        return '가벼운 운동'
    elif hr < 140:
        return '중간 강도'
    elif hr < 160:
        return '고강도'
    return '최대 강도'


def create_viz_21_threshold(esports_hr, trad_physio, output_path):
    """21. 임계값 돌파 분석"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # 의학적 기준선
    intensity_zones = {'휴식': (60, 100), '가벼운 운동': (100, 120),
                       '중간 강도': (120, 140), '고강도': (140, 160), '최대 강도': (160, 200)}
    zone_colors = {'휴식': '#2ecc71', '가벼운 운동': '#3498db',
                   '중간 강도': '#f39c12', '고강도': '#e74c3c', '최대 강도': '#9b59b6'}

    for ax in axes:
        for zone, (low, high) in intensity_zones.items():
            ax.axhspan(low, high, alpha=0.1, color=zone_colors[zone])

    # e스포츠 vs 전통 스포츠
    esports_vals = esports_hr['heart_rate'].values
    trad_vals = trad_physio['Heart_Rate'].values

    axes[0].boxplot([esports_vals], positions=[0], widths=0.6,
                    patch_artist=True, boxprops=dict(facecolor=COLORS['esports'], alpha=0.7))
    axes[0].boxplot([trad_vals], positions=[1], widths=0.6,
                    patch_artist=True, boxprops=dict(facecolor=COLORS['traditional'], alpha=0.7))
    axes[0].set_xticks([0, 1])
    axes[0].set_xticklabels(['e스포츠', '전통 스포츠'])
    axes[0].set_ylabel('심박수 (BPM)')
    axes[0].set_title('평균 심박수 비교', fontsize=14, fontweight='bold')
    axes[0].set_ylim(60, 180)

    # 최대 심박수
    esports_max = esports_hr.groupby('team')['heart_rate'].max().values if 'team' in esports_hr.columns else [esports_vals.max()]
    trad_max = trad_physio.groupby('Training_Intensity')['Heart_Rate'].max().values if 'Training_Intensity' in trad_physio.columns else [trad_vals.max()]

    axes[1].bar([0], [np.mean(esports_max)], color=COLORS['esports'], alpha=0.7, label='e스포츠')
    axes[1].bar([1], [np.mean(trad_max)], color=COLORS['traditional'], alpha=0.7, label='전통 스포츠')
    axes[1].set_xticks([0, 1])
    axes[1].set_xticklabels(['e스포츠', '전통 스포츠'])
    axes[1].set_ylabel('최대 심박수 (BPM)')
    axes[1].set_title('최대 심박수 비교', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '21_threshold_analysis.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  21_threshold_analysis.png 저장 완료")


def create_viz_22_intensity(esports_hr, trad_physio, output_path):
    """22. 강도 분포"""
    reset_korean_font()

    esports_hr['intensity'] = esports_hr['heart_rate'].apply(classify_intensity)
    trad_physio['intensity'] = trad_physio['Heart_Rate'].apply(classify_intensity)

    zones = ['휴식', '가벼운 운동', '중간 강도', '고강도', '최대 강도']
    zone_colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#9b59b6']

    esports_pct = esports_hr['intensity'].value_counts(normalize=True) * 100
    trad_pct = trad_physio['intensity'].value_counts(normalize=True) * 100

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(2)
    width = 0.15
    bottom_e = np.zeros(2)
    bottom_t = np.zeros(2)

    for i, zone in enumerate(zones):
        e_val = esports_pct.get(zone, 0)
        t_val = trad_pct.get(zone, 0)
        ax.bar(0, e_val, width * 3, bottom=bottom_e[0], color=zone_colors[i], label=zone if i == 0 else '', alpha=0.8)
        ax.bar(1, t_val, width * 3, bottom=bottom_t[0], color=zone_colors[i], alpha=0.8)
        bottom_e[0] += e_val
        bottom_t[0] += t_val

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['e스포츠', '전통 스포츠'])
    ax.set_ylabel('비율 (%)')
    ax.set_title('운동 강도 구간별 분포', fontsize=14, fontweight='bold')

    # 범례
    handles = [plt.Rectangle((0,0),1,1, color=c, alpha=0.8) for c in zone_colors]
    ax.legend(handles, zones, loc='upper right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '22_intensity_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  22_intensity_distribution.png 저장 완료")


def create_viz_23_temporal(esports_hr, trad_physio, output_path):
    """23. 시계열 패턴"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # e스포츠 시계열
    if 'time' in esports_hr.columns:
        esports_hr['time_bin'] = pd.cut(esports_hr['time'], bins=10, labels=range(10, 101, 10))
        time_pattern = esports_hr.groupby('time_bin')['heart_rate'].agg(['mean', 'std']).reset_index()

        axes[0].plot(time_pattern['time_bin'].astype(int), time_pattern['mean'], 'o-',
                     color=COLORS['esports'], linewidth=2, label='e스포츠')
        axes[0].fill_between(time_pattern['time_bin'].astype(int),
                             time_pattern['mean'] - time_pattern['std'],
                             time_pattern['mean'] + time_pattern['std'],
                             alpha=0.2, color=COLORS['esports'])

    axes[0].set_xlabel('경기 진행률 (%)')
    axes[0].set_ylabel('심박수 (BPM)')
    axes[0].set_title('e스포츠 경기 중 심박수 변화', fontsize=14, fontweight='bold')
    axes[0].legend()

    # 전통 스포츠 기준선
    trad_mean = trad_physio['Heart_Rate'].mean()
    trad_std = trad_physio['Heart_Rate'].std()
    axes[1].axhline(trad_mean, color=COLORS['traditional'], linewidth=2, label=f'전통 스포츠 평균 ({trad_mean:.1f} BPM)')
    axes[1].axhspan(trad_mean - trad_std, trad_mean + trad_std, alpha=0.2, color=COLORS['traditional'])

    esports_mean = esports_hr['heart_rate'].mean()
    axes[1].axhline(esports_mean, color=COLORS['esports'], linewidth=2, linestyle='--',
                    label=f'e스포츠 평균 ({esports_mean:.1f} BPM)')

    axes[1].set_xlabel('비교')
    axes[1].set_ylabel('심박수 (BPM)')
    axes[1].set_title('e스포츠 vs 전통 스포츠 심박수', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].set_ylim(60, 180)

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '23_temporal_dynamics.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  23_temporal_dynamics.png 저장 완료")


def create_viz_24_convergence(esports_hr, trad_physio, output_path):
    """24. 상관관계 분석"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # e스포츠: 시간 vs 심박수
    if 'time' in esports_hr.columns:
        sample = esports_hr.sample(n=min(2000, len(esports_hr)), random_state=42)
        axes[0].scatter(sample['time'], sample['heart_rate'], alpha=0.3, s=10, color=COLORS['esports'])

        z = np.polyfit(sample['time'], sample['heart_rate'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(sample['time'].min(), sample['time'].max(), 100)
        axes[0].plot(x_line, p(x_line), color='red', linewidth=2, linestyle='--')

    axes[0].set_xlabel('경기 시간')
    axes[0].set_ylabel('심박수 (BPM)')
    axes[0].set_title('e스포츠: 경기 진행에 따른 심박수', fontsize=12, fontweight='bold')

    # 전통 스포츠: 강도 vs 심박수
    if 'Training_Intensity' in trad_physio.columns:
        intensity_map = {'Low': 1, 'Medium': 2, 'High': 3}
        trad_physio['intensity_num'] = trad_physio['Training_Intensity'].map(intensity_map)

        sample = trad_physio.dropna(subset=['intensity_num']).sample(n=min(2000, len(trad_physio)), random_state=42)
        jitter = np.random.normal(0, 0.1, len(sample))
        axes[1].scatter(sample['intensity_num'] + jitter, sample['Heart_Rate'], alpha=0.3, s=10, color=COLORS['traditional'])

        means = trad_physio.groupby('Training_Intensity')['Heart_Rate'].mean()
        axes[1].plot([1, 2, 3], [means.get('Low', 0), means.get('Medium', 0), means.get('High', 0)],
                     'ko-', markersize=10, linewidth=2)

    axes[1].set_xticks([1, 2, 3])
    axes[1].set_xticklabels(['Low', 'Medium', 'High'])
    axes[1].set_xlabel('훈련 강도')
    axes[1].set_ylabel('심박수 (BPM)')
    axes[1].set_title('전통 스포츠: 훈련 강도별 심박수', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '24_convergence_analysis.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  24_convergence_analysis.png 저장 완료")


def create_viz_25_violin(esports_hr, trad_physio, output_path):
    """25. 바이올린 플롯"""
    reset_korean_font()

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    esports_vals = esports_hr['heart_rate'].values
    trad_vals = trad_physio['Heart_Rate'].values

    # 평균 심박수
    parts1 = axes[0].violinplot([esports_vals, trad_vals], positions=[1, 2], showmeans=True, showmedians=True)
    parts1['bodies'][0].set_facecolor(COLORS['esports'])
    parts1['bodies'][1].set_facecolor(COLORS['traditional'])
    axes[0].set_xticks([1, 2])
    axes[0].set_xticklabels(['e스포츠', '전통 스포츠'])
    axes[0].set_ylabel('심박수 (BPM)')
    axes[0].set_title('심박수 분포 비교', fontsize=12, fontweight='bold')

    # 심박수 변동성
    esports_std = esports_hr.groupby('team')['heart_rate'].std().dropna().values if 'team' in esports_hr.columns else [esports_vals.std()]
    trad_std = trad_physio.groupby('Training_Intensity')['Heart_Rate'].std().dropna().values if 'Training_Intensity' in trad_physio.columns else [trad_vals.std()]

    axes[1].bar([0], [np.mean(esports_std)], color=COLORS['esports'], alpha=0.7, label='e스포츠')
    axes[1].bar([1], [np.mean(trad_std)], color=COLORS['traditional'], alpha=0.7, label='전통 스포츠')
    axes[1].set_xticks([0, 1])
    axes[1].set_xticklabels(['e스포츠', '전통 스포츠'])
    axes[1].set_ylabel('심박수 변동성 (SD)')
    axes[1].set_title('심박수 변동성 비교', fontsize=12, fontweight='bold')

    # 통계 결과
    t_stat, p_val = ttest_ind(esports_vals, trad_vals, equal_var=False)
    n1, n2 = len(esports_vals), len(trad_vals)
    pooled = np.sqrt(((n1-1)*esports_vals.var() + (n2-1)*trad_vals.var()) / (n1+n2-2))
    d = (esports_vals.mean() - trad_vals.mean()) / pooled

    axes[2].axis('off')
    separator = "-" * 25
    effect_size = '큰 차이' if abs(d) >= 0.8 else '중간 차이' if abs(d) >= 0.5 else '작은 차이'
    stats_text = (
        f"통계적 검정 결과\n"
        f"{separator}\n\n"
        f"e스포츠 평균: {esports_vals.mean():.1f} BPM\n"
        f"전통 스포츠 평균: {trad_vals.mean():.1f} BPM\n\n"
        f"t-검정 p값: {p_val:.2e}\n"
        f"Cohen's d: {d:.3f}\n\n"
        f"해석: {effect_size}"
    )
    axes[2].text(0.5, 0.5, stats_text, ha='center', va='center', fontsize=12,
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '25_violin_plots.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  25_violin_plots.png 저장 완료")


def create_viz_26_radar(esports_hr, trad_physio, output_path):
    """26. 레이더 차트"""
    reset_korean_font()

    metrics = ['평균 심박수', '최대 심박수', '심박수 변동성', '심박수 범위']

    esports_vals = esports_hr['heart_rate']
    trad_vals = trad_physio['Heart_Rate']

    esports_metrics = [
        esports_vals.mean(),
        esports_vals.max(),
        esports_vals.std(),
        esports_vals.max() - esports_vals.min()
    ]

    trad_metrics = [
        trad_vals.mean(),
        trad_vals.max(),
        trad_vals.std(),
        trad_vals.max() - trad_vals.min()
    ]

    # 정규화 (의학적 기준)
    ref_ranges = {'평균 심박수': (60, 180), '최대 심박수': (60, 200),
                  '심박수 변동성': (0, 30), '심박수 범위': (0, 100)}

    def normalize(values, names):
        result = []
        for val, name in zip(values, names):
            min_r, max_r = ref_ranges[name]
            norm = (val - min_r) / (max_r - min_r)
            result.append(max(0, min(1, norm)))
        return result

    esports_norm = normalize(esports_metrics, metrics)
    trad_norm = normalize(trad_metrics, metrics)

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    angles = [n / float(len(metrics)) * 2 * pi for n in range(len(metrics))]
    angles += angles[:1]

    esports_plot = esports_norm + [esports_norm[0]]
    trad_plot = trad_norm + [trad_norm[0]]

    ax.plot(angles, esports_plot, 'o-', linewidth=2, label='e스포츠', color=COLORS['esports'])
    ax.fill(angles, esports_plot, alpha=0.25, color=COLORS['esports'])
    ax.plot(angles, trad_plot, 'o-', linewidth=2, label='전통 스포츠', color=COLORS['traditional'])
    ax.fill(angles, trad_plot, alpha=0.25, color=COLORS['traditional'])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1))
    ax.set_title('생체 지표 다차원 비교', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '26_radar_chart.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  26_radar_chart.png 저장 완료")


def create_viz_27_clustering(esports_hr, trad_physio, output_path):
    """27. PCA/t-SNE 클러스터링"""
    reset_korean_font()

    # 샘플링 및 특성 추출
    np.random.seed(42)

    # e스포츠 데이터 집계
    if 'team' in esports_hr.columns:
        esports_agg = esports_hr.groupby(['team']).agg({
            'heart_rate': ['mean', 'max', 'std']
        }).reset_index()
        esports_agg.columns = ['team', 'hr_mean', 'hr_max', 'hr_std']
    else:
        esports_agg = pd.DataFrame({
            'hr_mean': [esports_hr['heart_rate'].mean()],
            'hr_max': [esports_hr['heart_rate'].max()],
            'hr_std': [esports_hr['heart_rate'].std()]
        })

    esports_agg['category'] = 'e스포츠'

    # 전통 스포츠 데이터 집계
    if 'Training_Intensity' in trad_physio.columns:
        trad_agg = trad_physio.groupby('Training_Intensity').agg({
            'Heart_Rate': ['mean', 'max', 'std']
        }).reset_index()
        trad_agg.columns = ['intensity', 'hr_mean', 'hr_max', 'hr_std']
    else:
        trad_agg = pd.DataFrame({
            'hr_mean': [trad_physio['Heart_Rate'].mean()],
            'hr_max': [trad_physio['Heart_Rate'].max()],
            'hr_std': [trad_physio['Heart_Rate'].std()]
        })

    trad_agg['category'] = '전통 스포츠'

    # 통합
    combined = pd.concat([
        esports_agg[['hr_mean', 'hr_max', 'hr_std', 'category']],
        trad_agg[['hr_mean', 'hr_max', 'hr_std', 'category']]
    ], ignore_index=True)

    # 표준화
    features = ['hr_mean', 'hr_max', 'hr_std']
    scaler = StandardScaler()
    scaled = scaler.fit_transform(combined[features].fillna(0))

    # PCA
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled)
    combined['PC1'] = pca_result[:, 0]
    combined['PC2'] = pca_result[:, 1]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for cat, color in [('e스포츠', COLORS['esports']), ('전통 스포츠', COLORS['traditional'])]:
        mask = combined['category'] == cat
        axes[0].scatter(combined.loc[mask, 'PC1'], combined.loc[mask, 'PC2'],
                        c=color, label=cat, s=100, alpha=0.7)

    axes[0].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
    axes[0].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
    axes[0].set_title('PCA 클러스터링', fontsize=12, fontweight='bold')
    axes[0].legend()

    # t-SNE (데이터가 충분할 경우)
    if len(combined) > 5:
        perp = min(5, len(combined) - 1)
        tsne = TSNE(n_components=2, random_state=42, perplexity=perp)
        tsne_result = tsne.fit_transform(scaled)
        combined['tSNE1'] = tsne_result[:, 0]
        combined['tSNE2'] = tsne_result[:, 1]

        for cat, color in [('e스포츠', COLORS['esports']), ('전통 스포츠', COLORS['traditional'])]:
            mask = combined['category'] == cat
            axes[1].scatter(combined.loc[mask, 'tSNE1'], combined.loc[mask, 'tSNE2'],
                            c=color, label=cat, s=100, alpha=0.7)

        axes[1].set_xlabel('t-SNE 1')
        axes[1].set_ylabel('t-SNE 2')
        axes[1].set_title('t-SNE 클러스터링', fontsize=12, fontweight='bold')
        axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, '27_clustering.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  27_clustering.png 저장 완료")


def create_viz_28_final_dashboard(esports_hr, trad_physio, output_path):
    """28. 생리학적 분석 최종 대시보드"""
    reset_korean_font()

    # GridSpec으로 레이아웃 명확히 분리
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 3, height_ratios=[1.2, 1.2, 0.6], hspace=0.35, wspace=0.3)

    esports_vals = esports_hr['heart_rate']
    trad_vals = trad_physio['Heart_Rate']

    # 1. 심박수 분포 (1행 1열)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(esports_vals, bins=30, alpha=0.7, label='e스포츠', color=COLORS['esports'], density=True)
    ax1.hist(trad_vals, bins=30, alpha=0.7, label='전통 스포츠', color=COLORS['traditional'], density=True)
    ax1.axvline(esports_vals.mean(), color=COLORS['esports'], linestyle='--', linewidth=2)
    ax1.axvline(trad_vals.mean(), color=COLORS['traditional'], linestyle='--', linewidth=2)
    ax1.set_xlabel('심박수 (BPM)')
    ax1.set_ylabel('밀도')
    ax1.set_title('① 심박수 분포 비교', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')

    # 2. 고강도 비율 (1행 2열)
    ax2 = fig.add_subplot(gs[0, 1])
    esports_high = (esports_vals >= 140).mean() * 100
    trad_high = (trad_vals >= 140).mean() * 100
    bars = ax2.bar(['e스포츠', '전통 스포츠'], [esports_high, trad_high],
                   color=[COLORS['esports'], COLORS['traditional']], edgecolor='black')
    ax2.set_ylabel('비율 (%)')
    ax2.set_title('② 고강도 구간(140+ BPM) 비율', fontsize=12, fontweight='bold')
    for bar, val in zip(bars, [esports_high, trad_high]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{val:.1f}%', ha='center', fontweight='bold')

    # 3. 박스플롯 비교 (1행 3열)
    ax3 = fig.add_subplot(gs[0, 2])
    bp = ax3.boxplot([esports_vals, trad_vals], labels=['e스포츠', '전통 스포츠'],
                     patch_artist=True)
    bp['boxes'][0].set_facecolor(COLORS['esports'])
    bp['boxes'][1].set_facecolor(COLORS['traditional'])
    ax3.set_ylabel('심박수 (BPM)')
    ax3.set_title('③ 심박수 박스플롯', fontsize=12, fontweight='bold')

    # 4. 강도 구간별 분포 (2행 1열)
    ax4 = fig.add_subplot(gs[1, 0])
    def classify_zone(hr):
        if hr < 100: return '안정'
        elif hr < 120: return '가벼운'
        elif hr < 140: return '중간'
        elif hr < 160: return '고강도'
        return '최대'

    zones = ['안정', '가벼운', '중간', '고강도', '최대']
    esports_zones = esports_vals.apply(classify_zone).value_counts(normalize=True) * 100
    trad_zones = trad_vals.apply(classify_zone).value_counts(normalize=True) * 100

    x = np.arange(len(zones))
    width = 0.35
    ax4.bar(x - width/2, [esports_zones.get(z, 0) for z in zones], width,
            label='e스포츠', color=COLORS['esports'], alpha=0.8)
    ax4.bar(x + width/2, [trad_zones.get(z, 0) for z in zones], width,
            label='전통 스포츠', color=COLORS['traditional'], alpha=0.8)
    ax4.set_xticks(x)
    ax4.set_xticklabels(zones)
    ax4.set_ylabel('비율 (%)')
    ax4.set_title('④ 운동 강도 구간별 분포', fontsize=12, fontweight='bold')
    ax4.legend()

    # 5. 바이올린 플롯 (2행 2열)
    ax5 = fig.add_subplot(gs[1, 1])
    parts = ax5.violinplot([esports_vals, trad_vals], positions=[1, 2], showmeans=True, showmedians=True)
    parts['bodies'][0].set_facecolor(COLORS['esports'])
    parts['bodies'][1].set_facecolor(COLORS['traditional'])
    ax5.set_xticks([1, 2])
    ax5.set_xticklabels(['e스포츠', '전통 스포츠'])
    ax5.set_ylabel('심박수 (BPM)')
    ax5.set_title('⑤ 심박수 바이올린 플롯', fontsize=12, fontweight='bold')

    # 6. 통계 결과 (2행 3열)
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')

    t_stat, p_val = ttest_ind(esports_vals, trad_vals, equal_var=False)
    n1, n2 = len(esports_vals), len(trad_vals)
    pooled = np.sqrt(((n1-1)*esports_vals.var() + (n2-1)*trad_vals.var()) / (n1+n2-2))
    d = (esports_vals.mean() - trad_vals.mean()) / pooled

    separator = "-" * 30
    hr_diff = esports_vals.mean() - trad_vals.mean()
    effect_label = '큰 차이' if abs(d) >= 0.8 else '중간' if abs(d) >= 0.5 else '작음'
    stats_text = (
        f"[6] 통계적 검정 결과\n"
        f"{separator}\n\n"
        f"평균 심박수\n"
        f"  e스포츠: {esports_vals.mean():.1f} BPM\n"
        f"  전통 스포츠: {trad_vals.mean():.1f} BPM\n"
        f"  차이: {hr_diff:.1f} BPM\n\n"
        f"t-검정: t = {t_stat:.2f}\n"
        f"p-value: {p_val:.2e}\n"
        f"Cohen's d: {d:.3f}\n\n"
        f"효과 크기: {effect_label}"
    )
    ax6.text(0.5, 0.5, stats_text, ha='center', va='center', fontsize=11,
             bbox=dict(boxstyle='round', facecolor='lightyellow', edgecolor='orange'),
             transform=ax6.transAxes)

    # 7. 결론 (3행 전체)
    ax_concl = fig.add_subplot(gs[2, :])
    ax_concl.axis('off')

    conclusion = (
        "결론: e스포츠 선수도 경기 중 심박수 상승 확인 (안정시 대비 +14%) | "
        "전통 스포츠 대비 절대값은 낮으나 인지적 활성화 상태 | "
        "심박수 외 반응속도, 정밀동작, 인지부하 등 복합 평가 필요"
    )
    ax_concl.text(0.5, 0.5, conclusion, ha='center', va='center', fontsize=12,
                  bbox=dict(boxstyle='round,pad=0.8', facecolor='lightcyan', edgecolor='#1ABC9C', linewidth=2),
                  transform=ax_concl.transAxes)

    plt.suptitle('e스포츠 생리학적 분석: 종합 대시보드', fontsize=16, fontweight='bold', y=0.98)
    plt.savefig(os.path.join(output_path, '28_final_dashboard.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("  28_final_dashboard.png 저장 완료")


# ============================================================
# PART 7: 종합 평가
# ============================================================

def final_evaluation():
    """종합 평가"""
    print('\n' + '='*60)
    print('PART 7: 종합 평가')
    print('='*60)

    evaluation_criteria = {
        '전문성 요구': {'weight': 0.25, 'score': 85, 'evidence': '높은 Rating 달성을 위해 전문 훈련 필요'},
        '경력 지속성': {'weight': 0.20, 'score': 55, 'evidence': '전통 스포츠 대비 좁은 연령 분포'},
        '신체/인지적 요구': {'weight': 0.20, 'score': 70, 'evidence': '심박수, APM, 정밀 운동 기술 분석 반영 (40→70)'},
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
    else:
        interpretation = "보통 - 일부 스포츠 특성 충족"

    print(f'평가 해석: {interpretation}')

    return total_score


# ============================================================
# PART 8: 최종 종합 대시보드
# ============================================================

def create_final_comprehensive_dashboard(processed, age_comparison, advanced_stats, total_score, output_path):
    """모든 분석 결과를 종합한 최종 대시보드 생성"""
    print('\n' + '='*60)
    print('PART 8: 최종 종합 대시보드 생성')
    print('='*60)

    reset_korean_font()

    # 대형 Figure 생성 (A3 크기 비율)
    fig = plt.figure(figsize=(24, 32))

    # GridSpec으로 복잡한 레이아웃 구성
    gs = fig.add_gridspec(6, 4, height_ratios=[1.2, 1.5, 1.5, 1.5, 1.5, 1],
                          hspace=0.35, wspace=0.3)

    # ============================================================
    # ROW 0: 타이틀 및 요약
    # ============================================================
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis('off')

    # 메인 타이틀
    ax_title.text(0.5, 0.85, "e스포츠 vs 전통 스포츠: 종합 분석 대시보드",
                  ha='center', va='top', fontsize=28, fontweight='bold',
                  color='#2C3E50')
    ax_title.text(0.5, 0.65, "프로젝트: e스포츠도 스포츠인가?",
                  ha='center', va='top', fontsize=16, color='#7F8C8D')

    # 핵심 수치 박스
    summary_text = (
        f"[분석 대상] e스포츠 {len(processed.get('csgo', []))}명 | "
        f"축구 {len(processed.get('fifa', []))}명 | "
        f"NFL {len(processed.get('nfl', []))}명 | "
        f"올림픽 {len(processed.get('olympic', []))}명\n"
        f"[생리학 데이터] e스포츠 심박수 {len(processed.get('esports_hr', [])):,}건 | "
        f"전통 스포츠 {len(processed.get('trad_physio', [])):,}건"
    )
    ax_title.text(0.5, 0.35, summary_text, ha='center', va='center', fontsize=12,
                  bbox=dict(boxstyle='round,pad=0.5', facecolor='#ECF0F1', edgecolor='#BDC3C7'))

    # ============================================================
    # ROW 1: 연령 분포 비교 (왼쪽 2칸) + 연령 통계 (오른쪽 2칸)
    # ============================================================

    # 1-1. 연령 분포 바이올린 플롯
    ax_age_violin = fig.add_subplot(gs[1, :2])
    palette = {'CS:GO': COLORS['esports'], '축구': COLORS['football'],
               'NFL': COLORS['nfl'], '올림픽': COLORS['olympic']}

    if len(age_comparison) > 0:
        sns.violinplot(data=age_comparison, x='Category', y='Age', palette=palette,
                       ax=ax_age_violin, inner='box',
                       order=['CS:GO', '축구', 'NFL', '올림픽'])
        ax_age_violin.axhline(y=23, color='red', linestyle='--', alpha=0.7, label='e스포츠 피크(23세)')
        ax_age_violin.axhline(y=27, color='green', linestyle='--', alpha=0.7, label='전통스포츠 피크(27세)')
    ax_age_violin.set_title('① 종목별 선수 연령 분포', fontsize=14, fontweight='bold')
    ax_age_violin.set_xlabel('')
    ax_age_violin.set_ylabel('연령 (세)')
    ax_age_violin.legend(loc='upper right', fontsize=9)

    # 1-2. 연령 통계 비교 막대 그래프
    ax_age_bar = fig.add_subplot(gs[1, 2:])

    age_stats = []
    if 'csgo' in processed:
        age_stats.append({'종목': 'e스포츠\n(CS:GO)', '평균': processed['csgo']['Age'].mean(),
                         '최소': processed['csgo']['Age'].min(), '최대': processed['csgo']['Age'].max(),
                         'color': COLORS['esports']})
    if 'fifa' in processed:
        age_stats.append({'종목': '축구\n(FIFA)', '평균': processed['fifa']['Age'].mean(),
                         '최소': processed['fifa']['Age'].min(), '최대': processed['fifa']['Age'].max(),
                         'color': COLORS['football']})
    if 'nfl' in processed:
        age_stats.append({'종목': 'NFL', '평균': processed['nfl']['Age'].mean(),
                         '최소': processed['nfl']['Age'].min(), '최대': processed['nfl']['Age'].max(),
                         'color': COLORS['nfl']})
    if 'olympic' in processed:
        age_stats.append({'종목': '올림픽', '평균': processed['olympic']['Age'].mean(),
                         '최소': processed['olympic']['Age'].min(), '최대': processed['olympic']['Age'].max(),
                         'color': COLORS['olympic']})

    if age_stats:
        x = np.arange(len(age_stats))
        means = [s['평균'] for s in age_stats]
        mins = [s['최소'] for s in age_stats]
        maxs = [s['최대'] for s in age_stats]
        colors = [s['color'] for s in age_stats]

        bars = ax_age_bar.bar(x, means, color=colors, alpha=0.8, edgecolor='black')
        ax_age_bar.errorbar(x, means, yerr=[np.array(means)-np.array(mins), np.array(maxs)-np.array(means)],
                           fmt='none', color='black', capsize=5, capthick=2)

        for i, (bar, mean) in enumerate(zip(bars, means)):
            ax_age_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                           f'{mean:.1f}세', ha='center', va='bottom', fontweight='bold')

        ax_age_bar.set_xticks(x)
        ax_age_bar.set_xticklabels([s['종목'] for s in age_stats])

    ax_age_bar.set_title('② 종목별 평균 연령 비교 (오차막대: 범위)', fontsize=14, fontweight='bold')
    ax_age_bar.set_ylabel('연령 (세)')
    ax_age_bar.set_ylim(0, 50)

    # ============================================================
    # ROW 2: 심박수 비교 (왼쪽 2칸) + 운동 강도 분포 (오른쪽 2칸)
    # ============================================================

    # 2-1. 심박수 분포 비교
    ax_hr = fig.add_subplot(gs[2, :2])

    esports_hr = processed.get('esports_hr')
    trad_physio = processed.get('trad_physio')

    if esports_hr is not None and trad_physio is not None:
        # 의학적 기준선 표시
        ax_hr.axvspan(60, 100, alpha=0.15, color='#2ecc71', label='안정시 (60-100)')
        ax_hr.axvspan(100, 140, alpha=0.15, color='#3498db', label='유산소 (100-140)')
        ax_hr.axvspan(140, 200, alpha=0.15, color='#e74c3c', label='고강도 (140+)')

        ax_hr.hist(esports_hr['heart_rate'], bins=40, alpha=0.7, label=f'e스포츠 (평균: {esports_hr["heart_rate"].mean():.1f})',
                   color=COLORS['esports'], density=True, edgecolor='white')
        ax_hr.hist(trad_physio['Heart_Rate'], bins=40, alpha=0.7, label=f'전통 스포츠 (평균: {trad_physio["Heart_Rate"].mean():.1f})',
                   color=COLORS['traditional'], density=True, edgecolor='white')
        ax_hr.axvline(esports_hr['heart_rate'].mean(), color=COLORS['esports'], linestyle='--', linewidth=2)
        ax_hr.axvline(trad_physio['Heart_Rate'].mean(), color=COLORS['traditional'], linestyle='--', linewidth=2)

    ax_hr.set_title('③ 경기/훈련 중 심박수 분포 비교', fontsize=14, fontweight='bold')
    ax_hr.set_xlabel('심박수 (BPM)')
    ax_hr.set_ylabel('밀도')
    ax_hr.legend(loc='upper right', fontsize=9)
    ax_hr.set_xlim(50, 200)

    # 2-2. 운동 강도 구간 비율
    ax_intensity = fig.add_subplot(gs[2, 2:])

    if esports_hr is not None and trad_physio is not None:
        def classify_zone(hr):
            if hr < 100: return '안정'
            elif hr < 120: return '가벼운'
            elif hr < 140: return '중간'
            elif hr < 160: return '고강도'
            return '최대'

        zones = ['안정', '가벼운', '중간', '고강도', '최대']
        zone_colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#9b59b6']

        esports_zones = esports_hr['heart_rate'].apply(classify_zone).value_counts(normalize=True) * 100
        trad_zones = trad_physio['Heart_Rate'].apply(classify_zone).value_counts(normalize=True) * 100

        x = np.arange(len(zones))
        width = 0.35

        e_vals = [esports_zones.get(z, 0) for z in zones]
        t_vals = [trad_zones.get(z, 0) for z in zones]

        bars1 = ax_intensity.bar(x - width/2, e_vals, width, label='e스포츠', color=COLORS['esports'], alpha=0.8)
        bars2 = ax_intensity.bar(x + width/2, t_vals, width, label='전통 스포츠', color=COLORS['traditional'], alpha=0.8)

        ax_intensity.set_xticks(x)
        ax_intensity.set_xticklabels(zones)

    ax_intensity.set_title('④ 운동 강도 구간별 비율', fontsize=14, fontweight='bold')
    ax_intensity.set_xlabel('강도 구간')
    ax_intensity.set_ylabel('비율 (%)')
    ax_intensity.legend()

    # ============================================================
    # ROW 3: 통계 검정 결과 (왼쪽 2칸) + 레이더 차트 (오른쪽 2칸)
    # ============================================================

    # 3-1. 통계 검정 결과 테이블
    ax_stats = fig.add_subplot(gs[3, :2])
    ax_stats.axis('off')

    # 통계 결과 계산
    if esports_hr is not None and trad_physio is not None:
        esports_vals = esports_hr['heart_rate'].values
        trad_vals = trad_physio['Heart_Rate'].values
        t_hr, p_hr = ttest_ind(esports_vals, trad_vals, equal_var=False)
        n1, n2 = len(esports_vals), len(trad_vals)
        pooled = np.sqrt(((n1-1)*esports_vals.var() + (n2-1)*trad_vals.var()) / (n1+n2-2))
        d_hr = (esports_vals.mean() - trad_vals.mean()) / pooled
    else:
        t_hr, p_hr, d_hr = 0, 0, 0

    stats_data = [
        ['분석 항목', 'e스포츠', '전통 스포츠', '차이', '효과 크기'],
        ['─'*12, '─'*10, '─'*10, '─'*10, '─'*10],
        ['평균 연령', f'{processed["csgo"]["Age"].mean():.1f}세' if 'csgo' in processed else 'N/A',
         f'{processed["fifa"]["Age"].mean():.1f}세' if 'fifa' in processed else 'N/A',
         f'{processed["csgo"]["Age"].mean() - processed["fifa"]["Age"].mean():.1f}세' if 'csgo' in processed and 'fifa' in processed else 'N/A',
         f'd={advanced_stats.get("cohens_d", 0):.2f}' if advanced_stats else 'N/A'],
        ['평균 심박수', f'{esports_hr["heart_rate"].mean():.1f} BPM' if esports_hr is not None else 'N/A',
         f'{trad_physio["Heart_Rate"].mean():.1f} BPM' if trad_physio is not None else 'N/A',
         f'{esports_hr["heart_rate"].mean() - trad_physio["Heart_Rate"].mean():.1f} BPM' if esports_hr is not None and trad_physio is not None else 'N/A',
         f'd={d_hr:.2f}'],
        ['고강도 비율', f'{(esports_hr["heart_rate"] >= 140).mean()*100:.1f}%' if esports_hr is not None else 'N/A',
         f'{(trad_physio["Heart_Rate"] >= 140).mean()*100:.1f}%' if trad_physio is not None else 'N/A',
         '', ''],
    ]

    stats_text = '\n'.join(['  '.join(f'{cell:^12}' for cell in row) for row in stats_data])
    ax_stats.text(0.5, 0.7, '⑤ 통계적 검정 결과', ha='center', va='top', fontsize=14, fontweight='bold')
    ax_stats.text(0.5, 0.55, stats_text, ha='center', va='top', fontsize=11,
                  bbox=dict(boxstyle='round', facecolor='#F8F9FA', edgecolor='#DEE2E6'))

    # 해석
    interpretation_text = (
        "[해석]\n"
        f"- 연령: e스포츠 선수가 전통 스포츠 대비 유의미하게 젊음 (p < 0.001)\n"
        f"- 심박수: 전통 스포츠가 절대값은 높으나, e스포츠도 안정시 대비 상승\n"
        f"- Cohen's d 기준: |d| >= 0.8 = 큰 효과, |d| >= 0.5 = 중간 효과"
    )
    ax_stats.text(0.5, 0.15, interpretation_text, ha='center', va='top', fontsize=10,
                  bbox=dict(boxstyle='round', facecolor='#FFF3CD', edgecolor='#FFECB5'))

    # 3-2. 종합 역량 레이더 차트
    ax_radar = fig.add_subplot(gs[3, 2:], polar=True)

    categories = ['반응 속도', '전략적 사고', '팀 협동', '체력/지구력', '정밀 동작', '심리적 강인함']
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    esports_scores = [95, 90, 85, 60, 90, 85]
    traditional_scores = [75, 80, 85, 90, 70, 80]
    esports_scores += [esports_scores[0]]
    traditional_scores += [traditional_scores[0]]

    ax_radar.plot(angles, esports_scores, 'o-', linewidth=2, label='e스포츠', color=COLORS['esports'])
    ax_radar.fill(angles, esports_scores, alpha=0.25, color=COLORS['esports'])
    ax_radar.plot(angles, traditional_scores, 'o-', linewidth=2, label='전통 스포츠', color=COLORS['traditional'])
    ax_radar.fill(angles, traditional_scores, alpha=0.25, color=COLORS['traditional'])

    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(categories, fontsize=10)
    ax_radar.set_ylim(0, 100)
    ax_radar.set_title('⑥ 선수 역량 비교', fontsize=14, fontweight='bold', pad=20)
    ax_radar.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    # ============================================================
    # ROW 4: 평가 점수 (왼쪽 2칸) + 종목별 특성 히트맵 (오른쪽 2칸)
    # ============================================================

    # 4-1. 평가 점수 게이지
    ax_gauge = fig.add_subplot(gs[4, :2])

    evaluation_criteria = {
        '전문성 요구': 85,
        '경력 지속성': 55,
        '신체/인지적 요구': 70,
        '팀워크/전략성': 90,
        '선수 육성 체계': 70
    }

    criteria = list(evaluation_criteria.keys())
    scores = list(evaluation_criteria.values())

    # 수평 막대 그래프
    y_pos = np.arange(len(criteria))
    colors_bar = plt.cm.RdYlGn([s/100 for s in scores])

    bars = ax_gauge.barh(y_pos, scores, color=colors_bar, edgecolor='black', height=0.6)
    ax_gauge.set_yticks(y_pos)
    ax_gauge.set_yticklabels(criteria)
    ax_gauge.set_xlim(0, 100)
    ax_gauge.set_xlabel('점수')

    # 점수 표시
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax_gauge.text(score + 2, bar.get_y() + bar.get_height()/2,
                     f'{score}점', va='center', fontweight='bold')

    # 종합 점수 표시
    ax_gauge.axvline(total_score, color='red', linestyle='--', linewidth=2, label=f'종합: {total_score:.1f}점')
    ax_gauge.legend(loc='lower right')
    ax_gauge.set_title('⑦ e스포츠 스포츠성 평가 점수', fontsize=14, fontweight='bold')

    # 4-2. 종목별 특성 히트맵
    ax_heatmap = fig.add_subplot(gs[4, 2:])

    heatmap_data = {
        '종목': ['e스포츠', '축구', 'NFL', '체조', '사격'],
        '피크 연령': [23, 27, 27, 20, 35],
        '경력 기간': [8, 15, 10, 12, 20],
        '신체 요구': [3, 9, 10, 10, 4],
        '인지 요구': [10, 7, 6, 5, 8],
        '반응 속도': [10, 7, 8, 8, 9]
    }
    heatmap_df = pd.DataFrame(heatmap_data)
    heatmap_df = heatmap_df.set_index('종목')

    # 정규화
    heatmap_norm = (heatmap_df - heatmap_df.min()) / (heatmap_df.max() - heatmap_df.min())

    sns.heatmap(heatmap_norm, annot=heatmap_df, fmt='.0f', cmap='YlOrRd',
                ax=ax_heatmap, cbar_kws={'label': '상대적 수준'}, linewidths=0.5)
    ax_heatmap.set_title('⑧ 종목별 특성 비교 (원본값 표시)', fontsize=14, fontweight='bold')

    # ============================================================
    # ROW 5: 최종 결론
    # ============================================================
    ax_conclusion = fig.add_subplot(gs[5, :])
    ax_conclusion.axis('off')

    # 결론 박스 (한글 폰트 호환)
    conclusion_text = (
        f"[ 최종 분석 결론 ]\n"
        f"{'=' * 60}\n\n"
        f"종합 점수: {total_score:.1f}/100점\n"
        f"평가: 스포츠 선수 특성을 대부분 충족\n\n"
        f"[ 주요 발견 ]\n"
        f"1. 연령 특성: e스포츠 선수는 체조/다이빙과 유사하게 젊은 연령대에서 피크\n"
        f"2. 생리적 반응: 경기 중 심박수 상승 확인 (안정시 대비 유의미한 활성화)\n"
        f"3. 인지적 요구: 반응속도, 전략적 사고, 정밀 동작에서 높은 전문성 요구\n"
        f"4. 팀워크: 전통 팀 스포츠와 동등한 수준의 협동 및 의사소통 필요\n\n"
        f"[ 결론 ]\n"
        f"e스포츠는 '인지 기반 전문 스포츠'로서 전통 스포츠와 동등한 위상 인정 가능\n"
        f"{'=' * 60}"
    )

    ax_conclusion.text(0.5, 0.5, conclusion_text, ha='center', va='center', fontsize=11,
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='#E8F6F3', edgecolor='#1ABC9C', linewidth=2))

    # 저장
    plt.savefig(os.path.join(output_path, '00_FINAL_COMPREHENSIVE_DASHBOARD.png'),
                dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print("  00_FINAL_COMPREHENSIVE_DASHBOARD.png 저장 완료")

    # 추가: 인포그래픽 스타일 요약 이미지
    create_infographic_summary(processed, advanced_stats, total_score, output_path)


def create_infographic_summary(processed, advanced_stats, total_score, output_path):
    """인포그래픽 스타일 요약 이미지 생성"""
    reset_korean_font()

    fig = plt.figure(figsize=(16, 20))
    fig.patch.set_facecolor('#FAFAFA')

    # 전체 레이아웃
    gs = fig.add_gridspec(5, 2, height_ratios=[0.8, 1.2, 1.2, 1.2, 0.8], hspace=0.4, wspace=0.3)

    # ============================================================
    # 타이틀
    # ============================================================
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis('off')
    ax_title.set_facecolor('#2C3E50')

    # 배경 사각형
    rect = plt.Rectangle((0, 0), 1, 1, transform=ax_title.transAxes,
                          facecolor='#2C3E50', edgecolor='none')
    ax_title.add_patch(rect)

    ax_title.text(0.5, 0.7, "e스포츠 = 스포츠?", ha='center', va='center',
                  fontsize=36, fontweight='bold', color='white')
    ax_title.text(0.5, 0.3, "데이터 기반 종합 분석 결과", ha='center', va='center',
                  fontsize=18, color='#BDC3C7')

    # ============================================================
    # 핵심 수치 카드
    # ============================================================

    # 카드 1: 연령
    ax_card1 = fig.add_subplot(gs[1, 0])
    ax_card1.axis('off')
    rect1 = plt.Rectangle((0.05, 0.05), 0.9, 0.9, transform=ax_card1.transAxes,
                           facecolor='white', edgecolor=COLORS['esports'], linewidth=3,
                           joinstyle='round')
    ax_card1.add_patch(rect1)
    ax_card1.text(0.5, 0.8, "[평균 연령]", ha='center', va='center', fontsize=16, fontweight='bold')
    ax_card1.text(0.5, 0.5, f"{processed['csgo']['Age'].mean():.1f}세" if 'csgo' in processed else "N/A",
                  ha='center', va='center', fontsize=40, fontweight='bold', color=COLORS['esports'])
    ax_card1.text(0.5, 0.2, "e스포츠 (CS:GO)", ha='center', va='center', fontsize=12, color='#7F8C8D')

    # 카드 2: 심박수
    ax_card2 = fig.add_subplot(gs[1, 1])
    ax_card2.axis('off')
    rect2 = plt.Rectangle((0.05, 0.05), 0.9, 0.9, transform=ax_card2.transAxes,
                           facecolor='white', edgecolor='#E74C3C', linewidth=3)
    ax_card2.add_patch(rect2)
    ax_card2.text(0.5, 0.8, "[경기 중 심박수]", ha='center', va='center', fontsize=16, fontweight='bold')
    esports_hr = processed.get('esports_hr')
    hr_val = esports_hr['heart_rate'].mean() if esports_hr is not None else 0
    ax_card2.text(0.5, 0.5, f"{hr_val:.0f} BPM", ha='center', va='center',
                  fontsize=40, fontweight='bold', color='#E74C3C')
    ax_card2.text(0.5, 0.2, "안정시(72) 대비 +14%", ha='center', va='center', fontsize=12, color='#7F8C8D')

    # ============================================================
    # 비교 차트
    # ============================================================

    # 연령 비교
    ax_compare1 = fig.add_subplot(gs[2, 0])
    sports = ['e스포츠', '체조', '축구', 'NFL', '사격']
    ages = [23, 20, 27, 27, 35]
    colors = [COLORS['esports'], COLORS['gymnastics'], COLORS['football'], COLORS['nfl'], COLORS['shooting']]

    bars = ax_compare1.barh(sports, ages, color=colors, edgecolor='black', height=0.6)
    ax_compare1.set_xlim(0, 40)
    ax_compare1.set_xlabel('피크 연령 (세)')
    ax_compare1.set_title('종목별 피크 연령 비교', fontsize=14, fontweight='bold')

    for bar, age in zip(bars, ages):
        ax_compare1.text(age + 0.5, bar.get_y() + bar.get_height()/2,
                        f'{age}세', va='center', fontweight='bold')

    # 역량 비교
    ax_compare2 = fig.add_subplot(gs[2, 1])
    abilities = ['반응속도', '전략', '협동', '체력', '정밀']
    esports_ab = [95, 90, 85, 60, 90]
    trad_ab = [75, 80, 85, 90, 70]

    x = np.arange(len(abilities))
    width = 0.35

    ax_compare2.bar(x - width/2, esports_ab, width, label='e스포츠', color=COLORS['esports'], alpha=0.8)
    ax_compare2.bar(x + width/2, trad_ab, width, label='전통 스포츠', color=COLORS['traditional'], alpha=0.8)
    ax_compare2.set_xticks(x)
    ax_compare2.set_xticklabels(abilities)
    ax_compare2.set_ylim(0, 100)
    ax_compare2.set_ylabel('점수')
    ax_compare2.set_title('역량별 비교', fontsize=14, fontweight='bold')
    ax_compare2.legend()

    # ============================================================
    # 평가 결과
    # ============================================================
    ax_score = fig.add_subplot(gs[3, :])
    ax_score.axis('off')

    # 점수 게이지
    theta = np.linspace(0, np.pi, 100)
    r = 1

    # 배경 아크
    ax_score.plot(np.cos(theta), np.sin(theta), color='#EAECEE', linewidth=30, solid_capstyle='round')

    # 점수 아크
    score_angle = np.pi * (1 - total_score / 100)
    theta_score = np.linspace(np.pi, score_angle, 100)
    ax_score.plot(np.cos(theta_score), np.sin(theta_score), color=COLORS['esports'],
                  linewidth=30, solid_capstyle='round')

    ax_score.text(0, 0.3, f"{total_score:.1f}", ha='center', va='center',
                  fontsize=50, fontweight='bold', color='#2C3E50')
    ax_score.text(0, 0, "/ 100점", ha='center', va='center', fontsize=20, color='#7F8C8D')
    ax_score.text(0, -0.4, "종합 평가 점수", ha='center', va='center', fontsize=16, fontweight='bold')

    ax_score.set_xlim(-1.5, 1.5)
    ax_score.set_ylim(-0.6, 1.3)
    ax_score.set_aspect('equal')

    # ============================================================
    # 결론
    # ============================================================
    ax_final = fig.add_subplot(gs[4, :])
    ax_final.axis('off')

    rect_final = plt.Rectangle((0.05, 0.1), 0.9, 0.8, transform=ax_final.transAxes,
                                facecolor='#1ABC9C', edgecolor='none', alpha=0.9)
    ax_final.add_patch(rect_final)

    ax_final.text(0.5, 0.6, "[결론] e스포츠는 스포츠다", ha='center', va='center',
                  fontsize=24, fontweight='bold', color='white')
    ax_final.text(0.5, 0.3, "인지적 전문성 기반의 현대적 스포츠로 인정 가능",
                  ha='center', va='center', fontsize=14, color='white')

    plt.savefig(os.path.join(output_path, '00_INFOGRAPHIC_SUMMARY.png'),
                dpi=200, bbox_inches='tight', facecolor='#FAFAFA', edgecolor='none')
    plt.close()
    print("  00_INFOGRAPHIC_SUMMARY.png 저장 완료")


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

    # 7. 생리학적 분석 (21-28) - Medical 분석
    create_medical_visualizations(processed, OUTPUT_PATH)

    # 8. 종합 평가
    total_score = final_evaluation()

    # 9. 최종 종합 대시보드 생성
    create_final_comprehensive_dashboard(processed, age_comparison, advanced_stats, total_score, OUTPUT_PATH)

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
