"""자연어 식단 파서 테스트."""
from __future__ import annotations

from nlp_mvp.nutrition_parser import parse_meal_text


def test_parse_korean_meal_items_and_metadata():
    result = parse_meal_text(
        "오늘 점심에 김치찌개랑 공기밥 먹었어. 만족도는 4점.",
        user_id="user1",
        base_date="2026-05-01",
    )

    assert result["user_id"] == "user1"
    assert result["meal_date"] == "2026-05-01"
    assert result["meal_type"] == "lunch"
    assert result["satisfaction"] == 4
    assert [item["raw_name"] for item in result["items"]] == ["김치찌개", "공기밥"]


def test_parse_relative_date_and_restaurant_hint():
    result = parse_meal_text(
        "어제 장인김치찌개에서 김치찌개 2인분 먹었어.",
        user_id="user1",
        base_date="2026-05-01",
    )

    assert result["meal_date"] == "2026-04-30"
    assert result["restaurant_hint"] == "장인김치찌개"
    assert result["items"][0]["raw_name"] == "김치찌개"
    assert result["items"][0]["quantity"] == 2.0
    assert result["items"][0]["unit"] == "인분"
