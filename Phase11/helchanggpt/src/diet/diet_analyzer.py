"""
diet_analyzer.py
생성된 식단을 분석합니다.

1. 영양소 교차 검증 (목표 대비 오차 확인)
2. 제약사항 위반 체크 (당뇨→고GI, 고혈압→고나트륨)
3. 영양 키워드 추출
4. 식단 요약 생성
"""

from dataclasses import dataclass, field
from .macro_calculator import MacroTargets
from .nutrition_db import search_food, validate_food_nutrition, COMMON_FOODS_DB


@dataclass
class DietAnalysis:
    """식단 분석 결과"""
    # 영양소 검증
    calorie_diff: float = 0                       # 목표 대비 차이 (kcal)
    calorie_accuracy_pct: float = 0               # 칼로리 정확도 (%)
    macro_accuracy: dict = field(default_factory=dict)  # 탄단지 비율 오차

    # 제약사항 체크
    constraint_warnings: list[str] = field(default_factory=list)

    # 개별 음식 검증
    food_validations: list[dict] = field(default_factory=list)

    # 키워드 + 요약
    keywords: list[str] = field(default_factory=list)
    summary: str = ""

    # 종합 점수
    overall_score: int = 0  # 0~100
    grade: str = ""


# 제약사항별 위험 식품 키워드
CONSTRAINT_RISK_FOODS = {
    "당뇨": {
        "risk_keywords": ["흰쌀밥", "백미밥", "설탕", "꿀", "주스", "과일주스", "떡", "빵", "시럽"],
        "max_carb_per_meal_g": 50,
        "note": "1끼 탄수화물 50g 이하 권장",
    },
    "고혈압": {
        "risk_keywords": ["김치", "장아찌", "젓갈", "라면", "찌개", "국물", "가공육"],
        "max_sodium_mg": 2000,
        "note": "일일 나트륨 2000mg 이하 권장",
    },
    "고지혈증": {
        "risk_keywords": ["삼겹살", "곱창", "치즈", "버터", "튀김", "프라이"],
        "max_saturated_fat_g": 15,
        "note": "포화지방 15g 이하 권장",
    },
    "신장질환": {
        "risk_keywords": ["프로틴", "단백질보충제"],
        "max_protein_g_per_kg": 0.8,
        "note": "체중 1kg당 단백질 0.8g 이하 권장",
    },
}


def analyze_diet_plan(
    meal_plan: dict,
    macro_targets: MacroTargets,
    constraints: list[str] | None = None,
    weight_kg: float | None = None,
) -> DietAnalysis:
    """
    생성된 식단을 종합 분석합니다.

    Args:
        meal_plan: LLM이 생성한 식단 JSON
        macro_targets: 목표 탄단지
        constraints: 제약사항 리스트
        weight_kg: 체중 (단백질 검증용)
    """
    analysis = DietAnalysis()

    daily = meal_plan.get("daily_total", {})

    # 1. 칼로리 정확도
    actual_cal = daily.get("calories_kcal", 0)
    target_cal = macro_targets.total_kcal
    analysis.calorie_diff = round(actual_cal - target_cal, 1)
    analysis.calorie_accuracy_pct = round(
        (1 - abs(analysis.calorie_diff) / max(target_cal, 1)) * 100, 1
    )

    # 2. 탄단지 비율 오차
    actual_macros = daily.get("actual_macros", {})
    analysis.macro_accuracy = {
        "carb": {
            "target": macro_targets.carb_ratio,
            "actual": actual_macros.get("carb_ratio", 0),
            "diff": round(actual_macros.get("carb_ratio", 0) - macro_targets.carb_ratio, 1),
        },
        "protein": {
            "target": macro_targets.protein_ratio,
            "actual": actual_macros.get("protein_ratio", 0),
            "diff": round(actual_macros.get("protein_ratio", 0) - macro_targets.protein_ratio, 1),
        },
        "fat": {
            "target": macro_targets.fat_ratio,
            "actual": actual_macros.get("fat_ratio", 0),
            "diff": round(actual_macros.get("fat_ratio", 0) - macro_targets.fat_ratio, 1),
        },
    }

    # 3. 제약사항 위반 체크
    if constraints:
        _check_constraints(analysis, meal_plan, constraints, weight_kg)

    # 4. 개별 음식 영양소 검증
    _validate_individual_foods(analysis, meal_plan)

    # 5. 키워드 추출
    analysis.keywords = _extract_diet_keywords(meal_plan)

    # 6. 식단 요약
    analysis.summary = _generate_summary(meal_plan, analysis)

    # 7. 종합 점수
    _calculate_score(analysis)

    return analysis


