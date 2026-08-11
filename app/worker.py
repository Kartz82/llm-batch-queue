"""RQ worker entrypoint:  python -m app.worker"""
from __future__ import annotations

from .queue import QUEUE_NAME, get_redis
from .tracing import init_tracing


def main() -> None:
    init_tracing("llm-batch-queue-worker")
    from rq import Queue, Worker

    conn = get_redis()
    Worker([Queue(QUEUE_NAME, connection=conn)], connection=conn).work()


if __name__ == "__main__":
    main()
