"""
diet_prompts.py
식단 생성을 위한 LLM 프롬프트 템플릿.
Zero-shot, Few-shot, CoT(Chain-of-Thought) 3가지 방식을 비교합니다.
"""

# ═══════════════════════════════════════
# Zero-shot 프롬프트
# ═══════════════════════════════════════

ZERO_SHOT_PROMPT = """당신은 스포츠 영양학 전문가입니다.

아래 사용자 정보를 바탕으로 하루 식단을 생성해주세요.

[사용자 정보]
- 성별: {gender}, 나이: {age}세, 키: {height_cm}cm, 체중: {weight_kg}kg
- 체지방률: {body_fat_percent}%
- 운동 목표: {goal_type}
- 제약사항: {constraints}
- 목표 칼로리: {target_kcal}kcal
- 탄단지 비율: 탄수화물 {carb_ratio}% / 단백질 {protein_ratio}% / 지방 {fat_ratio}%
- 탄수화물 {carb_g}g / 단백질 {protein_g}g / 지방 {fat_g}g

[생성 규칙]
1. 아침, 점심, 저녁, 간식 총 4끼를 구성하세요.
2. 각 음식마다 정확한 양(g 또는 단위)과 칼로리, 탄단지(g)를 표기하세요.
3. 한국인이 쉽게 구할 수 있는 음식으로 구성하세요.
4. 제약사항이 있으면 반드시 반영하세요.
5. 각 끼니마다 식사 팁을 한 줄 포함하세요.

아래 JSON 형식으로만 응답하세요:
{{
  "meals": {{
    "breakfast": {{
      "menu_name": "<식단명>",
      "foods": [
        {{"name": "<음식명>", "amount": "<양>", "calories_kcal": <숫자>, "carb_g": <숫자>, "protein_g": <숫자>, "fat_g": <숫자>}}
      ],
      "tip": "<식사 팁>"
    }},
    "lunch": {{ ... }},
    "dinner": {{ ... }},
    "snack": {{ ... }}
  }}
}}"""


# ═══════════════════════════════════════
# Few-shot 프롬프트
# ═══════════════════════════════════════

