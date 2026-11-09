from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.post import Post
from app.models.user import User
from app.repositories.post import PostRepository
from app.schemas.common import Page
from app.schemas.post import PostCreate, PostFilters, PostRead, PostUpdate


class PostService:
    def __init__(self, db: Session) -> None:
        self.repository = PostRepository(db)

    def get_or_404(self, post_id: int) -> Post:
        post = self.repository.get(post_id)
        if post is None:
            raise AppError(404, "post_not_found", "Publicación no encontrada")
        return post

    def list(self, filters: PostFilters) -> Page[PostRead]:
        items, total = self.repository.list(filters)
        return Page.build(
            items=[PostRead.model_validate(post) for post in items],
            total=total,
            params=filters,
        )

    def create(self, payload: PostCreate, author: User) -> PostRead:
        post = self.repository.create(payload, author)
        return PostRead.model_validate(post)

    def update(self, post_id: int, payload: PostUpdate, current_user: User) -> PostRead:
        post = self.get_or_404(post_id)
        self._ensure_can_manage(post, current_user)
        post = self.repository.update(post, payload)
        return PostRead.model_validate(post)

    def delete(self, post_id: int, current_user: User) -> None:
        post = self.get_or_404(post_id)
        self._ensure_can_manage(post, current_user)
        self.repository.delete(post)

    @staticmethod
    def _ensure_can_manage(post: Post, current_user: User) -> None:
        if post.author_id != current_user.id and not current_user.is_superuser:
            raise AppError(
                403,
                "forbidden",
                "Solo el autor o un superusuario puede modificar esta publicación",
            )
