"""
meal_scheduler.py
사용자 일정(기상/취침/운동/근무)에 맞춰 끼니별 추천 섭취 시간을 배정합니다.

기능:
  1. 기상~취침 시간 기반 끼니 시간 자동 배정
  2. 운동일/비운동일 분기 (운동 전후 간식 배치)
  3. 끼니별 칼로리 배분 비율 조정
  4. 시간대별 영양 전략 (아침→탄수화물, 저녁→단백질 등)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class UserSchedule:
    """사용자 일정 정보"""
    wake_time: str = "07:00"              # 기상 시간
    sleep_time: str = "23:00"             # 취침 시간
    workout_time: str | None = None       # 운동 시간 (예: "18:00")
    workout_duration_min: int = 60        # 운동 시간 (분)
    work_start: str = "09:00"             # 근무 시작
    work_end: str = "18:00"               # 근무 종료
    is_workout_day: bool = True           # 오늘 운동일 여부
    schedule_note: str = ""               # 특이사항 ("야근", "재택" 등)


@dataclass
class MealTimeSlot:
    """끼니별 시간 슬롯"""
    meal_key: str                         # "breakfast", "morning_snack" 등
    meal_name: str                        # 표시명
    recommended_time: str                 # 추천 시간 "HH:MM"
    time_window: str                      # 섭취 가능 범위 "HH:MM~HH:MM"
    calorie_ratio: float                  # 일일 칼로리 배분 비율
    timing_reason: str                    # 시간 배정 이유
    nutrition_focus: str                  # 영양 전략 ("탄수화물 중심", "고단백" 등)
    is_optional: bool = False             # 건너뛸 수 있는지


@dataclass
class MealSchedule:
    """하루 전체 식사 스케줄"""
    slots: list[MealTimeSlot]
    schedule: UserSchedule
    total_meals: int = 0
    is_workout_day: bool = True
    notes: list[str] = field(default_factory=list)


# ═══════════════════════════════════════
# 시간 유틸리티
# ═══════════════════════════════════════

def _parse_time(time_str: str) -> datetime:
    """HH:MM 문자열을 datetime으로 변환합니다."""
    h, m = map(int, time_str.split(":"))
    return datetime(2000, 1, 1, h, m)


def _format_time(dt: datetime) -> str:
    """datetime을 HH:MM 문자열로 변환합니다."""
    return dt.strftime("%H:%M")


def _add_minutes(time_str: str, minutes: int) -> str:
    """시간에 분을 더합니다."""
    dt = _parse_time(time_str) + timedelta(minutes=minutes)
    return _format_time(dt)


def _time_window(center: str, before_min: int = 30, after_min: int = 30) -> str:
    """중심 시간에서 ±범위의 시간대를 생성합니다."""
    start = _add_minutes(center, -before_min)
    end = _add_minutes(center, after_min)
    return f"{start}~{end}"


# ═══════════════════════════════════════
# 스케줄 생성
# ═══════════════════════════════════════

def create_meal_schedule(
    schedule: UserSchedule,
    goal_type: str = "체중관리",
) -> MealSchedule:
    """
    사용자 일정에 맞춰 끼니별 시간과 칼로리 배분을 생성합니다.

    Args:
        schedule: 사용자 일정 정보
        goal_type: 운동 목표 (칼로리 배분에 영향)

    Returns:
        MealSchedule
    """
    wake = schedule.wake_time
    sleep = schedule.sleep_time
    workout = schedule.workout_time
    is_workout = schedule.is_workout_day and workout is not None
    note = schedule.schedule_note.lower()

    slots = []
    notes = []

    # ── 야근 감지 ──
    is_late_night = "야근" in note or "늦게" in note
    if is_late_night:
        notes.append("야근 일정 반영: 저녁 식단을 소화 부담 적은 메뉴로 조정")

    # ── 재택 감지 ──
    is_remote = "재택" in note or "집" in note

    # ── 1. 아침 식사 ──
    breakfast_time = _add_minutes(wake, 30)
    slots.append(MealTimeSlot(
        meal_key="breakfast",
        meal_name="아침 식사",
        recommended_time=breakfast_time,
        time_window=_time_window(breakfast_time, 0, 60),
        calorie_ratio=0.25,
        timing_reason="기상 30분 후 신진대사 활성화",
        nutrition_focus="복합 탄수화물 + 단백질 (하루 에너지 시작)",
    ))

    # ── 2. 오전 간식 ──
    morning_snack_time = _add_minutes(wake, 180)  # 기상 3시간 후
    slots.append(MealTimeSlot(
        meal_key="morning_snack",
        meal_name="오전 간식",
        recommended_time=morning_snack_time,
        time_window=_time_window(morning_snack_time, 30, 30),
        calorie_ratio=0.08,
        timing_reason="점심 전 혈당 유지",
        nutrition_focus="단백질 + 건강한 지방 (견과류, 요거트)",
        is_optional=True,
    ))

    # ── 3. 점심 식사 ──
    lunch_time = "12:30"
    if is_remote:
        lunch_time = "12:00"
    slots.append(MealTimeSlot(
        meal_key="lunch",
        meal_name="점심 식사",
        recommended_time=lunch_time,
        time_window=_time_window(lunch_time, 30, 60),
        calorie_ratio=0.30 if not is_late_night else 0.35,
        timing_reason="하루 중 가장 활동량이 많은 시간대의 에너지 공급",
        nutrition_focus="균형 잡힌 탄단지 (가장 큰 끼니)",
    ))

    # ── 4. 운동일 분기 ──
    if is_workout:
        workout_start = _parse_time(workout)
        workout_end_time = _format_time(workout_start + timedelta(minutes=schedule.workout_duration_min))

        # 오후 간식 → 운동 전 간식으로 변경
        pre_workout_time = _add_minutes(workout, -60)
        slots.append(MealTimeSlot(
            meal_key="pre_workout",
            meal_name="운동 전 간식",
            recommended_time=pre_workout_time,
            time_window=_time_window(pre_workout_time, 30, 0),
            calorie_ratio=0.07,
            timing_reason=f"운동({workout}) 60분 전 에너지 보충",
            nutrition_focus="빠른 탄수화물 + 소량 단백질 (바나나, 에너지바)",
        ))

        # 운동 후 보충
        post_workout_time = _add_minutes(workout_end_time, 15)
        slots.append(MealTimeSlot(
            meal_key="post_workout",
            meal_name="운동 후 보충",
            recommended_time=post_workout_time,
            time_window=_time_window(post_workout_time, 0, 30),
            calorie_ratio=0.08,
            timing_reason=f"운동 직후 30분 이내 근회복 골든타임",
            nutrition_focus="빠른 단백질 + 탄수화물 (프로틴쉐이크 + 바나나)",
        ))

        # 저녁 식사 (운동 후)
        dinner_time = _add_minutes(workout_end_time, 60)
        dinner_ratio = 0.22
    else:
        # 비운동일: 오후 간식
        afternoon_snack_time = "15:00"
        slots.append(MealTimeSlot(
            meal_key="afternoon_snack",
            meal_name="오후 간식",
            recommended_time=afternoon_snack_time,
            time_window=_time_window(afternoon_snack_time, 30, 30),
            calorie_ratio=0.07,
            timing_reason="오후 에너지 저하 방지",
            nutrition_focus="단백질 + 식이섬유 (프로틴바, 과일)",
            is_optional=True,
        ))

        dinner_time = "19:00"
        dinner_ratio = 0.25

    # ── 5. 저녁 식사 ──
    if is_late_night:
        dinner_time = _add_minutes(schedule.work_end, 30) if "야근" not in note else "21:00"
        dinner_ratio = 0.17
        notes.append("야근 시 저녁: 소화 부담 적은 샐러드/수프 권장")

    # 취침 3시간 전까지 마무리
    sleep_dt = _parse_time(sleep)
    dinner_dt = _parse_time(dinner_time)
    cutoff = sleep_dt - timedelta(hours=3)
    if dinner_dt > cutoff:
        dinner_time = _format_time(cutoff)
        notes.append(f"취침({sleep}) 3시간 전인 {dinner_time}까지 저녁 식사 권장")

    slots.append(MealTimeSlot(
        meal_key="dinner",
        meal_name="저녁 식사",
        recommended_time=dinner_time,
        time_window=_time_window(dinner_time, 30, 30),
        calorie_ratio=dinner_ratio,
        timing_reason=f"취침 {sleep} 최소 3시간 전 마무리",
        nutrition_focus="고단백 + 채소 중심 (취침 전 소화 고려)" if is_late_night
            else "단백질 + 건강한 지방 (근회복 지원)" if is_workout
            else "균형 잡힌 저녁 (과식 방지)",
    ))

    # ── 비율 정규화 ──
    total_ratio = sum(s.calorie_ratio for s in slots)
    for s in slots:
        s.calorie_ratio = round(s.calorie_ratio / total_ratio, 3)

    # ── 시간순 정렬 ──
    slots.sort(key=lambda s: _parse_time(s.recommended_time))

    return MealSchedule(
        slots=slots,
        schedule=schedule,
        total_meals=len(slots),
        is_workout_day=is_workout,
        notes=notes,
    )


def get_meal_calorie_allocation(
    meal_schedule: MealSchedule,
    total_kcal: int,
) -> dict[str, int]:
    """각 끼니별 목표 칼로리를 계산합니다."""
    allocation = {}
    for slot in meal_schedule.slots:
        allocation[slot.meal_key] = round(total_kcal * slot.calorie_ratio)
    return allocation


def schedule_to_prompt_context(meal_schedule: MealSchedule) -> str:
    """LLM 프롬프트에 삽입할 스케줄 컨텍스트를 생성합니다."""
    lines = ["[일정 정보]"]
    s = meal_schedule.schedule
    lines.append(f"- 기상: {s.wake_time}, 취침: {s.sleep_time}")
    lines.append(f"- 근무: {s.work_start}~{s.work_end}")

    if meal_schedule.is_workout_day and s.workout_time:
        lines.append(f"- 오늘 운동: {s.workout_time} ({s.workout_duration_min}분)")
    else:
        lines.append("- 오늘 운동: 없음 (휴식일)")

    if s.schedule_note:
        lines.append(f"- 특이사항: {s.schedule_note}")

    lines.append("")
    lines.append("[끼니별 시간 배정]")
    for slot in meal_schedule.slots:
        opt = " (선택)" if slot.is_optional else ""
        lines.append(
            f"- {slot.recommended_time} {slot.meal_name}{opt}: "
            f"{slot.nutrition_focus} (~{round(slot.calorie_ratio*100)}%)"
        )

    if meal_schedule.notes:
        lines.append("")
        lines.append("[주의사항]")
        for note in meal_schedule.notes:
            lines.append(f"- {note}")

    return "\n".join(lines)
