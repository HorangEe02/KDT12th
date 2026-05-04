"""User 테이블에 인증 관련 컬럼을 추가 (idempotent).

SQLAlchemy create_all 은 새 컬럼을 자동 추가하지 않으므로
ALTER TABLE 로 직접 패치. SQLite 는 ADD COLUMN 만 지원 (컬럼 변경/삭제 X).

사용:
    docker exec mini-lunch-api python /tmp/migrate_auth_columns.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/database/mini.db")

# (column_name, definition)
NEW_COLUMNS = [
    ("email", "VARCHAR(120)"),
    ("password_hash", "VARCHAR(255)"),
    ("role", "VARCHAR(20) NOT NULL DEFAULT 'user'"),
    ("updated_at", "DATETIME"),
    ("last_login_at", "DATETIME"),
]


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB 파일 없음: {DB_PATH}", file=sys.stderr)
        return 1

    print(f"DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = existing_columns(conn, "users")
        print(f"기존 컬럼: {sorted(cols)}")

        added = []
        for name, ddl in NEW_COLUMNS:
            if name in cols:
                continue
            sql = f"ALTER TABLE users ADD COLUMN {name} {ddl}"
            print(f"  + {sql}")
            conn.execute(sql)
            added.append(name)

        # 인덱스 추가 (이미 있으면 무시)
        for idx_sql in (
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS ix_users_role ON users(role)",
        ):
            print(f"  + {idx_sql}")
            conn.execute(idx_sql)

        # updated_at 누락 행 보정 (기존 created_at 으로 채움)
        if "updated_at" in added:
            conn.execute(
                "UPDATE users SET updated_at = COALESCE(updated_at, created_at)"
            )

        conn.commit()
        cols_after = existing_columns(conn, "users")
        print(f"\n최종 컬럼: {sorted(cols_after)}")
        if added:
            print(f"\n✅ 추가된 컬럼: {added}")
        else:
            print("\n✅ 변경 사항 없음 (이미 최신)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
