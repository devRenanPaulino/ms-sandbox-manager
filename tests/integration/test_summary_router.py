from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.routers.summary_router import get_summary_service
from app.services.summary_service import (
  SummaryContent,
  SummaryService,
  SummaryTimeoutError,
  SummaryUnavailableError,
)

TEL = "%2B5511977776666"


class FakeSummarizer:
  def __init__(self, result=None, error=None):
    self.result, self.error, self.received = result, error, None

  async def summarize(self, messages):
    self.received = messages
    if self.error:
      raise self.error
    return self.result


@pytest.fixture
def with_summarizer():
  def _set(summarizer):
    app.dependency_overrides[get_summary_service] = lambda: summarizer
  return _set


def seed(mongo_db, n=35):
  base = datetime(2024, 1, 1, tzinfo=timezone.utc)
  mongo_db["stories_chats"].insert_many([
    {"id_message_twilio": f"SM{i}", "tel_client": "+5511977776666", "text": f"msg {i}",
     "direction": "entrada" if i % 2 else "saida", "date_time": base + timedelta(minutes=i)}
    for i in range(n)
  ])


class TestSummarize:
  def test_returns_structured_summary_from_history(self, api_client, mongo_db, with_summarizer):
    seed(mongo_db)
    summarizer = FakeSummarizer(SummaryContent(
      necessidade_principal="Cesta básica", status_atual="Aguardando documentos", proximos_passos="Agendar retirada"))
    with_summarizer(summarizer)

    response = api_client.post(f"/api/chats/{TEL}/summarize")

    assert response.status_code == 200
    body = response.json()
    assert body["necessidade_principal"] == "Cesta básica"
    assert body["messages_used"] == 35
    assert summarizer.received[0]["text"] == "msg 0"  # ordem cronológica

  def test_unknown_conversation_returns_404(self, api_client, with_summarizer):
    with_summarizer(FakeSummarizer())
    assert api_client.post(f"/api/chats/{TEL}/summarize").status_code == 404

  def test_provider_failure_returns_502_with_friendly_message(self, api_client, mongo_db, with_summarizer):
    seed(mongo_db)
    with_summarizer(FakeSummarizer(error=SummaryUnavailableError("chave inválida")))

    response = api_client.post(f"/api/chats/{TEL}/summarize")

    assert response.status_code == 502
    assert "histórico" in response.json()["detail"]
    assert "chave" not in response.json()["detail"]  # não vaza detalhe do provedor

  def test_provider_timeout_returns_504(self, api_client, mongo_db, with_summarizer):
    seed(mongo_db)
    with_summarizer(FakeSummarizer(error=SummaryTimeoutError("lento")))

    assert api_client.post(f"/api/chats/{TEL}/summarize").status_code == 504

  def test_requires_authentication(self, anon_client):
    assert anon_client.post(f"/api/chats/{TEL}/summarize").status_code == 401


class TestSummaryService:
  def test_without_api_key_raises_unavailable(self):
    import asyncio
    service = SummaryService(api_key="", model="m", timeout_seconds=1)

    with pytest.raises(SummaryUnavailableError):
      asyncio.run(service.summarize([{"direction": "entrada", "text": "oi"}]))
