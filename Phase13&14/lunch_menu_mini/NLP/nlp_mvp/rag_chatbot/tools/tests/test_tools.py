"""Smoke tests for the Phase 7 Tool Calling package."""
from __future__ import annotations

import pytest

from nlp_mvp.rag_chatbot.tools.definitions import (
    TOOL_DEFINITIONS,
    TOOL_NAMES,
    get_tool_schema,
)
from nlp_mvp.rag_chatbot.tools.executors import ToolExecutor
from nlp_mvp.rag_chatbot.tools.fallback import (
    parse_tool_calls,
    strip_tool_calls,
)
from nlp_mvp.rag_chatbot.tools.formatter import format_tool_result
from nlp_mvp.rag_chatbot.tools.router import guess_tool_from_query


# =============================================================================
# definitions
# =============================================================================
def test_tool_definitions_count_and_schema():
    assert len(TOOL_DEFINITIONS) == 8
    assert len(TOOL_NAMES) == 8
    expected = {
        "get_lunch_recommendations",
        "get_current_weather",
        "get_nutrition_diagnosis",
        "get_restaurant_info",
        "cast_vote",
        "get_vote_status",
        "record_meal",
        "get_visit_history",
    }
    assert set(TOOL_NAMES) == expected
    for t in TOOL_DEFINITIONS:
        assert t["type"] == "function"
        assert "name" in t["function"]
        assert "description" in t["function"]
        assert "parameters" in t["function"]


def test_get_tool_schema_lookup():
    s = get_tool_schema("get_current_weather")
    assert s is not None
    assert s["function"]["name"] == "get_current_weather"
    assert get_tool_schema("nonexistent") is None


# =============================================================================
# fallback parser
# =============================================================================
def test_parse_tool_calls_simple():
    text = "날씨를 확인할게요. [TOOL: get_current_weather]"
    calls = parse_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "get_current_weather"
    assert calls[0]["args"] == {}


def test_parse_tool_calls_with_kwargs():
    text = '[TOOL: get_lunch_recommendations(team_id="team1", top_n=3)]'
    calls = parse_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "get_lunch_recommendations"
    assert calls[0]["args"] == {"team_id": "team1", "top_n": 3}


def test_parse_tool_calls_multiple():
    text = """먼저 날씨 확인: [TOOL: get_current_weather]
그리고 추천 조회: [TOOL: get_lunch_recommendations(top_n=5)]"""
    calls = parse_tool_calls(text)
    assert len(calls) == 2
    assert calls[0]["name"] == "get_current_weather"
    assert calls[1]["name"] == "get_lunch_recommendations"
    assert calls[1]["args"]["top_n"] == 5


def test_parse_tool_calls_bare_identifier_value():
    text = "[TOOL: get_restaurant_info(restaurant_id=R001)]"
    calls = parse_tool_calls(text)
    assert calls[0]["args"]["restaurant_id"] == "R001"


def test_parse_tool_calls_ignores_unparseable():
    text = "[TOOL: garbage 123 ***] and [TOOL: get_current_weather]"
    calls = parse_tool_calls(text)
    # The garbage block matches the block regex but fails name regex; skipped
    assert len(calls) == 1
    assert calls[0]["name"] == "get_current_weather"


def test_parse_tool_calls_empty_string():
    assert parse_tool_calls("") == []
    assert parse_tool_calls(None) == []  # type: ignore[arg-type]


def test_strip_tool_calls():
    text = "답변 먼저 [TOOL: get_current_weather] 그리고 설명"
    assert strip_tool_calls(text) == "답변 먼저  그리고 설명"


# =============================================================================
# router
# =============================================================================
def test_router_picks_weather():
    g = guess_tool_from_query("오늘 비 와?")
    assert g is not None
    assert g["name"] == "get_current_weather"


def test_router_picks_nutrition():
    g = guess_tool_from_query("이번 주 단백질 부족해?")
    assert g["name"] == "get_nutrition_diagnosis"


def test_router_picks_recommendations_default():
    g = guess_tool_from_query("뭐 먹지?")
    assert g["name"] == "get_lunch_recommendations"


