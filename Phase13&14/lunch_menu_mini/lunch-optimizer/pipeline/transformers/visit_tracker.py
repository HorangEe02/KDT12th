"""
VisitTracker — 팀 방문 이력 관리 · 영업일 계산 · 신선도 점수.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from database.models import Restaurant, VisitHistory

logger = logging.getLogger(__name__)


# =============================================================================
# 영업일 유틸 (월~금, 공휴일 미포함 — Phase 2 에서 확장)
# =============================================================================
def count_business_days(start: date, end: date) -> int:
    """start ~ end 사이의 영업일 수 (양끝 포함)."""
    if end < start:
        return 0
    count = 0
    d = start
    while d <= end:
        if d.weekday() < 5:  # 월~금
            count += 1
        d += timedelta(days=1)
    return count


def business_days_ago(days: int, ref: Optional[date] = None) -> date:
    """ref 기준 N 영업일 전 날짜."""
    ref = ref or date.today()
    d = ref
    remaining = days
    while remaining > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            remaining -= 1
    return d


class VisitTracker:
    """
    팀 방문 이력 관리.
    """

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    # Record
    # -------------------------------------------------------------------------
    def record_visit(
        self,
        team_id: str,
        restaurant_id: str,
        visit_date: date,
        participant_count: int,
        satisfaction_scores: Optional[list[int]] = None,
    ) -> VisitHistory:
        avg_satisfaction: Optional[float] = None
        if satisfaction_scores:
            valid = [s for s in satisfaction_scores if s is not None]
            if valid:
                avg_satisfaction = sum(valid) / len(valid)

        try:
            visit = VisitHistory(
                visit_date=visit_date,
                team_id=team_id,
                restaurant_id=restaurant_id,
                participant_count=participant_count,
                avg_satisfaction=avg_satisfaction,
            )
            self.session.add(visit)
            self.session.commit()
            self.session.refresh(visit)
            logger.info(
                "Visit recorded: team=%s restaurant=%s date=%s",
                team_id, restaurant_id, visit_date,
            )
            return visit
        except Exception as e:
            self.session.rollback()
            logger.exception("record_visit failed: %s", e)
            raise

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------
    def get_recent_visits(
        self, team_id: str, days: int = 10
    ) -> list[dict[str, Any]]:
        """최근 N 영업일 방문 기록."""
        start_date = business_days_ago(days)
        rows = list(
            self.session.execute(
                select(VisitHistory, Restaurant)
                .join(Restaurant, VisitHistory.restaurant_id == Restaurant.id, isouter=True)
                .where(
                    VisitHistory.team_id == team_id,
                    VisitHistory.visit_date >= start_date,
                )
                .order_by(VisitHistory.visit_date.desc())
            ).all()
        )
        result = []
        for visit, restaurant in rows:
            result.append({
                "date": visit.visit_date.isoformat(),
                "restaurant_id": visit.restaurant_id,
                "restaurant_name": restaurant.name if restaurant else visit.restaurant_id,
                "participants": visit.participant_count,
                "satisfaction": visit.avg_satisfaction,
            })
        return result

    def get_visit_frequency(
        self, team_id: str, days: int = 30
    ) -> dict[str, dict[str, Any]]:
        """음식점별 방문 빈도."""
        start_date = business_days_ago(days)
        rows = list(
            self.session.execute(
                select(VisitHistory, Restaurant)
                .join(Restaurant, VisitHistory.restaurant_id == Restaurant.id, isouter=True)
                .where(
                    VisitHistory.team_id == team_id,
                    VisitHistory.visit_date >= start_date,
                )
            ).all()
        )

        freq: dict[str, dict[str, Any]] = {}
        today = date.today()
        for visit, restaurant in rows:
            key = restaurant.name if restaurant else visit.restaurant_id
            if key not in freq:
                freq[key] = {
                    "count": 0,
                    "last_visit": visit.visit_date,
                    "avg_satisfaction": None,
                    "_satisfaction_list": [],
                    "restaurant_id": visit.restaurant_id,
                }
            freq[key]["count"] += 1
            if visit.visit_date > freq[key]["last_visit"]:
                freq[key]["last_visit"] = visit.visit_date
            if visit.avg_satisfaction is not None:
                freq[key]["_satisfaction_list"].append(visit.avg_satisfaction)

        # 최종 포맷
        result = {}
        for key, info in freq.items():
            sats = info.pop("_satisfaction_list")
            info["avg_satisfaction"] = (
                round(sum(sats) / len(sats), 2) if sats else None
            )
            info["days_since"] = (today - info["last_visit"]).days
            info["last_visit"] = info["last_visit"].isoformat()
            result[key] = info
        return result

    def get_overvisited(
        self,
        team_id: str,
        threshold: int = 4,
        days: int = 20,
    ) -> list[str]:
        """최근 N 영업일 내 threshold 회 이상 방문한 음식점 ID."""
        start_date = business_days_ago(days)
        rows = self.session.execute(
            select(VisitHistory.restaurant_id, func.count().label("cnt"))
            .where(
                VisitHistory.team_id == team_id,
                VisitHistory.visit_date >= start_date,
            )
            .group_by(VisitHistory.restaurant_id)
            .having(func.count() >= threshold)
        ).all()
        return [row[0] for row in rows]

    # -------------------------------------------------------------------------
    # Freshness
    # -------------------------------------------------------------------------
    def get_days_since_last_visit(
        self, team_id: str, restaurant_id: str
    ) -> Optional[int]:
        """마지막 방문 이후 경과 영업일 수 (없으면 None)."""
        last = self.session.execute(
            select(func.max(VisitHistory.visit_date)).where(
                VisitHistory.team_id == team_id,
                VisitHistory.restaurant_id == restaurant_id,
            )
        ).scalar()
        if last is None:
            return None
        return count_business_days(last, date.today()) - 1  # 본인 제외

    def calculate_freshness_score(
        self, team_id: str, restaurant_id: str
    ) -> int:
        """방문 신선도 점수 (0~100)."""
        days_since = self.get_days_since_last_visit(team_id, restaurant_id)
        if days_since is None:
            return 100
        if days_since == 0:
            return 0
        if days_since >= 10:
            return 90
        if 5 <= days_since <= 9:
            return 70
        if 3 <= days_since <= 4:
            return 40
        return 10  # 1~2 영업일 전

    def get_never_visited(
        self,
        team_id: str,
        all_restaurant_ids: list[str],
    ) -> list[str]:
        """한 번도 방문하지 않은 음식점 ID 리스트."""
        if not all_restaurant_ids:
            return []
        visited = set(
            self.session.execute(
                select(VisitHistory.restaurant_id.distinct()).where(
                    VisitHistory.team_id == team_id,
                    VisitHistory.restaurant_id.in_(all_restaurant_ids),
                )
            ).scalars().all()
        )
        return [rid for rid in all_restaurant_ids if rid not in visited]
