from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    username: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    should_log_statements: bool = False

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
