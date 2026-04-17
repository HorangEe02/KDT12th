# 🗺️ Phase 3 구현 가이드 — 지도 & 시각화 with Claude Code

> **목표**: Folium 인터랙티브 지도와 Plotly 차트를 완성하여, 사용자가 클릭·필터·탐색으로 원정 동선을 시각적으로 이해할 수 있게 만든다.
> **실제 작업 시간**: 약 2시간
> **대상 독자**: 지도·시각화 담당(주) + 데이터 엔지니어(지원)
> **전제 조건**: [Phase 2 가이드](./PHASE2_GUIDE.md) 완료, `validate_phase2.py` PASS

---

## 🎯 0. Phase 3 개요

### 완료 조건 (5가지 모두 참)
1. ✅ 탭 2에서 **경기장·맛집·숙소·관광지 4개 레이어**가 토글되는 Folium 지도 표시
2. ✅ **마커 클릭 시 우측 컬럼에 상세 정보**가 즉시 표시 (양방향 통신)
3. ✅ 출발지 → 경기장 **경로 폴리라인**이 지도 위에 그려짐 (카카오모빌리티 또는 Fallback)
4. ✅ 탭 1에 **승률 예측 게이지 + 구단별 원정 승률 막대그래프** 표시
5. ✅ 탭 3에 **맛집 평점 × 거리 산점도** + 카드 리스트 표시

### 이 Phase에서 산출되는 파일

```
src/
├── viz/
│   ├── folium_map.py          # Folium 지도 컴포넌트 (재사용 가능)
│   ├── plotly_charts.py       # Plotly 차트 3종
│   └── popup_builder.py       # Folium Popup HTML 생성기
├── api/
│   └── kakao_map.py           # 카카오모빌리티 경로 API (with 캐싱)
└── ui/tabs/
    ├── tab1_games.py          # 승률 게이지 + 차트 추가
    ├── tab2_map.py            # Folium 지도 렌더링 완성
    └── tab3_places.py         # 산점도 + 카드 리스트 완성

data/
└── route_cache/               # 카카오모빌리티 응답 캐시
```

### 작업 순서 맵

```
 [Step 1. 인터페이스 합의]
                    ▼
 [Step 2. Folium 기본 지도] ──► 🎨 시각화 담당 주 작업 시작
                    ▼
 [Step 3. Popup 디자인 + 날씨 연동]
                    ▼
 [Step 4. 마커 클릭 양방향 UX] ★ 시그니처 기능
                    ▼
 [Step 5. 카카오 경로 + Fallback]
                    ▼
 [Step 6. Plotly 차트 2종] (필수)
                    ▼
 [Step 7. 승률 게이지] (권장)
                    ▼
 [Step 8. Tab 2, 3 통합]
                    ▼
 [Step 9. 검증 & 시연]
```

---

## 🧾 1. Step 1. 인터페이스 합의 (10분)

### 왜 먼저 하나
이 Phase에서 만드는 함수들은 탭 2·탭 3 모두에서 호출됩니다. **시그니처를 먼저 정해두지 않으면 탭별로 중복 구현**이 일어나고, Phase 4 AI 에이전트도 이 함수들을 호출할 예정이라 계약 변경 리스크가 커져요.

### 공개 함수 시그니처 (확정)

```python
# src/viz/folium_map.py
def create_map(
    center: tuple[float, float],        # (lat, lng)
    zoom: int = 13,
    stadium: dict | None = None,         # 경기장 정보 1개
    places: dict[str, list[dict]] | None = None,  # {"food": [...], "stay": [...], ...}
    route: list[tuple[float, float]] | None = None,  # 폴리라인 좌표들
    weather: dict | None = None,         # 경기장 팝업에 주입
) -> folium.Map:
    """원정 플래너용 인터랙티브 지도 생성"""


def render_map_in_streamlit(
    m: folium.Map,
    height: int = 550,
    width: int | None = None,
) -> dict:
    """
    Streamlit에 지도 렌더링 + 클릭 이벤트 반환.
    
    Returns:
        st_folium의 반환 dict (last_object_clicked 등)
    """
```

```python
# src/viz/plotly_charts.py
def bar_away_win_rate(df: pd.DataFrame, highlight_team: str) -> go.Figure: ...
def scatter_places(places: list[dict], stadium_coord: tuple) -> go.Figure: ...
def gauge_win_rate(prob: float, team_name: str) -> go.Figure: ...
```

```python
# src/api/kakao_map.py
def get_car_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    waypoints: list[tuple[float, float]] | None = None,
) -> dict:
    """
    Returns:
        {
            "vertexes": [(lat, lng), ...],      # 폴리라인용
            "duration_sec": 7200,
            "distance_m": 320000,
            "toll_fare": 15600,
            "fallback": False,                  # True면 직선 거리 대체
        }
    """
```

### 🤖 Claude Code 프롬프트

````
docs/VIZ_CONTRACT.md 파일을 만들어서 위 세 모듈의 함수 시그니처를
그대로 옮겨 저장해줘. 그리고 각 함수에:
1. 언제 호출되는지 (어느 탭에서)
2. 어떤 데이터가 입력되는지 (Phase 1의 CSV 기준)
3. 실패 시 반환값
을 추가로 명시해줘.

