import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import cast
from uuid import uuid4

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import ConsumerRecord
from opentelemetry.trace import Tracer

from common.brokers.interface import AbstractConsumerInterceptor
from common.brokers.kafka.settings import KafkaConsumerSettings
from common.logs import LoggerLike


class KafkaConsumer:
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
        self._interceptors: list[AbstractConsumerInterceptor] = []

    def set_message_handler(self, on_message: Callable[[dict], Awaitable[None]]) -> None:
        self._on_message = on_message

    def add_interceptor(self, interceptor: AbstractConsumerInterceptor) -> None:
        self._interceptors.append(interceptor)

    async def start(self) -> None:
        self._logger.info(
            "Starting the kafka consumer '%s' on server '%s' with topic '%s'...",
            self._client_id,
            self._settings.address,
            self._settings.topic,
        )
        await self._consumer.start()
        self._processor = asyncio.create_task(self._process_messages())

    def _retrieve_headers(self, message: ConsumerRecord) -> dict[str, str]:
        headers = {}
        if message.headers is not None:
            for key, value in message.headers:
                headers[key] = value.decode("utf-8")
        return headers

    async def _process_messages(self) -> None:
        if self._processor is None:
            raise ValueError("Consumer is not started")

        if self._on_message is None:
            raise ValueError("Consumer message handler is not set")

        async for message in self._consumer:
            headers = self._retrieve_headers(message)
            payload = cast(dict, message.value)
            for interceptor in self._interceptors:
                await interceptor.before_receive(message.topic, payload, headers)

            try:
                await self._on_message(payload)
            except Exception as error:
                for interceptor in self._interceptors:
                    await interceptor.on_error(message.topic, payload, headers, error)
                raise error

            for interceptor in self._interceptors:
                await interceptor.after_receive(message.topic, payload, headers)

    async def is_healthy(self) -> bool:
        await self._consumer.topics()
        if self._processor is None or self._processor.done():
            return False
        return True

    async def stop(self) -> None:
        self._logger.info("Shutting down the kafka consumer '%s'...", self._client_id)
        await self._consumer.stop()
