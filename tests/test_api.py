import os
import tempfile

# Enable metrics for these tests before importing the app so middleware registers
os.environ['METRICS_ENABLED'] = 'true'

from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_metrics_ok():
    # perform a request so middleware creates a metric
    r0 = client.get('/health')
    assert r0.status_code == 200

    r = client.get('/metrics')
    assert r.status_code == 200
    # ensure prometheus text format exists and contains HTTP metric or petra metric
    assert ('http_requests_total' in r.text) or ('petra_health_checks_total' in r.text) or ('HELP' in r.text)


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
