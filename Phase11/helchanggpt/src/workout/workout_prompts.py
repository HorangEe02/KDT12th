"""
workout_prompts.py
운동 루틴 생성을 위한 LLM 프롬프트 템플릿.

모든 루틴에 면책 안내 문구를 포함합니다:
"이 운동 루틴은 AI가 추천하는 참고용 가이드이며, 개인의 체력 수준과 건강 상태에 따라
적합하지 않을 수 있습니다. 본인에게 맞게 운동 방법·강도·횟수를 조정하시고,
통증이나 불편함이 있으면 즉시 중단하고 전문가와 상담하세요."
"""

# ═══════════════════════════════════════
# 면책/안내 문구 (모든 응답에 포함)
# ═══════════════════════════════════════

DISCLAIMER = (
    "⚠️ 본 운동 루틴은 AI가 추천하는 참고용 가이드이며, 정답이 아닐 수 있습니다. "
    "개인의 체력 수준·건강 상태·부상 이력에 따라 적합하지 않을 수 있으므로, "
    "본인에게 맞게 운동 방법·강도·횟수를 자유롭게 수정하거나 변경하면서 진행해주세요. "
    "운동 중 통증이나 불편함이 있으면 즉시 중단하고 전문가(트레이너·의사)와 상담하시기 바랍니다."
)

DISCLAIMER_SHORT = (
    "⚠️ AI 추천 루틴은 참고용입니다. 본인 체력에 맞게 조정하세요. 통증 시 즉시 중단!"
)


# ═══════════════════════════════════════
# 분할 방식 결정 로직
# ═══════════════════════════════════════

SPLIT_RECOMMENDATIONS = {
    1: {"split": "전신", "description": "주 1회는 전신 운동으로 전체 근육군을 자극"},
    2: {"split": "상하분할", "description": "상체/하체 교대로 효율적 회복"},
    3: {"split": "전신", "description": "전신 운동 3회, 충분한 회복일 확보"},
    4: {"split": "상하분할", "description": "상체2회/하체2회 균형 잡힌 구성"},
    5: {"split": "PPL+상하", "description": "밀기/당기기/하체 + 상체/하체 조합"},
    6: {"split": "PPL", "description": "Push/Pull/Legs 2회 반복"},
    7: {"split": "부위별분할", "description": "매일 다른 부위 집중 (고급자용)"},
}


def get_recommended_split(frequency: int, experience: str) -> dict:
    """운동 빈도와 경험에 따라 추천 분할 방식을 결정합니다."""
    base = SPLIT_RECOMMENDATIONS.get(frequency, SPLIT_RECOMMENDATIONS[3])

    # 입문/초급은 전신 운동 권장
    if experience in ("입문", "초급") and frequency <= 4:
        return {"split": "전신", "description": f"입문/초급은 전신 운동이 효율적 (주 {frequency}회)"}

    return base


# ═══════════════════════════════════════
# 운동 루틴 생성 프롬프트
# ═══════════════════════════════════════

