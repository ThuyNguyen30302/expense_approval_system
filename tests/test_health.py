from app.main import app


def test_app_imports() -> None:
    assert app.title == "Expense Approval System"


def test_health_endpoint_returns_ok(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
