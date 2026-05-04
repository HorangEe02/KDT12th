"""공공데이터포털(`apis.data.go.kr`) 식약처 영양성분 API 수집기.

설계 목표:
  - URL/검색 파라미터/응답 필드명을 환경 변수로 주입 가능 → 어떤 식약처 영양 API
    데이터셋(예: 1471000/FoodNtrCpntDbInfo01, 1471057/FoodNtritionData)에든 적응.
  - 응답을 식품안전나라 collector 와 동일한 정규화 dict 로 반환 → 상위 라우터·시드
    스크립트가 식별 없이 두 provider 결과를 호환.
  - 인증키는 ``DATA_GO_KR_API_KEY_DECODED`` (raw, 미인코딩) 를 ``params`` 로 전달
    → ``requests`` 가 자동 URL 인코딩 (이중 인코딩 방지).

응답 필드명은 API 별로 미묘하게 다르므로 다중 키 후보(`_FIELD_KEYS`)를 순회한다.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Final, Optional

import requests

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# 환경 변수 기반 설정 (override 가능)
# ------------------------------------------------------------------------------
_DEFAULT_URL: Final[str] = (
    "https://apis.data.go.kr/1471000/FoodNtrCpntDbInfo01/getFoodNtrCpntDbInq01"
)
_DEFAULT_NAME_PARAM: Final[str] = "FOOD_NM_KR"
_DEFAULT_NUM_OF_ROWS: Final[int] = 20
_TIMEOUT: Final[int] = 8
_MAX_RETRIES: Final[int] = 3
_BULK_SLEEP_SEC: Final[float] = 0.4


def _env(name: str, default: str = "") -> str:
    val = os.environ.get(name, "").strip()
    return val or default


# ------------------------------------------------------------------------------
# 응답 필드 정규화
# ------------------------------------------------------------------------------
# 각 정규화 키 → 응답 row 에서 시도할 키 후보 목록
# 식약처 영양성분 DB (FoodNtrCpntDbInfo02) AMT_NUM 표준 매핑:
#   AMT_NUM1=에너지(kcal) / AMT_NUM2=수분 / AMT_NUM3=단백질 / AMT_NUM4=지방
#   AMT_NUM5=회분 / AMT_NUM6=탄수화물 / AMT_NUM7=당류 / AMT_NUM8=식이섬유
#   AMT_NUM99=나트륨(mg)
# 식품안전나라 I2790 매핑(NUTR_CONT*)은 다른 순서 — 둘 다 fallback 으로 등록.
_FIELD_KEYS: Final[dict[str, tuple[str, ...]]] = {
    "food_name": ("FOOD_NM_KR", "DESC_KOR", "FOOD_REF_NM", "foodNm"),
    "food_code": ("FOOD_CD", "NUM", "foodCd"),
    "group_name": ("DB_GRP_NM", "FOOD_CAT1_NM", "GROUP_NAME", "FOOD_GROUP"),
    "maker_name": ("MAKER_NAME", "MFR_NM", "mfrNm"),
    "serving_size": ("SERVING_SIZE", "SERVING_WT", "servingWt"),
    "calories": ("AMT_NUM1", "NUTR_CONT1", "ENERGY", "ENERC", "engKcal", "kcal"),
    "protein": ("AMT_NUM3", "NUTR_CONT3", "PROCNT", "prot"),
    "fat": ("AMT_NUM4", "NUTR_CONT4", "FATCE", "fatce"),
    "carbs": ("AMT_NUM6", "NUTR_CONT2", "CHOCDF", "carbo"),
    "sugar": ("AMT_NUM7", "NUTR_CONT5", "SUGAR", "sugar"),
    "sodium": ("AMT_NUM99", "NUTR_CONT6", "NA", "sodium"),
}


def _pick(row: dict[str, Any], keys: tuple[str, ...]) -> Optional[Any]:
    for k in keys:
        if k not in row:
            continue
        v = row[k]
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace("%", "")
    if not s or s.upper() in {"N/A", "NULL", "-"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_row(row: dict[str, Any]) -> dict[str, Any]:
    """raw row → 표준 영양 dict (식품안전나라 collector 와 동일 형태)."""
    name = _pick(row, _FIELD_KEYS["food_name"]) or ""
    serving = _to_float(_pick(row, _FIELD_KEYS["serving_size"])) or 100.0
    return {
        "food_code": str(_pick(row, _FIELD_KEYS["food_code"]) or ""),
        "food_name": (name or "").strip(),
        "group_name": _pick(row, _FIELD_KEYS["group_name"]) or "",
        "maker_name": _pick(row, _FIELD_KEYS["maker_name"]) or "",
        "serving_size": serving,
        "calories": _to_float(_pick(row, _FIELD_KEYS["calories"])),
        "carbs": _to_float(_pick(row, _FIELD_KEYS["carbs"])),
        "protein": _to_float(_pick(row, _FIELD_KEYS["protein"])),
        "fat": _to_float(_pick(row, _FIELD_KEYS["fat"])),
        "sugar": _to_float(_pick(row, _FIELD_KEYS["sugar"])),
        "sodium": _to_float(_pick(row, _FIELD_KEYS["sodium"])),
    }


# ------------------------------------------------------------------------------
# Collector
# ------------------------------------------------------------------------------
class DataGoKrNutritionCollector:
    """공공데이터포털 식약처 영양성분 API 어댑터."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        url: Optional[str] = None,
        name_param: Optional[str] = None,
    ) -> None:
        # 우선순위: 명시 인자 > env DECODED > env ENCODED
        self.api_key = (
            api_key
            or _env("DATA_GO_KR_API_KEY_DECODED")
            or _env("DATA_GO_KR_API_KEY_ENCODED")
        )
        self.url = url or _env("DATA_GO_KR_NUTRITION_URL", _DEFAULT_URL)
        self.name_param = name_param or _env(
            "DATA_GO_KR_NUTRITION_NAME_PARAM", _DEFAULT_NAME_PARAM
        )
        self.is_encoded_key = "%" in (self.api_key or "")

    @property
    def has_key(self) -> bool:
        return bool(self.api_key) and "your_" not in self.api_key

    # --------------------------------------------------------------------------
    def _request(self, params: dict[str, Any]) -> Optional[list[dict[str, Any]]]:
        """공공데이터포털 호출. JSON 응답을 우선 시도, 실패 시 None."""
        if not self.has_key:
            logger.warning("data.go.kr nutrition: API key missing")
            return None

        # Decoded key 면 params 로, Encoded key 면 URL 에 raw string 으로 부착
        if self.is_encoded_key:
            full_url = (
                f"{self.url}?serviceKey={self.api_key}"
                + "".join(f"&{k}={v}" for k, v in params.items())
            )
            req_args = {"timeout": _TIMEOUT}
            target_url = full_url
        else:
            params = {"serviceKey": self.api_key, **params}
            req_args = {"params": params, "timeout": _TIMEOUT}
            target_url = self.url

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = requests.get(target_url, **req_args)
                ctype = resp.headers.get("Content-Type", "").lower()
                text = resp.text

                # 공공데이터포털 인증 실패는 보통 HTML script alert 응답
                if "인증" in text and "유효" in text:
                    logger.warning("data.go.kr nutrition: auth key rejected")
                    return None

                if "json" in ctype or text.lstrip().startswith("{"):
                    return _extract_rows_json(resp.json())
                if text.lstrip().startswith("<"):
                    return _extract_rows_xml(text)
                logger.warning("data.go.kr nutrition unexpected content-type=%s", ctype)
                return None
            except requests.RequestException as e:
                logger.warning(
                    "data.go.kr request attempt %d/%d failed: %s",
                    attempt, _MAX_RETRIES, e,
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(min(2 ** attempt, 5))
        return None

    # --------------------------------------------------------------------------
    def search_by_name(
        self,
        food_name: str,
        max_results: int = _DEFAULT_NUM_OF_ROWS,
    ) -> list[dict[str, Any]]:
        """식품명으로 영양 정보 검색. 식품안전나라 collector 와 동일 인터페이스."""
        if not food_name or not food_name.strip():
            return []

        params = {
            "pageNo": 1,
            "numOfRows": max_results,
            "type": "json",
            self.name_param: food_name.strip(),
        }
        rows = self._request(params)
        if rows is None:
            return []

        results = [_parse_row(r) for r in rows if r]
        results = [r for r in results if r["food_name"]]

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
        out: dict[str, list[dict[str, Any]]] = {}
        for i, name in enumerate(food_names):
            out[name] = self.search_by_name(name, max_results=max_each)
            if i < len(food_names) - 1:
                time.sleep(_BULK_SLEEP_SEC)
        return out


# ------------------------------------------------------------------------------
# 응답 추출 헬퍼
# ------------------------------------------------------------------------------
def _extract_rows_json(payload: Any) -> list[dict[str, Any]]:
    """공공데이터포털 JSON 응답에서 row 리스트를 다중 경로로 추출.

    지원 구조:
      A. {response:{body:{items:{item:[...]}}}}  ← 일반 OpenAPI v2
      B. {response:{body:{items:[...]}}}         ← items 가 직접 배열
      C. {header:..., body:{items:[...]}}        ← 식약처 FoodNtrCpntDbInfo02
      D. {body:{items:[...]}}                    ← 단순 변형
      E. {items:[...]}                           ← 최소
    """
    if not isinstance(payload, dict):
        return []

    # response wrapper 가 있으면 한 단계 들어감
    if "response" in payload:
        body = payload.get("response", {}).get("body", {})
    elif "body" in payload:
        body = payload.get("body", {})
    else:
        body = payload

    if not isinstance(body, dict):
        return []

    items = body.get("items")

    # items 가 dict 인 경우 ({item: [...]} 형태)
    if isinstance(items, dict):
        item = items.get("item")
        if isinstance(item, list):
            return item
        if isinstance(item, dict):
            return [item]
        return []

    # items 가 list 인 경우 (식약처 v02 표준)
    if isinstance(items, list):
        return items

    # 다른 fallback
    if isinstance(body.get("item"), list):
        return body["item"]
    return []


def _extract_rows_xml(text: str) -> list[dict[str, Any]]:
    """간이 XML 파서 — <item>...</item> 단위 추출 (의존성 회피)."""
    import re
    rows: list[dict[str, Any]] = []
    for block in re.findall(r"<item>(.*?)</item>", text, re.DOTALL):
        row: dict[str, Any] = {}
        for k, v in re.findall(r"<(\w+)>([^<]*)</\1>", block):
            row[k] = v.strip()
        if row:
            rows.append(row)
    return rows
