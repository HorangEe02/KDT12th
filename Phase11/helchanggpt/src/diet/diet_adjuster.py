"""
diet_adjuster.py
일정 변동, 끼니 교체, 못 먹은 끼니 보정 등 식단 동적 조정 기능.

기능:
  1. 일정 변동 감지 + 식단 재조정 (야근, 회식, 아침 건너뜀 등)
  2. 개별 끼니 교체 (동일 칼로리/탄단지 범위 대체 메뉴)
  3. 못 먹은 끼니 칼로리 재배분
  4. 회식/외식 칼로리 추정 + 나머지 끼니 조정
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime

from .eating_out_db import estimate_eating_out_calories, EATING_OUT_DB


@dataclass
class ScheduleChange:
    """감지된 일정 변동"""
    change_type: str          # "late_dinner" | "skip_meal" | "eating_out" | "no_workout" | "swap_meal" | "ate_extra"
    details: dict = field(default_factory=dict)
    original_text: str = ""


@dataclass
class AdjustmentResult:
    """식단 조정 결과"""
    adjusted_plan: dict               # 조정된 식단
    changes_made: list[str]           # 변경 사항 설명
    calorie_rebalance: dict = field(default_factory=dict)   # 재배분 내역
    warnings: list[str] = field(default_factory=list)


# ═══════════════════════════════════════
# 일정 변동 감지 (자연어 → 구조화)
# ═══════════════════════════════════════

CHANGE_PATTERNS = {
    "late_dinner": {
        "keywords": ["야근", "늦게 먹", "저녁 늦", "밤에 먹", "야식"],
        "time_pattern": r"(\d{1,2})시|(\d{1,2}:\d{2})",
    },
    "skip_meal": {
        "keywords": ["못 먹", "건너뛰", "안 먹", "굶", "빼먹", "시간 없"],
        "meal_pattern": r"(아침|점심|저녁|간식)",
    },
    "eating_out": {
        "keywords": ["회식", "외식", "밖에서", "식당", "약속", "모임", "회식자리"],
        "meal_pattern": r"(아침|점심|저녁)",
    },
    "no_workout": {
        "keywords": ["운동 안", "운동 못", "쉬는 날", "운동 쉬", "헬스 안"],
    },
    "swap_meal": {
        "keywords": ["바꿔", "다른 거", "대체", "변경", "교체", "마음에 안"],
        "meal_pattern": r"(아침|점심|저녁|간식)",
    },
    "ate_extra": {
        "keywords": ["치킨 먹", "피자 먹", "라면 먹", "과식", "폭식", "많이 먹"],
    },
}

MEAL_KEY_MAP = {"아침": "breakfast", "점심": "lunch", "저녁": "dinner", "간식": "snack"}


def detect_schedule_change(text: str) -> ScheduleChange | None:
    """
    사용자 자연어 입력에서 일정 변동을 감지합니다.

    Args:
        text: 사용자 입력 (예: "오늘 야근이라 저녁 10시에 먹어야 해요")

    Returns:
        ScheduleChange 또는 None
    """
    text_lower = text.lower()

    for change_type, config in CHANGE_PATTERNS.items():
        if any(kw in text_lower for kw in config["keywords"]):
            details = {}

            # 시간 추출
            time_pattern = config.get("time_pattern")
            if time_pattern:
                match = re.search(time_pattern, text)
                if match:
                    groups = match.groups()
                    hour = next((g for g in groups if g), None)
                    if hour and ":" not in hour:
                        details["time"] = f"{int(hour):02d}:00"
                    elif hour:
                        details["time"] = hour

            # 끼니 추출
            meal_pattern = config.get("meal_pattern")
            if meal_pattern:
                match = re.search(meal_pattern, text)
                if match:
                    meal_kr = match.group(1)
                    details["meal"] = MEAL_KEY_MAP.get(meal_kr, meal_kr)
                    details["meal_kr"] = meal_kr

            # 음식명 추출 (ate_extra)
            if change_type == "ate_extra":
                for food in ["치킨", "피자", "라면", "햄버거", "떡볶이", "족발", "삼겹살"]:
                    if food in text:
                        details["food"] = food
                        break

            return ScheduleChange(
                change_type=change_type,
                details=details,
                original_text=text,
            )

    return None


# ═══════════════════════════════════════
# 식단 조정 엔진
# ═══════════════════════════════════════

def adjust_diet_plan(
    meal_plan: dict,
    change: ScheduleChange,
    total_kcal: int = 1800,
    model: str = "exaone3.5",
    use_llm: bool = False,
) -> AdjustmentResult:
    """
    일정 변동에 따라 식단을 조정합니다.

    Args:
        meal_plan: 원본 식단 JSON
        change: 감지된 일정 변동
        total_kcal: 일일 목표 칼로리
        model: LLM 모델 (use_llm=True 시)
        use_llm: LLM으로 재생성 여부

    Returns:
        AdjustmentResult
    """
    handlers = {
        "late_dinner": _handle_late_dinner,
        "skip_meal": _handle_skip_meal,
        "eating_out": _handle_eating_out,
        "no_workout": _handle_no_workout,
        "swap_meal": _handle_swap_meal,
        "ate_extra": _handle_ate_extra,
    }

    handler = handlers.get(change.change_type)
    if not handler:
        return AdjustmentResult(
            adjusted_plan=meal_plan,
            changes_made=["인식할 수 없는 변동 유형"],
        )

    return handler(meal_plan, change, total_kcal)


def _handle_late_dinner(
    plan: dict, change: ScheduleChange, total_kcal: int
) -> AdjustmentResult:
    """야근/늦은 저녁 대응."""
    meals = plan.get("meals", {})
    changes = []
    rebalance = {}

    dinner = meals.get("dinner", {})
    dinner_cal = dinner.get("subtotal", {}).get("calories_kcal", 0)

    # 저녁 칼로리 30% 감소
    reduced_cal = round(dinner_cal * 0.7)
    surplus = dinner_cal - reduced_cal

    # 저녁 → 소화 부담 적은 메뉴로 교체 제안
    dinner["_adjustment"] = {
        "reason": "야근으로 인한 늦은 저녁",
        "original_calories": dinner_cal,
        "adjusted_calories": reduced_cal,
        "recommendation": "소화 부담 적은 샐러드, 수프, 두부 요리 권장",
        "alternatives": [
            {"menu_name": "가벼운 닭가슴살 샐러드", "calories_kcal": reduced_cal},
            {"menu_name": "된장국 + 두부", "calories_kcal": reduced_cal},
            {"menu_name": "연어 포케볼 (밥 적게)", "calories_kcal": reduced_cal},
        ],
    }

    if change.details.get("time"):
        dinner["_adjustment"]["adjusted_time"] = change.details["time"]

    changes.append(f"저녁 칼로리 {dinner_cal}→{reduced_cal}kcal로 감소 (야근 대응)")

    # 점심에 칼로리 재배분
    lunch = meals.get("lunch", {})
    lunch_cal = lunch.get("subtotal", {}).get("calories_kcal", 0)
    lunch["_adjustment"] = {
        "added_calories": surplus,
        "recommendation": f"점심에 {surplus}kcal 추가 섭취 권장 (예: 반찬 추가, 밥 양 증가)",
    }
    changes.append(f"점심에 {surplus}kcal 추가 배분")

    rebalance = {"dinner": f"-{surplus}kcal", "lunch": f"+{surplus}kcal"}

    return AdjustmentResult(
        adjusted_plan=plan,
        changes_made=changes,
        calorie_rebalance=rebalance,
        warnings=["야근 시 취침 2시간 전까지 식사를 마치세요", "소화가 잘 되는 따뜻한 음식을 권장합니다"],
    )


def _handle_skip_meal(
    plan: dict, change: ScheduleChange, total_kcal: int
) -> AdjustmentResult:
    """못 먹은 끼니 보정."""
    meals = plan.get("meals", {})
    skipped_key = change.details.get("meal", "breakfast")
    skipped_kr = change.details.get("meal_kr", "아침")
    changes = []
    rebalance = {}

    skipped = meals.get(skipped_key, {})
    skipped_cal = skipped.get("subtotal", {}).get("calories_kcal", 0)

    if not skipped_cal:
        skipped_cal = round(total_kcal * 0.25)

    # 나머지 끼니에 재배분
    remaining_meals = [k for k in ["breakfast", "lunch", "dinner", "snack"]
                       if k != skipped_key and k in meals]
    per_meal_add = round(skipped_cal / max(len(remaining_meals), 1))

    for meal_key in remaining_meals:
        meal = meals.get(meal_key, {})
        meal["_adjustment"] = {
            "added_calories": per_meal_add,
            "reason": f"{skipped_kr} 건너뜀 → 칼로리 재배분",
            "recommendation": f"이 끼니에 {per_meal_add}kcal 추가 (단백질 위주 추가 권장)",
        }
        rebalance[meal_key] = f"+{per_meal_add}kcal"

    skipped["_adjustment"] = {"skipped": True, "calories_redistributed": skipped_cal}
    rebalance[skipped_key] = f"-{skipped_cal}kcal (건너뜀)"

    changes.append(f"{skipped_kr} 건너뜀 ({skipped_cal}kcal)")
    changes.append(f"나머지 {len(remaining_meals)}끼에 각 {per_meal_add}kcal 추가")
    changes.append("단백질 보충을 위해 간식에 프로틴 쉐이크 추가 권장")

    return AdjustmentResult(
        adjusted_plan=plan,
        changes_made=changes,
        calorie_rebalance=rebalance,
        warnings=[f"아침을 건너뛰면 점심 과식 위험이 높아집니다", "최소 단백질 보충 간식을 섭취하세요"],
    )


def _handle_eating_out(
    plan: dict, change: ScheduleChange, total_kcal: int
) -> AdjustmentResult:
    """회식/외식 대응."""
    meals = plan.get("meals", {})
    eating_meal = change.details.get("meal", "dinner")
    eating_kr = change.details.get("meal_kr", "저녁")
    changes = []
    rebalance = {}

    # 외식 칼로리 추정
    est = estimate_eating_out_calories("회식_일반")
    estimated_cal = est.get("estimated_kcal", 800)

    # 원래 끼니 칼로리
    original_meal = meals.get(eating_meal, {})
    original_cal = original_meal.get("subtotal", {}).get("calories_kcal", 0)
    calorie_diff = estimated_cal - original_cal

    original_meal["_adjustment"] = {
        "eating_out": True,
        "estimated_calories": estimated_cal,
        "original_calories": original_cal,
        "calorie_excess": max(calorie_diff, 0),
        "eating_out_tips": est.get("tips", []),
        "recommendation": "회식 시 채소 반찬을 먼저 드시고, 술보다 물을 자주 드세요",
    }

    changes.append(f"{eating_kr} 회식/외식 예정 (추정 {estimated_cal}kcal, 원래 {original_cal}kcal)")

    # 다른 끼니 칼로리 감소
    if calorie_diff > 0:
        other_meals = [k for k in ["breakfast", "lunch", "dinner", "snack"]
                       if k != eating_meal and k in meals]
        per_meal_reduce = round(calorie_diff / max(len(other_meals), 1))

        for meal_key in other_meals:
            meal = meals.get(meal_key, {})
            meal["_adjustment"] = {
                "reduced_calories": per_meal_reduce,
                "reason": f"{eating_kr} 회식 대비 칼로리 절약",
            }
            rebalance[meal_key] = f"-{per_meal_reduce}kcal"

        rebalance[eating_meal] = f"+{calorie_diff}kcal (회식)"
        changes.append(f"나머지 끼니에서 총 {calorie_diff}kcal 절약")

    return AdjustmentResult(
        adjusted_plan=plan,
        changes_made=changes,
        calorie_rebalance=rebalance,
        warnings=[
            "회식 시 단백질 반찬 위주로 선택하세요",
            "음주 시 1잔당 약 100~150kcal 추가됩니다",
            "다음 날 아침 물을 충분히 마시고, 평소 식단으로 복귀하세요",
        ],
    )


def _handle_no_workout(
    plan: dict, change: ScheduleChange, total_kcal: int
) -> AdjustmentResult:
    """운동 안 하는 날 대응."""
    meals = plan.get("meals", {})
    changes = []

    # 운동 전후 간식 제거
    for key in ["pre_workout", "post_workout"]:
        if key in meals:
            removed_cal = meals[key].get("subtotal", {}).get("calories_kcal", 0)
            meals[key]["_adjustment"] = {"removed": True, "reason": "운동 없는 날"}
            changes.append(f"{key} 간식 제거 (-{removed_cal}kcal)")

    # 총 칼로리 200kcal 감소 권장
    changes.append("운동 없는 날: 총 칼로리 100~200kcal 줄이기 권장")
    changes.append("탄수화물 비율을 약간 줄이고 단백질 유지")

    return AdjustmentResult(
        adjusted_plan=plan,
        changes_made=changes,
        warnings=["운동 없는 날에도 단백질 섭취는 유지하세요 (근손실 방지)"],
    )


def _handle_swap_meal(
    plan: dict, change: ScheduleChange, total_kcal: int
) -> AdjustmentResult:
    """개별 끼니 교체."""
    meals = plan.get("meals", {})
    swap_key = change.details.get("meal", "lunch")
    swap_kr = change.details.get("meal_kr", "점심")

    original = meals.get(swap_key, {})
    original_cal = original.get("subtotal", {}).get("calories_kcal", 0)

    # 동일 칼로리 범위의 대체 메뉴 제안
    alternatives = _generate_alternatives(swap_key, original_cal)

    original["_adjustment"] = {
        "swap_requested": True,
        "original_menu": original.get("menu_name", ""),
        "original_calories": original_cal,
        "alternatives": alternatives,
        "instruction": "아래 대체 메뉴 중 선택하거나, LLM으로 새 메뉴를 생성할 수 있습니다",
    }

    return AdjustmentResult(
        adjusted_plan=plan,
        changes_made=[f"{swap_kr} 대체 메뉴 {len(alternatives)}개 제안"],
    )


def _handle_ate_extra(
    plan: dict, change: ScheduleChange, total_kcal: int
) -> AdjustmentResult:
    """과식/추가 음식 섭취 보정."""
    food = change.details.get("food", "간식")
    extra_calories = estimate_eating_out_calories(food).get("estimated_kcal", 500)

    changes = [f"'{food}' 추가 섭취 (추정 {extra_calories}kcal)"]
    changes.append("내일 식단에서 칼로리 보정을 권장합니다")

    return AdjustmentResult(
        adjusted_plan=plan,
        changes_made=changes,
        calorie_rebalance={"tomorrow_adjustment": f"-{round(extra_calories * 0.5)}kcal"},
        warnings=[
            "한 번의 과식으로 체중이 변하지는 않습니다. 자책하지 마세요!",
            f"내일 {round(extra_calories * 0.5)}kcal만 줄이면 충분히 보정됩니다",
            "물을 충분히 마시면 나트륨 배출에 도움이 됩니다",
        ],
    )


def _generate_alternatives(meal_key: str, target_cal: int) -> list[dict]:
    """칼로리 범위가 유사한 대체 메뉴를 생성합니다."""
    alt_menus = {
        "breakfast": [
            {"menu_name": "바나나 프로틴 스무디", "calories_kcal": 350, "description": "바나나 + 프로틴파우더 + 우유 + 오트밀"},
            {"menu_name": "두부 스크램블 + 통밀빵", "calories_kcal": 380, "description": "두부 150g + 계란 1개 + 통밀빵 1쪽"},
            {"menu_name": "그래놀라 요거트볼", "calories_kcal": 340, "description": "그릭요거트 + 그래놀라 + 과일"},
        ],
        "lunch": [
            {"menu_name": "참치 비빔밥", "calories_kcal": 480, "description": "참치캔 + 현미밥 + 채소"},
            {"menu_name": "소고기 미역국 정식", "calories_kcal": 450, "description": "소고기 미역국 + 잡곡밥 + 반찬"},
            {"menu_name": "두부 샐러드 + 고구마", "calories_kcal": 420, "description": "두부 + 채소 + 고구마 + 드레싱"},
        ],
        "dinner": [
            {"menu_name": "닭가슴살 채소볶음", "calories_kcal": 380, "description": "닭가슴살 + 파프리카 + 양파 볶음"},
            {"menu_name": "연어 포케볼", "calories_kcal": 450, "description": "연어 + 아보카도 + 현미밥(소량) + 채소"},
            {"menu_name": "두부 된장찌개 + 잡곡밥", "calories_kcal": 400, "description": "된장찌개 + 두부 + 잡곡밥 2/3공기"},
        ],
        "snack": [
            {"menu_name": "프로틴 쉐이크 + 사과", "calories_kcal": 250, "description": "프로틴파우더 + 우유 + 사과"},
            {"menu_name": "삶은 계란 2개 + 견과류", "calories_kcal": 260, "description": "계란 2개 + 아몬드 15g"},
            {"menu_name": "그릭요거트 + 블루베리", "calories_kcal": 200, "description": "그릭요거트 150g + 블루베리 50g"},
        ],
    }

    return alt_menus.get(meal_key, alt_menus["lunch"])


# ═══════════════════════════════════════
# LLM 기반 식단 재조정
# ═══════════════════════════════════════

def adjust_with_llm(
    meal_plan: dict,
    change_text: str,
    user_profile: dict,
    model: str = "exaone3.5",
) -> dict:
    """
    LLM을 사용하여 자연어 변동 사항을 반영한 식단을 재생성합니다.

    Args:
        meal_plan: 원본 식단
        change_text: 사용자 변동 사항 텍스트
        user_profile: 사용자 프로필
        model: Ollama 모델
    """
    from openai import OpenAI

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    prompt = f"""당신은 스포츠 영양학 전문가입니다.

아래 원본 식단에 사용자의 일정 변동을 반영하여 식단을 수정해주세요.

[원본 식단]
{json.dumps(meal_plan.get('meals', {}), ensure_ascii=False, indent=2)[:1500]}

[사용자 변동 사항]
"{change_text}"

[수정 규칙]
1. 변동 사항에 해당하는 끼니만 수정하세요.
2. 일일 총 칼로리가 크게 변하지 않도록 다른 끼니에서 보정하세요.
3. 수정된 끼니에 추천 섭취 시간을 포함하세요.
4. 각 음식의 칼로리, 탄단지를 정확히 계산하세요.

원본과 동일한 JSON 구조로 수정된 식단만 반환하세요."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=3000,
        )

        content = response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())

    except Exception as e:
        return {"error": str(e), "fallback": "규칙 기반 조정을 사용합니다"}
