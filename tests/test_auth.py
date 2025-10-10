import time
from app import schemas, models, oauth2
from app.config import settings
from fastapi import status
import jwt
import pytest


def test_login(test_user, client):
    res = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    assert res.status_code == 200
    login_res = schemas.TokenWithRefresh(**res.json())

    # Verify access token
    payload = jwt.decode(
        login_res.access_token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
    )
    id = payload.get("user_id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"

    # Verify refresh token is present
    assert login_res.refresh_token is not None
    assert login_res.access_token != login_res.refresh_token


@pytest.mark.parametrize(
    "login, password, status_code",
    [
        ("test_login", "wrong_password", 401),
        ("wrong_login", "test_password", 401),
        ("wrong_login", "wrong_password", 401),
        ("test_login", None, 401),
        (None, "wrong_password", 401),
    ],
)
def test_login_incorrect(test_user, client, login, password, status_code):
    res = client.post(
        "/login",
        data={"username": login, "password": password},
    )
    assert res.status_code == status_code
    assert res.json().get("detail") == "Invalid credentials"


def test_login_returns_refresh_token(client, test_user):
    """Test that login now returns both access and refresh tokens"""
    response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    assert data["access_token"] != data["refresh_token"]


def test_refresh_token_structure(client, test_user):
    """Test that refresh token contains correct payload"""
    response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )

    refresh_token = response.json()["refresh_token"]

    payload = jwt.decode(
        refresh_token,
        oauth2.SECRET_KEY,
        algorithms=[oauth2.ALGORITHM],
    )

    assert payload["type"] == "refresh"
    assert "user_id" in payload
    assert "token_version" in payload
    assert "exp" in payload


def test_refresh_endpoint_creates_new_tokens(client, test_user):
    """Test that /refresh endpoint returns new tokens"""
    login_response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    initial_refresh_token = login_response.json()["refresh_token"]
    initial_access_token = login_response.json()["access_token"]

    # Wait 1 second to ensure different timestamps in JWT
    time.sleep(1)

    refresh_response = client.post(
        f"/refresh?refresh_token={initial_refresh_token}",
    )

    assert refresh_response.status_code == status.HTTP_200_OK
    data = refresh_response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Verify tokens are different
    assert data["access_token"] != initial_access_token
    assert data["refresh_token"] != initial_refresh_token


def test_old_refresh_token_invalidated_after_refresh(client, test_user):
    """Test that old refresh token cannot be reused (token rotation)"""
    login_response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    old_refresh_token = login_response.json()["refresh_token"]

    client.post(f"/refresh?refresh_token={old_refresh_token}")

    reuse_response = client.post(
        f"/refresh?refresh_token={old_refresh_token}",
    )

    assert reuse_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert reuse_response.json()["detail"] == "Invalid or expired refresh token"


def test_token_version_increments_on_refresh(client, test_user, db_session):
    """Test that token_version increments when refreshing"""
    user = (
        db_session.query(models.User)
        .filter(models.User.login == test_user["login"])
        .first()
    )
    initial_version = user.token_version

    login_response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    refresh_token = login_response.json()["refresh_token"]

    client.post(f"/refresh?refresh_token={refresh_token}")

    db_session.refresh(user)
    assert user.token_version == initial_version + 1


def test_invalid_refresh_token_rejected(client):
    """Test that invalid refresh token is rejected"""
    response = client.post(
        "/refresh?refresh_token=invalid_token",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired refresh token"


def test_access_token_as_refresh_token_rejected(client, test_user):
    """Test that access token cannot be used as refresh token"""
    login_response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        f"/refresh?refresh_token={access_token}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_invalidates_refresh_token(client, test_user, logged_client):
    """Test that logout invalidates the refresh token"""
    login_response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = logged_client.post("/logout")
    assert logout_response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post(
        f"/refresh?refresh_token={refresh_token}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_increments_token_version(client, test_user, logged_client, db_session):
    """Test that logout increments token version"""
    user = (
        db_session.query(models.User)
        .filter(models.User.login == test_user["login"])
        .first()
    )
    version_before = user.token_version

    logged_client.post("/logout")

    db_session.refresh(user)
    assert user.token_version == version_before + 1


def test_logout_clears_refresh_token_in_db(
    client, test_user, logged_client, db_session
):
    """Test that logout clears refresh_token from database"""
    client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )

    user = (
        db_session.query(models.User)
        .filter(models.User.login == test_user["login"])
        .first()
    )
    assert user.refresh_token is not None

    logged_client.post("/logout")

    db_session.refresh(user)
    assert user.refresh_token is None


def test_refresh_token_stored_in_database(client, test_user, db_session):
    """Test that refresh token is stored in database"""
    response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    refresh_token = response.json()["refresh_token"]

    user = (
        db_session.query(models.User)
        .filter(models.User.login == test_user["login"])
        .first()
    )
    assert user.refresh_token == refresh_token


def test_multiple_logins_invalidate_previous_refresh_tokens(
    client, test_user, db_session
):
    """Test that logging in again invalidates previous refresh tokens"""
    first_login = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    first_refresh_token = first_login.json()["refresh_token"]

    # Wait 1 second to ensure different timestamps in JWT
    time.sleep(1)

    second_login = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    second_refresh_token = second_login.json()["refresh_token"]

    # Tokens should be different (different exp times and stored token changed)
    assert first_refresh_token != second_refresh_token

    # First refresh token should no longer work (overwritten in DB)
    response = client.post(
        f"/refresh?refresh_token={first_refresh_token}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Second refresh token should work
    response = client.post(
        f"/refresh?refresh_token={second_refresh_token}",
    )

    assert response.status_code == status.HTTP_200_OK


def test_refresh_token_updates_in_database_after_refresh(client, test_user, db_session):
    """Test that refresh token in DB updates after using /refresh"""
    login_response = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        f"/refresh?refresh_token={old_refresh_token}",
    )
    new_refresh_token = refresh_response.json()["refresh_token"]

    user = (
        db_session.query(models.User)
        .filter(models.User.login == test_user["login"])
        .first()
    )
    assert user.refresh_token == new_refresh_token
    assert user.refresh_token != old_refresh_token
