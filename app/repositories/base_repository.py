from abc import ABC, abstractmethod
from app.domain.models import MessageChat
from typing import List

class IChatRepository(ABC):

  @abstractmethod
  def save_message(self, message: MessageChat) -> str:
    pass

  @abstractmethod
  def search_history_for_tel(self, telefone: str) -> List[dict]:
    pass