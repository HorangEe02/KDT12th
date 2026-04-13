"""
diet_generator.py
LLM으로 맞춤 식단을 생성하고, 모델별·프롬프트별·파라미터별 결과를 비교합니다.

Ollama 로컬 모델(exaone3.5, qwen3.5 등)을 기본으로 사용합니다.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime

from .macro_calculator import MacroTargets, calculate_macro_targets
from .diet_prompts import build_diet_prompt


@dataclass
class DietGenerationResult:
    """LLM 식단 생성 결과"""
    meal_plan: dict
    model: str
    prompt_type: str          # "zero_shot" | "few_shot" | "cot"
    temperature: float
    latency_sec: float
    success: bool = True
    error: str = ""


def _extract_json(text: str) -> dict:
    """LLM 응답에서 JSON을 추출합니다."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{"):
                text = part
                break
    return json.loads(text.strip())


def generate_diet_plan(
    user_profile: dict,
    macro_targets: MacroTargets | None = None,
    model: str = "exaone3.5",
    prompt_type: str = "few_shot",
    temperature: float = 0.7,
    ollama_base_url: str = "http://localhost:11434/v1",
) -> DietGenerationResult:
    """
    LLM으로 식단을 생성합니다.

    Args:
        user_profile: Stage 1 UserProfile 딕셔너리
        macro_targets: 탄단지 목표 (None이면 자동 계산)
        model: Ollama 모델명 (exaone3.5, qwen3.5:9b 등)
        prompt_type: "zero_shot" | "few_shot" | "cot"
        temperature: 생성 temperature
        ollama_base_url: Ollama API URL

    Returns:
        DietGenerationResult
    """
    from openai import OpenAI

    # 탄단지 목표 자동 계산
    if macro_targets is None:
        calc = user_profile.get("calculated", {})
        nlp = user_profile.get("nlp_analysis", {})
        macro_targets = calculate_macro_targets(
            total_kcal=calc.get("recommended_intake_kcal", 2000),
            goal_type=nlp.get("goal_type", "체중관리"),
            constraints=nlp.get("constraints", []),
            weight_kg=user_profile.get("basic", {}).get("weight_kg"),
        )

    # 프롬프트 생성
    prompt = build_diet_prompt(prompt_type, user_profile, macro_targets)

    # LLM 호출
    client = OpenAI(base_url=ollama_base_url, api_key="ollama")
    start = time.time()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=3000,
        )

        latency = round(time.time() - start, 2)
        content = response.choices[0].message.content
        meal_plan = _extract_json(content)

        # 끼니별 소계 + 일일 총계 자동 계산
        meal_plan = _calculate_totals(meal_plan, macro_targets)

        return DietGenerationResult(
            meal_plan=meal_plan,
            model=model,
            prompt_type=prompt_type,
            temperature=temperature,
            latency_sec=latency,
        )

    except Exception as e:
        return DietGenerationResult(
            meal_plan={},
            model=model,
            prompt_type=prompt_type,
            temperature=temperature,
            latency_sec=round(time.time() - start, 2),
            success=False,
            error=str(e),
        )


def _calculate_totals(meal_plan: dict, macro: MacroTargets) -> dict:
    """끼니별 소계와 일일 총계를 계산합니다."""
    meals = meal_plan.get("meals", {})
    daily = {"calories_kcal": 0, "carb_g": 0, "protein_g": 0, "fat_g": 0}

    for meal_key, meal_data in meals.items():
        if not isinstance(meal_data, dict):
            continue

        foods = meal_data.get("foods", [])
        subtotal = {"calories_kcal": 0, "carb_g": 0, "protein_g": 0, "fat_g": 0}

        for food in foods:
            subtotal["calories_kcal"] += food.get("calories_kcal", 0)
            subtotal["carb_g"] += food.get("carb_g", 0)
            subtotal["protein_g"] += food.get("protein_g", 0)
            subtotal["fat_g"] += food.get("fat_g", 0)

        # 소수점 정리
        subtotal = {k: round(v, 1) for k, v in subtotal.items()}
        meal_data["subtotal"] = subtotal

        daily["calories_kcal"] += subtotal["calories_kcal"]
        daily["carb_g"] += subtotal["carb_g"]
        daily["protein_g"] += subtotal["protein_g"]
        daily["fat_g"] += subtotal["fat_g"]

    daily = {k: round(v, 1) for k, v in daily.items()}

    # 실제 비율 계산
    total_cal = daily["calories_kcal"] or 1
    daily["actual_macros"] = {
        "carb_ratio": round(daily["carb_g"] * 4 / total_cal * 100, 1),
        "protein_ratio": round(daily["protein_g"] * 4 / total_cal * 100, 1),
        "fat_ratio": round(daily["fat_g"] * 9 / total_cal * 100, 1),
    }

    meal_plan["daily_total"] = daily

    # 메타 정보 추가
    meal_plan["meta"] = {
        "target_kcal": macro.total_kcal,
        "target_macros": {
            "carb_ratio": macro.carb_ratio,
            "protein_ratio": macro.protein_ratio,
            "fat_ratio": macro.fat_ratio,
        },
        "calorie_diff": round(daily["calories_kcal"] - macro.total_kcal, 1),
        "generated_at": datetime.now().isoformat(),
    }

    return meal_plan


