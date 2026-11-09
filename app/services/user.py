from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserFilters, UserRead, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def get_or_404(self, user_id: int) -> User:
        user = self.repository.get(user_id)
        if user is None:
            raise AppError(404, "user_not_found", "Usuario no encontrado")
        return user

    def list(self, filters: UserFilters) -> Page[UserRead]:
        items, total = self.repository.list(filters)
        return Page.build(
            items=[UserRead.model_validate(user) for user in items],
            total=total,
            params=filters,
        )

    def create(self, payload: UserCreate) -> UserRead:
        if self.repository.get_by_email(payload.email) is not None:
            raise AppError(409, "email_already_exists", "El email ya está registrado")

        try:
            user = self.repository.create(payload, hash_password(payload.password))
        except IntegrityError:
            self.repository.db.rollback()
            raise AppError(
                409,
                "email_already_exists",
                "El email ya está registrado",
            ) from None

        return UserRead.model_validate(user)

    def update(self, user_id: int, payload: UserUpdate) -> UserRead:
        user = self.get_or_404(user_id)

        new_email = payload.email.lower() if payload.email else None
        if new_email and new_email != user.email:
            existing = self.repository.get_by_email(new_email)
            if existing is not None:
                raise AppError(409, "email_already_exists", "El email ya está registrado")

        if payload.password:
            user.hashed_password = hash_password(payload.password)

        user = self.repository.update(user, payload)
        return UserRead.model_validate(user)

    def delete(self, user_id: int) -> None:
        user = self.get_or_404(user_id)
        self.repository.delete(user)
