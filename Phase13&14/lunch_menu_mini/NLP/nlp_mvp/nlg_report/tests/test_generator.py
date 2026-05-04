"""generator.py 단위 테스트 — Ollama 모킹 + in-memory DB."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.nlg_report.fact_extractor import WeeklyFacts
from nlp_mvp.nlg_report.generator import (
    ReportGenerator,
    ReportResult,
    ensure_schema,
    minimal_message,
    render_template,
    validate_report,
)
from nlp_mvp.shared.db import override_engine, reset_engine


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


# =============================================================================
# validate_report
# =============================================================================
class TestValidate:
    def test_valid(self):
        text_str = (
            "이번 주 정말 수고 많으셨어요 💪 단백질도 잘 챙기셨고 균형 잡힌 식단이었어요 😊 "
            "내일은 샐러드와 함께 가벼운 한 끼 어떠세요 ✨"
        )
        r = validate_report(text_str)
        assert r["valid"] is True
        assert r["emoji_count"] >= 2

    def test_too_short(self):
        r = validate_report("짧음")
        assert not r["valid"]
        assert any("too_short" in i for i in r["issues"])

    def test_too_long(self):
        r = validate_report("가" * 700 + " 💪 😊 ✨")
        assert not r["valid"]
        assert any("too_long" in i for i in r["issues"])

    def test_no_emoji(self):
        r = validate_report("이번 주 50자 이상 충분한 길이의 리포트입니다 아주 길게 작성해봅니다 정말로요 진짜")
        assert not r["valid"]
        assert "no_emoji" in r["issues"]

    def test_forbidden_word(self):
        r = validate_report(
            "이번 주 식단이 잘못되었습니다 💪 😊 ✨ 충분히 긴 텍스트로 50자 이상 작성합니다."
        )
        assert not r["valid"]
        assert any("forbidden" in i for i in r["issues"])


# =============================================================================
# render_template / minimal_message
# =============================================================================
class TestRenderTemplate:
    def test_empty_facts(self):
        facts = _make_facts(meal_count=0)
        text_out = render_template(facts)
        assert "기록" in text_out
        assert "홍길동" in text_out

    def test_with_lack(self):
        facts = _make_facts(lack=["단백질"])
        text_out = render_template(facts)
        assert "단백질" in text_out

    def test_balanced(self):
        facts = _make_facts(lack=[])
        text_out = render_template(facts)
        assert "괜찮" in text_out or "균형" in text_out


class TestMinimalMessage:
    def test_basic(self):
        facts = _make_facts()
        msg = minimal_message(facts)
        assert "홍길동" in msg
        assert "5" in msg


# =============================================================================
# ReportGenerator (모킹)
# =============================================================================
@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, "
            "target_calories REAL, target_protein REAL)"
        ))
        conn.execute(text("INSERT INTO users VALUES (1, '홍길동', 2000, 60)"))
        conn.execute(text("""
            CREATE TABLE meal_history (
                id INTEGER PRIMARY KEY, user_id INTEGER, restaurant_id INTEGER,
                meal_date DATE, menu TEXT, normalized_menu_id TEXT, satisfaction INTEGER
            )
        """))
        conn.execute(text(
            "CREATE TABLE nutrition_info (id TEXT PRIMARY KEY, food_name TEXT, "
            "calories REAL, protein REAL, carbs REAL, fat REAL, sodium REAL)"
        ))
        conn.execute(text("CREATE TABLE restaurants (id INTEGER PRIMARY KEY, category TEXT)"))
        conn.execute(text(
            "INSERT INTO nutrition_info VALUES ('a', '메뉴', 650, 22, 80, 25, 1300)"
        ))
        conn.execute(text("""
            INSERT INTO meal_history (id, user_id, meal_date, menu, normalized_menu_id, satisfaction)
            VALUES (1, 1, '2026-04-06', '메뉴', 'a', 5),
                   (2, 1, '2026-04-07', '메뉴', 'a', 4),
                   (3, 1, '2026-04-08', '메뉴', 'a', 5)
        """))
    override_engine(engine)
    yield engine
    reset_engine()


VALID_LLM_RESPONSE = (
    "이번 주 정말 잘 챙겨드셨어요 💪 단백질도 적절히 보충하셨고 균형 잡힌 한 주였답니다 😊 "
    "내일은 가볍게 샐러드 한 그릇으로 시작해볼까요 ✨"
)


class TestEnsureSchema:
    def test_creates_table(self, in_memory_db):
        ensure_schema()
        with in_memory_db.connect() as conn:
            tables = {
                row[0] for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
        assert "nutrition_reports" in tables

    def test_idempotent(self, in_memory_db):
        ensure_schema()
        ensure_schema()


class TestReportGenerator:
    def test_llm_success(self, in_memory_db):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = VALID_LLM_RESPONSE
        gen = ReportGenerator(ollama_client=mock_ollama)
        result = gen.generate(user_id=1, week_start=date(2026, 4, 6))
        assert isinstance(result, ReportResult)
        assert result.generation_method == "llm"
        assert result.report_id is not None
        assert "💪" in result.nlg_text

    def test_llm_fails_falls_back_to_template(self, in_memory_db):
        mock_ollama = MagicMock()
        mock_ollama.chat.side_effect = RuntimeError("ollama down")
        gen = ReportGenerator(ollama_client=mock_ollama, max_retries=1)
        result = gen.generate(user_id=1, week_start=date(2026, 4, 6))
        assert result.generation_method == "template"
        assert result.nlg_text  # 비어있지 않음

    def test_validation_fail_falls_back(self, in_memory_db):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = "짧음"  # validation 실패
        gen = ReportGenerator(ollama_client=mock_ollama, max_retries=1)
        result = gen.generate(user_id=1, week_start=date(2026, 4, 6))
        assert result.generation_method == "template"

    def test_save_and_fetch(self, in_memory_db):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = VALID_LLM_RESPONSE
        gen = ReportGenerator(ollama_client=mock_ollama)

        r1 = gen.generate(user_id=1, week_start=date(2026, 4, 6))
        assert r1.report_id is not None

        # 캐시 hit
        r2 = gen.get_or_generate(user_id=1, week_start=date(2026, 4, 6))
        assert r2.report_id == r1.report_id
        # ollama 는 첫 호출만 사용되어야 함
        assert mock_ollama.chat.call_count == 1

    def test_no_save(self, in_memory_db):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = VALID_LLM_RESPONSE
        gen = ReportGenerator(ollama_client=mock_ollama)
        result = gen.generate(user_id=1, week_start=date(2026, 4, 6), save=False)
        assert result.report_id is None

    def test_empty_user_uses_template(self, in_memory_db):
        mock_ollama = MagicMock()
        # 빈 주차에 대해 LLM 이 valid response 를 못 만든다고 가정
        mock_ollama.chat.side_effect = RuntimeError("ollama down")
        gen = ReportGenerator(ollama_client=mock_ollama, max_retries=0)
        result = gen.generate(user_id=1, week_start=date(2025, 1, 6))  # 데이터 없는 주
        assert result.generation_method == "template"
        assert result.facts["meal_count"] == 0
