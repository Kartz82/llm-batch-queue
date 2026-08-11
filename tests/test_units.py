"""Unit tests for retry policy, LLM backend, and the store."""
from app import store
from app.llm import generate
from app.queue import get_redis, retry_intervals


def test_retry_intervals_backoff():
    ivals = retry_intervals()
    assert ivals == [1, 2, 4]  # MAX_RETRIES=3 → exponential, capped at 60


def test_echo_backend_is_offline():
    assert generate("Ping") == "[echo] Ping"


def test_store_roundtrip():
    conn = get_redis()
    store.create_batch(conn, "b1", [("j1", "p1"), ("j2", "p2")])
    store.record(conn, "b1", "j1", state="finished", result="ok", attempts=1)
    rows = {r["job_id"]: r for r in store.get_jobs(conn, "b1")}
    assert rows["j1"]["state"] == "finished"
    assert rows["j1"]["result"] == "ok"
    assert rows["j2"]["state"] == "queued"
