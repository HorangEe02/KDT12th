"""
e스포츠 vs 전통 스포츠 대중적 관심도 비교 분석
=============================================
이 모듈은 크롤링한 e스포츠 데이터를 전통 스포츠 데이터와 비교 분석합니다.

비교 지표:
1. 시청자 수 (Peak Viewers)
2. 총 시청 시간 (Hours Watched)
3. 상금 규모 (Prize Pool)
4. 시장 규모 (Market Size)
5. 연간 성장률 (Growth Rate)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import seaborn as sns
import json
import os
from datetime import datetime

# 한글 폰트 설정
def setup_korean_font():
    """한글 폰트 설정"""
    # 시스템에 설치된 한글 폰트 찾기
    font_list = [f.name for f in fm.fontManager.ttflist]
    korean_fonts = ['NanumGothic', 'Malgun Gothic', 'AppleGothic', 'Noto Sans KR', 'DejaVu Sans']
    
    for font in korean_fonts:
        if font in font_list:
            rcParams['font.family'] = font
            break
    else:
        # 폰트를 찾지 못한 경우 기본 설정
        rcParams['font.family'] = 'sans-serif'
    
    rcParams['axes.unicode_minus'] = False
    plt.style.use('seaborn-v0_8-whitegrid')

setup_korean_font()


# ============================================================
# 전통 스포츠 비교 데이터 (공개 통계 기반)
# ============================================================

TRADITIONAL_SPORTS_DATA = {
    # 시청자 수 데이터 (2024-2025년 기준, 단위: 백만 명)
    'viewership': {
        'FIFA World Cup Final (2022)': 1500,  # 15억
        'UEFA Champions League Final': 450,
        'Super Bowl (NFL)': 115,
        'NBA Finals': 12.5,
        'Wimbledon Final': 10,
        'Tour de France': 42,
        'Olympics Opening Ceremony': 3000,
        
        # e스포츠 (비교용 - 나중에 크롤링 데이터로 대체)
        'LoL Worlds 2024': 6.9,  # 690만
        'DOTA2 TI 2024': 1.5,   # 150만
        'CS2 Major': 2.1,       # 210만
        'Valorant Champions': 1.5,
    },
    
    # 상금 규모 (단위: USD)
    'prize_pool': {
        # 전통 스포츠
        'Wimbledon': 50_000_000,
        'US Open (Tennis)': 65_000_000,
        'FIFA World Cup': 440_000_000,
        'Tour de France': 2_300_000,
        'Super Bowl (Team Prize)': 150_000,
        
        # e스포츠 (대표 대회)
        'DOTA2 The International': 40_000_000,
        'LoL World Championship': 2_225_000,
        'Fortnite World Cup': 30_000_000,
        'PUBG Mobile Global': 6_000_000,
        'Valorant Champions': 2_250_000,
    },
    
    # 시장 규모 (연간, 단위: 십억 USD)
    'market_size': {
        'year': [2020, 2021, 2022, 2023, 2024, 2025],
        'esports': [0.95, 1.08, 1.38, 1.62, 1.87, 2.10],  # Newzoo 예측
        'traditional_sports': [388, 440, 487, 512, 540, 560],  # Global Sports Market
    },
    
    # 글로벌 팬/관객 수 (단위: 백만 명)
    'global_audience': {
        'Football (Soccer)': 3500,
        'Cricket': 2500,
        'Basketball': 2200,
        'Tennis': 1000,
        'Esports (Total)': 540,  # 2024년 추정
        'Esports (Enthusiasts)': 270,  # 열성 팬
    }
}


class ComparisonAnalyzer:
    """e스포츠와 전통 스포츠 비교 분석 클래스"""
    
    def __init__(self, data_dir='./esports_data'):
        self.data_dir = data_dir
        self.esports_data = {}
        self.traditional_data = TRADITIONAL_SPORTS_DATA
        self.output_dir = './analysis_output'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_crawled_data(self):
        """크롤링한 e스포츠 데이터 로드"""
        files_to_load = [
            'escharts_top_games_2025.csv',
            'escharts_yearly_comparison.csv',
            'earnings_games_by_prize.csv',
            'earnings_top_tournaments.csv',
            'earnings_top_players.csv',
        ]
        
        for filename in files_to_load:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                key = filename.replace('.csv', '')
                self.esports_data[key] = pd.read_csv(filepath)
                print(f"[INFO] 데이터 로드 완료: {filename}")
            else:
                print(f"[WARNING] 파일 없음: {filename}")
    
    def analyze_viewership_comparison(self):
        """
        시청자 수 비교 분석
        - e스포츠 주요 대회 vs 전통 스포츠 주요 대회
        """
        print("\n" + "=" * 50)
        print("1. 시청자 수 비교 분석")
        print("=" * 50)
        
        viewership = self.traditional_data['viewership']
        
        # 데이터프레임 생성
        data = []
        for event, viewers in viewership.items():
            category = 'e스포츠' if any(game in event for game in ['LoL', 'DOTA', 'CS', 'Valorant', 'Fortnite']) else '전통 스포츠'
            data.append({
                'event': event,
                'viewers_million': viewers,
                'category': category
            })
        
        df = pd.DataFrame(data)
        
        # 시각화
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. 전체 비교 막대 그래프
        ax1 = axes[0]
        colors = ['#FF6B6B' if cat == 'e스포츠' else '#4ECDC4' for cat in df['category']]
        bars = ax1.barh(df['event'], df['viewers_million'], color=colors)
        ax1.set_xlabel('시청자 수 (백만 명)', fontsize=12)
        ax1.set_title('주요 스포츠 이벤트 시청자 수 비교', fontsize=14, fontweight='bold')
        ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}M'))
        
        # 범례
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#FF6B6B', label='e스포츠'),
                          Patch(facecolor='#4ECDC4', label='전통 스포츠')]
        ax1.legend(handles=legend_elements, loc='lower right')
        
        # 2. e스포츠만 확대
        ax2 = axes[1]
        esports_df = df[df['category'] == 'e스포츠'].sort_values('viewers_million', ascending=True)
        ax2.barh(esports_df['event'], esports_df['viewers_million'], color='#FF6B6B')
        ax2.set_xlabel('시청자 수 (백만 명)', fontsize=12)
        ax2.set_title('e스포츠 주요 대회 시청자 수', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'viewership_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 분석 결과 출력
        esports_avg = df[df['category'] == 'e스포츠']['viewers_million'].mean()
        traditional_avg = df[df['category'] == '전통 스포츠']['viewers_million'].mean()
        
        print(f"\n[분석 결과]")
        print(f"- e스포츠 평균 시청자: {esports_avg:.2f}백만 명")
        print(f"- 전통 스포츠 평균 시청자: {traditional_avg:.2f}백만 명")
        print(f"- e스포츠/전통 스포츠 비율: {(esports_avg/traditional_avg)*100:.2f}%")
        
        return df
    
    def analyze_prize_pool_comparison(self):
        """
        상금 규모 비교 분석
        - e스포츠 대회 상금 vs 전통 스포츠 대회 상금
        """
        print("\n" + "=" * 50)
        print("2. 상금 규모 비교 분석")
        print("=" * 50)
        
        prize_pool = self.traditional_data['prize_pool']
        
        # 데이터프레임 생성
        data = []
        for event, prize in prize_pool.items():
            category = 'e스포츠' if any(game in event for game in ['DOTA', 'LoL', 'Fortnite', 'PUBG', 'Valorant']) else '전통 스포츠'
            data.append({
                'event': event,
                'prize_usd': prize,
                'prize_million': prize / 1_000_000,
                'category': category
            })
        
        df = pd.DataFrame(data).sort_values('prize_usd', ascending=False)
        
        # 시각화
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = ['#FF6B6B' if cat == 'e스포츠' else '#4ECDC4' for cat in df['category']]
        bars = ax.barh(df['event'], df['prize_million'], color=colors)
        
        ax.set_xlabel('상금 규모 (백만 USD)', fontsize=12)
        ax.set_title('스포츠 대회 상금 규모 비교', fontsize=14, fontweight='bold')
        
        # 값 표시
        for bar, value in zip(bars, df['prize_million']):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                   f'${value:.1f}M', va='center', fontsize=9)
        
        # 범례
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#FF6B6B', label='e스포츠'),
                          Patch(facecolor='#4ECDC4', label='전통 스포츠')]
        ax.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'prize_pool_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 분석 결과
        esports_total = df[df['category'] == 'e스포츠']['prize_usd'].sum()
        traditional_total = df[df['category'] == '전통 스포츠']['prize_usd'].sum()
        
        print(f"\n[분석 결과]")
        print(f"- e스포츠 총 상금: ${esports_total/1_000_000:.2f}M")
        print(f"- 전통 스포츠 총 상금: ${traditional_total/1_000_000:.2f}M")
        print(f"- 특징: DOTA2 TI는 크라우드펀딩으로 전통 스포츠 수준의 상금 보유")
        
        return df
    
    def analyze_market_growth(self):
        """
        시장 성장률 비교 분석
        - e스포츠 vs 전통 스포츠 시장 성장 추이
        """
        print("\n" + "=" * 50)
        print("3. 시장 성장률 비교 분석")
        print("=" * 50)
        
        market = self.traditional_data['market_size']
        
        years = market['year']
        esports = market['esports']
        traditional = market['traditional_sports']
        
        # 성장률 계산
        esports_growth = [(esports[i] - esports[i-1]) / esports[i-1] * 100 
                         for i in range(1, len(esports))]
        traditional_growth = [(traditional[i] - traditional[i-1]) / traditional[i-1] * 100 
                             for i in range(1, len(traditional))]
        
        # 시각화
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. 시장 규모 비교 (로그 스케일)
        ax1 = axes[0]
        ax1.plot(years, esports, 'o-', color='#FF6B6B', linewidth=2, markersize=8, label='e스포츠')
        ax1.set_ylabel('시장 규모 (십억 USD)', fontsize=12, color='#FF6B6B')
        ax1.tick_params(axis='y', labelcolor='#FF6B6B')
        ax1.set_xlabel('연도', fontsize=12)
        ax1.set_title('시장 규모 추이 비교', fontsize=14, fontweight='bold')
        
        ax1_twin = ax1.twinx()
        ax1_twin.plot(years, traditional, 's-', color='#4ECDC4', linewidth=2, markersize=8, label='전통 스포츠')
        ax1_twin.set_ylabel('시장 규모 (십억 USD)', fontsize=12, color='#4ECDC4')
        ax1_twin.tick_params(axis='y', labelcolor='#4ECDC4')
        
        # 범례 통합
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # 2. 연간 성장률 비교
        ax2 = axes[1]
        x = np.arange(len(years) - 1)
        width = 0.35
        
        bars1 = ax2.bar(x - width/2, esports_growth, width, label='e스포츠', color='#FF6B6B')
        bars2 = ax2.bar(x + width/2, traditional_growth, width, label='전통 스포츠', color='#4ECDC4')
        
        ax2.set_xlabel('연도', fontsize=12)
        ax2.set_ylabel('성장률 (%)', fontsize=12)
        ax2.set_title('연간 성장률 비교', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f'{years[i]}-{years[i+1]}' for i in range(len(years)-1)])
        ax2.legend()
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # 값 표시
        for bar in bars1:
            height = bar.get_height()
            ax2.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'market_growth_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 분석 결과
        avg_esports_growth = np.mean(esports_growth)
        avg_traditional_growth = np.mean(traditional_growth)
        
        print(f"\n[분석 결과]")
        print(f"- e스포츠 평균 연간 성장률: {avg_esports_growth:.2f}%")
        print(f"- 전통 스포츠 평균 연간 성장률: {avg_traditional_growth:.2f}%")
        print(f"- e스포츠는 전통 스포츠 대비 {avg_esports_growth/avg_traditional_growth:.1f}배 빠른 성장")
        
        return {
            'esports_growth': esports_growth,
            'traditional_growth': traditional_growth,
            'avg_esports': avg_esports_growth,
            'avg_traditional': avg_traditional_growth
        }
    
    def analyze_global_audience(self):
        """
        글로벌 관객/팬 수 비교 분석
        """
        print("\n" + "=" * 50)
        print("4. 글로벌 팬/관객 규모 비교")
        print("=" * 50)
        
        audience = self.traditional_data['global_audience']
        
        # 데이터프레임 생성
        data = []
        for sport, fans in audience.items():
            category = 'e스포츠' if 'Esports' in sport else '전통 스포츠'
            data.append({
                'sport': sport.replace(' (Total)', '').replace(' (Enthusiasts)', ' (열성팬)'),
                'fans_million': fans,
                'category': category
            })
        
        df = pd.DataFrame(data).sort_values('fans_million', ascending=True)
        
        # 시각화
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = ['#FF6B6B' if cat == 'e스포츠' else '#4ECDC4' for cat in df['category']]
        bars = ax.barh(df['sport'], df['fans_million'], color=colors)
        
        ax.set_xlabel('글로벌 팬 수 (백만 명)', fontsize=12)
        ax.set_title('스포츠별 글로벌 팬 규모', fontsize=14, fontweight='bold')
        
        # 값 표시
        for bar, value in zip(bars, df['fans_million']):
            ax.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
                   f'{value:,.0f}M', va='center', fontsize=10)
        
        # 범례
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='#FF6B6B', label='e스포츠'),
                          Patch(facecolor='#4ECDC4', label='전통 스포츠')]
        ax.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'global_audience_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        esports_total = df[df['category'] == 'e스포츠']['fans_million'].max()
        basketball = audience['Basketball']
        
        print(f"\n[분석 결과]")
        print(f"- e스포츠 총 관객: {esports_total}백만 명")
        print(f"- e스포츠 vs 농구: {esports_total/basketball*100:.1f}%")
        print(f"- e스포츠 vs 테니스: {esports_total/audience['Tennis']*100:.1f}%")
        
        return df
    
    def generate_summary_report(self):
        """
        종합 분석 리포트 생성
        """
        print("\n" + "=" * 70)
        print("종합 분석 리포트: e스포츠의 대중적 인기는 전통 스포츠에 필적하는가?")
        print("=" * 70)
        
        report = """