def test_router_no_match():
    assert guess_tool_from_query("안녕하세요") is None
    assert guess_tool_from_query("") is None


# =============================================================================
# executors (with mocked HTTP)
# =============================================================================
def test_executor_unknown_tool():
    ex = ToolExecutor(
        http_get=lambda p, q: {},
        http_post=lambda p, b: {},
    )
    result = ex.execute("not_a_tool", {})
    assert result["ok"] is False
    assert "unknown tool" in result["error"]


def test_executor_get_current_weather():
    calls = []
    def mock_get(path, params):
        calls.append((path, params))
        return {"temp": 15, "sky_str": "맑음", "pop": 10, "dust_grade": "좋음"}
    ex = ToolExecutor(http_get=mock_get)
    result = ex.execute("get_current_weather", {})
    assert result["ok"] is True
    assert result["data"]["temp"] == 15
    assert calls[0][0] == "/weather/current"


def test_executor_get_lunch_recommendations_defaults():
    captured: list = []
    def mock_get(path, params):
        captured.append(params)
        return [{"name": "test", "category": "한식", "distance_m": 100, "composite_score": 80}]
    ex = ToolExecutor(http_get=mock_get)
    result = ex.execute("get_lunch_recommendations", {})
    assert result["ok"] is True
    assert captured[0] == {"team_id": "team1", "user_id": "user1", "top_n": 5}


def test_executor_cast_vote_missing_args():
    ex = ToolExecutor(http_post=lambda p, b: {})
    result = ex.execute("cast_vote", {})
    assert result["ok"] is False
    assert "required" in result["error"].lower() or "missing" in result["error"].lower()


def test_executor_restaurant_info_nutrition_fallback():
    def mock_get(path, params):
        if "nutrition" in path:
            from nlp_mvp.rag_chatbot.tools.executors import ToolExecutionError
            raise ToolExecutionError("404")
        return {"id": "R001", "name": "테스트", "category": "한식", "distance_m": 100}
    ex = ToolExecutor(http_get=mock_get)
    result = ex.execute("get_restaurant_info", {"restaurant_id": "R001"})
    assert result["ok"] is True
    assert result["data"]["nutrition"] is None
    assert result["data"]["name"] == "테스트"


def test_executor_record_meal_optional_fields():
    captured = {}
    def mock_post(path, body):
        captured.update(body)
        return {"id": 1, "menu_name": "김치찌개", "calories": 550}
    ex = ToolExecutor(http_post=mock_post)
    result = ex.execute(
        "record_meal",
        {"user_id": "u1", "restaurant_id": "R001", "menu_name": "김치찌개", "satisfaction": 5},
    )
    assert result["ok"] is True
    assert captured["menu_name"] == "김치찌개"
    assert captured["satisfaction"] == 5


# =============================================================================
# formatter
# =============================================================================
def test_formatter_success_falls_through_to_json():
    result = {"ok": True, "tool": "unknown_tool", "data": {"k": "v"}}
    out = format_tool_result(result)
    assert "unknown_tool" in out
    assert "k" in out


def test_formatter_error():
    out = format_tool_result({"ok": False, "tool": "cast_vote", "error": "boom"})
    assert "cast_vote" in out
    assert "실패" in out
    assert "boom" in out


def test_formatter_weather():
    out = format_tool_result({
        "ok": True,
        "tool": "get_current_weather",
        "data": {
            "temp": 18,
            "sky_str": "흐림",
            "pop": 30,
            "dust_grade": "보통",
            "tips": ["우산 챙기세요", "실내 추천"],
        },
    })
    assert "18" in out
    assert "흐림" in out
    assert "우산" in out


def test_formatter_recommendations():
    out = format_tool_result({
        "ok": True,
        "tool": "get_lunch_recommendations",
        "data": [
            {"name": "한솥도시락", "category": "한식", "distance_m": 120, "composite_score": 85},
            {"name": "스시로", "category": "일식", "distance_m": 350, "composite_score": 78},
        ],
    })
    assert "한솥도시락" in out
    assert "85" in out
    assert "스시로" in out
