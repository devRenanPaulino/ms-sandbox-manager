from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

# DTO de entrada
class MessageCreateRequest(BaseModel):
  id_message_twilio: str = Field(..., description="ID gerado pelo Twilio")
  tel_client: str = Field(..., description="Telefone com +55 e DDD")
  text: Optional[str] = None
  url_midia: Optional[str] = None
  id_colaborador: Optional[int] = None # nulo se for cliente mandando

# Entidade de domínio
class MessageChat(BaseModel):
  id_message_twilio: str
  tel_client: str
  text: Optional[str] = None
  url_midia: Optional[str] = None
  id_colaborador: Optional[int] = None
  direction: str # entrada ou saída
  date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# DTO de retorno
class MessageResponse(BaseModel):
  id_db: str = Field(..., description="O _id convertido em string no mongo db")
  id_message_twilio: str
  tel_client: str
  text: Optional[str] = None
  url_midia: Optional[str] = None
  id_colaborador: Optional[int] = None
  direction: str
  date_time: datetime