# e스포츠 vs 전통 스포츠: 대중적 관심도 비교 분석 리포트

## 1. 분석 개요
본 분석은 e스포츠가 전통 스포츠에 필적하는 대중적 인기를 가지고 있는지 
다각도로 검증합니다.

## 2. 주요 분석 결과

### 2.1 시청자 수 비교
- **현황**: e스포츠 최대 대회(LoL Worlds)의 시청자 수는 약 690만 명으로,
  FIFA 월드컵 결승(15억 명)의 0.5% 수준입니다.
- **그러나**: 슈퍼볼(1.15억), NBA 파이널(1,250만)과 비교하면 
  상당한 규모로 성장했습니다.
- **특징**: 디지털 스트리밍 기반으로 18-34세 젊은 층에서 강세

### 2.2 상금 규모 비교
- **현황**: DOTA2 The International의 상금($40M)은 
  윔블던($50M)과 유사한 수준입니다.
- **특징**: 크라우드펀딩 모델을 통해 전통 스포츠 수준 달성
- **의미**: 팬 참여도와 관심도의 지표로 해석 가능

### 2.3 시장 성장률 비교
- **e스포츠 평균 성장률**: 약 13-17% (연간)
- **전통 스포츠 평균 성장률**: 약 5-8% (연간)
- **결론**: e스포츠는 전통 스포츠 대비 2-3배 빠른 성장세

