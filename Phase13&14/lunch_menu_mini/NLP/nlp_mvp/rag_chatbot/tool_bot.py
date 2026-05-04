"""
ToolCallingBot — RAG chatbot with Phase 7 tool-calling loop.

Flow for a single user turn:

    1. Build a system prompt that describes the 8 available tools
       (prompt fallback format). Optional: also pass them as Ollama `tools`
       parameter when native support is available.
    2. LLM call → raw response may contain `[TOOL: name(args)]` blocks (or,
       with native tool support, a `tool_calls` array).
    3. Parse tool calls → execute each via `ToolExecutor` → format results.
    4. If any tools were called, feed the formatted results back into the
       LLM as another turn and ask for a final answer.
    5. Return `{response, tool_calls, iterations, latency_ms}`.

Kept self-contained so `LunchCoachBot` (Phase 5) is untouched.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from nlp_mvp.rag_chatbot.tools.definitions import TOOL_DEFINITIONS
from nlp_mvp.rag_chatbot.tools.executors import ToolExecutor
from nlp_mvp.rag_chatbot.tools.fallback import (
    parse_tool_calls,
    strip_tool_calls,
)
from nlp_mvp.rag_chatbot.tools.formatter import format_tool_result
from nlp_mvp.rag_chatbot.tools.router import guess_tool_from_query
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


SYSTEM_PROMPT = """당신은 Mini 식사 최적화 챗봇입니다.
아침/점심/저녁 모두 지원합니다 — 사용자 query 앞에 [아침]/[점심]/[저녁] prefix가 있거나
query 안에 시간대 키워드가 있으면 그에 맞춰 답하세요.

필요할 때 아래 도구를 호출하세요.

도구 호출 방식:
- 한 줄에 `[TOOL: 도구이름(인자1=값1, 인자2=값2)]` 형식으로 작성
- 여러 도구를 동시에 호출할 수 있음
- 도구 호출 후 결과를 받아 최종 답변을 작성
- 도구가 필요 없으면 바로 한국어로 답변
- 시간대가 명시된 경우 meal_type 인자를 함께 전달 (breakfast/lunch/dinner)

사용 가능한 도구:
{tool_list}

규칙:
- 쓰기 도구(cast_vote, record_meal)는 사용자가 명시적으로 요청할 때만 호출
- 도구 호출 전에 간단히 왜 그 도구를 쓰는지 한 문장 설명
- 최종 답변은 자연스러운 한국어 대화체
- 추천 카테고리는 시간대에 맞춰: 아침=카페/베이커리/죽/김밥, 저녁=한식/일식/고깃집/회식, 점심=전체"""


def _build_system_prompt() -> str:
    lines = []
    for t in TOOL_DEFINITIONS:
        fn = t["function"]
        name = fn["name"]
        desc = fn["description"].split(".")[0]
        lines.append(f"- {name}: {desc}")
    return SYSTEM_PROMPT.format(tool_list="\n".join(lines))


@dataclass
class ToolChatResponse:
    response: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    latency_ms: int = 0
    fallback_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "iterations": self.iterations,
            "latency_ms": self.latency_ms,
            "fallback_used": self.fallback_used,
        }


class ToolCallingBot:
    """
    Chatbot that can call Mini lunch-optimizer endpoints via tool functions.

    Args:
        user_id: integer user id (passed to tools that need it)
        ollama_client: optional OllamaClient; default: new instance
        executor: optional ToolExecutor; default: new instance pointing at env
        max_iterations: safety cap on tool-calling loop (default 3)
        temperature: LLM temperature
    """

    def __init__(
        self,
        user_id: int | str = 1,
        ollama_client=None,
        executor: ToolExecutor | None = None,
        max_iterations: int = 3,
        temperature: float = 0.2,
        llm_client=None,
    ):
        self.user_id = str(user_id)
        # Phase 14: 'ollama_client'는 backward-compat 별칭.
        client = llm_client or ollama_client
        if client is None:
            from nlp_mvp.shared.llm.factory import get_tools_client
            client = get_tools_client()
        self.ollama = client
        self.llm = client
        self.executor = executor or ToolExecutor()
        self.max_iterations = max_iterations
        self.temperature = temperature
        self._system_prompt = _build_system_prompt()
        logger.info(f"ToolCallingBot initialized: user={self.user_id}")

    # -------------------------------------------------------------------------
    def chat(self, user_query: str) -> ToolChatResponse:
        """Run a full tool-calling turn and return the structured response."""
        start = time.time()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_query},
        ]
        all_calls: list[dict[str, Any]] = []
        all_results: list[dict[str, Any]] = []
        fallback_used = False

        final_text = ""
        iterations = 0

        for i in range(self.max_iterations):
            iterations = i + 1
            try:
                raw = self.ollama.chat(
                    messages=messages,
                    options={"temperature": self.temperature},
                )
            except Exception as e:
                logger.exception(f"Ollama chat failed: {e}")
                final_text = f"죄송합니다. 일시적인 오류가 발생했어요. ({e})"
                break

            # 1. Try to parse tool calls from the response
            calls = parse_tool_calls(raw)

            # 2. On the first iteration, if no explicit calls and no prior
            #    activity, fall back to intent heuristic
            if not calls and not all_calls and i == 0:
                guess = guess_tool_from_query(user_query)
                if guess is not None:
                    calls = [guess]
                    fallback_used = True
                    logger.info(f"Fallback router picked: {guess['name']}")

            if not calls:
                # No more tools to call — LLM has produced the final answer
                final_text = strip_tool_calls(raw)
                break

            # 3. Execute each tool call
            step_results: list[dict[str, Any]] = []
            for call in calls:
                args = self._inject_defaults(call.get("args", {}))
                result = self.executor.execute(call["name"], args)
                step_results.append(result)
                all_calls.append(call)
                all_results.append(result)

            # 4. Feed results back to the LLM and iterate
            result_text = "\n\n".join(format_tool_result(r) for r in step_results)
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": (
                    "아래는 방금 호출한 도구의 결과입니다. 이 정보를 바탕으로 "
                    "사용자에게 자연스러운 한국어 답변을 작성해주세요. "
                    "추가 도구가 필요하면 다시 호출해도 됩니다.\n\n"
                    f"{result_text}"
                ),
            })

        latency_ms = int((time.time() - start) * 1000)
        return ToolChatResponse(
            response=final_text or "응답을 생성하지 못했습니다.",
            tool_calls=all_calls,
            tool_results=all_results,
            iterations=iterations,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
        )

    # -------------------------------------------------------------------------
    def _inject_defaults(self, args: dict[str, Any]) -> dict[str, Any]:
        """Inject `user_id` when a tool needs it and the LLM didn't provide one."""
        out = dict(args)
        if "user_id" in out and not out["user_id"]:
            out["user_id"] = self.user_id
        if "user_id" not in out and out.get("_inject_user_id"):
            out["user_id"] = self.user_id
            out.pop("_inject_user_id", None)
        return out


__all__ = ["ToolCallingBot", "ToolChatResponse"]
