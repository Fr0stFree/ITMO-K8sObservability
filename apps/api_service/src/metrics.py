from prometheus_client import Counter, Histogram, Gauge


REQUESTS_TOTAL = Counter(
    name="app_requests_total",
    documentation="Total number of processed requests",
    labelnames=("path", "method")
)

REQUEST_LATENCY = Histogram(
    name="app_request_latency_seconds",
    documentation="Request latency",
    labelnames=("path", "method"),
    buckets=(0.1, 0.3, 0.5, 1, 2, 5),
)

IN_PROGRESS_REQUESTS = Gauge(
    name="app_inprogress_requests",
    documentation="Number of in-progress requests",
    labelnames=("path", "method"),
)
