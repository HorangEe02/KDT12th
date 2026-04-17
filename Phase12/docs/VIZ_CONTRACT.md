# 📐 VIZ_CONTRACT — Phase 3 시각화/지도/경로 함수 계약

Phase 3 산출 모듈의 공개 함수 시그니처 · 입력 · 실패 반환값을 팀 전체가 공유하는 단일 진실원.
Phase 4 AI 에이전트(Function Calling)가 이 계약대로 호출하므로 시그니처 변경은 팀 합의 후에만.

---

## 1. `src/viz/folium_map.py`

### `create_map(center, zoom=13, stadium=None, places=None, route=None, weather=None) -> folium.Map`

원정 플래너 인터랙티브 지도 생성.

| 파라미터 | 타입 | 설명 |
|---|---|---|
| center | `tuple[float, float]` | `(lat, lng)` — 지도 중심 |
| zoom | `int` | 초기 줌 (13~15 권장) |
| stadium | `dict \| None` | stadiums.csv 한 행 dict (short_name·stadium_name·home_team·address·lat·lng·capacity·subway_station) |
| places | `dict[str, list[dict]] \| None` | `{"food": [...], "stay": [...], "tour": [...]}` — POI 스키마 준수 |
| route | `list[tuple[float, float]] \| None` | 폴리라인 정점 `[(lat,lng), ...]` |
| weather | `dict \| None` | weather_api 스키마 dict (경기장 popup 주입용) |

**호출처**: `src/ui/tabs/tab2_map.py`

**실패 시**: None 인자는 허용. 잘못된 좌표여도 folium이 렌더하므로 검증은 호출측 책임.

### `render_map_in_streamlit(m, height=550, width=None) -> dict`

`st_folium`으로 렌더 + 클릭 이벤트 수신.

**반환**: `{"last_object_clicked": {"lat":..., "lng":...} | None, "last_clicked": ...}` (st_folium 원형 반환).

---

## 2. `src/viz/popup_builder.py`

### `stadium_popup_html(stadium, weather=None) -> str`
### `place_popup_html(place) -> str`

**보안 규약**: 모든 동적 문자열은 `html.escape()` 필수. 이미지 URL은 `http://` → `https://` 치환.

---

## 3. `src/viz/plotly_charts.py`

### `bar_away_win_rate(df: pd.DataFrame, highlight_team: str) -> go.Figure`

**입력**: `data/team_stats_10yr.csv` DataFrame
**동작**: 최근 3년 평균 `away_win_rate` 집계 + 선택 팀만 팀 컬러
**호출처**: tab1_games

### `scatter_places(places: list[dict], stadium_coord: tuple) -> go.Figure`

**입력**: POI dict 리스트 (food 카테고리 권장)
**실패 시**: 빈 리스트 → "데이터 없음" annotation figure 반환
**호출처**: tab3_places

### `gauge_win_rate(prob: float, team_name: str) -> go.Figure`

**입력**: 0.0~1.0 확률 + 팀 약칭
**호출처**: tab1_games (Phase 4 예측 모델 연동 예정, 현재 더미)

---

## 4. `src/api/kakao_map.py`

### `get_car_route(origin, destination, waypoints=None) -> dict`

**엔드포인트**: `https://apis-navi.kakaomobility.com/v1/directions`
**인증**: `.env` 의 `KAKAO_MOBILITY_API_KEY` 우선, 없으면 `KAKAO_REST_API_KEY`

**성공 반환**:
```python
{
    "vertexes": [(lat, lng), ...],
    "duration_sec": 7200,
    "distance_m": 320000,
    "toll_fare": 15600,
    "fallback": False,
}
```

**실패/키없음 Fallback**:
```python
{
    "vertexes": [origin, destination],   # 직선
    "duration_sec": None,
    "distance_m": <haversine_m>,
    "toll_fare": None,
    "fallback": True,
}
```

**캐시**: `data/route_cache/{md5(origin+dest+waypoints)}.json` (1일 이상 무한)

**호출처**: `src/ui/tabs/tab2_map.py`, Phase 4 AI 에이전트

---

*마지막 업데이트: 2026-04-17 (Phase 3 Step 1)*
