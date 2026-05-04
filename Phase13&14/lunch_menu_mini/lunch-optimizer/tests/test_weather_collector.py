"""
WeatherCollector 단위 테스트.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from pipeline.collectors.weather_collector import WeatherCollector


# =============================================================================
# base datetime
# =============================================================================
class TestBaseDatetime:
    def test_ncst_after_delay(self):
        """11:45 → 11시 정시 사용 (40분 지났음)."""
        now = datetime(2026, 4, 5, 11, 45)
        date_str, time_str = WeatherCollector._get_ncst_base_datetime(now)
        assert date_str == "20260405"
        assert time_str == "1100"

    def test_ncst_before_delay(self):
        """11:20 → 10시 정시 사용 (40분 전)."""
        now = datetime(2026, 4, 5, 11, 20)
        date_str, time_str = WeatherCollector._get_ncst_base_datetime(now)
        assert date_str == "20260405"
        assert time_str == "1000"

    def test_vilage_after_publish(self):
        """11:15 → 11시 발표 사용 (10분 경과)."""
        now = datetime(2026, 4, 5, 11, 15)
        date_str, time_str = WeatherCollector._get_vilage_base_datetime(now)
        assert date_str == "20260405"
        assert time_str == "1100"

    def test_vilage_before_publish(self):
        """11:05 → 8시 발표 사용 (11시 발표는 11:10 이후)."""
        now = datetime(2026, 4, 5, 11, 5)
        date_str, time_str = WeatherCollector._get_vilage_base_datetime(now)
        assert time_str == "0800"

    def test_vilage_midnight(self):
        """00:05 → 전날 23시 발표."""
        now = datetime(2026, 4, 5, 0, 5)
        date_str, time_str = WeatherCollector._get_vilage_base_datetime(now)
        assert date_str == "20260404"
        assert time_str == "2300"


# =============================================================================
# API 호출 (mocking)
# =============================================================================
class TestUltraSrtNcst:
    def test_success(self, fake_datago_key, kma_ncst_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = kma_ncst_response

        with patch("requests.get", return_value=mock_resp):
            collector = WeatherCollector()
            result = collector.get_ultra_srt_ncst()

        assert result is not None
        assert result["temp"] == 12.5
        assert result["humidity"] == 55
        assert result["rain_type"] == 0
        assert result["rain_type_str"] == "없음"
        assert result["wind_speed"] == 2.3

    def test_result_code_error(self, fake_datago_key):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = {
            "response": {
                "header": {"resultCode": "03", "resultMsg": "NO_DATA"},
                "body": {},
            }
        }
        with patch("requests.get", return_value=mock_resp):
            collector = WeatherCollector()
            assert collector.get_ultra_srt_ncst() is None

    def test_xml_error_response(self, fake_datago_key):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/xml"}
        mock_resp.text = "<error>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</error>"
        with patch("requests.get", return_value=mock_resp):
            collector = WeatherCollector()
            assert collector.get_ultra_srt_ncst() is None


class TestVilageFcst:
    def test_parses_current_slot(self, fake_datago_key, kma_fcst_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = kma_fcst_response

        with patch("requests.get", return_value=mock_resp):
            collector = WeatherCollector()
            result = collector.get_vilage_fcst()

        assert result is not None
        assert result["sky"] == 4
        assert result["sky_str"] == "흐림"
        assert result["pop"] == 30
        assert result["tmn"] == 8
        assert result["tmx"] == 18


# =============================================================================
# Collect 통합
# =============================================================================
class TestCollectIntegration:
    def test_combines_both(
        self, fake_datago_key, kma_ncst_response, kma_fcst_response
    ):
        # 두 번 호출되므로 side_effect 로 구분
        call_count = {"n": 0}

        def side_effect(url, params=None, timeout=None):
            call_count["n"] += 1
            resp = MagicMock(status_code=200)
            resp.headers = {"Content-Type": "application/json"}
            resp.text = "{}"
            if "UltraSrtNcst" in url:
                resp.json.return_value = kma_ncst_response
            else:
                resp.json.return_value = kma_fcst_response
            return resp

        with patch("requests.get", side_effect=side_effect):
            collector = WeatherCollector()
            result = collector.collect()

        assert result is not None
        assert result["temp"] == 12.5
        assert result["sky_str"] == "흐림"
        assert result["pop"] == 30
        assert "collected_at" in result
        assert call_count["n"] == 2
