# 🍱 승(承) — 뭘 먹지? | 구현 가이드라인

## 📌 개요

이 문서는 **헬창지피티(HelChangGPT)** 프로젝트의 **2단계: AI 맞춤 식단 생성** 구현을 위한
구현 가이드라인입니다.

1단계에서 생성된 `UserProfile`을 입력받아, 사용자의 목표·신체 조건·제약사항에 맞는
**일일 식단을 LLM으로 생성**하고, **NLP 모델로 영양소를 분석·요약**하여 제공합니다.

---

## 1. 1단계(기)로부터 받는 입력

```python
# 1단계 UserProfile에서 2단계가 사용하는 핵심 필드

STAGE2_INPUT = {
    # ── 칼로리 기준 ──
    "recommended_intake_kcal": 1397,   # 권장 섭취 칼로리 (인바디 or 자동계산)
    "tdee_kcal": 1697,                 # TDEE (자동계산)
    "bmr_kcal": 1168,                  # 기초대사량
    
    # ── 목표 정보 ──
    "goal_type": "체지방감소",           # 목표 유형
    "goal_keywords": ["체지방", "근육"], # 핵심 키워드
    
    # ── 신체 정보 ──
    "weight_kg": 59.1,
    "height_cm": 156.9,
    "age": 51,
    "gender": "여성",
    "body_fat_percent": 37.5,
    
    # ── 제약사항 ──
    "constraints": ["당뇨"],            # 질환/부상 제약
    
    # ── 인바디 권장 ──
    "fat_adjustment_kg": -10.0,         # 지방 조절 목표
    "muscle_adjustment_kg": 3.8,        # 근육 조절 목표
    "priority": "지방감량우선",
}
```

---

## 2. 출력 데이터 구조

2단계의 최종 출력은 **일일 식단 + 영양 분석 JSON** 입니다.

```python
MEAL_PLAN_SCHEMA = {
    # ── 식단 메타 정보 ──
    "meta": {
        "target_kcal": int,              # 목표 칼로리
        "target_macros": {               # 목표 탄단지 비율
            "carb_ratio": float,         # 탄수화물 비율 (%)
            "protein_ratio": float,      # 단백질 비율 (%)
            "fat_ratio": float,          # 지방 비율 (%)
        },
        "goal_type": str,
        "model_used": str,               # 사용한 LLM 모델
        "temperature": float,            # 사용한 temperature
        "generated_at": str,
    },
    
    # ── 끼니별 식단 ──
    "meals": {
        "breakfast": {
            "menu_name": str,            # 식단명 (예: "고단백 그릭요거트볼")
            "foods": [
                {
                    "name": str,         # 음식명
                    "amount": str,       # 양 (예: "200g", "1개")
                    "calories_kcal": int,
                    "carb_g": float,
                    "protein_g": float,
                    "fat_g": float,
                    "sodium_mg": float,   # 나트륨 (선택)
                    "fiber_g": float,     # 식이섬유 (선택)
                }
            ],
            "subtotal": {
                "calories_kcal": int,
                "carb_g": float,
                "protein_g": float,
                "fat_g": float,
            },
            "tip": str,                  # 식사 팁 (예: "운동 1시간 전 섭취 권장")
        },
        "lunch": { ... },               # 동일 구조
        "dinner": { ... },              # 동일 구조
        "snack": { ... },               # 간식 (선택)
    },
    
    # ── 일일 총계 ──
    "daily_total": {
        "calories_kcal": int,
        "carb_g": float,
        "protein_g": float,
        "fat_g": float,
        "actual_macros": {
            "carb_ratio": float,
            "protein_ratio": float,
            "fat_ratio": float,
        },
    },
    
    # ── NLP 분석 결과 ──
    "nlp_analysis": {
        "summary": str,                  # 식단 요약 (mT5/BART)
        "keywords": list,                # 핵심 영양 키워드 (KeyBERT)
        "warnings": list,                # 주의사항 (제약 충돌 등)
    },
}
```

---

## 3. 목표별 탄단지 비율 설계