이 문서는 팀 내 "이 함수는 이렇게 생길 것이다"의 계약 문서로 쓰여.
````

---

## 🗺️ 2. Step 2. Folium 기본 지도 컴포넌트 (30분)

### 목표
경기장 1개 + 4개 POI 레이어가 토글되는 **재사용 가능한 지도 함수**를 완성한다.

### 핵심 설계 포인트

- `folium.FeatureGroup`으로 카테고리별 레이어 분리 → `LayerControl`로 토글
- POI가 30개 이상이면 **`MarkerCluster`**로 자동 군집화 (성능 확보)
- 카테고리별 **색상·아이콘 구분** (빨강-경기장·주황-맛집·파랑-숙소·녹색-관광지)
- 클릭 이벤트 처리를 위해 마커에 `tooltip`과 `popup` 모두 설정

### 🤖 Claude Code 프롬프트

````
src/viz/folium_map.py를 docs/VIZ_CONTRACT.md 명세대로 구현해줘.

### 상단 상수
```python
LAYER_STYLES = {
    "stadium": {"color": "red",    "icon": "baseball-ball", "prefix": "fa"},
    "food":    {"color": "orange", "icon": "utensils",       "prefix": "fa"},
    "stay":    {"color": "blue",   "icon": "bed",            "prefix": "fa"},
    "tour":    {"color": "green",  "icon": "camera",         "prefix": "fa"},
}

CATEGORY_LABELS_KO = {
    "food": "🍽️ 음식점",
    "stay": "🏨 숙박",
    "tour": "🎡 관광지",
}
```

### create_map 구현

1. folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
2. 경기장 FeatureGroup 추가 (Stadium)
   - stadium이 None이 아니면 큰 빨간 마커
   - popup은 Step 3에서 만들 popup_builder 사용 (일단 간단한 HTML로)
3. places dict를 순회하며 3개 FeatureGroup 추가
   - 각 카테고리마다 MarkerCluster 사용 (len(places[cat]) > 20일 때만)
   - 20 이하면 개별 마커로 표시
4. route가 있으면 folium.PolyLine 추가
   - color="#0066FF", weight=4, opacity=0.7
   - dash_array 파라미터 사용으로 점선 처리 (fallback일 때)
5. folium.LayerControl(collapsed=False) 추가 (토글 UI)

### 검증용 테스트
파일 하단에 if __name__ == "__main__": 블록으로
- 잠실야구장 중심 지도 생성
- Phase 1의 poi_cache/잠실_food.json, 잠실_stay.json 로드
- 더미 route (잠실 주변 임의 좌표 5개)
- m.save("/tmp/test_map.html") 후 브라우저에서 확인 안내 출력

### 코딩 규칙
- 모든 좌표는 (lat, lng) 튜플로 통일
- folium이 내부적으로 [lat, lng] 리스트를 쓰니 변환 함수 하나 유틸화
- 모든 텍스트는 한글 가능, HTML escape는 Step 3 popup_builder에서 처리

작성 후 python -m src.viz.folium_map 실행해 지도 HTML 생성 확인.
````

### 검증
```bash
python -m src.viz.folium_map
open /tmp/test_map.html   # Mac, Linux는 xdg-open, Windows는 start
```

지도가 열리고 **4개 레이어 토글 버튼**이 우상단에 보여야 합니다.

---

## 🎨 3. Step 3. Popup 디자인 + 날씨 연동 (20분)

### 목표
마커 Popup을 **깔끔한 HTML 카드**로 디자인하고, 경기장 Popup에는 우천 확률을 포함한다.

### 🤖 Claude Code 프롬프트

````
src/viz/popup_builder.py를 만들어줘. Folium Popup의 HTML을 생성하는
전용 모듈이야.

### Public 함수

```python
def stadium_popup_html(stadium: dict, weather: dict | None = None) -> str:
    """경기장 마커용 HTML"""

def place_popup_html(place: dict) -> str:
    """음식점/숙박/관광지 마커용 HTML"""
```

### stadium_popup_html 구조

```html
<div style="font-family: 'Pretendard', sans-serif; width: 260px;">
  <div style="background: #DC2626; color: white; padding: 8px 12px; 
              border-radius: 6px 6px 0 0; font-weight: bold; font-size: 15px;">
    ⚾ {stadium_name}
  </div>
  <div style="padding: 10px 12px; background: white;">
    <div style="color: #666; font-size: 12px; margin-bottom: 6px;">
      🏠 홈팀: {home_team}
    </div>
    <div style="color: #333; font-size: 13px; margin-bottom: 6px;">
      📍 {address}
    </div>
    <div style="color: #333; font-size: 12px;">
      🚇 {subway_station}
    </div>
    {weather_section}
    <div style="color: #999; font-size: 11px; margin-top: 8px;">
      좌석 수: {capacity:,}석
    </div>
  </div>
</div>
```

weather_section은 weather가 있을 때만:
```html
<div style="margin-top: 10px; padding: 8px; background: #EFF6FF; 
            border-radius: 4px;">
  <div style="font-size: 12px; color: #1E40AF;">
    ⛅ {sky} · 강수확률 {precipitation_prob}%
  </div>
  {rain_warning}  <!-- precipitation_prob >= 60이면 "☔ 우산 필수" 배지 -->
</div>
```

