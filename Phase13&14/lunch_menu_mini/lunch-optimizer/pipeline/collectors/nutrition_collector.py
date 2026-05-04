"""
식품안전나라 영양성분 DB API (I2790) 수집기.

- search_by_name: 식품명 키워드 검색
- get_by_code: 식품코드 조회
- search_bulk: 여러 키워드 일괄 검색
- NUTR_CONT 필드의 "", "N/A", 이상치 방어
"""
from __future__ import annotations

import logging
import time
from typing import Any, Final, Optional
from urllib.parse import quote

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# 상수
# =============================================================================
_BASE_URL: Final[str] = "https://openapi.foodsafetykorea.go.kr/api"
_SERVICE_ID: Final[str] = "I2790"
_DEFAULT_FORMAT: Final[str] = "json"
_MAX_RETRIES: Final[int] = 3
_TIMEOUT: Final[float] = 10.0
_BULK_SLEEP_SEC: Final[float] = 0.5

# NUTR_CONT 필드 매핑
_NUTR_FIELDS: Final[dict[str, str]] = {
    "calories":     "NUTR_CONT1",
    "carbs":        "NUTR_CONT2",
    "protein":      "NUTR_CONT3",
    "fat":          "NUTR_CONT4",
    "sugar":        "NUTR_CONT5",
    "sodium":       "NUTR_CONT6",
    "cholesterol":  "NUTR_CONT7",
    "saturated_fat": "NUTR_CONT8",
    "trans_fat":    "NUTR_CONT9",
}

# 이상치 임계 (100g 당)
_OUTLIER_THRESHOLDS_PER_100G: Final[dict[str, float]] = {
    "calories": 900,
    "protein": 100,
    "fat": 100,
    "carbs": 100,
}


