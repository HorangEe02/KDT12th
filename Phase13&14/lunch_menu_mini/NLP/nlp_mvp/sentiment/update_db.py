"""
A1 감성분석 — DB 스키마 확장 + 통합 파이프라인 + CLI.

- ensure_schema(engine): restaurants 컬럼 5개 + reviews 테이블 추가 (멱등)
- run_sentiment_update(...): 수집→전처리→분석→집계→DB UPSERT
- CLI: --limit / --min-reviews / --dry-run / --source
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from nlp_mvp.sentiment import preprocess
from nlp_mvp.sentiment.crawler import (
    AIHubSource, KakaoPublicSource, ReviewCrawler, SyntheticSource
)
from nlp_mvp.shared.db import get_engine, get_session
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 스키마 마이그레이션
# =============================================================================
REQUIRED_COLUMNS: dict[str, str] = {
    "sentiment_score": "REAL DEFAULT NULL",
    "sentiment_pos_ratio": "REAL DEFAULT NULL",
    "sentiment_neg_ratio": "REAL DEFAULT NULL",
    "sentiment_sample_size": "INTEGER DEFAULT 0",
    "sentiment_updated_at": "DATETIME DEFAULT NULL",
}

REVIEWS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id TEXT NOT NULL,
    source TEXT NOT NULL,
    text TEXT NOT NULL,
    sentiment_label TEXT,
    sentiment_confidence REAL,
    external_id TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (restaurant_id, source, text)
)
""".strip()

REVIEWS_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_reviews_restaurant ON reviews(restaurant_id)",
    "CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source)",
]


def ensure_schema(engine: Optional[Engine] = None) -> None:
    """
    restaurants 테이블에 감성 컬럼 5개 추가 + reviews 테이블 생성. 멱등.
    """
    engine = engine or get_engine()
    with engine.begin() as conn:
        # 현재 restaurants 컬럼 조회
        existing = {
            row[1] for row in conn.execute(text("PRAGMA table_info(restaurants)"))
        }
        if not existing:
            raise RuntimeError(
                "restaurants table not found. "
                "Run lunch-optimizer Subtopic 1 pipeline first or seed the DB."
            )

        # 누락된 컬럼만 추가
        for col, col_def in REQUIRED_COLUMNS.items():
            if col not in existing:
                logger.info("Adding column: restaurants.%s", col)
                conn.execute(
                    text(f"ALTER TABLE restaurants ADD COLUMN {col} {col_def}")
                )

        # reviews 테이블
        conn.execute(text(REVIEWS_TABLE_SQL))
        for idx_sql in REVIEWS_INDEX_SQL:
            conn.execute(text(idx_sql))

    logger.info("ensure_schema() done")


# =============================================================================
# Crawler builder
# =============================================================================
SourceName = Literal["synthetic", "aihub", "kakao_public"]


def _build_crawler(source: SourceName) -> ReviewCrawler:
    mapping: dict[str, list] = {
        "synthetic":    [SyntheticSource()],
        "aihub":        [AIHubSource(), SyntheticSource()],  # fallback
        "kakao_public": [KakaoPublicSource(), SyntheticSource()],
    }
    return ReviewCrawler(mapping[source])


