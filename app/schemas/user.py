from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import PageParams


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=150)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=150)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def email_not_null(cls, value: EmailStr | None) -> EmailStr | None:
        if value is None:
            raise ValueError("El email no puede ser nulo")
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserFilters(PageParams):
    q: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    sort_by: Literal["id", "email", "created_at"] = "id"
    order: Literal["asc", "desc"] = "asc"
