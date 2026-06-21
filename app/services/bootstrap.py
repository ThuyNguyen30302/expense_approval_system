from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.services.auth import normalize_email


def seed_admin_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
) -> tuple[User, bool]:
    users = UserRepository(db)
    normalized_email = normalize_email(email)
    existing_user = users.get_by_email(normalized_email)

    if existing_user is not None:
        existing_user.full_name = full_name
        existing_user.hashed_password = hash_password(password)
        existing_user.role = UserRole.ADMIN.value
        existing_user.is_active = True
        existing_user.deactivated_at = None
        db.commit()
        db.refresh(existing_user)
        return existing_user, False

    admin = User(
        email=normalized_email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    created_admin = users.create(admin)
    db.commit()
    db.refresh(created_admin)
    return created_admin, True
