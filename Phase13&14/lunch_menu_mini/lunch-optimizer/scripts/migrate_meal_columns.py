"""영양 자연어 입력 기능을 위한 DB 마이그레이션 (idempotent).

추가:
  - meal_history.raw_text          TEXT
  - meal_history.nutrition_source  VARCHAR(50)
  - meal_history.match_confidence  FLOAT
  - nutrition_info.source          VARCHAR(50) DEFAULT 'unverified'
  - nutrition_info.match_confidence FLOAT
  - meal_items 테이블은 SQLAlchemy create_all() 이 자동 생성

사용:
    docker exec mini-lunch-api python /tmp/migrate_meal_columns.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")


PATCHES = [
    # (table, column, ddl)
    ("meal_history", "raw_text", "TEXT"),
    ("meal_history", "nutrition_source", "VARCHAR(50)"),
    ("meal_history", "match_confidence", "FLOAT"),
    ("nutrition_info", "source", "VARCHAR(50) NOT NULL DEFAULT 'unverified'"),
    ("nutrition_info", "match_confidence", "FLOAT"),
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
        added = []
        for table, column, ddl in PATCHES:
            cols = existing_columns(conn, table)
            if column in cols:
                continue
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"
            print(f"  + {sql}")
            conn.execute(sql)
            added.append((table, column))
        conn.commit()

        # meal_items 테이블 자동 생성은 컨테이너 lifespan 의 init_schema() 가 처리
        # (Base.metadata.create_all)

        print()
        if added:
            print(f"✅ 추가된 컬럼: {added}")
        else:
            print("✅ 변경 사항 없음 (이미 최신)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
