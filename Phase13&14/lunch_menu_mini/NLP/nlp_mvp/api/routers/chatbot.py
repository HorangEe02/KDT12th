"""
/nlp/chatbot/* 라우터 — RAG 영양 상담 챗봇.

- POST /nlp/chatbot/chat
- POST /nlp/chatbot/chat/stream     (SSE, M7)
- POST /nlp/chatbot/reset
- GET  /nlp/chatbot/stats           (Insights 대시보드용)
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Iterator, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from nlp_mvp.api.rate_limit import rate_limit
from nlp_mvp.api.schemas import (
    ChatIn,
    ChatOut,
    ChatRecommendation,
    ChatResetIn,
    ChatResetOut,
    ToolCallRecord,
    ToolChatIn,
    ToolChatOut,
    ToolResultRecord,
)
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/nlp/chatbot", tags=["nlp-chatbot"])


# =============================================================================
# meal_type 처리 — 다중 식사 시간 (헤비 옵션)
# =============================================================================
_MEAL_TYPE_PREFIX = {
    "breakfast": "[아침] ",
    "lunch": "[점심] ",
    "dinner": "[저녁] ",
}


def _apply_meal_type(query: str, meal_type: Optional[str]) -> str:
    """meal_type 이 명시되면 query 앞에 한국어 prefix 부착.

    LLM 이 시스템 프롬프트의 "[아침]/[점심]/[저녁] prefix 인식" 규칙을 따라
    적절한 카테고리·톤으로 답변하도록 유도한다. any 또는 None 이면 원본 그대로.
    """
    if not meal_type or meal_type == "any":
        return query
    prefix = _MEAL_TYPE_PREFIX.get(meal_type, "")
    return f"{prefix}{query}" if prefix else query


# =============================================================================
# user_id 별 세션 캐시
# =============================================================================
_SESSIONS: dict[int, tuple[Any, float]] = {}
_SESSIONS_LOCK = threading.Lock()
_SESSION_TTL = 1800  # 30 minutes

# 간단한 통계 축적 (Insights 탭용)
_STATS: dict[str, Any] = {
    "total_calls": 0,
    "total_latency_ms": 0,
    "hallucination_warnings": 0,
    "last_error": None,
}
_STATS_LOCK = threading.Lock()


def _get_bot(user_id: int):
    """LunchCoachBot 싱글톤 (user_id 별, TTL).

    Phase 14: LLM provider/모델은 factory.get_chat_client() 가 결정한다.
    LLM_PROVIDER_CHAT (gemini|ollama) 와 GEMINI_MODEL_CHAT / OLLAMA_MODEL_CHAT
    env 를 읽음. PUT /nlp/settings/model 이 env 를 덮어쓰고 세션 캐시를 clear
    하면 다음 요청에서 새 provider/모델로 재생성된다.
    """
    from nlp_mvp.rag_chatbot.chatbot import LunchCoachBot
    from nlp_mvp.shared.llm.factory import get_chat_client

    now = time.time()
    with _SESSIONS_LOCK:
        cached = _SESSIONS.get(user_id)
        if cached is not None:
            bot, ts = cached
            if now - ts < _SESSION_TTL:
                _SESSIONS[user_id] = (bot, now)  # touch
                return bot

        # GC stale entries
        stale = [k for k, (_, ts) in _SESSIONS.items() if now - ts >= _SESSION_TTL]
        for k in stale:
            _SESSIONS.pop(k, None)

        client = get_chat_client()
        bot = LunchCoachBot(user_id=user_id, llm_client=client)
        _SESSIONS[user_id] = (bot, now)
        return bot


# =============================================================================
# POST /nlp/chatbot/chat
# =============================================================================
@router.post("/chat", response_model=ChatOut)
@rate_limit("10/minute")  # #5 LLM 호출 비용 보호
def chat(request: Request, payload: ChatIn) -> ChatOut:
    try:
        bot = _get_bot(payload.user_id)
    except Exception as e:
        logger.exception("bot init failed")
        raise HTTPException(status_code=503, detail=f"chatbot unavailable: {e}")

    try:
        resp = bot.chat(
            user_query=_apply_meal_type(payload.query, payload.meal_type),
            top_k_meal=payload.top_k_meal,
            top_k_nutrition=payload.top_k_nutrition,
            top_k_restaurant=payload.top_k_restaurant,
        )
    except Exception as e:
        logger.exception(f"chatbot.chat failed: {e}")
        with _STATS_LOCK:
            _STATS["last_error"] = str(e)
        raise HTTPException(status_code=500, detail="chat failed")

    # stats 업데이트
    with _STATS_LOCK:
        _STATS["total_calls"] += 1
        _STATS["total_latency_ms"] += int(resp.latency_ms or 0)
        if (
            resp.validation
            and resp.validation.get("mentioned_count", -1) == 0
            and len(resp.recommendations) > 0
        ):
            _STATS["hallucination_warnings"] += 1

    ctx = resp.context_used or {}
    context_summary = {
        "meal_history": len(ctx.get("meal_history", []) or []),
        "nutrition_info": len(ctx.get("nutrition_info", []) or []),
        "restaurants": len(ctx.get("restaurants", []) or []),
    }

    recs = [
        ChatRecommendation(
            name=str(r.get("name", "")),
            reason=r.get("reason"),
            category=r.get("category"),
        )
        for r in (resp.recommendations or [])
        if r.get("name")
    ]

    return ChatOut(
        response=resp.response,
        recommendations=recs,
        latency_ms=resp.latency_ms,
        validation=resp.validation or {},
        context_summary=context_summary,
    )


# =============================================================================
# POST /nlp/chatbot/reset
# =============================================================================
@router.post("/reset", response_model=ChatResetOut)
def reset(payload: ChatResetIn) -> ChatResetOut:
    with _SESSIONS_LOCK:
        entry = _SESSIONS.pop(payload.user_id, None)
    if entry is not None:
        try:
            entry[0].reset()
        except Exception:
            pass
    return ChatResetOut(user_id=payload.user_id, reset=True)


# =============================================================================
# GET /nlp/chatbot/stats
# =============================================================================
@router.get("/stats")
def stats() -> dict[str, Any]:
    with _STATS_LOCK:
        s = dict(_STATS)
    avg = (s["total_latency_ms"] / s["total_calls"]) if s["total_calls"] else 0.0
    s["avg_latency_ms"] = round(avg, 1)
    s["active_sessions"] = len(_SESSIONS)
    return s


# =============================================================================
# POST /nlp/chatbot/chat/stream — SSE streaming
# =============================================================================
def _sse(event_type: str, data: dict[str, Any]) -> str:
    """Encode a single SSE frame."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_chat(payload: ChatIn) -> Iterator[str]:
    """Generator yielding SSE frames for a streaming chat turn."""
    start = time.time()
    # 다중 식사 시간 — meal_type 명시 시 query 앞에 [아침]/[점심]/[저녁] 부착
    effective_query = _apply_meal_type(payload.query, payload.meal_type)

    # 1. Acquire bot (session-cached)
    try:
        bot = _get_bot(payload.user_id)
    except Exception as e:
        logger.exception("bot init failed")
        yield _sse("error", {"message": f"chatbot unavailable: {e}"})
        yield "data: [DONE]\n\n"
        return

    # 2. Retrieve context
    try:
        context = bot.retriever.retrieve(
            query=effective_query,
            user_id=payload.user_id,
            top_k_meal=payload.top_k_meal,
            top_k_nutrition=payload.top_k_nutrition,
            top_k_restaurant=payload.top_k_restaurant,
        )
    except Exception as e:
        logger.exception(f"retrieve failed: {e}")
        context = {"meal_history": [], "nutrition_info": [], "restaurants": []}

    context_summary = {
        "meal_history": len(context.get("meal_history", []) or []),
        "nutrition_info": len(context.get("nutrition_info", []) or []),
        "restaurants": len(context.get("restaurants", []) or []),
    }
    yield _sse("meta", {"context_summary": context_summary})

    # 3. Build prompt (reuse bot's prompt builder + history)
    from nlp_mvp.rag_chatbot.chatbot import (
        extract_recommendations,
        strip_json_block,
        validate_response,
    )
    from nlp_mvp.rag_chatbot.prompt_templates import build_prompt

    messages = build_prompt(
        user_query=effective_query,
        context=context,
        history=list(bot.history.messages),
    )

    # 4. Stream tokens from Ollama
    full_text = ""
    try:
        for chunk in bot.ollama.chat_stream(
            messages=messages,
            options={"temperature": bot.temperature},
        ):
            full_text += chunk
            yield _sse("token", {"token": chunk})
    except Exception as e:
        logger.exception(f"chat_stream failed: {e}")
        with _STATS_LOCK:
            _STATS["last_error"] = str(e)
        yield _sse("error", {"message": str(e)})
        yield "data: [DONE]\n\n"
        return

    # 5. Parse final response
    recommendations = extract_recommendations(full_text)
    display_text = strip_json_block(full_text)
    validation = validate_response(full_text, context)

    # 6. Update history (display text only, not raw JSON block)
    bot.history.add_user(payload.query)
    bot.history.add_assistant(display_text)

    latency_ms = int((time.time() - start) * 1000)

    # 7. Stats
    with _STATS_LOCK:
        _STATS["total_calls"] += 1
        _STATS["total_latency_ms"] += latency_ms
        if (
            validation
            and validation.get("mentioned_count", -1) == 0
            and len(recommendations) > 0
        ):
            _STATS["hallucination_warnings"] += 1

    # 8. Final meta frame
    yield _sse(
        "final",
        {
            "recommendations": recommendations,
            "validation": validation,
            "latency_ms": latency_ms,
            "display_text": display_text,
        },
    )
    yield "data: [DONE]\n\n"


