from bubus import BaseEvent
from opentelemetry.trace.span import Span

from service_crawler.src.crawling.models import CrawledURL


class WorkerCrawlStartedEvent(BaseEvent):
    worker_id: int
    url: str
    method: str
    span: Span


class WorkerCrawlCompletedEvent(BaseEvent):
    result: CrawledURL
    worker_id: int
    span: Span


class WorkerCrawlFailedEvent(BaseEvent):
    worker_id: int
    url: str
    method: str
    error_message: str
    span: Span


class WorkerIdleEvent(BaseEvent):
    worker_id: int
