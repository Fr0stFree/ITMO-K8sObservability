from pydantic import Field
from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    username: str = Field("postgres", alias="POSTGRES_USER")
    password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    database: str = Field("postgres", alias="POSTGRES_DB")
    host: str = Field("localhost", alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    should_log_statements: bool = Field(False, alias="POSTGRES_LOG_STATEMENTS")

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
