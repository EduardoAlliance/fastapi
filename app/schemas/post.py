from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
)

from app.schemas.common import PageParams

PostTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
PostContent = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class PostAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None


class PostBase(BaseModel):
    title: PostTitle
    content: PostContent


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: PostTitle | None = None
    content: PostContent | None = None

    @field_validator("title", "content")
    @classmethod
    def not_null(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            raise ValueError(f"El campo {info.field_name} no puede ser nulo")
        return value


class PostRead(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    author: PostAuthor
    created_at: datetime
    updated_at: datetime


class PostFilters(PageParams):
    q: str | None = Field(default=None, min_length=1, max_length=100)
    author_id: int | None = Field(default=None, ge=1)
    sort_by: Literal["id", "title", "created_at"] = "id"
    order: Literal["asc", "desc"] = "asc"
