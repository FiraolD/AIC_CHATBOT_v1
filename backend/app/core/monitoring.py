"""Prometheus registry and application metrics.

Central home for all metric objects so middleware, the generator and the
retriever all report into one registry rendered at GET /metrics.
"""
import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

# --- HTTP metrics (filled by MetricsMiddleware) ---
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["route", "method", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["route", "method"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# --- LLM metrics (filled by the generator) ---
llm_requests_total = Counter(
    "llm_requests_total",
    "LLM completion requests",
    ["model", "status"],  # status: success | error
)
llm_duration_seconds = Histogram(
    "llm_duration_seconds",
    "LLM completion latency in seconds",
    ["model"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
)

# --- Retrieval metrics (filled by the retriever) ---
retrieval_duration_seconds = Histogram(
    "retrieval_duration_seconds",
    "RAG retrieval latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# --- Business metrics ---
chat_messages_total = Counter(
    "chat_messages_total",
    "Chat messages processed",
    ["role"],  # user | assistant
)


def render_metrics() -> tuple[bytes, str]:
    """Return (payload, content_type) for the Prometheus scrape endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST


class Timer:
    """Small context manager to observe histogram durations."""

    def __init__(self, histogram, **labels):
        self.histogram = histogram
        self.labels = labels
        self.start = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        elapsed = time.perf_counter() - self.start
        if self.labels:
            self.histogram.labels(**self.labels).observe(elapsed)
        else:
            self.histogram.observe(elapsed)
        return False
