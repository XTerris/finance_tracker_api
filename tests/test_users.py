from app import schemas
from app import models


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


def test_get_user(test_user, client):
    res = client.get(f"/users/{test_user['id']}")
    assert res.status_code == 200
    user = schemas.User(**res.json())
    assert user.id == test_user["id"]


def test_get_user_non_existent(test_user, client):
    res = client.get("/users/1234567")
    assert res.status_code == 404
    assert res.json().get("detail") == "User was not found"


def test_get_all_users(test_users, client):
    res = client.get("/users/")
    assert res.status_code == 200
    assert len(res.json()) == len(test_users)
    user = schemas.User(**res.json()[0])


def test_update_user(test_user, logged_client):
    update = {"username": "new_username", "password": "new_password"}
    res = logged_client.put("/users/", json=update)
    assert res.status_code == 200
    updated_user = schemas.User(**res.json())
    assert updated_user.id == test_user["id"]
    assert updated_user.username == update["username"]


def test_update_user_unauthorized(test_user, client):
    update = {"username": "new_username", "password": "new_password"}
    res = client.put("/users/", json=update)
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


def test_delete_user(test_user, logged_client, db_session):
    res = logged_client.delete("/users/")
    assert res.status_code == 204
    user_query = db_session.query(models.User).filter(models.User.id == test_user["id"])
    assert user_query.first() == None


def test_delete_user_unauthorized(test_user, client):
    res = client.delete("/users/")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"


def test_get_current_user(test_user, logged_client):
    res = logged_client.get("/users/me")
    assert res.status_code == 200
    user = schemas.User(**res.json())
    assert user.id == test_user["id"]
    assert user.username == test_user["username"]
    assert user.login == test_user["login"]


def test_get_current_user_unauthorized(test_user, client):
    res = client.get("/users/me")
    assert res.status_code == 401
    assert res.json().get("detail") == "Not authenticated"
