"""
/nlp/menu/* 라우터.

- POST /nlp/menu/normalize
- GET  /nlp/menu/stats
"""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from nlp_mvp.api.schemas import MenuNormalizeIn, MenuNormalizeOut, MenuStatsOut
from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp/menu", tags=["nlp-menu"])


# =============================================================================
# 싱글톤 캐시 (lifespan 에서 주입 가능)
# =============================================================================
_normalizer = None


def get_normalizer():
    """MenuNormalizer 싱글톤. 지연 로딩."""
    global _normalizer
    if _normalizer is None:
        from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer
        try:
            _normalizer = MenuNormalizer(enable_embedding=False)
        except Exception as e:
            logger.warning(f"MenuNormalizer init with embedding disabled failed: {e}")
            raise
    return _normalizer


def set_normalizer(normalizer) -> None:
    """lifespan 에서 미리 로드한 인스턴스를 주입할 때 사용."""
    global _normalizer
    _normalizer = normalizer


# =============================================================================
# POST /nlp/menu/normalize
# =============================================================================
@router.post("/normalize", response_model=MenuNormalizeOut)
def normalize(payload: MenuNormalizeIn) -> MenuNormalizeOut:
    try:
        normalizer = get_normalizer()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"normalizer unavailable: {e}")

    start = time.time()
    result = normalizer.normalize(payload.raw_name)
    latency_ms = int((time.time() - start) * 1000)

    return MenuNormalizeOut(
        raw=result.raw,
        cleaned=result.cleaned,
        matched_id=result.matched_id,
        matched_name=result.matched_name,
        confidence=result.confidence,
        method=result.method,  # type: ignore[arg-type]
        latency_ms=latency_ms,
    )


# =============================================================================
# GET /nlp/menu/stats
# =============================================================================
@router.get("/stats", response_model=MenuStatsOut)
def stats() -> MenuStatsOut:
    """메뉴 정규화 통계 — menu_normalization + meal_items 두 소스 합산.

    - menu_normalization: 명시적 정규화 호출 캐시 (있으면)
    - meal_items: 자연어 영양 입력에서 누적된 match_type
    두 소스를 union 해 method/match_type 별 카운트 + hit_rate 계산.
    """
    engine = get_engine()
    by_method: dict[str, int] = {}

    # source A: menu_normalization
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT method, COUNT(*) AS n FROM menu_normalization "
                    "GROUP BY method"
                )
            ).mappings().fetchall()
        for r in rows:
            k = r["method"] or "unknown"
            by_method[k] = by_method.get(k, 0) + int(r["n"])
    except Exception as e:
        logger.info(f"menu_normalization table not available: {e}")

    # source B: meal_items (자연어 영양 입력)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT match_type AS method, COUNT(*) AS n FROM meal_items "
                    "WHERE match_type IS NOT NULL GROUP BY match_type"
                )
            ).mappings().fetchall()
        for r in rows:
            k = r["method"] or "unknown"
            by_method[k] = by_method.get(k, 0) + int(r["n"])
    except Exception as e:
        logger.info(f"meal_items table not available: {e}")

    total = sum(by_method.values())
    # hit = 명확하게 매칭된 method (rule, levenshtein, embedding, nlp_parse, local_food_name 등)
    UNVERIFIED = {"unverified", "unknown", "user_added", "manual", None}
    hit = sum(v for k, v in by_method.items() if k not in UNVERIFIED)
    return MenuStatsOut(
        total=total,
        by_method=by_method,
        hit_rate=(hit / total) if total > 0 else 0.0,
    )
