# 📦 Phase 1 구현 가이드 — 데이터 파이프라인 구축 with Claude Code

> **목표**: 공공데이터 5종을 수집·정제하여 Phase 2~4가 즉시 사용할 수 있는 표준 CSV/JSON으로 저장한다.
> **실제 작업 시간**: 약 2시간 (데이터 엔지니어 기준)
> **대상 독자**: 데이터 엔지니어(주) + 나머지 팀원(병렬 작업)
> **전제 조건**: [Phase 0 가이드](./PHASE0_GUIDE.md) 완료, 최소 TourAPI 키 발급 (또는 승인 대기 중)

---

## 🎯 0. Phase 1 개요

### 완료 조건 (4가지 모두 참이어야 함)
1. ✅ `data/` 디렉토리에 **5종 데이터 파일**이 모두 존재
2. ✅ `scripts/validate_data.py` 실행 시 **모든 검증 통과**
3. ✅ `python -c "from src.data_loader import load_all_data; load_all_data()"` **에러 없음**
4. ✅ Phase 2~4 담당자가 더미 또는 실제 데이터로 **코딩 시작 가능**

### 이 Phase에서 산출되는 파일

```
data/
├── kbo_schedule_2026.csv         # 720경기
├── stadiums.csv                   # 10개 구장
├── team_stats_10yr.csv            # 팀별 과거 10년 승률
├── poi_cache/
│   ├── 잠실_food.json             # 경기장별 × 카테고리별
│   ├── 잠실_stay.json
│   ├── 잠실_tour.json
│   └── ... (총 30개 JSON)
└── weather_cache/                 # 실시간 API라 Phase 1엔 빈 디렉토리만

src/
├── data_loader.py                 # 통합 로더
└── api/
    ├── tour_api.py                # TourAPI 클라이언트
    └── weather_api.py             # 기상청 클라이언트

scripts/
├── seed_dummy_data.py             # 더미 데이터 생성
├── fetch_kbo_schedule.py          # KBO 일정 수집
├── cache_poi.py                   # TourAPI 일괄 캐싱
└── validate_data.py               # 품질 검증
```

### 작업 순서 맵

```
 [Step 1. 데이터 스키마 합의] ──┐
                              │
 [Step 2. 더미 데이터 생성] ──┴──► 🚀 Phase 2~4 병렬 착수 가능
                              │
 [Step 3. 구장 좌표] ──────────┤  (15분, 수기 하드코딩)
                              │
 [Step 4. KBO 경기일정] ──────┤  (30분, 3단 폴백 전략)
                              │
 [Step 5. 팀 전적] ────────────┤  (30분)
                              │
 [Step 6. TourAPI 클라이언트] ─┤  (30분, 핵심 모듈)
                              │
 [Step 7. 기상청 클라이언트] ──┤  (15분)
                              │
 [Step 8. 통합 로더] ──────────┤
                              ▼
 [Step 9. 검증 스크립트] ─────► ✅ Phase 1 완료
```

---

## 📋 1. Step 1. 데이터 스키마 합의 — **가장 먼저!**

### 왜 먼저 하나
Phase 2~4 담당자들이 이 스키마를 보고 뼈대 코드를 병렬로 작성합니다. **스키마가 중간에 바뀌면 Phase 2~4 전체가 리팩토링 대상**이 되므로, Step 1에서 팀 전체가 합의하고 Git에 먼저 커밋해야 합니다.

### 데이터 계약 (Data Contract)

#### 1-1. `kbo_schedule_2026.csv`
```
컬럼                  타입         예시               설명
-----------------------------------------------------------------
game_id              str         20260328_LG_KT     YYYYMMDD_AWAY_HOME
date                 date        2026-03-28         ISO 8601 형식
day_of_week          str         토                  한글 1자
home_team            str         KT                 약칭 표준 (아래 참조)
away_team            str         LG                 약칭 표준
stadium              str         수원                구장 도시명
start_time           str         14:00              HH:MM (24시간)
broadcast            str         SBS                지상파/케이블 (결측 OK)
```

**팀 약칭 표준** (반드시 이 10개로 통일):
`LG, KT, SSG, 두산, KIA, NC, 삼성, 롯데, 한화, 키움`

#### 1-2. `stadiums.csv`
```
컬럼                타입     예시              설명
--------------------------------------------------
stadium_name       str      잠실야구장        풀네임
short_name         str      잠실              경기일정 CSV의 stadium과 매칭되는 키
home_team          str      LG,두산          복수 팀이면 쉼표 구분
city               str      서울              광역시/도 단위
address            str      서울특별시 송파구 올림픽로 25
lat                float    37.5122
lng                float    127.0719
capacity           int      25000
subway_station     str      잠실(2호선,8호선)
```

#### 1-3. `team_stats_10yr.csv`
```
컬럼                  타입     예시        설명
-----------------------------------------------
year                 int      2025       시즌 연도
team                 str      LG         팀 약칭
games_played         int      144
wins                 int      81
losses               int      58
draws                int      5
win_rate             float    0.583
home_win_rate        float    0.611
away_win_rate        float    0.555
final_rank           int      1
```

