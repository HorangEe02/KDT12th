"""Tab 4 — AI 원정 플래너 챗봇.

모드:
  단일 LLM + tool_use (기본) — OpenAI 호환 Function Calling
  Multi-Agent (토글)           — Supervisor → Expert → Synthesizer
시연 안전장치: 사이드바 '🎬 시연 모드' 활성화 시 mock_responses에서 답변 재생.
"""
from __future__ import annotations

import json
import time

import streamlit as st

from src.ai.llm_client import chat_complete
from src.ai.mock_responses import FALLBACK_RESPONSE, get_mock_response
from src.ai.prompts import build_system_prompt
from src.ai.tools import TOOL_SCHEMAS, execute_tool

_EXAMPLES = [
    "광주 원정 1박 2일, 아이랑 가려는데 추천해줘",
    "이번 주말 부산 맛집 세 곳 알려줘",
    "비 올 확률 높으면 실내 관광지는?",
]


def _render_tool_expander(tool_calls: list[dict], executed: list[dict]) -> None:
    with st.expander("🔍 AI가 수행한 작업 (Thought → Action → Observation)", expanded=True):
        st.markdown(f"💭 **Thought**: LLM이 {len(tool_calls)}개 도구 호출이 필요하다고 판단했습니다.")
        st.divider()
        for i, (call, done) in enumerate(zip(tool_calls, executed), 1):
            st.markdown(f"### 🔧 Action {i}: `{call['name']}`")
            st.json(call.get("arguments", {}))
            st.markdown(f"### 📋 Observation {i}")
            result = done.get("result", {})
            if result.get("success"):
                data = result.get("data")
                if isinstance(data, dict) and "games" in data:
                    st.success(f"✅ 경기 {data.get('count', 0)}개 조회")
                    if data["games"]:
                        st.dataframe(data["games"][:5], use_container_width=True, hide_index=True)
                elif isinstance(data, dict) and "win_probability" in data:
                    st.success(f"✅ 승률 {data.get('win_percentage')}")
                    st.json(data)
                elif isinstance(data, dict) and "places" in data:
                    st.success(f"✅ POI {data.get('count', 0)}곳")
                    if data["places"]:
                        st.dataframe(data["places"], use_container_width=True, hide_index=True)
                elif isinstance(data, dict) and "distance_km" in data:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("거리", f"{data['distance_km']} km")
                    c2.metric("소요", f"{data['duration_min']}분" if data.get("duration_min") else "—")
                    c3.metric("통행료", f"{data['toll_fare']:,}원" if data.get("toll_fare") else "—")
                    if data.get("fallback"):
                        st.caption("※ 카카오모빌리티 API 미승인 → 직선 거리 fallback")
                elif isinstance(data, dict) and "tips" in data:
                    st.success(f"✅ RAG 검색 {len(data['tips'])}건")
                    for t in data["tips"]:
                        st.markdown(f"- **[{t.get('stadium')}/{t.get('category')}]** {t.get('tip')}")
                else:
                    st.json(data)
            else:
                st.error(f"❌ {result.get('error', '알 수 없는 오류')}")
            if i < len(tool_calls):
                st.divider()


def _run_tool_cycle(messages: list[dict], tool_calls: list[dict]) -> tuple[list[dict], list[dict]]:
    """각 tool_call 실행 + 도구 결과 메시지 리스트 준비."""
    executed: list[dict] = []
    tool_msgs: list[dict] = []
    for call in tool_calls:
        result = execute_tool(call["name"], call.get("arguments", {}))
        executed.append({"name": call["name"], "arguments": call.get("arguments", {}), "result": result})
        tool_msgs.append({
            "role": "tool",
            "name": call["name"],
            "content": json.dumps(result, ensure_ascii=False, default=str)[:1500],
        })
    # 도구 결과를 assistant 메시지로 wrap해서 LLM에 재전달
    messages.append({
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": c.get("id", f"call_{i}"),
                "type": "function",
                "function": {"name": c["name"], "arguments": json.dumps(c.get("arguments", {}), ensure_ascii=False)},
            }
            for i, c in enumerate(tool_calls)
        ],
    })
    messages.extend(tool_msgs)
    return messages, executed


def _stream_mock(text: str, delay: float = 0.012) -> None:
    placeholder = st.empty()
    rendered = ""
    for ch in text:
        rendered += ch
        placeholder.markdown(rendered + "▌")
        if ch in "\n\u3000 ":
            time.sleep(delay * 2)
    placeholder.markdown(rendered)