### place_popup_html 구조

카테고리별 헤더 색상:
- food: #F97316 (주황)
- stay: #3B82F6 (파랑)
- tour: #10B981 (녹색)

```html
<div style="font-family: 'Pretendard'; width: 240px;">
  <div style="background: {category_color}; color: white; 
              padding: 8px 12px; border-radius: 6px 6px 0 0;">
    {category_emoji} {title}
  </div>
  <div style="padding: 10px 12px; background: white;">
    {first_image ? `<img src="..." style="width:100%; height:120px; 
                        object-fit:cover; border-radius:4px; margin-bottom:8px;"/>` : ""}
    <div style="color: #333; font-size: 12px;">{addr}</div>
    <div style="color: #666; font-size: 12px;">
      📏 경기장에서 {dist_m}m
    </div>
    {tel ? `<div>📞 ${tel}</div>` : ""}
  </div>
</div>
```

### 보안 처리

모든 동적 문자열(title, addr, tel 등)은 html.escape()로 이스케이프.
import html 사용.

### 통합
folium_map.py의 create_map()에서 마커 생성 시
folium.Popup(html=stadium_popup_html(...), max_width=300)
folium.Popup(html=place_popup_html(...), max_width=260)
형태로 사용.

### 테스트
파일 하단에 더미 stadium, weather, place 데이터로
HTML 출력 확인 print.
````

### 검증
```bash
python -m src.viz.popup_builder
# 생성된 HTML을 브라우저에서 렌더링 확인 (복붙)

python -m src.viz.folium_map
# 지도에서 마커 클릭 시 새 Popup 디자인 적용 확인
```

---

## ⭐ 4. Step 4. 마커 클릭 → 우측 상세 패널 (30분) — **시그니처 기능**

### 목표
`st_folium()`의 `last_object_clicked` 반환값을 활용해 **Streamlit 우측 컬럼이 실시간으로 업데이트**되는 양방향 UX를 구현. 이게 발표 데모의 클라이맥스입니다.

### 작동 방식

```
사용자 클릭 → Folium JavaScript 이벤트
              ↓
st_folium이 클릭 좌표를 Python에 반환
              ↓
Streamlit 재실행 시 해당 좌표에서 가장 가까운 POI 찾기
              ↓
우측 컬럼(st.columns)에 상세 카드 렌더링
```

### 🤖 Claude Code 프롬프트

````
src/ui/tabs/tab2_map.py를 완성해줘. 마커 클릭 양방향 UX가 핵심.

### 레이아웃

```python
def render(filters: dict):
    st.subheader("🗺️ 원정 동선 지도")
    
    # 데이터 준비
    schedule = load_schedule()
    stadiums = load_stadiums()
    
    # filters["team"]의 첫 원정 경기 선택 (가장 가까운 날짜)
    away = schedule[schedule.away_team == filters["team"]]
    # date_range 필터 적용
    ...
    if len(away) == 0:
        st.info("선택한 기간에 원정 경기가 없습니다.")
        return
    
    selected_game = away.iloc[0]  # 첫 경기 (나중에 selectbox로 확장)
    stadium_row = stadiums[stadiums.short_name == selected_game.stadium].iloc[0]
    
    # 2컬럼 레이아웃: 지도(8), 상세(4)
    col_map, col_detail = st.columns([8, 4])
    
    with col_map:
        # POI 로드
        poi = {
            "food": load_poi(stadium_row.short_name, "food"),
            "stay": load_poi(stadium_row.short_name, "stay"),
            "tour": load_poi(stadium_row.short_name, "tour"),
        }
        
        # 날씨 (캐싱 적용)
        weather = get_forecast_cached(
            stadium_row.lat, stadium_row.lng,
            str(selected_game.date)
        )
        
        # 경로 (Step 5에서 추가, 지금은 None)
        route = None
        
        # 지도 생성
        m = create_map(
            center=(stadium_row.lat, stadium_row.lng),
            zoom=14,
            stadium=stadium_row.to_dict(),
            places=poi,
            route=route,
            weather=weather,
        )
        
        # 렌더링 + 클릭 이벤트 수신
        map_state = render_map_in_streamlit(m, height=550)
    
    with col_detail:
        st.markdown("### 📍 선택한 장소")
        clicked = map_state.get("last_object_clicked")
        
        if clicked is None:
            st.info("지도의 마커를 클릭하면 상세 정보가 표시됩니다.")
        else:
            lat, lng = clicked["lat"], clicked["lng"]
            # 가장 가까운 POI 찾기 (haversine 또는 단순 euclidean)
            nearest = find_nearest_poi(lat, lng, poi)
            render_detail_card(nearest)

### 헬퍼 함수

