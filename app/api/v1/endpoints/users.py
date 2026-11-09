from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ActiveUser, SessionDep, SuperuserDep
from app.core.exceptions import AppError
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserFilters, UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_me(current_user: ActiveUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("")
def list_users(
    db: SessionDep,
    _: ActiveUser,
    filters: Annotated[UserFilters, Query()],
) -> Page[UserRead]:
    return UserService(db).list(filters)


@router.get("/{user_id}")
def read_user(user_id: int, db: SessionDep, _: ActiveUser) -> UserRead:
    return UserRead.model_validate(UserService(db).get_or_404(user_id))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: SessionDep, _: SuperuserDep) -> UserRead:
    return UserService(db).create(payload)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: SessionDep,
    current_user: ActiveUser,
) -> UserRead:
    if user_id != current_user.id and not current_user.is_superuser:
        raise AppError(403, "forbidden", "Solo puedes editar tu propio perfil")
    return UserService(db).update(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: SessionDep, _: SuperuserDep) -> None:
    UserService(db).delete(user_id)
