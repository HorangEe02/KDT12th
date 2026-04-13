"""
profile_builder.py
모든 분석 결과를 통합하여 최종 사용자 프로필을 생성합니다.

인바디 데이터, 자연어 입력, 자동 계산 결과를 하나의 구조화된 JSON으로 통합합니다.
"""

from datetime import datetime

from .profile_ner import extract_entities_rule_based
from .goal_classifier import classify_goal_rule_based, GoalType
from .keyword_extractor import extract_keywords
from .body_calculator import calculate_all_metrics
from .health_analyzer import analyze_health_risks, calculate_profile_confidence


# ═══════════════════════════════════════
# 식이 제약 자동 매핑
# ═══════════════════════════════════════

DIETARY_CONSTRAINT_MAP = {
    "당뇨": {
        "flags": ["high_glycemic_warning", "low_carb_priority"],
        "note": "탄수화물 비율 낮추고 GI 지수 낮은 식품 권장",
    },
    "고혈압": {
        "flags": ["low_sodium_priority"],
        "note": "나트륨 하루 2000mg 이하 제한",
    },
    "고지혈증": {
        "flags": ["low_fat_priority", "low_cholesterol"],
        "note": "포화지방 줄이고 오메가3 풍부한 식품 권장",
    },
    "신장질환": {
        "flags": ["low_protein_warning", "low_potassium"],
        "note": "단백질 제한, 칼륨·인 주의",
    },
}

# 자연어에서 감지할 추가 식이 키워드
DIETARY_TEXT_KEYWORDS = {
    "채식": {"flags": ["vegetarian_flag"], "note": "채식 식단 구성"},
    "비건": {"flags": ["vegan_flag"], "note": "동물성 식품 완전 배제"},
    "유당불내증": {"flags": ["lactose_intolerant"], "note": "유제품 대체"},
    "글루텐 프리": {"flags": ["gluten_free"], "note": "밀가루 대체"},
    "알레르기": {"flags": ["allergen_check"], "note": "알레르기 유발 식품 확인 필요"},
}


def _detect_dietary_flags(constraints: list[str], text: str = "") -> dict:
    """제약사항과 텍스트에서 식이 플래그를 추출합니다."""
    flags = []
    notes = []

    for constraint in constraints:
        mapping = DIETARY_CONSTRAINT_MAP.get(constraint)
        if mapping:
            flags.extend(mapping["flags"])
            notes.append(mapping["note"])

    for keyword, mapping in DIETARY_TEXT_KEYWORDS.items():
        if keyword in text:
            flags.extend(mapping["flags"])
            notes.append(mapping["note"])

    return {"flags": list(set(flags)), "notes": notes}


def _determine_priority(weight_control: dict) -> str:
    """인바디 체중조절 데이터에서 우선순위를 결정합니다."""
    fat_adj = abs(weight_control.get("fat_adjustment_kg") or 0)
    muscle_adj = abs(weight_control.get("muscle_adjustment_kg") or 0)

    if fat_adj > muscle_adj * 2:
        return "지방감량우선"
    elif muscle_adj > fat_adj * 2:
        return "근육증가우선"
    else:
        return "균형관리"


def build_user_profile(
    inbody_data=None,
    natural_text: str | None = None,
    model_used: str = "rule_based",
) -> dict:
    """
    인바디 데이터와/또는 자연어 입력을 통합하여 최종 프로필을 생성합니다.

    Args:
        inbody_data: InBodyData 객체 또는 인바디 딕셔너리 (None 가능)
        natural_text: 자연어 입력 텍스트 (None 가능)
        model_used: 사용한 주요 모델명

    Returns:
        구조화된 사용자 프로필 딕셔너리

    Examples:
        >>> profile = build_user_profile(
        ...     natural_text="25세 남성 178cm 82kg. 체지방 줄이고 근육 늘리고 싶어요. 주 3회 운동."
        ... )
        >>> profile["basic"]["age"]
        25
        >>> profile["nlp_analysis"]["goal_type"]
        '체지방감소'
    """
    profile = {
        "basic": {},
        "body_composition": {},
        "calculated": {},
        "nlp_analysis": {},
        "recommendations": {},
        "health_risk_flags": {},
        "dietary_flags": {},
        "profile_confidence": {},
        "meta": {
            "input_type": "unknown",
            "has_inbody": False,
            "created_at": datetime.now().isoformat(),
            "model_used": model_used,
        },
    }

    # ── Step 1: 인바디 데이터 적용 ──
    if inbody_data is not None:
        _apply_inbody_data(profile, inbody_data)

    # ── Step 2: 자연어 분석 적용 ──
    if natural_text:
        _apply_natural_language(profile, natural_text, has_inbody=inbody_data is not None)

    # ── Step 3: 자동 계산 ──
    _apply_auto_calculations(profile)

    # ── Step 4: 건강 위험도 분석 ──
    health_flags = analyze_health_risks(profile, natural_text or "")
    profile["health_risk_flags"] = {
        "visceral_fat_risk": health_flags.visceral_fat_risk,
        "abdominal_obesity": health_flags.abdominal_obesity,
        "sarcopenia_risk": health_flags.sarcopenia_risk,
        "smi": health_flags.smi,
        "metabolic_syndrome_indicators": health_flags.metabolic_syndrome_indicators,
        "metabolic_syndrome_details": health_flags.metabolic_syndrome_details,
        "cardiovascular_risk_level": health_flags.cardiovascular_risk_level,
        "warnings": health_flags.warnings,
        "recommendations": health_flags.recommendations,
    }

    # ── Step 5: 식이 제약 매핑 ──
    constraints = profile.get("nlp_analysis", {}).get("constraints", [])
    profile["dietary_flags"] = _detect_dietary_flags(constraints, natural_text or "")

    # ── Step 6: 프로필 신뢰도 ──
    confidence = calculate_profile_confidence(profile)
    profile["profile_confidence"] = {
        "score": confidence.score,
        "level": confidence.level,
        "missing_fields": confidence.missing_fields,
        "suggestion": confidence.suggestion,
    }

    return profile


