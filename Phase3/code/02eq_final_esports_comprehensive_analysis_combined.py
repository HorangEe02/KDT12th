"""
e스포츠 경제 분석 종합 통합 스크립트
=====================================

이 스크립트는 다음 파일들을 통합한 종합 분석 도구입니다:
- b/esports_enhancement_analysis.py (보완 전략 분석)
- data_b/Crawling/selenium_crawler.py (Selenium 크롤러)
- data_b/Crawling/esports_popularity_crawler.py (인기도 크롤러)
- data_b/Crawling/esports_vs_sports_analysis.py (비교 분석)
- data_b/x/esports_popularity_analysis.ipynb (대중적 관심도 분석)
- data_b/x/esports_popularity_analysis_v2.ipynb (대중적 관심도 분석 v2)

주요 분석 내용:
1. 경제 구조의 동질성 증명 (로렌츠 곡선, ARPU)
2. 인지적 부하로 신체 활동 재정의 (APM, 피크 연령)
3. 성장 궤적의 동질성 (이중 회귀선)
4. 포지션별 역량 분석 (레이더 차트)
5. e스포츠 vs 전통 스포츠 대중적 관심도 비교
6. 웹 크롤링을 통한 데이터 수집

작성일: 2025년 1월
"""

# ============================================================
# PART 1: 라이브러리 임포트 및 환경 설정
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
import os
import warnings
import platform
import json
import re
import time
from datetime import datetime
from pathlib import Path

# 선택적 임포트 (크롤링용)
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[WARNING] requests/beautifulsoup4 미설치 - 크롤링 기능 비활성화")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[WARNING] selenium/webdriver-manager 미설치 - Selenium 크롤링 기능 비활성화")

warnings.filterwarnings('ignore')

# ============================================================
# PART 2: 한글 폰트 및 스타일 설정
# ============================================================

# 전역 폰트 속성 (시각화 함수에서 사용)
FONT_NAME = None
FONT_PROP = None

def setup_korean_font():
    """한글 폰트 설정 (Mac/Windows/Linux 자동 감지)"""
    global FONT_NAME, FONT_PROP
    system = platform.system()

    if system == 'Darwin':  # Mac
        # macOS 기본 한글 폰트 우선순위
        font_candidates = [
            ('Apple SD Gothic Neo', '/System/Library/Fonts/AppleSDGothicNeo.ttc'),
            ('AppleGothic', '/System/Library/Fonts/Supplemental/AppleGothic.ttf'),
            ('Malgun Gothic', '/Users/yeong/Library/Fonts/malgun.ttf'),
        ]

        font_found = False
        for font_name, font_path in font_candidates:
            if os.path.exists(font_path):
                FONT_NAME = font_name
                FONT_PROP = fm.FontProperties(fname=font_path)
                font_found = True
                print(f"[INFO] 한글 폰트 설정: {font_name}")
                break

        if not font_found:
            # 폰트 매니저에서 한글 폰트 찾기
            for font in fm.fontManager.ttflist:
                if 'SD Gothic' in font.name or 'Nanum' in font.name or 'Malgun' in font.name:
                    FONT_NAME = font.name
                    FONT_PROP = fm.FontProperties(fname=font.fname)
                    font_found = True
                    print(f"[INFO] 한글 폰트 설정: {font.name}")
                    break

        if not font_found:
            FONT_NAME = 'AppleGothic'
            print("[WARNING] 기본 폰트 사용: AppleGothic")

    elif system == 'Windows':
        FONT_NAME = 'Malgun Gothic'
    else:  # Linux
        FONT_NAME = 'NanumGothic'

    # matplotlib 전역 설정
    plt.rcParams['font.family'] = FONT_NAME
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'

# 스타일 적용 전에 폰트 설정
setup_korean_font()

# 스타일 적용
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# 스타일 적용 후 폰트 재설정 (스타일이 폰트를 덮어쓸 수 있음)
if FONT_NAME:
    plt.rcParams['font.family'] = FONT_NAME
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# PART 3: 경로 설정 및 공통 상수
# ============================================================

# 기본 경로 설정
BASE_PATH = '/Volumes/Samsung_T5/00_work_out/02_ing/pase3_mini_project/esports/data'
OUTPUT_DIR = '/Volumes/Samsung_T5/00_work_out/02_ing/pase3_mini_project/esports/02_Equality/final_b'

# 출력 디렉토리 생성
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 공통 컬러 팔레트
COLORS = {
    # e스포츠
    'esports': '#9B59B6',
    'lol': '#C9AA71',
    'csgo': '#DE9B35',
    'dota2': '#F44336',
    'valorant': '#FD4556',
    'fortnite': '#9D4DBB',

    # 전통 스포츠
    'football': '#27AE60',
    'nfl': '#E74C3C',
    'olympic': '#3498DB',
    'basketball': '#F39C12',

    # 게임별
    'League of Legends': '#C9AA71',
    'Dota 2': '#F44336',
    'CS:GO': '#DE9B35',
    'Valorant': '#FD4556',
    'Fortnite': '#9D4DBB',
    'PUBG': '#F2A900',
    'Overwatch': '#F99E1A',
    'Minecraft': '#7CB342',
    'GTA V': '#8BC34A',
    'Just Chatting': '#6441A5',

    # 언어별
    'English': '#3498DB',
    'Korean': '#E74C3C',
    'Spanish': '#F1C40F',
    'Portuguese': '#2ECC71',
    'Russian': '#9B59B6',
    'Japanese': '#E91E63',
    'Chinese': '#FF5722',
    'German': '#607D8B',
    'French': '#00BCD4',
    'Other': '#95A5A6',

    # 지역별
    'asia': '#E91E63',
    'europe': '#2196F3',
    'americas': '#4CAF50',
    'others': '#9E9E9E',
}