def _check_constraints(
    analysis: DietAnalysis,
    meal_plan: dict,
    constraints: list[str],
    weight_kg: float | None,
):
    """제약사항 위반 여부를 체크합니다."""
    meals = meal_plan.get("meals", {})

    for constraint in constraints:
        config = CONSTRAINT_RISK_FOODS.get(constraint)
        if not config:
            continue

        # 위험 식품 체크
        for meal_key, meal_data in meals.items():
            if not isinstance(meal_data, dict):
                continue
            for food in meal_data.get("foods", []):
                food_name = food.get("name", "")
                for risk_kw in config.get("risk_keywords", []):
                    if risk_kw in food_name:
                        analysis.constraint_warnings.append(
                            f"[{constraint}] {meal_key}의 '{food_name}'은 주의가 필요합니다 ({config['note']})"
                        )

        # 당뇨: 1끼 탄수화물 체크
        if constraint == "당뇨":
            max_carb = config.get("max_carb_per_meal_g", 50)
            for meal_key, meal_data in meals.items():
                if not isinstance(meal_data, dict):
                    continue
                subtotal = meal_data.get("subtotal", {})
                carb = subtotal.get("carb_g", 0)
                if carb > max_carb:
                    analysis.constraint_warnings.append(
                        f"[당뇨] {meal_key} 탄수화물 {carb}g → {max_carb}g 이하 권장"
                    )

        # 고혈압: 일일 나트륨 체크
        if constraint == "고혈압":
            total_sodium = sum(
                food.get("sodium_mg", 0)
                for meal_data in meals.values()
                if isinstance(meal_data, dict)
                for food in meal_data.get("foods", [])
            )
            max_sodium = config.get("max_sodium_mg", 2000)
            if total_sodium > max_sodium:
                analysis.constraint_warnings.append(
                    f"[고혈압] 일일 나트륨 {total_sodium}mg → {max_sodium}mg 이하 권장"
                )

        # 신장질환: 체중 대비 단백질 체크
        if constraint == "신장질환" and weight_kg:
            daily = meal_plan.get("daily_total", {})
            total_protein = daily.get("protein_g", 0)
            max_protein = weight_kg * config.get("max_protein_g_per_kg", 0.8)
            if total_protein > max_protein:
                analysis.constraint_warnings.append(
                    f"[신장질환] 일일 단백질 {total_protein}g → {round(max_protein)}g 이하 권장"
                )


def _validate_individual_foods(analysis: DietAnalysis, meal_plan: dict):
    """개별 음식의 영양소를 DB와 교차 검증합니다."""
    meals = meal_plan.get("meals", {})
    for meal_key, meal_data in meals.items():
        if not isinstance(meal_data, dict):
            continue
        for food in meal_data.get("foods", []):
            name = food.get("name", "")
            kcal = food.get("calories_kcal", 0)
            result = validate_food_nutrition(name, kcal)
            analysis.food_validations.append({
                "meal": meal_key,
                "food": name,
                **result,
            })


def _extract_diet_keywords(meal_plan: dict) -> list[str]:
    """식단에서 핵심 키워드를 추출합니다."""
    keywords = set()
    meals = meal_plan.get("meals", {})

    for meal_data in meals.values():
        if not isinstance(meal_data, dict):
            continue
        for food in meal_data.get("foods", []):
            name = food.get("name", "")
            # 주요 식재료 추출
            for term in ["닭가슴살", "현미", "연어", "고구마", "오트밀", "두부", "계란",
                         "브로콜리", "시금치", "그릭요거트", "프로틴", "아몬드", "아보카도",
                         "통밀", "잡곡", "소고기", "참치", "바나나"]:
                if term in name:
                    keywords.add(term)

    # 영양 특성 키워드
    daily = meal_plan.get("daily_total", {})
    actual = daily.get("actual_macros", {})
    if actual.get("protein_ratio", 0) > 30:
        keywords.add("고단백")
    if actual.get("carb_ratio", 0) < 40:
        keywords.add("저탄수화물")
    if actual.get("fat_ratio", 0) < 25:
        keywords.add("저지방")

    return sorted(keywords)


def _generate_summary(meal_plan: dict, analysis: DietAnalysis) -> str:
    """식단 요약을 생성합니다."""
    daily = meal_plan.get("daily_total", {})
    cal = daily.get("calories_kcal", 0)
    carb = daily.get("carb_g", 0)
    protein = daily.get("protein_g", 0)
    fat = daily.get("fat_g", 0)

    meals = meal_plan.get("meals", {})
    meal_names = []
    for key in ["breakfast", "lunch", "dinner", "snack"]:
        data = meals.get(key, {})
        if isinstance(data, dict) and data.get("menu_name"):
            meal_names.append(data["menu_name"])

    summary = f"총 {cal}kcal (탄{carb}g·단{protein}g·지{fat}g). "
    if meal_names:
        summary += f"구성: {' / '.join(meal_names)}. "

    if analysis.constraint_warnings:
        summary += f"주의사항 {len(analysis.constraint_warnings)}건."
    else:
        summary += "제약사항 위반 없음."

    return summary


def _calculate_score(analysis: DietAnalysis):
    """식단 종합 점수를 산출합니다."""
    score = 100

    # 칼로리 오차 감점 (50kcal당 -5점)
    score -= min(abs(analysis.calorie_diff) / 50 * 5, 30)

    # 탄단지 비율 오차 감점 (5%당 -5점)
    for macro_info in analysis.macro_accuracy.values():
        diff = abs(macro_info.get("diff", 0))
        score -= min(diff / 5 * 5, 10)

    # 제약사항 위반 감점 (건당 -10점)
    score -= len(analysis.constraint_warnings) * 10

    # 검증 실패 음식 감점 (건당 -3점)
    unverified = sum(1 for v in analysis.food_validations if not v.get("verified", True))
    score -= unverified * 3

    score = max(round(score), 0)
    analysis.overall_score = score

    if score >= 90:
        analysis.grade = "A"
    elif score >= 75:
        analysis.grade = "B"
    elif score >= 60:
        analysis.grade = "C"
    else:
        analysis.grade = "D"