# =============================================================================
# 메인 파이프라인
# =============================================================================
def run_sentiment_update(
    limit: Optional[int] = None,
    min_reviews: int = 5,
    dry_run: bool = False,
    source: SourceName = "synthetic",
    refresh_after_days: int = 7,
    skip_model_load: bool = False,
) -> dict[str, Any]:
    """
    A1 감성분석 통합 파이프라인.

    Args:
        limit: 처리할 최대 식당 수
        min_reviews: 최소 리뷰 수 (미달 시 score NULL 유지)
        dry_run: True 면 DB 쓰기 없이 집계 결과만 로그
        source: 데이터 소스 선택
        refresh_after_days: 이 일수보다 오래된 식당만 재처리
        skip_model_load: True 면 감성분석 스킵 (스키마만 검증)

    Returns:
        {"processed": N, "updated": M, "skipped": K, "errors": E, "duration_sec": T}
    """
    start = time.time()
    stats: dict[str, Any] = {
        "processed": 0, "updated": 0, "skipped": 0, "errors": 0,
    }

    engine = get_engine()
    ensure_schema(engine)

    crawler = _build_crawler(source)

    # Lazy model loading (테스트·dry-run 에서 torch 미설치 허용)
    analyzer = None
    if not skip_model_load:
        try:
            from nlp_mvp.sentiment.sentiment_pipeline import get_default_analyzer
            analyzer = get_default_analyzer()
        except ImportError as e:
            logger.warning("Model load skipped (transformers/torch missing): %s", e)
            skip_model_load = True

    # 대상 식당 선정
    cutoff = (datetime.utcnow() - timedelta(days=refresh_after_days)).isoformat()
    query = text("""
        SELECT id FROM restaurants
        WHERE sentiment_updated_at IS NULL
           OR sentiment_updated_at < :cutoff
        ORDER BY id
        LIMIT :limit
    """)
    with get_session() as session:
        rows = session.execute(
            query,
            {"cutoff": cutoff, "limit": limit if limit is not None else 10 ** 9},
        ).fetchall()
        restaurant_ids = [row[0] for row in rows]

    logger.info("Target restaurants: %d (source=%s)", len(restaurant_ids), source)

    for rest_id in restaurant_ids:
        stats["processed"] += 1
        try:
            # ① 수집
            # restaurant_id 가 문자열일 수 있으므로 crawler 는 해시 가능한 값 필요
            # SyntheticSource 는 int 를 기대하므로 hash 변환
            rid_int = hash(rest_id) & 0x7FFFFFFF
            raw_reviews = crawler.fetch_reviews(rid_int, max_count=50)

            # ② 전처리
            cleaned = [
                {**r, "text": preprocess.clean_text(r.get("text", ""))}
                for r in raw_reviews
            ]
            valid = [r for r in cleaned if preprocess.is_valid_review(r["text"])]
            unique = preprocess.deduplicate(valid)

            if len(unique) < min_reviews:
                stats["skipped"] += 1
                logger.info(
                    "restaurant %s: skipped (%d < %d)",
                    rest_id, len(unique), min_reviews,
                )
                continue

            # ③ 감성분석
            if skip_model_load or analyzer is None:
                logger.info(
                    "restaurant %s: model load skipped → dry simulation",
                    rest_id,
                )
                # 시뮬레이션: 모두 neutral 로 처리 (집계만 검증)
                analyses = [
                    {"label": "neutral", "confidence": 0.5}
                    for _ in unique
                ]
            else:
                analyses = analyzer.analyze_batch([r["text"] for r in unique])

            # ④ 집계
            from nlp_mvp.sentiment.sentiment_pipeline import aggregate
            agg = aggregate(analyses, min_sample=min_reviews)
            if agg["score"] is None:
                stats["skipped"] += 1
                continue

            # ⑤ DB 쓰기
            if not dry_run:
                with get_session() as sess:
                    # reviews INSERT (중복 방지)
                    for review, result in zip(unique, analyses):
                        sess.execute(
                            text("""
                                INSERT OR IGNORE INTO reviews
                                    (restaurant_id, source, text,
                                     sentiment_label, sentiment_confidence,
                                     external_id, fetched_at)
                                VALUES
                                    (:rid, :src, :txt, :lbl, :conf, :eid, :ft)
                            """),
                            {
                                "rid": str(rest_id),
                                "src": review.get("source", "unknown"),
                                "txt": review["text"],
                                "lbl": result["label"],
                                "conf": result["confidence"],
                                "eid": review.get("external_id"),
                                "ft": review.get("fetched_at"),
                            },
                        )
                    # restaurants UPDATE
                    sess.execute(
                        text("""
                            UPDATE restaurants
                            SET sentiment_score = :score,
                                sentiment_pos_ratio = :pos,
                                sentiment_neg_ratio = :neg,
                                sentiment_sample_size = :size,
                                sentiment_updated_at = :ts
                            WHERE id = :rid
                        """),
                        {
                            "score": agg["score"],
                            "pos": agg["pos_ratio"],
                            "neg": agg["neg_ratio"],
                            "size": agg["sample_size"],
                            "ts": datetime.utcnow().isoformat(),
                            "rid": rest_id,
                        },
                    )
                    sess.commit()

            stats["updated"] += 1
            logger.info(
                "restaurant %s: score=%.3f (pos=%.2f neg=%.2f n=%d)",
                rest_id, agg["score"], agg["pos_ratio"],
                agg["neg_ratio"], agg["sample_size"],
            )

        except Exception as e:
            stats["errors"] += 1
            logger.exception("restaurant %s failed: %s", rest_id, e)

    stats["duration_sec"] = round(time.time() - start, 2)
    logger.info("run_sentiment_update done: %s", stats)
    return stats


# =============================================================================
# CLI
# =============================================================================
def main() -> None:
    parser = argparse.ArgumentParser(description="Mini A1 Sentiment Update")
    parser.add_argument("--limit", type=int, default=None, help="처리 식당 최대 수")
    parser.add_argument("--min-reviews", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--source",
        choices=["synthetic", "aihub", "kakao_public"],
        default="synthetic",
    )
    parser.add_argument("--refresh-after-days", type=int, default=7)
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="감성분석 스킵 (transformers 미설치 환경에서 DB 파이프라인만 검증)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    stats = run_sentiment_update(
        limit=args.limit,
        min_reviews=args.min_reviews,
        dry_run=args.dry_run,
        source=args.source,
        refresh_after_days=args.refresh_after_days,
        skip_model_load=args.skip_model,
    )
    print(stats)


if __name__ == "__main__":
    main()
