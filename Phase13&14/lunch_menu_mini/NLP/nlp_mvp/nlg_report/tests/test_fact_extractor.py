"""fact_extractor.py 단위 테스트."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.nlg_report.fact_extractor import (
    DEFAULT_TARGETS,
    day_balance_score,
    detect_lack_excess,
    extract_weekly_facts,
    format_week_label,
    get_week_start,
)
from nlp_mvp.shared.db import override_engine, reset_engine


@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, "
            "target_calories REAL, target_protein REAL)"
        ))
        conn.execute(text("INSERT INTO users VALUES (1, 'Test', 2000, 60)"))
        conn.execute(text("""
            CREATE TABLE meal_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                restaurant_id INTEGER,
                meal_date DATE,
                menu TEXT,
                normalized_menu_id TEXT,
                satisfaction INTEGER
            )
        """))
        conn.execute(text(
            "CREATE TABLE nutrition_info (id TEXT PRIMARY KEY, food_name TEXT, "
            "calories REAL, protein REAL, carbs REAL, fat REAL, sodium REAL)"
        ))
        conn.execute(text("CREATE TABLE restaurants (id INTEGER PRIMARY KEY, category TEXT)"))
    return engine


@pytest.fixture(autouse=True)
def _reset(test_engine):
    override_engine(test_engine)
    yield
    reset_engine()


# =============================================================================
# 주차 유틸
# =============================================================================
class TestWeekUtils:
    def test_format_label(self):
        label = format_week_label(date(2026, 4, 6))
        assert "2026" in label
        assert "4월" in label

    def test_get_week_start_monday(self):
        # 2026-04-08 is Wednesday
        ws = get_week_start(date(2026, 4, 8))
        assert ws.weekday() == 0  # Monday
        assert ws == date(2026, 4, 6)

    def test_already_monday(self):
        ws = get_week_start(date(2026, 4, 6))
        assert ws == date(2026, 4, 6)


# =============================================================================
# 균형 점수
# =============================================================================
class TestBalanceScore:
    def test_perfect(self):
        row = pd.Series({"calories": 2000, "protein": 60, "carbs": 300, "fat": 55})
        assert day_balance_score(row) > 0.95

    def test_poor(self):
        row = pd.Series({"calories": 500, "protein": 10, "carbs": 50, "fat": 5})
        assert day_balance_score(row) < 0.5

    def test_zero(self):
        row = pd.Series({"calories": 0, "protein": 0, "carbs": 0, "fat": 0})
        assert day_balance_score(row) == 0.0


# =============================================================================
# 부족/과다 판정
# =============================================================================
class TestDetectLackExcess:
    def test_low_protein(self):
        avg = {"calories": 650, "protein": 10, "sodium": 500, "fat": 20}
        targets = {"target_calories": 650, "target_protein": 20}
        lack, excess = detect_lack_excess(avg, targets)
        assert "단백질" in lack

    def test_high_sodium(self):
        avg = {"calories": 650, "protein": 30, "sodium": 3000, "fat": 20}
        targets = {"target_calories": 650, "target_protein": 20}
        lack, excess = detect_lack_excess(avg, targets)
        assert "나트륨" in excess

    def test_high_calories(self):
        avg = {"calories": 2000, "protein": 30, "sodium": 500, "fat": 20}
        targets = {"target_calories": 650, "target_protein": 20}
        lack, excess = detect_lack_excess(avg, targets)
        assert "칼로리" in excess

    def test_balanced(self):
        avg = {"calories": 650, "protein": 25, "sodium": 1000, "fat": 20}
        targets = {"target_calories": 650, "target_protein": 20}
        lack, excess = detect_lack_excess(avg, targets)
        assert lack == []
        assert excess == []


# =============================================================================
# extract_weekly_facts
# =============================================================================
class TestExtractWeeklyFacts:
    def test_empty_week(self):
        facts = extract_weekly_facts(user_id=1, week_start=date(2026, 4, 6))
        assert facts.is_empty()
        assert facts.meal_count == 0
        assert facts.user_name == "Test"
        assert facts.target_calories == 2000

    def test_with_meals(self, test_engine):
        with test_engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO nutrition_info VALUES "
                "('kimchi', '김치찌개', 650, 22, 80, 25, 1300)"
            ))
            conn.execute(text("""
                INSERT INTO meal_history
                    (id, user_id, meal_date, menu, normalized_menu_id, satisfaction)
                VALUES
                    (1, 1, '2026-04-06', '김치찌개', 'kimchi', 5),
                    (2, 1, '2026-04-07', '김치찌개', 'kimchi', 4)
            """))
        facts = extract_weekly_facts(user_id=1, week_start=date(2026, 4, 6))
        assert facts.meal_count == 2
        assert facts.avg_protein == 22.0
        assert facts.avg_calories_per_meal == 650.0
        assert facts.has_nutrition_data is True
        assert facts.avg_satisfaction == 4.5
        assert facts.best_day is not None

    def test_sparse(self, test_engine):
        with test_engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO nutrition_info VALUES ('a', '메뉴', 500, 20, 60, 15, 800)"
            ))
            conn.execute(text(
                "INSERT INTO meal_history (id, user_id, meal_date, menu, normalized_menu_id) "
                "VALUES (1, 1, '2026-04-06', '메뉴', 'a')"
            ))
        facts = extract_weekly_facts(user_id=1, week_start=date(2026, 4, 6))
        assert facts.is_sparse()

    def test_unknown_user(self):
        facts = extract_weekly_facts(user_id=999, week_start=date(2026, 4, 6))
        assert facts.user_name == "사용자999"
        assert facts.target_calories == DEFAULT_TARGETS["calories_per_day"]
