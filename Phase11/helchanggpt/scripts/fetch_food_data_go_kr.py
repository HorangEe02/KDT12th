"""
fetch_food_data_go_kr.py
공공데이터포털(data.go.kr) 식품영양성분 DB 정보 API로 식품 데이터를 수집합니다.

식품안전나라 API 키가 유효하지 않을 때의 대안입니다.
공공데이터포털 API는 인코딩된 키를 그대로 사용합니다.

API 정보:
  - 식품의약품안전처_식품영양성분DB정보 (서비스 ID: 1471000/FoodNtrIrdntInfoService1)
  - https://www.data.go.kr/data/15127578/openapi.do

사전 준비:
    1. https://www.data.go.kr 회원가입
    2. 위 API 페이지에서 "활용신청"
    3. scripts/.env 파일에 DATA_GO_KR_API_KEY 입력

사용법:
    python scripts/fetch_food_data_go_kr.py
    python scripts/fetch_food_data_go_kr.py --query 닭가슴살
    python scripts/fetch_food_data_go_kr.py --fitness-foods
    python scripts/fetch_food_data_go_kr.py --max-items 5000

출력:
    data/nutrition/foods.json
    data/nutrition/foods.csv
    data/nutrition/summary.json
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_GO_KR_API_KEY, OUTPUT_FILES, ensure_dirs, check_api_key

# ── API 설정 ──
API_BASE = "http://apis.data.go.kr/1471000/FoodNtrIrdntInfoService1/getFoodNtrItdntList1"

# ── 필드 매핑 ──
FIELD_MAP = {
    "DESC_KOR": "food_name",
    "FOOD_CD": "food_code",
    "GROUP_NAME": "food_group",
    "RESEARCH_YEAR": "research_year",
    "MAKER_NAME": "manufacturer",
    "SERVING_WT": "serving_size",
    "NUTR_CONT1": "calories_kcal",
    "NUTR_CONT2": "carb_g",
    "NUTR_CONT3": "protein_g",
    "NUTR_CONT4": "fat_g",
    "NUTR_CONT5": "sugar_g",
    "NUTR_CONT6": "sodium_mg",
    "NUTR_CONT7": "cholesterol_mg",
    "NUTR_CONT8": "saturated_fat_g",
    "NUTR_CONT9": "trans_fat_g",
}

FITNESS_FOOD_QUERIES = [
    "닭가슴살", "계란", "두부", "연어", "참치", "소고기", "돼지고기",
    "우유", "요거트", "치즈", "콩",
    "현미밥", "고구마", "오트밀", "바나나", "감자", "통밀빵", "흰쌀밥",
    "브로콜리", "시금치", "양배추", "토마토", "사과",
    "아보카도", "당근", "양파",
    "아몬드", "호두",
    "김치", "된장찌개", "비빔밥", "불고기", "삼계탕",
    "잡곡밥", "미역국", "제육볶음",
]


def fetch_foods(api_key: str, food_name: str = "", page_no: int = 1, num_of_rows: int = 100) -> dict | None:
    """data.go.kr API에서 식품 데이터를 가져옵니다."""
    params = {
        "serviceKey": api_key,  # 인코딩된 키 그대로 전달
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "type": "json",
    }
    if food_name:
        params["DESC_KOR"] = food_name

    try:
        resp = requests.get(API_BASE, params=params, timeout=30)

        # 디버그: 응답 확인
        if resp.status_code != 200:
            print(f"  ⚠️ HTTP {resp.status_code}")
            return None

        # HTML 응답 체크 (인증 오류 등)
        content_type = resp.headers.get("content-type", "")
        if "html" in content_type:
            print(f"  ⚠️ HTML 응답 (API 키 오류 가능): {resp.text[:100]}")
            return None

        data = resp.json()

        # 응답 구조 확인
        header = data.get("header", {})
        if header.get("resultCode") != "00":
            print(f"  ⚠️ API 오류: {header.get('resultCode')} - {header.get('resultMsg')}")
            return None

        body = data.get("body", {})
        return body

    except requests.exceptions.RequestException as e:
        print(f"  ❌ 요청 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        # XML 응답일 수 있음 — XML 파싱 시도
        try:
            return _parse_xml_response(resp.text)
        except Exception:
            print(f"  ❌ 응답 파싱 실패: {e}")
            print(f"     응답 앞부분: {resp.text[:200]}")
            return None


def _parse_xml_response(xml_text: str) -> dict | None:
    """XML 응답을 파싱합니다 (JSON 실패 시 폴백)."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_text)

        # 에러 체크
        result_code = root.findtext(".//resultCode")
        if result_code and result_code != "00":
            result_msg = root.findtext(".//resultMsg")
            print(f"  ⚠️ API 오류 (XML): {result_code} - {result_msg}")
            return None

        items = []
        for item in root.iter("item"):
            food = {}
            for child in item:
                food[child.tag] = child.text
            items.append(food)

        total_count = root.findtext(".//totalCount")

        return {
            "totalCount": int(total_count) if total_count else len(items),
            "items": {"item": items} if items else {},
        }
    except ET.ParseError:
        return None


def parse_food_item(raw: dict) -> dict:
    """API 응답 아이템을 표준 형식으로 변환합니다."""
    item = {}
    for api_field, our_field in FIELD_MAP.items():
        value = raw.get(api_field, "")
        if our_field.endswith(("_kcal", "_g", "_mg")):
            try:
                item[our_field] = round(float(value), 2) if value and value not in ("N/A", "", "-") else None
            except (ValueError, TypeError):
                item[our_field] = None
        else:
            item[our_field] = value if value else None
    return item


