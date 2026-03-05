# 🎮⚽ e스포츠 vs 전통 스포츠: 선수 특성 비교 분석

> **"e스포츠도 스포츠인가?"** - 데이터 기반 선수 특성 분석을 통한 답변

---

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **대주제** | e스포츠도 스포츠인가? |
| **소주제** | 선수 특성 비교 |
| **분석 목표** | e스포츠 선수의 프로필이 전통 스포츠 선수와 어떻게 다른지 데이터 기반 분석 |
| **주요 지표** | 연령 분포, 경력 기간, 신체 조건, 포지션별 특성 |

---

## 🎯 연구 질문

1. **연령 분포**: e스포츠 선수의 피크 연령은 전통 스포츠와 비교해 몇 살인가?
2. **경력 기간**: 프로 선수로서의 경력 기간이 전업 가능한 수준인가?
3. **신체 조건**: 신체 조건(키/몸무게)이 e스포츠 성과에 영향을 미치는가?
4. **연령-성과 관계**: 연령과 수입/성과 간의 상관관계는 어떠한가?

---

## 📁 데이터셋

| 데이터셋 | 출처 | 선수 수 | 용도 |
|----------|------|---------|------|
| [CSGO Pro Players](https://www.kaggle.com/datasets/naumanaarif/csgo-pro-players-dataset) | Kaggle | 811명 | e스포츠 대표 |
| [FIFA Data for EDA](https://www.kaggle.com/datasets/mukeshmanral/fifa-data-for-eda-and-stats/data) | Kaggle | 18,147명 | 축구 선수 |
| [NFL Dataset](https://www.kaggle.com/datasets/aryashah2k/beginners-sports-analytics-nfl-dataset) | Kaggle | 1,303명 | 미식축구 선수 |
| [120 Years Olympic History](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results) | Kaggle | 62,808명 | 올림픽 선수 (2000년 이후) |

---

## 🔧 기술 스택

```
Python 3.x
├── pandas          # 데이터 처리
├── numpy           # 수치 연산
├── matplotlib      # 시각화
├── seaborn         # 고급 시각화
└── scipy           # 통계 분석
```

---

## 📊 주요 분석 결과

### 1️⃣ 연령 비교 (t-test 결과)

```
┌─────────────────────────────────────────────────────────┐
│  e스포츠 평균: 25.85세  vs  전통 스포츠 평균: 29.52세   │
│  평균 차이: 3.67세 (p-value: 5.04×10⁻⁸¹)              │
│  결론: ✅ 통계적으로 유의미한 차이                      │
└─────────────────────────────────────────────────────────┘
```

### 2️⃣ 종목별 연령 통계

| 종목 | 평균 연령 | 연령 범위 | 표준편차 |
|------|-----------|-----------|----------|
| 🎮 CS:GO | 25.85세 | 17~36세 | ±3.67세 |
| ⚽ 축구 | 25.12세 | 16~45세 | ±4.67세 |
| 🏈 NFL | 32.09세 | 26~47세 | ±3.25세 |
| 🏅 올림픽 | 26.08세 | 13~73세 | ±6.42세 |

### 3️⃣ 신체 조건 비교

| 종목 | 평균 키 | 평균 몸무게 | 특징 |
|------|---------|-------------|------|
| 🏈 NFL | 188cm | 109kg | 가장 높은 신체 요구 |
| ⚽ 축구 | 181cm | 75kg | 포지션별 차별화 |
| 🎮 e스포츠 | - | - | 신체 조건 무관 |

---

## 📈 스포츠 인정 관점 평가

| 평가 항목 | 점수 | 평가 근거 |
|-----------|------|----------|
| 전문성 요구 | 85/100 | 높은 수준의 전문 훈련 필요 |
| 경력 지속성 | 55/100 | 전통 스포츠 대비 좁은 연령 분포 |
| 신체적 요구 | 25/100 | 반응속도 외 신체 조건 무관 |
| 팀워크/전략 | 90/100 | 높은 전략성과 협업 능력 요구 |
| 선수 육성 체계 | 70/100 | 아카데미, 연습생 시스템 존재 |
| **종합** | **65/100** | 전문성 인정, 신체 요소 부족 |

---

## 💡 결론

### "e스포츠도 스포츠인가?"에 대한 답변

> e스포츠는 **전문성, 팀워크, 전략적 사고** 측면에서 전통 스포츠와 유사한 특성을 보입니다.  
> 다만, **신체적 요구사항**이 현저히 낮다는 점에서 전통적인 스포츠 정의와는 차이가 있습니다.

**제안**: e스포츠는 **"마인드 스포츠"** 또는 **"디지털 스포츠"**라는 새로운 카테고리로 분류하는 것이 적절합니다.

---

## 📂 파일 구조

```
project/
├── data/
│   ├── csgo_players.csv
│   ├── fifa_eda_stats.csv
│   ├── Beginners Sports Analytics NFL Dataset/
│   │   └── players.csv
│   └── 120 years of Olympic history_athletes and results/
│       └── athlete_events.csv
├── esports_player_characteristics.ipynb    # 메인 분석 노트북
├── esports_analysis_report.docx            # 결론 보고서
└── README.md                               # 프로젝트 설명
```

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 필요 라이브러리 설치
pip install pandas numpy matplotlib seaborn scipy
```

### 2. 데이터 준비

Kaggle에서 데이터셋을 다운로드하여 `data/` 폴더에 배치합니다.

### 3. 노트북 실행

```bash
jupyter notebook esports_player_characteristics.ipynb
```

---

## ⚠️ 연구의 한계

1. **데이터 한계**
   - e스포츠 선수의 신체 조건 데이터 부재
   - 경력 기간 직접 계산 불가 (경력 시작 연도 미포함)
   - LoL 데이터는 일반 유저 통계로 프로 선수 분석에 부적합

2. **향후 과제**
   - e스포츠 선수 신체 조건 및 건강 데이터 수집
   - 경력 기간 및 은퇴 후 진로 추적 연구
   - 반응속도, 인지 능력 등 e스포츠 특화 지표 개발
   - 다양한 e스포츠 종목으로 분석 확대

---

## 📚 참고 자료

### 데이터 출처
- [CSGO Pro Players Dataset](https://www.kaggle.com/datasets/naumanaarif/csgo-pro-players-dataset)
- [FIFA Data for EDA and Stats](https://www.kaggle.com/datasets/mukeshmanral/fifa-data-for-eda-and-stats/data)
- [Beginners Sports Analytics NFL Dataset](https://www.kaggle.com/datasets/aryashah2k/beginners-sports-analytics-nfl-dataset)
- [120 Years of Olympic History](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results)

### 추가 참고
- [HLTV.org](https://www.hltv.org/) - CS:GO 통계
- [Liquipedia](https://liquipedia.net/) - e스포츠 위키
- [Transfermarkt](https://www.transfermarkt.com/) - 축구 선수 데이터

---

## 📝 작성 정보

| 항목 | 내용 |
|------|------|
| 작성일 | 2025년 1월 |
| 프로젝트 | e스포츠도 스포츠인가? |
| 담당 | 팀원 3 (선수 특성 비교) |

---

## 📄 라이선스

이 프로젝트는 학술 연구 및 교육 목적으로 제작되었습니다.
