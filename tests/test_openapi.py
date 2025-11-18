from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def test_openapi_routes_present():
    r = client.get('/openapi.json')
    assert r.status_code == 200
    data = r.json()
    paths = data.get('paths', {})
    assert '/health' in paths
    assert '/ready' in paths
    assert '/metrics' in paths
    assert '/api/v1/models' in paths
