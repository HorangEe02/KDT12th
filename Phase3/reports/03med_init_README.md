# 👤 e스포츠 vs 전통 스포츠: 선수 특성 비교 분석

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **대주제** | e스포츠도 스포츠인가? |
| **소주제** | 선수 특성 비교 |
| **담당** | 팀원 3 |
| **분석 목표** | e스포츠 선수의 프로필이 전통 스포츠 선수와 어떻게 다른지 데이터 기반 분석 |

---

## 📁 폴더 구조

```
data_c/
├── esports_player_characteristics.ipynb  # 메인 분석 노트북
├── README.md                              # 본 문서
├── data/                                  # 데이터 폴더
│   ├── csgo_players.csv                  # CS:GO 프로 선수 데이터
│   ├── fifa_eda_stats.csv                # FIFA 선수 통계
│   ├── LeaguePlayerStats.csv             # LoL 선수 통계
│   ├── 120 years of Olympic history.../  # 올림픽 선수 데이터
│   └── Beginners Sports Analytics NFL.../# NFL 선수 데이터
└── [시각화 결과]
    ├── 01_age_distribution.png           # 연령 분포 비교
    ├── 02_age_comparison_histogram.png   # 연령 히스토그램
    ├── 03_csgo_age_rating.png           # CS:GO 연령-성과 관계
    ├── 04_physical_comparison.png        # 신체 조건 비교
    ├── 05_football_position.png          # 축구 포지션별 특성
    ├── 06_nfl_position.png               # NFL 포지션별 특성
    ├── 07_age_performance.png            # 연령-성과 관계
    ├── 08_comprehensive_dashboard.png    # 종합 대시보드
    ├── 09_correlation_heatmap.png        # 상관관계 히트맵 (추가)
    ├── 10_radar_chart.png               # 레이더 차트 (추가)
    ├── 11_bubble_chart.png              # 버블 차트 (추가)
    ├── 12_age_group_violin.png          # 연령대별 성과 (추가)
    └── 13_evaluation_dashboard.png      # 종합 평가 대시보드 (추가)
```

---

## 📊 사용 데이터셋

