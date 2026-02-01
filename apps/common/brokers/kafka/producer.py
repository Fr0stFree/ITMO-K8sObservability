import json
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from opentelemetry.trace import Tracer

from common.brokers.interface import IProducerInterceptor
from common.brokers.kafka.settings import KafkaProducerSettings
from common.logs import LoggerLike


class KafkaProducer:

    def __init__(
        self,
        settings: KafkaProducerSettings,
        logger: LoggerLike,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._client_id = f"{settings.client_prefix}-{uuid4().hex[:6]}"
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.address,
            client_id=self._client_id,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        self._interceptor: list[IProducerInterceptor] = []

    def add_interceptor(self, interceptor: IProducerInterceptor) -> None:
        self._interceptor.append(interceptor)

    async def start(self) -> None:
        self._logger.info(
            "Starting the kafka producer '%s' on server '%s' with topic '%s'...",
            self._client_id,
            self._settings.address,
            self._settings.topic,
        )
        await self._producer.start()

    async def is_healthy(self) -> bool:
        await self._producer.partitions_for(self._settings.topic)
        return True

    async def stop(self) -> None:
        self._logger.info("Shutting down the kafka producer '%s'...", self._client_id)
        await self._producer.stop()

    def _encode_headers(self, headers: dict[str, str]) -> list[tuple[str, bytes]]:
        return [(key, value.encode("utf-8")) for key, value in headers.items()]

    async def send(self, payload: dict, meta: dict) -> None:
        for interceptor in self._interceptor:
            await interceptor.before_send(self._settings.topic, payload, meta)

        try:
            headers = self._encode_headers(meta)
            await self._producer.send_and_wait(self._settings.topic, payload, headers=headers)
        except Exception as error:
            for interceptor in self._interceptor:
                await interceptor.on_error(self._settings.topic, payload, meta, error)
            raise error

        for interceptor in self._interceptor:
            await interceptor.after_send(self._settings.topic, payload, meta)
