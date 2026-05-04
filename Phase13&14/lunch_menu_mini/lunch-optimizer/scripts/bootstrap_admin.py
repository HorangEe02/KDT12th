"""초기 관리자 계정 생성/승격 (idempotent).

사용:
    # .env에 다음 설정 후
    #   ADMIN_EMAIL=admin@example.com
    #   ADMIN_PASSWORD=<강력한 비밀번호>

    docker exec mini-lunch-api python /tmp/bootstrap_admin.py

또는 환경변수 직접 전달:
    docker exec -e ADMIN_EMAIL=foo@bar -e ADMIN_PASSWORD=xxx mini-lunch-api \
        python /tmp/bootstrap_admin.py

동작:
    1. ADMIN_EMAIL 사용자가 없으면 → role=admin 으로 생성
    2. 있으면 → role=admin 강제 승격 (이미 admin이면 변경 없음)
    3. 비밀번호는 ADMIN_PASSWORD 가 주어졌고 사용자가 없을 때만 적용
       (이미 존재하는 사용자의 비밀번호는 덮어쓰지 않음 — 안전)
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime

# 패키지 import 를 위해 /app 을 path 에 추가
sys.path.insert(0, "/app")

from auth.passwords import hash_password  # noqa: E402
from database.connection import get_session  # noqa: E402
from database.models import Team, User  # noqa: E402


def main() -> int:
    email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD") or ""

    if not email:
        print("[error] ADMIN_EMAIL 환경변수 미설정", file=sys.stderr)
        return 1

    print(f"target email: {email}")

    with get_session() as session:
        existing = session.query(User).filter(User.email == email).first()

        if existing is None:
            if not password or len(password) < 8:
                print(
                    "[error] 신규 admin 생성에는 ADMIN_PASSWORD (8자+) 필요",
                    file=sys.stderr,
                )
                return 1
            # 기본 팀 보장
            if session.get(Team, "team1") is None:
                session.add(Team(id="team1", name="Default"))
                session.flush()
            user = User(
                id=f"admin-{uuid.uuid4().hex[:8]}",
                email=email,
                password_hash=hash_password(password),
                role="admin",
                name="Administrator",
                team_id="team1",
                avatar_emoji="🛡️",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(user)
            session.flush()
            session.commit()
            print(f"✅ admin 계정 생성: id={user.id} email={email}")
            return 0

        # 기존 사용자 → admin 으로 승격
        if existing.role != "admin":
            print(f"  user '{existing.id}' role 변경: {existing.role} → admin")
            existing.role = "admin"
        else:
            print("  이미 admin 권한 보유")

        if not existing.is_active:
            print("  is_active=False → True 복구")
            existing.is_active = True

        # 비밀번호는 명시적으로 'reset' 모드일 때만 갱신 (안전 가드)
        if password and os.environ.get("ADMIN_PASSWORD_RESET", "0") == "1":
            existing.password_hash = hash_password(password)
            print("  비밀번호 재설정됨 (ADMIN_PASSWORD_RESET=1)")

        session.flush()
        session.commit()
        print(f"✅ admin 계정 동기화 완료: id={existing.id}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
