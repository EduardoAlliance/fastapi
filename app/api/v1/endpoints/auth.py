from fastapi import APIRouter, Request, status

from app.api.deps import RateLimiterDep, RefreshTokenStoreDep, SessionDep
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth import AuthService
from app.services.rate_limit import enforce_login_rate_limit
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: SessionDep) -> UserRead:
    return UserService(db).create(payload)


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: SessionDep,
    limiter: RateLimiterDep,
    tokens: RefreshTokenStoreDep,
) -> TokenResponse:
    client_ip = request.client.host if request.client else "unknown"
    enforce_login_rate_limit(limiter, client_ip, payload.email)
    return AuthService(db, tokens).login(payload.email, payload.password)


@router.post("/refresh")
def refresh(
    payload: RefreshRequest,
    db: SessionDep,
    tokens: RefreshTokenStoreDep,
) -> TokenResponse:
    return AuthService(db, tokens).refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest,
    db: SessionDep,
    tokens: RefreshTokenStoreDep,
) -> None:
    AuthService(db, tokens).logout(payload.refresh_token)
