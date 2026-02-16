from http import HTTPMethod

from bubus import BaseEvent
from opentelemetry.trace.span import Span

from service_crawler.src.crawling.models import ResourceStatus


class WorkerCrawlStartedEvent(BaseEvent):
    worker_id: int
    span: Span
    url: str
    method: HTTPMethod


class WorkerCrawlCompletedEvent(BaseEvent):
    worker_id: int
    span: Span
    url: str
    status: ResourceStatus
    method: HTTPMethod
    comment: str | None = None


class WorkerCrawlFailedEvent(BaseEvent):
    worker_id: int
    span: Span
    url: str
    method: HTTPMethod
    error: Exception


class WorkerIdleEvent(BaseEvent):
    worker_id: int
