"""
MenuNutritionMapper + MealTracker + NutritionDiagnostic + NutritionRecommendScorer 테스트.
"""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from pipeline.transformers.nutrition_scorer import (
    MealTracker,
    MenuNutritionMapper,
    NutritionDiagnostic,
    NutritionRecommendScorer,
    simplify_menu_name,
)
from pipeline.utils.nutrition_standards import NutritionStatus


# =============================================================================
# simplify_menu_name
# =============================================================================
class TestSimplifyMenuName:
    def test_removes_brand(self):
        assert "서브웨이" not in simplify_menu_name("서브웨이 이탈리안BMT")

    def test_removes_size(self):
        result = simplify_menu_name("왕돈까스 15cm")
        assert "15" not in result
        assert "cm" not in result

    def test_keeps_core(self):
        assert "이탈리안BMT" in simplify_menu_name("서브웨이 이탈리안BMT 15cm")


# =============================================================================
# MenuNutritionMapper
# =============================================================================
class TestMenuNutritionMapper:
    def test_exact_match(self):
        collector = MagicMock()
        collector.search_by_name.return_value = [
            {"food_name": "김치찌개", "calories": 520, "protein": 28},
            {"food_name": "참치김치찌개", "calories": 580, "protein": 32},
        ]
        mapper = MenuNutritionMapper(collector)
        result = mapper.find_best_match("김치찌개")
        assert result is not None
        assert result["food_name"] == "김치찌개"
        assert result["match_type"] == "exact"
        assert result["match_score"] == 1.0

    def test_fuzzy_match(self):
        collector = MagicMock()
        # 정확 일치는 없고, 유사한 것만
        collector.search_by_name.return_value = [
            {"food_name": "김치찌개류", "calories": 520, "protein": 28},
        ]
        mapper = MenuNutritionMapper(collector)
        result = mapper.find_best_match("김치찌개")
        assert result is not None
        assert result["match_type"] in ("fuzzy", "exact")

    def test_no_match_returns_none(self):
        collector = MagicMock()
        collector.search_by_name.return_value = [
            {"food_name": "전혀다른음식이름XYZ", "calories": 100},
        ]
        mapper = MenuNutritionMapper(collector)
        result = mapper.find_best_match("김치찌개")
        # 유사도 80% 미만 → None (단순화 재시도도 동일 결과)
        assert result is None

    def test_cache_hit(self):
        collector = MagicMock()
        collector.search_by_name.return_value = [
            {"food_name": "김치찌개", "calories": 520, "protein": 28},
        ]
        mapper = MenuNutritionMapper(collector)
        mapper.find_best_match("김치찌개")
        mapper.find_best_match("김치찌개")
        # 두 번째는 캐시 hit → collector 는 1회만 호출
        assert collector.search_by_name.call_count == 1

    def test_category_avg_fallback(self):
        collector = MagicMock()
        collector.search_by_name.return_value = []
        mapper = MenuNutritionMapper(collector)
        result = mapper.map_restaurant_to_nutrition(
            {"id": "r1", "category": "한식", "menu_type": "국물"}
        )
        assert result is not None
        assert result["match_type"] == "category_avg"
        assert result["calories"] > 0


# =============================================================================
# MealTracker
# =============================================================================
class TestMealTracker:
    def test_record_and_summary(self):
        tracker = MealTracker()
        base = date(2026, 3, 30)  # 월요일
        for i in range(5):
            tracker.record_meal(
                user_id="u1",
                restaurant_id=f"r{i}",
                menu_name="김치찌개",
                nutrition={"calories": 650, "carbs": 85, "protein": 28,
                           "fat": 18, "sodium": 700},
                meal_date=base + timedelta(days=i),
            )
        summary = tracker.get_weekly_summary("u1", reference_date=base)
        assert summary["meal_count"] == 5
        assert summary["recorded_days"] == 5
        assert summary["weekly_avg"]["calories"] == 650
        assert summary["macro_ratio"]["carbs_pct"] > 0

    def test_empty_user(self):
        tracker = MealTracker()
        summary = tracker.get_weekly_summary("unknown")
        assert summary["meal_count"] == 0
        assert summary["recorded_days"] == 0

    def test_missing_days_tracked(self):
        tracker = MealTracker()
        base = date(2026, 3, 30)  # 월
        for i in [0, 2, 4]:  # 월, 수, 금
            tracker.record_meal(
                user_id="u1",
                restaurant_id=f"r{i}",
                menu_name="X",
                nutrition={"calories": 600, "protein": 25, "carbs": 80,
                           "fat": 18, "sodium": 900},
                meal_date=base + timedelta(days=i),
            )
        summary = tracker.get_weekly_summary("u1", reference_date=base)
        assert summary["recorded_days"] == 3
        assert len(summary["missing_days"]) == 4


