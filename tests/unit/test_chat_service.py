from datetime import datetime, timezone

import pytest

from app.domain.models import MessageCreateRequest, MessageTemplateRequest
from app.gateways.base_gateway import GatewayRequestError
from app.services.chat_service import ChatService, NotificationGatewayError, NotificationGatewayUnavailableError
from tests.fakes import FakeChatRepository, FakeNotificationGateway

TEMPLATE_SID = "HX_TEST_TEMPLATE"


def make_service(repo=None, gateway=None) -> ChatService:
  return ChatService(
    repo=repo or FakeChatRepository(),
    gateway=gateway or FakeNotificationGateway(configured=True),
    template_sid=TEMPLATE_SID,
  )


class TestSendMessage:
  def test_uses_gateway_sid_when_configured_and_successful(self):
    repo = FakeChatRepository()
    gateway = FakeNotificationGateway(configured=True)
    service = make_service(repo, gateway)

    result = service.send_message(MessageCreateRequest(tel_client="+5511999999999", text="Olá"))

    assert result["id_twilio"] == "SM_FAKE_TEXT"
    assert gateway.sent_texts == [{"to": "+5511999999999", "body": "Olá"}]
    assert repo.messages[0]["direction"] == "saida"
    assert repo.messages[0]["id_message_twilio"] == "SM_FAKE_TEXT"

  def test_falls_back_to_mock_sid_when_gateway_not_configured(self):
    repo = FakeChatRepository()
    gateway = FakeNotificationGateway(configured=False)
    service = make_service(repo, gateway)

    result = service.send_message(MessageCreateRequest(tel_client="+5511999999999", text="Olá"))

    assert result["id_twilio"].startswith("SM_MOCK_")
    assert repo.messages[0]["id_message_twilio"] == result["id_twilio"]

  def test_falls_back_to_mock_sid_and_still_saves_when_gateway_raises(self):
    repo = FakeChatRepository()
    gateway = FakeNotificationGateway(configured=True)
    gateway.raise_on_send_text = RuntimeError("janela de 24h expirada")
    service = make_service(repo, gateway)

    result = service.send_message(MessageCreateRequest(tel_client="+5511999999999", text="Olá"))

    assert result["id_twilio"].startswith("SM_MOCK_")
    assert len(repo.messages) == 1


class TestReceiveWebhookMessage:
  def test_strips_whatsapp_prefix_and_marks_unread_incoming(self):
    repo = FakeChatRepository()
    service = make_service(repo)

    service.receive_webhook_message(body="Oi", from_="whatsapp:+5511988887777", message_sid="SM123")

    saved = repo.messages[0]
    assert saved["tel_client"] == "+5511988887777"
    assert saved["direction"] == "entrada"
    assert saved["read"] is False


class TestGetHistory:
  def test_injects_utc_on_naive_datetime_and_returns_chronological_order(self):
    repo = FakeChatRepository()
    service = make_service(repo)

    older = datetime(2024, 1, 1, 12, 0, 0)  # naive
    newer = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    repo.messages = [
      {"_id": "2", "tel_client": "+55119", "text": "segunda", "id_colaborador": None,
       "direction": "saida", "date_time": newer, "id_message_twilio": "b"},
      {"_id": "1", "tel_client": "+55119", "text": "primeira", "id_colaborador": None,
       "direction": "entrada", "date_time": older, "id_message_twilio": "a"},
    ]

    history = service.get_history("+55119", skip=0, limit=20)

    assert [m.text for m in history] == ["primeira", "segunda"]
    assert history[0].date_time.tzinfo is not None


class TestInitiateConversation:
  def make_payload(self):
    return MessageTemplateRequest(tel_client="+5511999999999", param_1="Segunda", param_2="10h")

  def test_raises_when_gateway_not_configured(self):
    service = make_service(gateway=FakeNotificationGateway(configured=False))

    with pytest.raises(NotificationGatewayUnavailableError):
      service.initiate_conversation(self.make_payload())

  def test_raises_notification_gateway_error_when_provider_rejects(self):
    gateway = FakeNotificationGateway(configured=True)
    gateway.raise_on_send_template = GatewayRequestError("número inválido")
    service = make_service(gateway=gateway)

    with pytest.raises(NotificationGatewayError):
      service.initiate_conversation(self.make_payload())

  def test_saves_rendered_message_on_success(self):
    repo = FakeChatRepository()
    gateway = FakeNotificationGateway(configured=True)
    service = make_service(repo, gateway)

    result = service.initiate_conversation(self.make_payload())

    assert result["id_twilio"] == "SM_FAKE_TEMPLATE"
    assert gateway.sent_templates[0]["content_sid"] == TEMPLATE_SID
    assert "Segunda" in repo.messages[0]["text"]
    assert "10h" in repo.messages[0]["text"]


class TestConversationsAndReadStatus:
  def test_get_active_conversations_delegates_to_repository(self):
    repo = FakeChatRepository()
    service = make_service(repo)
    repo.messages.append({
      "tel_client": "+5511999999999", "text": "oi", "date_time": datetime.now(timezone.utc),
      "direction": "entrada", "read": False,
    })

    conversations = service.get_active_conversations()

    assert conversations[0]["tel_client"] == "+5511999999999"
    assert conversations[0]["unread_count"] == 1

  def test_mark_as_read_delegates_to_repository(self):
    repo = FakeChatRepository()
    service = make_service(repo)
    repo.messages.append({
      "tel_client": "+5511999999999", "text": "oi", "date_time": datetime.now(timezone.utc),
      "direction": "entrada", "read": False,
    })

    updated = service.mark_as_read("+5511999999999")

    assert updated == 1
    assert repo.messages[0]["read"] is True
