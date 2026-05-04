"""
LLM Provider 팩토리.

기능별로 provider를 분리해 라우터/봇 코드가 직접 OllamaClient/GeminiClient를
import하지 않고 팩토리만 호출하도록 한다.

환경 변수
---------
- LLM_PROVIDER_CHAT     (gemini|ollama, 기본: gemini)
- LLM_PROVIDER_REPORT   (gemini|ollama, 기본: gemini)
- LLM_PROVIDER_TOOLS    (gemini|ollama, 기본: gemini)
- GEMINI_MODEL_CHAT     (기본: gemini-2.5-pro)
- GEMINI_MODEL_REPORT   (기본: gemini-2.5-pro)
- GEMINI_MODEL_TOOLS    (기본: gemini-2.5-pro)
- OLLAMA_MODEL_CHAT     (기본: $OLLAMA_MODEL or qwen3.5:9b)
- OLLAMA_MODEL_REPORT   (기본: $OLLAMA_MODEL or gemma4:e4b)

provider:model 접두사 표기
--------------------------
"gemini:gemini-2.5-pro" 또는 "ollama:qwen3.5:9b" 형식 모두 허용.
parse_model_id() 로 분리.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from nlp_mvp.shared.llm.base import LLMClient
from nlp_mvp.shared.logger import get_logger

logger = get_logger("nlp_mvp.shared.llm.factory")


# =============================================================================
# Provider/모델 식별
# =============================================================================
def parse_model_id(model_id: str) -> tuple[str, str]:
    """
    "gemini:gemini-2.5-pro" → ("gemini", "gemini-2.5-pro")
    "ollama:qwen3.5:9b"     → ("ollama", "qwen3.5:9b")
    "qwen3.5:9b"            → ("", "qwen3.5:9b")  (legacy, no provider prefix)
    """
    if not model_id:
        return "", ""
    if model_id.startswith("gemini:"):
        return "gemini", model_id[len("gemini:"):]
    if model_id.startswith("ollama:"):
        return "ollama", model_id[len("ollama:"):]
    return "", model_id


def format_model_id(provider: str, model: str) -> str:
    """provider 접두사 부착. provider 비어있으면 모델만 반환."""
    if not provider:
        return model
    return f"{provider}:{model}"


# =============================================================================
# 기본값 결정
# =============================================================================
def _get_provider(role: str, default: str = "gemini") -> str:
    """role ∈ {chat, report, tools} 에 대한 provider 환경변수 조회."""
    env = f"LLM_PROVIDER_{role.upper()}"
    val = (os.getenv(env, "") or "").strip().lower()
    if val in ("gemini", "ollama"):
        return val
    return default


def _get_model_for_provider(provider: str, role: str) -> Optional[str]:
    """provider/role 조합에 맞는 모델 env를 조회."""
    if provider == "gemini":
        return os.getenv(
            f"GEMINI_MODEL_{role.upper()}",
            os.getenv("GEMINI_MODEL_CHAT", "gemini-2.5-pro"),
        )
    if provider == "ollama":
        return os.getenv(
            f"OLLAMA_MODEL_{role.upper()}",
            os.getenv("OLLAMA_MODEL", "qwen3.5:9b"),
        )
    return None


# =============================================================================
# Public 팩토리
# =============================================================================
def make_client(provider: str, model: Optional[str] = None) -> LLMClient:
    """provider 명시 + (선택) 모델로 클라이언트 생성."""
    provider = (provider or "").strip().lower()
    if provider == "gemini":
        from nlp_mvp.shared.llm.gemini import GeminiClient
        return GeminiClient(model=model)
    if provider == "ollama":
        from nlp_mvp.shared.llm.ollama import OllamaClient
        return OllamaClient(model=model)
    raise ValueError(f"Unknown LLM provider: {provider!r}")


def get_chat_client() -> LLMClient:
    """AI 상담(/nlp/chatbot/chat)용 클라이언트."""
    provider = _get_provider("chat")
    model = _get_model_for_provider(provider, "chat")
    logger.info(f"get_chat_client: provider={provider}, model={model}")
    return make_client(provider, model)


def get_report_client() -> LLMClient:
    """주간 NLG 리포트(/nlp/reports/...)용 클라이언트."""
    provider = _get_provider("report")
    model = _get_model_for_provider(provider, "report")
    logger.info(f"get_report_client: provider={provider}, model={model}")
    return make_client(provider, model)


def get_tools_client() -> LLMClient:
    """Tool calling(/nlp/chatbot/chat/tools)용 클라이언트."""
    provider = _get_provider("tools")
    model = _get_model_for_provider(provider, "tools")
    logger.info(f"get_tools_client: provider={provider}, model={model}")
    return make_client(provider, model)


def get_active_summary() -> dict[str, Any]:
    """현재 활성 provider/model 조합 (UI/디버그용)."""
    return {
        "chat": {
            "provider": _get_provider("chat"),
            "model": _get_model_for_provider(_get_provider("chat"), "chat"),
        },
        "report": {
            "provider": _get_provider("report"),
            "model": _get_model_for_provider(_get_provider("report"), "report"),
        },
        "tools": {
            "provider": _get_provider("tools"),
            "model": _get_model_for_provider(_get_provider("tools"), "tools"),
        },
    }


# =============================================================================
# 통합 모델 목록
# =============================================================================
def list_available_models() -> list[dict[str, Any]]:
    """
    Ollama + Gemini 양쪽 설치/사용 가능 모델을 통합 반환.
    각 항목에 'provider' 키 포함.

    Returns:
        [{"name": "qwen3.5:9b", "provider": "ollama", "size": "...", ...},
         {"name": "gemini-2.5-pro", "provider": "gemini", "size": "", ...}, ...]
    """
    out: list[dict[str, Any]] = []

    # Ollama
    try:
        from nlp_mvp.shared.llm.ollama import OllamaClient
        out.extend(OllamaClient().available_models_detail())
    except Exception as e:
        logger.warning(f"ollama list failed: {e}")

    # Gemini (auth 실패해도 화이트리스트는 반환)
    try:
        from nlp_mvp.shared.llm.gemini import GeminiClient
        out.extend(GeminiClient().available_models_detail())
    except Exception as e:
        logger.warning(f"gemini list failed: {e}")

    return out


__all__ = [
    "parse_model_id",
    "format_model_id",
    "make_client",
    "get_chat_client",
    "get_report_client",
    "get_tools_client",
    "get_active_summary",
    "list_available_models",
]
