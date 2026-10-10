from urllib.parse import quote

import pytest
from twilio.request_validator import RequestValidator

from app.core.config import settings

WEBHOOK_URL = "http://testserver/chat/webhook"


@pytest.fixture
def signed_webhook(monkeypatch):
  monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "token-de-teste")
  monkeypatch.setattr(settings, "TWILIO_WEBHOOK_URL", WEBHOOK_URL)

  def _post(client, data, signature=None):
    sig = signature if signature is not None else RequestValidator("token-de-teste").compute_signature(WEBHOOK_URL, data)
    return client.post("/chat/webhook", data=data, headers={"X-Twilio-Signature": sig})

  return _post


class TestSendMessage:
  def test_send_message_returns_201_and_persists(self, api_client):
    response = api_client.post("/chat/send", json={"tel_client": "+5511999999999", "text": "Olá"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "Mensagem Enviada com sucesso"
    assert body["id_twilio"] == "SM_FAKE_TEXT"


class TestWebhook:
  def test_webhook_persists_incoming_message_and_returns_200(self, api_client, signed_webhook):
    response = signed_webhook(
      api_client,
      {"Body": "Oi, tenho uma dúvida", "From": "whatsapp:+5511988887777", "MessageSid": "SM999"},
    )

    assert response.status_code == 200

    history = api_client.get(f"/chat/history/{quote('+5511988887777', safe='')}")
    assert history.status_code == 200
    assert history.json()[0]["text"] == "Oi, tenho uma dúvida"
    assert history.json()[0]["direction"] == "entrada"


class TestHistory:
  def test_get_history_returns_empty_list_for_unknown_phone(self, api_client):
    response = api_client.get(f"/chat/history/{quote('+5511000000000', safe='')}")

    assert response.status_code == 200
    assert response.json() == []


class TestInitiate:
  def test_initiate_returns_503_when_gateway_not_configured(self, api_client, fake_gateway):
    fake_gateway.configured = False

    response = api_client.post(
      "/chat/initiate",
      json={"tel_client": "+5511999999999", "param_1": "Segunda", "param_2": "10h"},
    )

    assert response.status_code == 503

  def test_initiate_returns_200_and_opens_window_when_configured(self, api_client):
    response = api_client.post(
      "/chat/initiate",
      json={"tel_client": "+5511999999999", "param_1": "Segunda", "param_2": "10h"},
    )

    assert response.status_code == 200
    assert response.json()["id_twilio"] == "SM_FAKE_TEMPLATE"


class TestConversationsAndRead:
  def test_conversations_and_mark_as_read_flow(self, api_client, signed_webhook):
    signed_webhook(
      api_client,
      {"Body": "Oi", "From": "whatsapp:+5511977776666", "MessageSid": "SM1"},
    )

    conversations = api_client.get("/chat/conversations")
    assert conversations.status_code == 200
    assert conversations.json()[0]["unread_count"] == 1

    read_response = api_client.put(f"/chat/read/{quote('+5511977776666', safe='')}")
    assert read_response.status_code == 200
    assert read_response.json()["messagens_updated"] == 1

    conversations_after = api_client.get("/chat/conversations")
    assert conversations_after.json()[0]["unread_count"] == 0


class TestAutenticacao:
  ROTAS = [
    ("get", "/chat/conversations"),
    ("get", "/chat/history/%2B5511999999999"),
    ("put", "/chat/read/%2B5511999999999"),
    ("post", "/chat/send"),
    ("post", "/chat/initiate"),
  ]

  @pytest.mark.parametrize("metodo,rota", ROTAS)
  def test_rotas_exigem_token(self, anon_client, metodo, rota):
    assert getattr(anon_client, metodo)(rota).status_code == 401

  def test_token_expirado_retorna_401(self, anon_client, make_token):
    token = make_token(exp_in=-60)
    r = anon_client.get("/chat/conversations", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401

  def test_token_de_outro_emissor_retorna_401(self, anon_client, make_token):
    token = make_token(issuer="outro")
    r = anon_client.get("/chat/conversations", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401

  def test_token_assinado_por_outra_chave_retorna_401(self, anon_client):
    r = anon_client.get("/chat/conversations", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401

  def test_refresh_token_sem_groups_retorna_403(self, anon_client, make_token):
    token = make_token(groups=None, type="refresh")
    r = anon_client.get("/chat/conversations", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

  def test_sem_chave_configurada_falha_fechado(self, anon_client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY", "")
    monkeypatch.setattr(settings, "JWT_PUBLIC_KEY_PATH", "")
    assert anon_client.get("/chat/conversations", headers=auth_headers).status_code == 503

  def test_webhook_sem_assinatura_retorna_403(self, anon_client, signed_webhook):
    r = signed_webhook(anon_client, {"Body": "x", "From": "whatsapp:+5511988887777", "MessageSid": "SM1"}, signature="forjada")
    assert r.status_code == 403

  def test_webhook_nao_exige_jwt_mas_exige_assinatura(self, anon_client, signed_webhook):
    r = signed_webhook(anon_client, {"Body": "x", "From": "whatsapp:+5511988887777", "MessageSid": "SM2"})
    assert r.status_code == 200