#### 1-4. `poi_cache/{stadium}_{category}.json`
```json
[
  {
    "content_id": "126508",
    "title": "롯데월드",
    "category": "tour",
    "addr": "서울특별시 송파구 올림픽로 240",
    "lat": 37.5112,
    "lng": 127.0981,
    "tel": "02-411-2000",
    "first_image": "http://tong.visitkorea.or.kr/...",
    "dist_m": 520,
    "stadium": "잠실"
  }
]
```

카테고리 값: `food` (음식점), `stay` (숙박), `tour` (관광지)

#### 1-5. 기상청 응답 (런타임만, CSV 저장 안 함)
```python
# src/api/weather_api.py의 get_forecast()가 반환할 dict
{
    "date": "2026-04-19",
    "sky": "맑음",              # 맑음/구름많음/흐림
    "precipitation_prob": 20,   # 0~100
    "temp_min": 8,
    "temp_max": 18,
    "rain_expected": False,
}
```

### 🤖 Claude Code 프롬프트

````
data/SCHEMA.md 파일을 만들어서 PHASE1_GUIDE.md의 "Step 1. 데이터 스키마 합의"
섹션을 그대로 복사해 저장해줘. 이 파일은 팀 전체의 데이터 계약 문서 역할을 해.

그리고 src/config.py를 만들어서 다음 상수를 정의해줘:

# 팀 약칭 목록
TEAMS = ["LG", "KT", "SSG", "두산", "KIA", "NC", "삼성", "롯데", "한화", "키움"]

# TourAPI content_type 매핑
CONTENT_TYPE = {
    "tour": 12,    # 관광지
    "stay": 32,    # 숙박
    "food": 39,    # 음식점
}

# 데이터 파일 경로
from pathlib import Path
DATA_DIR = Path(__file__).parent.parent / "data"
POI_CACHE_DIR = DATA_DIR / "poi_cache"

# API 엔드포인트
TOUR_API_BASE = "http://apis.data.go.kr/B551011/KorService1"
WEATHER_API_BASE = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"

모든 상수에 주석으로 용도를 간단히 설명해줘.
````

### 검증
```bash
ls data/SCHEMA.md && cat src/config.py | grep TEAMS
```

### 커밋
```bash
git add data/SCHEMA.md src/config.py
git commit -m "docs(phase-1): define data schema contract"
git push origin main
```

> 👥 **팀 전체에 알림**: 이 커밋 후 팀원 전원이 `git pull` 해서 스키마를 공유받아야 합니다. Phase 2~4 담당자는 이 스키마로 뼈대 작업 시작 가능.

---

## 🌱 2. Step 2. 더미 데이터 선행 생성 — **Phase 2~4 블록 해제의 열쇠**

### 목표
실제 데이터 수집이 시간이 걸리는 동안, 현실적 규모의 **가짜 CSV를 먼저 만들어** 다른 팀원이 즉시 개발을 시작할 수 있게 한다. 나중에 같은 스키마로 실제 데이터로 교체.

### 🤖 Claude Code 프롬프트

````
scripts/seed_dummy_data.py를 만들어줘. 이 스크립트는 data/ 디렉토리 안에
스키마를 준수하는 더미 CSV 3종과 더미 POI JSON을 생성해. 요구사항:

1. `seed_schedule()` 함수:
   - 2026-03-28부터 2026-09-30까지 매일 5경기 생성 (월요일 제외)
   - 10개 팀을 랜덤 조합
   - start_time은 평일 18:30, 주말 14:00/17:00/18:00 중 랜덤
   - stadium은 home_team에 따라 결정 (stadium_name → short_name 매핑)
   - 720경기 내외로 생성되어야 함
   - data/kbo_schedule_2026.csv로 저장

2. `seed_stadiums()` 함수:
   - 10개 구장 실제 데이터를 하드코딩:
     잠실(LG,두산,서울,37.5122,127.0719,25000)
     고척(키움,서울,37.4982,126.8670,16744)
     문학(SSG,인천,37.4371,126.6932,23000)
     수원(KT,수원,37.2997,127.0097,20000)
     대전(한화,대전,36.3171,127.4293,13000)
     대구(삼성,대구,35.8411,128.6816,24000)
     광주(KIA,광주,35.1683,126.8889,20500)
     창원(NC,창원,35.2222,128.5820,22112)
     사직(롯데,부산,35.1940,129.0611,22990)
     한밭(한화 보조,대전,36.3262,127.4171,9000)
   - data/stadiums.csv로 저장

3. `seed_team_stats()` 함수:
   - 2015~2025년 × 10팀 = 110행
   - win_rate는 0.35~0.65 사이 랜덤
   - home_win_rate = win_rate + 랜덤(0.02~0.08) (홈 우위 반영)
   - away_win_rate = win_rate - 랜덤(0.02~0.08)
   - final_rank는 연도 내 win_rate 순으로 1~10
   - data/team_stats_10yr.csv로 저장

