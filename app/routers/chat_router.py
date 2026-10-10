from urllib.parse import unquote

from fastapi import APIRouter, Depends, Form, HTTPException
from pymongo.database import Database

from app.core.config import settings
from app.core.database import get_database
from app.core.security import require_auth, validar_assinatura_twilio
from app.domain.models import (
  ConversationPreviewResponse,
  MessageCreateRequest,
  MessageResponse,
  MessageTemplateRequest,
)
from app.gateways.base_gateway import INotificationGateway
from app.gateways.twilio_gateway import get_twilio_gateway
from app.repositories.mongo_repository import MongoChatRepository
from app.services.chat_service import ChatService, NotificationGatewayError, NotificationGatewayUnavailableError
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat de Conversa"])


def get_chat_service(
  db: Database = Depends(get_database),
  gateway: INotificationGateway = Depends(get_twilio_gateway),
) -> ChatService:
  repo = MongoChatRepository(db)
  return ChatService(repo=repo, gateway=gateway, template_sid=settings.TWILIO_TEMPLATE_SID)


@router.post("/send", response_model=dict, status_code=201, dependencies=[Depends(require_auth)])
def send_message(payload: MessageCreateRequest, service: ChatService = Depends(get_chat_service)):
  try:
    return service.send_message(payload)
  except Exception as e:
    print("ERRO DETALHADO:", str(e))
    raise HTTPException(status_code=500, detail=str(e))


# Receber mensagens (POST para enviar dados novos de um servidor externo para a aplicação.)
@router.post("/webhook", status_code=200, dependencies=[Depends(validar_assinatura_twilio)])
def twilio_webhook(
  Body: str = Form(...),
  From: str = Form(...),
  MessageSid: str = Form(...),
  service: ChatService = Depends(get_chat_service),
):
  try:
    id_gen = service.receive_webhook_message(body=Body, from_=From, message_sid=MessageSid)
    print(f"[Webhook] Nova mensagem recebida de {From} salva no Atlas! ID: {id_gen}")
    return ""
  except Exception as e:
    print("\nERRO DENTRO DO WEBHOOK")
    print("O MOTIVO DO ERRO FOI:", str(e))
    print("-----------------------------------------\n")
    return ""


@router.get("/history/{tel:path}", response_model=List[MessageResponse], dependencies=[Depends(require_auth)])
def get_history(tel: str, skip: int = 0, limit: int = 20, service: ChatService = Depends(get_chat_service)):
  try:
    # unquote garante que %2B → + mesmo em casos de double-encoding pelo frontend
    tel = unquote(tel)
    return service.get_history(tel, skip=skip, limit=limit)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiate", response_model=dict, status_code=200, dependencies=[Depends(require_auth)])
def initiate_conversation(payload: MessageTemplateRequest, service: ChatService = Depends(get_chat_service)):
  try:
    return service.initiate_conversation(payload)
  except NotificationGatewayUnavailableError as e:
    raise HTTPException(status_code=503, detail=str(e))
  except NotificationGatewayError as e:
    raise HTTPException(status_code=400, detail=f"Erro na Twilio: {str(e)}")
  except Exception as e:
    print("ERRO NO POST INITIATE:", str(e))
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationPreviewResponse], dependencies=[Depends(require_auth)])
def get_active_conversations(service: ChatService = Depends(get_chat_service)):
  try:
    return service.get_active_conversations()
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Erro ao buscar conversas ativas: {str(e)}")


@router.put("/read/{tel}", response_model=dict, status_code=200, dependencies=[Depends(require_auth)])
def mark_as_read(tel: str, service: ChatService = Depends(get_chat_service)):
  try:
    modified_count = service.mark_as_read(tel)
    return {
      "status": "Mensagens marcadas como lidas com sucesso",
      "messagens_updated": modified_count,
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Erro ao atualizar status de leitura: {str(e)}")
