"""
OllamaClient — LLMClient 구현체 (provider="ollama").

기존 nlp_mvp.shared.ollama_client.OllamaClient 의 코드를 이동.
인터페이스는 100% 동일 + LLMClient ABC 준수.
이전 코드와의 호환을 위해 OllamaError 등의 별칭도 유지한다 (shim 파일에서 재노출).
"""
from __future__ import annotations

import json as _json
import os
import time
from typing import Any, Iterator, Optional

from dotenv import load_dotenv

from nlp_mvp.shared.llm.base import (
    LLMClient,
    LLMConnectionError,
    LLMError,
    LLMModelNotFoundError,
)
from nlp_mvp.shared.logger import get_logger

load_dotenv()

logger = get_logger("nlp_mvp.shared.llm.ollama")

# =============================================================================
# 기본값
# =============================================================================
DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF = 1.5

# SDK 가용성 (lazy)
_OLLAMA_SDK_AVAILABLE: Optional[bool] = None


def _is_sdk_available() -> bool:
    global _OLLAMA_SDK_AVAILABLE
    if _OLLAMA_SDK_AVAILABLE is None:
        try:
            import ollama  # noqa: F401
            _OLLAMA_SDK_AVAILABLE = True
        except ImportError:
            _OLLAMA_SDK_AVAILABLE = False
            logger.warning(
                "ollama SDK not installed; falling back to HTTP. "
                "Install via `pip install ollama==0.3.0`"
            )
    return _OLLAMA_SDK_AVAILABLE


# =============================================================================
# 호환 예외 — 이전 import 경로 유지용
# =============================================================================
OllamaError = LLMError
OllamaConnectionError = LLMConnectionError
OllamaModelNotFoundError = LLMModelNotFoundError


