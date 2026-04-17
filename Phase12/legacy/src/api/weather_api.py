"""기상청 단기예보 API 클라이언트.

WGS84 좌표를 기상청 격자로 변환하여 `/getVilageFcst` 호출.
키 미설정 또는 API 실패 시 Mock(맑음, POP=0) 반환 → Phase 2~4 블록 방지.

Streamlit에서는 @st.cache_data(ttl=1800)로 감싸 30분 캐싱 권장.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta

import httpx

from src import config

log = logging.getLogger(__name__)

_ENDPOINT = f"{config.WEATHER_API_BASE}/getVilageFcst"
_BASE_TIMES = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]


def dfs_xy_conv(lat: float, lon: float) -> tuple[int, int]:
    """WGS84 → 기상청 격자 좌표 변환 (Lambert Conformal Conic).

    기상청 "동네예보 조회서비스 오픈 API 활용가이드" 참고.
    """
    RE = 6371.00877
    GRID = 5.0
    SLAT1 = 30.0
    SLAT2 = 60.0
    OLON = 126.0
    OLAT = 38.0
    XO = 43
    YO = 136

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn * math.cos(slat1)) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y


def _latest_base(now: datetime) -> tuple[str, str]:
    """가장 최근 발표 시각(base_date, base_time) 계산. 발표 후 10분 버퍼."""
    threshold = now - timedelta(minutes=10)
    hh_mm = threshold.strftime("%H%M")
    for bt in reversed(_BASE_TIMES):
        if hh_mm >= bt:
            return threshold.strftime("%Y%m%d"), bt
    # 새벽 02:10 이전 → 전날 23시
    yesterday = threshold - timedelta(days=1)
    return yesterday.strftime("%Y%m%d"), "2300"


def _mock_forecast(target_date: str) -> dict:
    return {
        "date": target_date,
        "sky": "맑음",
        "precipitation_prob": 0,
        "temp_min": 15,
        "temp_max": 23,
        "rain_expected": False,
    }


def _empty_forecast(target_date: str) -> dict:
    return {
        "date": target_date,
        "sky": None,
        "precipitation_prob": None,
        "temp_min": None,
        "temp_max": None,
        "rain_expected": None,
    }


SKY_MAP = {"1": "맑음", "3": "구름많음", "4": "흐림"}


def get_forecast(lat: float, lng: float, target_date: str) -> dict:
    """특정 좌표·날짜의 예보.

    Args:
        lat, lng: WGS84 좌표
        target_date: 'YYYY-MM-DD'

    Returns:
        SCHEMA.md의 기상 dict. API 키 누락 시 Mock, 호출 실패 시 None 필드.
    """
    if not config.WEATHER_API_KEY:
        log.info("WEATHER_API_KEY 미설정 → Mock 예보 반환")
        return _mock_forecast(target_date)

    try:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        log.warning("target_date 형식 오류: %s", target_date)
        return _empty_forecast(target_date)

    now = datetime.now()
    delta_days = (target_dt.date() - now.date()).days
    if delta_days < 0 or delta_days > 3:
        log.info("단기예보 범위 초과 (%+d일). 근사치 반환.", delta_days)
        return _mock_forecast(target_date)

    base_date, base_time = _latest_base(now)
    nx, ny = dfs_xy_conv(lat, lng)
    params = {
        "serviceKey": config.WEATHER_API_KEY,
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    try:
        resp = httpx.get(
            _ENDPOINT,
            params=params,
            timeout=httpx.Timeout(config.DEFAULT_API_TIMEOUT),
        )
        resp.raise_for_status()
        data = resp.json()
        items = data["response"]["body"]["items"]["item"]
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        log.warning("기상청 API 실패: %s", exc)
        return _empty_forecast(target_date)

    fcst_date = target_dt.strftime("%Y%m%d")
    pops, tmns, tmxs, skys = [], [], [], []
    for it in items:
        if it.get("fcstDate") != fcst_date:
            continue
        cat, val = it.get("category"), it.get("fcstValue")
        if cat == "POP":
            try:
                pops.append(int(val))
            except ValueError:
                pass
        elif cat == "TMN":
            try:
                tmns.append(float(val))
            except ValueError:
                pass
        elif cat == "TMX":
            try:
                tmxs.append(float(val))
            except ValueError:
                pass
        elif cat == "SKY":
            skys.append(SKY_MAP.get(str(val), "맑음"))

    if not pops and not skys:
        log.warning("대상 날짜 데이터 없음: %s", target_date)
        return _empty_forecast(target_date)

    pop = max(pops) if pops else 0
    return {
        "date": target_date,
        "sky": skys[0] if skys else "맑음",
        "precipitation_prob": pop,
        "temp_min": min(tmns) if tmns else None,
        "temp_max": max(tmxs) if tmxs else None,
        "rain_expected": pop >= 60,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(get_forecast(37.5122, 127.0719, tomorrow))
