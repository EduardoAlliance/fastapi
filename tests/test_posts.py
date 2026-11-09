from tests.helpers import (
    create_post,
    register_and_login,
    superuser_headers,
)


def test_list_posts_requires_authentication(client):
    response = client.get("/api/v1/posts")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_create_post_requires_authentication(client):
    response = client.post(
        "/api/v1/posts",
        json={"title": "Sin token", "content": "No debería crearse"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_create_post(client):
    user, headers = register_and_login(
        client,
        "ana@example.com",
        full_name="Ana Pérez",
    )

    response = create_post(client, headers, "Mi primer post", "Contenido del post")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Mi primer post"
    assert body["content"] == "Contenido del post"
    assert body["author_id"] == user["id"]
    assert body["author"]["id"] == user["id"]
    assert body["author"]["email"] == "ana@example.com"
    assert body["author"]["full_name"] == "Ana Pérez"
    assert "created_at" in body
    assert "updated_at" in body


def test_create_post_ignores_author_id_from_payload(client):
    user, headers = register_and_login(client, "ana@example.com")
    other, _ = register_and_login(client, "zoe@example.com")

    response = client.post(
        "/api/v1/posts",
        headers=headers,
        json={
            "title": "Autoría forzada",
            "content": "El autor debe ser el usuario autenticado",
            "author_id": other["id"],
        },
    )

    assert response.status_code == 201
    assert response.json()["author_id"] == user["id"]


def test_create_post_validation_error(client):
    _, headers = register_and_login(client, "ana@example.com")

    response = client.post(
        "/api/v1/posts",
        headers=headers,
        json={"title": "   ", "content": ""},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert len(body["error"]["details"]) >= 2


def test_list_posts_with_pagination_and_search(client):
    _, headers = register_and_login(client, "ana@example.com")
    for index in range(3):
        create_post(
            client,
            headers,
            title=f"Paginación {index}",
            content=f"Contenido {index}",
        )

    response = client.get(
        "/api/v1/posts",
        headers=headers,
        params={"q": "Paginación", "page": 1, "size": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["size"] == 2
    assert body["pages"] == 2
    assert len(body["items"]) == 2


def test_list_posts_filter_by_author(client):
    ana, ana_headers = register_and_login(client, "ana@example.com")
    zoe, zoe_headers = register_and_login(client, "zoe@example.com")
    create_post(client, ana_headers, "Post de Ana", "Contenido de Ana")
    create_post(client, zoe_headers, "Post de Zoe", "Contenido de Zoe")

    response = client.get(
        "/api/v1/posts",
        headers=ana_headers,
        params={"author_id": zoe["id"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["author_id"] == zoe["id"]
    assert body["items"][0]["author"]["email"] == "zoe@example.com"
    assert ana["id"] != zoe["id"]


def test_read_post_not_found(client):
    _, headers = register_and_login(client, "ana@example.com")

    response = client.get("/api/v1/posts/999", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "post_not_found"


def test_update_own_post(client):
    _, headers = register_and_login(client, "ana@example.com")
    post = create_post(client, headers).json()

    response = client.patch(
        f"/api/v1/posts/{post['id']}",
        headers=headers,
        json={"title": "Título actualizado", "content": "Contenido actualizado"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Título actualizado"
    assert body["content"] == "Contenido actualizado"


def test_update_other_post_forbidden(client):
    _, ana_headers = register_and_login(client, "ana@example.com")
    _, zoe_headers = register_and_login(client, "zoe@example.com")
    post = create_post(client, ana_headers).json()

    response = client.patch(
        f"/api/v1/posts/{post['id']}",
        headers=zoe_headers,
        json={"title": "Intento no permitido"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_superuser_can_update_other_post(client, db):
    headers = superuser_headers(client, db)
    _, ana_headers = register_and_login(client, "ana@example.com")
    post = create_post(client, ana_headers).json()

    response = client.patch(
        f"/api/v1/posts/{post['id']}",
        headers=headers,
        json={"title": "Editado por admin"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Editado por admin"


def test_update_post_rejects_null_fields(client):
    _, headers = register_and_login(client, "ana@example.com")
    post = create_post(client, headers).json()

    response = client.patch(
        f"/api/v1/posts/{post['id']}",
        headers=headers,
        json={"title": None},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_delete_own_post(client):
    _, headers = register_and_login(client, "ana@example.com")
    post = create_post(client, headers).json()

    response = client.delete(f"/api/v1/posts/{post['id']}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""

    missing = client.get(f"/api/v1/posts/{post['id']}", headers=headers)
    assert missing.status_code == 404


def test_delete_other_post_forbidden(client):
    _, ana_headers = register_and_login(client, "ana@example.com")
    _, zoe_headers = register_and_login(client, "zoe@example.com")
    post = create_post(client, ana_headers).json()

    response = client.delete(f"/api/v1/posts/{post['id']}", headers=zoe_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_superuser_can_delete_other_post(client, db):
    headers = superuser_headers(client, db)
    _, ana_headers = register_and_login(client, "ana@example.com")
    post = create_post(client, ana_headers).json()

    response = client.delete(f"/api/v1/posts/{post['id']}", headers=headers)

    assert response.status_code == 204

    missing = client.get(f"/api/v1/posts/{post['id']}", headers=headers)
    assert missing.status_code == 404


def test_delete_user_cascades_posts(client, db):
    headers = superuser_headers(client, db)
    ana, ana_headers = register_and_login(client, "ana@example.com")
    post = create_post(client, ana_headers).json()

    response = client.delete(f"/api/v1/users/{ana['id']}", headers=headers)
    assert response.status_code == 204

    missing = client.get(f"/api/v1/posts/{post['id']}", headers=headers)
    assert missing.status_code == 404
