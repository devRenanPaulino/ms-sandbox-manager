from datetime import datetime, timezone

import mongomock
import pytest

from app.domain.models import MessageChat
from app.repositories.mongo_repository import MongoChatRepository


@pytest.fixture
def repo():
  db = mongomock.MongoClient()["db_raiz_do_bem_test"]
  return MongoChatRepository(db)


def make_message(tel="+5511999999999", direction="entrada", read=True, text="oi", when=None):
  return MessageChat(
    id_message_twilio="SM123",
    tel_client=tel,
    text=text,
    direction=direction,
    date_time=when or datetime.now(timezone.utc),
    read=read,
  )


def seed(repo, **kwargs):
  """Grava direto na coleção com horário fixo; save_message sempre usa o relógio do servidor."""
  repo.collection.insert_one(make_message(**kwargs).model_dump())


class TestSaveMessage:
  def test_returns_generated_id_and_persists_document(self, repo):
    id_gen = repo.save_message(make_message())

    stored = repo.collection.find_one()
    assert str(stored["_id"]) == id_gen
    assert stored["tel_client"] == "+5511999999999"

  def test_stamps_date_time_with_the_database_clock_not_the_caller_clock(self, repo):
    # Relógio local errado (ex.: 2001) não pode vazar para a conversa: vale a hora do servidor Mongo.
    repo.save_message(make_message(when=datetime(2001, 1, 1, tzinfo=timezone.utc)))

    stored = repo.collection.find_one()
    assert stored["date_time"].year >= 2026

  def test_messages_saved_in_sequence_keep_their_order(self, repo):
    repo.save_message(make_message(text="primeira"))
    repo.save_message(make_message(text="segunda"))

    ordered = list(repo.collection.find().sort("date_time", 1))
    assert [m["text"] for m in ordered] == ["primeira", "segunda"]


class TestSearchHistoryForTel:
  def test_filters_by_phone_and_orders_newest_first(self, repo):
    older = datetime(2024, 1, 1, tzinfo=timezone.utc)
    newer = datetime(2024, 1, 2, tzinfo=timezone.utc)
    seed(repo, tel="+5511111111111", text="antiga", when=older)
    seed(repo, tel="+5511111111111", text="nova", when=newer)
    seed(repo, tel="+5522222222222", text="outro numero", when=newer)

    result = repo.search_history_for_tel("+5511111111111")

    assert [doc["text"] for doc in result] == ["nova", "antiga"]

  def test_respects_skip_and_limit(self, repo):
    for i in range(5):
      seed(repo, tel="+5511111111111", text=f"msg{i}", when=datetime(2024, 1, i + 1, tzinfo=timezone.utc))

    page = repo.search_history_for_tel("+5511111111111", skip=1, limit=2)

    assert [doc["text"] for doc in page] == ["msg3", "msg2"]


class TestGetDistinctConversations:
  def test_returns_last_message_and_unread_count_per_phone(self, repo):
    seed(repo, tel="+5511111111111", direction="entrada", read=False, text="primeira",
                                    when=datetime(2024, 1, 1, tzinfo=timezone.utc))
    seed(repo, tel="+5511111111111", direction="entrada", read=False, text="ultima",
                                    when=datetime(2024, 1, 2, tzinfo=timezone.utc))
    seed(repo, tel="+5522222222222", direction="saida", read=True, text="oferta",
                                    when=datetime(2024, 1, 1, tzinfo=timezone.utc))

    conversations = {c["tel_client"]: c for c in repo.get_distinct_conversations()}

    assert conversations["+5511111111111"]["text"] == "ultima"
    assert conversations["+5511111111111"]["unread_count"] == 2
    assert conversations["+5522222222222"]["unread_count"] == 0

  def test_does_not_count_outgoing_messages_as_unread(self, repo):
    repo.save_message(make_message(tel="+5511111111111", direction="saida", read=True, text="oi"))

    conversations = repo.get_distinct_conversations()

    assert conversations[0]["unread_count"] == 0


class TestMarkMessagesAsRead:
  def test_marks_only_unread_incoming_messages_for_phone(self, repo):
    repo.save_message(make_message(tel="+5511111111111", direction="entrada", read=False))
    repo.save_message(make_message(tel="+5511111111111", direction="saida", read=True))
    repo.save_message(make_message(tel="+5522222222222", direction="entrada", read=False))

    modified = repo.mark_messages_as_read("+5511111111111")

    assert modified == 1
    remaining_unread = list(repo.collection.find({"tel_client": "+5522222222222", "read": False}))
    assert len(remaining_unread) == 1

  def test_returns_zero_when_nothing_to_update(self, repo):
    repo.save_message(make_message(tel="+5511111111111", direction="entrada", read=True))

    modified = repo.mark_messages_as_read("+5511111111111")

    assert modified == 0
