from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services.bootstrap import seed_admin_user
from tests.test_auth_users import auth_headers, login_user, register_user


def create_expense(
    client: TestClient,
    token: str,
    *,
    title: str = "Client lunch",
    category: str = "meals",
    amount: str = "45.75",
    currency: str = "USD",
    expense_date: str = "2026-06-18",
    receipt: dict | None = None,
) -> dict:
    payload = {
        "title": title,
        "description": "Lunch with client after project meeting.",
        "category": category,
        "amount": amount,
        "currency": currency,
        "expense_date": expense_date,
        "department": "Sales",
        "project_code": "ACME-001",
    }
    if receipt is not None:
        payload["receipt"] = receipt

    response = client.post(
        "/api/v1/expenses",
        headers=auth_headers(token),
        json=payload,
    )
    assert response.status_code == 201
    return response.json()


def create_admin_token(client: TestClient, db_session: Session) -> str:
    seed_admin_user(
        db_session,
        email="admin@example.com",
        password="strong-password",
        full_name="Admin User",
    )
    return login_user(client, "admin@example.com")


def audit_event_count(db_session: Session, event_type: str) -> int:
    return db_session.query(AuditLog).filter(AuditLog.event_type == event_type).count()


def test_employee_can_create_draft_expense_with_receipt(client: TestClient, db_session: Session) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")

    body = create_expense(
        client,
        token,
        receipt={
            "url": "https://example.com/receipt.pdf",
            "file_name": "receipt.pdf",
            "content_type": "application/pdf",
            "metadata": {"source": "demo"},
        },
    )

    assert body["title"] == "Client lunch"
    assert body["status"] == "draft"
    assert body["amount"] == "45.75"
    assert body["currency"] == "USD"
    assert len(body["receipts"]) == 1
    assert body["receipts"][0]["file_name"] == "receipt.pdf"
    assert audit_event_count(db_session, "expense_created") == 1
    assert audit_event_count(db_session, "receipt_added") == 1


def test_create_expense_validates_core_fields(client: TestClient) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")

    response = client.post(
        "/api/v1/expenses",
        headers=auth_headers(token),
        json={
            "title": "",
            "category": "meals",
            "amount": "-1.00",
            "currency": "usd",
            "expense_date": "2026-06-18",
        },
    )

    assert response.status_code == 422


def test_create_expense_rejects_empty_receipt_reference(client: TestClient) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")

    response = client.post(
        "/api/v1/expenses",
        headers=auth_headers(token),
        json={
            "title": "Client lunch",
            "category": "meals",
            "amount": "45.75",
            "currency": "USD",
            "expense_date": "2026-06-18",
            "receipt": {"content_type": "application/pdf"},
        },
    )

    assert response.status_code == 422


def test_employee_list_is_scoped_and_admin_can_see_all(client: TestClient, db_session: Session) -> None:
    register_user(client, email="first@example.com")
    first_token = login_user(client, "first@example.com")
    first_expense = create_expense(client, first_token, title="First", category="meals")

    register_user(client, email="second@example.com")
    second_token = login_user(client, "second@example.com")
    second_expense = create_expense(client, second_token, title="Second", category="travel")

    own_response = client.get("/api/v1/expenses", headers=auth_headers(first_token))
    assert own_response.status_code == 200
    assert own_response.json()["total"] == 1
    assert own_response.json()["items"][0]["id"] == first_expense["id"]

    escaped_response = client.get(
        f"/api/v1/expenses?requester_id={second_expense['requester_id']}",
        headers=auth_headers(first_token),
    )
    assert escaped_response.status_code == 200
    assert escaped_response.json()["total"] == 0

    admin_token = create_admin_token(client, db_session)
    admin_response = client.get("/api/v1/expenses", headers=auth_headers(admin_token))
    assert admin_response.status_code == 200
    assert admin_response.json()["total"] == 2


