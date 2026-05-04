"""prompt.py 단위 테스트."""
from __future__ import annotations

from nlp_mvp.nlg_report.fact_extractor import WeeklyFacts
from nlp_mvp.nlg_report.prompt import (
    REPORT_SYSTEM_PROMPT,
    build_report_prompt,
    format_facts_for_user,
)


def _make_facts(meal_count=5, **overrides) -> WeeklyFacts:
    base = dict(
        week_label="2026년 4월 1주차",
        week_start="2026-04-06",
        week_end="2026-04-13",
        user_id=1,
        user_name="홍길동",
        meal_count=meal_count,
        total_calories=3500,
        avg_calories_per_meal=700,
        avg_protein=25,
        avg_carbs=90,
        avg_fat=30,
        avg_sodium=1500,
        target_calories=2000,
        target_protein=60,
    )
    base.update(overrides)
    return WeeklyFacts(**base)


class TestSystemPrompt:
    def test_contains_required_sections(self):
        assert "런치 코치" in REPORT_SYSTEM_PROMPT
        assert "이모지" in REPORT_SYSTEM_PROMPT
        assert "금기" in REPORT_SYSTEM_PROMPT


class TestFormatFactsForUser:
    def test_normal(self):
        facts = _make_facts(lack=["단백질"], excess=["나트륨"])
        text = format_facts_for_user(facts)
        assert "홍길동" in text
        assert "5회" in text
        assert "단백질" in text
        assert "나트륨" in text

    def test_empty_week(self):
        facts = _make_facts(meal_count=0)
        text = format_facts_for_user(facts)
        assert "기록이 없습니다" in text
        assert "홍길동" in text

    def test_sparse_week(self):
        facts = _make_facts(meal_count=2)
        text = format_facts_for_user(facts)
        assert "2건" in text
        assert "기록" in text

    def test_with_best_day(self):
        facts = _make_facts(
            best_day={
                "date": "2026-04-07",
                "menu": "샐러드",
                "balance_score": 0.9,
                "reason": "균형",
            }
        )
        text = format_facts_for_user(facts)
        assert "샐러드" in text

    def test_with_satisfaction(self):
        facts = _make_facts(avg_satisfaction=4.2)
        text = format_facts_for_user(facts)
        assert "4.2" in text

    def test_with_categories(self):
        facts = _make_facts(top_categories=[("한식", 3), ("양식", 2)])
        text = format_facts_for_user(facts)
        assert "한식" in text


class TestBuildReportPrompt:
    def test_two_messages(self):
        facts = _make_facts()
        messages = build_report_prompt(facts)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_system_first(self):
        facts = _make_facts()
        messages = build_report_prompt(facts)
        assert "런치 코치" in messages[0]["content"]
