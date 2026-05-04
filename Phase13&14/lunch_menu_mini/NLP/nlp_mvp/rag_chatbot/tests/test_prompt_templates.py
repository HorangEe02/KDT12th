"""prompt_templates.py 단위 테스트."""
from __future__ import annotations

from nlp_mvp.rag_chatbot.prompt_templates import (
    SYSTEM_PROMPT,
    build_prompt,
    format_context,
)


class TestFormatContext:
    def test_empty(self):
        result = format_context({})
        assert "데이터 없음" in result

    def test_with_meals(self):
        ctx = {
            "meal_history": [{"text": "2026-04-01: 김치찌개", "metadata": {}}],
            "nutrition_info": [],
            "restaurants": [],
        }
        result = format_context(ctx)
        assert "최근 식사 이력" in result
        assert "김치찌개" in result

    def test_with_all_sections(self):
        ctx = {
            "meal_history": [{"text": "2026-04-01: 김치찌개"}],
            "nutrition_info": [{"text": "김치찌개는 650kcal"}],
            "restaurants": [{"text": "맛집A 한식 250m"}],
        }
        result = format_context(ctx)
        assert "최근 식사 이력" in result
        assert "관련 영양 정보" in result
        assert "주변 추천 식당" in result

    def test_only_restaurants(self):
        ctx = {
            "meal_history": [],
            "nutrition_info": [],
            "restaurants": [{"text": "맛집A"}],
        }
        result = format_context(ctx)
        assert "주변 추천 식당" in result
        assert "최근 식사 이력" not in result


class TestBuildPrompt:
    def test_includes_system(self):
        messages = build_prompt("안녕", {}, history=None)
        assert messages[0]["role"] == "system"
        assert "런치 코치" in messages[0]["content"]

    def test_includes_user_query(self):
        messages = build_prompt("오늘 점심 추천", {}, history=None)
        assert messages[-1]["role"] == "user"
        assert "오늘 점심 추천" in messages[-1]["content"]

    def test_includes_history(self):
        history = [
            {"role": "user", "content": "이전 질문"},
            {"role": "assistant", "content": "이전 답변"},
        ]
        messages = build_prompt("현재 질문", {}, history=history)
        # system + history(2) + current user = 4
        assert len(messages) == 4
        assert messages[1]["content"] == "이전 질문"
        assert messages[2]["content"] == "이전 답변"

    def test_no_history(self):
        messages = build_prompt("Q", {}, history=None)
        assert len(messages) == 2

    def test_context_in_user_message(self):
        ctx = {
            "meal_history": [],
            "nutrition_info": [],
            "restaurants": [{"text": "맛집A"}],
        }
        messages = build_prompt("질문", ctx)
        assert "맛집A" in messages[-1]["content"]
        assert "질문" in messages[-1]["content"]


class TestSystemPrompt:
    def test_contains_required_sections(self):
        assert "런치 코치" in SYSTEM_PROMPT
        assert "환각 방지" in SYSTEM_PROMPT
        assert "json" in SYSTEM_PROMPT.lower()
        assert "recommendations" in SYSTEM_PROMPT
