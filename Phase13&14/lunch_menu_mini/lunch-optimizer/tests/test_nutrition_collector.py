"""
NutritionCollector 단위 테스트.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline.collectors.nutrition_collector import (
    NutritionCollector, _parse_nutr, _parse_serving_size
)


# =============================================================================
# 파싱 유틸
# =============================================================================
class TestParseNutr:
    def test_empty_string_returns_zero(self):
        assert _parse_nutr("") == 0.0

    def test_na_returns_none(self):
        assert _parse_nutr("N/A") is None
        assert _parse_nutr("NA") is None
        assert _parse_nutr("-") is None

    def test_number(self):
        assert _parse_nutr("12.5") == 12.5

    def test_invalid_returns_none(self):
        assert _parse_nutr("abc") is None

    def test_none(self):
        assert _parse_nutr(None) == 0.0


class TestParseServingSize:
    def test_default(self):
        assert _parse_serving_size("") == 100.0
        assert _parse_serving_size(None) == 100.0

    def test_valid(self):
        assert _parse_serving_size("400") == 400.0


# =============================================================================
# Collector
# =============================================================================
class TestSearchByName:
    def test_success(self, fake_food_safety_key, nutrition_api_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = nutrition_api_response

        with patch("requests.get", return_value=mock_resp):
            collector = NutritionCollector()
            results = collector.search_by_name("김치찌개")

        assert len(results) == 3
        # 정확 일치가 첫 번째
        assert results[0]["food_name"] == "김치찌개"
        assert results[0]["calories"] == 520
        assert results[0]["protein"] == 28

    def test_empty_query(self, fake_food_safety_key):
        collector = NutritionCollector()
        assert collector.search_by_name("") == []

    def test_na_and_empty_fields(self, fake_food_safety_key, nutrition_api_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = nutrition_api_response

        with patch("requests.get", return_value=mock_resp):
            collector = NutritionCollector()
            results = collector.search_by_name("김치찌개")

        # "두부김치찌개" 의 fat="" → 0.0, sugar="N/A" → None
        dubu = next(r for r in results if r["food_name"] == "두부김치찌개")
        assert dubu["fat"] == 0.0
        assert dubu["sugar"] is None

    def test_no_result_code(self, fake_food_safety_key, nutrition_api_no_result):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = nutrition_api_no_result

        with patch("requests.get", return_value=mock_resp):
            collector = NutritionCollector()
            assert collector.search_by_name("없는음식") == []

    def test_html_error_response(self, fake_food_safety_key):
        """HTML 에러 페이지 방어."""
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.text = "<html>error</html>"
        with patch("requests.get", return_value=mock_resp):
            collector = NutritionCollector()
            assert collector.search_by_name("김치찌개") == []


class TestBulk:
    def test_bulk_search(self, fake_food_safety_key, nutrition_api_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = nutrition_api_response

        with patch("requests.get", return_value=mock_resp), patch("time.sleep"):
            collector = NutritionCollector()
            results = collector.search_bulk(["김치찌개", "된장찌개"])

        assert len(results) == 2
        assert "김치찌개" in results
        assert "된장찌개" in results
