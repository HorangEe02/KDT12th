"""levenshtein.py 단위 테스트."""
from __future__ import annotations

from nlp_mvp.menu_normalizer.levenshtein import (
    adaptive_cutoff,
    distance_to_confidence,
    find_candidates,
)


class TestAdaptiveCutoff:
    def test_short(self):
        assert adaptive_cutoff(2) == 1
        assert adaptive_cutoff(3) == 1

    def test_medium(self):
        assert adaptive_cutoff(4) == 2
        assert adaptive_cutoff(6) == 2

    def test_long(self):
        assert adaptive_cutoff(7) == 3
        assert adaptive_cutoff(10) == 3


class TestDistanceToConfidence:
    def test_perfect_match(self):
        assert distance_to_confidence(0, 5) == 1.0

    def test_half(self):
        assert abs(distance_to_confidence(2, 4) - 0.5) < 0.01

    def test_zero_length(self):
        assert distance_to_confidence(0, 0) == 0.0

    def test_clamp_negative(self):
        assert distance_to_confidence(10, 4) == 0.0


class TestFindCandidates:
    def test_exact_match(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        res = find_candidates("김치찌개", menus, cutoff=0)
        assert len(res) == 1
        assert res[0]["confidence"] == 1.0
        assert res[0]["distance"] == 0

    def test_one_char_diff(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        res = find_candidates("김치찌게", menus)
        assert len(res) == 1
        assert res[0]["distance"] == 1

    def test_too_different(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        res = find_candidates("라면", menus)
        assert len(res) == 0

    def test_top_k(self):
        menus = [
            {"id": "a", "name": "김치찌개"},
            {"id": "b", "name": "김치볶음"},
            {"id": "c", "name": "된장찌개"},
        ]
        res = find_candidates("김치찌개", menus, cutoff=3, top_k=2)
        assert len(res) <= 2
        assert res[0]["id"] == "a"

    def test_empty_query(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        assert find_candidates("", menus) == []

    def test_empty_menus(self):
        assert find_candidates("김치찌개", []) == []
