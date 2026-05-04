"""scoring_patch + scoring_patch_ab 단위 테스트."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.integration import scoring_patch as sp
from nlp_mvp.integration import scoring_patch_ab as ab


# =============================================================================
# v1 / v2a / v2b 공식
# =============================================================================
class TestFormulas:
    def test_v1_matches_manual_computation(self):
        # 80*0.30 + 60*0.20 + 70*0.20 + 50*0.30 = 24 + 12 + 14 + 15 = 65
        assert sp.compute_composite_score_v1(80, 60, 70, 50) == pytest.approx(65.0)

    def test_v1_clips_out_of_range(self):
        # 음수 / 100 초과 → clip
        assert sp.compute_composite_score_v1(-10, 200, 50, 50) == pytest.approx(
            0 * 0.30 + 100 * 0.20 + 50 * 0.20 + 50 * 0.30
        )

    def test_v2a_adds_sentiment_axis(self):
        # s=100 → 80*0.25 + 60*0.15 + 70*0.15 + 50*0.25 + 100*0.20
        #       = 20 + 9 + 10.5 + 12.5 + 20 = 72.0
        assert sp.compute_composite_score_v2a(80, 60, 70, 50, 100) == pytest.approx(
            72.0
        )

    def test_v2b_amplifies_positive_sentiment(self):
        v1 = 65.0
        # s=+1.0 → 65 * (1 + 0.15*1) = 74.75
        assert sp.compute_composite_score_v2b(v1, 1.0) == pytest.approx(74.75)
        # s=-1.0 → 65 * 0.85 = 55.25
        assert sp.compute_composite_score_v2b(v1, -1.0) == pytest.approx(55.25)

    def test_sentiment_score_0_100_mapping(self):
        assert sp.sentiment_score_0_100({"score": -1.0}) == pytest.approx(0.0)
        assert sp.sentiment_score_0_100({"score": 0.0}) == pytest.approx(50.0)
        assert sp.sentiment_score_0_100({"score": 1.0}) == pytest.approx(100.0)


# =============================================================================
# compute_composite_score_v2 (퍼블릭 진입점) — 폴백 동작
# =============================================================================
class TestV2PublicAPI:
    RESTAURANT = {"distance_score": 80}
    WEATHER = {"score": 60}
    NUTRITION = {"score": 70}
    TEAM = {"score": 50}

    def test_no_sentiment_falls_back_to_v1(self):
        v2 = sp.compute_composite_score_v2(
            self.RESTAURANT, self.WEATHER, self.NUTRITION, self.TEAM, None
        )
        v1 = sp.compute_composite_score_v1(80, 60, 70, 50)
        assert v2 == pytest.approx(v1)

    def test_low_review_count_falls_back(self):
        v2 = sp.compute_composite_score_v2(
            self.RESTAURANT,
            self.WEATHER,
            self.NUTRITION,
            self.TEAM,
            sentiment={"score": 0.9, "review_count": 1},  # < MIN_SAMPLE
        )
        v1 = sp.compute_composite_score_v1(80, 60, 70, 50)
        assert v2 == pytest.approx(v1)

    def test_positive_sentiment_increases_score(self):
        v1 = sp.compute_composite_score_v1(80, 60, 70, 50)
        v2 = sp.compute_composite_score_v2(
            self.RESTAURANT,
            self.WEATHER,
            self.NUTRITION,
            self.TEAM,
            sentiment={"score": 0.8, "review_count": 10},
        )
        assert v2 > v1

    def test_negative_sentiment_decreases_or_rebalances(self):
        v2 = sp.compute_composite_score_v2(
            self.RESTAURANT,
            self.WEATHER,
            self.NUTRITION,
            self.TEAM,
            sentiment={"score": -0.8, "review_count": 10},
        )
        # -0.8 → 10 on 0~100 scale.
        # 80*0.25 + 60*0.15 + 70*0.15 + 50*0.25 + 10*0.20 = 20+9+10.5+12.5+2 = 54.0
        assert v2 == pytest.approx(54.0)


# =============================================================================
# A/B compute + 로그
# =============================================================================
class TestAB:
    @pytest.fixture()
    def engine(self, tmp_path):
        db_path = tmp_path / "ab_test.db"
        eng = create_engine(f"sqlite:///{db_path}", future=True)
        ab.ensure_schema(eng)
        return eng

    def test_compute_ab_with_valid_sentiment(self):
        result = ab.compute_ab(
            restaurant_id="R001",
            distance=80, weather=60, nutrition=70, team=50,
            sentiment={"score": 0.6, "review_count": 12},
        )
        assert result["restaurant_id"] == "R001"
        assert result["valid"] is True
        assert result["review_count"] == 12
        # diff_a and diff_b should reflect sentiment influence
        assert result["v1"] == pytest.approx(65.0)
        assert result["v2a"] != result["v1"]

    def test_compute_ab_without_sentiment(self):
        result = ab.compute_ab(
            restaurant_id="R002",
            distance=80, weather=60, nutrition=70, team=50,
            sentiment=None,
        )
        assert result["valid"] is False
        assert result["review_count"] == 0
        assert result["sentiment_score"] is None

    def test_log_and_fetch_round_trip(self, engine):
        result = ab.compute_ab(
            restaurant_id="R003",
            distance=80, weather=60, nutrition=70, team=50,
            sentiment={"score": 0.4, "review_count": 5},
        )
        ab.log_ab_sample(engine, result)

        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT COUNT(*) FROM ab_scoring_log")
            ).scalar()
        assert rows == 1

        samples = ab.fetch_recent_samples(engine, limit=10)
        assert len(samples) == 1
        assert samples[0]["restaurant_id"] == "R003"