```python
"""
macro_calculator.py
목표 유형에 따른 탄수화물·단백질·지방 비율과 그램 수를 계산합니다.
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


# ── 목표별 권장 탄단지 비율 ──
# 참고: 대한비만학회, ACSM, ISSN 가이드라인 기반

MACRO_RATIOS = {
    "체지방감소": {
        "carb": 0.40,      # 탄수화물 40%
        "protein": 0.35,   # 단백질 35% (근손실 방지)
        "fat": 0.25,       # 지방 25%
        "description": "고단백·저탄수화물로 체지방 감소 + 근손실 방지",
    },
    "근력증가": {
        "carb": 0.45,      # 탄수화물 45% (운동 에너지)
        "protein": 0.30,   # 단백질 30% (근합성)
        "fat": 0.25,       # 지방 25%
        "description": "충분한 단백질 + 탄수화물로 근합성 극대화",
    },
    "체력향상": {
        "carb": 0.50,      # 탄수화물 50% (지구력 에너지)
        "protein": 0.25,   # 단백질 25%
        "fat": 0.25,       # 지방 25%
        "description": "탄수화물 중심으로 운동 에너지 확보",
    },
    "체중관리": {
        "carb": 0.50,      # 균형 잡힌 비율
        "protein": 0.25,
        "fat": 0.25,
        "description": "균형 잡힌 영양소 비율로 현 체중 유지",
    },
    "건강개선": {
        "carb": 0.45,      # 정제 탄수화물 줄이고 복합 탄수화물 중심
        "protein": 0.25,
        "fat": 0.30,       # 건강한 지방 비율 높임
        "description": "복합 탄수화물 + 건강한 지방으로 혈당 관리",
    },
}

# ── 제약사항에 따른 비율 보정 ──
CONSTRAINT_ADJUSTMENTS = {
    "당뇨": {"carb": -0.10, "protein": +0.05, "fat": +0.05,
             "note": "탄수화물 비율 낮추고 GI 지수 낮은 식품 권장"},
    "고혈압": {"carb": 0, "protein": 0, "fat": 0,
               "note": "나트륨 하루 2000mg 이하 제한"},
    "신장질환": {"carb": +0.05, "protein": -0.10, "fat": +0.05,
                 "note": "단백질 제한, 칼륨·인 주의"},
}


def calculate_macro_targets(
    total_kcal: int,
    goal_type: str,
    constraints: list[str] = None,
    weight_kg: float = None,
) -> MacroTargets:
    """
    목표와 제약사항에 따라 탄단지 목표를 계산합니다.
    
    Args:
        total_kcal: 일일 목표 칼로리
        goal_type: 운동 목표 유형
        constraints: 제약사항 리스트
        weight_kg: 체중 (체중 대비 단백질 계산용)
    """
    ratios = MACRO_RATIOS.get(goal_type, MACRO_RATIOS["체중관리"])
    carb_r = ratios["carb"]
    protein_r = ratios["protein"]
    fat_r = ratios["fat"]
    
    # 제약사항 보정 적용
    if constraints:
        for constraint in constraints:
            adj = CONSTRAINT_ADJUSTMENTS.get(constraint)
            if adj:
                carb_r += adj["carb"]
                protein_r += adj["protein"]
                fat_r += adj["fat"]
        
        # 비율 합이 1.0 되도록 정규화
        total = carb_r + protein_r + fat_r
        carb_r /= total
        protein_r /= total
        fat_r /= total
    
    # 그램 계산 (탄수화물 4kcal/g, 단백질 4kcal/g, 지방 9kcal/g)
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
    )
```

---

## 4. 영양성분 데이터베이스 연동

### 4-1. 식약처 공공 API 연동

```python
"""
nutrition_db.py
식품의약품안전처 식품영양성분 DB API를 연동합니다.

API 정보:
  - 포털: https://www.data.go.kr/data/15127578/openapi.do
  - 제공: 식품명, 에너지(kcal), 탄수화물(g), 단백질(g), 지방(g),
          나트륨(mg), 식이섬유(g), 1회섭취참고량 등
  - 형식: XML / JSON
  - 인증: 공공데이터포털 API 키 필요

DB 대안 (오프라인):
  - 식품영양성분DB 통합 자료집 (XLSX, 548품목)
  - URL: https://www.data.go.kr/data/15047698/fileData.do
"""

import requests
import pandas as pd
from functools import lru_cache


# ── API 설정 ──
FOOD_API_BASE = "http://apis.data.go.kr/1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01"


@lru_cache(maxsize=500)
def search_food_nutrition(food_name: str, api_key: str) -> list[dict]:
    """
    식품명으로 영양성분을 검색합니다.
    
    Args:
        food_name: 검색할 음식명 (예: "닭가슴살", "현미밥")
        api_key: 공공데이터포털 API 인증키
    
    Returns:
        [{"name": "닭가슴살구이", "kcal": 165, "carb_g": 0, 
          "protein_g": 31, "fat_g": 3.6, ...}, ...]
    """
    params = {
        "serviceKey": api_key,
        "FOOD_NM_KR": food_name,
        "pageNo": 1,
        "numOfRows": 5,
        "type": "json",
    }
    
    resp = requests.get(FOOD_API_BASE, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    
    items = data.get("body", {}).get("items", [])
    results = []
    for item in items:
        results.append({
            "name": item.get("FOOD_NM_KR", ""),
            "category": item.get("FOOD_CAT1_NM", ""),
            "serving_size": item.get("SERVING_SIZE", ""),
            "kcal": _to_float(item.get("AMT_NUM1", 0)),
            "carb_g": _to_float(item.get("AMT_NUM7", 0)),
            "protein_g": _to_float(item.get("AMT_NUM3", 0)),
            "fat_g": _to_float(item.get("AMT_NUM4", 0)),
            "sodium_mg": _to_float(item.get("AMT_NUM14", 0)),
            "fiber_g": _to_float(item.get("AMT_NUM8", 0)),
            "sugar_g": _to_float(item.get("AMT_NUM9", 0)),
        })
    
    return results


def _to_float(val) -> float:
    """문자열을 float로 변환합니다."""
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0


# ── 오프라인 DB (CSV 로드) ──

def load_nutrition_csv(csv_path: str) -> pd.DataFrame:
    """
    식약처 영양성분 통합 자료집 CSV를 로드합니다.
    
    사전 다운로드 필요:
    https://www.data.go.kr/data/15047698/fileData.do
    
    컬럼 매핑:
      식품명 → name
      에너지(kcal) → kcal
      탄수화물(g) → carb_g
      단백질(g) → protein_g
      지방(g) → fat_g
      나트륨(mg) → sodium_mg
    """
    df = pd.read_csv(csv_path, encoding="utf-8")
    
    column_map = {
        "식품명": "name",
        "에너지(kcal)": "kcal",
        "탄수화물(g)": "carb_g",
        "단백질(g)": "protein_g",
        "지방(g)": "fat_g",
        "나트륨(mg)": "sodium_mg",
        "식이섬유(g)": "fiber_g",
        "당류(g)": "sugar_g",
        "1회섭취참고량": "serving_size",
    }
    
    df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
    return df


def search_nutrition_offline(df: pd.DataFrame, food_name: str, top_n: int = 3) -> list[dict]:
    """오프라인 DB에서 음식 영양성분을 검색합니다."""
    matches = df[df["name"].str.contains(food_name, case=False, na=False)]
    return matches.head(top_n).to_dict("records")
```