# =============================================================================
# OllamaClient
# =============================================================================
class OllamaClient(LLMClient):
    """Ollama 서버 호출 래퍼."""

    provider = "ollama"

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
    ):
        self._host = host or os.getenv("OLLAMA_HOST", DEFAULT_HOST)
        self._model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._sdk_client = None
        logger.info(f"OllamaClient initialized: host={self._host}, model={self._model}")

    @property
    def model(self) -> str:
        return self._model

    @property
    def host(self) -> str:
        return self._host

    # -------------------------------------------------------------------------
    # SDK lazy init
    # -------------------------------------------------------------------------
    def _get_sdk_client(self):
        if self._sdk_client is None and _is_sdk_available():
            import ollama
            self._sdk_client = ollama.Client(host=self._host, timeout=self.timeout)
        return self._sdk_client

    # -------------------------------------------------------------------------
    # 공개 API
    # -------------------------------------------------------------------------
    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> str:
        model = model or self._model
        options = options or {}
        logger.debug(
            f"chat() called: model={model}, messages={len(messages)}, options={options}"
        )

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                start = time.time()
                if _is_sdk_available():
                    text = self._chat_sdk(messages, model, options)
                else:
                    text = self._chat_http(messages, model, options)
                elapsed = time.time() - start
                logger.info(
                    f"chat() OK (attempt={attempt}, latency={elapsed:.2f}s, "
                    f"tokens≈{len(text)//4})"
                )
                return text
            except LLMModelNotFoundError:
                raise
            except Exception as e:
                last_error = e
                if attempt <= self.max_retries:
                    wait = self.retry_backoff ** attempt
                    logger.warning(
                        f"chat() failed (attempt={attempt}): {e}, "
                        f"retrying in {wait:.1f}s"
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"chat() failed permanently: {e}")

        raise LLMConnectionError(
            f"Ollama chat failed after {self.max_retries + 1} attempts: {last_error}"
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> Iterator[str]:
        model = model or self._model
        options = options or {}
        logger.debug(
            f"chat_stream() called: model={model}, messages={len(messages)}, "
            f"options={options}"
        )
        start = time.time()
        try:
            if _is_sdk_available():
                yield from self._chat_stream_sdk(messages, model, options)
            else:
                yield from self._chat_stream_http(messages, model, options)
        finally:
            elapsed = time.time() - start
            logger.info(f"chat_stream() done (latency={elapsed:.2f}s)")

    def _chat_stream_sdk(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any],
    ) -> Iterator[str]:
        import ollama
        client = self._get_sdk_client()
        try:
            for chunk in client.chat(
                model=model,
                messages=messages,
                options=options,
                stream=True,
            ):
                if isinstance(chunk, dict):
                    content = chunk.get("message", {}).get("content", "")
                else:
                    content = getattr(
                        getattr(chunk, "message", None), "content", ""
                    )
                if content:
                    yield content
        except ollama.ResponseError as e:
            if "not found" in str(e).lower():
                raise LLMModelNotFoundError(
                    f"Model '{model}' not found. Run: ollama pull {model}"
                ) from e
            raise LLMError(f"Ollama response error: {e}") from e

    def _chat_stream_http(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any],
    ) -> Iterator[str]:
        import requests

        url = f"{self._host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options,
        }
        try:
            with requests.post(
                url, json=payload, timeout=self.timeout, stream=True
            ) as r:
                if r.status_code == 404:
                    raise LLMModelNotFoundError(
                        f"Model '{model}' not found. Run: ollama pull {model}"
                    )
                if not r.ok:
                    raise LLMError(f"HTTP {r.status_code}: {r.text[:200]}")
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        chunk = _json.loads(line)
                    except Exception:
                        continue
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        return
        except requests.exceptions.ConnectionError as e:
            raise LLMConnectionError(f"Cannot connect to {self._host}") from e
        except requests.exceptions.Timeout as e:
            raise LLMConnectionError(f"Timeout on {url}") from e

    def ping(self) -> bool:
        try:
            if _is_sdk_available():
                client = self._get_sdk_client()
                client.list()
            else:
                import requests
                r = requests.get(f"{self._host}/api/tags", timeout=5)
                r.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"ping failed: {e}")
            return False

    def available_models_detail(self) -> list[dict[str, Any]]:
        def _fmt_size(raw: Any) -> str:
            try:
                n = int(raw)
            except (TypeError, ValueError):
                return str(raw or "")
            gb = n / (1024 ** 3)
            return f"{gb:.1f}GB" if gb >= 1 else f"{n / (1024 ** 2):.0f}MB"

        try:
            if _is_sdk_available():
                client = self._get_sdk_client()
                result = client.list()
                out: list[dict[str, Any]] = []
                for m in result.get("models", []):
                    name = m.get("name") or m.get("model") or ""
                    if not name:
                        continue
                    size_raw = m.get("size")
                    modified = m.get("modified_at") or m.get("modified") or ""
                    out.append({
                        "name": name,
                        "size": _fmt_size(size_raw),
                        "modified": str(modified),
                        "provider": self.provider,
                    })
                return out
            else:
                import requests
                r = requests.get(f"{self._host}/api/tags", timeout=5)
                r.raise_for_status()
                out = []
                for m in r.json().get("models", []):
                    out.append({
                        "name": m.get("name", ""),
                        "size": _fmt_size(m.get("size")),
                        "modified": str(m.get("modified_at", "")),
                        "provider": self.provider,
                    })
                return out
        except Exception as e:
            logger.warning(f"available_models_detail failed: {e}")
            return []

    # -------------------------------------------------------------------------
    # 내부 호출
    # -------------------------------------------------------------------------
    def _chat_sdk(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any],
    ) -> str:
        import ollama
        client = self._get_sdk_client()
        try:
            response = client.chat(model=model, messages=messages, options=options)
            if isinstance(response, dict):
                return response["message"]["content"]
            return response.message.content
        except ollama.ResponseError as e:
            if "not found" in str(e).lower():
                raise LLMModelNotFoundError(
                    f"Model '{model}' not found. Run: ollama pull {model}"
                ) from e
            raise LLMError(f"Ollama response error: {e}") from e

    def _chat_http(
        self,
        messages: list[dict[str, str]],
        model: str,
        options: dict[str, Any],
    ) -> str:
        import requests

        url = f"{self._host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            raise LLMConnectionError(f"Cannot connect to {self._host}") from e
        except requests.exceptions.Timeout as e:
            raise LLMConnectionError(f"Timeout on {url}") from e

        if r.status_code == 404:
            raise LLMModelNotFoundError(
                f"Model '{model}' not found. Run: ollama pull {model}"
            )
        if not r.ok:
            raise LLMError(f"HTTP {r.status_code}: {r.text[:200]}")

        data = r.json()
        return data.get("message", {}).get("content", "")


# =============================================================================
# 싱글톤 헬퍼 (선택)
# =============================================================================
_default_client: Optional[OllamaClient] = None


def get_default_client() -> OllamaClient:
    """프로세스 전역 기본 OllamaClient (lazy init)."""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client


__all__ = [
    "OllamaClient",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaModelNotFoundError",
    "get_default_client",
]
