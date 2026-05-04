"""crawler.py 단위 테스트."""
from __future__ import annotations

from nlp_mvp.sentiment.crawler import (
    SEED_REVIEWS, ReviewCrawler, ReviewSource, SyntheticSource
)


class TestSyntheticSource:
    def test_returns_reviews(self):
        src = SyntheticSource()
        reviews = src.fetch(restaurant_id=1, max_count=20)
        assert len(reviews) == 20
        for r in reviews:
            assert r["source"] == "synthetic"
            assert isinstance(r["text"], str)
            assert len(r["text"]) > 0
            assert "external_id" in r
            assert "fetched_at" in r

    def test_deterministic_by_id(self):
        """같은 restaurant_id 는 같은 샘플을 반환."""
        a = SyntheticSource().fetch(restaurant_id=42, max_count=10)
        b = SyntheticSource().fetch(restaurant_id=42, max_count=10)
        assert [r["text"] for r in a] == [r["text"] for r in b]

    def test_different_id_different_sample(self):
        a = SyntheticSource().fetch(restaurant_id=1, max_count=10)
        b = SyntheticSource().fetch(restaurant_id=2, max_count=10)
        assert [r["text"] for r in a] != [r["text"] for r in b]

    def test_max_count_limit(self):
        src = SyntheticSource()
        reviews = src.fetch(restaurant_id=1, max_count=1000)
        # SEED 최대치를 넘지 않음
        assert len(reviews) == len(SEED_REVIEWS)


class TestReviewCrawlerFallback:
    def test_fallback_to_next_source(self):
        class FailingSource(ReviewSource):
            name = "failing"
            def fetch(self, restaurant_id, max_count=100):
                raise RuntimeError("simulated failure")

        crawler = ReviewCrawler([FailingSource(), SyntheticSource()])
        reviews = crawler.fetch_reviews(restaurant_id=1, max_count=5)
        assert len(reviews) == 5
        assert reviews[0]["source"] == "synthetic"

    def test_returns_first_success(self):
        src1 = SyntheticSource()
        crawler = ReviewCrawler([src1])
        reviews = crawler.fetch_reviews(restaurant_id=1, max_count=3)
        assert len(reviews) == 3

    def test_empty_sources_raises(self):
        import pytest
        with pytest.raises(ValueError):
            ReviewCrawler([])


class TestSeedData:
    def test_seed_count(self):
        assert len(SEED_REVIEWS) == 50

    def test_seed_uniqueness(self):
        assert len(set(SEED_REVIEWS)) == 50