```python
@st.cache_data(ttl=1800)
def get_forecast_cached(lat, lng, date):
    from src.api.weather_api import get_forecast
    return get_forecast(lat, lng, date)

def find_nearest_poi(lat: float, lng: float, poi: dict) -> dict:
    """클릭 좌표에 가장 가까운 POI 반환. 0.001도 이내면 매치로 간주."""
    import math
    all_places = []
    for cat, places in poi.items():
        for p in places:
            p["_category"] = cat
            all_places.append(p)
    if not all_places:
        return None
    nearest = min(all_places, 
                  key=lambda p: (p["lat"]-lat)**2 + (p["lng"]-lng)**2)
    return nearest

def render_detail_card(poi: dict):
    """우측 컬럼에 POI 상세 정보 카드 렌더링"""
    if poi is None:
        st.warning("해당 위치에 정보가 없습니다.")
        return
    
    # 이미지 (있으면)
    if poi.get("first_image"):
        st.image(poi["first_image"], use_container_width=True)
    
    st.markdown(f"### {poi['title']}")
    category_badges = {"food": "🍽️ 음식점", "stay": "🏨 숙박", "tour": "🎡 관광지"}
    st.caption(category_badges.get(poi.get("_category"), ""))
    
    st.markdown(f"📍 {poi.get('addr', '')}")
    st.markdown(f"📏 경기장에서 **{poi.get('dist_m', '?')}m**")
    if poi.get("tel"):
        st.markdown(f"📞 {poi['tel']}")
    
    # 제휴 쿠폰 (수익 모델 발표용 장식)
    st.success("🎁 제휴 쿠폰: 5% 할인 (데모)")
```

### render_map_in_streamlit 구현 (src/viz/folium_map.py에 추가)

```python
def render_map_in_streamlit(m, height=550, width=None):
    from streamlit_folium import st_folium
    return st_folium(
        m,
        height=height,
        width=width,
        returned_objects=["last_object_clicked", "last_clicked"],
        use_container_width=True,
    )
```

작성 후 탭 2에서 마커 클릭 시 우측 패널이 즉시 바뀌는지 확인.
````

### 검증
- 탭 2 진입 → 지도 + 우측 "마커를 클릭하세요" 안내
- 맛집 마커 클릭 → 우측에 해당 식당 사진·이름·주소·전화번호 카드 표시
- 숙소 마커 클릭 → 우측 카드가 숙소 정보로 교체
- 경기장 마커 클릭 → 경기장 정보 + 우천 확률 표시

> 💡 **발표 데모 핵심**: 이 단계에서 **"클릭 하나로 정보가 살아 움직이는 UX"** 영상을 10초 정도 녹화해두면 발표 때 최고 임팩트를 냅니다.

---

## 🛣️ 5. Step 5. 카카오모빌리티 경로 + Fallback (30분)

### 목표
출발지(사용자 지정 또는 기본값)에서 경기장까지의 **실제 자동차 경로**를 지도에 그리고, API 장애 시 **직선 거리로 Fallback**.

### 🤖 Claude Code 프롬프트

````
src/api/kakao_map.py를 구현해줘. 카카오모빌리티 길찾기 API 클라이언트.

### 환경변수
.env의 KAKAO_MOBILITY_API_KEY 사용 (KAKAO_REST_API_KEY와 별개).
실제 카카오모빌리티 길찾기 API는 카카오 REST API 키로도 호출 가능하니
두 키 중 하나만 있으면 작동하게 fallback 처리.

### Public 함수

```python
@cached_to_disk  # 디렉토리 캐시 데코레이터 (아래 정의)
def get_car_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    waypoints: list[tuple[float, float]] | None = None,
) -> dict:
    """
    Returns:
        {
            "vertexes": [(lat, lng), ...],    # 폴리라인용 좌표 배열
            "duration_sec": 7200,
            "distance_m": 320000,
            "toll_fare": 15600,
            "fallback": False,
        }
        실패/키없음 시:
        {
            "vertexes": [(origin), (destination)],  # 직선
            "duration_sec": None,
            "distance_m": haversine_distance_m,
            "toll_fare": None,
            "fallback": True,
        }
    """
```

### 엔드포인트
`https://apis-navi.kakaomobility.com/v1/directions`

Headers:
- Authorization: KakaoAK {REST_API_KEY}
- Content-Type: application/json

Query params:
- origin: "127.0719,37.5122" (lng,lat 순서 주의!)
- destination: "127.0097,37.2997"
- waypoints: "127.0,37.5|127.1,37.6" (있을 때만)
- priority: "RECOMMEND"

### 응답 파싱
response.routes[0].sections[*].roads[*].vertexes는 [lng, lat, lng, lat, ...] 평탄 배열.
이걸 (lat, lng) 튜플 리스트로 변환.
summary에서 duration (초), distance (미터), toll_fare (원) 추출.

### 디스크 캐싱 데코레이터

```python
def cached_to_disk(func):
    """data/route_cache/{hash}.json으로 응답 캐싱"""
    def wrapper(origin, destination, waypoints=None):
        import hashlib, json, os
        key_str = f"{origin}_{destination}_{waypoints}"
        key = hashlib.md5(key_str.encode()).hexdigest()
        cache_path = f"data/route_cache/{key}.json"
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                return json.load(f)
        result = func(origin, destination, waypoints)
        os.makedirs("data/route_cache", exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result
    return wrapper
```

### Fallback 로직

