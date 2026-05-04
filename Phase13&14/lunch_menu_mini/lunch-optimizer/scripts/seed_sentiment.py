"""감성 분석 합성 시드 (KcELECTRA 추론 시간 비용 회피용).

실행 시 식당 100개 샘플에 대해 카테고리·평점 분포 기반 가짜 sentiment를
생성해 nutrition Insights 페이지의 SentimentOverview 차트가 시연 가능하도록
즉시 채운다.

향후 `/nlp/sentiment/refresh` 엔드포인트가 실 KcELECTRA 추론으로 덮어씀.

사용:
    docker exec mini-lunch-api python /tmp/seed_sentiment.py
옵션:
    SAMPLE_SIZE=200   (기본 100)
    SEED_RANDOM=42    (재현용)
"""
from __future__ import annotations

import os
import random
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")
SAMPLE_SIZE = int(os.environ.get("SAMPLE_SIZE", "100"))
SEED_RANDOM = int(os.environ.get("SEED_RANDOM", "42"))

# 카테고리별 sentiment 평균 (현실적 인기도 기반):
#   한식 0.45 / 양식 0.55 / 일식 0.50 / 중식 0.40 / 분식 0.55 / 술집 0.30 / 카페 0.60
CATEGORY_BIAS = {
    "한식": 0.45,
    "양식": 0.55,
    "일식": 0.50,
    "중식": 0.40,
    "분식": 0.55,
    "술집": 0.30,
    "패스트푸드": 0.45,
    "도시락": 0.50,
    "치킨": 0.65,
    "샐러드": 0.60,
    "야식": 0.40,
    "기사식당": 0.35,
    "샤브샤브": 0.55,
    "퓨전": 0.50,
    "뷔페": 0.40,
    "간식": 0.55,
    "아시아음식": 0.50,
}
DEFAULT_BIAS = 0.45


def _gauss_clamp(mean: float, sigma: float, lo: float, hi: float) -> float:
    """가우시안 분포 + 클램프."""
    val = random.gauss(mean, sigma)
    return max(lo, min(hi, val))


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    random.seed(SEED_RANDOM)
    print(f"DB: {DB_PATH}")
    print(f"sample size: {SAMPLE_SIZE}")
    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        # 컬럼 존재 확인
        cols = {r[1] for r in conn.execute("PRAGMA table_info(restaurants)").fetchall()}
        required = {"sentiment_score", "sentiment_pos_ratio", "sentiment_sample_size"}
        missing = required - cols
        if missing:
            print(
                f"[error] restaurants 테이블에 컬럼 누락: {missing}. "
                "먼저 migrate_sentiment_columns.py 실행.",
                file=sys.stderr,
            )
            return 1

        # 평점 ≥ 3.0 식당 중 무작위 SAMPLE_SIZE 추출 (현실적 — 평가가 있는 식당)
        cur = conn.execute(
            """
            SELECT id, name, category, rating
            FROM restaurants
            WHERE is_active = 1
              AND (rating IS NULL OR rating >= 3.0)
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (SAMPLE_SIZE,),
        )
        rows = cur.fetchall()
        print(f"  picked {len(rows)} restaurants")

        updated = 0
        for r in rows:
            rid, name, category, rating = r
            cat = category or ""
            base = CATEGORY_BIAS.get(cat, DEFAULT_BIAS)

            # 평점이 있으면 1.0 ~ 5.0 → -0.5 ~ +0.5 보정에 가중
            rating_adj = 0.0
            if rating is not None:
                rating_adj = (float(rating) - 3.5) * 0.18  # 3.5점 기준

            score = _gauss_clamp(base + rating_adj, sigma=0.18, lo=-0.85, hi=0.95)
            # pos_ratio: score 가 +1 이면 ~0.92, -1 이면 ~0.10 으로 매핑
            pos_ratio = max(0.05, min(0.95, 0.5 + score * 0.45))
            sample_size = random.randint(5, 35)

            conn.execute(
                """
                UPDATE restaurants SET
                    sentiment_score = ?,
                    sentiment_pos_ratio = ?,
                    sentiment_sample_size = ?,
                    sentiment_updated_at = ?
                WHERE id = ?
                """,
                (round(score, 3), round(pos_ratio, 3), sample_size, now, rid),
            )
            updated += 1

        conn.commit()

        # 통계 출력
        stat = conn.execute(
            """
            SELECT
                COUNT(*) AS n,
                ROUND(AVG(sentiment_score), 3) AS avg_score,
                ROUND(MIN(sentiment_score), 3) AS min_s,
                ROUND(MAX(sentiment_score), 3) AS max_s
            FROM restaurants
            WHERE sentiment_score IS NOT NULL
            """
        ).fetchone()
        print(f"\n✅ updated: {updated}")
        print(f"   total w/ sentiment: {stat[0]}")
        print(f"   avg score: {stat[1]}, min: {stat[2]}, max: {stat[3]}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
