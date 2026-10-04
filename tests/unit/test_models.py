from datetime import timezone

from app.domain.models import MessageChat, MessageCreateRequest


class TestMessageCreateRequest:
  def test_optional_fields_default_to_none(self):
    payload = MessageCreateRequest(tel_client="+5511999999999")

    assert payload.text is None
    assert payload.id_colaborador is None
    assert payload.id_message_twilio is None


class TestMessageChat:
  def test_read_defaults_to_true(self):
    message = MessageChat(
      id_message_twilio="SM123",
      tel_client="+5511999999999",
      direction="saida",
    )

    assert message.read is True

  def test_date_time_defaults_to_timezone_aware_utc_now(self):
    message = MessageChat(
      id_message_twilio="SM123",
      tel_client="+5511999999999",
      direction="entrada",
    )

    assert message.date_time.tzinfo is not None
    assert message.date_time.tzinfo == timezone.utc