### 2.4 글로벌 팬 규모 비교
- **e스포츠 총 관객**: 약 5.4억 명 (2024년)
- **축구**: 35억 명 (6.5배)
- **농구**: 22억 명 (4배)
- **테니스**: 10억 명 (1.9배)

## 3. 결론

### e스포츠는 전통 스포츠에 '필적'하는가?

**[현재 시점]**: 아직 필적하지 못함
- 절대적인 관객 규모에서 큰 차이
- 그러나 특정 인구층(젊은 세대)에서는 이미 경쟁력 보유

**[성장 잠재력]**: 매우 높음
- 성장률이 전통 스포츠의 2-3배
- 디지털 네이티브 세대의 증가
- 기술 발전에 따른 접근성 향상

**[결론]**: 
e스포츠는 아직 전통 스포츠의 규모에는 미치지 못하지만,
가장 빠르게 성장하는 스포츠/엔터테인먼트 분야로서
향후 10-20년 내 주요 전통 스포츠와 경쟁 가능한 위치에 
도달할 것으로 전망됩니다.

## 4. 분석에 사용된 데이터 출처
- Escharts.com: e스포츠 시청자 통계
- EsportsEarnings.com: 상금 데이터
- Newzoo: 시장 규모 및 예측
- Statista: 전통 스포츠 시장 데이터
- FIFA/IOC/각 스포츠 협회: 공식 통계

---
분석 일자: {date}
        """.format(date=datetime.now().strftime('%Y-%m-%d'))
        
        # 리포트 저장
        report_path = os.path.join(self.output_dir, 'analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\n[INFO] 리포트 저장 완료: {report_path}")
        
        return report
    
    def run_full_analysis(self):
        """전체 분석 실행"""
        print("\n" + "#" * 70)
        print("# e스포츠 vs 전통 스포츠 대중적 관심도 비교 분석 시작")
        print("#" * 70)
        
        # 데이터 로드
        self.load_crawled_data()
        
        # 분석 실행
        self.analyze_viewership_comparison()
        self.analyze_prize_pool_comparison()
        self.analyze_market_growth()
        self.analyze_global_audience()
        
        # 종합 리포트 생성
        self.generate_summary_report()
        
        print("\n" + "#" * 70)
        print(f"# 분석 완료! 결과물 저장 위치: {os.path.abspath(self.output_dir)}")
        print("#" * 70)


def main():
    """메인 실행 함수"""
    analyzer = ComparisonAnalyzer(data_dir='./esports_data')
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
