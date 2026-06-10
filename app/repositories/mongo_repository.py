from app.repositories.base_repository import IChatRepository
from app.domain.models import MessageChat
from pymongo.database import Database
from typing import List

class MongoChatRepository(IChatRepository):
  def __init__(self, db: Database):
    self.collection = db["stories_chats"]

  def save_message(self, message: MessageChat) -> str:
    #.dict() transforma o objeto Pydantic em um dicionário estruturado (JSON)
    data_dict = message.dict()
    resultado = self.collection.insert_one(data_dict)
    # Retorna o ID gerado pelo MongoDB convertido em String
    return str(resultado.inserted_id)
  
  def search_history_for_tel(self, tel: str) -> List[dict]:
    # Filtra por telefone e sort() para ordenar (1 = Mais antigo ao mais novo)
    cursor = self.collection.find({"tel_client": tel}).sort("date_time", 1)
    return list(cursor)
  
  def get_distinct_conversations(self) -> list[dict]:
    """Faz a agregação no Mongo para trazer a última mensagem de cada número."""
    pipeline = [
      {"$sort": {"date_time": -1}},
      {
        "$group": {
          "_id": "$tel_client",
          "text": {"$first": "$text"},
          "date_time": {"$first": "$date_time"},
          "direction": {"$first": "$direction"},
          # Se direction == "entrada" AND read == False, soma 1, senão 0
          "unread_count": {
            "$sum": {
              "$cond": [
                {
                  "$and": [
                    {"$eq": ["$direction", "entrada"]},
                    {"$eq": ["$read", False]}
                  ]
                },
                1, # if True
                0  # if False
              ]
            }
          }
        }
      },
      {
        "$project": {
          "tel_client": "$_id",
          "text": 1,
          "date_time": 1,
          "direction": 1,
          "unread_count": 1,
          "_id": 0
        }
      },
        {"$sort": {"date_time": -1}}
    ]
    return list(self.collection.aggregate(pipeline))
  
  def mark_messages_as_read(self, tel: str) -> int:
    """Marcar todas as mensagens recebidas de um número específico como lidas."""
    result = self.collection.update_many(
      {
        "tel_client": tel,
        "direction": "entrada",
        "read": {"$ne": True} # Atualiza o que  for False ou registros que não tinham o campo
      },
      {"$set": {"read": True}}
    )
    return result.modified_count


