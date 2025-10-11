from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Transaction, Category, Account, Goal, Reminder
from app.oauth2 import create_access_token
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from urllib.parse import quote_plus
from datetime import date, timedelta


DB_URL = f"postgresql+psycopg2://{quote_plus(settings.DB_USERNAME)}:{quote_plus(settings.DB_PASSWORD)}@{settings.DB_HOSTNAME}:{settings.DB_PORT}/{settings.DB_NAME}_test"
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
def test_users(client):
    user_data = [
        {
            "username": "test_username",
            "login": "test_login",
            "password": "test_password",
        },
        {
            "username": "test_username_2",
            "login": "test_login_2",
            "password": "test_password",
        },
    ]
    for i in range(len(user_data)):
        res = client.post("/users/", json=user_data[i])
        assert res.status_code == 201
        pwd = user_data[i]["password"]
        user_data[i] = res.json()
        user_data[i]["password"] = pwd
    return user_data


@pytest.fixture
def test_user(test_users):
    return test_users[0]


@pytest.fixture
def token(test_user):
    token = create_access_token(data={"user_id": test_user["id"]})
    return token


@pytest.fixture
def logged_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def test_categories(test_users, db_session):
    data = [
        {
            "name": "Income",
            "user_id": test_users[0]["id"],
        },
        {
            "name": "Expenses",
            "user_id": test_users[0]["id"],
        },
        {
            "name": "Shopping",
            "user_id": test_users[1]["id"],
        },
        {
            "name": "General",
            "user_id": None,  # System-wide category
        },
    ]
    db_session.add_all([Category(**cat) for cat in data])
    db_session.commit()
    data = db_session.query(Category).all()
    return data


@pytest.fixture
def test_accounts(test_users, db_session):
    data = [
        {
            "name": "Checking Account",
            "balance": 1000.0,
            "user_id": test_users[0]["id"],
        },
        {
            "name": "Savings Account",
            "balance": 5000.0,
            "user_id": test_users[0]["id"],
        },
        {
            "name": "Credit Card",
            "balance": -500.0,
            "user_id": test_users[1]["id"],
        },
    ]
    db_session.add_all([Account(**acc) for acc in data])
    db_session.commit()
    data = db_session.query(Account).all()
    return data


@pytest.fixture
def test_transactions(test_users, test_categories, test_accounts, db_session):
    data = [
        {
            "title": "Salary",
            "amount": 20000,
            "is_income": True,
            "user_id": test_users[0]["id"],
            "category_id": test_categories[0].id,  # Income category
            "account_id": test_accounts[0].id,  # Checking Account
        },
        {
            "title": "Shopping",
            "amount": 2000,
            "is_income": False,
            "user_id": test_users[0]["id"],
            "category_id": test_categories[1].id,  # Expenses category
            "account_id": test_accounts[1].id,  # Savings Account
        },
        {
            "title": "Taxes",
            "amount": 500,
            "is_income": False,
            "user_id": test_users[1]["id"],
            "category_id": test_categories[2].id,  # Shopping category
            "account_id": test_accounts[2].id,  # Credit Card
        },
    ]
    db_session.add_all([Transaction(**trans) for trans in data])
    db_session.commit()
    data = db_session.query(Transaction).all()
    return data


@pytest.fixture
def test_goals(test_users, test_accounts, db_session):
    data = [
        {
            "user_id": test_users[0]["id"],
            "account_id": test_accounts[0].id,  # Checking Account
            "target_amount": 10000.0,
            "deadline": date.today() + timedelta(days=365),  # 1 year from now
            "is_completed": False,
        },
        {
            "user_id": test_users[0]["id"],
            "account_id": test_accounts[1].id,  # Savings Account
            "target_amount": 50000.0,
            "deadline": date.today() + timedelta(days=730),  # 2 years from now
            "is_completed": True,
        },
        {
            "user_id": test_users[1]["id"],
            "account_id": test_accounts[2].id,  # Credit Card (other user)
            "target_amount": 1000.0,
            "deadline": date.today() + timedelta(days=90),  # 3 months from now
            "is_completed": False,
        },
    ]
    db_session.add_all([Goal(**goal) for goal in data])
    db_session.commit()
    data = db_session.query(Goal).all()
    return data


@pytest.fixture
def test_reminders(test_users, db_session):
    data = [
        {
            "user_id": test_users[0]["id"],
            "title": "Pay rent",
            "amount": 1200.0,
            "date": date.today() + timedelta(days=30),
            "recurrence": timedelta(days=30),  # Monthly
            "is_active": True,
        },
        {
            "user_id": test_users[0]["id"],
            "title": "Electricity bill",
            "amount": 150.0,
            "date": date.today() + timedelta(days=7),
            "recurrence": None,  # One-time
            "is_active": True,
        },
        {
            "user_id": test_users[0]["id"],
            "title": "Old reminder",
            "amount": 50.0,
            "date": date.today() - timedelta(days=10),
            "recurrence": None,
            "is_active": False,
        },
        {
            "user_id": test_users[1]["id"],
            "title": "Other user reminder",
            "amount": 200.0,
            "date": date.today() + timedelta(days=5),
            "recurrence": None,
            "is_active": True,
        },
    ]
    db_session.add_all([Reminder(**reminder) for reminder in data])
    db_session.commit()
    data = db_session.query(Reminder).all()
    return data
