"""표준 한식 영양값 수동 시드 (식약처 API 키 없이도 동작).

값 출처: 식품영양성분 데이터베이스 공개 자료 + 일반 표준 영양값(100g 기준).
정확한 수치는 식약처 OpenAPI 키 발급 후 seed_nutrition_info.py 로 갱신 권장.

NOTE: ORM 클래스(NutritionInfo)는 source/match_confidence 컬럼이 정의돼
      있지 않으므로 raw SQL 로 INSERT/UPDATE 한다. 모델 정의가 동기화되면
      ORM 버전으로 단순화 가능.

사용:
    docker exec mini-lunch-api python /tmp/seed_nutrition_info_manual.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")
STANDARD_RESTAURANT_ID = "_standard"

# (food_name, kcal, carbs_g, protein_g, fat_g, sugar_g, sodium_mg) — 100g 또는 100ml 기준
STANDARD_NUTRITION = [
    # 찌개·국 (100g 기준)
    ("김치찌개",       60,  6.0,  5.0,  2.0, 1.5, 800),
    ("된장찌개",       50,  5.0,  4.0,  1.5, 1.0, 750),
    ("부대찌개",      130,  8.0,  8.0,  7.0, 1.5, 950),
    ("순두부찌개",     55,  4.0,  5.0,  2.5, 1.0, 700),
    ("갈비탕",         95,  3.0,  7.0,  6.0, 0.5, 600),
    ("설렁탕",         60,  1.0,  7.0,  3.0, 0.3, 500),
    ("육개장",         80,  4.0,  5.0,  5.0, 1.0, 850),
    ("감자탕",        110,  8.0,  7.0,  6.0, 1.5, 700),
    # 밥류 (100g 기준)
    ("쌀밥",          145, 33.0,  3.0,  0.4, 0.1,   1),
    ("잡곡밥",        135, 30.0,  3.5,  0.6, 0.2,   2),
    ("비빔밥",        130, 19.0,  4.0,  4.0, 2.0, 400),
    ("볶음밥",        165, 22.0,  4.0,  6.0, 1.5, 500),
    # 면류
    ("라면",          480, 78.0, 10.0, 16.0, 5.0,1700),
    ("짜장면",        165, 26.0,  4.0,  5.0, 4.0, 800),
    ("짬뽕",          100, 11.0,  6.0,  4.0, 2.0,1500),
    ("냉면",          110, 22.0,  4.0,  1.0, 3.0, 800),
    ("칼국수",         95, 16.0,  4.0,  1.5, 1.0, 600),
    # 분식
    ("김밥",          175, 28.0,  5.0,  4.0, 2.0, 600),
    ("떡볶이",        175, 36.0,  4.0,  1.5,12.0, 700),
    ("순대",          230, 30.0, 11.0,  6.0, 1.0, 750),
    # 고기·구이
    ("삼겹살",        330,  0.0, 17.0, 28.0, 0.0,  60),
    ("제육볶음",      200,  8.0, 13.0, 12.0, 4.0, 600),
    ("닭갈비",        165,  7.0, 14.0,  9.0, 3.0, 550),
    # 양식·일식
    ("돈가스",        290, 22.0, 13.0, 17.0, 2.0, 500),
    ("스파게티",      160, 25.0,  5.0,  4.0, 3.0, 400),
    ("초밥",          145, 28.0,  5.0,  1.5, 6.0, 350),
    # 음료 (100ml 기준)
    ("아메리카노",      5,  1.0,  0.3,  0.0, 0.0,   3),
    ("라떼",           50,  4.5,  3.0,  2.0, 4.5,  35),
]


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    inserted = 0
    updated = 0
    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        # nutrition_info 의 unique 제약은 (restaurant_id) — _standard 행은 1개만 허용.
        # 다중 음식 시드를 위해 unique 제약 회피: 식당 id 별로 분리한다.
        for name, kcal, carbs, protein, fat, sugar, sodium in STANDARD_NUTRITION:
            rid = f"{STANDARD_RESTAURANT_ID}::{name}"
            cur = conn.execute(
                "SELECT id FROM nutrition_info WHERE restaurant_id = ?",
                (rid,),
            )
            existing = cur.fetchone()
            if existing is not None:
                conn.execute(
                    """
                    UPDATE nutrition_info SET
                        food_name=?, match_type='standard_seed', match_score=0.95,
                        serving_size=100.0,
                        calories=?, carbs=?, protein=?, fat=?, sugar=?, sodium=?,
                        mapped_at=?, source='manual_seed', match_confidence=0.95
                    WHERE restaurant_id = ?
                    """,
                    (name, kcal, carbs, protein, fat, sugar, sodium, now, rid),
                )
                updated += 1
                print(f"  ~ updated: {name}  ({kcal} kcal)")
            else:
                conn.execute(
                    """
                    INSERT INTO nutrition_info
                        (restaurant_id, food_name, match_type, match_score,
                         serving_size, calories, carbs, protein, fat, sugar, sodium,
                         mapped_at, source, match_confidence)
                    VALUES (?, ?, 'standard_seed', 0.95, 100.0,
                            ?, ?, ?, ?, ?, ?, ?, 'manual_seed', 0.95)
                    """,
                    (rid, name, kcal, carbs, protein, fat, sugar, sodium, now),
                )
                inserted += 1
                print(f"  + inserted: {name}  ({kcal} kcal)")
        conn.commit()
    finally:
        conn.close()

    print()
    print(f"✅ inserted: {inserted}")
    print(f"   updated:  {updated}")
    print(f"   total seeded standard rows: {inserted + updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
