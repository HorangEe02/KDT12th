"""
메뉴명 규칙 기반 전처리 모듈.

- 괄호 · 크기 · 수량 · 특수문자 제거
- 동의어 사전 기반 표준화
- 순수 함수 (side-effect 없음)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 정규식 상수
# =============================================================================
_BRACKET_PATTERN = re.compile(r"[\(\[\{（［｛].*?[\)\]\}）］｝]")
_SIZE_PATTERN = re.compile(r"[\s]?(대|중|소|특|왕|미니|라지|스몰|점보)$")
_QUANTITY_PATTERN = re.compile(r"\s?\d+\s?(인분|개|그릇|팩|세트)")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_NON_ALNUM_PATTERN = re.compile(r"[^\w가-힣\s]")


# =============================================================================
# 함수
# =============================================================================
def preprocess_menu_name(raw: Any) -> str:
    """원시 메뉴명을 정제한다."""
    if not isinstance(raw, str):
        return ""
    text = raw
    text = _BRACKET_PATTERN.sub("", text)
    text = _QUANTITY_PATTERN.sub("", text)
    text = _SIZE_PATTERN.sub("", text)
    text = _NON_ALNUM_PATTERN.sub("", text)
    text = _WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()


def apply_synonyms(text: str, synonym_dict: dict[str, Any]) -> str:
    """동의어 사전 기반 치환. 가장 긴 key 부터 매칭(greedy). 한 번만 치환."""
    if not text or not synonym_dict:
        return text

    mapping = synonym_dict.get("synonyms", synonym_dict)
    if not isinstance(mapping, dict):
        return text

    for src in sorted((k for k in mapping.keys() if isinstance(k, str)), key=len, reverse=True):
        if src and src in text:
            text = text.replace(src, mapping[src])
            break
    return text


def load_synonym_dict(path: str | Path | None = None) -> dict[str, Any]:
    """동의어 사전 JSON 로드. 실패 시 빈 dict."""
    if path is None:
        path = Path(__file__).parent / "synonym_dict.json"
    path = Path(path)

    if not path.exists():
        logger.warning(f"Synonym dict not found: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded synonym dict from {path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return {}


# =============================================================================
# 클래스
# =============================================================================
class SynonymDict:
    """동의어 사전 래퍼. 캐싱 및 재로드 지원."""

    def __init__(self, path: str | Path | None = None):
        self.path = path
        self._dict: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        self._dict = load_synonym_dict(self.path)

    def apply(self, text: str) -> str:
        return apply_synonyms(text, self._dict)

    def add(self, src: str, dst: str) -> None:
        mapping = self._dict.setdefault("synonyms", {})
        mapping[src] = dst

    def save(self) -> None:
        if self.path is None:
            raise ValueError("No path to save to")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._dict, f, ensure_ascii=False, indent=2)

    def __len__(self) -> int:
        return len(self._dict.get("synonyms", {}))