1. API 키가 없거나 빈 문자열 → 즉시 fallback
2. httpx 요청 실패 (timeout, 5xx) → fallback
3. 응답에 routes가 없거나 비어있음 → fallback

Fallback 시 haversine 거리 계산 (별도 함수).

### 테스트

```python
if __name__ == "__main__":
    # 잠실 → 수원 실제 경로
    route = get_car_route((37.5122, 127.0719), (37.2997, 127.0097))
    print(f"거리: {route['distance_m']/1000:.1f}km")
    print(f"시간: {route['duration_sec']/60:.0f}분")
    print(f"Fallback: {route['fallback']}")
    print(f"정점 수: {len(route['vertexes'])}")
```
````

### 🤖 tab2_map.py 통합 프롬프트

````
src/ui/tabs/tab2_map.py에서 route 파라미터를 실제로 연결해줘.

1. 상단에 "출발지" 입력 UI 추가:
   ```python
   origin_options = {
       "서울역": (37.5547, 126.9707),
       "강남역": (37.4979, 127.0276),
       "내 위치 직접 입력": None,
   }
   origin_choice = st.radio("출발지", list(origin_options.keys()), horizontal=True)
   if origin_choice == "내 위치 직접 입력":
       col_a, col_b = st.columns(2)
       lat = col_a.number_input("위도", value=37.5547, format="%.4f")
       lng = col_b.number_input("경도", value=126.9707, format="%.4f")
       origin = (lat, lng)
   else:
       origin = origin_options[origin_choice]
   ```

2. get_car_route 호출:
   ```python
   from src.api.kakao_map import get_car_route
   route_data = get_car_route(
       origin=origin,
       destination=(stadium_row.lat, stadium_row.lng),
   )
   route = route_data["vertexes"]
   ```

3. 경로 요약 카드를 지도 위에 표시:
   ```python
   c1, c2, c3 = st.columns(3)
   c1.metric("거리", f"{route_data['distance_m']/1000:.1f} km")
   c2.metric("예상 소요", f"{route_data['duration_sec']//60:.0f} 분" 
             if route_data['duration_sec'] else "—")
   c3.metric("통행료", f"{route_data['toll_fare']:,} 원" 
             if route_data['toll_fare'] else "—")
   
   if route_data["fallback"]:
       st.warning("⚠️ 경로 API 연결 실패로 직선 거리로 표시됩니다.")
   ```

4. create_map 호출 시 route=route 전달

작성 후 탭 2에서 출발지 변경 시 경로가 다시 그려지는지 확인.
````

### 검증
- 출발지 "서울역" 선택 → 잠실 제외 원정 경기에 대해 실제 도로 따라 파란 선
- 카카오 API 키 없을 때 → 직선 점선 + "API 연결 실패" 경고
- 동일 출발/목적지 조합 재호출 시 캐시 로드 (로그 확인)

---

## 📊 6. Step 6. Plotly 차트 2종 (30분)

### 목표
탭 1에 구단별 원정 승률 막대그래프, 탭 3에 맛집 산점도 구현.

### 🤖 Claude Code 프롬프트

````
src/viz/plotly_charts.py를 만들어줘.

### bar_away_win_rate 구현

```python
import plotly.graph_objects as go
from src.ui.components.hero import TEAM_COLORS

def bar_away_win_rate(df: pd.DataFrame, highlight_team: str) -> go.Figure:
    """
    구단별 원정 승률 막대그래프. 선택된 팀은 팀 컬러로 강조.
    
    Args:
        df: team_stats_10yr.csv DataFrame
        highlight_team: 강조할 팀 약칭
    """
    # 최근 3년 평균 원정 승률 집계
    recent = df[df.year >= df.year.max() - 2]
    agg = recent.groupby("team")["away_win_rate"].mean().reset_index()
    agg = agg.sort_values("away_win_rate", ascending=False)
    
    # 선택 팀만 컬러, 나머지는 회색
    highlight_color = TEAM_COLORS.get(highlight_team, {}).get("color", "#888")
    colors = [highlight_color if t == highlight_team else "#D1D5DB" 
              for t in agg["team"]]
    
    fig = go.Figure(
        data=[go.Bar(
            x=agg["team"],
            y=agg["away_win_rate"],
            marker_color=colors,
            text=[f"{v:.3f}" for v in agg["away_win_rate"]],
            textposition="outside",
        )]
    )
    fig.update_layout(
        title=f"구단별 최근 3년 원정 승률 (강조: {highlight_team})",
        xaxis_title="구단",
        yaxis_title="원정 승률",
        yaxis_range=[0, 0.7],
        template="simple_white",
        height=380,
        font=dict(family="Pretendard, sans-serif"),
    )
    return fig
```

### scatter_places 구현

