from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_health_reports_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    # Security headers are applied to every response
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "X-Request-Id" in resp.headers


def test_protected_route_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 401


def test_login_rejects_bad_credentials(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "demo.analyst", "password": "wrong"})
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_login_validation_rejects_blank_username(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "   ", "password": "x"})
    assert resp.status_code == 422


def test_login_sets_httponly_cookie_and_me_works(client: TestClient) -> None:
    settings = get_settings()
    resp = client.post("/api/auth/login", json={"username": settings.demo_username, "password": settings.demo_password})
    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert settings.session_cookie_name in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == settings.demo_username


def test_cookie_session_requires_csrf_header_for_unsafe_methods(client: TestClient) -> None:
    settings = get_settings()
    client.post("/api/auth/login", json={"username": settings.demo_username, "password": settings.demo_password})
    # No X-Requested-With header => blocked
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 403
    resp = client.post("/api/auth/logout", headers={"X-Requested-With": "XMLHttpRequest"})
    assert resp.status_code == 200


def test_logout_clears_session(auth_client: TestClient) -> None:
    assert auth_client.get("/api/auth/me").status_code == 200
    auth_client.post("/api/auth/logout")
    assert auth_client.get("/api/auth/me").status_code == 401
