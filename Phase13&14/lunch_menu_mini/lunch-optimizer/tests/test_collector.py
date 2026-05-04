"""
RestaurantCollector 단위 테스트 (requests mocking).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline.collectors.restaurant_collector import (
    DailyQuotaTracker, RestaurantCollector
)


# =============================================================================
# Quota tracker
# =============================================================================
class TestDailyQuotaTracker:
    def test_initial_state(self):
        q = DailyQuotaTracker(limit=10)
        assert q.remaining == 10
        assert not q.is_exhausted()

    def test_increment(self):
        q = DailyQuotaTracker(limit=3)
        for _ in range(3):
            q.increment()
        assert q.is_exhausted()
        assert q.remaining == 0


# =============================================================================
# 수집기
# =============================================================================
class TestFetchPage:
    def test_successful_fetch(self, fake_kakao_key, sample_kakao_response):
        collector = RestaurantCollector()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = sample_kakao_response
        mock_resp.raise_for_status = lambda: None

        with patch("requests.get", return_value=mock_resp) as mock_get:
            data = collector._fetch_page(page=1)

        assert data is not None
        assert "documents" in data
        mock_get.assert_called_once()
        assert collector.stats.api_calls == 1

    def test_429_retries_with_retry_after(self, fake_kakao_key, sample_kakao_response):
        collector = RestaurantCollector()

        responses = [
            MagicMock(status_code=429, headers={"Retry-After": "0"}),
            MagicMock(status_code=200),
        ]
        responses[1].json.return_value = sample_kakao_response
        responses[1].raise_for_status = lambda: None

        with patch("requests.get", side_effect=responses), patch("time.sleep"):
            data = collector._fetch_page(page=1)

        assert data is not None

    def test_401_returns_none(self, fake_kakao_key):
        collector = RestaurantCollector()
        mock_resp = MagicMock(status_code=401)
        with patch("requests.get", return_value=mock_resp):
            assert collector._fetch_page(page=1) is None

    def test_retries_on_network_error(self, fake_kakao_key):
        import requests as req_mod
        collector = RestaurantCollector()
        with patch("requests.get", side_effect=req_mod.ConnectionError("boom")), \
             patch("time.sleep"):
            assert collector._fetch_page(page=1) is None
        assert collector.stats.api_calls == collector.MAX_RETRIES
        assert collector.stats.errors == 1


class TestCollectAll:
    def test_collects_documents(self, fake_kakao_key, sample_kakao_response):
        collector = RestaurantCollector()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = sample_kakao_response
        mock_resp.raise_for_status = lambda: None

        with patch("requests.get", return_value=mock_resp), patch("time.sleep"):
            docs = collector.collect_all()

        assert len(docs) == 5  # sample_kakao_documents 길이
        assert collector.stats.pages_fetched == 1
        assert collector.stats.total_fetched == 5
        assert collector.stats.errors == 0

    def test_stops_on_empty_documents(self, fake_kakao_key):
        collector = RestaurantCollector()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "meta": {"is_end": False},
            "documents": [],
        }
        mock_resp.raise_for_status = lambda: None
        with patch("requests.get", return_value=mock_resp), patch("time.sleep"):
            docs = collector.collect_all()
        assert docs == []
