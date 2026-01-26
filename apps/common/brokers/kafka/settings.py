from pydantic import Field
from pydantic_settings import BaseSettings


class KafkaProducerSettings(BaseSettings):
    topic: str = Field(..., alias="KAFKA_PRODUCER_TOPIC")
    address: str = Field(..., alias="KAFKA_PRODUCER_ADDRESS")
    client_prefix: str = Field(..., alias="KAFKA_PRODUCER_CLIENT_PREFIX")
