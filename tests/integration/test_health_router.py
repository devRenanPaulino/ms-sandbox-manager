import app.main as main


class _AdminOk:
  def command(self, *_):
    return {"ok": 1}


class _AdminDown:
  def command(self, *_):
    raise RuntimeError("mongo fora")


class _Mongo:
  def __init__(self, admin):
    self.admin = admin


def test_health_ok_com_mongo_no_ar(anon_client, monkeypatch):
  monkeypatch.setattr(main, "mongo_client", _Mongo(_AdminOk()))
  resposta = anon_client.get("/health")
  assert resposta.status_code == 200
  assert resposta.json() == {"status": "ok", "mongodb": "up"}


def test_health_aceita_head(anon_client, monkeypatch):
  monkeypatch.setattr(main, "mongo_client", _Mongo(_AdminOk()))
  assert anon_client.head("/health").status_code == 200


def test_health_503_quando_mongo_cai(anon_client, monkeypatch):
  monkeypatch.setattr(main, "mongo_client", _Mongo(_AdminDown()))
  resposta = anon_client.get("/health")
  assert resposta.status_code == 503
  assert resposta.json()["status"] == "degraded"
