from contextlib import asynccontextmanager
from typing import AsyncGenerator
import grpc
import uvicorn
from fastapi import FastAPI

from api_service.src.config import logger, LOGGING_CONFIG
from protocol import greeter_pb2_grpc, greeter_pb2

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting the application...")
    yield
    logger.info("Application shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    channel = grpc.insecure_channel("localhost:50051")
    stub = greeter_pb2_grpc.GreeterServiceStub(channel)
    response = stub.SayHello(
        greeter_pb2.HelloRequest(name="Danila")
    )
    return {"result": response.message}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG, log_level="info")
