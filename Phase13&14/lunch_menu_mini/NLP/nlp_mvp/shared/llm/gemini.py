"""
GeminiClient — LLMClient 구현체 (provider="gemini").

Google Generative AI (gemini-2.5-pro / -flash) 호출 래퍼.

설계 원칙
---------
- 공식 `google-generativeai` SDK 사용
- 메시지 변환: OpenAI 스타일(messages) → Gemini 스타일(contents + system_instruction)
- 옵션 변환: temperature/max_tokens/top_p/top_k → GenerationConfig
- 스트리밍 지원 (generate_content(stream=True))
- Function Calling 지원 (Tool / FunctionDeclaration)
- 타임아웃 + 재시도

환경 변수
---------
- GEMINI_API_KEY      (필수)
- GEMINI_MODEL_CHAT   (기본 모델, 미설정 시 gemini-2.5-pro)
- GEMINI_HOST_LABEL   (대시보드 표시용, 기본 "google-generativeai")
"""
from __future__ import annotations

import os
import time
from typing import Any, Iterator, Optional

from dotenv import load_dotenv

from nlp_mvp.shared.llm.base import (
    LLMAuthError,
    LLMClient,
    LLMConnectionError,
    LLMError,
    LLMModelNotFoundError,
    ToolCall,
    ToolCallResult,
)
from nlp_mvp.shared.logger import get_logger

load_dotenv()

logger = get_logger("nlp_mvp.shared.llm.gemini")

# =============================================================================
# 기본값
# =============================================================================
DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF = 1.5
DEFAULT_HOST_LABEL = "google-generativeai"

# 화이트리스트 (UI / settings 검증용)
KNOWN_MODELS = (
    "gemini-2.5-pro",
    "gemini-2.5-flash",
)


# =============================================================================
# SDK lazy import
# =============================================================================
_GENAI = None


def _genai():
    """google.generativeai 모듈 lazy import + 1회 configure."""
    global _GENAI
    if _GENAI is None:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as e:
            raise LLMError(
                "google-generativeai not installed. "
                "Add `google-generativeai>=0.8.0` to requirements.txt"
            ) from e
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key.startswith("YOUR_"):
            raise LLMAuthError(
                "GEMINI_API_KEY not set. Get one at "
                "https://aistudio.google.com/app/apikey "
                "and add to .env"
            )
        genai.configure(api_key=api_key)
        _GENAI = genai
    return _GENAI


# =============================================================================
# 메시지/옵션 변환 유틸
# =============================================================================
def _split_system(messages: list[dict[str, str]]) -> tuple[Optional[str], list[dict[str, str]]]:
    """OpenAI messages를 (system_text, rest)로 분리.

    Gemini는 system을 별도 필드(system_instruction)로 받기 때문.
    여러 system 메시지가 있으면 줄바꿈으로 합친다.
    """
    sys_parts: list[str] = []
    rest: list[dict[str, str]] = []
    for m in messages:
        if m.get("role") == "system":
            content = m.get("content")
            if content:
                sys_parts.append(str(content))
        else:
            rest.append(m)
    system_text = "\n\n".join(sys_parts) if sys_parts else None
    return system_text, rest


def _to_contents(messages: list[dict[str, str]]) -> list[dict[str, Any]]:
    """OpenAI messages → Gemini contents.

    role 매핑:
      user      → user
      assistant → model
      tool      → user (function response, 단순 텍스트 변환)
    """
    contents: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        if role == "assistant":
            role = "model"
        elif role not in ("user", "model"):
            role = "user"
        text = m.get("content", "") or ""
        contents.append({"role": role, "parts": [{"text": str(text)}]})
    return contents


def _to_generation_config(options: Optional[dict[str, Any]]) -> dict[str, Any]:
    """OpenAI 스타일 옵션 → Gemini GenerationConfig."""
    options = options or {}
    cfg: dict[str, Any] = {}
    if "temperature" in options:
        cfg["temperature"] = float(options["temperature"])
    if "top_p" in options:
        cfg["top_p"] = float(options["top_p"])
    if "top_k" in options:
        cfg["top_k"] = int(options["top_k"])
    if "max_tokens" in options:
        cfg["max_output_tokens"] = int(options["max_tokens"])
    elif "num_predict" in options:  # Ollama 호환
        cfg["max_output_tokens"] = int(options["num_predict"])
    if "stop" in options:
        cfg["stop_sequences"] = list(options["stop"])
    return cfg


