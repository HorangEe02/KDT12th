"""Folium Popup HTML 빌더 — 경기장 / POI용 카드 HTML 생성.

보안: 모든 동적 문자열은 html.escape() 처리. 이미지 URL은 https 강제 치환.
"""
from __future__ import annotations

import html
from typing import Any

CATEGORY_COLOR = {
    "food": "#F97316",
    "stay": "#3B82F6",
    "tour": "#10B981",
}
CATEGORY_EMOJI = {
    "food": "🍽️",
    "stay": "🏨",
    "tour": "🎡",
}
CATEGORY_LABELS = {
    "food": "음식점",
    "stay": "숙박",
    "tour": "관광지",
}

_FONT_STACK = "'Plus Jakarta Sans', 'Pretendard', 'Noto Sans KR', sans-serif"


def _safe(v: Any) -> str:
    if v is None:
        return ""
    return html.escape(str(v))


def _https(url: str) -> str:
    if not url:
        return ""
    return url.replace("http://", "https://", 1)


def stadium_popup_html(stadium: dict, weather: dict | None = None) -> str:
    """경기장 마커 Popup HTML.

    Args:
        stadium: stadiums.csv 한 행 dict
        weather: weather_api 반환 dict (Optional)
    """
    stadium_name = _safe(stadium.get("stadium_name") or stadium.get("short_name"))
    home_team = _safe(stadium.get("home_team"))
    address = _safe(stadium.get("address"))
    subway = _safe(stadium.get("subway_station"))
    capacity = stadium.get("capacity") or 0
    try:
        capacity_str = f"{int(capacity):,}"
    except (ValueError, TypeError):
        capacity_str = "—"

    weather_block = ""
    if weather and weather.get("sky") is not None:
        sky = _safe(weather.get("sky"))
        pop = weather.get("precipitation_prob")
        pop_str = _safe(pop) if pop is not None else "—"
        temp_min = weather.get("temp_min")
        temp_max = weather.get("temp_max")
        temp_line = ""
        if temp_min is not None and temp_max is not None:
            temp_line = (
                f"<div style='font-size:11px;color:#555;margin-top:4px;'>"
                f"🌡️ {temp_min}°C ~ {temp_max}°C</div>"
            )
        rain_warn = ""
        if isinstance(pop, (int, float)) and pop >= 60:
            rain_warn = (
                "<div style='display:inline-block;margin-top:6px;padding:3px 8px;"
                "background:#FEE2E2;color:#991B1B;border-radius:999px;font-size:11px;"
                "font-weight:700;'>☔ 우산 필수</div>"
            )
        weather_block = (
            f"<div style='margin-top:10px;padding:8px 10px;background:#EFF6FF;"
            f"border-radius:6px;'>"
            f"<div style='font-size:12px;color:#1E40AF;font-weight:600;'>"
            f"⛅ {sky} · 강수확률 {pop_str}%</div>"
            f"{temp_line}{rain_warn}</div>"
        )

    return (
        f"<div style=\"font-family:{_FONT_STACK};width:270px;\">"
        f"<div style='background:#DC2626;color:white;padding:9px 12px;"
        f"border-radius:6px 6px 0 0;font-weight:800;font-size:15px;'>"
        f"⚾ {stadium_name}</div>"
        f"<div style='padding:10px 12px;background:white;color:#1F2937;'>"
        f"<div style='color:#666;font-size:12px;margin-bottom:6px;'>🏠 홈팀: {home_team}</div>"
        f"<div style='font-size:13px;margin-bottom:6px;'>📍 {address}</div>"
        f"<div style='font-size:12px;'>🚇 {subway}</div>"
        f"{weather_block}"
        f"<div style='color:#9CA3AF;font-size:11px;margin-top:8px;'>"
        f"좌석 수: {capacity_str}석</div>"
        f"</div></div>"
    )


def place_popup_html(place: dict) -> str:
    """POI 마커 Popup HTML."""
    category = str(place.get("category", "tour"))
    color = CATEGORY_COLOR.get(category, "#475569")
    emoji = CATEGORY_EMOJI.get(category, "📍")
    label = CATEGORY_LABELS.get(category, "장소")

    title = _safe(place.get("title"))
    addr = _safe(place.get("addr"))
    tel = _safe(place.get("tel"))
    first_image = _https(str(place.get("first_image", "")))
    dist_m = place.get("dist_m") or 0
    try:
        dist_str = f"{int(dist_m):,}"
    except (ValueError, TypeError):
        dist_str = "—"

    image_block = ""
    if first_image:
        image_block = (
            f"<img src='{_safe(first_image)}' "
            f"style='width:100%;height:120px;object-fit:cover;"
            f"border-radius:4px;margin-bottom:8px;' alt='' />"
        )

    tel_block = (
        f"<div style='font-size:12px;color:#555;margin-top:4px;'>📞 {tel}</div>"
        if tel else ""
    )

    return (
        f"<div style=\"font-family:{_FONT_STACK};width:250px;\">"
        f"<div style='background:{color};color:white;padding:9px 12px;"
        f"border-radius:6px 6px 0 0;font-weight:800;font-size:14px;'>"
        f"{emoji} {title}</div>"
        f"<div style='padding:10px 12px;background:white;color:#1F2937;'>"
        f"{image_block}"
        f"<div style='font-size:12px;color:#9CA3AF;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-bottom:4px;'>{label}</div>"
        f"<div style='font-size:12px;'>{addr}</div>"
        f"<div style='font-size:12px;color:#666;margin-top:4px;'>"
        f"📏 경기장에서 {dist_str}m</div>"
        f"{tel_block}"
        f"</div></div>"
    )


if __name__ == "__main__":
    demo_stadium = {
        "stadium_name": "잠실야구장",
        "home_team": "LG,두산",
        "address": "서울특별시 송파구 올림픽로 25",
        "subway_station": "잠실종합운동장(2,9호선)",
        "capacity": 25000,
    }
    demo_weather = {
        "sky": "구름많음",
        "precipitation_prob": 65,
        "temp_min": 8,
        "temp_max": 18,
        "rain_expected": True,
    }
    demo_place = {
        "title": "잠실 맛있는집",
        "category": "food",
        "addr": "서울특별시 송파구 근처 맛있는집",
        "tel": "02-111-2222",
        "first_image": "http://example.com/img.jpg",
        "dist_m": 420,
    }
    print("--- stadium ---")
    print(stadium_popup_html(demo_stadium, demo_weather))
    print("--- place ---")
    print(place_popup_html(demo_place))
