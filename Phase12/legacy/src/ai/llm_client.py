"""LLM 고수준 래퍼 — chat_complete() 단일 계약 + 3단계 Fallback.

선택 순서:
  1차  로컬 Ollama (OLLAMA_CHAT_MODEL / OLLAMA_TOOL_MODEL)
  2차  Gemini API (배포 환경·Ollama 미가용 시 자동 전환)
  3차  규칙 기반 응답 (완전 오프라인 안전망)

Cloud Run 환경(IS_CLOUD_RUN=True)에선 Ollama를 건너뛰고 Gemini부터 시도.
"""
from __future__ import annotations

import logging

import httpx

from src import config
from src.ai import gemini_client, ollama_client

log = logging.getLogger(__name__)


def _fallback_response(messages: list[dict]) -> dict:
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = str(m.get("content", "")).lower()
            break

    canned = {
        ("안녕", "hello", "hi"):
            "안녕하세요! 원정 응원 플래너입니다. 현재 AI 서비스 연결에 문제가 있어 간단히 안내드려요. "
            "좌측 사이드바에서 팀·기간을 선택하시고, 탭 1(경기), 탭 2(지도), 탭 3(맛집)을 차례로 살펴보시면 됩니다.",
        ("추천", "recommend", "맛집"):
            "AI 서비스가 일시적으로 응답하지 않습니다. 탭 3 '맛집·숙소' 에서 구장 선택 후 POI 리스트를 확인해 주세요.",
        ("경기", "일정", "schedule"):
            "AI 연결 오류로 탭 1 '경기 & 예측'에서 원정 경기 리스트를 직접 확인해 주세요.",
    }
    for keywords, text in canned.items():
        if any(k in user_msg for k in keywords):
            return _wrap_fallback(text)
    return _wrap_fallback(
        "AI 서비스가 일시적으로 응답하지 않습니다. Ollama 서버 또는 Gemini API 상태를 확인해 주세요."
    )


def _wrap_fallback(content: str) -> dict:
    return {
        "content": content,
        "tool_calls": None,
        "model": "fallback",
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "stream": None,
    }


def _try_ollama(
    messages: list[dict],
    tools: list[dict] | None,
    temperature: float,
    max_tokens: int,
    prefer_tool_model: bool,
) -> dict | None:
    """Ollama 시도. 서버 다운/에러 시 None 반환."""
    if config.IS_CLOUD_RUN:
        return None
    if not ollama_client.health():
        return None
    primary = config.OLLAMA_TOOL_MODEL if prefer_tool_model else config.OLLAMA_CHAT_MODEL
    try:
        resp = ollama_client.chat(
            model=primary,
            messages=messages,
            tools=tools,
            temperature=temperature,
            num_predict=max_tokens,
            stream=False,
        )
        resp["stream"] = None
        return resp
    except httpx.HTTPError as exc:
        log.warning("Ollama 주 모델 실패 (%s): %s", primary, exc)

    fb = config.OLLAMA_FALLBACK_MODEL
    if fb and fb != primary:
        try:
            resp = ollama_client.chat(
                model=fb,
                messages=messages,
                tools=tools,
                temperature=temperature,
                num_predict=max_tokens,
                stream=False,
            )
            resp["stream"] = None
            return resp
        except httpx.HTTPError as exc:
            log.warning("Ollama fallback 모델 실패 (%s): %s", fb, exc)

    return None


def _try_gemini(
    messages: list[dict],
    tools: list[dict] | None,
    temperature: float,
    max_tokens: int,
) -> dict | None:
    """Gemini 시도. SDK/키 부재 시 None."""
    if not gemini_client.health():
        return None
    resp = gemini_client.chat(
        messages=messages,
        tools=tools,
        temperature=temperature,
        num_predict=max_tokens,
    )
    # 모델 에러/unavailable은 건너뛰기
    if "unavailable" in resp.get("model", "") or "error" in resp.get("model", ""):
        return None
    resp["stream"] = None
    return resp


def chat_complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    stream: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
    prefer_tool_model: bool = False,
) -> dict:
    """3단계 Fallback 채팅 완성.

    Returns:
        {content, tool_calls, model, usage, stream}
    """
    temperature = config.OLLAMA_TEMPERATURE if temperature is None else temperature
    max_tokens = config.OLLAMA_MAX_TOKENS if max_tokens is None else max_tokens

    # 스트리밍은 Ollama 로컬에서만 지원 (Gemini는 우선 non-stream)
    if stream and not config.IS_CLOUD_RUN and ollama_client.health():
        primary = config.OLLAMA_TOOL_MODEL if prefer_tool_model else config.OLLAMA_CHAT_MODEL
        try:
            gen = ollama_client.chat(
                model=primary,
                messages=messages,
                tools=tools,
                temperature=temperature,
                num_predict=max_tokens,
                stream=True,
            )
            return {
                "content": "",
                "tool_calls": None,
                "model": primary,
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "stream": gen,
            }
        except httpx.HTTPError as exc:
            log.warning("Ollama 스트리밍 실패: %s — 동기 모드로 전환", exc)

    # 1차: Ollama
    resp = _try_ollama(messages, tools, temperature, max_tokens, prefer_tool_model)
    if resp is not None:
        return resp

    # 2차: Gemini
    resp = _try_gemini(messages, tools, temperature, max_tokens)
    if resp is not None:
        return resp

    # 3차: 규칙 기반
    return _fallback_response(messages)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    resp = chat_complete(
        [
            {"role": "system", "content": "당신은 KBO 원정 응원 전문 플래너입니다. 한국어로만 2~3문장 이내 간결하게."},
            {"role": "user", "content": "LG 팬인데 이번 주말 KT 원정 어때?"},
        ],
        temperature=0.7,
        max_tokens=200,
    )
    print(f"Model   : {resp['model']}")
    print(f"Content : {resp['content']}")
    print(f"Usage   : {resp['usage']}")
