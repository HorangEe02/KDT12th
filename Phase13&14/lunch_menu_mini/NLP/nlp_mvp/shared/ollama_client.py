"""
Backward-compat shim.

기존 코드가 `from nlp_mvp.shared.ollama_client import OllamaClient`로
import하던 것을 그대로 동작시키기 위한 재노출 모듈.
실 구현은 nlp_mvp.shared.llm.ollama 로 이동.
"""
from nlp_mvp.shared.llm.ollama import (
    DEFAULT_HOST,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF,
    OllamaClient,
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
    get_default_client,
)

__all__ = [
    "OllamaClient",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaModelNotFoundError",
    "get_default_client",
    "DEFAULT_HOST",
    "DEFAULT_MODEL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_BACKOFF",
]
