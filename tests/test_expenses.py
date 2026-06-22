from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.approval_decision import ApprovalDecision
from app.models.audit_log import AuditLog
from app.models.payment import Payment
from app.models.user import User
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


def create_user_with_role(
    db_session: Session,
    *,
    email: str,
    role: str,
    manager_id: object | None = None,
) -> User:
    user = User(
        email=email,
        full_name=email.split("@")[0].replace(".", " ").title(),
        hashed_password=hash_password("strong-password"),
        role=role,
        manager_id=manager_id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_workflow_users(db_session: Session) -> tuple[User, str, User, str, User, str]:
    manager = create_user_with_role(db_session, email="manager@example.com", role="manager")
    accountant = create_user_with_role(db_session, email="accountant@example.com", role="accountant")
    employee = create_user_with_role(
        db_session,
        email="employee@example.com",
        role="employee",
        manager_id=manager.id,
    )
    return (
        employee,
        "employee@example.com",
        manager,
        "manager@example.com",
        accountant,
        "accountant@example.com",
    )


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


def test_manager_accounting_payment_happy_path_and_audit_history(
    client: TestClient,
    db_session: Session,
) -> None:
    employee, employee_email, manager, manager_email, _accountant, accountant_email = create_workflow_users(db_session)
    employee_token = login_user(client, employee_email)
    manager_token = login_user(client, manager_email)
    accountant_token = login_user(client, accountant_email)

    expense = create_expense(client, employee_token)
    assert expense["assigned_manager_id"] == str(manager.id)

    submit_response = client.post(
        f"/api/v1/expenses/{expense['id']}/submit",
        headers=auth_headers(employee_token),
    )
    assert submit_response.status_code == 200

    manager_list_response = client.get("/api/v1/expenses?status=submitted", headers=auth_headers(manager_token))
    assert manager_list_response.status_code == 200
    assert manager_list_response.json()["total"] == 1

    manager_approval_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-approval",
        headers=auth_headers(manager_token),
        json={"comment": "Approved for client meeting."},
    )
    assert manager_approval_response.status_code == 200
    assert manager_approval_response.json()["status"] == "manager_approved"
    assert manager_approval_response.json()["manager_decided_at"] is not None

    accountant_list_response = client.get("/api/v1/expenses?status=manager_approved", headers=auth_headers(accountant_token))
    assert accountant_list_response.status_code == 200
    assert accountant_list_response.json()["total"] == 1

    accounting_approval_response = client.post(
        f"/api/v1/expenses/{expense['id']}/accounting-approval",
        headers=auth_headers(accountant_token),
        json={"comment": "Receipt and policy checks completed."},
    )
    assert accounting_approval_response.status_code == 200
    assert accounting_approval_response.json()["status"] == "accountant_approved"
    assert accounting_approval_response.json()["accountant_decided_at"] is not None

    payment_pending_response = client.post(
        f"/api/v1/expenses/{expense['id']}/payment-pending",
        headers=auth_headers(accountant_token),
        json={"payment_method": "bank_transfer", "notes": "Scheduled in weekly payment batch."},
    )
    assert payment_pending_response.status_code == 200
    assert payment_pending_response.json()["status"] == "payment_pending"

    paid_response = client.post(
        f"/api/v1/expenses/{expense['id']}/paid",
        headers=auth_headers(accountant_token),
        json={
            "payment_method": "bank_transfer",
            "payment_reference": "BANK-REF-123",
            "notes": "Paid in June reimbursement batch.",
        },
    )
    assert paid_response.status_code == 200
    assert paid_response.json()["status"] == "paid"
    assert paid_response.json()["paid_at"] is not None

    expense_id = UUID(expense["id"])
    decisions = db_session.query(ApprovalDecision).filter(ApprovalDecision.expense_id == expense_id).all()
    assert [(decision.stage, decision.decision) for decision in decisions] == [
        ("manager", "approved"),
        ("accounting", "approved"),
    ]
    assert db_session.query(Payment).filter(Payment.expense_id == expense_id).count() == 2
    assert audit_event_count(db_session, "manager_approved") == 1
    assert audit_event_count(db_session, "accountant_approved") == 1
    assert audit_event_count(db_session, "payment_pending") == 1
    assert audit_event_count(db_session, "expense_paid") == 1

    audit_response = client.get(
        f"/api/v1/expenses/{expense['id']}/audit-log?limit=3",
        headers=auth_headers(employee_token),
    )
    assert audit_response.status_code == 200
    assert audit_response.json()["total"] == 6
    assert audit_response.json()["limit"] == 3
    assert [item["event_type"] for item in audit_response.json()["items"]] == [
        "expense_created",
        "expense_submitted",
        "manager_approved",
    ]


