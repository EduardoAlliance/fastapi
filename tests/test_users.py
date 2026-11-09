from tests.helpers import (
    create_user,
    login_user,
    register_and_login,
    superuser_headers,
)


def test_list_users_requires_authentication(client):
    response = client.get("/api/v1/users")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_create_user_requires_superuser(client):
    _, headers = register_and_login(client, "ana@example.com")

    response = create_user(client, headers, "zoe@example.com")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_superuser_can_create_user(client, db):
    headers = superuser_headers(client, db)

    response = create_user(client, headers, "zoe@example.com", full_name="Zoe")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "zoe@example.com"
    assert body["full_name"] == "Zoe"
    assert body["is_active"] is True
    assert body["is_superuser"] is False
    assert "hashed_password" not in body
    assert "password" not in body


def test_create_duplicate_email_returns_conflict(client, db):
    headers = superuser_headers(client, db)
    create_user(client, headers, "zoe@example.com")

    response = create_user(client, headers, "ZOE@EXAMPLE.COM")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_exists"


def test_create_user_validation_error(client, db):
    headers = superuser_headers(client, db)

    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={"email": "no-es-email", "password": "corta"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert len(body["error"]["details"]) >= 2


def test_list_users_with_pagination(client, db):
    headers = superuser_headers(client, db)
    for index in range(3):
        create_user(client, headers, f"pagination-{index}@example.com")

    response = client.get(
        "/api/v1/users",
        headers=headers,
        params={"q": "pagination-", "page": 1, "size": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["size"] == 2
    assert body["pages"] == 2
    assert len(body["items"]) == 2


def test_list_users_with_search_and_sort(client, db):
    headers = superuser_headers(client, db)
    create_user(client, headers, "zoe@example.com")
    create_user(client, headers, "ana@example.com")

    response = client.get(
        "/api/v1/users",
        headers=headers,
        params={"q": "ana@", "sort_by": "email", "order": "asc"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "ana@example.com"


def test_read_user_not_found(client, db):
    headers = superuser_headers(client, db)

    response = client.get("/api/v1/users/999", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


def test_update_own_profile(client):
    user, headers = register_and_login(client, "ana@example.com")

    response = client.patch(
        f"/api/v1/users/{user['id']}",
        headers=headers,
        json={"full_name": "Ana Actualizada", "password": "nuevaClave123"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Ana Actualizada"

    login_response = login_user(client, "ana@example.com", "nuevaClave123")
    assert login_response.status_code == 200


def test_update_other_user_forbidden(client):
    _, ana_headers = register_and_login(client, "ana@example.com")
    zoe, _ = register_and_login(client, "zoe@example.com")

    response = client.patch(
        f"/api/v1/users/{zoe['id']}",
        headers=ana_headers,
        json={"full_name": "Intento no permitido"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_superuser_can_update_other_user(client, db):
    headers = superuser_headers(client, db)
    zoe, _ = register_and_login(client, "zoe@example.com")

    response = client.patch(
        f"/api/v1/users/{zoe['id']}",
        headers=headers,
        json={"full_name": "Zoe Actualizada"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Zoe Actualizada"


def test_update_user_duplicate_email(client, db):
    headers = superuser_headers(client, db)
    create_user(client, headers, "ana@example.com")
    zoe = create_user(client, headers, "zoe@example.com").json()

    response = client.patch(
        f"/api/v1/users/{zoe['id']}",
        headers=headers,
        json={"email": "ANA@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_exists"


def test_delete_requires_superuser(client):
    user, headers = register_and_login(client, "ana@example.com")

    response = client.delete(f"/api/v1/users/{user['id']}", headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_superuser_can_delete_user(client, db):
    headers = superuser_headers(client, db)
    target = create_user(client, headers, "zoe@example.com").json()

    response = client.delete(f"/api/v1/users/{target['id']}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""

    missing = client.get(f"/api/v1/users/{target['id']}", headers=headers)
    assert missing.status_code == 404
