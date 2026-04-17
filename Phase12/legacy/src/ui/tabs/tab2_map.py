"""Tab 2 — 원정 동선 지도: Folium + 마커 클릭 양방향 UX + 카카오 경로."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.api.kakao_map import get_car_route
from src.api.weather_api import get_forecast
from src.data_loader import load_poi, load_schedule, load_stadiums
from src.ui.components.place_card import render_place_card
from src.viz.folium_map import create_map, render_map_in_streamlit

_ORIGIN_PRESETS = {
    "서울역": (37.5547, 126.9707),
    "강남역": (37.4979, 127.0276),
    "수원역": (37.2657, 127.0009),
    "대전역": (36.3322, 127.4342),
    "내 위치 직접 입력": None,
}


@st.cache_data(ttl=1800, show_spinner=False)
def _get_forecast_cached(lat: float, lng: float, date_str: str) -> dict:
    return get_forecast(lat, lng, date_str)


@st.cache_data(ttl=3600, show_spinner=False)
def _get_route_cached(origin: tuple, destination: tuple) -> dict:
    return get_car_route(origin, destination)


def _find_nearest_poi(lat: float, lng: float, poi: dict[str, list[dict]]) -> dict | None:
    best: dict | None = None
    best_d = float("inf")
    for cat, items in poi.items():
        for p in items:
            try:
                plat = float(p["lat"])
                plng = float(p["lng"])
            except (KeyError, TypeError, ValueError):
                continue
            d = (plat - lat) ** 2 + (plng - lng) ** 2
            if d < best_d:
                best_d = d
                copy = dict(p)
                copy["_category"] = cat
                best = copy
    return best


def render(filters: dict) -> None:
    st.subheader("🗺️ 원정 동선 지도")

    schedule = load_schedule()
    stadiums = load_stadiums()

    team = filters.get("team", "LG")
    date_range = filters.get("date_range")
    away = schedule[schedule["away_team"] == team]
    if date_range and len(date_range) == 2:
        start, end = date_range
        mask = (away["date"] >= pd.Timestamp(start)) & (away["date"] <= pd.Timestamp(end))
        away = away.loc[mask]
    away = away.sort_values("date").reset_index(drop=True)

    if len(away) == 0:
        st.info("선택한 기간에 원정 경기가 없습니다. 사이드바에서 기간을 넓혀보세요.")
        return

    # 선택 경기 + 출발지 선택
    col_game, col_origin = st.columns([3, 2])
    with col_game:
        away["_label"] = away.apply(
            lambda r: f"{r['date'].strftime('%Y-%m-%d')} @ {r['stadium']} vs {r['home_team']}",
            axis=1,
        )
        picked_label = st.selectbox(
            "🎯 경기 선택",
            options=away["_label"].tolist(),
            index=0,
            key="tab2_selected_game",
        )
        selected_game = away[away["_label"] == picked_label].iloc[0]

    with col_origin:
        origin_choice = st.selectbox(
            "🚗 출발지",
            options=list(_ORIGIN_PRESETS.keys()),
            index=0,
            key="tab2_origin",
        )

    if origin_choice == "내 위치 직접 입력":
        col_lat, col_lng = st.columns(2)
        lat = col_lat.number_input("위도", value=37.5547, format="%.4f", key="tab2_lat")
        lng = col_lng.number_input("경도", value=126.9707, format="%.4f", key="tab2_lng")
        origin = (float(lat), float(lng))
    else:
        origin = _ORIGIN_PRESETS[origin_choice]

    stadium_row = stadiums[stadiums["short_name"] == selected_game["stadium"]]
    if stadium_row.empty:
        st.warning(f"구장 정보가 없습니다: {selected_game['stadium']}")
        return
    stadium = stadium_row.iloc[0].to_dict()

    # 경로 조회 (캐시)
    dest = (float(stadium["lat"]), float(stadium["lng"]))
    route_data = _get_route_cached(origin, dest)

    # 경로 요약 메트릭
    c1, c2, c3 = st.columns(3)
    dist_km = (route_data.get("distance_m") or 0) / 1000
    c1.metric("거리", f"{dist_km:.1f} km")
    dur = route_data.get("duration_sec")
    c2.metric("예상 소요", f"{dur // 60:.0f} 분" if dur else "—")
    toll = route_data.get("toll_fare")
    c3.metric("통행료", f"{toll:,} 원" if toll else "—")

    if route_data.get("fallback"):
        st.warning(
            "⚠️ 카카오모빌리티 길찾기 API 미등록 또는 실패 — **직선 거리로 표시**됩니다. "
            ".env의 `KAKAO_MOBILITY_API_KEY` 또는 `KAKAO_REST_API_KEY`에 길찾기 "
            "서비스 승인이 필요합니다."
        )

    # POI + 날씨
    short = stadium["short_name"]
    poi = {
        "food": load_poi(short, "food"),
        "stay": load_poi(short, "stay"),
        "tour": load_poi(short, "tour"),
    }
    weather = _get_forecast_cached(
        float(stadium["lat"]),
        float(stadium["lng"]),
        selected_game["date"].strftime("%Y-%m-%d"),
    )

    # 지도 + 상세 패널
    col_map, col_detail = st.columns([8, 4])

    with col_map:
        m = create_map(
            center=(float(stadium["lat"]), float(stadium["lng"])),
            zoom=14,
            stadium=stadium,
            places=poi,
            route=route_data.get("vertexes"),
            weather=weather,
        )
        map_state = render_map_in_streamlit(m, height=560, key="tab2_folium_map")

    with col_detail:
        st.markdown("### 📍 선택한 장소")
        clicked = map_state.get("last_object_clicked")
        if not clicked:
            st.info("지도의 마커를 클릭하면 상세 정보가 표시됩니다.")
        else:
            lat_c = clicked.get("lat")
            lng_c = clicked.get("lng")
            if lat_c is None or lng_c is None:
                st.warning("클릭 좌표를 읽을 수 없습니다.")
            else:
                nearest = _find_nearest_poi(float(lat_c), float(lng_c), poi)
                if nearest:
                    render_place_card(nearest, compact=True)
                else:
                    # 경기장 마커일 가능성
                    st.markdown(f"### ⚾ {stadium.get('stadium_name', short)}")
                    st.markdown(f"📍 {stadium.get('address', '')}")
                    st.markdown(f"🚇 {stadium.get('subway_station', '')}")
                    if weather and weather.get("sky"):
                        pop = weather.get("precipitation_prob", 0)
                        st.markdown(f"⛅ {weather['sky']} · 강수 확률 {pop}%")
