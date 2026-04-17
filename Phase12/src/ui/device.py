"""디바이스(뷰포트) 감지 및 사이드바 토글 헬퍼.

Phase 2 UIUX 리파인 — 사용자 환경 분리 (web / mobile).
- 쿼리 파라미터 `?device=mobile` 우선
- 사이드바 최상단 라디오 위젯으로 수동 전환
- 선택 결과는 session_state['viewport']에 저장 + 쿼리 파라미터 동기화
- 모바일일 때 컨테이너 폭을 480px로 제한하는 CSS 훅 삽입
"""
from __future__ import annotations

import streamlit as st

VIEWPORTS = ["web", "mobile"]
_LABELS = {"web": "🖥️ 데스크톱", "mobile": "📱 모바일"}

RENDERERS = ["streamlit", "react"]
_RENDERER_LABELS = {"streamlit": "🧩 Streamlit", "react": "⚛️ React"}


def _resolve_initial() -> str:
    """쿼리 파라미터 > session_state > 기본값 'web' 우선순위로 초기 viewport 결정."""
    q = st.query_params.get("device")
    if q in VIEWPORTS:
        st.session_state["viewport"] = q
        return q
    return st.session_state.get("viewport", "web")


def render_device_toggle() -> str:
    """사이드바 최상단에 뷰포트 토글을 렌더하고 선택값을 반환한다."""
    current = _resolve_initial()

    st.sidebar.markdown("### 📐 뷰포트")
    try:
        default_idx = VIEWPORTS.index(current)
    except ValueError:
        default_idx = 0
    picked = st.sidebar.radio(
        "보기 모드",
        options=VIEWPORTS,
        index=default_idx,
        format_func=lambda v: _LABELS[v],
        horizontal=True,
        label_visibility="collapsed",
        key="sb_viewport",
    )
    if picked != current:
        st.session_state["viewport"] = picked
        st.query_params["device"] = picked
        current = picked

    st.sidebar.caption("모바일 레이아웃은 480px 폭 기준")
    st.sidebar.divider()

    if current == "mobile":
        st.markdown(
            "<style>.stApp > div:first-child,.block-container { max-width: 480px !important; "
            "margin-left: auto !important; margin-right: auto !important; }</style>",
            unsafe_allow_html=True,
        )

    return current


def _resolve_renderer() -> str:
    q = st.query_params.get("renderer")
    if q in RENDERERS:
        st.session_state["renderer"] = q
        return q
    return st.session_state.get("renderer", "streamlit")


def render_renderer_toggle() -> str:
    """사이드바에 렌더러 토글 (뷰포트 아래) 렌더 후 선택값 반환."""
    current = _resolve_renderer()

    st.sidebar.markdown("### 🎨 렌더러")
    try:
        default_idx = RENDERERS.index(current)
    except ValueError:
        default_idx = 0
    picked = st.sidebar.radio(
        "렌더링 엔진",
        options=RENDERERS,
        index=default_idx,
        format_func=lambda v: _RENDERER_LABELS[v],
        horizontal=True,
        label_visibility="collapsed",
        key="sb_renderer",
    )
    if picked != current:
        st.session_state["renderer"] = picked
        st.query_params["renderer"] = picked
        current = picked

    help_text = (
        "Streamlit 네이티브 HTML" if current == "streamlit"
        else "React 18 + Tailwind CDN (iframe)"
    )
    st.sidebar.caption(help_text)
    st.sidebar.divider()
    return current
