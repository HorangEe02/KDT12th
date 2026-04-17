"""원정 계획 공유 — Firestore 저장 + 쿼리 파라미터 복원.

사이드바 "🔗 계획 공유" 버튼으로 filters를 Firestore에 저장 → plan_id URL 반환.
앱 시작 시 ?plan_id=xxx 있으면 filters 자동 복원 (사이드바 기본값).
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from src.db import firestore_client as fs


def apply_shared_plan_from_query() -> bool:
    """앱 시작 시 1회 호출. ?plan_id=xxx 있으면 filters를 session_state에 선주입."""
    if st.session_state.get("_plan_applied"):
        return False
    plan_id = st.query_params.get("plan_id")
    if not plan_id:
        return False

    plan = fs.load_shared_plan(plan_id)
    if not plan:
        st.session_state["_plan_applied"] = True
        return False

    # 사이드바 위젯 기본값으로 사용될 session_state 키들
    if plan.get("team"):
        st.session_state["selected_team"] = plan["team"]
    if plan.get("budget") is not None:
        st.session_state["sb_budget"] = int(plan["budget"])
    if plan.get("party"):
        st.session_state["sb_party"] = plan["party"]
    if plan.get("transport"):
        st.session_state["sb_transport"] = plan["transport"]
    if plan.get("date_start") and plan.get("date_end"):
        try:
            ds = date.fromisoformat(plan["date_start"])
            de = date.fromisoformat(plan["date_end"])
            st.session_state["sb_dates"] = (ds, de)
        except (ValueError, TypeError):
            pass

    st.session_state["_plan_applied"] = True
    st.session_state["_loaded_plan_id"] = plan_id
    return True


def render_share_button(filters: dict) -> None:
    """사이드바에 '🔗 계획 공유' 버튼 렌더. 클릭 시 Firestore 저장 + URL 표시."""
    if not fs.health():
        st.sidebar.caption("🔗 공유 기능: Firestore 미연결")
        return

    if st.sidebar.button("🔗 계획 공유 링크 생성", use_container_width=True):
        author_id = fs.get_or_create_user_id(st.session_state)
        plan_id = fs.save_shared_plan(filters, author_id=author_id)
        if plan_id:
            st.session_state["_last_shared_plan"] = plan_id
            st.sidebar.success(f"✅ 생성: {plan_id}")
        else:
            st.sidebar.error("❌ 공유 실패 (Firestore 연결 확인)")

    last = st.session_state.get("_last_shared_plan")
    if last:
        share_url = f"?plan_id={last}"
        st.sidebar.code(share_url, language=None)
        st.sidebar.caption("↑ 이 경로를 URL에 붙여 공유하세요")

    loaded = st.session_state.get("_loaded_plan_id")
    if loaded:
        st.sidebar.info(f"📥 공유 계획 불러옴: `{loaded}`")
