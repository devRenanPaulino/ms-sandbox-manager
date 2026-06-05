from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_database
from app.domain.models import MessageChat, MessageCreateRequest, MessageResponse
from app.repositories.mongo_repository import MongoChatRepository
from datetime import datetime, timezone
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat de Conversa"])

def get_repository(db = Depends(get_database)) -> MongoChatRepository:
  return MongoChatRepository(db)

@router.post("/send", response_model=dict, status_code=201)
def send_message(payload: MessageCreateRequest, repo: MongoChatRepository = Depends(get_repository)):
  try:
    new_message = MessageChat(
      id_message_twilio=payload.id_message_twilio,
      tel_client=payload.tel_client,
      text=payload.text,
      url_midia=payload.url_midia,
      id_colaborador=payload.id_colaborador,
      direction="saida",
      date_time=datetime.utcnow()
    )

    id_gen = repo.save_message(new_message)
    return {"status": "Mensagem Enviada com sucesso", "id_db": id_gen}
  
  except Exception as e:
    print("ERRO DETALHADO:", str(e))
    raise HTTPException(status_code=500, detail=str(e))
  
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

