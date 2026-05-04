"""
WeatherDataIntegrator + WeatherMenuScorer 단위 테스트.
"""
from __future__ import annotations

import pytest

from pipeline.transformers.weather_scorer import (
    WeatherDataIntegrator,
    WeatherMenuScorer,
)


# =============================================================================
# Integrator
# =============================================================================
class TestIntegrator:
    def test_both_sources(self):
        weather = {"temp": 15, "rain_type": 0, "pop": 10, "wind_speed": 2, "sky": 1, "sky_str": "맑음"}
        air = {"pm10_value": 30, "pm25_value": 15, "pm10_grade": 1, "pm25_grade": 1}
        result = WeatherDataIntegrator.integrate(weather, air)
        assert result["temp"] == 15
        assert result["pm10"] == 30
        assert result["dust_grade"] == "좋음"
        assert result["outdoor_comfort"] == "매우좋음"

    def test_air_none(self):
        weather = {"temp": 15, "rain_type": 0, "pop": 10, "wind_speed": 2}
        result = WeatherDataIntegrator.integrate(weather, None)
        assert result["pm10"] is None
        assert result["dust_grade"] is None

    def test_dust_worst_wins(self):
        air = {"pm10_grade": 2, "pm25_grade": 3, "pm10_value": 50, "pm25_value": 60}
        result = WeatherDataIntegrator.integrate({"temp": 15}, air)
        assert result["dust_grade"] == "나쁨"

    @pytest.mark.parametrize(
        "temp,rain,pop,dust,wind,expected",
        [
            (20, 0, 10, "좋음", 2, "매우좋음"),
            (20, 0, 30, "보통", 4, "좋음"),
            (12, 0, 50, "보통", 2, "보통"),
            (5, 1, 80, "나쁨", 2, "나쁨"),
            (-10, 0, 0, None, 2, "매우나쁨"),
            (20, 0, 0, "매우나쁨", 2, "매우나쁨"),
        ],
    )
    def test_outdoor_comfort(self, temp, rain, pop, dust, wind, expected):
        assert WeatherDataIntegrator.calculate_outdoor_comfort(
            temp=temp, rain_type=rain, pop=pop, dust_grade=dust, wind_speed=wind
        ) == expected


# =============================================================================
# MenuScorer
# =============================================================================
class TestMenuScorer:
    def test_cold_weather_soup_bonus(self):
        r = {"menu_type": "국물", "distance_m": 200, "indoor": True}
        w = {"temp": 3, "rain_type": 0, "pop": 10, "wind_speed": 1}
        assert WeatherMenuScorer.calculate_weather_score(r, w) >= 75

    def test_cold_weather_sushi_penalty(self):
        r = {"menu_type": "초밥", "distance_m": 200, "indoor": True}
        w = {"temp": 3, "rain_type": 0, "pop": 10, "wind_speed": 1}
        assert WeatherMenuScorer.calculate_weather_score(r, w) <= 45

    def test_hot_weather_cold_noodle_bonus(self):
        r = {"menu_type": "면류", "sub_category": "냉면", "distance_m": 200, "indoor": True}
        w = {"temp": 32, "rain_type": 0, "pop": 5, "wind_speed": 1}
        assert WeatherMenuScorer.calculate_weather_score(r, w) >= 75

    def test_hot_weather_soup_penalty(self):
        r = {"menu_type": "국물", "distance_m": 200, "indoor": True}
        w = {"temp": 33, "rain_type": 0, "pop": 5, "wind_speed": 1}
        assert WeatherMenuScorer.calculate_weather_score(r, w) <= 40

    def test_rainy_day_nearby_bonus(self):
        nearby = {"menu_type": "양식", "distance_m": 150, "indoor": True}
        far = {"menu_type": "양식", "distance_m": 450, "indoor": True}
        w = {"temp": 18, "rain_type": 1, "pop": 80, "wind_speed": 1}
        score_near = WeatherMenuScorer.calculate_weather_score(nearby, w)
        score_far = WeatherMenuScorer.calculate_weather_score(far, w)
        assert score_near > score_far
        assert score_near - score_far >= 25

    def test_dusty_day_indoor_bonus(self):
        indoor_r = {"menu_type": "한식", "distance_m": 300, "indoor": True}
        outdoor_r = {"menu_type": "한식", "distance_m": 300, "indoor": False}
        w = {"temp": 18, "rain_type": 0, "pop": 20, "wind_speed": 2, "dust_grade": "나쁨"}
        s_in = WeatherMenuScorer.calculate_weather_score(indoor_r, w)
        s_out = WeatherMenuScorer.calculate_weather_score(outdoor_r, w)
        assert s_in > s_out

    def test_neutral_weather(self):
        r = {"menu_type": "한식", "distance_m": 200, "indoor": True}
        w = {"temp": 20, "rain_type": 0, "pop": 10, "wind_speed": 1, "dust_grade": "좋음"}
        score = WeatherMenuScorer.calculate_weather_score(r, w)
        assert 45 <= score <= 60

    def test_score_clamped(self):
        r = {"menu_type": "국물", "distance_m": 150, "indoor": True}
        w = {"temp": 1, "rain_type": 1, "pop": 90, "wind_speed": 1, "dust_grade": "나쁨"}
        score = WeatherMenuScorer.calculate_weather_score(r, w)
        assert 0 <= score <= 100


