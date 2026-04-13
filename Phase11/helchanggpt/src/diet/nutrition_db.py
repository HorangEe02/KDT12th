"""
nutrition_db.py
식품 영양성분 데이터베이스를 관리합니다.

1. 로컬 JSON (scripts/fetch_nutrition_api.py로 수집한 데이터)
2. 자주 사용되는 피트니스 식품 기본 DB
3. 음식명 검색 + 영양소 조회
"""

import json
from pathlib import Path
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "nutrition"

# ═══════════════════════════════════════
# 피트니스 기본 식품 DB (API 없이 즉시 사용)
# ═══════════════════════════════════════

COMMON_FOODS_DB = {
    # ── 탄수화물 ──
    "현미밥 1공기": {"kcal": 330, "carb_g": 68, "protein_g": 7, "fat_g": 2.5, "sodium_mg": 5},
    "백미밥 1공기": {"kcal": 310, "carb_g": 69, "protein_g": 5, "fat_g": 0.8, "sodium_mg": 3},
    "고구마 1개(150g)": {"kcal": 190, "carb_g": 44, "protein_g": 2, "fat_g": 0.2, "sodium_mg": 18},
    "통밀빵 1쪽": {"kcal": 80, "carb_g": 14, "protein_g": 4, "fat_g": 1, "sodium_mg": 130},
    "오트밀 40g": {"kcal": 150, "carb_g": 27, "protein_g": 5, "fat_g": 2.5, "sodium_mg": 2},
    "잡곡밥 1공기": {"kcal": 320, "carb_g": 66, "protein_g": 8, "fat_g": 2, "sodium_mg": 5},

    # ── 단백질 ──
    "닭가슴살 100g": {"kcal": 109, "carb_g": 0, "protein_g": 23, "fat_g": 1.2, "sodium_mg": 45},
    "닭가슴살 150g": {"kcal": 165, "carb_g": 0, "protein_g": 35, "fat_g": 1.8, "sodium_mg": 68},
    "소고기 등심 100g": {"kcal": 240, "carb_g": 0.3, "protein_g": 26, "fat_g": 14.4, "sodium_mg": 52},
    "연어 100g": {"kcal": 182, "carb_g": 0, "protein_g": 25, "fat_g": 8.1, "sodium_mg": 59},
    "참치캔 100g": {"kcal": 130, "carb_g": 0, "protein_g": 28, "fat_g": 1.5, "sodium_mg": 350},
    "계란 1개": {"kcal": 72, "carb_g": 0.4, "protein_g": 6.3, "fat_g": 5, "sodium_mg": 70},
    "계란 2개": {"kcal": 144, "carb_g": 0.8, "protein_g": 12.6, "fat_g": 10, "sodium_mg": 140},
    "두부 반모(150g)": {"kcal": 130, "carb_g": 4, "protein_g": 13, "fat_g": 7, "sodium_mg": 7},
    "그릭요거트 150g": {"kcal": 130, "carb_g": 6, "protein_g": 17, "fat_g": 4, "sodium_mg": 55},
    "프로틴쉐이크 1잔": {"kcal": 150, "carb_g": 8, "protein_g": 25, "fat_g": 2, "sodium_mg": 180},

    # ── 채소 ──
    "브로콜리 100g": {"kcal": 35, "carb_g": 5.6, "protein_g": 3.7, "fat_g": 0.4, "sodium_mg": 15},
    "시금치 100g": {"kcal": 23, "carb_g": 2.3, "protein_g": 3.0, "fat_g": 0.3, "sodium_mg": 70},
    "양배추 100g": {"kcal": 25, "carb_g": 5.8, "protein_g": 1.3, "fat_g": 0.1, "sodium_mg": 18},
    "토마토 1개(150g)": {"kcal": 27, "carb_g": 5.8, "protein_g": 1.3, "fat_g": 0.3, "sodium_mg": 8},
    "샐러드 채소 100g": {"kcal": 15, "carb_g": 2.5, "protein_g": 1.2, "fat_g": 0.2, "sodium_mg": 10},

    # ── 과일 ──
    "바나나 1개": {"kcal": 106, "carb_g": 27, "protein_g": 1.3, "fat_g": 0.4, "sodium_mg": 1},
    "사과 1개": {"kcal": 95, "carb_g": 25, "protein_g": 0.5, "fat_g": 0.3, "sodium_mg": 2},
    "블루베리 100g": {"kcal": 57, "carb_g": 14, "protein_g": 0.7, "fat_g": 0.3, "sodium_mg": 1},

    # ── 건강한 지방 ──
    "아몬드 20g": {"kcal": 116, "carb_g": 4, "protein_g": 4, "fat_g": 10, "sodium_mg": 0},
    "아보카도 반개": {"kcal": 120, "carb_g": 6, "protein_g": 1.5, "fat_g": 11, "sodium_mg": 5},
    "올리브오일 1큰술": {"kcal": 120, "carb_g": 0, "protein_g": 0, "fat_g": 14, "sodium_mg": 0},

    # ── 한식 ──
    "김치 60g": {"kcal": 10, "carb_g": 1.8, "protein_g": 0.8, "fat_g": 0.2, "sodium_mg": 390},
    "된장찌개 1인분": {"kcal": 105, "carb_g": 8.4, "protein_g": 7.2, "fat_g": 4.5, "sodium_mg": 1350},
    "미역국 1인분": {"kcal": 45, "carb_g": 3.5, "protein_g": 4.0, "fat_g": 1.5, "sodium_mg": 800},
    "무가당 두유 200ml": {"kcal": 70, "carb_g": 3, "protein_g": 7, "fat_g": 3.5, "sodium_mg": 100},
}