def test_expense_filters_and_pagination(client: TestClient, db_session: Session) -> None:
    admin_token = create_admin_token(client, db_session)
    first = create_expense(
        client,
        admin_token,
        title="Older meal",
        category="meals",
        expense_date="2026-06-10",
    )
    create_expense(
        client,
        admin_token,
        title="Newer travel",
        category="travel",
        expense_date="2026-06-20",
    )

    filtered_response = client.get(
        "/api/v1/expenses?category=meals&from_date=2026-06-01&to_date=2026-06-15",
        headers=auth_headers(admin_token),
    )
    assert filtered_response.status_code == 200
    assert filtered_response.json()["total"] == 1
    assert filtered_response.json()["items"][0]["id"] == first["id"]

    paged_response = client.get(
        "/api/v1/expenses?limit=1&offset=1",
        headers=auth_headers(admin_token),
    )
    assert paged_response.status_code == 200
    assert paged_response.json()["limit"] == 1
    assert paged_response.json()["offset"] == 1
    assert len(paged_response.json()["items"]) == 1


def test_detail_update_and_forbidden_access(client: TestClient) -> None:
    register_user(client, email="owner@example.com")
    owner_token = login_user(client, "owner@example.com")
    expense = create_expense(client, owner_token)

    register_user(client, email="other@example.com")
    other_token = login_user(client, "other@example.com")

    detail_response = client.get(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(owner_token),
    )
    assert detail_response.status_code == 200

    forbidden_response = client.get(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(other_token),
    )
    assert forbidden_response.status_code == 403

    update_response = client.patch(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(owner_token),
        json={"title": "Updated lunch", "amount": "50.00"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated lunch"
    assert update_response.json()["amount"] == "50.00"

    forbidden_update = client.patch(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(other_token),
        json={"title": "Nope"},
    )
    assert forbidden_update.status_code == 403


def test_submit_sets_status_and_blocks_later_update(client: TestClient, db_session: Session) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")
    expense = create_expense(client, token)

    submit_response = client.post(
        f"/api/v1/expenses/{expense['id']}/submit",
        headers=auth_headers(token),
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "submitted"
    assert submit_response.json()["submitted_at"] is not None
    assert audit_event_count(db_session, "expense_submitted") == 1

    update_response = client.patch(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(token),
        json={"title": "Too late"},
    )
    assert update_response.status_code == 409

    second_submit_response = client.post(
        f"/api/v1/expenses/{expense['id']}/submit",
        headers=auth_headers(token),
    )
    assert second_submit_response.status_code == 409


def test_cancel_requires_reason_and_blocks_invalid_status(client: TestClient, db_session: Session) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")
    expense = create_expense(client, token)

    missing_reason_response = client.post(
        f"/api/v1/expenses/{expense['id']}/cancel",
        headers=auth_headers(token),
        json={},
    )
    assert missing_reason_response.status_code == 422

    cancel_response = client.post(
        f"/api/v1/expenses/{expense['id']}/cancel",
        headers=auth_headers(token),
        json={"reason": "Submitted by mistake."},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert cancel_response.json()["cancelled_at"] is not None
    assert audit_event_count(db_session, "expense_cancelled") == 1

    second_cancel_response = client.post(
        f"/api/v1/expenses/{expense['id']}/cancel",
        headers=auth_headers(token),
        json={"reason": "Try again."},
    )
    assert second_cancel_response.status_code == 409


def test_admin_can_access_and_update_any_expense(client: TestClient, db_session: Session) -> None:
    register_user(client, email="employee@example.com")
    employee_token = login_user(client, "employee@example.com")
    expense = create_expense(client, employee_token)

    admin_token = create_admin_token(client, db_session)
    update_response = client.patch(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(admin_token),
        json={"department": "Finance"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["department"] == "Finance"


def test_date_range_filter_accepts_iso_dates(client: TestClient, db_session: Session) -> None:
    admin_token = create_admin_token(client, db_session)
    create_expense(client, admin_token, title="June", expense_date=date(2026, 6, 18).isoformat())

    response = client.get(
        "/api/v1/expenses?from_date=2026-06-01&to_date=2026-06-30",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
