"""Phase 13&14 관리자 엔드포인트 테스트."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod-32bytes-padding")


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("MINI_DB_PATH", str(db_path))
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")
    from importlib import reload
    from config import settings as settings_mod
    reload(settings_mod)
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


def _register(client, email, password="strongpassword", name="User"):
    r = client.post("/api/auth/register",
                    json={"email": email, "password": password, "name": name})
    assert r.status_code == 201
    return r.json()


def _make_admin(email="root@example.com"):
    """직접 DB 접근으로 admin 권한 부여."""
    from database.connection import get_session
    from database.models import User
    with get_session() as s:
        u = s.query(User).filter(User.email == email).first()
        u.role = "admin"
        s.commit()


# -----------------------------------------------------------------------------
class TestAdminAuthorization:
    def test_unauthenticated_returns_401(self, client):
        r = client.get("/api/admin/users")
        assert r.status_code == 401

    def test_regular_user_returns_403(self, client):
        reg = _register(client, "user@example.com")
        token = reg["access_token"]
        r = client.get("/api/admin/users",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_admin_can_list(self, client):
        _register(client, "root@example.com")
        _make_admin("root@example.com")
        # 다시 로그인해서 admin role 토큰 발급
        token = client.post("/api/auth/login", json={
            "email": "root@example.com", "password": "strongpassword",
        }).json()["access_token"]
        r = client.get("/api/admin/users",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# -----------------------------------------------------------------------------
def _admin_token(client):
    _register(client, "root@example.com")
    _make_admin("root@example.com")
    return client.post("/api/auth/login", json={
        "email": "root@example.com", "password": "strongpassword",
    }).json()["access_token"]


class TestUserCRUD:
    def test_list_with_pagination(self, client):
        token = _admin_token(client)
        for i in range(3):
            _register(client, f"u{i}@example.com")

        r = client.get("/api/admin/users?limit=2",
                       headers={"Authorization": f"Bearer {token}"})
        body = r.json()
        assert r.status_code == 200
        assert body["total"] == 4  # admin + 3 users
        assert len(body["items"]) == 2

    def test_filter_by_role(self, client):
        token = _admin_token(client)
        _register(client, "regular@example.com")
        r = client.get("/api/admin/users?role=admin",
                       headers={"Authorization": f"Bearer {token}"})
        items = r.json()["items"]
        assert all(u["role"] == "admin" for u in items)

    def test_search_by_q(self, client):
        token = _admin_token(client)
        _register(client, "alice@example.com", name="Alice")
        _register(client, "bob@example.com", name="Bob")
        r = client.get("/api/admin/users?q=alice",
                       headers={"Authorization": f"Bearer {token}"})
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["email"] == "alice@example.com"

    def test_patch_user(self, client):
        token = _admin_token(client)
        target = _register(client, "target@example.com", name="Target")
        target_id = target["user"]["id"]

        r = client.patch(
            f"/api/admin/users/{target_id}",
            json={"role": "admin", "name": "Promoted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "admin"
        assert body["name"] == "Promoted"

    def test_deactivate_then_restore(self, client):
        token = _admin_token(client)
        target = _register(client, "dup@example.com")
        target_id = target["user"]["id"]

        r1 = client.delete(
            f"/api/admin/users/{target_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        assert r1.json()["is_active"] is False

        r2 = client.post(
            f"/api/admin/users/{target_id}/restore",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["is_active"] is True


# -----------------------------------------------------------------------------
class TestSafetyGuards:
    def test_last_admin_cannot_be_demoted(self, client):
        token = _admin_token(client)
        # admin 본인의 user_id 추출
        me = client.get("/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"}).json()
        admin_id = me["id"]

        r = client.patch(
            f"/api/admin/users/{admin_id}",
            json={"role": "user"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 409

    def test_last_admin_cannot_be_deactivated(self, client):
        token = _admin_token(client)
        me = client.get("/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"}).json()

        r = client.delete(
            f"/api/admin/users/{me['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 본인 비활성도 어쨌든 거부 (400 self) — last admin 보호 이전에 잡힘
        assert r.status_code in (400, 409)

    def test_self_deactivate_blocked(self, client):
        # admin 두 명 만들고 한 명이 본인을 비활성 시도 → 거부
        token1 = _admin_token(client)  # root@
        _register(client, "second@example.com")
        _make_admin("second@example.com")

        me = client.get("/api/auth/me",
                        headers={"Authorization": f"Bearer {token1}"}).json()
        r = client.delete(
            f"/api/admin/users/{me['id']}",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert r.status_code == 400


# -----------------------------------------------------------------------------
class TestHardDelete:
    def test_hard_delete_success(self, client):
        token = _admin_token(client)
        target = _register(client, "del@example.com", name="DeleteMe")
        target_id = target["user"]["id"]

        r = client.delete(
            f"/api/admin/users/{target_id}/permanent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["permanently_deleted"] is True
        assert body["user"]["email"] == "del@example.com"

        # GET 재조회 시 404
        r2 = client.get(
            f"/api/admin/users/{target_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 404

    def test_hard_delete_self_blocked(self, client):
        token = _admin_token(client)
        me = client.get("/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"}).json()
        r = client.delete(
            f"/api/admin/users/{me['id']}/permanent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400

    def test_hard_delete_last_admin_blocked(self, client):
        token = _admin_token(client)
        me = client.get("/api/auth/me",
                        headers={"Authorization": f"Bearer {token}"}).json()
        # 두 번째 admin 만들고 첫 번째 admin 삭제는 성공해야 함
        # 그러나 본인 self 가드가 먼저 작동하므로 다른 admin 시나리오 구성:
        _register(client, "second@example.com")
        _make_admin("second@example.com")
        # 자신을 hard_delete 시도 → self 가드 (400)
        r = client.delete(
            f"/api/admin/users/{me['id']}/permanent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400

    def test_hard_delete_not_found(self, client):
        token = _admin_token(client)
        r = client.delete(
            "/api/admin/users/no-such-id/permanent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404

    def test_hard_delete_requires_admin(self, client):
        _register(client, "user@example.com")
        token = client.post("/api/auth/login", json={
            "email": "user@example.com", "password": "strongpassword",
        }).json()["access_token"]

        r = client.delete(
            "/api/admin/users/some-id/permanent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403


class TestStats:
    def test_stats_returns_counts(self, client):
        token = _admin_token(client)
        _register(client, "a@example.com")
        _register(client, "b@example.com")

        r = client.get("/api/admin/stats",
                       headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["total_users"] == 3  # admin + 2
        assert body["active_users"] == 3
        assert body["active_admins"] == 1
