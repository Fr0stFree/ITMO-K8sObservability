from pydantic_settings import BaseSettings


class GRPCServerSettings(BaseSettings):
    workers_amount: int = 10
    port: int = 50051


class GRPCClientSettings(BaseSettings):
    target: str = "localhost:50051"
