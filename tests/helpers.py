from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

DEFAULT_PASSWORD = "secreto123"


def register_user(
    client,
    email: str,
    password: str = DEFAULT_PASSWORD,
    full_name: str | None = None,
):
    payload = {"email": email, "password": password}
    if full_name is not None:
        payload["full_name"] = full_name
    return client.post("/api/v1/auth/register", json=payload)


def login_user(client, email: str, password: str = DEFAULT_PASSWORD):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def auth_headers(client, email: str, password: str = DEFAULT_PASSWORD) -> dict[str, str]:
    response = login_user(client, email, password)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def register_and_login(
    client,
    email: str,
    password: str = DEFAULT_PASSWORD,
    full_name: str | None = None,
):
    response = register_user(client, email, password, full_name)
    assert response.status_code == 201, response.text
    return response.json(), auth_headers(client, email, password)


def set_user_active(db: Session, email: str, is_active: bool) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    assert user is not None
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def promote_superuser(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    assert user is not None
    user.is_superuser = True
    db.commit()
    db.refresh(user)
    return user


def superuser_headers(
    client,
    db: Session,
    email: str = "admin@example.com",
    password: str = DEFAULT_PASSWORD,
) -> dict[str, str]:
    register_and_login(client, email, password)
    promote_superuser(db, email)
    return auth_headers(client, email, password)


def create_user(
    client,
    headers: dict[str, str],
    email: str,
    password: str = DEFAULT_PASSWORD,
    full_name: str | None = None,
):
    payload = {"email": email, "password": password}
    if full_name is not None:
        payload["full_name"] = full_name
    return client.post("/api/v1/users", headers=headers, json=payload)


def create_post(
    client,
    headers: dict[str, str],
    title: str = "Publicación de prueba",
    content: str = "Contenido de prueba",
):
    return client.post(
        "/api/v1/posts",
        headers=headers,
        json={"title": title, "content": content},
    )
