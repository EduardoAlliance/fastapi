from math import ceil

from pydantic import BaseModel, Field


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Número de página")
    size: int = Field(default=20, ge=1, le=100, description="Elementos por página")


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size) if total else 0,
        )
