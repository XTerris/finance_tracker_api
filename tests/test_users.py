from app import schemas
from app.config import settings
import jwt
import pytest


def test_create_user(client):
    username = "test_username"
    login = "test_login"
    password = "test_password"
    res = client.post(
        "/users/", json={"username": username, "login": login, "password": password}
    )
    new_user = schemas.User(**res.json())
    assert new_user.username == username
    assert new_user.login == login


def test_login(test_user, client):
    res = client.post(
        "/login",
        data={"username": test_user["login"], "password": test_user["password"]},
    )
    assert res.status_code == 200
    login_res = schemas.Token(**res.json())
    payload = jwt.decode(
        login_res.access_token, settings.SECRET_KEY, algorithms=settings.ALGORITHM
    )
    id = payload.get("user_id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"


@pytest.mark.parametrize("login, password, status_code", [
    ("test_login", "wrong_password", 401),
    ("wrong_login", "test_password", 401),
    ("wrong_login", "wrong_password", 401),
    ("test_login", None, 401),
    (None, "wrong_password", 401)
])
def test_incorrect_login(test_user, client, login, password, status_code):
    res = client.post(
        "/login",
        data={"username": login,
              "password": password},
    )
    assert res.status_code == status_code
    assert res.json().get("detail") == "Invalid credentials"