def _apply_inbody_data(profile: dict, inbody_data) -> None:
    """인바디 데이터를 프로필에 적용합니다."""
    # InBodyData 객체 또는 딕셔너리 모두 지원
    if hasattr(inbody_data, "raw"):
        data = inbody_data.raw
    elif isinstance(inbody_data, dict):
        data = inbody_data
    else:
        return

    profile["meta"]["has_inbody"] = True
    profile["meta"]["input_type"] = "inbody_image"

    basic = data.get("basic_info", {})
    profile["basic"] = {
        "age": basic.get("age"),
        "gender": basic.get("gender"),
        "height_cm": basic.get("height_cm"),
        "weight_kg": data.get("body_composition", {}).get("weight_kg"),
    }

    mfa = data.get("muscle_fat_analysis", {})
    oa = data.get("obesity_analysis", {})
    rp = data.get("research_params", {})
    oe = data.get("obesity_evaluation", {})

    profile["body_composition"] = {
        "skeletal_muscle_mass_kg": mfa.get("skeletal_muscle_mass_kg"),
        "body_fat_mass_kg": mfa.get("body_fat_mass_kg"),
        "body_fat_percent": oa.get("body_fat_percent"),
        "bmi": oa.get("bmi"),
        "bmr_kcal": rp.get("bmr_kcal"),
        "lean_body_mass_kg": rp.get("lean_body_mass_kg"),
        "visceral_fat_level": oe.get("visceral_fat_level"),
        "waist_hip_ratio": oe.get("waist_hip_ratio"),
        "inbody_score": data.get("inbody_score"),
    }

    wc = data.get("weight_control", {})
    profile["recommendations"] = {
        "weight_adjustment_kg": wc.get("weight_adjustment_kg"),
        "fat_adjustment_kg": wc.get("fat_adjustment_kg"),
        "muscle_adjustment_kg": wc.get("muscle_adjustment_kg"),
        "priority": _determine_priority(wc),
    }


def _apply_natural_language(profile: dict, text: str, has_inbody: bool) -> None:
    """자연어 분석 결과를 프로필에 적용합니다."""
    if has_inbody:
        profile["meta"]["input_type"] = "both"
    else:
        profile["meta"]["input_type"] = "natural_language"

    # NER 추출
    entities = extract_entities_rule_based(text)

    # 인바디 없을 때 기본 정보를 자연어에서 채움
    if not has_inbody:
        profile["basic"] = {
            "age": entities.age,
            "gender": entities.gender,
            "height_cm": entities.height_cm,
            "weight_kg": entities.weight_kg,
        }

    # 목표 분류
    goal_result = classify_goal_rule_based(text)

    # 키워드 추출
    keyword_result = extract_keywords(text, top_n=5)

    profile["nlp_analysis"] = {
        "goal_type": goal_result.goal_type.value,
        "goal_confidence": goal_result.confidence,
        "goal_method": goal_result.method,
        "goal_reason": goal_result.reason,
        "goal_keywords": [kw for kw, _ in keyword_result.keywords],
        "constraints": entities.constraints,
        "experience_level": entities.experience_level or "입문",
        "exercise_frequency": entities.exercise_frequency or 3,
        "preferred_exercises": entities.preferred_exercises,
        "body_fat_percent_from_text": entities.body_fat_percent,
    }


def _apply_auto_calculations(profile: dict) -> None:
    """BMI, BMR, TDEE 등을 자동 계산합니다."""
    b = profile.get("basic", {})

    if not (b.get("weight_kg") and b.get("height_cm")):
        return

    nlp = profile.get("nlp_analysis", {})
    goal_type = nlp.get("goal_type", "체중관리")
    frequency = nlp.get("exercise_frequency", 3)
    gender = b.get("gender", "남성")

    # 인바디 데이터가 있으면 체지방률 등 활용
    body_comp = profile.get("body_composition", {})

    metrics = calculate_all_metrics(
        weight_kg=b["weight_kg"],
        height_cm=b["height_cm"],
        age=b.get("age", 30),
        gender=gender,
        exercise_frequency=frequency,
        goal_type=goal_type,
        body_fat_percent=body_comp.get("body_fat_percent")
            or nlp.get("body_fat_percent_from_text"),
        visceral_fat_level=body_comp.get("visceral_fat_level"),
        waist_hip_ratio=body_comp.get("waist_hip_ratio"),
        skeletal_muscle_mass_kg=body_comp.get("skeletal_muscle_mass_kg"),
    )

    profile["calculated"] = {
        "bmi": metrics.bmi,
        "bmi_category": metrics.bmi_category,
        "bmr_kcal": metrics.bmr_kcal,
        "tdee_kcal": metrics.tdee_kcal,
        "recommended_intake_kcal": metrics.recommended_intake_kcal,
        "ideal_weight_kg": metrics.ideal_weight_kg,
        "ideal_weight_range": list(metrics.ideal_weight_range),
        "body_fat_category": metrics.body_fat_category,
        "visceral_fat_risk": metrics.visceral_fat_risk,
        "smi": metrics.smi,
        "sarcopenia_risk": metrics.sarcopenia_risk,
    }

    # 인바디 BMR이 있으면 비교 정보 추가
    inbody_bmr = body_comp.get("bmr_kcal")
    if inbody_bmr:
        profile["calculated"]["bmr_inbody_kcal"] = inbody_bmr
        profile["calculated"]["bmr_diff_kcal"] = metrics.bmr_kcal - inbody_bmr
