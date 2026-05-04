"""
거리 계산 · 거리 점수 산출 · 카카오 raw → 정제 DataFrame 변환.

Mini 0README §핵심 알고리즘 §1 의 거리 점수 테이블을 구현한다:
    ~100m → 100, ~200m → 85, ~300m → 70, ~400m → 50, 400m+ → 30

GUIDE Subtopic 1 §4 의 RestaurantTransformer 클래스를 함께 제공한다.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any, Final, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# 지구 상수
# =============================================================================
EARTH_RADIUS_M: Final[float] = 6_371_000.0  # 평균 반지름 (m)


# =============================================================================
# Haversine 거리
# =============================================================================
def haversine_distance(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    두 좌표 간의 지표면 거리 (미터).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        dlambda / 2
    ) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


# =============================================================================
# 거리 점수
# =============================================================================
_DISTANCE_SCORE_TABLE: Final[tuple[tuple[float, int], ...]] = (
    (100.0, 100),
    (200.0, 85),
    (300.0, 70),
    (400.0, 50),
)
_DEFAULT_SCORE_BEYOND: Final[int] = 30


def compute_distance_score(distance_m: float) -> int:
    """
    거리(m) → 100점 만점 거리 점수.

    구간:
        ≤ 100m → 100
        ≤ 200m → 85
        ≤ 300m → 70
        ≤ 400m → 50
        > 400m → 30
    """
    if distance_m < 0:
        raise ValueError(f"distance_m must be non-negative, got {distance_m}")

    for max_d, score in _DISTANCE_SCORE_TABLE:
        if distance_m <= max_d:
            return score
    return _DEFAULT_SCORE_BEYOND


# 호환 함수 (GUIDE §4 명명)
def calculate_distance_score(distance_m: int) -> int:
    """`compute_distance_score` 의 GUIDE 명명 호환 별칭."""
    return compute_distance_score(distance_m)


# =============================================================================
# 메뉴 타입 분류
# =============================================================================
def classify_menu_type(category: Optional[str], sub_category: Optional[str]) -> str:
    """
    카테고리·서브카테고리 → 메뉴 타입 분류.

    GUIDE Subtopic 1 §4.1 의 매핑 규칙을 구현.
    """
    if not category:
        return "기타"

    cat = category.strip()
    sub = (sub_category or "").strip()

    # 한식
    if cat == "한식":
        if "국수" in sub or "칼국수" in sub:
            return "면류"
        if "국" in sub or "탕" in sub or "찌개" in sub:
            return "국물"
        if "죽" in sub:
            return "죽"
    # 일식
    if cat == "일식":
        if "초밥" in sub or "롤" in sub:
            return "초밥"
        if "라멘" in sub or "우동" in sub or "소바" in sub:
            return "면류"
    # 양식
    if cat == "양식":
        if "햄버거" in sub or "버거" in sub:
            return "버거"
        if "파스타" in sub or "스파게티" in sub:
            return "면류"
    return cat


# =============================================================================
# RestaurantTransformer
# =============================================================================
class RestaurantTransformer:
    """
    카카오 API raw 응답 → 정제된 DataFrame.

    파이프라인:
        transform()           → DataFrame
        enrich_with_scores()  → distance_score 컬럼 추가
    """

    @staticmethod
    def _parse_category(category_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        "음식점 > 한식 > 도시락" → ("한식", "도시락")
        "음식점 > 카페"        → ("카페", None)
        ""                     → (None, None)
        """
        if not category_name:
            return None, None
        parts = [p.strip() for p in category_name.split(">")]
        # "음식점" prefix 제거
        if parts and parts[0] == "음식점":
            parts = parts[1:]
        if not parts:
            return None, None
        category = parts[0] if len(parts) >= 1 else None
        sub_category = parts[1] if len(parts) >= 2 else None
        return category, sub_category

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            if value is None or value == "":
                return default
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def transform(cls, raw_data: list[dict[str, Any]]) -> pd.DataFrame:
        """
        카카오 documents → 정제된 DataFrame.

        컬럼:
            id, name, category, sub_category, menu_type, address, phone,
            lat, lng, distance_m, place_url, collected_at
        """
        if not raw_data:
            logger.info("transform() called with empty raw_data")
            return pd.DataFrame()

        rows = []
        now = datetime.utcnow()
        for doc in raw_data:
            try:
                doc_id = str(doc.get("id", "")).strip()
                if not doc_id:
                    continue

                category_name = doc.get("category_name", "") or ""
                category, sub_category = cls._parse_category(category_name)
                menu_type = classify_menu_type(category, sub_category)

                address = doc.get("road_address_name") or doc.get("address_name") or None
                phone = (doc.get("phone") or "").strip() or None

                rows.append({
                    "id": doc_id,
                    "name": (doc.get("place_name") or "").strip(),
                    "category": category,
                    "sub_category": sub_category,
                    "menu_type": menu_type,
                    "address": address,
                    "phone": phone,
                    "lat": cls._safe_float(doc.get("y")),
                    "lng": cls._safe_float(doc.get("x")),
                    "distance_m": cls._safe_int(doc.get("distance")),
                    "place_url": doc.get("place_url") or "",
                    "collected_at": now,
                })
            except Exception as e:
                logger.warning("Skipping malformed doc: %s", e)
                continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        # 중복 제거 (id 기준)
        df = df.drop_duplicates(subset=["id"], keep="first")
        # 거리 오름차순
        df = df.sort_values(by="distance_m", ascending=True).reset_index(drop=True)
        logger.info("transform() produced %d unique restaurants", len(df))
        return df

    @classmethod
    def enrich_with_scores(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame 에 distance_score 컬럼을 추가하여 반환.
        """
        if df.empty:
            return df
        result = df.copy()
        result["distance_score"] = result["distance_m"].apply(compute_distance_score)
        return result
