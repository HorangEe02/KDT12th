"""
리뷰 텍스트 전처리 (순수 함수).

- clean_text:       URL/이모지/공백 정규화
- is_valid_review:  길이·의미성 검사
- deduplicate:      정제 후 동일 텍스트 제거
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

try:
    import emoji  # type: ignore
    _HAS_EMOJI = True
except ImportError:
    _HAS_EMOJI = False


# =============================================================================
# 정규식 상수 (모듈 레벨에서 1회 컴파일)
# =============================================================================
_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE_PATTERN = re.compile(r"\s+")
# 숫자·특수문자·공백만 있는 경우
_NON_MEANINGFUL_PATTERN = re.compile(r"^[\d\s\W]+$")
# emoji 라이브러리 없을 때 대체: 기본 이모지 블록
_EMOJI_FALLBACK_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002600-\U000027BF"  # misc symbols & dingbats
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    if _HAS_EMOJI:
        return emoji.replace_emoji(text, replace="")
    return _EMOJI_FALLBACK_PATTERN.sub("", text)


# =============================================================================
# 공개 API
# =============================================================================
def clean_text(text: Any) -> str:
    """
    리뷰 텍스트 정제.

    1. 타입이 str 이 아니면 "" 반환
    2. URL 제거 (http/https/www)
    3. 이모지 제거 (emoji 라이브러리 우선, 없으면 regex fallback)
    4. 연속 공백 → 단일 공백
    5. 양쪽 공백 트림
    """
    if not isinstance(text, str):
        return ""
    t = _URL_PATTERN.sub("", text)
    t = _strip_emoji(t)
    t = _WHITESPACE_PATTERN.sub(" ", t)
    return t.strip()


def is_valid_review(text: Any, min_len: int = 5) -> bool:
    """
    리뷰 유효성 검사.

    다음 경우 False:
      - str 이 아닌 경우
      - 길이 < min_len
      - 숫자·특수문자·공백만 있는 경우
    """
    if not isinstance(text, str):
        return False
    if len(text) < min_len:
        return False
    if _NON_MEANINGFUL_PATTERN.match(text):
        return False
    return True


def deduplicate(
    reviews: list[dict[str, Any]],
    text_key: str = "text",
) -> list[dict[str, Any]]:
    """
    정제(clean_text) 결과의 MD5 해시 기준으로 중복 제거.
    입력 순서 보존.
    """
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for r in reviews:
        cleaned = clean_text(r.get(text_key, ""))
        if not cleaned:
            continue
        digest = hashlib.md5(cleaned.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        result.append(r)
    return result
