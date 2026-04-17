"""카카오모빌리티 길찾기 API 클라이언트 + 디스크 캐시 + Fallback.

VIZ_CONTRACT.md 계약 준수:
- 성공: {vertexes, duration_sec, distance_m, toll_fare, fallback=False}
- 실패/키없음: 직선 + haversine 거리 + fallback=True
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any

import httpx

from src import config

log = logging.getLogger(__name__)

_ENDPOINT = "https://apis-navi.kakaomobility.com/v1/directions"
_CACHE_DIR = config.DATA_DIR / "route_cache"


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """두 좌표 사이 대원거리(m). R=6371km 기준."""
    lat1, lng1 = a
    lat2, lng2 = b
    R = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    aa = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(aa), math.sqrt(1 - aa))
    return R * c


def _cache_key(origin: tuple, destination: tuple, waypoints) -> str:
    payload = json.dumps(
        {"origin": origin, "destination": destination, "waypoints": waypoints},
        sort_keys=True,
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _read_cache(key: str) -> dict | None:
    path = _CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("경로 캐시 읽기 실패 (%s): %s", path.name, exc)
        return None


def _write_cache(key: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _CACHE_DIR / f"{key}.json"
    try:
        # tuple → list 직렬화 (JSON 왕복 안전)
        serializable: dict[str, Any] = dict(data)
        serializable["vertexes"] = [list(v) for v in data.get("vertexes", [])]
        path.write_text(json.dumps(serializable, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        log.warning("경로 캐시 쓰기 실패 (%s): %s", path.name, exc)


def _fallback(origin: tuple, destination: tuple) -> dict:
    return {
        "vertexes": [tuple(origin), tuple(destination)],
        "duration_sec": None,
        "distance_m": _haversine_m(origin, destination),
        "toll_fare": None,
        "fallback": True,
    }


def _resolve_key() -> str:
    # 모빌리티 키 우선, 없으면 REST 공용 키로 폴백
    return config.KAKAO_MOBILITY_API_KEY or config.KAKAO_REST_API_KEY or ""


def _parse_route(payload: dict) -> dict | None:
    try:
        routes = payload.get("routes") or []
        if not routes:
            return None
        route0 = routes[0]
        summary = route0.get("summary") or {}
        sections = route0.get("sections") or []
        vertex_pairs: list[tuple[float, float]] = []
        for sec in sections:
            for road in sec.get("roads") or []:
                flat = road.get("vertexes") or []
                for i in range(0, len(flat) - 1, 2):
                    lng = float(flat[i])
                    lat = float(flat[i + 1])
                    vertex_pairs.append((lat, lng))
        if not vertex_pairs:
            return None
        return {
            "vertexes": vertex_pairs,
            "duration_sec": int(summary.get("duration") or 0) or None,
            "distance_m": float(summary.get("distance") or 0) or None,
            "toll_fare": (summary.get("fare") or {}).get("toll"),
            "fallback": False,
        }
    except (KeyError, TypeError, ValueError) as exc:
        log.warning("카카오 응답 파싱 실패: %s", exc)
        return None


def get_car_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    waypoints: list[tuple[float, float]] | None = None,
) -> dict:
    """출발지 → 목적지 자동차 경로. 실패 시 haversine 직선 fallback."""
    origin_t = (float(origin[0]), float(origin[1]))
    destination_t = (float(destination[0]), float(destination[1]))
    wp_list = [tuple(map(float, p)) for p in waypoints] if waypoints else None

    key = _cache_key(origin_t, destination_t, wp_list)
    cached = _read_cache(key)
    if cached is not None:
        if cached.get("vertexes"):
            cached["vertexes"] = [tuple(v) for v in cached["vertexes"]]
        return cached

    api_key = _resolve_key()
    if not api_key:
        log.info("카카오 API 키 없음 → Fallback")
        result = _fallback(origin_t, destination_t)
        _write_cache(key, result)
        return result

    params = {
        "origin": f"{origin_t[1]},{origin_t[0]}",
        "destination": f"{destination_t[1]},{destination_t[0]}",
        "priority": "RECOMMEND",
    }
    if wp_list:
        params["waypoints"] = "|".join(f"{p[1]},{p[0]}" for p in wp_list)

    headers = {
        "Authorization": f"KakaoAK {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.get(
            _ENDPOINT, params=params, headers=headers,
            timeout=httpx.Timeout(config.DEFAULT_API_TIMEOUT),
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("카카오모빌리티 호출 실패: %s → Fallback", exc)
        result = _fallback(origin_t, destination_t)
        _write_cache(key, result)
        return result

    parsed = _parse_route(data)
    if parsed is None:
        log.warning("카카오 응답에서 경로 추출 실패 → Fallback")
        result = _fallback(origin_t, destination_t)
    else:
        result = parsed

    _write_cache(key, result)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    # 잠실 → 수원
    route = get_car_route((37.5122, 127.0719), (37.2997, 127.0097))
    km = (route["distance_m"] or 0) / 1000
    print(f"거리: {km:.1f} km")
    print(f"소요: {(route['duration_sec'] or 0)/60:.0f} 분" if route["duration_sec"] else "소요: —")
    print(f"통행료: {route['toll_fare'] or '—'}")
    print(f"Fallback: {route['fallback']}")
    print(f"정점 수: {len(route['vertexes'])}")
