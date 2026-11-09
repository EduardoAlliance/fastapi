from datetime import timedelta

from app.core.security import create_access_token, create_refresh_token, decode_token
from tests.helpers import (
    login_user,
    register_and_login,
    register_user,
    set_user_active,
)


def test_register_and_login(client):
    register_response = register_user(
        client,
        "ana@example.com",
        full_name="Ana Pérez",
    )

    assert register_response.status_code == 201
    registered = register_response.json()
    assert registered["email"] == "ana@example.com"
    assert registered["full_name"] == "Ana Pérez"
    assert registered["is_superuser"] is False
    assert "hashed_password" not in registered

    login_response = login_user(client, "ANA@EXAMPLE.COM")

    assert login_response.status_code == 200
    token = login_response.json()
    assert token["token_type"] == "bearer"
    assert token["access_token"]
    assert token["refresh_token"]
    assert token["expires_in"] > 0


def test_register_duplicate_email_returns_conflict(client):
    register_user(client, "ana@example.com")
    response = register_user(client, "ANA@EXAMPLE.COM")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_exists"


def test_register_does_not_allow_superuser_escalation(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ana@example.com",
            "password": "secreto123",
            "is_superuser": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["is_superuser"] is False


def test_login_with_wrong_password(client):
    register_user(client, "ana@example.com")

    response = login_user(client, "ana@example.com", "incorrecta")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_with_unknown_email(client):
    response = login_user(client, "nadie@example.com")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_with_inactive_user(client, db):
    register_user(client, "ana@example.com")
    set_user_active(db, "ana@example.com", False)

    response = login_user(client, "ana@example.com")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "inactive_user"


def test_read_me(client):
    user, headers = register_and_login(client, "ana@example.com")

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]
    assert response.json()["email"] == "ana@example.com"


def test_read_me_without_token(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_read_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer esto-no-es-un-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_read_me_with_expired_token(client):
    user, _ = register_and_login(client, "ana@example.com")
    expired = create_access_token(
        subject=str(user["id"]),
        expires_delta=timedelta(minutes=-1),
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_expired"


def test_inactive_user_with_valid_token_is_forbidden(client, db):
    _, headers = register_and_login(client, "ana@example.com")
    set_user_active(db, "ana@example.com", False)

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "inactive_user"


def test_refresh_returns_new_tokens(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != refresh_token

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"


def test_refresh_with_access_token_is_rejected(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["access_token"]},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_refresh_with_invalid_token_is_rejected(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "esto-no-es-un-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_refresh_with_expired_token_is_rejected(client):
    user, _ = register_and_login(client, "ana@example.com")
    expired = create_refresh_token(
        subject=str(user["id"]),
        expires_delta=timedelta(minutes=-1),
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_expired"


def test_refresh_with_inactive_user_is_forbidden(client, db):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    set_user_active(db, "ana@example.com", False)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "inactive_user"


def test_refresh_token_cannot_access_protected_routes(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    refresh_token = login.json()["refresh_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_refresh_rotation_keeps_working_with_new_token(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")

    first = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    second = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first.json()["refresh_token"]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["refresh_token"] != first.json()["refresh_token"]

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {second.json()['access_token']}"},
    )
    assert me.status_code == 200


def test_refresh_token_reuse_is_detected(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    refresh_token = login.json()["refresh_token"]

    first = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert first.status_code == 200

    reused = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "token_reused"

    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first.json()["refresh_token"]},
    )
    assert rotated.status_code == 401
    assert rotated.json()["error"]["code"] == "token_revoked"


def test_logout_revokes_refresh_token(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    refresh_token = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 204

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_revoked"


def test_logout_after_rotation_closes_the_session(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")

    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    current_refresh = rotated.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": current_refresh},
    )
    assert logout.status_code == 204

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": current_refresh},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_revoked"


def test_logout_with_access_token_is_rejected(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login.json()["access_token"]},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_logout_with_invalid_token_is_rejected(client):
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "esto-no-es-un-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_logout_accepts_expired_refresh_token(client):
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    valid_refresh = login.json()["refresh_token"]
    payload = decode_token(valid_refresh)

    expired = create_refresh_token(
        subject=str(payload["sub"]),
        expires_delta=timedelta(minutes=-1),
        session_id=str(payload["sid"]),
    )

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": expired},
    )
    assert logout.status_code == 204

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": valid_refresh},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "token_revoked"


def test_refresh_flow_works_when_redis_is_unavailable(client, redis):
    redis.available = False
    register_user(client, "ana@example.com")
    login = login_user(client, "ana@example.com")
    assert login.status_code == 200

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )

    assert response.status_code == 200
    assert response.json()["refresh_token"]
