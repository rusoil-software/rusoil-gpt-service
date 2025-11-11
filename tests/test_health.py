import os
import tempfile

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert "uptime" in j
    assert "version" in j


def test_ready_local_mode():
    os.environ["MODE"] = "local"
    r = client.get("/ready")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ready"


def test_ready_missing_db_returns_503(tmp_path):
    os.environ["MODE"] = "prod"
    # point DB and INDEX to temporary non-existent locations
    os.environ["DATABASE_PATH"] = str(tmp_path / "no_db.sqlite")
    os.environ["INDEX_DIR"] = str(tmp_path / "no_indexes")
    r = client.get("/ready")
    assert r.status_code == 503
    j = r.json()
    assert j["status"] == "not-ready"
    assert j["db_ok"] is False
