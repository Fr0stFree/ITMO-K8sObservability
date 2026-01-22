from contextlib import asynccontextmanager
from typing import AsyncGenerator
import grpc
import uvicorn
from fastapi import FastAPI

from api_service.src.config import logger, LOGGING_CONFIG
from protocol.monitoring_service_pb2_grpc import MonitoringServiceStub
from protocol.monitoring_service_pb2 import AddTargetRequest


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting the application...")
    yield
    logger.info("Application shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/{url}")
async def root(url: str):
    channel = grpc.insecure_channel("localhost:50051")
    stub = MonitoringServiceStub(channel)
    response = stub.AddTarget(AddTargetRequest(target_url=url))
    print(f"{response = }")
    return "OK"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG, log_level="info")
