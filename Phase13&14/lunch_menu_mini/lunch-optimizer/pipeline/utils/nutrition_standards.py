"""
영양 기준값 상수 및 판정 함수.

출처: 한국인 영양소 섭취기준 + 식약처 권장량 (점심 1끼 기준, 일일 권장량의 약 35%).
"""
from __future__ import annotations

from enum import Enum
from typing import Final

# =============================================================================
# 점심 1끼 기준 권장량
# =============================================================================
LUNCH_STANDARDS: Final[dict[str, dict[str, float | int | str]]] = {
    "calories": {"min": 500, "max": 800, "target": 650, "unit": "kcal"},
    "carbs":    {"min": 65,  "max": 110, "target": 85,  "unit": "g"},
    "protein":  {"min": 20,  "max": 40,  "target": 28,  "unit": "g"},
    "fat":      {"min": 10,  "max": 25,  "target": 18,  "unit": "g"},
    "sodium":   {"max": 800, "target": 600, "unit": "mg"},
    "sugar":    {"max": 18,  "target": 12,  "unit": "g"},
}

# 탄단지 이상적 비율 (총 칼로리 대비 %)
IDEAL_MACRO_RATIO: Final[dict[str, float]] = {
    "carbs": 0.55,    # 55~65%
    "protein": 0.20,  # 15~20%
    "fat": 0.25,      # 15~30%
}

# 매크로 영양소 에너지 (kcal/g)
MACRO_KCAL_PER_G: Final[dict[str, float]] = {
    "carbs": 4.0,
    "protein": 4.0,
    "fat": 9.0,
}

# 판정 임계치 (target 대비)
DEFICIENT_THRESHOLD: Final[float] = 0.80   # 80% 미만 → 부족
EXCESSIVE_THRESHOLD: Final[float] = 1.20   # 120% 초과 → 과다


# =============================================================================
# 영양 상태 판정
# =============================================================================
class NutritionStatus(str, Enum):
    DEFICIENT = "부족"
    ADEQUATE = "적정"
    EXCESSIVE = "과다"


def judge_nutrient(nutrient: str, value: float) -> NutritionStatus:
    """
    영양소 값을 기준값과 비교하여 부족/적정/과다 판정.

    Args:
        nutrient: "calories", "carbs", "protein", "fat", "sodium", "sugar"
        value: 실제 섭취량

    Returns:
        NutritionStatus enum
    """
    standard = LUNCH_STANDARDS.get(nutrient)
    if standard is None:
        return NutritionStatus.ADEQUATE

    # 상한만 있는 영양소 (나트륨, 당류)
    if nutrient in ("sodium", "sugar"):
        max_val = float(standard["max"])
        if value > max_val * EXCESSIVE_THRESHOLD:
            return NutritionStatus.EXCESSIVE
        return NutritionStatus.ADEQUATE

    # 정상 영양소 (target 기준)
    target = float(standard["target"])
    if value < target * DEFICIENT_THRESHOLD:
        return NutritionStatus.DEFICIENT
    if value > target * EXCESSIVE_THRESHOLD:
        return NutritionStatus.EXCESSIVE
    return NutritionStatus.ADEQUATE


def deviation_pct(nutrient: str, value: float) -> float:
    """
    기준값 대비 편차 (%).

    양수: 초과, 음수: 부족.
    sodium/sugar 는 max 기준, 나머지는 target 기준.
    """
    standard = LUNCH_STANDARDS.get(nutrient)
    if standard is None:
        return 0.0
    baseline_val = standard.get("target") or standard.get("max") or 1
    baseline = float(baseline_val)  # type: ignore[arg-type]
    if baseline == 0:
        return 0.0
    return (value - baseline) / baseline * 100


# =============================================================================
# 카테고리별 fallback 영양값 (실제 API 매칭 실패 시)
# =============================================================================
CATEGORY_AVG_NUTRITION: Final[dict[str, dict[str, float]]] = {
    # 한식
    "한식_밥류":   {"calories": 650, "carbs": 90, "protein": 25, "fat": 18, "sodium": 900, "sugar": 8},
    "한식_국물":   {"calories": 480, "carbs": 55, "protein": 20, "fat": 12, "sodium": 1200, "sugar": 6},
    "한식_면류":   {"calories": 580, "carbs": 95, "protein": 18, "fat": 14, "sodium": 1500, "sugar": 5},
    "한식_기본":   {"calories": 600, "carbs": 80, "protein": 22, "fat": 16, "sodium": 1000, "sugar": 7},
    # 일식
    "일식_초밥":   {"calories": 520, "carbs": 68, "protein": 28, "fat": 14, "sodium": 900, "sugar": 8},
    "일식_면류":   {"calories": 560, "carbs": 80, "protein": 20, "fat": 18, "sodium": 1400, "sugar": 5},
    "일식_기본":   {"calories": 550, "carbs": 70, "protein": 25, "fat": 16, "sodium": 1100, "sugar": 6},
    # 양식
    "양식_파스타": {"calories": 680, "carbs": 85, "protein": 22, "fat": 28, "sodium": 900, "sugar": 10},
    "양식_버거":   {"calories": 780, "carbs": 62, "protein": 35, "fat": 42, "sodium": 1100, "sugar": 12},
    "양식_기본":   {"calories": 700, "carbs": 75, "protein": 28, "fat": 32, "sodium": 1000, "sugar": 10},
    # 기타
    "중식":        {"calories": 720, "carbs": 88, "protein": 24, "fat": 30, "sodium": 1400, "sugar": 10},
    "동남아":      {"calories": 520, "carbs": 65, "protein": 22, "fat": 16, "sodium": 1000, "sugar": 8},
    "샐러드":      {"calories": 380, "carbs": 35, "protein": 22, "fat": 18, "sodium": 600,  "sugar": 8},
    "카페":        {"calories": 420, "carbs": 50, "protein": 12, "fat": 18, "sodium": 500,  "sugar": 12},
    "분식":        {"calories": 580, "carbs": 80, "protein": 15, "fat": 18, "sodium": 1100, "sugar": 10},
    "기타":        {"calories": 600, "carbs": 75, "protein": 22, "fat": 22, "sodium": 1000, "sugar": 8},
}


def lookup_category_avg(category: str | None, menu_type: str | None = None) -> dict[str, float]:
    """
    카테고리·메뉴 타입을 기반으로 fallback 영양값을 반환.
    """
    category = (category or "").strip()
    menu_type = (menu_type or "").strip()

    # 한식 세분화
    if category == "한식":
        if menu_type in ("국물", "죽", "탕"):
            return dict(CATEGORY_AVG_NUTRITION["한식_국물"])
        if menu_type == "면류":
            return dict(CATEGORY_AVG_NUTRITION["한식_면류"])
        return dict(CATEGORY_AVG_NUTRITION["한식_밥류"])

    # 일식
    if category == "일식":
        if menu_type == "초밥":
            return dict(CATEGORY_AVG_NUTRITION["일식_초밥"])
        if menu_type == "면류":
            return dict(CATEGORY_AVG_NUTRITION["일식_면류"])
        return dict(CATEGORY_AVG_NUTRITION["일식_기본"])

    # 양식
    if category == "양식":
        if menu_type == "면류":
            return dict(CATEGORY_AVG_NUTRITION["양식_파스타"])
        if menu_type == "버거":
            return dict(CATEGORY_AVG_NUTRITION["양식_버거"])
        return dict(CATEGORY_AVG_NUTRITION["양식_기본"])

    direct = CATEGORY_AVG_NUTRITION.get(category)
    if direct:
        return dict(direct)

    return dict(CATEGORY_AVG_NUTRITION["기타"])