# =============================================================================
# NutritionDiagnostic
# =============================================================================
class TestDiagnoseBalanced:
    def test_balanced_high_score(self, balanced_week):
        result = NutritionDiagnostic.diagnose_weekly(balanced_week)
        assert result["overall_status"] == "양호"
        assert result["overall_score"] >= 85

    def test_protein_deficient(self, protein_deficient_week):
        result = NutritionDiagnostic.diagnose_weekly(protein_deficient_week)
        protein_status = result["nutrient_status"]["protein"]["status"]
        assert protein_status == NutritionStatus.DEFICIENT.value
        # 추천 메시지에 단백질이 우선으로 포함
        assert any("단백질" in rec for rec in result["recommendations"])

    def test_sodium_excess(self, sodium_excess_week):
        result = NutritionDiagnostic.diagnose_weekly(sodium_excess_week)
        sodium_status = result["nutrient_status"]["sodium"]["status"]
        assert sodium_status == NutritionStatus.EXCESSIVE.value
        assert any("나트륨" in rec for rec in result["recommendations"])

    def test_data_insufficient(self):
        sparse = {
            "weekly_avg": {},
            "recorded_days": 0,
        }
        result = NutritionDiagnostic.diagnose_weekly(sparse)
        assert result["overall_status"] == "데이터부족"

    def test_macro_balance_check(self, protein_deficient_week):
        """탄단지 비율 70:10:20 → 불균형."""
        result = NutritionDiagnostic.diagnose_weekly(protein_deficient_week)
        assert result["macro_balance"]["status"] == "불균형"
        assert "단백질" in result["macro_balance"]["verdict"]


# =============================================================================
# NutritionRecommendScorer
# =============================================================================
class TestRecommendScorer:
    def test_high_protein_bonus_when_deficient(self, protein_deficient_week):
        high_protein_restaurant = {
            "calories": 650, "carbs": 65, "protein": 35, "fat": 18, "sodium": 700
        }
        score = NutritionRecommendScorer.calculate_nutrition_score(
            high_protein_restaurant, protein_deficient_week
        )
        assert score >= 75

    def test_sodium_penalty_when_excess(self, sodium_excess_week):
        # 고나트륨 + 고지방 (밸런스·칼로리 보너스 미적용) → 명확한 페널티
        high_sodium_restaurant = {
            "calories": 900, "carbs": 60, "protein": 15, "fat": 45, "sodium": 1500
        }
        score = NutritionRecommendScorer.calculate_nutrition_score(
            high_sodium_restaurant, sodium_excess_week
        )
        assert score < 60  # base 60 - 15 penalty, 보너스 없음

    def test_balanced_restaurant_bonus(self, balanced_week):
        balanced_restaurant = {
            "calories": 650, "carbs": 88, "protein": 33, "fat": 18, "sodium": 700
        }
        score = NutritionRecommendScorer.calculate_nutrition_score(
            balanced_restaurant, balanced_week
        )
        assert score >= 70

    def test_rank_descending(self, protein_deficient_week):
        restaurants = [
            {"id": "a", "nutrition": {"calories": 650, "protein": 35, "carbs": 65, "fat": 18, "sodium": 700}},
            {"id": "b", "nutrition": {"calories": 700, "protein": 15, "carbs": 100, "fat": 25, "sodium": 900}},
            {"id": "c", "nutrition": {"calories": 600, "protein": 28, "carbs": 70, "fat": 20, "sodium": 800}},
        ]
        ranked = NutritionRecommendScorer.rank_by_nutrition(
            restaurants, protein_deficient_week
        )
        scores = [r["nutrition_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)
        # 고단백 식당 "a" 가 최상위
        assert ranked[0]["id"] == "a"

    def test_advice_message(self, protein_deficient_week):
        high_protein = {"calories": 650, "protein": 30, "fat": 18, "sodium": 700}
        advice = NutritionRecommendScorer.get_nutrition_advice_for_restaurant(
            high_protein, protein_deficient_week
        )
        assert "단백질" in advice
