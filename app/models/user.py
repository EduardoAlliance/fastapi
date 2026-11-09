from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.post import Post


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )
