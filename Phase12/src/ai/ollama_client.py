"""Ollama 저수준 클라이언트 — REST /api/chat, /api/embeddings, /api/tags.

httpx 기반 (ollama 공식 파이썬 패키지 의존 없이 동작).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Iterable

import httpx

from src import config

log = logging.getLogger(__name__)


def health() -> bool:
    """Ollama 서버 도달 가능 여부. 모델 목록 조회 성공 시 True."""
    try:
        resp = httpx.get(
            f"{config.OLLAMA_HOST}/api/tags",
            timeout=httpx.Timeout(3.0),
        )
        resp.raise_for_status()
        return True
    except httpx.HTTPError:
        return False


def list_models() -> list[str]:
    """설치된 모델 이름 리스트."""
    try:
        resp = httpx.get(
            f"{config.OLLAMA_HOST}/api/tags",
            timeout=httpx.Timeout(5.0),
        )
        resp.raise_for_status()
        data = resp.json()
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("모델 목록 조회 실패: %s", exc)
        return []


def has_model(name: str) -> bool:
    """특정 모델(정확 일치 또는 접두어 일치)이 설치됐는지."""
    models = list_models()
    if name in models:
        return True
    # "gemma4:e4b" 같이 suffix 포함 매칭
    return any(m == name or m.startswith(f"{name}:") for m in models)


def chat(
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    num_predict: int = 800,
    stream: bool = False,
    timeout: int | None = None,
) -> dict:
    """Ollama /api/chat 호출.

    Args:
        model: 모델 이름 (예: gemma4:e4b)
        messages: [{"role": "system"|"user"|"assistant"|"tool", "content": "...", "tool_calls": [...] 선택}]
        tools: OpenAI tool_use 스키마 리스트 (선택)
        temperature, num_predict: 생성 파라미터
        stream: True면 제너레이터 반환
        timeout: 초, 기본 config.OLLAMA_REQUEST_TIMEOUT

    Returns:
        stream=False: {"content": str, "tool_calls": list|None, "model": str, "usage": dict}
        stream=True : Iterable[str] — 청크 단위 content
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": bool(stream),
        # Gemma 3/4 계열은 reasoning(thinking) 모드를 기본 활성화하는 경우가 있어
        # content가 비고 thinking 필드에만 텍스트가 채워진다. 명시적으로 끈다.
        "think": False,
        "options": {
            "temperature": float(temperature),
            "num_predict": int(num_predict),
        },
    }
    if tools:
        payload["tools"] = tools

    url = f"{config.OLLAMA_HOST}/api/chat"
    t_out = timeout if timeout is not None else config.OLLAMA_REQUEST_TIMEOUT

    if stream:
        return _stream_chat(url, payload, t_out)
    return _sync_chat(url, payload, t_out)


def _sync_chat(url: str, payload: dict, timeout: int) -> dict:
    with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    msg = data.get("message") or {}
    tool_calls_raw = msg.get("tool_calls") or []
    tool_calls = None
    if tool_calls_raw:
        tool_calls = []
        for i, tc in enumerate(tool_calls_raw):
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({
                "id": tc.get("id") or f"call_{i}",
                "name": fn.get("name", ""),
                "arguments": args or {},
            })

    # content가 비었는데 thinking만 채워진 경우 (구버전 Ollama + Gemma 조합),
    # thinking을 content로 승격하여 UX 단절 방지.
    content = msg.get("content", "") or ""
    thinking = msg.get("thinking") or ""
    if not content and thinking:
        log.info("content 비어 thinking을 승격 (모델 reasoning 모드)")
        content = thinking

    return {
        "content": content,
        "tool_calls": tool_calls,
        "model": data.get("model", payload.get("model", "")),
        "usage": {
            "input_tokens": int(data.get("prompt_eval_count") or 0),
            "output_tokens": int(data.get("eval_count") or 0),
        },
    }


def _stream_chat(url: str, payload: dict, timeout: int) -> Iterable[str]:
    with httpx.stream("POST", url, json=payload, timeout=httpx.Timeout(timeout)) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = obj.get("message") or {}
            chunk = msg.get("content", "")
            if chunk:
                yield chunk
            if obj.get("done"):
                break


def embed(text: str, model: str | None = None) -> list[float]:
    """임베딩 벡터 생성. 실패 시 빈 리스트."""
    model = model or config.OLLAMA_EMBED_MODEL
    try:
        resp = httpx.post(
            f"{config.OLLAMA_HOST}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=httpx.Timeout(30.0),
        )
        resp.raise_for_status()
        data = resp.json()
        return list(data.get("embedding") or [])
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("임베딩 실패 (%s): %s", model, exc)
        return []


def warm_up(model: str | None = None) -> bool:
    """모델 예열 — 첫 응답 지연 흡수."""
    model = model or config.OLLAMA_CHAT_MODEL
    try:
        chat(model, [{"role": "user", "content": "ping"}],
             temperature=0.0, num_predict=4, timeout=30)
        return True
    except httpx.HTTPError as exc:
        log.warning("모델 예열 실패 (%s): %s", model, exc)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(f"서버 상태: {'OK' if health() else 'DOWN'}")
    models = list_models()
    print(f"설치된 모델 수: {len(models)}")
    print(f"gemma4:e4b 존재: {has_model('gemma4:e4b')}")
    print(f"bge-m3:latest 존재: {has_model('bge-m3:latest')}")

    resp = chat(
        config.OLLAMA_CHAT_MODEL,
        [
            {"role": "system", "content": "당신은 KBO 원정 응원 가이드입니다. 한 문장으로만 답하세요."},
            {"role": "user", "content": "안녕하세요!"},
        ],
        temperature=0.5, num_predict=80,
    )
    print(f"Model: {resp['model']}")
    print(f"Content: {resp['content']}")
    print(f"Tokens: {resp['usage']}")