```python
def scatter_places(places: list[dict], stadium_coord: tuple) -> go.Figure:
    """
    맛집 평점 × 거리 산점도.
    X축: 거리(m), Y축: 평점(1~5), 크기: dist_m 역수 * 10
    
    Args:
        places: POI 리스트 (food 카테고리)
        stadium_coord: 경기장 (lat, lng) — 호버 정보용
    """
    if not places:
        fig = go.Figure()
        fig.add_annotation(
            text="데이터가 없습니다",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#888"),
        )
        return fig
    
    # 평점이 없으면 랜덤 (더미 데이터 대응)
    import random
    random.seed(42)
    
    x = [p["dist_m"] for p in places]
    y = [p.get("rating") or round(random.uniform(3.5, 4.8), 1) for p in places]
    names = [p["title"] for p in places]
    
    fig = go.Figure(
        data=[go.Scatter(
            x=x, y=y, mode="markers",
            marker=dict(
                size=[max(8, 20 - d/200) for d in x],
                color="#F97316",
                opacity=0.7,
                line=dict(color="white", width=1),
            ),
            text=names,
            hovertemplate="<b>%{text}</b><br>거리: %{x}m<br>평점: %{y}<extra></extra>",
        )]
    )
    fig.update_layout(
        title="경기장 주변 음식점 — 거리 vs 평점",
        xaxis_title="거리 (m)",
        yaxis_title="평점",
        yaxis_range=[3, 5],
        template="simple_white",
        height=400,
        font=dict(family="Pretendard, sans-serif"),
    )
    return fig
```

### tab1_games.py, tab3_places.py 통합

tab1_games.py에 추가:
```python
from src.viz.plotly_charts import bar_away_win_rate
from src.data_loader import load_team_stats

stats = load_team_stats()
fig = bar_away_win_rate(stats, filters["team"])
st.plotly_chart(fig, use_container_width=True)

# 해석 코멘트 (강의 요구 "분석 결과 설명")
best_team = stats.groupby("team")["away_win_rate"].mean().idxmax()
st.caption(f"💡 최근 3년 원정 승률이 가장 높은 팀은 **{best_team}**입니다.")
```

tab3_places.py 완성:
```python
from src.viz.plotly_charts import scatter_places
from src.data_loader import load_poi

# 경기장 POI 로드
food = load_poi(selected_stadium, "food")
stay = load_poi(selected_stadium, "stay")
tour = load_poi(selected_stadium, "tour")

# 서브탭
sub_tabs = st.tabs(["🍽️ 음식점", "🏨 숙박", "🎡 관광지"])

with sub_tabs[0]:
    st.plotly_chart(scatter_places(food, ...), use_container_width=True)
    # 카드 리스트 (expander로)
    for item in food[:10]:
        with st.expander(f"🍽️ {item['title']}"):
            st.markdown(f"📍 {item.get('addr', '')}")
            st.markdown(f"📏 {item.get('dist_m', 0)}m")
            if item.get("first_image"):
                st.image(item["first_image"], width=300)

with sub_tabs[1]:
    # 숙박 카드만 (산점도 생략)
    for item in stay[:10]: ...

with sub_tabs[2]:
    for item in tour[:10]: ...
```

작성 후 두 탭에서 차트가 렌더링되는지 확인.
````

### 검증
- 탭 1: 10개 구단 막대그래프, 선택된 팀만 컬러
- 탭 1 하단: "최근 3년 원정 승률 가장 높은 팀은..." 해석 문구
- 탭 3 음식점 서브탭: 산점도 + 카드 리스트

---

## 🎯 7. Step 7. 승률 게이지 인디케이터 (20분, 권장)

### 목표
탭 1 경기 카드에 **원형 게이지**로 승률 시각화. Plotly Indicator 활용. Phase 4의 예측 모델과 연동 예정이지만, 지금은 더미 값으로 먼저 렌더링.

### 🤖 Claude Code 프롬프트

````
src/viz/plotly_charts.py에 gauge_win_rate 함수를 추가.

```python
def gauge_win_rate(prob: float, team_name: str) -> go.Figure:
    """
    승률 예측 게이지.
    Args:
        prob: 0.0 ~ 1.0
        team_name: 팀 약칭
    """
    color = TEAM_COLORS.get(team_name, {}).get("color", "#3B82F6")
    pct = prob * 100
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number={"suffix": "%", "font": {"size": 36}},
        delta={"reference": 50, "increasing": {"color": color}, 
               "decreasing": {"color": "#6B7280"}},
        title={"text": f"{team_name} 승률 예측", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color, "thickness": 0.7},
            "steps": [
                {"range": [0, 40], "color": "#FEE2E2"},
                {"range": [40, 60], "color": "#FEF3C7"},
                {"range": [60, 100], "color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.75,
                "value": 50,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Pretendard, sans-serif"),
    )
    return fig
```

tab1_games.py에서 선택된 경기 정보 카드에 사용:

```python
# 임시 더미값 (Phase 4에서 실제 모델로 교체)
import random
random.seed(selected_game.game_id.__hash__() % 1000)
win_prob = round(random.uniform(0.35, 0.65), 2)

col_info, col_gauge = st.columns([3, 2])
with col_info:
    st.markdown(f"### 🆚 vs {selected_game.home_team} @ {selected_game.stadium}")
    st.markdown(f"📅 {selected_game.date} ({selected_game.day_of_week})")
    st.markdown(f"🕐 {selected_game.start_time}")

with col_gauge:
    st.plotly_chart(
        gauge_win_rate(win_prob, filters["team"]),
        use_container_width=True,
    )
```

작성 후 탭 1에 게이지가 렌더링되는지 확인.
````

