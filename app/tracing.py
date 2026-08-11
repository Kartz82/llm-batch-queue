"""OpenTelemetry setup with a no-op fallback (tracing never breaks the app)."""
from __future__ import annotations

from contextlib import contextmanager

from .config import settings

_initialized = False


def init_tracing(service_name: str = "llm-batch-queue") -> None:
    global _initialized
    if settings.otel_exporter == "none" or _initialized:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        if settings.otel_exporter == "otlp":
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint)
        else:
            exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _initialized = True
    except Exception:  # tracing is best-effort; never crash the request path
        pass


@contextmanager
def span(name: str, **attrs):
    """Start a span if OTel is available; otherwise a no-op context."""
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("llm-batch-queue")
        with tracer.start_as_current_span(name) as s:
            for k, v in attrs.items():
                s.set_attribute(k, str(v))
            yield s
    except Exception:
        yield None
