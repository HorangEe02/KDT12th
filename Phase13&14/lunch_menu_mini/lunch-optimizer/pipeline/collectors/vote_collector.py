"""
VoteManager — 팀 투표 세션 · 투표 · 거부권 · 마감 로직.
"""
from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.models import (
    Restaurant, User, Veto, VisitHistory, Vote, VoteSession
)

logger = logging.getLogger(__name__)


class VoteError(RuntimeError):
    """VoteManager 관련 예외."""


class VoteManager:
    """
    투표 세션 전담 매니저. DB 세션을 주입받아 사용.

    Usage:
        with get_session() as session:
            mgr = VoteManager(session)
            mgr.open_session("team1")
            mgr.cast_vote("user1", "rest1")
    """

    # 투표 가능 시간 (로컬 시각)
    VOTE_START_HOUR: int = 10
    VOTE_END_HOUR: int = 11
    VOTE_END_MINUTE: int = 30

    # 최소 참여율 (50%)
    MIN_PARTICIPATION: float = 0.5

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    # 유틸
    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_date(d: Optional[date]) -> date:
        return d or date.today()

    def _is_vote_time(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        start = now.replace(
            hour=self.VOTE_START_HOUR, minute=0, second=0, microsecond=0
        )
        end = now.replace(
            hour=self.VOTE_END_HOUR, minute=self.VOTE_END_MINUTE, second=0, microsecond=0
        )
        return start <= now <= end

    def _get_session(
        self, team_id: str, vote_date: date
    ) -> Optional[VoteSession]:
        return self.session.execute(
            select(VoteSession).where(
                VoteSession.team_id == team_id,
                VoteSession.vote_date == vote_date,
            )
        ).scalar_one_or_none()

    # -------------------------------------------------------------------------
    # Open Session
    # -------------------------------------------------------------------------
    def open_session(
        self,
        team_id: str,
        vote_date: Optional[date] = None,
    ) -> VoteSession:
        """투표 세션 개시 (기존 세션 있으면 반환)."""
        vote_date = self._resolve_date(vote_date)
        try:
            existing = self._get_session(team_id, vote_date)
            if existing is not None:
                logger.info("Reusing existing session: %s", existing.to_dict())
                return existing

            session_obj = VoteSession(
                vote_date=vote_date,
                team_id=team_id,
                status="open",
                open_at=datetime.utcnow(),
            )
            self.session.add(session_obj)
            self.session.commit()
            self.session.refresh(session_obj)
            logger.info("Opened vote session: team=%s date=%s", team_id, vote_date)
            return session_obj
        except Exception as e:
            self.session.rollback()
            logger.exception("open_session failed: %s", e)
            raise

    # -------------------------------------------------------------------------
    # Cast Vote
    # -------------------------------------------------------------------------
    def cast_vote(
        self,
        user_id: str,
        restaurant_id: str,
        vote_date: Optional[date] = None,
        admin_override: bool = False,
    ) -> dict[str, Any]:
        """
        투표 행사. 동일 날짜·사용자는 UPDATE.

        Returns:
            {"status": "created" | "updated", "vote": Vote, "warning": str | None}
        """
        vote_date = self._resolve_date(vote_date)

        user = self.session.get(User, user_id)
        if user is None:
            raise VoteError(f"User not found: {user_id}")

        if not admin_override and not self._is_vote_time():
            raise VoteError(
                f"투표 가능 시간이 아닙니다 "
                f"({self.VOTE_START_HOUR:02d}:00~{self.VOTE_END_HOUR:02d}:{self.VOTE_END_MINUTE:02d})"
            )

        session_obj = self._get_session(user.team_id, vote_date)
        if session_obj is None:
            raise VoteError(f"No open session for team={user.team_id} date={vote_date}")
        if session_obj.status != "open":
            raise VoteError(f"세션이 '{session_obj.status}' 상태입니다 (open 아님)")

        restaurant = self.session.get(Restaurant, restaurant_id)
        if restaurant is None:
            raise VoteError(f"Restaurant not found: {restaurant_id}")

        # 거부권 확인 (경고만)
        warning: Optional[str] = None
        veto = self.session.execute(
            select(Veto).where(
                Veto.veto_date == vote_date,
                Veto.restaurant_id == restaurant_id,
            )
        ).scalar_one_or_none()
        if veto is not None:
            warning = f"거부권이 걸린 음식점입니다 (사유: {veto.reason or '이유 미기재'})"

        try:
            existing_vote = self.session.execute(
                select(Vote).where(
                    Vote.vote_date == vote_date,
                    Vote.user_id == user_id,
                )
            ).scalar_one_or_none()

            if existing_vote is None:
                vote = Vote(
                    vote_date=vote_date,
                    user_id=user_id,
                    restaurant_id=restaurant_id,
                )
                self.session.add(vote)
                self.session.flush()
                session_obj.total_votes = (session_obj.total_votes or 0) + 1
                self.session.commit()
                self.session.refresh(vote)
                return {"status": "created", "vote": vote, "warning": warning}
            else:
                existing_vote.restaurant_id = restaurant_id
                existing_vote.updated_at = datetime.utcnow()
                self.session.commit()
                self.session.refresh(existing_vote)
                return {"status": "updated", "vote": existing_vote, "warning": warning}
        except Exception as e:
            self.session.rollback()
            logger.exception("cast_vote failed: %s", e)
            raise

    # -------------------------------------------------------------------------
    # Veto
    # -------------------------------------------------------------------------
    def cast_veto(
        self,
        user_id: str,
        restaurant_id: str,
        reason: Optional[str] = None,
        veto_date: Optional[date] = None,
    ) -> Veto:
        veto_date = self._resolve_date(veto_date)
        try:
            existing = self.session.execute(
                select(Veto).where(
                    Veto.veto_date == veto_date,
                    Veto.user_id == user_id,
                    Veto.restaurant_id == restaurant_id,
                )
            ).scalar_one_or_none()
            if existing is not None:
                if reason:
                    existing.reason = reason
                    self.session.commit()
                return existing

            veto = Veto(
                veto_date=veto_date,
                user_id=user_id,
                restaurant_id=restaurant_id,
                reason=reason,
            )
            self.session.add(veto)
            self.session.commit()
            self.session.refresh(veto)
            logger.info("Veto cast: user=%s restaurant=%s", user_id, restaurant_id)
            return veto
        except Exception as e:
            self.session.rollback()
            logger.exception("cast_veto failed: %s", e)
            raise

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------
    def get_current_status(
        self,
        team_id: str,
        vote_date: Optional[date] = None,
    ) -> dict[str, Any]:
        vote_date = self._resolve_date(vote_date)

        team_users = list(
            self.session.execute(
                select(User).where(
                    User.team_id == team_id, User.is_active == True  # noqa: E712
                )
            ).scalars().all()
        )
        team_member_ids = {u.id for u in team_users}
        member_lookup = {u.id: u for u in team_users}

        session_obj = self._get_session(team_id, vote_date)

        votes = []
        if team_member_ids:
            votes = list(
                self.session.execute(
                    select(Vote).where(
                        Vote.vote_date == vote_date,
                        Vote.user_id.in_(team_member_ids),
                    )
                ).scalars().all()
            )

        vetoes = []
        if team_member_ids:
            vetoes = list(
                self.session.execute(
                    select(Veto).where(
                        Veto.veto_date == vote_date,
                        Veto.user_id.in_(team_member_ids),
                    )
                ).scalars().all()
            )

        voted_user_ids = {v.user_id for v in votes}
        not_voted_names = [u.name for u in team_users if u.id not in voted_user_ids]

        restaurant_ids = {v.restaurant_id for v in votes} | {ve.restaurant_id for ve in vetoes}
        restaurants: dict[str, Restaurant] = {}
        if restaurant_ids:
            rows = self.session.execute(
                select(Restaurant).where(Restaurant.id.in_(restaurant_ids))
            ).scalars().all()
            restaurants = {r.id: r for r in rows}

        tally_counter: dict[str, int] = {}
        for v in votes:
            tally_counter[v.restaurant_id] = tally_counter.get(v.restaurant_id, 0) + 1

        tally = [
            {
                "restaurant_id": rid,
                "restaurant_name": restaurants[rid].name if rid in restaurants else rid,
                "votes": cnt,
            }
            for rid, cnt in sorted(tally_counter.items(), key=lambda x: x[1], reverse=True)
        ]

        votes_detail = []
        for v in votes:
            user = member_lookup.get(v.user_id)
            restaurant = restaurants.get(v.restaurant_id)
            votes_detail.append({
                "user_id": v.user_id,
                "user_name": user.name if user else v.user_id,
                "avatar": user.avatar_emoji if user else "🧑",
                "restaurant_id": v.restaurant_id,
                "restaurant_name": restaurant.name if restaurant else v.restaurant_id,
                "voted_at": v.updated_at.strftime("%H:%M") if v.updated_at else "",
            })

        vetoed = []
        for veto in vetoes:
            user = member_lookup.get(veto.user_id)
            restaurant = restaurants.get(veto.restaurant_id)
            vetoed.append({
                "restaurant_id": veto.restaurant_id,
                "restaurant_name": restaurant.name if restaurant else veto.restaurant_id,
                "veto_by": user.name if user else veto.user_id,
                "reason": veto.reason or "",
            })

        team_members = len(team_users)
        voted_count = len(voted_user_ids)
        participation_rate = (
            round(voted_count / team_members * 100, 1) if team_members > 0 else 0.0
        )

        return {
            "vote_date": vote_date.isoformat(),
            "status": session_obj.status if session_obj else "none",
            "team_members": team_members,
            "voted_count": voted_count,
            "participation_rate": participation_rate,
            "votes": votes_detail,
            "not_voted": not_voted_names,
            "vetoed": vetoed,
            "tally": tally,
        }

    # -------------------------------------------------------------------------
    # Close Session
    # -------------------------------------------------------------------------
    def _days_since_last_visit(
        self, team_id: str, restaurant_id: str, ref: date
    ) -> int:
        """마지막 방문일로부터 경과 일수 (방문 없음 → 매우 큰 값)."""
        last = self.session.execute(
            select(func.max(VisitHistory.visit_date)).where(
                VisitHistory.team_id == team_id,
                VisitHistory.restaurant_id == restaurant_id,
            )
        ).scalar()
        if last is None:
            return 10 ** 6
        return (ref - last).days

    def close_session(
        self,
        team_id: str,
        vote_date: Optional[date] = None,
    ) -> dict[str, Any]:
        vote_date = self._resolve_date(vote_date)
        session_obj = self._get_session(team_id, vote_date)
        if session_obj is None:
            raise VoteError(f"No session to close for team={team_id} date={vote_date}")
        if session_obj.status == "finalized":
            return {
                "winner": {"restaurant_id": session_obj.winner_restaurant_id},
                "already_finalized": True,
            }

        status = self.get_current_status(team_id, vote_date)
        tally = status["tally"]
        participation_rate = status["participation_rate"]
        warning: Optional[str] = None

        if participation_rate < self.MIN_PARTICIPATION * 100:
            warning = f"참여율 {participation_rate}% — 50% 미만입니다"

        winner_id: Optional[str] = None
        tiebreak_reason: Optional[str] = None

        if not tally:
            tiebreak_reason = "no_votes"
        else:
            top_count = tally[0]["votes"]
            top_candidates = [t for t in tally if t["votes"] == top_count]

            if len(top_candidates) == 1:
                winner_id = top_candidates[0]["restaurant_id"]
            else:
                # 최근 방문이 가장 오래된 음식점 선호
                def _sort_key(t):
                    rid = t["restaurant_id"]
                    days = self._days_since_last_visit(team_id, rid, vote_date)
                    return -days  # 오래된 것 우선

                top_candidates.sort(key=_sort_key)
                best_days = self._days_since_last_visit(
                    team_id, top_candidates[0]["restaurant_id"], vote_date
                )
                remaining_ties = [
                    c for c in top_candidates
                    if self._days_since_last_visit(team_id, c["restaurant_id"], vote_date)
                    == best_days
                ]
                if len(remaining_ties) > 1:
                    chosen = random.choice(remaining_ties)
                    winner_id = chosen["restaurant_id"]
                    tiebreak_reason = "random_after_freshness_tie"
                else:
                    winner_id = top_candidates[0]["restaurant_id"]
                    tiebreak_reason = "least_recent_visit"

        # Update session
        try:
            session_obj.status = "finalized"
            session_obj.close_at = datetime.utcnow()
            session_obj.winner_restaurant_id = winner_id
            self.session.commit()
            self.session.refresh(session_obj)
        except Exception:
            self.session.rollback()
            raise

        winner_name = None
        if winner_id:
            r = self.session.get(Restaurant, winner_id)
            winner_name = r.name if r else winner_id

        return {
            "winner": {
                "restaurant_id": winner_id,
                "restaurant_name": winner_name,
                "votes": tally[0]["votes"] if tally else 0,
                "tiebreak_reason": tiebreak_reason,
            },
            "total_votes": sum(t["votes"] for t in tally),
            "participation_rate": participation_rate,
            "finalized_at": (
                session_obj.close_at.isoformat() if session_obj.close_at else None
            ),
            "warning": warning,
        }

    # -------------------------------------------------------------------------
    # History
    # -------------------------------------------------------------------------
    def get_vote_history(
        self, team_id: str, days: int = 30
    ) -> list[dict[str, Any]]:
        since = date.today() - timedelta(days=days)
        sessions = list(
            self.session.execute(
                select(VoteSession).where(
                    VoteSession.team_id == team_id,
                    VoteSession.vote_date >= since,
                ).order_by(VoteSession.vote_date.desc())
            ).scalars().all()
        )
        return [s.to_dict() for s in sessions]
