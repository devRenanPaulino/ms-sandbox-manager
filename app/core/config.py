import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
  MONGO_URI: str = os.getenv("MONGO_URI")
  MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "db_raiz_do_bem")

  TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
  TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
  TWILIO_NUMBER: str = os.getenv("TWILIO_NUMBER", "whatsapp:+14155238886")
  # URL pública exata do webhook cadastrada na Twilio (usada para validar a assinatura).
  TWILIO_WEBHOOK_URL: str = os.getenv("TWILIO_WEBHOOK_URL", "")

  # Autenticação: chave PÚBLICA do JWT emitido pela raiz-do-bem-api (PEM inline ou caminho).
  JWT_PUBLIC_KEY: str = os.getenv("JWT_PUBLIC_KEY", "")
  JWT_PUBLIC_KEY_PATH: str = os.getenv("JWT_PUBLIC_KEY_PATH", "")
  JWT_ISSUER: str = os.getenv("JWT_ISSUER", "raiz-do-bem")

  TWILIO_TEMPLATE_SID: str = os.getenv("TWILIO_TEMPLATE_SID", "HXb5b62575e6e4ff6129ad7c8efe1f983e")

settings = Settings()