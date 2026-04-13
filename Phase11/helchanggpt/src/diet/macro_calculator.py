"""
macro_calculator.py
목표 유형에 따른 탄수화물·단백질·지방 비율과 그램 수를 계산합니다.

참고 기준: 대한비만학회, ACSM, ISSN 가이드라인
"""

from dataclasses import dataclass


@dataclass
class MacroTargets:
    """일일 탄단지 목표"""
    carb_ratio: float       # 탄수화물 비율 (%)
    protein_ratio: float    # 단백질 비율 (%)
    fat_ratio: float        # 지방 비율 (%)
    carb_g: float           # 탄수화물 그램
    protein_g: float        # 단백질 그램
    fat_g: float            # 지방 그램
    total_kcal: int         # 총 칼로리
    description: str = ""   # 비율 설명
    notes: list[str] = None # 제약사항 반영 메모


MACRO_RATIOS = {
    "체지방감소": {
        "carb": 0.40, "protein": 0.35, "fat": 0.25,
        "description": "고단백·저탄수화물로 체지방 감소 + 근손실 방지",
    },
    "근력증가": {
        "carb": 0.45, "protein": 0.30, "fat": 0.25,
        "description": "충분한 단백질 + 탄수화물로 근합성 극대화",
    },
    "체력향상": {
        "carb": 0.50, "protein": 0.25, "fat": 0.25,
        "description": "탄수화물 중심으로 운동 에너지 확보",
    },
    "체중관리": {
        "carb": 0.50, "protein": 0.25, "fat": 0.25,
        "description": "균형 잡힌 영양소 비율로 현 체중 유지",
    },
    "건강개선": {
        "carb": 0.45, "protein": 0.25, "fat": 0.30,
        "description": "복합 탄수화물 + 건강한 지방으로 혈당 관리",
    },
}

CONSTRAINT_ADJUSTMENTS = {
    "당뇨": {"carb": -0.10, "protein": +0.05, "fat": +0.05,
             "note": "탄수화물 비율 낮추고 GI 지수 낮은 식품 권장"},
    "고혈압": {"carb": 0, "protein": 0, "fat": 0,
               "note": "나트륨 하루 2000mg 이하 제한"},
    "고지혈증": {"carb": 0, "protein": 0, "fat": -0.05,
                 "note": "포화지방 줄이고 불포화지방 권장"},
    "신장질환": {"carb": +0.05, "protein": -0.10, "fat": +0.05,
                 "note": "단백질 제한, 칼륨·인 주의"},
}


def calculate_macro_targets(
    total_kcal: int,
    goal_type: str,
    constraints: list[str] | None = None,
    weight_kg: float | None = None,
) -> MacroTargets:
    """
    목표와 제약사항에 따라 탄단지 목표를 계산합니다.

    Args:
        total_kcal: 일일 목표 칼로리
        goal_type: 운동 목표 유형
        constraints: 제약사항 리스트
        weight_kg: 체중 (체중 대비 단백질 보장용)

    Returns:
        MacroTargets
    """
    ratios = MACRO_RATIOS.get(goal_type, MACRO_RATIOS["체중관리"])
    carb_r = ratios["carb"]
    protein_r = ratios["protein"]
    fat_r = ratios["fat"]
    description = ratios["description"]
    notes = []

    # 제약사항 보정
    if constraints:
        for constraint in constraints:
            adj = CONSTRAINT_ADJUSTMENTS.get(constraint)
            if adj:
                carb_r += adj["carb"]
                protein_r += adj["protein"]
                fat_r += adj["fat"]
                notes.append(adj["note"])

        # 비율 합이 1.0 되도록 정규화
        total = carb_r + protein_r + fat_r
        carb_r /= total
        protein_r /= total
        fat_r /= total

    # 그램 계산 (탄 4kcal/g, 단 4kcal/g, 지 9kcal/g)
    carb_g = round((total_kcal * carb_r) / 4, 1)
    protein_g = round((total_kcal * protein_r) / 4, 1)
    fat_g = round((total_kcal * fat_r) / 9, 1)

    # 체중 기반 최소 단백질 보장 (체중 × 1.2g 이상)
    if weight_kg:
        min_protein_g = weight_kg * 1.2
        if protein_g < min_protein_g:
            protein_g = round(min_protein_g, 1)

    return MacroTargets(
        carb_ratio=round(carb_r * 100, 1),
        protein_ratio=round(protein_r * 100, 1),
        fat_ratio=round(fat_r * 100, 1),
        carb_g=carb_g,
        protein_g=protein_g,
        fat_g=fat_g,
        total_kcal=total_kcal,
        description=description,
        notes=notes or None,
    )
