from contextlib import asynccontextmanager
from typing import AsyncGenerator
import grpc
import uvicorn
from fastapi import FastAPI, Depends

from apps.api_service.src.logs import logger, LOGGING_CONFIG
from protocol.monitoring_service_pb2_grpc import MonitoringServiceStub
from protocol.monitoring_service_pb2 import AddTargetRequest


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting the application...")
    channel = grpc.aio.insecure_channel("localhost:50051")
    monitoring_service = MonitoringServiceStub(channel)
    app.state.monitoring_service = monitoring_service

    yield

    await channel.close()
    logger.info("Application shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/{url}", response_model=None)
async def root(url: str) -> str:
    app.state.monitoring_service.AddTarget(AddTargetRequest(target_url=url))
    return "OK"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG, log_level="info")