# =============================================================================
# GeminiClient
# =============================================================================
class GeminiClient(LLMClient):
    """Google Gemini API 호출 래퍼."""

    provider = "gemini"

    def __init__(
        self,
        model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
        host_label: Optional[str] = None,
    ):
        self._model = model or os.getenv("GEMINI_MODEL_CHAT", DEFAULT_MODEL)
        self._host = host_label or os.getenv("GEMINI_HOST_LABEL", DEFAULT_HOST_LABEL)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        logger.info(f"GeminiClient initialized: model={self._model}")

    @property
    def model(self) -> str:
        return self._model

    @property
    def host(self) -> str:
        return self._host

    # -------------------------------------------------------------------------
    # 핵심 호출
    # -------------------------------------------------------------------------
    def _build_model(
        self,
        model_name: str,
        system_text: Optional[str],
        tools: Optional[list[Any]] = None,
    ):
        genai = _genai()
        kwargs: dict[str, Any] = {}
        if system_text:
            kwargs["system_instruction"] = system_text
        if tools:
            kwargs["tools"] = tools
        return genai.GenerativeModel(model_name=model_name, **kwargs)

    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> str:
        model_name = model or self._model
        system_text, rest = _split_system(messages)
        contents = _to_contents(rest)
        gen_config = _to_generation_config(options)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                start = time.time()
                gm = self._build_model(model_name, system_text)
                response = gm.generate_content(
                    contents,
                    generation_config=gen_config or None,
                    request_options={"timeout": self.timeout},
                )
                text = self._extract_text(response)
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
                self._classify_and_maybe_raise(e, model_name)
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
            f"Gemini chat failed after {self.max_retries + 1} attempts: {last_error}"
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> Iterator[str]:
        model_name = model or self._model
        system_text, rest = _split_system(messages)
        contents = _to_contents(rest)
        gen_config = _to_generation_config(options)

        start = time.time()
        try:
            gm = self._build_model(model_name, system_text)
            stream = gm.generate_content(
                contents,
                generation_config=gen_config or None,
                stream=True,
                request_options={"timeout": self.timeout},
            )
            for chunk in stream:
                text = self._extract_text(chunk)
                if text:
                    yield text
        except Exception as e:
            self._classify_and_maybe_raise(e, model_name)
            raise LLMError(f"Gemini stream error: {e}") from e
        finally:
            elapsed = time.time() - start
            logger.info(f"chat_stream() done (latency={elapsed:.2f}s)")

    # -------------------------------------------------------------------------
    # Tool / function calling
    # -------------------------------------------------------------------------
    def chat_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> ToolCallResult:
        """
        Gemini Function Calling 한 턴.

        tools 형식 (OpenAI/Anthropic 호환):
          [{"name": "...", "description": "...",
            "parameters": {"type": "object", "properties": {...}, "required": [...]}}]
        """
        model_name = model or self._model
        system_text, rest = _split_system(messages)
        contents = _to_contents(rest)
        gen_config = _to_generation_config(options)

        gemini_tools = self._convert_tools(tools)

        try:
            gm = self._build_model(model_name, system_text, tools=gemini_tools)
            response = gm.generate_content(
                contents,
                generation_config=gen_config or None,
                request_options={"timeout": self.timeout},
            )
        except Exception as e:
            self._classify_and_maybe_raise(e, model_name)
            raise LLMError(f"Gemini tool call failed: {e}") from e

        # 응답에서 function_call들과 텍스트 추출
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        try:
            for cand in getattr(response, "candidates", []) or []:
                content = getattr(cand, "content", None)
                if content is None:
                    continue
                for part in getattr(content, "parts", []) or []:
                    fc = getattr(part, "function_call", None)
                    if fc is not None and getattr(fc, "name", ""):
                        # args is a proto Struct → coerce to dict
                        args = dict(fc.args) if fc.args else {}
                        tool_calls.append(ToolCall(name=fc.name, args=args))
                    else:
                        t = getattr(part, "text", None)
                        if t:
                            text_parts.append(t)
        except Exception as e:
            logger.warning(f"failed to parse Gemini tool response: {e}")

        return ToolCallResult(
            text="".join(text_parts).strip(),
            tool_calls=tool_calls,
            raw=None,
        )

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[Any]:
        """OpenAI 스타일 tool 정의 → Gemini Tool/FunctionDeclaration."""
        genai = _genai()
        from google.generativeai.types import (  # type: ignore
            FunctionDeclaration,
            Tool,
        )
        decls = []
        for t in tools:
            name = t.get("name") or ""
            if not name:
                continue
            desc = t.get("description") or ""
            params = t.get("parameters") or {"type": "object", "properties": {}}
            decls.append(
                FunctionDeclaration(
                    name=name,
                    description=desc,
                    parameters=params,
                )
            )
        return [Tool(function_declarations=decls)] if decls else []

    # -------------------------------------------------------------------------
    # 메타
    # -------------------------------------------------------------------------
    def ping(self) -> bool:
        try:
            genai = _genai()
            # 가벼운 호출 — 모델 목록 1개만
            _ = next(iter(genai.list_models()), None)
            return True
        except Exception as e:
            logger.warning(f"ping failed: {e}")
            return False

    def available_models_detail(self) -> list[dict[str, Any]]:
        """
        Gemini는 정적 화이트리스트 + (가능하면) live list_models() 결과 합집합.

        Returns:
            [{"name": "gemini-2.5-pro", "size": "", "modified": "",
              "provider": "gemini"}, ...]
        """
        names: set[str] = set(KNOWN_MODELS)
        try:
            genai = _genai()
            for m in genai.list_models():
                # generateContent 지원하는 모델만
                methods = getattr(m, "supported_generation_methods", []) or []
                if "generateContent" not in methods:
                    continue
                raw_name = getattr(m, "name", "")
                # "models/gemini-2.5-pro" → "gemini-2.5-pro"
                short = raw_name.split("/")[-1] if raw_name else ""
                if short.startswith("gemini-"):
                    names.add(short)
        except LLMAuthError:
            # API key 없을 때는 화이트리스트만 반환 (UI 표시용)
            pass
        except Exception as e:
            logger.warning(f"available_models_detail (live fetch) failed: {e}")

        return [
            {"name": n, "size": "", "modified": "", "provider": self.provider}
            for n in sorted(names)
        ]

    # -------------------------------------------------------------------------
    # 내부 helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _extract_text(response: Any) -> str:
        """Gemini response → text. 다양한 형태에 대응."""
        # 1) response.text 가 직접 있는 경우 (가장 일반)
        try:
            t = getattr(response, "text", None)
            if t:
                return str(t)
        except Exception:
            pass
        # 2) candidates[].content.parts[].text 직접 순회
        out: list[str] = []
        try:
            for cand in getattr(response, "candidates", []) or []:
                content = getattr(cand, "content", None)
                if content is None:
                    continue
                for part in getattr(content, "parts", []) or []:
                    t = getattr(part, "text", None)
                    if t:
                        out.append(t)
        except Exception:
            pass
        return "".join(out)

    @staticmethod
    def _classify_and_maybe_raise(e: Exception, model_name: str) -> None:
        """Gemini SDK 예외를 LLM* 계열로 변환 (raise는 호출자가)."""
        msg = str(e).lower()
        if "api key" in msg or "permission" in msg or "401" in msg or "403" in msg:
            raise LLMAuthError(f"Gemini auth failed: {e}") from e
        if "not found" in msg or "404" in msg:
            raise LLMModelNotFoundError(
                f"Gemini model '{model_name}' not found"
            ) from e
        if "timeout" in msg or "deadline" in msg:
            raise LLMConnectionError(f"Gemini timeout: {e}") from e


__all__ = ["GeminiClient", "KNOWN_MODELS", "DEFAULT_MODEL"]
