"""한국관광공사 TourAPI 경량 클라이언트.

Streamlit 및 스크립트 환경 모두에서 호출 가능. 실패 시 빈 리스트 반환.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from src import config

log = logging.getLogger(__name__)

_ENDPOINT = f"{config.TOUR_API_BASE}/locationBasedList2"


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_items(body_items: Any) -> list[dict]:
    if not body_items:
        return []
    raw = body_items.get("item") if isinstance(body_items, dict) else None
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return raw
    return []


def _map_item(item: dict, content_type: int) -> dict:
    category = config.CONTENT_TYPE_REVERSE.get(content_type, "tour")
    return {
        "content_id": str(item.get("contentid", "")),
        "title": item.get("title", "").strip(),
        "category": category,
        "addr": item.get("addr1", ""),
        "lat": _coerce_float(item.get("mapy")),
        "lng": _coerce_float(item.get("mapx")),
        "tel": item.get("tel", "") or "",
        "first_image": item.get("firstimage", "") or "",
        "dist_m": _coerce_float(item.get("dist")),
        "stadium": "",
    }


def get_nearby_places(
    lat: float,
    lng: float,
    radius: int = 3000,
    content_type: int = 39,
    num_rows: int = 30,
) -> list[dict]:
    """지정 좌표 반경 내 POI 조회.

    Args:
        lat: 위도 (33~38)
        lng: 경도 (124~132)
        radius: 반경 m, 최대 20000
        content_type: 12=관광지, 32=숙박, 39=음식점
        num_rows: 최대 반환 개수

    Returns:
        SCHEMA.md의 POI dict 리스트. 실패/키 누락 시 빈 리스트.
    """
    if not (33 <= lat <= 39):
        log.warning("위도 범위 벗어남: %s", lat)
        return []
    if not (124 <= lng <= 132):
        log.warning("경도 범위 벗어남: %s", lng)
        return []
    if not config.TOUR_API_KEY:
        log.warning("TOUR_API_KEY 미설정. 빈 결과 반환.")
        return []

    radius = min(max(100, radius), 20000)
    params = {
        "serviceKey": config.TOUR_API_KEY,
        "mapX": lng,
        "mapY": lat,
        "radius": radius,
        "contentTypeId": content_type,
        "MobileOS": "ETC",
        "MobileApp": "AwayGameCompanion",
        "_type": "json",
        "numOfRows": num_rows,
        "pageNo": 1,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AwayGameCompanion/1.0)",
        "Accept": "application/json",
    }
    try:
        resp = httpx.get(
            _ENDPOINT,
            params=params,
            headers=headers,
            timeout=httpx.Timeout(config.DEFAULT_API_TIMEOUT),
        )
        resp.raise_for_status()
        text = resp.text
        if "SERVICE KEY IS NOT REGISTERED" in text or "SERVICE_KEY" in text.upper() and "ERROR" in text.upper():
            log.warning("TourAPI 서비스 키 미등록: %s", text[:200])
            return []
        data = resp.json()
    except httpx.HTTPError as exc:
        log.warning("TourAPI HTTP 오류: %s", exc)
        return []
    except ValueError as exc:
        log.warning("TourAPI JSON 파싱 실패: %s", exc)
        return []

    try:
        body = data["response"]["body"]
    except (KeyError, TypeError):
        log.warning("TourAPI 응답 구조 예상과 다름")
        return []

    items = _normalize_items(body.get("items"))
    return [_map_item(i, content_type) for i in items]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = get_nearby_places(37.5122, 127.0719, radius=2000, content_type=39, num_rows=5)
    print(f"잠실 음식점 {len(results)}건")
    for r in results[:5]:
        print(f"- {r['title']} ({r['dist_m']:.0f}m)")