def _handle_single_llm(user_input: str, filters: dict, use_tools: bool) -> str:
    system_prompt = build_system_prompt(filters)
    recent = st.session_state.get("messages", [])[-10:]
    # OpenAI-호환 메시지에서 tool 결과 제거 (새 cycle 시작)
    clean_recent = [m for m in recent if m.get("role") in ("user", "assistant")]
    messages = [{"role": "system", "content": system_prompt}] + clean_recent + [
        {"role": "user", "content": user_input}
    ]

    with st.spinner("AI가 생각 중..."):
        resp = chat_complete(
            messages,
            tools=TOOL_SCHEMAS if use_tools else None,
            temperature=0.7,
            max_tokens=700,
            prefer_tool_model=use_tools,
        )

    st.session_state["last_model"] = resp.get("model", "?")

    tool_calls = resp.get("tool_calls")
    if tool_calls:
        messages, executed = _run_tool_cycle(messages, tool_calls)
        _render_tool_expander(tool_calls, executed)
        with st.spinner("최종 답변 생성 중..."):
            final = chat_complete(messages, temperature=0.6, max_tokens=700)
        st.session_state["last_model"] = final.get("model", "?")
        st.markdown("### 💬 AI 답변")
        answer = final.get("content") or "(답변 생성 실패)"
    else:
        answer = resp.get("content") or "(답변 생성 실패)"

    st.markdown(answer)
    if resp.get("model") == "fallback":
        st.warning("⚠️ Ollama 서버 응답 없음 → 규칙 기반 fallback 응답입니다.")
    return answer


def _handle_multi_agent(user_input: str, filters: dict) -> str:
    from src.ai.agents import run_multi_agent

    with st.expander("🎬 에이전트 협업 과정", expanded=True):
        log_placeholder = st.empty()
        log_lines: list[str] = []

        def cb(stage: str, msg: str) -> None:
            log_lines.append(f"- **{stage}** · {msg}")
            log_placeholder.markdown("\n".join(log_lines))

        with st.spinner("Multi-Agent 작업 중..."):
            result = run_multi_agent(user_input, filters, progress_callback=cb)

        st.markdown("---")
        st.markdown("#### 전문가 분석 결과")
        for k, v in result["findings"].items():
            st.markdown(f"**{k}**  \n{v[:400]}{'...' if len(v) > 400 else ''}")

    st.markdown("### 💬 AI 최종 답변")
    st.markdown(result["final"])
    st.session_state["last_model"] = "multi-agent"
    return result["final"]


def _handle_mock(user_input: str) -> str:
    mock = get_mock_response(user_input) or FALLBACK_RESPONSE
    if "tool_calls_shown" in mock and mock["tool_calls_shown"]:
        with st.expander("🎬 [시연 모드] AI가 수행한 작업", expanded=False):
            for tc in mock["tool_calls_shown"]:
                st.markdown(f"- 🔧 `{tc}` 호출")
    _stream_mock(mock["response"])
    st.session_state["last_model"] = "mock"
    return mock["response"]


def render(filters: dict) -> None:
    st.subheader("🤖 AI 원정 플래너")
    st.caption("자연어로 원정 계획을 물어보세요. 로컬 Ollama(gemma4)가 응답합니다.")

    # 모드 토글
    col_a, col_b, col_c = st.columns([2, 2, 3])
    with col_a:
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state["messages"] = []
            st.rerun()
    with col_b:
        use_tools = st.toggle("🛠️ 도구 호출", value=True, help="LLM이 5종 도구를 자동 호출")
    with col_c:
        use_multi = st.toggle("🎭 Multi-Agent", value=False, help="Supervisor→Expert→Synthesizer 순차 협업")

    demo_mode = bool(st.session_state.get("demo_mode", False))
    model_badge = st.session_state.get("last_model", "—")
    st.caption(f"🎬 시연 모드: **{'ON' if demo_mode else 'OFF'}**  ·  최근 응답 모델: `{model_badge}`")
    st.divider()

    # 기존 대화 렌더
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 예시 프롬프트 (빈 대화일 때만)
    if not st.session_state.get("messages"):
        st.markdown("##### 💡 예시 질문")
        cols = st.columns(3)
        for col, ex in zip(cols, _EXAMPLES):
            with col:
                if st.button(ex, use_container_width=True, key=f"ex_{hash(ex)}"):
                    st.session_state["_pending_input"] = ex
                    st.rerun()

    # 사용자 입력
    user_input = st.chat_input("원정 계획을 알려드릴게요!")
    if not user_input and st.session_state.get("_pending_input"):
        user_input = st.session_state.pop("_pending_input")

    if user_input:
        st.session_state.setdefault("messages", []).append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            if demo_mode:
                answer = _handle_mock(user_input)
            elif use_multi:
                answer = _handle_multi_agent(user_input, filters)
            else:
                answer = _handle_single_llm(user_input, filters, use_tools=use_tools)

        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.rerun()
