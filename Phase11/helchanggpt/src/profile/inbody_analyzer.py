"""
inbody_analyzer.py
인바디 데이터를 종합 분석하여 체형 판정, 건강 위험도, AI 코칭 메시지를 생성합니다.

분석 항목:
  1. 체형 분석 (C/I/D자형)
  2. 비만 분석 (BMI + 체지방률 조합)
  3. 내장지방 위험도 (VFA 기반)
  4. 근감소증 위험 (SMI)
  5. 수분 균형 (ECW 비율)
  6. 부위별 근육 발달 균형
  7. 신체변화 트렌드
  8. LLM 기반 AI 코칭 메시지
"""


def _to_float(val, default=None):
    """값을 안전하게 float로 변환합니다."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

from dataclasses import dataclass, field
from .inbody_parser import InBodyData


@dataclass
class InBodyAnalysis:
    """인바디 종합 분석 결과"""
    # 체형 판정
    body_shape: str = ""                     # "C자형" | "I자형" | "D자형"
    body_shape_description: str = ""

    # 비만 분석
    obesity_grade: str = ""                  # "저체중|정상|과체중|비만1|비만2|고도비만"
    bmi_status: str = ""
    body_fat_status: str = ""
    combined_assessment: str = ""            # BMI+체지방률 종합

    # 내장지방
    visceral_fat_risk: str = ""              # "매우양호|양호|주의|위험"
    vfa_cm2: float | None = None

    # 근감소증
    smi_value: float | None = None
    sarcopenia_risk: str = ""                # "정상|경계|위험"

    # 수분 균형
    ecw_status: str = ""                     # "정상|경계|이상"
    ecw_ratio: float | None = None

    # 부위별 균형
    muscle_balance: dict = field(default_factory=dict)

    # 변화 트렌드
    trend_summary: str = ""

    # 점수/등급
    overall_grade: str = ""                  # "A+|A|B+|B|C|D"
    inbody_score: int | None = None

    # AI 코칭
    coaching_messages: list[str] = field(default_factory=list)
    praise_points: list[str] = field(default_factory=list)
    improvement_points: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)

    # 전체 데이터
    raw_data: dict = field(default_factory=dict)


# ═══════════════════════════════════════
# 기준값 상수
# ═══════════════════════════════════════

BMI_GRADES = [
    (18.5, "저체중"), (23.0, "정상"), (25.0, "과체중"),
    (30.0, "1단계 비만"), (35.0, "2단계 비만"), (999, "고도비만"),
]

BF_PCT_MALE = [(6, "필수지방"), (13, "운동선수"), (17, "건강"), (24, "평균"), (100, "비만")]
BF_PCT_FEMALE = [(13, "필수지방"), (20, "운동선수"), (24, "건강"), (31, "평균"), (100, "비만")]

VFA_GRADES = [(50, "매우양호"), (100, "양호"), (150, "주의"), (999, "위험")]

SMI_THRESHOLDS = {"남성": 7.0, "여성": 5.4}

ECW_RANGE = (0.360, 0.390)  # 정상 범위


def analyze_inbody(inbody: InBodyData, user_text: str = "") -> InBodyAnalysis:
    """
    인바디 데이터를 종합 분석합니다.

    Args:
        inbody: 파싱된 InBodyData
        user_text: 사용자 추가 텍스트 (목표 등)

    Returns:
        InBodyAnalysis
    """
    analysis = InBodyAnalysis(raw_data=inbody.raw)
    gender = inbody.basic_info.get("gender", "남성")

    # 1. 체형 판정
    _analyze_body_shape(analysis, inbody)

    # 2. 비만 분석
    _analyze_obesity(analysis, inbody, gender)

    # 3. 내장지방
    _analyze_visceral_fat(analysis, inbody)

    # 4. 근감소증
    _analyze_sarcopenia(analysis, inbody, gender)

    # 5. 수분 균형
    _analyze_ecw(analysis, inbody)

    # 6. 부위별 근육 균형
    _analyze_muscle_balance(analysis, inbody)

    # 7. 변화 트렌드
    _analyze_trend(analysis, inbody)

    # 8. 종합 등급
    _calculate_grade(analysis, inbody)

    # 9. 코칭 메시지 생성
    _generate_coaching(analysis, inbody, gender)

    return analysis


def _analyze_body_shape(analysis: InBodyAnalysis, data: InBodyData):
    """체형(C/I/D자형)을 판정합니다."""
    mfa = data.muscle_fat_analysis
    weight = _to_float(mfa.get("weight_kg"), 0)
    smm = _to_float(mfa.get("skeletal_muscle_mass_kg"), 0)
    fat = _to_float(mfa.get("body_fat_mass_kg"), 0)

    if not (weight and smm and fat):
        return

    smm_ratio = smm / weight if weight else 0
    fat_ratio = fat / weight if weight else 0

    if fat_ratio > smm_ratio * 1.3:
        analysis.body_shape = "C자형"
        analysis.body_shape_description = "체지방이 골격근보다 많은 체형. 유산소 운동과 식이 조절을 통한 체지방 감량이 권장됩니다."
    elif abs(smm_ratio - fat_ratio) < 0.05 or (smm_ratio > fat_ratio * 0.7 and fat_ratio > smm_ratio * 0.7):
        analysis.body_shape = "I자형"
        analysis.body_shape_description = "체중, 골격근, 체지방이 균형 잡힌 표준 체형입니다."
    else:
        analysis.body_shape = "D자형"
        analysis.body_shape_description = "골격근이 체지방보다 많은 건강한 체형. 꾸준한 운동을 통해 현재 상태를 유지하세요."


def _analyze_obesity(analysis: InBodyAnalysis, data: InBodyData, gender: str):
    """BMI + 체지방률 종합 비만 분석."""
    oa = data.obesity_analysis or {}
    bmi = _to_float(oa.get("bmi"))
    bf_pct = _to_float(oa.get("body_fat_percent"))

    if bmi:
        for threshold, grade in BMI_GRADES:
            if bmi < threshold:
                analysis.bmi_status = grade
                break

    if bf_pct is not None:
        ranges = BF_PCT_MALE if gender == "남성" else BF_PCT_FEMALE
        for threshold, status in ranges:
            if bf_pct <= threshold:
                analysis.body_fat_status = status
                break

    # 종합 판정
    if bmi and bf_pct is not None:
        if analysis.bmi_status == "정상" and analysis.body_fat_status in ("운동선수", "건강"):
            analysis.combined_assessment = "건강 체형 (정상 BMI + 양호한 체지방률)"
        elif analysis.bmi_status == "정상" and analysis.body_fat_status == "비만":
            analysis.combined_assessment = "마른 비만 주의 (정상 BMI이나 체지방률 높음)"
        elif analysis.bmi_status in ("과체중", "1단계 비만") and analysis.body_fat_status in ("운동선수", "건강"):
            analysis.combined_assessment = "근육형 과체중 (높은 BMI이나 체지방률 낮음 → 근육이 많음)"
        elif analysis.bmi_status in ("과체중", "1단계 비만") and analysis.body_fat_status in ("평균", "비만"):
            analysis.combined_assessment = "과체중/비만 (체중 감량 권장)"
        else:
            analysis.combined_assessment = f"BMI: {analysis.bmi_status} / 체지방률: {analysis.body_fat_status}"

    analysis.obesity_grade = analysis.bmi_status


def _analyze_visceral_fat(analysis: InBodyAnalysis, data: InBodyData):
    """내장지방 위험도 판정 (VFA 기반)."""
    vfa = _to_float((data.visceral_fat or {}).get("vfa_cm2"))
    if vfa is None:
        return

    analysis.vfa_cm2 = vfa
    for threshold, grade in VFA_GRADES:
        if vfa <= threshold:
            analysis.visceral_fat_risk = grade
            break


def _analyze_sarcopenia(analysis: InBodyAnalysis, data: InBodyData, gender: str):
    """근감소증 위험 판정 (SMI 기반)."""
    smi = _to_float((data.research_params or {}).get("smi"))
    if smi is None:
        return

    analysis.smi_value = smi
    threshold = SMI_THRESHOLDS.get(gender, 7.0)

    if smi >= threshold * 1.2:
        analysis.sarcopenia_risk = "정상"
    elif smi >= threshold:
        analysis.sarcopenia_risk = "경계"
    else:
        analysis.sarcopenia_risk = "위험"


def _analyze_ecw(analysis: InBodyAnalysis, data: InBodyData):
    """세포외수분비 분석."""
    ecw = _to_float((data.ecw_ratio or {}).get("whole_body"))
    if ecw is None:
        return

    analysis.ecw_ratio = ecw
    if ECW_RANGE[0] <= ecw <= ECW_RANGE[1]:
        analysis.ecw_status = "정상"
    elif ecw < ECW_RANGE[0]:
        analysis.ecw_status = "경계 (낮음)"
    elif ecw <= 0.400:
        analysis.ecw_status = "경계 (높음)"
    else:
        analysis.ecw_status = "이상 (부종 가능성)"


def _analyze_muscle_balance(analysis: InBodyAnalysis, data: InBodyData):
    """부위별 근육 발달 균형 분석."""
    seg = data.segmental_lean
    if not seg:
        return

    parts = {}
    for side in [("right_arm_pct", "오른팔"), ("left_arm_pct", "왼팔"),
                 ("trunk_pct", "몸통"), ("right_leg_pct", "오른다리"), ("left_leg_pct", "왼다리")]:
        val = seg.get(side[0])
        if val is not None:
            parts[side[1]] = val

    if not parts:
        return

    avg = sum(parts.values()) / len(parts)
    imbalances = []

    # 좌우 비대칭 확인
    ra, la = seg.get("right_arm_pct"), seg.get("left_arm_pct")
    if ra and la and abs(ra - la) > 5:
        imbalances.append(f"팔 좌우 불균형 ({abs(ra - la):.1f}% 차이)")

    rl, ll = seg.get("right_leg_pct"), seg.get("left_leg_pct")
    if rl and ll and abs(rl - ll) > 5:
        imbalances.append(f"다리 좌우 불균형 ({abs(rl - ll):.1f}% 차이)")

    # 부위별 발달 부족
    for part_name, val in parts.items():
        if val < 90:
            imbalances.append(f"{part_name} 근육 발달 부족 ({val}%)")

    analysis.muscle_balance = {
        "parts": parts,
        "average_pct": round(avg, 1),
        "imbalances": imbalances,
        "is_balanced": len(imbalances) == 0,
    }


def _analyze_trend(analysis: InBodyAnalysis, data: InBodyData):
    """신체변화 트렌드를 분석합니다."""
    history = data.body_history
    if not history or not history.get("weight_series"):
        return

    weights = [w for w in history.get("weight_series", []) if w is not None]
    smms = [s for s in history.get("smm_series", []) if s is not None]
    bfps = [b for b in history.get("bfp_series", []) if b is not None]

    parts = []
    if len(weights) >= 2:
        diff = weights[-1] - weights[0]
        parts.append(f"체중 {'+' if diff > 0 else ''}{diff:.1f}kg")
    if len(smms) >= 2:
        diff = smms[-1] - smms[0]
        parts.append(f"골격근 {'+' if diff > 0 else ''}{diff:.1f}kg")
    if len(bfps) >= 2:
        diff = bfps[-1] - bfps[0]
        parts.append(f"체지방률 {'+' if diff > 0 else ''}{diff:.1f}%")

    if parts:
        n = len(history.get("dates", []))
        analysis.trend_summary = f"{n}회 측정 기간 동안: {', '.join(parts)}"


def _calculate_grade(analysis: InBodyAnalysis, data: InBodyData):
    """종합 등급을 산출합니다."""
    score = _to_float(data.inbody_score)
    if score is not None:
        score = int(score)
    analysis.inbody_score = score

    if score is None:
        return

    if score >= 90:
        analysis.overall_grade = "A+"
    elif score >= 80:
        analysis.overall_grade = "A"
    elif score >= 70:
        analysis.overall_grade = "B+"
    elif score >= 60:
        analysis.overall_grade = "B"
    elif score >= 50:
        analysis.overall_grade = "C"
    else:
        analysis.overall_grade = "D"


def _generate_coaching(analysis: InBodyAnalysis, data: InBodyData, gender: str):
    """분석 결과 기반 코칭 메시지를 생성합니다."""
    praise = []
    improve = []
    actions = []

    # 체형 기반
    if analysis.body_shape == "D자형":
        praise.append("골격근이 체지방보다 많은 건강한 D자형 체형입니다.")
    elif analysis.body_shape == "I자형":
        praise.append("균형 잡힌 I자형 체형입니다.")
    elif analysis.body_shape == "C자형":
        improve.append("체지방 비율이 높은 C자형입니다. 유산소 운동과 식이 조절이 필요합니다.")
        actions.append("주 3회 이상 30분 유산소 운동 시작")

    # 체지방률 기반
    if analysis.body_fat_status in ("운동선수", "건강"):
        praise.append(f"체지방률이 '{analysis.body_fat_status}' 수준으로 매우 양호합니다.")
    elif analysis.body_fat_status == "비만":
        improve.append("체지방률이 비만 기준을 초과합니다.")
        actions.append("일일 칼로리 섭취를 TDEE 대비 300~500kcal 줄이기")

    # 내장지방
    if analysis.visceral_fat_risk == "매우양호":
        praise.append(f"내장지방 단면적이 {analysis.vfa_cm2}cm²로 매우 양호합니다.")
    elif analysis.visceral_fat_risk in ("주의", "위험"):
        improve.append(f"내장지방 단면적 {analysis.vfa_cm2}cm²: 관리가 필요합니다.")
        actions.append("정제 탄수화물과 알코올 섭취 줄이기")

    # 근감소증
    if analysis.sarcopenia_risk == "정상":
        praise.append(f"SMI {analysis.smi_value} kg/m²로 근감소증 위험이 없습니다.")
    elif analysis.sarcopenia_risk == "위험":
        improve.append(f"SMI {analysis.smi_value} kg/m²로 근감소증 위험이 있습니다.")
        actions.append("체중 1kg당 단백질 1.2~1.5g 섭취 + 주 3회 근력 운동")

    # 수분 균형
    if analysis.ecw_status == "이상 (부종 가능성)":
        improve.append("세포외수분비가 높아 부종 가능성이 있습니다.")
        actions.append("나트륨 섭취 줄이기, 충분한 수분 섭취")

    # 근육 균형
    if analysis.muscle_balance.get("imbalances"):
        for imb in analysis.muscle_balance["imbalances"]:
            improve.append(imb)
        actions.append("약한 부위 집중 보강 운동 추가")

    # 인바디 점수
    if analysis.inbody_score is not None and analysis.inbody_score >= 80:
        praise.append(f"인바디 점수 {analysis.inbody_score}점으로 우수합니다!")

    # 종합 메시지
    messages = []
    if praise:
        messages.append("잘하고 있는 점: " + " ".join(praise))
    if improve:
        messages.append("개선이 필요한 점: " + " ".join(improve))
    if actions:
        messages.append("추천 행동: " + " / ".join(actions))

    analysis.praise_points = praise
    analysis.improvement_points = improve
    analysis.action_items = actions
    analysis.coaching_messages = messages


def generate_coaching_with_llm(
    analysis: InBodyAnalysis,
    model: str = "exaone3.5",
    ollama_base_url: str = "http://localhost:11434/v1",
) -> str:
    """LLM을 사용하여 자연스러운 코칭 메시지를 생성합니다."""
    from openai import OpenAI

    client = OpenAI(base_url=ollama_base_url, api_key="ollama")

    prompt = f"""당신은 전문 피트니스 코치입니다. 아래 인바디 분석 결과를 보고 따뜻하고 동기부여가 되는 코칭 메시지를 작성해주세요.

분석 결과:
- 체형: {analysis.body_shape} ({analysis.body_shape_description})
- BMI 상태: {analysis.bmi_status}
- 체지방률: {analysis.body_fat_status}
- 종합 판정: {analysis.combined_assessment}
- 내장지방: {analysis.visceral_fat_risk} (VFA {analysis.vfa_cm2}cm²)
- 근감소증: {analysis.sarcopenia_risk} (SMI {analysis.smi_value})
- 인바디 점수: {analysis.inbody_score}/100 ({analysis.overall_grade})
- 잘하는 점: {', '.join(analysis.praise_points)}
- 개선 필요: {', '.join(analysis.improvement_points)}

200자 이내로 한국어 코칭 메시지를 작성하세요. 칭찬으로 시작하고, 구체적인 행동 제안 1~2개를 포함하세요."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content
