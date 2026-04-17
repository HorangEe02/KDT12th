# 📐 데이터 계약 문서 (Data Contract)

이 문서는 Phase 1에서 산출되는 모든 데이터의 **단일 진실원**입니다.
Phase 2~4 담당자는 이 스키마를 기준으로 뼈대 코드를 작성합니다.
스키마 변경은 팀 합의 후에만 수행하며, 변경 시 이 문서를 먼저 업데이트합니다.

---

## 1. `data/kbo_schedule_2026.csv`

| 컬럼 | 타입 | 예시 | 설명 |
|---|---|---|---|
| game_id | str | 20260328_LG_KT | `YYYYMMDD_AWAY_HOME` |
| date | date (ISO) | 2026-03-28 | ISO 8601 `YYYY-MM-DD` |
| day_of_week | str | 토 | 한글 1자 (월/화/수/목/금/토/일) |
| home_team | str | KT | 팀 약칭 표준 (아래 참조) |
| away_team | str | LG | 팀 약칭 표준 |
| stadium | str | 수원 | 구장 short_name |
| start_time | str | 14:00 | `HH:MM` (24시간) |
| broadcast | str | SBS | 지상파/케이블 (결측 허용) |

---

## 2. `data/stadiums.csv`

| 컬럼 | 타입 | 예시 | 설명 |
|---|---|---|---|
| stadium_name | str | 잠실야구장 | 풀네임 |
| short_name | str | 잠실 | schedule의 `stadium`과 매칭되는 키 |
| home_team | str | LG,두산 | 복수 팀이면 쉼표 구분 |
| city | str | 서울 | 광역시/도 단위 |
| address | str | 서울특별시 송파구 올림픽로 25 | 도로명 주소 |
| lat | float | 37.5122 | 위도 |
| lng | float | 127.0719 | 경도 |
| capacity | int | 25000 | 수용 인원 |
| subway_station | str | 잠실종합운동장(2,9호선) | 주변 지하철 |

---

## 3. `data/team_stats_10yr.csv`

| 컬럼 | 타입 | 예시 | 설명 |
|---|---|---|---|
| year | int | 2025 | 시즌 연도 |
| team | str | LG | 팀 약칭 표준 |
| games_played | int | 144 | 총 경기 수 |
| wins | int | 81 | 승 |
| losses | int | 58 | 패 |
| draws | int | 5 | 무 |
| win_rate | float | 0.583 | 전체 승률 |
| home_win_rate | float | 0.611 | 홈 승률 |
| away_win_rate | float | 0.555 | 원정 승률 |
| final_rank | int | 1 | 최종 순위 (1~10) |

---

## 4. `data/poi_cache/{short_name}_{category}.json`

카테고리 값: `food` (음식점), `stay` (숙박), `tour` (관광지)

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

---

## 5. 기상청 응답 스키마 (런타임, CSV 저장 없음)

`src/api/weather_api.get_forecast()`의 반환 dict:

```python
{
    "date": "2026-04-19",
    "sky": "맑음",              # 맑음 / 구름많음 / 흐림
    "precipitation_prob": 20,   # 0~100
    "temp_min": 8,
    "temp_max": 18,
    "rain_expected": False,
}
```

API 실패 시 각 필드가 `None`인 dict 반환. UI는 "정보 없음"으로 표시.

---

## 6. 팀 약칭 표준

반드시 다음 10개로 통일 (`src/config.TEAMS`):

```
LG, KT, SSG, 두산, KIA, NC, 삼성, 롯데, 한화, 키움
```

### 팀 → 홈구장 매핑 (`src/config.HOME_STADIUM`)

| 팀 | short_name |
|---|---|
| LG | 잠실 |
| 두산 | 잠실 |
| 키움 | 고척 |
| SSG | 문학 |
| KT | 수원 |
| 한화 | 대전 |
| 삼성 | 대구 |
| KIA | 광주 |
| NC | 창원 |
| 롯데 | 사직 |

---

## 7. TourAPI content_type 매핑

`src/config.CONTENT_TYPE`:

| 카테고리 | contentTypeId |
|---|---|
| tour (관광지) | 12 |
| stay (숙박) | 32 |
| food (음식점) | 39 |

---

## 8. 시즌 상수 (`src/config.py`)

| 상수 | 값 |
|---|---|
| SEASON_START | 2026-03-28 |
| SEASON_END | 2026-09-30 |
| ALL_STAR_BREAK | (2026-07-10, 2026-07-15) |

---

*마지막 업데이트: 2026-04-17 (Phase 1 Step 1)*
