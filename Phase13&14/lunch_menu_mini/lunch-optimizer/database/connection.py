"""
SQLAlchemy 엔진·세션 팩토리.

모든 DB 접근은 이 모듈의 `get_session()` 컨텍스트 매니저를 사용합니다.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings

# =============================================================================
# 엔진 싱글톤
# =============================================================================
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def _ensure_sqlite_dir() -> None:
    """SQLite 파일 경로의 디렉토리를 미리 생성."""
    path = settings.db.sqlite_path
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    """프로세스 전역 SQLAlchemy Engine."""
    global _engine
    if _engine is None:
        _ensure_sqlite_dir()
        _engine = create_engine(
            settings.db.url,
            echo=settings.db.echo,
            future=True,
            connect_args={"check_same_thread": False}
            if settings.db.url.startswith("sqlite")
            else {},
        )
    return _engine


def get_sessionmaker() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            future=True,
        )
    return _SessionLocal


@contextmanager
def get_session() -> Iterator[Session]:
    """
    세션 컨텍스트 매니저. 예외 시 자동 rollback, 항상 close.

    사용 예:
        with get_session() as session:
            session.execute(...)
            session.commit()
    """
    SessionLocal = get_sessionmaker()
    session: Session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_schema() -> None:
    """
    models.Base 의 모든 테이블을 생성한다 (존재하지 않는 경우).
    마이그레이션 도구 없이 MVP 단계용.
    """
    from database.models import Base  # 지연 import (순환 방지)

    engine = get_engine()
    Base.metadata.create_all(engine)
    ensure_auth_schema(engine)
    ensure_nutrition_v1_schema(engine)


def _sqlite_columns(conn, table_name: str) -> dict[str, tuple]:
    return {
        row[1]: row
        for row in conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    }


def _add_column_if_missing(conn, table_name: str, column_name: str, ddl: str) -> None:
    columns = _sqlite_columns(conn, table_name)
    if column_name not in columns:
        conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def ensure_auth_schema(engine: Engine | None = None) -> None:
    """
    Phase 13&14 인증/RBAC에 필요한 SQLite users 컬럼을 보강한다.

    기존 데모 DB는 게스트 사용자 스키마로 생성되어 `email`, `password_hash`,
    `role` 컬럼이 없을 수 있다. `create_all()`은 기존 테이블을 변경하지
    않으므로 앱 시작 시 멱등적으로 누락 컬럼과 인덱스를 추가한다.
    """
    engine = engine or get_engine()
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        ).fetchone()
        if not exists:
            return

        _add_column_if_missing(conn, "users", "email", "email VARCHAR(120)")
        _add_column_if_missing(
            conn, "users", "password_hash", "password_hash VARCHAR(255)"
        )
        _add_column_if_missing(
            conn, "users", "role", "role VARCHAR(20) NOT NULL DEFAULT 'user'"
        )
        _add_column_if_missing(conn, "users", "updated_at", "updated_at DATETIME")
        _add_column_if_missing(conn, "users", "last_login_at", "last_login_at DATETIME")
        conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email)")
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_users_role ON users(role)")
        conn.exec_driver_sql(
            "UPDATE users SET updated_at = COALESCE(updated_at, created_at)"
        )


def _rebuild_meal_history_nullable_restaurant(conn) -> None:
    columns = _sqlite_columns(conn, "meal_history")
    target_columns = [
        "id",
        "user_id",
        "restaurant_id",
        "meal_date",
        "menu_name",
        "calories",
        "carbs",
        "protein",
        "fat",
        "sugar",
        "sodium",
        "satisfaction",
        "raw_text",
        "meal_type",
        "parsed_items_json",
        "nutrition_source",
        "match_confidence",
        "needs_review",
        "restaurant_name_snapshot",
        "restaurant_place_url",
        "created_at",
        "updated_at",
    ]
    backup = "meal_history_v0_backup"
    conn.exec_driver_sql(f"DROP TABLE IF EXISTS {backup}")
    conn.exec_driver_sql(f"ALTER TABLE meal_history RENAME TO {backup}")
    conn.exec_driver_sql("""
        CREATE TABLE meal_history (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(50) NOT NULL,
            restaurant_id VARCHAR(64),
            meal_date DATE NOT NULL,
            menu_name VARCHAR(100),
            calories FLOAT,
            carbs FLOAT,
            protein FLOAT,
            fat FLOAT,
            sugar FLOAT,
            sodium FLOAT,
            satisfaction INTEGER,
            raw_text TEXT,
            meal_type VARCHAR(20),
            parsed_items_json TEXT,
            nutrition_source VARCHAR(50),
            match_confidence FLOAT,
            needs_review BOOLEAN NOT NULL DEFAULT 0,
            restaurant_name_snapshot VARCHAR(100),
            restaurant_place_url VARCHAR(300),
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    select_exprs = []
    for column in target_columns:
        if column in columns:
            select_exprs.append(column)
        elif column == "needs_review":
            select_exprs.append("0 AS needs_review")
        elif column in ("created_at", "updated_at"):
            select_exprs.append("CURRENT_TIMESTAMP")
        else:
            select_exprs.append(f"NULL AS {column}")
    conn.exec_driver_sql(
        f"""
        INSERT INTO meal_history ({", ".join(target_columns)})
        SELECT {", ".join(select_exprs)}
        FROM {backup}
        """
    )
    conn.exec_driver_sql(f"DROP TABLE {backup}")


def ensure_nutrition_v1_schema(engine: Engine | None = None) -> None:
    """
    v1.0 자연어 식단 기록에 필요한 SQLite 스키마를 보강한다.

    SQLAlchemy `create_all()`은 기존 테이블의 누락 컬럼이나 nullable 제약을
    변경하지 않으므로, SQLite MVP 환경에서는 시작 시 멱등 보강을 수행한다.
    """
    engine = engine or get_engine()
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='meal_history'")
        ).fetchone()
        if exists:
            columns = _sqlite_columns(conn, "meal_history")
            restaurant_col = columns.get("restaurant_id")
            if restaurant_col is not None and int(restaurant_col[3] or 0) == 1:
                _rebuild_meal_history_nullable_restaurant(conn)

            _add_column_if_missing(conn, "meal_history", "raw_text", "raw_text TEXT")
            _add_column_if_missing(conn, "meal_history", "meal_type", "meal_type VARCHAR(20)")
            _add_column_if_missing(
                conn, "meal_history", "parsed_items_json", "parsed_items_json TEXT"
            )
            _add_column_if_missing(
                conn, "meal_history", "nutrition_source", "nutrition_source VARCHAR(50)"
            )
            _add_column_if_missing(
                conn, "meal_history", "match_confidence", "match_confidence FLOAT"
            )
            _add_column_if_missing(
                conn,
                "meal_history",
                "needs_review",
                "needs_review BOOLEAN NOT NULL DEFAULT 0",
            )
            _add_column_if_missing(
                conn,
                "meal_history",
                "restaurant_name_snapshot",
                "restaurant_name_snapshot VARCHAR(100)",
            )
            _add_column_if_missing(
                conn,
                "meal_history",
                "restaurant_place_url",
                "restaurant_place_url VARCHAR(300)",
            )
            _add_column_if_missing(
                conn,
                "meal_history",
                "updated_at",
                "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            )

        # restaurants 테이블 — 영업 시간대 컬럼 (헤비 옵션)
        rest_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants'")
        ).fetchone()
        if rest_exists:
            _add_column_if_missing(
                conn,
                "restaurants",
                "serves_breakfast",
                "serves_breakfast BOOLEAN NOT NULL DEFAULT 1",
            )
            _add_column_if_missing(
                conn,
                "restaurants",
                "serves_lunch",
                "serves_lunch BOOLEAN NOT NULL DEFAULT 1",
            )
            _add_column_if_missing(
                conn,
                "restaurants",
                "serves_dinner",
                "serves_dinner BOOLEAN NOT NULL DEFAULT 1",
            )

        conn.exec_driver_sql("""
            CREATE TABLE IF NOT EXISTS meal_items (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                meal_history_id INTEGER NOT NULL,
                raw_name VARCHAR(100) NOT NULL,
                normalized_name VARCHAR(100),
                food_code VARCHAR(50),
                quantity FLOAT NOT NULL DEFAULT 1.0,
                unit VARCHAR(20) NOT NULL DEFAULT 'serving',
                serving_size FLOAT,
                calories FLOAT,
                carbs FLOAT,
                protein FLOAT,
                fat FLOAT,
                sugar FLOAT,
                sodium FLOAT,
                source VARCHAR(50) NOT NULL DEFAULT 'unverified',
                match_type VARCHAR(30) NOT NULL DEFAULT 'unverified',
                match_confidence FLOAT,
                needs_review BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(meal_history_id) REFERENCES meal_history(id) ON DELETE CASCADE
            )
        """)
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_meal_user_date ON meal_history(user_id, meal_date)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_meal_items_meal ON meal_items(meal_history_id)"
        )


def reset_engine() -> None:
    """테스트 정리용: 전역 엔진·세션 팩토리 초기화."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
