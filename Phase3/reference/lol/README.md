# 🌍 LoL 월드 챔피언십 역대 분석 프로젝트

## 📌 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **대주제** | LoL 월드 챔피언십 역대 분석 |
| **팀원 수** | 4명 |
| **사용 도구** | Python, Jupyter Lab |
| **데이터 수집** | Kaggle, 웹 크롤링 (Leaguepedia, Liquipedia, Oracle's Elixir) |

---

## 👥 팀원별 역할 분담

| 팀원 | 소주제 | 파일명 | 주요 시각화 |
|------|--------|--------|-------------|
| **A** | 지역별 우승/준우승 성과 분석 | `A_region_performance_analysis.ipynb` | 스택 바 차트, 트리맵, 파이 차트 |
| **B** | 연도별 결승전 경기 분석 | `B_finals_game_analysis.ipynb` | 라인 차트, 히트맵, 박스플롯 |
| **C** | MVP 및 우승팀 선수 분석 | `C_mvp_player_analysis.ipynb` | 도넛 차트, 레이더 차트, 산점도 |
| **D** | LCK vs LPL 맞대결 분석 | `D_lck_vs_lpl_analysis.ipynb` | 히트맵, 그룹 바 차트, 에어리어 차트 |

---

## 📂 프로젝트 구조

```
lol_worlds_project/
│
├── README.md                           # 프로젝트 개요
├── A_region_performance_analysis.ipynb # 팀원 A: 지역별 성과 분석
├── B_finals_game_analysis.ipynb        # 팀원 B: 결승전 분석
├── C_mvp_player_analysis.ipynb         # 팀원 C: MVP/선수 분석
├── D_lck_vs_lpl_analysis.ipynb         # 팀원 D: LCK vs LPL 분석
│
├── data/                               # 데이터 폴더 (생성 필요)
│   ├── worlds_results.csv
│   ├── player_stats.csv
│   └── matchup_history.csv
│
└── outputs/                            # 시각화 결과물 폴더 (생성 필요)
    ├── region_stacked_bar.png
    ├── finals_game_time_trend.png
    └── ...
```

---

## 🔧 환경 설정

### 필수 라이브러리 설치

```bash
pip install pandas numpy matplotlib seaborn plotly requests beautifulsoup4
```

### Jupyter Lab 설치 (선택)

```bash
pip install jupyterlab
jupyter lab
```

### 한글 폰트 설정

```python
# Windows
plt.rc('font', family='Malgun Gothic')

# Mac
plt.rc('font', family='AppleGothic')

# 마이너스 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False
```

---

## 📊 데이터 수집 가이드

### 1. Kaggle 데이터셋

| 데이터셋 | URL |
|---------|-----|
| League of Legends Worlds 2011-2022 | https://www.kaggle.com/datasets/pedrocsar/league-of-legends-worlds-20112022-stats |
| LoL Esports Match Data | https://www.kaggle.com/datasets/chuckephron/leagueoflegends |

**다운로드 방법:**
```bash
# Kaggle API 사용
pip install kaggle
kaggle datasets download -d pedrocsar/league-of-legends-worlds-20112022-stats
```

### 2. 크롤링 소스

| 사이트 | URL | 데이터 종류 |
|--------|-----|------------|
| **Leaguepedia** | https://lol.fandom.com/wiki/World_Championship | 역대 결과, 선수 정보 |
| **Liquipedia** | https://liquipedia.net/leagueoflegends/World_Championship | 대회 정보 |
| **Oracle's Elixir** | https://oracleselixir.com/tools/downloads | 경기 상세 통계 (CSV) |
| **Games of Legends** | https://gol.gg/ | 프로 경기 상세 데이터 |

---

## 📈 시각화 예시

### 팀원 A - 지역별 우승 분석
- 지역별 우승/준우승 스택 바 차트
- 우승 비율 파이 차트
- 트리맵 (지역 → 팀 계층)

### 팀원 B - 결승전 분석
- 연도별 평균 경기 시간 라인 차트
- 스코어 유형 분포 (3-0, 3-1, 3-2)
- 경기 시간 박스플롯

### 팀원 C - MVP/선수 분석
- 포지션별 MVP 분포 도넛 차트
- 선수 스탯 레이더 차트
- KDA vs Kill Participation 산점도

### 팀원 D - LCK vs LPL 분석
- 전체 전적 파이 차트
- 연도별 전적 그룹 바 차트
- 팀별 H2H 히트맵

---

## 📋 발표 체크리스트

- [ ] 주제 선정 배경 설명
- [ ] 각 팀원 역할 분담 명시
- [ ] 사용한 그래프 및 선택 이유 설명
- [ ] **결론 도출** (가장 중요!)
- [ ] 자료 출처 명시

### ⚠️ 피해야 할 점
- 단순 코드 나열 금지
- 그래프만 보여주고 끝내지 않기
- 시각화의 의미와 인사이트 반드시 포함

---

## 📅 일정

| 단계 | 내용 | 기한 |
|------|------|------|
| 1 | 데이터 수집 및 전처리 | - |
| 2 | 개인별 시각화 완료 | - |
| 3 | 팀별 통합 및 발표자료 제작 | - |
| 4 | 발표 (팀당 20분) | 오후 2시 |

---

## 📚 참고 자료

### 데이터 출처
- Kaggle: https://www.kaggle.com/
- Leaguepedia: https://lol.fandom.com/
- Liquipedia: https://liquipedia.net/leagueoflegends/
- Oracle's Elixir: https://oracleselixir.com/

### Python 라이브러리 문서
- Matplotlib: https://matplotlib.org/stable/
- Seaborn: https://seaborn.pydata.org/
- Plotly: https://plotly.com/python/

---

## 🏆 프로젝트 목표

> **"단순한 데이터 나열이 아닌, 인사이트 있는 스토리텔링으로 LoL e스포츠의 역사를 시각화한다"**

---

**Good Luck! 🎮**
