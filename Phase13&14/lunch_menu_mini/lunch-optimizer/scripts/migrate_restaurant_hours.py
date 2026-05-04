"""restaurants 테이블에 영업 시간대 Boolean 컬럼 추가 (idempotent).

추가:
  - serves_breakfast  BOOLEAN NOT NULL DEFAULT 1
  - serves_lunch      BOOLEAN NOT NULL DEFAULT 1
  - serves_dinner     BOOLEAN NOT NULL DEFAULT 1

기본값 1(허용) — ETL/사용자 큐레이션이 영업시간 정보를 알게 되면
추가로 카테고리별 휴리스틱이나 Kakao API 응답으로 갱신.

이 스크립트는 자동 마이그레이션 (`database/connection.py`) 도 동시에 적용하므로,
서버 재시작만으로도 컬럼은 추가됨. 본 스크립트는 명시적 점검·재실행용.

사용:
    python scripts/migrate_restaurant_hours.py
    docker exec mini-lunch-api python /app/scripts/migrate_restaurant_hours.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")

PATCHES = [
    ("restaurants", "serves_breakfast", "serves_breakfast BOOLEAN NOT NULL DEFAULT 1"),
    ("restaurants", "serves_lunch", "serves_lunch BOOLEAN NOT NULL DEFAULT 1"),
    ("restaurants", "serves_dinner", "serves_dinner BOOLEAN NOT NULL DEFAULT 1"),
]


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def main(db_path: str = DB_PATH) -> int:
    if not os.path.exists(db_path):
        print(f"[error] DB 파일 없음: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    try:
        applied = 0
        skipped = 0
        for table, col, ddl in PATCHES:
            cols = existing_columns(conn, table)
            if col in cols:
                print(f"[skip] {table}.{col} 이미 존재")
                skipped += 1
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
            print(f"[ok] {table}.{col} 추가")
            applied += 1
        conn.commit()
        print(f"\n총 {applied} 컬럼 추가, {skipped} 건너뜀.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    sys.exit(main(db))
