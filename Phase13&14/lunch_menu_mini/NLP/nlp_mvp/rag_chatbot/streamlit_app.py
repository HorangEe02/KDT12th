"""
Streamlit 데모 UI.

실행:
    cd Mini/NLP
    streamlit run nlp_mvp/rag_chatbot/streamlit_app.py
"""
import streamlit as st
from sqlalchemy import text

from nlp_mvp.rag_chatbot.chatbot import LunchCoachBot
from nlp_mvp.rag_chatbot.indexer import ChromaDBIndexer
from nlp_mvp.shared.db import get_session
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="🍱 런치 코치", page_icon="🍱", layout="wide")
st.title("🍱 런치 코치 — AI 점심 상담")


# -----------------------------------------------------------------------------
# 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")

    @st.cache_data(ttl=60)
    def load_users():
        try:
            with get_session() as session:
                rows = session.execute(
                    text("SELECT id, name FROM users ORDER BY id")
                ).fetchall()
            return [(r[0], r[1]) for r in rows]
        except Exception as e:
            logger.warning(f"load_users failed: {e}")
            return [(1, "기본 사용자")]

    users = load_users()
    user_id = st.selectbox(
        "사용자",
        options=[u[0] for u in users],
        format_func=lambda x: dict(users).get(x, f"user_{x}"),
    )

    st.divider()

    if st.button("🔄 인덱스 재빌드"):
        with st.spinner("ChromaDB 인덱싱 중..."):
            try:
                indexer = ChromaDBIndexer()
                result = indexer.build_all(user_id=user_id)
                st.success(f"완료: {result}")
            except ImportError as e:
                st.error(f"의존성 누락: {e}")

    if st.button("🗑️ 대화 초기화"):
        st.session_state.pop("bot", None)
        st.session_state.pop("messages", None)
        st.rerun()

    st.divider()
    st.caption("**모델 정보**")
    bot_obj = st.session_state.get("bot")
    model_name = bot_obj.ollama.model if bot_obj else "..."
    st.code(f"Ollama: {model_name}")


# -----------------------------------------------------------------------------
# 챗봇 초기화
# -----------------------------------------------------------------------------
if "bot" not in st.session_state or st.session_state.get("user_id") != user_id:
    try:
        st.session_state["bot"] = LunchCoachBot(user_id=user_id)
        st.session_state["user_id"] = user_id
        st.session_state["messages"] = []
    except ImportError as e:
        st.error(f"의존성 누락: {e}")
        st.stop()

bot: LunchCoachBot = st.session_state["bot"]


# -----------------------------------------------------------------------------
# 대화 UI
# -----------------------------------------------------------------------------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("recommendations"):
            cols = st.columns(min(3, len(msg["recommendations"])))
            for col, rec in zip(cols, msg["recommendations"]):
                with col:
                    st.info(
                        f"**{rec.get('restaurant', '')}**\n\n"
                        f"🍽️ {rec.get('menu', '')}\n\n"
                        f"_{rec.get('reason', '')}_"
                    )


if user_input := st.chat_input("오늘 점심, 뭐가 좋을까요?"):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("런치 코치가 생각 중... 🤔"):
            response = bot.chat(user_input)

        st.markdown(response.response)

        if response.recommendations:
            st.markdown("### 🎯 추천")
            cols = st.columns(min(3, len(response.recommendations)))
            for col, rec in zip(cols, response.recommendations):
                with col:
                    st.info(
                        f"**{rec.get('restaurant', '')}**\n\n"
                        f"🍽️ {rec.get('menu', '')}\n\n"
                        f"_{rec.get('reason', '')}_"
                    )

        with st.expander("🔍 디버그"):
            st.write(f"**응답 속도:** {response.latency_ms} ms")
            st.write(f"**환각 검증:** {response.validation}")
            st.json(response.context_used)

    st.session_state["messages"].append({
        "role": "assistant",
        "content": response.response,
        "recommendations": response.recommendations,
    })
