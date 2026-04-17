"""팀 로고 셀렉터 — renderer 파라미터로 Streamlit/React 전환.

- renderer='streamlit': st.markdown 기반 카드 그리드
- renderer='react'   : Tailwind + KBO SVG 로고 카드
양쪽 모두 `<a href="?team=XX" target="_top">`로 URL 쿼리 동기화.
"""
from __future__ import annotations

import streamlit as st

from src.config import TEAMS
from src.ui.components.hero import TEAM_COLORS


def _render_streamlit(selected_team: str, viewport: str) -> None:
    cards: list[str] = []
    for code in TEAMS:
        palette = TEAM_COLORS.get(code, {"color": "#888", "nameKo": code})
        selected_cls = " selected" if code == selected_team else ""
        cards.append(
            f'<a href="?team={code}" target="_top" '
            f'class="se-team-card{selected_cls}" title="{palette["nameKo"]}">'
            f'<div class="se-team-card__badge" style="background: {palette["color"]};">'
            f'{code}</div>'
            f'<div class="se-team-card__code">{code}</div>'
            f'<div class="se-team-card__name">{palette["nameKo"]}</div>'
            f'</a>'
        )
    grid_cls = "se-team-grid--mobile" if viewport == "mobile" else "se-team-grid--web"
    html = (
        '<div class="se-team-wrap">'
        '<div class="se-team-wrap__header">'
        '<h3 class="se-team-wrap__title">SELECT YOUR TEAM</h3>'
        '<span class="se-team-wrap__help">⚡ 클릭 → URL 동기화</span>'
        '</div>'
        f'<div class="se-team-grid {grid_cls}">'
        + "".join(cards)
        + '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_react(selected_team: str, viewport: str) -> None:
    from src.ui.assets import get_all_team_logos_data_uri
    from src.ui.components.react_loader import load_react_component

    logos = get_all_team_logos_data_uri()
    teams: list[dict] = []
    for code in TEAMS:
        palette = TEAM_COLORS.get(code, {"color": "#888", "nameKo": code})
        teams.append({
            "code": code,
            "nameKo": palette["nameKo"],
            "color": palette["color"],
        })
    cfg = {
        "teams": teams,
        "selected": selected_team,
        "viewport": viewport,
        "logos": logos,
    }
    height = 540 if viewport == "mobile" else 260
    load_react_component("team_selector.html", cfg, height=height)


def render(selected_team: str = "LG", viewport: str = "web", renderer: str = "streamlit") -> None:
    if renderer == "react":
        _render_react(selected_team, viewport)
    else:
        _render_streamlit(selected_team, viewport)
