from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import CurrentUserResponse, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(request: RegisterRequest, db: Session = Depends(get_db)) -> User:
    return AuthService(db).register(request)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).login(request.email, request.password)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
