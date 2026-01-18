from contextlib import contextmanager
import time
from typing import Generator

from opentelemetry import trace

from metrics import (
    REQUESTS_TOTAL,
    REQUEST_LATENCY,
    IN_PROGRESS_REQUESTS,
)

tracer = trace.get_tracer("api-gateway.tracing")


@contextmanager
def process_endpoint(path: str, method: str) -> Generator[None, None, None]:
    with tracer.start_as_current_span(
        name="process_endpoint",
        attributes={
            "app.path": path,
            "app.method": method,
        },
    ) as span:
        REQUESTS_TOTAL.labels(path=path, method=method).inc()
        IN_PROGRESS_REQUESTS.labels(path=path, method=method).inc()

        start_time = time.time()

        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise exc
        finally:
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(path=path, method=method).observe(duration)
            IN_PROGRESS_REQUESTS.labels(path=path, method=method).dec()
