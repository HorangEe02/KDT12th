"""Multi-Agent 순차 호출 오케스트레이터.

Supervisor → [Schedule | Strategy | Place] → Synthesizer
- 동일 Ollama 모델에 서로 다른 system_prompt로 역할 연기
- progress_callback(stage, message)로 UI 실시간 업데이트
"""
from __future__ import annotations

import json
import logging
import re
from typing import Callable

from src.ai.llm_client import chat_complete
from src.ai.prompts import AGENT_PROMPTS
from src.ai.tools import TOOL_SCHEMAS, execute_tool

log = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], None]


def _call_agent(
    agent_key: str,
    user_query: str,
    filters: dict,
    findings: dict[str, str],
    use_tools: bool,
    temperature: float = 0.5,
    max_tokens: int = 500,
) -> tuple[str, list[dict]]:
    """단일 에이전트 호출 — 응답 텍스트 + 도구 호출 기록 반환."""
    system = AGENT_PROMPTS[agent_key]
    user_content = f"사용자 질문: {user_query}\n사용자 설정: {filters}"
    if findings:
        user_content += f"\n\n이미 수집된 정보:\n" + "\n\n".join(
            f"【{k}】\n{v}" for k, v in findings.items()
        )

    resp = chat_complete(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        tools=TOOL_SCHEMAS if use_tools else None,
        temperature=temperature,
        max_tokens=max_tokens,
        prefer_tool_model=use_tools,
    )

    tool_log: list[dict] = []
    if resp.get("tool_calls"):
        for call in resp["tool_calls"]:
            result = execute_tool(call["name"], call.get("arguments", {}))
            tool_log.append({
                "name": call["name"],
                "arguments": call.get("arguments", {}),
                "result": result,
            })
        # 도구 결과 요약을 에이전트 응답에 병합
        summary_lines = [f"[{t['name']}] " + _summarize_tool_result(t["result"]) for t in tool_log]
        findings_text = (resp.get("content") or "") + "\n\n" + "\n".join(summary_lines)
    else:
        findings_text = resp.get("content") or "(응답 없음)"

    return findings_text.strip(), tool_log


def _summarize_tool_result(result: dict, limit: int = 240) -> str:
    """도구 결과를 LLM context용 짧은 요약 문자열로 변환."""
    if not result.get("success"):
        return f"실패: {result.get('error', '알 수 없음')}"
    data = result.get("data")
    if data is None:
        return "성공 (데이터 없음)"
    try:
        text = json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(data)
    return text[:limit] + ("..." if len(text) > limit else "")


def _decide_agents(user_query: str, filters: dict) -> list[str]:
    """Supervisor 호출 → 어떤 에이전트를 쓸지 결정."""
    resp = chat_complete(
        [
            {"role": "system", "content": AGENT_PROMPTS["supervisor"]},
            {"role": "user", "content": f"질문: {user_query}\n사용자 설정: {filters}"},
        ],
        temperature=0.2,
        max_tokens=200,
    )
    text = resp.get("content") or ""
    try:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            plan = json.loads(match.group())
            agents = plan.get("agents") or []
            agents = [a for a in agents if a in ("schedule", "strategy", "place")]
            if agents:
                return agents
    except (json.JSONDecodeError, TypeError):
        pass
    # 폴백: 키워드 기반 규칙
    q = user_query.lower()
    fallback = []
    if any(k in q for k in ("경기", "일정", "스케줄", "언제")):
        fallback.append("schedule")
    if any(k in q for k in ("승률", "이길", "예측", "전략", "날씨", "비", "우천")):
        fallback.append("strategy")
    if any(k in q for k in ("맛집", "숙소", "호텔", "관광", "먹을", "추천", "코스")):
        fallback.append("place")
    if not fallback:
        fallback = ["schedule", "place"]
    return fallback


def run_multi_agent(
    user_query: str,
    filters: dict,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    """Multi-Agent 파이프라인 실행.

    Returns:
        {
            "final": str,         # 최종 답변
            "findings": dict,     # 에이전트별 중간 결과
            "tool_log": list,     # 전체 도구 호출 기록
            "agents_used": list,  # 실제 호출한 에이전트
        }
    """
    def _emit(stage: str, msg: str) -> None:
        if progress_callback:
            try:
                progress_callback(stage, msg)
            except Exception as exc:
                log.warning("progress_callback 오류: %s", exc)

    filters = filters or {}

    _emit("supervisor", "🎬 작업 계획 수립 중...")
    agents_plan = _decide_agents(user_query, filters)
    _emit("supervisor", f"📋 호출 에이전트: {', '.join(agents_plan)}")

    findings: dict[str, str] = {}
    all_tool_logs: list[dict] = []
    for agent in agents_plan:
        _emit(agent, f"🔎 {agent} 에이전트 작업 중...")
        text, tool_log = _call_agent(
            agent_key=agent,
            user_query=user_query,
            filters=filters,
            findings=findings,
            use_tools=True,
        )
        findings[agent] = text
        all_tool_logs.extend(tool_log)
        _emit(agent, f"✅ {agent} 완료 ({len(tool_log)}개 도구 호출)")

    _emit("synthesizer", "✍️ 최종 답변 작성 중...")
    synth_resp = chat_complete(
        [
            {"role": "system", "content": AGENT_PROMPTS["synthesizer"]},
            {
                "role": "user",
                "content": (
                    f"사용자 질문: {user_query}\n사용자 설정: {filters}\n\n"
                    "전문가 분석:\n"
                    + "\n\n".join(f"【{k}】\n{v}" for k, v in findings.items())
                ),
            },
        ],
        temperature=0.7,
        max_tokens=700,
    )
    final_answer = synth_resp.get("content") or "최종 답변 생성 실패"
    _emit("synthesizer", "✅ 완료")

    return {
        "final": final_answer,
        "findings": findings,
        "tool_log": all_tool_logs,
        "agents_used": agents_plan,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run_multi_agent(
        "이번 주말 KIA 원정 가서 맛집 추천해줘",
        {"team": "LG", "date_range": ("2026-04-18", "2026-04-20"), "budget": 30, "party": "couple", "transport": "train"},
        progress_callback=lambda s, m: print(f"[{s}] {m}"),
    )
    print("\n=== 최종 답변 ===")
    print(result["final"])
    print(f"\n에이전트: {result['agents_used']}")
    print(f"도구 호출: {len(result['tool_log'])}건")
