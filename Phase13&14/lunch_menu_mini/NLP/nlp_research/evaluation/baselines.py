"""
Recommender baselines for E1 vs Popular vs Random comparison.

Each baseline shares the same `recommend(user_id, top_n) -> list[dict]`
interface as `EmbeddingCFRecommender`.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from nlp_research.models.embedding_cf.recommender import MealHistorySource


class PopularRecommender:
    """
    Recommends menus globally sorted by average satisfaction (high → low).
    Excludes menus the target user has already eaten.
    """

    def __init__(self, source: MealHistorySource):
        self.source = source
        self._popular = self._compute_popular()

    def _compute_popular(self) -> list[dict[str, Any]]:
        agg: dict[str, dict[str, Any]] = {}
        for rows in self.source.meal_history.values():
            for r in rows:
                menu = r.get("menu_name")
                sat = r.get("satisfaction")
                if not menu or sat is None:
                    continue
                slot = agg.setdefault(menu, {
                    "menu": menu,
                    "restaurant": r.get("restaurant_id"),
                    "_sum": 0.0,
                    "_n": 0,
                })
                slot["_sum"] += float(sat)
                slot["_n"] += 1
        out = []
        for slot in agg.values():
            if slot["_n"] == 0:
                continue
            out.append({
                "menu": slot["menu"],
                "restaurant": slot["restaurant"],
                "score": round(slot["_sum"] / slot["_n"], 4),
                "similar_user_count": slot["_n"],
                "reason": f"평균 평점 {slot['_sum']/slot['_n']:.2f}점",
            })
        return sorted(out, key=lambda x: x["score"], reverse=True)

    def recommend(self, user_id: Any, top_n: int = 10) -> list[dict[str, Any]]:
        visited = {
            r.get("menu_name") for r in self.source.get_user(user_id)
        }
        return [m for m in self._popular if m["menu"] not in visited][:top_n]


class RandomRecommender:
    """Random shuffle of all distinct menus, excluding visited."""

    def __init__(self, source: MealHistorySource, seed: int = 42):
        self.source = source
        self._rng = random.Random(seed)
        self._all_menus = self._collect_menus()

    def _collect_menus(self) -> list[dict[str, Any]]:
        seen: dict[str, dict] = {}
        for rows in self.source.meal_history.values():
            for r in rows:
                menu = r.get("menu_name")
                if not menu or menu in seen:
                    continue
                seen[menu] = {
                    "menu": menu,
                    "restaurant": r.get("restaurant_id"),
                    "score": 0.0,
                    "similar_user_count": 0,
                    "reason": "random baseline",
                }
        return list(seen.values())

    def recommend(self, user_id: Any, top_n: int = 10) -> list[dict[str, Any]]:
        visited = {
            r.get("menu_name") for r in self.source.get_user(user_id)
        }
        candidates = [m for m in self._all_menus if m["menu"] not in visited]
        self._rng.shuffle(candidates)
        return candidates[:top_n]


__all__ = ["PopularRecommender", "RandomRecommender"]
