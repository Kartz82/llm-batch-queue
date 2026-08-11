import os

# Hermetic: in-memory Redis, inline job execution, offline echo LLM, no tracing.
os.environ.setdefault("USE_FAKE_REDIS", "1")
os.environ.setdefault("QUEUE_SYNC", "1")
os.environ.setdefault("LLM_BACKEND", "echo")
os.environ.setdefault("OTEL_EXPORTER", "none")
os.environ.setdefault("MAX_RETRIES", "3")
