"""
기상청 단기예보 API 수집기.

- 초단기실황 (getUltraSrtNcst) — 현재 관측값
- 단기예보 (getVilageFcst) — 수 시간 앞 예보
- base_date / base_time 자동 계산 (자정·발표 직후 엣지 케이스 포함)
- XML 에러 방어, 재시도 (exponential backoff)
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Final, Optional

import requests

from config.settings import settings
from pipeline.utils.coordinate_converter import latlon_to_grid

logger = logging.getLogger(__name__)


# =============================================================================
# 상수
# =============================================================================
# 단기예보 발표 시각 (정시)
_VILAGE_PUBLISH_HOURS: Final[tuple[int, ...]] = (2, 5, 8, 11, 14, 17, 20, 23)
# API 제공 지연 — 발표 후 10분 뒤부터 사용 가능
_PUBLISH_DELAY_MIN: Final[int] = 10

# 초단기실황: 매 정시 발표, 40분 뒤 제공
_NCST_DELAY_MIN: Final[int] = 40

_SKY_MAP: Final[dict[int, str]] = {1: "맑음", 3: "구름많음", 4: "흐림"}
_PTY_MAP: Final[dict[int, str]] = {
    0: "없음", 1: "비", 2: "비/눈", 3: "눈",
    5: "빗방울", 6: "빗방울눈날림", 7: "눈날림",
}


# =============================================================================
# 유틸
# =============================================================================
def _parse_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value in ("", "-", "-999"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value in ("", "-", "-999"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


# =============================================================================
# 수집기
# =============================================================================
class WeatherCollector:
    """
    기상청 단기예보 API 수집기.

    Usage:
        collector = WeatherCollector()  # settings 의 사무실 좌표 사용
        weather = collector.collect()
    """

    TIMEOUT = 10.0
    MAX_RETRIES = 3

    def __init__(
        self,
        service_key: Optional[str] = None,
        nx: Optional[int] = None,
        ny: Optional[int] = None,
    ):
        self.service_key = service_key or settings.datago.decoded_key
        if not self.service_key or "your_" in self.service_key:
            raise RuntimeError(
                "DATA_GO_KR_API_KEY_DECODED is not set. Configure Mini/.env."
            )

        if nx is None or ny is None:
            nx, ny = latlon_to_grid(settings.office.lat, settings.office.lng)
        self.nx = nx
        self.ny = ny
        logger.info("WeatherCollector initialized: grid=(%d, %d)", self.nx, self.ny)

    # -------------------------------------------------------------------------
    # base_date / base_time 계산
    # -------------------------------------------------------------------------
    @staticmethod
    def _get_ncst_base_datetime(now: Optional[datetime] = None) -> tuple[str, str]:
        """
        초단기실황 기준 시각.

        매 정시 + 40분 뒤부터 제공되므로,
        현재 시각이 HH:40 이전이면 한 시간 전의 정시 사용.
        """
        now = now or datetime.now()
        if now.minute < _NCST_DELAY_MIN:
            target = now - timedelta(hours=1)
        else:
            target = now
        return target.strftime("%Y%m%d"), target.strftime("%H00")

    @staticmethod
    def _get_vilage_base_datetime(now: Optional[datetime] = None) -> tuple[str, str]:
        """
        단기예보 기준 시각.

        발표 시각 리스트 중 현재 시각 + 지연 여유 (10분) 를 넘는 가장 최근 발표를 선택.
        자정 전후 엣지 케이스: 00:00~02:09 → 전날 23시 발표 사용.
        """
        now = now or datetime.now()
        current_minutes = now.hour * 60 + now.minute

        chosen_hour: Optional[int] = None
        for h in reversed(_VILAGE_PUBLISH_HOURS):
            publish_minutes = h * 60 + _PUBLISH_DELAY_MIN
            if current_minutes >= publish_minutes:
                chosen_hour = h
                break

        if chosen_hour is None:
            # 자정 직후 → 전날 23시 발표
            target_day = now - timedelta(days=1)
            return target_day.strftime("%Y%m%d"), "2300"

        return now.strftime("%Y%m%d"), f"{chosen_hour:02d}00"

    # -------------------------------------------------------------------------
    # 내부 HTTP 호출
    # -------------------------------------------------------------------------
    def _request(self, path: str, params: dict[str, Any]) -> Optional[dict[str, Any]]:
        url = settings.weather.base_url + path
        params["serviceKey"] = self.service_key

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.TIMEOUT)
                ctype = resp.headers.get("Content-Type", "").lower()
                text = resp.text

                # XML 에러 응답 방어
                if "xml" in ctype or text.lstrip().startswith("<"):
                    logger.warning(
                        "Weather API returned non-JSON (XML error?): %s",
                        text[:200],
                    )
                    return None

                data = resp.json()
                header = (
                    data.get("response", {}).get("header", {}) if isinstance(data, dict) else {}
                )
                result_code = header.get("resultCode", "")
                if result_code != "00":
                    logger.warning(
                        "Weather API error: code=%s msg=%s",
                        result_code, header.get("resultMsg", ""),
                    )
                    return None
                return data
            except requests.RequestException as e:
                logger.warning(
                    "weather request attempt %d/%d failed: %s",
                    attempt, self.MAX_RETRIES, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 5))
        return None

    # -------------------------------------------------------------------------
    # 초단기실황
    # -------------------------------------------------------------------------
    def get_ultra_srt_ncst(self) -> Optional[dict[str, Any]]:
        base_date, base_time = self._get_ncst_base_datetime()
        params = {
            "numOfRows": 10,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": self.nx,
            "ny": self.ny,
        }
        data = self._request(settings.weather.ultra_ncst_path, params)
        if data is None:
            return None

        items = (
            data.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        ) or []

        by_cat = {it.get("category"): it.get("obsrValue") for it in items}

        rain_type = _parse_int(by_cat.get("PTY"), default=0)
        return {
            "temp": _parse_float(by_cat.get("T1H")),
            "humidity": _parse_int(by_cat.get("REH")),
            "rain_type": rain_type,
            "rain_type_str": _PTY_MAP.get(rain_type, "없음"),
            "rain_1h": _parse_float(by_cat.get("RN1")),
            "wind_speed": _parse_float(by_cat.get("WSD")),
            "wind_dir": _parse_int(by_cat.get("VEC")),
            "base_date": base_date,
            "base_time": base_time,
        }

    # -------------------------------------------------------------------------
    # 단기예보
    # -------------------------------------------------------------------------
    def get_vilage_fcst(self) -> Optional[dict[str, Any]]:
        base_date, base_time = self._get_vilage_base_datetime()
        params = {
            "numOfRows": 300,  # 여러 시간대 + 여러 카테고리 포함 → 넉넉히
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": self.nx,
            "ny": self.ny,
        }
        data = self._request(settings.weather.vilage_fcst_path, params)
        if data is None:
            return None

        items = (
            data.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        ) or []
        if not items:
            return None

        # 현재 시각과 가장 가까운 미래 예보 시각 선택
        now = datetime.now()
        now_str = now.strftime("%H%M")
        today = now.strftime("%Y%m%d")

        # (fcstDate, fcstTime) 후보 수집
        candidates: list[tuple[str, str]] = []
        for it in items:
            fd = it.get("fcstDate", "")
            ft = it.get("fcstTime", "")
            if (fd, ft) not in candidates:
                candidates.append((fd, ft))

        # 가장 가까운 미래 timeslot
        def _score(c: tuple[str, str]) -> int:
            fd, ft = c
            if fd < today:
                return -10**9
            return int(fd) * 10000 + int(ft)

        future = [c for c in candidates if c[0] > today or (c[0] == today and c[1] >= now_str)]
        chosen = min(future, default=max(candidates, key=_score))
        fcst_date, fcst_time = chosen

        # 해당 슬롯의 카테고리별 값
        by_cat: dict[str, Any] = {}
        # 오늘의 TMN/TMX 는 별도 수집
        tmn_val: Optional[float] = None
        tmx_val: Optional[float] = None
        for it in items:
            cat = it.get("category")
            val = it.get("fcstValue")
            if it.get("fcstDate") == fcst_date and it.get("fcstTime") == fcst_time:
                by_cat[cat] = val
            if it.get("fcstDate") == today:
                if cat == "TMN" and tmn_val is None:
                    tmn_val = _parse_float(val)
                if cat == "TMX" and tmx_val is None:
                    tmx_val = _parse_float(val)

        sky_code = _parse_int(by_cat.get("SKY"), default=1)
        return {
            "sky": sky_code,
            "sky_str": _SKY_MAP.get(sky_code, "맑음"),
            "pop": _parse_int(by_cat.get("POP")),
            "tmp": _parse_float(by_cat.get("TMP")),
            "tmn": tmn_val if tmn_val is not None else _parse_float(by_cat.get("TMN")),
            "tmx": tmx_val if tmx_val is not None else _parse_float(by_cat.get("TMX")),
            "fcst_date": fcst_date,
            "fcst_time": fcst_time,
        }

    # -------------------------------------------------------------------------
    # 통합
    # -------------------------------------------------------------------------
    def collect(self) -> Optional[dict[str, Any]]:
        """
        초단기실황 + 단기예보 통합 dict.
        """
        ncst = self.get_ultra_srt_ncst()
        fcst = self.get_vilage_fcst()
        if ncst is None and fcst is None:
            logger.error("Both weather APIs failed")
            return None

        result = {
            "temp": (ncst or {}).get("temp", 0.0),
            "humidity": (ncst or {}).get("humidity", 0),
            "rain_type": (ncst or {}).get("rain_type", 0),
            "rain_type_str": (ncst or {}).get("rain_type_str", "없음"),
            "rain_1h": (ncst or {}).get("rain_1h", 0.0),
            "wind_speed": (ncst or {}).get("wind_speed", 0.0),
            "sky": (fcst or {}).get("sky", 1),
            "sky_str": (fcst or {}).get("sky_str", "맑음"),
            "pop": (fcst or {}).get("pop", 0),
            "tmn": (fcst or {}).get("tmn", 0.0),
            "tmx": (fcst or {}).get("tmx", 0.0),
            "collected_at": datetime.utcnow().isoformat(),
        }
        return result
