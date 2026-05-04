"""indexer.py 단위 테스트 — chromadb 없이 동작하는 순수 함수만."""
from __future__ import annotations

from nlp_mvp.rag_chatbot.indexer import (
    format_meal_history_row,
    format_nutrition_row,
    format_restaurant_row,
)


class TestFormatMealHistoryRow:
    def test_basic(self):
        row = {
            "meal_date": "2026-04-01",
            "menu": "김치찌개",
            "calories": 650.0,
            "protein": 22.0,
            "satisfaction": 4,
        }
        result = format_meal_history_row(row)
        assert "2026-04-01" in result
        assert "김치찌개" in result
        assert "650" in result
        assert "22" in result
        assert "4/5" in result

    def test_missing_fields(self):
        result = format_meal_history_row({})
        assert "미상" in result
        assert "0kcal" in result

    def test_none_values(self):
        row = {"meal_date": "2026-04-02", "menu": "라면",
               "calories": None, "protein": None}
        result = format_meal_history_row(row)
        assert "라면" in result


class TestFormatNutritionRow:
    def test_basic(self):
        row = {
            "food_name": "김치찌개",
            "calories": 650,
            "protein": 22,
            "carbs": 50,
            "fat": 15,
            "sodium": 1200,
        }
        result = format_nutrition_row(row)
        assert "김치찌개" in result
        assert "650kcal" in result
        assert "단백질 22g" in result
        assert "1200mg" in result

    def test_missing(self):
        result = format_nutrition_row({"food_name": "X"})
        assert "X" in result
        assert "0kcal" in result


class TestFormatRestaurantRow:
    def test_with_sentiment(self):
        row = {
            "name": "맛집A",
            "category": "한식",
            "distance_m": 250,
            "rating": 4.5,
            "sentiment_score": 0.42,
            "menu_type": "김치찌개",
        }
        result = format_restaurant_row(row)
        assert "맛집A" in result
        assert "한식" in result
        assert "250m" in result
        assert "4.5" in result
        assert "+0.42" in result
        assert "김치찌개" in result

    def test_without_sentiment(self):
        row = {
            "name": "맛집B",
            "category": "양식",
            "distance_m": 500,
            "rating": 3.8,
            "sentiment_score": None,
            "menu_type": "파스타",
        }
        result = format_restaurant_row(row)
        assert "맛집B" in result
        assert "감성 점수" not in result

    def test_negative_sentiment(self):
        row = {"name": "C", "sentiment_score": -0.3}
        result = format_restaurant_row(row)
        assert "-0.30" in result