WORKOUT_PROMPT = """당신은 공인 피트니스 트레이너(NSCA-CPT)입니다.
사용자 정보와 목표에 맞는 주간 운동 루틴을 생성해주세요.

[사용자 정보]
- 성별: {gender}, 나이: {age}세, 키: {height_cm}cm, 체중: {weight_kg}kg
- 체지방률: {body_fat_percent}%
- 운동 목표: {goal_type}
- 경험 수준: {experience_level}
- 주당 운동 횟수: {frequency}회
- 제약사항/부상: {constraints}
- 추천 분할: {split_type} ({split_description})

[생성 규칙]
1. {frequency}일 운동 + 나머지 휴식일로 구성하세요.
2. 각 운동일에는 웜업(5~10분), 메인 운동(4~6종목), 쿨다운(5~10분)을 포함하세요.
3. 메인 운동마다 다음을 포함: 운동명, 목표 근육, 세트수, 반복수, 세트간 휴식(초), 강도(저/중/고), 수행방법, 대체운동 2개, 주의사항
4. 제약사항/부상이 있는 부위의 운동은 반드시 대체 운동으로 교체하거나 주의사항을 명시하세요.
5. {goal_type} 목표에 맞는 유산소/무산소 비율을 적용하세요.
6. 각 운동일에 예상 소요 시간(분)과 예상 소모 칼로리를 포함하세요.
7. 각 운동일에 오늘의 운동 팁을 포함하세요.
8. 한국 헬스장에서 흔히 볼 수 있는 장비 기준으로 구성하세요.

[중요 안내]
이 루틴은 참고용이며 정답이 아닙니다. 사용자에게 본인 체력에 맞게 자유롭게 조정하라는 안내를 반드시 포함하세요.

아래 JSON 형식으로만 응답하세요:
{{
  "weekly_plan": {{
    "day1": {{
      "day_label": "<요일>",
      "focus": "<오늘의 부위/테마>",
      "estimated_time_min": <숫자>,
      "estimated_calories": <숫자>,
      "warmup": {{
        "exercises": [
          {{"name": "<운동명>", "duration_min": <숫자>, "description": "<설명>"}}
        ]
      }},
      "main_workout": {{
        "exercises": [
          {{
            "name": "<운동명>",
            "target_muscle": "<근육군>",
            "sets": <숫자>,
            "reps": "<반복수>",
            "rest_sec": <숫자>,
            "intensity": "<저|중|고>",
            "description": "<수행 방법>",
            "alternatives": ["<대체1>", "<대체2>"],
            "caution": "<주의사항 또는 빈 문자열>"
          }}
        ]
      }},
      "cooldown": {{
        "exercises": [
          {{"name": "<운동명>", "duration_min": <숫자>, "description": "<설명>"}}
        ]
      }},
      "tip": "<오늘의 운동 팁>"
    }}
  }},
  "rest_days": ["<휴식 요일1>", "<휴식 요일2>", ...],
  "disclaimer": "<AI 추천 루틴 면책 안내 문구>"
}}"""


GOAL_CARDIO_RATIO = {
    "체지방감소": {"cardio_pct": 40, "strength_pct": 60, "note": "유산소 비중 높여 지방 연소 극대화"},
    "근력증가": {"cardio_pct": 15, "strength_pct": 85, "note": "근력 운동 위주, 유산소는 마무리용"},
    "체력향상": {"cardio_pct": 50, "strength_pct": 50, "note": "유산소와 근력 균형"},
    "체중관리": {"cardio_pct": 35, "strength_pct": 65, "note": "기초대사량 유지를 위한 근력 + 유산소"},
    "건강개선": {"cardio_pct": 45, "strength_pct": 55, "note": "심폐 기능 향상 + 관절 부담 적은 운동"},
}


def build_workout_prompt(
    user_profile: dict,
    frequency: int | None = None,
) -> str:
    """운동 루틴 생성 프롬프트를 구성합니다."""
    basic = user_profile.get("basic", {})
    nlp = user_profile.get("nlp_analysis", {})
    bc = user_profile.get("body_composition", {})

    freq = frequency or nlp.get("exercise_frequency", 3)
    experience = nlp.get("experience_level", "입문")
    goal = nlp.get("goal_type", "체중관리")
    constraints = nlp.get("constraints", [])

    split_info = get_recommended_split(freq, experience)

    # 제약사항 텍스트
    constraint_text = ", ".join(constraints) if constraints else "없음"
    if constraints:
        constraint_text += " (해당 부위 운동 시 대체 운동 제시 또는 주의사항 명시 필수)"

    return WORKOUT_PROMPT.format(
        gender=basic.get("gender", "미입력"),
        age=basic.get("age", "미입력"),
        height_cm=basic.get("height_cm", "미입력"),
        weight_kg=basic.get("weight_kg", "미입력"),
        body_fat_percent=bc.get("body_fat_percent") or "미측정",
        goal_type=goal,
        experience_level=experience,
        frequency=freq,
        constraints=constraint_text,
        split_type=split_info["split"],
        split_description=split_info["description"],
    )