### 검증
- 탭 1 경기 카드 오른쪽에 원형 게이지
- 게이지 색상이 선택 팀 컬러로 변화
- 50% 기준선에서 빨강/노랑/녹색 영역 구분

---

## 🔗 8. Step 8. Tab 2, 3 최종 통합 & 공통 함수 재사용 (10분)

이 Step은 **점검 성격**이에요. Step 2~7에서 만든 함수들이 탭 2·3에 일관되게 쓰이는지 확인.

### 점검 항목

- [ ] `create_map()`이 탭 2에서만 호출되는가? 탭 3에서 미니맵이 필요하면 `zoom=15, show_route=False` 인자로 호출
- [ ] POI 카드 UI를 만드는 로직이 중복되지 않았는가? `src/ui/components/place_card.py`로 추출
- [ ] 차트 해석 문구(caption)가 모든 차트에 있는가? (강의 요구 사항)
- [ ] 빈 데이터 경고(`st.info` 또는 `st.warning`)가 모든 데이터 로딩 지점에 있는가?

### 🤖 Claude Code 프롬프트

````
src/ui/components/place_card.py를 만들어서
탭 2 우측 상세 패널과 탭 3 카드 리스트에서 공통으로 쓰는
POI 카드 UI 함수를 추출해줘.

```python
def render_place_card(place: dict, compact: bool = False):
    """
    Args:
        place: POI dict
        compact: True면 이미지 작게, False면 풀 사이즈
    """
```

탭 2의 render_detail_card와 탭 3의 카드 렌더링이 이 함수를 호출하도록 리팩토링.
````

---

## 🔍 9. Step 9. 검증 & 시연 준비

### 자동 검증 스크립트

### 🤖 Claude Code 프롬프트

````
scripts/validate_phase3.py를 작성해줘. 다음을 검증:

1. 파일 존재
   - src/viz/folium_map.py, plotly_charts.py, popup_builder.py
   - src/api/kakao_map.py
   - src/ui/components/place_card.py

2. 함수 시그니처 (AST 파싱)
   - create_map, render_map_in_streamlit, bar_away_win_rate,
     scatter_places, gauge_win_rate, get_car_route가 모두 정의됨

3. 런타임 smoke test
   - create_map으로 지도 생성 후 m._repr_html_()에 
     "folium" 문자열 포함 확인
   - bar_away_win_rate로 figure 생성 후 figure.data 존재 확인
   - get_car_route 호출 후 반환 dict에 "vertexes", "fallback" 키 존재

4. 의존성 확인
   - streamlit-folium, plotly가 pip list에 존재

출력은 validate_phase2.py와 동일 스타일.
````

### 시연 체크리스트 (발표 데모용 3분 시나리오)

1. **0:00~0:30** — 앱 첫 화면, 히어로 + 사이드바 보여주기
2. **0:30~1:00** — 팀 로고 셀렉터에서 다른 팀 클릭 → 색상 전환
3. **1:00~1:30** — 탭 2 이동, **마커 클릭 → 우측 패널 실시간 업데이트** ★
4. **1:30~2:00** — 출발지 변경 → 경로 다시 그려짐, 거리/시간 메트릭 변경
5. **2:00~2:30** — 탭 1 이동, **승률 게이지 + 막대그래프** 강조
6. **2:30~3:00** — 탭 3 이동, 맛집 산점도 + 카드 리스트

### 스크린샷 촬영
- 탭 2 전체 (지도 + 우측 상세 패널)
- 탭 1 승률 게이지 클로즈업
- 탭 3 산점도

---

## 👥 10. 병렬 작업 가이드

### 🤖 AI / 분석 담당
- Phase 4 준비 가속:
  - `src/ai/predict.py` 로지스틱 회귀 학습 완성 (이번 Phase의 더미 `win_prob` 대체할 모델)
  - 모델 산출물 `models/win_rate_model.pkl` 저장
  - 학습 피처: `team_stats_10yr.csv`의 `home_win_rate`, `away_win_rate`, 최근 3년 평균 승률
- OpenAI API 구조화된 출력 실험 (tool_use 예제)

### 🎨 프론트 / UX 담당
- Phase 2에서 만든 `badges.html`의 호버·클릭 애니메이션 폴리싱
- `assets/css/style.css`에 다크모드 변수 초안 (Phase 5용)
- 모바일 뷰포트에서 레이아웃 깨짐 체크 및 이슈 리스트업

### 🧑‍✈️ 팀장 / 데이터 엔지니어
- Phase 4, 5 가이드 문서 초안
- Streamlit Cloud 배포 리허설 (현재 상태 한 번 배포)
- 발표 슬라이드 아키텍처 다이어그램 작성 (Mermaid 또는 Figma)

---

## 🧾 11. 완료 체크리스트

### 지도 (필수)
- [ ] `create_map()` 4개 레이어 + LayerControl 작동
- [ ] MarkerCluster 적용 (POI 30개 이상)
- [ ] 마커 클릭 → 우측 상세 패널 업데이트 ★ 시그니처 기능
- [ ] 카카오모빌리티 경로 또는 Fallback 표시
- [ ] 경기장 Popup에 우천 확률 포함

