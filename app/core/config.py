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

  # Resumo por IA (Google Gemini). O modelo é configurável porque os IDs do Gemini são descontinuados com o tempo.
  GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
  GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
  GEMINI_TIMEOUT_SECONDS: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

  TWILIO_TEMPLATE_SID: str = os.getenv("TWILIO_TEMPLATE_SID", "HXb5b62575e6e4ff6129ad7c8efe1f983e")

settings = Settings()