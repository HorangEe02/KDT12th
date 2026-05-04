"""
sentiment_pipeline.py 단위 테스트.

transformers/torch 미설치 시 SentimentAnalyzer 관련 테스트는 자동 스킵.
aggregate() 테스트는 항상 실행.
"""
from __future__ import annotations

import pytest

from nlp_mvp.sentiment.sentiment_pipeline import aggregate


# =============================================================================
# aggregate — 순수 함수, 항상 실행
# =============================================================================
class TestAggregate:
    def test_all_positive(self):
        results = [{"label": "positive", "confidence": 0.9}] * 10
        agg = aggregate(results)
        assert agg["score"] == 1.0
        assert agg["pos_ratio"] == 1.0
        assert agg["sample_size"] == 10

    def test_all_negative(self):
        results = [{"label": "negative", "confidence": 0.9}] * 10
        agg = aggregate(results)
        assert agg["score"] == -1.0
        assert agg["neg_ratio"] == 1.0

    def test_mixed(self):
        results = (
            [{"label": "positive", "confidence": 0.9}] * 6
            + [{"label": "negative", "confidence": 0.9}] * 4
        )
        agg = aggregate(results)
        assert agg["score"] == pytest.approx(0.2)  # (6 - 4) / 10
        assert agg["pos_ratio"] == 0.6
        assert agg["neg_ratio"] == 0.4

    def test_insufficient_samples(self):
        results = [{"label": "positive", "confidence": 0.9}] * 3
        agg = aggregate(results, min_sample=5)
        assert agg["score"] is None
        assert agg["reason"] == "insufficient_samples"
        assert agg["sample_size"] == 3

    def test_empty(self):
        agg = aggregate([])
        assert agg["score"] is None
        assert agg["sample_size"] == 0

    def test_neutral_does_not_affect_score(self):
        results = (
            [{"label": "positive", "confidence": 0.9}] * 5
            + [{"label": "neutral", "confidence": 0.9}] * 5
        )
        agg = aggregate(results)
        # (5 - 0) / 10 = 0.5
        assert agg["score"] == 0.5
        assert agg["neu_ratio"] == 0.5


# =============================================================================
# SentimentAnalyzer — transformers 필요, 없으면 skip
# =============================================================================
_has_torch = pytest.importorskip.__module__ is not None  # dummy
try:
    import torch  # noqa: F401
    import transformers  # noqa: F401
    _HAS_ML = True
except ImportError:
    _HAS_ML = False


@pytest.mark.skipif(not _HAS_ML, reason="transformers/torch not installed")
class TestSentimentAnalyzer:
    @pytest.fixture(scope="class")
    def analyzer(self):
        from nlp_mvp.sentiment.sentiment_pipeline import SentimentAnalyzer
        return SentimentAnalyzer()

    @pytest.mark.parametrize("text", [
        "정말 맛있고 친절해요. 최고의 식당이에요!",
        "분위기도 좋고 음식도 훌륭합니다.",
        "가격 대비 만족도가 정말 높아요.",
    ])
    def test_clearly_positive(self, analyzer, text):
        result = analyzer.analyze(text)
        assert result["label"] in ("positive", "neutral")  # 관대한 허용
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.parametrize("text", [
        "음식이 너무 짜고 서비스도 최악이었어요.",
        "다시는 안 갈 거예요. 정말 실망.",
        "가격만 비싸고 맛은 형편없어요.",
    ])
    def test_clearly_negative(self, analyzer, text):
        result = analyzer.analyze(text)
        assert result["label"] in ("negative", "neutral")
        assert 0.0 <= result["confidence"] <= 1.0
