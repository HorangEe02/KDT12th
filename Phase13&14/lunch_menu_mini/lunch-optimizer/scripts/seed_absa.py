"""ABSA(측면별 감성) 합성 시드.

restaurant_absa 테이블에 sentiment_score 가 있는 식당들에 대해
5개 측면(taste/service/price/hygiene/ambience)별 합성 점수를 시드한다.

각 측면은 base sentiment_score 에 가우시안 노이즈를 더해 식당별로
다른 측면 강점/약점을 갖도록 함.

사용:
    docker exec mini-lunch-api python /tmp/seed_absa.py
"""
from __future__ import annotations

import os
import random
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")
SEED_RANDOM = int(os.environ.get("SEED_RANDOM", "42"))

ASPECTS = ["taste", "service", "price", "hygiene", "ambience"]
# 카테고리별 측면 가중치 (한식은 taste 강점, 카페는 ambience 강점 등 — 시드 다양성)
CATEGORY_BIAS = {
    "한식":   {"taste": +0.10, "price": +0.05, "service": -0.05, "hygiene":  0.0, "ambience": -0.05},
    "양식":   {"taste": +0.05, "price": -0.10, "service": +0.05, "hygiene": +0.05, "ambience": +0.10},
    "일식":   {"taste": +0.10, "price": -0.05, "service": +0.05, "hygiene": +0.10, "ambience":  0.0},
    "중식":   {"taste": +0.05, "price": +0.05, "service": -0.10, "hygiene":  0.0, "ambience": -0.10},
    "분식":   {"taste":  0.0,  "price": +0.20, "service": -0.05, "hygiene": -0.10, "ambience": -0.15},
    "치킨":   {"taste": +0.10, "price":  0.0,  "service": +0.05, "hygiene": +0.05, "ambience":  0.0},
    "술집":   {"taste":  0.0,  "price": -0.10, "service":  0.0,  "hygiene": -0.10, "ambience": +0.10},
    "카페":   {"taste":  0.0,  "price": -0.15, "service": +0.05, "hygiene": +0.05, "ambience": +0.20},
}
DEFAULT_BIAS = {a: 0.0 for a in ASPECTS}


def _classify(score: float) -> str:
    if score >= 0.2:
        return "positive"
    if score <= -0.15:
        return "negative"
    return "neutral"


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    random.seed(SEED_RANDOM)
    print(f"DB: {DB_PATH}")
    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        # 시드 대상: sentiment_score 있는 식당 모두
        cur = conn.execute(
            """
            SELECT id, name, category, sentiment_score, sentiment_sample_size
            FROM restaurants
            WHERE sentiment_score IS NOT NULL
            """
        )
        rows = cur.fetchall()
        print(f"  target restaurants: {len(rows)}")

        inserted = 0
        updated = 0
        for rid, name, cat, base_score, sample_size in rows:
            bias = CATEGORY_BIAS.get(cat or "", DEFAULT_BIAS)
            for aspect in ASPECTS:
                # 기본 점수 = sentiment_score + 카테고리 측면 편향 + Gaussian 노이즈
                noise = random.gauss(0, 0.12)
                score = max(-0.95, min(0.95, base_score + bias.get(aspect, 0.0) + noise))
                sentiment = _classify(score)
                # confidence: dummy 와 비슷한 분포 0.55–0.85
                confidence = round(min(0.95, 0.55 + abs(score) * 0.4 + random.gauss(0, 0.05)), 4)
                ss = sample_size or random.randint(5, 30)

                # UPSERT
                cur2 = conn.execute(
                    "SELECT id FROM restaurant_absa WHERE restaurant_id=? AND aspect=?",
                    (str(rid), aspect),
                )
                if cur2.fetchone():
                    conn.execute(
                        """
                        UPDATE restaurant_absa SET
                            sentiment=?, score=?, confidence=?, sample_size=?, updated_at=?
                        WHERE restaurant_id=? AND aspect=?
                        """,
                        (sentiment, round(score, 3), confidence, ss, now, str(rid), aspect),
                    )
                    updated += 1
                else:
                    conn.execute(
                        """
                        INSERT INTO restaurant_absa
                            (restaurant_id, aspect, sentiment, score, confidence, sample_size, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (str(rid), aspect, sentiment, round(score, 3), confidence, ss, now),
                    )
                    inserted += 1
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM restaurant_absa").fetchone()[0]
        print(f"\n✅ inserted: {inserted}, updated: {updated}, total rows: {total}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
