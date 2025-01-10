from app import schemas
from .database import client, db_session


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
