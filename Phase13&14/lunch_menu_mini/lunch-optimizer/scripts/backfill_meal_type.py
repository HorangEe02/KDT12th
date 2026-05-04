"""기존 meal_history 행들 중 meal_type 이 NULL 인 것을 created_at 시각으로
추론하여 채우는 백필 스크립트 (idempotent).

추론 규칙 (created_at 의 시(hour) 기준):
  06:00 ~ 09:59  → breakfast
  10:00 ~ 14:59  → lunch
  15:00 ~ 23:59  → dinner
  00:00 ~ 05:59  → dinner (야식/심야)

이미 meal_type 이 채워진 행은 건드리지 않는다.

사용:
    # dry-run (변경하지 않고 영향 받을 행만 출력)
    python scripts/backfill_meal_type.py --dry-run

    # 실제 적용
    python scripts/backfill_meal_type.py

    # Docker
    docker exec mini-lunch-api python /app/scripts/backfill_meal_type.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.environ.get("MINI_DB_PATH", "/app/data/mini.db")


def infer_meal_type(created_at: str) -> str:
    """created_at ISO 문자열 → 시각 기반 meal_type 추론."""
    try:
        dt = datetime.fromisoformat(created_at)
    except (TypeError, ValueError):
        return "lunch"  # 파싱 실패 시 기본값
    hour = dt.hour
    if 6 <= hour < 10:
        return "breakfast"
    if 10 <= hour < 15:
        return "lunch"
    return "dinner"


def main() -> int:
    parser = argparse.ArgumentParser(description="meal_type 백필 (NULL 행만 추론하여 채움)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 변경하지 않고 영향 받을 행 수와 분포만 출력",
    )
    parser.add_argument(
        "--db",
        default=DB_PATH,
        help=f"DB 경로 (기본: {DB_PATH})",
    )
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"[error] DB 파일 없음: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        # 1) 영향 받을 행 조회
        rows = conn.execute(
            "SELECT id, created_at FROM meal_history WHERE meal_type IS NULL OR meal_type = ''"
        ).fetchall()
        if not rows:
            print("[ok] 백필할 행 없음 (모든 meal_history 가 이미 meal_type 보유).")
            return 0

        # 2) 추론
        plan: dict[str, int] = {"breakfast": 0, "lunch": 0, "dinner": 0}
        updates: list[tuple[str, int]] = []
        for r in rows:
            mt = infer_meal_type(r["created_at"] or "")
            plan[mt] = plan.get(mt, 0) + 1
            updates.append((mt, r["id"]))

        print(f"[plan] 영향 받을 행: {len(rows)}")
        for mt, n in plan.items():
            print(f"  - {mt}: {n}")

        if args.dry_run:
            print("[dry-run] 변경 없이 종료.")
            return 0

        # 3) 실제 적용
        cur = conn.cursor()
        cur.executemany(
            "UPDATE meal_history SET meal_type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            updates,
        )
        conn.commit()
        print(f"[ok] {cur.rowcount} 행 업데이트 완료.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
