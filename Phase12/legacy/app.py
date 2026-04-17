import streamlit as st

from src import config
from src.data_loader import load_schedule, load_stadiums, load_team_stats
from src.ui.components import bottom_nav, hero, team_selector
from src.ui.device import render_device_toggle, render_renderer_toggle
from src.ui.sidebar import render_sidebar
from src.ui.tabs import tab1_games, tab2_map, tab3_places, tab4_ai, tab5_badges

st.set_page_config(
    page_title="원정 응원 플래너",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

_css_path = config.ASSETS_CSS_DIR / "style.css"
if _css_path.exists():
    _css = _css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

for key, default in [
    ("filters", {}),
    ("selected_team", "LG"),
    ("messages", []),
    ("visited_stadiums", []),
    ("generate_trigger", False),
    ("viewport", "web"),
    ("renderer", "streamlit"),
]:
    st.session_state.setdefault(key, default)

if "team" in st.query_params:
    _q_team = st.query_params["team"]
    if _q_team in config.TEAMS:
        st.session_state["selected_team"] = _q_team

# Phase 5 — 공유 URL (?plan_id=xxx)로 진입한 경우 filters 복원
try:
    from src.ui.plan_share import apply_shared_plan_from_query
    apply_shared_plan_from_query()
except ImportError:
    pass

viewport = render_device_toggle()
renderer = render_renderer_toggle()

load_schedule()
load_stadiums()
load_team_stats()

hero.render(st.session_state["selected_team"], viewport, renderer)
team_selector.render(st.session_state["selected_team"], viewport, renderer)

filters = render_sidebar()

tab_labels = [
    "⚾ 경기 & 예측",
    "🗺️ 동선 지도",
    "🍽️ 맛집·숙소",
    "🤖 AI 플래너",
    "🏅 내 뱃지",
]
tabs = st.tabs(tab_labels)

active_tab_idx = 0
with tabs[0]:
    tab1_games.render(filters)
with tabs[1]:
    tab2_map.render(filters)
with tabs[2]:
    tab3_places.render(filters)
with tabs[3]:
    tab4_ai.render(filters)
with tabs[4]:
    tab5_badges.render({**filters, "viewport": viewport, "renderer": renderer})

if viewport == "mobile":
    bottom_nav.render(active_idx=active_tab_idx)

st.divider()
st.markdown(
    """
    <div style='text-align:center; color:#888; font-size:0.85rem; padding:8px 0 20px;
                font-family: "Plus Jakarta Sans", sans-serif;'>
      데이터 출처:
      <a href='https://www.data.go.kr/' target='_blank'>공공데이터포털</a> ·
      <a href='https://api.visitkorea.or.kr/' target='_blank'>한국관광공사 TourAPI</a> ·
      기상청 단기/중기예보 · Kakao Maps<br>
      © 2026 원정 응원 플래너 팀 · 미니 프로젝트
    </div>
    """,
    unsafe_allow_html=True,
)
