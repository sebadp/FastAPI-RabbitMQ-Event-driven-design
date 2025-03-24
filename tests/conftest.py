import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient

# Base de datos de prueba en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
import pytest
from unittest.mock import MagicMock
from app.events.publisher import EventPublisher


@pytest.fixture(scope="function", autouse=True)
def mock_rabbitmq(monkeypatch):
    """Mockea RabbitMQ para evitar dependencias en los tests"""
    mock_publisher = MagicMock()
    monkeypatch.setattr(EventPublisher, "publish_event", mock_publisher.publish_event)


@pytest.fixture(scope="function")
def db_session():
    """Crea una base de datos de prueba para cada test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Configura un cliente de prueba para FastAPI"""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