### 4-2. 자주 사용되는 음식 기본 DB

```python
"""
common_foods.py
API 호출 없이 빠르게 참조할 수 있는 한국 대표 음식 영양 정보입니다.
LLM 프롬프트에 포함하거나, 생성 결과 검증에 사용합니다.
"""

COMMON_FOODS_DB = {
    # ── 탄수화물 (밥·면·빵) ──
    "현미밥 1공기": {"kcal": 330, "carb_g": 68, "protein_g": 7, "fat_g": 2.5},
    "백미밥 1공기": {"kcal": 310, "carb_g": 69, "protein_g": 5, "fat_g": 0.8},
    "고구마 1개(150g)": {"kcal": 190, "carb_g": 44, "protein_g": 2, "fat_g": 0.2},
    "통밀빵 1쪽": {"kcal": 80, "carb_g": 14, "protein_g": 4, "fat_g": 1},
    "오트밀 40g": {"kcal": 150, "carb_g": 27, "protein_g": 5, "fat_g": 2.5},
    
    # ── 단백질 (육류·어류·계란) ──
    "닭가슴살 100g": {"kcal": 165, "carb_g": 0, "protein_g": 31, "fat_g": 3.6},
    "소고기 안심 100g": {"kcal": 190, "carb_g": 0, "protein_g": 28, "fat_g": 8},
    "연어 100g": {"kcal": 208, "carb_g": 0, "protein_g": 20, "fat_g": 13},
    "계란 1개": {"kcal": 72, "carb_g": 0.4, "protein_g": 6.3, "fat_g": 5},
    "두부 반모(150g)": {"kcal": 130, "carb_g": 4, "protein_g": 13, "fat_g": 7},
    "그릭요거트 150g": {"kcal": 130, "carb_g": 6, "protein_g": 17, "fat_g": 4},
    
    # ── 채소·과일 ──
    "브로콜리 100g": {"kcal": 34, "carb_g": 7, "protein_g": 2.8, "fat_g": 0.4},
    "시금치 100g": {"kcal": 23, "carb_g": 3.6, "protein_g": 2.9, "fat_g": 0.4},
    "바나나 1개": {"kcal": 93, "carb_g": 24, "protein_g": 1, "fat_g": 0.3},
    "사과 1개": {"kcal": 95, "carb_g": 25, "protein_g": 0.5, "fat_g": 0.3},
    "아보카도 반개": {"kcal": 120, "carb_g": 6, "protein_g": 1.5, "fat_g": 11},
    
    # ── 건강한 지방 ──
    "아몬드 20g": {"kcal": 116, "carb_g": 4, "protein_g": 4, "fat_g": 10},
    "올리브오일 1큰술": {"kcal": 120, "carb_g": 0, "protein_g": 0, "fat_g": 14},
}
```

---

## 5. LLM 기반 식단 생성

### 5-1. 프롬프트 설계

