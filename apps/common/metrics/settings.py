from pydantic import Field
from pydantic_settings import BaseSettings


class MetricsServerSettings(BaseSettings):
    port: int = Field(9000, alias="METRICS_SERVER_PORT")

