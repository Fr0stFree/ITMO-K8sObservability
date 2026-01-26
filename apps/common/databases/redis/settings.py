from pydantic import Field
from pydantic_settings import BaseSettings


class RedisClientSettings(BaseSettings):
    host: str = Field("localhost", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    db: int = Field(0, alias="REDIS_DB")
    password: str | None = Field(None, alias="REDIS_PASSWORD")

    @property
    def dsn(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
