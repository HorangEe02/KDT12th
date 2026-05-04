"""
Tool result formatter — converts raw API dicts into short Korean summaries
that the LLM can incorporate naturally into its next response.

Keeping the summaries compact matters: every tool result is re-injected into
the prompt for the next LLM turn, so verbose JSON eats the context window
fast on small local models.
"""
from __future__ import annotations

import json
from typing import Any


def _truncate(text: str, n: int = 500) -> str:
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def format_tool_result(result: dict[str, Any]) -> str:
    """
    Format a `ToolExecutor.execute()` return value into a single
    human-readable string. On success, we hand-format per-tool for brevity;
    otherwise we fall back to JSON.
    """
    tool = result.get("tool", "?")
    if not result.get("ok"):
        return f"[{tool}] 실패: {result.get('error', 'unknown error')}"

    data = result.get("data")
    if data is None:
        return f"[{tool}] 결과 없음"

    fn = _FORMATTERS.get(tool)
    if fn is not None:
        try:
            return fn(data)
        except Exception:
            pass  # fall through to json

    return f"[{tool}] {_truncate(json.dumps(data, ensure_ascii=False))}"


# =============================================================================
# Per-tool formatters
# =============================================================================
def _fmt_recommendations(data: Any) -> str:
    if not isinstance(data, list) or not data:
        return "[get_lunch_recommendations] 추천 결과 없음"
    lines = ["[get_lunch_recommendations]"]
    for i, r in enumerate(data[:5], 1):
        name = r.get("name", "?")
        score = r.get("composite_score") or r.get("score") or 0
        category = r.get("category") or ""
        distance = r.get("distance_m") or r.get("distance") or 0
        lines.append(f"{i}. {name} ({category}) · {distance}m · {score}점")
    return "\n".join(lines)


def _fmt_weather(data: Any) -> str:
    if not isinstance(data, dict):
        return "[get_current_weather] 데이터 없음"
    temp = data.get("temp", "?")
    sky = data.get("sky_str") or data.get("sky") or "?"
    pop = data.get("pop", "?")
    dust = data.get("dust_grade") or data.get("pm10") or "?"
    tips = data.get("tips") or []
    out = [
        f"[get_current_weather] 기온 {temp}°C · {sky} · 강수확률 {pop}% · 미세먼지 {dust}"
    ]
    if tips:
        out.append("팁: " + "; ".join(str(t) for t in tips[:3]))
    return "\n".join(out)


def _fmt_diagnosis(data: Any) -> str:
    if not isinstance(data, dict):
        return "[get_nutrition_diagnosis] 데이터 없음"
    status = data.get("overall_status", "?")
    score = data.get("overall_score", "?")
    parts = [f"[get_nutrition_diagnosis] {status} ({score}점)"]
    nutr = data.get("nutrient_status") or {}
    if isinstance(nutr, dict) and nutr:
        items = ", ".join(f"{k}={v}" for k, v in list(nutr.items())[:5])
        parts.append(items)
    return " · ".join(parts)


def _fmt_restaurant(data: Any) -> str:
    if not isinstance(data, dict):
        return "[get_restaurant_info] 데이터 없음"
    name = data.get("name", "?")
    cat = data.get("category", "")
    dist = data.get("distance_m", "?")
    line = f"[get_restaurant_info] {name} ({cat}) · {dist}m"
    nutr = data.get("nutrition")
    if isinstance(nutr, dict) and nutr:
        cal = nutr.get("calories", "?")
        prot = nutr.get("protein", "?")
        line += f" · {cal}kcal · 단백질 {prot}g"
    return line


def _fmt_cast_vote(data: Any) -> str:
    if not isinstance(data, dict):
        return "[cast_vote] 응답 없음"
    status = data.get("status", "ok")
    rid = data.get("restaurant_id", "?")
    warn = data.get("warning")
    out = f"[cast_vote] {status} · restaurant={rid}"
    if warn:
        out += f" · ⚠️ {warn}"
    return out


def _fmt_vote_status(data: Any) -> str:
    if not isinstance(data, dict):
        return "[get_vote_status] 데이터 없음"
    total = data.get("total_votes", 0)
    members = data.get("total_members", "?")
    votes = data.get("votes") or []
    out = [f"[get_vote_status] {total}/{members} 투표"]
    for v in votes[:3]:
        name = v.get("restaurant_name") or v.get("restaurant_id")
        count = v.get("vote_count", 0)
        out.append(f"  · {name}: {count}표")
    winner = data.get("winner_restaurant_id")
    if winner:
        out.append(f"임시 우승: {winner}")
    return "\n".join(out)


def _fmt_record_meal(data: Any) -> str:
    if not isinstance(data, dict):
        return "[record_meal] 저장됨"
    return (
        f"[record_meal] {data.get('menu_name', '?')} "
        f"({data.get('calories', '?')}kcal) 저장됨"
    )


def _fmt_visit_history(data: Any) -> str:
    if not isinstance(data, list) or not data:
        return "[get_visit_history] 이력 없음"
    lines = ["[get_visit_history]"]
    for v in data[:5]:
        name = v.get("restaurant_name") or v.get("restaurant_id", "?")
        date = v.get("visit_date", "?")
        lines.append(f"  · {date}: {name}")
    return "\n".join(lines)


_FORMATTERS = {
    "get_lunch_recommendations": _fmt_recommendations,
    "get_current_weather": _fmt_weather,
    "get_nutrition_diagnosis": _fmt_diagnosis,
    "get_restaurant_info": _fmt_restaurant,
    "cast_vote": _fmt_cast_vote,
    "get_vote_status": _fmt_vote_status,
    "record_meal": _fmt_record_meal,
    "get_visit_history": _fmt_visit_history,
}


__all__ = ["format_tool_result"]
