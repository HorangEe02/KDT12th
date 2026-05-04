"""
영양 분석 · 매핑 · 진단 · 추천 엔진.

- MenuNutritionMapper      : 메뉴명 → 식품안전나라 DB 퍼지 매칭
- MealTracker              : 식사 기록 관리 + 주간 요약
- NutritionDiagnostic      : 주간 진단 + 추천 메시지
- NutritionRecommendScorer : 주간 이력 기반 음식점 영양 점수
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Optional

from pipeline.collectors.nutrition_collector import NutritionCollector
from pipeline.utils.nutrition_standards import (
    CATEGORY_AVG_NUTRITION,
    DEFICIENT_THRESHOLD,
    EXCESSIVE_THRESHOLD,
    IDEAL_MACRO_RATIO,
    LUNCH_STANDARDS,
    MACRO_KCAL_PER_G,
    NutritionStatus,
    deviation_pct,
    judge_nutrient,
    lookup_category_avg,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 퍼지 매칭 유틸 (thefuzz 가 있으면 우선, 없으면 difflib)
# =============================================================================
def _similarity(a: str, b: str) -> float:
    """0~1 유사도. thefuzz 설치 시 WRatio/100, 아니면 SequenceMatcher."""
    if not a or not b:
        return 0.0
    try:
        from thefuzz import fuzz  # type: ignore
        return fuzz.WRatio(a, b) / 100.0
    except ImportError:
        pass
    try:
        from fuzzywuzzy import fuzz  # type: ignore
        return fuzz.WRatio(a, b) / 100.0
    except ImportError:
        pass
    return SequenceMatcher(None, a, b).ratio()


_BRAND_KEYWORDS: tuple[str, ...] = (
    "서브웨이", "맥도날드", "롯데리아", "버거킹", "KFC",
    "스타벅스", "이디야", "투썸", "파리바게뜨",
)
_SIZE_KEYWORDS: tuple[str, ...] = (
    "레귤러", "라지", "스몰", "미니", "왕", "특대", "점보",
)
_UNIT_RE = re.compile(r"\d+\s?(cm|ml|g|인분|개|팩|세트)")


def simplify_menu_name(name: str) -> str:
    """브랜드·사이즈·수량 제거 후 핵심 키워드만 추출."""
    if not name:
        return ""
    text = name
    for brand in _BRAND_KEYWORDS:
        text = text.replace(brand, "")
    for size in _SIZE_KEYWORDS:
        text = text.replace(size, "")
    text = _UNIT_RE.sub("", text)
    # 특수문자 제거
    text = re.sub(r"[^\w가-힣\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# =============================================================================
# MenuNutritionMapper
# =============================================================================
class MenuNutritionMapper:
    """
    음식점 메뉴 → 식품안전나라 영양성분 DB 매핑.

    매핑 우선순위:
        1. 캐시 hit
        2. 정확 일치 (exact)
        3. 퍼지 매칭 (similarity ≥ 0.80)
        4. 단순화 후 재검색
        5. 실패 → None
    """

    FUZZY_THRESHOLD: float = 0.80

    def __init__(self, collector: NutritionCollector):
        self.collector = collector
        self._cache: dict[str, Optional[dict[str, Any]]] = {}

    def find_best_match(
        self,
        menu_name: str,
    ) -> Optional[dict[str, Any]]:
        """단일 메뉴명 → 최적 영양 매칭."""
        if not menu_name or not menu_name.strip():
            return None

        key = menu_name.strip()
        if key in self._cache:
            return self._cache[key]

        candidates = self.collector.search_by_name(key, max_results=10)
        result = self._select_best(candidates, key)

        if result is None:
            simplified = simplify_menu_name(key)
            if simplified and simplified != key:
                candidates = self.collector.search_by_name(simplified, max_results=10)
                result = self._select_best(candidates, simplified)
                if result is not None:
                    result["match_type"] = "simplified"

        self._cache[key] = result
        return result

    def _select_best(
        self,
        candidates: list[dict[str, Any]],
        query: str,
    ) -> Optional[dict[str, Any]]:
        if not candidates:
            return None

        # 1. 정확 일치
        for c in candidates:
            if c.get("food_name") == query:
                return {**c, "match_type": "exact", "match_score": 1.0}

        # 2. 퍼지 매칭
        scored = [
            (_similarity(query, c.get("food_name", "")), c)
            for c in candidates
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best = scored[0]
        if best_score >= self.FUZZY_THRESHOLD:
            return {**best, "match_type": "fuzzy", "match_score": best_score}

        return None

    def map_restaurant_to_nutrition(
        self,
        restaurant: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """
        음식점 → 대표 영양 정보 (실패 시 카테고리 평균 fallback).
        """
        for key in ("sub_category", "menu_type", "category"):
            value = restaurant.get(key)
            if value:
                result = self.find_best_match(str(value))
                if result is not None:
                    return result

        # Fallback: 카테고리 평균
        category = restaurant.get("category")
        menu_type = restaurant.get("menu_type")
        avg = lookup_category_avg(category, menu_type)
        return {
            **avg,
            "food_name": f"[평균] {category or '기타'}",
            "food_code": None,
            "match_type": "category_avg",
            "match_score": None,
            "serving_size": 100.0,
        }

    def get_category_avg_nutrition(self, category: str) -> dict[str, float]:
        """카테고리 평균 영양값 조회 (외부 호출용)."""
        return lookup_category_avg(category, None)

    def build_nutrition_cache(
        self,
        restaurants: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """여러 음식점 일괄 매핑."""
        result: dict[str, dict[str, Any]] = {}
        for i, r in enumerate(restaurants):
            rid = str(r.get("id", "")).strip()
            if not rid:
                continue
            nutrition = self.map_restaurant_to_nutrition(r)
            if nutrition:
                result[rid] = nutrition
            if (i + 1) % 10 == 0:
                logger.info(
                    "Nutrition mapping progress: %d/%d", i + 1, len(restaurants)
                )
        logger.info("Nutrition cache built: %d/%d entries", len(result), len(restaurants))
        return result


# =============================================================================
# MealTracker
# =============================================================================
class MealTracker:
    """
    식사 기록 저장 + 주간 영양 요약.

    본 클래스는 메모리 기반 구현이며, DB 영속화는 `NutritionLoader` 가 담당.
    DB 미사용 테스트·단독 사용 시에는 본 클래스의 `_records` dict 를 직접 활용.
    """

    def __init__(self):
        self._records: list[dict[str, Any]] = []

    def record_meal(
        self,
        user_id: str,
        restaurant_id: str,
        menu_name: str,
        nutrition: dict[str, Any],
        meal_date: Optional[date] = None,
        satisfaction: Optional[int] = None,
    ) -> dict[str, Any]:
        meal_date = meal_date or date.today()
        record = {
            "id": len(self._records) + 1,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "menu_name": menu_name,
            "meal_date": meal_date,
            "calories": float(nutrition.get("calories") or 0),
            "carbs": float(nutrition.get("carbs") or 0),
            "protein": float(nutrition.get("protein") or 0),
            "fat": float(nutrition.get("fat") or 0),
            "sugar": float(nutrition.get("sugar") or 0),
            "sodium": float(nutrition.get("sodium") or 0),
            "satisfaction": satisfaction,
            "created_at": datetime.utcnow(),
        }
        self._records.append(record)
        return record

    def get_weekly_summary(
        self,
        user_id: str,
        week_offset: int = 0,
        reference_date: Optional[date] = None,
    ) -> dict[str, Any]:
        """
        `week_offset=0` → 이번 주, `-1` → 지난 주.
        """
        today = reference_date or date.today()
        # 이번 주 월요일
        monday = today - timedelta(days=today.weekday())
        week_start = monday + timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)

        records = [
            r for r in self._records
            if r["user_id"] == user_id and week_start <= r["meal_date"] <= week_end
        ]

        by_day: dict[date, list[dict[str, Any]]] = defaultdict(list)
        for r in records:
            by_day[r["meal_date"]].append(r)

        # 일별 합계
        daily_records = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            day_records = by_day.get(d, [])
            if not day_records:
                continue
            total = {
                "date": d.isoformat(),
                "day": ["월", "화", "수", "목", "금", "토", "일"][i],
                "calories": sum(r["calories"] for r in day_records),
                "carbs": sum(r["carbs"] for r in day_records),
                "protein": sum(r["protein"] for r in day_records),
                "fat": sum(r["fat"] for r in day_records),
                "sodium": sum(r["sodium"] for r in day_records),
            }
            daily_records.append(total)

        recorded_days = len(daily_records)
        missing_days = [
            (week_start + timedelta(days=i)).isoformat()
            for i in range(7)
            if not by_day.get(week_start + timedelta(days=i))
        ]

        if recorded_days == 0:
            return {
                "period": {"start": week_start.isoformat(), "end": week_end.isoformat()},
                "meal_count": 0,
                "daily_records": [],
                "weekly_avg": {},
                "weekly_total": {},
                "macro_ratio": {},
                "recorded_days": 0,
                "missing_days": missing_days,
            }

        # 주간 평균 (기록이 있는 날만)
        weekly_avg = {
            k: sum(d[k] for d in daily_records) / recorded_days
            for k in ("calories", "carbs", "protein", "fat", "sodium")
        }
        weekly_total = {
            k: sum(d[k] for d in daily_records)
            for k in ("calories", "carbs", "protein", "fat", "sodium")
        }

        # 탄단지 비율 (kcal 기준)
        kcal_from_carbs = weekly_total["carbs"] * MACRO_KCAL_PER_G["carbs"]
        kcal_from_protein = weekly_total["protein"] * MACRO_KCAL_PER_G["protein"]
        kcal_from_fat = weekly_total["fat"] * MACRO_KCAL_PER_G["fat"]
        total_macro_kcal = kcal_from_carbs + kcal_from_protein + kcal_from_fat

        if total_macro_kcal > 0:
            macro_ratio = {
                "carbs_pct": round(kcal_from_carbs / total_macro_kcal * 100, 1),
                "protein_pct": round(kcal_from_protein / total_macro_kcal * 100, 1),
                "fat_pct": round(kcal_from_fat / total_macro_kcal * 100, 1),
            }
        else:
            macro_ratio = {"carbs_pct": 0.0, "protein_pct": 0.0, "fat_pct": 0.0}

        return {
            "period": {"start": week_start.isoformat(), "end": week_end.isoformat()},
            "meal_count": len(records),
            "daily_records": daily_records,
            "weekly_avg": weekly_avg,
            "weekly_total": weekly_total,
            "macro_ratio": macro_ratio,
            "recorded_days": recorded_days,
            "missing_days": missing_days,
        }

    def get_daily_detail(
        self, user_id: str, meal_date: date
    ) -> Optional[dict[str, Any]]:
        day_records = [
            r for r in self._records
            if r["user_id"] == user_id and r["meal_date"] == meal_date
        ]
        if not day_records:
            return None
        total = {
            "date": meal_date.isoformat(),
            "meal_count": len(day_records),
            "calories": sum(r["calories"] for r in day_records),
            "protein": sum(r["protein"] for r in day_records),
            "carbs": sum(r["carbs"] for r in day_records),
            "fat": sum(r["fat"] for r in day_records),
            "sodium": sum(r["sodium"] for r in day_records),
            "records": day_records,
        }
        return total

    def get_nutrient_trend(
        self, user_id: str, days: int = 14
    ) -> list[dict[str, Any]]:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        by_day: dict[date, dict[str, float]] = defaultdict(
            lambda: {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sodium": 0.0}
        )
        for r in self._records:
            if r["user_id"] != user_id:
                continue
            if start_date <= r["meal_date"] <= today:
                d = by_day[r["meal_date"]]
                d["calories"] += r["calories"]
                d["carbs"] += r["carbs"]
                d["protein"] += r["protein"]
                d["fat"] += r["fat"]
                d["sodium"] += r["sodium"]

        result = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            row = by_day.get(d)
            result.append({
                "date": d.isoformat(),
                "calories": row["calories"] if row else 0,
                "carbs": row["carbs"] if row else 0,
                "protein": row["protein"] if row else 0,
                "fat": row["fat"] if row else 0,
                "sodium": row["sodium"] if row else 0,
                "has_record": row is not None,
            })
        return result


# =============================================================================
# NutritionDiagnostic
# =============================================================================
class NutritionDiagnostic:
    """
    주간 섭취 데이터 → 종합 영양 진단.
    """

    @classmethod
    def diagnose_weekly(
        cls, weekly_summary: dict[str, Any]
    ) -> dict[str, Any]:
        weekly_avg = weekly_summary.get("weekly_avg") or {}
        recorded_days = weekly_summary.get("recorded_days", 0)

        if recorded_days == 0:
            return {
                "overall_status": "데이터부족",
                "overall_score": 0,
                "nutrient_status": {},
                "macro_balance": {},
                "recommendations": ["이번 주 식사 기록이 없습니다. 먼저 기록해주세요."],
                "data_warning": "기록 없음",
                "diagnosed_at": datetime.utcnow().isoformat(),
            }

        # 영양소별 상태
        nutrient_status: dict[str, dict[str, Any]] = {}
        for key in ("calories", "carbs", "protein", "fat"):
            avg = weekly_avg.get(key, 0)
            status = judge_nutrient(key, avg)
            target = LUNCH_STANDARDS[key]["target"]
            nutrient_status[key] = {
                "status": status.value,
                "avg": round(avg, 1),
                "target": target,
                "deviation_pct": round(deviation_pct(key, avg), 1),
            }

        # 나트륨 · 당류 (max 기준)
        for key in ("sodium", "sugar"):
            avg = weekly_avg.get(key, 0)
            status = judge_nutrient(key, avg)
            standard = LUNCH_STANDARDS[key]
            nutrient_status[key] = {
                "status": status.value,
                "avg": round(avg, 1),
                "max": standard["max"],
                "deviation_pct": round(deviation_pct(key, avg), 1),
            }

        # 탄단지 비율 균형 체크
        macro_ratio = weekly_summary.get("macro_ratio", {})
        ideal = {k: v * 100 for k, v in IDEAL_MACRO_RATIO.items()}
        current = {
            "carbs": macro_ratio.get("carbs_pct", 0),
            "protein": macro_ratio.get("protein_pct", 0),
            "fat": macro_ratio.get("fat_pct", 0),
        }
        # protein_pct 이 15~20 범위 밖이면 불균형
        protein_pct = current["protein"]
        is_balanced = 15 <= protein_pct <= 25

        verdict = ""
        if protein_pct < 15:
            verdict = "단백질 비율이 권장 범위(15~20%)보다 낮습니다"
        elif protein_pct > 25:
            verdict = "단백질 비율이 권장 범위보다 높습니다"
        elif current["fat"] > 35:
            verdict = "지방 비율이 권장 범위(15~30%)를 초과합니다"
            is_balanced = False
        elif current["carbs"] > 68:
            verdict = "탄수화물 비율이 높습니다"
            is_balanced = False
        else:
            verdict = "탄단지 비율이 양호합니다"

        macro_balance = {
            "status": "양호" if is_balanced else "불균형",
            "current_ratio": current,
            "ideal_ratio": ideal,
            "verdict": verdict,
        }

        # 종합 점수
        overall_score = cls._calculate_overall_score(nutrient_status)

        # 종합 상태
        if overall_score >= 85:
            overall_status = "양호"
        elif overall_score >= 65:
            overall_status = "주의"
        else:
            overall_status = "경고"

        # 추천 메시지
        recommendations = cls._generate_recommendations(nutrient_status, macro_balance)

        result = {
            "overall_status": overall_status,
            "overall_score": overall_score,
            "nutrient_status": nutrient_status,
            "macro_balance": macro_balance,
            "recommendations": recommendations,
            "diagnosed_at": datetime.utcnow().isoformat(),
        }

        if recorded_days < 3:
            result["data_warning"] = (
                f"기록 일수가 {recorded_days}일로 부족합니다. 진단 정확도가 낮을 수 있습니다"
            )

        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def _calculate_overall_score(
        nutrient_status: dict[str, dict[str, Any]],
    ) -> int:
        score = 100
        for key, info in nutrient_status.items():
            status = info.get("status")
            if status == NutritionStatus.ADEQUATE.value:
                continue
            if status == NutritionStatus.DEFICIENT.value:
                score -= 12 if key == "protein" else 10
            elif status == NutritionStatus.EXCESSIVE.value:
                if key == "sodium":
                    score -= 15
                elif key == "sugar":
                    score -= 12
                else:
                    score -= 10
        return max(0, min(100, score))

    @staticmethod
    def _generate_recommendations(
        nutrient_status: dict[str, dict[str, Any]],
        macro_balance: dict[str, Any],
    ) -> list[str]:
        """우선순위: 단백질 부족 > 나트륨 과다 > 탄수 과다 > 지방 과다 > 칼로리"""
        recs: list[str] = []

        if nutrient_status.get("protein", {}).get("status") == NutritionStatus.DEFICIENT.value:
            recs.append("단백질 섭취를 늘려보세요 (고기, 생선, 두부, 계란 등)")

        if nutrient_status.get("sodium", {}).get("status") == NutritionStatus.EXCESSIVE.value:
            recs.append("나트륨 섭취가 많습니다. 국물을 남기는 습관을 추천합니다")

        if nutrient_status.get("carbs", {}).get("status") == NutritionStatus.EXCESSIVE.value:
            recs.append("탄수화물 비중이 높습니다. 밥 양을 조금 줄여보세요")

        if nutrient_status.get("fat", {}).get("status") == NutritionStatus.EXCESSIVE.value:
            recs.append("지방 섭취가 많습니다. 튀김류를 줄이고 구이·찜을 선택해보세요")

        if nutrient_status.get("calories", {}).get("status") == NutritionStatus.DEFICIENT.value:
            recs.append("칼로리가 부족합니다. 균형 잡힌 한 끼를 놓치지 마세요")
        elif nutrient_status.get("calories", {}).get("status") == NutritionStatus.EXCESSIVE.value:
            recs.append("칼로리 섭취가 많습니다. 포션 사이즈를 조절해보세요")

        if nutrient_status.get("sugar", {}).get("status") == NutritionStatus.EXCESSIVE.value:
            recs.append("당류 섭취가 많습니다. 디저트·음료를 줄여보세요")

        # 매크로 불균형
        if macro_balance.get("status") == "불균형" and macro_balance.get("verdict"):
            recs.append(macro_balance["verdict"])

        if not recs:
            recs.append("훌륭한 영양 균형을 유지하고 있어요! 이대로 계속해주세요 💪")

        return recs[:5]

    @staticmethod
    def compare_with_previous(
        current: dict[str, Any],
        previous: dict[str, Any],
    ) -> dict[str, Any]:
        if not previous or previous.get("overall_status") == "데이터부족":
            return {
                "score_change": None,
                "improved": [],
                "worsened": [],
                "unchanged": [],
                "note": "지난 주 데이터 없음",
            }

        score_change = (current.get("overall_score", 0)
                        - previous.get("overall_score", 0))

        improved, worsened, unchanged = [], [], []
        current_ns = current.get("nutrient_status", {})
        previous_ns = previous.get("nutrient_status", {})
        for key in ("calories", "protein", "carbs", "fat", "sodium", "sugar"):
            cur = current_ns.get(key, {}).get("status")
            prev = previous_ns.get(key, {}).get("status")
            if cur is None or prev is None:
                continue
            if cur == prev:
                unchanged.append(key)
            elif cur == NutritionStatus.ADEQUATE.value:
                improved.append(key)
            elif prev == NutritionStatus.ADEQUATE.value:
                worsened.append(key)
            else:
                unchanged.append(key)

        return {
            "score_change": score_change,
            "improved": improved,
            "worsened": worsened,
            "unchanged": unchanged,
        }


# =============================================================================
# NutritionRecommendScorer
# =============================================================================
class NutritionRecommendScorer:
    """
    주간 이력 × 음식점 영양 정보 → 0~100 추천 점수.
    """

    BASE_SCORE: int = 60

    @classmethod
    def calculate_nutrition_score(
        cls,
        restaurant_nutrition: dict[str, Any],
        weekly_summary: dict[str, Any],
    ) -> int:
        score = cls.BASE_SCORE
        r = restaurant_nutrition or {}
        avg = (weekly_summary or {}).get("weekly_avg") or {}

        r_protein = float(r.get("protein") or 0)
        r_fat = float(r.get("fat") or 0)
        r_carbs = float(r.get("carbs") or 0)
        r_sodium = float(r.get("sodium") or 0)
        r_cal = float(r.get("calories") or 0)

        avg_protein = float(avg.get("protein") or 0)
        avg_fat = float(avg.get("fat") or 0)
        avg_carbs = float(avg.get("carbs") or 0)
        avg_sodium = float(avg.get("sodium") or 0)
        avg_cal = float(avg.get("calories") or 0)

        # 단백질 보충
        if avg_protein and avg_protein < 20 and r_protein > 25:
            score += 25
        elif avg_protein and avg_protein < 25 and r_protein > 30:
            score += 20

        # 칼로리 부족 보충
        if avg_cal and avg_cal < 500 and 500 <= r_cal <= 800:
            score += 10

        # 지방 억제
        if avg_fat > 30 and r_fat > 35:
            score -= 15

        # 나트륨 억제
        if avg_sodium > 1000 and r_sodium > 1200:
            score -= 15

        # 탄수 억제
        if avg_carbs > 100 and r_carbs > 90:
            score -= 10

        # 탄단지 비율 보너스 (음식점 단품)
        total_macro_kcal = (r_carbs * 4) + (r_protein * 4) + (r_fat * 9)
        if total_macro_kcal > 0:
            carbs_pct = r_carbs * 4 / total_macro_kcal
            protein_pct = r_protein * 4 / total_macro_kcal
            if (
                0.5 <= carbs_pct <= 0.65
                and 0.15 <= protein_pct <= 0.25
            ):
                score += 10

        # 적정 칼로리 보너스
        if 500 <= r_cal <= 800:
            score += 5

        return max(0, min(100, int(round(score))))

    @classmethod
    def rank_by_nutrition(
        cls,
        restaurants_with_nutrition: list[dict[str, Any]],
        weekly_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []
        for r in restaurants_with_nutrition:
            new_r = dict(r)
            new_r["nutrition_score"] = cls.calculate_nutrition_score(
                r.get("nutrition", r), weekly_summary
            )
            scored.append(new_r)
        scored.sort(key=lambda x: x["nutrition_score"], reverse=True)
        return scored

    @classmethod
    def get_nutrition_advice_for_restaurant(
        cls,
        restaurant_nutrition: dict[str, Any],
        weekly_summary: dict[str, Any],
    ) -> str:
        avg = (weekly_summary or {}).get("weekly_avg") or {}
        r = restaurant_nutrition or {}

        r_protein = float(r.get("protein") or 0)
        r_sodium = float(r.get("sodium") or 0)
        r_fat = float(r.get("fat") or 0)

        avg_protein = float(avg.get("protein") or 0)
        avg_sodium = float(avg.get("sodium") or 0)
        avg_fat = float(avg.get("fat") or 0)

        if avg_protein and avg_protein < 25 and r_protein > 25:
            return "이번 주 단백질이 부족했는데, 이 메뉴는 단백질이 풍부해서 좋은 선택이에요!"
        if avg_sodium > 1000 and r_sodium > 1200:
            return "이번 주 나트륨 섭취가 많았어요. 국물은 남기는 걸 추천합니다."
        if avg_fat > 30 and r_fat < 20:
            return "이번 주 지방 섭취가 많았는데, 이 메뉴는 저지방이라 균형에 좋아요."
        return "오늘의 한 끼로 괜찮은 선택입니다."
