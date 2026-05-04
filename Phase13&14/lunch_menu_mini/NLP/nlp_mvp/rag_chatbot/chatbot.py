"""
LunchCoachBot — RAG + Ollama 대화 엔진.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp_mvp.rag_chatbot.history import ConversationHistory
from nlp_mvp.rag_chatbot.prompt_templates import build_prompt
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 응답 데이터 클래스
# =============================================================================
@dataclass
class ChatResponse:
    response: str
    recommendations: list[dict[str, str]] = field(default_factory=list)
    context_used: dict = field(default_factory=dict)
    latency_ms: int = 0
    validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "recommendations": self.recommendations,
            "context_used": self.context_used,
            "latency_ms": self.latency_ms,
            "validation": self.validation,
        }


# =============================================================================
# 응답 파싱 유틸 — 순수 함수
# =============================================================================
_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def extract_recommendations(response: str) -> list[dict[str, str]]:
    """LLM 응답에서 JSON 블록을 찾아 recommendations 추출. 실패 시 빈 리스트."""
    if not response:
        return []
    match = _JSON_BLOCK_RE.search(response)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
        recs = data.get("recommendations", [])
        if isinstance(recs, list):
            return [r for r in recs if isinstance(r, dict)]
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e}")
    return []


def strip_json_block(response: str) -> str:
    """응답 본문에서 JSON 블록 제거 (UI 표시용)."""
    if not response:
        return ""
    return _JSON_BLOCK_RE.sub("", response).strip()


def validate_response(
    response: str,
    context: dict[str, list[dict]],
) -> dict[str, Any]:
    """
    환각 검증: 응답에 언급된 식당명이 context["restaurants"] 에 존재하는가?
    """
    allowed = {
        r.get("metadata", {}).get("name", "")
        for r in (context.get("restaurants", []) if context else [])
        if r.get("metadata")
    }
    allowed.discard("")

    mentioned = set()
    if response:
        for name in allowed:
            if name and name in response:
                mentioned.add(name)

    return {
        "hallucination_detected": False,  # 엄격 검증은 시나리오 2 에서
        "allowed_count": len(allowed),
        "mentioned_count": len(mentioned),
        "mentioned": sorted(mentioned),
    }


# =============================================================================
# 메인 챗봇 클래스
# =============================================================================
class LunchCoachBot:
    """RAG + Ollama 기반 영양 상담 챗봇."""

    def __init__(
        self,
        user_id: int,
        ollama_client=None,
        retriever=None,
        max_turns: int = 5,
        temperature: float = 0.3,
        llm_client=None,
    ):
        self.user_id = user_id

        # Phase 14: 어떤 LLMClient든 받음. 'ollama_client'는 backward-compat 별칭.
        client = llm_client or ollama_client
        if client is None:
            from nlp_mvp.shared.llm.factory import get_chat_client
            client = get_chat_client()
        # 'self.ollama' 이름은 기존 코드 호환 위해 유지 (실제 타입은 LLMClient).
        self.ollama = client
        self.llm = client

        if retriever is None:
            from nlp_mvp.rag_chatbot.retriever import Retriever
            retriever = Retriever()
        self.retriever = retriever

        self.history = ConversationHistory(max_turns=max_turns)
        self.temperature = temperature
        logger.info(f"LunchCoachBot initialized: user_id={user_id}")

    def chat(
        self,
        user_query: str,
        top_k_meal: int = 5,
        top_k_nutrition: int = 5,
        top_k_restaurant: int = 5,
    ) -> ChatResponse:
        """동기 대화 호출."""
        start = time.time()

        # 1. 컨텍스트 검색
        try:
            context = self.retriever.retrieve(
                query=user_query,
                user_id=self.user_id,
                top_k_meal=top_k_meal,
                top_k_nutrition=top_k_nutrition,
                top_k_restaurant=top_k_restaurant,
            )
        except Exception as e:
            logger.exception(f"retrieve failed: {e}")
            context = {"meal_history": [], "nutrition_info": [], "restaurants": []}

        # 2. 프롬프트 빌드 (이력 포함)
        messages = build_prompt(
            user_query=user_query,
            context=context,
            history=list(self.history.messages),
        )

        # 3. LLM 호출
        try:
            raw_response = self.ollama.chat(
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": 512,   # #perf 응답 길이 상한 (thinking 폭주 방지)
                    "num_ctx": 2048,      # #perf 컨텍스트 크기 축소
                },
            )
        except Exception as e:
            logger.exception(f"Ollama chat failed: {e}")
            return ChatResponse(
                response=f"죄송합니다. 일시적인 오류가 발생했어요. ({e})",
                context_used=context,
                latency_ms=int((time.time() - start) * 1000),
            )

        # 4. 파싱
        recommendations = extract_recommendations(raw_response)
        display_text = strip_json_block(raw_response)

        # 5. 환각 검증
        validation = validate_response(raw_response, context)

        # 6. 이력 업데이트
        self.history.add_user(user_query)
        self.history.add_assistant(display_text)

        latency_ms = int((time.time() - start) * 1000)
        logger.info(
            f"chat() done: user={self.user_id}, latency={latency_ms}ms, "
            f"recs={len(recommendations)}"
        )

        return ChatResponse(
            response=display_text,
            recommendations=recommendations,
            context_used=context,
            latency_ms=latency_ms,
            validation=validation,
        )

    def reset(self) -> None:
        """대화 이력 초기화."""
        self.history.clear()
