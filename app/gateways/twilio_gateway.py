from functools import lru_cache

from twilio.rest import Client

from app.core.config import settings
from app.gateways.base_gateway import (
  ExternalMessageResult,
  GatewayNotConfiguredError,
  GatewayRequestError,
  INotificationGateway,
)


class TwilioWhatsAppGateway(INotificationGateway):
  def __init__(self, account_sid: str, auth_token: str, whatsapp_number: str):
    self._whatsapp_number = whatsapp_number
    self._client = Client(account_sid, auth_token) if account_sid and auth_token else None

  def is_configured(self) -> bool:
    return self._client is not None

  def send_text(self, to: str, body: str) -> ExternalMessageResult:
    if not self.is_configured():
      raise GatewayNotConfiguredError("Credenciais do Twilio não configuradas.")

    message_sent = self._client.messages.create(
      from_=self._whatsapp_number,
      body=body,
      to=f"whatsapp:{to}",
    )
    return ExternalMessageResult(sid=message_sent.sid, delivered=True)

  def send_template(self, to: str, content_sid: str, content_variables: str) -> ExternalMessageResult:
    if not self.is_configured():
      raise GatewayNotConfiguredError("Credenciais do Twilio não configuradas.")

    try:
      message_sent = self._client.messages.create(
        from_=self._whatsapp_number,
        to=f"whatsapp:{to}",
        content_sid=content_sid,
        content_variables=content_variables,
      )
    except Exception as twilio_err:
      raise GatewayRequestError(str(twilio_err)) from twilio_err

    return ExternalMessageResult(sid=message_sent.sid, delivered=True)


@lru_cache
def get_twilio_gateway() -> TwilioWhatsAppGateway:
  return TwilioWhatsAppGateway(
    account_sid=settings.TWILIO_ACCOUNT_SID,
    auth_token=settings.TWILIO_AUTH_TOKEN,
    whatsapp_number=settings.TWILIO_NUMBER,
  )
