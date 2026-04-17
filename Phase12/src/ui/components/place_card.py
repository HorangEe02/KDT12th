"""POI 공통 카드 컴포넌트 — tab2 상세 패널 + tab3 카드 리스트에서 공용으로 사용."""
from __future__ import annotations

import streamlit as st

CATEGORY_LABEL = {
    "food": "🍽️ 음식점",
    "stay": "🏨 숙박",
    "tour": "🎡 관광지",
}
CATEGORY_ACCENT = {
    "food": "#F97316",
    "stay": "#3B82F6",
    "tour": "#10B981",
}


def _https(url: str) -> str:
    if not url:
        return ""
    return url.replace("http://", "https://", 1)


def render_place_card(place: dict | None, compact: bool = False) -> None:
    """POI dict → Streamlit 카드 렌더.

    Args:
        place: POI 스키마 dict. None이면 경고.
        compact: True면 이미지 작게, 전화/제휴 쿠폰 생략.
    """
    if not place:
        st.warning("표시할 장소 정보가 없습니다.")
        return

    category = place.get("_category") or place.get("category") or "tour"
    label = CATEGORY_LABEL.get(category, "📍 장소")
    accent = CATEGORY_ACCENT.get(category, "#475569")

    title = str(place.get("title") or "이름 없음")
    addr = str(place.get("addr") or "")
    tel = str(place.get("tel") or "")
    first_image = _https(str(place.get("first_image") or ""))
    dist_m = place.get("dist_m") or 0
    try:
        dist_str = f"{int(dist_m):,}m"
    except (ValueError, TypeError):
        dist_str = "—"

    if first_image:
        width = 280 if compact else None
        try:
            if compact:
                st.image(first_image, width=width)
            else:
                st.image(first_image, use_container_width=True)
        except Exception:
            pass

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
        f"<span style='background:{accent};color:white;padding:2px 10px;"
        f"border-radius:999px;font-size:0.7rem;font-weight:700;letter-spacing:0.08em;"
        f"text-transform:uppercase;'>{label}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"### {title}")

    if addr:
        st.markdown(f"📍 {addr}")
    st.markdown(f"📏 경기장에서 **{dist_str}**")
    if tel and not compact:
        st.markdown(f"📞 {tel}")

    if not compact:
        st.success("🎁 제휴 쿠폰: 5% 할인 (데모)")