def compute_dietary_flags(food: dict) -> dict:
    """식품의 식이 플래그를 계산합니다."""
    sodium = food.get("sodium_mg") or 0
    sugar = food.get("sugar_g") or 0
    sat_fat = food.get("saturated_fat_g") or 0
    protein = food.get("protein_g") or 0
    calories = food.get("calories_kcal") or 1

    return {
        "high_sodium": sodium > 600,
        "high_sugar": sugar > 10,
        "high_saturated_fat": sat_fat > 5,
        "high_protein": protein > 15,
        "low_calorie": calories < 100,
        "protein_ratio_pct": round((protein * 4 / max(calories, 1)) * 100, 1),
    }


def fetch_all_foods(api_key: str, queries: list[str] | None = None, max_items: int = 5000) -> list[dict]:
    """전체 식품 데이터를 수집합니다."""
    all_foods = []
    seen_codes = set()

    if queries:
        for i, query in enumerate(queries, 1):
            print(f"  [{i}/{len(queries)}] '{query}' 검색 중...")
            body = fetch_foods(api_key, food_name=query, num_of_rows=100)

            if body:
                items_data = body.get("items", {})
                items = items_data.get("item", []) if isinstance(items_data, dict) else []
                # 단일 아이템이 dict로 올 수 있음
                if isinstance(items, dict):
                    items = [items]

                for raw in items:
                    item = parse_food_item(raw)
                    code = item.get("food_code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        item["dietary_flags"] = compute_dietary_flags(item)
                        all_foods.append(item)

                print(f"    → {len(items)}건 (누적 {len(all_foods)}건)")
            time.sleep(0.3)
    else:
        page = 1
        while len(all_foods) < max_items:
            print(f"  페이지 {page} 수집 중 (현재 {len(all_foods)}건)...")
            body = fetch_foods(api_key, page_no=page, num_of_rows=100)

            if not body:
                break

            items_data = body.get("items", {})
            items = items_data.get("item", []) if isinstance(items_data, dict) else []
            if isinstance(items, dict):
                items = [items]
            if not items:
                break

            for raw in items:
                item = parse_food_item(raw)
                code = item.get("food_code")
                if code and code not in seen_codes:
                    seen_codes.add(code)
                    item["dietary_flags"] = compute_dietary_flags(item)
                    all_foods.append(item)

            total = body.get("totalCount", 0)
            print(f"    → {len(items)}건 (누적 {len(all_foods)}/{total}건)")

            if len(all_foods) >= total or len(all_foods) >= max_items:
                break

            page += 1
            time.sleep(0.5)

    return all_foods


def save_results(foods: list[dict]):
    """결과를 JSON + CSV + 요약으로 저장합니다."""
    # JSON
    with open(OUTPUT_FILES["nutrition_foods"], "w", encoding="utf-8") as f:
        json.dump(foods, f, ensure_ascii=False, indent=2)
    print(f"  ✅ JSON: {OUTPUT_FILES['nutrition_foods']} ({len(foods)}건)")

    # CSV
    try:
        import pandas as pd
        df = pd.json_normalize(foods)
        df.to_csv(OUTPUT_FILES["nutrition_foods_csv"], index=False, encoding="utf-8-sig")
        print(f"  ✅ CSV:  {OUTPUT_FILES['nutrition_foods_csv']}")
    except ImportError:
        pass

    # 요약
    groups = {}
    for f in foods:
        g = f.get("food_group", "미분류") or "미분류"
        groups[g] = groups.get(g, 0) + 1

    summary = {
        "total_items": len(foods),
        "source": "공공데이터포털 식품의약품안전처_식품영양성분DB정보",
        "collected_at": datetime.now().isoformat(),
        "food_groups": dict(sorted(groups.items(), key=lambda x: -x[1])),
    }
    with open(OUTPUT_FILES["nutrition_summary"], "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 요약: {OUTPUT_FILES['nutrition_summary']}")


def main():
    parser = argparse.ArgumentParser(description="공공데이터포털 식품영양성분 데이터 수집")
    parser.add_argument("--query", type=str, help="특정 식품명 검색")
    parser.add_argument("--fitness-foods", action="store_true", help="피트니스 관련 식품만")
    parser.add_argument("--max-items", type=int, default=5000, help="최대 수집 건수")
    args = parser.parse_args()

    ensure_dirs()

    print("=" * 60)
    print("🍱 공공데이터포털 식품영양성분 데이터 수집")
    print("=" * 60)

    if not check_api_key("DATA_GO_KR_API_KEY", DATA_GO_KR_API_KEY):
        return

    queries = None
    if args.query:
        queries = [args.query]
    elif args.fitness_foods:
        queries = FITNESS_FOOD_QUERIES

    print(f"\n📥 수집 시작...")
    foods = fetch_all_foods(DATA_GO_KR_API_KEY, queries=queries, max_items=args.max_items)

    if not foods:
        print("❌ 수집된 데이터가 없습니다.")
        print("   API 키를 확인해주세요. data.go.kr → 마이페이지 → 인증키 확인")
        return

    print(f"\n📊 총 {len(foods)}건 수집 완료")
    save_results(foods)
    print("\n✨ 완료!")


if __name__ == "__main__":
    main()
