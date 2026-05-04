"""
/nlp/models · /nlp/settings · /nlp/settings/model 라우터.

Phase 14: Multi-provider (ollama + gemini) 지원.

- GET  /nlp/models          모든 provider의 모델 목록 + 활성 chat/report/tools
- GET  /nlp/settings        현재 chat/report/tools (provider+model) + 언어
- PUT  /nlp/settings/model  { model, role, provider } 활성 모델 변경

모델 식별
---------
응답의 model name은 "provider:model" 접두사 표기 사용 (예: "gemini:gemini-2.5-pro").
요청의 model 필드는 "provider:model" 또는 "model"(이전 호환) 둘 다 허용.

본 엔드포인트는 **프로세스 로컬**이다. uvicorn 재시작 시 .env 기본값으로 되돌아간다.
"""
from __future__ import annotations

import hmac
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from nlp_mvp.api.schemas import (
    ModelListOut,
    OllamaModelOut,
    SettingsOut,
    SettingsUpdateIn,
    SettingsUpdateOut,
)
from nlp_mvp.shared.llm.factory import (
    format_model_id,
    get_active_summary,
    list_available_models,
    parse_model_id,
)
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp", tags=["nlp-settings"])


# =============================================================================
# Admin auth
# =============================================================================
def _get_admin_token() -> str:
    return os.getenv("NLP_ADMIN_TOKEN", "").strip()


def require_admin(x_admin_token: Optional[str] = Header(default=None)) -> None:
    """X-Admin-Token 검증. NLP_DEV_MODE=1 이면 스킵."""
    if os.getenv("NLP_DEV_MODE", "0") == "1":
        logger.debug("NLP_DEV_MODE=1 — admin token check skipped")
        return

    expected = _get_admin_token()
    if not expected:
        logger.warning("admin endpoint called but NLP_ADMIN_TOKEN is not set")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token not configured (set NLP_ADMIN_TOKEN or NLP_DEV_MODE=1)",
        )
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Token",
        )


# =============================================================================
# Whitelist (Phase 14: Ollama + Gemini)
# =============================================================================
_DEFAULT_MODEL_WHITELIST = frozenset({
    # Ollama
    "ollama:qwen3.5:4b",
    "ollama:qwen3.5:9b",
    "ollama:qwen3.5:latest",
    "ollama:qwen2.5:7b-instruct",
    "ollama:gemma4:e2b",
    "ollama:gemma4:e4b",
    "ollama:gemma4:latest",
    "ollama:gemma4:26b",
    "ollama:exaone3.5:latest",
    "ollama:exaone-deep:latest",
    "ollama:nemotron-cascade-2:latest",
    "ollama:gpt-oss:20b",
    # Gemini
    "gemini:gemini-2.5-pro",
    "gemini:gemini-2.5-flash",
    # Backward-compat: bare names without provider prefix (assumed ollama)
    "qwen3.5:4b",
    "qwen3.5:9b",
    "qwen3.5:latest",
    "qwen2.5:7b-instruct",
    "gemma4:e2b",
    "gemma4:e4b",
    "gemma4:latest",
    "gemma4:26b",
    "exaone3.5:latest",
    "exaone-deep:latest",
    "nemotron-cascade-2:latest",
    "gpt-oss:20b",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
})


def get_model_whitelist() -> frozenset[str]:
    raw = os.getenv("NLP_MODEL_WHITELIST", "").strip()
    if not raw:
        return _DEFAULT_MODEL_WHITELIST
    return frozenset(m.strip() for m in raw.split(",") if m.strip())


# =============================================================================
# Env helpers
# =============================================================================
def get_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://localhost:11434")


def _resolve_provider_for_role(role: str) -> str:
    """role ∈ {chat, report, tools} → provider env."""
    env = f"LLM_PROVIDER_{role.upper()}"
    val = (os.getenv(env, "") or "").strip().lower()
    if val in ("gemini", "ollama"):
        return val
    return "gemini"  # default Phase 14


def _resolve_model_for_role(role: str) -> str:
    """role 별 활성 모델 (provider:model 접두사 포함)."""
    provider = _resolve_provider_for_role(role)
    if provider == "gemini":
        model = os.getenv(
            f"GEMINI_MODEL_{role.upper()}",
            os.getenv("GEMINI_MODEL_CHAT", "gemini-2.5-pro"),
        )
    else:
        model = os.getenv(
            f"OLLAMA_MODEL_{role.upper()}",
            os.getenv("OLLAMA_MODEL", "qwen3.5:9b"),
        )
    return format_model_id(provider, model)


def get_chat_model() -> str:
    return _resolve_model_for_role("chat")


def get_report_model() -> str:
    return _resolve_model_for_role("report")


def get_tools_model() -> str:
    return _resolve_model_for_role("tools")


# =============================================================================
# Cache invalidation
# =============================================================================
def _invalidate_caches(role: str) -> None:
    """관련 싱글톤 drop. 다음 요청에서 새 env로 재생성."""
    roles = {role}
    if role == "both":
        roles = {"chat", "report"}
    elif role == "all":
        roles = {"chat", "report", "tools"}

    if {"chat", "tools"} & roles:
        try:
            from nlp_mvp.api.routers import chatbot as chatbot_router
            with chatbot_router._SESSIONS_LOCK:  # type: ignore[attr-defined]
                chatbot_router._SESSIONS.clear()  # type: ignore[attr-defined]
            with chatbot_router._TOOL_LOCK:  # type: ignore[attr-defined]
                chatbot_router._TOOL_BOTS.clear()  # type: ignore[attr-defined]
            logger.info("chatbot/tool sessions cleared")
        except Exception as e:
            logger.warning(f"chatbot cache clear failed: {e}")

    if "report" in roles:
        try:
            from nlp_mvp.api.routers import reports as reports_router
            reports_router.set_generator(None)
            logger.info("reports generator cleared")
        except Exception as e:
            logger.warning(f"reports cache clear failed: {e}")