### 차트 (필수 2개 + 권장 1개)
- [ ] 구단별 원정 승률 막대그래프 (탭 1)
- [ ] 맛집 평점 × 거리 산점도 (탭 3)
- [ ] 승률 게이지 인디케이터 (탭 1) — 권장

### 공통
- [ ] `place_card.py` 공통 컴포넌트 추출 완료
- [ ] 모든 차트에 해석 캡션 추가
- [ ] 빈 데이터 경고 처리 전수 완료
- [ ] `scripts/validate_phase3.py` PASS
- [ ] 3분 데모 시나리오 리허설 1회 이상
- [ ] 스크린샷 3종 촬영

---

## 🆘 12. 트러블슈팅 FAQ

### Q1. `st_folium()`이 매번 지도를 새로 그려 느립니다
`returned_objects=["last_object_clicked"]`로 관심 이벤트만 지정하세요. 또 `key="map_tab2"`처럼 고유 key를 주면 rerun 시 기존 인스턴스 재사용으로 성능이 개선됩니다.

### Q2. 마커가 너무 많아서 브라우저가 렌더링 못 합니다
`MarkerCluster`를 적용하면 500개 이상도 원활합니다. `from folium.plugins import MarkerCluster` 후 FeatureGroup 대신 쓰세요. 또는 `zoom_start`를 낮춰 초기 뷰에서 군집화.

### Q3. 카카오모빌리티 401 Unauthorized
- 헤더가 `Authorization: KakaoAK {key}` 형식인지 확인 (공백 포함)
- 카카오 REST API 키(앱 설정의 "REST API 키")를 사용. JavaScript 키 아님
- 앱 관리 → 플랫폼 → Web 설정에 도메인 등록했는지 확인 (localhost 포함)

### Q4. 한글 Popup이 네모(□)로 보입니다
CSS에 폰트 지정이 안 된 상태. `popup_builder.py`의 `<div style="font-family: 'Pretendard', 'Noto Sans KR', sans-serif;">`로 감쌌는지 확인. 그래도 안 되면 `folium.Map()` 생성 시 `tiles="CartoDB positron"`으로 변경.

### Q5. Plotly 차트가 Streamlit에서 잘립니다
`use_container_width=True` 옵션이 빠졌거나, 컨테이너(columns)의 비율이 너무 작아서. `col1, col2 = st.columns([3, 2])`처럼 비율을 주거나 전체 너비로 배치.

### Q6. `last_object_clicked`가 None만 반환됩니다
`st_folium()`의 `returned_objects` 인자에 `"last_object_clicked"` 문자열이 정확히 포함되어 있어야 합니다. 오타(`last_clicked_object` 등) 주의.

### Q7. 경로 폴리라인이 지도 밖으로 튀어 나갑니다
`folium.Map` 생성 후 `m.fit_bounds([...])`로 경로 전체가 보이게 조정. 또는 `create_map()` 내부에서 route가 있으면 자동으로 fit_bounds 호출하도록 로직 추가.

### Q8. TourAPI 이미지가 HTTP라 Streamlit에서 blocked
Streamlit이 HTTPS면 혼합 콘텐츠 차단. 해결: `img src="https://"` 강제 치환, 또는 `first_image.replace("http://", "https://")` 전처리.

---

## 🎬 13. 다음 Phase로 넘어가기 전 확인

다음 5가지가 ✅이면 Phase 4 시작 준비 완료.

1. ✅ `python scripts/validate_phase3.py` 종료 코드 **0**
2. ✅ 탭 2 마커 클릭 양방향 UX가 정상 작동
3. ✅ 탭 1, 3에 Plotly 차트가 팀 컬러로 렌더링
4. ✅ 카카오 API 실패 시 Fallback이 정상 동작 (한 번이라도 시험)
5. ✅ `CLAUDE.md` "현재 진행 Phase"가 **Phase 4**로 업데이트

### Phase 4로 전환하는 Claude Code 프롬프트

````
Phase 3 지도 & 시각화가 완료됐어. scripts/validate_phase3.py 실행해
모두 PASS인지 확인.

통과했다면:
1. CLAUDE.md의 "현재 진행 Phase"를 Phase 4로 업데이트
2. IMPLEMENTATION_PLAN.md Phase 4 섹션 참고
3. 첫 작업인 "4-1. 승률 예측 모델"을 src/ai/predict.py에 구현
4. 학습 데이터는 data/team_stats_10yr.csv
5. 학습된 모델을 models/win_rate_model.pkl로 저장
6. tab1_games.py의 더미 win_prob을 실제 모델 예측값으로 교체

실패 항목이 있으면 해결 후 진행.
````

---

## 📚 참고

- 전체 계획: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) Phase 3 섹션
- 이전 가이드: [PHASE2_GUIDE.md](./PHASE2_GUIDE.md)
- streamlit-folium 문서: https://folium.streamlit.app/
- Plotly Python 갤러리: https://plotly.com/python/
- 카카오모빌리티 길찾기 API: https://developers.kakaomobility.com/docs/navi-api/directions/
- Folium 공식 문서: https://python-visualization.github.io/folium/

---

*가이드 마지막 업데이트: 2026-04-17*
*예상 총 소요 시간: 2시간 (지도·시각화 담당 1명 기준)*
