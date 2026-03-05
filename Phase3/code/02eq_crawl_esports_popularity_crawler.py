"""
e스포츠 대중적 관심도 분석을 위한 크롤링 모듈
=====================================
주제: "e스포츠도 스포츠인가?" - 대중적 관심도 비교 분석
소주제: e스포츠의 대중적 인기는 전통 스포츠에 필적하는가?

크롤링 대상 사이트:
1. escharts.com - e스포츠 시청자 통계
2. esportsearnings.com - e스포츠 상금 데이터
3. newzoo.com - 시장 규모 및 리포트

분석에 활용할 수 있는 데이터:
- 시청자 수 (Peak Viewers, Hours Watched)
- 상금 규모
- 시장 성장률
- 게임/대회별 인기도
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
from datetime import datetime
import os


class EsportsChartsCrawler:
    """
    Escharts.com 크롤러
    - 주요 대회 시청자 수
    - 게임별 인기도 순위
    - 연도별 시청자 통계
    """
    
    def __init__(self):
        self.base_url = "https://escharts.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_top_games(self, year=2025):
        """
        게임별 시청자 순위 크롤링
        - Peak Viewers (최고 동시 시청자)
        - Hours Watched (총 시청 시간)
        """
        url = f"{self.base_url}/top-games?year={year}"
        print(f"[INFO] 게임 순위 크롤링 중: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            games_data = []
            
            # 테이블에서 게임 정보 추출
            table_rows = soup.select('table tbody tr, .game-row, [class*="game"]')
            
            for row in table_rows:
                try:
                    game_info = {}
                    
                    # 게임 이름
                    name_elem = row.select_one('a[href*="/games/"], .game-name, td:first-child')
                    if name_elem:
                        game_info['game_name'] = name_elem.get_text(strip=True)
                    
                    # 시청자 수 데이터 (텍스트에서 숫자 추출)
                    text_content = row.get_text()
                    
                    # Peak Viewers 패턴 매칭 (예: 4.8M, 1.1M, 420.4K)
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
                        
                except Exception as e:
                    continue
            
            return pd.DataFrame(games_data) if games_data else None
            
        except Exception as e:
            print(f"[ERROR] 게임 순위 크롤링 실패: {e}")
            return None
    
    def get_tournament_stats(self, game='lol', limit=50):
        """
        특정 게임의 대회별 시청자 통계 크롤링
        
        Parameters:
        - game: 게임 코드 (lol, csgo, valorant, dota2, mobile-legends 등)
        - limit: 가져올 대회 수
        """
        url = f"{self.base_url}/tournaments/{game}"
        print(f"[INFO] {game} 대회 통계 크롤링 중: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tournaments_data = []
            
            # 대회 목록 추출
            tournament_items = soup.select('table tbody tr, .tournament-item, [class*="tournament"]')
            
            for item in tournament_items[:limit]:
                try:
                    tournament = {}
                    
                    # 대회명
                    name_elem = item.select_one('a[href*="/tournaments/"], .tournament-name')
                    if name_elem:
                        tournament['tournament_name'] = name_elem.get_text(strip=True)
                        tournament['url'] = name_elem.get('href', '')
                    
                    # 날짜
                    date_elem = item.select_one('.date, td:nth-child(2), [class*="date"]')
                    if date_elem:
                        tournament['date'] = date_elem.get_text(strip=True)
                    
                    # 시청자 수
                    viewers_elem = item.select_one('.viewers, td:nth-child(3), [class*="viewer"]')
                    if viewers_elem:
                        tournament['peak_viewers'] = self._parse_viewer_count(viewers_elem.get_text())
                    
                    if tournament.get('tournament_name'):
                        tournaments_data.append(tournament)
                        
                except Exception as e:
                    continue
            
            return pd.DataFrame(tournaments_data) if tournaments_data else None
            
        except Exception as e:
            print(f"[ERROR] 대회 통계 크롤링 실패: {e}")
            return None
    
    def get_tournament_details(self, tournament_url):
        """
        개별 대회의 상세 시청자 통계 크롤링
        
        Returns:
        - peak_viewers: 최고 동시 시청자
        - hours_watched: 총 시청 시간
        - avg_viewers: 평균 시청자
        - airtime: 방송 시간
        """
        full_url = f"{self.base_url}{tournament_url}" if not tournament_url.startswith('http') else tournament_url
        print(f"[INFO] 대회 상세 정보 크롤링: {full_url}")
        
        try:
            response = self.session.get(full_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {'url': full_url}
            
            # 대회명
            title = soup.select_one('h1, .tournament-title')
            if title:
                details['tournament_name'] = title.get_text(strip=True)
            
            # 통계 카드에서 데이터 추출
            stat_cards = soup.select('.stat-card, .stats-item, [class*="stat"]')
            
            for card in stat_cards:
                label = card.select_one('.label, .stat-label, dt')
                value = card.select_one('.value, .stat-value, dd')
                
                if label and value:
                    label_text = label.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)
                    
                    if 'peak' in label_text:
                        details['peak_viewers'] = self._parse_viewer_count(value_text)
                    elif 'hours' in label_text or 'watched' in label_text:
                        details['hours_watched'] = value_text
                    elif 'average' in label_text or 'avg' in label_text:
                        details['avg_viewers'] = self._parse_viewer_count(value_text)
                    elif 'airtime' in label_text:
                        details['airtime'] = value_text
            
            return details
            
        except Exception as e:
            print(f"[ERROR] 대회 상세 정보 크롤링 실패: {e}")
            return None
    
    def get_yearly_comparison(self, years=[2020, 2021, 2022, 2023, 2024, 2025]):
        """
        연도별 e스포츠 시청자 트렌드 크롤링
        - 연도별 성장 추이 분석에 활용
        """
        yearly_data = []
        
        for year in years:
            print(f"[INFO] {year}년 데이터 크롤링 중...")
            
            url = f"{self.base_url}/top-games?year={year}"
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 해당 연도의 총 시청자 수 등 집계 데이터
                year_stats = {
                    'year': year,
                    'total_peak_viewers': 0,
                    'top_games_count': 0
                }
                
                # 페이지에서 숫자 추출
                text_content = soup.get_text()
                peak_matches = re.findall(r'(\d+\.?\d*)\s*([MKmk])', text_content)
                
                for match in peak_matches[:10]:  # 상위 10개 게임
                    value = float(match[0])
                    unit = match[1].upper()
                    if unit == 'M':
                        year_stats['total_peak_viewers'] += int(value * 1_000_000)
                    elif unit == 'K':
                        year_stats['total_peak_viewers'] += int(value * 1_000)
                    year_stats['top_games_count'] += 1
                
                yearly_data.append(year_stats)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"[WARNING] {year}년 데이터 크롤링 실패: {e}")
                continue
        
        return pd.DataFrame(yearly_data) if yearly_data else None
    
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
    """
    EsportsEarnings.com 크롤러
    - 상금 규모 데이터 (전통 스포츠와 비교 가능)
    - 게임별/대회별/선수별 상금 통계
    """
    
    def __init__(self):
        self.base_url = "https://www.esportsearnings.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_games_by_prize(self):
        """
        게임별 총 상금 순위 크롤링
        - 전통 스포츠 상금과 비교 분석에 활용
        """
        url = f"{self.base_url}/games"
        print(f"[INFO] 게임별 상금 순위 크롤링: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            games_data = []
            
            # 테이블에서 게임별 상금 정보 추출
            table = soup.select_one('table, .games-table')
            if table:
                rows = table.select('tr')[1:]  # 헤더 제외
                
                for row in rows:
                    cols = row.select('td')
                    if len(cols) >= 3:
                        game = {
                            'rank': len(games_data) + 1,
                            'game_name': cols[0].get_text(strip=True) if cols[0] else '',
                            'total_prize': self._parse_prize(cols[1].get_text(strip=True)) if cols[1] else 0,
                            'tournament_count': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                            'player_count': cols[3].get_text(strip=True) if len(cols) > 3 else ''
                        }
                        games_data.append(game)
            
            return pd.DataFrame(games_data) if games_data else None
            
        except Exception as e:
            print(f"[ERROR] 게임별 상금 크롤링 실패: {e}")
            return None
    
    def get_top_tournaments(self, limit=100):
        """
        상금 규모 기준 상위 대회 크롤링
        - 대회별 상금 규모
        - 참가 선수 수
        """
        url = f"{self.base_url}/tournaments"
        print(f"[INFO] 상위 대회 상금 크롤링: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tournaments_data = []
            
            # 대회 목록 추출
            table = soup.select_one('table')
            if table:
                rows = table.select('tr')[1:]
                
                for row in rows[:limit]:
                    cols = row.select('td')
                    if len(cols) >= 2:
                        tournament = {
                            'rank': len(tournaments_data) + 1,
                            'tournament_name': cols[0].get_text(strip=True),
                            'prize_pool': self._parse_prize(cols[1].get_text(strip=True)) if cols[1] else 0,
                            'game': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                            'date': cols[3].get_text(strip=True) if len(cols) > 3 else ''
                        }
                        tournaments_data.append(tournament)
            
            return pd.DataFrame(tournaments_data) if tournaments_data else None
            
        except Exception as e:
            print(f"[ERROR] 대회 상금 크롤링 실패: {e}")
            return None
    
    def get_top_players(self, limit=100):
        """
        상금 수입 기준 상위 선수 크롤링
        - 전통 스포츠 선수 수입과 비교 가능
        """
        url = f"{self.base_url}/players"
        print(f"[INFO] 선수별 상금 크롤링: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            players_data = []
            
            table = soup.select_one('table')
            if table:
                rows = table.select('tr')[1:]
                
                for row in rows[:limit]:
                    cols = row.select('td')
                    if len(cols) >= 2:
                        player = {
                            'rank': len(players_data) + 1,
                            'player_name': cols[0].get_text(strip=True),
                            'total_earnings': self._parse_prize(cols[1].get_text(strip=True)) if cols[1] else 0,
                            'game': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                            'country': cols[3].get_text(strip=True) if len(cols) > 3 else ''
                        }
                        players_data.append(player)
            
            return pd.DataFrame(players_data) if players_data else None
            
        except Exception as e:
            print(f"[ERROR] 선수 상금 크롤링 실패: {e}")
            return None
    
    def get_yearly_prize_stats(self):
        """
        연도별 총 상금 규모 크롤링
        - e스포츠 시장 성장 추이 분석
        """
        url = f"{self.base_url}/history"
        print(f"[INFO] 연도별 상금 통계 크롤링: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            yearly_data = []
            
            # 연도별 데이터 추출
            year_sections = soup.select('.year-stats, [class*="year"], table tr')
            
            for section in year_sections:
                text = section.get_text()
                
                # 연도 패턴 매칭
                year_match = re.search(r'20[12]\d', text)
                prize_match = re.search(r'\$[\d,]+\.?\d*\s*[MKB]?', text)
                
                if year_match and prize_match:
                    yearly_data.append({
                        'year': int(year_match.group()),
                        'total_prize': self._parse_prize(prize_match.group())
                    })
            
            return pd.DataFrame(yearly_data) if yearly_data else None
            
        except Exception as e:
            print(f"[ERROR] 연도별 상금 크롤링 실패: {e}")
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


class NewzooCrawler:
    """
    Newzoo.com 크롤러
    - e스포츠 시장 규모 리포트
    - 글로벌 관객 수 통계
    - 시장 예측 데이터
    """
    
    def __init__(self):
        self.base_url = "https://newzoo.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_resources_list(self, resource_type='all', tag='esports'):
        """
        Newzoo 리소스 목록 크롤링
        - 리포트, 인포그래픽, 기사 등
        """
        url = f"{self.base_url}/resources?type={resource_type}&tag={tag}"
        print(f"[INFO] Newzoo 리소스 크롤링: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            resources = []
            
            # 리소스 카드 추출
            cards = soup.select('.resource-card, .card, article, [class*="resource"]')
            
            for card in cards:
                resource = {}
                
                # 제목
                title = card.select_one('h2, h3, .title, a')
                if title:
                    resource['title'] = title.get_text(strip=True)
                    if title.get('href'):
                        resource['url'] = title.get('href')
                
                # 설명
                desc = card.select_one('p, .description, .excerpt')
                if desc:
                    resource['description'] = desc.get_text(strip=True)
                
                # 날짜
                date = card.select_one('.date, time, [class*="date"]')
                if date:
                    resource['date'] = date.get_text(strip=True)
                
                # 태그
                tags = card.select('.tag, .category')
                if tags:
                    resource['tags'] = [t.get_text(strip=True) for t in tags]
                
                if resource.get('title'):
                    resources.append(resource)
            
            return pd.DataFrame(resources) if resources else None
            
        except Exception as e:
            print(f"[ERROR] Newzoo 리소스 크롤링 실패: {e}")
            return None
    
    def get_market_data(self):
        """
        e스포츠 시장 데이터 크롤링
        - 시장 규모
        - 관객 수
        - 성장률
        
        참고: Newzoo의 상세 데이터는 유료이므로,
        공개된 요약 정보만 크롤링합니다.
        """
        urls = [
            f"{self.base_url}/insights/",
            f"{self.base_url}/resources?tag=esports",
        ]
        
        market_data = []
        
        for url in urls:
            print(f"[INFO] 시장 데이터 크롤링: {url}")
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 숫자 데이터 추출 (시장 규모, 관객 수 등)
                text_content = soup.get_text()
                
                # 시장 규모 패턴 (예: $1.8 billion, €2.1B)
                market_size = re.findall(r'[\$€]\s*(\d+\.?\d*)\s*([BMK]illion|[BMK])', text_content, re.IGNORECASE)
                
                # 관객 수 패턴 (예: 500 million viewers)
                audience = re.findall(r'(\d+\.?\d*)\s*([BMK]illion)?\s*(viewers|audience|fans)', text_content, re.IGNORECASE)
                
                # 성장률 패턴 (예: 15% growth, +20%)
                growth = re.findall(r'[+-]?\s*(\d+\.?\d*)\s*%\s*(growth|increase|CAGR)', text_content, re.IGNORECASE)
                
                if market_size or audience or growth:
                    market_data.append({
                        'source_url': url,
                        'market_size_mentions': market_size[:5],
                        'audience_mentions': audience[:5],
                        'growth_mentions': growth[:5]
                    })
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[WARNING] 시장 데이터 크롤링 실패: {e}")
                continue
        
        return market_data if market_data else None


def save_data(data, filename, output_dir='./data'):
    """데이터를 CSV 파일로 저장"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    if isinstance(data, pd.DataFrame):
        data.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] 데이터 저장 완료: {filepath}")
    elif isinstance(data, list):
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] 데이터 저장 완료: {filepath}")
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] 데이터 저장 완료: {filepath}")


