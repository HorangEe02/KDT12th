"""KBO 로고 에셋 로더 — SVG → base64 data URI 변환.

React 컴포넌트의 APP_CONFIG에 주입하기 위한 Phase 2b 전용 헬퍼.
외장 볼륨 I/O 최소화를 위해 functools.lru_cache 사용 (Streamlit 런타임 독립).
"""
from __future__ import annotations

import base64
from functools import lru_cache

from src import config

_LOGO_DIR = config.PROJECT_ROOT / "uiux" / "KBO_logo"

TEAM_LOGO_FILES: dict[str, str] = {
    "LG": "LG.svg",
    "KT": "KT.svg",
    "SSG": "SSG.svg",
    "두산": "DOOSAN.svg",
    "KIA": "KIA.svg",
    "NC": "NC.svg",
    "삼성": "SAMSUNG.svg",
    "롯데": "LOTTE.svg",
    "한화": "HANWHA.svg",
    "키움": "KIWOOM.svg",
}


@lru_cache(maxsize=None)
def _cached_data_uri(path_str: str) -> str:
    from pathlib import Path
    p = Path(path_str)
    if not p.exists():
        return ""
    content = p.read_bytes()
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def get_team_logo_data_uri(team: str) -> str:
    """팀 약칭 → SVG data URI. 없으면 빈 문자열."""
    filename = TEAM_LOGO_FILES.get(team)
    if not filename:
        return ""
    return _cached_data_uri(str(_LOGO_DIR / filename))


def get_all_team_logos_data_uri() -> dict[str, str]:
    """10팀 로고 data URI dict."""
    return {team: _cached_data_uri(str(_LOGO_DIR / fname)) for team, fname in TEAM_LOGO_FILES.items()}


def get_kbo_logo_data_uri(variant: int = 1) -> str:
    """KBO 리그 로고 data URI. variant 1 or 2."""
    name = f"KBO_{variant}.svg"
    return _cached_data_uri(str(_LOGO_DIR / name))
