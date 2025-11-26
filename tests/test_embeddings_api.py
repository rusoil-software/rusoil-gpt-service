import os
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_single_embedding():
    r = client.post('/embeddings', json={'input': 'hello world'})
    assert r.status_code == 200
    j = r.json()
    assert 'embedding' in j
    assert isinstance(j['embedding'], list)


def test_batch_embedding():
    r = client.post('/embeddings/batch', json={'inputs': ['hello', 'world']})
    assert r.status_code == 200
    j = r.json()
    assert 'embeddings' in j
    assert isinstance(j['embeddings'], list)
    assert len(j['embeddings']) == 2


def test_chunk_embedding_empty():
    r = client.post('/embeddings/chunk', json={'input': ''})
    assert r.status_code == 200
    j = r.json()
    assert 'embeddings' in j
    assert j['embeddings'] == []


def test_batch_too_large():
    big = ['x'] * 2000
    r = client.post('/embeddings/batch', json={'inputs': big})
    assert r.status_code == 400
