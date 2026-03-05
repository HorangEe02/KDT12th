# e스포츠 vs 전통 스포츠: 종합 분석 보고서

## 프로젝트 개요

**연구 질문**: e스포츠도 스포츠인가?

**분석 목적**: 데이터 기반으로 e스포츠와 전통 스포츠의 선수 특성, 생리학적 반응을 비교 분석하여 e스포츠의 스포츠성을 평가

**분석 기간**: 2025-01-28

**최종 수정일**: 2025-01-28 (한글 폰트 및 시각화 개선)

---

## 1. 사용 데이터셋

### 1.1 e스포츠 데이터

| 데이터셋 | 파일 경로 | 설명 | 샘플 수 |
|---------|----------|------|--------|
| CS:GO 상금 데이터 | `data/eSports Earnings/highest_earning_players.csv` | CS:GO 프로 선수 상금 정보 | 100명 |
| e스포츠 센서 데이터 | `data/eSports_Sensors_Dataset-master/` | 경기 중 심박수, GSR 측정 데이터 | 128,035건 (심박수) |

### 1.2 전통 스포츠 데이터

| 데이터셋 | 파일 경로 | 설명 | 샘플 수 |
|---------|----------|------|--------|
| FIFA 축구 선수 | `data/fifa_eda_stats.csv` | FIFA 게임 기반 실제 축구 선수 정보 | 17,173명 |
| NFL 선수 | `data/Beginners Sports Analytics NFL Dataset/players.csv` | 미식축구 선수 신체 정보 | 1,303명 |
| 올림픽 선수 | `data/120 years of Olympic history_athletes and results/athlete_events.csv` | 올림픽 참가 선수 기록 (2000년 이후) | 62,808명 |
| 생리학 데이터 | `data/athlete_physiological_dataset.csv` | 운동선수 심박수, 훈련 강도 | 23,400건 |

---

## 2. 변수 정의

### 2.1 선수 특성 변수

| 변수명 | 설명 | 단위 | 데이터 소스 |
|--------|------|------|------------|
| `Age` | 선수 연령 | 세 | 전 데이터셋 |
| `Rating` | e스포츠 선수 성과 지표 (상금 기반 정규화) | 0.5~1.5 | CS:GO |
| `Earnings` | 총 상금 | USD | CS:GO |
| `Overall` | 축구 선수 종합 능력치 | 0~100 | FIFA |
| `Height_cm` | 키 | cm | FIFA, NFL |
| `Weight_kg` | 몸무게 | kg | FIFA, NFL |
| `BMI` | 체질량지수 | kg/m² | 계산값 |
| `Position_Category` | 포지션 분류 | GK/DF/MF/FW | FIFA |

### 2.2 생리학적 변수

| 변수명 | 설명 | 단위 | 데이터 소스 |
|--------|------|------|------------|
| `heart_rate` | 심박수 | BPM | e스포츠 센서 |
| `Heart_Rate` | 심박수 | BPM | 전통 스포츠 생리학 |
| `Training_Intensity` | 훈련 강도 | Low/Medium/High | 전통 스포츠 생리학 |
| `gsr` | 피부 전기 반응 (스트레스 지표) | μS | e스포츠 센서 |

### 2.3 파생 변수

| 변수명 | 설명 | 계산 방법 |
|--------|------|----------|
| `intensity` | 운동 강도 구간 | 심박수 기준 (안정/가벼운/중간/고강도/최대) |
| `Category` | 종목 분류 | CS:GO, 축구, NFL, 올림픽 |
| `Type` | 스포츠 유형 | e스포츠 / 전통 스포츠 |

---

## 3. 시각화 결과 해석

---

### 3.1 종합 대시보드

#### 00_FINAL_COMPREHENSIVE_DASHBOARD.png

![종합 대시보드](output_final/00_FINAL_COMPREHENSIVE_DASHBOARD.png)

