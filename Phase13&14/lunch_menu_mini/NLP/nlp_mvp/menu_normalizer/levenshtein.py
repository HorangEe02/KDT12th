"""
Levenshtein 기반 후보 검색.

`python-Levenshtein` 미설치 시 `difflib.SequenceMatcher` 폴백.
"""
from __future__ import annotations

from typing import Any

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# python-Levenshtein 우선, 없으면 difflib 폴백
try:
    import Levenshtein as _lev  # type: ignore

    def _distance(a: str, b: str) -> int:
        return _lev.distance(a, b)

    _BACKEND = "python-Levenshtein"
except ImportError:
    def _distance(a: str, b: str) -> int:
        # 표준 Levenshtein DP (한국어 짧은 문자열 기준 충분히 빠름)
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, start=1):
            curr = [i] + [0] * len(b)
            for j, cb in enumerate(b, start=1):
                cost = 0 if ca == cb else 1
                curr[j] = min(
                    curr[j - 1] + 1,
                    prev[j] + 1,
                    prev[j - 1] + cost,
                )
            prev = curr
        return prev[-1]

    _BACKEND = "difflib-fallback"

logger.debug(f"Levenshtein backend: {_BACKEND}")


def adaptive_cutoff(target_len: int) -> int:
    """길이에 따른 편집거리 임계값."""
    if target_len <= 3:
        return 1
    elif target_len <= 6:
        return 2
    else:
        return 3


def distance_to_confidence(distance: int, target_len: int) -> float:
    """편집거리 → confidence 점수 (0~1)."""
    if target_len == 0:
        return 0.0
    return max(0.0, 1.0 - distance / target_len)


def find_candidates(
    query: str,
    standard_menus: list[dict[str, Any]],
    cutoff: int | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    편집거리 기반 후보 검색.

    Returns confidence 내림차순.
    """
    if not query or not standard_menus:
        return []

    if cutoff is None:
        cutoff = adaptive_cutoff(len(query))

    candidates = []
    for menu in standard_menus:
        name = menu["name"]
        dist = _distance(query, name)
        if dist <= cutoff:
            conf = distance_to_confidence(dist, max(len(query), len(name)))
            candidates.append({
                "id": menu["id"],
                "name": name,
                "distance": dist,
                "confidence": conf,
            })

    candidates.sort(key=lambda x: (-x["confidence"], x["distance"]))
    return candidates[:top_k]