@lru_cache(maxsize=1)
def load_nutrition_db() -> list[dict]:
    """수집된 식품 영양성분 JSON을 로드합니다."""
    foods_path = DATA_DIR / "foods.json"
    if not foods_path.exists():
        return []
    with open(foods_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_food(query: str, top_n: int = 5) -> list[dict]:
    """
    식품명으로 영양성분을 검색합니다.
    로컬 JSON → COMMON_FOODS_DB 순서로 검색합니다.

    Args:
        query: 검색할 음식명
        top_n: 최대 결과 수

    Returns:
        [{"name": "닭가슴살 100g", "kcal": 109, "carb_g": 0, ...}, ...]
    """
    results = []

    # 1. 로컬 JSON DB 검색
    db = load_nutrition_db()
    for item in db:
        name = item.get("food_name", "")
        if query in (name or ""):
            results.append({
                "name": name,
                "kcal": item.get("calories_kcal"),
                "carb_g": item.get("carb_g"),
                "protein_g": item.get("protein_g"),
                "fat_g": item.get("fat_g"),
                "sodium_mg": item.get("sodium_mg"),
                "source": "api_db",
            })
            if len(results) >= top_n:
                return results

    # 2. 기본 DB 검색
    for name, nutrients in COMMON_FOODS_DB.items():
        if query in name:
            results.append({"name": name, **nutrients, "source": "common_db"})
            if len(results) >= top_n:
                return results

    return results


def validate_food_nutrition(food_name: str, claimed_kcal: float) -> dict:
    """LLM이 생성한 음식의 칼로리를 DB와 교차 검증합니다."""
    matches = search_food(food_name, top_n=1)
    if not matches:
        return {"verified": False, "reason": "DB에서 찾을 수 없음"}

    db_kcal = matches[0].get("kcal", 0)
    if db_kcal and abs(db_kcal - claimed_kcal) / max(db_kcal, 1) > 0.3:
        return {
            "verified": False,
            "reason": f"칼로리 차이 큼 (LLM: {claimed_kcal}, DB: {db_kcal})",
            "db_value": db_kcal,
        }

    return {"verified": True, "db_value": db_kcal}
