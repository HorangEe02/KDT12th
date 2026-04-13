"""
body_calculator.py
신체 정보를 바탕으로 주요 건강 지표를 계산합니다.

BMR: Mifflin-St Jeor 공식 (ADA 권장, 현대 인구에서 더 정확)
BMI: 아시아-태평양(KSSO) 기준 6단계
체지방률: 남녀별 5단계 판정
"""

from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════
# BMI 분류 (대한비만학회 KSSO 기준)
# ═══════════════════════════════════════

class BMICategory(Enum):
    UNDERWEIGHT = "저체중"           # < 18.5
    NORMAL = "정상"                  # 18.5 ~ 22.9
    OVERWEIGHT = "과체중"            # 23.0 ~ 24.9
    OBESE_1 = "1단계 비만"           # 25.0 ~ 29.9
    OBESE_2 = "2단계 비만"           # 30.0 ~ 34.9
    OBESE_3 = "3단계 비만(고도비만)"  # >= 35.0


# ═══════════════════════════════════════
# 체지방률 분류
# ═══════════════════════════════════════

class BodyFatCategory(Enum):
    ESSENTIAL = "필수지방"
    ATHLETIC = "운동선수"
    FITNESS = "건강"
    AVERAGE = "평균"
    OBESE = "비만"


# 체지방률 기준표 (성별, 상한값 기준)
BODY_FAT_RANGES = {
    "남성": [
        (5.0, BodyFatCategory.ESSENTIAL),
        (13.0, BodyFatCategory.ATHLETIC),
        (17.0, BodyFatCategory.FITNESS),
        (24.0, BodyFatCategory.AVERAGE),
        (100.0, BodyFatCategory.OBESE),
    ],
    "여성": [
        (13.0, BodyFatCategory.ESSENTIAL),
        (20.0, BodyFatCategory.ATHLETIC),
        (24.0, BodyFatCategory.FITNESS),
        (31.0, BodyFatCategory.AVERAGE),
        (100.0, BodyFatCategory.OBESE),
    ],
}


# ═══════════════════════════════════════
# 내장지방 레벨 분류
# ═══════════════════════════════════════

class VisceralFatRisk(Enum):
    NORMAL = "정상"      # 1-9
    CAUTION = "주의"     # 10-14
    DANGER = "위험"      # 15+


# ═══════════════════════════════════════
# 활동 수준 계수
# ═══════════════════════════════════════

class ActivityLevel(Enum):
    SEDENTARY = 1.2         # 거의 운동 안 함 (주 0회)
    LIGHT = 1.375           # 주 1~2회 가벼운 운동
    MODERATE = 1.55         # 주 3~4회 중간 강도
    ACTIVE = 1.725          # 주 5~6회 강한 운동
    VERY_ACTIVE = 1.9       # 매일 고강도 + 육체노동


# ═══════════════════════════════════════
# 목표별 칼로리 조정
# ═══════════════════════════════════════

GOAL_CALORIE_ADJUSTMENTS = {
    "체지방감소": -500,     # 주당 약 0.5kg 감량
    "근력증가": +300,       # 린매스 증가
    "체력향상": 0,          # 유지
    "체중관리": 0,          # 유지
    "건강개선": -300,       # 완만한 감량
}


@dataclass
class BodyMetrics:
    """계산된 신체 지표"""
    bmi: float
    bmi_category: str
    bmr_kcal: int
    tdee_kcal: int
    recommended_intake_kcal: int
    ideal_weight_kg: float
    ideal_weight_range: tuple[float, float]
    body_fat_category: str | None = None
    visceral_fat_risk: str | None = None
    smi: float | None = None              # 골격근지수
    sarcopenia_risk: bool | None = None   # 근감소증 위험


def calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float, BMICategory]:
    """
    BMI를 계산하고 KSSO(대한비만학회) 기준으로 판정합니다.

    Args:
        weight_kg: 체중 (kg)
        height_cm: 키 (cm)

    Returns:
        (BMI 수치, BMI 카테고리)
    """
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = BMICategory.UNDERWEIGHT
    elif bmi < 23.0:
        category = BMICategory.NORMAL
    elif bmi < 25.0:
        category = BMICategory.OVERWEIGHT
    elif bmi < 30.0:
        category = BMICategory.OBESE_1
    elif bmi < 35.0:
        category = BMICategory.OBESE_2
    else:
        category = BMICategory.OBESE_3

    return bmi, category


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> int:
    """
    기초대사량을 Mifflin-St Jeor 공식으로 계산합니다.
    ADA(미국영양사협회) 권장 공식으로, Harris-Benedict보다 현대 인구에서 더 정확합니다.

    남성: BMR = 10 × 체중(kg) + 6.25 × 키(cm) - 5 × 나이 + 5
    여성: BMR = 10 × 체중(kg) + 6.25 × 키(cm) - 5 × 나이 - 161

    Args:
        weight_kg: 체중 (kg)
        height_cm: 키 (cm)
        age: 나이
        gender: "남성" 또는 "여성"

    Returns:
        기초대사량 (kcal)
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "남성":
        bmr = base + 5
    else:
        bmr = base - 161
    return max(round(bmr), 800)  # 최소 800kcal 보장


def calculate_bmr_harris_benedict(
    weight_kg: float, height_cm: float, age: int, gender: str
) -> int:
    """
    Harris-Benedict 개정판 (1984) 기초대사량 계산.
    비교 실험용으로 제공합니다.

    남성: BMR = 88.362 + (13.397 × 체중) + (4.799 × 키) - (5.677 × 나이)
    여성: BMR = 447.593 + (9.247 × 체중) + (3.098 × 키) - (4.330 × 나이)
    """
    if gender == "남성":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return max(round(bmr), 800)


def calculate_tdee(bmr: int, exercise_frequency: int) -> int:
    """
    TDEE(총 일일 에너지 소비량)를 계산합니다.

    Args:
        bmr: 기초대사량 (kcal)
        exercise_frequency: 주당 운동 횟수

    Returns:
        TDEE (kcal)
    """
    if exercise_frequency <= 0:
        multiplier = ActivityLevel.SEDENTARY.value
    elif exercise_frequency <= 2:
        multiplier = ActivityLevel.LIGHT.value
    elif exercise_frequency <= 4:
        multiplier = ActivityLevel.MODERATE.value
    elif exercise_frequency <= 6:
        multiplier = ActivityLevel.ACTIVE.value
    else:
        multiplier = ActivityLevel.VERY_ACTIVE.value

    return round(bmr * multiplier)


def calculate_recommended_intake(tdee: int, goal_type: str, gender: str = "남성") -> int:
    """
    목표에 따른 권장 섭취 칼로리를 계산합니다.

    Args:
        tdee: TDEE (kcal)
        goal_type: 운동 목표 유형
        gender: 성별 (최소 섭취량 보장용)

    Returns:
        권장 섭취 칼로리 (kcal)
    """
    adjustment = GOAL_CALORIE_ADJUSTMENTS.get(goal_type, 0)
    recommended = tdee + adjustment
    min_intake = 1500 if gender == "남성" else 1200
    return max(recommended, min_intake)


def calculate_ideal_weight(height_cm: float) -> tuple[float, tuple[float, float]]:
    """
    적정 체중과 정상 체중 범위를 계산합니다.

    Args:
        height_cm: 키 (cm)

    Returns:
        (적정 체중(BMI 22 기준), (최소 정상 체중, 최대 정상 체중))
    """
    height_m = height_cm / 100
    ideal = round(22.0 * (height_m ** 2), 1)
    range_min = round(18.5 * (height_m ** 2), 1)
    range_max = round(22.9 * (height_m ** 2), 1)
    return ideal, (range_min, range_max)


def classify_body_fat_percent(body_fat_percent: float, gender: str) -> BodyFatCategory:
    """
    체지방률을 성별에 따라 판정합니다.

    Args:
        body_fat_percent: 체지방률 (%)
        gender: "남성" 또는 "여성"

    Returns:
        BodyFatCategory enum
    """
    ranges = BODY_FAT_RANGES.get(gender, BODY_FAT_RANGES["남성"])
    for upper_bound, category in ranges:
        if body_fat_percent <= upper_bound:
            return category
    return BodyFatCategory.OBESE


def classify_visceral_fat(level: int) -> VisceralFatRisk:
    """
    내장지방 레벨을 판정합니다.

    Args:
        level: InBody 내장지방 레벨 (1-20)

    Returns:
        VisceralFatRisk enum
    """
    if level <= 9:
        return VisceralFatRisk.NORMAL
    elif level <= 14:
        return VisceralFatRisk.CAUTION
    else:
        return VisceralFatRisk.DANGER


def check_abdominal_obesity(waist_hip_ratio: float, gender: str) -> bool:
    """
    복부비만 여부를 판정합니다. (KSSO 기준)

    Args:
        waist_hip_ratio: 허리-엉덩이 비율 (WHR)
        gender: "남성" 또는 "여성"

    Returns:
        복부비만 여부
    """
    threshold = 0.90 if gender == "남성" else 0.85
    return waist_hip_ratio > threshold


def calculate_smi(skeletal_muscle_mass_kg: float, height_cm: float) -> tuple[float, bool]:
    """
    골격근지수(SMI)를 계산하고 근감소증 위험을 판정합니다.
    (AWGS 아시아 근감소증 워킹그룹 기준)

    SMI = 골격근량(kg) / 신장(m)²

    Args:
        skeletal_muscle_mass_kg: 골격근량 (kg)
        height_cm: 키 (cm)

    Returns:
        (SMI 수치, 근감소증 위험 여부)
    """
    height_m = height_cm / 100
    smi = round(skeletal_muscle_mass_kg / (height_m ** 2), 2)
    # AWGS 기준: 남성 < 7.0, 여성 < 5.4 → 근감소 의심
    # 성별 구분 없이 보수적 기준 적용 (성별은 호출 측에서 판단)
    return smi, smi < 7.0


def calculate_all_metrics(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    exercise_frequency: int = 3,
    goal_type: str = "체중관리",
    body_fat_percent: float | None = None,
    visceral_fat_level: int | None = None,
    waist_hip_ratio: float | None = None,
    skeletal_muscle_mass_kg: float | None = None,
) -> BodyMetrics:
    """
    모든 신체 지표를 한 번에 계산합니다.

    Args:
        weight_kg: 체중 (kg)
        height_cm: 키 (cm)
        age: 나이
        gender: "남성" 또는 "여성"
        exercise_frequency: 주당 운동 횟수
        goal_type: 운동 목표 유형
        body_fat_percent: 체지방률 (인바디 데이터 있을 때)
        visceral_fat_level: 내장지방 레벨 (인바디)
        waist_hip_ratio: WHR (인바디)
        skeletal_muscle_mass_kg: 골격근량 (인바디)

    Returns:
        BodyMetrics 데이터클래스
    """
    bmi, bmi_category = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, exercise_frequency)
    recommended = calculate_recommended_intake(tdee, goal_type, gender)
    ideal_weight, ideal_range = calculate_ideal_weight(height_cm)

    metrics = BodyMetrics(
        bmi=bmi,
        bmi_category=bmi_category.value,
        bmr_kcal=bmr,
        tdee_kcal=tdee,
        recommended_intake_kcal=recommended,
        ideal_weight_kg=ideal_weight,
        ideal_weight_range=ideal_range,
    )

    # 체지방률 판정
    if body_fat_percent is not None:
        bf_cat = classify_body_fat_percent(body_fat_percent, gender)
        metrics.body_fat_category = bf_cat.value

    # 내장지방 판정
    if visceral_fat_level is not None:
        vf_risk = classify_visceral_fat(visceral_fat_level)
        metrics.visceral_fat_risk = vf_risk.value

    # 근감소증 판정
    if skeletal_muscle_mass_kg is not None:
        smi, risk = calculate_smi(skeletal_muscle_mass_kg, height_cm)
        # 성별별 기준 적용
        threshold = 7.0 if gender == "남성" else 5.4
        metrics.smi = smi
        metrics.sarcopenia_risk = smi < threshold

    return metrics
