# 🍱 직장인 점심 최적화 파이프라인

> **"오늘 뭐 먹지?"를 데이터로 해결합니다.**
>
> 날씨, 영양 밸런스, 팀 선호도, 음식점 정보를 통합 분석하여
> 매일 반복되는 점심 의사결정 피로를 줄여주는 데이터 파이프라인 & 대시보드 프로젝트

---

## 📌 프로젝트 개요

### 배경 및 문제 정의

직장인이 하루 중 가장 자주 마주하는 소소한 스트레스 중 하나가 **"점심 뭐 먹지?"**입니다.
매일 같은 고민을 반복하면서도, 결국 익숙한 곳만 방문하거나 팀원 간 의견이 엇갈려
불필요한 시간을 소모하게 됩니다.

이 프로젝트는 다음과 같은 **실생활 불편함**을 해결합니다.

- 매일 반복되는 점심 메뉴 선택의 **의사결정 피로(Decision Fatigue)**
- 같은 음식점만 반복 방문하는 **편향된 식사 패턴**
- 날씨·미세먼지를 고려하지 않은 **비효율적인 외출**
- 주간 단위 **영양 불균형** 누적 (단백질 부족, 탄수화물 과다 등)
- 팀 단위 식사 시 **의견 수렴의 비효율성**

### 해결 방안

4개의 공공 API 및 사용자 데이터를 **하나의 파이프라인**으로 통합하고,
가중 점수 알고리즘을 통해 **오늘의 최적 점심**을 추천하는 시스템을 구축합니다.

---

## 🎯 프로젝트 기획 의도

### 주제

**"데이터 기반 직장인 점심 의사결정 최적화 시스템"**

직장인의 점심 식사라는 일상적이고 반복적인 행위를 데이터 파이프라인으로 구조화하여,
날씨·영양·거리·팀 선호도 4개 축의 정보를 통합 분석하고 최적의 메뉴를 추천하는
실시간 의사결정 지원 대시보드를 구축합니다.

### 기획 의도

이 프로젝트는 단순한 맛집 추천 앱이 아니라, **데이터 엔지니어링의 전체 생애주기**를 경험하기 위한
미니 프로젝트입니다. 다음 세 가지 관점에서 기획되었습니다.

**1. 실생활 문제의 데이터화**

"오늘 뭐 먹지?"라는 질문은 단순해 보이지만, 실제로는 거리·날씨·건강·동료 선호·예산·방문 이력 등
다양한 변수가 얽힌 복합 의사결정 문제입니다. 이를 정량화 가능한 점수 모델로 변환함으로써,
일상의 모호한 판단을 데이터 기반의 명확한 의사결정으로 전환할 수 있음을 보여줍니다.

**2. End-to-End 파이프라인 학습**

수집(Extract) → 정제(Transform) → 적재(Load) → 시각화(Dashboard)로 이어지는
전체 데이터 파이프라인을 하나의 주제 안에서 경험합니다. 4개의 이질적인 데이터 소스(지도 API,
기상 API, 식품 영양 API, 사용자 입력)를 통합하는 과정에서 실무에서 마주하는
스키마 불일치, API 호출 제한, 데이터 갱신 주기 차이 등의 문제를 자연스럽게 학습합니다.

**3. 비즈니스 확장 가능성**

직장인 점심 최적화는 사내 복지 플랫폼, 기업용 식권 서비스, 건강관리 앱,
상권 분석 도구 등으로 확장 가능한 실용적 주제입니다. 프로토타입 수준의 MVP를 통해
비즈니스 가치를 검증하고, 이후 실서비스로 발전시킬 수 있는 토대를 마련합니다.

### 도출할 인사이트

이 프로젝트를 통해 다음과 같은 인사이트를 도출할 수 있습니다.

| 영역 | 도출 인사이트 | 활용처 |
|------|-------------|--------|
| **의사결정 효율** | 점심 메뉴 결정에 소요되는 시간과 인지 부하를 정량적으로 측정하고 절감 효과를 산출 | 사내 생산성 보고서 |
| **식사 패턴 분석** | 개인·팀 단위 음식 카테고리 편중도, 재방문율, 요일별 선호 변화 파악 | 개인 건강관리, 팀 문화 개선 |
| **날씨-메뉴 상관관계** | 기온·미세먼지·강수량과 메뉴 유형 선택 간의 통계적 상관관계 규명 | 외식업 마케팅 전략 |
| **영양 불균형 조기 감지** | 주간 단위 탄·단·지 비율 추적을 통한 영양 편향 자동 경고 | 기업 건강관리 프로그램 |
| **집단 선호도 예측** | 팀원 투표 이력 학습을 통한 합의 도달 시간 단축 모델 | 그룹 의사결정 도구 |

