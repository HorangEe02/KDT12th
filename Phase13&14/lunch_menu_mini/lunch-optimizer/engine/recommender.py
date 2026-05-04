"""
LunchRecommender — Mini 통합 추천 엔진.

4개 소주제의 scorer 를 하나로 조립:
    distance (Subtopic 1)  — 거리 점수
    weather  (Subtopic 2)  — 날씨 적합도
    nutrition(Subtopic 3)  — 주간 이력 기반 영양 점수
    team     (Subtopic 4)  — 투표 + 신선도 + 선호 예측

공식:
    composite = distance*0.3 + weather*0.2 + nutrition*0.2 + team*0.3

투표 없음 → 가중치 재분배:
    composite = distance*0.4 + weather*0.3 + nutrition*0.3 + team*0.0

반환: 추천 리스트 + highlights/warnings 자연어 생성.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import Restaurant
from pipeline.collectors.vote_collector import VoteManager
from pipeline.loaders.db_loader import (
    NutritionLoader, RestaurantLoader, WeatherLoader
)
from pipeline.transformers.nutrition_scorer import (
    NutritionDiagnostic, NutritionRecommendScorer
)
from pipeline.transformers.team_scorer import (
    TeamPreferenceAnalyzer, TeamRecommendScorer
)
from pipeline.transformers.visit_tracker import VisitTracker
from pipeline.transformers.weather_scorer import WeatherMenuScorer

logger = logging.getLogger(__name__)


# =============================================================================
# 가중치
# =============================================================================
DEFAULT_WEIGHTS: dict[str, float] = {
    "distance": 0.3,
    "weather": 0.2,
    "nutrition": 0.2,
    "team": 0.3,
}

NO_VOTE_WEIGHTS: dict[str, float] = {
    "distance": 0.4,
    "weather": 0.3,
    "nutrition": 0.3,
    "team": 0.0,
}


# =============================================================================
# LunchRecommender
# =============================================================================
class LunchRecommender:
    """
    Mini 최종 통합 추천 엔진.
    """

    def __init__(self, session: Session, team_id: str, user_id: str):
        self.session = session
        self.team_id = team_id
        self.user_id = user_id

        # Loader / Manager 인스턴스
        self.restaurant_loader = RestaurantLoader(session)
        self.weather_loader = WeatherLoader(session)
        self.nutrition_loader = NutritionLoader(session)
        self.vote_manager = VoteManager(session)
        self.visit_tracker = VisitTracker(session)
        self.preference_analyzer = TeamPreferenceAnalyzer(session)
        self.team_scorer = TeamRecommendScorer(
            self.preference_analyzer, self.visit_tracker
        )

        # 캐시 (한 번의 get_recommendations 호출 동안 재사용)
        self._weather_cache: Optional[dict[str, Any]] = None
        self._nutrition_summary_cache: Optional[dict[str, Any]] = None
        self._vote_status_cache: Optional[dict[str, Any]] = None
        self._diagnosis_cache: Optional[dict[str, Any]] = None

    # -------------------------------------------------------------------------
    # 컨텍스트 로딩
    # -------------------------------------------------------------------------
    def _get_weather(self) -> dict[str, Any]:
        if self._weather_cache is None:
            latest = self.weather_loader.get_latest_weather()
            self._weather_cache = latest.to_dict() if latest is not None else {}
        return self._weather_cache

    def _get_nutrition_summary(self) -> dict[str, Any]:
        if self._nutrition_summary_cache is None:
            today = date.today()
            monday = today - timedelta(days=today.weekday())
            stats = self.nutrition_loader.get_weekly_stats(self.user_id, monday)
            # macro_ratio 추가 (Subtopic 3 의 weekly 엔드포인트와 동일)
            total = stats.get("weekly_total") or {}
            c = (total.get("carbs", 0) or 0) * 4
            p = (total.get("protein", 0) or 0) * 4
            f = (total.get("fat", 0) or 0) * 9
            total_macro = c + p + f
            if total_macro > 0:
                stats["macro_ratio"] = {
                    "carbs_pct": round(c / total_macro * 100, 1),
                    "protein_pct": round(p / total_macro * 100, 1),
                    "fat_pct": round(f / total_macro * 100, 1),
                }
            else:
                stats["macro_ratio"] = {"carbs_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0}
            self._nutrition_summary_cache = stats
        return self._nutrition_summary_cache

    def _get_diagnosis(self) -> dict[str, Any]:
        if self._diagnosis_cache is None:
            summary = self._get_nutrition_summary()
            self._diagnosis_cache = NutritionDiagnostic.diagnose_weekly(summary)
        return self._diagnosis_cache

    def _get_vote_status(self) -> dict[str, Any]:
        if self._vote_status_cache is None:
            self._vote_status_cache = self.vote_manager.get_current_status(self.team_id)
        return self._vote_status_cache

    # -------------------------------------------------------------------------
    # 메인 진입점
    # -------------------------------------------------------------------------
    def get_recommendations(self, top_n: int = 5) -> list[dict[str, Any]]:
        """
        4축 가중합 통합 추천.
        """
        restaurants = self.restaurant_loader.get_active_restaurants()
        if not restaurants:
            logger.warning("No active restaurants to rank")
            return []

        weather = self._get_weather()
        nutrition_summary = self._get_nutrition_summary()
        diagnosis = self._get_diagnosis()
        vote_status = self._get_vote_status()

        # 투표 여부에 따른 가중치
        has_votes = vote_status.get("voted_count", 0) > 0
        weights = DEFAULT_WEIGHTS if has_votes else NO_VOTE_WEIGHTS

        scored_list = []
        for restaurant in restaurants:
            r_dict = restaurant.to_dict()

            # 1. Distance (이미 계산돼 DB 에 저장됨)
            distance_score = int(r_dict.get("distance_score") or 0)

            # 2. Weather
            if weather:
                weather_score = WeatherMenuScorer.calculate_weather_score(r_dict, weather)
            else:
                weather_score = 50  # neutral

            # 3. Nutrition
            nutrition_info = self.nutrition_loader.get_nutrition_by_restaurant(restaurant.id)
            nutrition_dict = nutrition_info.to_dict() if nutrition_info else {}
            nutrition_score = NutritionRecommendScorer.calculate_nutrition_score(
                nutrition_dict, nutrition_summary
            )

            # 4. Team
            team_score = self.team_scorer.calculate_team_score(
                self.team_id, restaurant.id, vote_status
            )

            # Composite
            composite = (
                distance_score * weights["distance"]
                + weather_score * weights["weather"]
                + nutrition_score * weights["nutrition"]
                + team_score * weights["team"]
            )
            composite = int(round(composite))

            scores = {
                "distance": distance_score,
                "weather": weather_score,
                "nutrition": nutrition_score,
                "team": team_score,
            }

            highlights = self._generate_highlights(
                r_dict, scores, weather, diagnosis, vote_status, nutrition_dict
            )
            warnings = self._generate_warnings(
                r_dict, scores, diagnosis, nutrition_dict, vote_status
            )

            scored_list.append({
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.name,
                "category": restaurant.category,
                "menu_type": restaurant.menu_type,
                "distance_m": restaurant.distance_m,
                "composite_score": composite,
                "scores": scores,
                "highlights": highlights,
                "warnings": warnings,
                "weights_used": weights,
            })

        scored_list.sort(key=lambda x: x["composite_score"], reverse=True)

        # Rank 부여
        for i, item in enumerate(scored_list, start=1):
            item["rank"] = i

        return scored_list[:top_n]

    # -------------------------------------------------------------------------
    # Highlights / Warnings
    # -------------------------------------------------------------------------
    def _generate_highlights(
        self,
        restaurant: dict[str, Any],
        scores: dict[str, int],
        weather: dict[str, Any],
        diagnosis: dict[str, Any],
        vote_status: dict[str, Any],
        nutrition: dict[str, Any],
    ) -> list[str]:
        highlights: list[str] = []

        # 가장 가까운 곳 (≥ 85점)
        if scores["distance"] >= 85:
            distance_m = restaurant.get("distance_m", 0)
            highlights.append(f"🏃 가까운 곳 (도보 약 {int(distance_m)}m)")

        # 날씨 적합 (≥ 75)
        if scores["weather"] >= 75:
            weather_str = weather.get("sky_str") or ""
            temp = weather.get("temp")
            if temp is not None:
                highlights.append(f"🌤️ 오늘 날씨({temp:.0f}°C {weather_str})에 잘 맞아요")
            else:
                highlights.append("🌤️ 오늘 날씨에 잘 맞는 메뉴예요")

        # 영양 보충
        if scores["nutrition"] >= 75:
            lack = []
            for key, info in (diagnosis.get("nutrient_status") or {}).items():
                if info.get("status") == "부족":
                    lack.append(key)
            if "protein" in lack and nutrition.get("protein", 0) and nutrition["protein"] >= 25:
                highlights.append("🥩 이번 주 부족한 단백질 보충에 좋아요")
            elif lack:
                highlights.append("📊 이번 주 영양 균형에 도움이 돼요")
            else:
                highlights.append("📊 영양 균형이 좋은 메뉴예요")

        # 팀 투표
        for t in vote_status.get("tally", []):
            if t.get("restaurant_id") == restaurant["id"] and t.get("votes", 0) > 0:
                highlights.append(f"🗳️ 팀원 {t['votes']}명이 투표했어요")
                break

        # 새로운 곳 (신선도 100)
        freshness = self.visit_tracker.calculate_freshness_score(
            self.team_id, restaurant["id"]
        )
        if freshness == 100 and len(highlights) < 3:
            highlights.append("✨ 한 번도 방문하지 않은 새로운 곳이에요")

        return highlights[:3]

    def _generate_warnings(
        self,
        restaurant: dict[str, Any],
        scores: dict[str, int],
        diagnosis: dict[str, Any],
        nutrition: dict[str, Any],
        vote_status: dict[str, Any],
    ) -> list[str]:
        warnings: list[str] = []

        # 거부권
        for v in vote_status.get("vetoed", []):
            if v.get("restaurant_id") == restaurant["id"]:
                reason = v.get("reason", "") or "이유 미기재"
                warnings.append(f"⛔ 거부권이 걸린 음식점 ({reason})")
                break

        # 나트륨 과다 주간 + 고나트륨 메뉴
        sodium_status = (
            diagnosis.get("nutrient_status", {}).get("sodium", {}).get("status")
        )
        if sodium_status == "과다":
            if nutrition.get("sodium") and nutrition["sodium"] >= 1200:
                warnings.append("⚠️ 나트륨이 높아요. 국물은 남기세요")

        # 지방 과다
        fat_status = (
            diagnosis.get("nutrient_status", {}).get("fat", {}).get("status")
        )
        if fat_status == "과다":
            if nutrition.get("fat") and nutrition["fat"] >= 30:
                warnings.append("⚠️ 지방 섭취가 많은 한 주였어요")

        # 최근 방문
        freshness = self.visit_tracker.calculate_freshness_score(
            self.team_id, restaurant["id"]
        )
        if freshness <= 10:
            warnings.append("🔁 최근에 방문한 곳이에요")

        return warnings[:2]

    # -------------------------------------------------------------------------
    # Explain
    # -------------------------------------------------------------------------
    def explain_recommendation(
        self, restaurant_id: str
    ) -> dict[str, Any]:
        """특정 음식점의 상세 추천 이유."""
        recommendations = self.get_recommendations(top_n=1000)
        match = next(
            (r for r in recommendations if r["restaurant_id"] == restaurant_id), None
        )
        if match is None:
            return {"error": "Restaurant not found", "restaurant_id": restaurant_id}

        # 추가 설명 데이터
        vote_status = self._get_vote_status()
        team_votes = next(
            (t["votes"] for t in vote_status.get("tally", [])
             if t["restaurant_id"] == restaurant_id),
            0,
        )

        return {
            **match,
            "details": {
                "composite_formula": (
                    f"distance*{match['weights_used']['distance']} + "
                    f"weather*{match['weights_used']['weather']} + "
                    f"nutrition*{match['weights_used']['nutrition']} + "
                    f"team*{match['weights_used']['team']}"
                ),
                "team_votes": team_votes,
                "freshness_score": self.visit_tracker.calculate_freshness_score(
                    self.team_id, restaurant_id
                ),
            },
        }