```python
"""
diet_prompts.py
식단 생성을 위한 LLM 프롬프트 템플릿입니다.
Zero-shot, Few-shot, CoT(Chain-of-Thought) 3가지 방식을 비교합니다.
"""

# ══════════════════════════════════════
# 방식 1: Zero-shot 프롬프트
# ══════════════════════════════════════

ZERO_SHOT_PROMPT = """
당신은 스포츠 영양학 전문가입니다.

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
}}
"""


# ══════════════════════════════════════
# 방식 2: Few-shot 프롬프트
# ══════════════════════════════════════

FEW_SHOT_PROMPT = """
당신은 스포츠 영양학 전문가입니다.
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
        {{"name": "닭가슴살 구이", "amount": "150g", "calories_kcal": 248, "carb_g": 0, "protein_g": 47, "fat_g": 5.4}},
        {{"name": "브로콜리", "amount": "100g", "calories_kcal": 34, "carb_g": 7, "protein_g": 2.8, "fat_g": 0.4}},
        {{"name": "방울토마토", "amount": "80g", "calories_kcal": 14, "carb_g": 3, "protein_g": 0.7, "fat_g": 0.2}}
      ],
      "tip": "단백질 흡수를 위해 천천히 씹어 드세요"
    }},
    "dinner": {{ ... }},
    "snack": {{ ... }}
  }}
}}

[예시 2 - 건강개선 목표, 여성, 1400kcal, 당뇨 제약]
입력: 50세 여성, 157cm 59kg, 체지방률 37%, 목표: 건강개선, 1400kcal, 탄35/단30/지35, 제약: 당뇨
출력:
{{
  "meals": {{
    "breakfast": {{
      "menu_name": "저GI 두부 스크램블",
      "foods": [
        {{"name": "두부 스크램블", "amount": "두부 150g + 계란 1개", "calories_kcal": 202, "carb_g": 4, "protein_g": 19, "fat_g": 12}},
        {{"name": "통밀빵", "amount": "1쪽", "calories_kcal": 80, "carb_g": 14, "protein_g": 4, "fat_g": 1}},
        {{"name": "무가당 두유", "amount": "200ml", "calories_kcal": 70, "carb_g": 3, "protein_g": 7, "fat_g": 3.5}}
      ],
      "tip": "혈당 급상승을 막기 위해 단백질을 먼저 섭취하세요"
    }},
    ...
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

JSON 형식으로만 응답하세요.
"""


# ══════════════════════════════════════
# 방식 3: Chain-of-Thought 프롬프트
# ══════════════════════════════════════

COT_PROMPT = """
당신은 스포츠 영양학 전문가입니다.
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
- 이 사용자의 핵심 니즈가 무엇인지 파악하세요.
- 제약사항이 식단에 어떤 영향을 미치는지 분석하세요.

Step 2) 끼니별 칼로리 배분 계획
- 아침:점심:저녁:간식 비율을 정하세요. (일반적으로 25:35:30:10)
- 각 끼니의 목표 칼로리와 탄단지를 계산하세요.

Step 3) 음식 선택 기준 설정
- 제약사항을 고려한 피해야 할 식품과 권장 식품을 나열하세요.
- 한국인 식습관에 맞는 현실적인 음식을 선택하세요.

Step 4) 식단 구성 및 영양소 계산
- 각 끼니의 음식을 구체적으로 정하고, 정확한 영양소를 계산하세요.

Step 5) 검증
- 일일 총 칼로리가 목표 ±50kcal 이내인지 확인하세요.
- 탄단지 비율이 목표와 ±5% 이내인지 확인하세요.
- 제약사항에 위배되는 음식이 없는지 확인하세요.

추론 과정을 먼저 보여준 뒤, 마지막에 "```json"과 "```" 사이에 최종 식단 JSON을 넣어주세요.
JSON 구조는 아래와 같습니다:
{{
  "reasoning": "<추론 과정 요약>",
  "meals": {{
    "breakfast": {{ "menu_name": "...", "foods": [...], "tip": "..." }},
    "lunch": {{ ... }},
    "dinner": {{ ... }},
    "snack": {{ ... }}
  }}
}}
"""
```

### 5-2. LLM 호출 및 비교

