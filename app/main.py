"""FastAPI surface. Versioned under /v1; async batch submit + status polling."""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from rq import Retry

from . import __version__, store
from .config import settings
from .jobs import process_prompt
from .queue import get_queue, get_redis, retry_intervals
from .schemas import (
    BatchCreate,
    BatchCreated,
    BatchStatus,
    HealthResponse,
    JobResult,
)
from .tracing import init_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tracing("llm-batch-queue-api")
    yield


app = FastAPI(
    title="Async LLM Batch Queue",
    version=__version__,
    summary="Submit batches of prompts; a Redis/RQ worker pool processes them with "
    "retries, dead-lettering and OpenTelemetry tracing.",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = __version__
    return response


@app.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    try:
        get_redis().ping()
        redis_state = "up"
    except Exception:
        redis_state = "down"
    return HealthResponse(
        version=__version__, redis=redis_state, llm_backend=settings.llm_backend
    )


@app.post("/v1/batches", response_model=BatchCreated, status_code=202)
def create_batch(body: BatchCreate) -> BatchCreated:
    batch_id = uuid.uuid4().hex[:12]
    conn = get_redis()
    q = get_queue(conn)

    jobs = [(uuid.uuid4().hex[:12], p) for p in body.prompts]
    store.create_batch(conn, batch_id, jobs)

    for job_id, prompt in jobs:
        q.enqueue(
            process_prompt,
            batch_id,
            job_id,
            prompt,
            job_id=f"{batch_id}-{job_id}",
            retry=Retry(max=settings.max_retries, interval=retry_intervals()),
        )
    return BatchCreated(
        batch_id=batch_id, job_count=len(jobs), status_url=f"/v1/batches/{batch_id}"
    )


@app.get("/v1/batches/{batch_id}", response_model=BatchStatus)
def batch_status(batch_id: str) -> BatchStatus:
    rows = store.get_jobs(get_redis(), batch_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No batch {batch_id!r}.")
    jobs = [JobResult(**r) for r in rows]
    finished = sum(j.state == "finished" for j in jobs)
    failed = sum(j.state == "failed" for j in jobs)
    queued = sum(j.state == "queued" for j in jobs)
    return BatchStatus(
        batch_id=batch_id,
        total=len(jobs),
        finished=finished,
        failed=failed,
        queued=queued,
        done=queued == 0,
        jobs=jobs,
    )