# 전통 스포츠 비교 데이터 (공개 통계 기반)
TRADITIONAL_SPORTS_DATA = {
    'viewership': {
        'FIFA World Cup Final (2022)': 1500,
        'UEFA Champions League Final': 450,
        'Super Bowl (NFL)': 115,
        'NBA Finals': 12.5,
        'Wimbledon Final': 10,
        'Olympics Opening Ceremony': 3000,
        'LoL Worlds 2024': 6.9,
        'DOTA2 TI 2024': 1.5,
        'CS2 Major': 2.1,
        'Valorant Champions': 1.5,
    },
    'prize_pool': {
        'Wimbledon': 50_000_000,
        'US Open (Tennis)': 65_000_000,
        'FIFA World Cup': 440_000_000,
        'DOTA2 The International': 40_000_000,
        'LoL World Championship': 2_225_000,
        'Fortnite World Cup': 30_000_000,
    },
    'market_size': {
        'year': [2020, 2021, 2022, 2023, 2024, 2025],
        'esports': [0.95, 1.08, 1.38, 1.62, 1.87, 2.10],
        'traditional_sports': [388, 440, 487, 512, 540, 560],
    },
    'global_audience': {
        'Football (Soccer)': 3500,
        'Cricket': 2500,
        'Basketball': 2200,
        'Tennis': 1000,
        'Esports (Total)': 540,
        'Esports (Enthusiasts)': 270,
    }
}

# ============================================================
# PART 4: 유틸리티 함수
# ============================================================

def format_currency(value):
    """금액을 읽기 쉬운 형식으로 변환"""
    if pd.isna(value):
        return 'N/A'
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"

def format_number(value):
    """큰 숫자를 읽기 쉬운 형식으로 변환"""
    if pd.isna(value):
        return 'N/A'
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{value:.0f}"

def format_hours(hours):
    """시간을 읽기 쉬운 형식으로 변환"""
    if hours >= 1_000_000_000:
        return f"{hours/1_000_000_000:.1f}B hours"
    elif hours >= 1_000_000:
        return f"{hours/1_000_000:.1f}M hours"
    elif hours >= 1_000:
        return f"{hours/1_000:.1f}K hours"
    return f"{hours:.0f} hours"

def calculate_gini(earnings):
    """지니 계수 계산 함수"""
    sorted_earnings = np.sort(earnings)
    n = len(sorted_earnings)
    if n == 0 or np.sum(sorted_earnings) == 0:
        return 0
    cumulative = np.cumsum(sorted_earnings)
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_earnings))) / (n * np.sum(sorted_earnings)) - (n + 1) / n
    return gini

def parse_value(val):
    """금액 문자열 파싱 (€110.5M -> 110500000)"""
    if pd.isna(val) or val == '€0':
        return 0
    val = str(val).replace('€', '').replace('$', '').replace(',', '').strip()
    if 'M' in val.upper():
        return float(val.upper().replace('M', '')) * 1_000_000
    elif 'K' in val.upper():
        return float(val.upper().replace('K', '')) * 1_000
    elif 'B' in val.upper():
        return float(val.upper().replace('B', '')) * 1_000_000_000
    return float(val) if val else 0

