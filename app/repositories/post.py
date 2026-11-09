from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostFilters, PostUpdate


class PostRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _with_author(self):
        return select(Post).options(joinedload(Post.author))

    def get(self, post_id: int) -> Post | None:
        return self.db.scalar(self._with_author().where(Post.id == post_id))

    def create(self, payload: PostCreate, author: User) -> Post:
        post = Post(
            title=payload.title,
            content=payload.content,
            author=author,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def update(self, post: Post, payload: PostUpdate) -> Post:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(post, field, value)
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete(self, post: Post) -> None:
        self.db.delete(post)
        self.db.commit()

    def list(self, filters: PostFilters) -> tuple[list[Post], int]:
        conditions = []

        if filters.q:
            pattern = f"%{filters.q}%"
            conditions.append(
                or_(
                    Post.title.ilike(pattern),
                    Post.content.ilike(pattern),
                )
            )
        if filters.author_id is not None:
            conditions.append(Post.author_id == filters.author_id)

        total = self.db.scalar(select(func.count()).select_from(Post).where(*conditions)) or 0

        sort_column = getattr(Post, filters.sort_by)
        order_by = asc(sort_column) if filters.order == "asc" else desc(sort_column)

        items = list(
            self.db.scalars(
                self._with_author()
                .where(*conditions)
                .order_by(order_by)
                .offset((filters.page - 1) * filters.size)
                .limit(filters.size)
            ).all()
        )
        return items, total