---

## 📡 트렌드 조사 및 분석

### 1. 직장인 식사 환경의 구조적 변화

**점심값 고공행진과 소비 패턴 변화**

수도권 직장인의 평균 점심 식비는 2017년 대비 약 58% 상승하여 9,500원을 기록했으며,
삼성동 등 주요 업무지구에서는 평균 15,000원에 달하는 것으로 나타났습니다
(NHN페이코 모바일 식권 결제 데이터 기준). 이러한 비용 상승은 직장인들의 점심 선택에
가격 민감도를 높이는 동시에, "한 끼를 제대로 먹겠다"는 가치 소비 경향과 맞물리며
의사결정의 복잡성을 가중시키고 있습니다.

**1인 가구 증가와 혼밥 문화의 일상화**

국가데이터처의 장래가구추계에 따르면, 국내 1인 가구 수는 2025년 처음으로 800만 가구를
돌파하여 815만 6천 가구를 기록했으며, 2026년에는 836만 가구로 늘어날 것으로
전망됩니다. 혼밥에 대한 인식도 2014년의 "쓸쓸하다, 이상하다"에서 2025년에는
"좋다, 즐기다, 편하다"로 크게 전환되었습니다.

**건강·편리미엄 트렌드**

서울대 푸드비즈니스랩 문정훈 교수의 분석에 따르면, 2026년 한국인의 식탁은
'건강'과 '편리미엄(편리함+프리미엄)'이 주도할 것으로 전망됩니다.
덮밥류(+8.2%), 샐러드(+22.2%), 샌드위치(+7.0%), 비빔밥(+13.7%) 등
영양 균형을 맞춘 한 그릇 간편식 메뉴가 두드러진 성장세를 보이고 있습니다.

### 2. 의사결정 피로(Decision Fatigue) 연구 동향

의사결정 피로는 연속된 선택이 이후 판단의 질을 저하시키는 현상으로,
최근 식품 선택 분야에서도 주목받고 있습니다.

- **하루 평균 35,000건의 의사결정**: 성인은 하루에 약 35,000건의 결정을 내리며,
  그중 식사 관련 결정은 약 200~250건에 달합니다 (Pignatiello et al., 2020).
- **오후 판단력 저하**: 판사의 가석방 심사 연구에서, 오전 승인율은 약 65%인 반면
  점심 직전에는 거의 0%까지 떨어졌다가 식후 다시 65%로 회복되는 패턴이
  관찰되었습니다 (Danziger et al., 2011).
- **식사 사전 결정의 효과**: 식사를 미리 결정한 사람들이 업무 집중 시간에
  67% 더 높은 생산성을 보였다는 연구 결과가 보고되었습니다.
- **선택 과부하**: 현대 식품 환경에서 배달 앱과 식당의 과도한 선택지는
  "선택 과부하(Choice Overload)" 상태를 유발하며, 이는 결정 지연이나
  습관적 선택으로 이어집니다.

### 3. 간편식(HMR) 시장과 푸드테크 성장

| 지표 | 수치 | 출처 |
|------|------|------|
| 국내 간편식 시장 규모 (2023) | 약 6.5~7조 원 | 유로모니터 / 농촌경제연구원 |
| 간편식 시장 전망 (2026) | 약 7조 원 | 유로모니터 |
| 국내 간편식 시장 CAGR | 5.23% (2025~2033) | IMARC Group |
| 글로벌 HMR 시장 규모 (2024) | 133.3억 달러 | Business Research Insights |
| 글로벌 HMR 시장 전망 (2033) | 289.4억 달러 (CAGR 11.4%) | Business Research Insights |
| 온라인 식품 시장 규모 (2025) | 약 52조 원 | 서울대 푸드비즈니스랩 |
| 1인 가구 비율 | 전체의 약 42% | 한국농수산식품유통공사(aT) |

AI 기반 메뉴 추천 시스템 도입이 가속화되고 있으며, 배달의민족은 1,900만 건의 빅데이터를
활용하여 외식 트렌드를 분석하고 개인화 추천을 강화하고 있습니다. SNS에서 배달 식사 관련
가장 많이 언급된 키워드는 '칼로리'로, 소비자들이 건강을 의식한 선택을 하고 있음을
보여줍니다.

### 4. 관련 리서치 자료 및 링크

**국내 트렌드 리포트**

