"""React HTML 파일을 읽어 APP_CONFIG 주입 후 Streamlit에 렌더링하는 공통 헬퍼."""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from src import config

_REACT_DIR = config.ASSETS_DIR / "react"


def load_react_component(filename: str, config_dict: dict, height: int = 260) -> None:
    html_path = _REACT_DIR / filename
    if not html_path.exists():
        st.warning(f"React 컴포넌트 {filename}이 아직 없습니다.")
        return

    html = html_path.read_text(encoding="utf-8")
    payload = json.dumps(config_dict, ensure_ascii=False)
    inject = f"<script>window.APP_CONFIG = {payload};</script>"

    if "</head>" in html:
        html = html.replace("</head>", f"{inject}</head>", 1)
    else:
        html = inject + html

    components.html(html, height=height, scrolling=False)