FEW_SHOT_PROMPT = """당신은 스포츠 영양학 전문가입니다.
사용자 정보를 바탕으로 맞춤 하루 식단을 생성합니다.

[예시 1 - 체지방감소 목표, 남성, 1800kcal]
입력: 28세 남성, 180cm 85kg, 체지방률 25%, 목표: 체지방감소, 1800kcal, 탄40/단35/지25
출력:
{{
  "meals": {{
    "breakfast": {{
      "menu_name": "고단백 오트밀볼",
      "foods": [
        {{"name": "오트밀", "amount": "40g", "calories_kcal": 150, "carb_g": 27, "protein_g": 5, "fat_g": 2.5}},
        {{"name": "그릭요거트", "amount": "150g", "calories_kcal": 130, "carb_g": 6, "protein_g": 17, "fat_g": 4}},
        {{"name": "블루베리", "amount": "50g", "calories_kcal": 29, "carb_g": 7, "protein_g": 0.4, "fat_g": 0.2}},
        {{"name": "아몬드", "amount": "10g", "calories_kcal": 58, "carb_g": 2, "protein_g": 2, "fat_g": 5}}
      ],
      "tip": "운동 1~2시간 전 섭취 시 에너지 공급에 효과적입니다"
    }},
    "lunch": {{
      "menu_name": "닭가슴살 현미 도시락",
      "foods": [
        {{"name": "현미밥", "amount": "150g (2/3공기)", "calories_kcal": 220, "carb_g": 45, "protein_g": 5, "fat_g": 1.7}},
        {{"name": "닭가슴살 구이", "amount": "150g", "calories_kcal": 165, "carb_g": 0, "protein_g": 35, "fat_g": 1.8}},
        {{"name": "브로콜리", "amount": "100g", "calories_kcal": 35, "carb_g": 5.6, "protein_g": 3.7, "fat_g": 0.4}},
        {{"name": "방울토마토", "amount": "80g", "calories_kcal": 14, "carb_g": 3, "protein_g": 0.7, "fat_g": 0.2}}
      ],
      "tip": "단백질 흡수를 위해 천천히 씹어 드세요"
    }},
    "dinner": {{
      "menu_name": "연어 샐러드 정식",
      "foods": [
        {{"name": "연어 구이", "amount": "120g", "calories_kcal": 218, "carb_g": 0, "protein_g": 30, "fat_g": 9.7}},
        {{"name": "고구마", "amount": "100g", "calories_kcal": 126, "carb_g": 29, "protein_g": 1.3, "fat_g": 0.1}},
        {{"name": "샐러드 채소", "amount": "100g", "calories_kcal": 15, "carb_g": 2.5, "protein_g": 1.2, "fat_g": 0.2}},
        {{"name": "올리브오일 드레싱", "amount": "1큰술", "calories_kcal": 120, "carb_g": 0, "protein_g": 0, "fat_g": 14}}
      ],
      "tip": "저녁은 취침 3시간 전까지 마무리하세요"
    }},
    "snack": {{
      "menu_name": "프로틴 간식",
      "foods": [
        {{"name": "프로틴쉐이크", "amount": "1잔", "calories_kcal": 150, "carb_g": 8, "protein_g": 25, "fat_g": 2}},
        {{"name": "바나나", "amount": "1개", "calories_kcal": 106, "carb_g": 27, "protein_g": 1.3, "fat_g": 0.4}}
      ],
      "tip": "운동 직후 30분 이내 섭취하면 근회복에 효과적입니다"
    }}
  }}
}}

이제 아래 사용자 정보로 식단을 생성해주세요.

[사용자 정보]
- 성별: {gender}, 나이: {age}세, 키: {height_cm}cm, 체중: {weight_kg}kg
- 체지방률: {body_fat_percent}%
- 운동 목표: {goal_type}
- 제약사항: {constraints}
- 목표 칼로리: {target_kcal}kcal
- 탄단지 비율: 탄수화물 {carb_ratio}% / 단백질 {protein_ratio}% / 지방 {fat_ratio}%
- 탄수화물 {carb_g}g / 단백질 {protein_g}g / 지방 {fat_g}g

JSON 형식으로만 응답하세요."""


# ═══════════════════════════════════════
# Chain-of-Thought 프롬프트
# ═══════════════════════════════════════

COT_PROMPT = """당신은 스포츠 영양학 전문가입니다.
사용자 맞춤 식단을 단계별로 추론한 뒤 최종 식단을 생성합니다.

[사용자 정보]
- 성별: {gender}, 나이: {age}세, 키: {height_cm}cm, 체중: {weight_kg}kg
- 체지방률: {body_fat_percent}%
- 운동 목표: {goal_type}
- 제약사항: {constraints}
- 목표 칼로리: {target_kcal}kcal
- 목표 탄단지: 탄수화물 {carb_g}g / 단백질 {protein_g}g / 지방 {fat_g}g

아래 단계를 따라 추론한 뒤 최종 식단 JSON을 생성하세요.

Step 1) 사용자 상황 분석
- 핵심 니즈와 제약사항이 식단에 미치는 영향을 파악하세요.

Step 2) 끼니별 칼로리 배분
- 아침:점심:저녁:간식 = 25:35:30:10 비율로 배분하세요.

Step 3) 음식 선택 기준
- 제약사항을 고려한 피해야 할 식품과 권장 식품을 정하세요.

Step 4) 식단 구성 및 영양소 계산
- 각 끼니의 음식을 구체적으로 정하고, 정확한 영양소를 계산하세요.

Step 5) 검증
- 총 칼로리가 목표 ±50kcal 이내인지 확인하세요.
- 탄단지 비율이 목표와 ±5% 이내인지 확인하세요.

추론 과정을 먼저 보여준 뒤, 마지막에 ```json과 ``` 사이에 최종 식단 JSON을 넣어주세요.
JSON 구조:
{{
  "reasoning": "<추론 과정 요약>",
  "meals": {{
    "breakfast": {{ "menu_name": "...", "foods": [...], "tip": "..." }},
    "lunch": {{ ... }},
    "dinner": {{ ... }},
    "snack": {{ ... }}
  }}
}}"""


