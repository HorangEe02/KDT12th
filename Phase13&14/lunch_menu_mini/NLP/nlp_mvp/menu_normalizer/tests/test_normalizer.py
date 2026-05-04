"""normalizer.py 단위 테스트 (임베딩 비활성화)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.menu_normalizer.loader import SyntheticMenuLoader
from nlp_mvp.menu_normalizer.normalizer import (
    MenuNormalizer,
    NormalizationResult,
    ensure_schema,
    run_batch_normalization,
)
from nlp_mvp.shared.db import override_engine, reset_engine


@pytest.fixture(scope="module")
def normalizer():
    return MenuNormalizer(
        loader=SyntheticMenuLoader(),
        enable_embedding=False,
    )


# =============================================================================
# 매칭 단계별
# =============================================================================
class TestRuleStage:
    def test_exact(self, normalizer):
        r = normalizer.normalize("김치찌개")
        assert r.method == "rule"
        assert r.confidence == 1.0
        assert r.matched_id == "kimchi_jjigae"

    def test_bracket(self, normalizer):
        r = normalizer.normalize("김치찌개(大)")
        assert r.method == "rule"
        assert r.matched_id == "kimchi_jjigae"

    def test_synonym(self, normalizer):
        r = normalizer.normalize("김찌")
        assert r.matched_name == "김치찌개"

    def test_size_suffix(self, normalizer):
        r = normalizer.normalize("짬뽕 특")
        assert r.method == "rule"
        assert r.matched_id == "jjamppong"


class TestLevenshteinStage:
    def test_typo(self, normalizer):
        # "김치찌게" → "김치찌개" (1 char diff)
        r = normalizer.normalize("김치찌게")
        assert r.method == "levenshtein"
        assert r.matched_id == "kimchi_jjigae"


class TestNoMatch:
    def test_completely_unrelated(self, normalizer):
        r = normalizer.normalize("외계어쿠키")
        assert r.matched_id is None
        assert r.method == "none"


class TestErrorHandling:
    def test_none_input(self, normalizer):
        r = normalizer.normalize(None)
        assert r.method in ("none", "error")
        assert r.matched_id is None

    def test_empty_string(self, normalizer):
        r = normalizer.normalize("")
        assert r.matched_id is None


class TestBatch:
    def test_normalize_batch(self, normalizer):
        results = normalizer.normalize_batch(["김치찌개", "짜장면", "외계어"])
        assert len(results) == 3
        assert all(isinstance(r, NormalizationResult) for r in results)


# =============================================================================
# DB 적재 + 배치 파이프라인
# =============================================================================
@pytest.fixture
def in_memory_db():
    """restaurants 테이블만 가진 in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE restaurants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                menu_type TEXT
            )
        """))
        conn.execute(text(
            "INSERT INTO restaurants (id, name, menu_type) VALUES "
            "('r1', '식당1', '김치찌개'), "
            "('r2', '식당2', '짜장면'), "
            "('r3', '식당3', '돈가스(中)')"
        ))
    override_engine(engine)
    yield engine
    reset_engine()


class TestEnsureSchema:
    def test_creates_table(self, in_memory_db):
        ensure_schema()
        with in_memory_db.connect() as conn:
            tables = {
                row[0] for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
        assert "menu_normalization" in tables

    def test_idempotent(self, in_memory_db):
        ensure_schema()
        ensure_schema()  # 재실행 OK


class TestRunBatchNormalization:
    def test_dry_run(self, in_memory_db, normalizer):
        stats = run_batch_normalization(
            source_query="SELECT DISTINCT menu_type FROM restaurants",
            source_table="restaurants.menu_type",
            dry_run=True,
            normalizer=normalizer,
        )
        assert stats["processed"] == 3
        # menu_normalization 에 아무것도 안 들어감
        with in_memory_db.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM menu_normalization")).scalar()
        assert count == 0

    def test_actual_write(self, in_memory_db, normalizer):
        stats = run_batch_normalization(
            source_query="SELECT DISTINCT menu_type FROM restaurants",
            source_table="restaurants.menu_type",
            dry_run=False,
            normalizer=normalizer,
        )
        assert stats["processed"] == 3
        with in_memory_db.connect() as conn:
            rows = conn.execute(
                text("SELECT raw_name, normalized_id FROM menu_normalization")
            ).fetchall()
        assert len(rows) == 3
        names = {r[0]: r[1] for r in rows}
        assert names["김치찌개"] == "kimchi_jjigae"
        assert names["짜장면"] == "jjajangmyeon"
