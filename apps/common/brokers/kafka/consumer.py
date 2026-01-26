import asyncio
from collections.abc import Awaitable, Callable
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, ConsumerRecord

from common.brokers.kafka.settings import KafkaConsumerSettings
from common.logs import LoggerLike


class KafkaConsumer:
    def __init__(self, settings: KafkaConsumerSettings, logger: LoggerLike) -> None:
        self._settings = settings
        self._logger = logger
        self._client_id = f"{settings.client_prefix}-{uuid4().hex[:6]}"
        self._consumer = AIOKafkaConsumer(settings.topic, client_id=self._client_id, group_id=settings.group)
        self._processor: asyncio.Task | None = None
        self._on_message: Callable[[ConsumerRecord], Awaitable[None]] | None = None

    def set_message_handler(self, on_message: Callable[[ConsumerRecord], Awaitable[None]]) -> None:
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
            await self._on_message(message)

    async def is_healthy(self) -> bool:
        await self._consumer.topics()
        # TODO: process task
        return True

    async def stop(self) -> None:
        self._logger.info("Shutting down the consumer producer '%s'...", self._client_id)
        await self._consumer.stop()
