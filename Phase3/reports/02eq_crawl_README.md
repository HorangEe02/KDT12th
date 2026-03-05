# e스포츠 대중적 관심도 분석 프로젝트

## 📌 프로젝트 개요

**주제**: "e스포츠도 스포츠인가?"
**소주제**: e스포츠의 대중적 인기는 전통 스포츠에 필적하는가?

이 프로젝트는 e스포츠와 전통 스포츠의 대중적 관심도를 비교 분석하기 위해 
다양한 데이터 소스에서 데이터를 크롤링하고 분석합니다.

---

## 🎯 크롤링 대상 및 수집 데이터

### 1. Escharts.com (e스포츠 시청자 통계)
| 데이터 | 설명 | 용도 |
|--------|------|------|
| Peak Viewers | 최고 동시 시청자 수 | 대회별 인기도 측정 |
| Hours Watched | 총 시청 시간 | 관심도 심층 분석 |
| Game Rankings | 게임별 시청자 순위 | 게임 간 인기도 비교 |
| Yearly Trends | 연도별 추이 | 성장률 분석 |

### 2. EsportsEarnings.com (e스포츠 상금 데이터)
| 데이터 | 설명 | 용도 |
|--------|------|------|
| Total Prize Pool | 게임별 총 상금 | 시장 규모 추정 |
| Tournament Prizes | 대회별 상금 | 전통 스포츠 대회와 비교 |
| Player Earnings | 선수별 수입 | 선수 수입 비교 |

### 3. Newzoo.com (시장 분석 리포트)
| 데이터 | 설명 | 용도 |
|--------|------|------|
| Market Size | 시장 규모 | 산업 규모 비교 |
| Audience Data | 관객 수 예측 | 팬층 규모 분석 |
| Growth Rates | 성장률 | 미래 전망 분석 |

---

## 📁 프로젝트 구조

```
esports_crawler/
├── esports_popularity_crawler.py   # 메인 크롤링 모듈
├── esports_vs_sports_analysis.py   # 비교 분석 및 시각화
├── requirements.txt                 # 필요 패키지
├── README.md                        # 사용 가이드
│
├── esports_data/                    # 크롤링 데이터 저장
│   ├── escharts_top_games_2025.csv
│   ├── escharts_lol_tournaments.csv
│   ├── escharts_yearly_comparison.csv
│   ├── earnings_games_by_prize.csv
│   ├── earnings_top_tournaments.csv
│   ├── earnings_top_players.csv
│   └── newzoo_market_data.json
│
└── analysis_output/                 # 분석 결과
    ├── viewership_comparison.png
    ├── prize_pool_comparison.png
    ├── market_growth_comparison.png
    ├── global_audience_comparison.png
    └── analysis_report.md
```

---

## 🔧 설치 방법

### 1. 필요 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 한글 폰트 설치 (선택사항, 시각화용)
```bash
# Ubuntu/Debian
sudo apt-get install fonts-nanum

# macOS (Homebrew)
brew install font-nanum-gothic
```

---

## 🚀 실행 방법

### Step 1: 데이터 크롤링
```bash
python esports_popularity_crawler.py
```

**예상 실행 시간**: 약 5-10분 (사이트 응답 속도에 따라 다름)

**출력 파일**:
- `esports_data/` 폴더에 CSV 파일들 생성

### Step 2: 비교 분석 및 시각화
```bash
python esports_vs_sports_analysis.py
```

**출력 파일**:
- `analysis_output/` 폴더에 그래프 이미지 및 리포트 생성

---

## 📊 분석 지표

### 대중적 관심도 측정 지표

1. **시청자 수 (Viewership)**
   - e스포츠: Peak Viewers (동시 시청자)
   - 전통 스포츠: TV 시청률, 스트리밍 시청자

2. **상금 규모 (Prize Pool)**
   - 팬들의 관심과 투자를 반영하는 지표
   - 크라우드펀딩 상금 = 팬 참여도

3. **시장 규모 (Market Size)**
   - 광고, 스폰서십, 미디어 권리 등 포함
   - 상업적 가치 = 대중적 관심도

4. **글로벌 팬 수 (Global Audience)**
   - 정기적으로 시청/참여하는 팬 수
   - 열성 팬(Enthusiasts) vs 일반 시청자

---

## ⚠️ 크롤링 주의사항

### 법적/윤리적 고려사항
1. **robots.txt 확인**: 각 사이트의 크롤링 정책 준수
2. **Rate Limiting**: 서버 부하 방지를 위해 요청 간 딜레이 추가
3. **개인정보**: 개인 식별 정보 수집 금지
4. **상업적 이용**: 데이터의 상업적 이용 시 라이선스 확인

### 기술적 주의사항
```python
# 적절한 딜레이 추가
import time
time.sleep(1)  # 요청 간 1초 대기

# User-Agent 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (학술연구용 크롤러)'
}

# 에러 핸들링
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
```

---

## 📈 예상 분석 결과

### 가설 검증

**가설**: e스포츠의 대중적 인기는 전통 스포츠에 필적한다

**예상 결과**:
- ❌ 절대적 규모: 전통 스포츠에 미치지 못함
- ✅ 성장률: 전통 스포츠 대비 2-3배 빠름
- ✅ 젊은 층: 18-34세에서 강력한 경쟁력
- ⚖️ 상금 규모: 일부 대회는 전통 스포츠 수준

---

## 🔍 추가 데이터 소스 (참고용)

크롤링이 어려운 경우 활용 가능한 공공 데이터:

| 사이트 | 데이터 유형 | URL |
|--------|------------|-----|
| Statista | 시장 통계 | statista.com |
| SocialBlade | 유튜브/트위치 채널 통계 | socialblade.com |
| TwitchTracker | 트위치 스트리밍 통계 | twitchtracker.com |
| SullyGnome | 트위치 게임/채널 분석 | sullygnome.com |
| Liquipedia | e스포츠 위키 데이터 | liquipedia.net |

---

## 📝 참고 문헌 및 데이터 출처

1. Newzoo Global Esports & Live Streaming Market Report
2. Escharts Annual Esports Statistics
3. Statista - Sports Market Data
4. FIFA/UEFA/IOC 공식 보고서

---

## 🤝 문의 및 기여

이 프로젝트는 학술 연구 목적으로 작성되었습니다.
데이터 수집 시 각 사이트의 이용약관을 준수해주세요.