```python
"""
diet_generator.py
식단을 생성하고, 모델별 · 프롬프트별 · 파라미터별 결과를 비교합니다.
"""

import json
import time
from openai import OpenAI
from dataclasses import dataclass


@dataclass
class GenerationResult:
    """LLM 식단 생성 결과"""
    meal_plan: dict
    model: str
    prompt_type: str          # "zero_shot" | "few_shot" | "cot"
    temperature: float
    latency_sec: float
    input_tokens: int
    output_tokens: int


def generate_diet_plan(
    user_profile: dict,
    macro_targets: "MacroTargets",
    model: str = "gpt-4o",
    prompt_type: str = "few_shot",
    temperature: float = 0.7,
    api_key: str = None,
) -> GenerationResult:
    """
    LLM으로 식단을 생성합니다.
    
    Args:
        user_profile: 1단계 UserProfile
        macro_targets: 탄단지 목표
        model: "gpt-4o" | "exaone-3.5" 등
        prompt_type: "zero_shot" | "few_shot" | "cot"
        temperature: 생성 temperature
        api_key: API 키
    """
    # 프롬프트 선택
    prompt_map = {
        "zero_shot": ZERO_SHOT_PROMPT,
        "few_shot": FEW_SHOT_PROMPT,
        "cot": COT_PROMPT,
    }
    template = prompt_map[prompt_type]
    
    # 프롬프트 변수 채우기
    prompt = template.format(
        gender=user_profile["basic"]["gender"],
        age=user_profile["basic"]["age"],
        height_cm=user_profile["basic"]["height_cm"],
        weight_kg=user_profile["basic"]["weight_kg"],
        body_fat_percent=user_profile.get("body_composition", {}).get("body_fat_percent", "미측정"),
        goal_type=user_profile["nlp_analysis"]["goal_type"],
        constraints=", ".join(user_profile["nlp_analysis"]["constraints"]) or "없음",
        target_kcal=macro_targets.total_kcal,
        carb_ratio=macro_targets.carb_ratio,
        protein_ratio=macro_targets.protein_ratio,
        fat_ratio=macro_targets.fat_ratio,
        carb_g=macro_targets.carb_g,
        protein_g=macro_targets.protein_g,
        fat_g=macro_targets.fat_g,
    )
    
    # LLM 호출
    client = OpenAI(api_key=api_key)
    start = time.time()
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=3000,
    )
    
    latency = time.time() - start
    content = response.choices[0].message.content
    
    # JSON 추출
    meal_plan = _extract_json(content)
    
    return GenerationResult(
        meal_plan=meal_plan,
        model=model,
        prompt_type=prompt_type,
        temperature=temperature,
        latency_sec=round(latency, 2),
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )


def _extract_json(text: str) -> dict:
    """LLM 응답에서 JSON을 추출합니다."""
    text = text.strip()
    
    # 코드블록 내부 JSON 추출
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    return json.loads(text.strip())


# ══════════════════════════════════════
# 비교 실험 실행기
# ══════════════════════════════════════

def run_comparison_experiment(
    user_profile: dict,
    macro_targets: "MacroTargets",
    api_keys: dict,
) -> list[GenerationResult]:
    """
    모델 · 프롬프트 · temperature 조합별 식단 생성 비교 실험을 수행합니다.
    
    실험 매트릭스:
    - 모델: ["gpt-4o", "exaone-3.5"]
    - 프롬프트: ["zero_shot", "few_shot", "cot"]
    - temperature: [0.3, 0.7, 1.0]
    총 2 × 3 × 3 = 18가지 조합
    """
    results = []
    
    experiments = [
        # (model, prompt_type, temperature)
        ("gpt-4o", "zero_shot", 0.3),
        ("gpt-4o", "zero_shot", 0.7),
        ("gpt-4o", "zero_shot", 1.0),
        ("gpt-4o", "few_shot", 0.3),
        ("gpt-4o", "few_shot", 0.7),
        ("gpt-4o", "few_shot", 1.0),
        ("gpt-4o", "cot", 0.3),
        ("gpt-4o", "cot", 0.7),
        ("gpt-4o", "cot", 1.0),
        # EXAONE도 동일하게 반복
    ]
    
    for model, prompt_type, temp in experiments:
        try:
            result = generate_diet_plan(
                user_profile=user_profile,
                macro_targets=macro_targets,
                model=model,
                prompt_type=prompt_type,
                temperature=temp,
                api_key=api_keys.get(model),
            )
            results.append(result)
            print(f"[OK] {model} / {prompt_type} / temp={temp} ({result.latency_sec}s)")
        except Exception as e:
            print(f"[ERR] {model} / {prompt_type} / temp={temp}: {e}")
    
    return results
```

---

## 6. NLP 분석 모듈

### 6-1. 영양소 키워드 추출

```python
"""
nutrition_keyword_extractor.py
생성된 식단에서 핵심 영양 키워드를 추출합니다.
"""

from keybert import KeyBERT


NUTRITION_STOPWORDS = ["식단", "식사", "끼니", "음식", "먹다", "섭취", "하루"]


def extract_nutrition_keywords(meal_plan_text: str, top_n: int = 8) -> list[tuple[str, float]]:
    """
    식단 텍스트에서 핵심 영양 키워드를 추출합니다.
    
    예시 출력:
        [("고단백", 0.85), ("저탄수화물", 0.79), ("닭가슴살", 0.72),
         ("현미", 0.68), ("식이섬유", 0.65), ...]
    """
    kw_model = KeyBERT("paraphrase-multilingual-MiniLM-L12-v2")
    
    keywords = kw_model.extract_keywords(
        meal_plan_text,
        keyphrase_ngram_range=(1, 2),
        top_n=top_n,
        use_mmr=True,
        diversity=0.5,
    )
    
    # 영양 무관 키워드 필터링
    filtered = [(kw, score) for kw, score in keywords if kw not in NUTRITION_STOPWORDS]
    return filtered
```

### 6-2. 식단 요약 (mT5 / BART)

