"""
Mini SQLite 공용 DB 접근 레이어.

모든 nlp_mvp 모듈은 여기서 제공하는 `get_session()` 컨텍스트 매니저와
`get_engine()` 을 통해 DB 에 접근한다.

설계 원칙
---------
- **단일 엔진 재사용**: `create_engine()` 은 프로세스당 1회만
- **컨텍스트 매니저 패턴**: 세션 누수 방지
- **Reflect 지원**: 기존 Mini 테이블(`restaurants`, `meal_history`, ...) 자동 매핑
- **In-memory 오버라이드**: 테스트에서 `:memory:` 엔진 주입 가능
- **환경 변수 주도**: `MINI_DB_PATH` 로 실제 DB 파일 경로 제어

사용 예
-------
    from nlp_mvp.shared.db import get_session, get_engine

    with get_session() as session:
        rows = session.execute(text("SELECT * FROM restaurants LIMIT 5")).fetchall()
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from nlp_mvp.shared.logger import get_logger

# =============================================================================
# 환경 변수 로드 (상위 → 하위 순, 하위가 우선)
# =============================================================================
_THIS_FILE = Path(__file__).resolve()
_NLP_ROOT = _THIS_FILE.parent.parent.parent              # Mini/NLP/
_MINI_ROOT = _NLP_ROOT.parent                          # Mini/

# 1. 공용 Mini/.env
_parent_env = _MINI_ROOT / ".env"
if _parent_env.exists():
    load_dotenv(_parent_env, override=False)

# 2. NLP 로컬 override
_local_env = _NLP_ROOT / ".env"
if _local_env.exists():
    load_dotenv(_local_env, override=True)

DEFAULT_DB_PATH = "../lunch-optimizer/database/mini.db"
logger = get_logger("nlp_mvp.shared.db")


# =============================================================================
# 모듈 전역 (싱글톤)
# =============================================================================
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None
_metadata: Optional[MetaData] = None


# =============================================================================
# 엔진 / 세션 팩토리
# =============================================================================
def _resolve_db_url(db_path: Optional[str] = None) -> str:
    """
    SQLite URL 을 결정한다.

    우선순위:
    1. 인자 `db_path`
    2. 환경변수 `MINI_DB_PATH`
    3. 기본값 `../lunch-optimizer/database/mini.db` (Mini/NLP 기준)

    상대 경로는 **Mini/NLP/** 디렉토리를 기준으로 해석된다.

    특수값:
    - ":memory:" → `sqlite:///:memory:`
    """
    if db_path is None:
        db_path = os.getenv("MINI_DB_PATH", DEFAULT_DB_PATH)

    if db_path == ":memory:":
        return "sqlite:///:memory:"

    path_obj = Path(db_path).expanduser()
    if not path_obj.is_absolute():
        # Mini/NLP/ 기준 상대 경로로 해석
        path_obj = (_NLP_ROOT / path_obj).resolve()
    else:
        path_obj = path_obj.resolve()
    return f"sqlite:///{path_obj}"


def get_engine(db_path: Optional[str] = None, echo: bool = False) -> Engine:
    """
    프로세스 전역 SQLAlchemy Engine 반환 (싱글톤).

    Args:
        db_path: 최초 호출 시 지정 가능. 이후 호출은 무시된다.
        echo: True 면 SQL 을 콘솔에 출력 (디버깅용).
    """
    global _engine
    if _engine is None:
        url = _resolve_db_url(db_path)
        logger.info(f"Creating SQLAlchemy engine: {url}")
        _engine = create_engine(
            url,
            echo=echo,
            future=True,
            connect_args={"check_same_thread": False},  # SQLite + 스레드
        )
    return _engine


def get_sessionmaker() -> sessionmaker:
    """Session 팩토리 반환 (싱글톤)."""
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
    세션 컨텍스트 매니저.

    사용 예:
        with get_session() as session:
            session.execute(...)
            session.commit()

    예외 발생 시 자동 rollback. 항상 close().
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


# =============================================================================
# 메타데이터 (Reflect)
# =============================================================================
def get_metadata(refresh: bool = False) -> MetaData:
    """
    Mini 기존 테이블을 reflect 한 MetaData 반환.

    Args:
        refresh: True 면 캐시 무시하고 재반영 (스키마 변경 후).

    사용 예:
        md = get_metadata()
        restaurants = md.tables["restaurants"]
        print(restaurants.columns.keys())
    """
    global _metadata
    if _metadata is None or refresh:
        _metadata = MetaData()
        try:
            _metadata.reflect(bind=get_engine())
            logger.info(
                f"Reflected {len(_metadata.tables)} tables: "
                f"{sorted(_metadata.tables.keys())}"
            )
        except Exception as e:
            logger.warning(f"Reflect failed (DB may not exist yet): {e}")
    return _metadata


def table_exists(table_name: str) -> bool:
    """테이블 존재 여부 확인."""
    try:
        with get_engine().connect() as conn:
            row = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
                {"n": table_name},
            ).fetchone()
            return row is not None
    except Exception as e:
        logger.warning(f"table_exists({table_name}) failed: {e}")
        return False


# =============================================================================
# 테스트 지원 (엔진 주입·리셋)
# =============================================================================
def override_engine(engine: Engine) -> None:
    """
    테스트 전용: 전역 엔진을 외부 엔진으로 교체.

    주의: 프로덕션 코드에서는 사용 금지.
    """
    global _engine, _SessionLocal, _metadata
    _engine = engine
    _SessionLocal = None
    _metadata = None
    logger.info("Engine overridden (test mode)")


def reset_engine() -> None:
    """전역 엔진·세션·메타데이터 초기화 (테스트 정리용)."""
    global _engine, _SessionLocal, _metadata
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
    _engine = None
    _SessionLocal = None
    _metadata = None


__all__ = [
    "get_engine",
    "get_sessionmaker",
    "get_session",
    "get_metadata",
    "table_exists",
    "override_engine",
    "reset_engine",
]
