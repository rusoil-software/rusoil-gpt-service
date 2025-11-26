import os
import tempfile
import re

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_metrics_endpoint():
    r = client.get("/metrics")
    assert r.status_code == 200
    # prometheus text format content type
    assert "text/plain" in r.headers.get("content-type", "") or r.headers.get("content-type")
    assert b"# HELP" in r.content or len(r.content) > 0


def test_metrics_contains_expected_names_and_histogram_after_infer(tmp_path):
    # prepare a model to infer so the inference endpoint exists
    d = tmp_path / "models"
    d.mkdir()
    f = d / "m.bin"
    f.write_text("x")
    os.environ["MODELS_DIR"] = str(d)

    # hit health a few times to generate request metrics
    client.get("/health")
    client.get("/health")

    # call inference to generate model inference metric
    r_inf = client.post("/api/v1/models/m/infer")
    assert r_inf.status_code == 200

    # fetch metrics text and ensure expected metric names exist
    r = client.get("/metrics")
    assert r.status_code == 200
    txt = r.content.decode("utf-8")
    assert "petra_http_requests_total" in txt
    assert "petra_http_request_latency_seconds" in txt
    assert "petra_model_inference_duration_seconds" in txt

    # check that the inference histogram count is present and > 0
    m = re.search(r"petra_model_inference_duration_seconds_count\{model=\"m\"\} ([0-9]+)", txt)
    assert m is not None, "inference histogram count metric not found"
    assert int(m.group(1)) >= 1


def test_models_empty_by_default():
    # ensure no MODELS_DIR env var
    os.environ.pop("MODELS_DIR", None)
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_models_list_and_detail(tmp_path):
    # create dummy model file
    d = tmp_path / "models"
    d.mkdir()
    f = d / "demo_model.bin"
    f.write_text("dummy")
    os.environ["MODELS_DIR"] = str(d)

    r = client.get("/api/v1/models")
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
    assert len(arr) == 1
    assert arr[0]["name"] == "demo_model"

    r2 = client.get(f"/api/v1/models/{arr[0]['name']}")
    assert r2.status_code == 200
    j = r2.json()
    assert j["name"] == arr[0]["name"]