def test_manager_reject_and_return_paths_enforce_reasons_and_statuses(
    client: TestClient,
    db_session: Session,
) -> None:
    _employee, employee_email, _manager, manager_email, _accountant, accountant_email = create_workflow_users(db_session)
    employee_token = login_user(client, employee_email)
    manager_token = login_user(client, manager_email)
    accountant_token = login_user(client, accountant_email)

    expense = create_expense(client, employee_token)
    missing_reason_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-rejection",
        headers=auth_headers(manager_token),
        json={},
    )
    assert missing_reason_response.status_code == 422

    invalid_status_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-rejection",
        headers=auth_headers(manager_token),
        json={"reason": "Not submitted."},
    )
    assert invalid_status_response.status_code == 409

    client.post(f"/api/v1/expenses/{expense['id']}/submit", headers=auth_headers(employee_token))
    reject_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-rejection",
        headers=auth_headers(manager_token),
        json={"reason": "Receipt does not match submitted amount."},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "manager_rejected"

    returned_expense = create_expense(client, employee_token, title="Needs clearer receipt")
    client.post(f"/api/v1/expenses/{returned_expense['id']}/submit", headers=auth_headers(employee_token))
    return_response = client.post(
        f"/api/v1/expenses/{returned_expense['id']}/return-to-employee",
        headers=auth_headers(manager_token),
        json={"reason": "Please attach a clearer receipt."},
    )
    assert return_response.status_code == 200
    assert return_response.json()["status"] == "returned_to_employee"

    resubmit_response = client.post(
        f"/api/v1/expenses/{returned_expense['id']}/submit",
        headers=auth_headers(employee_token),
    )
    assert resubmit_response.status_code == 200
    assert resubmit_response.json()["status"] == "submitted"

    client.post(
        f"/api/v1/expenses/{returned_expense['id']}/manager-approval",
        headers=auth_headers(manager_token),
        json={},
    )
    accounting_return_response = client.post(
        f"/api/v1/expenses/{returned_expense['id']}/return-to-employee",
        headers=auth_headers(accountant_token),
        json={"reason": "Policy code missing."},
    )
    assert accounting_return_response.status_code == 200
    assert accounting_return_response.json()["status"] == "returned_to_employee"


def test_workflow_role_boundaries_and_invalid_payment_transition(
    client: TestClient,
    db_session: Session,
) -> None:
    _employee, employee_email, manager, manager_email, _accountant, accountant_email = create_workflow_users(db_session)
    other_manager = create_user_with_role(db_session, email="other.manager@example.com", role="manager")
    employee_token = login_user(client, employee_email)
    manager_token = login_user(client, manager_email)
    other_manager_token = login_user(client, other_manager.email)
    accountant_token = login_user(client, accountant_email)

    expense = create_expense(client, employee_token)
    client.post(f"/api/v1/expenses/{expense['id']}/submit", headers=auth_headers(employee_token))

    employee_approval_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-approval",
        headers=auth_headers(employee_token),
        json={},
    )
    assert employee_approval_response.status_code == 403

    other_manager_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-approval",
        headers=auth_headers(other_manager_token),
        json={},
    )
    assert other_manager_response.status_code == 403

    accountant_too_early_response = client.post(
        f"/api/v1/expenses/{expense['id']}/accounting-approval",
        headers=auth_headers(accountant_token),
        json={},
    )
    assert accountant_too_early_response.status_code == 409

    manager_response = client.post(
        f"/api/v1/expenses/{expense['id']}/manager-approval",
        headers=auth_headers(manager_token),
        json={},
    )
    assert manager_response.status_code == 200
    assert manager_response.json()["assigned_manager_id"] == str(manager.id)

    employee_payment_response = client.post(
        f"/api/v1/expenses/{expense['id']}/payment-pending",
        headers=auth_headers(employee_token),
        json={},
    )
    assert employee_payment_response.status_code == 403

    payment_too_early_response = client.post(
        f"/api/v1/expenses/{expense['id']}/payment-pending",
        headers=auth_headers(accountant_token),
        json={},
    )
    assert payment_too_early_response.status_code == 409


def test_accountant_can_access_expense_after_accounting_rejection(
    client: TestClient,
    db_session: Session,
) -> None:
    _employee, employee_email, _manager, manager_email, _accountant, accountant_email = create_workflow_users(db_session)
    employee_token = login_user(client, employee_email)
    manager_token = login_user(client, manager_email)
    accountant_token = login_user(client, accountant_email)

    expense = create_expense(client, employee_token)
    client.post(f"/api/v1/expenses/{expense['id']}/submit", headers=auth_headers(employee_token))
    client.post(
        f"/api/v1/expenses/{expense['id']}/manager-approval",
        headers=auth_headers(manager_token),
        json={},
    )
    rejection_response = client.post(
        f"/api/v1/expenses/{expense['id']}/accounting-rejection",
        headers=auth_headers(accountant_token),
        json={"reason": "Expense is outside reimbursable policy."},
    )
    assert rejection_response.status_code == 200
    assert rejection_response.json()["status"] == "accountant_rejected"

    detail_response = client.get(
        f"/api/v1/expenses/{expense['id']}",
        headers=auth_headers(accountant_token),
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "accountant_rejected"


def test_audit_history_forbidden_for_unrelated_user(client: TestClient) -> None:
    register_user(client, email="owner@example.com")
    owner_token = login_user(client, "owner@example.com")
    expense = create_expense(client, owner_token)

    register_user(client, email="other@example.com")
    other_token = login_user(client, "other@example.com")

    response = client.get(
        f"/api/v1/expenses/{expense['id']}/audit-log",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403
