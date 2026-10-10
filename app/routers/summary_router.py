from functools import lru_cache
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.security import require_auth
from app.domain.models import ChatSummaryResponse
from app.routers.chat_router import get_chat_service
from app.services.chat_service import ChatService
from app.services.summary_service import SummaryService, SummaryTimeoutError, SummaryUnavailableError

router = APIRouter(prefix="/api/chats", tags=["Resumo por IA"])

SUMMARY_MESSAGE_LIMIT = 50  # últimas N mensagens enviadas ao modelo


@lru_cache
def get_summary_service() -> SummaryService:
  return SummaryService(
    api_key=settings.GEMINI_API_KEY,
    model=settings.GEMINI_MODEL,
    timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
  )


@router.post("/{tel:path}/summarize", response_model=ChatSummaryResponse, dependencies=[Depends(require_auth)])
async def summarize_chat(
  tel: str,
  chat: ChatService = Depends(get_chat_service),
  summarizer: SummaryService = Depends(get_summary_service),
):
  tel = unquote(tel)
  history = await run_in_threadpool(chat.get_history, tel, 0, SUMMARY_MESSAGE_LIMIT)
  if not history:
    raise HTTPException(status_code=404, detail="Conversa não encontrada.")

  try:
    summary = await summarizer.summarize([m.model_dump() for m in history])
  except SummaryTimeoutError as e:
    raise HTTPException(status_code=504, detail=f"{e} Consulte o histórico normalmente.")
  except SummaryUnavailableError as e:
    print(f"[Resumo] {e}")
    raise HTTPException(status_code=502, detail="Não foi possível gerar o resumo agora. Consulte o histórico normalmente.")

  return ChatSummaryResponse(tel_client=tel, messages_used=len(history), **summary.model_dump())
