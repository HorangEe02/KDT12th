"""
통합 추천 엔진 v2 — NLP 감성 점수 보정 패치.

기존 Mini lunch-optimizer 의 가중 점수 공식에 감성 축(A1 SentimentAnalyzer
집계 결과)을 반영한다. 순수 함수 모음이며 SQLAlchemy/DB 의존성은 없다.

공식
----
v1 (기존):
    score = distance * 0.30 + weather * 0.20 + nutrition * 0.20 + team * 0.30

v2a (재가중 — 본 모듈의 기본):
    score = distance * 0.25 + weather * 0.15 + nutrition * 0.15
          + team * 0.25    + sentiment * 0.20

v2b (보정계수):
    score = v1_score * (1 + 0.15 * sentiment_score_norm)
    (sentiment_score_norm ∈ [-1, +1])

폴백
----
- sentiment 가 None 또는 review_count < MIN_SAMPLE → v1 공식 그대로 반환
- 각 입력 점수는 [0, 100] 범위를 기대하지만, 범위 밖 값도 clip 하여 허용
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict

# =============================================================================
# 상수
# =============================================================================
# v1 — 기존 가중치
W_V1 = {
    "distance": 0.30,
    "weather": 0.20,
    "nutrition": 0.20,
    "team": 0.30,
}

# v2a — 재가중 (감성 20%)
W_V2A = {
    "distance": 0.25,
    "weather": 0.15,
    "nutrition": 0.15,
    "team": 0.25,
    "sentiment": 0.20,
}

# v2b — 보정계수 (기존 공식에 1 + α·s 곱)
V2B_ALPHA = 0.15

# 최소 리뷰 수 — 이 미만이면 감성 결과를 신뢰하지 않고 v1 폴백
MIN_SAMPLE = 3


class SentimentInput(TypedDict, total=False):
    """scoring_patch 가 기대하는 sentiment dict 스키마."""
    score: float         # [-1, +1]  (aggregate 결과의 "score" 필드)
    pos_ratio: float     # [0, 1]
    neg_ratio: float
    neu_ratio: float
    review_count: int    # sample_size


# =============================================================================
# 유틸
# =============================================================================
def _clip(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """value 를 [lo, hi] 범위로 clamp."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return lo
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _sentiment_is_valid(sentiment: Optional[dict[str, Any]]) -> bool:
    """sentiment dict 가 신뢰할 만한지 판단."""
    if not sentiment:
        return False
    if sentiment.get("score") is None:
        return False
    rc = sentiment.get("review_count", sentiment.get("sample_size", 0))
    try:
        return int(rc) >= MIN_SAMPLE
    except (TypeError, ValueError):
        return False


def sentiment_score_0_100(sentiment: dict[str, Any]) -> float:
    """
    sentiment["score"] (-1~+1) → 0~100 스케일 변환.

    -1 → 0, 0 → 50, +1 → 100
    """
    raw = float(sentiment.get("score") or 0.0)
    raw = max(-1.0, min(1.0, raw))
    return (raw + 1.0) * 50.0


# =============================================================================
# 핵심 공식
# =============================================================================
def compute_composite_score_v1(
    distance: float,
    weather: float,
    nutrition: float,
    team: float,
) -> float:
    """기존 Mini v1 공식. scoring_patch_ab 와 테스트에서 재사용."""
    return (
        _clip(distance) * W_V1["distance"]
        + _clip(weather) * W_V1["weather"]
        + _clip(nutrition) * W_V1["nutrition"]
        + _clip(team) * W_V1["team"]
    )


def compute_composite_score_v2a(
    distance: float,
    weather: float,
    nutrition: float,
    team: float,
    sentiment_0_100: float,
) -> float:
    """v2a — 재가중 (감성 축 20%)."""
    return (
        _clip(distance) * W_V2A["distance"]
        + _clip(weather) * W_V2A["weather"]
        + _clip(nutrition) * W_V2A["nutrition"]
        + _clip(team) * W_V2A["team"]
        + _clip(sentiment_0_100) * W_V2A["sentiment"]
    )


def compute_composite_score_v2b(
    v1_score: float,
    sentiment_raw_score: float,
) -> float:
    """v2b — 보정계수. v1 * (1 + α·s), s ∈ [-1,+1]."""
    s = max(-1.0, min(1.0, float(sentiment_raw_score or 0.0)))
    return _clip(v1_score * (1.0 + V2B_ALPHA * s))


# =============================================================================
# 퍼블릭 API
# =============================================================================
def compute_composite_score_v2(
    restaurant: dict[str, Any],
    weather: dict[str, Any],
    nutrition: dict[str, Any],
    team: dict[str, Any],
    sentiment: Optional[dict[str, Any]] = None,
) -> float:
    """
    통합 추천 엔진 v2 진입점.

    Args:
        restaurant: {"distance_score": float, ...}
        weather:    {"score": float, ...}
        nutrition:  {"score": float, ...}
        team:       {"score": float, ...}
        sentiment:  {"score": float, "review_count": int, ...} | None

    Returns:
        0~100 범위의 종합 점수. sentiment 없으면 v1 공식.
    """
    dist = float(restaurant.get("distance_score", restaurant.get("score", 0)) or 0)
    wx = float(weather.get("score", 0) or 0)
    nt = float(nutrition.get("score", 0) or 0)
    tm = float(team.get("score", 0) or 0)

    if not _sentiment_is_valid(sentiment):
        return compute_composite_score_v1(dist, wx, nt, tm)

    assert sentiment is not None  # for type checker
    return compute_composite_score_v2a(
        dist, wx, nt, tm, sentiment_score_0_100(sentiment)
    )


__all__ = [
    "W_V1",
    "W_V2A",
    "V2B_ALPHA",
    "MIN_SAMPLE",
    "SentimentInput",
    "sentiment_score_0_100",
    "compute_composite_score_v1",
    "compute_composite_score_v2a",
    "compute_composite_score_v2b",
    "compute_composite_score_v2",
]
