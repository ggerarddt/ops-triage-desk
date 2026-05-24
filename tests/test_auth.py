"""Authentication and access-control tests."""
import os
import tempfile

import pytest

from core.config import SEED_USERS
from core.database import init_schema, seed_users, session as db_session
from services.auth_service import find_user_by_username, verify_password
from app import app


@pytest.fixture(scope="module")
def test_db(tmp_path_factory):
    """Create a temporary SQLite database and seed it."""
    db_file = tmp_path_factory.mktemp("triage") / "test.db"
    init_schema(str(db_file))
    seed_users(SEED_USERS, str(db_file))
    return str(db_file)


@pytest.fixture(autouse=True)
def patch_database(monkeypatch, test_db):
    """Make all core.database functions use the test DB."""
    import core.database as db_mod

    original_get_conn = db_mod._get_conn
    original_session = db_mod.session

    db_path = test_db

    def patched_get_conn(path=None):
        return original_get_conn(db_path)

    def patched_session(path=None):
        return original_session(db_path)

    monkeypatch.setattr(db_mod, "_get_conn", patched_get_conn)
    monkeypatch.setattr(db_mod, "session", patched_session)
    return test_db


@pytest.fixture
def client(test_db, monkeypatch):
    """Flask test client with test database."""
    app.secret_key = "test-only"
    with app.test_client() as c:
        yield c


class TestAuthFindUser:
    def test_find_operator1(self):
        user = find_user_by_username("operator1")
        assert user is not None
        assert user["role"] == "operator"

    def test_find_supervisor1(self):
        user = find_user_by_username("supervisor1")
        assert user is not None
        assert user["role"] == "supervisor"

    def test_nonexistent_user(self):
        assert find_user_by_username("nonexistent") is None


class TestAuthVerifyPassword:
    def test_correct_password(self):
        user = find_user_by_username("operator1")
        assert verify_password(user, "ChangeMe123!")

    def test_wrong_password(self):
        user = find_user_by_username("supervisor1")
        assert not verify_password(user, "WrongPassword")


class TestAuthLoginLogout:
    def test_login_success_operator(self, client):
        resp = client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Redirects to triage page
        assert b"New Incident Report" in resp.data

    def test_login_success_supervisor(self, client):
        resp = client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_invalid_password(self, client):
        resp = client.post("/login", data={
            "username": "operator1",
            "password": "WrongPassword",
        })
        assert resp.status_code == 200  # Login page re-shown
        assert b"Invalid username or password" in resp.data

    def test_login_nonexistent_user(self, client):
        resp = client.post("/login", data={
            "username": "ghost",
            "password": "anything",
        })
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_logout(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200
        assert b"logged out" in resp.data


class TestAccessControl:
    def test_admin_operator_blocked(self, client):
        client.post("/login", data={
            "username": "operator1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/admin")
        assert resp.status_code == 302  # Redirect
        assert b"You do not have permission" in resp.data or b"redirected" in resp.data.lower()

    def test_admin_supervisor_allowed(self, client):
        client.post("/login", data={
            "username": "supervisor1",
            "password": "ChangeMe123!",
        })
        resp = client.get("/admin")
        assert resp.status_code == 200
        assert b"Admin" in resp.data

    def test_unauthenticated_redirect(self, client):
        resp = client.get("/triage")
        assert resp.status_code == 302
        assert "login" in resp.location

    def test_root_redirects_unauthenticated(self, client):
        resp = client.get("/")
        assert resp.status_code == 302
        assert "login" in resp.location
