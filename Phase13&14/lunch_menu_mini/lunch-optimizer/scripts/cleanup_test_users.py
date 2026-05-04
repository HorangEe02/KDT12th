"""
일회성 테스트 사용자 정리 스크립트.

사용:
    docker exec -it mini-lunch-api python scripts/cleanup_test_users.py --dry-run
    docker exec -it mini-lunch-api python scripts/cleanup_test_users.py --apply

동작:
    1. users / buddy_joins / buddy_posts / votes / meal_history / vetoes / visit_history /
       chat_messages 의 현재 행 수를 보고
    2. --apply 옵션 시:
       - 테이블별 archive JSON 백업을 /app/database/_archive_<timestamp>.json 에 저장
       - 위 테이블 전체 삭제 (트랜잭션 단위)
       - 외래키 의존 순서대로 처리

⚠ 식당(restaurants), 영양(nutrition_info), 날씨(weather_logs) 등 데이터 자산은 건드리지 않음.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import sqlite3

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/database/mini.db")

# 외래키 참조 그래프를 따라 자식 → 부모 순서로 삭제
USER_DEPENDENT_TABLES = [
    "buddy_joins",      # buddy_posts 자식
    "buddy_posts",
    "vetoes",           # vote_sessions 자식
    "votes",            # vote_sessions 자식
    "vote_sessions",
    "meal_history",
    "visit_history",
    "chat_messages",
    "users",            # 마지막 (다른 테이블이 참조)
]


def fetch_counts(conn: sqlite3.Connection) -> dict[str, int]:
    cur = conn.cursor()
    counts: dict[str, int] = {}
    for t in USER_DEPENDENT_TABLES:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = -1  # 테이블 없음
    return counts


def archive_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup one-off test users")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제로 삭제 수행 (지정하지 않으면 dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="명시적 dry-run (--apply 없으면 default)",
    )
    parser.add_argument(
        "--archive-dir",
        default="/app/database",
        help="백업 JSON 저장 디렉토리 (default: /app/database)",
    )
    args = parser.parse_args()

    if not Path(DB_PATH).exists():
        print(f"[error] DB 파일이 없음: {DB_PATH}", file=sys.stderr)
        return 1

    apply = bool(args.apply)
    print(f"DB:        {DB_PATH}")
    print(f"Mode:      {'APPLY (DESTRUCTIVE)' if apply else 'dry-run (no changes)'}")
    print()

    conn = sqlite3.connect(DB_PATH)
    try:
        # PRAGMA foreign_keys 켜기 (cascade 위해)
        conn.execute("PRAGMA foreign_keys = ON")

        before = fetch_counts(conn)
        print("현재 행 수:")
        for t, n in before.items():
            label = f"{n:>6,}" if n >= 0 else "    --"
            print(f"  {t:20s} {label}")

        total = sum(n for n in before.values() if n >= 0)
        if total == 0:
            print("\n정리할 행이 없습니다. 종료.")
            return 0

        if not apply:
            print("\n[dry-run] 실제 삭제하려면 --apply 추가.")
            return 0

        # 1. archive
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_path = Path(args.archive_dir) / f"_archive_users_{ts}.json"
        archive: dict[str, list[dict]] = {}
        for t in USER_DEPENDENT_TABLES:
            if before.get(t, -1) > 0:
                try:
                    archive[t] = archive_table(conn, t)
                except sqlite3.OperationalError:
                    pass
        archive_path.write_text(
            json.dumps(archive, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"\n[archive] {archive_path} ({sum(len(v) for v in archive.values())} rows)")

        # 2. 트랜잭션 단위 삭제
        cur = conn.cursor()
        for t in USER_DEPENDENT_TABLES:
            if before.get(t, -1) > 0:
                cur.execute(f"DELETE FROM {t}")
                print(f"  DELETE FROM {t:20s} -> {cur.rowcount} rows")
        conn.commit()

        after = fetch_counts(conn)
        print("\n삭제 후 행 수:")
        for t, n in after.items():
            label = f"{n:>6,}" if n >= 0 else "    --"
            print(f"  {t:20s} {label}")

        print("\n✅ cleanup 완료")
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
