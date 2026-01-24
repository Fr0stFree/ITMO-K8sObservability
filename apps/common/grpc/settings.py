from pydantic import Field
from pydantic_settings import BaseSettings


class GRPCServerSettings(BaseSettings):
    workers_amount: int = Field(10, alias="GRPC_SERVER_WORKERS_AMOUNT")
    port: int = Field(50051, alias="GRPC_SERVER_PORT")


class GRPCClientSettings(BaseSettings):
    address: str = Field("localhost:50051", alias="GRPC_TARGET_ADDRESS")
