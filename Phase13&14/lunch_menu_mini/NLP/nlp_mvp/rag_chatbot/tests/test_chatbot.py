"""chatbot.py 단위 테스트 — Ollama / Retriever 모킹."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from nlp_mvp.rag_chatbot.chatbot import (
    ChatResponse,
    LunchCoachBot,
    extract_recommendations,
    strip_json_block,
    validate_response,
)
from nlp_mvp.rag_chatbot.history import ConversationHistory


# =============================================================================
# 파싱 유틸
# =============================================================================
class TestExtractRecommendations:
    def test_valid_json(self):
        resp = '''답변입니다.
```json
{"recommendations": [{"restaurant": "A", "menu": "B", "reason": "C"}]}
```'''
        recs = extract_recommendations(resp)
        assert len(recs) == 1
        assert recs[0]["restaurant"] == "A"

    def test_multiple(self):
        resp = '''```json
{"recommendations": [{"restaurant": "A"}, {"restaurant": "B"}]}
```'''
        recs = extract_recommendations(resp)
        assert len(recs) == 2

    def test_no_json(self):
        assert extract_recommendations("일반 응답") == []

    def test_empty(self):
        assert extract_recommendations("") == []

    def test_malformed_json(self):
        resp = '```json\n{not valid}\n```'
        assert extract_recommendations(resp) == []

    def test_no_recommendations_key(self):
        resp = '```json\n{"other": []}\n```'
        assert extract_recommendations(resp) == []


class TestStripJsonBlock:
    def test_strip(self):
        resp = '본문\n```json\n{"a": 1}\n```\n'
        assert strip_json_block(resp).strip() == "본문"

    def test_no_block(self):
        assert strip_json_block("순수 텍스트") == "순수 텍스트"

    def test_empty(self):
        assert strip_json_block("") == ""


# =============================================================================
# 환각 검증
# =============================================================================
class TestValidateResponse:
    def test_within_context(self):
        ctx = {"restaurants": [{"metadata": {"name": "A식당"}}]}
        result = validate_response("A식당을 추천합니다.", ctx)
        assert "A식당" in result["mentioned"]
        assert result["allowed_count"] == 1
        assert result["mentioned_count"] == 1

    def test_no_mention(self):
        ctx = {"restaurants": [{"metadata": {"name": "A식당"}}]}
        result = validate_response("그냥 대답입니다.", ctx)
        assert result["mentioned_count"] == 0

    def test_empty_context(self):
        result = validate_response("응답", {})
        assert result["allowed_count"] == 0


# =============================================================================
# LunchCoachBot — 모킹
# =============================================================================
@pytest.fixture
def mock_ollama():
    mock = MagicMock()
    mock.chat.return_value = '''맛있는 점심을 추천드려요!
```json
{"recommendations": [{"restaurant": "A식당", "menu": "김치찌개", "reason": "건강식"}]}
```'''
    mock.model = "qwen2.5:7b-instruct"
    return mock


@pytest.fixture
def mock_retriever():
    mock = MagicMock()
    mock.retrieve.return_value = {
        "meal_history": [{"text": "어제: 라면", "metadata": {}, "distance": 0.3}],
        "nutrition_info": [],
        "restaurants": [{"text": "A식당 한식", "metadata": {"name": "A식당"}, "distance": 0.2}],
    }
    return mock


class TestLunchCoachBot:
    def test_chat_returns_response(self, mock_ollama, mock_retriever):
        bot = LunchCoachBot(
            user_id=1,
            ollama_client=mock_ollama,
            retriever=mock_retriever,
        )
        result = bot.chat("뭐 먹을까")
        assert isinstance(result, ChatResponse)
        assert "맛있는" in result.response
        assert len(result.recommendations) == 1
        assert result.recommendations[0]["restaurant"] == "A식당"
        assert result.latency_ms >= 0

    def test_history_updated(self, mock_ollama, mock_retriever):
        bot = LunchCoachBot(user_id=1, ollama_client=mock_ollama, retriever=mock_retriever)
        bot.chat("Q1")
        bot.chat("Q2")
        # 2턴 = 4 messages
        assert len(bot.history.messages) == 4

    def test_reset(self, mock_ollama, mock_retriever):
        bot = LunchCoachBot(user_id=1, ollama_client=mock_ollama, retriever=mock_retriever)
        bot.chat("Q")
        bot.reset()
        assert len(bot.history.messages) == 0

    def test_ollama_failure_returns_error(self, mock_retriever):
        mock_ollama = MagicMock()
        mock_ollama.chat.side_effect = RuntimeError("connection failed")
        bot = LunchCoachBot(user_id=1, ollama_client=mock_ollama, retriever=mock_retriever)
        result = bot.chat("Q")
        assert "오류" in result.response
        assert result.recommendations == []

    def test_retriever_failure_continues(self, mock_ollama):
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = RuntimeError("chroma down")
        bot = LunchCoachBot(user_id=1, ollama_client=mock_ollama, retriever=mock_retriever)
        result = bot.chat("Q")
        # retriever 실패해도 ollama 는 호출되어야 함
        assert result.context_used == {"meal_history": [], "nutrition_info": [], "restaurants": []}
        assert mock_ollama.chat.called

    def test_validation_in_response(self, mock_ollama, mock_retriever):
        bot = LunchCoachBot(user_id=1, ollama_client=mock_ollama, retriever=mock_retriever)
        result = bot.chat("Q")
        assert "A식당" in result.validation["mentioned"]


# =============================================================================
# ConversationHistory
# =============================================================================
class TestConversationHistory:
    def test_add_and_len(self):
        h = ConversationHistory(max_turns=3)
        h.add_user("u1")
        h.add_assistant("a1")
        assert len(h) == 2

    def test_prune_by_turns(self):
        h = ConversationHistory(max_turns=2)
        for i in range(5):
            h.add_user(f"u{i}")
            h.add_assistant(f"a{i}")
        # 최대 2턴 = 4 메시지
        assert len(h) == 4

    def test_prune_by_chars(self):
        h = ConversationHistory(max_turns=100, max_chars=50)
        h.add_user("x" * 30)
        h.add_assistant("y" * 30)
        # 60자 > 50 → 첫 메시지 제거
        assert len(h) == 1

    def test_clear(self):
        h = ConversationHistory()
        h.add_user("Q")
        h.clear()
        assert len(h) == 0