4. `seed_poi_cache()` 함수:
   - 10개 구장 × 3개 카테고리 = 30개 JSON 파일
   - 각 파일에 더미 POI 20~30개
   - content_id, title, category는 반드시 현실적인 한국어 이름
   - lat/lng은 구장 좌표 ± 0.02 (약 2km 반경) 랜덤
   - data/poi_cache/{short_name}_{category}.json

5. 모든 랜덤은 random.seed(42) 고정해서 재현 가능하게

6. 스크립트 끝에 `if __name__ == "__main__":` 블록으로
   4개 함수를 순서대로 실행하고 결과 요약 print

마지막에 python scripts/seed_dummy_data.py 실행해서 결과 보여줘.
````

### 검증
```bash
python scripts/seed_dummy_data.py

# 출력 예시:
# ✅ 720 games → data/kbo_schedule_2026.csv
# ✅ 10 stadiums → data/stadiums.csv
# ✅ 110 team stats → data/team_stats_10yr.csv
# ✅ 30 POI cache files in data/poi_cache/

ls data/*.csv
ls data/poi_cache/ | wc -l   # 30
```

### 🚀 팀원 전원 알림 타이밍

이 Step 완료 직후 Slack/Discord에 공유:

> "더미 데이터 생성 완료! `git pull` 해서 `data/` 받아가세요. Phase 2~4 담당자는 이 데이터로 바로 작업 시작 가능합니다. 실제 데이터는 곧 교체됩니다."

---

## 🏟️ 3. Step 3. 구장 좌표 데이터 확정 (15분)

### 목표
Step 2에서 더미로 만든 `stadiums.csv`를 **실제 좌표와 정보로 수기 보정**한다.

### 실행 방법
더미 데이터의 구장 정보는 이미 정확한 값으로 하드코딩되어 있지만, 다음 항목만 수기 추가:

1. `address` 컬럼 — 카카오맵에서 각 구장 정확한 도로명 주소 복사
2. `subway_station` 컬럼 — 지하철 노선까지 포함

### 🤖 Claude Code 프롬프트 (선택)

````
data/stadiums.csv에 address, subway_station 컬럼을 추가해줘.
각 구장의 정보는 다음과 같아:

잠실: "서울특별시 송파구 올림픽로 25", "잠실종합운동장(2,9호선)"
고척: "서울특별시 구로구 경인로 430", "구일(1호선)"
문학: "인천광역시 미추홀구 매소홀로 618", "문학경기장(인천1호선)"
수원: "경기도 수원시 장안구 경수대로 893", "없음 (버스 환승)"
대전: "대전광역시 중구 대종로 373", "중앙로(1호선)"
대구: "대구광역시 수성구 야구전설로 1", "아양교(1호선)"
광주: "광주광역시 북구 서림로 10", "없음 (버스)"
창원: "경상남도 창원시 마산회원구 삼호로 63", "없음 (버스)"
사직: "부산광역시 동래구 사직로 45", "사직(3호선)"

pandas로 기존 CSV를 읽고 컬럼 추가 후 다시 저장해줘.
````

### 검증
```bash
python -c "import pandas as pd; df = pd.read_csv('data/stadiums.csv'); print(df[['short_name','address','subway_station']])"
```

---

## ⚾ 4. Step 4. KBO 경기일정 실제 수집 (30분)

### 목표
더미 데이터를 **2026 시즌 실제 일정으로 교체**한다.

### 3단 폴백 전략

**Plan A: 공식 사이트 파싱 (시도 → 실패 시 B)**
KBO 공식 사이트는 ASP.NET WebForms로 동적 로딩이 많아 정적 파싱이 어렵습니다. 성공 확률 30%.