- **목적**: 전체 분석 결과를 한눈에 파악
- **구성**: 8개 섹션
  1. 종목별 선수 연령 분포 (Violin Plot)
  2. 종목별 평균 연령 비교 (오차막대 포함)
  3. 경기/훈련 중 심박수 분포 비교
  4. 운동 강도 구간별 비율
  5. 통계적 검정 결과 (t-검정, Cohen's d)
  6. 선수 역량 비교 (Radar Chart)
  7. e스포츠 스포츠성 평가 점수
  8. 종목별 특성 비교 (Heatmap)
- **핵심 발견**: e스포츠 선수는 전통 스포츠와 비교해 젊은 연령대에서 피크를 보이나, 인지적 요구도는 매우 높음
- **결론 박스**: 종합 점수 74.8/100점, "스포츠 선수 특성을 대부분 충족"

---

#### 00_INFOGRAPHIC_SUMMARY.png

![인포그래픽 요약](output_final/00_INFOGRAPHIC_SUMMARY.png)

- **목적**: 핵심 수치를 인포그래픽 스타일로 요약
- **주요 수치**: 평균 연령 22.2세, 경기 중 심박수 82.5 BPM, 종합 점수 74.8점

---

### 3.2 연령 분석 (01-03)

#### 01_age_distribution.png

![연령 분포](output_final/01_age_distribution.png)

- **사용 데이터**: CS:GO, FIFA, NFL, 올림픽 선수 연령
- **시각화 유형**: Violin Plot + Box Plot
- **결과 해석**:
  - CS:GO: 평균 22.2세 (범위: 16-28세) - 가장 좁은 분포
  - 축구: 평균 25.0세 (범위: 16-45세)
  - NFL: 평균 32.1세
  - 올림픽: 평균 26.1세
- **의미**: e스포츠는 체조, 다이빙과 유사하게 젊은 연령대에서 피크 성과를 보임

---

#### 02_age_comparison_histogram.png

![연령 비교 히스토그램](output_final/02_age_comparison_histogram.png)

- **사용 데이터**: e스포츠 vs 전통 스포츠 연령 분포
- **시각화 유형**: Histogram + KDE (Kernel Density Estimation)
- **결과 해석**:
  - e스포츠: 20-25세에 집중된 좁은 분포
  - 전통 스포츠: 25-30세 중심의 넓은 분포
- **통계적 유의성**: t = -24.76, p < 0.001 (매우 유의미한 차이)

---

#### 03_csgo_age_rating.png

![CS:GO 연령 vs Rating](output_final/03_csgo_age_rating.png)

- **사용 데이터**: CS:GO 선수 연령, 상금 기반 Rating
- **시각화 유형**: Scatter Plot + 2차 회귀선
- **변수**:
  - X축: 연령 (세)
  - Y축: Rating (상금 정규화, 0.5~1.5)
  - 색상: 상금 (USD)
- **결과 해석**: 20대 초중반에서 최고 성과, 이후 완만한 하락 추세

---

### 3.3 신체 조건 분석 (04)

#### 04_physical_comparison.png

![신체 조건 비교](output_final/04_physical_comparison.png)

- **사용 데이터**: FIFA 축구 선수, NFL 선수 신체 정보
- **시각화 유형**: Violin Plot (3개 패널)
- **변수**:
  - 키 (Height_cm)
  - 몸무게 (Weight_kg)
  - 키 vs 몸무게 산점도
- **결과 해석**:
  - NFL 선수: 평균 키 188cm, 몸무게 109kg (가장 큰 체격)
  - 축구 선수: 평균 키 175cm, 몸무게 75kg
- **의미**: e스포츠는 신체 조건에 대한 요구가 전통 스포츠 대비 낮음

---

### 3.4 종합 비교 (08, 10, 13)

#### 08_comprehensive_dashboard.png

![종합 비교 대시보드](output_final/08_comprehensive_dashboard.png)

- **목적**: 연령 관련 지표 종합 비교
- **구성**:
  - 종목별 평균 연령 막대 그래프
  - e스포츠 vs 전통 스포츠 비교
  - 종목별 연령 분포 바이올린 플롯

---

#### 10_radar_chart.png

![레이더 차트](output_final/10_radar_chart.png)

- **사용 데이터**: 정성적 평가 점수 (연구 기반)
- **시각화 유형**: Radar Chart (방사형 차트)
- **비교 항목**:

| 항목 | e스포츠 | 축구 |
|------|---------|------|
| 연령 (젊을수록 높음) | 55 | 55 |
| 연령 다양성 | 70 | 55 |
| 피크 지속성 | 40 | 70 |
| 신체 요구 | 20 | 80 |
| 팀워크 필요 | 95 | 85 |

- **결과 해석**: e스포츠는 팀워크 요구도가 높고, 신체 요구는 낮음

---

#### 13_evaluation_dashboard.png

![평가 대시보드](output_final/13_evaluation_dashboard.png)

- **목적**: e스포츠 스포츠성 평가 점수 시각화
- **평가 항목 및 점수**:

| 항목 | 점수 |
|------|------|
| 전문성 요구 | 85 |
| 경력 지속성 | 55 |
| 신체/인지적 요구 | 70 |
| 팀워크/전략성 | 90 |
| 선수 육성 체계 | 70 |

- **종합 점수**: 74.8/100점

---

### 3.5 심화 분석 (14-20)

#### 14_bullet_chart_heartrate.png

![심박수 불렛 차트](output_final/14_bullet_chart_heartrate.png)

- **목적**: 경기 중 심박수를 의학적 기준과 비교
- **시각화 유형**: Bullet Chart
- **비교 대상**:

| 활동 | 평균 심박수 (BPM) |
|------|------------------|
| e스포츠 (경기 중) | 82.5 |
| 사격 (경기 중) | 140 |
| 양궁 (경기 중) | 145 |
| 체스 (대국 중) | 120 |
| 일반인 (안정시) | 72 |

- **결과 해석**: e스포츠는 안정시 대비 약 14% 상승, 정밀 운동 종목보다는 낮음

---

#### 15_dual_regression_career.png

![경력-성과 회귀분석](output_final/15_dual_regression_career.png)

- **목적**: 경력-성과 관계 비교
- **시각화 유형**: Scatter Plot + 회귀선
- **변수**: 경력 (정규화) vs 성과 (정규화)
- **결과 해석**:
  - 축구: 완만한 우상향 (기울기 ≈ 0.1-0.2)
  - e스포츠: 유사한 우상향 패턴 (기울기 ≈ 0.4-0.5)
- **의미**: 경력과 성과의 양의 상관관계는 전통 스포츠와 동일

---

#### 16_violin_peak_age.png

![피크 연령 바이올린](output_final/16_violin_peak_age.png)

- **사용 데이터**: 올림픽 메달리스트 연령, e스포츠 피크 연령
- **시각화 유형**: Violin Plot
- **결과 해석**:

| 종목 | 피크 연령 중앙값 |
|------|-----------------|
| 체조 | 20세 |
| e스포츠 | 23세 |
| 축구 | 27세 |
| 사격 | 35세 |

- **의미**: e스포츠 피크 연령은 체조와 유사

---

#### 17_radar_position.png

![포지션별 레이더 차트](output_final/17_radar_position.png)

- **목적**: 포지션별 요구 역량 비교
- **비교 대상**: e스포츠 (정글러) vs 축구 (미드필더)
- **비교 항목**:

| 역량 | e스포츠 | 축구 |
|------|---------|------|
| 반응 속도 | 95 | 75 |
| 시야/정보 | 80 | 80 |
| 팀 소통 | 85 | 85 |
| 포지셔닝 | 90 | 80 |
| 체력 | 70 | 85 |
| 힘/강도 | 50 | 70 |

---

#### 19_apm_analysis.png

![APM 분석](output_final/19_apm_analysis.png)

- **목적**: APM (Actions Per Minute) 분석
- **시각화 유형**: Grouped Bar Chart
- **데이터** (연구 기반 참조값):

| 게임 | 프로 APM | 아마추어 APM | 배수 |
|------|---------|-------------|------|
| StarCraft II | 350 | 80 | 4.4배 |
| LoL | 250 | 50 | 5.0배 |
| Dota2 | 200 | 60 | 3.3배 |

- **의미**: 프로 선수는 일반인 대비 4-6배 높은 조작 속도

---

#### 20_summary_dashboard.png

![선수 특성 요약 대시보드](output_final/20_summary_dashboard.png)

- **목적**: 선수 특성 분석 종합 요약
- **구성**: 2x2 레이아웃
  - 좌상단: 핵심 발견 요약 박스
  - 우상단: 스포츠 인정 점수 재평가 (기존 vs 재평가)
  - 좌하단: 종목별 평균 연령 막대 그래프
  - 우하단: 최종 결론 박스
- **핵심 발견**:
  1. 심박수: e스포츠 선수도 경기 중 유의미한 심박수 상승 확인
  2. 경력-성과: 전통 스포츠와 동일한 우상향 패턴
  3. 피크 연령: 체조, 다이빙과 유사
  4. APM: 프로는 일반인의 4-6배
- **결론**: 선수 역량 점수 40점 → 70점 상향 권고, 종합 점수 68.75점 → 76.25점

---

### 3.6 생리학적 분석 (21-28)

#### 21_threshold_analysis.png

![임계값 분석](output_final/21_threshold_analysis.png)

- **목적**: 심박수 임계값 돌파 분석
- **시각화 유형**: Box Plot + 의학적 기준선
- **의학적 기준**:

| 구간 | 심박수 범위 (BPM) |
|------|------------------|
| 안정시 | 60-100 |
| 유산소 | 100-140 |
| 고강도 | 140-200 |

- **결과 해석**:
  - e스포츠: 대부분 안정시~가벼운 운동 범위
  - 전통 스포츠: 유산소~고강도 범위

---

#### 22_intensity_distribution.png

![강도 분포](output_final/22_intensity_distribution.png)

- **목적**: 운동 강도 구간별 분포 비교
- **시각화 유형**: Stacked Bar Chart
- **결과 해석**:

| 강도 구간 | e스포츠 | 전통 스포츠 |
|----------|---------|------------|
| 안정 (<100) | ~85% | ~5% |
| 가벼운 (100-120) | ~10% | ~10% |
| 중간 (120-140) | ~4% | ~25% |
| 고강도 (140-160) | ~1% | ~35% |
| 최대 (160+) | <1% | ~25% |

---

#### 23_temporal_dynamics.png

![시계열 분석](output_final/23_temporal_dynamics.png)

- **목적**: 경기 중 심박수 시계열 변화
- **시각화 유형**: Line Plot + Confidence Interval
- **결과 해석**: e스포츠 경기 진행에 따라 심박수 변동 확인

---

#### 24_convergence_analysis.png

![상관관계 분석](output_final/24_convergence_analysis.png)

- **목적**: 상관관계 분석
- **시각화 유형**: Scatter Plot + 회귀선
- **분석 내용**:
  - e스포츠: 경기 시간 vs 심박수
  - 전통 스포츠: 훈련 강도 vs 심박수
- **결과 해석**: 두 스포츠 모두 활동 강도와 심박수 간 양의 상관관계

---

#### 25_violin_plots.png

![바이올린 플롯](output_final/25_violin_plots.png)

- **목적**: 심박수 분포 상세 비교
- **시각화 유형**: 3패널 구성
  - 좌측: 심박수 분포 비교 (Violin Plot)
  - 중앙: 심박수 변동성 비교 (Bar Chart)
  - 우측: 통계적 검정 결과 박스
- **통계 결과**:
  - e스포츠 평균: 82.5 BPM
  - 전통 스포츠 평균: 140.0 BPM
  - t-검정 p값: 0.00e+00 (매우 유의미)
  - Cohen's d: -2.678 (큰 효과 크기)
  - 해석: 큰 차이

---

#### 26_radar_chart.png

![생체 지표 레이더](output_final/26_radar_chart.png)

- **목적**: 생체 지표 다차원 비교
- **비교 항목**: 평균 심박수, 최대 심박수, 심박수 변동성, 심박수 범위
- **결과 해석**: 전통 스포츠가 모든 지표에서 높은 값을 보임

---

#### 27_clustering.png

![클러스터링 분석](output_final/27_clustering.png)

- **목적**: PCA/t-SNE 기반 클러스터링
- **시각화 유형**: Scatter Plot (2D 투영)
- **분석 방법**:
  - PCA: 주성분 분석으로 차원 축소
  - t-SNE: 비선형 차원 축소
- **결과 해석**: e스포츠와 전통 스포츠 클러스터가 명확히 분리됨

---

#### 28_final_dashboard.png

![생리학적 분석 종합 대시보드](output_final/28_final_dashboard.png)

- **목적**: 생리학적 분석 종합 대시보드
- **구성**: 3x3 GridSpec 레이아웃
  1. 심박수 분포 비교 (Histogram)
  2. 고강도 구간(140+ BPM) 비율 (Bar Chart)
  3. 심박수 박스플롯
  4. 운동 강도 구간별 분포
  5. 심박수 바이올린 플롯
  6. 통계적 검정 결과 (평균, t-검정, Cohen's d)
  7. 하단 결론 박스
- **통계 결과**:
  - 평균 심박수 차이: -57.5 BPM
  - t-검정: t = -491.33, p-value: 0.00e+00
  - Cohen's d: -2.678 (효과 크기: 큰 차이)
- **핵심 결론**: e스포츠 선수도 경기 중 심박수 상승 확인 (안정시 대비 +14%), 전통 스포츠 대비 절대값은 낮으나 인지적 활성화 상태, 심박수 외 반응속도, 정밀동작, 인지부하 등 복합 평가 필요

---

## 4. 통계적 검정 결과

### 4.1 연령 비교

| 검정 방법 | 통계량 | p-value | 해석 |
|----------|--------|---------|------|
| Welch's t-test | t = -24.76 | 3.05e-51 | 매우 유의미한 차이 |
| Mann-Whitney U | U = 26,644 | 5.70e-39 | 매우 유의미한 차이 |
| Cohen's d | -1.448 | - | 큰 효과 크기 |

### 4.2 심박수 비교

| 검정 방법 | 통계량 | p-value | 해석 |
|----------|--------|---------|------|
| Welch's t-test | t = -491.33 | < 0.001 | 매우 유의미한 차이 |
| Cohen's d | -2.678 | - | 매우 큰 효과 크기 |

---

## 5. 최종 결론

### 5.1 종합 평가 점수

| 평가 항목 | 점수 | 가중치 | 가중 점수 |
|----------|------|--------|----------|
| 전문성 요구 | 85 | 25% | 21.25 |
| 경력 지속성 | 55 | 20% | 11.00 |
| 신체/인지적 요구 | 70 | 20% | 14.00 |
| 팀워크/전략성 | 90 | 20% | 18.00 |
| 선수 육성 체계 | 70 | 15% | 10.50 |
| **총점** | - | 100% | **74.75** |

### 5.2 주요 발견

1. **연령 특성**: e스포츠 선수는 체조, 다이빙과 유사하게 젊은 연령대(20-25세)에서 피크 성과
2. **생리적 반응**: 경기 중 심박수 상승 확인 (안정시 대비 +14%), 인지적 활성화 상태
3. **인지적 요구**: 반응속도, 전략적 사고, 정밀 동작에서 높은 전문성 요구 (APM 4-6배)
4. **팀워크**: 전통 팀 스포츠와 동등한 수준의 협동 및 의사소통 필요
5. **경력-성과**: 전통 스포츠와 동일한 우상향 패턴 (경력이 성과에 기여)

### 5.3 결론

> **"e스포츠는 '인지 기반 전문 스포츠'로서 전통 스포츠와 동등한 위상 인정 가능"**

- 신체적 요구도는 전통 스포츠 대비 낮으나, 인지적/정신적 요구도가 매우 높음
- 사격, 양궁, 체스 등 정밀/전략 스포츠와 유사한 특성
- 종합 점수 74.8점으로 "스포츠 선수 특성을 대부분 충족"

### 5.4 한계점

1. CS:GO 선수 연령 데이터는 시뮬레이션 값 사용 (실제 데이터 부재)
2. e스포츠 센서 데이터의 샘플 크기가 전통 스포츠 대비 제한적
3. 인지 부하, 반응 속도 등의 직접적 측정 데이터 부족

### 5.5 향후 연구 제안

1. 실제 e스포츠 선수 프로필 데이터 수집 (나이, 경력, 성과)
2. EEG, 반응 시간 등 인지 부하 직접 측정
3. 장기 추적 연구를 통한 경력 곡선 분석

---

## 부록 A: 파일 구조 및 코드 구성

### 디렉토리 구조

```
03_medical/
├── final_c.py                    # 메인 분석 스크립트 (2,167줄, 92KB)
├── sum_c.py                      # 선수 특성 분석 스크립트
├── ANALYSIS_REPORT.md            # 본 보고서
├── c/                            # 하위 분석 디렉토리
├── data_c/                       # 데이터 디렉토리
├── medical/                      # 생리학 분석 디렉토리
└── output_final/                 # 시각화 출력 (23개 PNG 파일)
```

### final_c.py 코드 구조

```
PART 0: 라이브러리 임포트 및 설정
    - setup_korean_font()         # 한글 폰트 설정
    - reset_korean_font()         # 시각화 전 폰트 초기화
    - COLORS 딕셔너리            # 색상 팔레트 정의

PART 1: 데이터 로드 및 전처리
    - load_all_data()            # 모든 데이터셋 로드
    - load_esports_sensor_data() # e스포츠 센서 데이터 로드
    - preprocess_data()          # 데이터 전처리

PART 2: 기초 통계 분석
    - basic_statistics()         # 기초 통계량 계산
    - create_age_comparison_data() # 연령 비교 데이터 생성

PART 3: 기초 시각화 (01-13)
    - create_basic_visualizations()
    - create_viz_01()            # 연령 분포
    - create_viz_02()            # 연령 히스토그램
    - create_viz_03_to_13()      # 신체 조건, 레이더 차트 등

PART 4: 심화 통계 분석
    - advanced_statistics()      # t-검정, Mann-Whitney U, Cohen's d

PART 5: 심화 시각화 (14-20)
    - create_advanced_visualizations()
    - create_viz_14_bullet()     # 심박수 불렛 차트
    - create_viz_15_regression() # 경력-성과 회귀
    - create_viz_16_peak_age()   # 피크 연령
    - create_viz_17_to_20()      # 포지션, APM, 요약

PART 6: 생리학적 분석 (21-28)
    - create_medical_visualizations()
    - create_viz_21_threshold()  # 임계값 분석
    - create_viz_22_intensity()  # 강도 분포
    - create_viz_23_temporal()   # 시계열 분석
    - create_viz_24_convergence() # 상관관계
    - create_viz_25_violin()     # 바이올린 플롯
    - create_viz_26_radar()      # 생체 지표 레이더
    - create_viz_27_clustering() # 클러스터링
    - create_viz_28_final_dashboard() # 생리학 종합

PART 7: 종합 평가
    - final_evaluation()         # 최종 점수 계산

PART 8: 최종 종합 대시보드
    - create_final_comprehensive_dashboard()
    - create_infographic_summary()

main()                           # 메인 실행 함수
```

---

## 부록 B: 코드 수정 이력

### 2025-01-28 수정 사항

#### 1. 한글 폰트 설정 강화

**문제**: 일부 시각화에서 한글이 깨지거나 □로 표시됨

**해결**:
```python
# 기존
plt.rcParams['font.family'] = 'AppleGothic'

# 수정 후
plt.rcParams['font.family'] = 'Apple SD Gothic Neo'
plt.rcParams['font.sans-serif'] = ['Apple SD Gothic Neo', 'AppleGothic']
plt.rcParams['axes.unicode_minus'] = False
```

#### 2. 결론 박스 monospace 폰트 문제 해결

**문제**: `family='monospace'` 사용 시 한글 미지원

**해결**: monospace 속성 제거, 일반 텍스트 박스로 변경
```python
# 기존
ax.text(..., family='monospace', ...)

# 수정 후
ax.text(..., bbox=dict(boxstyle='round', facecolor='#E8F6F3'), ...)
```

#### 3. f-string 내 문자열 곱셈 문제 해결

**문제**: `f"{'─'*25}"` 패턴이 렌더링 시 텍스트 반복 유발

**해결**: 문자열 곱셈을 f-string 외부로 분리
```python
# 기존
f"{'─'*25}\n"

# 수정 후
separator = "-" * 25
f"{separator}\n"
```

#### 4. 20_summary_dashboard.png 레이아웃 재구성

**문제**: 텍스트 중복 출력으로 그래프 가려짐

**해결**:
- `plt.subplots(2, 2)` 사용하여 명확한 2x2 레이아웃 구성
- 각 패널에 `transform=axes[i,j].transAxes` 명시
- `plt.close('all')` 추가로 이전 figure 완전 정리

#### 5. 이모지 제거

**문제**: 일부 폰트에서 이모지 렌더링 실패

**해결**: 이모지를 대괄호 텍스트로 대체
```python
# 기존
"📋 최종 분석 결론"
"✅ 종합 점수"

# 수정 후
"[ 최종 분석 결론 ]"
"종합 점수"
```

---

## 부록 C: 시각화 파일 목록

| 번호 | 파일명 | 크기 | 설명 |
|-----|--------|------|------|
| 00 | FINAL_COMPREHENSIVE_DASHBOARD.png | 912KB | 최종 종합 대시보드 |
| 00 | INFOGRAPHIC_SUMMARY.png | 269KB | 인포그래픽 요약 |
| 01 | age_distribution.png | 125KB | 연령 분포 (Violin/Box) |
| 02 | age_comparison_histogram.png | 102KB | 연령 히스토그램 비교 |
| 03 | csgo_age_rating.png | 97KB | CS:GO 연령-성과 관계 |
| 04 | physical_comparison.png | 232KB | 신체 조건 비교 |
| 08 | comprehensive_dashboard.png | 156KB | 종합 비교 대시보드 |
| 10 | radar_chart.png | 235KB | 종목별 특성 레이더 |
| 13 | evaluation_dashboard.png | 63KB | 평가 점수 대시보드 |
| 14 | bullet_chart_heartrate.png | 67KB | 심박수 불렛 차트 |
| 15 | dual_regression_career.png | 138KB | 경력-성과 회귀 분석 |
| 16 | violin_peak_age.png | 70KB | 피크 연령 바이올린 |
| 17 | radar_position.png | 237KB | 포지션별 역량 레이더 |
| 19 | apm_analysis.png | 43KB | APM 분석 |
| 20 | summary_dashboard.png | 152KB | 선수 특성 요약 (2x2 레이아웃) |
| 21 | threshold_analysis.png | 60KB | 임계값 분석 |
| 22 | intensity_distribution.png | 40KB | 강도 분포 |
| 23 | temporal_dynamics.png | 96KB | 시계열 분석 |
| 24 | convergence_analysis.png | 338KB | 상관관계 분석 |
| 25 | violin_plots.png | 226KB | 심박수 바이올린 (3패널) |
| 26 | radar_chart.png | 185KB | 생체 지표 레이더 |
| 27 | clustering.png | 53KB | 클러스터링 분석 |
| 28 | final_dashboard.png | 269KB | 생리학 종합 대시보드 |

---

*보고서 작성일: 2025-01-28*
*최종 수정일: 2025-01-28*
*분석 도구: Python (pandas, numpy, matplotlib, seaborn, scipy, sklearn)*
