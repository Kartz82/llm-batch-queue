"""Redis connection + RQ queue. A cached connection keeps the in-memory fake
Redis shared across enqueue and synchronous (test) job execution.
"""
from __future__ import annotations

from functools import lru_cache

from rq import Queue

from .config import settings

QUEUE_NAME = "llm"


@lru_cache(maxsize=1)
def get_redis():
    if settings.use_fake_redis:
        import fakeredis

        return fakeredis.FakeStrictRedis()
    import redis

    return redis.from_url(settings.redis_url)


def get_queue(connection=None) -> Queue:
    # is_async=False (QUEUE_SYNC=1) executes jobs inline — used by tests.
    return Queue(
        QUEUE_NAME,
        connection=connection or get_redis(),
        is_async=not settings.queue_sync,
    )


def retry_intervals() -> list[int]:
    return [min(2**i, 60) for i in range(max(1, settings.max_retries))]
