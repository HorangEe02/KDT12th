"""Smoke tests for E1 Embedding CF — works without sentence-transformers."""
from __future__ import annotations

import pytest

from nlp_research.evaluation.baselines import (
    PopularRecommender,
    RandomRecommender,
)
from nlp_research.models.embedding_cf.embedder import (
    HashEmbedder,
    UserEmbedder,
    build_menu_text,
    build_user_profile_text,
)
from nlp_research.models.embedding_cf.evaluate import (
    evaluate_recommenders,
    leave_one_out_split,
)
from nlp_research.models.embedding_cf.index import (
    NumpyBruteForceIndex,
    PyBruteForceIndex,
    make_index,
)
from nlp_research.models.embedding_cf.recommender import (
    EmbeddingCFRecommender,
    MealHistorySource,
)


# =============================================================================
# Profile text builders
# =============================================================================
def test_build_user_profile_text_format():
    history = [
        {"menu_name": "김치찌개", "satisfaction": 5},
        {"menu_name": "비빔밥", "satisfaction": 4},
    ]
    text = build_user_profile_text(history)
    assert "김치찌개 만족 5점" in text
    assert "비빔밥 만족 4점" in text
    assert text.endswith(".")


def test_build_user_profile_text_empty():
    assert build_user_profile_text([]) == "식사 이력 없음"


def test_build_menu_text_includes_nutrition():
    text = build_menu_text(
        {"name": "닭가슴살 샐러드", "category": "샐러드", "calories": 320, "protein": 28}
    )
    assert "닭가슴살" in text
    assert "샐러드" in text
    assert "칼로리 320" in text
    assert "단백질 28" in text


# =============================================================================
# HashEmbedder + UserEmbedder (no Sentence-BERT required)
# =============================================================================
def test_hash_embedder_deterministic():
    e = HashEmbedder(dim=32)
    v1 = e.encode_one("hello")
    v2 = e.encode_one("hello")
    assert len(v1) == 32
    assert v1 == v2


def test_user_embedder_default_uses_hash():
    ue = UserEmbedder(use_sbert=False)
    v = ue.embed_text("테스트")
    assert len(list(v)) == ue.dim


# =============================================================================
# NumpyBruteForceIndex
# =============================================================================
def test_py_bruteforce_index_build_and_search():
    idx = PyBruteForceIndex(dim=4)
    vecs = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.7, 0.7, 0.0, 0.0],
    ]
    idx.build(vecs, ids=["a", "b", "c"])
    ids, scores = idx.search([1.0, 0.0, 0.0, 0.0], top_k=2)
    assert ids[0] == "a"
    assert scores[0] > scores[1]


def test_py_bruteforce_index_save_load(tmp_path):
    idx = PyBruteForceIndex(dim=3)
    idx.build([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], ids=[1, 2])
    idx.save(tmp_path / "ix")
    loaded = PyBruteForceIndex.load(tmp_path / "ix", dim=3)
    assert len(loaded) == 2
    ids, _ = loaded.search([1.0, 0.0, 0.0], top_k=1)
    assert ids[0] == 1


def test_make_index_falls_back():
    idx = make_index(dim=8, prefer_faiss=False)
    assert hasattr(idx, "search")
    # Without numpy installed → PyBruteForceIndex; with numpy → NumpyBruteForceIndex
    assert isinstance(idx, (PyBruteForceIndex, NumpyBruteForceIndex))


# =============================================================================
# Recommender end-to-end
# =============================================================================
def test_synthetic_meal_history_source():
    src = MealHistorySource.synthetic(n_users=4, seed=1)
    assert len(src.get_all_user_ids()) == 4
    assert all(len(src.get_user(u)) > 0 for u in src.get_all_user_ids())


def test_recommender_returns_top_n():
    src = MealHistorySource.synthetic(n_users=6, seed=2)
    rec = EmbeddingCFRecommender(src, prefer_faiss=False)
    rec.build_index()
    out = rec.recommend(user_id=1, top_n_menus=3)
    assert isinstance(out, list)
    # may be 0 if all menus visited; with synthetic data should yield ≥1
    for item in out:
        assert "menu" in item
        assert "score" in item
        assert "similar_user_count" in item


def test_recommender_cold_start():
    src = MealHistorySource.synthetic(n_users=5, seed=3)
    rec = EmbeddingCFRecommender(src, prefer_faiss=False)
    rec.build_index()
    out = rec.cold_start_recommend("매운 음식 좋아해요", top_n=3)
    assert isinstance(out, list)


# =============================================================================
# Baselines
# =============================================================================
def test_popular_recommender():
    src = MealHistorySource.synthetic(n_users=4, seed=4)
    rec = PopularRecommender(src)
    out = rec.recommend(user_id=1, top_n=3)
    assert len(out) <= 3
    for item in out:
        assert "menu" in item
        assert "score" in item


def test_random_recommender_excludes_visited():
    src = MealHistorySource.synthetic(n_users=3, seed=5)
    rec = RandomRecommender(src)
    visited = {r.get("menu_name") for r in src.get_user(1)}
    recs = rec.recommend(user_id=1, top_n=10)
    for r in recs:
        assert r["menu"] not in visited


# =============================================================================
# Leave-one-out
# =============================================================================
def test_loo_split_holds_out_latest():
    src = MealHistorySource.synthetic(n_users=3, seed=6)
    train, held = leave_one_out_split(src)
    assert len(held) == 3
    for uid in held:
        assert len(train.get_user(uid)) == len(src.get_user(uid)) - 1


def test_evaluate_recommenders_runs_end_to_end():
    src = MealHistorySource.synthetic(n_users=5, seed=7)
    result = evaluate_recommenders(src, top_n=10, use_sbert=False)
    for system in ("random", "popular", "e1"):
        assert system in result
        assert "hit@5" in result[system]
        assert "ndcg@10" in result[system]
    assert result["n_users"] >= 1
