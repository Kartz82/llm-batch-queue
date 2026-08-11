"""End-to-end API tests (fake Redis, inline execution, echo LLM — fully offline)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_reports_redis_and_backend():
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["redis"] == "up"
    assert body["llm_backend"] == "echo"


def test_version_header_present():
    assert "X-API-Version" in client.get("/healthz").headers


def test_submit_batch_processes_all_prompts():
    r = client.post("/v1/batches", json={"prompts": ["hello", "world"]})
    assert r.status_code == 202
    batch_id = r.json()["batch_id"]
    assert r.json()["job_count"] == 2

    status = client.get(f"/v1/batches/{batch_id}").json()
    assert status["total"] == 2
    assert status["finished"] == 2
    assert status["failed"] == 0
    assert status["done"] is True
    results = {j["result"] for j in status["jobs"]}
    assert results == {"[echo] hello", "[echo] world"}


def test_unknown_batch_404():
    assert client.get("/v1/batches/deadbeef").status_code == 404


def test_empty_prompts_rejected():
    assert client.post("/v1/batches", json={"prompts": []}).status_code == 422