@router.post("/chat/stream")
@rate_limit("10/minute")  # #5
def chat_stream(request: Request, payload: ChatIn) -> StreamingResponse:
    """
    SSE streaming version of /chat.

    Frames (each `data: { "type": ..., ... }\\n\\n`):
      - type="meta"   · { context_summary }
      - type="token"  · { token } (possibly many)
      - type="final"  · { recommendations, validation, latency_ms, display_text }
      - type="error"  · { message }
      - terminator    · `data: [DONE]\\n\\n`
    """
    return StreamingResponse(
        _stream_chat(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# POST /nlp/chatbot/chat/tools — Phase 7 tool-calling endpoint
# =============================================================================
_TOOL_BOTS: dict[str, Any] = {}
_TOOL_LOCK = threading.Lock()


def _get_tool_bot(user_id: str, temperature: float, max_iterations: int):
    """Lazily instantiate and cache a ToolCallingBot per user_id.

    Phase 14: provider/모델은 factory.get_tools_client() 가 결정.
    LLM_PROVIDER_TOOLS env 로 gemini ↔ ollama 토글.
    """
    import os
    from nlp_mvp.rag_chatbot.tool_bot import ToolCallingBot
    from nlp_mvp.rag_chatbot.tools.executors import ToolExecutor
    from nlp_mvp.shared.llm.factory import get_tools_client

    with _TOOL_LOCK:
        bot = _TOOL_BOTS.get(user_id)
        if bot is None:
            base = os.getenv("LUNCH_API_BASE", "http://localhost:8000/api")
            bot = ToolCallingBot(
                user_id=user_id,
                llm_client=get_tools_client(),
                executor=ToolExecutor(base_url=base),
                max_iterations=max_iterations,
                temperature=temperature,
            )
            _TOOL_BOTS[user_id] = bot
        else:
            bot.temperature = temperature
            bot.max_iterations = max_iterations
        return bot


@router.post("/chat/tools", response_model=ToolChatOut)
@rate_limit("10/minute")  # #5
def chat_with_tools(request: Request, payload: ToolChatIn) -> ToolChatOut:
    """
    RAG chatbot with Phase 7 Tool Calling.

    The bot may call any of the 8 tool functions (see
    `nlp_mvp.rag_chatbot.tools.definitions.TOOL_DEFINITIONS`) during a single
    turn and returns the final natural-language answer plus the full call
    trace for debugging / UI display.
    """
    try:
        bot = _get_tool_bot(
            str(payload.user_id),
            temperature=payload.temperature,
            max_iterations=payload.max_iterations,
        )
    except Exception as e:
        logger.exception("tool bot init failed")
        raise HTTPException(status_code=503, detail=f"tool bot unavailable: {e}")

    try:
        resp = bot.chat(_apply_meal_type(payload.query, payload.meal_type))
    except Exception as e:
        logger.exception(f"tool chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"tool chat failed: {e}")

    # Stats update (reuse the classic /chat counter)
    with _STATS_LOCK:
        _STATS["total_calls"] += 1
        _STATS["total_latency_ms"] += int(resp.latency_ms or 0)

    return ToolChatOut(
        response=resp.response,
        tool_calls=[
            ToolCallRecord(name=c["name"], args=c.get("args") or {})
            for c in resp.tool_calls
        ],
        tool_results=[
            ToolResultRecord(
                ok=bool(r.get("ok")),
                tool=str(r.get("tool", "?")),
                data=r.get("data"),
                error=r.get("error"),
            )
            for r in resp.tool_results
        ],
        iterations=resp.iterations,
        latency_ms=resp.latency_ms,
        fallback_used=resp.fallback_used,
    )


@router.get("/tools")
def list_tools() -> dict[str, Any]:
    """Expose the 8 tool schemas so the frontend can render a help panel."""
    from nlp_mvp.rag_chatbot.tools.definitions import TOOL_DEFINITIONS
    return {"tools": TOOL_DEFINITIONS, "count": len(TOOL_DEFINITIONS)}
