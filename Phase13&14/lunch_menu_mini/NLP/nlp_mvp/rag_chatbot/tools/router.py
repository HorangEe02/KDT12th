"""
Intent → Tool heuristic router (prompt-fallback mode).

When the LLM doesn't produce any `[TOOL: ...]` markers, we use keyword
matching as a last resort to pick a reasonable default. This is a safety
net, not the primary path; real usage should rely on either native tool
calling or explicit LLM-emitted markers.
"""
from __future__ import annotations

from typing import Any

INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "get_current_weather",
        ["날씨", "비", "미세먼지", "기온", "춥", "더워", "습"],
    ),
    (
        "get_nutrition_diagnosis",
        ["영양", "단백질", "칼로리", "탄수화물", "지방", "균형"],
    ),
    (
        "get_vote_status",
        ["투표 현황", "투표 진행", "몇 명", "누가 뽑", "득표"],
    ),
    (
        "get_visit_history",
        ["어제 먹", "지난주", "최근 방문", "방문 기록", "히스토리"],
    ),
    (
        "get_lunch_recommendations",
        ["추천", "뭐 먹", "뭐먹", "점심", "메뉴"],
    ),
]


def guess_tool_from_query(query: str) -> dict[str, Any] | None:
    """
    Heuristic: return `{"name": ..., "args": {}}` for the first matching
    intent pattern, or None if nothing matches.
    """
    if not query:
        return None
    lowered = query.lower()
    for tool_name, keywords in INTENT_PATTERNS:
        if any(kw in lowered for kw in keywords):
            return {"name": tool_name, "args": {}}
    return None


__all__ = ["guess_tool_from_query", "INTENT_PATTERNS"]
