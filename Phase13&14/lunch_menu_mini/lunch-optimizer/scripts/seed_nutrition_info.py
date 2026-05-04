"""표준 한식 메뉴 영양 정보 시드 (data.go.kr 식약처 API 우선, 식품안전나라 폴백).

NutritionCollector dual-provider 라우팅을 통해 정확한 영양값을 가져온 뒤
raw SQL 로 nutrition_info 테이블에 UPSERT 한다.

restaurant_id 는 ``_standard::<food_name>`` 형태로 unique 제약을 회피하면서
``find_nutrition_by_food_name`` 의 식당-무관 검색이 정상 매칭되도록 한다.

ORM(NutritionInfo) 클래스가 source/match_confidence 컬럼을 정의하지 않아 발생하는
TypeError 를 회피하기 위해 sqlite3 직접 쓰기를 사용한다.

사용:
    docker exec mini-lunch-api python /tmp/seed_nutrition_info.py
옵션:
    SEED_FOODS=음식1,음식2,...   (쉼표로 추가 음식 지정)
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, "/app")

from pipeline.collectors.nutrition_collector import NutritionCollector  # noqa: E402

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")
STANDARD_RESTAURANT_PREFIX = "_standard"

DEFAULT_FOODS = [
    # 한식 찌개·국
    "김치찌개", "된장찌개", "부대찌개", "순두부찌개",
    "갈비탕", "설렁탕", "육개장", "감자탕",
    # 밥류
    "쌀밥", "잡곡밥", "비빔밥", "볶음밥",
    # 면류
    "라면", "짜장면", "짬뽕", "냉면", "칼국수",
    # 분식
    "김밥", "떡볶이", "순대",
    # 고기·구이
    "삼겹살", "제육볶음", "닭갈비",
    # 양식·일식
    "돈가스", "스파게티", "초밥",
    # 음료
    "아메리카노", "라떼",
]


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    extra = os.environ.get("SEED_FOODS", "").strip()
    foods = list(DEFAULT_FOODS)
    if extra:
        foods.extend([f.strip() for f in extra.split(",") if f.strip()])

    print(f"target foods: {len(foods)}")

    try:
        collector = NutritionCollector()
    except Exception as e:  # noqa: BLE001
        print(f"[error] NutritionCollector 초기화 실패: {e}", file=sys.stderr)
        return 1

    inserted = 0
    updated = 0
    skipped_nodata = 0
    failures = 0
    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        for food in foods:
            try:
                results = collector.search_by_name(food, max_results=3)
                if not results:
                    print(f"  · skip(no api data): {food}")
                    skipped_nodata += 1
                    continue
                top = results[0]
                api_name = top.get("food_name", "?")
                cal = _to_float(top.get("calories"))
                carbs = _to_float(top.get("carbs"))
                protein = _to_float(top.get("protein"))
                fat = _to_float(top.get("fat"))
                sugar = _to_float(top.get("sugar"))
                sodium = _to_float(top.get("sodium"))
                serving = _to_float(top.get("serving_size")) or 100.0
                food_code = top.get("food_code") or ""
                rid = f"{STANDARD_RESTAURANT_PREFIX}::{food}"

                cur = conn.execute(
                    "SELECT id FROM nutrition_info WHERE restaurant_id = ?",
                    (rid,),
                )
                if cur.fetchone() is not None:
                    conn.execute(
                        """
                        UPDATE nutrition_info SET
                            food_name=?, food_code=?,
                            match_type='standard_seed', match_score=0.95,
                            serving_size=?, calories=?, carbs=?, protein=?,
                            fat=?, sugar=?, sodium=?,
                            mapped_at=?, source='data_go_kr', match_confidence=0.95
                        WHERE restaurant_id = ?
                        """,
                        (food, food_code, serving, cal, carbs, protein,
                         fat, sugar, sodium, now, rid),
                    )
                    updated += 1
                    print(f"  ~ updated: {food}  ←  '{api_name}'  ({cal} kcal)")
                else:
                    conn.execute(
                        """
                        INSERT INTO nutrition_info
                            (restaurant_id, food_name, food_code, match_type, match_score,
                             serving_size, calories, carbs, protein, fat, sugar, sodium,
                             mapped_at, source, match_confidence)
                        VALUES (?, ?, ?, 'standard_seed', 0.95,
                                ?, ?, ?, ?, ?, ?, ?, ?, 'data_go_kr', 0.95)
                        """,
                        (rid, food, food_code, serving, cal, carbs, protein,
                         fat, sugar, sodium, now),
                    )
                    inserted += 1
                    print(f"  + inserted: {food}  ←  '{api_name}'  ({cal} kcal)")
            except Exception as e:  # noqa: BLE001
                print(f"  ! fail: {food} ({e})", file=sys.stderr)
                failures += 1

        conn.commit()
    finally:
        conn.close()

    print()
    print(f"✅ inserted: {inserted}")
    print(f"   updated:  {updated}")
    print(f"   skipped(no api data): {skipped_nodata}")
    print(f"   failures: {failures}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
