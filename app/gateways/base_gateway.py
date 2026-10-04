from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExternalMessageResult:
  sid: str
  delivered: bool
  error: Optional[str] = None


class GatewayNotConfiguredError(Exception):
  """Levantada quando o gateway de notificação não possui credenciais configuradas."""


class GatewayRequestError(Exception):
  """Levantada quando o provedor externo recusa ou falha ao processar o envio."""


class INotificationGateway(ABC):

  @abstractmethod
  def is_configured(self) -> bool:
    pass

  @abstractmethod
  def send_text(self, to: str, body: str) -> ExternalMessageResult:
    pass

  @abstractmethod
  def send_template(self, to: str, content_sid: str, content_variables: str) -> ExternalMessageResult:
    pass
