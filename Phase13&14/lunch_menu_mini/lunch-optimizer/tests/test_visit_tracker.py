"""
VisitTracker 단위 테스트.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from database.connection import get_session
from pipeline.transformers.visit_tracker import (
    VisitTracker, business_days_ago, count_business_days
)


# =============================================================================
# Business days 유틸
# =============================================================================
class TestBusinessDays:
    def test_count_same_day(self):
        assert count_business_days(date(2026, 4, 6), date(2026, 4, 6)) == 1

    def test_count_full_week(self):
        assert count_business_days(date(2026, 4, 6), date(2026, 4, 10)) == 5

    def test_count_with_weekend(self):
        # 금(4/10) → 월(4/13) = 2 영업일
        assert count_business_days(date(2026, 4, 10), date(2026, 4, 13)) == 2


# =============================================================================
# Record
# =============================================================================
class TestRecord:
    def test_basic(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            visit = tracker.record_visit(
                team_id="team1",
                restaurant_id="r1",
                visit_date=date(2026, 4, 3),
                participant_count=5,
            )
            assert visit.id is not None

    def test_with_satisfaction_avg(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            visit = tracker.record_visit(
                "team1", "r1", date(2026, 4, 3),
                participant_count=5,
                satisfaction_scores=[4, 5, 4, 3, 5],
            )
            assert visit.avg_satisfaction == pytest.approx(4.2)


# =============================================================================
# Frequency
# =============================================================================
class TestFrequency:
    def test_counts_per_restaurant(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            today = date.today()
            for i in range(3):
                tracker.record_visit("team1", "r1", today - timedelta(days=i), 5)
            for i in range(2):
                tracker.record_visit("team1", "r2", today - timedelta(days=i), 5)

            freq = tracker.get_visit_frequency("team1", days=30)

        total = sum(info["count"] for info in freq.values())
        assert total == 5

    def test_overvisited_detects(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            today = date.today()
            for i in range(5):
                tracker.record_visit("team1", "r1", today - timedelta(days=i), 5)
            over = tracker.get_overvisited("team1", threshold=4, days=30)
        assert "r1" in over


# =============================================================================
# Freshness
# =============================================================================
class TestFreshness:
    def test_never_visited_100(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            assert tracker.calculate_freshness_score("team1", "r99") == 100

    def test_yesterday_is_low(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            tracker.record_visit("team1", "r1", date.today() - timedelta(days=1), 5)
            score = tracker.calculate_freshness_score("team1", "r1")
            assert score <= 40  # 1~2 or 3~4 영업일 구간

    def test_month_ago_is_90(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            tracker.record_visit("team1", "r1", date.today() - timedelta(days=30), 5)
            assert tracker.calculate_freshness_score("team1", "r1") == 90


# =============================================================================
# Never visited
# =============================================================================
class TestNeverVisited:
    def test_returns_unvisited(self, seed_team_and_users):
        with get_session() as session:
            tracker = VisitTracker(session)
            tracker.record_visit("team1", "r1", date.today(), 5)
            tracker.record_visit("team1", "r2", date.today(), 5)
            never = tracker.get_never_visited("team1", ["r1", "r2", "r3", "r4"])
        assert set(never) == {"r3", "r4"}
