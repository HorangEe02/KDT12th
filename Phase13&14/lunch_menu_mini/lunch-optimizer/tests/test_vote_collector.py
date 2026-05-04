"""
VoteManager 단위 테스트 (in-memory SQLite).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from database.connection import get_session
from database.models import VisitHistory
from pipeline.collectors.vote_collector import VoteError, VoteManager


# =============================================================================
# Session open
# =============================================================================
class TestOpenSession:
    def test_open_new(self, seed_team_and_users):
        with get_session() as session:
            mgr = VoteManager(session)
            s = mgr.open_session("team1")
            assert s.status == "open"
            assert s.team_id == "team1"

    def test_open_duplicate_returns_existing(self, seed_team_and_users):
        with get_session() as session:
            mgr = VoteManager(session)
            s1 = mgr.open_session("team1")
            s2 = mgr.open_session("team1")
            assert s1.id == s2.id


# =============================================================================
# Cast vote
# =============================================================================
class TestCastVote:
    def test_create_new(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            result = mgr.cast_vote("user1", "r1")
            assert result["status"] == "created"
            assert result["vote"].restaurant_id == "r1"

    def test_update_existing(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            result = mgr.cast_vote("user1", "r2")
            assert result["status"] == "updated"
            assert result["vote"].restaurant_id == "r2"

    def test_no_session_raises(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            with pytest.raises(VoteError, match="No open session"):
                mgr.cast_vote("user1", "r1")

    def test_unknown_user_raises(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            with pytest.raises(VoteError, match="User not found"):
                mgr.cast_vote("ghost", "r1")

    def test_unknown_restaurant_raises(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            with pytest.raises(VoteError, match="Restaurant not found"):
                mgr.cast_vote("user1", "nonexistent")

    def test_vote_on_vetoed_warns(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_veto("user2", "r1", reason="어제 먹었어요")
            result = mgr.cast_vote("user1", "r1")
            assert result["status"] == "created"
            assert result["warning"] is not None
            assert "거부권" in result["warning"]


# =============================================================================
# Status
# =============================================================================
class TestStatus:
    def test_status_with_votes(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            mgr.cast_vote("user2", "r1")
            mgr.cast_vote("user3", "r2")
            status = mgr.get_current_status("team1")

        assert status["team_members"] == 5
        assert status["voted_count"] == 3
        assert status["participation_rate"] == 60.0
        assert len(status["tally"]) == 2
        assert status["tally"][0]["restaurant_id"] == "r1"
        assert status["tally"][0]["votes"] == 2
        assert "사용자4" in status["not_voted"]


# =============================================================================
# Close
# =============================================================================
class TestClose:
    def test_clear_winner(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            mgr.cast_vote("user2", "r1")
            mgr.cast_vote("user3", "r2")
            mgr.cast_vote("user4", "r2")
            mgr.cast_vote("user5", "r1")
            result = mgr.close_session("team1")

        assert result["winner"]["restaurant_id"] == "r1"
        assert result["total_votes"] == 5
        assert result["warning"] is None

    def test_low_participation_warning(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            result = mgr.close_session("team1")
        assert result["warning"] is not None
        assert "50%" in result["warning"]

    def test_tiebreak_by_least_recent_visit(self, seed_team_and_users, always_vote_time):
        """
        r1, r2 둘 다 1표. r1 은 어제 방문 → r2 (미방문) 선택.
        """
        with get_session() as session:
            visit = VisitHistory(
                visit_date=date.today() - timedelta(days=1),
                team_id="team1",
                restaurant_id="r1",
                participant_count=5,
            )
            session.add(visit)
            session.commit()

        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            mgr.cast_vote("user2", "r2")
            result = mgr.close_session("team1")

        assert result["winner"]["restaurant_id"] == "r2"

    def test_idempotent_close(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "r1")
            mgr.cast_vote("user2", "r1")
            mgr.cast_vote("user3", "r1")
            mgr.close_session("team1")
            second = mgr.close_session("team1")
        assert second.get("already_finalized") is True


# =============================================================================
# Veto
# =============================================================================
class TestVeto:
    def test_cast_and_retrieve(self, seed_team_and_users, always_vote_time):
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            veto = mgr.cast_veto("user1", "r3", reason="어제 먹었어요")
            assert veto.restaurant_id == "r3"

            status = mgr.get_current_status("team1")
            assert any(v["restaurant_id"] == "r3" for v in status["vetoed"])
