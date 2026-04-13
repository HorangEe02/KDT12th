"""
workout_generator.py
LLM으로 맞춤 운동 루틴을 생성합니다.
Ollama 로컬 모델(exaone3.5, qwen3.5 등)을 사용합니다.
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime

from .workout_prompts import (
    build_workout_prompt, DISCLAIMER, DISCLAIMER_SHORT,
    get_recommended_split, GOAL_CARDIO_RATIO,
)


@dataclass
class WorkoutGenerationResult:
    """운동 루틴 생성 결과"""
    workout_plan: dict
    model: str
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


def generate_workout_plan(
    user_profile: dict,
    frequency: int | None = None,
    model: str = "exaone3.5",
    temperature: float = 0.7,
    ollama_base_url: str = "http://localhost:11434/v1",
) -> WorkoutGenerationResult:
    """
    LLM으로 주간 운동 루틴을 생성합니다.

    Args:
        user_profile: Stage 1 UserProfile
        frequency: 주당 운동 횟수 (None이면 프로필에서 자동 결정)
        model: Ollama 모델
        temperature: 생성 temperature
    """
    from openai import OpenAI

    prompt = build_workout_prompt(user_profile, frequency)

    client = OpenAI(base_url=ollama_base_url, api_key="ollama")
    start = time.time()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4000,
        )

        latency = round(time.time() - start, 2)
        content = response.choices[0].message.content
        plan = _extract_json(content)

        # 메타 정보 + 면책 문구 추가
        plan = _enrich_plan(plan, user_profile, model, temperature, frequency)

        return WorkoutGenerationResult(
            workout_plan=plan,
            model=model,
            temperature=temperature,
            latency_sec=latency,
        )

    except Exception as e:
        return WorkoutGenerationResult(
            workout_plan={},
            model=model,
            temperature=temperature,
            latency_sec=round(time.time() - start, 2),
            success=False,
            error=str(e),
        )


def _enrich_plan(
    plan: dict, profile: dict, model: str, temperature: float, frequency: int | None
) -> dict:
    """생성된 루틴에 메타 정보, 주간 요약, 면책 문구를 추가합니다."""
    nlp = profile.get("nlp_analysis", {})
    freq = frequency or nlp.get("exercise_frequency", 3)
    goal = nlp.get("goal_type", "체중관리")
    experience = nlp.get("experience_level", "입문")
    constraints = nlp.get("constraints", [])
    split_info = get_recommended_split(freq, experience)

    # 메타 정보
    plan["meta"] = {
        "goal_type": goal,
        "frequency": freq,
        "split_type": split_info["split"],
        "experience_level": experience,
        "constraints_applied": constraints,
        "cardio_ratio": GOAL_CARDIO_RATIO.get(goal, {}),
        "model_used": model,
        "temperature": temperature,
        "generated_at": datetime.now().isoformat(),
    }

    # 면책 문구 (항상 포함)
    plan["disclaimer"] = DISCLAIMER
    plan["disclaimer_short"] = DISCLAIMER_SHORT

    # 주간 요약 계산
    weekly = plan.get("weekly_plan", {})
    total_time = 0
    total_cal = 0
    muscles = set()
    session_count = 0

    for day_key, day_data in weekly.items():
        if not isinstance(day_data, dict) or day_key == "rest_days":
            continue
        session_count += 1
        total_time += day_data.get("estimated_time_min", 0)
        total_cal += day_data.get("estimated_calories", 0)

        for ex in day_data.get("main_workout", {}).get("exercises", []):
            muscles.add(ex.get("target_muscle", ""))

    plan["weekly_summary"] = {
        "total_sessions": session_count,
        "total_estimated_time_min": total_time,
        "total_estimated_calories": total_cal,
        "muscle_groups_covered": sorted(muscles - {""}),
    }

    return plan


def generate_demo_workout_plan(
    frequency: int = 3,
    goal_type: str = "체지방감소",
    experience: str = "입문",
    constraints: list[str] | None = None,
) -> dict:
    """LLM 없이 데모 운동 루틴을 생성합니다."""
    constraints = constraints or []
    has_knee = "무릎 부상" in constraints
    has_back = "허리 부상" in constraints
    has_shoulder = "어깨 부상" in constraints

    plan = {
        "weekly_plan": {},
        "rest_days": [],
        "disclaimer": DISCLAIMER,
        "disclaimer_short": DISCLAIMER_SHORT,
    }

    # 요일 배정
    ALL_DAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

    if frequency == 3:
        days = [("day1", "월요일"), ("day2", "수요일"), ("day3", "금요일")]
        plan["rest_days"] = ["화요일", "목요일", "토요일", "일요일"]
    elif frequency == 4:
        days = [("day1", "월요일"), ("day2", "화요일"), ("day3", "목요일"), ("day4", "금요일")]
        plan["rest_days"] = ["수요일", "토요일", "일요일"]
    elif frequency == 5:
        days = [("day1", "월요일"), ("day2", "화요일"), ("day3", "수요일"), ("day4", "금요일"), ("day5", "토요일")]
        plan["rest_days"] = ["목요일", "일요일"]
    elif frequency == 6:
        days = [("day1", "월요일"), ("day2", "화요일"), ("day3", "수요일"), ("day4", "목요일"), ("day5", "금요일"), ("day6", "토요일")]
        plan["rest_days"] = ["일요일"]
    elif frequency >= 7:
        days = [(f"day{i+1}", ALL_DAYS[i]) for i in range(7)]
        plan["rest_days"] = []
    elif frequency == 2:
        days = [("day1", "화요일"), ("day2", "금요일")]
        plan["rest_days"] = ["월요일", "수요일", "목요일", "토요일", "일요일"]
    elif frequency == 1:
        days = [("day1", "수요일")]
        plan["rest_days"] = ["월요일", "화요일", "목요일", "금요일", "토요일", "일요일"]
    else:
        days = [("day1", "월요일"), ("day2", "수요일"), ("day3", "금요일")]
        plan["rest_days"] = ["화요일", "목요일", "토요일", "일요일"]

    # 부위별 루틴 분배 (빈도에 따라 세분화)
    if frequency >= 6:
        focus_rotation = ["가슴 + 삼두", "등 + 이두", "하체", "어깨 + 코어", "가슴 + 등", "하체 + 유산소", "전신 + 유산소"]
    elif frequency == 5:
        focus_rotation = ["가슴 + 삼두", "등 + 이두", "하체", "어깨 + 코어", "전신 + 유산소"]
    elif frequency == 4:
        focus_rotation = ["상체(밀기)", "하체", "상체(당기기)", "전신 + 유산소"]
    else:
        focus_rotation = ["상체 + 코어", "하체 + 유산소", "전신 + 유산소"]

    for i, (day_key, day_label) in enumerate(days):
        focus = focus_rotation[i % len(focus_rotation)]

        # 웜업
        warmup = {
            "exercises": [
                {"name": "트레드밀 걷기", "duration_min": 5, "description": "시속 5km로 가볍게 걸으며 체온 올리기"},
                {"name": "동적 스트레칭", "duration_min": 5, "description": "팔 돌리기, 무릎 올리기, 몸통 회전"},
            ]
        }

        # 메인 운동 (부위별)
        if "상체" in focus:
            exercises = [
                {"name": "푸쉬업" if not has_shoulder else "월 푸쉬업",
                 "target_muscle": "가슴", "sets": 3, "reps": "8~12", "rest_sec": 60, "intensity": "중",
                 "description": "팔꿈치를 45도로 유지하며 가슴까지 내려갔다 올라옵니다",
                 "alternatives": ["머신 체스트프레스", "덤벨 플라이"],
                 "caution": "어깨 부상 시 가동범위를 줄이세요" if has_shoulder else ""},
                {"name": "랫풀다운", "target_muscle": "등", "sets": 3, "reps": "10~12", "rest_sec": 60, "intensity": "중",
                 "description": "견갑골을 모으며 바를 쇄골 쪽으로 당깁니다",
                 "alternatives": ["시티드 로우", "밴드 풀다운"], "caution": ""},
                {"name": "덤벨 숄더프레스" if not has_shoulder else "사이드 레터럴 레이즈(가볍게)",
                 "target_muscle": "어깨", "sets": 3, "reps": "10~12", "rest_sec": 60, "intensity": "중" if not has_shoulder else "저",
                 "description": "덤벨을 귀 옆에서 머리 위로 밀어 올립니다" if not has_shoulder else "가벼운 무게로 팔을 옆으로 들어올립니다",
                 "alternatives": ["머신 숄더프레스", "프론트레이즈"],
                 "caution": "어깨 통증 시 즉시 중단" if has_shoulder else ""},
                {"name": "플랭크", "target_muscle": "코어", "sets": 3, "reps": "30초", "rest_sec": 45, "intensity": "중",
                 "description": "팔꿈치와 발끝으로 몸을 지탱, 일직선 유지",
                 "alternatives": ["데드버그", "무릎 플랭크"], "caution": "허리 통증 시 무릎 플랭크로 대체" if has_back else ""},
            ]
        elif "하체" in focus:
            exercises = [
                {"name": "레그프레스" if has_knee else "고블릿 스쿼트",
                 "target_muscle": "하체", "sets": 3, "reps": "10~12", "rest_sec": 90, "intensity": "중",
                 "description": "머신에서 발판을 밀어냅니다 (무릎 부담 적음)" if has_knee else "덤벨을 가슴 앞에 들고 스쿼트",
                 "alternatives": ["월 싯", "의자 스쿼트"],
                 "caution": "무릎 통증 시 가동범위 줄이기" if has_knee else ""},
                {"name": "런지" if not has_knee else "힙 브릿지",
                 "target_muscle": "하체/둔근", "sets": 3, "reps": "10(각)" if not has_knee else "15", "rest_sec": 60, "intensity": "중",
                 "description": "한 발을 앞으로 내딛고 무릎을 구부립니다" if not has_knee else "누워서 엉덩이를 들어올립니다",
                 "alternatives": ["불가리안 스플릿 스쿼트", "힙쓰러스트"],
                 "caution": "무릎 부상 시 힙 브릿지로 대체" if has_knee else ""},
                {"name": "사이클", "target_muscle": "하체/유산소", "sets": 1, "reps": "20분", "rest_sec": 0, "intensity": "중",
                 "description": "실내 자전거를 중간 강도로 타기 (무릎 부담 적음)",
                 "alternatives": ["일립티컬", "트레드밀 경사 걷기"], "caution": ""},
                {"name": "카프레이즈", "target_muscle": "종아리", "sets": 3, "reps": "15~20", "rest_sec": 30, "intensity": "저",
                 "description": "발끝으로 서서 종아리를 수축합니다",
                 "alternatives": ["시티드 카프레이즈"], "caution": ""},
            ]
        else:  # 전신
            exercises = [
                {"name": "레그프레스" if has_knee else "스쿼트",
                 "target_muscle": "하체", "sets": 3, "reps": "10~12", "rest_sec": 90, "intensity": "중",
                 "description": "전신 운동의 기본, 하체 전체 자극",
                 "alternatives": ["고블릿 스쿼트", "레그프레스"], "caution": "무릎 주의" if has_knee else ""},
                {"name": "푸쉬업", "target_muscle": "가슴/삼두", "sets": 3, "reps": "8~12", "rest_sec": 60, "intensity": "중",
                 "description": "상체 밀기 동작의 기본",
                 "alternatives": ["인클라인 푸쉬업", "머신 체스트프레스"], "caution": ""},
                {"name": "랫풀다운", "target_muscle": "등/이두", "sets": 3, "reps": "10~12", "rest_sec": 60, "intensity": "중",
                 "description": "상체 당기기 동작의 기본",
                 "alternatives": ["시티드 로우", "밴드 로우"], "caution": ""},
                {"name": "트레드밀 걷기(경사)", "target_muscle": "전신/유산소", "sets": 1, "reps": "15분", "rest_sec": 0, "intensity": "중",
                 "description": "경사도 5~8%에서 시속 5km 걷기",
                 "alternatives": ["사이클", "일립티컬"], "caution": ""},
            ]

        # 쿨다운
        cooldown = {
            "exercises": [
                {"name": "정적 스트레칭", "duration_min": 5, "description": "운동한 부위 위주로 20~30초씩 스트레칭"},
                {"name": "폼롤러", "duration_min": 3, "description": "등, 허벅지, 종아리를 폼롤러로 마사지"},
            ]
        }

        tips = [
            "운동 전 물 한 잔, 운동 중 수시로 수분 보충하세요",
            "호흡을 멈추지 마세요! 힘 쓸 때 내쉬고, 돌아올 때 들이쉽니다",
            "무게보다 자세가 먼저입니다. 올바른 자세를 유지하세요",
        ]

        plan["weekly_plan"][day_key] = {
            "day_label": day_label,
            "focus": focus,
            "estimated_time_min": 50 + (i % 2) * 10,
            "estimated_calories": 250 + (i % 3) * 50,
            "warmup": warmup,
            "main_workout": {"exercises": exercises},
            "cooldown": cooldown,
            "tip": tips[i % len(tips)],
        }

    # 메타 + 주간 요약
    plan["meta"] = {
        "goal_type": goal_type,
        "frequency": frequency,
        "split_type": "전신",
        "experience_level": experience,
        "constraints_applied": constraints,
        "model_used": "demo",
        "generated_at": datetime.now().isoformat(),
    }

    muscles = set()
    total_time = 0
    total_cal = 0
    for d in plan["weekly_plan"].values():
        if not isinstance(d, dict):
            continue
        total_time += d.get("estimated_time_min", 0)
        total_cal += d.get("estimated_calories", 0)
        for ex in d.get("main_workout", {}).get("exercises", []):
            muscles.add(ex.get("target_muscle", "").split("/")[0])

    plan["weekly_summary"] = {
        "total_sessions": len(days),
        "total_estimated_time_min": total_time,
        "total_estimated_calories": total_cal,
        "muscle_groups_covered": sorted(muscles - {""}),
    }

    return plan
