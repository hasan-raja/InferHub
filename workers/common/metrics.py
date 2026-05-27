from prometheus_client import Counter, Histogram

WORKER_REQUESTS = Counter(
    "inferhub_worker_requests_total",
    "Total worker gRPC requests",
    ("worker", "method", "status"),
)

WORKER_LATENCY = Histogram(
    "inferhub_worker_latency_seconds",
    "Worker gRPC request latency",
    ("worker", "method"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

WORKER_RETRIES = Counter(
    "inferhub_worker_retries_total",
    "Provider retry attempts",
    ("worker", "method"),
)

