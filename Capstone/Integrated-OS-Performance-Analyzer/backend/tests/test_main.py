from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_root():
    with (
        patch("app.main.mongodb.connect"),
        patch("app.main.mongodb.disconnect"),
        TestClient(app) as client,
    ):
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_success():
    with (
        patch("app.main.mongodb.connect"),
        patch("app.main.mongodb.disconnect"),
        patch("app.main.mongodb.ping", return_value=True),
        TestClient(app) as client,
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_health_failure():
    with (
        patch("app.main.mongodb.connect"),
        patch("app.main.mongodb.disconnect"),
        patch("app.main.mongodb.ping", return_value=False),
        TestClient(app) as client,
    ):
        response = client.get("/health")

    assert response.status_code == 503


def test_cors_allowed_origin():
    with (
        patch("app.main.mongodb.connect"),
        patch("app.main.mongodb.disconnect"),
        TestClient(app) as client,
    ):
        response = client.get("/", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    )


def test_cors_preflight():
    with (
        patch("app.main.mongodb.connect"),
        patch("app.main.mongodb.disconnect"),
        TestClient(app) as client,
    ):
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    )
    assert "GET" in response.headers.get("access-control-allow-methods", "")


def test_cors_disallowed_origin():
    with (
        patch("app.main.mongodb.connect"),
        patch("app.main.mongodb.disconnect"),
        TestClient(app) as client,
    ):
        response = client.get("/", headers={"Origin": "http://untrusted-site.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