| 데이터셋 | 출처 | 선수 수 | 용도 |
|----------|------|---------|------|
| CS:GO Pro Players | [Kaggle](https://www.kaggle.com/datasets/naumanaarif/csgo-pro-players-dataset) | 811명 | e스포츠 선수 연령/성과 |
| FIFA Data for EDA | [Kaggle](https://www.kaggle.com/datasets/mukeshmanral/fifa-data-for-eda-and-stats) | 18,147명 | 축구 선수 신체조건/연령 |
| NFL Dataset | [Kaggle](https://www.kaggle.com/datasets/aryashah2k/beginners-sports-analytics-nfl-dataset) | 1,303명 | NFL 선수 신체조건 |
| 120 Years Olympic History | [Kaggle](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history) | 62,808명 | 올림픽 선수 참고용 |

---

## 📈 분석 방법론

### 통계 분석 기법
1. **정규성 검정**: Shapiro-Wilk test
2. **등분산 검정**: Levene's test
3. **평균 비교**: Student's t-test, Welch's t-test
4. **비모수 검정**: Mann-Whitney U test
5. **효과 크기**: Cohen's d
6. **상관분석**: Pearson r, Spearman ρ
7. **회귀분석**: OLS 다항회귀 (2차)

### 주요 분석 질문
1. e스포츠 선수의 피크 연령은 전통 스포츠와 비교해 몇 살인가?
2. 프로 선수로서의 경력 기간이 전업 가능한 수준인가?
3. 신체 조건이 e스포츠 성과에 영향을 미치는가?
4. 연령과 수입/성과 간의 상관관계는 어떠한가?

---

## 🔬 주요 분석 결과

### 1. 연령 분포 비교

| 종목 | 평균 연령 | 표준편차 | 연령 범위 |
|------|----------|----------|----------|
| e스포츠 (CS:GO) | 25.9세 | 3.7세 | 17-36세 |
| 축구 (FIFA) | 25.1세 | 4.7세 | 16-45세 |
| NFL | 32.1세 | 3.2세 | 26-47세 |
| 올림픽 | 26.1세 | 5.3세 | 12-71세 |

**통계적 검정 결과**:
- Welch's t-test: p < 0.001 (유의미한 차이)
- Cohen's d: 효과 크기 중간~큼

### 2. 연령-성과 관계

| 종목 | 추정 피크 연령 | 상관계수 (Pearson) |
|------|--------------|-------------------|
| CS:GO | 약 23-25세 | -0.15 ~ -0.20 |
| FIFA | 약 28-31세 | 0.20 ~ 0.25 |

**해석**: e스포츠 선수는 전통 스포츠보다 더 이른 피크 연령을 보임

### 3. 신체 조건 비교

| 종목 | 평균 키 | 평균 몸무게 | BMI |
|------|--------|-----------|-----|
| 축구 (FIFA) | 181.3cm | 75.3kg | 22.9 |
| NFL | 186.0cm | 100.9kg | 29.1 |
| 올림픽 | 176.7cm | 72.5kg | 23.0 |

**결론**: 전통 스포츠는 포지션별로 명확한 신체 요구사항 존재

---

## 📊 시각화 설명

### 기본 시각화 (01-08)

| 시각화 | 설명 | 해석 |
|--------|------|------|
| 01_age_distribution | Violin + Box Plot | 종목별 연령 분포 비교 |
| 02_age_comparison_histogram | 히스토그램 + KDE | e스포츠 vs 전통 스포츠 연령 비교 |
| 03_csgo_age_rating | Scatter + 추세선 | CS:GO 연령-Rating 관계 |
| 04_physical_comparison | 4개 서브플롯 | 키, 몸무게, BMI 비교 |
| 05_football_position | Box Plot 3종 | 축구 포지션별 신체조건 |
| 06_nfl_position | Box Plot 3종 | NFL 포지션별 신체조건 |
| 07_age_performance | Scatter 2종 | 연령-성과 관계 비교 |
| 08_comprehensive_dashboard | 종합 대시보드 | 모든 분석 결과 요약 |

### 추가 시각화 (09-13) - v2

| 시각화 | 설명 | 해석 |
|--------|------|------|
| 09_correlation_heatmap | 상관관계 히트맵 | CS:GO/FIFA 변수 간 상관관계 |
| 10_radar_chart | 레이더 차트 | 종목별 선수 특성 비교 |
| 11_bubble_chart | 버블 차트 | 연령-성과-경험 다차원 관계 |
| 12_age_group_violin | 연령대별 바이올린 | 연령대별 성과 분포 |
| 13_evaluation_dashboard | 종합 평가 대시보드 | 가중 점수 및 평가 결과 |

---

## 🏆 종합 평가 결과

### 선수 특성 관점 평가 (100점 만점)

| 평가 항목 | 점수 | 가중치 | 가중 점수 | 근거 |
|----------|------|--------|----------|------|
| 전문성 요구 | 85점 | 25% | 21.25점 | 높은 Rating 달성을 위한 전문 훈련 필요 |
| 경력 지속성 | 55점 | 20% | 11.00점 | 전통 스포츠 대비 좁은 연령 분포 |
| 신체/인지적 요구 | 40점 | 20% | 8.00점 | 반응속도, 집중력 필요하나 신체 영향 미미 |
| 팀워크/전략성 | 90점 | 20% | 18.00점 | 팀 기반 게임에서 높은 전략성 요구 |
| 선수 육성 체계 | 70점 | 15% | 10.50점 | 아카데미, 연습생 시스템 존재 |

**종합 점수: 68.75/100점**

**평가**: 높음 - 스포츠 선수 특성을 대부분 충족

---

## ⚠️ 분석의 한계점

1. **데이터 한계**
   - e스포츠 선수의 신체 조건 데이터 부재
   - 경력 기간 직접 계산 불가 (경력 시작 연도 미포함)
   - LoL 데이터는 일반 유저 통계로 프로 선수 분석에 부적합

2. **방법론적 한계**
   - 게임별 특성 차이 미반영
   - 지역/리그별 차이 미분석
   - 시계열 변화 추적 불가

---

## 📚 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1 | 2025-01-27 | 초기 분석 및 시각화 (01-08) 구현 |
| v2 | 2025-01-27 | 인코딩 자동 감지 함수 추가 |
| v2 | 2025-01-27 | 심화 통계 분석 추가 (t-test, Mann-Whitney, Cohen's d) |
| v2 | 2025-01-27 | 상관관계 분석 추가 (Pearson, Spearman) |
| v2 | 2025-01-27 | 회귀 분석 추가 (OLS) |
| v2 | 2025-01-27 | 추가 시각화 (09-13) |
| v2 | 2025-01-27 | 종합 평가 시스템 구현 |
| v2 | 2025-01-27 | README.md 작성 |

---

## 🔗 참고자료

### 데이터 출처
1. [CSGO Pro Players Dataset](https://www.kaggle.com/datasets/naumanaarif/csgo-pro-players-dataset)
2. [FIFA Data for EDA and Stats](https://www.kaggle.com/datasets/mukeshmanral/fifa-data-for-eda-and-stats)
3. [NFL Dataset (Beginners)](https://www.kaggle.com/datasets/aryashah2k/beginners-sports-analytics-nfl-dataset)
4. [120 Years of Olympic History](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history)

### 추가 참고
- HLTV.org (CS:GO 통계)
- Liquipedia (e스포츠 위키)
- Transfermarkt (축구 선수 데이터)

---

**작성일**: 2025년 1월 27일
**프로젝트**: e스포츠도 스포츠인가? - 팀원 3 (선수 특성 비교)
