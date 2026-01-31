import json
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from opentelemetry.trace import Tracer

from common.brokers.kafka.settings import KafkaProducerSettings
from common.logs import LoggerLike
from common.tracing.context.kafka import KafkaContextInjector


class KafkaProducer:
    context_injector = KafkaContextInjector()

    def __init__(
        self,
        settings: KafkaProducerSettings,
        logger: LoggerLike,
        tracer: Tracer,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._tracer = tracer
        self._client_id = f"{settings.client_prefix}-{uuid4().hex[:6]}"
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.address,
            client_id=self._client_id,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

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

    async def send(self, payload: dict) -> None:
        with self._tracer.start_as_current_span(
            "kafka.produce",
            attributes={"messaging.destination": self._settings.topic, "messaging.client_id": self._client_id},
        ):
            headers = {}
            await self._producer.send_and_wait(
                self._settings.topic, payload, headers=self.context_injector.inject(headers)
            )
