"""Stadium Tour 뱃지 — renderer 파라미터로 Streamlit/React 전환.

- renderer='streamlit': 네이티브 카드 그리드 + Material Symbols
- renderer='react'   : Tailwind + 이미지 카드 + KBO 팀 로고 + 그라디언트 오버레이
"""
from __future__ import annotations

import streamlit as st

from src.data_loader import load_stadiums
from src.ui.components.hero import TEAM_COLORS


def _home_team_code(home_team_field: str) -> str:
    first = str(home_team_field).split(",")[0].strip()
    return first.replace("(보조)", "").strip()


def _render_streamlit(visited_stadiums: list[str], viewport: str) -> None:
    stadiums_df = load_stadiums()
    total = len(stadiums_df)
    visited_count = sum(1 for s in stadiums_df["short_name"] if s in visited_stadiums)
    pct = round(visited_count / total * 100) if total else 0
    grid_cls = "se-badges__grid--mobile" if viewport == "mobile" else "se-badges__grid--web"

    cards: list[str] = []
    for _, row in stadiums_df.iterrows():
        short = str(row["short_name"])
        city = str(row["city"])
        visited = short in visited_stadiums
        variant = " se-badge-card--visited" if visited else ""
        icon = "check_circle" if visited else "stadium"
        cards.append(
            f'<div class="se-badge-card{variant}">'
            f'<span class="material-symbols-outlined se-badge-card__icon">{icon}</span>'
            f'<div class="se-badge-card__name">{short}</div>'
            f'<div class="se-badge-card__city">{city}</div>'
            f'</div>'
        )

    celebrate = ""
    if visited_count == total and total > 0:
        celebrate = (
            '<div class="se-badges__celebrate">'
            '🎉 10개 구장 완주! 진정한 원정 응원러!'
            '</div>'
        )

    html = (
        '<div class="se-badges">'
        '<div class="se-badges__header">'
        '<div>'
        '<h2 class="se-badges__title">Stadium Tour</h2>'
        f'<div class="se-badges__meta">{visited_count} / {total} COMPLETED</div>'
        '</div>'
        f'<div class="se-badges__count">{pct}<small>%</small></div>'
        '</div>'
        + celebrate
        + f'<div class="se-badges__grid {grid_cls}">'
        + "".join(cards)
        + '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_react(visited_stadiums: list[str], viewport: str) -> None:
    from src.ui.assets import get_all_team_logos_data_uri
    from src.ui.components.react_loader import load_react_component

    stadiums_df = load_stadiums()
    logos = get_all_team_logos_data_uri()

    items: list[dict] = []
    for _, row in stadiums_df.iterrows():
        team_code = _home_team_code(row["home_team"])
        palette = TEAM_COLORS.get(team_code, {"color": "#00193c"})
        short = str(row["short_name"])
        items.append({
            "name": str(row["stadium_name"]),
            "short_name": short,
            "city": str(row["city"]),
            "team_code": team_code,
            "visited": short in visited_stadiums,
            "color": palette["color"],
        })

    cfg = {
        "stadiums": items,
        "totalVisited": sum(1 for i in items if i["visited"]),
        "viewport": viewport,
        "logos": logos,
    }
    height = 1100 if viewport == "mobile" else 560
    load_react_component("badges.html", cfg, height=height)


def render(
    visited_stadiums: list[str],
    viewport: str = "web",
    renderer: str = "streamlit",
) -> None:
    if renderer == "react":
        _render_react(visited_stadiums, viewport)
    else:
        _render_streamlit(visited_stadiums, viewport)
