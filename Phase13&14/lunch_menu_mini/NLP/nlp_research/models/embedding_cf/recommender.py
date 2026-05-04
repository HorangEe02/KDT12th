"""
E1 — Embedding Collaborative Filtering recommender.

Algorithm:
1. Build profile text per user from meal_history (menu + satisfaction).
2. Embed profiles → FAISS / NumPy index.
3. For target user → find top-K similar users.
4. Aggregate their high-rating menus (≥ min_satisfaction), excluding ones the
   target has already eaten.
5. Score = sum(similarity × satisfaction) → top-N.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from nlp_research.models.embedding_cf.embedder import (
    UserEmbedder,
    build_user_profile_text,
)
from nlp_research.models.embedding_cf.index import make_index


# =============================================================================
# Data source abstraction
# =============================================================================
class MealHistorySource:
    """
    Pluggable data source for the recommender.

    `meal_history` is a dict[user_id -> list of meal rows].
    Each row needs: menu_name, satisfaction, restaurant_id, meal_date.
    """

    def __init__(self, meal_history: dict[Any, list[dict[str, Any]]]):
        self.meal_history = meal_history

    def get_user(self, user_id: Any) -> list[dict[str, Any]]:
        return self.meal_history.get(user_id, [])

    def get_all_user_ids(self) -> list[Any]:
        return list(self.meal_history.keys())

    @classmethod
    def from_db(cls, engine=None) -> "MealHistorySource":
        """Load from Phase 5 mini.db meal_history table."""
        if engine is None:
            from nlp_mvp.shared.db import get_engine
            engine = get_engine()
        from sqlalchemy import text
        rows_by_user: dict[Any, list[dict]] = defaultdict(list)
        with engine.connect() as conn:
            res = conn.execute(text(
                "SELECT user_id, menu_name, restaurant_id, satisfaction, meal_date "
                "FROM meal_history ORDER BY meal_date"
            )).mappings().all()
            for r in res:
                rows_by_user[r["user_id"]].append(dict(r))
        return cls(dict(rows_by_user))

    @classmethod
    def synthetic(cls, n_users: int = 5, seed: int = 42) -> "MealHistorySource":
        """Generate mock data for tests / smoke benchmark."""
        import random
        rng = random.Random(seed)
        menus = [
            "김치찌개", "비빔밥", "냉면", "돈까스", "초밥", "쌀국수",
            "샐러드", "파스타", "치킨", "라멘", "갈비탕", "떡볶이",
        ]
        restaurants = [f"R{i:03d}" for i in range(1, 11)]
        history: dict[Any, list[dict]] = {}
        for u in range(1, n_users + 1):
            user_meals = []
            for d in range(15):
                user_meals.append({
                    "user_id": u,
                    "menu_name": rng.choice(menus),
                    "restaurant_id": rng.choice(restaurants),
                    "satisfaction": rng.randint(2, 5),
                    "meal_date": f"2026-04-{d+1:02d}",
                })
            history[u] = user_meals
        return cls(history)


# =============================================================================
# Recommender
# =============================================================================
class EmbeddingCFRecommender:
    """
    Embedding-based CF recommender.

    Args:
        source: MealHistorySource
        embedder: UserEmbedder (defaults to HashEmbedder for hermetic tests)
        prefer_faiss: index backend selection
    """

    def __init__(
        self,
        source: MealHistorySource,
        embedder: Optional[UserEmbedder] = None,
        prefer_faiss: str | bool = "auto",
    ):
        self.source = source
        self.embedder = embedder or UserEmbedder(use_sbert=False)
        self.index = make_index(self.embedder.dim, prefer_faiss=prefer_faiss)
        self._user_ids: list[Any] = []

    # -------------------------------------------------------------------------
    # Index lifecycle
    # -------------------------------------------------------------------------
    def build_index(self) -> int:
        """Embed all users and build the search index. Returns user count."""
        user_ids = self.source.get_all_user_ids()
        if not user_ids:
            return 0
        vectors = []
        for uid in user_ids:
            history = self.source.get_user(uid)
            vectors.append(self.embedder.embed_user_profile(history))
        self.index.build(vectors, list(user_ids))
        self._user_ids = list(user_ids)
        return len(user_ids)

    # -------------------------------------------------------------------------
    # Recommendation
    # -------------------------------------------------------------------------
    def recommend(
        self,
        user_id: Any,
        top_k_users: int = 20,
        top_n_menus: int = 5,
        exclude_visited: bool = True,
        min_satisfaction: float = 4.0,
    ) -> list[dict[str, Any]]:
        if not self._user_ids:
            self.build_index()

        target_history = self.source.get_user(user_id)
        target_vec = self.embedder.embed_user_profile(target_history)
        sim_user_ids, sim_scores = self.index.search(target_vec, top_k=top_k_users + 1)

        # Drop the target itself if present
        pairs = [
            (uid, sc) for uid, sc in zip(sim_user_ids, sim_scores) if uid != user_id
        ][:top_k_users]

        visited = {row.get("menu_name") for row in target_history}

        # Aggregate candidate menus
        agg: dict[str, dict[str, Any]] = {}
        for uid, sim in pairs:
            for row in self.source.get_user(uid):
                sat = row.get("satisfaction") or 0
                if sat < min_satisfaction:
                    continue
                menu = row.get("menu_name")
                if not menu or (exclude_visited and menu in visited):
                    continue
                slot = agg.setdefault(menu, {
                    "menu": menu,
                    "restaurant": row.get("restaurant_id"),
                    "score": 0.0,
                    "similar_user_count": 0,
                })
                slot["score"] += float(sim) * float(sat)
                slot["similar_user_count"] += 1

        ranked = sorted(agg.values(), key=lambda x: x["score"], reverse=True)
        for r in ranked:
            r["score"] = round(r["score"], 4)
            r["reason"] = (
                f"비슷한 취향 사용자 {r['similar_user_count']}명이 고평가"
            )
        return ranked[:top_n_menus]

    def cold_start_recommend(
        self,
        onboarding_text: str,
        top_n: int = 5,
        top_k_users: int = 20,
        min_satisfaction: float = 4.0,
    ) -> list[dict[str, Any]]:
        """Recommend for a brand-new user using a free-text profile."""
        if not self._user_ids:
            self.build_index()
        target_vec = self.embedder.embed_text(onboarding_text)
        sim_user_ids, sim_scores = self.index.search(target_vec, top_k=top_k_users)

        agg: dict[str, dict[str, Any]] = {}
        for uid, sim in zip(sim_user_ids, sim_scores):
            for row in self.source.get_user(uid):
                sat = row.get("satisfaction") or 0
                if sat < min_satisfaction:
                    continue
                menu = row.get("menu_name")
                if not menu:
                    continue
                slot = agg.setdefault(menu, {
                    "menu": menu,
                    "restaurant": row.get("restaurant_id"),
                    "score": 0.0,
                    "similar_user_count": 0,
                })
                slot["score"] += float(sim) * float(sat)
                slot["similar_user_count"] += 1

        ranked = sorted(agg.values(), key=lambda x: x["score"], reverse=True)
        for r in ranked:
            r["score"] = round(r["score"], 4)
            r["reason"] = (
                f"온보딩 텍스트와 유사한 사용자 {r['similar_user_count']}명 기반"
            )
        return ranked[:top_n]


__all__ = ["EmbeddingCFRecommender", "MealHistorySource"]
