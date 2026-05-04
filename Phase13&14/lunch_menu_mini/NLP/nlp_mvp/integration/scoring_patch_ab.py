"""
scoring_patch A/B — v1 / v2a / v2b 동시 계산 + 로그 기록.

실제 운영에서는 `scoring_patch.compute_composite_score_v2` 를 사용하고,
본 모듈은 비교 실험(A/B 로그 수집)용이다.

사용 예
-------
    from nlp_mvp.integration.scoring_patch_ab import compute_ab, ensure_schema, log_ab_sample
    from nlp_mvp.shared.db import get_engine

    ensure_schema(get_engine())
    result = compute_ab(
        restaurant_id="R001",
        distance=80, weather=60, nutrition=70, team=50,
        sentiment={"score": 0.6, "review_count": 12},
    )
    log_ab_sample(get_engine(), result)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from nlp_mvp.integration.scoring_patch import (
    _sentiment_is_valid,
    compute_composite_score_v1,
    compute_composite_score_v2a,
    compute_composite_score_v2b,
    sentiment_score_0_100,
)
from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 스키마 — ab_scoring_log
# =============================================================================
AB_LOG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ab_scoring_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    restaurant_id TEXT NOT NULL,
    v1 REAL NOT NULL,
    v2a REAL NOT NULL,
    v2b REAL NOT NULL,
    diff_a REAL NOT NULL,
    diff_b REAL NOT NULL,
    sentiment_score REAL,
    review_count INTEGER,
    valid INTEGER NOT NULL
)
""".strip()

AB_LOG_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_ab_scoring_log_restaurant "
    "ON ab_scoring_log(restaurant_id)"
)


def ensure_schema(engine: Optional[Engine] = None) -> None:
    """ab_scoring_log 테이블을 멱등하게 생성."""
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(text(AB_LOG_TABLE_SQL))
        conn.execute(text(AB_LOG_INDEX_SQL))
    logger.debug("ab_scoring_log schema ensured")


# =============================================================================
# 계산
# =============================================================================
def compute_ab(
    restaurant_id: str,
    distance: float,
    weather: float,
    nutrition: float,
    team: float,
    sentiment: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    세 공식(v1 / v2a / v2b) 을 한 번에 계산.

    Returns:
        {
          "restaurant_id": ...,
          "v1": float, "v2a": float, "v2b": float,
          "diff_a": v2a - v1, "diff_b": v2b - v1,
          "sentiment_score": float | None,
          "review_count": int,
          "valid": bool,              # sentiment 가 신뢰 가능한지
        }
    """
    v1 = compute_composite_score_v1(distance, weather, nutrition, team)

    valid = _sentiment_is_valid(sentiment)
    if valid and sentiment is not None:
        raw_s = float(sentiment.get("score") or 0.0)
        s_0_100 = sentiment_score_0_100(sentiment)
        rc = int(sentiment.get("review_count", sentiment.get("sample_size", 0)) or 0)
    else:
        raw_s = 0.0
        s_0_100 = 50.0  # neutral
        rc = 0

    v2a = compute_composite_score_v2a(distance, weather, nutrition, team, s_0_100)
    v2b = compute_composite_score_v2b(v1, raw_s)

    return {
        "restaurant_id": str(restaurant_id),
        "v1": round(v1, 4),
        "v2a": round(v2a, 4),
        "v2b": round(v2b, 4),
        "diff_a": round(v2a - v1, 4),
        "diff_b": round(v2b - v1, 4),
        "sentiment_score": raw_s if valid else None,
        "review_count": rc,
        "valid": valid,
    }


# =============================================================================
# 로깅
# =============================================================================
def log_ab_sample(
    engine: Optional[Engine],
    result: dict[str, Any],
) -> None:
    """compute_ab 결과를 ab_scoring_log 에 INSERT."""
    engine = engine or get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO ab_scoring_log
                        (created_at, restaurant_id, v1, v2a, v2b,
                         diff_a, diff_b, sentiment_score, review_count, valid)
                    VALUES
                        (:created_at, :rid, :v1, :v2a, :v2b,
                         :da, :db, :ss, :rc, :valid)
                    """
                ),
                {
                    "created_at": datetime.utcnow().isoformat(),
                    "rid": result["restaurant_id"],
                    "v1": result["v1"],
                    "v2a": result["v2a"],
                    "v2b": result["v2b"],
                    "da": result["diff_a"],
                    "db": result["diff_b"],
                    "ss": result["sentiment_score"],
                    "rc": result["review_count"],
                    "valid": 1 if result["valid"] else 0,
                },
            )
    except Exception as e:
        logger.warning(f"log_ab_sample failed: {e}")


def fetch_recent_samples(
    engine: Optional[Engine] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """최근 A/B 로그 조회 — NLP Insights 대시보드용."""
    engine = engine or get_engine()
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT restaurant_id, v1, v2a, v2b, diff_a, diff_b, "
                    "sentiment_score, review_count, created_at "
                    "FROM ab_scoring_log ORDER BY id DESC LIMIT :n"
                ),
                {"n": limit},
            ).mappings().fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"fetch_recent_samples failed: {e}")
        return []


__all__ = [
    "AB_LOG_TABLE_SQL",
    "ensure_schema",
    "compute_ab",
    "log_ab_sample",
    "fetch_recent_samples",
]
