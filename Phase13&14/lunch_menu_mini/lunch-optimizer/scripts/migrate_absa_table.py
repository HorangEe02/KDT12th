"""restaurant_absa 테이블 생성 (idempotent).

스키마:
  - restaurant_id  TEXT  (FK to restaurants.id)
  - aspect         VARCHAR(20)   (taste/service/price/hygiene/ambience)
  - sentiment      VARCHAR(20)   (positive/neutral/negative)
  - score          FLOAT         (-1.0 ~ +1.0)
  - confidence     FLOAT         (0.0 ~ 1.0)
  - sample_size    INTEGER
  - updated_at     DATETIME

(restaurant_id, aspect) 복합 unique.
"""
from __future__ import annotations

import os
import sqlite3
import sys

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[error] DB not found: {DB_PATH}", file=sys.stderr)
        return 1
    print(f"DB: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurant_absa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id TEXT NOT NULL,
                aspect VARCHAR(20) NOT NULL,
                sentiment VARCHAR(20) NOT NULL,
                score FLOAT,
                confidence FLOAT,
                sample_size INTEGER DEFAULT 0,
                updated_at DATETIME
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_restaurant_absa_rid_aspect
            ON restaurant_absa(restaurant_id, aspect)
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_restaurant_absa_aspect ON restaurant_absa(aspect)"
        )
        conn.commit()
        cur = conn.execute("PRAGMA table_info(restaurant_absa)")
        cols = [r[1] for r in cur.fetchall()]
        print(f"  ✅ table cols: {cols}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
