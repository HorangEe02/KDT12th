"""
health_analyzer.py
사용자 프로필 데이터를 기반으로 건강 위험도를 분석합니다.

- 내장지방 위험도
- 복부비만 판정 (WHR)
- 근감소증 위험 (SMI)
- 대사증후군 사전 스크리닝
- 프로필 신뢰도 점수
- 종합 건강 위험도 플래그
"""

from dataclasses import dataclass, field


@dataclass
class HealthRiskFlags:
    """건강 위험도 플래그"""
    visceral_fat_risk: str | None = None          # "정상" | "주의" | "위험"
    abdominal_obesity: bool | None = None         # 복부비만 여부
    sarcopenia_risk: bool | None = None           # 근감소증 위험
    smi: float | None = None                      # 골격근지수
    metabolic_syndrome_indicators: int = 0         # 대사증후군 해당 항목 수 (0-5)
    metabolic_syndrome_details: list[str] = field(default_factory=list)
    cardiovascular_risk_level: str = "낮음"        # "낮음" | "보통" | "높음"
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ProfileConfidence:
    """프로필 신뢰도 점수"""
    score: int                    # 0-100
    level: str                    # "높음" | "보통" | "낮음"
    missing_fields: list[str]     # 누락된 핵심 필드
    suggestion: str               # 개선 제안


# ═══════════════════════════════════════
# 대사증후군 관련 상수
# ═══════════════════════════════════════

# 대사증후군 진단 기준 (대한내과학회 기준)
# 5가지 항목 중 3개 이상 해당 시 대사증후군
METABOLIC_SYNDROME_CRITERIA = {
    "abdominal_obesity": {
        "description": "복부비만 (WHR 기반)",
        "남성": {"whr_threshold": 0.90},
        "여성": {"whr_threshold": 0.85},
    },
    "high_bmi": {
        "description": "비만 (BMI ≥ 25)",
        "threshold": 25.0,
    },
    "high_body_fat": {
        "description": "높은 체지방률",
        "남성": {"threshold": 25.0},
        "여성": {"threshold": 32.0},
    },
    "high_visceral_fat": {
        "description": "높은 내장지방 (레벨 ≥ 10)",
        "threshold": 10,
    },
}

# 텍스트에서 감지할 추가 위험 키워드
METABOLIC_TEXT_INDICATORS = {
    "고혈압": ["고혈압", "혈압 높", "혈압약"],
    "고혈당": ["당뇨", "혈당 높", "혈당", "인슐린"],
    "고지혈증": ["콜레스테롤", "고지혈", "중성지방"],
}


