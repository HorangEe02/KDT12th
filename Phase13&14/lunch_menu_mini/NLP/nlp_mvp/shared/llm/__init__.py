"""
LLM provider 추상화 패키지.

- base: LLMClient ABC + 공통 예외
- ollama: OllamaClient (기존 코드 이동)
- gemini: GeminiClient (Phase 14 신규)
- factory: provider env 기반 인스턴스 반환
"""
from nlp_mvp.shared.llm.base import (
    LLMClient,
    LLMError,
    LLMConnectionError,
    LLMModelNotFoundError,
)
from nlp_mvp.shared.llm.ollama import OllamaClient
from nlp_mvp.shared.llm.gemini import GeminiClient
from nlp_mvp.shared.llm.factory import (
    get_chat_client,
    get_report_client,
    get_tools_client,
    list_available_models,
)

__all__ = [
    "LLMClient",
    "LLMError",
    "LLMConnectionError",
    "LLMModelNotFoundError",
    "OllamaClient",
    "GeminiClient",
    "get_chat_client",
    "get_report_client",
    "get_tools_client",
    "list_available_models",
]