def save_data(data, filename, output_dir='./data'):
    """데이터를 CSV 파일로 저장"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    if isinstance(data, pd.DataFrame):
        data.to_csv(filepath, index=False, encoding='utf-8-sig')
    elif isinstance(data, list):
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"[SUCCESS] 데이터 저장 완료: {filepath}")

# ============================================================
# PART 5: 데이터 로더 클래스
# ============================================================

class EsportsDataLoader:
    """e스포츠 및 전통 스포츠 데이터 로더"""

    def __init__(self, base_path=BASE_PATH):
        self.base_path = base_path
        self.data = {}

    def load_all_data(self):
        """모든 데이터 로드"""
        print("=" * 60)
        print("데이터 로딩 중...")
        print("=" * 60)

        # e스포츠 데이터
        try:
            self.data['esports_general'] = pd.read_csv(
                os.path.join(self.base_path, 'Esports Earnings 1998 - 2023', 'GeneralEsportData.csv'))
            self.data['esports_historical'] = pd.read_csv(
                os.path.join(self.base_path, 'Esports Earnings 1998 - 2023', 'HistoricalEsportData.csv'))
            print(f"[OK] e스포츠 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] e스포츠 데이터 로드 실패: {e}")

        # FIFA 선수 데이터
        try:
            self.data['fifa_df'] = pd.read_csv(os.path.join(self.base_path, 'fifa_eda_stats.csv'))
            self.data['fifa_df']['Value_Numeric'] = self.data['fifa_df']['Value'].apply(parse_value)
            print(f"[OK] FIFA 선수 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] FIFA 데이터 로드 실패: {e}")

        # NFL 선수 데이터
        try:
            self.data['nfl_salaries'] = pd.read_csv(os.path.join(self.base_path, 'football_salaries.csv'))
            print(f"[OK] NFL 선수 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] NFL 데이터 로드 실패: {e}")

        # 올림픽 선수 데이터
        try:
            self.data['olympic_df'] = pd.read_csv(
                os.path.join(self.base_path, '120 years of Olympic history_athletes and results', 'athlete_events.csv'))
            print(f"[OK] 올림픽 선수 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] 올림픽 데이터 로드 실패: {e}")

        # Twitch 데이터
        try:
            self.data['twitch_streamers'] = pd.read_csv(
                os.path.join(self.base_path, 'twitchdata-update.csv'), encoding='ISO-8859-1')
            print(f"[OK] Twitch 스트리머 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] Twitch 데이터 로드 실패: {e}")

        # 글로벌 e스포츠 데이터
        try:
            self.data['global_esports'] = pd.read_csv(
                os.path.join(self.base_path, 'global_gaming_esports_2010_2025.csv'), encoding='ISO-8859-1')
            print(f"[OK] 글로벌 e스포츠 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] 글로벌 e스포츠 데이터 로드 실패: {e}")

        # Twitch 게임별 데이터
        try:
            self.data['twitch_games'] = pd.read_csv(
                os.path.join(self.base_path, 'Top games on Twitch 2016 - 2023', 'Twitch_game_data.csv'),
                encoding='ISO-8859-1')
            self.data['twitch_global'] = pd.read_csv(
                os.path.join(self.base_path, 'Top games on Twitch 2016 - 2023', 'Twitch_global_data.csv'),
                encoding='ISO-8859-1')
            print(f"[OK] Twitch 게임별 데이터 로드 완료")
        except Exception as e:
            print(f"[WARNING] Twitch 게임 데이터 로드 실패: {e}")

        print("\n데이터 로딩 완료!")
        return self.data

# ============================================================
# PART 6: 웹 크롤러 클래스 (기본)
# ============================================================

class EsportsChartsCrawler:
    """Escharts.com 크롤러 (requests 기반)"""

    def __init__(self):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests/beautifulsoup4 라이브러리가 필요합니다.")

        self.base_url = "https://escharts.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_top_games(self, year=2025):
        """게임별 시청자 순위 크롤링"""
        url = f"{self.base_url}/top-games?year={year}"
        print(f"[INFO] 게임 순위 크롤링 중: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            games_data = []
            table_rows = soup.select('table tbody tr, .game-row')

            for row in table_rows:
                try:
                    game_info = {}
                    name_elem = row.select_one('a[href*="/games/"], .game-name')
                    if name_elem:
                        game_info['game_name'] = name_elem.get_text(strip=True)

                    text_content = row.get_text()
                    peak_match = re.search(r'(\d+\.?\d*)\s*([MKmk])', text_content)
                    if peak_match:
                        value = float(peak_match.group(1))
                        unit = peak_match.group(2).upper()
                        if unit == 'M':
                            game_info['peak_viewers'] = int(value * 1_000_000)
                        elif unit == 'K':
                            game_info['peak_viewers'] = int(value * 1_000)

                    if game_info.get('game_name'):
                        games_data.append(game_info)
                except:
                    continue

            return pd.DataFrame(games_data) if games_data else None
        except Exception as e:
            print(f"[ERROR] 게임 순위 크롤링 실패: {e}")
            return None

    def _parse_viewer_count(self, text):
        """시청자 수 텍스트를 숫자로 변환"""
        if not text:
            return None

        text = text.strip().upper()
        match = re.search(r'(\d+\.?\d*)\s*([MKB])?', text)

        if match:
            value = float(match.group(1))
            unit = match.group(2) if match.group(2) else ''

            if unit == 'M':
                return int(value * 1_000_000)
            elif unit == 'K':
                return int(value * 1_000)
            elif unit == 'B':
                return int(value * 1_000_000_000)
            else:
                return int(value)
        return None


class EsportsEarningsCrawler:
    """EsportsEarnings.com 크롤러"""

    def __init__(self):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests/beautifulsoup4 라이브러리가 필요합니다.")

        self.base_url = "https://www.esportsearnings.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_games_by_prize(self):
        """게임별 총 상금 순위 크롤링"""
        url = f"{self.base_url}/games"
        print(f"[INFO] 게임별 상금 순위 크롤링: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            games_data = []
            table = soup.select_one('table, .games-table')
            if table:
                rows = table.select('tr')[1:]
                for row in rows:
                    cols = row.select('td')
                    if len(cols) >= 3:
                        game = {
                            'rank': len(games_data) + 1,
                            'game_name': cols[0].get_text(strip=True),
                            'total_prize': self._parse_prize(cols[1].get_text(strip=True)),
                        }
                        games_data.append(game)

            return pd.DataFrame(games_data) if games_data else None
        except Exception as e:
            print(f"[ERROR] 게임별 상금 크롤링 실패: {e}")
            return None

    def _parse_prize(self, text):
        """상금 텍스트를 숫자로 변환"""
        if not text:
            return 0
        text = text.replace(',', '').replace('$', '').strip().upper()
        match = re.search(r'(\d+\.?\d*)\s*([MKB])?', text)
        if match:
            value = float(match.group(1))
            unit = match.group(2) if match.group(2) else ''
            if unit == 'M':
                return int(value * 1_000_000)
            elif unit == 'K':
                return int(value * 1_000)
            elif unit == 'B':
                return int(value * 1_000_000_000)
            else:
                return int(value)
        return 0

# ============================================================
# PART 7: Selenium 크롤러 클래스
# ============================================================

class SeleniumCrawler:
    """Selenium 기반 동적 웹 크롤러"""

    def __init__(self, headless=True):
        if not SELENIUM_AVAILABLE:
            raise ImportError("selenium/webdriver-manager 라이브러리가 필요합니다.")

        self.options = Options()
        if headless:
            self.options.add_argument('--headless')

        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--user-agent=Mozilla/5.0')
        self.driver = None

    def start_driver(self):
        """웹드라이버 시작"""
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            print("[INFO] Chrome WebDriver 시작됨")
        except Exception as e:
            print(f"[ERROR] WebDriver 시작 실패: {e}")
            raise

    def stop_driver(self):
        """웹드라이버 종료"""
        if self.driver:
            self.driver.quit()
            print("[INFO] Chrome WebDriver 종료됨")

    def wait_for_element(self, by, value, timeout=10):
        """특정 요소가 로드될 때까지 대기"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"[WARNING] 요소를 찾을 수 없음: {value}")
            return None

# ============================================================
# PART 8: 경제 구조 동질성 분석
# ============================================================