# =============================================================================
# Tips
# =============================================================================
class TestWeatherTips:
    def test_cold(self):
        tips = WeatherMenuScorer.get_weather_tips({"temp": 3})
        assert any("영하권" in t or "추위" in t for t in tips)

    def test_rain(self):
        tips = WeatherMenuScorer.get_weather_tips({"temp": 15, "pop": 80})
        assert any("비" in t or "가까운" in t for t in tips)

    def test_dust(self):
        tips = WeatherMenuScorer.get_weather_tips({"temp": 15, "dust_grade": "나쁨"})
        assert any("미세먼지" in t for t in tips)

    def test_no_issue(self):
        tips = WeatherMenuScorer.get_weather_tips(
            {"temp": 20, "rain_type": 0, "pop": 0, "wind_speed": 1}
        )
        assert len(tips) >= 1


# =============================================================================
# Ranking
# =============================================================================
class TestRankRestaurants:
    def test_descending_order(self):
        restaurants = [
            {"id": "a", "menu_type": "초밥", "distance_m": 200, "indoor": True},
            {"id": "b", "menu_type": "국물", "distance_m": 200, "indoor": True},
            {"id": "c", "menu_type": "양식", "distance_m": 300, "indoor": True},
        ]
        cold_weather = {"temp": 3, "rain_type": 0, "pop": 10, "wind_speed": 1}
        ranked = WeatherMenuScorer.rank_restaurants_by_weather(restaurants, cold_weather)
        scores = [r["weather_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)
        # 추운 날씨 → 국물이 최상위
        assert ranked[0]["id"] == "b"


class TestMenuTypeRanking:
    def test_cold_weather_soup_top(self):
        cold = {"temp": 3, "rain_type": 0, "pop": 10, "wind_speed": 1}
        ranking = WeatherMenuScorer.get_menu_type_ranking(cold)
        assert ranking[0]["menu_type"] in ("국물", "죽")

    def test_hot_weather_cold_noodle_top(self):
        hot = {"temp": 33, "rain_type": 0, "pop": 5, "wind_speed": 1}
        ranking = WeatherMenuScorer.get_menu_type_ranking(hot)
        top_types = {ranking[0]["menu_type"], ranking[1]["menu_type"]}
        # 냉면·초밥·샐러드 중 하나가 최상위에 와야 함
        assert top_types & {"냉면", "초밥", "샐러드"}
