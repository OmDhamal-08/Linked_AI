from app.core.security import hash_password, verify_password
from tests.conftest import _signup


def test_signup_returns_token_and_free_plan(client):
    headers = _signup(client, "signup")
    me = client.get("/api/v1/users/me", headers={"Authorization": headers["Authorization"]})
    assert me.status_code == 200
    body = me.json()
    assert body["plan"] == "free"
    assert "password" not in body and "password_hash" not in body


def test_duplicate_signup_is_rejected(client):
    first = _signup(client, email="dupe@linkdine-test.com")
    assert first
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "dupe@linkdine-test.com", "password": "StrongPassword123"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_request"


def test_login_with_wrong_password_is_generic(client):
    _signup(client, email="login-check@linkdine-test.com")
    response = client.post("/api/v1/auth/login", json={"email": "login-check@linkdine-test.com", "password": "WrongPassword1"})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Email or password is incorrect."


def test_login_with_unknown_email_gives_same_error(client):
    response = client.post("/api/v1/auth/login", json={"email": "nobody@linkdine-test.com", "password": "WrongPassword1"})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Email or password is incorrect."


def test_login_success_returns_working_token(client):
    _signup(client, email="works@linkdine-test.com")
    response = client.post("/api/v1/auth/login", json={"email": "works@linkdine-test.com", "password": "StrongPassword123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "works@linkdine-test.com"


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_invalid_token_is_rejected(client):
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_profile_update(client):
    headers = _signup(client, "profile")
    response = client.post(
        "/api/v1/auth/profile",
        json={"name": "  Ada Lovelace  ", "avatar_url": "https://example.com/a.png"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Ada Lovelace"


def test_logout_endpoint(client):
    headers = _signup(client, "logout")
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200


def test_password_is_hashed_not_plaintext():
    stored = hash_password("StrongPassword123")
    assert "StrongPassword123" not in stored
    assert verify_password("StrongPassword123", stored)
    assert not verify_password("wrong-password", stored)
    assert not verify_password("anything", None)
