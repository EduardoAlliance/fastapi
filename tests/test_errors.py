from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_handlers import register_error_handlers


def test_unknown_route_returns_error_envelope(client):
    response = client.get("/api/v1/no-existe")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Recurso no encontrado"


def test_method_not_allowed_returns_error_envelope(client):
    response = client.post("/health")

    assert response.status_code == 405
    body = response.json()
    assert body["error"]["code"] == "method_not_allowed"
    assert body["error"]["message"] == "Método no permitido"


def test_unhandled_exception_returns_error_envelope():
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "Error interno del servidor"
    assert "boom" not in body["error"]["message"]
