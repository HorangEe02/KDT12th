"""
/nlp/v2/* — Phase 6 research v2 router (A2 / B2 / E1).

Strategy:
- A2 ABSA  → uses `nlp_research.models.absa.inference.load_inferencer`
- B2 NER   → uses `nlp_research.models.food_ner.inference.load_inferencer`
- E1 CF    → uses `nlp_research.models.embedding_cf.recommender` (with synthetic
              fallback when meal_history is empty)

Without trained weights, the inferencers return rule-based / dummy results
(`backend` field reflects which path was taken).

Models can be force-disabled by setting NLP_V2_DISABLE=1 — endpoints then
respond with 503 to signal "weights pending".
"""
from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from nlp_mvp.api.schemas import (
    V2ABSAOut,
    V2AspectSentiment,
    V2MenuExtractIn,
    V2MenuExtractOut,
    V2NEREntity,
    V2RecommendItem,
    V2RecommendOut,
)
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp/v2", tags=["nlp-research-v2"])


def _disabled() -> bool:
    return os.getenv("NLP_V2_DISABLE", "0") == "1"


def _maybe_503() -> None:
    if _disabled():
        raise HTTPException(
            status_code=503,
            detail="research v2 disabled (NLP_V2_DISABLE=1)",
        )


# Module-level inferencer cache. Loading a 430-500MB checkpoint takes ~8s
# (CPU torch + safetensors), so we keep the inferencer warm across requests.
# Lazy: first request after process start triggers the load.
_absa_inf: Optional[Any] = None
_ner_inf: Optional[Any] = None


def _get_absa_inferencer():
    global _absa_inf
    if _absa_inf is None:
        from nlp_research.models.absa.inference import load_inferencer
        _absa_inf = load_inferencer(model_path=None)
    return _absa_inf


def _get_ner_inferencer():
    global _ner_inf
    if _ner_inf is None:
        from nlp_research.models.food_ner.inference import load_inferencer
        _ner_inf = load_inferencer(model_path=None)
    return _ner_inf


# =============================================================================
# A2 ABSA
# =============================================================================
@router.get("/sentiment/{restaurant_id}", response_model=V2ABSAOut)
def absa(restaurant_id: str) -> V2ABSAOut:
    """
    Aspect-based sentiment for a restaurant.

    Priority:
      1. restaurant_absa 테이블에 시드된 데이터가 있으면 그것을 반환 (backend="seeded")
      2. 학습된 가중치가 있으면 ABSAInferencer 로 실시간 추론 (backend="trained")
      3. 둘 다 없으면 deterministic dummy (backend="dummy")
    """
    _maybe_503()

    # ── Priority 1: restaurant_absa table ──
    try:
        from nlp_mvp.shared.db import get_engine
        from sqlalchemy import text as sql_text

        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                sql_text(
                    "SELECT aspect, sentiment, confidence, score FROM restaurant_absa "
                    "WHERE restaurant_id = :rid ORDER BY aspect"
                ),
                {"rid": str(restaurant_id)},
            ).mappings().fetchall()
        if rows:
            aspects = [
                V2AspectSentiment(
                    aspect=str(r["aspect"]),
                    sentiment=str(r["sentiment"]),
                    confidence=float(r.get("confidence") or 0.0),
                    score=float(r.get("score") or 0.0),
                )
                for r in rows
            ]
            return V2ABSAOut(
                restaurant_id=restaurant_id,
                aspects=aspects,
                backend="seeded",
            )
    except Exception as e:
        logger.info(f"restaurant_absa table read skipped: {e}")

    try:
        from nlp_research.models.absa.inference import ABSAInferencer
    except ImportError as e:
        logger.warning(f"nlp_research not importable: {e}")
        raise HTTPException(
            status_code=503,
            detail="nlp_research package missing — install requirements first",
        )

    # Sample text proxy: pull a recent review for this restaurant if available.
    text = _fetch_sample_review_text(restaurant_id) or "맛있고 친절합니다"
    inf = _get_absa_inferencer()
    backend = "trained" if isinstance(inf, ABSAInferencer) else "dummy"

    def _synth_score(sentiment: str, conf: float) -> float:
        # Trained ABSA inferencer returns sentiment + confidence only;
        # synthesize a signed score in [-1, 1] for the Insights radar UI.
        if sentiment == "positive":
            return round(conf, 3)
        if sentiment == "negative":
            return round(-conf, 3)
        return 0.0

    aspects = [
        V2AspectSentiment(
            aspect=p["aspect"],
            sentiment=p["sentiment"],
            confidence=float(p.get("confidence", 0.0)),
            score=_synth_score(p["sentiment"], float(p.get("confidence", 0.0))),
        )
        for p in inf.predict(text)
    ]
    return V2ABSAOut(
        restaurant_id=restaurant_id,
        aspects=aspects,
        backend=backend,
    )


def _fetch_sample_review_text(restaurant_id: str) -> Optional[str]:
    """Best-effort: read one review for the restaurant from Phase 5 reviews table."""
    try:
        from sqlalchemy import text
        from nlp_mvp.shared.db import get_engine
        eng = get_engine()
        with eng.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT text FROM reviews WHERE restaurant_id = :rid "
                    "ORDER BY id DESC LIMIT 1"
                ),
                {"rid": restaurant_id},
            ).fetchone()
        return row[0] if row else None
    except Exception:
        return None