# =============================================================================
# GET /nlp/models
# =============================================================================
@router.get("/models", response_model=ModelListOut)
def list_models() -> ModelListOut:
    """모든 provider의 사용 가능 모델 + 활성 chat/report/tools."""
    raw = list_available_models()

    models = [
        OllamaModelOut(
            name=format_model_id(m.get("provider", "ollama"), m.get("name", "")),
            size=m.get("size", ""),
            modified=m.get("modified", ""),
            provider=m.get("provider", "ollama"),  # type: ignore[arg-type]
        )
        for m in raw
        if m.get("name")
    ]

    summary = get_active_summary()
    return ModelListOut(
        models=models,
        host=get_host(),
        active_chat=get_chat_model(),
        active_report=get_report_model(),
        active_tools=get_tools_model(),
        active_chat_provider=summary["chat"]["provider"],  # type: ignore[arg-type]
        active_report_provider=summary["report"]["provider"],  # type: ignore[arg-type]
        active_tools_provider=summary["tools"]["provider"],  # type: ignore[arg-type]
    )


# =============================================================================
# GET /nlp/settings
# =============================================================================
@router.get("/settings", response_model=SettingsOut)
def get_settings() -> SettingsOut:
    lang = os.getenv("NLP_LANGUAGE_PREF", "both")
    if lang not in ("en", "ko", "both"):
        lang = "both"
    summary = get_active_summary()
    return SettingsOut(
        chat_model=get_chat_model(),
        report_model=get_report_model(),
        tools_model=get_tools_model(),
        host=get_host(),
        language=lang,  # type: ignore[arg-type]
        chat_provider=summary["chat"]["provider"],  # type: ignore[arg-type]
        report_provider=summary["report"]["provider"],  # type: ignore[arg-type]
        tools_provider=summary["tools"]["provider"],  # type: ignore[arg-type]
    )


# =============================================================================
# PUT /nlp/settings/model
# =============================================================================
@router.put(
    "/settings/model",
    response_model=SettingsUpdateOut,
    dependencies=[Depends(require_admin)],
)
def update_model(payload: SettingsUpdateIn) -> SettingsUpdateOut:
    """
    활성 provider/모델 변경.

    payload.model 형식:
      - "gemini:gemini-2.5-pro"  ← 권장 (provider 명시)
      - "qwen3.5:9b"             ← 이전 호환 (provider 미지정 → ollama 가정 또는 payload.provider 사용)
    payload.role: chat | report | tools | both(=chat+report) | all(=chat+report+tools)
    """
    # 1) Whitelist check
    whitelist = get_model_whitelist()
    if payload.model not in whitelist:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Model '{payload.model}' is not in the allowed whitelist. "
                f"Allowed: {sorted(whitelist)[:20]}..."
            ),
        )

    # 2) Provider 결정
    parsed_provider, model_name = parse_model_id(payload.model)
    provider = (payload.provider or parsed_provider or "ollama").lower()
    if provider not in ("ollama", "gemini"):
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

    # 3) (옵션) 실제 사용 가능성 검증 — Ollama는 설치 여부, Gemini는 화이트리스트만
    if provider == "ollama":
        try:
            from nlp_mvp.shared.llm.ollama import OllamaClient
            installed = {m["name"] for m in OllamaClient().available_models_detail()}
        except Exception as e:
            logger.warning(f"availability check failed: {e}")
            installed = set()
        if installed and model_name not in installed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Ollama model '{model_name}' not installed. "
                    f"Available: {sorted(installed)[:10]}"
                ),
            )

    # 4) Apply env overrides — provider + model 둘 다
    roles_to_set = []
    if payload.role in ("chat", "both", "all"):
        roles_to_set.append("chat")
    if payload.role in ("report", "both", "all"):
        roles_to_set.append("report")
    if payload.role in ("tools", "all"):
        roles_to_set.append("tools")

    try:
        for r in roles_to_set:
            os.environ[f"LLM_PROVIDER_{r.upper()}"] = provider
            if provider == "gemini":
                os.environ[f"GEMINI_MODEL_{r.upper()}"] = model_name
            else:
                os.environ[f"OLLAMA_MODEL_{r.upper()}"] = model_name
    except Exception as e:
        return SettingsUpdateOut(
            status="error",
            role=payload.role,
            model=payload.model,
            chat_model=get_chat_model(),
            report_model=get_report_model(),
            tools_model=get_tools_model(),
            detail=str(e),
        )

    _invalidate_caches(payload.role)

    summary = get_active_summary()
    logger.info(
        f"Model updated: role={payload.role}, provider={provider}, "
        f"model={model_name}, chat={get_chat_model()}, "
        f"report={get_report_model()}, tools={get_tools_model()}"
    )

    return SettingsUpdateOut(
        status="ok",
        role=payload.role,
        model=payload.model,
        chat_model=get_chat_model(),
        report_model=get_report_model(),
        tools_model=get_tools_model(),
        chat_provider=summary["chat"]["provider"],  # type: ignore[arg-type]
        report_provider=summary["report"]["provider"],  # type: ignore[arg-type]
        tools_provider=summary["tools"]["provider"],  # type: ignore[arg-type]
    )
