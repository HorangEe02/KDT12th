"""규칙 기반 자연어 식단 파서.

LLM 없이도 MVP가 동작하도록 날짜, 식사 유형, 만족도, 음식명 후보를 보수적으로
추출한다. 영양 수치는 생성하지 않고 Lunch API의 검증 단계에 맡긴다.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Optional

from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer


_MEAL_TYPE_PATTERNS = [
    ("breakfast", ("아침", "조식")),
    ("lunch", ("점심", "런치", "중식")),
    ("dinner", ("저녁", "석식")),
    ("snack", ("간식", "야식")),
]

# 줄바꿈/세미콜론도 명확한 구분으로 처리. 공백 단독은 음식명 자체가 공백을
# 포함할 수 있어 (예: "치킨 마요") connector 에서 제외 — 사전 매칭 휴리스틱으로 보완.
_CONNECTOR_RE = re.compile(r"\s*(?:\n|;|랑|하고|그리고|및|,|/|\+|와|과)\s*")
_SATISFACTION_RE = re.compile(r"(?:만족도|만족|평점|점수)?\s*([1-5])\s*점")
_QUANTITY_RE = re.compile(r"(.+?)\s*(\d+(?:\.\d+)?)\s*(인분|개|그릇|공기|잔|조각|serving|g|그램)?$")
_REMOVE_WORDS = (
    "오늘",
    "어제",
    "그제",
    "이번",
    "아침",
    "점심",
    "저녁",
    "간식",
    "야식",
    "조식",
    "중식",
    "석식",
)
_TRAILING_RE = re.compile(
    r"(먹었어|먹었어요|먹었다|먹음|먹고|먹었고|먹은|먹었는데|먹었습니다|마셨어|마셨다|마심).*$"
)
_PARTICLE_RE = re.compile(r"(을|를|은|는|이|가|도|으로|로)$")

# 음식명 외 노이즈/감탄 표현 — _clean_item에서 제거.
# 사전 매칭에 방해되지 않도록 가능한 보수적으로만 등록한다.
_NOISE_WORDS: frozenset[str] = frozenset(
    {
        "맛도리", "맛집", "꿀맛", "꿀잼",
        "갓", "찐", "찐맛", "최고", "굿", "굳",
        "존맛", "존맛탱", "존맛탱구리", "jmt",
        "배달", "포장", "테이크아웃",
        "한그릇", "한공기",
    }
)


def _strip_noise_tokens(name: str) -> str:
    """음식명 후보에서 노이즈 토큰을 제거한다.

    공백 분리 단위로 검사하며, 모든 토큰이 노이즈인 경우 원문 유지(파괴 방지).
    """
    if not name:
        return name
    tokens = name.split()
    kept = [t for t in tokens if t.lower() not in _NOISE_WORDS]
    if not kept:
        return name
    return " ".join(kept)


def _parse_base_date(value: Optional[str]) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError:
        return date.today()


def _meal_date(text: str, base: date) -> date:
    if "그제" in text:
        return base - timedelta(days=2)
    if "어제" in text:
        return base - timedelta(days=1)
    return base


def _meal_type(text: str) -> str:
    for meal_type, keywords in _MEAL_TYPE_PATTERNS:
        if any(keyword in text for keyword in keywords):
            return meal_type
    return "unknown"


def _satisfaction(text: str) -> Optional[int]:
    match = _SATISFACTION_RE.search(text)
    if not match:
        return None
    return int(match.group(1))


def _restaurant_hint(text: str) -> Optional[str]:
    if "에서" not in text:
        return None
    before = text.split("에서", 1)[0].strip()
    before = re.sub(r"^(오늘|어제|그제|이번|아침|점심|저녁|간식|야식)\s*", "", before)
    before = before.strip(" ,.")
    if not before or before in {"집", "회사", "사무실"}:
        return None
    return before[-40:]


def _food_segment(text: str) -> str:
    segment = text
    if "에서" in segment:
        segment = segment.split("에서", 1)[1]
    segment = _SATISFACTION_RE.sub("", segment)
    segment = _TRAILING_RE.sub("", segment)
    for word in _REMOVE_WORDS:
        segment = segment.replace(word, " ")
    segment = re.sub(r"\s+", " ", segment)
    return segment.strip(" ,. ")


def _parse_quantity(raw: str) -> tuple[str, float, str]:
    raw = raw.strip()
    if not raw:
        return raw, 1.0, "serving"
    if "반" in raw and len(raw) <= 8:
        return raw.replace("반", "").strip() or raw, 0.5, "serving"
    match = _QUANTITY_RE.match(raw)
    if not match:
        return raw, 1.0, "serving"
    name = match.group(1).strip()
    quantity = float(match.group(2))
    unit = match.group(3) or "serving"
    return name, quantity, unit


def _clean_item(raw: str) -> str:
    cleaned = raw.strip(" ,. ")
    cleaned = re.sub(r"^(에|엔|에는|때|때는)\s+", "", cleaned)
    cleaned = _PARTICLE_RE.sub("", cleaned)
    cleaned = _strip_noise_tokens(cleaned)
    return cleaned.strip()


_DICT_SPLIT_THRESHOLD = 0.7  # 분리 시 각 토큰의 최소 매칭 신뢰도


def _split_parts_by_dictionary(
    parts: list[str],
    normalizer: Optional[MenuNormalizer],
) -> list[str]:
    """공백 분리된 두 토큰이 모두 사전 매칭되면 분리, 아니면 원문 유지.

    예) "갈비 공기밥" → ["갈비", "공기밥"] (둘 다 사전 매칭 시)
        "치킨 마요" → ["치킨 마요"] (하나라도 매칭 안 되면 원문)
        "김치찌개"  → ["김치찌개"] (공백 없음 → 그대로)
    """
    if normalizer is None:
        return parts
    out: list[str] = []
    for part in parts:
        tokens = [t for t in part.split() if t]
        if len(tokens) <= 1:
            out.append(part)
            continue
        # 모든 토큰이 임계값 이상 신뢰도로 정규화 매칭되어야 분리
        try:
            confidences = []
            for tok in tokens:
                # 노이즈 토큰은 분리 시도 전에 제거되어야 자연스러움
                if tok.lower() in _NOISE_WORDS:
                    confidences.append(0.0)
                    continue
                result = normalizer.normalize(tok)
                conf = float(getattr(result, "confidence", 0.0) or 0.0)
                # matched_name 이 있는 경우만 진짜 매칭으로 인정
                if not getattr(result, "matched_name", None):
                    conf = 0.0
                confidences.append(conf)
        except Exception:
            out.append(part)
            continue
        # 모든 토큰이 임계값 이상이어야 분리
        if confidences and all(c >= _DICT_SPLIT_THRESHOLD for c in confidences):
            out.extend(tokens)
        else:
            out.append(part)
    return out


def _normalize(name: str, normalizer: Optional[MenuNormalizer]) -> tuple[Optional[str], float, str]:
    if normalizer is None:
        return None, 0.55, "rule"
    try:
        result = normalizer.normalize(name)
    except Exception:
        return None, 0.5, "rule"
    if result.matched_name:
        return result.matched_name, float(result.confidence), result.method
    return result.cleaned or None, max(float(result.confidence), 0.55), result.method


def parse_meal_text(
    text: str,
    user_id: str = "user1",
    base_date: Optional[str] = None,
    normalizer: Optional[MenuNormalizer] = None,
) -> dict[str, Any]:
    """자연어 식단 문장을 구조화한다.

    Args:
        text: 사용자가 입력한 자연어 식단.
        user_id: 요청 사용자 ID.
        base_date: 상대 날짜 표현 해석 기준일(YYYY-MM-DD).
        normalizer: 선택적 메뉴 정규화기.

    Returns:
        저장 전 확인 UI에서 사용할 구조화 결과.
    """
    base = _parse_base_date(base_date)
    segment = _food_segment(text)
    raw_parts = [_clean_item(part) for part in _CONNECTOR_RE.split(segment)]
    raw_parts = [part for part in raw_parts if part]
    # 공백 분리 휴리스틱: 각 part 가 공백을 포함하고 split 한 토큰이 모두
    # 사전(normalizer)에서 충분히 매칭되면 분리. 아니면 원문 유지.
    raw_parts = _split_parts_by_dictionary(raw_parts, normalizer)

    warnings: list[str] = []
    items = []
    methods: list[str] = []
    for part in raw_parts:
        name, quantity, unit = _parse_quantity(part)
        name = _clean_item(name)
        if not name:
            continue
        normalized, confidence, method = _normalize(name, normalizer)
        methods.append(method)
        items.append({
            "raw_name": name,
            "normalized_name": normalized,
            "quantity": quantity,
            "unit": unit,
            "confidence": round(confidence, 3),
            "needs_review": confidence < 0.7,
        })

    if not items:
        warnings.append("음식명을 명확히 찾지 못했습니다. 직접 항목을 추가해 주세요.")

    avg_confidence = (
        round(sum(item["confidence"] for item in items) / len(items), 3)
        if items else 0.0
    )
    method = "rule"
    if methods:
        method = "rule+normalizer" if any(m != "rule" for m in methods) else "rule"

    return {
        "user_id": user_id,
        "raw_text": text,
        "meal_date": _meal_date(text, base).isoformat(),
        "meal_type": _meal_type(text),
        "restaurant_hint": _restaurant_hint(text),
        "satisfaction": _satisfaction(text),
        "items": items,
        "warnings": warnings,
        "parser": {
            "method": method,
            "confidence": avg_confidence,
        },
    }
