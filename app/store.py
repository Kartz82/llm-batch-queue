"""Batch/job result store backed by a Redis hash per batch."""
from __future__ import annotations

import json


def _key(batch_id: str) -> str:
    return f"batch:{batch_id}"


def create_batch(conn, batch_id: str, jobs: list[tuple[str, str]]) -> None:
    """Seed every job in a queued state. jobs = [(job_id, prompt), ...]."""
    mapping = {
        job_id: json.dumps(
            {
                "job_id": job_id,
                "state": "queued",
                "prompt": prompt,
                "result": None,
                "error": None,
                "attempts": 0,
            }
        )
        for job_id, prompt in jobs
    }
    conn.hset(_key(batch_id), mapping=mapping)


def record(conn, batch_id: str, job_id: str, **fields) -> None:
    raw = conn.hget(_key(batch_id), job_id)
    data = json.loads(raw) if raw else {"job_id": job_id}
    data.update(fields)
    conn.hset(_key(batch_id), job_id, json.dumps(data))


def get_jobs(conn, batch_id: str) -> list[dict]:
    raw = conn.hgetall(_key(batch_id))
    return [json.loads(v) for v in raw.values()]