PROMPT_TEMPLATES = {
    "zero_shot": ZERO_SHOT_PROMPT,
    "few_shot": FEW_SHOT_PROMPT,
    "cot": COT_PROMPT,
}


# ═══════════════════════════════════════
# 시간대별 식단 확장 프롬프트 (스케줄 연동)
# ═══════════════════════════════════════

SCHEDULED_DIET_PROMPT = """당신은 스포츠 영양학 전문가입니다.
사용자의 일정과 운동 계획에 맞춰 시간대별 맞춤 식단을 생성합니다.

[사용자 정보]
- 성별: {gender}, 나이: {age}세, 키: {height_cm}cm, 체중: {weight_kg}kg
- 체지방률: {body_fat_percent}%
- 운동 목표: {goal_type}
- 제약사항: {constraints}
- 목표 칼로리: {target_kcal}kcal
- 탄단지: 탄수화물 {carb_g}g / 단백질 {protein_g}g / 지방 {fat_g}g

{schedule_context}

[생성 규칙]
1. 위 시간 배정에 맞춰 각 끼니를 구성하세요.
2. 각 음식의 양(g), 칼로리, 탄단지를 정확히 표기하세요.
3. 각 끼니에 recommended_time(HH:MM)과 timing_reason을 포함하세요.
4. 운동 전 간식은 빠른 탄수화물, 운동 후는 프로틴+탄수화물 중심으로 구성하세요.
5. 제약사항을 반드시 반영하세요.
6. 각 끼니에 대체 메뉴 2개를 alternatives 배열로 제안하세요.
7. 한국인 식습관에 맞는 현실적 음식으로 구성하세요.

아래 JSON 형식으로만 응답하세요:
{{
  "meals": {{
    "<meal_key>": {{
      "menu_name": "<식단명>",
      "recommended_time": "<HH:MM>",
      "timing_reason": "<시간 배정 이유>",
      "foods": [
        {{"name": "<음식명>", "amount": "<양>", "calories_kcal": <숫자>, "carb_g": <숫자>, "protein_g": <숫자>, "fat_g": <숫자>}}
      ],
      "tip": "<식사 팁>",
      "alternatives": ["<대체 메뉴1>", "<대체 메뉴2>"]
    }}
  }}
}}"""

PROMPT_TEMPLATES["scheduled"] = SCHEDULED_DIET_PROMPT


def build_diet_prompt(
    prompt_type: str,
    user_profile: dict,
    macro_targets,
    schedule_context: str = "",
) -> str:
    """프롬프트 템플릿에 사용자 정보를 채워 반환합니다."""
    template = PROMPT_TEMPLATES.get(prompt_type, FEW_SHOT_PROMPT)

    basic = user_profile.get("basic", {})
    nlp = user_profile.get("nlp_analysis", {})
    bc = user_profile.get("body_composition", {})

    kwargs = dict(
        gender=basic.get("gender", "미입력"),
        age=basic.get("age", "미입력"),
        height_cm=basic.get("height_cm", "미입력"),
        weight_kg=basic.get("weight_kg", "미입력"),
        body_fat_percent=bc.get("body_fat_percent") or nlp.get("body_fat_percent_from_text") or "미측정",
        goal_type=nlp.get("goal_type", "체중관리"),
        constraints=", ".join(nlp.get("constraints", [])) or "없음",
        target_kcal=macro_targets.total_kcal,
        carb_ratio=macro_targets.carb_ratio,
        protein_ratio=macro_targets.protein_ratio,
        fat_ratio=macro_targets.fat_ratio,
        carb_g=macro_targets.carb_g,
        protein_g=macro_targets.protein_g,
        fat_g=macro_targets.fat_g,
    )

    if prompt_type == "scheduled" and schedule_context:
        kwargs["schedule_context"] = schedule_context

    return template.format(**kwargs)
