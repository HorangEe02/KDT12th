"""
TeamPreferenceAnalyzer + TeamRecommendScorer.

- 장기 선호도 분석 (카테고리, 식당, 가격대, 거리)
- 다양성 점수
- 투표+신선도+선호를 합쳐 team_score 산출
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import date, timedelta
from statistics import mean
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Restaurant, Veto, VisitHistory

logger = logging.getLogger(__name__)


# =============================================================================
# TeamPreferenceAnalyzer
# =============================================================================
class TeamPreferenceAnalyzer:
    """
    팀의 장기 선호도 분석.
    """

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    def _load_visits_with_restaurants(
        self, team_id: str, days: int
    ) -> list[tuple[VisitHistory, Optional[Restaurant]]]:
        since = date.today() - timedelta(days=days)
        rows = self.session.execute(
            select(VisitHistory, Restaurant)
            .join(Restaurant, VisitHistory.restaurant_id == Restaurant.id, isouter=True)
            .where(
                VisitHistory.team_id == team_id,
                VisitHistory.visit_date >= since,
            )
        ).all()
        return list(rows)

    # -------------------------------------------------------------------------
    def analyze_team_preference(
        self, team_id: str, days: int = 60
    ) -> dict[str, Any]:
        rows = self._load_visits_with_restaurants(team_id, days)

        if not rows:
            return {
                "favorite_categories": [],
                "favorite_restaurants": [],
                "avoided_restaurants": [],
                "preferred_price_range": None,
                "preferred_distance": None,
                "variety_score": 0,
            }

        # Category aggregation
        cat_stats: dict[str, dict[str, Any]] = {}
        rest_stats: dict[str, dict[str, Any]] = {}
        prices: list[int] = []
        distances: list[int] = []
        total_visits = len(rows)

        for visit, restaurant in rows:
            if restaurant is None:
                continue
            cat = restaurant.category or "기타"
            c = cat_stats.setdefault(cat, {"count": 0, "satisfactions": []})
            c["count"] += 1
            if visit.avg_satisfaction is not None:
                c["satisfactions"].append(visit.avg_satisfaction)

            rs = rest_stats.setdefault(restaurant.id, {
                "name": restaurant.name,
                "visits": 0,
                "satisfactions": [],
            })
            rs["visits"] += 1
            if visit.avg_satisfaction is not None:
                rs["satisfactions"].append(visit.avg_satisfaction)

            if restaurant.price_avg is not None:
                prices.append(restaurant.price_avg)
            if restaurant.distance_m is not None:
                distances.append(int(restaurant.distance_m))

        favorite_categories = sorted(
            [
                {
                    "category": cat,
                    "visit_pct": round(info["count"] / total_visits * 100, 1),
                    "avg_satisfaction": (
                        round(mean(info["satisfactions"]), 2)
                        if info["satisfactions"] else None
                    ),
                }
                for cat, info in cat_stats.items()
            ],
            key=lambda x: x["visit_pct"],
            reverse=True,
        )

        favorite_restaurants = sorted(
            [
                {
                    "restaurant_id": rid,
                    "name": info["name"],
                    "visits": info["visits"],
                    "avg_satisfaction": (
                        round(mean(info["satisfactions"]), 2)
                        if info["satisfactions"] else None
                    ),
                }
                for rid, info in rest_stats.items()
            ],
            key=lambda x: x["visits"],
            reverse=True,
        )[:10]

        # 회피 식당: 만족도 < 3.0 또는 거부권 빈도 높은 것
        since = date.today() - timedelta(days=days)
        veto_counter = Counter()
        veto_rows = self.session.execute(
            select(Veto).where(Veto.veto_date >= since)
        ).scalars().all()
        for veto in veto_rows:
            veto_counter[veto.restaurant_id] += 1

        avoided = []
        for rid, info in rest_stats.items():
            avg_sat = (
                mean(info["satisfactions"]) if info["satisfactions"] else None
            )
            if (avg_sat is not None and avg_sat < 3.0) or veto_counter.get(rid, 0) >= 2:
                avoided.append({
                    "restaurant_id": rid,
                    "name": info["name"],
                    "veto_count": veto_counter.get(rid, 0),
                    "avg_satisfaction": round(avg_sat, 2) if avg_sat else None,
                })
        avoided.sort(key=lambda x: (x["veto_count"] or 0), reverse=True)

        preferred_price = None
        if prices:
            preferred_price = {
                "min": min(prices),
                "max": max(prices),
                "avg": round(sum(prices) / len(prices)),
            }

        preferred_distance = None
        if distances:
            preferred_distance = {
                "max": max(distances),
                "avg": round(sum(distances) / len(distances)),
            }

        variety_score = self.calculate_variety_score(team_id, days=days)

        return {
            "favorite_categories": favorite_categories,
            "favorite_restaurants": favorite_restaurants,
            "avoided_restaurants": avoided[:5],
            "preferred_price_range": preferred_price,
            "preferred_distance": preferred_distance,
            "variety_score": variety_score,
        }

    # -------------------------------------------------------------------------
    def calculate_variety_score(
        self, team_id: str, days: int = 20
    ) -> int:
        rows = self._load_visits_with_restaurants(team_id, days)
        if not rows:
            return 0
        total_visits = len(rows)
        unique_restaurants = len({v.restaurant_id for v, _ in rows})
        return int(round(unique_restaurants / total_visits * 100))

    # -------------------------------------------------------------------------
    def predict_team_preference(
        self, team_id: str, restaurant_id: str, days: int = 60
    ) -> int:
        """
        특정 음식점에 대한 팀 선호 예측 점수 (0~100).
        """
        restaurant = self.session.get(Restaurant, restaurant_id)
        if restaurant is None:
            return 50  # neutral

        preference = self.analyze_team_preference(team_id, days=days)

        # 카테고리 만족도
        cat_score = 50.0
        for cat_info in preference["favorite_categories"]:
            if cat_info["category"] == (restaurant.category or "기타"):
                avg_sat = cat_info["avg_satisfaction"]
                if avg_sat is not None:
                    cat_score = avg_sat * 20  # 1~5 → 20~100
                else:
                    cat_score = 60
                break

        # 본인 식당 만족도
        own_score: Optional[float] = None
        for fav in preference["favorite_restaurants"]:
            if fav["restaurant_id"] == restaurant_id:
                avg_sat = fav["avg_satisfaction"]
                if avg_sat is not None:
                    own_score = avg_sat * 20
                break

        # 가격대 부합도
        price_score = 60.0
        price_pref = preference["preferred_price_range"]
        if price_pref and restaurant.price_avg is not None:
            diff = abs(restaurant.price_avg - price_pref["avg"])
            # avg 의 30% 이내 → 80점, 그 이상 점진 감소
            tolerance = max(price_pref["avg"] * 0.3, 1000)
            if diff <= tolerance:
                price_score = 80
            else:
                price_score = max(30, 80 - (diff - tolerance) / 1000 * 10)

        # 거리 부합도
        distance_score = 60.0
        dist_pref = preference["preferred_distance"]
        if dist_pref and restaurant.distance_m is not None:
            max_pref = dist_pref["max"]
            if restaurant.distance_m <= max_pref:
                distance_score = 80
            else:
                distance_score = max(30, 80 - (restaurant.distance_m - max_pref) / 50 * 5)

        weights = {
            "category": 0.40,
            "own": 0.30,
            "price": 0.15,
            "distance": 0.15,
        }
        if own_score is None:
            # own_score 없으면 category 에 가중치 재분배
            final = (
                cat_score * (weights["category"] + weights["own"])
                + price_score * weights["price"]
                + distance_score * weights["distance"]
            )
        else:
            final = (
                cat_score * weights["category"]
                + own_score * weights["own"]
                + price_score * weights["price"]
                + distance_score * weights["distance"]
            )

        return max(0, min(100, int(round(final))))

    # -------------------------------------------------------------------------
    def get_team_mood(self, team_id: str) -> str:
        preference = self.analyze_team_preference(team_id, days=30)
        variety_score = preference["variety_score"]

        # 최근 만족도
        recent_visits = self._load_visits_with_restaurants(team_id, days=14)
        satisfactions = [v.avg_satisfaction for v, _ in recent_visits if v.avg_satisfaction is not None]
        avg_recent = mean(satisfactions) if satisfactions else None

        if avg_recent is not None:
            if avg_recent < 3.0:
                return "불만족"
            if avg_recent >= 4.0 and variety_score > 70:
                return "모험적"
            if avg_recent >= 4.0:
                return "만족"
        if variety_score > 70:
            return "모험적"
        if variety_score < 40:
            return "보수적"
        return "보통"


# =============================================================================
# TeamRecommendScorer
# =============================================================================
class TeamRecommendScorer:
    """
    투표 + 신선도 + 선호 예측 → 팀 점수 (0~100).
    """

    VOTE_WEIGHT: float = 0.50
    FRESHNESS_WEIGHT: float = 0.25
    PREFERENCE_WEIGHT: float = 0.25

    def __init__(
        self,
        analyzer: TeamPreferenceAnalyzer,
        visit_tracker,  # VisitTracker (순환 import 방지)
    ):
        self.analyzer = analyzer
        self.visit_tracker = visit_tracker

    # -------------------------------------------------------------------------
    @staticmethod
    def _vote_score(votes: int, is_vetoed: bool) -> int:
        """투표 점수 (0~100). 거부권 있으면 -30."""
        if votes <= 0:
            base = 0
        elif votes == 1:
            base = 40
        elif votes == 2:
            base = 65
        else:
            base = 85
        if is_vetoed:
            base = max(0, base - 30)
        return base

    # -------------------------------------------------------------------------
    def calculate_team_score(
        self,
        team_id: str,
        restaurant_id: str,
        vote_status: dict[str, Any],
    ) -> int:
        """
        특정 음식점의 팀 점수.
        """
        # 투표 수 카운트
        votes = 0
        for t in vote_status.get("tally", []):
            if t.get("restaurant_id") == restaurant_id:
                votes = t.get("votes", 0)
                break

        # 거부권
        is_vetoed = any(
            v.get("restaurant_id") == restaurant_id
            for v in vote_status.get("vetoed", [])
        )

        vote_s = self._vote_score(votes, is_vetoed)
        freshness_s = self.visit_tracker.calculate_freshness_score(team_id, restaurant_id)
        preference_s = self.analyzer.predict_team_preference(team_id, restaurant_id)

        total = (
            vote_s * self.VOTE_WEIGHT
            + freshness_s * self.FRESHNESS_WEIGHT
            + preference_s * self.PREFERENCE_WEIGHT
        )
        return max(0, min(100, int(round(total))))

    # -------------------------------------------------------------------------
    def rank_for_team(
        self,
        team_id: str,
        restaurants: list[dict[str, Any]],
        vote_status: dict[str, Any],
    ) -> list[dict[str, Any]]:
        scored = []
        for r in restaurants:
            rid = r.get("id")
            if not rid:
                continue
            score = self.calculate_team_score(team_id, rid, vote_status)
            new_r = dict(r)
            new_r["team_score"] = score
            scored.append(new_r)
        scored.sort(key=lambda x: x["team_score"], reverse=True)
        return scored