**Plan B: 나무위키 HTML 파싱 (권장)**
[2026 KBO 리그 나무위키](https://namu.wiki/w/2026%20%EC%8B%A0%ED%95%9C%20SOL%20KBO%20%EB%A6%AC%EA%B7%B8)에 월별 경기일정 표가 잘 정리되어 있습니다. BeautifulSoup으로 파싱 가능.

**Plan C: 시드 CSV + 규칙 확장 (최후)**
팀장이 1~2주치(약 30경기)를 수기로 CSV에 입력하고, Claude Code가 KBO 일정 규칙(팀당 144경기, 요일별 패턴)에 따라 나머지 690경기를 생성.

### 🤖 Claude Code 프롬프트 (Plan B)

````
scripts/fetch_kbo_schedule.py를 만들어줘. 나무위키의 2026 KBO 리그 페이지에서
경기일정을 파싱해 data/kbo_schedule_2026.csv로 저장하는 스크립트야.

요구사항:

1. 라이브러리: requests + beautifulsoup4 (이미 requirements.txt에 있으면 추가 설치 불필요)

2. URL: https://namu.wiki/w/2026%20%EC%8B%A0%ED%95%9C%20SOL%20KBO%20%EB%A6%AC%EA%B7%B8

3. User-Agent 헤더를 브라우저처럼 설정 (나무위키가 기본 User-Agent 차단)

4. 실패 시 처리:
   - 네트워크 오류 → logging.error 후 exit(1)
   - HTML 구조 변경 → "파싱 실패, 더미 데이터 유지" 경고 후 exit(0)
   - 이 경우 Step 2에서 만든 더미 데이터가 그대로 남음

5. 파싱 성공 시:
   - 팀 약칭을 데이터 계약(src/config.py의 TEAMS)대로 정규화
     예: "kt wiz" → "KT", "LG 트윈스" → "LG"
   - game_id = f"{YYYYMMDD}_{away}_{home}"
   - 중복 game_id 제거

6. 최종 출력: "✅ Parsed N games → data/kbo_schedule_2026.csv"

7. 만약 나무위키 파싱이 복잡해서 안정적이지 않다면,
   scripts/seed_dummy_data.py의 seed_schedule()을 개선하는 방향으로
   대안 구현도 제안해줘. (현실적 팀 배정 로직 추가 등)

스크립트 작성 후 실제로 실행해서 결과를 보여줘.
````

### Plan B 실패 시 Plan C 프롬프트

````
나무위키 파싱이 불안정해. Plan C로 전환해줘.

scripts/seed_dummy_data.py의 seed_schedule() 함수를 개선해서 더 현실적인
2026 KBO 일정을 생성해줘:

1. 3/28 개막, 9/30 정규시즌 종료 (실제 일정 반영)
2. 팀당 정확히 144경기 (상대팀당 16경기 × 9팀 = 144)
3. 올스타 브레이크 7/10~7/15 경기 없음
4. 월요일은 경기 없음
5. 홈/어웨이 비율 72:72
6. 각 팀의 홈구장 고정

이렇게 수정하면 실제 KBO 일정과 거의 동일한 구조가 돼.
수정 후 재실행해서 데이터 품질 확인해줘.
````

### 검증
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/kbo_schedule_2026.csv', parse_dates=['date'])
print(f'총 경기: {len(df)}')
print(f'시즌 시작: {df.date.min()}')
print(f'시즌 종료: {df.date.max()}')
print(f'팀별 경기 수:')
print(df.groupby('home_team').size() + df.groupby('away_team').size())
"
```

각 팀이 **정확히 144경기**여야 합니다 (플랜 C 기준). 플랜 B로 실제 일정을 긁어왔다면 팀별 편차가 있을 수 있습니다.

---

## 📊 5. Step 5. 팀 전적 데이터 수집 (30분)

### 목표
승률 예측 모델(Phase 4)이 학습할 **팀별 과거 10년 성적 데이터** 완성.

### 전략 — "얕고 넓게"
팀 전적은 승률 예측 모델의 피처로만 쓰이므로 **깊이보다 일관성이 중요**합니다. 수기 10분이 API 크롤링 1시간보다 빠릅니다.

### 🤖 Claude Code 프롬프트

````
data/team_stats_10yr.csv의 더미 데이터를 실제 KBO 성적으로 교체해줘.
KBO 공식 사이트나 스탯티즈 크롤링 대신, 네가 알고 있는 2015~2025 시즌
팀별 최종 순위와 승률을 직접 기입하는 방식으로 만들어줘.

요구사항:

1. 2015~2025 × 10팀 = 110행
2. 컬럼은 data/SCHEMA.md의 team_stats_10yr 스키마를 정확히 따름
3. 핵심 필드는 최대한 정확하게:
   - year, team, wins, losses, draws, win_rate, final_rank
4. home_win_rate / away_win_rate는 정확한 수치를 모를 경우
   win_rate ± 0.03~0.06 범위로 합리적 추정치 생성
5. 네가 불확실한 연도는 주석에 "추정치" 표시는 하지 말고,
   합리적 범위 내 값으로 자연스럽게 채움
6. 2025 시즌 최종 순위는 매우 중요 (개막전 편성 기준):
   1위 KT, 2위 한화, 3위 KIA, 4위 삼성, 5위 NC
   (IMPLEMENTATION_PLAN.md 참고)
7. pandas로 저장, 인덱스 제외

작성 후 DataFrame을 print해서 결과 검토 가능하게 해줘.
````

> ⚠️ **데이터 정확도에 관한 주의**: LLM이 생성한 과거 성적은 실제 기록과 차이가 있을 수 있습니다. 프로젝트 목적(교육·시연)에는 충분하지만, 발표 시 "정확한 기록은 KBO 공식 자료를 참조"라고 명시하는 것이 안전합니다.

### 검증
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/team_stats_10yr.csv')
assert len(df) == 110, f'행 수 오류: {len(df)}'
assert df.win_rate.between(0.3, 0.7).all(), '승률 범위 오류'
print('✅ team_stats 검증 통과')
print(df[df.year == 2025].sort_values('final_rank'))
"
```

---

## 🌏 6. Step 6. TourAPI 클라이언트 작성 (30분) — **Phase 1의 핵심**

### 목표
한국관광공사 TourAPI를 호출하는 **재사용 가능한 클라이언트 모듈**을 작성하고, 이를 사용해 30개 POI 캐시 파일을 생성한다.

### 왜 중요한가
이 모듈은 Phase 2 지도 탭, Phase 4 AI 에이전트 모두에서 호출됩니다. **함수 시그니처를 한 번 정하면 바꾸기 어렵기 때문에** 신중하게 설계해야 합니다.

### 🤖 Claude Code 프롬프트 — 클라이언트 모듈

````
src/api/tour_api.py를 다음 명세대로 작성해줘:

### 목적
한국관광공사 TourAPI (공공데이터포털)를 호출하는 경량 클라이언트.

### 의존성
- httpx (동기)
- python-dotenv
- src.config에서 TOUR_API_BASE, CONTENT_TYPE import

### Public 함수

```python
def get_nearby_places(
    lat: float,
    lng: float,
    radius: int = 3000,
    content_type: int = 39,
    num_rows: int = 30,
) -> list[dict]:
    """
    지정 좌표 반경 내 관광 POI를 조회한다.

    Args:
        lat: 위도 (33~38 범위 검증)
        lng: 경도 (124~132 범위 검증)
        radius: 반경(m), 최대 20000
        content_type: 12=관광지, 32=숙박, 39=음식점
        num_rows: 최대 반환 개수

    Returns:
        data/SCHEMA.md의 POI 스키마를 따르는 dict 리스트
        실패 시 빈 리스트 반환 (예외 던지지 않음)
    """
```

### 내부 구현 규칙

1. 엔드포인트: `{TOUR_API_BASE}/locationBasedList1`
2. 쿼리 파라미터:
   - serviceKey: os.getenv("TOUR_API_KEY") — 디코딩된 키 사용
   - mapX: lng, mapY: lat (주의: TourAPI는 X가 경도, Y가 위도)
   - radius: radius
   - contentTypeId: content_type
   - MobileOS: "ETC"
   - MobileApp: "AwayGameCompanion"
   - _type: "json"
   - numOfRows: num_rows
   - pageNo: 1
3. 타임아웃 10초, httpx.Timeout 사용
4. 응답 구조: response.body.items.item (리스트 또는 단일 dict)
5. 단일 dict일 경우 리스트로 감싸기
6. 응답 → 스키마 필드로 매핑:
   - content_id ← contentid
   - title ← title
   - category ← content_type 역매핑 (12→tour, 32→stay, 39→food)
   - addr ← addr1
   - lat ← mapy (float 변환)
   - lng ← mapx (float 변환)
   - tel ← tel (없으면 빈 문자열)
   - first_image ← firstimage (없으면 빈 문자열)
   - dist_m ← dist (float 변환, 미터)
7. 에러 처리:
   - HTTP 에러, 타임아웃, JSON 파싱 실패 모두 logging.warning 후 빈 리스트 반환
   - 응답 body에 "SERVICE KEY IS NOT REGISTERED" 포함 시 명확한 에러 메시지
8. 로깅: logging 모듈 사용, print 금지

### 테스트 코드
파일 하단에 if __name__ == "__main__": 블록으로
잠실 좌표(37.5122, 127.0719)로 음식점을 5개 조회해 결과를 print.
.env에 TOUR_API_KEY가 있어야 작동.

작성 후 실제로 python -m src.api.tour_api 실행해 확인.
````

### 🤖 Claude Code 프롬프트 — POI 일괄 캐싱 스크립트

````
scripts/cache_poi.py를 다음 명세로 작성해줘:

### 목적
data/stadiums.csv의 10개 구장에 대해 3개 카테고리(tour, stay, food)를
각각 TourAPI로 조회해 data/poi_cache/{short_name}_{category}.json으로 저장.

### 처리 흐름
1. stadiums.csv 로드
2. for stadium in 10개:
       for category in ["tour", "stay", "food"]:
           places = get_nearby_places(lat, lng, 3000, CONTENT_TYPE[category], 30)
           파일에 저장
           print(f"[{stadium.short_name}/{category}] {len(places)}개 저장")
3. API rate limit 고려: 요청 사이 0.5초 sleep
4. 이미 파일이 존재하면 --force 플래그 없으면 skip

### CLI
argparse로 --force (캐시 무시 재호출) 옵션 지원

### 실행 결과 검증
30개 JSON 파일이 생기고 총 POI가 500개 이상인지 확인

작성 후 python scripts/cache_poi.py 실행 (.env 키 있는 경우만).
키가 없으면 "TOUR_API_KEY 없음, Step 2 더미 데이터 유지" 메시지 출력.
````

### 검증
```bash
# 파일 개수
ls data/poi_cache/*.json | wc -l    # 30

# 랜덤 1개 파일 샘플 확인
python -c "
import json
with open('data/poi_cache/잠실_food.json') as f:
    data = json.load(f)
print(f'잠실 음식점 {len(data)}개')
print(data[0])
"
```

---

## ⛅ 7. Step 7. 기상청 API 클라이언트 (15분)

### 목표
경기 당일 우천 확률 조회를 위한 기상청 단기예보 API 클라이언트 작성. **미리 캐싱하지 않고 런타임에 호출**하므로 모듈만 만들어두면 끝.

### 🤖 Claude Code 프롬프트

````
src/api/weather_api.py를 다음 명세로 작성해줘:

### Public 함수

```python
def get_forecast(lat: float, lng: float, target_date: str) -> dict:
    """
    특정 좌표의 특정 날짜 날씨 예보 조회.

    Args:
        lat, lng: 좌표
        target_date: "YYYY-MM-DD"

    Returns:
        {
            "date": "2026-04-19",
            "sky": "맑음",
            "precipitation_prob": 20,
            "temp_min": 8,
            "temp_max": 18,
            "rain_expected": False
        }

        API 실패 시 모든 값이 None인 dict 반환 (UI가 "정보 없음" 표시)
    """
```

### 내부 구현

1. 엔드포인트: {WEATHER_API_BASE}/getVilageFcst
2. WGS84 lat/lng → 기상청 격자 좌표 변환 함수 필요
   (람베르트 정각원추도법, 공식 매뉴얼의 dfs_xy_conv 알고리즘)
   - 이 변환 함수는 파일 안에 정의 (util 함수)
3. base_date: 오늘 (단기예보 가용 시간 고려)
4. base_time: 가장 최근 발표 시각 (02/05/08/11/14/17/20/23)
5. target_date가 오늘로부터 3일 이내가 아니면 근사치 반환
6. 응답 파싱:
   - SKY: 1=맑음, 3=구름많음, 4=흐림
   - POP: 강수확률 (0~100)
   - TMN/TMX: 최저/최고 기온
7. rain_expected = POP >= 60

### Streamlit 연동 고려
함수 상단에 주석으로 "Streamlit에서 @st.cache_data(ttl=1800)로 감싸서
30분 캐싱 권장" 명시.

### 테스트
if __name__ == "__main__":
    서울 잠실 좌표로 내일 예보 조회해 print.
````

### 검증
```bash
python -m src.api.weather_api
# 출력: {'date': '2026-04-18', 'sky': '맑음', 'precipitation_prob': 20, ...}
```

> 💡 **기상청 API가 승인 대기 중이라면**: 함수가 항상 `{"sky": "맑음", "precipitation_prob": 0, "rain_expected": False, ...}`를 반환하는 **모의(mock) 모드**를 추가해두면 Phase 2~4 개발이 막히지 않습니다.

---

## 🔗 8. Step 8. 통합 data_loader.py 작성

### 목표
Phase 2~4 담당자가 **`from src.data_loader import load_all_data`** 한 줄로 모든 데이터를 받을 수 있게 하는 통합 로더.

### 🤖 Claude Code 프롬프트

````
src/data_loader.py를 다음 명세로 작성해줘:

### Public 함수

```python
@st.cache_data(ttl=3600)
def load_schedule() -> pd.DataFrame:
    """kbo_schedule_2026.csv 로드, date 컬럼 파싱"""

@st.cache_data(ttl=3600)
def load_stadiums() -> pd.DataFrame:
    """stadiums.csv 로드"""

@st.cache_data(ttl=3600)
def load_team_stats() -> pd.DataFrame:
    """team_stats_10yr.csv 로드"""

@st.cache_data(ttl=3600)
def load_poi(stadium_short_name: str, category: str) -> list[dict]:
    """
    구장별 카테고리별 POI 캐시 로드.
    category는 'tour' | 'stay' | 'food' 중 하나.
    파일이 없으면 빈 리스트 반환.
    """

def load_all_data() -> dict:
    """
    모든 데이터를 한 번에 로드. Phase 1 검증 용도.

    Returns:
        {
            "schedule": DataFrame,
            "stadiums": DataFrame,
            "team_stats": DataFrame,
            "poi_counts": {"잠실_food": 30, ...}
        }
    """
```

### 규칙
1. pandas.read_csv 시 dtype 명시
2. 파일이 없으면 FileNotFoundError를 명확한 한국어 메시지와 함께 raise
3. @st.cache_data는 streamlit 실행 시에만 작동, 스크립트 실행 시는 무시되어야 함
   → try/except로 streamlit import 실패 시 no-op decorator 사용

### 파일 하단 테스트
if __name__ == "__main__":
    data = load_all_data()
    print(f"경기 수: {len(data['schedule'])}")
    print(f"구장 수: {len(data['stadiums'])}")
    print(f"팀 기록 수: {len(data['team_stats'])}")
    print(f"POI 캐시: {sum(data['poi_counts'].values())}개")

작성 후 python -m src.data_loader 실행해 결과 확인.
````

### 검증
```bash
python -m src.data_loader
```

기대 출력:
```
경기 수: 720
구장 수: 10
팀 기록 수: 110
POI 캐시: 약 600~800개
```

---

## 🔍 9. Step 9. 데이터 품질 검증 스크립트 — **Phase 2 진입 게이트**

### 목표
하나의 스크립트 실행으로 **"Phase 1이 완료되었는가"**를 자동 판정.

### 🤖 Claude Code 프롬프트

````
scripts/validate_data.py를 만들어줘. 이 스크립트는 Phase 1의 모든
산출물을 자동 검증하고, pass/fail을 명확히 출력해.

### 검증 항목

1. 파일 존재 확인
   - data/kbo_schedule_2026.csv
   - data/stadiums.csv
   - data/team_stats_10yr.csv
   - data/poi_cache/ (30개 JSON)
   - src/api/tour_api.py, weather_api.py
   - src/data_loader.py

2. kbo_schedule 검증
   - 행 수 600 이상
   - 날짜 범위 2026-03-28 ~ 2026-09-30
   - home_team, away_team 모두 TEAMS 상수 안의 값
   - game_id 중복 없음

3. stadiums 검증
   - 정확히 10행
   - lat 범위 33~38
   - lng 범위 124~132
   - short_name 유니크

4. team_stats 검증
   - year × team 조합 중복 없음
   - win_rate 범위 0.3~0.7
   - 각 연도 final_rank가 1~10 전부 존재

5. poi_cache 검증
   - 파일 30개
   - 각 파일 최소 5개 이상 POI (더미면 20+)
   - 필수 필드 (content_id, title, lat, lng) 결측 없음

6. 외래키 무결성
   - schedule의 stadium 값이 stadiums의 short_name에 전부 존재

### 출력 형식

```
================================================
Phase 1 Data Validation Report
================================================
[PASS] 파일 존재: 34/34
[PASS] KBO 일정: 720 games, 2026-03-28 ~ 2026-09-30
[PASS] 구장: 10 stadiums, 좌표 범위 정상
[FAIL] 팀 전적: 2020 시즌 final_rank 누락 (5, 7)
[PASS] POI 캐시: 30 files, 총 635 POIs
[PASS] 외래키: schedule.stadium → stadiums.short_name

총 검증: 6개
통과: 5개
실패: 1개

❌ Phase 1 미완료. 위 실패 항목을 해결한 후 재실행하세요.
```

### 종료 코드
- 전부 통과: exit(0)
- 하나라도 실패: exit(1)

### CI 연동 고려
exit code를 활용할 수 있게 하되, pytest가 아닌 단순 스크립트로 작성.
argparse로 --verbose 옵션 추가해 상세 로그 토글 가능하게.

작성 후 실행해서 검증 결과 보여줘.
````

### 검증
```bash
python scripts/validate_data.py

# 모든 항목 PASS 뜨면 Phase 2 진입 가능
echo $?   # 0이어야 함
```

---

## 👥 10. 병렬 작업 가이드 — Phase 1 동안 다른 팀원은?

데이터 엔지니어가 Step 1~9를 진행하는 2시간 동안, 나머지 팀원들은 놀면 안 됩니다. **Step 2(더미 데이터 생성) 완료 시점부터** 각자 다음 작업을 시작하세요.

### 🎨 프론트 / UX 담당
- Phase 2 "사이드바 필터" 뼈대 작성 시작
- 더미 `stadiums.csv`와 `kbo_schedule_2026.csv`를 읽어 팀 셀렉트박스 등 연동
- Figma로 5개 탭 와이어프레임 디테일링

### 🗺️ 지도 / 시각화 담당
- `streamlit-folium` 설치 및 헬로월드 (잠실 위치 마커 하나 찍기)
- Plotly로 더미 `team_stats_10yr.csv` 막대그래프 예제 만들기
- 구장 좌표로 한국 지도 전체 마커 배치 프로토타입

### 🤖 AI / 분석 담당
- OpenAI 또는 Gemini API 테스트 호출 (`"Hello"` 수준)
- `st.chat_message`, `st.chat_input` 기본 사용법 학습
- Phase 4 챗봇 시스템 프롬프트 초안 작성

### 🧑‍✈️ 팀장
- Phase 2~4 가이드 문서 초안 작성 착수
- 발표 자료 슬라이드 템플릿 준비 (표지, 목차, 아키텍처 다이어그램 틀)

---

## 🧾 11. 완료 체크리스트

- [ ] `data/SCHEMA.md` 작성 완료 및 팀 공유
- [ ] `src/config.py` 상수 정의
- [ ] 더미 데이터 5종 생성 (`seed_dummy_data.py` 실행)
- [ ] `stadiums.csv` 실제 주소·지하철 정보 추가
- [ ] `kbo_schedule_2026.csv` 실제 (또는 규칙 기반) 데이터로 교체
- [ ] `team_stats_10yr.csv` 11년치 성적 완성
- [ ] `src/api/tour_api.py` 작성 및 테스트
- [ ] `scripts/cache_poi.py` 실행하여 30개 POI 캐시 생성
- [ ] `src/api/weather_api.py` 작성 (mock 모드 포함)
- [ ] `src/data_loader.py` 통합 로더 완성
- [ ] `scripts/validate_data.py` 실행 → **전부 PASS**
- [ ] 커밋 & push → 팀원 `git pull`

---

## 🆘 12. 트러블슈팅 FAQ

### Q1. 나무위키 파싱이 HTML 변경 때문에 자꾸 깨집니다
나무위키는 HTML 구조가 자주 바뀝니다. 2시간 이상 헤매지 마세요. **Plan C(규칙 기반 생성)로 전환**하는 게 생산성에 훨씬 이롭습니다. 실제 팀별 144경기 · 시즌 기간 · 올스타 브레이크만 정확하면 발표에는 충분합니다.

### Q2. TourAPI 응답이 XML로 옵니다
요청 URL에 `_type=json` 파라미터가 빠졌을 가능성이 큽니다. `src/api/tour_api.py`의 params dict에 명시적으로 추가하세요.

### Q3. TourAPI가 "SERVICE KEY IS NOT REGISTERED" 반환
공공데이터포털의 serviceKey는 **"일반 인증키"와 "디코딩된 일반 인증키"** 두 가지 형태가 있습니다. `%`가 포함된 키(디코딩 전)를 `.env`에 그대로 넣고, 코드에서는 추가 디코딩 없이 사용하세요. URL 인코딩은 httpx가 자동 처리합니다.

### Q4. 기상청 API가 "NO_DATA" 반환
- base_time 계산 오류: 발표 시각(02/05/08/11/14/17/20/23)에서 **최소 1시간 지난 뒤** 요청해야 데이터가 있습니다
- 미래 날짜 범위 초과: 단기예보는 **발표 시점부터 +3일**까지만 유효
- 대안: 기상청 "동네예보" API 대신 **OpenWeatherMap 무료 API**로 대체 가능 (영문 응답)

### Q5. `pandas.read_csv`에서 한글 깨짐
Windows 환경에서 자주 발생. `pd.read_csv(path, encoding='utf-8-sig')`로 BOM 처리. 또는 저장 시 `df.to_csv(path, encoding='utf-8-sig', index=False)`.

### Q6. 팀 전적 연도가 2025로 되어 있는데, 2026 시즌 예측에 쓸 수 있나요?
네. 2026 시즌이 아직 진행 중이라 피처로는 **2025까지의 누적 기록**을 사용하는 것이 맞습니다. Phase 4 예측 모델은 "이 팀의 과거 성향"을 학습하는 것이므로 문제없습니다.

### Q7. validate_data.py에서 외래키 검증 실패
schedule.csv의 `stadium` 값이 stadiums.csv의 `short_name`과 정확히 일치해야 합니다. 공백·특수문자 차이로 자주 발생하므로 `df.stadium.str.strip()`으로 정규화하세요.

---

## 🎬 13. 다음 Phase로 넘어가기 전 확인

다음 5가지가 모두 ✅이면 Phase 2 시작 준비 완료입니다.

1. ✅ `python scripts/validate_data.py` 종료 코드 **0**
2. ✅ `python -m src.data_loader` 실행 시 모든 데이터 로드 성공
3. ✅ 팀원 전원이 `git pull`로 최신 데이터 받음
4. ✅ `src/config.py`와 `data/SCHEMA.md`가 팀의 단일 진실원으로 확립
5. ✅ `CLAUDE.md` "현재 진행 Phase" 필드가 **Phase 2**로 업데이트됨

### Phase 2로 전환하는 Claude Code 프롬프트

````
Phase 1이 완료됐어. scripts/validate_data.py를 실행해서
모든 항목이 PASS인지 먼저 확인해줘.

통과했다면:
1. CLAUDE.md의 "현재 진행 Phase"를 Phase 2로 업데이트
2. IMPLEMENTATION_PLAN.md의 Phase 2 섹션을 참고해서
   첫 번째 작업인 "2-1. app.py 메인 엔트리"를 진행

실패 항목이 있다면 그 내용을 요약하고 해결 방안 제시.
````

---

## 📚 참고

- 전체 계획: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) Phase 1 섹션
- 이전 가이드: [PHASE0_GUIDE.md](./PHASE0_GUIDE.md)
- 한국관광공사 TourAPI: https://api.visitkorea.or.kr/
- 공공데이터포털: https://www.data.go.kr/
- 기상청 단기예보 매뉴얼: "동네예보 조회서비스 오픈 API 활용가이드" PDF

---

*가이드 마지막 업데이트: 2026-04-17*
*예상 총 소요 시간: 2시간 (데이터 엔지니어 1명 기준)*
