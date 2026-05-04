"""preprocess.py 단위 테스트."""
from __future__ import annotations

import pytest

from nlp_mvp.sentiment.preprocess import (
    clean_text, deduplicate, is_valid_review
)


class TestCleanText:
    def test_url_removal(self):
        assert clean_text("맛있어요 https://example.com 최고") == "맛있어요 최고"

    def test_www_removal(self):
        assert clean_text("www.test.com 정말 좋아요") == "정말 좋아요"

    def test_emoji_removal(self):
        result = clean_text("정말 맛있어요 😍👍🍱")
        assert "😍" not in result
        assert "맛있어요" in result

    def test_whitespace_normalize(self):
        assert clean_text("  좋아요    정말   ") == "좋아요 정말"

    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""
        assert clean_text(123) == ""

    def test_keep_korean_english_mix(self):
        assert clean_text("delicious 맛있음") == "delicious 맛있음"


class TestIsValidReview:
    def test_too_short(self):
        assert not is_valid_review("굿")
        assert not is_valid_review("a")

    def test_only_digits(self):
        assert not is_valid_review("12345")

    def test_only_symbols(self):
        assert not is_valid_review("!!!!!!")
        assert not is_valid_review("...")

    def test_non_string(self):
        assert not is_valid_review(None)
        assert not is_valid_review(12345)

    def test_valid_korean(self):
        assert is_valid_review("음식 맛있어요")

    def test_valid_with_min_len(self):
        assert is_valid_review("맛있음좋음", min_len=4)
        assert not is_valid_review("짧음", min_len=4)


class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        reviews = [
            {"text": "맛있어요"},
            {"text": "맛있어요"},
            {"text": "좋아요"},
        ]
        result = deduplicate(reviews)
        assert len(result) == 2

    def test_preserves_order(self):
        reviews = [{"text": "A가 좋아요"}, {"text": "B가 좋아요"}, {"text": "A가 좋아요"}]
        result = deduplicate(reviews)
        assert [r["text"] for r in result] == ["A가 좋아요", "B가 좋아요"]

    def test_skips_empty(self):
        reviews = [{"text": ""}, {"text": "좋아요"}]
        result = deduplicate(reviews)
        assert len(result) == 1

    def test_after_clean_match(self):
        """공백 차이만 있는 리뷰는 동일로 취급."""
        reviews = [
            {"text": "맛있어요  정말"},
            {"text": "맛있어요 정말"},
        ]
        result = deduplicate(reviews)
        assert len(result) == 1
