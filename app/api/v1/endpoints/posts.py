from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import ActiveUser, SessionDep
from app.schemas.common import Page
from app.schemas.post import PostCreate, PostFilters, PostRead, PostUpdate
from app.services.post import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("")
def list_posts(
    db: SessionDep,
    _: ActiveUser,
    filters: Annotated[PostFilters, Query()],
) -> Page[PostRead]:
    return PostService(db).list(filters)


@router.get("/{post_id}")
def read_post(post_id: int, db: SessionDep, _: ActiveUser) -> PostRead:
    return PostRead.model_validate(PostService(db).get_or_404(post_id))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: SessionDep,
    current_user: ActiveUser,
) -> PostRead:
    return PostService(db).create(payload, current_user)


@router.patch("/{post_id}")
def update_post(
    post_id: int,
    payload: PostUpdate,
    db: SessionDep,
    current_user: ActiveUser,
) -> PostRead:
    return PostService(db).update(post_id, payload, current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: SessionDep, current_user: ActiveUser) -> None:
    PostService(db).delete(post_id, current_user)