| 자료명 | 출처 | 링크 |
|--------|------|------|
| 2025 직장인 점심식사 관련 인식 조사 | 트렌드모니터 | [링크](https://www.trendmonitor.co.kr/tmweb/trend/allTrend/detail.do?bIdx=3320&code=0302&trendType=CKOREA) |
| 2024 직장인 점심식사 및 구내식당 조사 | 트렌드모니터 | [링크](https://www.trendmonitor.co.kr/tmweb/trend/allTrend/detail.do?bIdx=2622&code=0402&trendType=CKOREA) |
| 푸드 트렌드 2026: 건강·편리미엄 주도 | 식품음료신문 | [링크](https://www.thinkfood.co.kr/news/articleView.html?idxno=103743) |
| 2026 외식 트렌드: 자기만족 건강식 | 식품외식경제 | [링크](https://www.foodbank.co.kr/news/articleView.html?idxno=67253) |
| 2025-2026 식품 소비 트렌드 | 푸드아이콘 | [링크](https://www.foodicon.co.kr/news/articleView.html?idxno=31955) |
| 2026 외식 트렌드: 경력상품·집밥경제 | 삼성웰스토리 | [링크](https://www.story-w.co.kr/story-w/3679/kfood_trend_product) |

**의사결정 피로 학술 연구**

| 자료명 | 출처 | 링크 |
|--------|------|------|
| Decision Fatigue: A Conceptual Analysis | PMC / J Health Psychol | [링크](https://pmc.ncbi.nlm.nih.gov/articles/PMC6119549/) |
| The Effect of Decision Fatigue on Food Choices | PMC (2025) | [링크](https://pmc.ncbi.nlm.nih.gov/articles/PMC12736114/) |
| Multi-domain Conceptual Framework for Decision Fatigue | Frontiers in Cognition | [링크](https://www.frontiersin.org/journals/cognition/articles/10.3389/fcogn.2025.1719312/full) |
| Decision Fatigue and Productivity Impact | Global Council for Behavioral Science | [링크](https://gc-bs.org/articles/the-cognitive-toll-deconstructing-decision-fatigue-and-its-pervasive-impact-on-productivity-and-morality/) |

**공공데이터 및 API**

| 자료명 | 출처 | 링크 |
|--------|------|------|
| 공공데이터포털 (통합) | 행정안전부 | [링크](https://www.data.go.kr/) |
| 서울 열린데이터광장 | 서울특별시 | [링크](https://data.seoul.go.kr/) |
| 식품영양성분 데이터베이스 Open API | 식품안전나라 | [링크](https://various.foodsafetykorea.go.kr/nutrient/industry/openApi/info.do) |
| 한국 서비스 Public API 모음 (2026) | GitHub (yybmion) | [링크](https://github.com/yybmion/public-apis-4Kr) |

---

## 📦 수집할 데이터 및 활용 모델

### 1. 수집할 데이터 상세

#### 소주제 1: 주변 음식점 데이터

| 항목 | 상세 |
|------|------|
| **수집 데이터** | 음식점명, GPS 좌표(위도/경도), 카테고리(한식/일식/양식 등), 도보 거리(m), 평균 평점, 리뷰 수, 가격대, 영업시간, 대표 메뉴 |
| **데이터 출처** | 카카오 로컬 API (`/v2/local/search/keyword`), 네이버 지도 검색 API |
| **갱신 주기** | 1일 1회 (영업시간 변동 반영) |
| **데이터 형식** | JSON (REST API 응답) |
| **예상 데이터 규모** | 사무실 반경 500m 기준 약 50~200건 |

#### 소주제 2: 날씨 및 대기질 데이터

| 항목 | 상세 |
|------|------|
| **수집 데이터** | 기온(°C), 습도(%), 강수확률(%), 하늘상태(맑음/구름/흐림/비), 풍속(m/s), 미세먼지(PM10), 초미세먼지(PM2.5), 대기질 등급 |
| **데이터 출처** | 기상청 단기예보 API (`getVilageFcst`), 에어코리아 대기질 API (`getMsrstnAcctoRltmMesureDnsty`) |
| **갱신 주기** | 1시간 1회 (단기예보 기준) |
| **데이터 형식** | XML/JSON (공공데이터포털 REST API) |
| **예상 데이터 규모** | 시간당 약 20~30개 필드 |

#### 소주제 3: 식품 영양성분 데이터

| 항목 | 상세 |
|------|------|
| **수집 데이터** | 식품명, 1회 제공량(g), 열량(kcal), 탄수화물(g), 단백질(g), 지방(g), 나트륨(mg), 당류(g), 포화지방(g), 식이섬유(g) |
| **데이터 출처** | 식품안전나라 영양성분 DB API (`/openapi/service`), 식품의약품안전처 식품영양성분 데이터셋 (CSV) |
| **갱신 주기** | 월 1회 (DB 업데이트 반영) |
| **데이터 형식** | JSON/CSV |
| **예상 데이터 규모** | 약 5,000~10,000건 (주요 외식 메뉴 기준) |

#### 소주제 4: 사용자 행동 데이터

| 항목 | 상세 |
|------|------|
| **수집 데이터** | 팀원 투표 기록, 개인 선호 카테고리, 방문 이력(일시/음식점/메뉴), 만족도 평가(1~5점), 알레르기/비선호 식재료 |
| **데이터 출처** | 자체 애플리케이션 내부 DB (사용자 직접 입력) |
| **갱신 주기** | 실시간 (이벤트 기반) |
| **데이터 형식** | 관계형 DB (SQLite/PostgreSQL) |
| **예상 데이터 규모** | 팀 5명 기준, 일 5건 × 250 영업일 = 연 6,250건 |

### 2. 데이터 출처 종합

```
┌──────────────────────────────────────────────────────────────────────┐
│                        외부 공공/민간 API                             │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ 카카오맵 API │  │ 기상청 API  │  │식품안전나라  │                  │
│  │ (REST/JSON) │  │ (REST/XML)  │  │  API (JSON) │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
│         │                │                │                          │
│         ▼                ▼                ▼                          │
│  ┌─────────────────────────────────────────────┐                     │
│  │         Python ETL 스크립트 (수집/정제)       │                     │
│  └──────────────────────┬──────────────────────┘                     │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────┐                     │
│  │       SQLite / PostgreSQL (통합 저장소)       │                     │
│  └──────────────────────┬──────────────────────┘                     │
│                         │                                            │
│         ┌───────────────┼───────────────┐                            │
│         ▼               ▼               ▼                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                     │
│  │ React 대시  │  │ FastAPI    │  │ Streamlit  │                     │
│  │  보드 (SPA) │  │ REST 서버  │  │ 분석 대시보드│                     │
│  └────────────┘  └────────────┘  └────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 3. 활용 모델 및 기술 정의

#### 추천 알고리즘

| 모델/기법 | 적용 영역 | 설명 |
|----------|----------|------|
| **가중 점수 모델 (Weighted Scoring)** | 통합 추천 엔진 | 거리(0.3) + 날씨(0.2) + 영양(0.2) + 팀선호(0.3)의 가중합으로 종합 점수 산출. 가중치는 사용자 피드백을 반영하여 동적 조정 가능 |
| **규칙 기반 매칭 (Rule-Based)** | 날씨-메뉴 매칭 | 기온·강수·미세먼지 조건에 따른 if-then 규칙으로 메뉴 유형별 적합도 산출. 예: 기온 < 10°C → 국물류 가산 |
| **협업 필터링 (Collaborative Filtering)** | 팀 선호도 예측 (Phase 3) | 팀원 간 투표 이력의 유사도를 기반으로 미투표 팀원의 선호를 예측. User-User CF 방식 적용 |
| **콘텐츠 기반 필터링 (Content-Based)** | 개인 메뉴 추천 (Phase 3) | 사용자의 과거 선택 메뉴의 영양 프로필·카테고리를 벡터화하여 유사 메뉴 추천 |

#### 데이터 처리 기술

| 기술 | 적용 영역 | 설명 |
|------|----------|------|
| **ETL Pipeline** | 데이터 수집 전체 | Python 기반 Extract-Transform-Load. requests로 API 호출, pandas로 정제, SQLAlchemy로 적재 |
| **스케줄링 (APScheduler)** | 자동 데이터 갱신 | cron 표현식 기반 주기적 API 호출 스케줄링. 날씨는 1시간, 음식점은 1일 주기 |
| **이상치 탐지 (Z-Score)** | 영양 데이터 검증 | 영양성분 값의 이상치를 Z-Score 기반으로 탐지하여 잘못된 데이터 필터링 |
| **데이터 캐싱 (Redis)** | API 응답 캐싱 (Phase 3) | 동일 조건 API 호출 결과를 캐싱하여 응답 속도 향상 및 호출 제한 관리 |

#### 시각화 기술

| 기술 | 차트 유형 | 적용 탭 |
|------|----------|---------|
| **Recharts (React)** | Radar Chart | 음식점 5축 분석 (거리/날씨/영양/평점/가격) |
| **Recharts (React)** | Area Chart + Line | 주간 칼로리 추이 + 목표선 |
| **Recharts (React)** | Donut Chart (Pie) | 탄·단·지 비율 시각화 |
| **Recharts (React)** | Horizontal Bar | 메뉴 유형별 날씨 적합도, 투표 결과 |
| **Recharts (React)** | Grouped Bar | 일별 영양소 섭취 비교 |

#### DB 스키마 (핵심 테이블)

```sql
-- 음식점 마스터
restaurants (id, name, category, lat, lng, distance_m, rating, price_avg, menu_type, indoor)

-- 날씨 로그
weather_logs (id, timestamp, temp, humidity, rain_prob, sky, pm10, pm25)

-- 영양 정보
nutrition_info (id, food_name, serving_g, calories, protein, carbs, fat, sodium)

-- 식사 기록
meal_history (id, user_id, restaurant_id, meal_date, menu, satisfaction, calories, protein, carbs, fat)

-- 팀 투표
team_votes (id, vote_date, user_id, restaurant_id, created_at)

-- 사용자
users (id, name, team_id, allergy, dislike_categories)
```

---

## 🏗️ 시스템 아키텍처

### 전체 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES (수집)                        │
├────────────┬────────────┬────────────────┬──────────────────────┤
│ 카카오맵    │ 기상청     │ 식품안전나라    │ 사용자 입력           │
│ /네이버 API │ 날씨 API   │ 영양성분 API   │ 투표/선호도           │
└─────┬──────┴─────┬──────┴───────┬────────┴──────────┬───────────┘
      │            │              │                   │
      ▼            ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ETL (변환/정제)                          │
├────────────┬────────────┬────────────────┬──────────────────────┤
│ 거리/평점   │ 환경 점수   │ 영양소 매핑    │ 선호도 집계           │
│ 필터링     │ 산출        │               │                      │
└─────┬──────┴─────┬──────┴───────┬────────┴──────────┬───────────┘
      │            │              │                   │
      ▼            ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    통합 추천 엔진 (Integration)                  │
│  종합점수 = 거리(0.3) + 날씨(0.2) + 영양(0.2) + 팀선호(0.3)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ SQLite/PostgreSQL│
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DASHBOARD (시각화/인터랙션)                      │
├────────────┬────────────┬────────────────┬──────────────────────┤
│ 🍽️ 음식점   │ 🌤️ 날씨    │ 📊 영양       │ 🗳️ 팀 투표           │
│ 탐색       │ 추천        │ 리포트         │                      │
└────────────┴────────────┴────────────────┴──────────────────────┘
```

### 대주제 및 4개 소주제

| # | 소주제 | 데이터 소스 | 핵심 기능 |
|---|--------|------------|----------|
| 1 | **주변 음식점 데이터 수집** | 카카오맵 / 네이버 지도 API | 반경 내 음식점 검색, 카테고리·거리·평점 기반 필터링 |
| 2 | **날씨 연동 메뉴 추천** | 기상청 단기예보 API, 에어코리아 API | 기온·미세먼지·강수확률에 따른 메뉴 유형 매칭 |
| 3 | **영양 균형 분석** | 식품안전나라 영양성분 DB API | 주간 탄·단·지 비율 트래킹, 영양 밸런스 진단 |
| 4 | **팀 투표 & 히스토리 관리** | 사용자 입력 (내부 DB) | 실시간 투표, 중복 방문 방지, 선호도 학습 |

---

## 🧮 핵심 알고리즘

### 가중 점수 모델 (Weighted Scoring Model)

각 음식점에 대해 4개 축의 점수를 산출하고, 가중합으로 최종 추천 점수를 계산합니다.

```
종합점수 = (거리점수 × 0.3) + (날씨적합도 × 0.2) + (영양균형 × 0.2) + (팀선호도 × 0.3)
```

#### 1. 거리 점수 (Distance Score)

| 거리 | 점수 |
|------|------|
| ~100m | 100 |
| ~200m | 85 |
| ~300m | 70 |
| ~400m | 50 |
| 400m~ | 30 |

#### 2. 날씨 적합도 (Weather Fitness)

기본 50점에서 조건 매칭 시 가산하는 방식입니다.

- 기온 < 10°C + 국물/죽 메뉴 → +30
- 기온 > 28°C + 면류/초밥 메뉴 → +25
- 미세먼지 "나쁨" + 실내 식당 → +15
- 강수확률 > 50% + 200m 이내 → +20

#### 3. 영양 균형 점수 (Nutrition Balance)

이번 주 섭취 이력 기반으로 부족한 영양소를 보충하는 메뉴에 가산합니다.

- 평균 단백질 < 25g + 고단백 메뉴(30g+) → +20
- 평균 지방 > 30g + 저지방 메뉴(15g-) → +20
- 적정 칼로리 범위(400~700kcal) → +10

#### 4. 팀 선호도 (Team Preference)

팀원 투표 수에 비례하여 점수를 부여합니다.

```
팀선호 점수 = min(투표수 × 25 + 25, 100)
```

---

## 📊 대시보드 기능 상세

### 탭 1: 🍽️ 음식점 탐색

- 카테고리 필터(한식/일식/양식/동남아)
- 종합 점수 기반 랭킹 리스트
- 음식점 선택 시 5축 레이더 차트(거리/날씨/영양/평점/가격) 상세 분석
- 방문 이력 및 최근 방문일 표시

### 탭 2: 🌤️ 날씨 추천

- 오늘의 기상 정보 요약(기온/습도/미세먼지/하늘상태/강수확률)
- 날씨 기반 맞춤 팁 자동 생성
- 메뉴 유형별 날씨 적합도 수평 바 차트
- 오늘 날씨 TOP 5 추천 리스트

### 탭 3: 📊 영양 리포트

- 주간 칼로리 추이 (Area Chart + 목표선)
- 탄수화물·단백질·지방 비율 (Donut Chart)
- 일별 영양소 섭취량 (Grouped Bar Chart)
- 영양 밸런스 자동 진단 (단백질 부족/과다/균형 양호)

### 탭 4: 🗳️ 팀 투표

- 팀원별 투표 인터페이스
- 랜덤 시뮬레이션 버튼
- 실시간 투표 현황 바 차트
- 결과 확정 시 "오늘의 점심" 배너 표시
- 최근 방문 기록 히스토리

---

## 🛠️ 기술 스택

### Frontend (대시보드)

| 기술 | 용도 |
|------|------|
| **React 18** | SPA 프레임워크 |
| **Recharts** | 데이터 시각화 (Area, Bar, Radar, Pie Chart) |
| **Tailwind CSS** | 유틸리티 기반 스타일링 |

### Backend (파이프라인) — 확장 시

| 기술 | 용도 |
|------|------|
| **Python 3.10+** | 데이터 수집 및 ETL 스크립트 |
| **FastAPI** | REST API 서버 |
| **SQLite / PostgreSQL** | 데이터 저장소 |
| **APScheduler** | 주기적 데이터 수집 스케줄링 |

### NLP 레이어 (Phase 5~6)

| 기술 | 용도 |
|------|------|
| **Transformers (Hugging Face)** | 한국어 사전학습 모델 로딩 |
| **KcELECTRA** (`nlp04/...`) | A1 리뷰 감성분석 (Zero-shot) |
| **Sentence-BERT** (`jhgan/ko-sroberta-multitask`) | B1 메뉴명 임베딩 매칭 |
| **python-Levenshtein** | B1 편집거리 기반 후보 검색 |
| **ChromaDB** | D3 RAG 벡터 데이터베이스 (로컬 · 메타데이터 필터) |
| **Ollama** (`qwen2.5:7b-instruct`) | D3 챗봇 / D5 NLG 리포트 로컬 LLM |
| **Streamlit** | D3 챗봇 데모 UI |
| **KoELECTRA + CRF** (Phase 6) | B2 Food NER (재료·알레르겐) |
| **DistilKoBERT** (Phase 6) | D1+D2 JointBERT (Intent + Slot) |
| **FAISS** (Phase 6) | E1 개인화 CF 유사도 인덱스 |

### 외부 API

| API | 제공처 | 용도 |
|-----|--------|------|
| 카카오 로컬 API | Kakao Developers | 주변 음식점 검색 |
| 기상청 단기예보 API | 공공데이터포털 | 날씨 정보 |
| 에어코리아 API | 공공데이터포털 | 미세먼지 정보 |
| 식품영양성분 DB API | 식품안전나라 | 메뉴별 영양성분 |

---

## 📁 프로젝트 구조

```
lunch-optimizer/
├── README.md                    # 프로젝트 설명서 (현재 파일)
├── dashboard/
│   ├── lunch-optimizer-dashboard.jsx   # React 대시보드 메인
│   ├── package.json
│   └── public/
├── pipeline/
│   ├── collectors/
│   │   ├── restaurant_collector.py    # 음식점 데이터 수집
│   │   ├── weather_collector.py       # 날씨 데이터 수집
│   │   ├── nutrition_collector.py     # 영양성분 데이터 수집
│   │   └── vote_collector.py          # 투표 데이터 수집
│   ├── transformers/
│   │   ├── distance_scorer.py         # 거리 점수 산출
│   │   ├── weather_scorer.py          # 날씨 적합도 산출
│   │   ├── nutrition_scorer.py        # 영양 균형 점수 산출
│   │   └── team_scorer.py             # 팀 선호도 점수 산출
│   ├── engine/
│   │   └── recommender.py             # 통합 추천 엔진
│   └── scheduler.py                   # 파이프라인 스케줄러
├── database/
│   ├── schema.sql                     # DB 스키마 정의
│   └── seed_data.sql                  # 초기 시드 데이터
├── api/
│   └── main.py                        # FastAPI 서버
├── docs/
│   ├── architecture.md                # 아키텍처 상세 문서
│   └── api-spec.md                    # API 명세서
├── tests/
│   ├── test_collectors.py
│   ├── test_scorers.py
│   └── test_recommender.py
├── GUIDE/                             # 🧩 4개 서브토픽 Claude Code 구현 가이드
├── ChatBOT/                           # 🤖 Ollama 기반 대화형 확장 가이드 (Phase1~4)
├── NLP/                               # 🧠 자연어 처리 확장 레이어 (Phase 5~6)
│   ├── README.md                          # NLP 레이어 진입점
│   ├── GUIDE_NLP_MVP_SCENARIO3.md         # 4주 전체 요약
│   ├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md   # 1주차 A1 감성분석 상세
│   ├── GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md  # 2주차 B1 메뉴 정규화
│   ├── GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md # 3주차 D3 RAG 챗봇
│   ├── GUIDE_NLP_MVP_STEP4_NLG_REPORT.md  # 4주차 D5 NLG 리포트
│   ├── GUIDE_NLP_RESEARCH_SCENARIO2.md    # 시나리오 2 (연구 · 10주)
│   └── nlp_mvp/                           # 구현 스켈레톤 (sentiment, menu_normalizer,
│                                          #   rag_chatbot, nlg_report, shared, api)
└── .env.example                       # 환경변수 템플릿
```

---

## 🚀 시작하기

### 사전 요구사항

- Node.js 18+ / npm 9+
- Python 3.10+ (백엔드 확장 시)
- 공공데이터포털 API 인증키

### 1. 대시보드 실행 (React)

```bash
# 저장소 클론
git clone https://github.com/your-repo/lunch-optimizer.git
cd lunch-optimizer/dashboard

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 2. 파이프라인 실행 (Python, 확장 시)

```bash
cd lunch-optimizer/pipeline

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp ../.env.example ../.env
# .env 파일에 API 키 입력

# 파이프라인 실행
python scheduler.py
```

### 3. 환경변수 설정

```env
# .env.example
KAKAO_REST_API_KEY=your_kakao_api_key
DATA_GO_KR_API_KEY=your_public_data_api_key
FOOD_SAFETY_API_KEY=your_food_safety_api_key
DB_URL=sqlite:///lunch_optimizer.db
OFFICE_LAT=37.5665      # 사무실 위도
OFFICE_LNG=126.9780     # 사무실 경도
SEARCH_RADIUS=500        # 검색 반경 (미터)
```

---

## 📈 기대 효과 및 활용 시나리오

### 정량적 효과

| 지표 | 기존 | 개선 후 |
|------|------|---------|
| 점심 메뉴 결정 시간 | 평균 15분 | 평균 3분 |
| 같은 음식점 재방문율 | 70% | 40% |
| 주간 영양 균형 인지율 | 10% | 80% |
| 팀 식사 합의 소요시간 | 평균 20분 | 평균 5분 |

### 활용 시나리오

- **중소기업 사내 복지 도구**: 직원 식사 만족도 향상 및 건강 관리
- **공유 오피스 커뮤니티**: 입주사 간 점심 네트워킹 촉진
- **건강관리 앱 연동**: 개인 식단 데이터 기반 맞춤 추천 확장
- **프랜차이즈 본사 분석**: 상권 내 직장인 메뉴 선호도 트렌드 파악
- **지자체 상권 분석**: 점심 시간대 유동인구 기반 소상공인 지원 정책 수립

---

## 🗺️ 로드맵

### Phase 1 — MVP (현재)
- [x] 파이프라인 아키텍처 설계
- [x] React 대시보드 프로토타입 (Mock 데이터)
- [x] 4개 탭 UI 구현
- [x] 가중 점수 알고리즘 구현

### Phase 2 — API 연동
- [ ] 카카오맵 API 실시간 연동
- [ ] 기상청 단기예보 API 연동
- [ ] 식품안전나라 영양성분 API 연동
- [ ] SQLite 데이터 영속화

### Phase 3 — 고도화
- [ ] 사용자 로그인 및 프로필 관리
- [ ] 머신러닝 기반 개인 선호도 학습
- [ ] Slack/Teams 봇 연동 (투표 알림)
- [ ] 모바일 반응형 최적화

### Phase 4 — 배포
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인 구축
- [ ] Streamlit 버전 병행 개발 (데이터 분석가용)
- [ ] 사용자 피드백 루프 구현

### 🎯 역할 분리 (2026-04-08 결정)
> **NLP = 메인 언어 처리 축 · ChatBOT = 선택적 추가 기능 (React 전용)**
> 상세: [`ROLE_SEPARATION_DECISION.md`](./ROLE_SEPARATION_DECISION.md)

### Phase 5 — 🎯 NLP 레이어 / 시나리오 3 (MVP, 4주) — **메인**
> **진입점:** [`NLP/README.md`](./NLP/README.md)
> **전체 요약:** [`NLP/GUIDE_NLP_MVP_SCENARIO3.md`](./NLP/GUIDE_NLP_MVP_SCENARIO3.md)

정형 데이터 기반 추천 엔진 위에 **자연어 이해·생성 레이어**를 추가하여, 리뷰 텍스트의
질적 평가·메뉴명 정규화·대화형 상담·자연어 리포트를 제공합니다.

- [x] **Step 0** 공용 유틸 (`shared/db.py`, `logger.py`, `ollama_client.py`) — [구현 완료](./NLP/nlp_mvp/shared/)
- [ ] **Step 1 / 1주차** A1 리뷰 감성분석 (KcELECTRA Zero-shot) · [`STEP1_SENTIMENT.md`](./NLP/GUIDE_NLP_MVP_STEP1_SENTIMENT.md)
  - `restaurants.sentiment_score` 컬럼으로 평점 보정
- [ ] **Step 2 / 2주차** B1 메뉴명 정규화 (규칙 + Levenshtein + Sentence-BERT) · [`STEP2_MENU_NORMALIZER.md`](./NLP/GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md)
  - 영양 DB 조인율 40% → 85%
- [ ] **Step 3 / 3주차** D3 RAG 영양 상담 챗봇 (ChromaDB + Ollama Qwen2.5) · [`STEP3_RAG_CHATBOT.md`](./NLP/GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md)
  - Streamlit 채팅 UI + 환각 방지 3중 방어
- [ ] **Step 4 / 4주차** D5 NLG 주간 영양 리포트 (수치 → 자연어) · [`STEP4_NLG_REPORT.md`](./NLP/GUIDE_NLP_MVP_STEP4_NLG_REPORT.md)
  - 하이브리드 (규칙 팩트 + LLM 생성) + 템플릿 fallback
- [ ] **Step 5 통합** — FastAPI `/nlp/*` 라우터 + React 대시보드 확장
  - 감성 뱃지, AI 코멘트 카드, AI 상담 탭

### Phase 6 — NLP 레이어 / 시나리오 2 (연구·심화, 10주)
> 상세: [`NLP/GUIDE_NLP_RESEARCH_SCENARIO2.md`](./NLP/GUIDE_NLP_RESEARCH_SCENARIO2.md)

MVP 위에 **자체 학습 NLP 모델 5종**을 얹어 파인튜닝·NER·임베딩·개인화 CF 를 증명합니다.

- [ ] **A2** ABSA — 맛/가격/서비스/청결 속성별 감성 파인튜닝 (BERT-SPC)
- [ ] **B2** Food NER — 재료·조리법·맛·알레르겐 개체 인식 (KoELECTRA + CRF)
- [ ] **D1 + D2** JointBERT — Intent/Slot 통합 분류기 (DistilKoBERT)
- [ ] **E1** 임베딩 기반 개인화 CF (Sentence-BERT + FAISS)
- [ ] Before/After 벤치마크 리포트 + 논문 초안 (IEEE 스타일)

### Phase 7 — ⚡ ChatBOT Function Calling 레이어 (선택, React 전용)
> 상세: [`ChatBOT/GUIDE_CHATBOT_INTEGRATION.md`](./ChatBOT/GUIDE_CHATBOT_INTEGRATION.md)

NLP MVP 완성 후 선택적 추가 기능으로, lunch-optimizer 28 엔드포인트를 LLM Tool 로 래핑.
⚠️ **Streamlit 경로 폐기 · React + FastAPI 만** 사용.

- [ ] **Phase 1** — Track B (React + FastAPI) 만 구현, Streamlit 스킵
- [ ] **Phase 2** — 8 Tool Functions (투표·식사기록·거부권 등 행동 실행 중심)
- [ ] **Phase 3** — 멀티턴 · 대명사 해석 · 사용자 프로필
- [ ] **Phase 4** — Docker Compose 통합 배포 (NLP + ChatBOT + lunch-optimizer)
- [ ] React 대시보드 "💬 AI 상담" 탭 추가 — NLP D3 RAG 챗봇 + ChatBOT Tool 결합

---

## 🤝 기여 방법

1. 이 저장소를 Fork합니다.
2. 기능 브랜치를 생성합니다. (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다. (`git commit -m 'feat: add amazing feature'`)
4. 브랜치에 Push합니다. (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다.

### 커밋 컨벤션

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드 추가
chore: 빌드/설정 변경
```

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 📞 문의

프로젝트에 대한 질문이나 제안이 있다면 Issues 탭을 이용해주세요.

---

<div align="center">

**🍱 점심 고민, 이제 데이터에게 맡기세요.**

*Built with data, served with love.*

</div>
