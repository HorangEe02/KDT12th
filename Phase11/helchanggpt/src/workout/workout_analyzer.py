"""
workout_analyzer.py
생성된 운동 루틴을 분석합니다.

1. 근육군 균형 점수
2. 제약사항 위반 체크
3. 유산소/무산소 비율 검증
4. 볼륨(세트×반복) 분석
5. 주간 요약 + 개선 제안
"""

from dataclasses import dataclass, field

from .workout_prompts import GOAL_CARDIO_RATIO, DISCLAIMER_SHORT


@dataclass
class WorkoutAnalysis:
    """운동 루틴 분석 결과"""
    # 근육군 균형
    muscle_coverage: dict = field(default_factory=dict)  # {근육군: 세트수}
    balance_score: float = 0                              # 0~100
    underworked_muscles: list[str] = field(default_factory=list)
    overworked_muscles: list[str] = field(default_factory=list)

    # 유산소/무산소 비율
    cardio_ratio: float = 0
    strength_ratio: float = 0
    ratio_assessment: str = ""

    # 제약사항
    constraint_warnings: list[str] = field(default_factory=list)

    # 볼륨
    total_weekly_sets: int = 0
    volume_assessment: str = ""

    # 종합
    overall_score: int = 0
    grade: str = ""
    improvements: list[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER_SHORT


ALL_MUSCLE_GROUPS = ["가슴", "등", "어깨", "하체", "이두", "삼두", "코어"]

# 경험별 주당 권장 세트 수 (부위당)
RECOMMENDED_WEEKLY_SETS = {
    "입문": (6, 10),
    "초급": (8, 12),
    "중급": (10, 16),
    "고급": (14, 22),
}


def analyze_workout_plan(
    workout_plan: dict,
    goal_type: str = "체중관리",
    experience: str = "입문",
    constraints: list[str] | None = None,
) -> WorkoutAnalysis:
    """
    운동 루틴을 종합 분석합니다.
    """
    analysis = WorkoutAnalysis()
    weekly = workout_plan.get("weekly_plan", {})

    # 1. 근육군 커버리지 + 세트 수 집계
    muscle_sets = {m: 0 for m in ALL_MUSCLE_GROUPS}
    cardio_minutes = 0
    strength_exercises = 0
    cardio_exercises = 0
    total_sets = 0

    for day_key, day_data in weekly.items():
        if not isinstance(day_data, dict):
            continue

        for ex in day_data.get("main_workout", {}).get("exercises", []):
            target = ex.get("target_muscle", "").split("/")[0].strip()
            sets = ex.get("sets", 0)
            reps = ex.get("reps", "")

            # 유산소 판별
            if "유산소" in target or "유산소" in ex.get("name", "") or "분" in str(reps):
                cardio_exercises += 1
                try:
                    mins = int(str(reps).replace("분", "").strip().split("~")[-1])
                    cardio_minutes += mins
                except (ValueError, IndexError):
                    cardio_minutes += 20
            else:
                strength_exercises += 1
                total_sets += sets
                # 근육군 매핑
                for mg in ALL_MUSCLE_GROUPS:
                    if mg in target:
                        muscle_sets[mg] += sets
                        break

    analysis.muscle_coverage = {k: v for k, v in muscle_sets.items() if v > 0}
    analysis.total_weekly_sets = total_sets

    # 2. 근육군 균형 점수
    covered = [m for m, s in muscle_sets.items() if s > 0]
    coverage_pct = len(covered) / len(ALL_MUSCLE_GROUPS) * 100

    # 표준편차로 균형 측정
    if covered:
        values = [muscle_sets[m] for m in covered]
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        uniformity = max(0, 100 - std * 10)
        analysis.balance_score = round((coverage_pct * 0.6 + uniformity * 0.4), 1)
    else:
        analysis.balance_score = 0

    # 부족/과다 근육군
    if covered:
        avg_sets = sum(muscle_sets[m] for m in covered) / len(covered) if covered else 0
        for mg in ALL_MUSCLE_GROUPS:
            if muscle_sets[mg] == 0:
                analysis.underworked_muscles.append(f"{mg} (운동 없음)")
            elif muscle_sets[mg] < avg_sets * 0.5:
                analysis.underworked_muscles.append(f"{mg} ({muscle_sets[mg]}세트 — 부족)")
            elif muscle_sets[mg] > avg_sets * 2:
                analysis.overworked_muscles.append(f"{mg} ({muscle_sets[mg]}세트 — 과다)")

    # 3. 유산소/무산소 비율
    total_ex = cardio_exercises + strength_exercises
    if total_ex > 0:
        analysis.cardio_ratio = round(cardio_exercises / total_ex * 100, 1)
        analysis.strength_ratio = round(strength_exercises / total_ex * 100, 1)

    target_ratio = GOAL_CARDIO_RATIO.get(goal_type, {})
    target_cardio = target_ratio.get("cardio_pct", 30)

    if abs(analysis.cardio_ratio - target_cardio) <= 15:
        analysis.ratio_assessment = f"적절 (목표 유산소 {target_cardio}%, 실제 {analysis.cardio_ratio}%)"
    elif analysis.cardio_ratio < target_cardio - 15:
        analysis.ratio_assessment = f"유산소 부족 (목표 {target_cardio}%, 실제 {analysis.cardio_ratio}%)"
        analysis.improvements.append(f"유산소 운동 추가 권장 (현재 {analysis.cardio_ratio}% → 목표 {target_cardio}%)")
    else:
        analysis.ratio_assessment = f"유산소 과다 (목표 {target_cardio}%, 실제 {analysis.cardio_ratio}%)"

    # 4. 볼륨 평가
    rec_range = RECOMMENDED_WEEKLY_SETS.get(experience, (8, 14))
    covered_count = max(len(covered), 1)
    avg_per_muscle = total_sets / covered_count

    if rec_range[0] <= avg_per_muscle <= rec_range[1]:
        analysis.volume_assessment = f"적절 (부위당 평균 {avg_per_muscle:.0f}세트, 권장 {rec_range[0]}~{rec_range[1]}세트)"
    elif avg_per_muscle < rec_range[0]:
        analysis.volume_assessment = f"볼륨 부족 (부위당 {avg_per_muscle:.0f}세트, 권장 {rec_range[0]}세트 이상)"
        analysis.improvements.append("세트 수를 늘리거나 종목을 추가하세요")
    else:
        analysis.volume_assessment = f"볼륨 과다 (부위당 {avg_per_muscle:.0f}세트, 권장 {rec_range[1]}세트 이하)"
        analysis.improvements.append("과훈련 주의: 세트 수를 줄이거나 휴식일을 추가하세요")

    # 5. 제약사항 체크
    if constraints:
        for day_key, day_data in weekly.items():
            if not isinstance(day_data, dict):
                continue
            for ex in day_data.get("main_workout", {}).get("exercises", []):
                contras = ex.get("contraindications", [])
                caution = ex.get("caution", "")
                name = ex.get("name", "")
                for c in constraints:
                    if c in " ".join(contras) or c in name:
                        if not caution:
                            analysis.constraint_warnings.append(
                                f"⚠️ {day_data.get('day_label', day_key)}의 '{name}'은 "
                                f"'{c}' 제약사항에 해당합니다. 대체 운동을 확인하세요."
                            )

    # 6. 종합 점수
    score = 50
    score += min(analysis.balance_score * 0.3, 30)

    if not analysis.constraint_warnings:
        score += 10

    if "적절" in analysis.ratio_assessment:
        score += 5
    if "적절" in analysis.volume_assessment:
        score += 5

    score -= len(analysis.underworked_muscles) * 3
    score -= len(analysis.constraint_warnings) * 5

    analysis.overall_score = max(0, min(round(score), 100))

    if analysis.overall_score >= 85:
        analysis.grade = "A"
    elif analysis.overall_score >= 70:
        analysis.grade = "B"
    elif analysis.overall_score >= 55:
        analysis.grade = "C"
    else:
        analysis.grade = "D"

    # 개선 제안 추가
    if analysis.underworked_muscles:
        analysis.improvements.append(
            f"부족한 부위: {', '.join(analysis.underworked_muscles[:3])} — 해당 부위 운동 추가 권장"
        )

    return analysis
