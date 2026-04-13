"""
eating_out_db.py
회식/외식 메뉴별 추정 칼로리 데이터베이스.
"""

EATING_OUT_DB = {
    # ── 회식 유형별 ──
    "회식_일반": {"estimated_kcal": 800, "carb_g": 80, "protein_g": 40, "fat_g": 35,
                  "tips": ["채소 반찬 먼저 섭취", "국물류 나트륨 주의", "밥 양 조절"]},
    "회식_고기": {"estimated_kcal": 1000, "carb_g": 50, "protein_g": 60, "fat_g": 55,
                  "tips": ["살코기 위주로 선택", "쌈채소 많이 섭취", "소주 1잔=90kcal"]},
    "회식_술자리": {"estimated_kcal": 1200, "carb_g": 100, "protein_g": 35, "fat_g": 50,
                    "tips": ["안주보다 물 자주 마시기", "음주 후 라면 자제"]},

    # ── 외식 메뉴별 ──
    "치킨": {"estimated_kcal": 700, "carb_g": 30, "protein_g": 50, "fat_g": 40,
             "tips": ["반마리 기준", "순살보다 뼈닭이 칼로리 낮음", "양념보다 후라이드가 낮음"]},
    "피자": {"estimated_kcal": 600, "carb_g": 70, "protein_g": 25, "fat_g": 25,
             "tips": ["2~3조각 기준", "씬크러스트 선택", "채소 토핑 추가"]},
    "라면": {"estimated_kcal": 500, "carb_g": 75, "protein_g": 10, "fat_g": 16,
             "tips": ["국물 절반만 섭취", "계란 추가로 단백질 보충", "나트륨 1800mg+ 주의"]},
    "햄버거": {"estimated_kcal": 550, "carb_g": 45, "protein_g": 25, "fat_g": 30,
               "tips": ["세트 대신 단품", "감자튀김 대신 샐러드", "콜라→물 교체"]},
    "떡볶이": {"estimated_kcal": 450, "carb_g": 75, "protein_g": 8, "fat_g": 12,
               "tips": ["1인분 기준", "치즈/라면 추가 시 +200kcal"]},
    "삼겹살": {"estimated_kcal": 600, "carb_g": 5, "protein_g": 35, "fat_g": 50,
               "tips": ["200g 기준", "쌈채소 많이 먹기", "목살이 더 기름 적음"]},
    "족발": {"estimated_kcal": 500, "carb_g": 5, "protein_g": 40, "fat_g": 35,
             "tips": ["200g 기준", "보쌈보다 칼로리 약간 높음"]},
    "초밥": {"estimated_kcal": 450, "carb_g": 60, "protein_g": 25, "fat_g": 10,
             "tips": ["10개 기준", "간장 적게 찍기 (나트륨)", "와사비는 OK"]},
    "비빔밥": {"estimated_kcal": 500, "carb_g": 80, "protein_g": 15, "fat_g": 12,
               "tips": ["참기름 적게", "채소 많이", "계란 추가 단백질"]},
    "김치찌개": {"estimated_kcal": 350, "carb_g": 20, "protein_g": 20, "fat_g": 18,
                 "tips": ["밥 포함 시 +300kcal", "나트륨 높음 주의"]},
    "칼국수": {"estimated_kcal": 450, "carb_g": 70, "protein_g": 15, "fat_g": 10,
               "tips": ["국물 적게 마시기", "면 양 조절"]},

    # ── 카페/간식 ──
    "카페라떼": {"estimated_kcal": 200, "carb_g": 18, "protein_g": 10, "fat_g": 8,
                 "tips": ["톨사이즈 기준", "시럽 빼기", "무지방 우유 선택"]},
    "아메리카노": {"estimated_kcal": 10, "carb_g": 0, "protein_g": 0, "fat_g": 0,
                    "tips": ["칼로리 거의 없음", "카페인 하루 400mg 이하"]},
    "케이크": {"estimated_kcal": 400, "carb_g": 45, "protein_g": 5, "fat_g": 22,
               "tips": ["1조각 기준", "초코→치즈→과일 순 칼로리"]},

    # ── 편의점 ──
    "삼각김밥": {"estimated_kcal": 200, "carb_g": 35, "protein_g": 5, "fat_g": 3,
                 "tips": ["참치마요 기준", "간편 탄수화물 보충"]},
    "컵라면": {"estimated_kcal": 300, "carb_g": 42, "protein_g": 7, "fat_g": 11,
               "tips": ["국물 반만", "나트륨 1000mg+ 주의"]},
}


def estimate_eating_out_calories(query: str) -> dict:
    """외식 메뉴 칼로리를 추정합니다."""
    query_lower = query.lower().replace(" ", "")

    # 정확한 매칭
    if query_lower in EATING_OUT_DB:
        return EATING_OUT_DB[query_lower]

    # 부분 매칭
    for key, data in EATING_OUT_DB.items():
        if key.replace("_", "") in query_lower or query_lower in key.replace("_", ""):
            return data

    # 키워드 매칭
    for key, data in EATING_OUT_DB.items():
        clean_key = key.replace("_", "").replace("회식", "")
        if clean_key and clean_key in query_lower:
            return data

    # 매칭 실패 시 기본값
    return {
        "estimated_kcal": 600,
        "carb_g": 60,
        "protein_g": 25,
        "fat_g": 25,
        "tips": ["외식 시 채소를 먼저 섭취하세요", "음료는 물이나 무가당 차로"],
    }


def list_eating_out_categories() -> dict:
    """외식 카테고리 목록을 반환합니다."""
    categories = {}
    for key, data in EATING_OUT_DB.items():
        categories[key] = {
            "estimated_kcal": data["estimated_kcal"],
            "tips": data.get("tips", [])[:1],
        }
    return categories
