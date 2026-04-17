"""Gemini API 클라이언트 — 신 SDK (google-genai) 기반.

Cloud Run 배포 시 Ollama 대체. chat/embed 인터페이스는 ollama_client와 동일.
무료 tier 기본 모델: gemini-2.5-flash-lite (한국어 OK, function calling 지원).
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from src import config

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client():
    """google-genai Client lazy init. SDK/키 부재 시 None."""
    if not config.GEMINI_API_KEY:
        return None
    try:
        from google import genai
        return genai.Client(api_key=config.GEMINI_API_KEY)
    except ImportError:
        log.warning("google-genai SDK 미설치")
        return None
    except Exception as exc:
        log.warning("Gemini 클라이언트 초기화 실패: %s", exc)
        return None


def health() -> bool:
    return _get_client() is not None


def _to_contents(messages: list[dict]):
    """OpenAI 메시지 → (system_instruction, contents) 변환. Content/Part 객체는 dict로 반환."""
    system_parts: list[str] = []
    contents: list[dict] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "") or ""
        if role == "system":
            if content:
                system_parts.append(content)
        elif role == "tool":
            # tool 결과를 user 메시지로 변환
            contents.append({
                "role": "user",
                "parts": [{"text": f"[도구 결과] {m.get('name','')}: {content}"}],
            })
        else:
            gemini_role = "model" if role == "assistant" else "user"
            if content:
                contents.append({"role": gemini_role, "parts": [{"text": content}]})
    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, contents


def _to_gemini_tools(tools: list[dict] | None):
    """OpenAI tool_use 스키마 → Gemini Tool 객체."""
    if not tools:
        return None
    try:
        from google.genai import types
    except ImportError:
        return None

    decls = []
    for t in tools:
        fn = t.get("function") or {}
        name = fn.get("name")
        if not name:
            continue
        params = fn.get("parameters") or {"type": "object", "properties": {}}
        decls.append(types.FunctionDeclaration(
            name=name,
            description=fn.get("description", ""),
            parameters_json_schema=params,
        ))
    if not decls:
        return None
    return [types.Tool(function_declarations=decls)]


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    num_predict: int = 800,
    model: str | None = None,
) -> dict:
    """Gemini 채팅 — ollama_client.chat과 동일 반환 포맷."""
    client = _get_client()
    if client is None:
        return {
            "content": "",
            "tool_calls": None,
            "model": "gemini-unavailable",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    try:
        from google.genai import types
    except ImportError:
        return {
            "content": "",
            "tool_calls": None,
            "model": "gemini-unavailable",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    model_name = model or config.GEMINI_CHAT_MODEL
    system_instruction, contents = _to_contents(messages)
    gemini_tools = _to_gemini_tools(tools)

    cfg_kwargs: dict[str, Any] = {
        "temperature": float(temperature),
        "max_output_tokens": int(num_predict),
    }
    if system_instruction:
        cfg_kwargs["system_instruction"] = system_instruction
    if gemini_tools:
        cfg_kwargs["tools"] = gemini_tools

    config_obj = types.GenerateContentConfig(**cfg_kwargs)

    for attempt_model in (model_name, config.GEMINI_FALLBACK_MODEL):
        if not attempt_model:
            continue
        try:
            resp = client.models.generate_content(
                model=attempt_model,
                contents=contents if contents else "hello",
                config=config_obj,
            )
            return _parse_response(resp, attempt_model)
        except Exception as exc:
            msg = str(exc)[:180]
            log.warning("Gemini %s 호출 실패: %s", attempt_model, msg)
            continue

    return {
        "content": "",
        "tool_calls": None,
        "model": f"{model_name}-error",
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


def _parse_response(resp, model_name: str) -> dict:
    content_text = ""
    tool_calls: list[dict] = []

    try:
        for candidate in (resp.candidates or []):
            if not candidate.content:
                continue
            for part in (candidate.content.parts or []):
                if getattr(part, "text", None):
                    content_text += part.text
                fc = getattr(part, "function_call", None)
                if fc and getattr(fc, "name", None):
                    args_raw = dict(fc.args) if fc.args else {}
                    # MapComposite → plain dict via JSON round-trip
                    try:
                        args = json.loads(json.dumps(args_raw, default=str))
                    except (TypeError, ValueError):
                        args = {}
                    tool_calls.append({
                        "id": f"gemini_call_{len(tool_calls)}",
                        "name": fc.name,
                        "arguments": args,
                    })
    except Exception as exc:
        log.warning("Gemini 응답 파싱 예외: %s", exc)

    usage = {"input_tokens": 0, "output_tokens": 0}
    try:
        um = resp.usage_metadata
        usage = {
            "input_tokens": int(getattr(um, "prompt_token_count", 0) or 0),
            "output_tokens": int(getattr(um, "candidates_token_count", 0) or 0),
        }
    except Exception:
        pass

    return {
        "content": content_text,
        "tool_calls": tool_calls or None,
        "model": model_name,
        "usage": usage,
    }


def embed(text: str, model: str | None = None) -> list[float]:
    """Gemini text embedding. 실패 시 빈 리스트."""
    client = _get_client()
    if client is None:
        return []
    model_name = model or config.GEMINI_EMBED_MODEL
    try:
        resp = client.models.embed_content(
            model=model_name,
            contents=text,
        )
        embeddings = resp.embeddings
        if embeddings and embeddings[0].values:
            return list(embeddings[0].values)
    except Exception as exc:
        log.warning("Gemini 임베딩 실패: %s", exc)
    return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(f"Health: {health()}")
    if health():
        resp = chat(
            [
                {"role": "system", "content": "당신은 KBO 원정 응원 전문 플래너입니다. 한국어 한 문장으로만 답하세요."},
                {"role": "user", "content": "LG 팬인데 반갑다고 인사해줘"},
            ],
            temperature=0.5,
            num_predict=100,
        )
        print(f"Model   : {resp['model']}")
        print(f"Content : {resp['content']}")
        print(f"Usage   : {resp['usage']}")

        vec = embed("야구 원정 응원")
        print(f"Embed dim: {len(vec)}")