def analyze_health_risks(
    profile: dict,
    user_text: str = "",
) -> HealthRiskFlags:
    """
    프로필 데이터와 자연어 입력에서 건강 위험도를 분석합니다.

    Args:
        profile: 사용자 프로필 딕셔너리
        user_text: 원본 사용자 입력 텍스트

    Returns:
        HealthRiskFlags 데이터클래스
    """
    flags = HealthRiskFlags()
    gender = profile.get("basic", {}).get("gender", "남성")
    body_comp = profile.get("body_composition", {})
    calculated = profile.get("calculated", {})

    # ── 1. 내장지방 위험도 ──
    visceral_level = body_comp.get("visceral_fat_level")
    if visceral_level is not None:
        if visceral_level <= 9:
            flags.visceral_fat_risk = "정상"
        elif visceral_level <= 14:
            flags.visceral_fat_risk = "주의"
            flags.warnings.append(f"내장지방 레벨 {visceral_level}: 유산소 운동과 식이 조절을 권장합니다.")
        else:
            flags.visceral_fat_risk = "위험"
            flags.warnings.append(f"내장지방 레벨 {visceral_level}: 전문의 상담을 권고합니다.")

    # ── 2. 복부비만 ──
    whr = body_comp.get("waist_hip_ratio")
    if whr is not None:
        threshold = 0.90 if gender == "남성" else 0.85
        flags.abdominal_obesity = whr > threshold
        if flags.abdominal_obesity:
            flags.warnings.append(f"복부비만 (WHR {whr}): 심혈관 질환 위험이 높아질 수 있습니다.")

    # ── 3. 근감소증 위험 ──
    smm = body_comp.get("skeletal_muscle_mass_kg")
    height_cm = profile.get("basic", {}).get("height_cm")
    if smm is not None and height_cm is not None:
        height_m = height_cm / 100
        smi = round(smm / (height_m ** 2), 2)
        flags.smi = smi
        threshold = 7.0 if gender == "남성" else 5.4
        flags.sarcopenia_risk = smi < threshold
        if flags.sarcopenia_risk:
            flags.warnings.append(
                f"근감소증 위험 (SMI {smi} kg/m²): 단백질 섭취 증가와 근력 운동을 권장합니다."
            )
            flags.recommendations.append("체중 1kg당 단백질 1.2-1.5g 섭취 권장")

    # ── 4. 대사증후군 스크리닝 ──
    met_count = 0
    met_details = []

    # 복부비만
    if flags.abdominal_obesity:
        met_count += 1
        met_details.append("복부비만")

    # 높은 BMI
    bmi = calculated.get("bmi") or body_comp.get("bmi")
    if bmi is not None and bmi >= 25.0:
        met_count += 1
        met_details.append(f"비만 (BMI {bmi})")

    # 높은 체지방률
    bf = body_comp.get("body_fat_percent")
    if bf is not None:
        bf_threshold = 25.0 if gender == "남성" else 32.0
        if bf >= bf_threshold:
            met_count += 1
            met_details.append(f"높은 체지방률 ({bf}%)")

    # 높은 내장지방
    if visceral_level is not None and visceral_level >= 10:
        met_count += 1
        met_details.append(f"내장지방 레벨 {visceral_level}")

    # 텍스트에서 추가 위험 요인 감지
    for indicator_name, keywords in METABOLIC_TEXT_INDICATORS.items():
        if any(kw in user_text for kw in keywords):
            met_count += 1
            met_details.append(f"{indicator_name} (자가 보고)")

    flags.metabolic_syndrome_indicators = min(met_count, 5)
    flags.metabolic_syndrome_details = met_details

    if met_count >= 3:
        flags.warnings.append(
            f"대사증후군 위험 ({met_count}개 항목 해당): 전문의 상담을 권고합니다."
        )

    # ── 5. 종합 심혈관 위험도 ──
    risk_score = 0
    if flags.abdominal_obesity:
        risk_score += 2
    if flags.visceral_fat_risk == "위험":
        risk_score += 3
    elif flags.visceral_fat_risk == "주의":
        risk_score += 1
    if bmi is not None and bmi >= 25.0:
        risk_score += 1
    if met_count >= 3:
        risk_score += 2

    if risk_score >= 5:
        flags.cardiovascular_risk_level = "높음"
    elif risk_score >= 2:
        flags.cardiovascular_risk_level = "보통"
    else:
        flags.cardiovascular_risk_level = "낮음"

    # ── 6. 권장사항 생성 ──
    age = profile.get("basic", {}).get("age", 0)
    if age >= 40 and flags.sarcopenia_risk:
        flags.recommendations.append("40대 이상 근감소증 위험: 주 3회 이상 근력 운동 권장")

    if flags.cardiovascular_risk_level in ("보통", "높음"):
        flags.recommendations.append("유산소 운동 주 150분 이상 + 식이 관리 권장")

    return flags


def calculate_profile_confidence(profile: dict) -> ProfileConfidence:
    """
    프로필의 완성도와 신뢰도를 점수로 산출합니다.

    Args:
        profile: 사용자 프로필 딕셔너리

    Returns:
        ProfileConfidence 데이터클래스
    """
    score = 0
    missing = []

    basic = profile.get("basic", {})
    body_comp = profile.get("body_composition", {})
    nlp = profile.get("nlp_analysis", {})
    meta = profile.get("meta", {})

    # 기본 정보 (각 10점)
    for field_name, label in [
        ("age", "나이"), ("gender", "성별"),
        ("height_cm", "키"), ("weight_kg", "체중"),
    ]:
        if basic.get(field_name):
            score += 10
        else:
            missing.append(label)

    # NLP 분석 (각 5점)
    if nlp.get("goal_type"):
        score += 10
    else:
        missing.append("운동 목표")

    if nlp.get("exercise_frequency"):
        score += 5
    else:
        missing.append("운동 빈도")

    if nlp.get("experience_level"):
        score += 5

    # 인바디 데이터 (큰 보너스)
    if meta.get("has_inbody"):
        score += 25
        if body_comp.get("body_fat_percent"):
            score += 5
        if body_comp.get("skeletal_muscle_mass_kg"):
            score += 5
        if body_comp.get("visceral_fat_level"):
            score += 5
    else:
        missing.append("인바디 데이터 (선택사항)")

    score = min(score, 100)

    if score >= 70:
        level = "높음"
    elif score >= 40:
        level = "보통"
    else:
        level = "낮음"

    # 개선 제안
    if not meta.get("has_inbody"):
        suggestion = "인바디 측정 결과를 업로드하면 더 정확한 분석이 가능합니다."
    elif missing:
        suggestion = f"다음 정보를 추가하면 분석 정확도가 향상됩니다: {', '.join(missing[:3])}"
    else:
        suggestion = "프로필이 충분히 완성되었습니다."

    return ProfileConfidence(
        score=score,
        level=level,
        missing_fields=missing,
        suggestion=suggestion,
    )
