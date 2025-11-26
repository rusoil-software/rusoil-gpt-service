import os
import time

import jwt
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def make_token(secret, user_id="u123", username="alice", ttl=60):
    payload = {"user_id": user_id, "username": username, "iat": int(time.time()), "exp": int(time.time()) + ttl}
    return jwt.encode(payload, secret, algorithm="HS256")


def test_missing_token_returns_401():
    r = client.get("/api/v1/me")
    assert r.status_code == 401


def test_invalid_token_returns_401():
    # malformed or bad signature
    token = "this.is.not.a.token"
    r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_expired_token_returns_401(tmp_path, monkeypatch):
    secret = os.getenv("AUTH_SECRET", "changeme")
    token = make_token(secret, ttl=-10)  # already expired
    r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_valid_token_returns_user(monkeypatch):
    secret = os.getenv("AUTH_SECRET", "changeme")
    token = make_token(secret, user_id="s42", username="bob", ttl=300)
    r = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    j = r.json()
    assert "user" in j
    assert j["user"]["user_id"] == "s42"
    assert j["user"]["username"] == "bob"
