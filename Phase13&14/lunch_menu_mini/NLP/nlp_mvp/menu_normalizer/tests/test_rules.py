"""rules.py 단위 테스트."""
from __future__ import annotations

import pytest

from nlp_mvp.menu_normalizer.rules import (
    SynonymDict,
    apply_synonyms,
    load_synonym_dict,
    preprocess_menu_name,
)


class TestPreprocess:
    @pytest.mark.parametrize("raw,expected", [
        ("김치찌개(大)", "김치찌개"),
        ("짬뽕 특", "짬뽕"),
        ("동태탕 1인분", "동태탕"),
        ("제육볶음★★★", "제육볶음"),
        ("  비빔밥   ", "비빔밥"),
        ("돈까스(中)", "돈까스"),
        ("순두부찌개 2개", "순두부찌개"),
        ("냉면[소]", "냉면"),
    ])
    def test_cases(self, raw, expected):
        assert preprocess_menu_name(raw) == expected

    def test_none_input(self):
        assert preprocess_menu_name(None) == ""

    def test_empty_string(self):
        assert preprocess_menu_name("") == ""

    def test_non_string(self):
        assert preprocess_menu_name(123) == ""


class TestSynonyms:
    def test_abbreviation(self):
        d = {"김찌": "김치찌개"}
        assert apply_synonyms("김찌", d) == "김치찌개"

    def test_variant(self):
        d = {"synonyms": {"돈가스": "돈까스"}}
        assert apply_synonyms("돈가스", d) == "돈까스"

    def test_no_match(self):
        d = {"김찌": "김치찌개"}
        assert apply_synonyms("라면", d) == "라면"

    def test_greedy_longest_match(self):
        d = {"synonyms": {"김찌": "김치찌개", "김치찌": "김치찌개특"}}
        # 더 긴 key 우선
        assert apply_synonyms("김치찌", d) == "김치찌개특"

    def test_empty_text(self):
        assert apply_synonyms("", {"a": "b"}) == ""

    def test_empty_dict(self):
        assert apply_synonyms("김찌", {}) == "김찌"


class TestLoadSynonymDict:
    def test_default_path(self):
        d = load_synonym_dict()
        assert "synonyms" in d
        assert len(d["synonyms"]) >= 60

    def test_missing_path(self, tmp_path):
        d = load_synonym_dict(tmp_path / "nonexistent.json")
        assert d == {}

    def test_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid}", encoding="utf-8")
        d = load_synonym_dict(p)
        assert d == {}


class TestSynonymDictClass:
    def test_add_and_apply(self, tmp_path):
        path = tmp_path / "syn.json"
        path.write_text('{"synonyms": {"a": "b"}}', encoding="utf-8")
        sd = SynonymDict(path)
        assert sd.apply("a") == "b"
        sd.add("c", "d")
        assert sd.apply("c") == "d"

    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "syn.json"
        path.write_text('{"synonyms": {}}', encoding="utf-8")
        sd = SynonymDict(path)
        sd.add("x", "y")
        sd.save()
        sd2 = SynonymDict(path)
        assert sd2.apply("x") == "y"

    def test_len(self, tmp_path):
        path = tmp_path / "syn.json"
        path.write_text('{"synonyms": {"a": "b", "c": "d"}}', encoding="utf-8")
        sd = SynonymDict(path)
        assert len(sd) == 2

    def test_save_without_path(self):
        sd = SynonymDict()  # path=None
        sd.add("a", "b")
        with pytest.raises(ValueError):
            sd.save()
