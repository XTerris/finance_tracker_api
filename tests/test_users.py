from app import schemas
from app import models
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
    assert res.status_code == 201
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
def test_incorrect_login(test_user, client, login, password, status_code):
    res = client.post(
        "/login",
        data={"username": login, "password": password},
    )
    assert res.status_code == status_code
    assert res.json().get("detail") == "Invalid credentials"


def test_get_user(test_user, client):
    res = client.get(f"/users/{test_user['id']}")
    assert res.status_code == 200
    user = schemas.User(**res.json())
    assert user.id == test_user["id"]


def test_get_non_existed_user(test_user, client):
    res = client.get(f"/users/{test_user['id'] + 1}")
    assert res.status_code == 404
    assert res.json().get("detail") == "User was not found"


def test_get_all_users(test_user, client):
    res = client.get("/users/")
    assert res.status_code == 200
    assert len(res.json()) == 1
    user = schemas.User(**res.json()[0])


def test_update_user(test_user, logged_client):
    update = {"username": "new_username", "password": "new_password"}
    res = logged_client.put("/users/", json=update)
    assert res.status_code == 200
    updated_user = schemas.User(**res.json())
    assert updated_user.id == test_user["id"]
    assert updated_user.username == update["username"]


def test_anauthorized_update_user(test_user, client):
    update = {"username": "new_username", "password": "new_password"}
    res = client.put("/users/", json=update)
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


def test_delete_user(test_user, logged_client, db_session):
    res = logged_client.delete("/users/")
    assert res.status_code == 204
    user_query = db_session.query(models.User).filter(models.User.id == test_user["id"])
    assert user_query.first() == None


def test_anuthorized_delete_user(test_user, client, db_session):
    res = client.delete("/users/")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"
