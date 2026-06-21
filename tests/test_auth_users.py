from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.services.bootstrap import seed_admin_user


def register_user(
    client: TestClient,
    email: str = "employee@example.com",
    password: str = "strong-password",
    full_name: str = "Employee User",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
        },
    )
    assert response.status_code == 201
    return response.json()


def login_user(
    client: TestClient,
    email: str,
    password: str = "strong-password",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    return body["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_admin(client: TestClient, db_session: Session) -> str:
    register_user(client, email="admin@example.com", full_name="Admin User")
    token = login_user(client, "admin@example.com")

    # The first admin promotion is test setup only; application users cannot self-promote.
    user = db_session.query(User).filter(User.email == "admin@example.com").one()
    user.role = "admin"
    db_session.commit()
    return token


def test_register_creates_employee_without_password_hash(client: TestClient) -> None:
    body = register_user(client, email="Employee@Example.com")

    assert body["email"] == "employee@example.com"
    assert body["role"] == "employee"
    assert body["is_active"] is True
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    register_user(client, email="employee@example.com")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "EMPLOYEE@example.com",
            "password": "strong-password",
            "full_name": "Other Employee",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "user_email_conflict"


def test_login_and_me_return_current_user(client: TestClient) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")

    response = client.get("/api/v1/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["email"] == "employee@example.com"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    register_user(client, email="employee@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "employee@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_invalid_credentials"


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_not_authenticated"


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers("not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_invalid_token"


def test_openapi_documents_http_bearer_auth(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    security_schemes = schema["components"]["securitySchemes"]
    assert security_schemes["HTTPBearer"]["type"] == "http"
    assert security_schemes["HTTPBearer"]["scheme"] == "bearer"


def test_seed_admin_creates_and_updates_admin_user(db_session: Session) -> None:
    user, created = seed_admin_user(
        db_session,
        email="Admin@Example.com",
        password="first-password",
        full_name="Admin User",
    )

    assert created is True
    assert user.email == "admin@example.com"
    assert user.role == "admin"
    assert user.is_active is True

    user.role = "employee"
    user.is_active = False
    db_session.commit()

    updated_user, updated_created = seed_admin_user(
        db_session,
        email="admin@example.com",
        password="second-password",
        full_name="Updated Admin",
    )

    assert updated_created is False
    assert updated_user.id == user.id
    assert updated_user.full_name == "Updated Admin"
    assert updated_user.role == "admin"
    assert updated_user.is_active is True
    assert updated_user.deactivated_at is None
    assert verify_password("second-password", updated_user.hashed_password)


def test_non_admin_cannot_create_users(client: TestClient) -> None:
    register_user(client, email="employee@example.com")
    token = login_user(client, "employee@example.com")

    response = client.post(
        "/api/v1/users",
        headers=auth_headers(token),
        json={
            "email": "manager@example.com",
            "password": "strong-password",
            "full_name": "Manager User",
            "role": "manager",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth_forbidden"


def test_user_can_read_self_but_not_another_user(client: TestClient) -> None:
    first_user = register_user(client, email="first@example.com")
    second_user = register_user(client, email="second@example.com")
    token = login_user(client, "first@example.com")

    self_response = client.get(
        f"/api/v1/users/{first_user['id']}",
        headers=auth_headers(token),
    )
    assert self_response.status_code == 200
    assert self_response.json()["email"] == "first@example.com"

    other_response = client.get(
        f"/api/v1/users/{second_user['id']}",
        headers=auth_headers(token),
    )
    assert other_response.status_code == 403
    assert other_response.json()["error"]["code"] == "auth_forbidden"


def test_admin_can_create_list_update_and_deactivate_user(
    client: TestClient,
    db_session: Session,
) -> None:
    admin_token = create_admin(client, db_session)

    create_response = client.post(
        "/api/v1/users",
        headers=auth_headers(admin_token),
        json={
            "email": "manager@example.com",
            "password": "strong-password",
            "full_name": "Manager User",
            "role": "manager",
            "department": "Sales",
        },
    )
    assert create_response.status_code == 201
    manager = create_response.json()
    assert manager["role"] == "manager"

    list_response = client.get(
        "/api/v1/users?role=manager&is_active=true",
        headers=auth_headers(admin_token),
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    update_response = client.patch(
        f"/api/v1/users/{manager['id']}",
        headers=auth_headers(admin_token),
        json={"full_name": "Updated Manager", "department": "Operations"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Updated Manager"

    deactivate_response = client.post(
        f"/api/v1/users/{manager['id']}/deactivate",
        headers=auth_headers(admin_token),
    )
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False
    assert deactivate_response.json()["deactivated_at"] is not None


def test_inactive_user_cannot_login(
    client: TestClient,
    db_session: Session,
) -> None:
    admin_token = create_admin(client, db_session)
    create_response = client.post(
        "/api/v1/users",
        headers=auth_headers(admin_token),
        json={
            "email": "inactive@example.com",
            "password": "strong-password",
            "full_name": "Inactive User",
            "role": "employee",
            "is_active": False,
        },
    )
    assert create_response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "strong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_invalid_credentials"
