import os
from fastapi import APIRouter, Depends, HTTPException, Form
from app.core.database import get_database
from app.domain.models import MessageChat, MessageCreateRequest, MessageResponse
from app.repositories.mongo_repository import MongoChatRepository
from datetime import datetime, timezone
from typing import List
from twilio.rest import Client

router = APIRouter(prefix="/chat", tags=["Chat de Conversa"])

twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(twilio_sid, twilio_token) if twilio_sid and twilio_token else None

def get_repository(db = Depends(get_database)) -> MongoChatRepository:
  return MongoChatRepository(db)

@router.post("/send", response_model=dict, status_code=201)
def send_message(payload: MessageCreateRequest, repo: MongoChatRepository = Depends(get_repository)):
  try:
    id_twilio_final = payload.id_message_twilio

    if twilio_client:
      try:
        message_sent = twilio_client.message.create(
          from_=twilio_number,
          body=payload.text,
          to=f"whatsapp:{payload.tel_client}"
        )
        id_twilio_final = message_sent.sid
        print(f"[Twilio] WhatsApp enviado para {payload.tel_client}. SID: {id_twilio_final}")
      except Exception as twilio_err:
        print(f"[Twilio] Erro no disparo (Mantenha a janela de 24h ativa): {twilio_err}")

    new_message = MessageChat(
      id_message_twilio=payload.id_message_twilio,
      tel_client=payload.tel_client,
      text=payload.text,
      url_midia=payload.url_midia,
      id_colaborador=payload.id_colaborador,
      direction="saida",
      date_time=datetime.now(timezone.utc)
    )

    id_gen = repo.save_message(new_message)
    return {"status": "Mensagem Enviada com sucesso", "id_db": id_gen, "id_twilio": id_twilio_final}
  
  except Exception as e:
    print("ERRO DETALHADO:", str(e))
    raise HTTPException(status_code=500, detail=str(e))
  
# Receber mensagens (POST para enviar dados novos de um servidor externo para a aplicação.)
@router.post("/webhook", status_code=200)
def twilio_webhook(
  Body: str = Form(...),
  From: str = Form(...),
  MessageSid: str = Form(...),
  repo: MongoChatRepository = Depends(get_repository)
):
  try:
    clean_tel = From.replace("whatsapp:", "")

    incoming_message = MessageChat(
      id_message_twilio=MessageSid,
      tel_client=clean_tel,
      text=Body,
      url_midia=None,
      id_colaborador=None,
      direction="entrada",
      date_time=datetime.now(timezone.utc)
    )

    id_gen = repo.save_message(incoming_message)
    print(f"[Webhook] Nova mensagem recebida de {clean_tel} salva no Atlas! ID: {id_gen}")

    return ""
  except Exception as e:
    print("ERRO NO WEBHOOK DA TWILIO:", str(e))
    return ""

  
@router.get("/history/{tel}", response_model=List[MessageResponse])
def get_history(tel: str, repo: MongoChatRepository = Depends(get_repository)):
  try:
    doc_db = repo.search_history_for_tel(tel)

    story_format = []
    for doc in doc_db:

      dt = doc.get("date_time")
      if isinstance(dt, datetime):
      # Se o datetime não tiver fuso horário, injeta o UTC para o Pydantic aceitar feliz
        if dt.tzinfo is None:
          dt = dt.replace(tzinfo=timezone.utc)

      filter_message = MessageResponse(
        id_db=str(doc["_id"]),
        id_message_twilio=doc.get("id_message_twilio"),
        tel_client=doc.get("tel_client"),
        text=doc.get("text"),
        url_midia=doc.get("url_midia"),
        id_colaborador=doc.get("id_colaborador"),
        direction=doc.get("direction"),
        date_time=dt
      )
      story_format.append(filter_message)

    return story_format
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

