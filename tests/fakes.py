from datetime import timezone
from typing import List, Optional

from app.domain.models import MessageChat
from app.gateways.base_gateway import ExternalMessageResult, GatewayNotConfiguredError, INotificationGateway
from app.repositories.base_repository import IChatRepository


class FakeChatRepository(IChatRepository):
  """Repositório em memória para testar a camada de serviço isolada do MongoDB."""

  def __init__(self):
    self.messages: List[dict] = []
    self._next_id = 1

  def save_message(self, message: MessageChat) -> str:
    doc = message.model_dump()
    doc["_id"] = str(self._next_id)
    self._next_id += 1
    self.messages.append(doc)
    return doc["_id"]

  def search_history_for_tel(self, tel: str, skip: int = 0, limit: int = 20) -> List[dict]:
    matching = [m for m in self.messages if m["tel_client"] == tel]
    # Alguns documentos legados podem ter date_time sem tzinfo (Mongo não guarda offset);
    # normaliza apenas para fins de ordenação, sem alterar o documento retornado.
    matching.sort(key=lambda m: self._as_aware(m["date_time"]), reverse=True)
    return matching[skip: skip + limit]

  @staticmethod
  def _as_aware(dt):
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

  def get_distinct_conversations(self) -> List[dict]:
    latest_by_tel = {}
    unread_by_tel = {}
    for m in sorted(self.messages, key=lambda m: self._as_aware(m["date_time"])):
      latest_by_tel[m["tel_client"]] = m
      if m["direction"] == "entrada" and not m.get("read", True):
        unread_by_tel[m["tel_client"]] = unread_by_tel.get(m["tel_client"], 0) + 1

    return [
      {
        "tel_client": tel,
        "text": doc.get("text"),
        "date_time": doc["date_time"],
        "direction": doc["direction"],
        "unread_count": unread_by_tel.get(tel, 0),
      }
      for tel, doc in latest_by_tel.items()
    ]

  def mark_messages_as_read(self, tel: str) -> int:
    count = 0
    for m in self.messages:
      if m["tel_client"] == tel and m["direction"] == "entrada" and not m.get("read", True):
        m["read"] = True
        count += 1
    return count


class FakeNotificationGateway(INotificationGateway):
  """Gateway controlável para testar o ChatService sem depender do SDK do Twilio."""

  def __init__(self, configured: bool = True):
    self.configured = configured
    self.sent_texts: List[dict] = []
    self.sent_templates: List[dict] = []
    self.text_result: Optional[ExternalMessageResult] = ExternalMessageResult(sid="SM_FAKE_TEXT", delivered=True)
    self.template_result: Optional[ExternalMessageResult] = ExternalMessageResult(sid="SM_FAKE_TEMPLATE", delivered=True)
    self.raise_on_send_text: Optional[Exception] = None
    self.raise_on_send_template: Optional[Exception] = None

  def is_configured(self) -> bool:
    return self.configured

  def send_text(self, to: str, body: str) -> ExternalMessageResult:
    if not self.configured:
      raise GatewayNotConfiguredError("Gateway não configurado.")
    if self.raise_on_send_text:
      raise self.raise_on_send_text
    self.sent_texts.append({"to": to, "body": body})
    return self.text_result

  def send_template(self, to: str, content_sid: str, content_variables: str) -> ExternalMessageResult:
    if not self.configured:
      raise GatewayNotConfiguredError("Gateway não configurado.")
    if self.raise_on_send_template:
      raise self.raise_on_send_template
    self.sent_templates.append({"to": to, "content_sid": content_sid, "content_variables": content_variables})
    return self.template_result