def _parse_nutr(value: Any) -> Optional[float]:
    """
    NUTR_CONT 값 파싱.

    "" → 0.0
    "N/A" → None
    기타 숫자 → float
    """
    if value is None or value == "":
        return 0.0
    if isinstance(value, str) and value.strip().upper() in ("N/A", "NA", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_serving_size(value: Any) -> float:
    """SERVING_SIZE 파싱 (기본 100g)."""
    if value is None or value == "":
        return 100.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 100.0


# =============================================================================
# 수집기
# =============================================================================
class NutritionCollector:
    """
    식품안전나라 I2790 API 수집기.
    """

    def __init__(self, api_key: Optional[str] = None):
        # ── 식품안전나라(I2790) 키 ──
        self.api_key = api_key or settings.datago.decoded_key or ""
        import os
        explicit = os.getenv("FOOD_SAFETY_API_KEY", "")
        if explicit and "your_" not in explicit:
            self.api_key = explicit
        self.has_food_safety_key = bool(self.api_key) and "your_" not in self.api_key

        # ── dual-provider 라우팅 설정 ──
        np = settings.nutrition_provider
        self._provider = (np.provider or "data_go_kr").lower()
        self._fallback_to_food_safety = bool(np.fallback_to_food_safety)
        self._dgk: Optional[Any] = None  # DataGoKrNutritionCollector lazy

        # food_safety 모드인데 키가 없으면 명확히 실패
        if self._provider == "food_safety" and not self.has_food_safety_key:
            raise RuntimeError(
                "NUTRITION_PROVIDER=food_safety 인데 FOOD_SAFETY_API_KEY 미설정. "
                "키를 설정하거나 NUTRITION_PROVIDER=data_go_kr 으로 변경."
            )

    def _get_dgk(self):
        """DataGoKrNutritionCollector lazy 초기화."""
        if self._dgk is None:
            try:
                from pipeline.collectors.data_go_kr_nutrition_collector import (
                    DataGoKrNutritionCollector,
                )
                self._dgk = DataGoKrNutritionCollector()
            except Exception as e:  # noqa: BLE001
                logger.warning("DataGoKrNutritionCollector init failed: %s", e)
                self._dgk = False  # type: ignore[assignment]
        return self._dgk if self._dgk else None

    # -------------------------------------------------------------------------
    # URL 빌더
    # -------------------------------------------------------------------------
    def _build_url(
        self,
        start_idx: int = 1,
        end_idx: int = 20,
        filter_key: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> str:
        path = f"{_BASE_URL}/{self.api_key}/{_SERVICE_ID}/{_DEFAULT_FORMAT}/{start_idx}/{end_idx}"
        if filter_key and filter_value is not None:
            # 한글 인코딩을 requests 에 맡김
            path += f"/{filter_key}={quote(filter_value)}"
        return path

    # -------------------------------------------------------------------------
    # HTTP 호출 (재시도 포함)
    # -------------------------------------------------------------------------
    def _request(self, url: str) -> Optional[dict[str, Any]]:
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = requests.get(url, timeout=_TIMEOUT)
                ctype = resp.headers.get("Content-Type", "").lower()
                text = resp.text

                if "json" not in ctype and text.lstrip().startswith("<"):
                    logger.warning(
                        "Nutrition API returned non-JSON (HTML/XML): %s",
                        text[:200],
                    )
                    return None

                data = resp.json()
                body = data.get(_SERVICE_ID, {}) if isinstance(data, dict) else {}
                result = body.get("RESULT") or {}
                code = result.get("CODE", "")

                if code == "INFO-000":
                    return body
                if code == "INFO-200":
                    logger.info("Nutrition API: no matching data")
                    return {"row": []}
                if code:
                    logger.warning(
                        "Nutrition API error: code=%s msg=%s",
                        code, result.get("MSG", ""),
                    )
                    return None

                # 일부 응답은 RESULT 없이 row 를 바로 반환
                if "row" in body:
                    return body
                return None
            except requests.RequestException as e:
                logger.warning(
                    "nutrition request attempt %d/%d failed: %s",
                    attempt, _MAX_RETRIES, e,
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 5))
        return None

    # -------------------------------------------------------------------------
    # 파싱
    # -------------------------------------------------------------------------
    def _parse_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """단일 row → 정제된 영양 dict."""
        serving_size = _parse_serving_size(row.get("SERVING_SIZE"))
        result: dict[str, Any] = {
            "food_code": row.get("FOOD_CD", ""),
            "food_name": (row.get("DESC_KOR") or "").strip(),
            "serving_size": serving_size,
            "group_name": row.get("GROUP_NAME") or "",
            "maker_name": row.get("MAKER_NAME") or "",
            "source": row.get("SUB_REF_NAME") or "",
            "year": row.get("RESEARCH_YEAR") or "",
        }
        for key, api_field in _NUTR_FIELDS.items():
            result[key] = _parse_nutr(row.get(api_field))
        return result

    def _is_outlier(self, parsed: dict[str, Any]) -> bool:
        """100g 당 환산 값이 이상치인지."""
        serving = parsed.get("serving_size") or 100.0
        if serving <= 0:
            return True
        factor = 100.0 / serving
        for key, threshold in _OUTLIER_THRESHOLDS_PER_100G.items():
            v = parsed.get(key)
            if v is None:
                continue
            if v * factor > threshold:
                return True
        return False

    # -------------------------------------------------------------------------
    # 공개 API
    # -------------------------------------------------------------------------
    def search_by_name(
        self,
        food_name: str,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """
        식품명 키워드 검색. NUTRITION_PROVIDER 설정에 따라 라우팅.
        """
        if not food_name or not food_name.strip():
            return []

        # ── dual-provider 라우팅 ──
        if self._provider in {"data_go_kr", "auto"}:
            dgk = self._get_dgk()
            if dgk is not None and dgk.has_key:
                rows = dgk.search_by_name(food_name, max_results=max_results)
                if rows:
                    return rows
                logger.info(
                    "data.go.kr nutrition: empty result for %r%s",
                    food_name,
                    " — falling back to food_safety" if (
                        self._fallback_to_food_safety and self.has_food_safety_key
                    ) else "",
                )
                if not (self._fallback_to_food_safety and self.has_food_safety_key):
                    return []
            else:
                if not (self._fallback_to_food_safety and self.has_food_safety_key):
                    return []
                logger.info("data.go.kr unavailable — falling back to food_safety")

        if not self.has_food_safety_key:
            return []

        url = self._build_url(
            start_idx=1,
            end_idx=max_results,
            filter_key="DESC_KOR",
            filter_value=food_name.strip(),
        )
        body = self._request(url)
        if body is None:
            return []

        rows = body.get("row") or []
        results: list[dict[str, Any]] = []
        for row in rows:
            parsed = self._parse_row(row)
            if self._is_outlier(parsed):
                logger.info(
                    "Skipping outlier: %s (serving=%s, cal=%s)",
                    parsed.get("food_name"),
                    parsed.get("serving_size"),
                    parsed.get("calories"),
                )
                continue
            results.append(parsed)

        # 정렬 우선순위: 정확 일치 > 짧은 이름 > "음식류" group
        def _rank_key(p: dict[str, Any]) -> tuple:
            name = p.get("food_name", "")
            exact = 0 if name == food_name else 1
            length = len(name)
            is_food_group = 0 if "음식" in (p.get("group_name") or "") else 1
            return (exact, is_food_group, length)

        results.sort(key=_rank_key)
        return results

    def search_bulk(
        self,
        food_names: list[str],
        max_each: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """여러 식품명 일괄 검색 (API 호출 간 0.5초 sleep)."""
        result: dict[str, list[dict[str, Any]]] = {}
        for i, name in enumerate(food_names):
            result[name] = self.search_by_name(name, max_results=max_each)
            if i < len(food_names) - 1:
                time.sleep(_BULK_SLEEP_SEC)
        return result

    def get_by_code(self, food_code: str) -> Optional[dict[str, Any]]:
        """식품코드로 조회."""
        if not food_code:
            return None
        url = self._build_url(
            start_idx=1, end_idx=1, filter_key="FOOD_CD", filter_value=food_code
        )
        body = self._request(url)
        if body is None:
            return None
        rows = body.get("row") or []
        if not rows:
            return None
        return self._parse_row(rows[0])
