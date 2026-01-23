from pydantic_settings import BaseSettings


class GRPCServerSettings(BaseSettings):
    workers_amount: int = 10
    port: int = 50051
