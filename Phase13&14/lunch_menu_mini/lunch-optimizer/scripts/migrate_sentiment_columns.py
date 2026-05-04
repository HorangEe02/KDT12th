"""restaurants 테이블에 감성 분석 결과 컬럼을 추가 (idempotent).

추가:
  - sentiment_score          FLOAT       (-1.0 ~ +1.0)
  - sentiment_pos_ratio      FLOAT       (0.0 ~ 1.0)  — 긍정 리뷰 비율
  - sentiment_sample_size    INTEGER     — 분석에 사용된 리뷰 수
  - sentiment_updated_at     DATETIME

사용:
    docker exec mini-lunch-api python /tmp/migrate_sentiment_columns.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")

PATCHES = [
    ("sentiment_score", "FLOAT"),
    ("sentiment_pos_ratio", "FLOAT"),
    ("sentiment_sample_size", "INTEGER"),
    ("sentiment_updated_at", "DATETIME"),
]


def existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    print(f"DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = existing_columns(conn, "restaurants")
        added = []
        for name, ddl in PATCHES:
            if name in cols:
                continue
            sql = f"ALTER TABLE restaurants ADD COLUMN {name} {ddl}"
            print(f"  + {sql}")
            conn.execute(sql)
            added.append(name)

        # 인덱스 (top N 정렬 최적화)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_restaurants_sentiment_score "
            "ON restaurants(sentiment_score DESC)"
        )
        conn.commit()

        if added:
            print(f"\n✅ 추가된 컬럼: {added}")
        else:
            print("\n✅ 변경 사항 없음 (이미 최신)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
