from pydantic_settings import BaseSettings


class MetricsServerSettings(BaseSettings):
    port: int = 9001
