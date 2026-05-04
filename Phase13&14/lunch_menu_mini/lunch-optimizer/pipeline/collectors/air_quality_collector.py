"""
에어코리아 대기질 API 수집기.

- 측정소별 실시간 측정정보 (getMsrstnAcctoRltmMesureDnsty)
- "-" 값 방어 (장비 점검 · 새벽 데이터 누락)
- PM10/PM2.5 등급 문자열 변환
"""
from __future__ import annotations

import logging
import time
from typing import Any, Final, Optional

import requests

from config.settings import settings

logger = logging.getLogger(__name__)

_GRADE_MAP: Final[dict[int, str]] = {
    1: "좋음",
    2: "보통",
    3: "나쁨",
    4: "매우나쁨",
}


def _parse_int_or_none(value: Any) -> Optional[int]:
    """'-', '' 등 무효값은 None, 정상값은 int."""
    if value is None or value == "" or value == "-":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_float_or_none(value: Any) -> Optional[float]:
    if value is None or value == "" or value == "-":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class AirQualityCollector:
    """에어코리아 대기질 수집기."""

    TIMEOUT = 10.0
    MAX_RETRIES = 3

    def __init__(
        self,
        service_key: Optional[str] = None,
        station_name: Optional[str] = None,
    ):
        self.service_key = service_key or settings.datago.decoded_key
        self.station_name = station_name or settings.air_quality.station_name

        if not self.service_key or "your_" in self.service_key:
            raise RuntimeError(
                "DATA_GO_KR_API_KEY_DECODED is not set. Configure Mini/.env."
            )

        logger.info(
            "AirQualityCollector initialized: station=%s", self.station_name
        )

    # -------------------------------------------------------------------------
    # HTTP
    # -------------------------------------------------------------------------
    def _request(self) -> Optional[dict[str, Any]]:
        url = settings.air_quality.base_url + settings.air_quality.realtime_path
        params = {
            "serviceKey": self.service_key,
            "returnType": "json",
            "numOfRows": 1,
            "pageNo": 1,
            "stationName": self.station_name,
            "dataTerm": "DAILY",
            "ver": "1.0",
        }
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.TIMEOUT)
                ctype = resp.headers.get("Content-Type", "").lower()
                text = resp.text
                if "xml" in ctype or text.lstrip().startswith("<"):
                    logger.warning(
                        "AirKorea returned non-JSON (XML error?): %s", text[:200]
                    )
                    return None
                data = resp.json()
                # 응답 스키마는 두 가지 변형이 있음:
                # 1) response.header.resultCode = "00"
                # 2) response.body.items = [...]
                header = (
                    data.get("response", {}).get("header", {})
                    if isinstance(data, dict) else {}
                )
                if header and header.get("resultCode") != "00":
                    logger.warning(
                        "AirKorea API error: code=%s msg=%s",
                        header.get("resultCode"), header.get("resultMsg"),
                    )
                    return None
                return data
            except requests.RequestException as e:
                logger.warning(
                    "airkorea request attempt %d/%d failed: %s",
                    attempt, self.MAX_RETRIES, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 5))
        return None

    # -------------------------------------------------------------------------
    # 공개 API
    # -------------------------------------------------------------------------
    def get_realtime_data(self) -> Optional[dict[str, Any]]:
        """
        측정소별 실시간 대기질 데이터 조회.
        """
        data = self._request()
        if data is None:
            return None

        items = (
            data.get("response", {}).get("body", {}).get("items", [])
            or []
        )
        if not items:
            logger.warning("AirKorea returned empty items for station=%s", self.station_name)
            return None

        item = items[0]
        pm10_grade = _parse_int_or_none(item.get("pm10Grade"))
        pm25_grade = _parse_int_or_none(item.get("pm25Grade"))
        khai_grade = _parse_int_or_none(item.get("khaiGrade"))

        return {
            "pm10_value": _parse_int_or_none(item.get("pm10Value")),
            "pm25_value": _parse_int_or_none(item.get("pm25Value")),
            "pm10_grade": pm10_grade,
            "pm25_grade": pm25_grade,
            "pm10_grade_str": _GRADE_MAP.get(pm10_grade) if pm10_grade else None,
            "pm25_grade_str": _GRADE_MAP.get(pm25_grade) if pm25_grade else None,
            "khai_value": _parse_int_or_none(item.get("khaiValue")),
            "khai_grade": khai_grade,
            "o3_value": _parse_float_or_none(item.get("o3Value")),
            "data_time": item.get("dataTime"),
            "station_name": self.station_name,
        }

    def get_dust_level(self) -> Optional[str]:
        """
        PM10 · PM2.5 등급 중 더 나쁜 것을 기준으로 종합 먼지 수준 반환.
        """
        data = self.get_realtime_data()
        if data is None:
            return None
        pm10_g = data.get("pm10_grade")
        pm25_g = data.get("pm25_grade")
        grades = [g for g in (pm10_g, pm25_g) if g is not None]
        if not grades:
            return None
        worst = max(grades)
        return _GRADE_MAP.get(worst)
