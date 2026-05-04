"""
In-process TTL cache for user-location-based restaurant lookups.

사용자가 반복적으로 근처 음식점을 조회할 때, 동일 그리드 셀 내 호출은
Kakao Local Search API 재호출 없이 메모리 캐시에서 반환합니다.

정책:
- 그리드 정규화: 100m 단위 (기본값). 동일 그리드 내 다른 좌표는 동일 키로 매핑.
- TTL: 5분 (기본값). 만료 시 다음 요청에서 자동 재수집.
- thread-safe: threading.Lock 으로 보호. (FastAPI + uvicorn 단일 프로세스 전제)

의도적으로 Redis 같은 외부 의존성은 배제. 로컬 개발 전용 단순 구조.
"""
from __future__ import annotations

from threading import Lock
from time import time
from typing import Any, Optional


class LocationCache:
    """좌표 + 반경 키로 결과를 TTL 캐싱."""

    def __init__(self, ttl_seconds: int = 300, grid_m: int = 100):
        """
        Args:
            ttl_seconds: 캐시 엔트리 유효 시간 (초). 기본 5분.
            grid_m: 좌표 정규화 그리드 크기 (미터). 기본 100m.
                    1도 ≈ 111km → 100m 그리드 step = 100 / 111_000 ≈ 0.0009도
        """
        self._store: dict[tuple, tuple[float, Any]] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds
        self._grid = grid_m

    def _key(self, lat: float, lng: float, radius: int) -> tuple[int, int, int]:
        step = self._grid / 111_000.0
        return (
            int(round(lat / step)),
            int(round(lng / step)),
            int(radius),
        )

    def get(self, lat: float, lng: float, radius: int) -> Optional[Any]:
        """캐시에서 값을 조회. 만료 엔트리는 제거 후 None 반환."""
        key = self._key(lat, lng, radius)
        now = time()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, payload = entry
            if expires_at <= now:
                # 만료 → 제거
                self._store.pop(key, None)
                return None
            return payload

    def set(self, lat: float, lng: float, radius: int, payload: Any) -> None:
        """값을 캐시에 저장. 기존 값이 있으면 덮어씀."""
        key = self._key(lat, lng, radius)
        with self._lock:
            self._store[key] = (time() + self._ttl, payload)

    def clear(self) -> None:
        """전체 캐시 초기화 (테스트/수동 invalidate 용)."""
        with self._lock:
            self._store.clear()

    def stats(self) -> dict[str, Any]:
        """현재 엔트리 수와 정책을 반환."""
        now = time()
        with self._lock:
            active = sum(1 for (exp, _) in self._store.values() if exp > now)
            expired = len(self._store) - active
        return {
            "active_entries": active,
            "expired_entries": expired,
            "ttl_seconds": self._ttl,
            "grid_m": self._grid,
        }


# Module-level singleton. main.py 에서 import 해서 사용.
location_cache = LocationCache(ttl_seconds=300, grid_m=100)
