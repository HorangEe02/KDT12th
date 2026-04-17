"""사이드바 필터 위젯 — 디바이스 토글(최상단) + 5종 필터 + 코스 생성 버튼.

디바이스 토글은 src.ui.device.render_device_toggle() 에서 먼저 렌더되므로
여기서는 그 아래에 원정 설정 필터만 구성한다.
"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src import config

_PARTY_OPTIONS = {
    "solo": "혼자",
    "couple": "커플",
    "family": "가족",
    "friends": "친구 그룹",
}
_TRANSPORT_OPTIONS = {
    "train": "🚄 KTX/SRT",
    "car": "🚗 자차",
    "bus": "🚌 고속버스",
}

_SEASON_START = date(2026, 3, 28)
_SEASON_END = date(2026, 9, 30)


def render_sidebar() -> dict:
    """원정 설정 사이드바 렌더 → filters dict 반환, session_state['filters']에 저장."""
    st.sidebar.header("🎽 원정 설정")

    selected_team = st.session_state.get("selected_team", "LG")
    try:
        default_idx = config.TEAMS.index(selected_team)
    except ValueError:
        default_idx = 0
    team = st.sidebar.selectbox(
        "응원팀",
        options=config.TEAMS,
        index=default_idx,
        key="sb_team",
    )
    if team != selected_team:
        st.session_state["selected_team"] = team
        st.query_params["team"] = team

    st.sidebar.divider()

    today = date.today()
    clamp_start = max(_SEASON_START, today)
    default_start = clamp_start if clamp_start <= _SEASON_END else _SEASON_START
    default_end = min(_SEASON_END, default_start + timedelta(days=3))

    date_range_raw = st.sidebar.date_input(
        "원정 기간",
        value=(default_start, default_end),
        min_value=_SEASON_START,
        max_value=_SEASON_END,
        key="sb_dates",
    )
    if isinstance(date_range_raw, tuple) and len(date_range_raw) == 2:
        date_range = date_range_raw
    else:
        date_range = (default_start, default_end)

    st.sidebar.divider()

    budget = st.sidebar.slider(
        "예산 (만원)",
        min_value=10,
        max_value=100,
        value=30,
        step=5,
        key="sb_budget",
    )

    party = st.sidebar.radio(
        "인원 구성",
        options=list(_PARTY_OPTIONS.keys()),
        format_func=lambda v: _PARTY_OPTIONS[v],
        key="sb_party",
    )

    transport = st.sidebar.radio(
        "이동수단",
        options=list(_TRANSPORT_OPTIONS.keys()),
        format_func=lambda v: _TRANSPORT_OPTIONS[v],
        key="sb_transport",
    )

    st.sidebar.divider()

    if st.sidebar.button("🎯 코스 생성", type="primary", use_container_width=True):
        st.session_state["generate_trigger"] = True

    st.sidebar.divider()

    # Phase 4 시연 안전장치
    demo_mode = st.sidebar.toggle(
        "🎬 시연 모드",
        value=bool(st.session_state.get("demo_mode", False)),
        help="Ollama/Gemini 서버 장애 대비 — 사전 녹화된 AI 응답 재생",
        key="sb_demo_mode",
    )
    st.session_state["demo_mode"] = demo_mode
    if demo_mode:
        st.sidebar.caption("⚠️ LLM 호출 없이 mock 응답 반환 (탭 4)")

    filters = {
        "team": team,
        "date_range": date_range,
        "budget": budget,
        "party": party,
        "transport": transport,
    }
    st.session_state["filters"] = filters

    # Phase 5 — 원정 계획 공유 (Firestore)
    try:
        from src.ui.plan_share import render_share_button
        st.sidebar.divider()
        render_share_button(filters)
    except ImportError:
        pass

    return filters