```python
"""
diet_summarizer.py
생성된 식단을 NLP 모델로 요약합니다.
mT5와 BART 두 모델의 결과를 비교합니다.
"""

from transformers import pipeline


def summarize_diet_with_mt5(diet_text: str) -> str:
    """
    mT5로 식단을 요약합니다.
    
    입력 예시:
        "아침: 오트밀 40g(150kcal) + 그릭요거트 150g(130kcal) + 블루베리 50g(29kcal).
         점심: 현미밥 2/3공기(220kcal) + 닭가슴살 구이 150g(248kcal) + 브로콜리 100g(34kcal).
         저녁: 연어 스테이크 120g(250kcal) + 고구마 100g(127kcal) + 샐러드(50kcal).
         간식: 아몬드 20g(116kcal) + 사과 1개(95kcal)."
         
    출력 예시:
        "하루 총 1449kcal의 고단백 저탄수화물 식단입니다. 
         단백질 위주의 닭가슴살과 연어를 중심으로 구성했으며, 
         복합 탄수화물인 현미와 고구마로 에너지를 보충합니다."
    """
    summarizer = pipeline(
        "summarization",
        model="google/mt5-base",
        tokenizer="google/mt5-base",
    )
    
    result = summarizer(
        diet_text,
        max_length=100,
        min_length=30,
        do_sample=False,
    )
    
    return result[0]["summary_text"]


def summarize_diet_with_bart(diet_text: str) -> str:
    """BART로 식단을 요약합니다. (비교 대상)"""
    summarizer = pipeline(
        "summarization",
        model="facebook/mbart-large-cc25",  # 또는 한국어 BART
        tokenizer="facebook/mbart-large-cc25",
    )
    
    result = summarizer(
        diet_text,
        max_length=100,
        min_length=30,
        do_sample=False,
    )
    
    return result[0]["summary_text"]


def summarize_diet_with_llm(diet_text: str, client, model: str = "gpt-4o") -> str:
    """LLM으로 식단을 요약합니다. (비교 대상)"""
    prompt = f"""
아래 식단을 2~3문장으로 요약해주세요. 
총 칼로리, 주요 영양 전략, 핵심 식재료를 포함해주세요.

식단:
{diet_text}

요약:
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()
```

### 6-3. 식단 검증 및 경고 생성

```python
"""
diet_validator.py
생성된 식단의 영양소가 목표에 부합하는지 검증하고 경고를 생성합니다.
"""


def validate_meal_plan(meal_plan: dict, macro_targets: "MacroTargets", constraints: list) -> dict:
    """
    식단을 검증하고 경고/피드백을 생성합니다.
    
    Returns:
        {
            "is_valid": True/False,
            "score": 85,          # 0~100 적합도 점수
            "warnings": [...],    # 경고 메시지 목록
            "suggestions": [...], # 개선 제안
        }
    """
    warnings = []
    suggestions = []
    score = 100
    
    # 일일 총 영양소 계산
    total = {"kcal": 0, "carb_g": 0, "protein_g": 0, "fat_g": 0}
    for meal_key in ["breakfast", "lunch", "dinner", "snack"]:
        meal = meal_plan.get("meals", {}).get(meal_key, {})
        for food in meal.get("foods", []):
            total["kcal"] += food.get("calories_kcal", 0)
            total["carb_g"] += food.get("carb_g", 0)
            total["protein_g"] += food.get("protein_g", 0)
            total["fat_g"] += food.get("fat_g", 0)
    
    # 1) 칼로리 검증 (±10% 허용)
    kcal_diff = abs(total["kcal"] - macro_targets.total_kcal)
    kcal_tolerance = macro_targets.total_kcal * 0.10
    if kcal_diff > kcal_tolerance:
        warnings.append(
            f"총 칼로리({total['kcal']}kcal)가 목표({macro_targets.total_kcal}kcal)와 "
            f"{kcal_diff}kcal 차이납니다"
        )
        score -= 15
    
    # 2) 탄단지 비율 검증
    total_macro_kcal = (total["carb_g"] * 4) + (total["protein_g"] * 4) + (total["fat_g"] * 9)
    if total_macro_kcal > 0:
        actual_carb_r = (total["carb_g"] * 4 / total_macro_kcal) * 100
        actual_protein_r = (total["protein_g"] * 4 / total_macro_kcal) * 100
        actual_fat_r = (total["fat_g"] * 9 / total_macro_kcal) * 100
        
        if abs(actual_protein_r - macro_targets.protein_ratio) > 10:
            warnings.append(
                f"단백질 비율({actual_protein_r:.0f}%)이 목표({macro_targets.protein_ratio}%)와 크게 다릅니다"
            )
            score -= 10
    
    # 3) 제약사항 위반 검증
    constraint_violations = _check_constraint_violations(meal_plan, constraints)
    if constraint_violations:
        warnings.extend(constraint_violations)
        score -= 20
    
    # 4) 최소 단백질 검증 (체중 × 1.0g 이상)
    if total["protein_g"] < 40:
        warnings.append(f"단백질({total['protein_g']}g)이 부족합니다. 최소 50g 이상 권장합니다")
        score -= 10
    
    # 5) 끼니 수 검증
    meal_count = sum(1 for k in ["breakfast", "lunch", "dinner"]
                     if meal_plan.get("meals", {}).get(k, {}).get("foods"))
    if meal_count < 3:
        warnings.append("3끼 식사가 모두 포함되지 않았습니다")
        score -= 10
    
    return {
        "is_valid": score >= 60,
        "score": max(0, score),
        "total_nutrients": total,
        "warnings": warnings,
        "suggestions": suggestions,
    }


# ── 제약사항별 금지 식품 목록 ──
CONSTRAINT_FORBIDDEN_FOODS = {
    "당뇨": ["설탕", "백미밥", "흰빵", "케이크", "사탕", "콜라", "주스", "떡", "과자"],
    "고혈압": ["라면", "짜장면", "김치찌개", "젓갈", "장아찌", "햄", "소시지"],
    "신장질환": ["바나나", "감자", "토마토", "시금치", "아몬드"],  # 칼륨 주의
}


def _check_constraint_violations(meal_plan: dict, constraints: list) -> list[str]:
    """제약사항에 위배되는 음식이 있는지 검사합니다."""
    violations = []
    
    all_food_names = []
    for meal_key in ["breakfast", "lunch", "dinner", "snack"]:
        meal = meal_plan.get("meals", {}).get(meal_key, {})
        for food in meal.get("foods", []):
            all_food_names.append(food.get("name", ""))
    
    for constraint in constraints:
        forbidden = CONSTRAINT_FORBIDDEN_FOODS.get(constraint, [])
        for food_name in all_food_names:
            for forbidden_food in forbidden:
                if forbidden_food in food_name:
                    violations.append(
                        f"[{constraint} 제약] '{food_name}'은(는) 권장되지 않는 식품입니다"
                    )
    
    return violations
```

