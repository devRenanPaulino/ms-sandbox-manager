import time

import jwt
import mongomock
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.config import settings
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


@pytest.fixture(scope="session")
def rsa_key():
  return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def jwt_config(monkeypatch, rsa_key):
  """Configura a chave pública que o serviço usa para validar os tokens."""
  pem = rsa_key.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
  ).decode()
  monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", pem)
  monkeypatch.setattr(settings, "JWT_ISSUER", "raiz-do-bem")


@pytest.fixture
def make_token(rsa_key):
  pem = rsa_key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
  )

  def _make(groups=("ADMIN",), exp_in=1800, issuer="raiz-do-bem", **extra):
    claims = {"iss": issuer, "sub": "user@raizdobem.org", "exp": int(time.time()) + exp_in, **extra}
    if groups is not None:
      claims["groups"] = list(groups)
    return jwt.encode(claims, pem, algorithm="RS256")

  return _make


@pytest.fixture
def auth_headers(make_token):
  return {"Authorization": f"Bearer {make_token()}"}


@pytest.fixture
def anon_client(mongo_db, fake_gateway):
  app.dependency_overrides[get_database] = lambda: mongo_db
  app.dependency_overrides[get_twilio_gateway] = lambda: fake_gateway

  with TestClient(app) as client:
    yield client

  app.dependency_overrides.clear()


@pytest.fixture
def api_client(anon_client, auth_headers):
  """Cliente já autenticado como colaborador (ADMIN)."""
  anon_client.headers.update(auth_headers)
  return anon_client
