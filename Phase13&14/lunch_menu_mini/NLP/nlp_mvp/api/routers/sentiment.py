"""
/nlp/sentiment/* 라우터.

- GET  /nlp/sentiment/{restaurant_id}
- GET  /nlp/sentiment/top
- POST /nlp/sentiment/refresh
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from sqlalchemy import text

from nlp_mvp.api.rate_limit import rate_limit
from nlp_mvp.api.schemas import (
    SentimentOut,
    SentimentRefreshIn,
    SentimentRefreshOut,
    SentimentTopItem,
)
from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp/sentiment", tags=["nlp-sentiment"])


# =============================================================================
# GET /nlp/sentiment/top  (먼저 선언 — /{restaurant_id} 와의 경로 충돌 방지)
# =============================================================================
@router.get("/top", response_model=list[SentimentTopItem])
def get_top(
    limit: int = Query(default=10, ge=1, le=100),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    min_reviews: int = Query(default=3, ge=0),
) -> list[SentimentTopItem]:
    """감성 점수 기준 상/하위 음식점 랭킹."""
    engine = get_engine()
    direction = "DESC" if order == "desc" else "ASC"
    sql = f"""
        SELECT id, name, sentiment_score, sentiment_pos_ratio,
               sentiment_sample_size
        FROM restaurants
        WHERE sentiment_score IS NOT NULL
          AND sentiment_sample_size >= :min_reviews
        ORDER BY sentiment_score {direction}
        LIMIT :limit
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(sql),
                {"min_reviews": min_reviews, "limit": limit},
            ).mappings().fetchall()
    except Exception as e:
        logger.warning(f"sentiment/top query failed: {e}")
        return []

    return [
        SentimentTopItem(
            restaurant_id=str(r["id"]),
            name=r.get("name"),
            score=float(r["sentiment_score"]),
            pos_ratio=float(r.get("sentiment_pos_ratio") or 0.0),
            review_count=int(r.get("sentiment_sample_size") or 0),
        )
        for r in rows
    ]


# =============================================================================
# GET /nlp/sentiment/{restaurant_id}
# =============================================================================
@router.get("/{restaurant_id}", response_model=SentimentOut)
def get_sentiment(restaurant_id: str) -> SentimentOut:
    """특정 음식점의 감성 점수·분포 반환. 데이터 없으면 0 기본값."""
    engine = get_engine()
    sql = """
        SELECT id, sentiment_score, sentiment_pos_ratio, sentiment_neg_ratio,
               sentiment_sample_size, sentiment_updated_at
        FROM restaurants
        WHERE id = :rid
        LIMIT 1
    """
    try:
        with engine.connect() as conn:
            row = conn.execute(text(sql), {"rid": restaurant_id}).mappings().fetchone()
    except Exception as e:
        logger.warning(f"sentiment/{restaurant_id} query failed: {e}")
        row = None

    if row is None:
        return SentimentOut(restaurant_id=restaurant_id)

    pos = float(row.get("sentiment_pos_ratio") or 0.0)
    neg = float(row.get("sentiment_neg_ratio") or 0.0)
    neu = max(0.0, 1.0 - pos - neg)
    return SentimentOut(
        restaurant_id=str(row["id"]),
        score=row.get("sentiment_score"),
        pos_ratio=pos,
        neg_ratio=neg,
        neu_ratio=neu,
        review_count=int(row.get("sentiment_sample_size") or 0),
        updated_at=str(row["sentiment_updated_at"])
        if row.get("sentiment_updated_at")
        else None,
    )


# =============================================================================
# POST /nlp/sentiment/refresh  (BackgroundTasks)
# =============================================================================
def _run_refresh_bg(payload: SentimentRefreshIn) -> None:
    """백그라운드 작업: 감성분석 파이프라인 실행."""
    try:
        from nlp_mvp.sentiment.update_db import run_sentiment_update
    except Exception as e:
        logger.error(f"sentiment.update_db import failed: {e}")
        return

    try:
        stats = run_sentiment_update(
            limit=payload.limit,
            min_reviews=payload.min_reviews,
            source=payload.source,  # type: ignore[arg-type]
            skip_model_load=payload.skip_model_load,
        )
        logger.info(f"sentiment refresh done: {stats}")
    except Exception as e:
        logger.exception(f"sentiment refresh failed: {e}")


@router.post("/refresh", response_model=SentimentRefreshOut, status_code=202)
@rate_limit("2/minute")  # #5 — DB 전체 스캔이라 아주 강하게 제한
def refresh(
    request: Request,
    payload: SentimentRefreshIn,
    background_tasks: BackgroundTasks,
) -> SentimentRefreshOut:
    """감성분석 파이프라인을 비동기로 큐잉."""
    background_tasks.add_task(_run_refresh_bg, payload)
    return SentimentRefreshOut(
        queued=True,
        limit=payload.limit,
        source=payload.source,
        message="sentiment refresh queued",
    )
