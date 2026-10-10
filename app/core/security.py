"""Autenticação do microsserviço.

O token é o mesmo JWT RS256 emitido pelo Quarkus (raiz-do-bem-api). Aqui só se
valida a assinatura com a chave PÚBLICA; a chave privada nunca sai da API.

O webhook da Twilio não carrega JWT: ele é autenticado pela assinatura
X-Twilio-Signature (HMAC com o Auth Token da conta).
"""
from pathlib import Path
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from twilio.request_validator import RequestValidator

from app.core.config import settings

ROLES_PERMITIDAS = {"ADMIN", "COLABORADOR"}

_bearer = HTTPBearer(auto_error=False)


def _carregar_chave_publica() -> Optional[str]:
  if settings.JWT_PUBLIC_KEY:
    # Variáveis de ambiente costumam trazer o PEM numa linha só, com "\n" literal.
    return settings.JWT_PUBLIC_KEY.replace("\n", "\n")
  if settings.JWT_PUBLIC_KEY_PATH:
    caminho = Path(settings.JWT_PUBLIC_KEY_PATH)
    if caminho.is_file():
      return caminho.read_text(encoding="utf-8")
  return None


def _nao_autenticado(detalhe: str) -> HTTPException:
  return HTTPException(
    status_code=401,
    detail=detalhe,
    headers={"WWW-Authenticate": "Bearer"},
  )


def require_auth(
  credenciais: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
  """Exige um access token válido de um colaborador. Retorna as claims."""
  chave = _carregar_chave_publica()
  if chave is None:
    # Fail closed: sem chave configurada o serviço recusa tudo em vez de abrir.
    raise HTTPException(status_code=503, detail="Autenticação não configurada no servidor.")

  if credenciais is None or credenciais.scheme.lower() != "bearer":
    raise _nao_autenticado("Token de acesso ausente.")

  try:
    claims = jwt.decode(
      credenciais.credentials,
      chave,
      algorithms=["RS256"],
      issuer=settings.JWT_ISSUER,
      options={"require": ["exp", "iss", "sub"]},
    )
  except jwt.PyJWTError:
    raise _nao_autenticado("Token inválido ou expirado.")

  # O refresh token não tem `groups`; esta checagem também o barra aqui.
  grupos = claims.get("groups") or []
  if not ROLES_PERMITIDAS.intersection(str(g).upper() for g in grupos):
    raise HTTPException(status_code=403, detail="Sem permissão para este recurso.")

  return claims


async def validar_assinatura_twilio(request: Request) -> None:
  """Garante que o POST do webhook foi assinado pela Twilio."""
  auth_token = settings.TWILIO_AUTH_TOKEN
  if not auth_token:
    raise HTTPException(status_code=503, detail="Webhook não configurado no servidor.")

  assinatura = request.headers.get("X-Twilio-Signature", "")
  # Atrás de proxy o request.url pode divergir da URL cadastrada na Twilio;
  # TWILIO_WEBHOOK_URL fixa exatamente o valor usado na assinatura.
  url = settings.TWILIO_WEBHOOK_URL or str(request.url)
  form = await request.form()

  if not RequestValidator(auth_token).validate(url, dict(form), assinatura):
    raise HTTPException(status_code=403, detail="Assinatura inválida.")
