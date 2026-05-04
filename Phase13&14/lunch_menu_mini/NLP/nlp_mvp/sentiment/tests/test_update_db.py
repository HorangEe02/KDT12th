"""update_db.py 단위 테스트."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.sentiment.update_db import (
    REQUIRED_COLUMNS, ensure_schema, run_sentiment_update
)
from nlp_mvp.shared.db import override_engine, reset_engine


# =============================================================================
# 픽스처: 최소 restaurants 테이블을 가진 in-memory DB
# =============================================================================
@pytest.fixture
def minimal_db(monkeypatch):
    """
    NLP 가 접근할 수 있는 최소한의 restaurants 테이블을 in-memory 로 구축.
    """
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE restaurants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        """))
        conn.execute(text(
            "INSERT INTO restaurants (id, name) VALUES "
            "('r1', '테스트식당1'), "
            "('r2', '테스트식당2'), "
            "('r3', '테스트식당3')"
        ))

    override_engine(engine)
    yield engine
    reset_engine()


# =============================================================================
# ensure_schema
# =============================================================================
class TestEnsureSchema:
    def test_adds_all_columns(self, minimal_db):
        ensure_schema(minimal_db)
        with minimal_db.connect() as conn:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(restaurants)"))}
        for required in REQUIRED_COLUMNS:
            assert required in cols

    def test_creates_reviews_table(self, minimal_db):
        ensure_schema(minimal_db)
        with minimal_db.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
        assert "reviews" in tables

    def test_idempotent(self, minimal_db):
        """두 번 호출해도 에러 없음."""
        ensure_schema(minimal_db)
        ensure_schema(minimal_db)  # 재실행
        with minimal_db.connect() as conn:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(restaurants)"))}
        assert "sentiment_score" in cols

    def test_raises_when_restaurants_missing(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        override_engine(engine)
        try:
            with pytest.raises(RuntimeError, match="restaurants table not found"):
                ensure_schema(engine)
        finally:
            reset_engine()


# =============================================================================
# run_sentiment_update
# =============================================================================
class TestRunSentimentUpdate:
    def test_dry_run_skips_model(self, minimal_db):
        """transformers 없이도 skip_model_load=True 로 dry_run 가능."""
        stats = run_sentiment_update(
            limit=3,
            min_reviews=5,
            dry_run=True,
            source="synthetic",
            skip_model_load=True,
        )
        assert stats["processed"] == 3
        assert stats["errors"] == 0
        # dry_run 이므로 실제 DB 변경 없음
        with minimal_db.connect() as conn:
            scores = conn.execute(
                text("SELECT sentiment_score FROM restaurants")
            ).fetchall()
        assert all(row[0] is None for row in scores)

    def test_actual_write_without_model(self, minimal_db):
        """skip_model_load=True 로 실제 쓰기 (neutral 시뮬레이션)."""
        stats = run_sentiment_update(
            limit=3,
            min_reviews=5,
            dry_run=False,
            source="synthetic",
            skip_model_load=True,
        )
        assert stats["updated"] == 3

        with minimal_db.connect() as conn:
            rows = conn.execute(text("""
                SELECT id, sentiment_score, sentiment_sample_size
                FROM restaurants
            """)).fetchall()
        for row in rows:
            assert row[1] is not None
            assert row[2] > 0
            # neutral 시뮬레이션: score = 0
            assert row[1] == 0

    def test_reviews_inserted(self, minimal_db):
        run_sentiment_update(
            limit=3, min_reviews=5, dry_run=False,
            source="synthetic", skip_model_load=True,
        )
        with minimal_db.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM reviews")
            ).scalar()
        assert count > 0

    def test_limit_respected(self, minimal_db):
        stats = run_sentiment_update(
            limit=1, min_reviews=5, dry_run=True,
            source="synthetic", skip_model_load=True,
        )
        assert stats["processed"] == 1
