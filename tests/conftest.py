import mongomock
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_database
from app.gateways.twilio_gateway import get_twilio_gateway
from app.main import app
from tests.fakes import FakeChatRepository, FakeNotificationGateway


@pytest.fixture
def fake_repo() -> FakeChatRepository:
  return FakeChatRepository()


@pytest.fixture
def fake_gateway() -> FakeNotificationGateway:
  return FakeNotificationGateway(configured=True)


@pytest.fixture
def mongo_db():
  client = mongomock.MongoClient()
  return client["db_raiz_do_bem_test"]


@pytest.fixture
def api_client(mongo_db, fake_gateway):
  app.dependency_overrides[get_database] = lambda: mongo_db
  app.dependency_overrides[get_twilio_gateway] = lambda: fake_gateway

  with TestClient(app) as client:
    yield client

  app.dependency_overrides.clear()
