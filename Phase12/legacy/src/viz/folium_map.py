"""Folium 인터랙티브 지도 — 경기장 + 4개 POI 레이어 + 경로 폴리라인.

VIZ_CONTRACT.md 계약 준수.
"""
from __future__ import annotations

import logging
from typing import Any

import folium
from folium.plugins import MarkerCluster

from src.viz.popup_builder import place_popup_html, stadium_popup_html

log = logging.getLogger(__name__)

LAYER_STYLES: dict[str, dict[str, str]] = {
    "stadium": {"color": "red", "icon": "baseball-ball", "prefix": "fa"},
    "food": {"color": "orange", "icon": "utensils", "prefix": "fa"},
    "stay": {"color": "blue", "icon": "bed", "prefix": "fa"},
    "tour": {"color": "green", "icon": "camera", "prefix": "fa"},
}

CATEGORY_LABELS_KO: dict[str, str] = {
    "stadium": "🏟️ 경기장",
    "food": "🍽️ 음식점",
    "stay": "🏨 숙박",
    "tour": "🎡 관광지",
}

_CLUSTER_THRESHOLD = 20


def _marker(place: dict, category: str) -> folium.Marker:
    style = LAYER_STYLES.get(category, LAYER_STYLES["tour"])
    icon = folium.Icon(color=style["color"], icon=style["icon"], prefix=style["prefix"])
    popup = folium.Popup(html=place_popup_html(place), max_width=280)
    return folium.Marker(
        location=(float(place["lat"]), float(place["lng"])),
        popup=popup,
        tooltip=str(place.get("title", "")),
        icon=icon,
    )


def _stadium_marker(stadium: dict, weather: dict | None) -> folium.Marker:
    style = LAYER_STYLES["stadium"]
    icon = folium.Icon(color=style["color"], icon=style["icon"], prefix=style["prefix"])
    popup = folium.Popup(html=stadium_popup_html(stadium, weather), max_width=300)
    return folium.Marker(
        location=(float(stadium["lat"]), float(stadium["lng"])),
        popup=popup,
        tooltip=str(stadium.get("stadium_name", stadium.get("short_name", ""))),
        icon=icon,
    )


def create_map(
    center: tuple[float, float],
    zoom: int = 13,
    stadium: dict | None = None,
    places: dict[str, list[dict]] | None = None,
    route: list[tuple[float, float]] | None = None,
    weather: dict | None = None,
) -> folium.Map:
    """원정 플래너 지도 생성 (VIZ_CONTRACT 준수)."""
    m = folium.Map(
        location=[center[0], center[1]],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # 경기장 레이어
    stadium_group = folium.FeatureGroup(name=CATEGORY_LABELS_KO["stadium"], show=True)
    if stadium:
        try:
            _stadium_marker(stadium, weather).add_to(stadium_group)
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("Stadium 마커 생성 실패: %s", exc)
    stadium_group.add_to(m)

    # POI 레이어 (food / stay / tour)
    if places:
        for category in ("food", "stay", "tour"):
            items = places.get(category) or []
            group = folium.FeatureGroup(name=CATEGORY_LABELS_KO[category], show=True)
            target: Any
            if len(items) > _CLUSTER_THRESHOLD:
                cluster = MarkerCluster(name=CATEGORY_LABELS_KO[category])
                cluster.add_to(group)
                target = cluster
            else:
                target = group
            for place in items:
                try:
                    _marker(place, category).add_to(target)
                except (KeyError, TypeError, ValueError) as exc:
                    log.warning("POI 마커 생성 실패 (%s): %s", category, exc)
            group.add_to(m)

    # 경로 폴리라인
    if route and len(route) >= 2:
        is_fallback = len(route) == 2
        dash = "8,8" if is_fallback else None
        folium.PolyLine(
            locations=[(lat, lng) for lat, lng in route],
            color="#0066FF",
            weight=4,
            opacity=0.75,
            dash_array=dash,
            tooltip="출발지 → 경기장",
        ).add_to(m)

        # 경로 전체가 보이도록 fit_bounds (stadium 중심보다 넓게)
        lats = [p[0] for p in route]
        lngs = [p[1] for p in route]
        m.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]], padding=(30, 30))

    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    return m


def render_map_in_streamlit(
    m: folium.Map,
    height: int = 550,
    width: int | None = None,
    key: str | None = "folium_map",
) -> dict:
    """st_folium으로 지도 렌더 + 클릭 이벤트 dict 반환."""
    from streamlit_folium import st_folium

    kwargs: dict[str, Any] = {
        "height": height,
        "returned_objects": ["last_object_clicked", "last_clicked"],
        "use_container_width": True,
        "key": key,
    }
    if width is not None:
        kwargs["width"] = width
    result = st_folium(m, **kwargs)
    return result or {}


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(ROOT))
    from src import config

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    stadium = {
        "stadium_name": "잠실야구장",
        "short_name": "잠실",
        "home_team": "LG,두산",
        "address": "서울특별시 송파구 올림픽로 25",
        "subway_station": "잠실종합운동장(2,9호선)",
        "capacity": 25000,
        "lat": 37.5122,
        "lng": 127.0719,
    }
    food = json.loads((config.POI_CACHE_DIR / "잠실_food.json").read_text(encoding="utf-8"))
    stay = json.loads((config.POI_CACHE_DIR / "잠실_stay.json").read_text(encoding="utf-8"))
    tour = json.loads((config.POI_CACHE_DIR / "잠실_tour.json").read_text(encoding="utf-8"))

    route = [
        (37.5547, 126.9707),   # 서울역
        (37.5400, 126.9900),
        (37.5300, 127.0200),
        (37.5200, 127.0500),
        (37.5122, 127.0719),   # 잠실
    ]
    weather = {
        "date": "2026-04-18", "sky": "맑음",
        "precipitation_prob": 20, "temp_min": 8, "temp_max": 18,
        "rain_expected": False,
    }

    m = create_map(
        center=(37.5122, 127.0719), zoom=14,
        stadium=stadium,
        places={"food": food, "stay": stay, "tour": tour},
        route=route, weather=weather,
    )
    out = Path("/tmp/test_map.html")
    m.save(str(out))
    print(f"✅ 지도 HTML 저장: {out}")
    print(f"브라우저: open {out}")