---

## 7. React 프론트엔드 가이드

### 7-1. 식단 추천 페이지 컴포넌트 구조

```
DietPage/
├── DietHeader               ← 목표 칼로리 · 탄단지 비율 요약 바
│   └── MacroProgressBar     ← 탄단지 목표 대비 진행률
├── MealCard (×4)            ← 아침/점심/저녁/간식 카드
│   ├── MealTitle            ← 식단명 + 칼로리
│   ├── FoodList             ← 음식 리스트 (이름, 양, 영양소)
│   └── MealTip              ← 식사 팁
├── DailyTotalCard           ← 일일 총계 + 도넛 차트
├── NutritionAnalysis        ← NLP 분석 결과
│   ├── DietSummary          ← mT5/BART 요약 텍스트
│   ├── KeywordTags          ← KeyBERT 키워드 태그
│   └── WarningBanner        ← 검증 경고 메시지
├── RegenerateButton         ← 다른 식단 생성 버튼
└── ModelComparisonPanel     ← LLM/프롬프트/temperature 비교 패널
    ├── ComparisonSelector   ← 비교 조건 선택
    └── SideBySideView       ← 좌우 비교 뷰
```

### 7-2. API 엔드포인트

```
POST /api/v1/diet/generate
  - Body: { 
      "user_profile": {...},       # 1단계 프로필
      "model": "gpt-4o",
      "prompt_type": "few_shot",
      "temperature": 0.7
    }
  - Response: MealPlan JSON

POST /api/v1/diet/validate
  - Body: { "meal_plan": {...}, "macro_targets": {...}, "constraints": [...] }
  - Response: ValidationResult JSON

POST /api/v1/diet/analyze
  - Body: { "meal_plan": {...} }
  - Response: { "summary": "...", "keywords": [...], "warnings": [...] }

GET  /api/v1/nutrition/search?food_name=닭가슴살
  - Response: [{ "name": "...", "kcal": ..., "carb_g": ..., ... }]

POST /api/v1/diet/compare
  - Body: { "user_profile": {...}, "experiments": [...] }
  - Response: [GenerationResult, ...]
```

---

## 8. 비교 실험 설계

### 8-1. 실험 매트릭스

| 실험 축 | 비교 대상 | 평가 지표 |
|---------|---------|---------|
| **모델** | OpenAI GPT-4o vs EXAONE 3.5 | 영양소 정확도, 실용성, 응답 속도 |
| **프롬프트** | Zero-shot vs Few-shot vs CoT | 형식 준수율, 영양소 정확도, 다양성 |
| **temperature** | 0.3 vs 0.7 vs 1.0 | 메뉴 다양성, 칼로리 정확도, 현실성 |
| **요약 모델** | mT5 vs BART vs LLM 요약 | ROUGE 스코어, 핵심 정보 포함률 |

### 8-2. 평가 지표 계산

