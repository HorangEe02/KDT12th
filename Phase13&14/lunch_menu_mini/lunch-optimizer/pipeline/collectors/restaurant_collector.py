"""
카카오 로컬 API 음식점 수집기 (순수 collector).

정제·점수·DB 적재는 pipeline.transformers / pipeline.loaders 가 담당한다.
본 모듈은 raw 카카오 응답을 list[dict] 로 반환하는 데에 집중한다.

Features:
- 페이지네이션 (최대 45p × 15개)
- 재시도 (exponential backoff, 최대 3회)
- 429 Rate limit 시 Retry-After 존중
- 일일 호출 카운터 (메모리, 일 10만 건 한도 가드)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterator, Optional

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# 통계
# =============================================================================
@dataclass
class CollectStats:
    pages_fetched: int = 0
    total_fetched: int = 0
    errors: int = 0
    api_calls: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "pages_fetched": self.pages_fetched,
            "total_fetched": self.total_fetched,
            "errors": self.errors,
            "api_calls": self.api_calls,
        }


# =============================================================================
# 일일 호출 카운터
# =============================================================================
@dataclass
class DailyQuotaTracker:
    """카카오 일일 한도 (10만 건) 가드. 메모리 기반."""
    limit: int = 100_000
    _date: date = field(default_factory=date.today)
    _count: int = 0

    def reset_if_new_day(self) -> None:
        today = date.today()
        if today != self._date:
            self._date = today
            self._count = 0

    def increment(self) -> None:
        self.reset_if_new_day()
        self._count += 1

    def is_exhausted(self) -> bool:
        self.reset_if_new_day()
        return self._count >= self.limit

    @property
    def remaining(self) -> int:
        self.reset_if_new_day()
        return max(0, self.limit - self._count)


# =============================================================================
# 수집기
# =============================================================================
class RestaurantCollector:
    """
    카카오 로컬 API 호출 전담 클래스.

    Usage:
        collector = RestaurantCollector()
        raw_docs = collector.collect_all()
        # raw_docs : list[dict]  (카카오 documents 그대로)
    """

    PAGE_SIZE = 15  # 카카오 API 최대값
    MAX_PAGES = 45  # 카카오 API 제한
    SLEEP_BETWEEN_REQUESTS = 0.3  # 초
    MAX_RETRIES = 3
    TIMEOUT = 10.0

    def __init__(
        self,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius_m: Optional[int] = None,
        category_code: Optional[str] = None,
        quota_tracker: Optional[DailyQuotaTracker] = None,
    ):
        self.lat = lat if lat is not None else settings.office.lat
        self.lng = lng if lng is not None else settings.office.lng
        self.radius_m = radius_m if radius_m is not None else settings.office.search_radius_m
        self.category_code = category_code or settings.kakao.default_category_code
        self.quota = quota_tracker or DailyQuotaTracker()
        self.stats = CollectStats()

        if not settings.kakao.has_key:
            raise RuntimeError(
                "KAKAO_REST_API_KEY is not set. "
                "Configure Mini/.env (copy from .env.example)."
            )

    # -------------------------------------------------------------------------
    # 저수준 API 호출
    # -------------------------------------------------------------------------
    def _fetch_page(self, page: int) -> Optional[dict[str, Any]]:
        """
        단일 페이지 조회. 실패 시 재시도 후 None.
        """
        if self.quota.is_exhausted():
            logger.error("Daily quota exhausted (limit=%d)", self.quota.limit)
            return None

        url = settings.kakao.base_url + settings.kakao.category_search_path
        params = {
            "category_group_code": self.category_code,
            "x": self.lng,
            "y": self.lat,
            "radius": self.radius_m,
            "page": page,
            "size": self.PAGE_SIZE,
            "sort": "distance",
        }
        headers = settings.kakao.request_headers

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self.stats.api_calls += 1
                self.quota.increment()
                response = requests.get(
                    url, params=params, headers=headers, timeout=self.TIMEOUT
                )
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 2))
                    logger.warning(
                        "Rate limited (429), waiting %.1fs before retry", retry_after
                    )
                    time.sleep(retry_after)
                    continue
                if response.status_code == 401:
                    # 상세 에러 메시지를 로깅하여 진단 용이하게
                    body = response.text[:200]
                    logger.error(
                        "Kakao API 401 Unauthorized — %s\n"
                        "  Check: 1) KAKAO_REST_API_KEY valid  "
                        "2) Kakao Developers > Web domain includes %s",
                        body,
                        settings.kakao.ka_origin,
                    )
                    return None
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.warning(
                    "fetch_page(page=%d) attempt %d/%d failed: %s",
                    page, attempt, self.MAX_RETRIES, e,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 5))  # exponential backoff
        logger.error("fetch_page(page=%d) permanently failed", page)
        self.stats.errors += 1
        return None

    # -------------------------------------------------------------------------
    # 페이지 순회
    # -------------------------------------------------------------------------
    def iter_pages(self) -> Iterator[list[dict[str, Any]]]:
        for page in range(1, self.MAX_PAGES + 1):
            data = self._fetch_page(page)
            if data is None:
                break

            documents = data.get("documents", []) or []
            meta = data.get("meta", {}) or {}

            if not documents:
                break

            self.stats.pages_fetched += 1
            yield documents

            if meta.get("is_end", True):
                break

            time.sleep(self.SLEEP_BETWEEN_REQUESTS)

    # -------------------------------------------------------------------------
    # 단일 중심점 수집
    # -------------------------------------------------------------------------
    def _collect_single(self) -> list[dict[str, Any]]:
        """단일 (lat, lng, radius_m) 로 카카오 API 페이지 순회."""
        docs: list[dict[str, Any]] = []
        for documents in self.iter_pages():
            docs.extend(documents)
            self.stats.total_fetched += len(documents)
        return docs

    # -------------------------------------------------------------------------
    # 영역 분할 수집 (pageable_count=45 제한 우회)
    # -------------------------------------------------------------------------
    @staticmethod
    def _grid_centers(
        lat: float, lng: float, radius_m: int, cell_radius: int = 250,
    ) -> list[tuple[float, float, int]]:
        """
        반경이 큰 경우 영역을 작은 셀(cell_radius)로 분할하여 각 셀 중심 좌표를 생성.
        카카오 API pageable_count=45 제한 때문에, 셀당 45개씩 수집하면 전체 커버 가능.

        Returns:
            [(cell_lat, cell_lng, cell_radius), ...]
        """
        import math
        # 셀 간격 = cell_radius * 1.5 (겹침 허용하여 빈 틈 방지)
        step_m = cell_radius * 1.5
        # 미터 → 위도/경도 변환 (근사)
        lat_per_m = 1.0 / 111_000.0
        lng_per_m = 1.0 / (111_000.0 * math.cos(math.radians(lat)))

        cells = []
        # 그리드 범위
        steps = int(math.ceil(radius_m / step_m))
        for dy in range(-steps, steps + 1):
            for dx in range(-steps, steps + 1):
                clat = lat + dy * step_m * lat_per_m
                clng = lng + dx * step_m * lng_per_m
                # 원래 중심에서 이 셀 중심까지의 거리가 반경 내인지 확인
                dist = math.sqrt((dy * step_m) ** 2 + (dx * step_m) ** 2)
                if dist <= radius_m + cell_radius:
                    cells.append((clat, clng, cell_radius))
        return cells

    # -------------------------------------------------------------------------
    # 메인
    # -------------------------------------------------------------------------
    def collect_all(self) -> list[dict[str, Any]]:
        """
        반경 내 모든 음식점 raw documents 수집.

        반경 ≤ 500m: 단일 요청 (45개 제한 내 충분)
        반경 > 500m: 영역 분할 수집 (250m 셀로 쪼개서 병렬 수집)

        Returns:
            list[dict] — 카카오 API documents 원본 (중복 제거 완료)
        """
        logger.info(
            "RestaurantCollector starting: center=(%s, %s), radius=%dm",
            self.lat, self.lng, self.radius_m,
        )

        if self.radius_m <= 500:
            # 작은 반경: 단일 수집으로 충분
            docs = self._collect_single()
        else:
            # 큰 반경: 영역 분할 수집
            cells = self._grid_centers(
                self.lat, self.lng, self.radius_m, cell_radius=250,
            )
            logger.info(
                "Grid subdivision: %dm radius → %d cells (250m each)",
                self.radius_m, len(cells),
            )
            seen_ids: set[str] = set()
            docs: list[dict[str, Any]] = []
            for i, (clat, clng, cr) in enumerate(cells):
                # 각 셀에서 수집
                sub = RestaurantCollector(
                    lat=clat, lng=clng, radius_m=cr,
                    category_code=self.category_code,
                    quota_tracker=self.quota,
                )
                sub_docs = sub._collect_single()
                # 중복 제거 (id 기준)
                for d in sub_docs:
                    did = str(d.get("id", ""))
                    if did and did not in seen_ids:
                        seen_ids.add(did)
                        docs.append(d)
                self.stats.pages_fetched += sub.stats.pages_fetched
                self.stats.total_fetched += sub.stats.total_fetched
                self.stats.errors += sub.stats.errors
                self.stats.api_calls += sub.stats.api_calls

                if self.quota.is_exhausted():
                    logger.warning("Quota exhausted during grid collection at cell %d/%d", i+1, len(cells))
                    break

        logger.info(
            "RestaurantCollector done: %d unique docs, stats=%s",
            len(docs), self.stats.to_dict(),
        )
        return docs


# =============================================================================
# CLI (단독 수집 + DataFrame 출력 — 적재는 scheduler 에서)
# =============================================================================
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Mini Restaurant Collector (raw)")
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lng", type=float, default=None)
    parser.add_argument("--radius", type=int, default=None)
    parser.add_argument("--show", type=int, default=5, help="상위 N개만 출력")
    args = parser.parse_args()

    logging.basicConfig(
        level=settings.logging.level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    collector = RestaurantCollector(
        lat=args.lat, lng=args.lng, radius_m=args.radius
    )
    docs = collector.collect_all()
    print(f"\nCollected {len(docs)} documents. Top {args.show}:")
    for i, doc in enumerate(docs[: args.show], 1):
        print(f"  {i}. {doc.get('place_name')} "
              f"({doc.get('category_name')}, {doc.get('distance')}m)")
    print(f"\nStats: {collector.stats.to_dict()}")


if __name__ == "__main__":
    main()
