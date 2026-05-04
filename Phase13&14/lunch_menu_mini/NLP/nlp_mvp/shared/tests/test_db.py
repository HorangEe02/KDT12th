"""nlp_mvp.shared.db 스모크 테스트."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.shared import db as db_module
from nlp_mvp.shared.db import (
    get_session,
    get_engine,
    get_metadata,
    table_exists,
    override_engine,
    reset_engine,
    _resolve_db_url,
)


@pytest.fixture(autouse=True)
def _reset_db_state():
    """각 테스트마다 엔진 초기화."""
    reset_engine()
    yield
    reset_engine()


@pytest.fixture
def in_memory_engine():
    """테스트용 in-memory SQLite 엔진."""
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE restaurants (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """))
        conn.execute(text("INSERT INTO restaurants (id, name) VALUES (1, 'Test')"))
        conn.execute(text("INSERT INTO restaurants (id, name) VALUES (2, 'Demo')"))
    return engine


class TestResolveDbUrl:
    def test_explicit_path(self):
        url = _resolve_db_url("/tmp/test.db")
        assert url.startswith("sqlite:///")
        assert "test.db" in url

    def test_memory(self):
        assert _resolve_db_url(":memory:") == "sqlite:///:memory:"

    def test_env_default(self, monkeypatch):
        monkeypatch.setenv("MINI_DB_PATH", ":memory:")
        assert _resolve_db_url(None) == "sqlite:///:memory:"


class TestOverrideEngine:
    def test_injection(self, in_memory_engine):
        override_engine(in_memory_engine)
        assert get_engine() is in_memory_engine

    def test_session_uses_overridden_engine(self, in_memory_engine):
        override_engine(in_memory_engine)
        with get_session() as session:
            rows = session.execute(text("SELECT name FROM restaurants ORDER BY id")).fetchall()
            assert [r[0] for r in rows] == ["Test", "Demo"]


class TestGetSession:
    def test_commit_persists(self, in_memory_engine):
        override_engine(in_memory_engine)
        with get_session() as session:
            session.execute(text("INSERT INTO restaurants (id, name) VALUES (3, 'New')"))
            session.commit()
        with get_session() as session:
            row = session.execute(
                text("SELECT name FROM restaurants WHERE id=3")
            ).fetchone()
            assert row[0] == "New"

    def test_exception_rolls_back(self, in_memory_engine):
        override_engine(in_memory_engine)
        with pytest.raises(RuntimeError):
            with get_session() as session:
                session.execute(text("INSERT INTO restaurants (id, name) VALUES (99, 'X')"))
                raise RuntimeError("simulated")
        # 롤백되어 99 는 없어야
        with get_session() as session:
            row = session.execute(
                text("SELECT name FROM restaurants WHERE id=99")
            ).fetchone()
            assert row is None


class TestTableExists:
    def test_existing(self, in_memory_engine):
        override_engine(in_memory_engine)
        assert table_exists("restaurants") is True

    def test_missing(self, in_memory_engine):
        override_engine(in_memory_engine)
        assert table_exists("nonexistent_table") is False


class TestGetMetadata:
    def test_reflects_tables(self, in_memory_engine):
        override_engine(in_memory_engine)
        md = get_metadata(refresh=True)
        assert "restaurants" in md.tables
        cols = md.tables["restaurants"].columns.keys()
        assert "id" in cols
        assert "name" in cols
