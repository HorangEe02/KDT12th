"""Tab 3 — 경기장 주변 맛집·숙소·관광지. 산점도 + 카드 리스트."""
from __future__ import annotations

import streamlit as st

from src.data_loader import load_poi, load_stadiums
from src.ui.components.place_card import render_place_card
from src.viz.plotly_charts import scatter_places


def _sorted_by_distance(items: list[dict]) -> list[dict]:
    def _key(p: dict) -> float:
        try:
            return float(p.get("dist_m") or 0)
        except (ValueError, TypeError):
            return float("inf")
    return sorted(items, key=_key)


def _render_card_list(items: list[dict], category: str, limit: int = 10) -> None:
    if not items:
        st.warning(f"{category} POI 캐시가 없습니다. `scripts/cache_poi.py --force` 실행을 확인하세요.")
        return
    for i, item in enumerate(_sorted_by_distance(items)[:limit]):
        item = {**item, "_category": category}
        with st.expander(
            f"{item.get('title', '이름 없음')}  ·  {int(item.get('dist_m') or 0):,}m",
            expanded=(i == 0),
        ):
            render_place_card(item, compact=True)


def render(filters: dict) -> None:
    st.subheader("🍽️ 경기장 주변 맛집·숙소·관광지")

    stadiums = load_stadiums()
    shorts = stadiums["short_name"].tolist()

    # filters["team"]의 원정 구장이 아닌, 사용자가 보고 싶은 구장 선택
    # (여러 팀이 잠실을 쓰는 경우도 있어 원정지 매칭은 복잡 → 독립 셀렉트)
    default_idx = 0
    sample = st.selectbox(
        "🏟️ 구장 선택",
        options=shorts,
        index=default_idx,
        key="tab3_stadium",
    )
    stadium_row = stadiums[stadiums["short_name"] == sample].iloc[0]
    stadium_coord = (float(stadium_row["lat"]), float(stadium_row["lng"]))

    food = load_poi(sample, "food")
    stay = load_poi(sample, "stay")
    tour = load_poi(sample, "tour")

    c1, c2, c3 = st.columns(3)
    c1.metric("🍽️ 음식점", f"{len(food)}곳")
    c2.metric("🏨 숙박", f"{len(stay)}곳")
    c3.metric("🎡 관광지", f"{len(tour)}곳")

    sub_tabs = st.tabs(["🍽️ 음식점", "🏨 숙박", "🎡 관광지"])

    with sub_tabs[0]:
        st.markdown("#### 📊 거리 × 평점 산점도")
        fig = scatter_places(food, stadium_coord)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "💡 마커 크기는 경기장과의 가까운 정도를 표현합니다 "
            "(실평점은 Phase 4에서 TourAPI detailInfo 연동 예정)."
        )
        st.markdown("#### 🧾 가까운 음식점 TOP 10")
        _render_card_list(food, "food", limit=10)

    with sub_tabs[1]:
        st.markdown("#### 🧾 가까운 숙박 TOP 10")
        _render_card_list(stay, "stay", limit=10)

    with sub_tabs[2]:
        st.markdown("#### 🧾 가까운 관광지 TOP 10")
        _render_card_list(tour, "tour", limit=10)
