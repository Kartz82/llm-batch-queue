"""API contracts."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class JobState(str, Enum):
    queued = "queued"
    finished = "finished"
    failed = "failed"


class BatchCreate(BaseModel):
    prompts: list[str] = Field(..., min_length=1, max_length=100,
                               examples=[["Summarize: cats", "Translate 'hello' to French"]])
    metadata: dict = Field(default_factory=dict)


class BatchCreated(BaseModel):
    batch_id: str
    job_count: int
    status_url: str


class JobResult(BaseModel):
    job_id: str
    state: JobState
    prompt: str
    result: str | None = None
    error: str | None = None
    attempts: int = 0


class BatchStatus(BaseModel):
    batch_id: str
    total: int
    finished: int
    failed: int
    queued: int
    done: bool
    jobs: list[JobResult]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    redis: str
    llm_backend: str
