"""
nlp_mvp 공용 로거 설정.

모든 nlp_mvp 서브 모듈은 다음 패턴으로 로거를 가져다 쓴다:

    from nlp_mvp.shared.logger import get_logger
    logger = get_logger(__name__)
    logger.info("hello")

설계 원칙
---------
- 루트 로거 "nlp_mvp" 에 핸들러를 1회만 부착 (중복 출력 방지)
- 콘솔 + 파일 핸들러 동시 지원
- 로그 포맷: 시각 + 로거 이름 + 레벨 + 메시지
- 환경 변수 LOG_LEVEL, LOG_FILE 로 오버라이드 가능
- `configure(...)` 를 명시적으로 호출하지 않아도 기본값으로 동작
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# =============================================================================
# 상수
# =============================================================================
ROOT_LOGGER_NAME = "nlp_mvp"
DEFAULT_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/nlp_mvp.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 3

# 루트 로거가 이미 설정되었는지 추적 (중복 핸들러 부착 방지)
_configured: bool = False


# =============================================================================
# 내부 유틸
# =============================================================================
def _resolve_level(level: Optional[str]) -> int:
    """문자열 레벨 → logging 상수. 잘못된 값이면 INFO."""
    if level is None:
        level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    level = level.upper() if isinstance(level, str) else "INFO"
    return getattr(logging, level, logging.INFO)


def _resolve_log_file(log_file: Optional[str]) -> Optional[Path]:
    """
    로그 파일 경로 결정.

    우선순위: 인자 > 환경변수 LOG_FILE > 기본값.
    빈 문자열/"none" 이면 파일 로깅 비활성.
    """
    if log_file is None:
        log_file = os.getenv("LOG_FILE", DEFAULT_LOG_FILE)
    if not log_file or log_file.lower() == "none":
        return None
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)


# =============================================================================
# 공개 API
# =============================================================================
def configure(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
    force: bool = False,
) -> logging.Logger:
    """
    nlp_mvp 루트 로거 설정.

    첫 호출 시에만 핸들러를 부착한다 (멱등성).

    Args:
        level: "DEBUG" | "INFO" | "WARNING" | "ERROR". None 이면 환경변수/기본값.
        log_file: 로그 파일 경로. None/"" 이면 파일 로깅 비활성.
        console: 콘솔 출력 여부.
        force: True 면 기존 핸들러를 모두 제거하고 재설정 (테스트 용도).

    Returns:
        설정된 nlp_mvp 루트 로거.
    """
    global _configured

    root = logging.getLogger(ROOT_LOGGER_NAME)

    if force:
        root.handlers.clear()
        _configured = False

    if _configured:
        return root

    root.setLevel(_resolve_level(level))
    root.propagate = False  # 최상위 root 로 전파 방지
    formatter = _build_formatter()

    # 콘솔 핸들러
    if console:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    # 파일 핸들러
    resolved_file = _resolve_log_file(log_file)
    if resolved_file is not None:
        file_handler = RotatingFileHandler(
            filename=str(resolved_file),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    _configured = True
    return root


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    서브 모듈에서 사용할 로거 반환.

    - `name` 이 None 이면 루트 (`nlp_mvp`) 반환
    - `__name__` 이 `nlp_mvp.xxx` 형태면 그대로 사용
    - 아니면 `nlp_mvp.<name>` 으로 네임스페이스 부여

    최초 호출 시 자동으로 `configure()` 를 호출한다 (lazy init).
    """
    if not _configured:
        configure()

    if name is None or name == ROOT_LOGGER_NAME:
        return logging.getLogger(ROOT_LOGGER_NAME)

    if name.startswith(ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)

    # 외부 호출 (예: __name__ == "nlp_mvp.sentiment.crawler")
    return logging.getLogger(name) if name.startswith(ROOT_LOGGER_NAME) \
        else logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def set_level(level: str) -> None:
    """런타임에 루트 로거 레벨 변경."""
    logging.getLogger(ROOT_LOGGER_NAME).setLevel(_resolve_level(level))


__all__ = ["configure", "get_logger", "set_level", "ROOT_LOGGER_NAME"]
