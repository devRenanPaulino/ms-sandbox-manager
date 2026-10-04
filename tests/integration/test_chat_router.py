from urllib.parse import quote


class TestSendMessage:
  def test_send_message_returns_201_and_persists(self, api_client):
    response = api_client.post("/chat/send", json={"tel_client": "+5511999999999", "text": "Olá"})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "Mensagem Enviada com sucesso"
    assert body["id_twilio"] == "SM_FAKE_TEXT"


class TestWebhook:
  def test_webhook_persists_incoming_message_and_returns_200(self, api_client):
    response = api_client.post(
      "/chat/webhook",
      data={"Body": "Oi, tenho uma dúvida", "From": "whatsapp:+5511988887777", "MessageSid": "SM999"},
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
  def test_conversations_and_mark_as_read_flow(self, api_client):
    api_client.post(
      "/chat/webhook",
      data={"Body": "Oi", "From": "whatsapp:+5511977776666", "MessageSid": "SM1"},
    )

    conversations = api_client.get("/chat/conversations")
    assert conversations.status_code == 200
    assert conversations.json()[0]["unread_count"] == 1

    read_response = api_client.put(f"/chat/read/{quote('+5511977776666', safe='')}")
    assert read_response.status_code == 200
    assert read_response.json()["messagens_updated"] == 1

    conversations_after = api_client.get("/chat/conversations")
    assert conversations_after.json()[0]["unread_count"] == 0
