import os
import tempfile
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_metrics_ok():
    r = client.get('/metrics')
    assert r.status_code == 200
    # basic prometheus text format contains HELP or TYPE
    assert 'HELP' in r.text or 'TYPE' in r.text


def test_models_listing_and_detail(tmp_path):
    # create a temporary model directory with a couple of files
    d = tmp_path / 'models'
    d.mkdir()
    f1 = d / 'modelA.bin'
    f1.write_text('abc')
    f2 = d / 'modelB.bin'
    f2.write_text('xyz')

    os.environ['MODEL_DIR'] = str(d)

    r = client.get('/api/v1/models')
    assert r.status_code == 200
    j = r.json()
    names = {m['name'] for m in j}
    assert 'modelA.bin' in names and 'modelB.bin' in names

    # detail
    r2 = client.get('/api/v1/models/modelA.bin')
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2['name'] == 'modelA.bin'