```python
"""
diet_evaluation.py
식단 생성 품질을 정량적으로 평가합니다.
"""


def evaluate_diet_quality(result: "GenerationResult", macro_targets: "MacroTargets") -> dict:
    """
    식단 생성 품질을 평가합니다.
    
    평가 항목:
    1. 칼로리 정확도 (목표 대비 오차율)
    2. 탄단지 비율 정확도
    3. 형식 준수율 (JSON 파싱 성공 여부)
    4. 메뉴 다양성 (고유 식재료 수)
    5. 현실성 (한국 식품 포함률)
    6. 응답 속도
    """
    plan = result.meal_plan
    
    # 1) 칼로리 정확도
    total_kcal = sum(
        food.get("calories_kcal", 0)
        for meal in plan.get("meals", {}).values()
        for food in meal.get("foods", [])
    )
    kcal_error_rate = abs(total_kcal - macro_targets.total_kcal) / macro_targets.total_kcal
    kcal_accuracy = max(0, 1 - kcal_error_rate) * 100
    
    # 2) 메뉴 다양성
    all_foods = [
        food.get("name", "")
        for meal in plan.get("meals", {}).values()
        for food in meal.get("foods", [])
    ]
    unique_foods = len(set(all_foods))
    
    # 3) 끼니 완성도
    meal_completeness = sum(
        1 for key in ["breakfast", "lunch", "dinner"]
        if plan.get("meals", {}).get(key, {}).get("foods")
    ) / 3 * 100
    
    return {
        "kcal_accuracy": round(kcal_accuracy, 1),
        "total_kcal_generated": total_kcal,
        "unique_foods_count": unique_foods,
        "meal_completeness": round(meal_completeness, 1),
        "latency_sec": result.latency_sec,
        "model": result.model,
        "prompt_type": result.prompt_type,
        "temperature": result.temperature,
    }
```

---

## 9. 3단계(운동)로의 연결

2단계에서 생성된 식단 정보는 3단계(운동 루틴)에서 다음과 같이 활용됩니다.

```
승(承) 식단 출력
    │
    ├──▶ 전(轉) 운동 루틴
    │    ├─ 식단 칼로리 기반 운동 강도 결정
    │    ├─ 탄수화물 섭취량 기반 유산소/무산소 비율 조정
    │    └─ 식사 시간 기반 운동 시간대 추천
    │
    └──▶ 결(結) 피드백
         └─ 식단 준수율 + 운동 일지 → 종합 피드백
```

---

## 10. 체크리스트 (v1.1 현황)

### 필수 구현

- [x] 목표별 탄단지 비율 계산 ✅ `macro_calculator.py` (5목표 × 4제약사항 보정)
- [x] 제약사항 반영 비율 보정 ✅ 당뇨/고혈압/고지혈증/신장질환
- [x] LLM 식단 생성 (EXAONE 3.5) ✅ `diet_generator.py`
- [x] LLM 식단 생성 (Qwen 3.5) ✅ 다국어 비교
- [x] Zero-shot / Few-shot / CoT / Scheduled 프롬프트 4종 ✅ `diet_prompts.py`
- [x] 식단 JSON 파싱 및 검증 ✅ `diet_analyzer.py`
- [x] 영양소 키워드 추출 (KeyBERT) ✅ `diet_analyzer.py`
- [x] 제약사항 위반 검사 ✅ 칼로리/탄수화물/나트륨 제한
- [x] React 식단 추천 페이지 UI ✅ 3탭 (AI대화 + 식단보기 + 저장이력)
- [x] AI 영양사 챗봇 ✅ `DietChatPanel` — 대화하며 식단 생성/수정
- [x] 3일치 식단 + 대체 음식 생성 ✅ `/api/v1/diet/generate-multiday`
- [x] 알레르기 10종 + 제외 식품 6종 토글 ✅
- [x] 식단 저장/조회/삭제 API ✅ `/api/v1/diet/save`, `history`, `delete`
- [x] 식단 사이드 미리보기 (탭 전환 없이 3일치 확인) ✅ `DietQuickPreview`
- [x] 페이지 새로고침 시 최근 식단 자동 복원 ✅

### 비교 분석

- [x] Zero-shot vs Few-shot vs CoT 비교 ✅ Few-shot 채택
- [x] temperature (0.3 / 0.7 / 1.0) 비교 ✅ 0.7 기본값
- [x] 영양소 정확도 정량 평가 ✅ `experiment_results.json`
- [ ] EXAONE vs Qwen 식단 품질 정량 비교

### 고도화 (선택)

- [x] 6가지 일정 변동 자동 대응 ✅ `diet_adjuster.py` (야근/회식/아침건너뜀 등)
- [x] 시간대별 끼니 배정 (운동 전후 간식) ✅ `meal_scheduler.py`
- [x] 외식/회식 칼로리 추정 DB (21종) ✅ `eating_out_db.py`
- [x] 3일치 식단 생성 ✅ (7일치는 향후)
- [x] 식품안전나라 API 연동 (1,146건) ✅ `nutrition_db.py`
- [ ] 식품 API 실시간 교차검증 (LLM 생성 영양소 검증)
- [ ] 장보기 리스트 자동 생성
- [ ] 요리 레시피 링크 연결

---

> **💡 핵심 원칙**: 식단 생성은 **목표 칼로리와 탄단지 비율을 정확히 맞추는 것**이 최우선이며,
> 동시에 **한국인 식습관에 맞는 현실적인 메뉴**를 구성해야 합니다.
> 제약사항(당뇨, 고혈압 등)이 있을 경우 **금지 식품 필터링이 반드시 동작**해야 합니다.
