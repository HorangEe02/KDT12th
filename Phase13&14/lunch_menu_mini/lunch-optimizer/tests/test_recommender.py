"""
LunchRecommender 통합 테스트 (Subtopic 1~4 전체).
"""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from database.connection import get_session
from database.models import NutritionInfo, WeatherLog
from engine.recommender import (
    DEFAULT_WEIGHTS, NO_VOTE_WEIGHTS, LunchRecommender
)
from pipeline.collectors.vote_collector import VoteManager


# =============================================================================
# Seed: 날씨 + 영양 매핑을 추가로 심어주는 헬퍼 fixture
# =============================================================================
@pytest.fixture
def seed_full_context(seed_team_and_users):
    """Subtopic 1~4 전체 컨텍스트 (날씨 + 영양 매핑) 심기."""
    from datetime import datetime

    with get_session() as session:
        # 날씨
        weather = WeatherLog(
            temp=18.0, humidity=55, rain_type=0, rain_type_str="없음",
            rain_1h=0.0, wind_speed=2.0, sky=1, sky_str="맑음",
            pop=10, tmn=12, tmx=22,
            pm10=40, pm25=20, dust_grade="좋음",
            outdoor_comfort="좋음",
        )
        session.add(weather)

        # 영양 매핑 (r1~r6)
        nutrition_fixtures = [
            ("r1", "한솥도시락", 650, 28, 85, 18, 700),
            ("r2", "서브웨이 샌드위치", 480, 24, 60, 14, 900),
            ("r3", "맥도날드 버거", 780, 35, 62, 42, 1100),
            ("r4", "김밥천국", 580, 20, 80, 18, 1100),
            ("r5", "초밥", 520, 28, 68, 14, 900),
            ("r6", "파스타", 680, 22, 85, 28, 900),
        ]
        for rid, name, cal, prot, carbs, fat, sodium in nutrition_fixtures:
            session.add(NutritionInfo(
                restaurant_id=rid, food_name=name, match_type="category_avg",
                serving_size=100.0,
                calories=cal, carbs=carbs, protein=prot, fat=fat, sodium=sodium,
            ))
        session.commit()
    yield


# =============================================================================
# Composite 기본 동작
# =============================================================================
class TestGetRecommendationsBasic:
    def test_returns_top_n(self, seed_full_context, always_vote_time):
        # 투표 3건
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            mgr.cast_vote("user2", "r1")
            mgr.cast_vote("user3", "r2")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=5)

        assert len(recs) == 5
        assert all("composite_score" in r for r in recs)
        assert all("rank" in r for r in recs)
        # 내림차순
        scores = [r["composite_score"] for r in recs]
        assert scores == sorted(scores, reverse=True)
        # 1위 / 2위 점수 확인
        assert recs[0]["composite_score"] >= recs[1]["composite_score"]

    def test_rank_assigned(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=3)

        assert [r["rank"] for r in recs] == [1, 2, 3]


# =============================================================================
# Composite 수식 검증
# =============================================================================
class TestCompositeFormula:
    def test_with_votes_uses_default_weights(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=5)

        assert recs[0]["weights_used"] == DEFAULT_WEIGHTS

    def test_without_votes_uses_no_vote_weights(self, seed_full_context):
        # 세션만 개시, 투표 없음
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=5)

        assert recs[0]["weights_used"] == NO_VOTE_WEIGHTS
        # team_score 가중치 0
        assert recs[0]["weights_used"]["team"] == 0.0

    def test_composite_manual_calc(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=10)

        for r in recs:
            s = r["scores"]
            w = r["weights_used"]
            expected = round(
                s["distance"] * w["distance"]
                + s["weather"] * w["weather"]
                + s["nutrition"] * w["nutrition"]
                + s["team"] * w["team"]
            )
            assert r["composite_score"] == expected


# =============================================================================
# Highlights / Warnings
# =============================================================================
class TestHighlightsWarnings:
    def test_close_distance_highlight(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=5)

        # r1 의 distance_score = 100 → 가까움 하이라이트
        r1 = next((r for r in recs if r["restaurant_id"] == "r1"), None)
        assert r1 is not None
        assert any("가까운" in h for h in r1["highlights"])

    def test_vote_highlight(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            mgr.cast_vote("user2", "r1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=5)

        r1 = next((r for r in recs if r["restaurant_id"] == "r1"), None)
        assert r1 is not None
        assert any("투표" in h for h in r1["highlights"])


# =============================================================================
# Veto 영향
# =============================================================================
class TestVetoImpact:
    def test_vetoed_restaurant_warning(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_veto("user1", "r1", reason="어제 먹었어요")
            mgr.cast_vote("user2", "r1")  # 거부권 있는 곳에도 투표 가능 (경고만)

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            recs = recommender.get_recommendations(top_n=10)

        r1 = next(r for r in recs if r["restaurant_id"] == "r1")
        assert any("거부권" in w for w in r1["warnings"])


# =============================================================================
# Explain
# =============================================================================
class TestExplain:
    def test_explain_includes_formula(self, seed_full_context, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")

        with get_session() as session:
            recommender = LunchRecommender(session, "team1", "user1")
            detail = recommender.explain_recommendation("r1")

        assert "composite_formula" in detail["details"]
        assert detail["restaurant_id"] == "r1"
