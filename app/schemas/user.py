from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class AdminUserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True
    manager_id: UUID | None = None
    department: str | None = Field(default=None, max_length=120)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    manager_id: UUID | None = None
    department: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    manager_id: UUID | None = None
    department: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    deactivated_at: datetime | None = None


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    limit: int
    offset: int
