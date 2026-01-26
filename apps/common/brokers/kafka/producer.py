from typing import Any
from uuid import uuid4

from aiokafka import AIOKafkaProducer

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
        # TODO: key, value serializers
        self._producer = AIOKafkaProducer(bootstrap_servers=settings.address, client_id=self._client_id)

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

    async def send(self, message: Any) -> None:
        await self._producer.send_and_wait(self._settings.topic, message)
