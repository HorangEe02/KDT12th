"""
Selenium 기반 동적 크롤링 모듈
==============================
JavaScript로 동적 로드되는 웹사이트를 위한 크롤링 코드

주의: 이 코드를 실행하려면 Chrome과 ChromeDriver가 설치되어 있어야 합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
import os


class SeleniumCrawler:
    """Selenium 기반 동적 웹 크롤러"""
    
    def __init__(self, headless=True):
        """
        Parameters:
        - headless: True면 브라우저 창을 표시하지 않음
        """
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = None
    
    def start_driver(self):
        """웹드라이버 시작"""
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            print("[INFO] Chrome WebDriver 시작됨")
        except Exception as e:
            print(f"[ERROR] WebDriver 시작 실패: {e}")
            print("[TIP] ChromeDriver를 수동으로 설치하세요")
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


class EschartsSeleniumCrawler(SeleniumCrawler):
    """
    Escharts.com Selenium 크롤러
    - 동적으로 로드되는 테이블 데이터 수집
    - 상세 대회 통계 수집
    """
    
    def __init__(self, headless=True):
        super().__init__(headless)
        self.base_url = "https://escharts.com"
    
    def get_tournament_detailed_stats(self, tournament_slug):
        """
        대회 상세 페이지에서 모든 통계 수집
        
        Parameters:
        - tournament_slug: 대회 URL 슬러그 (예: 'lol/2024-world-championship-worlds-2024')
        
        Returns:
        - dict: 상세 통계 데이터
        """
        url = f"{self.base_url}/tournaments/{tournament_slug}"
        print(f"[INFO] 대회 상세 통계 크롤링: {url}")
        
        self.driver.get(url)
        time.sleep(3)  # JavaScript 로드 대기
        
        stats = {'url': url}
        
        try:
            # 페이지 소스 파싱
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 대회명
            title = soup.select_one('h1')
            if title:
                stats['tournament_name'] = title.get_text(strip=True)
            
            # 통계 카드들
            stat_items = soup.select('[class*="stat"], .info-card, .data-item')
            
            for item in stat_items:
                text = item.get_text(strip=True)
                
                # Peak Viewers
                if 'Peak' in text or 'peak' in text:
                    match = re.search(r'(\d+\.?\d*)\s*([MKmk])?', text)
                    if match:
                        stats['peak_viewers'] = self._parse_number(match.group())
                
                # Hours Watched
                if 'Hours' in text or 'watched' in text.lower():
                    match = re.search(r'(\d+\.?\d*)\s*([MKmk])?', text)
                    if match:
                        stats['hours_watched'] = match.group()
                
                # Average Viewers
                if 'Average' in text or 'Avg' in text:
                    match = re.search(r'(\d+\.?\d*)\s*([MKmk])?', text)
                    if match:
                        stats['avg_viewers'] = self._parse_number(match.group())
            
            # 플랫폼별 시청자 데이터 (테이블에서 추출)
            tables = soup.select('table')
            for table in tables:
                headers = [th.get_text(strip=True) for th in table.select('th')]
                if any('Platform' in h or 'platform' in h for h in headers):
                    rows = table.select('tr')[1:]
                    platform_data = []
                    for row in rows:
                        cols = row.select('td')
                        if len(cols) >= 2:
                            platform_data.append({
                                'platform': cols[0].get_text(strip=True),
                                'viewers': cols[1].get_text(strip=True)
                            })
                    stats['platform_breakdown'] = platform_data
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] 상세 통계 수집 실패: {e}")
            return stats
    
    def get_all_tournaments_for_game(self, game='lol', year=2024, max_pages=5):
        """
        특정 게임의 모든 대회 목록 크롤링 (페이지네이션 포함)
        
        Parameters:
        - game: 게임 코드
        - year: 연도
        - max_pages: 최대 페이지 수
        """
        all_tournaments = []
        
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/tournaments/{game}?year={year}&page={page}"
            print(f"[INFO] 페이지 {page} 크롤링: {url}")
            
            self.driver.get(url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 대회 행 추출
            rows = soup.select('table tbody tr, .tournament-row, [class*="tournament"]')
            
            if not rows:
                print(f"[INFO] 페이지 {page}에 더 이상 데이터 없음")
                break
            
            for row in rows:
                try:
                    tournament = {}
                    
                    # 대회명과 링크
                    link = row.select_one('a[href*="/tournaments/"]')
                    if link:
                        tournament['name'] = link.get_text(strip=True)
                        tournament['url'] = link.get('href', '')
                    
                    # 날짜
                    date_elem = row.select_one('.date, td:nth-of-type(2)')
                    if date_elem:
                        tournament['date'] = date_elem.get_text(strip=True)
                    
                    # 시청자 수
                    text = row.get_text()
                    viewers_match = re.search(r'(\d+\.?\d*)\s*([MK])', text)
                    if viewers_match:
                        tournament['peak_viewers'] = self._parse_number(viewers_match.group())
                    
                    if tournament.get('name'):
                        all_tournaments.append(tournament)
                        
                except Exception as e:
                    continue
            
            time.sleep(1)  # Rate limiting
        
        return pd.DataFrame(all_tournaments)
    
    def get_top_matches(self, game='lol', limit=50):
        """
        역대 최고 시청자 매치 목록 크롤링
        """
        url = f"{self.base_url}/matches?game={game}&order=peak"
        print(f"[INFO] 최고 시청자 매치 크롤링: {url}")
        
        self.driver.get(url)
        time.sleep(3)
        
        matches = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        rows = soup.select('table tbody tr, .match-row')[:limit]
        
        for row in rows:
            try:
                match = {}
                
                # 팀 정보
                teams = row.select('.team-name, a[href*="/teams/"]')
                if len(teams) >= 2:
                    match['team1'] = teams[0].get_text(strip=True)
                    match['team2'] = teams[1].get_text(strip=True)
                
                # 대회 정보
                tournament = row.select_one('a[href*="/tournaments/"]')
                if tournament:
                    match['tournament'] = tournament.get_text(strip=True)
                
                # 시청자 수
                text = row.get_text()
                viewers_match = re.search(r'(\d+\.?\d*)\s*([MK])', text)
                if viewers_match:
                    match['peak_viewers'] = self._parse_number(viewers_match.group())
                
                if match.get('team1'):
                    matches.append(match)
                    
            except Exception as e:
                continue
        
        return pd.DataFrame(matches)
    
    def _parse_number(self, text):
        """숫자 문자열 파싱"""
        if not text:
            return 0
        
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
        
        return 0


class EsportsEarningsSeleniumCrawler(SeleniumCrawler):
    """
    EsportsEarnings.com Selenium 크롤러
    """
    
    def __init__(self, headless=True):
        super().__init__(headless)
        self.base_url = "https://www.esportsearnings.com"
    
    def get_games_ranking(self, sort_by='prize'):
        """
        게임별 순위 크롤링
        
        Parameters:
        - sort_by: 정렬 기준 ('prize', 'players', 'tournaments')
        """
        url = f"{self.base_url}/games/browse"
        print(f"[INFO] 게임 순위 크롤링: {url}")
        
        self.driver.get(url)
        time.sleep(3)
        
        games = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # 테이블 찾기
        table = soup.select_one('table.detail_list, table')
        
        if table:
            rows = table.select('tr')[1:]  # 헤더 제외
            
            for idx, row in enumerate(rows, 1):
                try:
                    cols = row.select('td')
                    if len(cols) >= 4:
                        game = {
                            'rank': idx,
                            'game_name': cols[0].get_text(strip=True),
                            'total_prize': self._parse_prize(cols[1].get_text(strip=True)),
                            'players': cols[2].get_text(strip=True),
                            'tournaments': cols[3].get_text(strip=True)
                        }
                        games.append(game)
                except Exception as e:
                    continue
        
        return pd.DataFrame(games)
    
    def get_tournament_history(self, game_id=None, year=2024):
        """
        특정 게임의 대회 역사 크롤링
        """
        if game_id:
            url = f"{self.base_url}/games/{game_id}/tournaments"
        else:
            url = f"{self.base_url}/tournaments"
        
        print(f"[INFO] 대회 역사 크롤링: {url}")
        
        self.driver.get(url)
        time.sleep(3)
        
        tournaments = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        rows = soup.select('table tr')[1:]
        
        for row in rows:
            try:
                cols = row.select('td')
                if len(cols) >= 3:
                    tournament = {
                        'name': cols[0].get_text(strip=True),
                        'prize': self._parse_prize(cols[1].get_text(strip=True)),
                        'date': cols[2].get_text(strip=True) if len(cols) > 2 else ''
                    }
                    tournaments.append(tournament)
            except:
                continue
        
        return pd.DataFrame(tournaments)
    
    def _parse_prize(self, text):
        """상금 문자열 파싱"""
        if not text:
            return 0
        
        text = text.replace(',', '').replace('$', '').strip()
        match = re.search(r'(\d+\.?\d*)', text)
        
        if match:
            return float(match.group(1))
        return 0


def run_selenium_crawling():
    """Selenium 크롤링 실행"""
    
    output_dir = './esports_data_selenium'
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("Selenium 기반 e스포츠 데이터 크롤링")
    print("=" * 60)
    
    # Escharts 크롤링
    print("\n[1/2] Escharts.com 크롤링...")
    escharts = EschartsSeleniumCrawler(headless=True)
    
    try:
        escharts.start_driver()
        
        # LoL 대회 데이터
        lol_tournaments = escharts.get_all_tournaments_for_game('lol', 2024, max_pages=3)
        if not lol_tournaments.empty:
            lol_tournaments.to_csv(f'{output_dir}/lol_tournaments_selenium.csv', index=False)
            print(f"[SUCCESS] LoL 대회 데이터 저장: {len(lol_tournaments)}개")
        
        # CS2 대회 데이터
        cs2_tournaments = escharts.get_all_tournaments_for_game('csgo', 2024, max_pages=3)
        if not cs2_tournaments.empty:
            cs2_tournaments.to_csv(f'{output_dir}/cs2_tournaments_selenium.csv', index=False)
            print(f"[SUCCESS] CS2 대회 데이터 저장: {len(cs2_tournaments)}개")
        
        # 최고 시청자 매치
        top_matches = escharts.get_top_matches('lol', limit=50)
        if not top_matches.empty:
            top_matches.to_csv(f'{output_dir}/top_matches_selenium.csv', index=False)
            print(f"[SUCCESS] 최고 시청자 매치 저장: {len(top_matches)}개")
        
    except Exception as e:
        print(f"[ERROR] Escharts 크롤링 실패: {e}")
    finally:
        escharts.stop_driver()
    
    # EsportsEarnings 크롤링
    print("\n[2/2] EsportsEarnings.com 크롤링...")
    earnings = EsportsEarningsSeleniumCrawler(headless=True)
    
    try:
        earnings.start_driver()
        
        # 게임 순위
        games_ranking = earnings.get_games_ranking()
        if not games_ranking.empty:
            games_ranking.to_csv(f'{output_dir}/games_ranking_selenium.csv', index=False)
            print(f"[SUCCESS] 게임 순위 저장: {len(games_ranking)}개")
        
    except Exception as e:
        print(f"[ERROR] EsportsEarnings 크롤링 실패: {e}")
    finally:
        earnings.stop_driver()
    
    print("\n" + "=" * 60)
    print(f"크롤링 완료! 저장 위치: {os.path.abspath(output_dir)}")
    print("=" * 60)


if __name__ == "__main__":
    run_selenium_crawling()
