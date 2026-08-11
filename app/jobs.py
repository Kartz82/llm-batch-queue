"""The RQ task: process one prompt, persist its result, surface failures to RQ."""
from __future__ import annotations

from . import store
from .config import settings
from .llm import generate
from .queue import get_redis
from .tracing import span


def _attempt_number() -> int:
    """Best-effort current attempt (1-based) using RQ's retry bookkeeping."""
    try:
        from rq import get_current_job

        job = get_current_job()
        if job is not None and job.retries_left is not None:
            return settings.max_retries - job.retries_left + 1
    except Exception:
        pass
    return 1


def process_prompt(batch_id: str, job_id: str, prompt: str) -> str:
    conn = get_redis()
    attempts = _attempt_number()
    with span("process_prompt", batch_id=batch_id, job_id=job_id, attempt=attempts):
        try:
            result = generate(prompt)
            store.record(
                conn, batch_id, job_id,
                state="finished", result=result, error=None, attempts=attempts,
            )
            return result
        except Exception as exc:
            # Persist the failure, then re-raise so RQ retries / dead-letters it.
            store.record(
                conn, batch_id, job_id,
                state="failed", error=str(exc), attempts=attempts,
            )
            raise
