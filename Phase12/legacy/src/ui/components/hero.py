"""Stadium Editorial 히어로 섹션 — renderer 파라미터로 Streamlit/React 전환.

- renderer='streamlit' (기본): st.markdown + 글로벌 CSS
- renderer='react'          : Tailwind CDN + React 18 (iframe) + KBO 로고 주입
팀 컬러 그라디언트는 양쪽 모두 유지.
"""
from __future__ import annotations

import streamlit as st

TEAM_COLORS: dict[str, dict[str, str]] = {
    "LG":   {"color": "#C30452", "subColor": "#FFCC00", "nameKo": "LG 트윈스"},
    "KT":   {"color": "#000000", "subColor": "#E5002D", "nameKo": "KT 위즈"},
    "SSG":  {"color": "#CE0E2D", "subColor": "#FFB81C", "nameKo": "SSG 랜더스"},
    "두산": {"color": "#131230", "subColor": "#ED1C24", "nameKo": "두산 베어스"},
    "KIA":  {"color": "#EA002C", "subColor": "#06141F", "nameKo": "KIA 타이거즈"},
    "NC":   {"color": "#315288", "subColor": "#A39161", "nameKo": "NC 다이노스"},
    "삼성": {"color": "#074CA1", "subColor": "#C0C0C0", "nameKo": "삼성 라이온즈"},
    "롯데": {"color": "#041E42", "subColor": "#ED1C24", "nameKo": "롯데 자이언츠"},
    "한화": {"color": "#FF6600", "subColor": "#000000", "nameKo": "한화 이글스"},
    "키움": {"color": "#570514", "subColor": "#B07F4A", "nameKo": "키움 히어로즈"},
}


def _render_streamlit(team: str, viewport: str) -> None:
    palette = TEAM_COLORS.get(team, TEAM_COLORS["LG"])
    gradient = f"linear-gradient(135deg, {palette['color']} 0%, {palette['subColor']} 100%)"
    size_cls = "se-hero--mobile" if viewport == "mobile" else "se-hero--web"
    html = f"""
<div class="se-hero {size_cls}" style="background: {gradient};">
  <div class="se-hero__inner">
    <div>
      <span class="se-hero__badge">KBO 2026 · AWAY COMPANION</span>
      <h1 class="se-hero__title"><span class="se-hero__ball">⚾</span> 원정 응원 플래너</h1>
      <p class="se-hero__subtitle">팀 선택 한 번으로 티켓·교통·맛집·숙소·관광을 한 번에</p>
    </div>
    <div class="se-hero__team">
      <div class="se-hero__team-name">{palette['nameKo']}</div>
      <div class="se-hero__team-tagline">선택된 팀 컬러로 테마가 변경됩니다</div>
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def _render_react(team: str, viewport: str) -> None:
    from src.ui.assets import get_kbo_logo_data_uri, get_team_logo_data_uri
    from src.ui.components.react_loader import load_react_component

    palette = TEAM_COLORS.get(team, TEAM_COLORS["LG"])
    cfg = {
        "team": team,
        "teamNameKo": palette["nameKo"],
        "color": palette["color"],
        "subColor": palette["subColor"],
        "viewport": viewport,
        "teamLogo": get_team_logo_data_uri(team),
        "kboLogo": get_kbo_logo_data_uri(1),
    }
    height = 260 if viewport == "mobile" else 240
    load_react_component("hero.html", cfg, height=height)


def render(team: str = "LG", viewport: str = "web", renderer: str = "streamlit") -> None:
    if renderer == "react":
        _render_react(team, viewport)
    else:
        _render_streamlit(team, viewport)
