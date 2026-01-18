from contextlib import asynccontextmanager
from typing import AsyncGenerator
from prometheus_client import make_asgi_app
from fastapi import FastAPI
import uvicorn

from config import logger, LOGGING_CONFIG
from tracing import process_endpoint
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Mounting /metrics endpoint...")
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("Setting up tracing...")
    FastAPIInstrumentor.instrument_app(app)
    yield
    logger.info("Application shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    with process_endpoint(path="/", method="GET"):
        return {"message": "Hello, World!"}


@app.get("/items/{item_id}")
async def read_item(item_id: int) -> dict:
    with process_endpoint(path="/items/:itemId", method="GET"):
        return {"item_id": item_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG, log_level="info")
