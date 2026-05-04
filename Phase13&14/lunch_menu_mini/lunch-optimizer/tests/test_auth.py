"""Phase 13&14 인증 단위 테스트.

실행:
    docker exec mini-lunch-api pytest /app/tests/test_auth.py -v
"""
from __future__ import annotations

import os
import time
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

# 테스트 시 임시 JWT 시크릿 + 임시 DB
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod-32bytes-padding")
os.environ.setdefault("JWT_EXPIRE_HOURS", "24")


# 각 테스트는 격리된 SQLite 파일 사용
@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("MINI_DB_PATH", str(db_path))
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")

    from importlib import reload
    # settings 가 module-level 에서 환경변수를 읽으므로 강제 reload
    from config import settings as settings_mod
    reload(settings_mod)
    # connection 의 engine/sessionmaker 싱글톤 리셋
    from database import connection as conn_mod
    reload(conn_mod)
    conn_mod._engine = None
    conn_mod._SessionLocal = None
    conn_mod.init_schema()
    yield


@pytest.fixture
def client():
    from importlib import reload
    from api import main as api_main
    reload(api_main)
    return TestClient(api_main.app)


# -----------------------------------------------------------------------------
# Password hashing
# -----------------------------------------------------------------------------
class TestPasswordHashing:
    def test_hash_password_minimum_length(self):
        from auth import hash_password
        with pytest.raises(ValueError):
            hash_password("short")

    def test_hash_then_verify(self):
        from auth import hash_password, verify_password
        h = hash_password("strongpassword")
        assert h != "strongpassword"
        assert verify_password("strongpassword", h) is True
        assert verify_password("wrongpassword", h) is False

    def test_verify_with_none_hash(self):
        from auth import verify_password
        assert verify_password("anything", None) is False


# -----------------------------------------------------------------------------
# JWT
# -----------------------------------------------------------------------------
class TestJWT:
    def test_create_and_decode(self):
        from auth import create_access_token, decode_access_token
        token = create_access_token(user_id="u1", email="a@b.com", role="user")
        payload = decode_access_token(token)
        assert payload["sub"] == "u1"
        assert payload["email"] == "a@b.com"
        assert payload["role"] == "user"

    def test_expiry(self):
        from auth import JWTError, create_access_token, decode_access_token
        token = create_access_token(
            user_id="u1", email="a@b.com", role="user",
            expires_in_seconds=1,
        )
        time.sleep(2)
        with pytest.raises(JWTError):
            decode_access_token(token)


# -----------------------------------------------------------------------------
# /api/auth/register
# -----------------------------------------------------------------------------
class TestRegister:
    def test_success(self, client):
        r = client.post("/api/auth/register", json={
            "email": "alice@example.com",
            "password": "strongpassword",
            "name": "Alice",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["access_token"]
        assert body["user"]["email"] == "alice@example.com"
        assert body["user"]["role"] == "user"
        assert "password_hash" not in body["user"]

    def test_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "bob@example.com", "password": "strongpassword", "name": "Bob",
        })
        r = client.post("/api/auth/register", json={
            "email": "bob@example.com", "password": "anotherone", "name": "Bob2",
        })
        assert r.status_code == 409

    def test_weak_password(self, client):
        r = client.post("/api/auth/register", json={
            "email": "weak@example.com", "password": "short", "name": "Weak",
        })
        assert r.status_code in (422, 500)  # pydantic min_length 또는 hash_password ValueError


# -----------------------------------------------------------------------------
# /api/auth/login
# -----------------------------------------------------------------------------
class TestLogin:
    def _register(self, client, email="user@example.com", password="strongpassword"):
        return client.post("/api/auth/register", json={
            "email": email, "password": password, "name": "User",
        })

    def test_success(self, client):
        self._register(client)
        r = client.post("/api/auth/login", json={
            "email": "user@example.com", "password": "strongpassword",
        })
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_wrong_password(self, client):
        self._register(client)
        r = client.post("/api/auth/login", json={
            "email": "user@example.com", "password": "wrongpassword",
        })
        assert r.status_code == 401
        # 메시지 enumeration 방지 — 동일 메시지
        assert "일치하지" in r.json()["detail"]

    def test_unknown_email(self, client):
        r = client.post("/api/auth/login", json={
            "email": "ghost@example.com", "password": "irrelevant",
        })
        assert r.status_code == 401


# -----------------------------------------------------------------------------
# /api/auth/me
# -----------------------------------------------------------------------------
class TestMe:
    def test_no_token_401(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_with_token(self, client):
        reg = client.post("/api/auth/register", json={
            "email": "me@example.com", "password": "strongpassword", "name": "Me",
        }).json()
        token = reg["access_token"]
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "me@example.com"

    def test_invalid_token_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer fakefakefake"})
        assert r.status_code == 401


# -----------------------------------------------------------------------------
# Soft-delete blocks login
# -----------------------------------------------------------------------------
class TestDeactivatedUser:
    def test_inactive_cannot_login(self, client):
        client.post("/api/auth/register", json={
            "email": "x@example.com", "password": "strongpassword", "name": "X",
        })
        # 직접 DB 에서 비활성화
        from database.connection import get_session
        from database.models import User
        with get_session() as s:
            u = s.query(User).filter(User.email == "x@example.com").first()
            u.is_active = False
            s.commit()

        r = client.post("/api/auth/login", json={
            "email": "x@example.com", "password": "strongpassword",
        })
        assert r.status_code == 401
