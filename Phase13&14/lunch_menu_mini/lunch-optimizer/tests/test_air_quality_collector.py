"""
AirQualityCollector 단위 테스트.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline.collectors.air_quality_collector import AirQualityCollector


class TestGetRealtimeData:
    def test_success(self, fake_datago_key, airkorea_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = airkorea_response

        with patch("requests.get", return_value=mock_resp):
            collector = AirQualityCollector()
            data = collector.get_realtime_data()

        assert data is not None
        assert data["pm10_value"] == 45
        assert data["pm25_value"] == 22
        assert data["pm10_grade"] == 2
        assert data["pm25_grade"] == 2
        assert data["pm10_grade_str"] == "보통"
        assert data["pm25_grade_str"] == "보통"
        assert data["station_name"]

    def test_dashed_values_become_none(self, fake_datago_key, airkorea_dashed_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = airkorea_dashed_response

        with patch("requests.get", return_value=mock_resp):
            collector = AirQualityCollector()
            data = collector.get_realtime_data()

        assert data is not None
        assert data["pm10_value"] is None
        assert data["pm25_value"] is None
        assert data["pm10_grade"] is None
        assert data["pm10_grade_str"] is None

    def test_empty_items_returns_none(self, fake_datago_key):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = {
            "response": {"header": {"resultCode": "00"}, "body": {"items": []}}
        }
        with patch("requests.get", return_value=mock_resp):
            collector = AirQualityCollector()
            assert collector.get_realtime_data() is None

    def test_xml_error(self, fake_datago_key):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/xml"}
        mock_resp.text = "<error/>"
        with patch("requests.get", return_value=mock_resp):
            collector = AirQualityCollector()
            assert collector.get_realtime_data() is None


class TestDustLevel:
    def test_worst_wins(self, fake_datago_key):
        """PM10=2 보통, PM25=3 나쁨 → '나쁨' 반환."""
        response = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {
                    "items": [{
                        "pm10Value": "50", "pm25Value": "60",
                        "pm10Grade": "2", "pm25Grade": "3",
                        "khaiValue": "", "khaiGrade": "3",
                        "o3Value": "", "dataTime": "",
                    }]
                },
            }
        }
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = response

        with patch("requests.get", return_value=mock_resp):
            collector = AirQualityCollector()
            level = collector.get_dust_level()
        assert level == "나쁨"

    def test_all_none(self, fake_datago_key, airkorea_dashed_response):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.text = "{}"
        mock_resp.json.return_value = airkorea_dashed_response

        with patch("requests.get", return_value=mock_resp):
            collector = AirQualityCollector()
            assert collector.get_dust_level() is None