def main():
    """메인 크롤링 실행 함수"""
    
    print("=" * 60)
    print("e스포츠 대중적 관심도 분석 - 데이터 크롤링")
    print("주제: e스포츠의 대중적 인기는 전통 스포츠에 필적하는가?")
    print("=" * 60)
    
    output_dir = './esports_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Escharts.com 크롤링
    print("\n[1/3] Escharts.com 크롤링 시작...")
    escharts = EsportsChartsCrawler()
    
    # 게임별 시청자 순위
    games_df = escharts.get_top_games(year=2025)
    if games_df is not None:
        save_data(games_df, 'escharts_top_games_2025.csv', output_dir)
    
    # 주요 게임별 대회 통계
    for game in ['lol', 'csgo', 'valorant', 'dota2']:
        tournaments_df = escharts.get_tournament_stats(game=game, limit=30)
        if tournaments_df is not None:
            save_data(tournaments_df, f'escharts_{game}_tournaments.csv', output_dir)
        time.sleep(2)
    
    # 연도별 비교
    yearly_df = escharts.get_yearly_comparison(years=[2020, 2021, 2022, 2023, 2024, 2025])
    if yearly_df is not None:
        save_data(yearly_df, 'escharts_yearly_comparison.csv', output_dir)
    
    # 2. EsportsEarnings.com 크롤링
    print("\n[2/3] EsportsEarnings.com 크롤링 시작...")
    earnings = EsportsEarningsCrawler()
    
    # 게임별 상금 순위
    games_prize_df = earnings.get_games_by_prize()
    if games_prize_df is not None:
        save_data(games_prize_df, 'earnings_games_by_prize.csv', output_dir)
    
    # 상위 대회 상금
    tournaments_prize_df = earnings.get_top_tournaments(limit=100)
    if tournaments_prize_df is not None:
        save_data(tournaments_prize_df, 'earnings_top_tournaments.csv', output_dir)
    
    # 상위 선수 상금
    players_df = earnings.get_top_players(limit=100)
    if players_df is not None:
        save_data(players_df, 'earnings_top_players.csv', output_dir)
    
    # 3. Newzoo 크롤링
    print("\n[3/3] Newzoo.com 크롤링 시작...")
    newzoo = NewzooCrawler()
    
    # 리소스 목록
    resources_df = newzoo.get_resources_list(tag='esports')
    if resources_df is not None:
        save_data(resources_df, 'newzoo_esports_resources.csv', output_dir)
    
    # 시장 데이터
    market_data = newzoo.get_market_data()
    if market_data:
        with open(os.path.join(output_dir, 'newzoo_market_data.json'), 'w', encoding='utf-8') as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] 시장 데이터 저장 완료: {output_dir}/newzoo_market_data.json")
    
    print("\n" + "=" * 60)
    print("크롤링 완료!")
    print(f"데이터 저장 위치: {os.path.abspath(output_dir)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