def generate_demo_meal_plan(
    target_kcal: int = 1800,
    goal_type: str = "체지방감소",
) -> dict:
    """LLM 없이 데모 식단을 생성합니다."""
    return {
        "meals": {
            "breakfast": {
                "menu_name": "고단백 오트밀볼",
                "foods": [
                    {"name": "오트밀", "amount": "40g", "calories_kcal": 150, "carb_g": 27, "protein_g": 5, "fat_g": 2.5},
                    {"name": "그릭요거트", "amount": "150g", "calories_kcal": 130, "carb_g": 6, "protein_g": 17, "fat_g": 4},
                    {"name": "블루베리", "amount": "50g", "calories_kcal": 29, "carb_g": 7, "protein_g": 0.4, "fat_g": 0.2},
                    {"name": "아몬드", "amount": "10g", "calories_kcal": 58, "carb_g": 2, "protein_g": 2, "fat_g": 5},
                ],
                "subtotal": {"calories_kcal": 367, "carb_g": 42, "protein_g": 24.4, "fat_g": 11.7},
                "tip": "운동 1~2시간 전 섭취 시 에너지 공급에 효과적입니다",
            },
            "lunch": {
                "menu_name": "닭가슴살 현미 도시락",
                "foods": [
                    {"name": "현미밥", "amount": "150g (2/3공기)", "calories_kcal": 235, "carb_g": 48, "protein_g": 5, "fat_g": 1.8},
                    {"name": "닭가슴살 구이", "amount": "150g", "calories_kcal": 165, "carb_g": 0, "protein_g": 35, "fat_g": 1.8},
                    {"name": "브로콜리", "amount": "100g", "calories_kcal": 35, "carb_g": 5.6, "protein_g": 3.7, "fat_g": 0.4},
                    {"name": "방울토마토", "amount": "80g", "calories_kcal": 14, "carb_g": 3, "protein_g": 0.7, "fat_g": 0.2},
                ],
                "subtotal": {"calories_kcal": 449, "carb_g": 56.6, "protein_g": 44.4, "fat_g": 4.2},
                "tip": "단백질 흡수를 위해 천천히 씹어 드세요",
            },
            "dinner": {
                "menu_name": "연어 샐러드 정식",
                "foods": [
                    {"name": "연어 구이", "amount": "120g", "calories_kcal": 218, "carb_g": 0, "protein_g": 30, "fat_g": 9.7},
                    {"name": "고구마", "amount": "100g", "calories_kcal": 126, "carb_g": 29, "protein_g": 1.3, "fat_g": 0.1},
                    {"name": "샐러드 채소", "amount": "100g", "calories_kcal": 15, "carb_g": 2.5, "protein_g": 1.2, "fat_g": 0.2},
                    {"name": "올리브오일 드레싱", "amount": "1큰술", "calories_kcal": 120, "carb_g": 0, "protein_g": 0, "fat_g": 14},
                ],
                "subtotal": {"calories_kcal": 479, "carb_g": 31.5, "protein_g": 32.5, "fat_g": 24},
                "tip": "저녁은 취침 3시간 전까지 마무리하세요",
            },
            "snack": {
                "menu_name": "프로틴 간식",
                "foods": [
                    {"name": "프로틴쉐이크", "amount": "1잔", "calories_kcal": 150, "carb_g": 8, "protein_g": 25, "fat_g": 2},
                    {"name": "바나나", "amount": "1개", "calories_kcal": 106, "carb_g": 27, "protein_g": 1.3, "fat_g": 0.4},
                ],
                "subtotal": {"calories_kcal": 256, "carb_g": 35, "protein_g": 26.3, "fat_g": 2.4},
                "tip": "운동 직후 30분 이내 섭취하면 근회복에 효과적입니다",
            },
        },
        "daily_total": {
            "calories_kcal": 1551,
            "carb_g": 165.1,
            "protein_g": 127.6,
            "fat_g": 42.3,
            "actual_macros": {"carb_ratio": 42.6, "protein_ratio": 32.9, "fat_ratio": 24.5},
        },
        "meta": {
            "target_kcal": target_kcal,
            "target_macros": {"carb_ratio": 40, "protein_ratio": 35, "fat_ratio": 25},
            "calorie_diff": 1551 - target_kcal,
            "model_used": "demo",
            "generated_at": datetime.now().isoformat(),
        },
    }


# ═══════════════════════════════════════
# 비교 실험 실행기
# ═══════════════════════════════════════

def run_comparison_experiment(
    user_profile: dict,
    macro_targets: MacroTargets | None = None,
    models: list[str] | None = None,
    prompt_types: list[str] | None = None,
    temperatures: list[float] | None = None,
) -> list[DietGenerationResult]:
    """
    모델·프롬프트·temperature 조합별 식단 생성 비교 실험을 수행합니다.

    기본 실험 매트릭스:
    - 모델: exaone3.5, qwen3.5:9b
    - 프롬프트: zero_shot, few_shot, cot
    - temperature: 0.3, 0.7, 1.0
    """
    if models is None:
        models = ["exaone3.5", "qwen3.5:9b"]
    if prompt_types is None:
        prompt_types = ["zero_shot", "few_shot", "cot"]
    if temperatures is None:
        temperatures = [0.3, 0.7, 1.0]

    results = []
    total = len(models) * len(prompt_types) * len(temperatures)
    count = 0

    for model in models:
        for prompt_type in prompt_types:
            for temp in temperatures:
                count += 1
                print(f"  [{count}/{total}] {model} / {prompt_type} / temp={temp} ...")

                result = generate_diet_plan(
                    user_profile=user_profile,
                    macro_targets=macro_targets,
                    model=model,
                    prompt_type=prompt_type,
                    temperature=temp,
                )

                status = "OK" if result.success else f"ERR: {result.error[:40]}"
                print(f"    → {status} ({result.latency_sec}s)")

                results.append(result)
                time.sleep(1)  # API 부하 방지

    return results
