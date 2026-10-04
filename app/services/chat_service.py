from datetime import datetime, timezone
from typing import List

from app.domain.models import (
  ConversationPreviewResponse,
  MessageChat,
  MessageCreateRequest,
  MessageResponse,
  MessageTemplateRequest,
)
from app.gateways.base_gateway import GatewayRequestError, INotificationGateway
from app.repositories.base_repository import IChatRepository


class NotificationGatewayUnavailableError(Exception):
  """Levantada quando uma operação exige o gateway de notificação e ele não está configurado."""


class NotificationGatewayError(Exception):
  """Levantada quando o provedor externo recusa ou falha ao processar o envio."""


def _mock_twilio_sid() -> str:
  return f"SM_MOCK_{int(datetime.now(timezone.utc).timestamp())}"


class ChatService:
  def __init__(self, repo: IChatRepository, gateway: INotificationGateway, template_sid: str):
    self._repo = repo
    self._gateway = gateway
    self._template_sid = template_sid

  def send_message(self, payload: MessageCreateRequest) -> dict:
    id_twilio_final = _mock_twilio_sid()

    if self._gateway.is_configured():
      try:
        result = self._gateway.send_text(to=payload.tel_client, body=payload.text)
        id_twilio_final = result.sid
      except Exception as twilio_err:
        print(f"[Twilio] Erro no disparo (Mantenha a janela de 24h ativa): {twilio_err}")

    new_message = MessageChat(
      id_message_twilio=id_twilio_final,
      tel_client=payload.tel_client,
      text=payload.text,
      id_colaborador=payload.id_colaborador,
      direction="saida",
      date_time=datetime.now(timezone.utc),
    )

    id_gen = self._repo.save_message(new_message)
    return {"status": "Mensagem Enviada com sucesso", "id_db": id_gen, "id_twilio": id_twilio_final}

  def receive_webhook_message(self, body: str, from_: str, message_sid: str) -> str:
    clean_tel = from_.replace("whatsapp:", "")

    incoming_message = MessageChat(
      id_message_twilio=message_sid,
      tel_client=clean_tel,
      text=body,
      id_colaborador=None,
      direction="entrada",
      date_time=datetime.now(timezone.utc),
      read=False,
    )

    return self._repo.save_message(incoming_message)

  def get_history(self, tel: str, skip: int = 0, limit: int = 20) -> List[MessageResponse]:
    doc_db = self._repo.search_history_for_tel(tel, skip=skip, limit=limit)

    story_format = []
    for doc in doc_db:
      dt = doc.get("date_time")
      if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

      story_format.append(
        MessageResponse(
          id_db=str(doc["_id"]),
          id_message_twilio=doc.get("id_message_twilio"),
          tel_client=doc.get("tel_client"),
          text=doc.get("text"),
          id_colaborador=doc.get("id_colaborador"),
          direction=doc.get("direction"),
          date_time=dt,
        )
      )

    # Mongo retorna do mais recente para o mais antigo (sort decrescente);
    # invertemos para que o lote apareça na ordem cronológica do chat.
    story_format.reverse()
    return story_format

  def initiate_conversation(self, payload: MessageTemplateRequest) -> dict:
    if not self._gateway.is_configured():
      raise NotificationGatewayUnavailableError("Serviço de notificação (Twilio) não configurado.")

    variables_json = f'{{"1":"{payload.param_1}","2":"{payload.param_2}"}}'

    try:
      result = self._gateway.send_template(
        to=payload.tel_client,
        content_sid=self._template_sid,
        content_variables=variables_json,
      )
    except GatewayRequestError as err:
      raise NotificationGatewayError(str(err)) from err

    texto_renderizado = f"Your appointment is coming up on {payload.param_1} at {payload.param_2}"

    new_message = MessageChat(
      id_message_twilio=result.sid,
      tel_client=payload.tel_client,
      text=texto_renderizado,
      id_colaborador=payload.id_colaborador,
      direction="saida",
      date_time=datetime.now(timezone.utc),
    )

    id_gen = self._repo.save_message(new_message)

    return {
      "status": "Template enviado e janela de conversa aberta!",
      "id_db": id_gen,
      "id_twilio": result.sid,
    }

  def get_active_conversations(self) -> List[ConversationPreviewResponse]:
    return self._repo.get_distinct_conversations()

  def mark_as_read(self, tel: str) -> int:
    return self._repo.mark_messages_as_read(tel)
