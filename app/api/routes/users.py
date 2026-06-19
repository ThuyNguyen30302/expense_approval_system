from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_admin
from app.models.user import User, UserRole
from app.schemas.user import AdminUserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.users import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserListResponse:
    users, total = UserService(db).list_users(
        limit=limit,
        offset=offset,
        role=role.value if role is not None else None,
        is_active=is_active,
    )
    return UserListResponse(items=users, total=total, limit=limit, offset=offset)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    request: AdminUserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    return UserService(db).create_user(request)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    return UserService(db).get_user_for_request(user_id, current_user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    request: UserUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    return UserService(db).update_user(user_id, request)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    return UserService(db).deactivate_user(user_id)
