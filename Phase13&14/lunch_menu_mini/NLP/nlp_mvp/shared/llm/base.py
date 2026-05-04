"""
LLMClient ABC + 공통 예외.

OllamaClient / GeminiClient 양쪽이 이 인터페이스를 구현한다.
라우터/봇은 항상 LLMClient만 보고 동작하므로 provider 교체에 무영향.

설계 의도
---------
- 기존 OllamaClient의 메서드 시그니처를 그대로 일반화 (호환성 100%)
- "messages"는 OpenAI 스타일 (role / content). 각 구현체가 내부 변환 책임
- 옵션(temperature 등)은 dict로 받아 provider별 키로 매핑
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional


# =============================================================================
# 예외
# =============================================================================
class LLMError(RuntimeError):
    """LLM 호출 실패의 루트 예외."""


class LLMConnectionError(LLMError):
    """연결 실패 (서버 미가동·타임아웃·네트워크)."""


class LLMModelNotFoundError(LLMError):
    """요청한 모델이 없음."""


class LLMAuthError(LLMError):
    """인증 실패 (API key 누락/잘못됨)."""


# =============================================================================
# Tool calling 데이터 클래스
# =============================================================================
class ToolCall:
    """단일 tool 호출 (provider-agnostic)."""

    __slots__ = ("name", "args")

    def __init__(self, name: str, args: dict[str, Any]):
        self.name = name
        self.args = args

    def __repr__(self) -> str:
        return f"ToolCall(name={self.name!r}, args={self.args!r})"


class ToolCallResult:
    """tool 호출 결과 (chat_with_tools 의 한 turn)."""

    __slots__ = ("text", "tool_calls", "raw")

    def __init__(
        self,
        text: str,
        tool_calls: list[ToolCall],
        raw: Optional[dict[str, Any]] = None,
    ):
        self.text = text
        self.tool_calls = tool_calls
        self.raw = raw

    def __repr__(self) -> str:
        return (
            f"ToolCallResult(text={self.text[:50]!r}..., "
            f"tool_calls={len(self.tool_calls)})"
        )


# =============================================================================
# LLMClient ABC
# =============================================================================
class LLMClient(ABC):
    """
    공통 LLM 클라이언트 인터페이스.

    구현체는 chat/chat_stream/ping/available_models_detail은 필수,
    chat_with_tools는 선택 (function calling 미지원 provider는 NotImplementedError).
    """

    #: provider 식별자 (e.g. "ollama", "gemini")
    provider: str = "abstract"

    @property
    @abstractmethod
    def model(self) -> str:
        """기본 사용 모델 이름 (provider 접두어 없는 raw name)."""

    @property
    @abstractmethod
    def host(self) -> str:
        """provider host/endpoint 식별자 (대시보드 표시용)."""

    # -------------------------------------------------------------------------
    # 핵심 호출
    # -------------------------------------------------------------------------
    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Non-streaming chat completion.

        Args:
            messages: OpenAI 스타일. role ∈ {"system","user","assistant"}
            model:    이 호출에만 사용할 모델 (기본: self.model)
            options:  {"temperature": 0.3, "max_tokens": 1024, ...}

        Returns:
            전체 응답 텍스트.

        Raises:
            LLMConnectionError, LLMModelNotFoundError, LLMError
        """

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> Iterator[str]:
        """Streaming version of chat — yields text chunks."""

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> str:
        """Single-prompt convenience wrapper."""
        return self.chat(
            [{"role": "user", "content": prompt}],
            model=model,
            options=options,
        )

    # -------------------------------------------------------------------------
    # Tool / function calling (optional)
    # -------------------------------------------------------------------------
    def chat_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        model: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> ToolCallResult:
        """
        Function calling 한 턴.

        Args:
            tools: OpenAI/Anthropic 스타일 tool definitions.
                   [{"name": "...", "description": "...",
                     "parameters": {"type":"object","properties":...}}]
        Returns:
            ToolCallResult — provider가 호출한 tool들 + (있다면) 텍스트.

        구현 안 한 provider는 NotImplementedError.
        """
        raise NotImplementedError(
            f"{self.provider} client does not support tool calling"
        )

    # -------------------------------------------------------------------------
    # 메타 정보
    # -------------------------------------------------------------------------
    @abstractmethod
    def ping(self) -> bool:
        """provider 도달 가능성 확인 (가벼운 호출)."""

    def available_models(self) -> list[str]:
        """이름만 반환."""
        return [m["name"] for m in self.available_models_detail() if m.get("name")]

    @abstractmethod
    def available_models_detail(self) -> list[dict[str, Any]]:
        """
        [{"name": "...", "size": "...", "modified": "...", "provider": "..."}]
        Provider 키 자동 채움 (구현체에서 self.provider 사용).
        """