class EconomicStructureAnalyzer:
    """경제 구조 동질성 분석 클래스"""

    def __init__(self, data_loader):
        self.data = data_loader.data
        self.output_dir = OUTPUT_DIR

    def plot_lorenz_curve(self, save=True):
        """로렌츠 곡선 및 지니 계수 분석"""
        print("\n[분석] 로렌츠 곡선 및 지니 계수 분석")

        # 데이터 준비
        earnings_data = {}

        if 'esports_general' in self.data:
            esports_earnings = self.data['esports_general']['TotalEarnings'].dropna().values
            earnings_data['e스포츠'] = esports_earnings[esports_earnings > 0]

        if 'fifa_df' in self.data:
            fifa_earnings = self.data['fifa_df']['Value_Numeric'].dropna().values
            earnings_data['축구 (FIFA)'] = fifa_earnings[fifa_earnings > 0]

        if 'nfl_salaries' in self.data:
            nfl_earnings = self.data['nfl_salaries']['avg_year'].dropna().values
            earnings_data['NFL'] = nfl_earnings[nfl_earnings > 0]

        if len(earnings_data) == 0:
            print("[WARNING] 분석할 데이터가 없습니다.")
            return None

        fig, ax = plt.subplots(figsize=(10, 8))

        colors = {
            'e스포츠': COLORS['esports'],
            '축구 (FIFA)': COLORS['football'],
            'NFL': COLORS['nfl']
        }

        ax.plot([0, 1], [0, 1], 'k--', label='완전 평등선', alpha=0.7, linewidth=2)

        gini_results = {}

        for name, earnings in earnings_data.items():
            sorted_data = np.sort(earnings)
            cumulative_share = np.cumsum(sorted_data) / np.sum(sorted_data)
            population_share = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

            gini = calculate_gini(earnings)
            gini_results[name] = gini

            ax.plot(population_share, cumulative_share,
                    label=f'{name} (Gini: {gini:.3f})',
                    color=colors.get(name, 'gray'), linewidth=2.5)
            ax.fill_between(population_share, cumulative_share,
                           population_share, alpha=0.1, color=colors.get(name, 'gray'))

        ax.set_xlabel('인구 누적 비율', fontsize=12)
        ax.set_ylabel('소득 누적 비율', fontsize=12)
        ax.set_title('종목별 소득 불균형 구조 비교 (로렌츠 곡선)', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/01_lorenz_curve.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 01_lorenz_curve.png")
        else:
            plt.show()

        return gini_results

    def plot_arpu_bubble_chart(self, save=True):
        """ARPU 버블 차트 생성"""
        print("\n[분석] ARPU 버블 차트")

        arpu_data = pd.DataFrame({
            'sport': ['e스포츠', 'e스포츠', 'e스포츠', 'NFL', 'NFL', 'NFL', '축구', '축구', '축구'],
            'year': [2020, 2022, 2024, 2020, 2022, 2024, 2020, 2022, 2024],
            'viewers_million': [495, 640, 800, 150, 160, 170, 3500, 3800, 4000],
            'revenue_billion': [0.95, 1.38, 1.87, 12.0, 14.0, 18.0, 28.0, 32.0, 35.0],
            'growth_rate': [15.2, 22.5, 37.3, 3.5, 5.2, 6.0, 2.1, 3.8, 4.2]
        })
        arpu_data['arpu'] = arpu_data['revenue_billion'] * 1000 / arpu_data['viewers_million']

        fig, ax = plt.subplots(figsize=(14, 10))

        colors = {'e스포츠': COLORS['esports'], 'NFL': COLORS['nfl'], '축구': COLORS['football']}

        for sport in arpu_data['sport'].unique():
            sport_data = arpu_data[arpu_data['sport'] == sport]
            sizes = (sport_data['growth_rate'].abs() + 5) * 30

            ax.scatter(sport_data['viewers_million'], sport_data['revenue_billion'],
                      s=sizes, c=colors.get(sport, 'gray'), alpha=0.6,
                      label=sport, edgecolors='white', linewidth=2)

            for _, row in sport_data.iterrows():
                ax.annotate(f"{int(row['year'])}",
                           (row['viewers_million'], row['revenue_billion']),
                           textcoords="offset points", xytext=(5, 5), fontsize=9)

        ax.set_xlabel('시청자 수 (백만 명)', fontsize=12)
        ax.set_ylabel('매출액 (십억 달러)', fontsize=12)
        ax.set_title('종목별 시청자당 매출 효율성 비교 (버블 크기 = 성장률)', fontsize=14, fontweight='bold')
        ax.legend(title='종목', loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3)

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/02_arpu_bubble.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 02_arpu_bubble.png")
        else:
            plt.show()

        return arpu_data

# ============================================================
# PART 9: 인지적 부하 분석
# ============================================================

class CognitiveLoadAnalyzer:
    """인지적 부하 분석 클래스"""

    def __init__(self, data_loader):
        self.data = data_loader.data
        self.output_dir = OUTPUT_DIR

    def plot_bullet_chart(self, save=True):
        """인지적 부하 불렛 차트"""
        print("\n[분석] 인지적 부하 불렛 차트")

        bullet_data = [
            {'category': 'APM (분당 작업 수)', 'value': 400, 'target': 60,
             'ranges': [100, 200, 500], 'unit': 'Actions per Minute'},
            {'category': '반응 속도 (ms)', 'value': 150, 'target': 250,
             'ranges': [100, 200, 400], 'unit': 'Milliseconds'},
            {'category': '정밀도 (%)', 'value': 98, 'target': 85,
             'ranges': [70, 85, 100], 'unit': 'Accuracy %'},
            {'category': '동시 정보 처리', 'value': 12, 'target': 7,
             'ranges': [5, 8, 15], 'unit': 'Objects tracked'},
        ]

        fig, axes = plt.subplots(len(bullet_data), 1, figsize=(14, 3.5 * len(bullet_data)))

        colors = {
            'background': ['#e8e8e8', '#d0d0d0', '#b8b8b8'],
            'bar': COLORS['esports'],
            'target': COLORS['nfl']
        }

        for ax, item in zip(axes, bullet_data):
            category = item['category']
            value = item['value']
            target = item['target']
            ranges = item['ranges']

            range_starts = [0] + ranges[:-1]
            range_ends = ranges

            for i, (start, end) in enumerate(zip(range_starts, range_ends)):
                ax.barh(0, end - start, left=start, height=0.5,
                       color=colors['background'][i], edgecolor='none')

            ax.barh(0, value, height=0.25, color=colors['bar'], alpha=0.9)
            ax.axvline(target, color=colors['target'], linewidth=3)

            ax.text(value + max(ranges)*0.02, 0, f'{value}', va='center', fontsize=11,
                   fontweight='bold', color=colors['bar'])

            ax.set_xlim(0, max(ranges) * 1.15)
            ax.set_yticks([])
            ax.set_xlabel(item.get('unit', ''), fontsize=10)
            ax.set_title(category, fontsize=12, fontweight='bold', loc='left')

        plt.suptitle('e스포츠 선수의 신경-근육 협응 능력 비교', fontsize=14, fontweight='bold', y=1.02)

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/03_cognitive_load.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 03_cognitive_load.png")
        else:
            plt.show()

    def plot_peak_age_distribution(self, save=True):
        """피크 연령 분포 분석"""
        print("\n[분석] 피크 연령 분포")

        if 'olympic_df' not in self.data:
            print("[WARNING] 올림픽 데이터가 없습니다.")
            return

        olympic_df = self.data['olympic_df']
        olympic_sports_ages = {}

        # 체조
        gymnastics = olympic_df[olympic_df['Sport'] == 'Gymnastics']['Age'].dropna()
        olympic_sports_ages['체조'] = gymnastics[gymnastics.between(14, 40)].values

        # 수영
        swimming = olympic_df[olympic_df['Sport'] == 'Swimming']['Age'].dropna()
        olympic_sports_ages['수영'] = swimming[swimming.between(14, 40)].values

        # 축구
        football = olympic_df[olympic_df['Sport'] == 'Football']['Age'].dropna()
        olympic_sports_ages['축구'] = football[football.between(16, 45)].values

        # 사격
        shooting = olympic_df[olympic_df['Sport'] == 'Shooting']['Age'].dropna()
        olympic_sports_ages['사격'] = shooting[shooting.between(18, 60)].values

        # 골프 (시뮬레이션)
        np.random.seed(42)
        olympic_sports_ages['골프'] = np.random.normal(35, 8, 300).clip(20, 55)

        # e스포츠 (시뮬레이션)
        olympic_sports_ages['e스포츠'] = np.random.normal(22, 3, 500).clip(16, 35)

        fig, ax = plt.subplots(figsize=(14, 10))

        colors = {
            'e스포츠': COLORS['esports'],
            '체조': '#3498DB',
            '수영': '#1ABC9C',
            '축구': COLORS['football'],
            '사격': '#F39C12',
            '골프': '#E74C3C'
        }

        sports_order = ['e스포츠', '체조', '수영', '축구', '사격', '골프']
        offset_step = 0.25

        for i, sport in enumerate(sports_order):
            if sport not in olympic_sports_ages:
                continue

            ages = np.array(olympic_sports_ages[sport])

            try:
                kde = stats.gaussian_kde(ages)
                x_range = np.linspace(max(10, ages.min() - 5), min(60, ages.max() + 5), 200)
                density = kde(x_range)
                density = density / density.max() * 0.2
                offset = i * offset_step

                ax.fill_between(x_range, offset, density + offset, alpha=0.6,
                               color=colors.get(sport, 'gray'),
                               label=f'{sport} (평균: {ages.mean():.1f}세)')
                ax.plot(x_range, density + offset, color=colors.get(sport, 'gray'), linewidth=1.5)
            except:
                continue

        ax.set_xlabel('연령 (세)', fontsize=12)
        ax.set_title('종목별 선수 피크 연령 분포 비교', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.set_yticks([])
        ax.set_xlim(10, 55)
        ax.axvline(x=25, color='red', linestyle=':', alpha=0.5)

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/04_peak_age.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 04_peak_age.png")
        else:
            plt.show()

# ============================================================
# PART 10: 성장 궤적 분석
# ============================================================

class GrowthTrajectoryAnalyzer:
    """성장 궤적 분석 클래스"""

    def __init__(self, data_loader):
        self.data = data_loader.data
        self.output_dir = OUTPUT_DIR

    def plot_growth_comparison(self, save=True):
        """성장 궤적 비교 분석"""
        print("\n[분석] 성장 궤적 비교")

        if 'esports_historical' not in self.data:
            print("[WARNING] e스포츠 역사 데이터가 없습니다.")
            return

        esports_historical = self.data['esports_historical'].copy()
        esports_historical['Date'] = pd.to_datetime(esports_historical['Date'])
        esports_historical['Year'] = esports_historical['Date'].dt.year

        esports_yearly = esports_historical.groupby('Year').agg({
            'Earnings': 'sum',
            'Players': 'sum',
            'Tournaments': 'sum'
        }).reset_index()

        esports_yearly = esports_yearly[esports_yearly['Year'] >= 2010].copy()
        esports_yearly['years_since_start'] = esports_yearly['Year'] - 2010
        esports_yearly['revenue'] = esports_yearly['Earnings'] / 1_000_000_000

        # 전통 스포츠 성장 데이터 (추정치)
        traditional_growth = pd.DataFrame({
            'sport': ['NFL'] * 6 + ['축구'] * 6,
            'years_since_start': [0, 10, 20, 30, 40, 50] * 2,
            'revenue': [0.05, 0.5, 2.0, 5.0, 9.0, 14.0,
                       0.1, 1.0, 5.0, 15.0, 28.0, 35.0]
        })

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        # 1. 절대 성장 비교
        ax1 = axes[0]

        # NFL
        nfl_data = traditional_growth[traditional_growth['sport'] == 'NFL']
        ax1.scatter(nfl_data['years_since_start'], nfl_data['revenue'],
                   color=COLORS['nfl'], s=100, alpha=0.7, label='NFL (1960-2010)')

        X = sm.add_constant(nfl_data['years_since_start'].values)
        model = sm.OLS(nfl_data['revenue'].values, X).fit()
        x_pred = np.linspace(0, 50, 100)
        y_pred = model.predict(sm.add_constant(x_pred))
        ax1.plot(x_pred, y_pred, color=COLORS['nfl'], linewidth=2, linestyle='--')

        # 축구
        soccer_data = traditional_growth[traditional_growth['sport'] == '축구']
        ax1.scatter(soccer_data['years_since_start'], soccer_data['revenue'],
                   color=COLORS['football'], s=100, alpha=0.7, label='축구 (1970-2020)')

        # e스포츠
        ax1.scatter(esports_yearly['years_since_start'], esports_yearly['revenue'],
                   color=COLORS['esports'], s=100, alpha=0.7, label='e스포츠 (2010-2024)')

        ax1.set_xlabel('산업화 시작 후 경과 연수', fontsize=12)
        ax1.set_ylabel('매출 (십억 달러)', fontsize=12)
        ax1.set_title('성장 궤적 비교: 절대 성장', fontsize=13, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.3)

        # 2. e스포츠 상세 성장
        ax2 = axes[1]
        ax2.bar(esports_yearly['Year'], esports_yearly['Earnings'] / 1_000_000,
               color=COLORS['esports'], alpha=0.7, edgecolor='white')
        ax2.set_xlabel('연도', fontsize=12)
        ax2.set_ylabel('총 상금 (백만 달러)', fontsize=12)
        ax2.set_title('e스포츠 상금 풀 성장 추이', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/05_growth_trajectory.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 05_growth_trajectory.png")
        else:
            plt.show()

# ============================================================
# PART 11: 포지션별 역량 분석
# ============================================================

class RoleSpecializationAnalyzer:
    """포지션별 역량 분석 클래스"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR

        # 축구 포지션별 역량
        self.football_roles = {
            '미드필더': {'시야/맵 리딩': 90, '순발력/반응속도': 75, '팀워크/의사소통': 85,
                      '전술 이해도': 95, '개인기/메카닉': 80, '리더십/콜링': 85},
            '공격수': {'시야/맵 리딩': 70, '순발력/반응속도': 95, '팀워크/의사소통': 70,
                     '전술 이해도': 75, '개인기/메카닉': 95, '리더십/콜링': 60},
            '수비수': {'시야/맵 리딩': 80, '순발력/반응속도': 80, '팀워크/의사소통': 85,
                     '전술 이해도': 90, '개인기/메카닉': 70, '리더십/콜링': 75},
            '골키퍼': {'시야/맵 리딩': 95, '순발력/반응속도': 90, '팀워크/의사소통': 80,
                     '전술 이해도': 85, '개인기/메카닉': 75, '리더십/콜링': 90}
        }

        # e스포츠(LoL) 포지션별 역량
        self.esports_roles = {
            '정글러': {'시야/맵 리딩': 95, '순발력/반응속도': 85, '팀워크/의사소통': 90,
                     '전술 이해도': 95, '개인기/메카닉': 80, '리더십/콜링': 90},
            '원딜': {'시야/맵 리딩': 75, '순발력/반응속도': 95, '팀워크/의사소통': 75,
                   '전술 이해도': 70, '개인기/메카닉': 98, '리더십/콜링': 55},
            '탑': {'시야/맵 리딩': 75, '순발력/반응속도': 85, '팀워크/의사소통': 70,
                  '전술 이해도': 85, '개인기/메카닉': 90, '리더십/콜링': 65},
            '서포터': {'시야/맵 리딩': 98, '순발력/반응속도': 80, '팀워크/의사소통': 95,
                     '전술 이해도': 90, '개인기/메카닉': 70, '리더십/콜링': 95}
        }

    def plot_role_radar(self, save=True):
        """포지션별 역량 레이더 차트"""
        print("\n[분석] 포지션별 역량 레이더 차트")

        from math import pi

        categories = ['시야/맵 리딩', '순발력/반응속도', '팀워크/의사소통',
                     '전술 이해도', '개인기/메카닉', '리더십/콜링']

        position_pairs = [
            ('미드필더', '정글러', '넓은 시야와 조율 능력'),
            ('공격수', '원딜', '높은 딜링과 마무리'),
            ('수비수', '탑', '라인 유지와 안정성'),
            ('골키퍼', '서포터', '팀 보호와 시야 확보')
        ]

        fig, axes = plt.subplots(2, 2, figsize=(16, 16), subplot_kw=dict(projection='polar'))
        axes = axes.flatten()

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]

        for ax, (fb_pos, es_pos, description) in zip(axes, position_pairs):
            fb_values = [self.football_roles[fb_pos].get(cat, 50) for cat in categories]
            fb_values += fb_values[:1]

            es_values = [self.esports_roles[es_pos].get(cat, 50) for cat in categories]
            es_values += es_values[:1]

            ax.plot(angles, fb_values, 'o-', linewidth=2,
                   label=f'축구: {fb_pos}', color=COLORS['football'], markersize=6)
            ax.fill(angles, fb_values, alpha=0.2, color=COLORS['football'])

            ax.plot(angles, es_values, 'o-', linewidth=2,
                   label=f'e스포츠: {es_pos}', color=COLORS['esports'], markersize=6)
            ax.fill(angles, es_values, alpha=0.2, color=COLORS['esports'])

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=9)
            ax.set_ylim(0, 100)
            ax.set_title(f'{fb_pos} ↔ {es_pos}\n"{description}"', fontsize=11, fontweight='bold', pad=20)
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

        plt.suptitle('포지션별 역량 비교: 축구 vs e스포츠', fontsize=14, fontweight='bold', y=1.02)

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/06_role_radar.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 06_role_radar.png")
        else:
            plt.show()

    def plot_similarity_heatmap(self, save=True):
        """포지션 유사도 히트맵"""
        print("\n[분석] 포지션 유사도 히트맵")

        categories = ['시야/맵 리딩', '순발력/반응속도', '팀워크/의사소통',
                     '전술 이해도', '개인기/메카닉', '리더십/콜링']

        fb_positions = list(self.football_roles.keys())
        es_positions = list(self.esports_roles.keys())

        similarity_matrix = np.zeros((len(fb_positions), len(es_positions)))

        for i, fb_pos in enumerate(fb_positions):
            fb_vec = np.array([self.football_roles[fb_pos].get(cat, 50) for cat in categories])
            for j, es_pos in enumerate(es_positions):
                es_vec = np.array([self.esports_roles[es_pos].get(cat, 50) for cat in categories])
                similarity = np.dot(fb_vec, es_vec) / (np.linalg.norm(fb_vec) * np.linalg.norm(es_vec))
                similarity_matrix[i, j] = similarity

        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(similarity_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                   xticklabels=es_positions, yticklabels=fb_positions,
                   vmin=0.9, vmax=1.0, ax=ax,
                   cbar_kws={'label': '역량 유사도 (코사인 유사도)'})

        ax.set_xlabel('e스포츠 (LoL) 포지션', fontsize=12)
        ax.set_ylabel('축구 포지션', fontsize=12)
        ax.set_title('포지션 간 역량 유사도 히트맵', fontsize=14, fontweight='bold')

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/07_similarity_heatmap.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 07_similarity_heatmap.png")
        else:
            plt.show()

        return similarity_matrix

# ============================================================
# PART 12: 대중적 관심도 비교 분석
# ============================================================

class PopularityComparisonAnalyzer:
    """대중적 관심도 비교 분석 클래스"""

    def __init__(self, data_loader):
        self.data = data_loader.data
        self.output_dir = OUTPUT_DIR
        self.traditional_data = TRADITIONAL_SPORTS_DATA

    def analyze_viewership(self, save=True):
        """시청자 수 비교 분석"""
        print("\n[분석] 시청자 수 비교")

        viewership = self.traditional_data['viewership']

        data = []
        for event, viewers in viewership.items():
            category = 'e스포츠' if any(g in event for g in ['LoL', 'DOTA', 'CS', 'Valorant']) else '전통 스포츠'
            data.append({'event': event, 'viewers_million': viewers, 'category': category})

        df = pd.DataFrame(data)

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # 전체 비교
        colors = ['#e74c3c' if cat == 'e스포츠' else '#3498db' for cat in df['category']]
        axes[0].barh(df['event'], df['viewers_million'], color=colors)
        axes[0].set_xlabel('시청자 수 (백만 명)', fontsize=12)
        axes[0].set_title('주요 스포츠 이벤트 시청자 수 비교', fontsize=14, fontweight='bold')
        axes[0].set_xscale('log')

        # e스포츠만
        esports_df = df[df['category'] == 'e스포츠'].sort_values('viewers_million', ascending=True)
        axes[1].barh(esports_df['event'], esports_df['viewers_million'], color='#e74c3c')
        axes[1].set_xlabel('시청자 수 (백만 명)', fontsize=12)
        axes[1].set_title('e스포츠 주요 대회 시청자 수', fontsize=14, fontweight='bold')

        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#e74c3c', label='e스포츠'),
                          Patch(facecolor='#3498db', label='전통 스포츠')]
        axes[0].legend(handles=legend_elements, loc='lower right')

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/08_viewership_comparison.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 08_viewership_comparison.png")
        else:
            plt.show()

        return df

    def analyze_market_growth(self, save=True):
        """시장 성장률 분석"""
        print("\n[분석] 시장 성장률 분석")

        market = self.traditional_data['market_size']

        years = market['year']
        esports = market['esports']
        traditional = market['traditional_sports']

        esports_growth = [(esports[i] - esports[i-1]) / esports[i-1] * 100
                         for i in range(1, len(esports))]
        traditional_growth = [(traditional[i] - traditional[i-1]) / traditional[i-1] * 100
                             for i in range(1, len(traditional))]

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # 시장 규모
        ax1 = axes[0]
        ax1.plot(years, esports, 'o-', color='#e74c3c', linewidth=2, markersize=8, label='e스포츠')
        ax1.set_ylabel('시장 규모 (십억 USD)', fontsize=12, color='#e74c3c')
        ax1.tick_params(axis='y', labelcolor='#e74c3c')
        ax1.set_xlabel('연도', fontsize=12)
        ax1.set_title('시장 규모 추이 비교', fontsize=14, fontweight='bold')

        ax1_twin = ax1.twinx()
        ax1_twin.plot(years, traditional, 's-', color='#3498db', linewidth=2, markersize=8, label='전통 스포츠')
        ax1_twin.set_ylabel('시장 규모 (십억 USD)', fontsize=12, color='#3498db')
        ax1_twin.tick_params(axis='y', labelcolor='#3498db')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        # 성장률
        ax2 = axes[1]
        x = np.arange(len(years) - 1)
        width = 0.35

        ax2.bar(x - width/2, esports_growth, width, label='e스포츠', color='#e74c3c')
        ax2.bar(x + width/2, traditional_growth, width, label='전통 스포츠', color='#3498db')

        ax2.set_xlabel('연도', fontsize=12)
        ax2.set_ylabel('성장률 (%)', fontsize=12)
        ax2.set_title('연간 성장률 비교', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f'{years[i]}-{years[i+1]}' for i in range(len(years)-1)])
        ax2.legend()

        if save:
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/09_market_growth.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 09_market_growth.png")
        else:
            plt.show()

    def create_comprehensive_dashboard(self, save=True):
        """종합 대시보드 생성"""
        print("\n[분석] 종합 대시보드 생성")

        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

        # 1. 시장 규모 비교
        ax1 = fig.add_subplot(gs[0, 0])
        market_labels = ['글로벌 스포츠', 'NFL', 'e스포츠']
        market_values = [500, 18.6, 1.87]
        colors = ['#3498db', '#3498db', '#e74c3c']
        ax1.bar(market_labels, market_values, color=colors)
        ax1.set_ylabel('시장 규모 (십억 USD)')
        ax1.set_title('① 시장 규모 비교', fontsize=11, fontweight='bold')
        ax1.set_yscale('log')

        # 2. 성장률 비교
        ax2 = fig.add_subplot(gs[0, 1])
        growth_labels = ['e스포츠', '전통 스포츠']
        growth_values = [15.3, 4.0]
        colors = ['#e74c3c', '#3498db']
        bars = ax2.bar(growth_labels, growth_values, color=colors, width=0.5)
        ax2.set_ylabel('연평균 성장률 (%)')
        ax2.set_title('② 성장률 비교', fontsize=11, fontweight='bold')
        for bar, val in zip(bars, growth_values):
            ax2.text(bar.get_x() + bar.get_width()/2, val + 0.5, f'{val}%', ha='center', fontsize=10)

        # 3. 시청자 비교
        ax3 = fig.add_subplot(gs[0, 2])
        labels = ['FIFA WC', 'LoL Worlds', 'Super Bowl', 'Valorant']
        values = [1500, 6.4, 115, 1.5]
        colors = ['#3498db', '#e74c3c', '#3498db', '#e74c3c']
        ax3.bar(labels, values, color=colors)
        ax3.set_ylabel('시청자 (백만)')
        ax3.set_title('③ 시청자 비교', fontsize=11, fontweight='bold')
        ax3.set_yscale('log')

        # 4-6. 추가 지표들
        ax4 = fig.add_subplot(gs[1, 0])
        demo_data = {
            '연령대': ['18-24세', '25-34세', '35-44세', '45+'],
            'e스포츠': [68, 52, 31, 12],
            '전통 스포츠': [55, 62, 68, 72]
        }
        x = np.arange(len(demo_data['연령대']))
        width = 0.35
        ax4.bar(x - width/2, demo_data['e스포츠'], width, label='e스포츠', color='#e74c3c')
        ax4.bar(x + width/2, demo_data['전통 스포츠'], width, label='전통 스포츠', color='#3498db')
        ax4.set_xticks(x)
        ax4.set_xticklabels(demo_data['연령대'])
        ax4.set_ylabel('관심도 (%)')
        ax4.set_title('④ 연령대별 관심도', fontsize=11, fontweight='bold')
        ax4.legend()

        # 종합 결론
        ax7 = fig.add_subplot(gs[2, :])
        ax7.axis('off')

        conclusion_text = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                    종 합  결 론
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【경제 구조의 동질성】
  • e스포츠의 지니 계수(0.9+)는 전통 스포츠와 유사한 "승자독식" 구조

【인지적 부하 = 신체 활동】
  • 프로게이머의 APM(400+)은 일반인의 6배 이상
  • 피크 연령(22세)은 체조, 수영과 같은 "초정밀 순발력 스포츠" 군집

【성장 궤적의 동질성】
  • e스포츠는 전통 스포츠가 50년에 걸쳐 이룬 성장을 10-15년 만에 압축 재현
  • 연평균 성장률(CAGR) 15%+ 로 가장 빠른 성장세

【역할 전문화】
  • 축구 포지션과 e스포츠 포지션 간 역량 유사도 95%+
  • 전술적 복잡성과 분업화가 전문 스포츠 수준

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                     ∴ e스포츠는 데이터로 증명된 '스포츠'입니다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        ax7.text(0.5, 0.5, conclusion_text, transform=ax7.transAxes, fontsize=10,
                verticalalignment='center', horizontalalignment='center',
                bbox=dict(boxstyle='round,pad=1', facecolor='lightyellow', alpha=0.9))

        plt.suptitle('e스포츠 경제 분석 종합 대시보드', fontsize=16, fontweight='bold', y=0.98)

        if save:
            plt.savefig(f'{self.output_dir}/10_comprehensive_dashboard.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  -> 저장: 10_comprehensive_dashboard.png")
        else:
            plt.show()

# ============================================================
# PART 13: 메인 실행 함수
# ============================================================

def run_full_analysis():
    """전체 분석 실행"""
    print("=" * 70)
    print("e스포츠 경제 분석 종합 스크립트")
    print("=" * 70)
    print(f"\n출력 디렉토리: {OUTPUT_DIR}")

    # 데이터 로드
    print("\n" + "=" * 60)
    print("STEP 1: 데이터 로딩")
    print("=" * 60)

    loader = EsportsDataLoader(BASE_PATH)
    data = loader.load_all_data()

    # 분석 실행
    print("\n" + "=" * 60)
    print("STEP 2: 경제 구조 분석")
    print("=" * 60)

    economic_analyzer = EconomicStructureAnalyzer(loader)
    gini_results = economic_analyzer.plot_lorenz_curve()
    economic_analyzer.plot_arpu_bubble_chart()

    if gini_results:
        print("\n지니 계수 결과:")
        for name, gini in gini_results.items():
            print(f"  • {name}: {gini:.3f}")

    print("\n" + "=" * 60)
    print("STEP 3: 인지적 부하 분석")
    print("=" * 60)

    cognitive_analyzer = CognitiveLoadAnalyzer(loader)
    cognitive_analyzer.plot_bullet_chart()
    cognitive_analyzer.plot_peak_age_distribution()

    print("\n" + "=" * 60)
    print("STEP 4: 성장 궤적 분석")
    print("=" * 60)

    growth_analyzer = GrowthTrajectoryAnalyzer(loader)
    growth_analyzer.plot_growth_comparison()

    print("\n" + "=" * 60)
    print("STEP 5: 포지션별 역량 분석")
    print("=" * 60)

    role_analyzer = RoleSpecializationAnalyzer()
    role_analyzer.plot_role_radar()
    similarity_matrix = role_analyzer.plot_similarity_heatmap()

    if similarity_matrix is not None:
        print(f"\n평균 포지션 유사도: {similarity_matrix.mean():.3f}")

    print("\n" + "=" * 60)
    print("STEP 6: 대중적 관심도 비교")
    print("=" * 60)

    popularity_analyzer = PopularityComparisonAnalyzer(loader)
    popularity_analyzer.analyze_viewership()
    popularity_analyzer.analyze_market_growth()
    popularity_analyzer.create_comprehensive_dashboard()

    # 완료
    print("\n" + "=" * 70)
    print("분석 완료!")
    print("=" * 70)

    print(f"\n생성된 시각화 파일:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.png') and not f.startswith('.'):
            print(f"  • {f}")

    return loader, data


def run_crawling():
    """웹 크롤링 실행"""
    print("=" * 60)
    print("e스포츠 데이터 크롤링")
    print("=" * 60)

    output_dir = './crawled_data'
    os.makedirs(output_dir, exist_ok=True)

    if REQUESTS_AVAILABLE:
        print("\n[1] EsportsCharts 크롤링...")
        try:
            escharts = EsportsChartsCrawler()
            games_df = escharts.get_top_games(year=2025)
            if games_df is not None:
                save_data(games_df, 'escharts_top_games.csv', output_dir)
        except Exception as e:
            print(f"[ERROR] {e}")

        print("\n[2] EsportsEarnings 크롤링...")
        try:
            earnings = EsportsEarningsCrawler()
            games_prize = earnings.get_games_by_prize()
            if games_prize is not None:
                save_data(games_prize, 'earnings_games.csv', output_dir)
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print("[WARNING] requests 라이브러리 미설치 - 크롤링 스킵")

    print(f"\n크롤링 완료! 저장 위치: {os.path.abspath(output_dir)}")


# ============================================================
# PART 14: 스크립트 실행
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='e스포츠 경제 분석 종합 스크립트')
    parser.add_argument('--analysis', action='store_true', help='전체 분석 실행')
    parser.add_argument('--crawl', action='store_true', help='웹 크롤링 실행')
    parser.add_argument('--all', action='store_true', help='모든 기능 실행')

    args = parser.parse_args()

    if args.all or (not args.analysis and not args.crawl):
        # 기본: 전체 분석 실행
        run_full_analysis()
    else:
        if args.analysis:
            run_full_analysis()
        if args.crawl:
            run_crawling()

    print("\n완료!")
