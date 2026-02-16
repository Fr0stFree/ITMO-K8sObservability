import asyncio
from collections.abc import Iterable, Sequence
from hashlib import md5

from bubus import EventBus
from dependency_injector.wiring import Provide, inject
from opentelemetry.trace import Tracer, use_span
from opentelemetry.trace.status import StatusCode

from common.brokers.interface import IBrokerProducer
from common.logs import LoggerLike
from service_crawler.src.container import Container
from service_crawler.src.crawling.events import (
    WorkerCrawlCompletedEvent,
    WorkerCrawlFailedEvent,
    WorkerCrawlStartedEvent,
    WorkerIdleEvent,
)
from service_crawler.src.crawling.worker import Worker
from service_crawler.src.db.repo import Repository


class CrawlingWorkerManager:
    @inject
    def __init__(
        self,
        workers: Sequence[Worker],
        bus: EventBus = Provide[Container.event_bus],
    ) -> None:
        self._workers = workers
        self._processor: asyncio.Task | None = None
        bus.on(WorkerCrawlStartedEvent, self._on_crawl_started)
        bus.on(WorkerCrawlCompletedEvent, self._on_crawl_completed)
        bus.on(WorkerCrawlFailedEvent, self._on_crawl_failed)
        bus.on(WorkerIdleEvent, self._on_worker_idle)

    @inject
    async def start(
        self,
        repo: Repository = Provide[Container.repository],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        targets = await repo.get_targets()
        self.register_urls(targets)
        logger.info(f"Pipeline is starting with {len(self._workers)} worker(s) and {len(targets)} target(s).")
        for worker in self._workers:
            await worker.start()

    @inject
    async def stop(self, logger: LoggerLike = Provide[Container.logger]) -> None:
        logger.info("Stopping crawling pipeline...")
        await asyncio.gather(*(worker.stop() for worker in self._workers))

    async def is_healthy(self) -> bool:
        workers = await asyncio.gather(*(worker.is_healthy() for worker in self._workers))
        return all(workers)

    def register_urls(self, urls: Iterable[str]) -> None:
        if not self._workers:
            return

        batches = {worker: [] for worker in self._workers}
        for url in urls:
            worker_index = int(md5(url.encode(), usedforsecurity=False).hexdigest(), 16) % len(self._workers)
            batches[self._workers[worker_index]].append(url)

        for worker, batch in batches.items():
            worker.add_urls(batch)

    def unregister_urls(self, urls: Iterable[str]) -> None:
        if not self._workers:
            return

        for worker in self._workers:
            worker.remove_urls(urls)

    @inject
    async def _on_crawl_started(
        self,
        event: WorkerCrawlStartedEvent,
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        with use_span(event.span, end_on_exit=False) as span:
            attributes = {
                "worker.id": event.worker_id,
                "crawl.url": event.url,
                "crawl.method": event.method,
            }
            logger.info(
                "Worker %d started crawling URL '%s' with method '%s'",
                event.worker_id,
                event.url,
                event.method,
            )
            span.set_attributes(attributes)

    @inject
    async def _on_crawl_completed(
        self,
        event: WorkerCrawlCompletedEvent,
        logger: LoggerLike = Provide[Container.logger],
        tracer: Tracer = Provide[Container.tracer],
        producer: IBrokerProducer = Provide[Container.broker_producer],
    ) -> None:
        with use_span(event.span, end_on_exit=True) as span:
            attributes = {
                "worker.id": event.worker_id,
                "crawl.url": event.url,
                "crawl.status": event.status,
                "crawl.method": event.method,
            }
            span.set_attributes(attributes)
            span.set_status(StatusCode.OK)
            logger.info(
                "Worker %d completed crawling URL '%s' with status '%s'", event.worker_id, event.url, event.status
            )

            with tracer.start_as_current_span("broker.produce"):
                payload = {
                    "updated_at": event.event_created_at.isoformat(),
                    "url": event.url,
                    "status": event.status.value,
                    "comment": event.comment,
                }
                await producer.send(payload, meta={})

    @inject
    async def _on_crawl_failed(
        self,
        event: WorkerCrawlFailedEvent,
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        with use_span(event.span, end_on_exit=True) as span:
            attributes = {
                "worker.id": event.worker_id,
                "crawl.url": event.url,
                "crawl.error": str(event.error),
            }
            span.set_attributes(attributes)
            span.record_exception(event.error)
            span.set_status(StatusCode.ERROR)
            logger.exception(
                "Worker %d failed crawling URL '%s' with error '%s'",
                event.worker_id,
                event.url,
                event.error,
            )

    @inject
    async def _on_worker_idle(
        self,
        event: WorkerIdleEvent,
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        logger.warning("Worker %d is idling due to no URLs to crawl", event.worker_id)
