from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserFilters, UserUpdate


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(self, payload: UserCreate, hashed_password: str) -> User:
        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, payload: UserUpdate) -> User:
        data = payload.model_dump(exclude_unset=True, exclude={"password"})
        if data.get("email"):
            data["email"] = data["email"].lower()
        for field, value in data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

    def list(self, filters: UserFilters) -> tuple[list[User], int]:
        conditions = []

        if filters.q:
            pattern = f"%{filters.q}%"
            conditions.append(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
        if filters.is_active is not None:
            conditions.append(User.is_active == filters.is_active)

        total = self.db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0

        sort_column = getattr(User, filters.sort_by)
        order_by = asc(sort_column) if filters.order == "asc" else desc(sort_column)

        items = list(
            self.db.scalars(
                select(User)
                .where(*conditions)
                .order_by(order_by)
                .offset((filters.page - 1) * filters.size)
                .limit(filters.size)
            ).all()
        )
        return items, total
