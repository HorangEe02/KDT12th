"""모바일 하단 네비게이션 미러 — 탭 순서와 활성 인덱스를 시각적으로 표시."""
from __future__ import annotations

import streamlit as st

_ITEMS = [
    ("sports_baseball", "MATCHES"),
    ("explore", "MAP"),
    ("hotel", "STAYS"),
    ("auto_awesome", "AI"),
    ("military_tech", "BADGES"),
]


def render(active_idx: int = 0) -> None:
    items_html = []
    for i, (icon, label) in enumerate(_ITEMS):
        cls = "se-bottom-nav__item"
        if i == active_idx:
            cls += " se-bottom-nav__item--active"
        items_html.append(
            f'<div class="{cls}">'
            f'<span class="material-symbols-outlined">{icon}</span>'
            f'<span>{label}</span></div>'
        )

    html = (
        '<div class="se-bottom-nav">'
        + "".join(items_html)
        + "</div>"
        + '<p style="text-align:center; color:#999; font-size:0.72rem; margin-top:6px; '
        'font-family: \'Plus Jakarta Sans\', sans-serif;">'
        "실제 탭 전환은 상단 탭을 사용하세요 · 이 영역은 모바일 네비 미러입니다</p>"
    )
    st.markdown(html, unsafe_allow_html=True)
