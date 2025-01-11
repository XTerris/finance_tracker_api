from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Transaction
from app.oauth2 import create_access_token
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


DB_URL = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOSTNAME}:{settings.DB_PORT}/{settings.DB_NAME}_test"
engine = create_engine(DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db: Session = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def test_user(client):
    user_data = {
        "username": "test_username",
        "login": "test_login",
        "password": "test_password",
    }
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
def token(test_user):
    token = create_access_token(data={"user_id": test_user['id']})
    return token


@pytest.fixture
def logged_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client


@pytest.fixture
def test_transactions(test_user, db_session):
    data = [
        {
            "title": "Salary",
            "type": "Income",
            "amount": "20000",
            "user_id": test_user["id"]
        },
        {
            "title": "Shopping",
            "type": "Outcome",
            "amount": "2000",
            "user_id": test_user["id"]
        },
        {
            "title": "Taxes",
            "type": "Outcome",
            "amount": "500",
            "user_id": test_user["id"]
        },
    ]
    db_session.add_all([Transaction(**trans) for trans in data])
    db_session.commit()
    data = db_session.query(Transaction).all()
    return data