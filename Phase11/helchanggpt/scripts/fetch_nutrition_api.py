"""
fetch_nutrition_api.py
식품안전나라 Open API (I2790)에서 식품영양성분 데이터를 수집합니다.

API 문서: https://www.foodsafetykorea.go.kr/api/newDataset498.do
서비스 ID: I2790 (식품영양성분 DB)

사전 준비:
    1. https://www.foodsafetykorea.go.kr 회원가입
    2. 마이페이지 → API 인증키 발급 신청
    3. scripts/.env 파일에 FOOD_SAFETY_API_KEY 입력

사용법:
    python scripts/fetch_nutrition_api.py
    python scripts/fetch_nutrition_api.py --query 닭가슴살
    python scripts/fetch_nutrition_api.py --max-items 5000
    python scripts/fetch_nutrition_api.py --demo  # API 키 없이 샘플 데이터 생성

출력:
    data/nutrition/foods.json    — 전체 식품 데이터 (JSON)
    data/nutrition/foods.csv     — 전체 식품 데이터 (CSV)
    data/nutrition/summary.json  — 수집 요약 정보
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# 프로젝트 루트 기준 경로 설정
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    FOOD_SAFETY_API_KEY,
    FOOD_SAFETY_API_BASE,
    FOOD_SAFETY_SERVICE_ID,
    OUTPUT_FILES,
    ensure_dirs,
    check_api_key,
)

# ── 서비스 ID 오버라이드 ──
# I2790(식품영양성분DB)은 별도 인증키 발급 필요
# COOKRCP01(조리식품 레시피+영양성분)은 기본 인증키로 접근 가능 (1146건)
FOOD_SAFETY_SERVICE_ID = "COOKRCP01"

# ── API 응답 필드 매핑 (COOKRCP01 서비스) ──
FIELD_MAP = {
    "RCP_NM": "food_name",              # 레시피명
    "RCP_SEQ": "food_code",             # 레시피 일련번호
    "RCP_PAT2": "food_group",           # 요리 분류 (반찬, 국, 밥 등)
    "RCP_WAY2": "cooking_method",       # 조리 방법 (찌기, 굽기 등)
    "INFO_WGT": "serving_size",         # 중량(1인분)
    "INFO_ENG": "calories_kcal",        # 에너지(kcal)
    "INFO_CAR": "carb_g",              # 탄수화물(g)
    "INFO_PRO": "protein_g",           # 단백질(g)
    "INFO_FAT": "fat_g",              # 지방(g)
    "INFO_NA": "sodium_mg",            # 나트륨(mg)
    "HASH_TAG": "hash_tag",            # 해시태그 (재료 키워드)
    "RCP_PARTS_DTLS": "ingredients",    # 재료 상세
    "ATT_FILE_NO_MAIN": "image_url",    # 대표 이미지 URL
    "RCP_NA_TIP": "sodium_tip",         # 나트륨 저감 팁
}

# ── 주요 식품 카테고리 (검색용) ──
FITNESS_FOOD_QUERIES = [
    # 고단백 식품
    "닭가슴살", "계란", "두부", "연어", "참치", "소고기", "돼지고기",
    "우유", "요거트", "치즈", "콩", "병아리콩",
    # 탄수화물 식품
    "현미밥", "고구마", "오트밀", "바나나", "감자", "통밀빵",
    "흰쌀밥", "파스타", "보리",
    # 채소/과일
    "브로콜리", "시금치", "양배추", "토마토", "사과", "블루베리",
    "아보카도", "고추", "양파", "당근",
    # 견과류/건강식품
    "아몬드", "호두", "땅콩버터", "올리브오일", "프로틴",
    # 한국 전통 음식
    "김치", "된장찌개", "비빔밥", "불고기", "삼계탕",
    "잡곡밥", "미역국", "제육볶음", "갈비탕",
]


def fetch_page(api_key: str, start: int, end: int, food_name: str = "") -> dict | None:
    """API에서 한 페이지의 데이터를 가져옵니다."""
    url = f"{FOOD_SAFETY_API_BASE}/{api_key}/{FOOD_SAFETY_SERVICE_ID}/json/{start}/{end}"
    if food_name:
        url += f"/RCP_NM={food_name}"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # API 응답 구조 확인
        service_data = data.get(FOOD_SAFETY_SERVICE_ID)
        if not service_data:
            print(f"  ⚠️ 서비스 데이터 없음: {list(data.keys())}")
            return None

        result = service_data.get("RESULT", {})
        if result.get("CODE") != "INFO-000":
            print(f"  ⚠️ API 오류: {result.get('CODE')} - {result.get('MSG')}")
            return None

        return service_data

    except requests.exceptions.RequestException as e:
        print(f"  ❌ 요청 실패: {e}")
        return None
    except json.JSONDecodeError:
        print(f"  ❌ JSON 파싱 실패")
        return None


def parse_food_item(raw: dict) -> dict:
    """API 응답의 원시 데이터를 표준 형식으로 변환합니다."""
    item = {}
    for api_field, our_field in FIELD_MAP.items():
        value = raw.get(api_field, "")
        # 숫자 필드 변환
        if our_field.endswith(("_kcal", "_g", "_mg")):
            try:
                item[our_field] = round(float(value), 2) if value and value != "N/A" else None
            except (ValueError, TypeError):
                item[our_field] = None
        else:
            item[our_field] = value if value else None
    return item


def fetch_all_foods(
    api_key: str,
    max_items: int = 10000,
    page_size: int = 100,
    queries: list[str] | None = None,
) -> list[dict]:
    """
    전체 식품 데이터를 수집합니다.

    Args:
        api_key: 식품안전나라 API 인증키
        max_items: 최대 수집 건수
        page_size: 페이지당 건수 (최대 1000)
        queries: 검색어 목록 (None이면 전체 수집)

    Returns:
        파싱된 식품 데이터 리스트
    """
    all_foods = []
    seen_codes = set()

    if queries:
        # 특정 식품명으로 검색
        for i, query in enumerate(queries, 1):
            print(f"  [{i}/{len(queries)}] '{query}' 검색 중...")
            data = fetch_page(api_key, 1, page_size, food_name=query)
            if data and "row" in data:
                for raw in data["row"]:
                    item = parse_food_item(raw)
                    code = item.get("food_code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        all_foods.append(item)
            time.sleep(0.3)  # API 부하 방지
    else:
        # 전체 데이터 페이지네이션
        total_fetched = 0
        page = 1
        while total_fetched < max_items:
            start = (page - 1) * page_size + 1
            end = min(page * page_size, max_items)
            print(f"  페이지 {page}: {start}~{end} 수집 중...")

            data = fetch_page(api_key, start, end)
            if not data or "row" not in data:
                break

            rows = data["row"]
            for raw in rows:
                item = parse_food_item(raw)
                code = item.get("food_code")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    all_foods.append(item)

            total_fetched += len(rows)
            if len(rows) < page_size:
                break  # 마지막 페이지

            page += 1
            time.sleep(0.5)

    return all_foods


def generate_demo_data() -> list[dict]:
    """API 키 없이 테스트용 샘플 데이터를 생성합니다."""
    print("📦 데모 모드: 샘플 식품 데이터를 생성합니다.")

    demo_foods = [
        {"food_name": "닭가슴살(삶은것)", "food_code": "D000001", "food_group": "육류",
         "serving_size": "100", "calories_kcal": 109, "carb_g": 0, "protein_g": 23.1,
         "fat_g": 1.2, "sugar_g": 0, "sodium_mg": 45, "cholesterol_mg": 58,
         "saturated_fat_g": 0.3, "trans_fat_g": 0},
        {"food_name": "현미밥", "food_code": "D000002", "food_group": "곡류",
         "serving_size": "210", "calories_kcal": 331, "carb_g": 72.0, "protein_g": 6.9,
         "fat_g": 1.7, "sugar_g": 0.5, "sodium_mg": 5, "cholesterol_mg": 0,
         "saturated_fat_g": 0.4, "trans_fat_g": 0},
        {"food_name": "계란(삶은것)", "food_code": "D000003", "food_group": "난류",
         "serving_size": "60", "calories_kcal": 87, "carb_g": 0.6, "protein_g": 7.5,
         "fat_g": 5.8, "sugar_g": 0.5, "sodium_mg": 80, "cholesterol_mg": 225,
         "saturated_fat_g": 1.6, "trans_fat_g": 0},
        {"food_name": "고구마(찐것)", "food_code": "D000004", "food_group": "서류",
         "serving_size": "150", "calories_kcal": 189, "carb_g": 44.3, "protein_g": 2.0,
         "fat_g": 0.2, "sugar_g": 10.5, "sodium_mg": 18, "cholesterol_mg": 0,
         "saturated_fat_g": 0.1, "trans_fat_g": 0},
        {"food_name": "브로콜리(삶은것)", "food_code": "D000005", "food_group": "채소류",
         "serving_size": "100", "calories_kcal": 35, "carb_g": 5.6, "protein_g": 3.7,
         "fat_g": 0.4, "sugar_g": 1.4, "sodium_mg": 15, "cholesterol_mg": 0,
         "saturated_fat_g": 0.1, "trans_fat_g": 0},
        {"food_name": "그릭요거트(무지방)", "food_code": "D000006", "food_group": "유제품류",
         "serving_size": "150", "calories_kcal": 87, "carb_g": 5.0, "protein_g": 15.0,
         "fat_g": 0.7, "sugar_g": 5.0, "sodium_mg": 55, "cholesterol_mg": 8,
         "saturated_fat_g": 0.3, "trans_fat_g": 0},
        {"food_name": "연어(구운것)", "food_code": "D000007", "food_group": "어류",
         "serving_size": "100", "calories_kcal": 182, "carb_g": 0, "protein_g": 25.4,
         "fat_g": 8.1, "sugar_g": 0, "sodium_mg": 59, "cholesterol_mg": 63,
         "saturated_fat_g": 1.3, "trans_fat_g": 0},
        {"food_name": "아몬드", "food_code": "D000008", "food_group": "견과류",
         "serving_size": "30", "calories_kcal": 173, "carb_g": 6.1, "protein_g": 6.3,
         "fat_g": 14.9, "sugar_g": 1.2, "sodium_mg": 0, "cholesterol_mg": 0,
         "saturated_fat_g": 1.1, "trans_fat_g": 0},
        {"food_name": "오트밀", "food_code": "D000009", "food_group": "곡류",
         "serving_size": "40", "calories_kcal": 154, "carb_g": 27.4, "protein_g": 5.3,
         "fat_g": 2.6, "sugar_g": 0.4, "sodium_mg": 2, "cholesterol_mg": 0,
         "saturated_fat_g": 0.4, "trans_fat_g": 0},
        {"food_name": "두부(부침)", "food_code": "D000010", "food_group": "두류",
         "serving_size": "100", "calories_kcal": 97, "carb_g": 2.6, "protein_g": 9.6,
         "fat_g": 5.3, "sugar_g": 0.6, "sodium_mg": 7, "cholesterol_mg": 0,
         "saturated_fat_g": 0.8, "trans_fat_g": 0},
        {"food_name": "바나나", "food_code": "D000011", "food_group": "과일류",
         "serving_size": "120", "calories_kcal": 106, "carb_g": 27.2, "protein_g": 1.3,
         "fat_g": 0.4, "sugar_g": 14.4, "sodium_mg": 1, "cholesterol_mg": 0,
         "saturated_fat_g": 0.1, "trans_fat_g": 0},
        {"food_name": "흰쌀밥", "food_code": "D000012", "food_group": "곡류",
         "serving_size": "210", "calories_kcal": 313, "carb_g": 68.7, "protein_g": 5.3,
         "fat_g": 0.6, "sugar_g": 0, "sodium_mg": 3, "cholesterol_mg": 0,
         "saturated_fat_g": 0.2, "trans_fat_g": 0},
        {"food_name": "소고기(등심,구이)", "food_code": "D000013", "food_group": "육류",
         "serving_size": "100", "calories_kcal": 240, "carb_g": 0.3, "protein_g": 26.1,
         "fat_g": 14.4, "sugar_g": 0, "sodium_mg": 52, "cholesterol_mg": 71,
         "saturated_fat_g": 5.6, "trans_fat_g": 0.4},
        {"food_name": "김치(배추김치)", "food_code": "D000014", "food_group": "절임류",
         "serving_size": "60", "calories_kcal": 10, "carb_g": 1.8, "protein_g": 0.8,
         "fat_g": 0.2, "sugar_g": 0.8, "sodium_mg": 390, "cholesterol_mg": 0,
         "saturated_fat_g": 0, "trans_fat_g": 0},
        {"food_name": "된장찌개", "food_code": "D000015", "food_group": "국/탕류",
         "serving_size": "300", "calories_kcal": 105, "carb_g": 8.4, "protein_g": 7.2,
         "fat_g": 4.5, "sugar_g": 1.2, "sodium_mg": 1350, "cholesterol_mg": 5,
         "saturated_fat_g": 0.8, "trans_fat_g": 0},
        {"food_name": "비빔밥", "food_code": "D000016", "food_group": "밥류",
         "serving_size": "400", "calories_kcal": 490, "carb_g": 78.0, "protein_g": 15.0,
         "fat_g": 12.0, "sugar_g": 5.0, "sodium_mg": 890, "cholesterol_mg": 120,
         "saturated_fat_g": 2.5, "trans_fat_g": 0},
        {"food_name": "프로틴쉐이크(초코)", "food_code": "D000017", "food_group": "건강식품",
         "serving_size": "300", "calories_kcal": 150, "carb_g": 8.0, "protein_g": 25.0,
         "fat_g": 2.0, "sugar_g": 3.0, "sodium_mg": 180, "cholesterol_mg": 30,
         "saturated_fat_g": 0.5, "trans_fat_g": 0},
        {"food_name": "아보카도", "food_code": "D000018", "food_group": "과일류",
         "serving_size": "100", "calories_kcal": 160, "carb_g": 8.5, "protein_g": 2.0,
         "fat_g": 14.7, "sugar_g": 0.7, "sodium_mg": 7, "cholesterol_mg": 0,
         "saturated_fat_g": 2.1, "trans_fat_g": 0},
        {"food_name": "시금치(삶은것)", "food_code": "D000019", "food_group": "채소류",
         "serving_size": "100", "calories_kcal": 23, "carb_g": 2.3, "protein_g": 3.0,
         "fat_g": 0.3, "sugar_g": 0.4, "sodium_mg": 70, "cholesterol_mg": 0,
         "saturated_fat_g": 0, "trans_fat_g": 0},
        {"food_name": "삼계탕", "food_code": "D000020", "food_group": "국/탕류",
         "serving_size": "500", "calories_kcal": 485, "carb_g": 35.0, "protein_g": 33.0,
         "fat_g": 22.0, "sugar_g": 1.0, "sodium_mg": 1100, "cholesterol_mg": 95,
         "saturated_fat_g": 6.0, "trans_fat_g": 0},
    ]

    # 식이 제약 플래그 추가
    for food in demo_foods:
        food["dietary_flags"] = _compute_dietary_flags(food)

    return demo_foods


def _compute_dietary_flags(food: dict) -> dict:
    """식품의 식이 플래그를 계산합니다."""
    flags = {}

    sodium = food.get("sodium_mg") or 0
    sugar = food.get("sugar_g") or 0
    sat_fat = food.get("saturated_fat_g") or 0
    protein = food.get("protein_g") or 0
    calories = food.get("calories_kcal") or 1

    flags["high_sodium"] = sodium > 600  # 1회 제공량 기준 고나트륨
    flags["high_sugar"] = sugar > 10
    flags["high_saturated_fat"] = sat_fat > 5
    flags["high_protein"] = protein > 15
    flags["low_calorie"] = calories < 100
    flags["protein_ratio_pct"] = round((protein * 4 / calories) * 100, 1) if calories > 0 else 0

    return flags


def save_results(foods: list[dict], output_json: Path, output_csv: Path, summary_path: Path):
    """수집 결과를 JSON + CSV + 요약 파일로 저장합니다."""
    # JSON 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(foods, f, ensure_ascii=False, indent=2)
    print(f"  ✅ JSON 저장: {output_json} ({len(foods)}건)")

    # CSV 저장
    try:
        import pandas as pd
        df = pd.json_normalize(foods)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"  ✅ CSV 저장: {output_csv}")
    except ImportError:
        print(f"  ⚠️ pandas 미설치로 CSV 저장 생략")

    # 요약 저장
    food_groups = {}
    for food in foods:
        group = food.get("food_group", "미분류")
        food_groups[group] = food_groups.get(group, 0) + 1

    summary = {
        "total_items": len(foods),
        "collected_at": datetime.now().isoformat(),
        "food_groups": food_groups,
        "fields": list(FIELD_MAP.values()),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 요약 저장: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="식품안전나라 식품영양성분 데이터 수집")
    parser.add_argument("--query", type=str, help="특정 식품명 검색")
    parser.add_argument("--max-items", type=int, default=5000, help="최대 수집 건수")
    parser.add_argument("--fitness-foods", action="store_true", help="피트니스 관련 식품만 수집")
    parser.add_argument("--demo", action="store_true", help="API 키 없이 데모 데이터 생성")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("🍱 식품안전나라 식품영양성분 데이터 수집")
    print("=" * 60)

    if args.demo:
        foods = generate_demo_data()
    else:
        if not check_api_key("FOOD_SAFETY_API_KEY", FOOD_SAFETY_API_KEY):
            print("\n💡 --demo 옵션으로 샘플 데이터를 생성할 수 있습니다.")
            print("   python scripts/fetch_nutrition_api.py --demo")
            return

        if args.query:
            queries = [args.query]
        elif args.fitness_foods:
            queries = FITNESS_FOOD_QUERIES
        else:
            queries = None

        print(f"\n📥 데이터 수집 시작 (최대 {args.max_items}건)...")
        foods = fetch_all_foods(
            api_key=FOOD_SAFETY_API_KEY,
            max_items=args.max_items,
            queries=queries,
        )

        # 식이 플래그 추가
        for food in foods:
            food["dietary_flags"] = _compute_dietary_flags(food)

    if not foods:
        print("❌ 수집된 데이터가 없습니다.")
        return

    print(f"\n📊 총 {len(foods)}건 수집 완료")
    save_results(
        foods,
        OUTPUT_FILES["nutrition_foods"],
        OUTPUT_FILES["nutrition_foods_csv"],
        OUTPUT_FILES["nutrition_summary"],
    )

    print("\n✨ 식품 영양성분 데이터 수집 완료!")


if __name__ == "__main__":
    main()
