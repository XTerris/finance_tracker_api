from app.config import settings
from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_URL = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOSTNAME}:{settings.DB_PORT}/{settings.DB_NAME}_test"
engine = create_engine(DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()


    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)