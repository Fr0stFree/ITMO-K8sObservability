import asyncio
from collections.abc import Awaitable, Callable, Iterable
import json
from uuid import uuid4

from aiokafka import AIOKafkaConsumer
from opentelemetry.context import Context
from opentelemetry.propagate import extract as extract_context
from opentelemetry.propagators.textmap import Getter
from opentelemetry.trace import Tracer

from common.brokers.kafka.settings import KafkaConsumerSettings
from common.logs import LoggerLike


class KafkaContextExtractor(Getter):
    def get(self, carrier: Iterable[tuple[str, bytes]], key: str) -> list[str] | None:
        values = [value.decode("utf-8") for header_key, value in carrier if header_key.lower() == key.lower()]
        return values or None

    def keys(self, carrier: Iterable[tuple[str, bytes]]) -> list[str]:
        return [key for key, _ in carrier]

    def extract(self, carrier: Iterable[tuple[str, bytes]]) -> Context:
        return extract_context(carrier, getter=self)


class KafkaConsumer:
    context_extractor = KafkaContextExtractor()

    def __init__(self, settings: KafkaConsumerSettings, logger: LoggerLike, tracer: Tracer) -> None:
        self._settings = settings
        self._logger = logger
        self._tracer = tracer
        self._client_id = f"{settings.client_prefix}-{uuid4().hex[:6]}"
        self._consumer = AIOKafkaConsumer(
            settings.topic,
            client_id=self._client_id,
            group_id=settings.group,
            bootstrap_servers=settings.address,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        self._processor: asyncio.Task | None = None
        self._on_message: Callable[[dict], Awaitable[None]] | None = None

    def set_message_handler(self, on_message: Callable[[dict], Awaitable[None]]) -> None:
        self._on_message = on_message

    async def start(self) -> None:
        self._logger.info(
            "Starting the kafka consumer '%s' on server '%s' with topic '%s'...",
            self._client_id,
            self._settings.address,
            self._settings.topic,
        )
        await self._consumer.start()
        self._processor = asyncio.create_task(self._process_messages())

    async def _process_messages(self) -> None:
        if self._processor is None:
            raise ValueError("Consumer is not started")

        if self._on_message is None:
            raise ValueError("Consumer message handler is not set")

        async for message in self._consumer:
            with self._tracer.start_as_current_span(
                "kafka.consume",
                attributes={
                    "consumer.topic": message.topic,
                    "consumer.client_id": self._client_id,
                    "consumer.offset": message.offset,
                },
                context=self.context_extractor.extract(message.headers),
            ):
                await self._on_message(message.value)

    async def is_healthy(self) -> bool:
        await self._consumer.topics()
        if self._processor is None or self._processor.done():
            return False
        return True

    async def stop(self) -> None:
        self._logger.info("Shutting down the kafka consumer '%s'...", self._client_id)
        await self._consumer.stop()
