from abc import ABC, abstractmethod
from app.domain.models import MessageChat
from typing import List


class IChatRepository(ABC):

  @abstractmethod
  def save_message(self, message: MessageChat) -> str:
    pass

  @abstractmethod
  def search_history_for_tel(self, tel: str, skip: int = 0, limit: int = 20) -> List[dict]:
    pass

  @abstractmethod
  def get_distinct_conversations(self) -> List[dict]:
    pass

  @abstractmethod
  def mark_messages_as_read(self, tel: str) -> int:
    pass
