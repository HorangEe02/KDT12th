"""Tab 5 — 10구장 컴플릿 뱃지 + Firestore 영속화.

Phase 5: 방문 구장을 Firestore에 저장·로드해 브라우저를 닫아도 유지됩니다.
user_id는 브라우저 세션 기반 UUID (session_state 저장).
"""
from __future__ import annotations

import streamlit as st

from src.db import firestore_client as fs
from src.ui.components import badges


def _render_controls(visited: list[str]) -> list[str]:
    col_a, col_b, col_c = st.columns([2, 2, 3])
    if not fs.health():
        with col_a:
            st.info("💾 Firestore 미연결 — 세션 저장만 가능")
        return visited

    user_id = fs.get_or_create_user_id(st.session_state)
    with col_a:
        if st.button("💾 Firestore 저장", use_container_width=True):
            if fs.save_visited_stadiums(user_id, visited):
                st.success("저장 완료!")
            else:
                st.error("저장 실패")
    with col_b:
        if st.button("📥 서버에서 불러오기", use_container_width=True):
            loaded = fs.load_visited_stadiums(user_id)
            if loaded:
                st.session_state["visited_stadiums"] = loaded
                st.success(f"{len(loaded)}개 구장 로드")
                st.rerun()
            else:
                st.info("저장된 기록이 없습니다")
    with col_c:
        st.caption(f"🆔 사용자 ID: `{user_id}`")
    return visited


def render(filters: dict) -> None:
    st.subheader("🏅 나의 원정 컴플릿 현황")
    st.caption("방문 구장을 Firestore에 저장하면 다음 접속 시 복원됩니다.")

    visited = st.session_state.get("visited_stadiums", [])
    if not visited:
        visited = ["잠실", "수원", "문학"]
        st.session_state["visited_stadiums"] = visited

    visited = _render_controls(visited)
    st.divider()

    viewport = filters.get("viewport") or st.session_state.get("viewport", "web")
    renderer = filters.get("renderer") or st.session_state.get("renderer", "streamlit")
    badges.render(visited, viewport=viewport, renderer=renderer)