# =============================================================================
# B2 Food NER
# =============================================================================
@router.post("/menu/extract", response_model=V2MenuExtractOut)
def menu_extract(payload: V2MenuExtractIn) -> V2MenuExtractOut:
    """Extract food entities (DISH/INGREDIENT/FLAVOR/...) from text."""
    _maybe_503()
    try:
        from nlp_research.models.food_ner.inference import FoodNERInferencer
    except ImportError:
        raise HTTPException(
            status_code=503, detail="nlp_research package missing"
        )

    inf = _get_ner_inferencer()
    backend = "trained" if isinstance(inf, FoodNERInferencer) else "rule_based"
    ents = [
        V2NEREntity(
            type=e["type"],
            value=e["value"],
            start_token=int(e.get("start_token", 0)),
            end_token=int(e.get("end_token", 0)),
        )
        for e in inf.predict(payload.text)
    ]
    return V2MenuExtractOut(
        text=payload.text,
        entities=ents,
        backend=backend,
    )


# =============================================================================
# E1 Embedding CF
# =============================================================================
@router.get("/recommend", response_model=V2RecommendOut)
def recommend(
    user_id: str = Query(min_length=1, max_length=128),
    top_n: int = Query(default=5, ge=1, le=20),
) -> V2RecommendOut:
    """Personalised menu recommendations (Embedding CF).

    Accepts arbitrary auth user IDs (e.g. ``admin-b3a54b99`` or numeric ``"1"``).
    For string IDs without DB meal_history, falls back to a synthetic 5-user
    profile so the demo always returns something useful.
    """
    _maybe_503()
    try:
        from nlp_research.models.embedding_cf.recommender import (
            EmbeddingCFRecommender,
            MealHistorySource,
        )
    except ImportError:
        raise HTTPException(
            status_code=503, detail="nlp_research package missing"
        )

    # Coerce numeric strings ("1") so they line up with synthetic user IDs.
    lookup_id: Any = user_id
    if isinstance(user_id, str) and user_id.isdigit():
        lookup_id = int(user_id)

    # `is_cold_start` flips off the "exclude_visited" filter so cold-start
    # surrogate users (auth IDs without DB history) still get recommendations
    # — otherwise the synthetic users have eaten everything in the 12-menu pool
    # and the result list is always empty.
    is_cold_start = False

    # Try real DB first; fall back to synthetic 5-user mock
    # The DB needs ≥ 2 users for CF to work (otherwise the only similar user is
    # the target itself, which is filtered out). For single-user DBs we still
    # use the requested user's tastes via synthetic-pool cold start.
    MIN_DB_USERS = 2
    try:
        source = MealHistorySource.from_db()
        all_ids = source.get_all_user_ids()
        if not all_ids:
            raise RuntimeError("empty meal_history")
        if len(all_ids) < MIN_DB_USERS:
            logger.info(
                f"E1 meal_history has {len(all_ids)} user(s) — "
                f"merging real history with synthetic peer pool"
            )
            # Keep the user's real history (so recs are personalised) and
            # graft on synthetic peers so CF has someone to compare against.
            real_history = {uid: source.get_user(uid) for uid in all_ids}
            synth = MealHistorySource.synthetic(n_users=5)
            merged = dict(synth.meal_history)
            merged.update(real_history)
            source = MealHistorySource(merged)
            # If the requested user is one of the real users, keep their id;
            # otherwise treat as cold-start.
            if lookup_id not in real_history:
                lookup_id = "__cold_start__"
                is_cold_start = True
        elif lookup_id not in all_ids:
            # If the requested user has no history, use synthetic so we don't
            # return an empty recommendation list.
            logger.info(
                f"E1 user_id={user_id!r} not in meal_history; "
                f"using synthetic source as cold-start surrogate"
            )
            source = MealHistorySource.synthetic(n_users=5)
            lookup_id = "__cold_start__"
            is_cold_start = True
        backend = "embedding_cf"
    except Exception as e:
        logger.info(f"E1 falling back to synthetic source: {e}")
        source = MealHistorySource.synthetic(n_users=5)
        if not (isinstance(lookup_id, int) and 1 <= lookup_id <= 5):
            lookup_id = "__cold_start__"
            is_cold_start = True
        backend = "embedding_cf"  # still embedding-based, just over mock data

    rec = EmbeddingCFRecommender(source, prefer_faiss=False)
    rec.build_index()
    items = rec.recommend(
        user_id=lookup_id,
        top_n_menus=top_n,
        exclude_visited=not is_cold_start,
    )
    return V2RecommendOut(
        user_id=str(user_id),
        recommendations=[
            V2RecommendItem(
                menu=str(it["menu"]),
                restaurant=str(it.get("restaurant") or "") or None,
                score=float(it.get("score", 0.0)),
                similar_user_count=int(it.get("similar_user_count", 0)),
                reason=str(it.get("reason") or "") or None,
            )
            for it in items
        ],
        backend=backend,
    )
